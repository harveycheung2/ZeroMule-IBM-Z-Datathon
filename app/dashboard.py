"""
ZeroMule Interactive Anti-Money Laundering & Mule-Ring Detection Dashboard.

Operational Panels:
1. 🏦 The Banking Silo View: Shows Bank A and Bank B independently. Isolated banks
   only see local single-hop benign transfers and trigger zero alerts.
2. 🛡️ The IBM Enclave Subgraph Reconstruction: Displays the unified cross-bank
   directed multigraph inside the confidential enclave, highlighting 5-hop mule rings in red.
3. ⚡ Real-Time In-Transaction Feed: Simulates a live streaming transaction feed with
   sub-millisecond execution timer (<30ms), dynamic epsilon DP gauge, and PRE-SETTLEMENT SCAM FREEZE.
4. 📊 Performance & Fairness Auditing: Displays PR-AUC, ROC curves, latency CDF, and demographic parity.
"""

import time
import json
import random
import datetime
from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np

# Page configuration
st.set_page_config(
    page_title="ZeroMule | IBM Datathon AML Enclave",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom High-End Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;600;700&family=IBM+Plex+Mono:wght@400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'IBM Plex Sans', -apple-system, sans-serif;
    }
    
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #0F62FE;
        letter-spacing: -0.5px;
        margin-bottom: 0px;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #A8A8A8;
        margin-bottom: 20px;
    }
    
    .metric-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.01) 100%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.25);
    }
    .metric-val {
        font-size: 1.8rem;
        font-weight: 700;
        font-family: 'IBM Plex Mono', monospace;
    }
    .metric-label {
        font-size: 0.82rem;
        text-transform: uppercase;
        color: #8D8D8D;
        letter-spacing: 0.8px;
    }
    
    .alert-freeze {
        background: linear-gradient(90deg, rgba(218, 30, 40, 0.25) 0%, rgba(218, 30, 40, 0.05) 100%);
        border-left: 5px solid #DA1E28;
        padding: 14px 18px;
        border-radius: 6px;
        margin-top: 10px;
        margin-bottom: 15px;
    }
    
    .badge-silo {
        background-color: #393939;
        color: #F4F4F4;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-enclave {
        background-color: #0F62FE;
        color: #FFFFFF;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# Sidebar controls
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/5/51/IBM_logo.svg", width=120)
st.sidebar.markdown("### **ZeroMule Control Center**")
st.sidebar.caption("See how banks can spot shared fraud without sharing raw records")

nav_choice = st.sidebar.radio(
    "Operational Views",
    [
        "1. 🏦 What One Bank Sees",
        "2. 🛡️ What ZeroMule Finds",
        "3. ⚡ Try a Transaction",
        "4. 📊 Evidence & Fairness",
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### **Privacy status**")
st.sidebar.markdown("🔒 **Hardware protection**: `Simulation`")
st.sidebar.info("Synthetic demo. No live bank data or verified hardware attestation.")
st.sidebar.markdown("🔑 **Account matching**: `Protected pseudonyms`")
st.sidebar.markdown("🛡️ **Data sharing**: `Protected embeddings`")
st.sidebar.markdown("⏱️ **Speed**: `Target under 30 ms`")

st.sidebar.markdown("---")
st.sidebar.caption("ZeroMule © 2026 | Built for IBM Datathon")


# Top Header
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown('<div class="main-title">🛡️ ZeroMule: Cross-Bank AML Detection</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Find shared fraud patterns while each bank keeps its raw records private</div>', unsafe_allow_html=True)
with col_h2:
    st.markdown(r"""
    <div style="text-align: right; padding-top: 10px;">
        <span class="badge-enclave">SIMULATED ENCLAVE</span>
        <span class="badge-silo" style="margin-left: 5px;">s390x ACCELERATED</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")


# ==========================================
# PANEL 1: BANKING SILO VIEW
# ==========================================
if "1." in nav_choice:
    st.subheader("🏦 What One Bank Sees")
    st.caption("Each bank sees only its own transactions. The full pattern is hidden across institutions.")
    if "scenario_started" not in st.session_state:
        st.session_state.scenario_started = False
    action_col, status_col = st.columns([1, 2])
    with action_col:
        if st.button("▶ Run high-risk money-flow demo", type="primary"):
            st.session_state.scenario_started = True
    with status_col:
        if st.session_state.scenario_started:
            st.success("Demo ready: Bank A → Bank B → Bank C → Bank A")
        else:
            st.info("Start the demo to reveal the cross-bank pattern.")
    st.markdown(r"""
    A suspicious group can split one flow across several banks. Each bank sees a normal-looking payment,
    but no single bank sees the complete path.
    """)

    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
        st.markdown('<div class="metric-card"><div class="metric-label">Bank A: catches alone</div><div class="metric-val" style="color: #DA1E28;">0.384</div></div>', unsafe_allow_html=True)
    with col_b2:
        st.markdown('<div class="metric-card"><div class="metric-label">Shared view available</div><div class="metric-val" style="color: #DA1E28;">0.0%</div></div>', unsafe_allow_html=True)
    with col_b3:
        st.markdown('<div class="metric-card"><div class="metric-label">Pattern missed alone</div><div class="metric-val" style="color: #FF8389;">100%</div></div>', unsafe_allow_html=True)

    st.write("")
    bank_tab = st.selectbox("Inspect Bank Perspective:", ["Bank A (Originator)", "Bank B (Intermediary)", "Bank C (Exit)"])

    col_view1, col_view2 = st.columns([3, 2])

    with col_view1:
        st.markdown(f"#### 🔍 Local View for {bank_tab}")
        if "Bank A" in bank_tab:
            st.info("🏦 **Bank A records**: Account 1 sends $32,500 to Account 2. On its own, this looks like a normal business payment. **Risk: low (0.12)**.")
            silo_df = pd.DataFrame([
                {"Time": "10:14 AM", "From": "Account 1 (Bank A)", "To": "Account 2 (Bank B)", "Amount": "$32,500", "Format": "Wire", "Status": "APPROVED", "Local Risk": "0.12"},
                {"Time": "11:05 AM", "From": "Account 3 (Bank A)", "To": "Account 4 (Bank A)", "Amount": "$1,450", "Format": "ACH", "Status": "APPROVED", "Local Risk": "0.04"},
                {"Time": "11:42 AM", "From": "Account 5 (Bank A)", "To": "Account 6 (Bank A)", "Amount": "$4,200", "Format": "Cheque", "Status": "APPROVED", "Local Risk": "0.08"},
            ])
        elif "Bank B" in bank_tab:
            st.info("🏦 **Bank B records**: Account 2 receives funds and sends $31,850 to Bank C. Bank B cannot see where the money started. **Risk: low (0.18)**.")
            silo_df = pd.DataFrame([
                {"Time": "10:14 AM", "From": "Account 1 (Bank A)", "To": "Account 2 (Bank B)", "Amount": "$32,500", "Format": "Wire", "Status": "RECEIVED", "Local Risk": "0.14"},
                {"Time": "11:32 AM", "From": "Account 2 (Bank B)", "To": "Account 3 (Bank C)", "Amount": "$31,850", "Format": "Wire", "Status": "APPROVED", "Local Risk": "0.18"},
                {"Time": "12:10 PM", "From": "Account 4 (Bank B)", "To": "Account 5 (Bank B)", "Amount": "$850", "Format": "Credit Card", "Status": "APPROVED", "Local Risk": "0.02"},
            ])
        else:
            st.info("🏦 **Bank C Ledger**: Observes incoming wire and eventual return transfer closing the circular path back to Bank A. Seen in isolation, it is indistinguishable from standard vendor trade. **Risk Score: 0.15 (CLEARED)**.")
            silo_df = pd.DataFrame([
                {"Time": "11:32 AM", "From": "Account 2 (Bank B)", "To": "Account 3 (Bank C)", "Amount": "$31,850", "Format": "Wire", "Status": "RECEIVED", "Local Risk": "0.11"},
                {"Time": "01:15 PM", "From": "Account 3 (Bank C)", "To": "Account 1 (Bank A)", "Amount": "$30,900", "Format": "Wire", "Status": "APPROVED", "Local Risk": "0.15"},
            ])
        st.dataframe(silo_df, width="stretch")

    with col_view2:
        st.markdown("#### 🚫 Why one bank misses it")
        st.markdown(r"""
        - Banks cannot simply share their customer records with one another.
        - Criminals exploit this by splitting one flow across several banks.
        - ZeroMule shares protected signals so the wider pattern can be spotted without sharing raw records.
        """)


# ==========================================
# PANEL 2: IBM ENCLAVE SUBGRAPH RECONSTRUCTION
# ==========================================
elif "2." in nav_choice:
    st.subheader("🛡️ What ZeroMule Finds")
    st.caption("Banks share protected signals—not raw customer ledgers—so the shared pattern can be detected.")
    st.markdown(r"""
    In this software simulation, **ZeroMule** matches HMAC pseudonyms (not cryptographic PSI)
    and reconstructs the cross-bank directed multigraph with $(\epsilon=2.0, \delta=10^{-5})$ Differentially Private embeddings.
    """)

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.markdown('<div class="metric-card"><div class="metric-label">Enclave PR-AUC</div><div class="metric-val" style="color: #0062FF;">0.892</div></div>', unsafe_allow_html=True)
    with col_m2:
        st.markdown('<div class="metric-card"><div class="metric-label">Rényi DP Epsilon</div><div class="metric-val" style="color: #198038;">1.84 / 2.0</div></div>', unsafe_allow_html=True)
    with col_m3:
        st.markdown('<div class="metric-card"><div class="metric-label">Matched Pseudonyms</div><div class="metric-val" style="color: #8A3FFC;">1,240 nodes</div></div>', unsafe_allow_html=True)
    with col_m4:
        st.markdown('<div class="metric-card"><div class="metric-label">Topology Identified</div><div class="metric-val" style="color: #DA1E28;">5-Hop Cycle</div></div>', unsafe_allow_html=True)

    st.write("")
    st.markdown('<div class="alert-freeze">🚨 <strong>SIMULATED SUSPICIOUS FLOW:</strong> Bank A → Bank B → Bank C → Bank A. Risk score: <strong>0.984 (high risk)</strong>.</div>', unsafe_allow_html=True)

    # Render interactive network graph
    st.markdown("#### 🕸️ Reconstructed Cross-Bank Topology")

    # Generate PyVis interactive visualization
    try:
        from pyvis.network import Network
        net = Network(height="450px", width="100%", bgcolor="#161616", font_color="#FFFFFF", directed=True)

        # Nodes
        net.add_node("ACC_000102", label="Bank A\nAccount 1", color="#DA1E28", size=25, x=-500, y=0, title="Bank A: starting point")
        net.add_node("ACC_000411", label="Bank B\nAccount 2", color="#DA1E28", size=22, x=-250, y=0, title="Bank B: first hop")
        net.add_node("ACC_000783", label="Bank C\nAccount 3", color="#DA1E28", size=22, x=0, y=0, title="Bank C: second hop")
        net.add_node("ACC_000215", label="Bank B\nAccount 4", color="#DA1E28", size=22, x=250, y=0, title="Bank B: third hop")
        net.add_node("ACC_000940", label="Bank A\nAccount 5", color="#DA1E28", size=22, x=500, y=0, title="Bank A: loop closes")

        # Benign background nodes
        net.add_node("ACC_BENIGN_1", label="Normal payment\nBank A", color="#0062FF", size=16, x=-250, y=190)
        net.add_node("ACC_BENIGN_2", label="Normal payment\nBank B", color="#0062FF", size=16, x=0, y=190)
        net.add_node("ACC_BENIGN_3", label="Normal payment\nBank C", color="#0062FF", size=16, x=250, y=190)

        # Circular mule ring edges
        net.add_edge("ACC_000102", "ACC_000411", label="$32.5k", color="#FF8389", width=4)
        net.add_edge("ACC_000411", "ACC_000783", label="$31.9k", color="#FF8389", width=4)
        net.add_edge("ACC_000783", "ACC_000215", label="$31.2k", color="#FF8389", width=4)
        net.add_edge("ACC_000215", "ACC_000940", label="$30.6k", color="#FF8389", width=4)
        net.add_edge("ACC_000940", "ACC_000102", label="", color="#DA1E28", width=5)

        # Benign linear edges
        net.add_edge("ACC_BENIGN_1", "ACC_BENIGN_2", label="normal", color="#525252", width=1)
        net.add_edge("ACC_BENIGN_2", "ACC_BENIGN_3", label="normal", color="#525252", width=1)
        net.set_options('{"physics": {"enabled": false}, "interaction": {"hover": true, "dragNodes": false}, "nodes": {"font": {"face": "Arial", "size": 18, "color": "#F4F4F4", "strokeWidth": 3, "strokeColor": "#161616"}, "margin": 10}, "edges": {"font": {"face": "Arial", "size": 14, "color": "#FFFFFF", "strokeWidth": 3, "strokeColor": "#161616"}, "arrows": {"to": {"enabled": true, "scaleFactor": 0.7}}, "smooth": {"type": "curvedCW", "roundness": 0.15}}}')

        html_path = Path(__file__).resolve().parent / "enclave_graph.html"
        net.save_graph(str(html_path))
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        st.components.v1.html(html_content, height=470)
    except Exception as e:
        st.warning(f"Interactive PyVis graph rendering fallback ({e})")


# ==========================================
# PANEL 3: REAL-TIME TRANSACTION FEED
# ==========================================
elif "3." in nav_choice:
    st.subheader("⚡ Try a Transaction")
    st.caption("Choose a sample payment and see how the protected analysis responds before settlement.")
    st.markdown("""
    This is a simulated live feed. Choose a sample payment to see how ZeroMule checks it
    before it is settled, while keeping each bank's raw records private.
    """)

    col_s1, col_s2 = st.columns([1, 1])
    with col_s1:
        stream_speed = st.slider("Streaming Speed (ms between events)", 200, 1500, 600, 100)
    with col_s2:
        decision_tau = st.slider("Enclave Decision Threshold (tau)", 0.30, 0.90, 0.50, 0.05)

    st.write("")
    live_container = st.empty()

    # Pre-canned simulation transactions
    sample_stream = [
        {"id": "TX_90184", "from": "Account 1 (Bank A)", "to": "Account 2 (Bank B)", "amt": "$32,500", "fmt": "Wire", "psi_ms": 1.2, "dp_ms": 0.4, "gat_ms": 11.8, "risk": 0.98, "type": "Ring opening"},
        {"id": "TX_90185", "from": "Account 6 (Bank C)", "to": "Account 7 (Bank A)", "amt": "$840", "fmt": "ACH", "psi_ms": 0.9, "dp_ms": 0.3, "gat_ms": 7.4, "risk": 0.04, "type": "Normal payroll"},
        {"id": "TX_90186", "from": "Account 2 (Bank B)", "to": "Account 3 (Bank C)", "amt": "$31,850", "fmt": "Wire", "psi_ms": 1.1, "dp_ms": 0.4, "gat_ms": 12.1, "risk": 0.99, "type": "Ring relay"},
        {"id": "TX_90187", "from": "Account 8 (Bank A)", "to": "Account 9 (Bank B)", "amt": "$2,100", "fmt": "Cheque", "psi_ms": 0.8, "dp_ms": 0.3, "gat_ms": 8.0, "risk": 0.08, "type": "Normal invoice"},
        {"id": "TX_90188", "from": "Account 5 (Bank A)", "to": "Account 1 (Bank A)", "amt": "$30,000", "fmt": "Wire", "psi_ms": 1.4, "dp_ms": 0.5, "gat_ms": 13.2, "risk": 0.995, "type": "Ring closure"},
    ]

    selected_tx = st.selectbox("Trigger Live Transaction Event:", [f"{tx['id']} - {tx['from']} -> {tx['to']} ({tx['amt']})" for tx in sample_stream])
    tx_idx = [f"{tx['id']} - {tx['from']} -> {tx['to']} ({tx['amt']})" for tx in sample_stream].index(selected_tx)
    tx = sample_stream[tx_idx]

    total_latency = tx["psi_ms"] + tx["dp_ms"] + tx["gat_ms"]

    col_res1, col_res2, col_res3 = st.columns(3)
    with col_res1:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Execution Time</div><div class="metric-val" style="color: #198038;">{total_latency:.1f} ms</div></div>', unsafe_allow_html=True)
    with col_res2:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Enclave Risk Score</div><div class="metric-val" style="color: {"#DA1E28" if tx["risk"] >= decision_tau else "#198038"};">{tx["risk"]:.3f}</div></div>', unsafe_allow_html=True)
    with col_res3:
        sla_pass = total_latency < 30.0
        st.markdown(f'<div class="metric-card"><div class="metric-label">Target SLA (<30ms)</div><div class="metric-val" style="color: #0062FF;">{"PASSED" if sla_pass else "VIOLATED"}</div></div>', unsafe_allow_html=True)

    st.write("")
    if tx["risk"] >= decision_tau:
        st.markdown(f"""
        <div class="alert-freeze">
            <h3 style="color: #DA1E28; margin: 0 0 8px 0;">🛑 PRE-SETTLEMENT SCAM FREEZE TRIGGERED</h3>
            <p style="margin: 0;"><strong>Transaction ID:</strong> {tx['id']} | <strong>Amount:</strong> {tx['amt']} | <strong>Topology:</strong> {tx['type']}</p>
            <p style="margin: 0; font-size: 0.9rem; color: #E0E0E0;">
                Inter-bank settlement suspended automatically within <strong>{total_latency:.1f}ms</strong>.
                Prevented victim balance drainage before ACH/Wire clearing cut-off.
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.success(f"✅ Transaction {tx['id']} Verified & Cleared in {total_latency:.1f}ms. No circular pattern detected.")


# ==========================================
# PANEL 4: BENCHMARKS & FAIRNESS
# ==========================================
elif "4." in nav_choice:
    st.subheader("📊 Evidence & Fairness")
    st.markdown("""
    Rigorous empirical evaluation comparing **ZeroMule** against single-bank isolated baselines,
    privacy utility retention curves, deterministic latency benchmarks, and Equalized-Odds fairness calibration.
    """)

    plots_dir = Path(__file__).resolve().parent.parent / "results" / "plots"

    tab_eval1, tab_eval2, tab_eval3, tab_eval4 = st.tabs([
        "1. PR-AUC Comparison",
        "2. Privacy-Utility Curve",
        "3. Latency Distribution (SLA)",
        "4. Demographic Fairness Parity",
    ])

    with tab_eval1:
        st.markdown("#### 🎯 PR-AUC Comparison: Breaking the Banking Silo")
        st.markdown("Cross-Bank Directed-GIN Enclave (**PR-AUC = 0.892**) vs Isolated Baselines (**PR-AUC = 0.384**).")
        p1 = plots_dir / "pr_auc_comparison.png"
        if p1.exists():
            st.image(str(p1), width="stretch")
        else:
            st.info("Run `python -m src.evaluation.generate_metrics` to generate plots.")

    with tab_eval2:
        st.markdown("#### 🛡️ Privacy-Utility Retention Across Epsilon")
        st.markdown(r"Quantifies PR-AUC preservation under Rényi Differential Privacy bounds $\epsilon \in [0.5, 8.0]$.")
        p2 = plots_dir / "privacy_utility_curve.png"
        if p2.exists():
            st.image(str(p2), width="stretch")
        else:
            st.info("Run `python -m src.evaluation.generate_metrics` to generate plots.")

    with tab_eval3:
        st.markdown("#### ⚡ Hardware-Accelerated Latency CDF (IBM Z / s390x)")
        st.markdown("Cumulative distribution proving deterministic execution under the **30ms P99 SLA**.")
        p3 = plots_dir / "latency_cdf.png"
        if p3.exists():
            st.image(str(p3), width="stretch")
        else:
            st.info("Run `benchmarks/latency_profiler.py` to benchmark latency.")

    with tab_eval4:
        st.markdown("#### ⚖️ Equalized-Odds Demographic Calibration (NeurIPS BAF)")
        st.markdown(r"Eliminating false positive lockout disparity on elderly accounts ($\text{Age} \ge 65$) while preserving 100% scam catch recall.")
        p4 = plots_dir / "fairness_parity.png"
        if p4.exists():
            st.image(str(p4), width="stretch")
        else:
            st.info("Run `python -m src.evaluation.fairness_tuner` to generate plots.")
