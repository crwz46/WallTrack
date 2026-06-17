from .chains import ChainManager
from .tracker import WalletTracker
from .export import ExportManager
from .charts import ChartGenerator
from .gas import GasTracker
from .flashloan import FlashLoanSimulator
from .history import HistoryManager
from .prices import PriceFeed
from .comparator import WalletComparator
from .scheduler import Scheduler
from .autocomplete import install
from .alerts import GasAlert

try:
    from .web3_provider import Web3Provider
except ImportError:
    Web3Provider = None
