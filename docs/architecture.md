# ZeroMule: Technical Architecture and System Specification

Repository: ZeroMule-IBM-Z-Datathon  
Platform Target: IBM Z / LinuxONE (s390x) and Confidential Computing Enclaves  
Standard Compliance: GDPR, GLBA, FCRA Privacy Bounds, sub-30ms P99 Latency SLA  

```
   +-----------------+       +-----------------+       +-----------------+
   |   Bank A Silo   |       |   Bank B Silo   |       |   Bank C Silo   |
   |  Private Ledger |       |  Private Ledger |       |  Private Ledger |
   +--------+--------+       +--------+--------+       +--------+--------+
            | Local GIN               | Local GIN               | Local GIN
            v                         v                         v
   +-----------------+       +-----------------+       +-----------------+
   |  Directed-GIN   |       |  Directed-GIN   |       |  Directed-GIN   |
   | Embeddings h_A  |       | Embeddings h_B  |       | Embeddings h_C  |
   +--------+--------+       +--------+--------+       +--------+--------+
            | Salted HMAC-SHA256 PSI  | Salted HMAC-SHA256 PSI  | Salted HMAC-SHA256 PSI
            | + DP Gaussian Noise     | + DP Gaussian Noise     | + DP Gaussian Noise
            +----------------+        |        +----------------+
                             v        v        v
                    +--------------------------------------+
                    |   IBM Z / LinuxONE Secure Enclave    |
                    |   (Confidential Computing Hub)       |
                    |                                      |
                    |  1. PSI Boundary Matcher (< 2ms)     |
                    |  2. RDP Budget Tracker (eps <= 2.0)  |
                    |  3. Boundary Subgraph GAT (< 8ms)    |
                    |  4. Contrastive Cycle Head (< 5ms)   |
                    |                                      |
                    |  End-to-End P99 Latency: < 30ms      |
                    +------------------+-------------------+
                                       |
                                       v
                    +--------------------------------------+
                    |      PRE-SETTLEMENT SCAM FREEZE      |
                    |  Equalized-Odds Calibrated Gate      |
                    |  Elderly Disparity <= 1.5%           |
                    +--------------------------------------+
```

---

## 1. System Overview and Problem Statement

Money laundering syndicates systematically fragment illicit capital flows across competing financial institutions to evade internal rules-based transaction monitoring systems (a technique termed smurfing). Because legal privacy regulations (GDPR, GLBA) prohibit banks from broadcasting unencrypted customer ledgers or account balances, isolated institutions only observe single-hop benign transfers, triggering zero alerts.

ZeroMule solves this coordination problem without violating financial secrecy regulations by combining:
1. Local Directed-GIN Encoders executed strictly inside each bank boundary.
2. Salted HMAC-SHA256 Private Set Intersection (PSI) for non-revealing boundary counterparty alignment.
3. (epsilon, delta)-Differential Privacy via L2-sensitivity clipped Gaussian perturbation.
4. Confidential Computing Enclave on IBM Z / LinuxONE orchestrating cross-bank graph boundary message passing within sub-30ms latency.
5. Demographic Fairness Calibration enforcing Equalized-Odds parity across demographic cohorts.

---

## 2. Mathematical Formulation

### 2.1 Local Directed-Multigraph GIN Layer
Traditional Graph Isomorphism Networks (GIN) aggregate undirected neighborhoods symmetrically. In financial networks, capital flows along strict causal, temporal vectors. ZeroMule separates incoming (N_in) and outgoing (N_out) neighborhoods:

$$h_v^{(l)} = \text{MLP}^{(l)}\left( (1 + \epsilon) h_v^{(l-1)} + \sum_{u \in \mathcal{N}_{\text{in}}(v)} W_{\text{in}}(h_u^{(l-1)} \parallel e_{uv}) + \sum_{w \in \mathcal{N}_{\text{out}}(v)} W_{\text{out}}(h_w^{(l-1)} \parallel e_{vw}) \right)$$

Where:
- $h_v^{(l)} \in \mathbb{R}^{d}$ denotes node representation at layer $l$.
- $e_{uv} \in \mathbb{R}^{m}$ encodes log-scaled transaction amount, payment format, and continuous sinusoidal temporal embeddings.
- $W_{\text{in}}, W_{\text{out}} \in \mathbb{R}^{d \times (d + m)}$ are learnable directed linear projection operators.
- $\epsilon$ is a learnable GIN injectivity parameter.

### 2.2 Sinusoidal Temporal Positional Encodings
To capture inter-transaction velocity without discretizing continuous time into rigid windows:

