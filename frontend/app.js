/**
 * ZeroMule — Apple Frosted Glass Coordinator Dashboard
 * Interactive Client-Side Privacy Engine, Singular Bank Inspector & Global Screening Overview
 */

// -----------------------------------------------------------------------------
// CONSTANTS & CONFIGURATION
// -----------------------------------------------------------------------------
const CONFIG = {
  rawAccount: "SG-DBS-884920194",
  sharedHmacKey: "interbank-shared-hmac-secret-2026",
  baseRawEmbedding: [2.419, -1.882, 0.941, 3.102],
  clipNormC: 1.0,
};

// Global App State
let state = {
  activePage: "info", // "info" | "bank" | "overview"
  scenario: "attack",  // "attack" | "payroll"
  sigma: 0.80,
  gateMode: "valid",   // "valid" | "tampered" | "plaintext"
  pseudoId: "8f4b5961a293847291a2bc8394e1d939281746b8c9d01e23a4b5c6d7e8f90123",
  perturbedEmbedding: [0.412, -0.319, 0.188, 0.504],

  // Singular Bank View State
  selectedBank: "bankA", // "bankA" | "bankB" | "bankC"
  bankTableFilter: "all", // "all" | "frozen" | "suspicious" | "cleared"

  // Overview Page Filter State
  globalSearch: "",
  globalStatusFilter: "all",
  globalBankFilter: "all",
};

