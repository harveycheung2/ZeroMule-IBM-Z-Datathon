"""
LightGBM bundle wrapper with SQLite-backed 8-feature history tracking.
Translates frontend bank labels to model canonical IDs, computes rolling
history features, scores transactions, and pseudonymises account IDs.
"""
import hashlib
import hmac
import json
import math
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import lightgbm as lgb
import numpy as np

BUNDLE_DIR = Path(__file__).resolve().parent / "model_bundle"
DB_PATH = Path(__file__).resolve().parent / "history.db"

BANK_LABEL_TO_ID = {"bankA": "1", "bankB": "10", "bankC": "12"}
BANK_ID_TO_DISPLAY = {"1": "BANK_A_SG", "10": "BANK_B_SG", "12": "BANK_C_SG"}
BANK_LABEL_TO_DISPLAY = {
    "bankA": "BANK_A_SG",
    "bankB": "BANK_B_SG",
    "bankC": "BANK_C_SG",
}

TRANSACTION_FEATURES = [
    "amount_paid", "amount_received",
    "log_amount_paid", "log_amount_received",
    "hour", "weekday", "day_of_month",
    "payment_currency", "receiving_currency", "payment_format",
]
HISTORY_FEATURES = [
    "sender_out_count_24h",
    "sender_out_amount_24h_same_currency",
    "receiver_in_count_24h",
    "receiver_in_amount_24h_same_currency",
    "sender_seconds_since_previous_outgoing",
    "pair_prior_count",
    "is_new_counterparty",
    "sender_amount_over_prior_mean_same_currency",
]

_HMAC_SECRET = b"zeromule-interbank-hmac-secret-2026"


def _pseudonymise(bank_id: str, account: str) -> str:
    key = _HMAC_SECRET + bank_id.encode()
    h = hmac.new(key, account.encode(), hashlib.sha256).hexdigest()
    return f"0x{h[:4]}..{h[-4:]}"


def _pseudonymise_full(bank_id: str, account: str) -> str:
    key = _HMAC_SECRET + bank_id.encode()
    return hmac.new(key, account.encode(), hashlib.sha256).hexdigest()


