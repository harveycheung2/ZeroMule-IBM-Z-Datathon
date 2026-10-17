"""
Data Schemas and Structures for ZeroMule-IBM-Z-Datathon.

Defines standardized data interfaces, contract schemas, and dataclasses for:
1. Transaction Ledgers (IBM AML format)
2. Laundering Patterns and Topology Ground Truth
3. Bank Silo Partition Specifications
4. Cross-Bank Boundary Intersections
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
import pandas as pd


@dataclass
class TransactionRecord:
    """
    Representation of a single financial transaction record.
    Matches standard IBM Transactions for AML schema.
    """
    timestamp: datetime
    from_bank: str
    from_account: str
    to_bank: str
    to_account: str
    amount_received: float
    receiving_currency: str
    amount_paid: float
    payment_currency: str
    payment_format: str
    is_laundering: int = 0


@dataclass
class LaunderingPattern:
    """
    Topology definition of an AML laundering pattern.
    Types: Cycle, Fan-In, Fan-Out, Scatter-Gather, Bipartite, Stacking.
    """
    pattern_id: int
    pattern_type: str
    involved_banks: List[str]
    involved_accounts: List[str]
    is_cross_bank: bool = False


@dataclass
class BankSiloPartition:
    """
    Represents an isolated bank partition containing only local ledger data.
    Institutions cannot view counterpart internal records.
    """
    bank_id: str
    internal_accounts: Set[str] = field(default_factory=set)
    boundary_accounts: Set[str] = field(default_factory=set)
    local_transactions: Optional[pd.DataFrame] = None
    node_feature_matrix: Optional[object] = None


@dataclass
class BoundaryIntersection:
    """
    Cryptographic PSI intersection matching counterparties across bank silos.
    """
    bank_pair: Tuple[str, str]
    pseudonymous_intersection_hashes: List[str] = field(default_factory=list)
    matched_boundary_edges: int = 0