// -----------------------------------------------------------------------------
// DATA REPOSITORIES FOR MULTI-PAGE VIEWS
// -----------------------------------------------------------------------------
const BANK_DATA = {
  bankA: {
    id: "BANK_A_SG",
    name: "Bank A (Origin Silo & Wire Hub)",
    role: "Originating Silo (Outbound High-Value Wire Processing)",
    signingKey: "Ed25519_skA (Pinned pkA in Enclave)",
    volume: "$14.2M",
    volumeCount: "48,120 Transactions Today",
    stoppedTxs: "14 Txs",
    stoppedAmount: "$184,200 Stopped · Pre-Settlement Held",
    suspiciousTxs: "42 Txs",
    suspiciousSub: "Cross-Bank Cycle Risk · Enclave Queue",
    budgetEps: "1.35",
    chartRole: "Origin Silo Horizon",
    transactions: [
      { id: "TX-A-9810", time: "18s ago", acc: "ACC-884920", pseudo: "0x8f4b..91a2", counterparty: "Bank B (Relay)", amount: "$4,900.00", localView: "Cleared (0.11)", action: "PRE-SETTLEMENT FREEZE", status: "frozen", prov: "Ed25519 Valid" },
      { id: "TX-A-9804", time: "2m ago", acc: "ACC-712390", pseudo: "0x3e11..cc04", counterparty: "Bank C (Settlement)", amount: "$3,450.00", localView: "Cleared (0.08)", action: "SETTLEMENT APPROVED", status: "cleared", prov: "Ed25519 Valid" },
      { id: "TX-A-9798", time: "5m ago", acc: "ACC-992384", pseudo: "0x9a88..44e1", counterparty: "Bank B (Relay)", amount: "$4,850.00", localView: "Suspicious (0.68)", action: "ENCLAVE REVIEW", status: "suspicious", prov: "Ed25519 Valid" },
      { id: "TX-A-9791", time: "9m ago", acc: "ACC-120488", pseudo: "0x1b4a..df90", counterparty: "Bank C (Settlement)", amount: "$12,400.00", localView: "Cleared (0.05)", action: "SETTLEMENT APPROVED", status: "cleared", prov: "Ed25519 Valid" },
      { id: "TX-A-9785", time: "14m ago", acc: "ACC-549210", pseudo: "0x6f99..33a0", counterparty: "Bank B (Relay)", amount: "$4,950.00", localView: "Cleared (0.14)", action: "PRE-SETTLEMENT FREEZE", status: "frozen", prov: "Ed25519 Valid" },
      { id: "TX-A-9779", time: "21m ago", acc: "ACC-331049", pseudo: "0x7c22..55b8", counterparty: "Bank B (Relay)", amount: "$2,100.00", localView: "Suspicious (0.71)", action: "ENCLAVE REVIEW", status: "suspicious", prov: "Ed25519 Valid" },
      { id: "TX-A-9772", time: "26m ago", acc: "ACC-884920", pseudo: "0x8f4b..91a2", counterparty: "Bank B (Relay)", amount: "$4,900.00", localView: "Suspicious (0.64)", action: "ENCLAVE REVIEW", status: "suspicious", prov: "Ed25519 Valid" },
      { id: "TX-A-9765", time: "34m ago", acc: "ACC-449102", pseudo: "0x2d88..99a1", counterparty: "Bank C (Settlement)", amount: "$1,850.00", localView: "Cleared (0.04)", action: "SETTLEMENT APPROVED", status: "cleared", prov: "Ed25519 Valid" },
    ]
  },
  bankB: {
    id: "BANK_B_SG",
    name: "Bank B (Intermediary Relay & P2P)",
    role: "Intermediary Relay (High-Frequency Split P2P Transfers)",
    signingKey: "Ed25519_skB (Pinned pkB in Enclave)",
    volume: "$11.8M",
    volumeCount: "39,410 Transactions Today",
    stoppedTxs: "19 Txs",
    stoppedAmount: "$242,000 Stopped · Layering Held",
    suspiciousTxs: "58 Txs",
    suspiciousSub: "Split Relays Held · Velocity Spikes",
    budgetEps: "1.20",
    chartRole: "Layering Relay Horizon",
    transactions: [
      { id: "TX-B-4412", time: "12s ago", acc: "ACC-319044", pseudo: "0x3a9c..44e0", counterparty: "Bank C (Settlement)", amount: "$2,450.00", localView: "Cleared (0.14)", action: "PRE-SETTLEMENT FREEZE", status: "frozen", prov: "Ed25519 Valid" },
      { id: "TX-B-4409", time: "38s ago", acc: "ACC-319044", pseudo: "0x3a9c..44e0", counterparty: "Bank C (Settlement)", amount: "$2,450.00", localView: "Cleared (0.14)", action: "PRE-SETTLEMENT FREEZE", status: "frozen", prov: "Ed25519 Valid" },
      { id: "TX-B-4401", time: "3m ago", acc: "ACC-662910", pseudo: "0x4b77..22f1", counterparty: "Bank A (Origin)", amount: "$750.00", localView: "Cleared (0.03)", action: "SETTLEMENT APPROVED", status: "cleared", prov: "Ed25519 Valid" },
      { id: "TX-B-4395", time: "6m ago", acc: "ACC-881204", pseudo: "0x5d99..88b4", counterparty: "Bank C (Settlement)", amount: "$2,400.00", localView: "Suspicious (0.75)", action: "ENCLAVE REVIEW", status: "suspicious", prov: "Ed25519 Valid" },
      { id: "TX-B-4389", time: "11m ago", acc: "ACC-119482", pseudo: "0x8e33..11c0", counterparty: "Bank C (Settlement)", amount: "$2,350.00", localView: "Suspicious (0.69)", action: "ENCLAVE REVIEW", status: "suspicious", prov: "Ed25519 Valid" },
      { id: "TX-B-4382", time: "18m ago", acc: "ACC-992015", pseudo: "0x1a44..55d9", counterparty: "Bank A (Origin)", amount: "$1,200.00", localView: "Cleared (0.07)", action: "SETTLEMENT APPROVED", status: "cleared", prov: "Ed25519 Valid" },
      { id: "TX-B-4375", time: "22m ago", acc: "ACC-441829", pseudo: "0x9c77..00e2", counterparty: "Bank C (Settlement)", amount: "$2,480.00", localView: "Suspicious (0.62)", action: "ENCLAVE REVIEW", status: "suspicious", prov: "Ed25519 Valid" },
      { id: "TX-B-4368", time: "29m ago", acc: "ACC-772910", pseudo: "0x2f11..77a5", counterparty: "Bank A (Origin)", amount: "$890.00", localView: "Cleared (0.02)", action: "SETTLEMENT APPROVED", status: "cleared", prov: "Ed25519 Valid" },
    ]
  },
  bankC: {
    id: "BANK_C_SG",
    name: "Bank C (Settlement & Cash-Out)",
    role: "Settlement / Cash-Out Endpoint (Rapid Liquidation Defense)",
    signingKey: "Ed25519_skC (Pinned pkC in Enclave)",
    volume: "$8.8M",
    volumeCount: "28,340 Transactions Today",
    stoppedTxs: "28 Txs",
    stoppedAmount: "$385,900 Stopped · Cash-Out Prevented",
    suspiciousTxs: "81 Txs",
    suspiciousSub: "Consolidation Inbound Flags · Perimeter Alert",
    budgetEps: "1.50",
    chartRole: "Settlement Liquidation Horizon",
    transactions: [
      { id: "TX-C-1940", time: "8s ago", acc: "ACC-772810", pseudo: "0x7e1d..b805", counterparty: "External ATM / Cashier", amount: "$4,900.00", localView: "Cleared (0.09)", action: "PRE-SETTLEMENT FREEZE", status: "frozen", prov: "Ed25519 Valid" },
      { id: "TX-C-1935", time: "45s ago", acc: "ACC-994821", pseudo: "0x9c2a..11e8", counterparty: "Crypto Exchange Relay", amount: "$4,800.00", localView: "Cleared (0.10)", action: "PRE-SETTLEMENT FREEZE", status: "frozen", prov: "Ed25519 Valid" },
      { id: "TX-C-1928", time: "2m ago", acc: "ACC-331902", pseudo: "0x4e88..22f0", counterparty: "Merchant POS", amount: "$142.50", localView: "Cleared (0.01)", action: "SETTLEMENT APPROVED", status: "cleared", prov: "Ed25519 Valid" },
      { id: "TX-C-1921", time: "5m ago", acc: "ACC-552910", pseudo: "0x6a11..33b4", counterparty: "Wire Settlement", amount: "$4,750.00", localView: "Suspicious (0.78)", action: "ENCLAVE REVIEW", status: "suspicious", prov: "Ed25519 Valid" },
      { id: "TX-C-1914", time: "9m ago", acc: "ACC-881940", pseudo: "0x1d55..99c2", counterparty: "Prepaid Card Hub", amount: "$3,900.00", localView: "Suspicious (0.81)", action: "ENCLAVE REVIEW", status: "suspicious", prov: "Ed25519 Valid" },
      { id: "TX-C-1907", time: "16m ago", acc: "ACC-221049", pseudo: "0x8f22..44e9", counterparty: "Commercial Supplier", amount: "$18,500.00", localView: "Cleared (0.04)", action: "SETTLEMENT APPROVED", status: "cleared", prov: "Ed25519 Valid" },
      { id: "TX-C-1901", time: "24m ago", acc: "ACC-449102", pseudo: "0x3b66..77a1", counterparty: "Fast P2P Liquidation", amount: "$4,650.00", localView: "Suspicious (0.73)", action: "ENCLAVE REVIEW", status: "suspicious", prov: "Ed25519 Valid" },
      { id: "TX-C-1895", time: "31m ago", acc: "ACC-661920", pseudo: "0x5c88..00d5", counterparty: "Retail Purchase", amount: "$89.90", localView: "Cleared (0.01)", action: "SETTLEMENT APPROVED", status: "cleared", prov: "Ed25519 Valid" },
    ]
  }
};

