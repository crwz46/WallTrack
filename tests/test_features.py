import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import tempfile
import sqlite3
from walltrack.gas import GasPrice, GasTracker
from walltrack.flashloan import FlashLoanSimulator
from walltrack.history import HistoryManager


class TestGasPrice:
    def test_low_traffic(self):
        gas = GasPrice(safe=5, standard=8, fast=12, timestamp="now")
        assert "Low traffic" in gas.recommendation()

    def test_high_traffic(self):
        gas = GasPrice(safe=80, standard=100, fast=150, timestamp="now")
        assert "Very high" in gas.recommendation()

    def test_estimate_cost(self):
        gas = GasPrice(safe=10, standard=20, fast=30, timestamp="now")
        costs = gas.estimate_cost(21000)
        assert costs["safe"] == 0.00021
        assert costs["standard"] == 0.00042
        assert costs["fast"] == 0.00063


class TestFlashLoanSimulator:
    def test_find_opportunities(self):
        sim = FlashLoanSimulator()
        opps = sim.find_arbitrage(min_profit_usd=0, loan_amount_eth=100)
        assert isinstance(opps, list)
        if opps:
            assert "profit_eth" in opps[0]
            assert "buy_from" in opps[0]
            assert "sell_to" in opps[0]

    def test_display_no_opps(self):
        sim = FlashLoanSimulator()
        opps = sim.find_arbitrage(min_profit_usd=1_000_000)
        FlashLoanSimulator.display(opps)


class TestHistory:
    def test_save_and_retrieve(self):
        db_path = os.path.join(
            tempfile.mkdtemp(), "test_walltrack.db"
        )
        hm = HistoryManager(db_path)
        data = {
            "address": "0xabc",
            "chain_id": "ethereum",
            "native_balance": 1.5,
            "transaction_count": 10,
            "top_tokens": [],
        }
        hm.save_snapshot(data)

        history = hm.get_history("0xabc")
        assert len(history) == 1
        assert history[0]["native_balance"] == 1.5

        balance_hist = hm.get_balance_history("0xabc")
        assert len(balance_hist) == 1
        assert balance_hist[0]["balance"] == 1.5
