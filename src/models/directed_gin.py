"""
Directed-Multigraph Graph Isomorphism Network (Directed-GIN).

Implements asymmetric directed message passing separating incoming and outgoing neighborhoods:
h_v^{(l)} = MLP^{(l)}(
    (1 + eps) * h_v^{(l-1)}
    + sum_{u in N_in(v)} W_in( [h_u^{(l-1)} || e_{uv}] )
    + sum_{w in N_out(v)} W_out( [h_w^{(l-1)} || e_{vw}] )
)

Includes:
- Learnable epsilon parameter per layer
- Projection layers W_in, W_out for edge-conditioned message passing
- Residual skip connections and LayerNorm for stable deep propagation
- Focal loss for extreme AML class imbalance (<0.1% positive laundering)
"""

import math
from typing import Tuple, Optional
import torch
import torch.nn as nn
import torch.nn.functional as F


class FocalLoss(nn.Module):
    """
    Focal Loss to combat extreme positive class imbalance:
    FL(p_t) = -alpha_t * (1 - p_t)^gamma * log(p_t)
    """
    def __init__(self, alpha: float = 0.85, gamma: float = 2.0, reduction: str = "mean"):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.reduction = reduction

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        bce_loss = F.binary_cross_entropy_with_logits(logits, targets, reduction="none")
        probs = torch.sigmoid(logits)
        p_t = targets * probs + (1 - targets) * (1 - probs)
        alpha_factor = targets * self.alpha + (1 - targets) * (1 - self.alpha)
        focal_weight = alpha_factor * ((1.0 - p_t) ** self.gamma)
        loss = focal_weight * bce_loss
        if self.reduction == "mean":
            return loss.mean()
        elif self.reduction == "sum":
            return loss.sum()
        return loss


class DirectedGINLayer(nn.Module):
    """
    Single Directed-GIN message passing layer.
    """
    def __init__(self, in_features: int, edge_features: int, out_features: int, eps: float = 0.0, learn_eps: bool = True):
        super().__init__()
        self.in_features = in_features
        self.edge_features = edge_features
        self.out_features = out_features

        if learn_eps:
            self.eps = nn.Parameter(torch.Tensor([eps]))
        else:
            self.register_buffer("eps", torch.Tensor([eps]))

        # Projection for incoming messages: [h_u || e_{uv}]
        self.w_in = nn.Linear(in_features + edge_features, out_features, bias=False)
        # Projection for outgoing messages: [h_w || e_{vw}]
        self.w_out = nn.Linear(in_features + edge_features, out_features, bias=False)

        # 2-layer MLP as required by GIN
        self.mlp = nn.Sequential(
            nn.Linear(out_features, out_features * 2),
            nn.LayerNorm(out_features * 2),
            nn.ReLU(),
            nn.Linear(out_features * 2, out_features),
            nn.LayerNorm(out_features),
        )

        # Residual shortcut if dimensions match or linear projection if they differ
        if in_features != out_features:
            self.shortcut = nn.Linear(in_features, out_features)
        else:
            self.shortcut = nn.Identity()

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor, edge_attr: torch.Tensor) -> torch.Tensor:
        """
        x: [num_nodes, in_features]
        edge_index: [2, num_edges] (row 0: src, row 1: dst)
        edge_attr: [num_edges, edge_features]
        """
        num_nodes = x.size(0)
        src = edge_index[0]
        dst = edge_index[1]

        # 1. Incoming neighborhood message aggregation for v (where v is dst):
        # sender is u = src, edge is u -> v
        in_msg_input = torch.cat([x[src], edge_attr], dim=-1)
        in_msg = self.w_in(in_msg_input)
        agg_in = torch.zeros((num_nodes, self.out_features), device=x.device, dtype=x.dtype)
        agg_in.index_add_(0, dst, in_msg)

        # 2. Outgoing neighborhood message aggregation for v (where v is src):
        # receiver is w = dst, edge is v -> w
        out_msg_input = torch.cat([x[dst], edge_attr], dim=-1)
        out_msg = self.w_out(out_msg_input)
        agg_out = torch.zeros((num_nodes, self.out_features), device=x.device, dtype=x.dtype)
        agg_out.index_add_(0, src, out_msg)

        # 3. Central node transformation: (1 + eps) * shortcut(x_v)
        self_x = self.shortcut(x)
        combined = (1.0 + self.eps) * self_x + agg_in + agg_out

        # 4. GIN MLP transformation + residual connection
        out = self.mlp(combined) + self_x
        return F.relu(out)


class DirectedGINEncoder(nn.Module):
    """
    Multi-layer Directed-GIN Encoder producing node and edge representations.
    """
    def __init__(
        self,
        node_in_dim: int = 7,
        edge_in_dim: int = 19,
        hidden_dim: int = 128,
        num_layers: int = 3,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.node_in_dim = node_in_dim
        self.edge_in_dim = edge_in_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers

        # Node feature initial projection
        self.node_emb = nn.Sequential(
            nn.Linear(node_in_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
        )

        # Edge feature projection
        self.edge_proj = nn.Sequential(
            nn.Linear(edge_in_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
        )

        # Stack of Directed-GIN Layers
        self.layers = nn.ModuleList([
            DirectedGINLayer(
                in_features=hidden_dim,
                edge_features=hidden_dim,
                out_features=hidden_dim,
                learn_eps=True,
            )
            for _ in range(num_layers)
        ])
        self.dropout = nn.Dropout(dropout)

        # Edge classification head (for local transaction risk scoring)
        self.edge_classifier = nn.Sequential(
            nn.Linear(hidden_dim * 3, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )

    def forward_nodes(self, x: torch.Tensor, edge_index: torch.Tensor, edge_attr: torch.Tensor) -> torch.Tensor:
        """
        Computes node representations h_v in R^{128} across all nodes.
        """
        h = self.node_emb(x)
        e = self.edge_proj(edge_attr)

        for layer in self.layers:
            h = layer(h, edge_index, e)
            h = self.dropout(h)
        return h

    def forward(
        self, x: torch.Tensor, edge_index: torch.Tensor, edge_attr: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Returns:
            node_embeddings: [num_nodes, hidden_dim]
            edge_logits: [num_edges, 1]
        """
        h = self.forward_nodes(x, edge_index, edge_attr)
        e = self.edge_proj(edge_attr)

        # Score edges based on concatenated [h_src || h_dst || e_attr]
        src, dst = edge_index[0], edge_index[1]
        edge_cat = torch.cat([h[src], h[dst], e], dim=-1)
        edge_logits = self.edge_classifier(edge_cat).squeeze(-1)
        return h, edge_logits
