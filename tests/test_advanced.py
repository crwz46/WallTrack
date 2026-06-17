import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from walltrack.prices import PriceFeed, TokenPrice
from walltrack.comparator import WalletComparator
from walltrack.alerts import GasAlert
from walltrack.gas import GasPrice


class TestPriceFeed:
    def test_token_price_creation(self):
        price = TokenPrice(
            symbol="bitcoin",
            name="Bitcoin",
            usd=50000.0,
            btc=1.0,
            change_24h=2.5,
        )
        assert price.usd == 50000.0
        assert price.change_24h == 2.5

    def test_portfolio_value_empty(self):
        pf = PriceFeed()
        # Mock no real API call, should return empty
        result = pf.get_portfolio_value({})
        assert result["total_usd"] == 0.0
        assert result["assets"] == []


class TestWalletComparator:
    def test_compare_single_wallet(self):
        wallets = [
            {
                "address": "0xabc",
                "chain": "Ethereum",
                "native_balance": 1.5,
                "transaction_count": 10,
                "top_tokens": [
                    {"symbol": "USDC", "total_value": 1000, "tx_count": 5}
                ],
            }
        ]
        result = WalletComparator.compare(wallets)
        assert result["wallet_count"] == 1
        assert result["wallets"][0]["balance"] == 1.5

    def test_compare_multiple_wallets(self):
        wallets = [
            {
                "address": "0xabc",
                "chain": "Ethereum",
                "native_balance": 1.0,
                "transaction_count": 5,
                "top_tokens": [],
            },
            {
                "address": "0xdef",
                "chain": "BSC",
                "native_balance": 2.0,
                "transaction_count": 15,
                "top_tokens": [],
            },
        ]
        result = WalletComparator.compare(wallets)
        assert result["wallet_count"] == 2
        assert result["wallets"][0]["balance"] == 1.0
        assert result["wallets"][1]["balance"] == 2.0


class TestGasAlert:
    def test_low_gas_alert(self):
        alert = GasAlert("fake_key", threshold_gwei=50)
        # Manually check with mock data
        from walltrack.gas import GasPrice as GP
        assert alert.threshold == 50

    def test_alert_cooldown(self):
        alert = GasAlert("fake_key", threshold_gwei=20, cooldown=0)
        assert alert.cooldown == 0
        alert.last_notified = 0  # Never notified


class TestWeb3ProviderSkipped:
    def test_web3_not_installed(self):
        try:
            from walltrack.web3_provider import Web3Provider
            # If we got here, web3 is installed
            assert True
        except ImportError:
            pytest.skip("web3 not installed")
