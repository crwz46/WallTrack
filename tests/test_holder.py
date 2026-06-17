import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from walltrack.holder_analyzer import (
    HolderAnalyzer,
    HolderDataFetcher,
    ConcentrationMetrics,
    Holder,
    TokenInfo,
)


class TestConcentrationMetrics:
    def test_top_n_concentration(self):
        holders = [
            Holder("0xA", 100, 50),
            Holder("0xB", 50, 25),
            Holder("0xC", 30, 15),
            Holder("0xD", 20, 10),
        ]
        top2 = ConcentrationMetrics.top_n_concentration(holders, 2)
        assert top2 == 75.0

    def test_herfindahl_index(self):
        holders = [
            Holder("0xA", 60, 60),
            Holder("0xB", 40, 40),
        ]
        hhi = ConcentrationMetrics.herfindahl_index(holders)
        assert hhi == pytest.approx(0.52, rel=0.01)

    def test_gini_coefficient(self):
        holders = [
            Holder("0xA", 100, 50),
            Holder("0xB", 100, 50),
        ]
        gini = ConcentrationMetrics.gini_coefficient(holders)
        assert gini == pytest.approx(0.0, abs=0.01)

    def test_risk_level_high(self):
        risk, icon = ConcentrationMetrics.risk_level(85, 0.3, 0.95)
        assert "HIGH" in risk

    def test_risk_level_low(self):
        risk, icon = ConcentrationMetrics.risk_level(20, 0.02, 0.3)
        assert "LOW" in risk


class TestHolderDataFetcher:
    def test_from_sample(self):
        ti, holders = HolderDataFetcher.from_sample("USDC")
        assert ti.symbol == "USDC"
        assert len(holders) <= 100
        assert all(h.percentage > 0 for h in holders)
        # All percentages should sum to ~100
        total = sum(h.percentage for h in holders)
        assert total == pytest.approx(100, abs=5)

    def test_sample_deterministic(self):
        ti1, h1 = HolderDataFetcher.from_sample("LINK")
        ti2, h2 = HolderDataFetcher.from_sample("LINK")
        assert ti1.symbol == ti2.symbol
        # Same seed should give same results
        assert h1[0].percentage == h2[0].percentage


class TestHolderAnalyzer:
    def test_analyze_sample(self):
        analyzer = HolderAnalyzer()
        report = analyzer.analyze(token_symbol="UNI")
        assert report["token"]["symbol"] == "UNI"
        assert "metrics" in report
        assert "top_holders" in report
        assert len(report["top_holders"]) == 10
        assert report["metrics"]["total_holders"] <= 100

    def test_metrics_in_report(self):
        analyzer = HolderAnalyzer()
        report = analyzer.analyze(token_symbol="PEPE")
        m = report["metrics"]
        assert "top10_pct" in m
        assert "hhi" in m
        assert "gini" in m
        assert "risk_label" in m
