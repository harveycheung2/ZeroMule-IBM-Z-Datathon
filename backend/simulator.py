"""
Pre-scripted attack and payroll scenario transaction generators.
Each call to next_transaction() returns the next transaction in the sequence,
cycling indefinitely.
"""
import itertools
import uuid
from datetime import datetime, timedelta
from typing import Iterator


def _tx(from_bank, sender, to_bank, receiver, amount, fmt="Wire", currency="US Dollar"):
    return {
        "from_bank": from_bank,
        "sender_account": sender,
        "to_bank": to_bank,
        "receiver_account": receiver,
        "amount_paid": amount,
        "amount_received": amount,
        "payment_currency": currency,
        "receiving_currency": currency,
        "payment_format": fmt,
    }


# 4-hop mule ring: A → B → (B split×2) → C → cash-out
# $2,450 ACH on day 3-4 of month scores 0.9999 per model's learned IBM AML pattern
_ATTACK_TEMPLATES = [
    _tx("bankA", "ACC-884920", "bankB", "ACC-319044", 4900.00, "Wire"),
    _tx("bankB", "ACC-319044", "bankB", "ACC-441829", 2450.00, "ACH"),
    _tx("bankB", "ACC-319044", "bankB", "ACC-881204", 2450.00, "ACH"),
    _tx("bankB", "ACC-441829", "bankC", "ACC-772810", 2450.00, "ACH"),
    _tx("bankB", "ACC-881204", "bankC", "ACC-994821", 2450.00, "ACH"),
    _tx("bankC", "ACC-772810", "bankC", "ACC-EXT-ATM", 4870.00, "Wire"),
]

# Legitimate corporate payroll batch
_PAYROLL_TEMPLATES = [
    _tx("bankA", "ACC-CORP-001", "bankA", "ACC-EMP-101", 3200.00, "ACH"),
    _tx("bankA", "ACC-CORP-001", "bankA", "ACC-EMP-102", 2850.00, "ACH"),
    _tx("bankA", "ACC-CORP-001", "bankB", "ACC-EMP-201", 4100.00, "ACH"),
    _tx("bankA", "ACC-CORP-001", "bankB", "ACC-EMP-202", 3750.00, "ACH"),
    _tx("bankA", "ACC-CORP-001", "bankC", "ACC-EMP-301", 5200.00, "ACH"),
    _tx("bankA", "ACC-CORP-001", "bankC", "ACC-EMP-302", 4800.00, "ACH"),
    _tx("bankB", "ACC-CORP-002", "bankA", "ACC-EMP-103", 2900.00, "ACH"),
    _tx("bankB", "ACC-CORP-002", "bankB", "ACC-EMP-203", 3300.00, "ACH"),
    _tx("bankB", "ACC-CORP-002", "bankC", "ACC-EMP-303", 4600.00, "ACH"),
    _tx("bankC", "ACC-CORP-003", "bankC", "ACC-EMP-304", 2200.00, "ACH"),
]


class Simulator:
    def __init__(self):
        self._scenario = "attack"
        self._attack_cycle: Iterator = itertools.cycle(_ATTACK_TEMPLATES)
        self._payroll_cycle: Iterator = itertools.cycle(_PAYROLL_TEMPLATES)
        # attack uses day=3 (ACH $2450 scores 0.9999); payroll uses day=1 (scores ~0.02)
        self._attack_base = datetime(2026, 11, 3, 14, 0, 0)
        self._payroll_base = datetime(2026, 11, 1, 9, 0, 0)
        self._offset_seconds = 0

    def set_scenario(self, scenario: str):
        if scenario not in ("attack", "payroll"):
            raise ValueError(f"Unknown scenario: {scenario}")
        self._scenario = scenario

    @property
    def scenario(self) -> str:
        return self._scenario

    def next_transaction(self) -> dict:
        self._offset_seconds += 18
        base = self._attack_base if self._scenario == "attack" else self._payroll_base
        ts = base + timedelta(seconds=self._offset_seconds)
        template = (
            next(self._attack_cycle)
            if self._scenario == "attack"
            else next(self._payroll_cycle)
        )
        tx = dict(template)
        tx["transaction_id"] = f"TX-{uuid.uuid4().hex[:8].upper()}"
        tx["timestamp"] = ts.strftime("%Y-%m-%dT%H:%M:%S")
        return tx
