import os
import sys
import time
import argparse
from typing import Dict, List, Optional

from .chains import ChainManager, DEFAULT_CHAIN, CHAINS
from .tracker import WalletTracker
from .export import ExportManager
from .charts import ChartGenerator
from .gas import GasTracker
from .flashloan import FlashLoanSimulator
from .history import HistoryManager
from .prices import PriceFeed
from .comparator import cmd_compare
from .alerts import GasAlert
from .holder_analyzer import HolderAnalyzer


def load_api_keys() -> Dict[str, str]:
    env_vars = [
        "ETHERSCAN_API_KEY",
        "BSCSCAN_API_KEY",
        "POLYGONSCAN_API_KEY",
        "ARBISCAN_API_KEY",
    ]
    return {v: os.environ.get(v) for v in env_vars if os.environ.get(v)}


def cmd_track(args, api_keys):
    chain_mgr = ChainManager(api_keys)
    tracker = WalletTracker(chain_mgr)

    try:
        result = tracker.analyze(args.address, args.chain, args.token_limit)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    if args.export:
        ext = args.export
        fpath = f"walltrack_report_{args.address[:8]}.{ext}"
        ExportManager.export(result, ext, fpath)
        print(f"Exported to {fpath}")

    if args.html:
        fpath = args.html if args.html != True else f"walltrack_report_{args.address[:8]}.html"
        ChartGenerator.to_html(result, fpath)
        print(f"HTML report saved to {fpath}")

    display_result(result)

    if args.save_history:
        HistoryManager().save_snapshot(result)

    return result


