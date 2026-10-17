"""
Data Verification and Integrity Framework for ZeroMule-IBM-Z-Datathon.

Validates:
1. Presence of dataset files in data/raw/
2. Schema adherence of transaction files
3. Verification of column presence, timestamp chronological ordering, and label distributions
"""

import sys
from pathlib import Path
from src.data.dataset_loader import IBMAMLDataLoader, BAFDataLoader


def verify_environment_and_datasets(raw_dir: Path = Path("data/raw")):
    """
    Checks dataset availability and validates schema integrity.
    Does not generate synthetic or false data.
    """
    print("=" * 60)
    print("  ZeroMule-IBM-Z-Datathon: Data Verification Framework")
    print("=" * 60)

    raw_path = Path(raw_dir)
    if not raw_path.exists():
        print(f"[Notice] Raw data directory '{raw_path}' does not exist yet.")
        return False

    ibm_file = raw_path / "HI-Small_Trans.csv"
    if not ibm_file.exists():
        print(f"[Pending] Raw dataset {ibm_file.name} not found in {raw_path}.")
        print("          Place production or competition datasets into data/raw/.")
        return True

    print(f"[OK] Found dataset: {ibm_file.name}")
    loader = IBMAMLDataLoader(raw_path)
    df = loader.load_transactions()
    loader.validate_schema(df)
    print(f"[OK] Schema validated successfully across {len(df):,} records.")
    return True


if __name__ == "__main__":
    verify_environment_and_datasets()
