import requests
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional


@dataclass
class GasPrice:
    safe: float
    standard: float
    fast: float
    timestamp: str

    def recommendation(self) -> str:
        if self.safe < 10:
            return "🟢 Low traffic — good time to transact"
        elif self.safe < 30:
            return "🟡 Moderate traffic"
        elif self.safe < 60:
            return "🟠 High traffic — fees are elevated"
        else:
            return "🔴 Very high traffic — wait if possible"

    def estimate_cost(self, gas_limit: int = 21000) -> Dict:
        return {
            "safe": round(self.safe * gas_limit * 1e-9, 6),
            "standard": round(self.standard * gas_limit * 1e-9, 6),
            "fast": round(self.fast * gas_limit * 1e-9, 6),
        }


class GasTracker:
    GAS_API_URL = "https://api.etherscan.io/api"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_gas_prices(self) -> GasPrice:
        params = {
            "module": "gastracker",
            "action": "gasoracle",
            "apikey": self.api_key,
        }
        resp = requests.get(self.GAS_API_URL, params=params, timeout=10)
        data = resp.json()

        if data.get("status") != "1":
            raise ValueError(f"Gas API Error: {data.get('message', 'Unknown')}")

        result = data["result"]
        return GasPrice(
            safe=int(result["SafeGasPrice"]),
            standard=int(result["ProposeGasPrice"]),
            fast=int(result["FastGasPrice"]),
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

    @staticmethod
    def display(gas: GasPrice):
        costs = gas.estimate_cost()
        print("=" * 50)
        print("  ⛽ GAS TRACKER")
        print("=" * 50)
        print(f"  Time    : {gas.timestamp}")
        print(f"  Status  : {gas.recommendation()}")
        print()
        print(f"  {'Level':12s} {'Price':>8s} {'ETH Transfer':>14s}")
        print(f"  {'─' * 12} {'─' * 8} {'─' * 14}")
        print(f"  {'Safe':12s} {gas.safe:>4d} gwei   {costs['safe']:>8.6f} ETH")
        print(f"  {'Standard':12s} {gas.standard:>4d} gwei   {costs['standard']:>8.6f} ETH")
        print(f"  {'Fast':12s} {gas.fast:>4d} gwei   {costs['fast']:>8.6f} ETH")
        print("=" * 50)
