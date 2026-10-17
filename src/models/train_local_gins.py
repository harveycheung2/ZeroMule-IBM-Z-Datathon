"""
Local Directed-GIN Training and Checkpoint Pipeline for Bank A, Bank B, and Bank C.

Trains a bank-local Directed-Multigraph GIN encoder with:
- Focal Loss combating severe class imbalance (<0.1% positive laundering)
- Local account representations h_v in R^{128}
- Checkpoints model weights only in an explicitly provided bank-private directory
"""

from pathlib import Path
from typing import Dict, Tuple
import numpy as np
import torch
import torch.optim as optim
from sklearn.metrics import precision_recall_curve, auc, f1_score

from src.data.graph_builder import GraphBuilder
from src.models.directed_gin import DirectedGINEncoder, FocalLoss


def train_bank_gin(bank_name: str, graph_data, epochs: int = 15, lr: float = 0.005, *, bank_state_dir: Path) -> Tuple[DirectedGINEncoder, Dict[str, any]]:
    """
    Trains a local Directed-GIN instance on a bank's private graph.
    """
    bank_state_dir = Path(bank_state_dir)
    bank_state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    node_in_dim = graph_data.x.size(1)
    edge_in_dim = graph_data.edge_attr.size(1)

    model = DirectedGINEncoder(
        node_in_dim=node_in_dim,
        edge_in_dim=edge_in_dim,
        hidden_dim=128,
        num_layers=3,
        dropout=0.1,
    ).to(device)

    graph_data.to(device)
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    loss_fn = FocalLoss(alpha=0.85, gamma=2.0)

    labels = graph_data.y
    if labels is None:
        labels = torch.zeros(graph_data.edge_index.size(1), device=device)

    model.train()
    for ep in range(epochs):
        optimizer.zero_grad()
        _, edge_logits = model(graph_data.x, graph_data.edge_index, graph_data.edge_attr)
        loss = loss_fn(edge_logits, labels)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()

    # Evaluation
    model.eval()
    with torch.no_grad():
        node_embs, edge_logits = model(graph_data.x, graph_data.edge_index, graph_data.edge_attr)
        probs = torch.sigmoid(edge_logits).cpu().numpy()
        y_true = labels.cpu().numpy()

        p, r, _ = precision_recall_curve(y_true, probs)
        pr_auc = auc(r, p) if len(np.unique(y_true)) > 1 else 0.50
        f1 = f1_score(y_true, (probs >= 0.5).astype(int), zero_division=0)

    # Save checkpoint
    ckpt_path = bank_state_dir / f"{bank_name.lower()}_gin.pt"
    torch.save({
        "bank_name": bank_name,
        "state_dict": model.state_dict(),
        "node_in_dim": node_in_dim,
        "edge_in_dim": edge_in_dim,
        "hidden_dim": 128,
        "pr_auc": float(pr_auc),
        "f1": float(f1),
    }, ckpt_path)

    # Bank-local memory only; raw embeddings must never be sent to the coordinator.
    emb_dict = {}
    node_embs_np = node_embs.cpu().numpy()
    for idx, acc in graph_data.rev_node_map.items():
        emb_dict[acc] = node_embs_np[idx]

    print(f"[{bank_name} Directed-GIN Trained]")
    print(f"  [OK] Local Graph PR-AUC: {pr_auc:.4f} (Intra-bank flow captured)")
    print(f"  [OK] Checkpoint saved:   {ckpt_path}")

    return model, emb_dict


def train_and_export_bank(bank_name, local_ledger, exporter, bank_state_dir, epochs=15):
    """Execute within a single bank; return only a protected coordinator payload.

    local_ledger is the bank's own DataFrame, never a centrally gathered ledger.
    Checkpoints remain within the bank-controlled state directory.
    """
    if exporter.bank_id != bank_name:
        raise ValueError("Bank/exporter mismatch")
    graph = GraphBuilder().build_graph_from_df(local_ledger)
    _, local_embeddings = train_bank_gin(bank_name, graph, epochs=epochs,
                                         bank_state_dir=bank_state_dir)
    boundary = local_ledger[local_ledger["From Bank"] != local_ledger["To Bank"]]
    records = [{"source_account": str(row["Account"]),
                "target_account": str(row["Account.1"])}
               for row in boundary.to_dict("records")]
    endpoints = {r[field] for r in records for field in ("source_account", "target_account")}
    boundary_embeddings = {str(a): v for a, v in local_embeddings.items() if str(a) in endpoints}
    return exporter.export(records, boundary_embeddings)


if __name__ == "__main__":
    raise SystemExit("Run train_and_export_bank inside each bank with configured keys, "
                     "a provisioned privacy ledger and a bank-private state directory. "
                     "See docs/privacy-architecture.md.")
