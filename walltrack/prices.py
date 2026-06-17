import requests
from dataclasses import dataclass
from typing import Dict, List, Optional


COINGECKO_API = "https://api.coingecko.com/api/v3"


@dataclass
class TokenPrice:
    symbol: str
    name: str
    usd: float
    btc: float
    change_24h: Optional[float]


class PriceFeed:
    def __init__(self):
        self._cache: Dict[str, TokenPrice] = {}

    def get_price(self, coin_id: str) -> Optional[TokenPrice]:
        if coin_id in self._cache:
            return self._cache[coin_id]

        try:
            resp = requests.get(
                f"{COINGECKO_API}/simple/price",
                params={
                    "ids": coin_id,
                    "vs_currencies": "usd,btc",
                    "include_24hr_change": "true",
                },
                timeout=10,
            )
            data = resp.json()
            if coin_id not in data:
                return None

            price = TokenPrice(
                symbol=coin_id,
                name=coin_id,
                usd=data[coin_id].get("usd", 0),
                btc=data[coin_id].get("btc", 0),
                change_24h=data[coin_id].get("usd_24h_change"),
            )
            self._cache[coin_id] = price
            return price
        except Exception:
            return None

    def get_prices(self, coin_ids: List[str]) -> Dict[str, TokenPrice]:
        result = {}
        for cid in coin_ids:
            price = self.get_price(cid)
            if price:
                result[cid] = price
        return result

    def search_coin(self, query: str) -> List[Dict]:
        try:
            resp = requests.get(
                f"{COINGECKO_API}/search",
                params={"query": query},
                timeout=10,
            )
            data = resp.json()
            return data.get("coins", [])[:5]
        except Exception:
            return []

    def get_portfolio_value(
        self, balances: Dict[str, float]
    ) -> Dict:
        total_usd = 0.0
        details = []

        for coin_id, amount in balances.items():
            price = self.get_price(coin_id)
            if price and price.usd:
                usd_value = amount * price.usd
                total_usd += usd_value
                details.append(
                    {
                        "coin": coin_id,
                        "amount": amount,
                        "price_usd": price.usd,
                        "value_usd": round(usd_value, 2),
                        "change_24h": price.change_24h,
                    }
                )

        return {
            "total_usd": round(total_usd, 2),
            "assets": details,
        }

    @staticmethod
    def display_portfolio(portfolio: Dict):
        print("=" * 60)
        print("  💰 PORTFOLIO VALUATION (USD)")
        print("=" * 60)

        if not portfolio["assets"]:
            print("\n  No price data available.")
            print("=" * 60)
            return

        print(
            f"\n  {'Coin':12s} {'Amount':>12s} {'Price USD':>10s} "
            f"{'Value USD':>12s} {'24h':>8s}"
        )
        print(f"  {'─' * 12} {'─' * 12} {'─' * 10} {'─' * 12} {'─' * 8}")

        for asset in portfolio["assets"]:
            change = asset.get("change_24h")
            change_str = (
                f"{change:+.2f}%"
                if change is not None
                else "N/A"
            )
            print(
                f"  {asset['coin']:12s} "
                f"{asset['amount']:>10.4f}  "
                f"${asset['price_usd']:>8.2f} "
                f"${asset['value_usd']:>8.2f}  "
                f"{change_str:>8s}"
            )

        print(f"\n  {'TOTAL':12s} {'':>12s} {'':>10s} "
              f"${portfolio['total_usd']:>8.2f}")
        print("=" * 60)