const GLOBAL_TRANSACTIONS = [
  { time: "15:46:12", pseudo: "0x8f4b5961a293847291a2bc8394e1d939281746b8", origin: "BANK_A_SG", dest: "BANK_B_SG", amount: "$4,900.00", score: "0.986", decision: "PRE-SETTLEMENT FREEZE", status: "frozen", latency: "24.2 ms" },
  { time: "15:45:55", pseudo: "0x3a9c44e0982143bc8819a004821039485761bc92", origin: "BANK_B_SG", dest: "BANK_C_SG", amount: "$2,450.00", score: "0.984", decision: "PRE-SETTLEMENT FREEZE", status: "frozen", latency: "23.8 ms" },
  { time: "15:45:20", pseudo: "0x7e1db805912834019a28bc839481729384710129", origin: "BANK_C_SG", dest: "CASH_OUT", amount: "$4,900.00", score: "0.988", decision: "PRE-SETTLEMENT FREEZE", status: "frozen", latency: "24.6 ms" },
  { time: "15:44:10", pseudo: "0x1a8844e19028347101928374655647382910abcd", origin: "BANK_A_SG", dest: "BANK_B_SG", amount: "$4,850.00", score: "0.680", decision: "ENCLAVE REVIEW", status: "review", latency: "22.1 ms" },
  { time: "15:43:02", pseudo: "0x9c2a11e89283746152435465768798091a2b3c4d", origin: "BANK_C_SG", dest: "EXTERNAL_WIRE", amount: "$4,800.00", score: "0.962", decision: "PRE-SETTLEMENT FREEZE", status: "frozen", latency: "25.1 ms" },
  { time: "15:41:45", pseudo: "0x3e11cc0491827364516273849501928374655647", origin: "BANK_A_SG", dest: "BANK_C_SG", amount: "$3,450.00", score: "0.082", decision: "SETTLEMENT APPROVED", status: "approved", latency: "18.4 ms" },
  { time: "15:40:19", pseudo: "0x5d9988b49102938475615243344556677889900a", origin: "BANK_B_SG", dest: "BANK_C_SG", amount: "$2,400.00", score: "0.750", decision: "ENCLAVE REVIEW", status: "review", latency: "21.9 ms" },
  { time: "15:38:50", pseudo: "0x1b4adf9082736451928374655647382910abcdef", origin: "BANK_A_SG", dest: "BANK_C_SG", amount: "$12,400.00", score: "0.024", decision: "SETTLEMENT APPROVED", status: "approved", latency: "16.8 ms" },
  { time: "15:36:20", pseudo: "0x6a1133b491827364516273849501928374655647", origin: "BANK_C_SG", dest: "SETTLED_WIRE", amount: "$4,750.00", score: "0.780", decision: "ENCLAVE REVIEW", status: "review", latency: "23.4 ms" },
  { time: "15:34:11", pseudo: "0x4b7722f182736451928374655647382910abcdef", origin: "BANK_B_SG", dest: "BANK_A_SG", amount: "$750.00", score: "0.015", decision: "SETTLEMENT APPROVED", status: "approved", latency: "17.2 ms" },
  { time: "15:31:05", pseudo: "0x6f9933a09102938475615243344556677889900a", origin: "BANK_A_SG", dest: "BANK_B_SG", amount: "$4,950.00", score: "0.975", decision: "PRE-SETTLEMENT FREEZE", status: "frozen", latency: "24.8 ms" },
  { time: "15:28:44", pseudo: "0x8f2244e982736451928374655647382910abcdef", origin: "BANK_C_SG", dest: "COMMERCIAL_HUB", amount: "$18,500.00", score: "0.038", decision: "SETTLEMENT APPROVED", status: "approved", latency: "19.1 ms" },
];

// -----------------------------------------------------------------------------
// CRYPTOGRAPHIC HELPER FUNCTIONS
// -----------------------------------------------------------------------------
async function computeHmacSha256(keyStr, messageStr) {
  try {
    const enc = new TextEncoder();
    const keyData = enc.encode(keyStr);
    const key = await window.crypto.subtle.importKey(
      "raw",
      keyData,
      { name: "HMAC", hash: { name: "SHA-256" } },
      false,
      ["sign"]
    );
    const signature = await window.crypto.subtle.sign(
      "HMAC",
      key,
      enc.encode(messageStr)
    );
    const hashArray = Array.from(new Uint8Array(signature));
    return hashArray.map(b => b.toString(16).padStart(2, "0")).join("");
  } catch (err) {
    let hash = 0x811c9dc5;
    const str = keyStr + messageStr;
    for (let i = 0; i < str.length; i++) {
      hash ^= str.charCodeAt(i);
      hash = (hash * 0x01000193) >>> 0;
    }
    return hash.toString(16).padStart(8, "0").repeat(8).slice(0, 64);
  }
}

function sampleGaussian(mean = 0, sigma = 1.0) {
  let u1 = Math.random();
  let u2 = Math.random();
  while (u1 === 0) u1 = Math.random();
  const z0 = Math.sqrt(-2.0 * Math.log(u1)) * Math.cos(2.0 * Math.PI * u2);
  return mean + z0 * sigma;
}

function applyLocalDifferentialPrivacy(vec, clipC, sigma) {
  const l2Norm = Math.sqrt(vec.reduce((sum, v) => sum + v * v, 0));
  const clipFactor = l2Norm > 0 ? Math.min(1.0, clipC / l2Norm) : 1.0;
  const clipped = vec.map(v => v * clipFactor);

  const noised = clipped.map(v => {
    const perturbed = v + sampleGaussian(0, sigma * 0.4);
    return Math.round(perturbed * 1000) / 1000;
  });

  return noised;
}

// -----------------------------------------------------------------------------
// DOM REFERENCES
// -----------------------------------------------------------------------------
// Page Navigation Tabs & Views
const tabBtnInfo = document.getElementById("tabBtnInfo");
const tabBtnBank = document.getElementById("tabBtnBank");
const tabBtnOverview = document.getElementById("tabBtnOverview");
const viewInfo = document.getElementById("viewInfo");
const viewBank = document.getElementById("viewBank");
const viewOverview = document.getElementById("viewOverview");

// Information View Elements
const btnScenarioAttack = document.getElementById("btnScenarioAttack");
const btnScenarioPayroll = document.getElementById("btnScenarioPayroll");
const sigmaSlider = document.getElementById("sigmaSlider");
const sigmaValDisplay = document.getElementById("sigmaValDisplay");
const epsEstDisplay = document.getElementById("epsEstDisplay");

const btnGateValid = document.getElementById("btnGateValid");
const btnGateTampered = document.getElementById("btnGateTampered");
const btnGatePlaintext = document.getElementById("btnGatePlaintext");
const btnRehashPayload = document.getElementById("btnRehashPayload");

const kpiSlaValue = document.getElementById("kpiSlaValue");
const kpiDpValue = document.getElementById("kpiDpValue");
const kpiDpBadge = document.getElementById("kpiDpBadge");
const kpiGateValue = document.getElementById("kpiGateValue");
const kpiGateBadge = document.getElementById("kpiGateBadge");

const coordinatorDecisionCard = document.getElementById("coordinatorDecisionCard");
const svgContainer = document.getElementById("svgContainer");

const rawJsonDisplay = document.getElementById("rawJsonDisplay");
const payloadJsonDisplay = document.getElementById("payloadJsonDisplay");
const gatekeeperErrorAlert = document.getElementById("gatekeeperErrorAlert");

const tagBankADp = document.getElementById("tagBankADp");
const tagBankBDp = document.getElementById("tagBankBDp");
const tagBankCDp = document.getElementById("tagBankCDp");

