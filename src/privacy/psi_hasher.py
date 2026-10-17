"""Bank-side keyed pseudonyms and equality matching; not cryptographic PSI."""

import base64
import hashlib
import hmac
import os
import re
from typing import Dict, List, Set, Tuple


def validate_token(value):
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError("Expected an HMAC-SHA256 pseudonym")


class PSIHasher:
    """Legacy class name for deterministic HMAC matching. Keys stay at banks."""

    def __init__(self, key: bytes = None):
        if key is None:
            encoded = os.environ.get("ZEROMULE_HMAC_KEY_B64")
            if not encoded:
                raise ValueError("ZEROMULE_HMAC_KEY_B64 is required")
            try:
                key = base64.b64decode(encoded, validate=True)
            except (ValueError, TypeError) as exc:
                raise ValueError("Invalid base64 HMAC key") from exc
        if not isinstance(key, bytes) or len(key) < 32:
            raise ValueError("HMAC key must contain at least 32 random bytes")
        self._key = key

    def hash_account(self, account_id: str) -> str:
        if not isinstance(account_id, str) or not account_id:
            raise ValueError("Account IDs must be nonempty strings")
        return hmac.new(self._key, b"zeromule/account/v1\x00" + account_id.encode(), hashlib.sha256).hexdigest()

    def hash_accounts(self, account_ids: List[str]) -> List[str]:
        return [self.hash_account(acc) for acc in account_ids]

    def create_blinded_ledger_records(self, records: List[dict], bank_id: str) -> List[dict]:
        """Allowlist only endpoints; amounts, timestamps, labels and extra PII never leave."""
        if not isinstance(bank_id, str) or not bank_id:
            raise ValueError("A bank ID is required")
        return [{"orig_account_hash": self.hash_account(r["source_account"]),
                 "dest_account_hash": self.hash_account(r["target_account"]),
                 "originating_bank": bank_id} for r in records]


class CentralPSICoordinator:
    """Legacy name for pseudonym intersection, revealing equality and membership."""

    def __init__(self):
        self.bank_hash_sets: Dict[str, Set[str]] = {}

    def register_bank_hashes(self, bank_id: str, account_hashes: Set[str]):
        tokens = set(account_hashes)
        for token in tokens:
            validate_token(token)
        self.bank_hash_sets[bank_id] = tokens

    def find_cross_bank_intersections(self) -> Dict[Tuple[str, str], Set[str]]:
        banks = list(self.bank_hash_sets)
        return {(b1, b2): self.bank_hash_sets[b1] & self.bank_hash_sets[b2]
                for i, b1 in enumerate(banks) for b2 in banks[i + 1:]}

    def get_all_boundary_hashes(self) -> Set[str]:
        return set().union(*self.find_cross_bank_intersections().values())
