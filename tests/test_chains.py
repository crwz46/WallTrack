import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from walltrack.chains import ChainManager, CHAINS, DEFAULT_CHAIN
from walltrack.tracker import WalletTracker
from walltrack.export import ExportManager


class MockResponse:
    def __init__(self, data):
        self._data = data

    def json(self):
        return self._data


def test_chain_config():
    assert "ethereum" in CHAINS
    assert "bsc" in CHAINS
    assert "polygon" in CHAINS
    assert "arbitrum" in CHAINS
    assert CHAINS[DEFAULT_CHAIN].name == "Ethereum"


def test_chain_manager_no_keys():
    mgr = ChainManager({})
    with pytest.raises(ValueError, match="not supported"):
        mgr.get_chain("invalid")


def test_chain_manager_no_api_key():
    mgr = ChainManager({})
    with pytest.raises(ValueError, match="API key for Ethereum not found"):
        mgr.call_api("ethereum", {"module": "account", "action": "balance"})


def test_export_json():
    data = {
        "address": "0x123",
        "chain": "Ethereum",
        "chain_id": "ethereum",
        "symbol": "ETH",
        "native_balance": 1.5,
        "transaction_count": 10,
        "last_transaction": None,
        "top_tokens": [],
    }
    output = ExportManager.to_json(data)
    assert '"native_balance": 1.5' in output
    assert '"address": "0x123"' in output


def test_export_csv():
    data = {
        "address": "0x123",
        "chain": "Ethereum",
        "chain_id": "ethereum",
        "symbol": "ETH",
        "native_balance": 1.5,
        "transaction_count": 10,
        "last_transaction": {
            "hash": "0xabc",
            "from": "0xfrom",
            "to": "0xto",
            "value": 0.5,
            "timestamp": "2025-01-01",
        },
        "top_tokens": [
            {"symbol": "USDC", "contract": "0xusdc", "total_value": 1000.0, "tx_count": 5}
        ],
    }
    output = ExportManager.to_csv(data)
    assert "USDC" in output
    assert "0xabc" in output


def test_list_chains():
    mgr = ChainManager({})
    chains = mgr.list_chains()
    assert "ethereum" in chains
    assert "bsc" in chains
    assert "polygon" in chains
    assert "arbitrum" in chains


@pytest.mark.parametrize("chain_id", ["ethereum", "bsc", "polygon", "arbitrum"])
def test_all_chains_exist(chain_id):
    mgr = ChainManager({})
    config = mgr.get_chain(chain_id)
    assert config.name is not None
    assert config.symbol is not None
    assert config.api_url is not None
