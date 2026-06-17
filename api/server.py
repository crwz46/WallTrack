import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

from walltrack.chains import ChainManager, DEFAULT_CHAIN
from walltrack.tracker import WalletTracker
from walltrack.gas import GasTracker
from walltrack.flashloan import FlashLoanSimulator
from walltrack.history import HistoryManager
from walltrack.prices import PriceFeed
from walltrack.charts import ChartGenerator
from walltrack.web3_provider import Web3Provider

app = FastAPI(
    title="WallTrack API",
    description="Multi-Chain Crypto Wallet Tracker API",
    version="2.0.0",
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


class TrackResponse(BaseModel):
    address: str
    chain: str
    native_balance: float
    transaction_count: int
    top_tokens: list


class CompareRequest(BaseModel):
    addresses: List[str]
    chain: str = DEFAULT_CHAIN


@app.get("/")
async def root():
    return {
        "name": "WallTrack API",
        "version": "2.0.0",
        "endpoints": {
            "GET /track/{address}": "Track wallet",
            "GET /gas": "Gas prices",
            "GET /price/{coin}": "Crypto price",
            "GET /portfolio/{address}": "Portfolio USD value",
            "POST /compare": "Compare wallets",
            "GET /web3/{address}": "On-chain data",
            "GET /flash": "Flash loan sim",
            "GET /history/{address}": "Portfolio history",
            "GET /report/{address}": "HTML report",
        },
    }


@app.get("/track/{address}", response_model=TrackResponse)
async def track(
    address: str,
    chain: str = Query(DEFAULT_CHAIN, description="Blockchain"),
):
    if not address.startswith("0x") or len(address) != 42:
        raise HTTPException(400, "Invalid address")

    cm = ChainManager(api_keys)
    tr = WalletTracker(cm)
    try:
        result = tr.analyze(address, chain)
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/gas")
async def gas():
    key = api_keys.get("ETHERSCAN_API_KEY")
    if not key:
        raise HTTPException(400, "ETHERSCAN_API_KEY not set")
    gt = GasTracker(key)
    prices = gt.get_gas_prices()
    costs = prices.estimate_cost()
    return {
        "safe": {"gwei": prices.safe, "eth": costs["safe"]},
        "standard": {"gwei": prices.standard, "eth": costs["standard"]},
        "fast": {"gwei": prices.fast, "eth": costs["fast"]},
        "recommendation": prices.recommendation(),
    }


@app.get("/price/{coin}")
async def price(coin: str):
    pf = PriceFeed()
    p = pf.get_price(coin)
    if not p:
        raise HTTPException(404, f"Coin '{coin}' not found")
    return {
        "coin": coin,
        "usd": p.usd,
        "btc": p.btc,
        "change_24h": p.change_24h,
    }


@app.get("/portfolio/{address}")
async def portfolio(
    address: str,
    chain: str = Query(DEFAULT_CHAIN),
):
    if not address.startswith("0x"):
        raise HTTPException(400, "Invalid address")

    cm = ChainManager(api_keys)
    tr = WalletTracker(cm)
    pf = PriceFeed()

    try:
        result = tr.analyze(address, chain)
    except ValueError as e:
        raise HTTPException(400, str(e))

    balances = {"ethereum": result["native_balance"]}
    for t in result.get("top_tokens", []):
        balances[t["symbol"].lower()] = t["total_value"]

    pv = pf.get_portfolio_value(balances)
    return {
        "address": address,
        "chain": chain,
        "native_balance": result["native_balance"],
        "portfolio": pv,
    }


@app.post("/compare")
async def compare(req: CompareRequest):
    if len(req.addresses) < 2:
        raise HTTPException(400, "Need at least 2 addresses")

    from walltrack.comparator import WalletComparator

    cm = ChainManager(api_keys)
    tr = WalletTracker(cm)
    results = []

    for addr in req.addresses:
        try:
            r = tr.analyze(addr, req.chain)
            results.append(r)
        except ValueError as e:
            results.append({"address": addr, "error": str(e)})

    comp = WalletComparator.compare(results)
    return comp


@app.get("/web3/{address}")
async def web3(address: str, chain: str = Query(DEFAULT_CHAIN)):
    try:
        w3 = Web3Provider(chain)
    except (ImportError, ValueError) as e:
        raise HTTPException(400, str(e))

    if not w3.is_connected():
        raise HTTPException(503, f"Cannot connect to {chain} RPC")

    data = w3.analyze_onchain(address)
    return data


@app.get("/flash")
async def flash(
    loan: float = Query(100.0),
    min_profit: float = Query(10.0),
):
    sim = FlashLoanSimulator()
    opps = sim.find_arbitrage(min_profit, loan)
    return {"opportunities": opps, "count": len(opps)}


@app.get("/history/{address}")
async def history(
    address: str,
    chain: str = Query(DEFAULT_CHAIN),
    limit: int = Query(30),
):
    hm = HistoryManager()
    rows = hm.get_balance_history(address, chain)
    return {
        "address": address,
        "chain": chain,
        "history": rows[-limit:],
    }


@app.get("/report/{address}", response_class=HTMLResponse)
async def report(address: str, chain: str = Query(DEFAULT_CHAIN)):
    cm = ChainManager(api_keys)
    tr = WalletTracker(cm)
    try:
        result = tr.analyze(address, chain)
    except ValueError as e:
        raise HTTPException(400, str(e))

    html = ChartGenerator.to_html(result)
    return HTMLResponse(content=html)


def run():
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("api.server:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    run()
