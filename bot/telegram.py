import os
import sys
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from walltrack.chains import ChainManager, DEFAULT_CHAIN
from walltrack.tracker import WalletTracker
from walltrack.gas import GasTracker
from walltrack.flashloan import FlashLoanSimulator
from walltrack.prices import PriceFeed
from walltrack.history import HistoryManager

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

api_keys = {
    v: os.environ.get(v)
    for v in [
        "ETHERSCAN_API_KEY",
        "BSCSCAN_API_KEY",
        "POLYGONSCAN_API_KEY",
        "ARBISCAN_API_KEY",
    ]
    if os.environ.get(v)
}

user_chains: dict = {}


def get_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🔍 Track", callback_data="track"),
                InlineKeyboardButton("⛽ Gas", callback_data="gas"),
            ],
            [
                InlineKeyboardButton("💰 Price", callback_data="price"),
                InlineKeyboardButton("💸 Flash", callback_data="flash"),
            ],
            [
                InlineKeyboardButton("📊 Portfolio", callback_data="portfolio"),
                InlineKeyboardButton("🔄 Chain", callback_data="chain"),
            ],
        ]
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_chains[uid] = DEFAULT_CHAIN

    await update.message.reply_text(
        "🚀 *WallTrack Bot*\n\n"
        "I track crypto wallets across 4 chains!\n\n"
        "Commands:\n"
        "`/track 0x...` — Track wallet\n"
        "`/gas` — Gas prices\n"
        "`/price ethereum` — Coin price\n"
        "`/flash` — Flash loan sim\n"
        "`/portfolio 0x...` — USD value\n"
        "`/history 0x...` — Balance history\n"
        "`/chain bsc` — Switch chain\n"
        "`/web3 0x...` — On-chain data\n\n"
        "Or just send me a wallet address!",
        parse_mode="Markdown",
        reply_markup=get_keyboard(),
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Commands:\n"
        "/track 0x... — Track wallet\n"
        "/gas — Gas prices\n"
        "/price <coin> — Crypto price\n"
        "/flash — Flash loan sim\n"
        "/portfolio 0x... — Portfolio USD\n"
        "/history 0x... — Balance history\n"
        "/web3 0x... — On-chain data\n"
        "/chain <name> — Switch chain\n"
        "/start — Show menu",
        reply_markup=get_keyboard(),
    )


async def chain_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    chains = ["ethereum", "bsc", "polygon", "arbitrum"]

    if context.args:
        c = context.args[0].lower()
        if c in chains:
            user_chains[uid] = c
            await update.message.reply_text(f"✅ Switched to *{c}*", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"Chains: {', '.join(chains)}")
    else:
        current = user_chains.get(uid, DEFAULT_CHAIN)
        await update.message.reply_text(f"Current chain: *{current}*", parse_mode="Markdown")