// Singular Bank View Elements
const btnBankA = document.getElementById("btnBankA");
const btnBankB = document.getElementById("btnBankB");
const btnBankC = document.getElementById("btnBankC");
const bankIdPill = document.getElementById("bankIdPill");
const bankLedgerPill = document.getElementById("bankLedgerPill");

const bankKpiVolume = document.getElementById("bankKpiVolume");
const bankKpiVolumeSub = document.getElementById("bankKpiVolumeSub");
const bankKpiStopped = document.getElementById("bankKpiStopped");
const bankKpiStoppedSub = document.getElementById("bankKpiStoppedSub");
const bankKpiSuspicious = document.getElementById("bankKpiSuspicious");
const bankKpiSuspiciousSub = document.getElementById("bankKpiSuspiciousSub");
const bankKpiBudget = document.getElementById("bankKpiBudget");
const bankKpiBudgetBadge = document.getElementById("bankKpiBudgetBadge");

const bankChartRolePill = document.getElementById("bankChartRolePill");
const bankRiskChartContainer = document.getElementById("bankRiskChartContainer");
const bankDetailRole = document.getElementById("bankDetailRole");
const bankDetailKey = document.getElementById("bankDetailKey");

const bankTableFilters = document.getElementById("bankTableFilters");
const bankTableBody = document.getElementById("bankTableBody");

// Overview Page Elements
const overviewTimelineChartContainer = document.getElementById("overviewTimelineChartContainer");
const overviewTopologyChartContainer = document.getElementById("overviewTopologyChartContainer");
const globalSearchInput = document.getElementById("globalSearchInput");
const globalStatusSelect = document.getElementById("globalStatusSelect");
const globalBankSelect = document.getElementById("globalBankSelect");
const globalTableBody = document.getElementById("globalTableBody");

// -----------------------------------------------------------------------------
// SVG RENDERERS: 4-STAGE FLOW & PAYROLL (INFORMATION VIEW)
// -----------------------------------------------------------------------------
function renderAttackSvg() {
  return `
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
        <filter id="glowRed" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="2" stdDeviation="4" flood-color="#DA1E28" flood-opacity="0.3"/>
        </filter>
      </defs>

      <rect x="20" y="12" width="640" height="38" rx="10" fill="#F5F5F7" stroke="#E5E5EA"/>
      <text x="35" y="35" font-family="Inter, sans-serif" font-size="11" font-weight="700" fill="#515154">LAUNDERING FLOW:</text>
      <circle cx="165" cy="31" r="6" fill="#DA1E28"/>
      <text x="177" y="35" font-family="Inter" font-size="11" font-weight="600" fill="#1D1D1F">1. Dirty Origin (#DA1E28)</text>
      <circle cx="320" cy="31" r="6" fill="#FF832B"/>
      <text x="332" y="35" font-family="Inter" font-size="11" font-weight="600" fill="#1D1D1F">2. Layering (#FF832B)</text>
      <circle cx="460" cy="31" r="6" fill="#6FD170"/>
      <text x="472" y="35" font-family="Inter" font-size="11" font-weight="600" fill="#1D1D1F">3. Masking (#6FD170)</text>
      <circle cx="590" cy="31" r="6" fill="#198038"/>
      <text x="602" y="35" font-family="Inter" font-size="11" font-weight="600" fill="#1D1D1F">4. Clean (#198038)</text>

      <!-- Hop 1 -->
      <path d="M 155 150 Q 250 85 335 125" fill="none" stroke="#DA1E28" stroke-width="4" marker-end="url(#arr1)"/>
      <text x="238" y="94" font-family="JetBrains Mono, monospace" font-size="10.5" font-weight="600" fill="#DA1E28">$4,900 (t=0s)</text>

      <!-- Hop 2 -->
      <path d="M 385 160 Q 470 210 515 255" fill="none" stroke="#FF832B" stroke-width="4" marker-end="url(#arr2)"/>
      <text x="465" y="195" font-family="JetBrains Mono, monospace" font-size="10.5" font-weight="600" fill="#FF832B">2 &times; $2,450 (t=38s)</text>

      <!-- Hop 3 -->
      <path d="M 490 295 Q 340 355 205 295" fill="none" stroke="#6FD170" stroke-width="4" marker-end="url(#arr3)"/>
      <text x="335" y="348" font-family="JetBrains Mono, monospace" font-size="10.5" font-weight="600" fill="#2E7D32">Consolidate (t=94s)</text>

      <!-- Hop 4 (Intercepted) -->
      <path d="M 150 255 Q 115 210 130 175" fill="none" stroke="#198038" stroke-width="4" stroke-dasharray="6,4" marker-end="url(#arr4)"/>
      
      <g filter="url(#glowRed)">
        <rect x="35" y="202" width="128" height="26" rx="7" fill="#DA1E28"/>
        <text x="99" y="219" font-family="Inter, sans-serif" font-size="10.5" font-weight="800" fill="#FFFFFF" text-anchor="middle">&#9889; INTERCEPTED</text>
      </g>

      <!-- Nodes -->
      <g transform="translate(135, 145)">
        <circle r="34" fill="#FFFFFF" stroke="#DA1E28" stroke-width="3.5"/>
        <text y="-5" font-family="Inter" font-size="11.5" font-weight="700" fill="#1D1D1F" text-anchor="middle">BANK A</text>
        <text y="12" font-family="JetBrains Mono" font-size="9" fill="#86868B" text-anchor="middle">0x8f4b..</text>
      </g>

      <g transform="translate(365, 135)">
        <circle r="34" fill="#FFFFFF" stroke="#FF832B" stroke-width="3.5"/>
        <text y="-5" font-family="Inter" font-size="11.5" font-weight="700" fill="#1D1D1F" text-anchor="middle">BANK B</text>
        <text y="12" font-family="JetBrains Mono" font-size="9" fill="#86868B" text-anchor="middle">0x3a9c..</text>
      </g>

      <g transform="translate(525, 280)">
        <circle r="34" fill="#FFFFFF" stroke="#6FD170" stroke-width="3.5"/>
        <text y="-5" font-family="Inter" font-size="11.5" font-weight="700" fill="#1D1D1F" text-anchor="middle">BANK C</text>
        <text y="12" font-family="JetBrains Mono" font-size="9" fill="#86868B" text-anchor="middle">0x7e1d..</text>
      </g>

      <g transform="translate(170, 285)">
        <circle r="34" fill="#FFFFFF" stroke="#198038" stroke-width="3.5"/>
        <text y="-5" font-family="Inter" font-size="11.5" font-weight="700" fill="#1D1D1F" text-anchor="middle">CASH OUT</text>
        <text y="12" font-family="JetBrains Mono" font-size="9" fill="#86868B" text-anchor="middle">0x9c2a..</text>
      </g>
    </svg>
  `;
}

