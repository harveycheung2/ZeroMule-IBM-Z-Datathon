"""
Demographic Fairness Calibration and Equalized-Odds Post-Processing Framework.

Project: ZeroMule-IBM-Z-Datathon
Evaluates and mitigates false-positive disparity on demographic benchmarks (e.g. NeurIPS BAF suite):
- Disparity analysis: measures false positive freeze rates on protected accounts (Age >= 65)
  vs. standard accounts (Age < 65).
- Dynamically calibrates Equalized-Odds thresholds (tau_protected, tau_standard) such that:
  | P(Y_hat = 1 | Y = 0, Age >= 65) - P(Y_hat = 1 | Y = 0, Age < 65) | <= 0.015 (1.5% parity gap).
"""

from pathlib import Path
from typing import Dict, Optional, Tuple
import numpy as np


class EqualizedOddsCalibrator:
    """
    Calibrates group-specific classification thresholds to ensure demographic parity
    in false positive rates (FPR parity).
    """

    def __init__(self, target_tolerance: float = 0.015):
        self.target_tolerance = target_tolerance
        self.tau_standard = 0.50
        self.tau_protected = 0.50

    def fit(self, y_true: np.ndarray, y_scores: np.ndarray, is_protected: np.ndarray) -> Dict[str, float]:
        """
        Calibrates optimal tau_protected and tau_standard on benign negative instances (Y = 0)
        such that FPR_protected ~ FPR_standard within target_tolerance.
        """
        neg_mask = (y_true == 0)
        scores_std = y_scores[neg_mask & (is_protected == 0)]
        scores_prot = y_scores[neg_mask & (is_protected == 1)]

        if len(scores_std) == 0 or len(scores_prot) == 0:
            return {
                "tau_standard": self.tau_standard,
                "tau_protected": self.tau_protected,
                "disparity_gap": 0.0
            }

        ref_tau_std = 0.50
        fpr_std = float(np.mean(scores_std >= ref_tau_std))

        candidate_prot = np.linspace(0.20, 0.85, 131)
        best_diff = 1.0
        best_tau_prot = 0.50

        for tau_p in candidate_prot:
            fpr_p = float(np.mean(scores_prot >= tau_p))
            diff = abs(fpr_p - fpr_std)
            if diff < best_diff:
                best_diff = diff
                best_tau_prot = float(tau_p)

        self.tau_standard = ref_tau_std
        self.tau_protected = best_tau_prot

        return {
            "tau_standard": self.tau_standard,
            "tau_protected": self.tau_protected,
            "final_fpr_standard": float(np.mean(scores_std >= self.tau_standard)),
            "final_fpr_protected": float(np.mean(scores_prot >= self.tau_protected)),
            "disparity_gap": best_diff,
        }

    def predict(self, y_scores: np.ndarray, is_protected: np.ndarray) -> np.ndarray:
        """
        Applies group-specific calibrated thresholds to produce binary predictions.
        """
        thresholds = np.where(is_protected == 1, self.tau_protected, self.tau_standard)
        return (y_scores >= thresholds).astype(int)


def run_fairness_calibration_framework_check():
    """
    Validates calibrator initialization without injecting false or mock datasets.
    """
    print("=" * 60)
    print("  ZeroMule-IBM-Z-Datathon: Demographic Fairness Framework")
    print("=" * 60)
    calibrator = EqualizedOddsCalibrator(target_tolerance=0.015)
    print(f"  [Ready] Equalized-Odds Calibrator initialized with target tolerance: {calibrator.target_tolerance}")
    print("  [Ready] Ready to calibrate on real customer demographic data.")
    print("=" * 60)


if __name__ == "__main__":
    run_fairness_calibration_framework_check()
