"""
Directed Multigraph Builder for ZeroMule Banking Ledgers.

Converts partitioned bank ledgers into PyTorch directed graph representations:
- Node feature matrix X in R^{|V| x d} (in-degree, out-degree, volume, time span)
- Edge indices (E_in, E_out) capturing directed transaction flows
- Edge feature tensor E in R^{|E| x m} with log-scaled amounts, one-hot format encodings,
  and continuous sinusoidal temporal positional embeddings.
"""

import math
from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd
import torch


class DirectedGraphData:
    """
    Graph data container compatible with PyTorch Geometric conventions.
    """
    def __init__(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
        edge_attr: torch.Tensor,
        y: Optional[torch.Tensor] = None,
        node_map: Optional[Dict[str, int]] = None,
        rev_node_map: Optional[Dict[int, str]] = None,
        edge_trans_ids: Optional[List[str]] = None,
    ):
        self.x = x
        self.edge_index = edge_index
        self.edge_attr = edge_attr
        self.y = y
        self.node_map = node_map or {}
        self.rev_node_map = rev_node_map or {}
        self.edge_trans_ids = edge_trans_ids or []

    @property
    def num_nodes(self) -> int:
        return self.x.size(0)

    @property
    def num_edges(self) -> int:
        return self.edge_index.size(1)

    def to(self, device):
        self.x = self.x.to(device)
        self.edge_index = self.edge_index.to(device)
        self.edge_attr = self.edge_attr.to(device)
        if self.y is not None:
            self.y = self.y.to(device)
        return self


def compute_sinusoidal_temporal_encoding(deltas: np.ndarray, d_model: int = 8) -> np.ndarray:
    """
    Sinusoidal temporal embedding layer:
    PE(t, 2i) = sin(t / 10000^(2i / d_model))
    PE(t, 2i + 1) = cos(t / 10000^(2i / d_model))
    """
    n = len(deltas)
    pe = np.zeros((n, d_model), dtype=np.float32)
    div_term = np.exp(np.arange(0, d_model, 2) * -(math.log(10000.0) / d_model))

    t_expanded = deltas[:, np.newaxis]
    pe[:, 0::2] = np.sin(t_expanded * div_term)
    pe[:, 1::2] = np.cos(t_expanded * div_term)
    return pe