class Scorer:
    def __init__(self):
        self._bundle_meta = json.loads((BUNDLE_DIR / "bundle.json").read_text())
        self._preprocessing = json.loads((BUNDLE_DIR / "preprocessing.json").read_text())
        self._history_schema = json.loads(
            (BUNDLE_DIR / "historical_feature_schema.json").read_text()
        )
        self._ordered_features = json.loads(
            (BUNDLE_DIR / "ordered_feature_schema.json").read_text()
        )["ordered_features"]
        self.threshold: float = self._bundle_meta["threshold"]
        self.model_version: str = self._bundle_meta["model_version"]
        self._booster = lgb.Booster(model_file=str(BUNDLE_DIR / "booster.txt"))
        self._cat_lookups = {
            k: {s: i for i, s in enumerate(v)}
            for k, v in self._preprocessing["categories"].items()
        }
        self._init_db()

    def _init_db(self):
        con = sqlite3.connect(str(DB_PATH))
        con.execute("""
            CREATE TABLE IF NOT EXISTS tx_history (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                ts            REAL NOT NULL,
                sender_bank   TEXT NOT NULL,
                sender_acct   TEXT NOT NULL,
                receiver_bank TEXT NOT NULL,
                receiver_acct TEXT NOT NULL,
                amount_paid   REAL NOT NULL,
                pay_currency  TEXT NOT NULL,
                recv_currency TEXT NOT NULL
            )
        """)
        con.commit()
        con.close()

    def _compute_history(
        self,
        con: sqlite3.Connection,
        ts: float,
        sender_bank: str,
        sender_acct: str,
        receiver_bank: str,
        receiver_acct: str,
        amount_paid: float,
        pay_currency: str,
    ) -> dict:
        window_start = ts - 86400.0

        row = con.execute(
            "SELECT COUNT(*), SUM(amount_paid) FROM tx_history "
            "WHERE ts >= ? AND ts < ? AND sender_bank=? AND sender_acct=? AND pay_currency=?",
            (window_start, ts, sender_bank, sender_acct, pay_currency),
        ).fetchone()
        sender_out_count_24h = row[0] or 0
        sender_out_amount_24h = row[1] or 0.0

        row2 = con.execute(
            "SELECT COUNT(*), SUM(amount_paid) FROM tx_history "
            "WHERE ts >= ? AND ts < ? AND receiver_bank=? AND receiver_acct=? AND recv_currency=?",
            (window_start, ts, receiver_bank, receiver_acct, pay_currency),
        ).fetchone()
        receiver_in_count_24h = row2[0] or 0
        receiver_in_amount_24h = row2[1] or 0.0

        prev_row = con.execute(
            "SELECT ts FROM tx_history "
            "WHERE ts < ? AND sender_bank=? AND sender_acct=? "
            "ORDER BY ts DESC LIMIT 1",
            (ts, sender_bank, sender_acct),
        ).fetchone()
        sender_seconds_since_prev: Optional[float] = None
        if prev_row:
            sender_seconds_since_prev = ts - prev_row[0]

        pair_row = con.execute(
            "SELECT COUNT(*) FROM tx_history "
            "WHERE ts < ? AND sender_bank=? AND sender_acct=? "
            "AND receiver_bank=? AND receiver_acct=?",
            (ts, sender_bank, sender_acct, receiver_bank, receiver_acct),
        ).fetchone()
        pair_prior_count = pair_row[0] or 0
        is_new_counterparty = 1 if pair_prior_count == 0 else 0

        mean_row = con.execute(
            "SELECT AVG(amount_paid) FROM tx_history "
            "WHERE ts < ? AND sender_bank=? AND sender_acct=? AND pay_currency=?",
            (ts, sender_bank, sender_acct, pay_currency),
        ).fetchone()
        prior_mean = mean_row[0] if mean_row and mean_row[0] else None
        ratio: Optional[float] = None
        if prior_mean and prior_mean > 0:
            ratio = amount_paid / prior_mean

        return {
            "sender_out_count_24h": sender_out_count_24h,
            "sender_out_amount_24h_same_currency": sender_out_amount_24h,
            "receiver_in_count_24h": receiver_in_count_24h,
            "receiver_in_amount_24h_same_currency": receiver_in_amount_24h,
            "sender_seconds_since_previous_outgoing": sender_seconds_since_prev,
            "pair_prior_count": pair_prior_count,
            "is_new_counterparty": is_new_counterparty,
            "sender_amount_over_prior_mean_same_currency": ratio,
        }

    def _build_vector(
        self,
        ts_dt: datetime,
        amount_paid: float,
        amount_received: float,
        payment_currency: str,
        receiving_currency: str,
        payment_format: str,
        history: dict,
    ) -> list:
        cat = self._cat_lookups
        tx_vec = [
            amount_paid,
            amount_received,
            math.log1p(amount_paid),
            math.log1p(amount_received),
            ts_dt.hour,
            ts_dt.weekday(),
            ts_dt.day,
            cat["payment_currency"].get(payment_currency, -1),
            cat["receiving_currency"].get(receiving_currency, -1),
            cat["payment_format"].get(payment_format, -1),
        ]
        hist_vec = []
        for field in self._history_schema["fields"]:
            v = history[field["name"]]
            hist_vec.append(float("nan") if v is None else float(v))
        return tx_vec + hist_vec

    def score(
        self,
        transaction_id: str,
        timestamp: str,
        from_bank_label: str,
        sender_account: str,
        to_bank_label: str,
        receiver_account: str,
        amount_paid: float,
        amount_received: float,
        payment_currency: str,
        receiving_currency: str,
        payment_format: str,
    ) -> dict:
        ts_dt = datetime.fromisoformat(timestamp)
        ts_unix = ts_dt.timestamp()
        sender_bank_id = BANK_LABEL_TO_ID.get(from_bank_label, from_bank_label)
        receiver_bank_id = BANK_LABEL_TO_ID.get(to_bank_label, to_bank_label)

        t0 = time.perf_counter()
        con = sqlite3.connect(str(DB_PATH))
        try:
            history = self._compute_history(
                con, ts_unix, sender_bank_id, sender_account,
                receiver_bank_id, receiver_account, amount_paid, payment_currency,
            )
            vec = self._build_vector(
                ts_dt, amount_paid, amount_received,
                payment_currency, receiving_currency, payment_format, history,
            )
            x = np.array([vec], dtype="float64")
            raw_score = float(self._booster.predict(x, num_threads=2)[0])
            latency_ms = (time.perf_counter() - t0) * 1000

            con.execute(
                "INSERT INTO tx_history "
                "(ts, sender_bank, sender_acct, receiver_bank, receiver_acct, "
                "amount_paid, pay_currency, recv_currency) VALUES (?,?,?,?,?,?,?,?)",
                (ts_unix, sender_bank_id, sender_account,
                 receiver_bank_id, receiver_account,
                 amount_paid, payment_currency, receiving_currency),
            )
            con.commit()
        finally:
            con.close()

        is_alert = raw_score >= self.threshold
        if is_alert:
            decision = "PRE-SETTLEMENT FREEZE"
            status = "frozen"
        elif raw_score >= 0.04:
            decision = "ENCLAVE REVIEW"
            status = "review"
        else:
            decision = "SETTLEMENT APPROVED"
            status = "approved"

        is_cross_bank = sender_bank_id != receiver_bank_id
        pseudo_short = _pseudonymise(sender_bank_id, sender_account)
        pseudo_full = _pseudonymise_full(sender_bank_id, sender_account)
        from_display = BANK_LABEL_TO_DISPLAY.get(from_bank_label, from_bank_label.upper())
        to_display = BANK_LABEL_TO_DISPLAY.get(to_bank_label, to_bank_label.upper())

        return {
            "transaction_id": transaction_id,
            "timestamp": timestamp,
            "risk_score": round(raw_score, 4),
            "alert": is_alert,
            "threshold": self.threshold,
            "decision": decision,
            "status": status,
            "hmac_pseudonym_short": pseudo_short,
            "hmac_pseudonym_full": pseudo_full,
            "is_cross_bank": is_cross_bank,
            "from_bank": from_bank_label,
            "to_bank": to_bank_label,
            "from_bank_display": from_display,
            "to_bank_display": to_display,
            "amount_paid": amount_paid,
            "amount_received": amount_received,
            "payment_currency": payment_currency,
            "receiving_currency": receiving_currency,
            "payment_format": payment_format,
            "sender_account": sender_account,
            "receiver_account": receiver_account,
            "latency_ms": round(latency_ms, 2),
            "model_version": self.model_version,
            "historical_features": history,
        }
