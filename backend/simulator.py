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


# Attack template uses placeholder keys for accounts — replaced with fresh IDs each ring.
# Ring topology: A(orig) → B(mule1) → B(mule2) + B(mule3) → C(coll1) + C(coll2) → C(atm)
_ATTACK_TEMPLATE = [
    ("bankA", "ORIG",  "bankB", "MULE1", 4900.00, "Wire"),
    ("bankB", "MULE1", "bankB", "MULE2", 2450.00, "ACH"),
    ("bankB", "MULE1", "bankB", "MULE3", 2450.00, "ACH"),
    ("bankB", "MULE2", "bankC", "COLL1", 2450.00, "ACH"),
    ("bankB", "MULE3", "bankC", "COLL2", 2450.00, "ACH"),
    ("bankC", "COLL1", "bankC", "ATM",   4870.00, "Wire"),
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

RING_SIZE = len(_ATTACK_TEMPLATE)


def _fresh_ring_accounts() -> dict:
    """Generate a new set of random account IDs for one ring so every ring is a new counterparty."""
    return {role: f"ACC-{uuid.uuid4().hex[:6].upper()}" for role in ("ORIG", "MULE1", "MULE2", "MULE3", "COLL1", "COLL2", "ATM")}


class Simulator:
    def __init__(self):
        self._scenario = "attack"
        self._payroll_cycle: Iterator = itertools.cycle(_PAYROLL_TEMPLATES)
        # attack uses day=3 (ACH $2450 scores 0.9999); payroll uses day=1 (scores ~0.02)
        self._attack_base = datetime(2026, 11, 3, 14, 0, 0)
        self._payroll_base = datetime(2026, 11, 1, 9, 0, 0)
        self._offset_seconds = 0
        self._ring_step = 0
        self._ring_accounts = _fresh_ring_accounts()

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

        if self._scenario == "attack":
            if self._ring_step == 0:
                self._ring_accounts = _fresh_ring_accounts()
            step = _ATTACK_TEMPLATE[self._ring_step]
            self._ring_step = (self._ring_step + 1) % RING_SIZE
            accs = self._ring_accounts
            tx = _tx(step[0], accs[step[1]], step[2], accs[step[3]], step[4], step[5])
        else:
            tx = dict(next(self._payroll_cycle))

        tx["transaction_id"] = f"TX-{uuid.uuid4().hex[:8].upper()}"
        tx["timestamp"] = ts.strftime("%Y-%m-%dT%H:%M:%S")
        return tx