def cmd_interactive(args, api_keys):
    chain_mgr = ChainManager(api_keys)
    tracker = WalletTracker(chain_mgr)
    history = HistoryManager()
    chains = chain_mgr.list_chains()
    pf = PriceFeed()

    current_chain = DEFAULT_CHAIN
    print("\n  🚀 WallTrack Interactive Mode")
    print("  " + "=" * 50)
    print("  Commands:")
    print("    <address>          Track wallet")
    print("    chain <name>       Switch chain")
    print("    gas                Check gas prices")
    print("    flash              Flash loan simulator")
    print("    history <addr>     Portfolio history")
    print("    compare <a> <b>    Compare wallets")
    print("    price <coin>       Check crypto price")
    print("    portfolio <addr>   USD portfolio value")
    print("    web3 <addr>        On-chain data (web3)")
    print("    gas-alert <gwei>   Monitor gas threshold")
    print("    help               Show help")
    print("    exit               Quit")
    print("  " + "=" * 50)

    while True:
        try:
            inp = input(f"\n  [{current_chain}]> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not inp:
            continue
        if inp == "exit":
            break
        if inp == "help":
            continue

        if inp.startswith("chain "):
            c = inp.split(" ", 1)[1]
            if c in chains:
                current_chain = c
                print(f"  Switched to {chains[c]}")
            else:
                print(f"  Unknown chain. Available: {', '.join(chains.keys())}")
            continue

        if inp == "gas":
            eth_key = api_keys.get("ETHERSCAN_API_KEY")
            if not eth_key:
                print("  Set ETHERSCAN_API_KEY for gas tracking")
                continue
            try:
                gas = GasTracker(eth_key)
                prices = gas.get_gas_prices()
                GasTracker.display(prices)
            except Exception as e:
                print(f"  Gas error: {e}")
            continue

        if inp == "flash":
            sim = FlashLoanSimulator()
            opps = sim.find_arbitrage()
            FlashLoanSimulator.display(opps)
            continue

        if inp.startswith("history "):
            addr = inp.split(" ", 1)[1]
            history.display_history(addr, current_chain)
            continue

        if inp.startswith("compare "):
            addrs = inp.split(" ")[1:]
            if len(addrs) >= 2:
                cmd_compare(addrs, chain_mgr, tracker)
            else:
                print("  Need at least 2 addresses: compare <a> <b> [c...]")
            continue

        if inp.startswith("price "):
            coin = inp.split(" ", 1)[1]
            price = pf.get_price(coin)
            if price:
                print(f"\n  {coin.upper():12s} ${price.usd:>8.2f} "
                      f"{price.change_24h:+.2f}%" if price.change_24h else "")
            else:
                print(f"  Coin '{coin}' not found")
            continue

        if inp.startswith("portfolio "):
            addr = inp.split(" ", 1)[1]
            try:
                result = tracker.analyze(addr, current_chain)
                balances = {"ethereum": result["native_balance"]}
                for t in result.get("top_tokens", []):
                    balances[t["symbol"].lower()] = t["total_value"]
                portfolio = pf.get_portfolio_value(balances)
                PriceFeed.display_portfolio(portfolio)
            except Exception as e:
                print(f"  Error: {e}")
            continue

        if inp.startswith("web3 "):
            addr = inp.split(" ", 1)[1]
            try:
                from .web3_provider import Web3Provider
                w3 = Web3Provider(current_chain)
                if not w3.is_connected():
                    print("  Web3 not connected")
                    continue
                data = w3.analyze_onchain(addr)
                print(f"\n  Web3 On-Chain ({data['chain']}):")
                print(f"  Balance    : {data['balance']:.6f}")
                print(f"  Tx Count   : {data['tx_count']}")
                print(f"  Block      : {data['latest_block']['number']}")
                print(f"  Gas Price  : {data['gas_price']['gwei']} gwei")
            except ImportError:
                print("  web3.py not installed. Run: pip install web3")
            except Exception as e:
                print(f"  Web3 error: {e}")
            continue

        if inp.startswith("gas-alert "):
            try:
                threshold = int(inp.split(" ")[1])
            except (IndexError, ValueError):
                print("  Usage: gas-alert <gwei_threshold>")
                continue
            eth_key = api_keys.get("ETHERSCAN_API_KEY")
            if not eth_key:
                print("  Set ETHERSCAN_API_KEY for gas alerts")
                continue
            alert = GasAlert(eth_key, threshold, GasAlert.display_alert)
            print(f"  Monitoring gas (threshold: {threshold} gwei)... Ctrl+C to stop")
            try:
                while True:
                    alert.check()
                    time.sleep(30)
            except KeyboardInterrupt:
                print("\n  Stopped gas monitoring")
            continue

        if inp.startswith("0x") and len(inp) == 42:
            try:
                result = tracker.analyze(inp, current_chain)
                display_result(result)
                history.save_snapshot(result)
            except Exception as e:
                print(f"  Error: {e}")
            continue

        print(f"  Unknown command: {inp}")


def cmd_gas(args, api_keys):
    eth_key = api_keys.get("ETHERSCAN_API_KEY")
    if not eth_key:
        print("Set ETHERSCAN_API_KEY env var for gas tracking.")
        sys.exit(1)
    gas = GasTracker(eth_key)
    prices = gas.get_gas_prices()
    GasTracker.display(prices)


def cmd_flash(args, api_keys):
    sim = FlashLoanSimulator()
    opps = sim.find_arbitrage(
        min_profit_usd=args.min_profit,
        loan_amount_eth=args.loan,
    )
    FlashLoanSimulator.display(opps)


def cmd_history(args, api_keys):
    history = HistoryManager()
    history.display_history(args.address, args.chain)


def cmd_compare_cli(args, api_keys):
    if len(args.addresses) < 2:
        print("Need at least 2 addresses to compare.")
        sys.exit(1)
    chain_mgr = ChainManager(api_keys)
    tracker = WalletTracker(chain_mgr)
    cmd_compare(args.addresses, chain_mgr, tracker)


def cmd_price(args, api_keys):
    pf = PriceFeed()
    if args.coin:
        price = pf.get_price(args.coin)
        if price:
            print(f"\n  {args.coin.upper():12s} ${price.usd:>8.2f} "
                  f"{price.change_24h:+.2f}%" if price.change_24h else "")
        else:
            print(f"Coin '{args.coin}' not found")
    else:
        print("Usage: walltrack price <coin_id>")
        print("Example: walltrack price ethereum")
        print("Example: walltrack price bitcoin")


def cmd_portfolio(args, api_keys):
    chain_mgr = ChainManager(api_keys)
    tracker = WalletTracker(chain_mgr)
    pf = PriceFeed()

    try:
        result = tracker.analyze(args.address, args.chain)
        balances = {"ethereum": result["native_balance"]}
        for t in result.get("top_tokens", []):
            balances[t["symbol"].lower()] = t["total_value"]
        portfolio = pf.get_portfolio_value(balances)
        PriceFeed.display_portfolio(portfolio)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def cmd_web3(args, api_keys):
    try:
        from .web3_provider import Web3Provider
    except ImportError:
        print("web3.py not installed. Run: pip install web3")
        sys.exit(1)

    w3 = Web3Provider(args.chain)
    if not w3.is_connected():
        print(f"Cannot connect to {args.chain} RPC")
        sys.exit(1)

    data = w3.analyze_onchain(args.address)
    print(f"\n  Web3 On-Chain ({data['chain']}):")
    print(f"  Connected  : {'Yes' if data['connected'] else 'No'}")
    print(f"  Balance    : {data['balance']:.6f}")
    print(f"  Tx Count   : {data['tx_count']}")
    print(f"  Block      : #{data['latest_block']['number']} "
          f"({data['latest_block']['tx_count']} tx)")
    print(f"  Gas Price  : {data['gas_price']['gwei']} gwei")


def cmd_holder(args, api_keys):
    eth_key = api_keys.get("ETHERSCAN_API_KEY", "")
    analyzer = HolderAnalyzer()
    report = analyzer.analyze(
        token_symbol=args.symbol,
        contract=args.contract or "",
        etherscan_key=eth_key,
    )
    HolderAnalyzer.display(report)

    if args.charts:
        try:
            from .holder_charts import generate_charts
            generate_charts(report, args.charts_dir)
        except ImportError:
            print("  Install matplotlib: pip install matplotlib")

    return report


def cmd_autocomplete(args, api_keys):
    from .autocomplete import install as install_comp
    install_comp(args.shell)


def cmd_gas_alert(args, api_keys):
    eth_key = api_keys.get("ETHERSCAN_API_KEY")
    if not eth_key:
        print("Set ETHERSCAN_API_KEY env var.")
        sys.exit(1)

    alert = GasAlert(eth_key, args.threshold, GasAlert.display_alert)
    print(f"Monitoring gas (threshold: {args.threshold} gwei)... Ctrl+C to stop")
    try:
        while True:
            alert.check()
            time.sleep(30)
    except KeyboardInterrupt:
        print("\nStopped gas monitoring")


def cmd_schedule(args, api_keys):
    from .scheduler import Scheduler

    sched = Scheduler(api_keys)
    addr_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "data", "watched.txt"
    )

    if args.action == "add" and args.address:
        sched.add_job(args.address, args.chain, args.interval)

        os.makedirs(os.path.dirname(addr_file), exist_ok=True)
        with open(addr_file, "a") as f:
            f.write(f"{args.address},{args.chain},{args.interval}\n")

    elif args.action == "list":
        jobs = sched.list_jobs()
        if not jobs and os.path.exists(addr_file):
            with open(addr_file) as f:
                for line in f:
                    parts = line.strip().split(",")
                    if len(parts) >= 1:
                        sched.jobs.clear()
                        break

        if not sched.jobs and os.path.exists(addr_file):
            with open(addr_file) as f:
                for line in f:
                    parts = line.strip().split(",")
                    addr = parts[0]
                    chain = parts[1] if len(parts) > 1 else "ethereum"
                    interval = int(parts[2]) if len(parts) > 2 else 3600
                    sched.add_job(addr, chain, interval)

        jobs = sched.list_jobs()
        if jobs:
            print(f"\n  📋 Scheduled Jobs ({len(jobs)}):")
            for j in jobs:
                print(f"  {j['address'][:10]}... | {j['chain']:10s} "
                      f"every {j['interval']}s | {'RUNNING' if j['running'] else 'IDLE'}")
        else:
            print("No jobs. Add with: walltrack schedule add <address>")

    elif args.action == "start":
        if os.path.exists(addr_file):
            with open(addr_file) as f:
                for line in f:
                    parts = line.strip().split(",")
                    if len(parts) >= 1:
                        addr = parts[0]
                        chain = parts[1] if len(parts) > 1 else "ethereum"
                        interval = int(parts[2]) if len(parts) > 2 else 3600
                        sched.add_job(addr, chain, interval)
        sched.start()
        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            sched.stop()

    elif args.action == "stop":
        sched.stop()


