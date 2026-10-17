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

    .stApp {
        background-color: #F5F5F7;
        background-image: 
            radial-gradient(at 15% 10%, rgba(0, 113, 227, 0.06) 0px, transparent 50%),
            radial-gradient(at 85% 20%, rgba(218, 30, 40, 0.04) 0px, transparent 50%),
            radial-gradient(at 50% 90%, rgba(25, 128, 56, 0.05) 0px, transparent 50%);
        font-family: -apple-system, BlinkMacSystemFont, "Inter", sans-serif;
        color: #1D1D1F;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2.5rem;
        max-width: 1400px;
    }

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

    .nav-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: rgba(255, 255, 255, 0.82);
        backdrop-filter: blur(24px);
        border-radius: 16px;
        padding: 12px 24px;
        border: 1px solid rgba(255, 255, 255, 0.9);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
        margin-bottom: 16px;
    }

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

    .mono-tag {
        font-family: "JetBrains Mono", monospace;
        font-size: 11px;
        background: #F0F0F5;
        color: #1D1D1F;
        padding: 3px 8px;
        border-radius: 6px;
        border: 1px solid rgba(0,0,0,0.06);
    }

    .silo-box {
        background: rgba(245, 245, 247, 0.7);
        border-radius: 14px;
        padding: 14px 16px;
        border: 1px solid rgba(0, 0, 0, 0.05);
        margin-bottom: 10px;
    }

    .boundary-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 9px 12px;
        background: rgba(245, 245, 247, 0.7);
        border-radius: 8px;
        font-size: 12px;
        margin-bottom: 8px;
        border: 1px solid rgba(0, 0, 0, 0.04);
    }

    table.apple-table-st {
        width: 100%;
        border-collapse: collapse;
        font-size: 12px;
    }
    table.apple-table-st th {
        text-align: left;
        padding: 8px 10px;
        font-size: 11px;
        font-weight: 700;
        color: #86868B;
        border-bottom: 1px solid #E5E5EA;
    }
    table.apple-table-st td {
        padding: 10px 10px;
        border-bottom: 1px solid rgba(0,0,0,0.04);
        color: #1D1D1F;
    }
