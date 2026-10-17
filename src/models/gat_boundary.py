"""
Graph Attention Network (GAT) for Cross-Bank Boundary Subgraph.

Processes DP-perturbed node embeddings across boundary bridges:
- Computes attention coefficients between inter-bank counterparties
- Weights suspicious cross-bank transaction bridges
- Propagates boundary context inside the simulated IBM secure enclave
"""

import math
from typing import Tuple, Optional
import torch
import torch.nn as nn
import torch.nn.functional as F


class BoundaryGATLayer(nn.Module):
    """
    Multi-head Graph Attention Layer for boundary transaction edges.
    """
    def __init__(self, in_features: int, out_features: int, num_heads: int = 4, dropout: float = 0.1, alpha: float = 0.2):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.num_heads = num_heads
        self.head_dim = out_features // num_heads
        self.dropout = dropout
        self.leaky_relu = nn.LeakyReLU(alpha)

        self.w_src = nn.Linear(in_features, out_features, bias=False)
        self.w_dst = nn.Linear(in_features, out_features, bias=False)
        self.attn_vec = nn.Parameter(torch.empty(size=(num_heads, 2 * self.head_dim)))
        nn.init.xavier_uniform_(self.attn_vec)

        self.shortcut = nn.Linear(in_features, out_features) if in_features != out_features else nn.Identity()
        self.norm = nn.LayerNorm(out_features)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        x: [num_nodes, in_features]
        edge_index: [2, num_edges] (src, dst)
        """
        num_nodes = x.size(0)
        num_edges = edge_index.size(1)

        src, dst = edge_index[0], edge_index[1]

        h_src = self.w_src(x).view(-1, self.num_heads, self.head_dim)
        h_dst = self.w_dst(x).view(-1, self.num_heads, self.head_dim)

        if num_edges == 0:
            return self.norm(self.shortcut(x)), torch.zeros((0, self.num_heads), device=x.device)

        # Pairwise attention logits on edges
        edge_src_h = h_src[src]  # [num_edges, heads, head_dim]
        edge_dst_h = h_dst[dst]  # [num_edges, heads, head_dim]
        edge_cat = torch.cat([edge_src_h, edge_dst_h], dim=-1)  # [num_edges, heads, 2*head_dim]

        # Dot product with attention vector
        scores = (edge_cat * self.attn_vec).sum(dim=-1)  # [num_edges, heads]
        scores = self.leaky_relu(scores)

        # Softmax over incoming edges for each dst node
        # Compute numerically stable softmax per head
        alpha_weights = torch.zeros_like(scores)
        for h in range(self.num_heads):
            head_scores = scores[:, h]
            # Max per dst node for numerical stability
            max_val = torch.full((num_nodes,), -1e9, device=x.device)
            max_val.scatter_reduce_(0, dst, head_scores, reduce="amax", include_self=False)
            exp_scores = torch.exp(head_scores - max_val[dst])

            sum_exp = torch.zeros(num_nodes, device=x.device)
            sum_exp.scatter_add_(0, dst, exp_scores)
            sum_exp = torch.clamp(sum_exp, min=1e-8)

            alpha_weights[:, h] = exp_scores / sum_exp[dst]

        # Aggregate weighted messages
        # [num_edges, heads, head_dim] * [num_edges, heads, 1]
        msg = edge_src_h * alpha_weights.unsqueeze(-1)
        agg = torch.zeros((num_nodes, self.num_heads, self.head_dim), device=x.device)
        for h in range(self.num_heads):
            agg[:, h, :].index_add_(0, dst, msg[:, h, :])

        out = agg.view(num_nodes, self.out_features)
        out = self.norm(out + self.shortcut(x))
        return F.elu(out), alpha_weights


class BoundaryGATNet(nn.Module):
    """
    2-Layer Boundary Graph Attention Network.
    """
    def __init__(self, in_features: int = 128, hidden_dim: int = 128, num_heads: int = 4):
        super().__init__()
        self.layer1 = BoundaryGATLayer(in_features, hidden_dim, num_heads=num_heads)
        self.layer2 = BoundaryGATLayer(hidden_dim, hidden_dim, num_heads=num_heads)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        h1, _ = self.layer1(x, edge_index)
        h2, attn = self.layer2(h1, edge_index)
        return h2, attn
