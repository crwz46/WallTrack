import random
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class Pool:
    dex: str
    token_a: str
    token_b: str
    price: float
    liquidity: float


class FlashLoanSimulator:
    def __init__(self):
        self.pools = self._generate_mock_pools()

    def _generate_mock_pools(self) -> List[Pool]:
        base_pools = [
            Pool("Uniswap V3", "ETH", "USDC", 3450.0, 50_000_000),
            Pool("Uniswap V3", "ETH", "USDC", 3452.0, 80_000_000),
            Pool("SushiSwap", "ETH", "USDC", 3448.0, 30_000_000),
            Pool("Curve", "ETH", "USDC", 3451.0, 100_000_000),
            Pool("Balancer", "ETH", "USDC", 3449.5, 40_000_000),
        ]

        for i in range(len(base_pools)):
            base_pools[i].price *= 1 + random.uniform(-0.003, 0.003)

        return base_pools

    def find_arbitrage(
        self, min_profit_usd: float = 10.0, loan_amount_eth: float = 100.0
    ) -> List[Dict]:
        opportunities = []

        for i in range(len(self.pools)):
            for j in range(len(self.pools)):
                if i >= j:
                    continue

                buy_pool = self.pools[i]
                sell_pool = self.pools[j]

                usdc_received = loan_amount_eth * buy_pool.price
                usdc_fee = usdc_received * 0.003
                usdc_net = usdc_received - usdc_fee

                eth_received = usdc_net / sell_pool.price
                eth_fee = eth_received * 0.003
                eth_net = eth_received - eth_fee

                profit_eth = eth_net - loan_amount_eth
                profit_usd = profit_eth * ((buy_pool.price + sell_pool.price) / 2)

                if profit_usd > min_profit_usd:
                    opportunities.append(
                        {
                            "buy_from": buy_pool.dex,
                            "buy_price": round(buy_pool.price, 2),
                            "sell_to": sell_pool.dex,
                            "sell_price": round(sell_pool.price, 2),
                            "spread_pct": round(
                                (sell_pool.price / buy_pool.price - 1) * 100, 4
                            ),
                            "loan_amount_eth": loan_amount_eth,
                            "profit_eth": round(profit_eth, 6),
                            "profit_usd": round(profit_usd, 2),
                            "feasible": profit_usd > 50,
                        }
                    )

        return sorted(
            opportunities, key=lambda x: x["profit_usd"], reverse=True
        )

    @staticmethod
    def display(opportunities: List[Dict]):
        print("=" * 70)
        print("  💰 FLASH LOAN ARBITRAGE SIMULATOR")
        print("=" * 70)

        if not opportunities:
            print("\n  No arbitrage opportunities found right now.")
            print("  Tip: Try a larger loan amount or lower min profit.")
            print("=" * 70)
            return

        print(f"\n  Found {len(opportunities)} opportunity(ies):\n")
        print(
            f"  {'#':3s} {'Buy':14s} {'Sell':14s} {'Spread':>8s} "
            f"{'Loan':>8s} {'Profit ETH':>12s} {'Profit USD':>12s} {'OK?':>4s}"
        )
        print(f"  {'─' * 3} {'─' * 14} {'─' * 14} {'─' * 8} "
              f"{'─' * 8} {'─' * 12} {'─' * 12} {'─' * 4}")

        for i, opp in enumerate(opportunities[:10], 1):
            ok = "✅" if opp["feasible"] else "❌"
            print(
                f"  {i:3d} {opp['buy_from']:14s} {opp['sell_to']:14s} "
                f"{opp['spread_pct']:>7.3f}% "
                f"{opp['loan_amount_eth']:>6.0f} "
                f"{opp['profit_eth']:>10.6f}  "
                f"${opp['profit_usd']:>8.2f}  {ok}"
            )

        print("=" * 70)
        print("  * Simulated market data — not real prices")