class GraphBuilder:
    """
    Builds directed multigraphs from transaction dataframes.
    """

    PAYMENT_FORMATS = ["Wire", "ACH", "Cheque", "Credit Card", "Cash"]
    CURRENCIES = ["US Dollar", "Euro", "Bitcoin", "Yen", "Swiss Franc"]

    def __init__(self, temporal_dim: int = 8):
        self.temporal_dim = temporal_dim

    def build_graph_from_df(self, df: pd.DataFrame) -> DirectedGraphData:
        """
        Transforms transaction ledger dataframe into a directed multigraph.
        """
        df = df.copy()
        if "Timestamp" in df.columns:
            df["dt"] = pd.to_datetime(df["Timestamp"])
            df = df.sort_values("dt").reset_index(drop=True)
            # Relative delta in hours
            df["time_delta_hours"] = (df["dt"] - df["dt"].min()).dt.total_seconds() / 3600.0
        else:
            df["time_delta_hours"] = np.arange(len(df), dtype=float)

        # Build unique node dictionary
        src_nodes = df["Account"].astype(str).tolist()
        dst_nodes = df["Account.1"].astype(str).tolist()
        unique_nodes = sorted(list(set(src_nodes + dst_nodes)))
        node_map = {node_id: idx for idx, node_id in enumerate(unique_nodes)}
        rev_node_map = {idx: node_id for node_id, idx in node_map.items()}
        num_nodes = len(unique_nodes)

        # Compute Node Features:
        # [in-degree, out-degree, total_in_vol, total_out_vol, net_vol, active_span_hours, unique_counterparties]
        in_degree = np.zeros(num_nodes, dtype=np.float32)
        out_degree = np.zeros(num_nodes, dtype=np.float32)
        total_in_vol = np.zeros(num_nodes, dtype=np.float32)
        total_out_vol = np.zeros(num_nodes, dtype=np.float32)
        first_time = np.full(num_nodes, np.inf, dtype=np.float32)
        last_time = np.full(num_nodes, -np.inf, dtype=np.float32)
        counterparties = [set() for _ in range(num_nodes)]

        src_indices = [node_map[s] for s in src_nodes]
        dst_indices = [node_map[d] for d in dst_nodes]
        amounts = df["Amount Paid"].values.astype(np.float32)
        times = df["time_delta_hours"].values.astype(np.float32)

        for s_idx, d_idx, amt, t in zip(src_indices, dst_indices, amounts, times):
            out_degree[s_idx] += 1
            in_degree[d_idx] += 1
            total_out_vol[s_idx] += amt
            total_in_vol[d_idx] += amt
            first_time[s_idx] = min(first_time[s_idx], t)
            first_time[d_idx] = min(first_time[d_idx], t)
            last_time[s_idx] = max(last_time[s_idx], t)
            last_time[d_idx] = max(last_time[d_idx], t)
            counterparties[s_idx].add(d_idx)
            counterparties[d_idx].add(s_idx)

        # Normalize node features
        span_hours = np.maximum(0.0, last_time - first_time)
        span_hours[np.isinf(span_hours)] = 0.0
        n_counterparties = np.array([len(cp) for cp in counterparties], dtype=np.float32)

        node_features = np.stack([
            np.log1p(in_degree),
            np.log1p(out_degree),
            np.log1p(total_in_vol),
            np.log1p(total_out_vol),
            np.sign(total_in_vol - total_out_vol) * np.log1p(np.abs(total_in_vol - total_out_vol)),
            np.log1p(span_hours),
            np.log1p(n_counterparties),
        ], axis=1).astype(np.float32)

        # Build Edge Features:
        # [log_amount, format_onehot (5), curr_onehot (5), temporal_sinusoidal (temporal_dim)]
        log_amounts = np.log1p(amounts)[:, np.newaxis]

        # One-hot payment format
        fmt_onehot = np.zeros((len(df), len(self.PAYMENT_FORMATS)), dtype=np.float32)
        for i, fmt in enumerate(self.PAYMENT_FORMATS):
            fmt_onehot[:, i] = (df["Payment Format"] == fmt).astype(np.float32)

        # One-hot currency
        curr_onehot = np.zeros((len(df), len(self.CURRENCIES)), dtype=np.float32)
        for i, curr in enumerate(self.CURRENCIES):
            curr_onehot[:, i] = (df["Receiving Currency"] == curr).astype(np.float32)

        # Sinusoidal temporal embedding
        temporal_emb = compute_sinusoidal_temporal_encoding(times, d_model=self.temporal_dim)

        edge_features = np.concatenate([
            log_amounts, fmt_onehot, curr_onehot, temporal_emb
        ], axis=1).astype(np.float32)

        # Construct PyTorch Tensors
        edge_index = torch.tensor([src_indices, dst_indices], dtype=torch.long)
        edge_attr = torch.tensor(edge_features, dtype=torch.float32)
        x = torch.tensor(node_features, dtype=torch.float32)

        # Edge labels (1 = laundering, 0 = benign)
        labels = df["Is Laundering"].values.astype(np.float32) if "Is Laundering" in df.columns else None
        y = torch.tensor(labels, dtype=torch.float32) if labels is not None else None

        trans_ids = df["Transaction_ID"].tolist() if "Transaction_ID" in df.columns else [f"TX_{i}" for i in range(len(df))]

        return DirectedGraphData(
            x=x,
            edge_index=edge_index,
            edge_attr=edge_attr,
            y=y,
            node_map=node_map,
            rev_node_map=rev_node_map,
            edge_trans_ids=trans_ids,
        )
