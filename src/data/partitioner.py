"""
Multi-Bank Silo Partitioner for ZeroMule-IBM-Z-Datathon.

Simulates strict regulatory compliance silos across competing financial institutions:
- Each bank maintains a private ledger invisible to other institutions.
- Cross-bank transactions define boundary nodes where accounts interact across borders.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Set, Tuple
import pandas as pd
from src.data.schemas import BankSiloPartition


class BasePartitioner(ABC):
    """
    Abstract partitioner interface for multi-institution financial simulation.
    """

    @abstractmethod
    def partition_ledger(self, df: pd.DataFrame) -> Dict[str, BankSiloPartition]:
        """Partitions global transactions into individual bank silos."""
        raise NotImplementedError("Subclasses must implement partition_ledger.")


class BankSiloPartitioner(BasePartitioner):
    """
    Splits global transaction records into independent bank silos and identifies boundary counterparties.
    """

    def __init__(self, silo_bank_names: List[str] = None):
        self.silo_bank_names = silo_bank_names or ["Bank_A", "Bank_B", "Bank_C"]

    def identify_boundary_accounts(self, df: pd.DataFrame) -> Dict[str, Set[str]]:
        """
        Identifies accounts involved in inter-bank transfers (cross-border boundary nodes).
        """
        boundary_accounts: Dict[str, Set[str]] = {b: set() for b in self.silo_bank_names}
        cross_bank_mask = df["From Bank"] != df["To Bank"]
        cross_df = df[cross_bank_mask]

        for bank in self.silo_bank_names:
            outbound = set(cross_df[cross_df["From Bank"] == bank]["Account"])
            inbound = set(cross_df[cross_df["To Bank"] == bank]["Account.1"])
            boundary_accounts[bank] = outbound.union(inbound)

        return boundary_accounts

    def partition_ledger(self, df: pd.DataFrame) -> Dict[str, BankSiloPartition]:
        """
        Filters transactions visible to each bank silo:
        A bank sees transactions where it is either the sending bank or the receiving bank.
        Internal accounts and balances of other banks remain hidden.
        """
        partitions = {}
        boundary_map = self.identify_boundary_accounts(df)

        for bank_name in self.silo_bank_names:
            visible_mask = (df["From Bank"] == bank_name) | (df["To Bank"] == bank_name)
            local_tx = df[visible_mask].copy()

            internal_accs = set(local_tx[local_tx["From Bank"] == bank_name]["Account"]).union(
                set(local_tx[local_tx["To Bank"] == bank_name]["Account.1"])
            )

            partitions[bank_name] = BankSiloPartition(
                bank_id=bank_name,
                internal_accounts=internal_accs,
                boundary_accounts=boundary_map.get(bank_name, set()),
                local_transactions=local_tx
            )

        return partitions