$$\text{PE}(\Delta t, 2i) = \sin\left(\frac{\Delta t}{10000^{2i/d_{\text{model}}}}\right), \quad \text{PE}(\Delta t, 2i+1) = \cos\left(\frac{\Delta t}{10000^{2i/d_{\text{model}}}}\right)$$

### 2.3 Salted HMAC-SHA256 Private Set Intersection (PSI)
To match cross-bank counterparties without revealing customer accounts, internal account numbers are pseudonymized using a keyed hash function with key $K$:

$$\mathcal{H}_K(\text{AccountID}) = \text{HMAC-SHA256}(K, \text{AccountID})$$

The coordinator matches intersection sets:

$$\mathcal{B}_{(A, B)} = \{\mathcal{H}_K(u) \mid u \in \mathcal{V}_A\} \cap \{\mathcal{H}_K(v) \mid v \in \mathcal{V}_B\}$$

Internal balances, counterparty identity details, and benign internal accounts are never transmitted.

### 2.4 (epsilon, delta)-Differential Privacy Perturbation
Boundary representations exported from individual bank silos are bounded via $L_2$-sensitivity clipping with threshold $C$:

$$\text{Clip}(h_v, C) = \frac{h_v}{\max\left(1, \frac{\|h_v\|_2}{C}\right)}$$

Calibrated zero-mean Gaussian perturbation is injected:

$$\tilde{h}_v = \text{Clip}(h_v, C) + \mathcal{N}\left(0, \sigma^2 C^2 \mathbf{I}\right)$$

Under Rényi Differential Privacy (RDP) for order $\alpha$:

$$\text{RDP}_{\alpha}(\sigma) = \frac{\alpha}{2\sigma^2}, \quad \epsilon(\delta) = \min_{\alpha > 1} \left( \sum_{t} \text{RDP}_{\alpha}^{(t)} + \frac{\log(1/\delta)}{\alpha - 1} \right)$$

ZeroMule operates within a privacy budget of $\epsilon \le 2.0$ with $\delta = 10^{-5}$.

### 2.5 Contrastive Cycle Risk Head
In the confidential enclave, boundary node embeddings pass through a 2-layer Graph Attention Network (GAT) followed by a contrastive topology head trained with InfoNCE loss:

$$\mathcal{L}_{\text{InfoNCE}} = -\log \frac{\exp(\text{sim}(z_i, z_j) / \tau)}{\sum_{k} \exp(\text{sim}(z_i, z_k) / \tau)}$$

This maximizes representation alignment for closed laundering rings while separating benign transfer paths.

### 2.6 Equalized-Odds Demographic Calibration
Senior citizen accounts (Age >= 65) are disproportionately targeted by impersonation scams, causing naive anomaly detectors to exhibit high false-positive freeze rates. ZeroMule applies Equalized-Odds threshold calibration:

$$|P(\hat{Y}=1 \mid Y=0, \text{Age} \ge 65) - P(\hat{Y}=1 \mid Y=0, \text{Age} < 65)| \le 0.015$$

---

## 3. IBM Z / s390x Execution Latency Budget

To intercept money mule transfers before settlement, total execution latency must stay strictly below 30ms at P99:

| Pipeline Stage | Implementation Mechanism | Target SLA | Benchmark Allocation |
| :--- | :--- | :--- | :--- |
| Stage 1: Salted PSI Lookup | HMAC-SHA256 Set Intersection | < 2.0 ms | 1.2 ms |
| Stage 2: DP Perturbation | L2 Norm Clip and Gaussian Injection | < 1.0 ms | 0.5 ms |
| Stage 3: GAT Message Passing | 2-Layer Multi-Head Boundary Attention | < 8.0 ms | 6.5 ms |
| Stage 4: Contrastive Risk Head | MLP Topology Risk Classifier | < 5.0 ms | 4.0 ms |
| Stage 5: Equalized-Odds Gate | Demographic Conditional Thresholding | < 0.5 ms | 0.1 ms |
| Total Round-Trip Execution | Hardware SIMD / ONNX Runtime | < 30.0 ms (P99) | 12.3 ms (P50), 24.5 ms (P99) |

---

## 4. Threat Model and Security Guarantees

1. Honest-but-Curious Participants: Individual financial institutions follow protocol rules but may attempt to infer counterparties or account balances from received embeddings. Differential privacy guarantees bounds against reconstruction attacks.
2. Malicious Coordinator Assumption: The central aggregator is untrusted and runs inside a hardware-isolated IBM Secure Execution enclave (Confidential Computing on LinuxONE). Enclave memory is encrypted via CPACF (CP Assist for Cryptographic Functions).
3. Zero Raw PII Transmission: Account numbers, personal identifying information, and raw transaction volumes never leave the bank boundary unhashed or unperturbed.
