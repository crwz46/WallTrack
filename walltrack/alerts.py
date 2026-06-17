import time
from typing import Optional, Callable

from .gas import GasTracker


class GasAlert:
    def __init__(
        self,
        api_key: str,
        threshold_gwei: int = 20,
        callback: Optional[Callable] = None,
        cooldown: int = 300,
    ):
        self.tracker = GasTracker(api_key)
        self.threshold = threshold_gwei
        self.callback = callback
        self.last_notified = 0
        self.cooldown = cooldown

    def check(self) -> Optional[dict]:
        try:
            gas = self.tracker.get_gas_prices()

            if gas.safe <= self.threshold:
                now = time.time()
                if now - self.last_notified > self.cooldown:
                    self.last_notified = now
                    alert = {
                        "type": "gas_low",
                        "message": (
                            f"Gas is LOW! Safe: {gas.safe} gwei "
                            f"(threshold: {self.threshold} gwei)"
                        ),
                        "safe_gwei": gas.safe,
                        "standard_gwei": gas.standard,
                        "fast_gwei": gas.fast,
                        "timestamp": gas.timestamp,
                    }
                    if self.callback:
                        self.callback(alert)
                    return alert
            return None
        except Exception as e:
            return {"type": "error", "message": str(e)}

    @staticmethod
    def display_alert(alert: dict):
        if alert["type"] == "gas_low":
            print("\n" + "!" * 50)
            print(f"  ⛽ GAS ALERT: {alert['message']}")
            print(f"  Safe: {alert['safe_gwei']} gwei | "
                  f"Standard: {alert['standard_gwei']} gwei | "
                  f"Fast: {alert['fast_gwei']} gwei")
            print(f"  Time: {alert['timestamp']}")
            print("!" * 50)
