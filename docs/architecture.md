# ZeroMule: Technical Architecture & System Specification

The coordinator is a software simulation, without hardware attestation. HMAC
matching is not cryptographic PSI. The authoritative privacy release design and
deployment requirements are in [Privacy architecture](privacy-architecture.md).
Latency figures below are historical targets/demonstrations and exclude durable
budget enforcement.

```
   ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
   │  Bank A Silo    │       │  Bank B Silo    │       │  Bank C Silo    │
   │  Private Ledger │       │  Private Ledger │       │  Private Ledger │
   └────────┬────────┘       └────────┬────────┘       └────────┬────────┘
            │ Local GIN               │ Local GIN               │ Local GIN
            ▼                         ▼                         ▼
   ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
   │ Directed-GIN    │       │ Directed-GIN    │       │ Directed-GIN    │
   │ Embeddings h_A  │       │ Embeddings h_B  │       │ Embeddings h_C  │
   └────────┬────────┘       └────────┬────────┘       └────────┬────────┘
            │ HMAC pseudonym matching  │ HMAC pseudonym matching  │ HMAC pseudonym matching
            │ + DP Gaussian Noise     │ + DP Gaussian Noise     │ + DP Gaussian Noise
            └────────────────┐        │        ┌────────────────┘
                             ▼        ▼        ▼
                    ┌──────────────────────────────────────┐
                    │   Coordinator simulation (enclave target)    │
                    │   (Confidential Computing Hub)       │
                    │                                      │
                    │  1. HMAC boundary matcher (< 2ms)     │
                    │  2. Bank-side budget before release  │
                    │  3. Boundary Subgraph GAT (< 8ms)    │
                    │  4. Contrastive Cycle Head (< 5ms)   │
                    │                                      │
                    │  ⚡ End-to-End P99 Latency: < 30ms   │
                    └──────────────────┬───────────────────┘
                                       │
                                       ▼
                    ┌──────────────────────────────────────┐
                    │     PRE-SETTLEMENT SCAM FREEZE       │
                    │  Equalized-Odds Calibrated Gate      │
                    │  Elderly Disparity <= 1.5%           │
                    └──────────────────────────────────────┘
```

---

## 1. Mathematical Formulation

### 1.1 Local Directed-Multigraph GIN Layer
Traditional Graph Isomorphism Networks (GIN) aggregate undirected neighborhoods symmetrically. In anti-money laundering, funds follow strict **temporal, directional causal vectors**. ZeroMule models asymmetric incoming ($\mathcal{N}_{\text{in}}$) and outgoing ($\mathcal{N}_{\text{out}}$) transaction flows:

$$h_v^{(l)} = \text{MLP}^{(l)}\left( (1 + \epsilon) h_v^{(l-1)} + \sum_{u \in \mathcal{N}_{\text{in}}(v)} W_{\text{in}}(h_u^{(l-1)} \parallel e_{uv}) + \sum_{w \in \mathcal{N}_{\text{out}}(v)} W_{\text{out}}(h_w^{(l-1)} \parallel e_{vw}) \right)$$

where:
- $h_v^{(l)} \in \mathbb{R}^{d}$ is the node representation at layer $l$.
- $e_{uv} \in \mathbb{R}^{m}$ encodes log-scaled transaction amount, one-hot payment format, and sinusoidal temporal embeddings:

$$\text{PE}(\Delta t, 2i) = \sin\left(\frac{\Delta t}{10000^{2i/d_{\text{model}}}}\right), \quad \text{PE}(\Delta t, 2i+1) = \cos\left(\frac{\Delta t}{10000^{2i/d_{\text{model}}}}\right)$$

- $W_{\text{in}}, W_{\text{out}} \in \mathbb{R}^{d \times (d + m)}$ are learnable directed projection operators.
- $\epsilon$ is a learnable GIN injectivity parameter.

---

### 1.2 HMAC pseudonym equality matching
To identify cross-bank counterparty overlap without leaking customer account numbers or PII:

$$\mathcal{H}_K(\text{AccountID}) = \text{HMAC-SHA256}(K, \text{AccountID})$$

The coordinator matches intersection sets:

$$\mathcal{B}_{(A, B)} = \{\mathcal{H}_K(u) \mid u \in \mathcal{V}_A\} \cap \{\mathcal{H}_K(v) \mid v \in \mathcal{V}_B\}$$

Raw balances, transaction amounts, and account attributes remain strictly local to each bank.

---

### 1.3 Differential privacy release boundary

The bank clips the complete embedding matrix to Frobenius norm C, giving a
replacement sensitivity bound of 2C even when graph changes affect many nodes.
Gaussian noise has standard deviation 2C times sigma. A persistent bank-wide
ledger reserves cumulative RDP cost before every release and rejects spending
over epsilon 2.0 at delta 1e-5. This protects values conditional on the disclosed
roster and topology; it does not make the graph or account membership DP.
See [Privacy architecture](privacy-architecture.md) for the exact scope,
composition, provisioning and rollback limitations.

---

### 1.4 Demographic Fairness & Equalized-Odds Calibration
Elderly accounts ($\text{Age} \ge 65$) are frequently targeted by grandparent scams and unauthorized impersonation, leading uncalibrated algorithms to generate high false-positive account freezes. Equalized-Odds calibration tunes group-specific decision thresholds:

$$|P(\hat{Y}=1 \mid Y=0, \text{Age} \ge 65) - P(\hat{Y}=1 \mid Y=0, \text{Age} < 65)| \le 0.015$$

This ensures elderly accounts are shielded from scam drainage without suffering disproportionate false account lockouts.

---

## 2. IBM Z / s390x Execution Latency Budget

| Pipeline Stage | Implementation | Latency Target | Empirical SLA |
| :--- | :--- | :--- | :--- |
| **Stage 1: HMAC Lookup** | HMAC-SHA256 hash set intersection | $< 2.0\text{ ms}$ | $1.2\text{ ms}$ |
| **Stage 2: DP Perturbation** | Vectorized $L_2$ norm clip + Gaussian sample | $< 1.0\text{ ms}$ | $0.4\text{ ms}$ |
| **Stage 3: GAT Message Passing** | 2-Layer multi-head boundary attention | $< 8.0\text{ ms}$ | $6.8\text{ ms}$ |
| **Stage 4: Contrastive Risk Head** | MLP Anomaly Classifier + Sigmoid score | $< 5.0\text{ ms}$ | $4.1\text{ ms}$ |
| **Stage 5: Equalized-Odds Gate** | Demographic conditional thresholding | $< 0.5\text{ ms}$ | $0.1\text{ ms}$ |
| **Total Round-Trip Execution** | Hardware-accelerated CPU / ONNX | **$< 30.0\text{ ms}$ (P99)** | **$13.5\text{ ms}$ (P50), $24.8\text{ ms}$ (P99)** |
