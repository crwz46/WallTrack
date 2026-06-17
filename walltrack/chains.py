import requests
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class ChainConfig:
    name: str
    symbol: str
    api_url: str
    explorer_url: str
    api_key_env: str
    native_token: str
    decimals: int = 18


CHAINS = {
    "ethereum": ChainConfig(
        name="Ethereum",
        symbol="ETH",
        api_url="https://api.etherscan.io/api",
        explorer_url="https://etherscan.io",
        api_key_env="ETHERSCAN_API_KEY",
        native_token="ETH",
    ),
    "bsc": ChainConfig(
        name="BNB Smart Chain",
        symbol="BNB",
        api_url="https://api.bscscan.com/api",
        explorer_url="https://bscscan.com",
        api_key_env="BSCSCAN_API_KEY",
        native_token="BNB",
    ),
    "polygon": ChainConfig(
        name="Polygon",
        symbol="MATIC",
        api_url="https://api.polygonscan.com/api",
        explorer_url="https://polygonscan.com",
        api_key_env="POLYGONSCAN_API_KEY",
        native_token="MATIC",
    ),
    "arbitrum": ChainConfig(
        name="Arbitrum",
        symbol="ETH",
        api_url="https://api.arbiscan.io/api",
        explorer_url="https://arbiscan.io",
        api_key_env="ARBISCAN_API_KEY",
        native_token="ETH",
    ),
}

DEFAULT_CHAIN = "ethereum"


class ChainManager:
    def __init__(self, api_keys: Dict[str, str]):
        self.api_keys = api_keys

    def get_chain(self, chain_id: str = DEFAULT_CHAIN) -> ChainConfig:
        if chain_id not in CHAINS:
            raise ValueError(
                f"Chain '{chain_id}' not supported. "
                f"Available: {', '.join(CHAINS.keys())}"
            )
        return CHAINS[chain_id]

    def get_api_key(self, chain_id: str) -> Optional[str]:
        chain = self.get_chain(chain_id)
        return self.api_keys.get(chain.api_key_env)

    def call_api(
        self, chain_id: str, params: Dict, timeout: int = 10
    ) -> Dict:
        chain = self.get_chain(chain_id)
        api_key = self.get_api_key(chain_id)
        if not api_key:
            raise ValueError(
                f"API key for {chain.name} not found. "
                f"Set {chain.api_key_env} env var."
            )
        params["apikey"] = api_key
        resp = requests.get(
            chain.api_url, params=params, timeout=timeout
        )
        data = resp.json()
        if data.get("status") != "1":
            msg = data.get("message", "Unknown error")
            if "No transactions found" in msg or "OK" in msg:
                return data
            raise ValueError(
                f"{chain.name} API Error: {msg}"
            )
        return data

    def list_chains(self) -> Dict[str, str]:
        return {k: v.name for k, v in CHAINS.items()}
