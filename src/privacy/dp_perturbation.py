"""
Differentially Private (DP) Perturbation Layer & RDP Privacy Accountant.

Implements L2-norm embedding clipping, Gaussian noise injection, and
Rényi Differential Privacy (RDP) accounting to strictly guarantee (epsilon, delta)-DP
for boundary node embeddings shared with the central coordinator.
"""

import math
from typing import Tuple, Union, Optional
import numpy as np


class DPPerturbation:
    """
    Applies L2-norm clipping and calibrated Gaussian perturbation to node representations.
    """

    def __init__(self, clip_norm: float = 1.0, sigma: float = 1.25, seed: Optional[int] = 42):
        """
        Args:
            clip_norm: L2 sensitivity clipping threshold C (default: 1.0)
            sigma: Noise multiplier sigma = std_dev / (C)
            seed: Optional random seed for reproducibility
        """
        self.clip_norm = float(clip_norm)
        self.sigma = float(sigma)
        self.rng = np.random.default_rng(seed)

    def clip_embeddings(self, embeddings: np.ndarray) -> np.ndarray:
        """
        Clip node embeddings using L2 sensitivity threshold C:
        Clip(h_v, C) = h_v / max(1, ||h_v||_2 / C)
        """
        norms = np.linalg.norm(embeddings, ord=2, axis=-1, keepdims=True)
        scaling_factor = np.maximum(1.0, norms / self.clip_norm)
        return embeddings / scaling_factor

    def perturb_embeddings(self, embeddings: np.ndarray) -> Tuple[np.ndarray, dict]:
        """
        Clip embeddings and inject Gaussian noise:
        h_tilde = Clip(h_v, C) + N(0, (sigma * C)^2 * I)

        Returns:
            perturbed_embeddings: ndarray with added Gaussian noise
            metadata: dict with clipping metrics and noise magnitude
        """
        clipped = self.clip_embeddings(embeddings)
        noise_std = self.sigma * self.clip_norm
        noise = self.rng.normal(loc=0.0, scale=noise_std, size=clipped.shape)
        perturbed = clipped + noise

        metadata = {
            "clip_norm_C": self.clip_norm,
            "sigma": self.sigma,
            "noise_std": noise_std,
            "avg_original_norm": float(np.mean(np.linalg.norm(embeddings, axis=-1))),
            "avg_clipped_norm": float(np.mean(np.linalg.norm(clipped, axis=-1))),
            "avg_perturbed_norm": float(np.mean(np.linalg.norm(perturbed, axis=-1))),
        }
        return perturbed, metadata


class RDPAccountant:
    """
    Rényi Differential Privacy (RDP) Accountant for Gaussian Mechanism.
    Computes cumulative (epsilon, delta)-DP bounds across multiple composition rounds.
    """

    def __init__(self, orders: Optional[np.ndarray] = None):
        if orders is None:
            self.orders = np.linspace(1.1, 64.0, 100)
        else:
            self.orders = np.array(orders)
        self.rdp = np.zeros_like(self.orders, dtype=float)

    def step(self, sigma: float, steps: int = 1):
        """
        Accumulates privacy budget consumption for Gaussian mechanism.
        For order alpha and noise multiplier sigma:
        RDP_alpha = alpha / (2 * sigma^2)
        """
        step_rdp = self.orders / (2.0 * (sigma ** 2))
        self.rdp += steps * step_rdp

    def get_privacy_spent(self, target_delta: float = 1e-5) -> Tuple[float, float, float]:
        """
        Converts accumulated RDP to (epsilon, delta)-DP using the standard RDP-to-DP conversion:
        epsilon(delta) = min_{alpha > 1} ( RDP(alpha) + log(1/delta) / (alpha - 1) )

        Returns:
            optimal_eps: Minimum epsilon achieved
            target_delta: The specified delta
            best_order: The optimal Rényi order alpha
        """
        epsilons = self.rdp + np.log(1.0 / target_delta) / (self.orders - 1.0)
        best_idx = np.argmin(epsilons)
        return float(epsilons[best_idx]), float(target_delta), float(self.orders[best_idx])

    def calibrate_sigma(
        self, target_eps: float = 2.0, target_delta: float = 1e-5, steps: int = 1
    ) -> float:
        """
        Finds the minimum sigma required to satisfy target_eps at target_delta for given steps.
        Uses binary search over sigma.
        """
        low_sigma, high_sigma = 0.1, 20.0
        for _ in range(50):
            mid_sigma = (low_sigma + high_sigma) / 2.0
            test_accountant = RDPAccountant(self.orders)
            test_accountant.step(mid_sigma, steps=steps)
            eps, _, _ = test_accountant.get_privacy_spent(target_delta)
            if eps <= target_eps:
                high_sigma = mid_sigma
            else:
                low_sigma = mid_sigma
        return high_sigma
