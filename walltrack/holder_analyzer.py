import requests
import random
import statistics
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


TOKEN_MAP = {
    "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "LINK": "0x514910771AF9Ca656af840dff83E8264EcF986CA",
    "UNI": "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
    "AAVE": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9",
    "MATIC": "0x7D1AfA7B718fb893dB30A3aBc0Cfc608AaCfeBB0",
    "SHIB": "0x95aD61b0a150d79219dCF64E1E6Cc01f0B64C4cE",
    "PEPE": "0x6982508145454Ce325dDbE47a25d4ec3d2311933",
}


@dataclass
class Holder:
    address: str
    balance: float
    percentage: float
    label: str = ""


@dataclass
class TokenInfo:
    symbol: str
    name: str
    decimals: int
    total_supply: float


class ConcentrationMetrics:
    """Calculate concentration, HHI, Gini coefficient for token holders."""

    @staticmethod
    def top_n_concentration(holders: List[Holder], n: int = 10) -> float:
        top = sorted(holders, key=lambda h: h.percentage, reverse=True)[:n]
        return sum(h.percentage for h in top)

    @staticmethod
    def herfindahl_index(holders: List[Holder]) -> float:
        shares = [h.percentage / 100 for h in holders]
        return sum(s * s for s in shares)

    @staticmethod
    def gini_coefficient(holders: List[Holder]) -> float:
        values = sorted([h.balance for h in holders])
        n = len(values)
        if n == 0 or sum(values) == 0:
            return 0.0
        cum_sum = 0
        for i, v in enumerate(values, 1):
            cum_sum += i * v
        return (2 * cum_sum) / (n * sum(values)) - (n + 1) / n

    @staticmethod
    def risk_level(
        top10_pct: float, hhi: float, gini: float
    ) -> Tuple[str, str]:
        score = 0
        if top10_pct > 80:
            score += 3
        elif top10_pct > 60:
            score += 2
        elif top10_pct > 40:
            score += 1

        if hhi > 0.2:
            score += 3
        elif hhi > 0.1:
            score += 2
        elif hhi > 0.05:
            score += 1

        if gini > 0.9:
            score += 3
        elif gini > 0.8:
            score += 2
        elif gini > 0.7:
            score += 1

        if score >= 7:
            return "HIGH CONCENTRATION", "🔴"
        elif score >= 4:
            return "MODERATE CONCENTRATION", "🟡"
        else:
            return "LOW CONCENTRATION", "🟢"


