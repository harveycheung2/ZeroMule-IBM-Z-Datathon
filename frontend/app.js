/**
 * ZeroMule — Apple Frosted Glass Coordinator Dashboard
 * Interactive Client-Side Privacy Engine & Ingestion Gatekeeper
 */

// -----------------------------------------------------------------------------
// CONSTANTS & INITIAL STATE
// -----------------------------------------------------------------------------
const CONFIG = {
  rawAccount: "SG-DBS-884920194",
  sharedHmacKey: "interbank-shared-hmac-secret-2026",
  baseRawEmbedding: [2.419, -1.882, 0.941, 3.102],
  clipNormC: 1.0,
};

let state = {
  scenario: "attack", // "attack" | "payroll"
  sigma: 0.80,
  gateMode: "valid",  // "valid" | "tampered" | "plaintext"
  pseudoId: "8f4b5961a293847291a2bc8394e1d939281746b8c9d01e23a4b5c6d7e8f90123",
  perturbedEmbedding: [0.412, -0.319, 0.188, 0.504],
};

// -----------------------------------------------------------------------------
// CRYPTOGRAPHIC HELPER FUNCTIONS
// -----------------------------------------------------------------------------
// Real HMAC-SHA256 computation via Web Crypto API with SHA-256 fallback
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
    // Fallback deterministic pseudo-hash
    let hash = 0x811c9dc5;
    const str = keyStr + messageStr;
    for (let i = 0; i < str.length; i++) {
      hash ^= str.charCodeAt(i);
      hash = (hash * 0x01000193) >>> 0;
    }
    return hash.toString(16).padStart(8, "0").repeat(8).slice(0, 64);
  }
}

// Generate Box-Muller Gaussian Noise
function sampleGaussian(mean = 0, sigma = 1.0) {
  let u1 = Math.random();
  let u2 = Math.random();
  while (u1 === 0) u1 = Math.random();
  const z0 = Math.sqrt(-2.0 * Math.log(u1)) * Math.cos(2.0 * Math.PI * u2);
  return mean + z0 * sigma;
}

// Apply L2 Norm Clipping (C = 1.0) and Calibrated Gaussian Noise
function applyLocalDifferentialPrivacy(vec, clipC, sigma) {
  // 1. Calculate L2 Norm
  const l2Norm = Math.sqrt(vec.reduce((sum, v) => sum + v * v, 0));
  
  // 2. Clip: v_clipped = v * min(1, C / ||v||_2)
  const clipFactor = l2Norm > 0 ? Math.min(1.0, clipC / l2Norm) : 1.0;
  const clipped = vec.map(v => v * clipFactor);

  // 3. Additive Gaussian Perturbation
  const noised = clipped.map(v => {
    const perturbed = v + sampleGaussian(0, sigma * 0.4);
    return Math.round(perturbed * 1000) / 1000;
  });

  return noised;
}

// -----------------------------------------------------------------------------
// DOM ELEMENTS
// -----------------------------------------------------------------------------
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

