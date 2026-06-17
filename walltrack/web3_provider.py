from dataclasses import dataclass
from typing import Dict, List, Optional
from .chains import ChainConfig


@dataclass
class RPCConfig:
    name: str
    chain_id: int
    rpc_url: str
    native_token: str


RPCS = {
    "ethereum": RPCConfig(
        name="Ethereum",
        chain_id=1,
        rpc_url="https://eth.llamarpc.com",
        native_token="ETH",
    ),
    "bsc": RPCConfig(
        name="BNB Smart Chain",
        chain_id=56,
        rpc_url="https://binance.llamarpc.com",
        native_token="BNB",
    ),
    "polygon": RPCConfig(
        name="Polygon",
        chain_id=137,
        rpc_url="https://polygon.llamarpc.com",
        native_token="MATIC",
    ),
    "arbitrum": RPCConfig(
        name="Arbitrum",
        chain_id=42161,
        rpc_url="https://arbitrum.llamarpc.com",
        native_token="ETH",
    ),
}


class Web3Provider:
    def __init__(self, chain_id: str = "ethereum"):
        if chain_id not in RPCS:
            raise ValueError(f"Unsupported chain: {chain_id}")
        self.config = RPCS[chain_id]
        self._w3 = None

    @property
    def w3(self):
        if self._w3 is None:
            try:
                from web3 import Web3
                self._w3 = Web3(Web3.HTTPProvider(self.config.rpc_url))
            except ImportError:
                raise ImportError(
                    "web3.py not installed. Run: pip install web3"
                )
        return self._w3

    def is_connected(self) -> bool:
        try:
            return self.w3.is_connected()
        except Exception:
            return False

    def get_eth_balance(self, address: str) -> float:
        checksum = self.w3.to_checksum_address(address)
        wei = self.w3.eth.get_balance(checksum)
        return wei / 1e18

    def get_transaction_count(self, address: str) -> int:
        checksum = self.w3.to_checksum_address(address)
        return self.w3.eth.get_transaction_count(checksum)

    def get_last_block(self) -> Dict:
        block = self.w3.eth.get_block("latest")
        return {
            "number": block["number"],
            "hash": block["hash"].hex(),
            "timestamp": block["timestamp"],
            "tx_count": len(block["transactions"]),
        }

    def get_gas_price(self) -> Dict:
        gwei = self.w3.eth.gas_price / 1e9
        return {
            "gwei": round(gwei, 2),
            "wei": self.w3.eth.gas_price,
        }

    def get_erc20_balance(
        self, wallet: str, token_address: str
    ) -> Optional[float]:
        checksum_wallet = self.w3.to_checksum_address(wallet)
        checksum_token = self.w3.to_checksum_address(token_address)

        abi = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"type":"function"}]'
        contract = self.w3.eth.contract(
            address=checksum_token, abi=abi
        )
        try:
            balance = contract.functions.balanceOf(checksum_wallet).call()
            decimals = contract.functions.decimals().call()
            return balance / (10 ** decimals)
        except Exception:
            return None

    def analyze_onchain(self, address: str) -> Dict:
        return {
            "chain": self.config.name,
            "connected": self.is_connected(),
            "balance": self.get_eth_balance(address),
            "tx_count": self.get_transaction_count(address),
            "latest_block": self.get_last_block(),
            "gas_price": self.get_gas_price(),
        }
