"""
Central Enclave Hub & Boundary Graph Aggregator (ZeroMule).

Simulates the confidential computing environment (e.g., IBM Secure Execution / Enclave):
1. Ingests blinded transaction hashes from participant banks.
2. Performs cryptographic PSI matching to identify boundary bridges.
3. Ingests DP-perturbed boundary node embeddings from local GINs.
4. Stitches the unified cross-bank boundary directed multigraph.
5. Executes Boundary GAT + Contrastive Cycle Risk Scoring.
"""

from typing import Dict, List, Tuple, Set, Optional
import numpy as np
import pandas as pd
import torch
import torch.nn as nn

from src.privacy.psi_hasher import PSIHasher, CentralPSICoordinator
from src.privacy.dp_perturbation import DPPerturbation, RDPAccountant
from src.models.gat_boundary import BoundaryGATNet
from src.models.contrastive_head import ContrastiveCycleClassifier


class EnclaveAggregator(nn.Module):
    """
    Coordinator module inside the confidential enclave.
    """
    def __init__(self, embedding_dim: int = 128, gat_heads: int = 4, seed: int = 42):
        super().__init__()
        self.embedding_dim = embedding_dim
        self.gat = BoundaryGATNet(in_features=embedding_dim, hidden_dim=embedding_dim, num_heads=gat_heads)
        self.classifier = ContrastiveCycleClassifier(in_features=embedding_dim, projection_dim=64)

        self.hasher = PSIHasher()
        self.psi_coord = CentralPSICoordinator()
        self.dp_engine = DPPerturbation(clip_norm=1.0, sigma=1.25, seed=seed)
        self.rdp_accountant = RDPAccountant()

    def process_cross_bank_transactions(
        self,
        df_boundary: pd.DataFrame,
        bank_node_embeddings: Dict[str, Dict[str, np.ndarray]],
        target_delta: float = 1e-5,
    ) -> Dict[str, any]:
        """
        End-to-end enclave execution:
        1. PSI boundary node matching.
        2. DP embedding clipping + noise perturbation.
        3. RDP budget tracking.
        4. GAT boundary attention + cycle classification.
        """
        # Step 1: PSI Boundary Discovery
        for bank_id, emb_map in bank_node_embeddings.items():
            acc_hashes = [self.hasher.hash_account(acc) for acc in emb_map.keys()]
            self.psi_coord.register_bank_hashes(bank_id, set(acc_hashes))

        # Boundary hashes that connect counterparties across banks
        intersections = self.psi_coord.find_cross_bank_intersections()
        boundary_hashes = self.psi_coord.get_all_boundary_hashes()

        # Step 2: Retrieve & Perturb Local Embeddings with DP
        perturbed_node_dict = {}
        all_raw_embs = []

        for bank_id, emb_map in bank_node_embeddings.items():
            for acc, emb in emb_map.items():
                acc_hash = self.hasher.hash_account(acc)
                all_raw_embs.append(emb)

        if all_raw_embs:
            raw_mat = np.array(all_raw_embs)
            perturbed_mat, dp_meta = self.dp_engine.perturb_embeddings(raw_mat)
            self.rdp_accountant.step(self.dp_engine.sigma, steps=1)
            spent_eps, spent_delta, opt_order = self.rdp_accountant.get_privacy_spent(target_delta)

            # Re-index into perturbed_node_dict
            idx = 0
            for bank_id, emb_map in bank_node_embeddings.items():
                for acc in emb_map.keys():
                    acc_hash = self.hasher.hash_account(acc)
                    perturbed_node_dict[acc_hash] = perturbed_mat[idx]
                    idx += 1
        else:
            spent_eps, spent_delta = 0.0, target_delta
            dp_meta = {}

        # Step 3: Stitch Enclave Boundary Subgraph
        # Map boundary transactions into graph tensor indices
        df_b = df_boundary.copy()
        df_b["src_hash"] = [self.hasher.hash_account(str(a)) for a in df_b["Account"]]
        df_b["dst_hash"] = [self.hasher.hash_account(str(a)) for a in df_b["Account.1"]]

        unique_hashes = sorted(list(set(df_b["src_hash"].tolist() + df_b["dst_hash"].tolist())))
        hash_to_idx = {h: i for i, h in enumerate(unique_hashes)}

        # Build node tensor X
        x_list = []
        for h in unique_hashes:
            if h in perturbed_node_dict:
                x_list.append(perturbed_node_dict[h])
            else:
                x_list.append(np.zeros(self.embedding_dim, dtype=np.float32))

        x_tensor = torch.tensor(np.array(x_list), dtype=torch.float32)

        src_indices = [hash_to_idx[h] for h in df_b["src_hash"]]
        dst_indices = [hash_to_idx[h] for h in df_b["dst_hash"]]
        edge_index = torch.tensor([src_indices, dst_indices], dtype=torch.long)

        # Step 4: GAT Boundary Processing + Anomaly Scoring
        self.eval()
        with torch.no_grad():
            gat_out, attn_weights = self.gat(x_tensor, edge_index)

            # Edge level representation: concatenated [h_src || h_dst]
            if edge_index.size(1) > 0:
                edge_rep = (gat_out[edge_index[0]] + gat_out[edge_index[1]]) / 2.0
                risk_scores, proj_embs = self.classifier(edge_rep)
            else:
                risk_scores = torch.empty(0)
                proj_embs = torch.empty((0, 64))

        df_b["enclave_risk_score"] = risk_scores.cpu().numpy()
        df_b["is_flagged_mule"] = (df_b["enclave_risk_score"] >= 0.50).astype(int)

        return {
            "scored_boundary_df": df_b,
            "privacy_metrics": {
                "epsilon_spent": spent_eps,
                "delta": spent_delta,
                "clip_norm_C": self.dp_engine.clip_norm,
                "sigma": self.dp_engine.sigma,
            },
            "psi_metrics": {
                "num_boundary_nodes": len(unique_hashes),
                "num_boundary_edges": len(df_b),
                "pairwise_intersections": {f"{k[0]}_x_{k[1]}": len(v) for k, v in intersections.items()},
            },
            "gat_node_embeddings": gat_out,
            "attention_weights": attn_weights,
        }
