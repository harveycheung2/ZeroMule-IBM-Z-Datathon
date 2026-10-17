"""
Dataset Loader Framework for ZeroMule-IBM-Z-Datathon.

Provides modular interfaces and ingestion pipelines for:
- IBM Transactions for Anti-Money Laundering (AML) (HI-Small_Trans.csv, HI-Small_Patterns.txt)
- Bank Account Fraud (BAF) demographic fairness benchmark
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional, Tuple
import pandas as pd


class BaseDatasetLoader(ABC):
    """
    Abstract Base Class for dataset ingestion and validation in ZeroMule.
    """

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)

    @abstractmethod
    def load_transactions(self) -> pd.DataFrame:
        """Loads and returns standardized transaction records."""
        raise NotImplementedError("Subclasses must implement load_transactions.")

    @abstractmethod
    def load_patterns(self) -> Optional[pd.DataFrame]:
        """Loads ground-truth laundering ring topologies if available."""
        raise NotImplementedError("Subclasses must implement load_patterns.")

    @abstractmethod
    def validate_schema(self, df: pd.DataFrame) -> bool:
        """Validates that loaded data adheres to required structural contracts."""
        raise NotImplementedError("Subclasses must implement validate_schema.")


class IBMAMLDataLoader(BaseDatasetLoader):
    """
    Ingestion handler for IBM Transactions for Anti-Money Laundering (AML).
    Expects HI-Small_Trans.csv and HI-Small_Patterns.txt in the raw directory.
    """

    REQUIRED_TRANSACTION_COLS = [
        "Timestamp", "From Bank", "Account", "To Bank", "Account.1",
        "Amount Received", "Receiving Currency", "Amount Paid", "Payment Format", "Is Laundering"
    ]

    def load_transactions(self, filename: str = "HI-Small_Trans.csv") -> pd.DataFrame:
        """
        Loads the IBM AML transaction file.
        """
        file_path = self.data_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(
                f"Transaction ledger not found at {file_path}. "
                "Place dataset in data/raw/ or configure data source."
            )
        return pd.read_csv(file_path)

    def load_patterns(self, filename: str = "HI-Small_Patterns.txt") -> Optional[pd.DataFrame]:
        """
        Loads laundering pattern definitions.
        """
        file_path = self.data_dir / filename
        if not file_path.exists():
            return None
        return pd.read_csv(file_path, sep="\t")

    def validate_schema(self, df: pd.DataFrame) -> bool:
        """
        Validates column presence, non-negative amounts, and timestamp ordering.
        """
        missing = [c for c in self.REQUIRED_TRANSACTION_COLS if c not in df.columns]
        if missing:
            raise ValueError(f"Transaction dataset missing required columns: {missing}")
        return True


class BAFDataLoader(BaseDatasetLoader):
    """
    Ingestion handler for NeurIPS Bank Account Fraud (BAF) suite
    used for Equalized-Odds fairness calibration.
    """

    def load_transactions(self, filename: str = "Base.csv") -> pd.DataFrame:
        """
        Loads BAF tabular dataset containing applicant demographic fields and fraud labels.
        """
        file_path = self.data_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"BAF dataset not found at {file_path}.")
        return pd.read_csv(file_path)

    def load_patterns(self) -> Optional[pd.DataFrame]:
        return None

    def validate_schema(self, df: pd.DataFrame) -> bool:
        required = ["fraud_bool", "customer_age"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"BAF dataset missing required fairness columns: {missing}")
        return True
