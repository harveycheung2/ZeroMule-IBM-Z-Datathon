"""
Private Set Intersection (PSI) using Salted HMAC-SHA256.

Allows multiple banking entities (e.g., Bank A, Bank B, Bank C) to cooperatively
identify cross-bank boundary accounts without revealing internal customer IDs,
balances, or PII to other participants or the coordinator.
"""

import hmac
import hashlib
from typing import Dict, List, Set, Tuple


class PSIHasher:
    """
    Cryptographic PSI Hasher leveraging HMAC-SHA256 with an ephemeral or shared salt.
    """

    def __init__(self, salt: bytes = b"zeromule_datathon_secret_salt_2026"):
        """
        Initialize hasher with a cryptographic salt agreed upon via secure key exchange.
        """
        self.salt = salt

    def hash_account(self, account_id: str) -> str:
        """
        Compute HMAC-SHA256 hash of an account ID.
        """
        h = hmac.new(self.salt, account_id.encode("utf-8"), hashlib.sha256)
        return h.hexdigest()

    def hash_accounts(self, account_ids: List[str]) -> List[str]:
        """
        Hash a list of account IDs.
        """
        return [self.hash_account(acc) for acc in account_ids]

    def create_blinded_ledger_records(
        self, records: List[Dict[str, any]], bank_id: str
    ) -> List[Dict[str, any]]:
        """
        Blinds account identifiers before transmission to the central enclave coordinator.
        Raw account IDs are replaced by salted hashes.
        """
        blinded = []
        for r in records:
            item = dict(r)
            item["orig_account_hash"] = self.hash_account(str(r["source_account"]))
            item["dest_account_hash"] = self.hash_account(str(r["target_account"]))
            item["originating_bank"] = bank_id
            # Redact raw accounts
            item.pop("source_account", None)
            item.pop("target_account", None)
            blinded.append(item)
        return blinded


class CentralPSICoordinator:
    """
    Central Enclave Coordinator matching blinded hashes across banks.
    """

    def __init__(self):
        self.bank_hash_sets: Dict[str, Set[str]] = {}

    def register_bank_hashes(self, bank_id: str, account_hashes: Set[str]):
        """
        Register blinded hashes sent by a participant bank.
        """
        self.bank_hash_sets[bank_id] = set(account_hashes)

    def find_cross_bank_intersections(self) -> Dict[Tuple[str, str], Set[str]]:
        """
        Compute pairwise intersections between banks to find bridge/boundary nodes.
        """
        intersections = {}
        banks = list(self.bank_hash_sets.keys())
        for i in range(len(banks)):
            for j in range(i + 1, len(banks)):
                b1, b2 = banks[i], banks[j]
                shared = self.bank_hash_sets[b1].intersection(self.bank_hash_sets[b2])
                intersections[(b1, b2)] = shared
        return intersections

    def get_all_boundary_hashes(self) -> Set[str]:
        """
        Returns all unique account hashes that appear in cross-bank boundary activities.
        """
        boundary = set()
        intersections = self.find_cross_bank_intersections()
        for common in intersections.values():
            boundary.update(common)
        return boundary
