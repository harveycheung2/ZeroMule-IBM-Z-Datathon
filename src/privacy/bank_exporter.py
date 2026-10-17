"""The only supported bank-to-coordinator release boundary."""

import copy
import json
import math
import re

import numpy as np
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from src.privacy.budget import PrivacyBudgetLedger
from src.privacy.dp_perturbation import DPPerturbation, DELTA, MAX_EPSILON, epsilon_for_rho, positive
from src.privacy.psi_hasher import PSIHasher, validate_token


def canonical_bytes(body):
    return json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


class BankPrivacyExporter:
    """Run inside one bank, with bank-only matching and signing keys.

    Each bank must use its sole authoritative ledger across all workers, models,
    datasets, key rotations and restarts. No seed or reset option is exposed.
    """

    def __init__(self, bank_id: str, ledger: PrivacyBudgetLedger,
                 signing_key: Ed25519PrivateKey, hasher=None, clip_norm=1.0, sigma=8.0):
        if not isinstance(bank_id, str) or not bank_id or ledger.bank_id != bank_id:
            raise ValueError("Exporter must use its bank's ledger")
        if not isinstance(signing_key, Ed25519PrivateKey):
            raise ValueError("A bank Ed25519 signing key is required")
        self.bank_id = bank_id
        self._ledger = ledger
        self._signing_key = signing_key
        self._hasher = hasher if hasher is not None else PSIHasher()
        self._dp = DPPerturbation(clip_norm, sigma)

    def export(self, records, embeddings):
        """Consume local {source_account, target_account, ...} records and ID map.

        The roster and topology are explicitly disclosed, pseudonymized inputs;
        Gaussian DP covers values only, conditional on this fixed public shape.
        """
        if not isinstance(embeddings, dict) or not embeddings:
            raise ValueError("A nonempty local embedding map is required")
        accounts = list(embeddings)
        tokens = self._hasher.hash_accounts(accounts)
        matrix = np.array([embeddings[a] for a in accounts], dtype=float)
        self._dp.clip_embeddings(matrix)  # Validate before charging the budget.
        edges = self._hasher.create_blinded_ledger_records(records, self.bank_id)
        known = set(tokens)
        if any(e["orig_account_hash"] not in known or e["dest_account_hash"] not in known for e in edges):
            raise ValueError("Every endpoint needs a local embedding")
        privacy = self._ledger.reserve(self._dp.sigma)
        protected, parameters = self._dp.perturb_embeddings(matrix)
        body = {"version": 1, "bank_id": self.bank_id,
                "embeddings": dict(zip(tokens, protected.tolist())),
                "edges": edges, "privacy": {**privacy, **parameters}}
        return {"body": body, "signature": self._signing_key.sign(canonical_bytes(body)).hex()}


def validate_protected_payload(payload, trusted_banks, embedding_dim):
    """Snapshot, authenticate and strictly validate a serialized protected payload.

    Signatures attest origin from a trusted bank exporter, not execution integrity
    on a compromised bank host. A schema alone cannot prove noise was applied.
    """
    if type(payload) is not dict or set(payload) != {"body", "signature"}:
        raise ValueError("Only signed protected payloads are accepted")
    try:
        payload = copy.deepcopy(payload)
        body = payload["body"]
        if type(body) is not dict or set(body) != {"version", "bank_id", "embeddings", "edges", "privacy"}:
            raise ValueError("Unexpected payload fields")
        bank = body["bank_id"]
        if type(body["version"]) is not int or body["version"] != 1 or not isinstance(bank, str):
            raise ValueError("Unsupported payload version/bank")
        key = trusted_banks.get(bank)
        if not isinstance(key, Ed25519PublicKey):
            raise ValueError("Untrusted bank")
        key.verify(bytes.fromhex(payload["signature"]), canonical_bytes(body))
        embeddings = body["embeddings"]
        if type(embeddings) is not dict or not embeddings:
            raise ValueError("Protected embeddings are required")
        for token, vector in embeddings.items():
            validate_token(token)
            if type(vector) is not list or len(vector) != embedding_dim:
                raise ValueError("Invalid protected embedding dimensions")
            if any(type(v) not in (int, float) or not math.isfinite(v) or abs(v) > np.finfo(np.float32).max for v in vector):
                raise ValueError("Invalid protected embedding values")
        if type(body["edges"]) is not list:
            raise ValueError("Invalid edges")
        for edge in body["edges"]:
            if type(edge) is not dict or set(edge) != {"orig_account_hash", "dest_account_hash", "originating_bank"}:
                raise ValueError("Unexpected edge fields; raw metadata is forbidden")
            if edge["originating_bank"] != bank:
                raise ValueError("Edge bank mismatch")
            for field in ("orig_account_hash", "dest_account_hash"):
                validate_token(edge[field])
                if edge[field] not in embeddings:
                    raise ValueError("Endpoint missing protected embedding")
        p = body["privacy"]
        if type(p) is not dict or set(p) != {"release_id", "epsilon_spent", "delta", "cumulative_rho", "clip_norm_C", "sigma", "noise_std"}:
            raise ValueError("Invalid privacy receipt")
        if not isinstance(p["release_id"], str) or re.fullmatch(r"[0-9a-f]{32}", p["release_id"]) is None:
            raise ValueError("Invalid release ID")
        for field in set(p) - {"release_id"}:
            if type(p[field]) not in (int, float):
                raise ValueError("Invalid privacy parameter type")
            positive(p[field], field)
        if p["delta"] != DELTA or p["epsilon_spent"] > MAX_EPSILON:
            raise ValueError("Invalid privacy budget")
        if p["cumulative_rho"] < 0.5 / p["sigma"] / p["sigma"]:
            raise ValueError("Underreported privacy cost")
        if not math.isclose(epsilon_for_rho(p["cumulative_rho"]), p["epsilon_spent"], rel_tol=1e-12):
            raise ValueError("Invalid cumulative privacy bound")
        if not math.isclose(p["noise_std"], 2 * p["clip_norm_C"] * p["sigma"], rel_tol=1e-12):
            raise ValueError("Invalid Gaussian parameters")
        return body
    except (InvalidSignature, TypeError, KeyError, OverflowError) as exc:
        raise ValueError("Invalid protected payload") from exc
