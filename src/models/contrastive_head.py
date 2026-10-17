"""
Self-Supervised Contrastive Cycle Classifier & Topology Anomaly Scorer.

Implements:
1. InfoNCE Subgraph Contrastive Loss:
   Encourages circular/ring-like topological representations to cluster tightly in latent space
   while separating dispersed linear benign payroll transfers.
2. Lightweight Multi-Layer Perceptron (MLP) Anomaly Scoring Head:
   Outputs calibrated risk probability S in [0, 1] for real-time AML intervention.
"""

from typing import Tuple, Optional
import torch
import torch.nn as nn
import torch.nn.functional as F


class InfoNCELoss(nn.Module):
    """
    InfoNCE Contrastive Loss:
    L = -log( exp(sim(q, k_pos) / tau) / (exp(sim(q, k_pos) / tau) + sum_neg exp(sim(q, k_neg) / tau)) )
    """
    def __init__(self, temperature: float = 0.07):
        super().__init__()
        self.temperature = temperature

    def forward(self, query: torch.Tensor, positive: torch.Tensor, negatives: torch.Tensor) -> torch.Tensor:
        """
        query: [batch_size, dim]
        positive: [batch_size, dim]
        negatives: [batch_size, num_negatives, dim] or [num_negatives, dim]
        """
        q_norm = F.normalize(query, dim=-1)
        p_norm = F.normalize(positive, dim=-1)

        # Positive logits: [batch_size, 1]
        pos_sim = (q_norm * p_norm).sum(dim=-1, keepdim=True) / self.temperature

        # Negative logits
        if negatives.dim() == 2:
            n_norm = F.normalize(negatives, dim=-1)
            neg_sim = torch.matmul(q_norm, n_norm.t()) / self.temperature
        else:
            n_norm = F.normalize(negatives, dim=-1)
            neg_sim = torch.bmm(n_norm, q_norm.unsqueeze(-1)).squeeze(-1) / self.temperature

        logits = torch.cat([pos_sim, neg_sim], dim=-1)
        labels = torch.zeros(logits.size(0), dtype=torch.long, device=logits.device)
        return F.cross_entropy(logits, labels)


class ContrastiveCycleClassifier(nn.Module):
    """
    Contrastive Topology Classifier & Risk Prediction Head for IBM Enclave Coordinator.
    """
    def __init__(self, in_features: int = 128, projection_dim: int = 64, temperature: float = 0.07):
        super().__init__()
        self.in_features = in_features
        self.projection_dim = projection_dim

        # Contrastive projector (for InfoNCE representation alignment)
        self.projector = nn.Sequential(
            nn.Linear(in_features, projection_dim),
            nn.ReLU(),
            nn.Linear(projection_dim, projection_dim),
        )

        # Anomaly scoring head: S in [0, 1]
        self.risk_head = nn.Sequential(
            nn.Linear(in_features, 64),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
        )

        self.info_nce = InfoNCELoss(temperature=temperature)

    def project(self, x: torch.Tensor) -> torch.Tensor:
        """
        Project embeddings to contrastive metric space.
        """
        return F.normalize(self.projector(x), dim=-1)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Returns:
            scores: Anomaly probabilities S in [0, 1]
            projections: Unit-norm contrastive feature embeddings
        """
        proj = self.project(x)
        logits = self.risk_head(x).squeeze(-1)
        scores = torch.sigmoid(logits)
        return scores, proj

    def compute_contrastive_loss(
        self, anchor_emb: torch.Tensor, pos_cycle_emb: torch.Tensor, neg_linear_emb: torch.Tensor
    ) -> torch.Tensor:
        q = self.projector(anchor_emb)
        k_pos = self.projector(pos_cycle_emb)
        k_neg = self.projector(neg_linear_emb)
        return self.info_nce(q, k_pos, k_neg)