function renderPayrollSvg() {
  return `
    <svg viewBox="0 0 680 410" width="100%" height="410" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <marker id="arrClean" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
          <polygon points="0 0, 8 3, 0 6" fill="#198038"/>
        </marker>
      </defs>

      <rect x="20" y="12" width="640" height="38" rx="10" fill="#F5F5F7" stroke="#E5E5EA"/>
      <text x="35" y="35" font-family="Inter, sans-serif" font-size="11" font-weight="700" fill="#198038">
        BENIGN TOPOLOGY: 1-TO-MANY CORPORATE PAYROLL DISTRIBUTION (ACYCLIC)
      </text>

      <line x1="180" y1="210" x2="440" y2="115" stroke="#198038" stroke-width="3.5" marker-end="url(#arrClean)"/>
      <text x="310" y="145" font-family="JetBrains Mono" font-size="10" font-weight="600" fill="#198038">$3,850.00 Salary</text>

      <line x1="180" y1="210" x2="440" y2="210" stroke="#198038" stroke-width="3.5" marker-end="url(#arrClean)"/>
      <text x="310" y="200" font-family="JetBrains Mono" font-size="10" font-weight="600" fill="#198038">$4,200.00 Salary</text>

      <line x1="180" y1="210" x2="440" y2="305" stroke="#198038" stroke-width="3.5" marker-end="url(#arrClean)"/>
      <text x="310" y="275" font-family="JetBrains Mono" font-size="10" font-weight="600" fill="#198038">$3,950.00 Salary</text>

      <g transform="translate(145, 210)">
        <circle r="40" fill="#FFFFFF" stroke="#0071E3" stroke-width="3.5"/>
        <text y="-5" font-family="Inter" font-size="12" font-weight="700" fill="#1D1D1F" text-anchor="middle">BANK A</text>
        <text y="12" font-family="JetBrains Mono" font-size="9" fill="#86868B" text-anchor="middle">Payroll Hub</text>
      </g>

      <g transform="translate(485, 110)">
        <circle r="32" fill="#FFFFFF" stroke="#198038" stroke-width="2.8"/>
        <text y="4" font-family="JetBrains Mono" font-size="10.5" font-weight="600" fill="#198038" text-anchor="middle">Emp #1</text>
      </g>
      <g transform="translate(485, 210)">
        <circle r="32" fill="#FFFFFF" stroke="#198038" stroke-width="2.8"/>
        <text y="4" font-family="JetBrains Mono" font-size="10.5" font-weight="600" fill="#198038" text-anchor="middle">Emp #2</text>
      </g>
      <g transform="translate(485, 310)">
        <circle r="32" fill="#FFFFFF" stroke="#198038" stroke-width="2.8"/>
        <text y="4" font-family="JetBrains Mono" font-size="10.5" font-weight="600" fill="#198038" text-anchor="middle">Emp #3</text>
      </g>
    </svg>
  `;
}

// -----------------------------------------------------------------------------
// SVG RENDERERS: SINGULAR BANK VIEW & OVERVIEW ANALYTICS CHARTS
// -----------------------------------------------------------------------------
function renderBankRiskChart(bankKey) {
  const isC = bankKey === "bankC";
  const isB = bankKey === "bankB";

  return `
    <svg viewBox="0 0 580 270" width="100%" height="270" xmlns="http://www.w3.org/2000/svg">
      <!-- Axis Lines -->
      <line x1="50" y1="220" x2="550" y2="220" stroke="#E5E5EA" stroke-width="1.5"/>
      <line x1="50" y1="30" x2="50" y2="220" stroke="#E5E5EA" stroke-width="1.5"/>

      <!-- Threshold Lines -->
      <line x1="380" y1="30" x2="380" y2="220" stroke="#DA1E28" stroke-width="1.5" stroke-dasharray="4,4"/>
      <text x="385" y="45" font-family="Inter" font-size="10" font-weight="700" fill="#DA1E28">Coordinator Freeze Threshold (0.80)</text>

      <!-- Grid Labels -->
      <text x="45" y="240" font-family="JetBrains Mono" font-size="10" fill="#86868B">0.0 (Benign)</text>
      <text x="260" y="240" font-family="JetBrains Mono" font-size="10" fill="#86868B">0.5 (Review)</text>
      <text x="480" y="240" font-family="JetBrains Mono" font-size="10" fill="#86868B">1.0 (Critical)</text>

      <!-- Normal Distribution Bell Curve (Local View) -->
      <path d="M 50 215 Q 120 210 160 140 Q 200 40 230 40 Q 260 40 300 150 Q 340 210 550 218" 
            fill="none" stroke="#0071E3" stroke-width="3"/>
      <path d="M 50 215 Q 120 210 160 140 Q 200 40 230 40 Q 260 40 300 150 Q 340 210 550 218 L 550 220 L 50 220 Z" 
            fill="rgba(0, 113, 227, 0.08)"/>

      <!-- Syndicate Spikes (Detected via Shared HMAC Matching) -->
      <circle cx="${isC ? '480' : isB ? '460' : '440'}" cy="65" r="7" fill="#DA1E28"/>
      <circle cx="${isC ? '495' : isB ? '475' : '455'}" cy="78" r="6" fill="#DA1E28"/>
      <circle cx="${isC ? '510' : isB ? '490' : '470'}" cy="85" r="5" fill="#DA1E28"/>
      <text x="${isC ? '460' : isB ? '440' : '420'}" y="50" font-family="Inter" font-size="10.5" font-weight="700" fill="#DA1E28">
        Mule Rings Intercepted (${isC ? '28' : isB ? '19' : '14'} Txs)
      </text>

      <!-- Annotation Legend -->
      <rect x="65" y="38" width="12" height="12" rx="3" fill="#0071E3"/>
      <text x="85" y="48" font-family="Inter" font-size="11" font-weight="600" fill="#1D1D1F">Local Horizon Volume</text>
    </svg>
  `;
}

