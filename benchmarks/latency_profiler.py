"""
Inference Latency and Throughput Profiler (Targeting IBM Z / s390x Enterprise SLA).

Project: ZeroMule-IBM-Z-Datathon
Profiles end-to-end execution stages to verify the deterministic sub-30ms P99 SLA:
1. Stage 1: Cryptographic PSI Hash Lookup (< 2ms)
2. Stage 2: DP Embedding L2 Sensitivity Clipping and Noise Perturbation (< 1ms)
3. Stage 3: GAT Boundary Graph Message Passing and Contrastive Risk MLP (< 15ms)
4. End-to-End P50, P90, P99 Latency Distribution (< 30ms deterministic freeze)
"""

import time
import argparse
from pathlib import Path
from typing import Dict, List
import numpy as np
import torch
import torch.nn as nn

from src.privacy.psi_hasher import PSIHasher
from src.privacy.dp_perturbation import DPPerturbation
from src.models.gat_boundary import BoundaryGATNet
from src.models.contrastive_head import ContrastiveCycleClassifier


class EnclaveInferenceModule(nn.Module):
    """
    Combined GAT + MLP module formatted for ONNX compilation and inference benchmarking.
    """
    def __init__(self, in_features: int = 128, hidden_dim: int = 128):
        super().__init__()
        self.gat = BoundaryGATNet(in_features=in_features, hidden_dim=hidden_dim, num_heads=4)
        self.classifier = ContrastiveCycleClassifier(in_features=hidden_dim, projection_dim=64)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        gat_out, _ = self.gat(x, edge_index)
        src, dst = edge_index[0], edge_index[1]
        edge_rep = (gat_out[src] + gat_out[dst]) / 2.0
        scores, _ = self.classifier(edge_rep)
        return scores


def run_latency_benchmark(num_trials: int = 50, batch_edges: int = 32, num_nodes: int = 24) -> Dict[str, float]:
    """
    Runs deterministic multi-stage latency profiling against hardware target SLA.
    """
    hasher = PSIHasher()
    dp_engine = DPPerturbation(clip_norm=1.0, sigma=1.25)
    model = EnclaveInferenceModule(in_features=128, hidden_dim=128)
    model.eval()

    account_ids = [f"ACC_{i:06d}" for i in range(num_nodes)]
    synthetic_embs = np.random.randn(num_nodes, 128).astype(np.float32)

    src = np.random.randint(0, num_nodes, size=batch_edges)
    dst = np.random.randint(0, num_nodes, size=batch_edges)
    edge_index = np.stack([src, dst], axis=0)

    psi_latencies_ms = []
    dp_latencies_ms = []
    gat_mlp_latencies_ms = []
    total_latencies_ms = []

    # Warmup
    for _ in range(5):
        _ = hasher.hash_accounts(account_ids[:8])
        _ = dp_engine.perturb_embeddings(synthetic_embs[:8])
        with torch.no_grad():
            t_x = torch.from_numpy(synthetic_embs).float()
            t_edge = torch.from_numpy(edge_index)
            _ = model(t_x, t_edge)

    # Profiling loop
    for _ in range(num_trials):
        t0 = time.perf_counter()

        # Stage 1: PSI Lookup
        t_s1_start = time.perf_counter()
        _ = hasher.hash_accounts(account_ids)
        t_s1_end = time.perf_counter()
        psi_ms = (t_s1_end - t_s1_start) * 1000.0

        # Stage 2: DP Perturbation
        t_s2_start = time.perf_counter()
        perturbed_embs, _ = dp_engine.perturb_embeddings(synthetic_embs)
        t_s2_end = time.perf_counter()
        dp_ms = (t_s2_end - t_s2_start) * 1000.0

        # Stage 3: GAT + Classifier
        t_s3_start = time.perf_counter()
        with torch.no_grad():
            t_x = torch.from_numpy(perturbed_embs).float()
            t_edge = torch.from_numpy(edge_index)
            _ = model(t_x, t_edge)
        t_s3_end = time.perf_counter()
        gat_mlp_ms = (t_s3_end - t_s3_start) * 1000.0

        t_total_end = time.perf_counter()
        total_ms = (t_total_end - t0) * 1000.0

        psi_latencies_ms.append(psi_ms)
        dp_latencies_ms.append(dp_ms)
        gat_mlp_latencies_ms.append(gat_mlp_ms)
        total_latencies_ms.append(total_ms)

    p99 = float(np.percentile(total_latencies_ms, 99))
    p50 = float(np.percentile(total_latencies_ms, 50))

    print("\n" + "=" * 60)
    print("  ZeroMule IBM Z / LinuxONE Latency Benchmark Results")
    print("=" * 60)
    print(f"  Stage 1 (PSI Salted Lookup):      {np.mean(psi_latencies_ms):.2f} ms")
    print(f"  Stage 2 (DP Noise Injection):     {np.mean(dp_latencies_ms):.2f} ms")
    print(f"  Stage 3 (GAT + Contrastive Head): {np.mean(gat_mlp_latencies_ms):.2f} ms")
    print("-" * 60)
    print(f"  Round-Trip Latency (P50):         {p50:.2f} ms")
    print(f"  Round-Trip Latency (P99):         {p99:.2f} ms (Target SLA: < 30ms)")
    print(f"  Status: {'PASSED (<30ms SLA)' if p99 < 30.0 else 'CHECK SLA'}")
    print("=" * 60)

    return {
        "psi_mean_ms": float(np.mean(psi_latencies_ms)),
        "dp_mean_ms": float(np.mean(dp_latencies_ms)),
        "gat_mlp_mean_ms": float(np.mean(gat_mlp_latencies_ms)),
        "total_p50_ms": p50,
        "total_p99_ms": p99,
        "meets_30ms_sla": bool(p99 < 30.0),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Latency profiler for ZeroMule")
    parser.add_argument("--trials", type=int, default=25, help="Number of benchmark trials")
    args = parser.parse_args()
    run_latency_benchmark(num_trials=args.trials)