class HolderDataFetcher:
    """Fetch token holder data from multiple sources."""

    @staticmethod
    def from_sample(token_symbol: str) -> Tuple[TokenInfo, List[Holder]]:
        """Generate synthetic but realistic holder data."""
        # Simulate realistic holder distributions
        random.seed(hash(token_symbol))

        total_supply_map = {
            "USDC": 30_000_000_000,
            "USDT": 80_000_000_000,
            "LINK": 600_000_000,
            "UNI": 1_000_000_000,
            "AAVE": 16_000_000,
            "MATIC": 10_000_000_000,
            "SHIB": 589_000_000_000_000,
            "PEPE": 420_000_000_000_000,
        }

        decimals_map = {
            "USDC": 6, "USDT": 6, "LINK": 18, "UNI": 18,
            "AAVE": 18, "MATIC": 18, "SHIB": 18, "PEPE": 18,
        }

        name_map = {
            "USDC": "USD Coin", "USDT": "Tether", "LINK": "Chainlink",
            "UNI": "Uniswap", "AAVE": "Aave", "MATIC": "Polygon",
            "SHIB": "Shiba Inu", "PEPE": "Pepe",
        }

        total_supply = total_supply_map.get(
            token_symbol.upper(), 1_000_000_000
        )
        decimals = decimals_map.get(token_symbol.upper(), 18)
        name = name_map.get(token_symbol.upper(), token_symbol.upper())

        ti = TokenInfo(
            symbol=token_symbol.upper(),
            name=name,
            decimals=decimals,
            total_supply=total_supply,
        )

        holders = []
        # Generate top 5 large holders (whales)
        whale_shares = [
            random.uniform(8, 25) for _ in range(5)
        ]
        whale_sum = sum(whale_shares)
        # Scale so top 5 = 40-65% of total
        scale = random.uniform(40, 65) / whale_sum
        whale_shares = [s * scale for s in whale_shares]

        for i, share in enumerate(whale_shares):
            addr = f"0x{random.randint(10**39, 10**40 - 1):040x}"
            holders.append(Holder(
                address=addr,
                balance=total_supply * share / 100,
                percentage=share,
                label="Whale" if i < 3 else "",
            ))

        # Generate mid-size holders (6-20)
        remaining = 100 - sum(whale_shares)
        mid_count = random.randint(10, 15)
        for _ in range(mid_count):
            share = random.uniform(0.5, min(5, remaining))
            remaining -= share
            addr = f"0x{random.randint(10**39, 10**40 - 1):040x}"
            holders.append(Holder(
                address=addr,
                balance=total_supply * share / 100,
                percentage=share,
            ))

        # Fill rest with small holders
        small_shares = []
        while remaining > 0 and len(holders) < 100:
            share = random.uniform(0.01, min(1, remaining))
            small_shares.append(share)
            remaining -= share
            if remaining < 0.01:
                break

        # Distribute remaining to first small holder
        if remaining > 0 and small_shares:
            small_shares[0] += remaining

        for share in small_shares:
            addr = f"0x{random.randint(10**39, 10**40 - 1):040x}"
            holders.append(Holder(
                address=addr,
                balance=total_supply * share / 100,
                percentage=share,
            ))

        # Sort by balance descending
        holders.sort(key=lambda h: h.balance, reverse=True)

        # Label top 3
        for i in range(min(3, len(holders))):
            holders[i].label = ["🐋 Whale", "🐳 Mega Whale", "🦈 Shark"][i]

        return ti, holders[:100]

    @staticmethod
    def from_covalent(
        contract: str,
        chain_id: int = 1,
        api_key: str = "",
    ) -> Tuple[Optional[TokenInfo], List[Holder]]:
        """Fetch real holder data from Covalent API."""
        if not api_key:
            return None, []

        url = (
            f"https://api.covalenthq.com/v1/{chain_id}"
            f"/tokens/{contract}/token_holders/"
        )
        try:
            resp = requests.get(
                url,
                params={"key": api_key, "page-size": 100},
                timeout=15,
            )
            data = resp.json()
            if not data.get("data"):
                return None, []

            items = data["data"]["items"]
            token_info = data["data"].get("pagination", {})
            ti = TokenInfo(
                symbol=items[0]["contract_ticker_symbol"],
                name=items[0]["contract_name"],
                decimals=items[0]["contract_decimals"],
                total_supply=sum(
                    int(i["balance"]) / (10 ** items[0]["contract_decimals"])
                    for i in items
                ),
            )

            holders = []
            for item in items:
                balance = int(item["balance"]) / (
                    10 ** items[0]["contract_decimals"]
                )
                pct = (balance / ti.total_supply * 100) if ti.total_supply else 0
                holders.append(Holder(
                    address=item["address"],
                    balance=balance,
                    percentage=pct,
                ))

            holders.sort(key=lambda h: h.balance, reverse=True)
            return ti, holders[:100]
        except Exception:
            return None, []

    @staticmethod
    def from_etherscan(
        contract: str,
        api_key: str = "",
    ) -> Tuple[Optional[TokenInfo], List[Holder]]:
        """Fetch holder data from Etherscan tokentx (free tier)."""
        if not api_key:
            return None, []

        url = "https://api.etherscan.io/api"
        try:
            # Get token transfer events
            resp = requests.get(
                url,
                params={
                    "module": "account",
                    "action": "tokentx",
                    "contractaddress": contract,
                    "page": 1,
                    "offset": 1000,
                    "sort": "desc",
                    "apikey": api_key,
                },
                timeout=15,
            )
            data = resp.json()
            if data.get("status") != "1":
                return None, []

            txs = data["result"]
            if not txs:
                return None, []

            decimals = int(txs[0].get("tokenDecimal", 18))
            symbol = txs[0].get("tokenSymbol", "?")

            # Aggregate balances from transfer events
            balances: Dict[str, float] = {}
            for tx in txs:
                for addr in [tx["from"], tx["to"]]:
                    if addr not in balances:
                        balances[addr] = 0.0
                val = int(tx["value"]) / (10 ** decimals)
                balances[tx["from"]] = balances.get(tx["from"], 0) - val
                balances[tx["to"]] = balances.get(tx["to"], 0) + val

            total_positive = sum(
                v for v in balances.values() if v > 0
            )
            if total_positive == 0:
                return None, []

            ti = TokenInfo(
                symbol=symbol, name=symbol, decimals=decimals,
                total_supply=total_positive,
            )

            holders = sorted(
                [
                    Holder(
                        address=addr,
                        balance=max(0, bal),
                        percentage=max(0, bal) / total_positive * 100,
                    )
                    for addr, bal in balances.items()
                    if bal > 0
                ],
                key=lambda h: h.percentage,
                reverse=True,
            )[:100]

            return ti, holders
        except Exception:
            return None, []


