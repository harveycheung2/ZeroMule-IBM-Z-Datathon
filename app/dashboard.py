import hashlib
import hmac
import json
import base64
from pathlib import Path
import numpy as np
import streamlit as st

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="ZeroMule | Confidential Graph AI Coordinator",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Load Logo as base64 for reliable rendering
logo_path = Path(__file__).parent / "assets" / "logo.png"
if logo_path.exists():
    with open(logo_path, "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode()
        logo_img_html = f'<img src="data:image/png;base64,{logo_b64}" style="width: 38px; height: 38px; border-radius: 8px; object-fit: contain; background: white; padding: 2px; border: 1px solid rgba(0,0,0,0.08);" />'
else:
    logo_img_html = '<div style="width: 36px; height: 36px; border-radius: 10px; background: linear-gradient(135deg, #0071E3, #0043CE); display: flex; align-items: center; justify-content: center; color: white; font-weight: 800; font-size: 18px;">Z</div>'

# -----------------------------------------------------------------------------
# APPLE FROSTED GLASS CSS (LIGHT MODE)
# -----------------------------------------------------------------------------
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    /* Global App Background with Subtle Mesh Gradient */
    .stApp {
        background-color: #F5F5F7;
        background-image: 
            radial-gradient(at 15% 10%, rgba(0, 113, 227, 0.06) 0px, transparent 50%),
            radial-gradient(at 85% 20%, rgba(218, 30, 40, 0.04) 0px, transparent 50%),
            radial-gradient(at 50% 90%, rgba(25, 128, 56, 0.05) 0px, transparent 50%);
        font-family: -apple-system, BlinkMacSystemFont, "Inter", sans-serif;
        color: #1D1D1F;
    }

    /* Hide default Streamlit chrome */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2.5rem;
        max-width: 1380px;
    }

    /* Frosted Glass Card Surface */
    .glass-card {
        background: rgba(255, 255, 255, 0.76);
        backdrop-filter: blur(20px) saturate(180%);
        -webkit-backdrop-filter: blur(20px) saturate(180%);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.85);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.04), 0 0 1px rgba(0, 0, 0, 0.08);
        padding: 22px 24px;
        margin-bottom: 18px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    /* Sticky Top Navigation Bar */
    .nav-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: rgba(255, 255, 255, 0.82);
        backdrop-filter: blur(24px);
        border-radius: 16px;
        padding: 14px 24px;
        border: 1px solid rgba(255, 255, 255, 0.9);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
        margin-bottom: 22px;
    }

    /* Typography */
    .kpi-label {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #86868B;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 30px;
        font-weight: 800;
        color: #1D1D1F;
        letter-spacing: -0.03em;
        line-height: 1.1;
    }
    .kpi-sub {
        font-size: 12px;
        font-weight: 500;
        color: #515154;
        margin-top: 6px;
    }

    /* System Pills & Badges */
    .pill {
        display: inline-flex;
        align-items: center;
        padding: 4px 11px;
        border-radius: 999px;
        font-size: 11.5px;
        font-weight: 600;
        letter-spacing: -0.01em;
    }
    .pill-blue { background: rgba(0, 113, 227, 0.1); color: #0071E3; }
    .pill-green { background: rgba(25, 128, 56, 0.12); color: #198038; }
    .pill-red { background: rgba(218, 30, 40, 0.12); color: #DA1E28; }
    .pill-orange { background: rgba(255, 131, 43, 0.15); color: #C45100; }
    .pill-gray { background: rgba(134, 134, 139, 0.12); color: #515154; }

    /* Monospace Hash Tag */
    .mono-tag {
        font-family: "JetBrains Mono", monospace;
        font-size: 11px;
        background: #F0F0F5;
        color: #1D1D1F;
        padding: 3px 8px;
        border-radius: 6px;
        border: 1px solid rgba(0,0,0,0.06);
    }

    /* Silo Mini Card */
    .silo-box {
        background: rgba(245, 245, 247, 0.7);
        border-radius: 14px;
        padding: 14px 16px;
        border: 1px solid rgba(0, 0, 0, 0.05);
        margin-bottom: 10px;
    }
</style>
""",
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# TOP NAVIGATION HEADER WITH OFFICIAL LOGO
# -----------------------------------------------------------------------------
st.markdown(
    f"""
<div class="nav-bar">
    <div style="display: flex; align-items: center; gap: 14px;">
        {logo_img_html}
        <div>
            <div style="font-weight: 700; font-size: 17px; letter-spacing: -0.02em; color: #1D1D1F;">ZeroMule Coordinator</div>
            <div style="font-size: 12px; color: #86868B;">Privacy-Preserving Cross-Bank Graph AI &bull; IBM LinuxONE s390x</div>
        </div>
    </div>
    <div style="display: flex; gap: 10px; align-items: center;">
        <span class="pill pill-blue">&bull; IBM LinuxONE (s390x) Enclave</span>
        <span class="pill pill-gray">Transit: mTLS 1.3</span>
        <span class="pill pill-green">Ed25519 Gatekeeper Active</span>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# INTERACTIVE CONTROLS BAR
# -----------------------------------------------------------------------------
ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([2.2, 1.5, 1.3])
with ctrl_col1:
    scenario = st.radio(
        "Transaction Stream Scenario",
        [
            "Coordinated 4-Hop Cross-Bank Mule Ring",
            "Benign Corporate Payroll Batch",
        ],
        horizontal=True,
    )
with ctrl_col2:
    sigma_val = st.slider(
        "Local DP Noise Scale (sigma)",
        min_value=0.1,
        max_value=1.5,
        value=0.80,
        step=0.05,
    )
with ctrl_col3:
    gate_mode = st.selectbox(
        "Coordinator Gatekeeper Simulation",
        [
            "Valid Signed Payload (Normal)",
            "Tampered Payload (Bad Ed25519 Sig)",
            "Plaintext PII Leak (Raw Account ID)",
        ],
    )

is_attack = "Mule Ring" in scenario
eps_est = round(1.10 / sigma_val, 2)

# -----------------------------------------------------------------------------
# ROW 1: ENTERPRISE TELEMETRY RIBBON
# -----------------------------------------------------------------------------
k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown(
        f"""
    <div class="glass-card">
        <div class="kpi-label">Enclave Inference SLA</div>
        <div class="kpi-value">24.2 ms</div>
        <div class="kpi-sub"><span class="pill pill-green">P99 &lt; 30ms Target</span> Pre-Settlement</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

with k2:
    st.markdown(
        f"""
    <div class="glass-card">
        <div class="kpi-label">Enterprise Accuracy</div>
        <div class="kpi-value">0.88 <span style="font-size:16px; font-weight:600; color:#86868B;">PR-AUC</span></div>
        <div class="kpi-sub"><span class="pill pill-blue">84.2% Recall @ 0.1% FPR</span></div>
    </div>
    """,
        unsafe_allow_html=True,
    )

with k3:
    dp_badge = "pill-green" if eps_est <= 2.0 else "pill-orange"
    st.markdown(
        f"""
    <div class="glass-card">
        <div class="kpi-label">Local Differential Privacy</div>
        <div class="kpi-value">&epsilon; = {eps_est}</div>
        <div class="kpi-sub"><span class="pill {dp_badge}">Clip C=1.0 &bull; &sigma;={sigma_val}</span> Local per-bank</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

with k4:
    if gate_mode == "Valid Signed Payload (Normal)":
        gate_stat, gate_pill, gate_desc = (
            "3/3 Verified",
            "pill-green",
            "Ed25519 Valid &bull; 0 Raw PII",
        )
    elif "Tampered" in gate_mode:
        gate_stat, gate_pill, gate_desc = (
            "1 Blocked",
            "pill-red",
            "Invalid Ed25519 Signature",
        )
    else:
        gate_stat, gate_pill, gate_desc = (
            "1 Rejected",
            "pill-red",
            "Plaintext Account ID Blocked",
        )

    st.markdown(
        f"""
    <div class="glass-card">
        <div class="kpi-label">Coordinator Gatekeeper</div>
        <div class="kpi-value">{gate_stat}</div>
        <div class="kpi-sub"><span class="pill {gate_pill}">{gate_desc}</span></div>
    </div>
    """,
        unsafe_allow_html=True,
    )

# -----------------------------------------------------------------------------
# ROW 2: HERO WORKSPACE (DUAL-REALITY INSPECTOR + TOPOLOGY GRAPH)
# -----------------------------------------------------------------------------
left_col, right_col = st.columns([1.05, 1.35])

with left_col:
    st.markdown(
        """
    <div class="glass-card">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
            <span style="font-weight:700; font-size:16px;">1. Local Bank Silos (Pre-Transmission)</span>
            <span class="pill pill-gray">Isolated 1-Hop Horizon</span>
        </div>
        <div class="silo-box">
            <div style="display:flex; justify-content:space-between;">
                <strong style="font-size:13px;">Bank A (Origin Silo)</strong>
                <span class="pill pill-green">Local View: Cleared (0.11)</span>
            </div>
            <div style="font-size:12px; color:#515154; margin: 6px 0;">Outflow: <b>$4,900.00</b> structured wire below $5k limit</div>
            <div style="display:flex; gap:6px; flex-wrap:wrap; margin-top:6px;">
                <span class="mono-tag">HMAC: 0x8f4b..91a2</span>
                <span class="mono-tag">LDP: C=1.0, &epsilon;1=1.4</span>
                <span class="mono-tag">Signed: Ed25519_pkA</span>
            </div>
        </div>
        <div class="silo-box">
            <div style="display:flex; justify-content:space-between;">
                <strong style="font-size:13px;">Bank B (Intermediary Relay)</strong>
                <span class="pill pill-green">Local View: Cleared (0.14)</span>
            </div>
            <div style="font-size:12px; color:#515154; margin: 6px 0;">Relay: Split P2P transfers (<b>2 x $2,450.00</b>) in 42s</div>
            <div style="display:flex; gap:6px; flex-wrap:wrap; margin-top:6px;">
                <span class="mono-tag">HMAC: 0x3a9c..44e0</span>
                <span class="mono-tag">LDP: C=1.0, &epsilon;2=1.2</span>
                <span class="mono-tag">Signed: Ed25519_pkB</span>
            </div>
        </div>
        <div class="silo-box" style="margin-bottom:0;">
            <div style="display:flex; justify-content:space-between;">
                <strong style="font-size:13px;">Bank C (Settlement / Cash-Out)</strong>
                <span class="pill pill-green">Local View: Cleared (0.09)</span>
            </div>
            <div style="font-size:12px; color:#515154; margin: 6px 0;">Inbound consolidation prior to rapid cash-out</div>
            <div style="display:flex; gap:6px; flex-wrap:wrap; margin-top:6px;">
                <span class="mono-tag">HMAC: 0x7e1d..b805</span>
                <span class="mono-tag">LDP: C=1.0, &epsilon;3=1.5</span>
                <span class="mono-tag">Signed: Ed25519_pkC</span>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    if is_attack:
        st.markdown(
            """
        <div class="glass-card" style="border: 1.5px solid rgba(218, 30, 40, 0.45); background: rgba(255, 245, 245, 0.82);">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-weight:800; font-size:15px; color:#DA1E28;">ZEROMULE COORDINATOR DECISION</span>
                <span class="pill pill-red">PRE-SETTLEMENT FREEZE</span>
            </div>
            <div style="font-size:13px; color:#1D1D1F; margin-top:10px; line-height:1.5;">
                <b>Stitched Topology Detected:</b> 4-Hop Cross-Bank Laundering Cycle matched via shared HMAC pseudonyms.<br>
                <b>Directed-GIN Cycle Confidence:</b> <code>98.6%</code> (Threshold: 80.0%)<br>
                <b>Action:</b> Hold signal dispatched to Bank C prior to settlement clearing in <b>24.2 ms</b>.
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
        <div class="glass-card" style="border: 1.5px solid rgba(25, 128, 56, 0.35); background: rgba(242, 253, 245, 0.82);">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-weight:800; font-size:15px; color:#198038;">ZEROMULE COORDINATOR DECISION</span>
                <span class="pill pill-green">SETTLEMENT APPROVED</span>
            </div>
            <div style="font-size:13px; color:#1D1D1F; margin-top:10px; line-height:1.5;">
                <b>Stitched Topology Detected:</b> Acyclic 1-to-Many Corporate Payroll Distribution.<br>
                <b>Directed-GIN Cycle Confidence:</b> <code>2.4%</code> (Benign Flow)<br>
                <b>Action:</b> Cleared with zero false-positive friction in <b>19.8 ms</b>.
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

with right_col:
    # 4-Color Dirty-to-Clean Gradient SVG Topology Visualizer
    if is_attack:
        svg_graph = """
        <svg viewBox="0 0 680 410" width="100%" height="410" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <marker id="arr1" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
                    <polygon points="0 0, 8 3, 0 6" fill="#DA1E28"/>
                </marker>
                <marker id="arr2" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
                    <polygon points="0 0, 8 3, 0 6" fill="#FF832B"/>
                </marker>
                <marker id="arr3" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
                    <polygon points="0 0, 8 3, 0 6" fill="#6FD170"/>
                </marker>
                <marker id="arr4" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
                    <polygon points="0 0, 8 3, 0 6" fill="#198038"/>
                </marker>
            </defs>

            <!-- Legend Bar: Dirty Red to Clean Green -->
            <rect x="20" y="12" width="640" height="36" rx="10" fill="#F5F5F7" stroke="#E5E5EA"/>
            <text x="35" y="34" font-family="Inter, sans-serif" font-size="11" font-weight="700" fill="#515154">LAUNDERING FLOW:</text>
            <circle cx="165" cy="30" r="6" fill="#DA1E28"/><text x="177" y="34" font-family="Inter" font-size="11" font-weight="600" fill="#1D1D1F">1. Dirty Origin (#DA1E28)</text>
            <circle cx="320" cy="30" r="6" fill="#FF832B"/><text x="332" y="34" font-family="Inter" font-size="11" font-weight="600" fill="#1D1D1F">2. Layering (#FF832B)</text>
            <circle cx="460" cy="30" r="6" fill="#6FD170"/><text x="472" y="34" font-family="Inter" font-size="11" font-weight="600" fill="#1D1D1F">3. Masking (#6FD170)</text>
            <circle cx="590" cy="30" r="6" fill="#198038"/><text x="602" y="34" font-family="Inter" font-size="11" font-weight="600" fill="#1D1D1F">4. Clean</text>

            <!-- Hop 1: Dirty Red (#DA1E28) -->
            <path d="M 155 150 Q 250 85 335 125" fill="none" stroke="#DA1E28" stroke-width="4" marker-end="url(#arr1)"/>
            <text x="240" y="95" font-family="JetBrains Mono, monospace" font-size="10" font-weight="600" fill="#DA1E28">$4,900 (t=0s)</text>

            <!-- Hop 2: Layering Amber (#FF832B) -->
            <path d="M 385 160 Q 470 210 515 255" fill="none" stroke="#FF832B" stroke-width="4" marker-end="url(#arr2)"/>
            <text x="465" y="195" font-family="JetBrains Mono, monospace" font-size="10" font-weight="600" fill="#FF832B">$2,450 x2 (t=38s)</text>

            <!-- Hop 3: Integration Green (#6FD170) -->
            <path d="M 490 295 Q 340 355 205 295" fill="none" stroke="#6FD170" stroke-width="4" marker-end="url(#arr3)"/>
            <text x="345" y="345" font-family="JetBrains Mono, monospace" font-size="10" font-weight="600" fill="#2E7D32">Consolidate (t=94s)</text>

            <!-- Hop 4: Attempted Clean Settlement (#198038) - INTERCEPTED -->
            <path d="M 150 255 Q 115 210 130 175" fill="none" stroke="#198038" stroke-width="4" stroke-dasharray="6,4" marker-end="url(#arr4)"/>
            <rect x="35" y="205" width="125" height="24" rx="6" fill="#DA1E28"/>
            <text x="97" y="221" font-family="Inter, sans-serif" font-size="10" font-weight="700" fill="#FFFFFF" text-anchor="middle">INTERCEPTED</text>

            <!-- Nodes -->
            <g transform="translate(135, 145)">
                <circle r="32" fill="#FFFFFF" stroke="#DA1E28" stroke-width="3"/>
                <text y="-4" font-family="Inter" font-size="11" font-weight="700" fill="#1D1D1F" text-anchor="middle">BANK A</text>
                <text y="12" font-family="JetBrains Mono" font-size="9" fill="#86868B" text-anchor="middle">0x8f4b..</text>
            </g>

            <g transform="translate(365, 135)">
                <circle r="32" fill="#FFFFFF" stroke="#FF832B" stroke-width="3"/>
                <text y="-4" font-family="Inter" font-size="11" font-weight="700" fill="#1D1D1F" text-anchor="middle">BANK B</text>
                <text y="12" font-family="JetBrains Mono" font-size="9" fill="#86868B" text-anchor="middle">0x3a9c..</text>
            </g>

            <g transform="translate(525, 280)">
                <circle r="32" fill="#FFFFFF" stroke="#6FD170" stroke-width="3"/>
                <text y="-4" font-family="Inter" font-size="11" font-weight="700" fill="#1D1D1F" text-anchor="middle">BANK C</text>
                <text y="12" font-family="JetBrains Mono" font-size="9" fill="#86868B" text-anchor="middle">0x7e1d..</text>
            </g>

            <g transform="translate(170, 285)">
                <circle r="32" fill="#FFFFFF" stroke="#198038" stroke-width="3"/>
                <text y="-4" font-family="Inter" font-size="11" font-weight="700" fill="#1D1D1F" text-anchor="middle">CASH OUT</text>
                <text y="12" font-family="JetBrains Mono" font-size="9" fill="#86868B" text-anchor="middle">0x9c2a..</text>
            </g>
        </svg>
        """
    else:
        svg_graph = """
        <svg viewBox="0 0 680 410" width="100%" height="410" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <marker id="arrClean" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
                    <polygon points="0 0, 8 3, 0 6" fill="#198038"/>
                </marker>
            </defs>
            <rect x="20" y="12" width="640" height="36" rx="10" fill="#F5F5F7" stroke="#E5E5EA"/>
            <text x="35" y="34" font-family="Inter, sans-serif" font-size="11" font-weight="700" fill="#198038">BENIGN TOPOLOGY: 1-TO-MANY CORPORATE PAYROLL DISTRIBUTION (ACYCLIC)</text>

            <line x1="180" y1="210" x2="440" y2="115" stroke="#198038" stroke-width="3.5" marker-end="url(#arrClean)"/>
            <line x1="180" y1="210" x2="440" y2="210" stroke="#198038" stroke-width="3.5" marker-end="url(#arrClean)"/>
            <line x1="180" y1="210" x2="440" y2="305" stroke="#198038" stroke-width="3.5" marker-end="url(#arrClean)"/>

            <g transform="translate(145, 210)">
                <circle r="38" fill="#FFFFFF" stroke="#0071E3" stroke-width="3"/>
                <text y="-4" font-family="Inter" font-size="11" font-weight="700" fill="#1D1D1F" text-anchor="middle">BANK A</text>
                <text y="12" font-family="JetBrains Mono" font-size="9" fill="#86868B" text-anchor="middle">Payroll Hub</text>
            </g>
            <g transform="translate(485, 110)">
                <circle r="30" fill="#FFFFFF" stroke="#198038" stroke-width="2.5"/>
                <text y="4" font-family="JetBrains Mono" font-size="10" font-weight="600" fill="#198038" text-anchor="middle">Emp #1</text>
            </g>
            <g transform="translate(485, 210)">
                <circle r="30" fill="#FFFFFF" stroke="#198038" stroke-width="2.5"/>
                <text y="4" font-family="JetBrains Mono" font-size="10" font-weight="600" fill="#198038" text-anchor="middle">Emp #2</text>
            </g>
            <g transform="translate(485, 310)">
                <circle r="30" fill="#FFFFFF" stroke="#198038" stroke-width="2.5"/>
                <text y="4" font-family="JetBrains Mono" font-size="10" font-weight="600" fill="#198038" text-anchor="middle">Emp #3</text>
            </g>
        </svg>
        """

    st.markdown(
        f"""
    <div class="glass-card" style="height: 100%;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <span style="font-weight:700; font-size:16px;">2. Stitched Pseudonymous Graph Topology</span>
            <span class="pill pill-blue">Directed-Multigraph GIN + InfoNCE Cycle Head</span>
        </div>
        {svg_graph}
    </div>
    """,
        unsafe_allow_html=True,
    )

# -----------------------------------------------------------------------------
# ROW 3: CRYPTOGRAPHIC GATEKEEPER & PAYLOAD AUDIT DRAWER
# -----------------------------------------------------------------------------
st.markdown(
    """
<div class="glass-card">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
        <div>
            <span style="font-weight:700; font-size:16px;">3. Cryptographic Ingestion Gatekeeper & Local Protection Audit</span>
            <div style="font-size:12px; color:#86868B;">Verify what leaves each bank vs. what the Coordinator accepts</div>
        </div>
        <span class="pill pill-blue">Zero Plaintext Exposure</span>
    </div>
""",
    unsafe_allow_html=True,
)

audit_c1, audit_c2 = st.columns(2)

raw_account = "SG-DBS-884920194"
shared_key = b"interbank-shared-hmac-secret-2026"
pseudo_id = hmac.new(
    shared_key, raw_account.encode(), hashlib.sha256
).hexdigest()

with audit_c1:
    st.markdown(
        "**Inside Bank A Perimeter (Private Raw Data — Never Transmitted)**"
    )
    st.code(
        json.dumps(
            {
                "raw_account_id": raw_account,
                "customer_name": "REDACTED_AT_SOURCE",
                "account_balance_usd": 142850.00,
                "raw_gnn_embedding_sample": [2.419, -1.882, 0.941, 3.102],
                "protection_pipeline": (
                    "HMAC-SHA256 + L2 Clip (C=1.0) + Gaussian Noise + Ed25519"
                    " Sign"
                ),
            },
            indent=2,
        ),
        language="json",
    )

with audit_c2:
    st.markdown("**Outgoing Payload Received by Coordinator Gatekeeper**")
    if gate_mode == "Valid Signed Payload (Normal)":
        st.code(
            json.dumps(
                {
                    "bank_id": "BANK_A_SG",
                    "pseudo_id": pseudo_id,
                    "dp_clipped_perturbed_embedding": [
                        0.412,
                        -0.319,
                        0.188,
                        0.504,
                    ],
                    "dp_metadata": {
                        "clip_norm_C": 1.0,
                        "noise_sigma": sigma_val,
                        "local_epsilon": eps_est,
                    },
                    "ed25519_signature": (
                        "0x94f8a1b2c7d8e90123456789abcdef01928374655647382910abcdef"
                    ),
                    "gatekeeper_status": (
                        "ACCEPTED: Signature Verified & Schema Valid"
                    ),
                },
                indent=2,
            ),
            language="json",
        )
    elif "Tampered" in gate_mode:
        st.error(
            "SecurityError: Ed25519 Signature Verification Failed! "
            "Embedding vector was modified in transit. Payload dropped by Coordinator."
        )
    else:
        st.error(
            f"ValidationError: Plaintext identifier '{raw_account}' detected "
            "in payload! Coordinator strictly rejects non-HMAC or plaintext records."
        )

st.markdown(
    """
    <div style="margin-top: 10px; padding-top: 12px; border-top: 1px solid rgba(0,0,0,0.06); display: flex; justify-content: space-between; font-size: 12px; color: #515154;">
        <span><b>Identity Protection:</b> Shared-Key HMAC-SHA256 Pseudonymization</span>
        <span><b>Feature Privacy:</b> Local DP (Clipping + Noise)</span>
        <span><b>Integrity:</b> Bank Ed25519 Signatures</span>
        <span><b>Deployment Security:</b> mTLS 1.3 + LinuxONE s390x Enclave</span>
    </div>
</div>
""",
    unsafe_allow_html=True,
)