</style>
""",
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# TOP NAVIGATION HEADER WITH OFFICIAL LOGO & VIEW SWITCHER
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
        <span class="pill pill-blue">&bull; IBM LinuxONE s390x Enclave</span>
        <span class="pill pill-gray">Transit: mTLS 1.3</span>
        <span class="pill pill-green">&#10003; Gatekeeper Active</span>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# 3-Page Navigation Tabs
view_mode = st.radio(
    "Navigation View",
    ["Information View", "Singular Bank View", "Screening Overview"],
    horizontal=True,
    label_visibility="collapsed",
)

# =============================================================================
# VIEW 1: INFORMATION VIEW (COORDINATOR & JUDGE MASTER SPECIFICATION)
# =============================================================================
if view_mode == "Information View":

    # Interactive Controls Bar
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

    # Telemetry Ribbon
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

    # Hero Workspace: Dual Reality Silo vs Coordinator + Topology SVG
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
        if is_attack:
            svg_graph = """
            <svg viewBox="0 0 680 410" width="100%" height="410" xmlns="http://www.w3.org/2000/svg">
                <defs>
                    <marker id="arr1" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="#DA1E28"/></marker>
                    <marker id="arr2" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="#FF832B"/></marker>
                    <marker id="arr3" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="#6FD170"/></marker>
                    <marker id="arr4" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="#198038"/></marker>
                </defs>
                <rect x="20" y="12" width="640" height="36" rx="10" fill="#F5F5F7" stroke="#E5E5EA"/>
                <text x="35" y="34" font-family="Inter, sans-serif" font-size="11" font-weight="700" fill="#515154">LAUNDERING FLOW:</text>
                <circle cx="165" cy="30" r="6" fill="#DA1E28"/><text x="177" y="34" font-family="Inter" font-size="11" font-weight="600" fill="#1D1D1F">1. Dirty Origin (#DA1E28)</text>
                <circle cx="320" cy="30" r="6" fill="#FF832B"/><text x="332" y="34" font-family="Inter" font-size="11" font-weight="600" fill="#1D1D1F">2. Layering (#FF832B)</text>
                <circle cx="460" cy="30" r="6" fill="#6FD170"/><text x="472" y="34" font-family="Inter" font-size="11" font-weight="600" fill="#1D1D1F">3. Masking (#6FD170)</text>
                <circle cx="590" cy="30" r="6" fill="#198038"/><text x="602" y="34" font-family="Inter" font-size="11" font-weight="600" fill="#1D1D1F">4. Clean</text>
                <path d="M 155 150 Q 250 85 335 125" fill="none" stroke="#DA1E28" stroke-width="4" marker-end="url(#arr1)"/>
                <text x="240" y="95" font-family="JetBrains Mono, monospace" font-size="10" font-weight="600" fill="#DA1E28">$4,900 (t=0s)</text>
                <path d="M 385 160 Q 470 210 515 255" fill="none" stroke="#FF832B" stroke-width="4" marker-end="url(#arr2)"/>
                <text x="465" y="195" font-family="JetBrains Mono, monospace" font-size="10" font-weight="600" fill="#FF832B">$2,450 x2 (t=38s)</text>
                <path d="M 490 295 Q 340 355 205 295" fill="none" stroke="#6FD170" stroke-width="4" marker-end="url(#arr3)"/>
                <text x="345" y="345" font-family="JetBrains Mono, monospace" font-size="10" font-weight="600" fill="#2E7D32">Consolidate (t=94s)</text>
                <path d="M 150 255 Q 115 210 130 175" fill="none" stroke="#198038" stroke-width="4" stroke-dasharray="6,4" marker-end="url(#arr4)"/>
                <rect x="35" y="205" width="125" height="24" rx="6" fill="#DA1E28"/>
                <text x="97" y="221" font-family="Inter, sans-serif" font-size="10" font-weight="700" fill="#FFFFFF" text-anchor="middle">INTERCEPTED</text>
                <g transform="translate(135, 145)"><circle r="32" fill="#FFFFFF" stroke="#DA1E28" stroke-width="3"/><text y="-4" font-family="Inter" font-size="11" font-weight="700" fill="#1D1D1F" text-anchor="middle">BANK A</text><text y="12" font-family="JetBrains Mono" font-size="9" fill="#86868B" text-anchor="middle">0x8f4b..</text></g>
                <g transform="translate(365, 135)"><circle r="32" fill="#FFFFFF" stroke="#FF832B" stroke-width="3"/><text y="-4" font-family="Inter" font-size="11" font-weight="700" fill="#1D1D1F" text-anchor="middle">BANK B</text><text y="12" font-family="JetBrains Mono" font-size="9" fill="#86868B" text-anchor="middle">0x3a9c..</text></g>
                <g transform="translate(525, 280)"><circle r="32" fill="#FFFFFF" stroke="#6FD170" stroke-width="3"/><text y="-4" font-family="Inter" font-size="11" font-weight="700" fill="#1D1D1F" text-anchor="middle">BANK C</text><text y="12" font-family="JetBrains Mono" font-size="9" fill="#86868B" text-anchor="middle">0x7e1d..</text></g>
                <g transform="translate(170, 285)"><circle r="32" fill="#FFFFFF" stroke="#198038" stroke-width="3"/><text y="-4" font-family="Inter" font-size="11" font-weight="700" fill="#1D1D1F" text-anchor="middle">CASH OUT</text><text y="12" font-family="JetBrains Mono" font-size="9" fill="#86868B" text-anchor="middle">0x9c2a..</text></g>
            </svg>
            """
        else:
            svg_graph = """
            <svg viewBox="0 0 680 410" width="100%" height="410" xmlns="http://www.w3.org/2000/svg">
                <defs><marker id="arrClean" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="#198038"/></marker></defs>
                <rect x="20" y="12" width="640" height="36" rx="10" fill="#F5F5F7" stroke="#E5E5EA"/>
                <text x="35" y="34" font-family="Inter, sans-serif" font-size="11" font-weight="700" fill="#198038">BENIGN TOPOLOGY: 1-TO-MANY CORPORATE PAYROLL DISTRIBUTION (ACYCLIC)</text>
                <line x1="180" y1="210" x2="440" y2="115" stroke="#198038" stroke-width="3.5" marker-end="url(#arrClean)"/>
                <line x1="180" y1="210" x2="440" y2="210" stroke="#198038" stroke-width="3.5" marker-end="url(#arrClean)"/>
                <line x1="180" y1="210" x2="440" y2="305" stroke="#198038" stroke-width="3.5" marker-end="url(#arrClean)"/>
                <g transform="translate(145, 210)"><circle r="38" fill="#FFFFFF" stroke="#0071E3" stroke-width="3"/><text y="-4" font-family="Inter" font-size="11" font-weight="700" fill="#1D1D1F" text-anchor="middle">BANK A</text><text y="12" font-family="JetBrains Mono" font-size="9" fill="#86868B" text-anchor="middle">Payroll Hub</text></g>
                <g transform="translate(485, 110)"><circle r="30" fill="#FFFFFF" stroke="#198038" stroke-width="2.5"/><text y="4" font-family="JetBrains Mono" font-size="10" font-weight="600" fill="#198038" text-anchor="middle">Emp #1</text></g>
                <g transform="translate(485, 210)"><circle r="30" fill="#FFFFFF" stroke="#198038" stroke-width="2.5"/><text y="4" font-family="JetBrains Mono" font-size="10" font-weight="600" fill="#198038" text-anchor="middle">Emp #2</text></g>
                <g transform="translate(485, 310)"><circle r="30" fill="#FFFFFF" stroke="#198038" stroke-width="2.5"/><text y="4" font-family="JetBrains Mono" font-size="10" font-weight="600" fill="#198038" text-anchor="middle">Emp #3</text></g>
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

    # Bottom Row: Cryptographic Gatekeeper & Payload Audit Drawer
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
                        "HMAC-SHA256 + L2 Clip (C=1.0) + Gaussian Noise +"
                        " Ed25519 Sign"
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
                "Embedding vector was modified in transit. Payload dropped by"
                " Coordinator."
            )
        else:
            st.error(
                f"ValidationError: Plaintext identifier '{raw_account}'"
                " detected in payload! Coordinator strictly rejects non-HMAC or"
                " plaintext records."
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

# =============================================================================
# VIEW 2: SINGULAR BANK VIEW (WHAT EACH BANK SEES INTERNALLY)
# =============================================================================
elif view_mode == "Singular Bank View":

    bank_choice = st.radio(
        "Participating Institution",
        [
            "Bank A (Origin Silo &bull; Wire Hub)",
            "Bank B (Intermediary Relay &bull; P2P)",
            "Bank C (Settlement &bull; Cash-Out)",
        ],
        horizontal=True,
    )

    bank_map = {
        "Bank A": {
            "id": "BANK_A_SG",
            "role": "Originating Silo (Outbound High-Value Wire Processing)",
            "key": "Ed25519_skA",
            "volume": "$14.2M",
            "vol_count": "48,120 Transactions Today",
            "stopped": "14 Txs",
            "stopped_val": "$184,200 Stopped",
            "suspicious": "42 Txs",
            "budget": "1.35",
            "txs": [
                ("TX-A-9810", "18s ago", "ACC-884920", "$4,900.00", "Bank B", "Cleared (0.11)", "PRE-SETTLEMENT FREEZE", "pill-red"),
                ("TX-A-9804", "2m ago", "ACC-712390", "$3,450.00", "Bank C", "Cleared (0.08)", "SETTLEMENT APPROVED", "pill-green"),
                ("TX-A-9798", "5m ago", "ACC-992384", "$4,850.00", "Bank B", "Suspicious (0.68)", "ENCLAVE REVIEW", "pill-orange"),
                ("TX-A-9791", "9m ago", "ACC-120488", "$12,400.00", "Bank C", "Cleared (0.05)", "SETTLEMENT APPROVED", "pill-green"),
            ]
        },
        "Bank B": {
            "id": "BANK_B_SG",
            "role": "Intermediary Relay (High-Frequency Split P2P Transfers)",
            "key": "Ed25519_skB",
            "volume": "$11.8M",
            "vol_count": "39,410 Transactions Today",
            "stopped": "19 Txs",
            "stopped_val": "$242,000 Stopped",
            "suspicious": "58 Txs",
            "budget": "1.20",
            "txs": [
                ("TX-B-4412", "12s ago", "ACC-319044", "$2,450.00", "Bank C", "Cleared (0.14)", "PRE-SETTLEMENT FREEZE", "pill-red"),
                ("TX-B-4409", "38s ago", "ACC-319044", "$2,450.00", "Bank C", "Cleared (0.14)", "PRE-SETTLEMENT FREEZE", "pill-red"),
                ("TX-B-4401", "3m ago", "ACC-662910", "$750.00", "Bank A", "Cleared (0.03)", "SETTLEMENT APPROVED", "pill-green"),
                ("TX-B-4395", "6m ago", "ACC-881204", "$2,400.00", "Bank C", "Suspicious (0.75)", "ENCLAVE REVIEW", "pill-orange"),
            ]
        },
        "Bank C": {
            "id": "BANK_C_SG",
            "role": "Settlement / Cash-Out Endpoint (Rapid Liquidation Defense)",
            "key": "Ed25519_skC",
            "volume": "$8.8M",
            "vol_count": "28,340 Transactions Today",
            "stopped": "28 Txs",
            "stopped_val": "$385,900 Stopped",
            "suspicious": "81 Txs",
            "budget": "1.50",
            "txs": [
                ("TX-C-1940", "8s ago", "ACC-772810", "$4,900.00", "ATM Cash Out", "Cleared (0.09)", "PRE-SETTLEMENT FREEZE", "pill-red"),
                ("TX-C-1935", "45s ago", "ACC-994821", "$4,800.00", "Crypto Exch", "Cleared (0.10)", "PRE-SETTLEMENT FREEZE", "pill-red"),
                ("TX-C-1928", "2m ago", "ACC-331902", "$142.50", "Merchant POS", "Cleared (0.01)", "SETTLEMENT APPROVED", "pill-green"),
                ("TX-C-1921", "5m ago", "ACC-552910", "$4,750.00", "Wire Settled", "Suspicious (0.78)", "ENCLAVE REVIEW", "pill-orange"),
            ]
        }
    }

    selected_key = "Bank A" if "Bank A" in bank_choice else "Bank B" if "Bank B" in bank_choice else "Bank C"
    b_info = bank_map[selected_key]

    # Telemetry
    bk1, bk2, bk3, bk4 = st.columns(4)
    with bk1:
        st.markdown(f"""
        <div class="glass-card">
            <div class="kpi-label">Local Volume Screened</div>
            <div class="kpi-value">{b_info['volume']}</div>
            <div class="kpi-sub"><span class="pill pill-blue">{b_info['vol_count']}</span></div>
        </div>
        """, unsafe_allow_html=True)
    with bk2:
        st.markdown(f"""
        <div class="glass-card">
            <div class="kpi-label">Fraud Frozen Pre-Settlement</div>
            <div class="kpi-value" style="color:#DA1E28;">{b_info['stopped']}</div>
            <div class="kpi-sub"><span class="pill pill-red">{b_info['stopped_val']}</span> Held</div>
        </div>
        """, unsafe_allow_html=True)
    with bk3:
        st.markdown(f"""
        <div class="glass-card">
            <div class="kpi-label">Suspicious / Under Review</div>
            <div class="kpi-value" style="color:#C45100;">{b_info['suspicious']}</div>
            <div class="kpi-sub"><span class="pill pill-orange">Cross-Bank Cycle Risk</span> Enclave Queue</div>
        </div>
        """, unsafe_allow_html=True)
    with bk4:
        st.markdown(f"""
        <div class="glass-card">
            <div class="kpi-label">Local DP Budget Consumption</div>
            <div class="kpi-value">&epsilon; = {b_info['budget']}</div>
            <div class="kpi-sub"><span class="pill pill-green">Max &epsilon; &le; 2.00</span> SQLite Atomic Guard</div>
        </div>
        """, unsafe_allow_html=True)

    # Hero Row
    b_col1, b_col2 = st.columns([1.1, 1.1])
    with b_col1:
        st.markdown(f"""
        <div class="glass-card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <span style="font-weight:700; font-size:16px;">Local Risk Score & Velocity Distribution</span>
                <span class="pill pill-gray">{selected_key} Horizon</span>
            </div>
            <svg viewBox="0 0 540 240" width="100%" height="240" xmlns="http://www.w3.org/2000/svg">
                <line x1="45" y1="190" x2="505" y2="190" stroke="#E5E5EA" stroke-width="1.5"/>
                <line x1="45" y1="30" x2="45" y2="190" stroke="#E5E5EA" stroke-width="1.5"/>
                <line x1="360" y1="30" x2="360" y2="190" stroke="#DA1E28" stroke-width="1.5" stroke-dasharray="4,4"/>
                <text x="365" y="45" font-family="Inter" font-size="10" font-weight="700" fill="#DA1E28">Freeze Threshold (0.80)</text>
                <text x="45" y="210" font-family="JetBrains Mono" font-size="9" fill="#86868B">0.0 (Benign)</text>
                <text x="240" y="210" font-family="JetBrains Mono" font-size="9" fill="#86868B">0.5 (Review)</text>
                <text x="450" y="210" font-family="JetBrains Mono" font-size="9" fill="#86868B">1.0 (Critical)</text>
                <path d="M 45 185 Q 110 180 150 120 Q 190 35 220 35 Q 250 35 290 130 Q 330 180 500 188" fill="none" stroke="#0071E3" stroke-width="3"/>
                <circle cx="430" cy="55" r="7" fill="#DA1E28"/>
                <circle cx="445" cy="68" r="6" fill="#DA1E28"/>
                <text x="400" y="40" font-family="Inter" font-size="10.5" font-weight="700" fill="#DA1E28">Intercepted ({b_info['stopped']})</text>
            </svg>
        </div>
        """, unsafe_allow_html=True)

    with b_col2:
        st.markdown(f"""
        <div class="glass-card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <span style="font-weight:700; font-size:16px;">Local Privacy Release Boundary</span>
                <span class="pill pill-green">Perimeter Enforced</span>
            </div>
            <div class="boundary-row">
                <span style="color:#515154; font-weight:600;">Institutional Role:</span>
                <strong>{b_info['role']}</strong>
            </div>
            <div class="boundary-row">
                <span style="color:#515154; font-weight:600;">Local SQLite Ledger:</span>
                <code>/data/bank_ledger.sqlite (&epsilon; &le; 2.0)</code>
            </div>
            <div class="boundary-row">
                <span style="color:#515154; font-weight:600;">Signing Key Provenance:</span>
                <code>{b_info['key']} (Pinned in Enclave)</code>
            </div>
            <div class="boundary-row">
                <span style="color:#515154; font-weight:600;">Perturbation Pipeline:</span>
                <strong>L2 Clip (C=1.0) + CSPRNG Gaussian Noise</strong>
            </div>
            <div class="boundary-row">
                <span style="color:#515154; font-weight:600;">Plaintext Protection:</span>
                <span class="pill pill-green">0 Raw Account IDs Leave Perimeter</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Local Transactions Table
    st.markdown(f"""
    <div class="glass-card">
        <div style="font-weight:700; font-size:16px; margin-bottom:12px;">{selected_key} Local Transaction Screening Stream</div>
        <table class="apple-table-st">
            <thead>
                <tr>
                    <th>Tx ID</th>
                    <th>Time</th>
                    <th>Account</th>
                    <th>Amount</th>
                    <th>Counterparty</th>
                    <th>Local View</th>
                    <th>Coordinator Action</th>
                </tr>
            </thead>
            <tbody>
                {''.join([f"<tr><td><b>{t[0]}</b></td><td>{t[1]}</td><td><code>{t[2]}</code></td><td><b>{t[3]}</b></td><td>{t[4]}</td><td><span class='pill pill-gray'>{t[5]}</span></td><td><span class='pill {t[7]}'>{t[6]}</span></td></tr>" for t in b_info['txs']])}
            </tbody>
        </table>
    </div>
    """, unsafe_allow_html=True)

# =============================================================================
# VIEW 3: SCREENING OVERVIEW (CROSS-BANK ANALYTICS & GLOBAL FEED)
# =============================================================================
else:
    # Network Ribbon
    ok1, ok2, ok3, ok4 = st.columns(4)
    with ok1:
        st.markdown("""
        <div class="glass-card">
            <div class="kpi-label">Total Transactions Screened</div>
            <div class="kpi-value">142,890</div>
            <div class="kpi-sub"><span class="pill pill-blue">$34.82M Volume</span> Across 3 Institutions</div>
        </div>
        """, unsafe_allow_html=True)
    with ok2:
        st.markdown("""
        <div class="glass-card">
            <div class="kpi-label">Mule Syndicates Intercepted</div>
            <div class="kpi-value" style="color:#DA1E28;">38 Rings</div>
            <div class="kpi-sub"><span class="pill pill-red">$1,842,500 Illicit Funds</span> Pre-Settlement</div>
        </div>
        """, unsafe_allow_html=True)
    with ok3:
        st.markdown("""
        <div class="glass-card">
            <div class="kpi-label">Pre-Settlement Interception Rate</div>
            <div class="kpi-value" style="color:#198038;">99.2%</div>
            <div class="kpi-sub"><span class="pill pill-green">Stopped at Hop 3</span> Zero Cash-Out Leak</div>
        </div>
        """, unsafe_allow_html=True)
    with ok4:
        st.markdown("""
        <div class="glass-card">
            <div class="kpi-label">Network Inference Latency</div>
            <div class="kpi-value">24.2 ms</div>
            <div class="kpi-sub"><span class="pill pill-gray">P50: 16.8 ms</span> &lt; 30ms RTGS SLA</div>
        </div>
        """, unsafe_allow_html=True)

    # 2 Analytical Graphs
    chart_c1, chart_c2 = st.columns(2)
    with chart_c1:
        st.markdown("""
        <div class="glass-card">
            <div style="font-weight:700; font-size:16px; margin-bottom:10px;">24-Hour Screening Velocity & Interceptions</div>
            <svg viewBox="0 0 540 230" width="100%" height="230" xmlns="http://www.w3.org/2000/svg">
                <line x1="45" y1="185" x2="505" y2="185" stroke="#E5E5EA" stroke-width="1.5"/>
                <line x1="45" y1="20" x2="45" y2="185" stroke="#E5E5EA" stroke-width="1.5"/>
                <text x="45" y="205" font-family="JetBrains Mono" font-size="9" fill="#86868B">00:00</text>
                <text x="160" y="205" font-family="JetBrains Mono" font-size="9" fill="#86868B">06:00</text>
                <text x="275" y="205" font-family="JetBrains Mono" font-size="9" fill="#86868B">12:00</text>
                <text x="390" y="205" font-family="JetBrains Mono" font-size="9" fill="#86868B">18:00</text>
                <text x="485" y="205" font-family="JetBrains Mono" font-size="9" fill="#86868B">Now</text>
                <path d="M 45 160 Q 100 150 150 120 T 260 75 T 380 90 T 500 60 L 500 185 L 45 185 Z" fill="rgba(0, 113, 227, 0.12)"/>
                <path d="M 45 160 Q 100 150 150 120 T 260 75 T 380 90 T 500 60" fill="none" stroke="#0071E3" stroke-width="3"/>
                <rect x="165" y="95" width="8" height="90" rx="3" fill="#DA1E28"/>
                <rect x="270" y="60" width="8" height="125" rx="3" fill="#DA1E28"/>
                <rect x="390" y="75" width="8" height="110" rx="3" fill="#DA1E28"/>
                <rect x="475" y="45" width="8" height="140" rx="3" fill="#DA1E28"/>
            </svg>
        </div>
        """, unsafe_allow_html=True)

    with chart_c2:
        st.markdown("""
        <div class="glass-card">
            <div style="font-weight:700; font-size:16px; margin-bottom:10px;">Syndicate Topology & Hop Distribution</div>
            <svg viewBox="0 0 540 230" width="100%" height="230" xmlns="http://www.w3.org/2000/svg">
                <line x1="140" y1="20" x2="140" y2="190" stroke="#E5E5EA" stroke-width="1.5"/>
                <text x="125" y="55" font-family="Inter" font-size="11" font-weight="700" fill="#1D1D1F" text-anchor="end">4-Hop Rings</text>
                <rect x="140" y="40" width="240" height="24" rx="6" fill="#DA1E28"/>
                <text x="390" y="56" font-family="JetBrains Mono" font-size="10.5" font-weight="700" fill="#DA1E28">58% (22 Rings)</text>

                <text x="125" y="105" font-family="Inter" font-size="11" font-weight="700" fill="#1D1D1F" text-anchor="end">3-Hop Cycles</text>
                <rect x="140" y="90" width="100" height="24" rx="6" fill="#FF832B"/>
                <text x="250" y="106" font-family="JetBrains Mono" font-size="10.5" font-weight="700" fill="#C45100">24% (9 Rings)</text>

                <text x="125" y="155" font-family="Inter" font-size="11" font-weight="700" fill="#1D1D1F" text-anchor="end">5+ Hop Meshes</text>
                <rect x="140" y="140" width="75" height="24" rx="6" fill="#6FD170"/>
                <text x="225" y="156" font-family="JetBrains Mono" font-size="10.5" font-weight="700" fill="#198038">18% (7 Rings)</text>
            </svg>
        </div>
        """, unsafe_allow_html=True)

    # Global Table
    st.markdown("""
    <div class="glass-card">
        <div style="font-weight:700; font-size:16px; margin-bottom:12px;">Global Multi-Bank Screening Feed</div>
        <table class="apple-table-st">
            <thead>
                <tr>
                    <th>Timestamp</th>
                    <th>HMAC Pseudonym</th>
                    <th>Origin</th>
                    <th>Destination</th>
                    <th>Amount</th>
                    <th>Cycle Score</th>
                    <th>Decision</th>
                    <th>Latency</th>
                </tr>
            </thead>
            <tbody>
                <tr><td>15:46:12</td><td><span class="mono-tag">0x8f4b..746b</span></td><td>BANK_A_SG</td><td>BANK_B_SG</td><td><b>$4,900.00</b></td><td>0.986</td><td><span class="pill pill-red">PRE-SETTLEMENT FREEZE</span></td><td>24.2 ms</td></tr>
                <tr><td>15:45:55</td><td><span class="mono-tag">0x3a9c..bc92</span></td><td>BANK_B_SG</td><td>BANK_C_SG</td><td><b>$2,450.00</b></td><td>0.984</td><td><span class="pill pill-red">PRE-SETTLEMENT FREEZE</span></td><td>23.8 ms</td></tr>
                <tr><td>15:45:20</td><td><span class="mono-tag">0x7e1d..0129</span></td><td>BANK_C_SG</td><td>CASH_OUT</td><td><b>$4,900.00</b></td><td>0.988</td><td><span class="pill pill-red">PRE-SETTLEMENT FREEZE</span></td><td>24.6 ms</td></tr>
                <tr><td>15:41:45</td><td><span class="mono-tag">0x3e11..5647</span></td><td>BANK_A_SG</td><td>BANK_C_SG</td><td><b>$3,450.00</b></td><td>0.082</td><td><span class="pill pill-green">SETTLEMENT APPROVED</span></td><td>18.4 ms</td></tr>
                <tr><td>15:40:19</td><td><span class="mono-tag">0x5d99..900a</span></td><td>BANK_B_SG</td><td>BANK_C_SG</td><td><b>$2,400.00</b></td><td>0.750</td><td><span class="pill pill-orange">ENCLAVE REVIEW</span></td><td>21.9 ms</td></tr>
                <tr><td>15:38:50</td><td><span class="mono-tag">0x1b4a..cdef</span></td><td>BANK_A_SG</td><td>BANK_C_SG</td><td><b>$12,400.00</b></td><td>0.024</td><td><span class="pill pill-green">SETTLEMENT APPROVED</span></td><td>16.8 ms</td></tr>
            </tbody>
        </table>
    </div>
    """, unsafe_allow_html=True)
