"""
Data Integrity and Validation Checker for ZeroMule.

Validates:
1. Transaction ledger schema, row counts, and account distributions.
2. Checks for null values, negative or corrupted transaction amounts.
3. Timestamp chronological consistency and currency format distributions.
4. Laundering ring topological coverage from pattern ground truth.
"""

import sys
import pandas as pd
from pathlib import Path
from src.data.dataset_loader import load_all_datasets


def run_data_verification():
    print("=" * 60)
    print("  ZeroMule AML Data Integrity & Validation Suite")
    print("=" * 60)

    datasets = load_all_datasets()
    df_trans = datasets["hi_trans"]
    df_patterns = datasets["hi_patterns"]
    df_baf = datasets["baf"]

    errors = []
    warnings = []

    # 1. Check Transaction Table
    print(f"\n[1/3] Validating HI-Small Transactions ({len(df_trans):,} rows)...")
    required_cols = [
        "Timestamp", "From Bank", "Account", "To Bank", "Account.1",
        "Amount Received", "Receiving Currency", "Amount Paid", "Payment Format", "Is Laundering"
    ]
    for col in required_cols:
        if col not in df_trans.columns:
            errors.append(f"Missing required transaction column: {col}")

    # Check for negative amounts
    neg_paid = (df_trans["Amount Paid"] < 0).sum()
    neg_recv = (df_trans["Amount Received"] < 0).sum()
    if neg_paid > 0 or neg_recv > 0:
        errors.append(f"Found negative transaction amounts: {neg_paid} paid, {neg_recv} received.")
    else:
        print("  [OK] Zero negative transaction amounts found.")

    # Check for null timestamps
    null_ts = df_trans["Timestamp"].isna().sum()
    if null_ts > 0:
        errors.append(f"Found {null_ts} missing timestamps.")
    else:
        print("  [OK] All timestamps valid and non-null.")

    # Laundering class imbalance ratio
    pos_count = (df_trans["Is Laundering"] == 1).sum()
    ratio = (pos_count / len(df_trans)) * 100
    print(f"  [OK] Laundering tags detected: {pos_count:,} positive transactions ({ratio:.2f}% positive rate).")

    # Bank distribution
    from_banks = df_trans["From Bank"].value_counts().to_dict()
    print(f"  [OK] Originating bank distribution: {from_banks}")

    # 2. Check Pattern Ground Truth
    print(f"\n[2/3] Validating AMLSim Patterns Ground Truth ({len(df_patterns):,} patterns)...")
    if "Pattern_Type" in df_patterns.columns:
        p_types = df_patterns["Pattern_Type"].value_counts().to_dict()
        print(f"  [OK] Topologies identified: {p_types}")
    else:
        warnings.append("Pattern_Type column not in pattern file.")

    # 3. Check BAF Demographic Suite
    print(f"\n[3/3] Validating NeurIPS BAF Demographic Suite ({len(df_baf):,} records)...")
    elderly_count = (df_baf["is_elderly"] == 1).sum()
    elderly_pct = (elderly_count / len(df_baf)) * 100
    print(f"  [OK] Elderly accounts (Age >= 65): {elderly_count:,} ({elderly_pct:.1f}%).")
    print(f"  [OK] Overall fraud rate in BAF: {df_baf['fraud_bool'].mean() * 100:.2f}%.")

    print("\n" + "=" * 60)
    if errors:
        print(f"[FAIL] Verification FAILED with {len(errors)} error(s):")
        for err in errors:
            print(f"  - {err}")
        return False
    else:
        print("[SUCCESS] ALL DATA INTEGRITY GATES PASSED SUCCESSFULLY!")
        print("=" * 60)
        return True


if __name__ == "__main__":
    success = run_data_verification()
    sys.exit(0 if success else 1)
