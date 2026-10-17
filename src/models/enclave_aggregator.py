"""Protected-payload coordinator simulation; hardware attestation is external."""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

from src.privacy.bank_exporter import validate_protected_payload
from src.privacy.psi_hasher import CentralPSICoordinator
from src.models.gat_boundary import BoundaryGATNet
from src.models.contrastive_head import ContrastiveCycleClassifier


class EnclaveAggregator(nn.Module):
    """Accept signed bank exports only; never handles matching keys or raw data."""

    def __init__(self, trusted_banks, embedding_dim=128, gat_heads=4):
        super().__init__()
        if not trusted_banks:
            raise ValueError("Pinned bank verification keys are required")
        self.trusted_banks = dict(trusted_banks)
        self.embedding_dim = embedding_dim
        self.gat = BoundaryGATNet(in_features=embedding_dim, hidden_dim=embedding_dim, num_heads=gat_heads)
        self.classifier = ContrastiveCycleClassifier(in_features=embedding_dim, projection_dim=64)

    def process_cross_bank_transactions(self, protected_payloads):
        if type(protected_payloads) not in (list, tuple) or not protected_payloads:
            raise ValueError("A nonempty sequence of protected bank payloads is required")
        bodies = [validate_protected_payload(p, self.trusted_banks, self.embedding_dim)
                  for p in protected_payloads]
        banks = [b["bank_id"] for b in bodies]
        if len(set(banks)) != len(banks):
            raise ValueError("Only one release per bank is allowed in an inference batch")
        # All validation precedes graph processing. Matching state is request-local.
        coordinator = CentralPSICoordinator()
        vectors, edges = {}, []
        for body in bodies:
            coordinator.register_bank_hashes(body["bank_id"], set(body["embeddings"]))
            for token, vector in body["embeddings"].items():
                vectors.setdefault(token, []).append(vector)
            edges.extend(body["edges"])
        tokens = sorted(vectors)
        indices = {token: index for index, token in enumerate(tokens)}
        # Multiple noisy estimates of the same pseudonym are post-processing.
        x = torch.tensor(np.array([np.mean(vectors[t], axis=0) for t in tokens]), dtype=torch.float32)
        edge_index = torch.tensor([[indices[e["orig_account_hash"]] for e in edges],
                                   [indices[e["dest_account_hash"]] for e in edges]], dtype=torch.long)
        device = next(self.parameters()).device
        x, edge_index = x.to(device), edge_index.to(device)
        self.eval()
        with torch.no_grad():
            gat_out, attention = self.gat(x, edge_index)
            if edges:
                edge_rep = (gat_out[edge_index[0]] + gat_out[edge_index[1]]) / 2
                scores, _ = self.classifier(edge_rep)
            else:
                scores = torch.empty(0, device=device)
        scored = pd.DataFrame(edges, columns=["orig_account_hash", "dest_account_hash", "originating_bank"])
        scored["enclave_risk_score"] = scores.cpu().numpy().reshape(-1)
        scored["is_flagged_mule"] = (scored["enclave_risk_score"] >= 0.5).astype(int)
        return {"scored_boundary_df": scored,
                "privacy_metrics": {b["bank_id"]: b["privacy"] for b in bodies},
                "matching_metrics": {
                    "num_boundary_nodes": len(tokens), "num_boundary_edges": len(edges),
                    "pairwise_intersections": {f"{a}_x_{b}": len(v) for (a, b), v in coordinator.find_cross_bank_intersections().items()}},
                "gat_node_embeddings": gat_out, "attention_weights": attention}
