"""
Local Directed-GIN Training Framework for ZeroMule-IBM-Z-Datathon.

Orchestrates local Directed-Multigraph GIN training across bank silos:
- Applies Focal Loss for extreme AML class imbalance (<0.1% positive laundering)
- Generates private node representations h_v
- Prepares privacy-preserving boundary embeddings for enclave transmission
"""

from pathlib import Path
from typing import Dict, Optional, Tuple
import torch
import torch.optim as optim

from src.models.directed_gin import DirectedGINEncoder, FocalLoss


class LocalBankTrainer:
    """
    Manages local training lifecycle for an isolated financial institution.
    """

    def __init__(
        self,
        bank_id: str,
        node_in_dim: int = 16,
        edge_in_dim: int = 24,
        hidden_dim: int = 64,
        device: Optional[str] = None
    ):
        self.bank_id = bank_id
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        self.model = DirectedGINEncoder(
            node_in_dim=node_in_dim,
            edge_in_dim=edge_in_dim,
            hidden_dim=hidden_dim,
            num_layers=3,
            dropout=0.1,
        ).to(self.device)
        self.loss_fn = FocalLoss(alpha=0.85, gamma=2.0)
        self.optimizer = optim.AdamW(self.model.parameters(), lr=0.005, weight_decay=1e-4)

    def train_epoch(self, graph_data) -> float:
        """
        Executes a single training epoch over local private transactions.
        """
        if graph_data is None:
            raise ValueError(f"No graph data available for bank {self.bank_id}.")
        self.model.train()
        self.optimizer.zero_grad()
        _, edge_logits = self.model(graph_data.x, graph_data.edge_index, graph_data.edge_attr)
        loss = self.loss_fn(edge_logits, graph_data.y)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
        self.optimizer.step()
        return float(loss.item())

    def export_boundary_embeddings(self, graph_data, boundary_indices: torch.Tensor) -> torch.Tensor:
        """
        Extracts node embeddings for boundary counterparties intended for differentially private export.
        """
        self.model.eval()
        with torch.no_grad():
            node_embs, _ = self.model(graph_data.x, graph_data.edge_index, graph_data.edge_attr)
        return node_embs[boundary_indices]


def run_training_framework_check():
    print("=" * 60)
    print("  ZeroMule-IBM-Z-Datathon: Training Pipeline Framework")
    print("=" * 60)
    trainer = LocalBankTrainer(bank_id="Bank_A")
    print(f"  [Ready] Initialized Directed-GIN trainer for Bank_A on {trainer.device}.")
    print("  [Ready] Architecture initialized with Focal Loss (alpha=0.85, gamma=2.0).")
    print("=" * 60)


if __name__ == "__main__":
    run_training_framework_check()