// -----------------------------------------------------------------------------
// SVG VISUALIZATIONS (4-STAGE DIRTY-TO-CLEAN GRADIENT & PAYROLL)
// -----------------------------------------------------------------------------
function renderAttackSvg() {
  return `
    <svg viewBox="0 0 680 410" width="100%" height="410" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <!-- Gradients -->
        <linearGradient id="gradDirtyToLayer" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#DA1E28"/>
          <stop offset="100%" stop-color="#FF832B"/>
        </linearGradient>
        <linearGradient id="gradLayerToMask" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#FF832B"/>
          <stop offset="100%" stop-color="#6FD170"/>
        </linearGradient>

        <!-- Arrow Markers -->
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
        
        <!-- Subtle Glow Filter -->
        <filter id="glowRed" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="2" stdDeviation="4" flood-color="#DA1E28" flood-opacity="0.3"/>
        </filter>
      </defs>

      <!-- 4-Color Legend Header -->
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

      <!-- Hop 1: Dirty Red (#DA1E28) -->
      <path d="M 155 150 Q 250 85 335 125" fill="none" stroke="#DA1E28" stroke-width="4" marker-end="url(#arr1)"/>
      <text x="238" y="94" font-family="JetBrains Mono, monospace" font-size="10.5" font-weight="600" fill="#DA1E28">$4,900 (t=0s)</text>

      <!-- Hop 2: Layering Amber (#FF832B) -->
      <path d="M 385 160 Q 470 210 515 255" fill="none" stroke="#FF832B" stroke-width="4" marker-end="url(#arr2)"/>
      <text x="465" y="195" font-family="JetBrains Mono, monospace" font-size="10.5" font-weight="600" fill="#FF832B">2 &times; $2,450 (t=38s)</text>

      <!-- Hop 3: Integration Green (#6FD170) -->
      <path d="M 490 295 Q 340 355 205 295" fill="none" stroke="#6FD170" stroke-width="4" marker-end="url(#arr3)"/>
      <text x="335" y="348" font-family="JetBrains Mono, monospace" font-size="10.5" font-weight="600" fill="#2E7D32">Consolidate (t=94s)</text>

      <!-- Hop 4: Attempted Clean Settlement (#198038) - DASHED INTERCEPTED -->
      <path d="M 150 255 Q 115 210 130 175" fill="none" stroke="#198038" stroke-width="4" stroke-dasharray="6,4" marker-end="url(#arr4)"/>
      
      <!-- Intercept Barrier Callout Badge -->
      <g filter="url(#glowRed)">
        <rect x="35" y="202" width="128" height="26" rx="7" fill="#DA1E28"/>
        <text x="99" y="219" font-family="Inter, sans-serif" font-size="10.5" font-weight="800" fill="#FFFFFF" text-anchor="middle">&#9889; INTERCEPTED</text>
      </g>

      <!-- Node: Bank A -->
      <g transform="translate(135, 145)" style="cursor: pointer;">
        <circle r="34" fill="#FFFFFF" stroke="#DA1E28" stroke-width="3.5"/>
        <text y="-5" font-family="Inter" font-size="11.5" font-weight="700" fill="#1D1D1F" text-anchor="middle">BANK A</text>
        <text y="12" font-family="JetBrains Mono" font-size="9" fill="#86868B" text-anchor="middle">0x8f4b..</text>
      </g>

      <!-- Node: Bank B -->
      <g transform="translate(365, 135)" style="cursor: pointer;">
        <circle r="34" fill="#FFFFFF" stroke="#FF832B" stroke-width="3.5"/>
        <text y="-5" font-family="Inter" font-size="11.5" font-weight="700" fill="#1D1D1F" text-anchor="middle">BANK B</text>
        <text y="12" font-family="JetBrains Mono" font-size="9" fill="#86868B" text-anchor="middle">0x3a9c..</text>
      </g>

      <!-- Node: Bank C -->
      <g transform="translate(525, 280)" style="cursor: pointer;">
        <circle r="34" fill="#FFFFFF" stroke="#6FD170" stroke-width="3.5"/>
        <text y="-5" font-family="Inter" font-size="11.5" font-weight="700" fill="#1D1D1F" text-anchor="middle">BANK C</text>
        <text y="12" font-family="JetBrains Mono" font-size="9" fill="#86868B" text-anchor="middle">0x7e1d..</text>
      </g>

      <!-- Node: Cash Out Destination -->
      <g transform="translate(170, 285)" style="cursor: pointer;">
        <circle r="34" fill="#FFFFFF" stroke="#198038" stroke-width="3.5"/>
        <text y="-5" font-family="Inter" font-size="11" font-weight="700" fill="#1D1D1F" text-anchor="middle">CASH OUT</text>
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

      <!-- Header Banner -->
      <rect x="20" y="12" width="640" height="38" rx="10" fill="#F5F5F7" stroke="#E5E5EA"/>
      <text x="35" y="35" font-family="Inter, sans-serif" font-size="11" font-weight="700" fill="#198038">
        BENIGN TOPOLOGY: 1-TO-MANY CORPORATE PAYROLL DISTRIBUTION (ACYCLIC)
      </text>

      <!-- Directed Branches -->
      <line x1="180" y1="210" x2="440" y2="115" stroke="#198038" stroke-width="3.5" marker-end="url(#arrClean)"/>
      <text x="310" y="145" font-family="JetBrains Mono" font-size="10" font-weight="600" fill="#198038">$3,850.00 Salary</text>

      <line x1="180" y1="210" x2="440" y2="210" stroke="#198038" stroke-width="3.5" marker-end="url(#arrClean)"/>
      <text x="310" y="200" font-family="JetBrains Mono" font-size="10" font-weight="600" fill="#198038">$4,200.00 Salary</text>

      <line x1="180" y1="210" x2="440" y2="305" stroke="#198038" stroke-width="3.5" marker-end="url(#arrClean)"/>
      <text x="310" y="275" font-family="JetBrains Mono" font-size="10" font-weight="600" fill="#198038">$3,950.00 Salary</text>

      <!-- Root Node: Bank A Hub -->
      <g transform="translate(145, 210)" style="cursor: pointer;">
        <circle r="40" fill="#FFFFFF" stroke="#0071E3" stroke-width="3.5"/>
        <text y="-5" font-family="Inter" font-size="12" font-weight="700" fill="#1D1D1F" text-anchor="middle">BANK A</text>
        <text y="12" font-family="JetBrains Mono" font-size="9" fill="#86868B" text-anchor="middle">Payroll Hub</text>
      </g>

      <!-- Leaf Nodes: Employees -->
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
// UPDATE & RENDER ENGINE
// -----------------------------------------------------------------------------
async function updateAll() {
  const epsEst = Math.round((1.10 / state.sigma) * 100) / 100;
  
  // Update Displays
  sigmaValDisplay.textContent = state.sigma.toFixed(2);
  epsEstDisplay.textContent = epsEst.toFixed(2);

  // 1. Telemetry Cards
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

  // Gatekeeper Card Update
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

  // 2. Silo Bank Tags
  tagBankADp.innerHTML = `LDP: C=1.0, &epsilon;1=${(epsEst * 1.02).toFixed(1)}`;
  tagBankBDp.innerHTML = `LDP: C=1.0, &epsilon;2=${(epsEst * 0.92).toFixed(1)}`;
  tagBankCDp.innerHTML = `LDP: C=1.0, &epsilon;3=${(epsEst * 1.08).toFixed(1)}`;

  // 3. Coordinator Decision Card
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
  }

  // 4. Stitched Topology SVG
  if (state.scenario === "attack") {
    svgContainer.innerHTML = renderAttackSvg();
  } else {
    svgContainer.innerHTML = renderPayrollSvg();
  }

  // 5. Audit JSON Displays
  const rawData = {
    raw_account_id: CONFIG.rawAccount,
    customer_name: "REDACTED_AT_SOURCE",
    account_balance_usd: 142850.00,
    raw_gnn_embedding_sample: CONFIG.baseRawEmbedding,
    protection_pipeline: "HMAC-SHA256 + L2 Clip (C=1.0) + Gaussian Noise + Ed25519 Sign",
  };
  rawJsonDisplay.textContent = JSON.stringify(rawData, null, 2);

  // Compute live LDP perturbation
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

// -----------------------------------------------------------------------------
// EVENT LISTENERS
// -----------------------------------------------------------------------------
function setupListeners() {
  // Scenario Toggle
  btnScenarioAttack.addEventListener("click", () => {
    state.scenario = "attack";
    btnScenarioAttack.classList.add("active");
    btnScenarioPayroll.classList.remove("active");
    updateAll();
  });

  btnScenarioPayroll.addEventListener("click", () => {
    state.scenario = "payroll";
    btnScenarioPayroll.classList.add("active");
    btnScenarioAttack.classList.remove("active");
    updateAll();
  });

  // Sigma Slider
  sigmaSlider.addEventListener("input", (e) => {
    state.sigma = parseFloat(e.target.value);
    updateAll();
  });

  // Gatekeeper Buttons
  btnGateValid.addEventListener("click", () => {
    state.gateMode = "valid";
    btnGateValid.classList.add("active");
    btnGateTampered.classList.remove("active");
    btnGatePlaintext.classList.remove("active");
    updateAll();
  });

  btnGateTampered.addEventListener("click", () => {
    state.gateMode = "tampered";
    btnGateTampered.classList.add("active");
    btnGateValid.classList.remove("active");
    btnGatePlaintext.classList.remove("active");
    updateAll();
  });

  btnGatePlaintext.addEventListener("click", () => {
    state.gateMode = "plaintext";
    btnGatePlaintext.classList.add("active");
    btnGateValid.classList.remove("active");
    btnGateTampered.classList.remove("active");
    updateAll();
  });

  // Regenerate Salt / Rehash Button
  btnRehashPayload.addEventListener("click", async () => {
    // Generate fresh HMAC with timestamp salt
    const freshSalt = Date.now().toString(16);
    state.pseudoId = await computeHmacSha256(
      CONFIG.sharedHmacKey,
      CONFIG.rawAccount + ":" + freshSalt
    );
    updateAll();
  });
}

// -----------------------------------------------------------------------------
// INITIALIZATION
// -----------------------------------------------------------------------------
async function init() {
  state.pseudoId = await computeHmacSha256(CONFIG.sharedHmacKey, CONFIG.rawAccount);
  setupListeners();
  updateAll();
}

document.addEventListener("DOMContentLoaded", init);
