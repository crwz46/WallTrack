# WallTrack — Multi-Chain Crypto Wallet Tracker

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://python.org)
[![CI](https://github.com/crwz46/WallTrack/actions/workflows/test.yml/badge.svg)](https://github.com/crwz46/WallTrack/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/license-MIT-brightgreen)](LICENSE)

The ultimate crypto wallet intelligence tool — track wallets across **4 chains**, monitor gas, simulate flash loans, value portfolios in USD, compare wallets, run automated scans, and more. All from your terminal.

## Features

| Feature | Description |
|---------|-------------|
| 🪙 **Multi-Chain** | Ethereum, BSC, Polygon, Arbitrum |
| 💰 **Balance + Token Lookup** | Native + ERC-20 token balances |
| 📜 **Transaction History** | Count, last tx, timestamps |
| ⛽ **Gas Tracker** | Real-time gas + cost estimates |
| 💸 **Flash Loan Simulator** | Arbitrage opportunity finder |
| 💵 **USD Portfolio Value** | Live prices via CoinGecko |
| 📊 **Portfolio History** | SQLite-based balance tracking |
| 🔄 **Wallet Comparison** | Compare 2+ wallets side-by-side |
| 🎨 **HTML Reports** | Dark-mode dashboard |
| 📁 **Export** | JSON, CSV |
| 🖥️ **Interactive Shell** | REPL-mode CLI |
| 🧠 **Web3 On-Chain** | Direct RPC reads (web3.py) |
| ⏰ **Scheduled Scanner** | Watch wallets for changes |
| 🔔 **Gas Alerts** | Notify when gas is cheap |
| 🐳 **Docker** | Containerized |
| ⌨️ **Autocomplete** | Tab completion for bash/zsh/pwsh |
| ✅ **CI + Tests** | GitHub Actions + pytest (23 tests) |

## Quick Start

```bash
pip install -r requirements.txt

# Set your API key
export ETHERSCAN_API_KEY=your_key_here

# Track a wallet
python main.py 0x742d35Cc6634C0532925a3b844Bc454e4438f44e
```

## Usage

### Wallet Tracking

```bash
# Ethereum (default)
python main.py 0x742d35Cc6634C0532925a3b844Bc454e4438f44e

# BSC / Polygon / Arbitrum
python main.py 0x... --chain bsc
python main.py 0x... --chain polygon
python main.py 0x... --chain arbitrum

# Save to history DB
python main.py 0x... --save-history

# Export + HTML
python main.py 0x... --export csv --html
```

### Interactive Shell
```bash
python main.py -i
#   0x...           Track wallet
#   chain bsc      Switch chain
#   gas            Gas prices
#   flash          Flash loans
#   price eth      Check price
#   portfolio 0x.. USD value
#   web3 0x...     On-chain data
#   compare a b    Compare wallets
#   history 0x...  Balance history
#   gas-alert 20   Monitor gas
```

### Gas & Market Data
```bash
python main.py gas                    # Gas prices
python main.py price bitcoin          # BTC price
python main.py price ethereum         # ETH price
```

### Portfolio (USD)
```bash
python main.py portfolio 0x...
# Fetches live prices for ETH + tokens via CoinGecko
```

### Compare Wallets
```bash
python main.py compare 0xABC 0xDEF
python main.py compare 0xA 0xB 0xC 0xD  # Up to 10 wallets
```

### Web3 On-Chain Data
```bash
pip install web3
python main.py web3 0x...
# Reads directly from blockchain RPC
```

### Flash Loan Simulator
```bash
python main.py flash
# Simulates arbitrage across Uniswap, SushiSwap, Curve, Balancer
```

### Scheduled Scanning
```bash
python main.py schedule add 0x... --interval 3600
python main.py schedule list
python main.py schedule start   # Background daemon
```

### Gas Alerts
```bash
python main.py gas-alert 20
# Monitors gas and notifies when SafeGasPrice <= 20 gwei
```

### Portfolio History
```bash
python main.py history 0x...
# Shows balance snapshots over time
```

### Autocomplete
```bash
python main.py autocomplete bash
python main.py autocomplete zsh
python main.py autocomplete powershell
```

## 🌐 Web API (FastAPI)

Turn WallTrack into a REST API service.

```bash
# Install
pip install -r requirements.txt

# Run
python -c "from api.server import run; run()"

# Or with Docker
docker-compose up api
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info |
| GET | `/track/{address}` | Track wallet |
| GET | `/gas` | Gas prices |
| GET | `/price/{coin}` | Crypto price |
| GET | `/portfolio/{address}` | USD portfolio value |
| POST | `/compare` | Compare wallets |
| GET | `/web3/{address}` | On-chain data |
| GET | `/flash` | Flash loan sim |
| GET | `/history/{address}` | Balance history |
| GET | `/report/{address}` | HTML report |

```bash
# Example
curl http://localhost:8000/track/0x742d35Cc6634C0532925a3b844Bc454e4438f44e
curl http://localhost:8000/gas
curl http://localhost:8000/price/bitcoin
curl http://localhost:8000/portfolio/0x...?chain=ethereum
```

## 🤖 Telegram Bot

Interact with WallTrack directly from Telegram.

### Setup

1. Talk to [@BotFather](https://t.me/botfather) on Telegram
2. Create a bot → get the token
3. Set `TELEGRAM_BOT_TOKEN` in your `.env`
4. Run the bot:

```bash
python -c "from bot.telegram import run; run()"

# Or with Docker
docker-compose up bot
```

### Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Show menu |
| `/track 0x...` | Track wallet |
| `/gas` | Gas prices |
| `/price ethereum` | Coin price |
| `/flash` | Flash loan sim |
| `/portfolio 0x...` | USD portfolio |
| `/history 0x...` | Balance history |
| `/web3 0x...` | On-chain data |
| `/chain bsc` | Switch chain |
| `/help` | Help |

Or just send a wallet address directly!

## 🐳 Docker

### All Services
```bash
docker-compose up --build
```

### Individual Services
```bash
docker-compose up cli    # Interactive CLI
docker-compose up api    # FastAPI on :8000
docker-compose up bot    # Telegram bot
```

## 🔑 API Keys

Get free API keys from each explorer:

| Chain | Explorer | Env Variable |
|-------|----------|-------------|
| Ethereum | [etherscan.io](https://etherscan.io/myapikey) | `ETHERSCAN_API_KEY` |
| BSC | [bscscan.com](https://bscscan.com/myapikey) | `BSCSCAN_API_KEY` |
| Polygon | [polygonscan.com](https://polygonscan.com/myapikey) | `POLYGONSCAN_API_KEY` |
| Arbitrum | [arbiscan.io](https://arbiscan.io/myapikey) | `ARBISCAN_API_KEY` |

Copy `.env.example` to `.env` and fill in your keys.

## ✅ Run Tests

```bash
pytest tests/ -v
```

## 📁 Project Structure

```
WallTrack/
├── main.py                    # CLI entry point
├── walltrack/                 # Core package
│   ├── __init__.py
│   ├── cli.py                 # CLI + interactive shell
│   ├── tracker.py             # Wallet tracking logic
│   ├── chains.py              # Multi-chain config
│   ├── export.py              # CSV/JSON export
│   ├── charts.py              # HTML reports
│   ├── gas.py                 # Gas tracker
│   ├── flashloan.py           # Flash loan simulator
│   ├── history.py             # SQLite history
│   ├── prices.py              # CoinGecko price feed
│   ├── comparator.py          # Wallet comparison
│   ├── scheduler.py           # Background scanner
│   ├── autocomplete.py        # Shell tab completion
│   ├── alerts.py              # Gas alerts
│   └── web3_provider.py       # On-chain RPC reader
├── api/
│   └── server.py              # FastAPI web service
├── bot/
│   └── telegram.py            # Telegram bot
├── tests/
│   ├── test_chains.py
│   ├── test_features.py
│   └── test_advanced.py
├── .github/workflows/
│   └── test.yml               # GitHub Actions CI
├── Dockerfile                 # CLI container
├── Dockerfile.api             # API container
├── Dockerfile.bot             # Bot container
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## 🏆 Why Recruiters Love This

| Skill | Demonstrated |
|-------|-------------|
| Python | OOP, type hints, package architecture |
| REST API | FastAPI, Pydantic, swagger docs |
| Async/Concurrency | Async endpoints, background tasks |
| API Integration | REST, JSON, rate limiting |
| Web3 / Blockchain | RPC, smart contract ABI, on-chain reads |
| Multi-chain | 4 blockchain explorer APIs |
| DevOps | Docker, docker-compose, CI/CD |
| Testing | 23 pytest tests |
| CLI Design | argparse, REPL shell |
| Data Persistence | SQLite, CRUD operations |
| Real-time Monitoring | Scheduler, gas alerts |
| Bot Development | python-telegram-bot |
| Finance | Gas tracking, flash loan sims |
| Infrastructure | Multi-service docker-compose |
