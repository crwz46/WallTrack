from datetime import datetime
from typing import Dict, List, Optional

from .chains import ChainManager, DEFAULT_CHAIN


class WalletTracker:
    def __init__(self, chain_mgr: ChainManager):
        self.chain_mgr = chain_mgr

    def get_native_balance(
        self, address: str, chain_id: str = DEFAULT_CHAIN
    ) -> float:
        params = {
            "module": "account",
            "action": "balance",
            "address": address,
            "tag": "latest",
        }
        data = self.chain_mgr.call_api(chain_id, params)
        wei = int(data["result"])
        chain = self.chain_mgr.get_chain(chain_id)
        return wei / (10 ** chain.decimals)

    def get_transaction_count(
        self, address: str, chain_id: str = DEFAULT_CHAIN
    ) -> int:
        params = {
            "module": "proxy",
            "action": "eth_getTransactionCount",
            "address": address,
            "tag": "latest",
        }
        data = self.chain_mgr.call_api(chain_id, params)
        return int(data["result"], 16)

    def get_last_transaction(
        self, address: str, chain_id: str = DEFAULT_CHAIN
    ) -> Optional[Dict]:
        params = {
            "module": "account",
            "action": "txlist",
            "address": address,
            "page": 1,
            "offset": 1,
            "sort": "desc",
        }
        data = self.chain_mgr.call_api(chain_id, params)
        txs = data.get("result", [])
        if not txs:
            return None
        tx = txs[0]
        chain = self.chain_mgr.get_chain(chain_id)
        return {
            "hash": tx["hash"],
            "from": tx["from"],
            "to": tx["to"],
            "value": int(tx["value"]) / (10 ** chain.decimals),
            "timestamp": datetime.fromtimestamp(
                int(tx["timeStamp"])
            ).strftime("%Y-%m-%d %H:%M:%S"),
        }

    def get_top_tokens(
        self, address: str, chain_id: str = DEFAULT_CHAIN, limit: int = 5
    ) -> List[Dict]:
        params = {
            "module": "account",
            "action": "tokentx",
            "address": address,
            "page": 1,
            "offset": 100,
            "sort": "desc",
        }
        data = self.chain_mgr.call_api(chain_id, params)
        txs = data.get("result", [])

        token_map: Dict[str, Dict] = {}
        for tx in txs:
            symbol = tx.get("tokenSymbol", "?")
            token_address = tx["contractAddress"]
            decimals = int(tx.get("tokenDecimal", 18))
            raw_value = int(tx.get("value", 0))
            value = raw_value / (10 ** decimals)

            if token_address not in token_map:
                token_map[token_address] = {
                    "symbol": symbol,
                    "contract": token_address,
                    "total_value": 0.0,
                    "tx_count": 0,
                }
            token_map[token_address]["total_value"] += value
            token_map[token_address]["tx_count"] += 1

        sorted_tokens = sorted(
            token_map.values(), key=lambda x: x["total_value"], reverse=True
        )
        return sorted_tokens[:limit]

    def analyze(
        self,
        address: str,
        chain_id: str = DEFAULT_CHAIN,
        token_limit: int = 5,
    ) -> Dict:
        chain = self.chain_mgr.get_chain(chain_id)
        native_balance = self.get_native_balance(address, chain_id)
        tx_count = self.get_transaction_count(address, chain_id)
        last_tx = self.get_last_transaction(address, chain_id)
        top_tokens = self.get_top_tokens(address, chain_id, token_limit)

        return {
            "address": address,
            "chain": chain.name,
            "chain_id": chain_id,
            "symbol": chain.symbol,
            "native_balance": native_balance,
            "transaction_count": tx_count,
            "last_transaction": last_tx,
            "top_tokens": top_tokens,
        }