class HolderAnalyzer:
    def __init__(self):
        self.token: Optional[TokenInfo] = None
        self.holders: List[Holder] = []
        self.metrics: Dict = {}

    def analyze(
        self,
        token_symbol: str = "",
        contract: str = "",
        covalent_key: str = "",
        etherscan_key: str = "",
    ) -> Dict:
        # Try real data first
        if covalent_key and contract:
            self.token, self.holders = HolderDataFetcher.from_covalent(
                contract, api_key=covalent_key
            )
        if not self.holders and etherscan_key and contract:
            self.token, self.holders = HolderDataFetcher.from_etherscan(
                contract, api_key=etherscan_key
            )
        if not self.holders:
            symbol = token_symbol or "UNI"
            print(f"  Using sample data for {symbol}...")
            self.token, self.holders = HolderDataFetcher.from_sample(symbol)

        self._calculate_metrics()
        return self._build_report()

    def _calculate_metrics(self):
        h = self.holders
        top10_pct = ConcentrationMetrics.top_n_concentration(h, 10)
        top5_pct = ConcentrationMetrics.top_n_concentration(h, 5)
        top1_pct = h[0].percentage if h else 0
        hhi = ConcentrationMetrics.herfindahl_index(h)
        gini = ConcentrationMetrics.gini_coefficient(h)
        risk, icon = ConcentrationMetrics.risk_level(top10_pct, hhi, gini)

        # Effective number of holders (1/HHI)
        eff_n = round(1 / hhi, 1) if hhi > 0 else len(h)

        self.metrics = {
            "total_holders": len(h),
            "top1_pct": round(top1_pct, 2),
            "top5_pct": round(top5_pct, 2),
            "top10_pct": round(top10_pct, 2),
            "hhi": round(hhi, 4),
            "gini": round(gini, 4),
            "effective_holders": eff_n,
            "risk_label": risk,
            "risk_icon": icon,
        }

    def _build_report(self) -> Dict:
        top10 = [
            {
                "rank": i + 1,
                "address": h.address,
                "balance": h.balance,
                "percentage": round(h.percentage, 2),
                "label": h.label,
            }
            for i, h in enumerate(self.holders[:10])
        ]

        return {
            "token": {
                "symbol": self.token.symbol if self.token else "?",
                "name": self.token.name if self.token else "?",
                "total_supply": int(self.token.total_supply) if self.token else 0,
            },
            "metrics": self.metrics,
            "top_holders": top10,
            "holders": [
                {
                    "rank": i + 1,
                    "address": h.address,
                    "balance": h.balance,
                    "percentage": round(h.percentage, 2),
                    "label": h.label,
                }
                for i, h in enumerate(self.holders)
            ],
        }

    @staticmethod
    def display(report: Dict):
        t = report["token"]
        m = report["metrics"]

        print("=" * 70)
        print(f"  {m['risk_icon']} TOKEN HOLDER ANALYZER — {t['symbol']}")
        print("=" * 70)
        print(f"\n  Token       : {t['name']} ({t['symbol']})")
        print(f"  Total Supply: {t['total_supply']:,}")
        print(f"  Holders     : {m['total_holders']:,}")

        print(f"\n  {'─' * 40}")
        print(f"  CONCENTRATION ANALYSIS")
        print(f"  {'─' * 40}")
        print(f"  Top 1 Holder : {m['top1_pct']:>6.2f}%")
        print(f"  Top 5 Holders: {m['top5_pct']:>6.2f}%")
        print(f"  Top 10 Holders: {m['top10_pct']:>5.2f}%")
        print(f"  HHI Index    : {m['hhi']:>8.4f}")
        print(f"  Gini Coeff   : {m['gini']:>8.4f}")
        print(f"  Effective N  : {m['effective_holders']:>8.1f}")
        print(f"  {'─' * 40}")

        risk_icon = m['risk_icon']
        risk_label = m['risk_label']
        print(f"\n  Risk Level   : {risk_icon} {risk_label}")

        print(f"\n  TOP 10 HOLDERS:")
        print(f"  {'Rank':5s} {'Address':44s} {'%':>8s} {'Label':>12s}")
        print(f"  {'─' * 5} {'─' * 44} {'─' * 8} {'─' * 12}")

        for h in report["top_holders"]:
            addr_short = f"{h['address'][:6]}...{h['address'][-4:]}"
            print(
                f"  {h['rank']:4d}. {addr_short:42s} "
                f"{h['percentage']:>6.2f}%  {h['label']:>12s}"
            )

        print("=" * 70)

        if m["risk_label"] == "HIGH CONCENTRATION":
            print(
                "  ⚠️  High concentration risk. "
                "Price can be heavily influenced by top holders."
            )
        elif m["risk_label"] == "MODERATE CONCENTRATION":
            print(
                "  📊 Moderate concentration. "
                "Some whale influence but relatively distributed."
            )
        else:
            print(
                "  ✅ Well distributed token. "
                "Low centralization risk."
            )
        print("=" * 70)
