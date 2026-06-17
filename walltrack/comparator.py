from typing import Dict, List
from datetime import datetime


class WalletComparator:
    @staticmethod
    def compare(wallets: List[Dict]) -> Dict:
        results = []
        for w in wallets:
            tokens = w.get("top_tokens", [])
            results.append(
                {
                    "address": w["address"],
                    "chain": w["chain"],
                    "balance": w["native_balance"],
                    "tx_count": w["transaction_count"],
                    "token_count": len(tokens),
                    "top_token_symbols": [
                        t["symbol"] for t in tokens[:3]
                    ],
                }
            )

        return {
            "compared_at": datetime.now().isoformat(),
            "wallet_count": len(results),
            "wallets": results,
        }

    @staticmethod
    def display(comparison: Dict):
        print("=" * 70)
        print("  🔄 WALLET COMPARISON")
        print("=" * 70)
        print(
            f"\n  {'#':3s} {'Address':22s} {'Chain':12s} "
            f"{'Balance':>10s} {'Tx':>8s} {'Tokens':>6s} {'Top 3':>20s}"
        )
        print(
            f"  {'─' * 3} {'─' * 22} {'─' * 12} "
            f"{'─' * 10} {'─' * 8} {'─' * 6} {'─' * 20}"
        )

        for i, w in enumerate(comparison["wallets"], 1):
            symbol = w["chain"][:3].upper()
            top = ", ".join(w["top_token_symbols"][:3])[:20]
            print(
                f"  {i:3d} {w['address'][:20]:22s} "
                f"{w['chain'][:10]:12s} "
                f"{w['balance']:>8.4f}  "
                f"{w['tx_count']:>6,}  "
                f"{w['token_count']:>4d}  "
                f"{top:>20s}"
            )

        print("=" * 70)


def cmd_compare(addresses: List[str], chain_mgr, tracker):
    results = []
    for addr in addresses:
        try:
            result = tracker.analyze(addr)
            results.append(result)
            print(f"  ✓ {addr[:10]}... scanned")
        except Exception as e:
            print(f"  ✗ {addr[:10]}... error: {e}")

    if results:
        comp = WalletComparator.compare(results)
        WalletComparator.display(comp)
    return results