function renderOverviewTimelineChart() {
  return `
    <svg viewBox="0 0 580 270" width="100%" height="270" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="blueGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#0071E3" stop-opacity="0.25"/>
          <stop offset="100%" stop-color="#0071E3" stop-opacity="0.0"/>
        </linearGradient>
      </defs>

      <!-- Axes -->
      <line x1="45" y1="220" x2="555" y2="220" stroke="#E5E5EA" stroke-width="1.5"/>
      <line x1="45" y1="30" x2="45" y2="220" stroke="#E5E5EA" stroke-width="1.5"/>

      <!-- X Labels -->
      <text x="45" y="238" font-family="JetBrains Mono" font-size="9.5" fill="#86868B">00:00</text>
      <text x="165" y="238" font-family="JetBrains Mono" font-size="9.5" fill="#86868B">06:00</text>
      <text x="290" y="238" font-family="JetBrains Mono" font-size="9.5" fill="#86868B">12:00</text>
      <text x="415" y="238" font-family="JetBrains Mono" font-size="9.5" fill="#86868B">18:00</text>
      <text x="525" y="238" font-family="JetBrains Mono" font-size="9.5" fill="#86868B">Now</text>

      <!-- Volume Area Curve -->
      <path d="M 45 190 Q 110 180 165 140 T 290 90 T 415 110 T 550 75 L 550 220 L 45 220 Z" fill="url(#blueGrad)"/>
      <path d="M 45 190 Q 110 180 165 140 T 290 90 T 415 110 T 550 75" fill="none" stroke="#0071E3" stroke-width="3"/>

      <!-- Intercept Spikes (Crimson Bars) -->
      <rect x="180" y="110" width="8" height="110" rx="3" fill="#DA1E28"/>
      <rect x="295" y="70" width="8" height="150" rx="3" fill="#DA1E28"/>
      <rect x="425" y="90" width="8" height="130" rx="3" fill="#DA1E28"/>
      <rect x="520" y="55" width="8" height="165" rx="3" fill="#DA1E28"/>

      <!-- Legend -->
      <circle cx="65" cy="45" r="5" fill="#0071E3"/>
      <text x="76" y="49" font-family="Inter" font-size="11" font-weight="600" fill="#1D1D1F">Screened Volume (6.2k/hr)</text>
      <rect x="255" y="40" width="10" height="10" rx="2" fill="#DA1E28"/>
      <text x="272" y="49" font-family="Inter" font-size="11" font-weight="600" fill="#1D1D1F">Syndicate Interceptions (38 Rings)</text>
    </svg>
  `;
}

function renderOverviewTopologyChart() {
  return `
    <svg viewBox="0 0 580 270" width="100%" height="270" xmlns="http://www.w3.org/2000/svg">
      <!-- Grid Lines -->
      <line x1="160" y1="20" x2="160" y2="230" stroke="#E5E5EA" stroke-width="1.5"/>

      <!-- Category 1: 4-Hop Rings (Coordinated Mule Rings) -->
      <text x="145" y="65" font-family="Inter" font-size="11.5" font-weight="700" fill="#1D1D1F" text-anchor="end">4-Hop Rings</text>
      <rect x="160" y="48" width="280" height="26" rx="6" fill="#DA1E28"/>
      <text x="450" y="66" font-family="JetBrains Mono" font-size="11" font-weight="700" fill="#DA1E28">58% (22 Rings)</text>

      <!-- Category 2: 3-Hop Rings (Rapid Triangular Transfers) -->
      <text x="145" y="115" font-family="Inter" font-size="11.5" font-weight="700" fill="#1D1D1F" text-anchor="end">3-Hop Cycles</text>
      <rect x="160" y="98" width="115" height="26" rx="6" fill="#FF832B"/>
      <text x="285" y="116" font-family="JetBrains Mono" font-size="11" font-weight="700" fill="#C45100">24% (9 Rings)</text>

      <!-- Category 3: 5+ Hop Meshes (Complex Multi-Layered) -->
      <text x="145" y="165" font-family="Inter" font-size="11.5" font-weight="700" fill="#1D1D1F" text-anchor="end">5+ Hop Meshes</text>
      <rect x="160" y="148" width="86" height="26" rx="6" fill="#6FD170"/>
      <text x="256" y="166" font-family="JetBrains Mono" font-size="11" font-weight="700" fill="#198038">18% (7 Rings)</text>

      <!-- Baseline Metric -->
      <rect x="50" y="200" width="480" height="34" rx="8" fill="#F5F5F7" stroke="#E5E5EA"/>
      <text x="65" y="222" font-family="Inter" font-size="11" font-weight="600" fill="#515154">
        Directed-GIN InfoNCE Cycle Accuracy: <strong style="color: #198038;">98.6% Precision</strong> &bull; Zero Raw Topology Leaks
      </text>
    </svg>
  `;
}

