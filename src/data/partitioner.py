"""
Multi-Bank Ledger Partitioner (Federated Data Simulation).

Simulates real-world banking privacy silos:
1. Partitions the unified transaction ledger into 3 private, disjoint bank ledgers
   (Bank A, Bank B, Bank C).
2. Isolates intra-bank records so each bank only observes transactions where it is
   the originating or receiving institution.
3. Extracts and indexes cross-bank boundary transactions for central enclave evaluation.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Tuple
from src.data.dataset_loader import load_all_datasets, PROCESSED_DATA_DIR


def partition_ledgers(
    df_trans: pd.DataFrame = None, output_dir: Path = PROCESSED_DATA_DIR
) -> Dict[str, pd.DataFrame]:
    """
    Partitions transactions into Bank A, Bank B, Bank C local ledgers,
    plus an isolated cross-bank boundary transaction set.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    if df_trans is None:
        datasets = load_all_datasets()
        df_trans = datasets["hi_trans"]

    banks = ["Bank_A", "Bank_B", "Bank_C"]
    bank_ledgers = {}

    print(f"\n[Partitioner] Partitioning {len(df_trans):,} global transactions across 3 bank silos...")

    # For each bank, it has visibility into transactions where it is the originating bank
    # (or participant in internal transfers).
    for b in banks:
        # A bank sees outgoing transactions originating from its accounts,
        # plus incoming inter-bank deposits once settled.
        bank_visibility_mask = (df_trans["From Bank"] == b) | (df_trans["To Bank"] == b)
        ledger = df_trans[bank_visibility_mask].copy()

        # Save private bank ledger
        out_csv = output_dir / f"{b.lower()}_ledger.csv"
        ledger.to_csv(out_csv, index=False)
        bank_ledgers[b] = ledger
        laundering_count = (ledger["Is Laundering"] == 1).sum()
        print(f"  [OK] {b} Ledger: {len(ledger):,} transactions ({laundering_count} tagged as laundering).")

    # Cross-bank boundary transactions: From Bank != To Bank
    cross_bank_mask = df_trans["From Bank"] != df_trans["To Bank"]
    df_boundary = df_trans[cross_bank_mask].copy()
    boundary_csv = output_dir / "cross_bank_boundary.csv"
    df_boundary.to_csv(boundary_csv, index=False)

    cross_laundering = (df_boundary["Is Laundering"] == 1).sum()
    print(f"  [OK] Cross-Bank Boundary Table: {len(df_boundary):,} transactions ({cross_laundering} cross-bank laundering hops).")

    return {
        "Bank_A": bank_ledgers["Bank_A"],
        "Bank_B": bank_ledgers["Bank_B"],
        "Bank_C": bank_ledgers["Bank_C"],
        "Boundary": df_boundary,
    }


if __name__ == "__main__":
    partition_ledgers()
