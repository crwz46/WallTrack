import time
import threading
from datetime import datetime
from typing import Callable, Dict, List, Optional

from .tracker import WalletTracker
from .history import HistoryManager
from .chains import ChainManager


class WatchJob:
    def __init__(
        self,
        address: str,
        chain: str = "ethereum",
        interval: int = 3600,
        callback: Optional[Callable] = None,
    ):
        self.address = address
        self.chain = chain
        self.interval = interval
        self.callback = callback
        self.last_balance = None
        self.last_tx_count = None
        self.running = False

    def tick(self, tracker: WalletTracker) -> Optional[Dict]:
        try:
            data = tracker.analyze(self.address, self.chain)
            changed = False

            if self.last_balance is not None:
                diff = data["native_balance"] - self.last_balance
                if abs(diff) > 0.001:
                    changed = True
                    if self.callback:
                        self.callback(
                            self.address,
                            "balance_changed",
                            {
                                "old": self.last_balance,
                                "new": data["native_balance"],
                                "diff": diff,
                            },
                        )

            if self.last_tx_count is not None:
                if data["transaction_count"] > self.last_tx_count:
                    changed = True
                    new_txs = (
                        data["transaction_count"] - self.last_tx_count
                    )
                    if self.callback:
                        self.callback(
                            self.address,
                            "new_transactions",
                            {"count": new_txs},
                        )

            self.last_balance = data["native_balance"]
            self.last_tx_count = data["transaction_count"]

            return data if changed else None
        except Exception:
            return None


class Scheduler:
    def __init__(self, api_keys: Dict[str, str]):
        self.jobs: List[WatchJob] = []
        self.thread: Optional[threading.Thread] = None
        self.running = False
        self.chain_mgr = ChainManager(api_keys)
        self.tracker = WalletTracker(self.chain_mgr)
        self.history = HistoryManager()

    def add_job(
        self,
        address: str,
        chain: str = "ethereum",
        interval: int = 3600,
        callback: Optional[Callable] = None,
    ):
        job = WatchJob(address, chain, interval, callback)
        self.jobs.append(job)
        print(
            f"  Added watch: {address[:10]}... "
            f"every {interval}s on {chain}"
        )

    def remove_job(self, address: str):
        self.jobs = [j for j in self.jobs if j.address != address]

    def list_jobs(self) -> List[Dict]:
        return [
            {
                "address": j.address,
                "chain": j.chain,
                "interval": j.interval,
                "running": j.running,
            }
            for j in self.jobs
        ]

    def _loop(self):
        while self.running:
            for job in self.jobs:
                job.running = True
                result = job.tick(self.tracker)
                if result:
                    self.history.save_snapshot(result)
                job.running = False
            time.sleep(60)

    def start(self):
        if self.running:
            print("Scheduler already running")
            return
        if not self.jobs:
            print("No jobs to run. Add wallets first.")
            return

        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        print(
            f"Scheduler started with {len(self.jobs)} job(s), "
            f"checking every 60s"
        )

    def stop(self):
        self.running = False
        print("Scheduler stopped")
