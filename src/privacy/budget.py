"""Durable bank-wide composition. Missing/corrupt ledgers fail closed.

Provisioning is a separate deployment action, never performed by an exporter.
SQLite BEGIN IMMEDIATE serializes reservations across processes and threads.
"""

from contextlib import contextmanager, closing
import math
import os
from pathlib import Path
import sqlite3
import uuid

from src.privacy.dp_perturbation import DELTA, MAX_EPSILON, epsilon_for_rho, positive


class PrivacyBudgetExceeded(RuntimeError):
    pass


class PrivacyBudgetLedger:
    def __init__(self, path, bank_id):
        self.path = Path(path).resolve()
        self.bank_id = bank_id
        # Open without CREATE even on the first use. A lost ledger is never reset.
        with self._connect() as db:
            self._validate(db)

    @classmethod
    def provision(cls, path, bank_id):
        """One-time administrative provisioning; refuses existing files."""
        if not isinstance(bank_id, str) or not bank_id:
            raise ValueError("A bank ID is required")
        path = Path(path).resolve()
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
        with closing(sqlite3.connect(path)) as db:
            db.executescript('''
                CREATE TABLE policy (bank TEXT NOT NULL, version INTEGER NOT NULL);
                CREATE TABLE releases (id TEXT PRIMARY KEY, rho REAL NOT NULL CHECK(rho > 0));
                CREATE TRIGGER no_release_update BEFORE UPDATE ON releases BEGIN SELECT RAISE(ABORT, 'immutable'); END;
                CREATE TRIGGER no_release_delete BEFORE DELETE ON releases BEGIN SELECT RAISE(ABORT, 'immutable'); END;
                CREATE TRIGGER no_policy_update BEFORE UPDATE ON policy BEGIN SELECT RAISE(ABORT, 'immutable'); END;
                CREATE TRIGGER no_policy_delete BEFORE DELETE ON policy BEGIN SELECT RAISE(ABORT, 'immutable'); END;
                CREATE TRIGGER no_policy_insert BEFORE INSERT ON policy WHEN EXISTS(SELECT 1 FROM policy) BEGIN SELECT RAISE(ABORT, 'immutable'); END;
            ''')
            db.execute("INSERT INTO policy VALUES (?, 1)", (bank_id,))
            db.commit()
        return cls(path, bank_id)

    @contextmanager
    def _connect(self):
        db = sqlite3.connect(self.path.as_uri() + "?mode=rw", uri=True, timeout=30)
        try:
            db.execute("PRAGMA synchronous=FULL")
            with db:
                yield db
        finally:
            db.close()

    def _validate(self, db):
        if db.execute("SELECT bank, version FROM policy").fetchall() != [(self.bank_id, 1)]:
            raise ValueError("Privacy ledger bank/policy mismatch")
        rows = db.execute("SELECT rho FROM releases").fetchall()
        if any(not math.isfinite(r[0]) or r[0] <= 0 for r in rows):
            raise ValueError("Invalid privacy ledger")
        return math.fsum(r[0] for r in rows)

    def reserve(self, sigma):
        sigma = positive(sigma, "sigma")
        rho = 0.5 / sigma / sigma
        if not math.isfinite(rho) or rho <= 0:
            raise ValueError("Invalid Gaussian privacy cost")
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            cumulative_rho = self._validate(db) + rho
            epsilon = epsilon_for_rho(cumulative_rho)
            if epsilon > MAX_EPSILON:
                raise PrivacyBudgetExceeded("Cumulative privacy budget exceeds epsilon 2.0 at delta 1e-5")
            release_id = uuid.uuid4().hex
            db.execute("INSERT INTO releases VALUES (?, ?)", (release_id, rho))
            # Commit before noise generation/signing/return; failures burn budget safely.
            db.commit()
        return {"release_id": release_id, "epsilon_spent": epsilon,
                "delta": DELTA, "cumulative_rho": cumulative_rho}