def display_result(data: Dict):
    chain = data["chain"]
    symbol = data["symbol"]
    print("=" * 60)
    print(f"  WALLTRACK — {chain}")
    print("=" * 60)
    print(f"\n  Address       : {data['address']}")
    print(f"  Balance       : {data['native_balance']:.6f} {symbol}")
    print(f"  Tx Count      : {data['transaction_count']:,}")

    if data["last_transaction"]:
        lt = data["last_transaction"]
        print(f"\n  Last Transaction:")
        print(f"    Hash      : {lt['hash']}")
        print(f"    From      : {lt['from']}")
        print(f"    To        : {lt['to']}")
        print(f"    Value     : {lt['value']:.6f} ETH")
        print(f"    Time      : {lt['timestamp']}")

    if data["top_tokens"]:
        print(f"\n  Top Tokens (by volume):")
        for i, token in enumerate(data["top_tokens"], 1):
            print(
                f"    {i}. {token['symbol']:10s} | "
                f"Vol: {token['total_value']:>12.2f} | "
                f"Tx: {token['tx_count']:>4d} | "
                f"{token['contract'][:10]}..."
            )
    print("=" * 60)


def build_parser():
    parser = argparse.ArgumentParser(
        description="WallTrack - Multi-Chain Crypto Wallet Tracker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  walltrack 0x...                        Track wallet
  walltrack 0x... --chain bsc            Track on BSC
  walltrack 0x... --export csv --html    Export report
  walltrack -i                           Interactive mode
  walltrack gas                          Check gas prices
  walltrack flash                        Flash loan simulator
  walltrack price ethereum               Check ETH price
  walltrack portfolio 0x...              USD portfolio value
  walltrack compare 0xA 0xB              Compare wallets
  walltrack web3 0x...                   On-chain data
  walltrack gas-alert 20                 Alert when gas < 20
  walltrack schedule add 0x...           Watch wallet
  walltrack autocomplete                 Tab completion
  walltrack holder UNI                    Analyze top holders
  walltrack holder SHIB --charts          Holder analysis + charts
  walltrack holder --contract 0x...       Analyze any token
        """,
    )

    parser.add_argument(
        "address", nargs="?", help="Wallet address",
    )
    parser.add_argument(
        "--chain", "-c", default=DEFAULT_CHAIN,
        help=f"Blockchain (default: {DEFAULT_CHAIN})",
    )
    parser.add_argument(
        "--export", choices=["json", "csv"],
        help="Export results to file",
    )
    parser.add_argument(
        "--html", nargs="?", const=True,
        help="Generate HTML report",
    )
    parser.add_argument(
        "--token-limit", type=int, default=5,
        help="Max tokens to show (default: 5)",
    )
    parser.add_argument(
        "--interactive", "-i", action="store_true",
        help="Interactive shell mode",
    )
    parser.add_argument(
        "--api-key",
        help="API key (overrides env vars)",
    )
    parser.add_argument(
        "--save-history", action="store_true",
        help="Save snapshot to history DB",
    )
    parser.add_argument(
        "--min-profit", type=float, default=10.0,
        help="Min profit USD for flash loan (default: 10)",
    )
    parser.add_argument(
        "--loan", type=float, default=100.0,
        help="Loan amount in ETH for flash loan (default: 100)",
    )
    parser.add_argument(
        "--interval", type=int, default=3600,
        help="Scan interval in seconds (default: 3600)",
    )
    parser.add_argument(
        "--threshold", type=int, default=20,
        help="Gas alert threshold in gwei (default: 20)",
    )
    parser.add_argument(
        "--shell",
        choices=["bash", "zsh", "powershell"],
        help="Shell for autocomplete installation",
    )
    parser.add_argument(
        "--symbol",
        default="",
        help="Token symbol for holder analysis (default: UNI)",
    )
    parser.add_argument(
        "--contract",
        default="",
        help="Token contract address for holder analysis",
    )
    parser.add_argument(
        "--charts", action="store_true",
        help="Generate matplotlib charts for holder analysis",
    )
    parser.add_argument(
        "--charts-dir", default="charts",
        help="Output directory for charts (default: charts)",
    )

    return parser


def run():
    parser = build_parser()

    if len(sys.argv) < 2:
        parser.print_help()
        return

    raw_cmd = sys.argv[1]
    api_keys = load_api_keys()

    if "--api-key" in sys.argv:
        idx = sys.argv.index("--api-key") + 1
        if idx < len(sys.argv):
            api_keys["ETHERSCAN_API_KEY"] = sys.argv[idx]

    if sys.argv[1] == "gas":
        args = parser.parse_args(sys.argv[1:2])
        return cmd_gas(args, api_keys)

    if sys.argv[1] == "flash":
        args = parser.parse_args(sys.argv[1:])
        return cmd_flash(args, api_keys)

    if sys.argv[1] == "price":
        if len(sys.argv) >= 3:
            args = parser.parse_args(["dummy"])
            args.coin = sys.argv[2]
        else:
            args = parser.parse_args(["dummy"])
            args.coin = None
        return cmd_price(args, api_keys)

    if sys.argv[1] == "portfolio":
        if len(sys.argv) >= 3:
            args = parser.parse_args(sys.argv[1:])
            args.address = None
            args.chain = DEFAULT_CHAIN
            # manually set address
            args.address = sys.argv[2]
            if "--chain" in sys.argv:
                ci = sys.argv.index("--chain") + 1
                if ci < len(sys.argv):
                    args.chain = sys.argv[ci]
        else:
            print("Usage: walltrack portfolio <address> [--chain chain]")
            return
        return cmd_portfolio(args, api_keys)

    if sys.argv[1] == "compare":
        if len(sys.argv) >= 4:
            args = parser.parse_args(["dummy"])
            args.addresses = sys.argv[2:]
        else:
            print("Usage: walltrack compare <addr1> <addr2> [addr3...]")
            return
        return cmd_compare_cli(args, api_keys)

    if sys.argv[1] == "web3":
        if len(sys.argv) >= 3:
            args = parser.parse_args(sys.argv[1:])
            args.address = sys.argv[2]
            args.chain = DEFAULT_CHAIN
            if "--chain" in sys.argv:
                ci = sys.argv.index("--chain") + 1
                if ci < len(sys.argv):
                    args.chain = sys.argv[ci]
        else:
            print("Usage: walltrack web3 <address> [--chain chain]")
            return
        return cmd_web3(args, api_keys)

    if sys.argv[1] == "gas-alert":
        if len(sys.argv) >= 3:
            try:
                threshold = int(sys.argv[2])
            except ValueError:
                print("Usage: walltrack gas-alert <gwei_threshold>")
                return
            args = parser.parse_args(["dummy"])
            args.threshold = threshold
        else:
            args = parser.parse_args(["dummy"])
            args.threshold = 20
        return cmd_gas_alert(args, api_keys)

    if sys.argv[1] == "autocomplete":
        shell = sys.argv[2] if len(sys.argv) >= 3 else None
        args = parser.parse_args(["dummy"])
        args.shell = shell
        return cmd_autocomplete(args, api_keys)

    if sys.argv[1] == "schedule":
        if len(sys.argv) >= 3:
            action = sys.argv[2]
            args = parser.parse_args(["dummy"])
            args.action = action
            args.address = None
            args.chain = DEFAULT_CHAIN
            args.interval = 3600

            if action == "add" and len(sys.argv) >= 4:
                args.address = sys.argv[3]
                if "--chain" in sys.argv:
                    ci = sys.argv.index("--chain") + 1
                    if ci < len(sys.argv):
                        args.chain = sys.argv[ci]
                if "--interval" in sys.argv:
                    ii = sys.argv.index("--interval") + 1
                    if ii < len(sys.argv):
                        args.interval = int(sys.argv[ii])
        else:
            print("Usage: walltrack schedule <add|list|start|stop> [...args]")
            return
        return cmd_schedule(args, api_keys)

    if sys.argv[1] == "holder":
        symbol = sys.argv[2] if len(sys.argv) >= 3 else "UNI"
        args = parser.parse_args(["dummy"])
        args.symbol = symbol
        args.contract = None
        args.charts = "--charts" in sys.argv
        args.charts_dir = "charts"

        if "--contract" in sys.argv:
            ci = sys.argv.index("--contract") + 1
            if ci < len(sys.argv):
                args.contract = sys.argv[ci]

        return cmd_holder(args, api_keys)

    args = parser.parse_args()

    if args.interactive:
        return cmd_interactive(args, api_keys)

    if args.address:
        return cmd_track(args, api_keys)

    parser.print_help()