// -----------------------------------------------------------------------------
// UPDATE FUNCTIONS FOR EACH VIEW
// -----------------------------------------------------------------------------
async function updateInfoView() {
  const epsEst = Math.round((1.10 / state.sigma) * 100) / 100;
  
  sigmaValDisplay.textContent = state.sigma.toFixed(2);
  epsEstDisplay.textContent = epsEst.toFixed(2);

  if (state.scenario === "attack") {
    kpiSlaValue.textContent = "24.2 ms";
  } else {
    kpiSlaValue.textContent = "19.8 ms";
  }

  kpiDpValue.innerHTML = `&epsilon; = ${epsEst.toFixed(2)}`;
  kpiDpBadge.innerHTML = `Clip C=1.0 &bull; &sigma;=${state.sigma.toFixed(2)}`;
  if (epsEst <= 2.0) {
    kpiDpBadge.className = "pill pill-green";
  } else {
    kpiDpBadge.className = "pill pill-orange";
  }

  if (state.gateMode === "valid") {
    kpiGateValue.textContent = "3/3 Verified";
    kpiGateBadge.className = "pill pill-green";
    kpiGateBadge.innerHTML = "Ed25519 Valid &bull; 0 Raw PII";
  } else if (state.gateMode === "tampered") {
    kpiGateValue.textContent = "1 Blocked";
    kpiGateBadge.className = "pill pill-red";
    kpiGateBadge.textContent = "Invalid Ed25519 Signature";
  } else {
    kpiGateValue.textContent = "1 Rejected";
    kpiGateBadge.className = "pill pill-red";
    kpiGateBadge.textContent = "Plaintext Account ID Blocked";
  }

  tagBankADp.innerHTML = `LDP: C=1.0, &epsilon;1=${(epsEst * 1.02).toFixed(1)}`;
  tagBankBDp.innerHTML = `LDP: C=1.0, &epsilon;2=${(epsEst * 0.92).toFixed(1)}`;
  tagBankCDp.innerHTML = `LDP: C=1.0, &epsilon;3=${(epsEst * 1.08).toFixed(1)}`;

  if (state.scenario === "attack") {
    coordinatorDecisionCard.className = "glass-card decision-card alert-attack";
    coordinatorDecisionCard.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <span class="decision-title">ZEROMULE COORDINATOR DECISION</span>
        <span class="pill pill-red">PRE-SETTLEMENT FREEZE</span>
      </div>
      <div class="decision-body">
        <b>Stitched Topology Detected:</b> 4-Hop Cross-Bank Laundering Cycle matched via shared HMAC pseudonyms.<br>
        <b>Directed-GIN Cycle Confidence:</b> <code>98.6%</code> (Threshold: 80.0%)<br>
        <b>Action:</b> Hold signal dispatched to Bank C prior to settlement clearing in <b>24.2 ms</b>.
      </div>
    `;
    svgContainer.innerHTML = renderAttackSvg();
  } else {
    coordinatorDecisionCard.className = "glass-card decision-card alert-payroll";
    coordinatorDecisionCard.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <span class="decision-title">ZEROMULE COORDINATOR DECISION</span>
        <span class="pill pill-green">SETTLEMENT APPROVED</span>
      </div>
      <div class="decision-body">
        <b>Stitched Topology Detected:</b> Acyclic 1-to-Many Corporate Payroll Distribution.<br>
        <b>Directed-GIN Cycle Confidence:</b> <code>2.4%</code> (Benign Flow)<br>
        <b>Action:</b> Cleared with zero false-positive friction in <b>19.8 ms</b>.
      </div>
    `;
    svgContainer.innerHTML = renderPayrollSvg();
  }

  const rawData = {
    raw_account_id: CONFIG.rawAccount,
    customer_name: "REDACTED_AT_SOURCE",
    account_balance_usd: 142850.00,
    raw_gnn_embedding_sample: CONFIG.baseRawEmbedding,
    protection_pipeline: "HMAC-SHA256 + L2 Clip (C=1.0) + Gaussian Noise + Ed25519 Sign",
  };
  rawJsonDisplay.textContent = JSON.stringify(rawData, null, 2);

  state.perturbedEmbedding = applyLocalDifferentialPrivacy(
    CONFIG.baseRawEmbedding,
    CONFIG.clipNormC,
    state.sigma
  );

  if (state.gateMode === "valid") {
    payloadJsonDisplay.classList.remove("hidden");
    gatekeeperErrorAlert.classList.add("hidden");

    const outgoingPayload = {
      bank_id: "BANK_A_SG",
      pseudo_id: state.pseudoId,
      dp_clipped_perturbed_embedding: state.perturbedEmbedding,
      dp_metadata: {
        clip_norm_C: CONFIG.clipNormC,
        noise_sigma: state.sigma,
        local_epsilon: epsEst,
      },
      ed25519_signature: "0x94f8a1b2c7d8e90123456789abcdef01928374655647382910abcdef",
      gatekeeper_status: "ACCEPTED: Signature Verified & Schema Valid",
    };
    payloadJsonDisplay.textContent = JSON.stringify(outgoingPayload, null, 2);
  } else if (state.gateMode === "tampered") {
    payloadJsonDisplay.classList.add("hidden");
    gatekeeperErrorAlert.classList.remove("hidden");
    gatekeeperErrorAlert.innerHTML = `
      <strong>SecurityError: Ed25519 Signature Verification Failed!</strong><br>
      Embedding vector was modified in transit. Provenance signature mismatch for bank public key <code>pk_BANK_A_SG</code>.<br>
      <strong>Action:</strong> Payload dropped immediately at Coordinator perimeter.
    `;
  } else {
    payloadJsonDisplay.classList.add("hidden");
    gatekeeperErrorAlert.classList.remove("hidden");
    gatekeeperErrorAlert.innerHTML = `
      <strong>ValidationError: Plaintext Identifier '${CONFIG.rawAccount}' Detected!</strong><br>
      Coordinator strictly rejects un-hashed raw account numbers and unmasked customer records.<br>
      <strong>Action:</strong> Connection severed & compliance incident logged.
    `;
  }
}

function updateBankView() {
  const current = BANK_DATA[state.selectedBank];
  if (!current) return;

  // Header & Badges
  bankIdPill.textContent = `Identifier: ${current.id}`;
  bankChartRolePill.textContent = current.chartRole;
  bankDetailRole.textContent = current.role;
  bankDetailKey.textContent = current.signingKey;

  // KPIs
  bankKpiVolume.textContent = current.volume;
  bankKpiVolumeSub.innerHTML = `<span class="pill pill-blue">${current.volumeCount}</span>`;

  bankKpiStopped.textContent = current.stoppedTxs;
  bankKpiStoppedSub.innerHTML = `<span class="pill pill-red">${current.stoppedAmount}</span>`;

  bankKpiSuspicious.textContent = current.suspiciousTxs;
  bankKpiSuspiciousSub.innerHTML = `<span class="pill pill-orange">${current.suspiciousSub}</span>`;

  bankKpiBudget.innerHTML = `&epsilon; = ${current.budgetEps}`;

  // Chart
  bankRiskChartContainer.innerHTML = renderBankRiskChart(state.selectedBank);

  // Table
  renderBankTable();
}

function renderBankTable() {
  const current = BANK_DATA[state.selectedBank];
  if (!current) return;

  const filtered = current.transactions.filter(tx => {
    if (state.bankTableFilter === "all") return true;
    return tx.status === state.bankTableFilter;
  });

  bankTableBody.innerHTML = filtered.map(tx => {
    let actionPill = "pill-green";
    if (tx.action.includes("FREEZE")) actionPill = "pill-red";
    else if (tx.action.includes("REVIEW")) actionPill = "pill-orange";

    return `
      <tr>
        <td><strong>${tx.id}</strong><div style="font-size:11px; color:#86868B;">${tx.time}</div></td>
        <td><code>${tx.acc}</code></td>
        <td><span class="mono-tag">${tx.pseudo}</span></td>
        <td>${tx.counterparty}</td>
        <td><strong>${tx.amount}</strong></td>
        <td><span class="pill ${tx.localView.includes('Cleared') ? 'pill-green' : 'pill-orange'}">${tx.localView}</span></td>
        <td><span class="pill ${actionPill}">${tx.action}</span></td>
        <td><span class="pill pill-gray">${tx.prov}</span></td>
      </tr>
    `;
  }).join("");
}

