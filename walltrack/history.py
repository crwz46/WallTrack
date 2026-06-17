import os
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional


DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "walltrack.db")


class HistoryManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    address TEXT NOT NULL,
                    chain TEXT NOT NULL DEFAULT 'ethereum',
                    native_balance REAL,
                    transaction_count INTEGER,
                    token_count INTEGER,
                    raw_data TEXT,
                    scanned_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_address_chain
                ON snapshots(address, chain)
            """)

    def save_snapshot(self, data: Dict):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO snapshots
                    (address, chain, native_balance, transaction_count,
                     token_count, raw_data, scanned_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["address"],
                    data.get("chain_id", "ethereum"),
                    data["native_balance"],
                    data["transaction_count"],
                    len(data.get("top_tokens", [])),
                    json.dumps(data, default=str),
                    datetime.now().isoformat(),
                ),
            )

    def get_history(
        self,
        address: str,
        chain: str = "ethereum",
        limit: int = 30,
    ) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT * FROM snapshots
                WHERE address = ? AND chain = ?
                ORDER BY scanned_at DESC
                LIMIT ?
                """,
                (address, chain, limit),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_balance_history(
        self, address: str, chain: str = "ethereum"
    ) -> List[Dict]:
        rows = self.get_history(address, chain, limit=100)
        return [
            {
                "balance": r["native_balance"],
                "tx_count": r["transaction_count"],
                "time": r["scanned_at"],
            }
            for r in reversed(rows)
        ]

    def display_history(self, address: str, chain: str = "ethereum"):
        history = self.get_balance_history(address, chain)
        if not history:
            print(f"\n  No history for {address} on {chain}")
            return

        print(f"\n  📊 Portfolio History: {address[:10]}...\n")
        print(f"  {'Scan Time':22s} {'Balance':>14s} {'Tx Count':>10s}")
        print(f"  {'─' * 22} {'─' * 14} {'─' * 10}")

        for entry in history[-10:]:
            print(
                f"  {entry['time'][:19]:22s} "
                f"{entry['balance']:>10.6f}  "
                f"{entry['tx_count']:>8,}"
            )

        if len(history) >= 2:
            first = history[0]
            last = history[-1]
            change = last["balance"] - first["balance"]
            pct = (change / first["balance"] * 100) if first["balance"] else 0
            arrow = "📈" if change >= 0 else "📉"
            print(f"\n  {arrow} Change: {change:+.6f} ({pct:+.2f}%)")
