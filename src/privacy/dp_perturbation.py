"""Gaussian mechanism and RDP calculations. Release enforcement lives in budget.py."""

import math
import secrets
from statistics import NormalDist
import numpy as np

ORDERS = np.arange(2.0, 257.0)
MAX_EPSILON = 2.0
DELTA = 1e-5


def positive(value, name):
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be finite and positive")
    return value


def epsilon_for_rho(rho, delta=DELTA, orders=ORDERS):
    if rho == 0:
        return 0.0
    return float(np.min(orders * rho + math.log(1 / delta) / (orders - 1)))


class DPPerturbation:
    """Clip the entire fixed-shape release to C; replacement sensitivity is 2C.

    Gaussian draws use OS randomness, with no deterministic production seed.
    This numerical mechanism does not protect the identity roster or topology.
    """

    def __init__(self, clip_norm=1.0, sigma=8.0):
        self.clip_norm = positive(clip_norm, "clip_norm")
        self.sigma = positive(sigma, "sigma")
        positive(2 * self.clip_norm * self.sigma, "noise_std")

    def clip_embeddings(self, embeddings):
        matrix = np.array(embeddings, dtype=np.float64, copy=True)
        if matrix.ndim != 2 or not matrix.size or not np.isfinite(matrix).all():
            raise ValueError("Embeddings must be a nonempty finite matrix")
        # Scale before computing norm to avoid overflow on large finite inputs.
        maximum = float(np.max(np.abs(matrix)))
        if maximum == 0:
            return matrix
        unit = matrix / maximum
        unit_norm = np.linalg.norm(unit)
        if maximum > self.clip_norm / unit_norm:
            return unit * (self.clip_norm / unit_norm)
        return matrix

    def perturb_embeddings(self, embeddings):
        clipped = self.clip_embeddings(embeddings)
        std = 2 * self.clip_norm * self.sigma
        normal = NormalDist()
        # Midpoints on an OS-random 52-bit uniform grid avoid inverse-CDF endpoints.
        noise = np.fromiter((normal.inv_cdf((secrets.randbits(52) + 0.5) / 2**52)
                             for _ in range(clipped.size)), dtype=float).reshape(clipped.shape)
        perturbed = clipped + std * noise
        if not np.isfinite(perturbed).all():
            raise ValueError("Nonfinite protected embedding")
        return perturbed, {"clip_norm_C": self.clip_norm, "sigma": self.sigma,
                           "noise_std": std}


class RDPAccountant:
    """Calculation utility only; cannot authorize exports or reset a release ledger."""

    def __init__(self, orders=None):
        self.orders = np.array(ORDERS if orders is None else orders, dtype=float)
        if self.orders.ndim != 1 or not self.orders.size or not np.isfinite(self.orders).all() or np.any(self.orders <= 1):
            raise ValueError("RDP orders must be finite and greater than one")
        self.rdp = np.zeros_like(self.orders)

    def step(self, sigma, steps=1):
        sigma = positive(sigma, "sigma")
        if type(steps) is not int or steps < 1:
            raise ValueError("steps must be a positive integer")
        self.rdp += steps * self.orders * (0.5 / sigma / sigma)

    def get_privacy_spent(self, target_delta=DELTA):
        if not 0 < target_delta < 1:
            raise ValueError("delta must be between zero and one")
        values = self.rdp + math.log(1 / target_delta) / (self.orders - 1)
        index = int(np.argmin(values))
        return (float(values[index]) if np.any(self.rdp) else 0.0,
                float(target_delta), float(self.orders[index]))

    def calibrate_sigma(self, target_eps=MAX_EPSILON, target_delta=DELTA, steps=1):
        positive(target_eps, "target_eps")
        low, high = 0.0, 1.0
        def spent(sigma):
            test = RDPAccountant(self.orders)
            test.step(sigma, steps)
            return test.get_privacy_spent(target_delta)[0]
        while spent(high) > target_eps:
            high *= 2
            if not math.isfinite(high):
                raise ValueError("Cannot calibrate requested budget")
        for _ in range(80):
            mid = (low + high) / 2
            if spent(mid) <= target_eps:
                high = mid
            else:
                low = mid
        return high