async def track(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    chain = user_chains.get(uid, DEFAULT_CHAIN)

    if not context.args:
        await update.message.reply_text("Usage: /track 0x...")
        return

    address = context.args[0]
    if not address.startswith("0x") or len(address) != 42:
        await update.message.reply_text("Invalid address")
        return

    await update.message.reply_text("🔍 Scanning...")

    try:
        cm = ChainManager(api_keys)
        tr = WalletTracker(cm)
        result = tr.analyze(address, chain)
        HistoryManager().save_snapshot(result)

        msg = (
            f"*WallTrack — {result['chain']}*\n"
            f"`{result['address'][:20]}...`\n\n"
            f"💰 *Balance:* {result['native_balance']:.6f} {result['symbol']}\n"
            f"📝 *Tx Count:* {result['transaction_count']:,}\n"
        )

        if result["last_transaction"]:
            lt = result["last_transaction"]
            msg += f"🕐 *Last Tx:* {lt['timestamp']}\n"

        if result["top_tokens"]:
            msg += "\n*Top Tokens:*\n"
            for t in result["top_tokens"][:3]:
                msg += f"• {t['symbol']}: {t['total_value']:,.2f}\n"

        await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


async def gas_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    key = api_keys.get("ETHERSCAN_API_KEY")
    if not key:
        await update.message.reply_text("ETHERSCAN_API_KEY not set")
        return

    await update.message.reply_text("⛽ Fetching gas...")

    try:
        gt = GasTracker(key)
        prices = gt.get_gas_prices()
        costs = prices.estimate_cost()

        msg = (
            f"⛽ *Gas Tracker*\n"
            f"{prices.recommendation()}\n\n"
            f"Safe     : {prices.safe} gwei (`{costs['safe']:.6f} ETH`)\n"
            f"Standard : {prices.standard} gwei (`{costs['standard']:.6f} ETH`)\n"
            f"Fast     : {prices.fast} gwei (`{costs['fast']:.6f} ETH`)\n"
            f"🕐 {prices.timestamp}"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


async def price_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /price ethereum")
        return

    coin = context.args[0].lower()
    await update.message.reply_text(f"💵 Checking {coin}...")

    try:
        pf = PriceFeed()
        p = pf.get_price(coin)
        if not p:
            await update.message.reply_text(f"Coin '{coin}' not found")
            return

        change = f"{p.change_24h:+.2f}%" if p.change_24h else "N/A"
        await update.message.reply_text(
            f"*{coin.upper()}*\n"
            f"💵 USD: `${p.usd:,.2f}`\n"
            f"₿ BTC: `{p.btc:.8f}`\n"
            f"📊 24h: {change}",
            parse_mode="Markdown",
        )
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


async def flash_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💸 Simulating...")

    try:
        sim = FlashLoanSimulator()
        opps = sim.find_arbitrage()

        if not opps:
            await update.message.reply_text("No arbitrage opportunities found.")
            return

        msg = "*💸 Flash Loan Arbitrage*\n\n"
        for opp in opps[:3]:
            msg += (
                f"Buy: {opp['buy_from']} → Sell: {opp['sell_to']}\n"
                f"Spread: {opp['spread_pct']:.3f}%\n"
                f"Profit: `{opp['profit_eth']:.6f} ETH` (${opp['profit_usd']:.2f})\n\n"
            )
        msg += "_Simulated data — not real prices_"
        await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


async def portfolio_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    chain = user_chains.get(uid, DEFAULT_CHAIN)

    if not context.args:
        await update.message.reply_text("Usage: /portfolio 0x...")
        return

    address = context.args[0]
    await update.message.reply_text("💵 Valuing portfolio...")

    try:
        cm = ChainManager(api_keys)
        tr = WalletTracker(cm)
        pf = PriceFeed()

        result = tr.analyze(address, chain)
        balances = {"ethereum": result["native_balance"]}
        for t in result.get("top_tokens", []):
            balances[t["symbol"].lower()] = t["total_value"]

        pv = pf.get_portfolio_value(balances)

        msg = f"*Portfolio — {address[:10]}...*\n"
        msg += f"*Chain:* {chain}\n\n"

        for a in pv["assets"][:5]:
            msg += f"• {a['coin']}: ${a['value_usd']:,.2f}\n"

        msg += f"\n*Total: ${pv['total_usd']:,.2f}*"
        await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


async def history_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /history 0x...")
        return

    address = context.args[0]
    try:
        hm = HistoryManager()
        history = hm.get_balance_history(address)

        if not history:
            await update.message.reply_text("No history yet. Scan a wallet first with /track")
            return

        msg = f"*📊 History — {address[:10]}...*\n\n"
        for entry in history[-5:]:
            msg += f"• {entry['time'][:10]}: {entry['balance']:.6f}\n"

        if len(history) >= 2:
            first = history[0]["balance"]
            last = history[-1]["balance"]
            change = last - first
            pct = (change / first * 100) if first else 0
            arrow = "📈" if change >= 0 else "📉"
            msg += f"\n{arrow} Change: {change:+.6f} ({pct:+.2f}%)"

        await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


async def web3_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    chain = user_chains.get(uid, DEFAULT_CHAIN)

    if not context.args:
        await update.message.reply_text("Usage: /web3 0x...")
        return

    address = context.args[0]
    await update.message.reply_text("🧠 Reading on-chain...")

    try:
        from walltrack.web3_provider import Web3Provider

        w3 = Web3Provider(chain)
        if not w3.is_connected():
            await update.message.reply_text(f"Cannot connect to {chain}")
            return

        data = w3.analyze_onchain(address)
        await update.message.reply_text(
            f"*🧠 {data['chain']} (On-Chain)*\n"
            f"Connected: {'✅' if data['connected'] else '❌'}\n"
            f"Balance: `{data['balance']:.6f}`\n"
            f"Tx Count: `{data['tx_count']}`\n"
            f"Block: `#{data['latest_block']['number']}`\n"
            f"Gas: `{data['gas_price']['gwei']} gwei`",
            parse_mode="Markdown",
        )
    except ImportError:
        await update.message.reply_text("web3.py not installed")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    chain = user_chains.get(uid, DEFAULT_CHAIN)
    text = update.message.text.strip()

    if text.startswith("0x") and len(text) == 42:
        await update.message.reply_text("🔍 Scanning...")
        try:
            cm = ChainManager(api_keys)
            tr = WalletTracker(cm)
            result = tr.analyze(text, chain)
            HistoryManager().save_snapshot(result)

            msg = (
                f"*WallTrack — {result['chain']}*\n"
                f"`{result['address'][:20]}...`\n\n"
                f"💰 *Balance:* {result['native_balance']:.6f} {result['symbol']}\n"
                f"📝 *Tx Count:* {result['transaction_count']:,}\n"
            )
            if result["top_tokens"]:
                msg += "\n*Top Tokens:*\n"
                for t in result["top_tokens"][:3]:
                    msg += f"• {t['symbol']}: {t['total_value']:,.2f}\n"

            await update.message.reply_text(msg, parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"Error: {e}")
    else:
        await update.message.reply_text(
            "Send a wallet address or use /help for commands",
            reply_markup=get_keyboard(),
        )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = update.effective_user.id
    data = query.data

    if data == "track":
        await query.edit_message_text("Send me a wallet address starting with 0x")
    elif data == "gas":
        await gas_cmd(update, context)
    elif data == "price":
        await query.edit_message_text("Usage: /price <coin>\nExample: /price bitcoin")
    elif data == "flash":
        await flash_cmd(update, context)
    elif data == "portfolio":
        await query.edit_message_text("Usage: /portfolio 0x...")
    elif data == "chain":
        await query.edit_message_text(
            "Change chain: /chain ethereum | /chain bsc | /chain polygon | /chain arbitrum"
        )


def run():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("TELEGRAM_BOT_TOKEN env var not set")
        print("Get one from @BotFather on Telegram")
        sys.exit(1)

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("track", track))
    app.add_handler(CommandHandler("gas", gas_cmd))
    app.add_handler(CommandHandler("price", price_cmd))
    app.add_handler(CommandHandler("flash", flash_cmd))
    app.add_handler(CommandHandler("portfolio", portfolio_cmd))
    app.add_handler(CommandHandler("history", history_cmd))
    app.add_handler(CommandHandler("web3", web3_cmd))
    app.add_handler(CommandHandler("chain", chain_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 WallTrack Bot running...")
    app.run_polling()


if __name__ == "__main__":
    run()