function updateOverviewView() {
  overviewTimelineChartContainer.innerHTML = renderOverviewTimelineChart();
  overviewTopologyChartContainer.innerHTML = renderOverviewTopologyChart();
  renderGlobalTable();
}

function renderGlobalTable() {
  const search = state.globalSearch.toLowerCase();
  const statusFilter = state.globalStatusFilter;
  const bankFilter = state.globalBankFilter;

  const filtered = GLOBAL_TRANSACTIONS.filter(tx => {
    if (statusFilter !== "all" && tx.status !== statusFilter) return false;
    if (bankFilter !== "all" && !tx.origin.includes(bankFilter) && !tx.dest.includes(bankFilter)) return false;
    if (search && !tx.pseudo.toLowerCase().includes(search) && !tx.amount.toLowerCase().includes(search)) return false;
    return true;
  });

  globalTableBody.innerHTML = filtered.map(tx => {
    let badgeClass = "pill-green";
    if (tx.status === "frozen") badgeClass = "pill-red";
    else if (tx.status === "review") badgeClass = "pill-orange";

    return `
      <tr>
        <td><span class="mono-tag">${tx.time}</span></td>
        <td><span class="mono-tag">${tx.pseudo.slice(0, 16)}...</span></td>
        <td><strong>${tx.origin}</strong></td>
        <td><strong>${tx.dest}</strong></td>
        <td><strong>${tx.amount}</strong></td>
        <td><code>${tx.score}</code></td>
        <td><span class="pill ${badgeClass}">${tx.decision}</span></td>
        <td><span class="pill pill-gray">${tx.latency}</span></td>
      </tr>
    `;
  }).join("");
}

// -----------------------------------------------------------------------------
// PAGE NAVIGATION SWITCHER
// -----------------------------------------------------------------------------
function switchPage(pageName) {
  state.activePage = pageName;

  // Toggle Tab Button Active Classes
  tabBtnInfo.classList.toggle("active", pageName === "info");
  tabBtnBank.classList.toggle("active", pageName === "bank");
  tabBtnOverview.classList.toggle("active", pageName === "overview");

  // Toggle Page View Active Classes
  viewInfo.classList.toggle("active", pageName === "info");
  viewBank.classList.toggle("active", pageName === "bank");
  viewOverview.classList.toggle("active", pageName === "overview");

  if (pageName === "info") {
    updateInfoView();
  } else if (pageName === "bank") {
    updateBankView();
  } else if (pageName === "overview") {
    updateOverviewView();
  }
}

// -----------------------------------------------------------------------------
// EVENT LISTENERS SETUP
// -----------------------------------------------------------------------------
function setupListeners() {
  // Page Nav Tabs
  tabBtnInfo.addEventListener("click", () => switchPage("info"));
  tabBtnBank.addEventListener("click", () => switchPage("bank"));
  tabBtnOverview.addEventListener("click", () => switchPage("overview"));

  // Information View Listeners
  btnScenarioAttack.addEventListener("click", () => {
    state.scenario = "attack";
    btnScenarioAttack.classList.add("active");
    btnScenarioPayroll.classList.remove("active");
    updateInfoView();
  });

  btnScenarioPayroll.addEventListener("click", () => {
    state.scenario = "payroll";
    btnScenarioPayroll.classList.add("active");
    btnScenarioAttack.classList.remove("active");
    updateInfoView();
  });

  sigmaSlider.addEventListener("input", (e) => {
    state.sigma = parseFloat(e.target.value);
    updateInfoView();
  });

  btnGateValid.addEventListener("click", () => {
    state.gateMode = "valid";
    btnGateValid.classList.add("active");
    btnGateTampered.classList.remove("active");
    btnGatePlaintext.classList.remove("active");
    updateInfoView();
  });

  btnGateTampered.addEventListener("click", () => {
    state.gateMode = "tampered";
    btnGateTampered.classList.add("active");
    btnGateValid.classList.remove("active");
    btnGatePlaintext.classList.remove("active");
    updateInfoView();
  });

  btnGatePlaintext.addEventListener("click", () => {
    state.gateMode = "plaintext";
    btnGatePlaintext.classList.add("active");
    btnGateValid.classList.remove("active");
    btnGateTampered.classList.remove("active");
    updateInfoView();
  });

  btnRehashPayload.addEventListener("click", async () => {
    const freshSalt = Date.now().toString(16);
    state.pseudoId = await computeHmacSha256(
      CONFIG.sharedHmacKey,
      CONFIG.rawAccount + ":" + freshSalt
    );
    updateInfoView();
  });

  // Singular Bank View Listeners
  btnBankA.addEventListener("click", () => {
    state.selectedBank = "bankA";
    btnBankA.classList.add("active");
    btnBankB.classList.remove("active");
    btnBankC.classList.remove("active");
    updateBankView();
  });

  btnBankB.addEventListener("click", () => {
    state.selectedBank = "bankB";
    btnBankB.classList.add("active");
    btnBankA.classList.remove("active");
    btnBankC.classList.remove("active");
    updateBankView();
  });

  btnBankC.addEventListener("click", () => {
    state.selectedBank = "bankC";
    btnBankC.classList.add("active");
    btnBankA.classList.remove("active");
    btnBankB.classList.remove("active");
    updateBankView();
  });

  bankTableFilters.querySelectorAll(".table-filter-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      bankTableFilters.querySelectorAll(".table-filter-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      state.bankTableFilter = btn.getAttribute("data-filter");
      renderBankTable();
    });
  });

  // Overview Page Listeners
  globalSearchInput.addEventListener("input", (e) => {
    state.globalSearch = e.target.value;
    renderGlobalTable();
  });

  globalStatusSelect.addEventListener("change", (e) => {
    state.globalStatusFilter = e.target.value;
    renderGlobalTable();
  });

  globalBankSelect.addEventListener("change", (e) => {
    state.globalBankFilter = e.target.value;
    renderGlobalTable();
  });
}

// -----------------------------------------------------------------------------
// INITIALIZATION
// -----------------------------------------------------------------------------
async function init() {
  state.pseudoId = await computeHmacSha256(CONFIG.sharedHmacKey, CONFIG.rawAccount);
  setupListeners();
  updateInfoView();
  updateBankView();
  updateOverviewView();
}

document.addEventListener("DOMContentLoaded", init);
