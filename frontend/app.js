/**
 * ZeroMule presentation frontend.
 * The walkthrough is a simulation. Telemetry snapshots never control its state.
 * Record-level summaries are derived from their own tables, not source KPI claims.
 */
const CONFIG = {
  apiBaseUrl: window.ZEROMULE_API_BASE || "",
  telemetryEndpoint: "/api/telemetry",
  fallbackJsonPath: "data/live_data.json",
  pollIntervalMs: 5000,
};
const BANKS = { bankA: "Bank A", bankB: "Bank B", bankC: "Bank C" };
const state = {
  activePage: "info", scenario: "attack", sigma: 0.8, gateMode: "valid",
  selectedBank: "bankA", bankTableFilter: "all",
  globalSearch: "", globalStatusFilter: "all", globalBankFilter: "all",
  bankData: { bankA: [], bankB: [], bankC: [] }, globalTransactions: [],
  source: "loading", fetching: false, perturbed: [],
};
const byId = id => document.getElementById(id);
const escapeHtml = value => String(value ?? "").replace(/[&<>"']/g, ch =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[ch]);
const money = value => new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(value);
function parseAmount(value) {
  if (typeof value === "number") return Number.isFinite(value) && value >= 0 ? value : null;
  if (typeof value !== "string" || !/^\$?(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d{1,2})?$/.test(value.trim())) return null;
  const number = Number(value.replace(/[$,]/g, ""));
  return Number.isFinite(number) && number >= 0 ? number : null;
}
function statusOf(value) {
  if (value === "frozen") return "frozen";
  if (value === "review" || value === "suspicious") return "review";
  if (value === "approved" || value === "cleared") return "approved";
  return "unknown";
}
function normaliseRows(rows) {
  return rows.filter(row => row && typeof row === "object" && !Array.isArray(row)).map(row => {
    // Keep only fields used by this view. Never inject source strings as markup.
    const clean = {};
    for (const key of ["id", "time", "acc", "pseudo", "counterparty", "origin", "dest"]) {
      clean[key] = typeof row[key] === "string" ? row[key].slice(0, 300) : "";
    }
    clean.status = statusOf(row.status);
    clean.amount = parseAmount(row.amount);
    return clean;
  });
}
function normaliseSnapshot(data) {
  if (!data || typeof data !== "object") throw new Error("Invalid snapshot");
  let recognised = false;
  const banks = { bankA: [], bankB: [], bankC: [] };
  for (const key of Object.keys(BANKS)) {
    const rows = data.bankData?.[key]?.transactions;
    if (rows !== undefined) {
      if (!Array.isArray(rows)) throw new Error("Invalid bank records");
      recognised = true;
      banks[key] = normaliseRows(rows);
    }
  }
  let global = [];
  if (data.globalTransactions !== undefined) {
    if (!Array.isArray(data.globalTransactions)) throw new Error("Invalid overview records");
    recognised = true;
    global = normaliseRows(data.globalTransactions);
  }
  if (!recognised) throw new Error("No supported records");
  return { banks, global };
}
function summarise(rows) {
  const counts = { frozen: 0, review: 0, approved: 0, unknown: 0 };
  for (const row of rows) counts[row.status]++;
  const known = rows.every(row => row.amount !== null);
  const held = rows.filter(row => row.status === "frozen");
  return {
    ...counts, total: rows.length,
    volume: known ? money(rows.reduce((sum, row) => sum + row.amount, 0)) : "Amount unavailable",
    heldVolume: held.every(row => row.amount !== null) ? money(held.reduce((sum, row) => sum + row.amount, 0)) : "Amount unavailable",
  };
}
function decisionBadge(status) {
  const labels = { frozen: "Simulated hold", review: "Review", approved: "Clear (example)", unknown: "Not supplied" };
  const colors = { frozen: "red", review: "orange", approved: "green", unknown: "gray" };
  return '<span class="pill pill-' + colors[status] + '">' + labels[status] + '</span>';
}
function bankName(value) {
  return ({ BANK_A_SG: "Bank A", BANK_B_SG: "Bank B", BANK_C_SG: "Bank C" })[value] || value || "Not supplied";
}
function activate(ids, selected) {
  for (const id of ids) {
    byId(id).classList.toggle("active", id === selected);
    byId(id).setAttribute("aria-pressed", String(id === selected));
  }
}
function bars(items) {
  const max = Math.max(1, ...items.map(item => item.count));
  return '<div class="summary-bars">' + items.map(item =>
    '<div class="summary-bar-row"><span>' + escapeHtml(item.label) + '</span><div class="summary-track">' +
    '<div class="summary-fill" style="width:' + (item.count / max * 100) + '%;background:' + item.color + '"></div></div>' +
    '<strong>' + item.count + '</strong></div>').join("") + '</div>';
}
function decisionBars(summary) {
  return bars([
    { label: "Simulated hold", count: summary.frozen, color: "#DA1E28" },
    { label: "Review", count: summary.review, color: "#C45100" },
    { label: "Clear", count: summary.approved, color: "#198038" },
    { label: "Not supplied", count: summary.unknown, color: "#777" },
  ]);
}

// A stable illustrative pseudonym is not a cryptographic or anonymous identity.
// This demo intentionally does not embed a pretend bank HMAC secret/signature.
function generateNoiseSample() {
  const raw = [2.419, -1.882, 0.941, 3.102];
  const norm = Math.hypot(...raw);
  state.perturbed = raw.map(value => {
    const u = 1 - Math.random(), v = Math.random();
    const noise = Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v) * state.sigma;
    return Math.round((value / Math.max(1, norm) + noise) * 1000) / 1000;
  });
}
function flowSvg() {
  const attack = state.scenario === "attack";
  const blocked = state.gateMode !== "valid";
  const color = attack ? "#B4232D" : "#147D3A";
  const nodes = attack
    ? [["Bank A", "Sends $4,900"], ["Bank B", "Splits the transfer"], ["Bank C", "Receives both parts"]]
    : [["Bank A", "Employer"], ["Bank B", "Employee accounts"], ["Bank C", "Employee account"]];
  const outcome = blocked ? "Data rejected in simulation — no decision issued"
    : attack ? "Flag for review before cash-out — simulated" : "Normal salary payments — clear in this example";
  return '<svg viewBox="0 0 700 360" role="img" aria-label="' +
    (attack ? "High-risk transfer from Bank A through Bank B to Bank C" : "Normal salary payments from Bank A to Banks B and C") +
    '" xmlns="http://www.w3.org/2000/svg">' +
    '<defs><marker id="flowArrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8" fill="' + color + '"/></marker></defs>' +
    '<text x="350" y="32" text-anchor="middle" font-size="19" font-weight="700" fill="#1D1D1F">' +
    (attack ? "One connected trail across three banks" : "One employer paying three employees") + '</text>' +
    (attack
      ? '<path d="M160 150 H278" fill="none" stroke="' + color + '" stroke-width="3" marker-end="url(#flowArrow)"/>' +
        '<path d="M385 150 H503" fill="none" stroke="' + color + '" stroke-width="3" marker-end="url(#flowArrow)"/>' +
        '<text x="225" y="95" text-anchor="middle" font-size="17">$4,900</text><text x="450" y="95" text-anchor="middle" font-size="17">2 × $2,450</text>'
      : '<path d="M160 150 Q225 65 335 113" fill="none" stroke="' + color + '" stroke-width="3" marker-end="url(#flowArrow)"/>' +
        '<path d="M110 185 Q335 280 560 193" fill="none" stroke="' + color + '" stroke-width="3" marker-end="url(#flowArrow)"/>' +
        '<text x="225" y="85" text-anchor="middle" font-size="16">$3,850 + $4,200</text><text x="335" y="265" text-anchor="middle" font-size="16">$3,950</text>') +
    nodes.map((node, i) => '<rect x="' + (60 + i * 225) + '" y="120" width="100" height="65" rx="18" fill="#FFFFFF" stroke="' + color + '" stroke-width="2"/>' +
      '<text x="' + (110 + i * 225) + '" y="158" text-anchor="middle" font-size="19" font-weight="700">' + node[0] + '</text>' +
      '<text x="' + (110 + i * 225) + '" y="212" text-anchor="middle" font-size="15">' + node[1] + '</text>').join("") +
    '<rect x="20" y="298" width="660" height="42" rx="12" fill="' + (blocked ? "#FFF2D6" : "#F2F4F7") + '"/>' +
    '<text x="350" y="325" text-anchor="middle" font-size="16" fill="#1D1D1F">' + outcome + '</text></svg>';
}
function updateInfoView() {
  const attack = state.scenario === "attack", rejected = state.gateMode !== "valid";
  activate(["btnScenarioAttack", "btnScenarioPayroll"], attack ? "btnScenarioAttack" : "btnScenarioPayroll");
  activate(["btnGateValid", "btnGateTampered", "btnGatePlaintext"],
    ({ valid: "btnGateValid", tampered: "btnGateTampered", plaintext: "btnGatePlaintext" })[state.gateMode]);
  byId("sigmaValDisplay").textContent = state.sigma.toFixed(2);
  byId("kpiOutcome").textContent = rejected ? "No decision" : attack ? "Review" : "Clear";
  byId("kpiGateValue").textContent = rejected ? "Rejected" : "Accepted";
  const descriptions = attack ? [
    "A customer sends $4,900 to Bank B. This bank sees only the outgoing payment.",
    "The money is split into two $2,450 transfers to Bank C.",
    "Two related transfers arrive. Together, the quick split and onward movement warrant review.",
  ] : [
    "An employer sends three salary payments totalling $12,000.",
    "Two employee accounts receive $3,850 and $4,200.",
    "An employee account receives $3,950. The example has no return flow.",
  ];
  byId("scenarioBankCards").innerHTML = descriptions.map((desc, i) =>
    '<div class="silo-box"><strong>' + ["Bank A", "Bank B", "Bank C"][i] +
    '</strong><p class="silo-desc">' + desc + '</p></div>').join("");
  byId("svgContainer").innerHTML = flowSvg();
  byId("coordinatorDecisionCard").className = "glass-card decision-card " + (rejected || attack ? "alert-attack" : "alert-payroll");
  byId("coordinatorDecisionCard").innerHTML =
    '<span class="decision-title">' + (rejected ? "DATA CHECK REJECTED — SIMULATION" : attack ? "FLAG FOR REVIEW — SIMULATION" : "NORMAL PAYMENTS — EXAMPLE") + '</span>' +
    '<p class="decision-body">' + (rejected
      ? "The example stops here. No model result or payment instruction is issued."
      : attack ? "The connected trail reveals a rapid split across banks. An investigator would review it; this example does not confirm fraud or freeze funds."
        : "These payments follow the salary example. No payment is actually approved or settled.") + '</p>';
  byId("rawJsonDisplay").textContent = JSON.stringify({
    example_only: true, account_id: "DEMO-ACCOUNT-01", customer: "Synthetic customer",
    numerical_summary: [2.419, -1.882, 0.941, 3.102],
  }, null, 2);
  byId("payloadJsonDisplay").textContent = JSON.stringify({
    example_only: true, coded_id: "demo-pseudonym-01",
    clipped_noisy_summary: state.perturbed,
    noise_scale: state.sigma, privacy_guarantee: "Not established by this illustration",
    signature: "Not generated or verified in this frontend",
  }, null, 2);
  byId("payloadJsonDisplay").classList.toggle("hidden", rejected);
  byId("gatekeeperErrorAlert").classList.toggle("hidden", !rejected);
  byId("gatekeeperErrorAlert").textContent = state.gateMode === "tampered"
    ? "Simulated rejection: the data was altered. A deployed service must actually verify its signature."
    : "Simulated rejection: an account ID was exposed. A deployed service must enforce the allowed fields.";
}
function updateBankView() {
  activate(["btnBankA", "btnBankB", "btnBankC"], { bankA: "btnBankA", bankB: "btnBankB", bankC: "btnBankC" }[state.selectedBank]);
  const rows = state.bankData[state.selectedBank], summary = summarise(rows);
  byId("bankIdPill").textContent = BANKS[state.selectedBank];
  byId("bankKpiVolume").textContent = summary.volume;
  byId("bankKpiVolumeSub").textContent = summary.total + " records in this snapshot";
  byId("bankKpiStopped").textContent = summary.frozen;
  byId("bankKpiStoppedSub").textContent = summary.heldVolume + " in marked transactions";
  byId("bankKpiSuspicious").textContent = summary.review;
  byId("bankKpiCleared").textContent = summary.approved;
  byId("bankRiskChartContainer").innerHTML = decisionBars(summary);
  const statusMap = { frozen: "frozen", suspicious: "review", cleared: "approved" };
  const labels = { all: "All", frozen: "Hold", suspicious: "Review", cleared: "Clear" };
  for (const button of byId("bankTableFilters").querySelectorAll("button")) {
    const filter = button.dataset.filter;
    button.textContent = labels[filter] + " (" + (filter === "all" ? rows.length : summary[statusMap[filter]]) + ")";
    button.classList.toggle("active", filter === state.bankTableFilter);
    button.setAttribute("aria-pressed", String(filter === state.bankTableFilter));
  }
  const filtered = rows.filter(row => state.bankTableFilter === "all" || row.status === statusMap[state.bankTableFilter]);
  byId("bankTableBody").innerHTML = filtered.map(row =>
    "<tr><td>" + escapeHtml(row.id || "Not supplied") + "<div class='source-time'>" + escapeHtml(row.time) +
    "</div></td><td>" + escapeHtml(row.acc) + "</td><td>" + escapeHtml(row.pseudo) +
    "</td><td>" + escapeHtml(bankName(row.counterparty)) + "</td><td>" + (row.amount === null ? "Unavailable" : money(row.amount)) +
    "</td><td>" + decisionBadge(row.status) + "</td></tr>").join("") || '<tr><td colspan="6">No matching records.</td></tr>';
}
function updateOverviewView() {
  const rows = state.globalTransactions, summary = summarise(rows);
  byId("overviewScreenedValue").textContent = summary.total;
  byId("overviewVolumeBadge").textContent = summary.volume + " in listed transfers";
  byId("overviewInterceptedRings").textContent = summary.frozen + " transfers";
  byId("overviewInterceptedAmount").textContent = summary.heldVolume + " marked for hold";
  byId("overviewInterceptRate").textContent = rows.length ? (summary.frozen / rows.length * 100).toFixed(1) + "%" : "—";
  byId("overviewTimelineChartContainer").innerHTML = decisionBars(summary);
  const origins = [...new Set(rows.map(row => row.origin))];
  byId("overviewTopologyChartContainer").innerHTML = origins.length ? bars(origins.map(origin => ({
    label: bankName(origin), count: rows.filter(row => row.origin === origin).length, color: "#0071E3",
  }))) : '<p class="empty-state">No overview records supplied.</p>';
  renderGlobalTable();
}
function renderGlobalTable() {
  const search = state.globalSearch.toLowerCase();
  const filtered = state.globalTransactions.filter(row =>
    (state.globalStatusFilter === "all" || row.status === state.globalStatusFilter) &&
    (state.globalBankFilter === "all" || row.origin.includes(state.globalBankFilter) || row.dest.includes(state.globalBankFilter)) &&
    (!search || [row.pseudo, bankName(row.origin), bankName(row.dest), row.amount === null ? "" : money(row.amount)].join(" ").toLowerCase().includes(search)));
  byId("globalTableBody").innerHTML = filtered.map(row =>
    "<tr><td>" + escapeHtml(row.time) + "</td><td><span title='" + escapeHtml(row.pseudo) + "'>" +
    escapeHtml(row.pseudo.slice(0, 16)) + (row.pseudo.length > 16 ? "…" : "") + "</span></td><td>" +
    escapeHtml(bankName(row.origin)) + "</td><td>" + escapeHtml(bankName(row.dest)) + "</td><td>" +
    (row.amount === null ? "Unavailable" : money(row.amount)) + "</td><td>" + decisionBadge(row.status) + "</td></tr>"
  ).join("") || '<tr><td colspan="6">No matching records.</td></tr>';
}
function switchPage(page) {
  state.activePage = page;
  for (const [key, suffix] of Object.entries({ info: "Info", bank: "Bank", overview: "Overview" })) {
    byId("view" + suffix).classList.toggle("active", key === page);
    byId("tabBtn" + suffix).classList.toggle("active", key === page);
    byId("tabBtn" + suffix).setAttribute("aria-pressed", String(key === page));
  }
}
async function loadSnapshot(url) {
  const response = await fetch(url, { cache: "no-store", signal: AbortSignal.timeout(4000) });
  if (!response.ok) throw new Error("Snapshot unavailable");
  return normaliseSnapshot(await response.json());
}
async function fetchBackendTelemetry() {
  if (state.fetching) return;
  state.fetching = true;
  let snapshot = null, source = "unavailable";
  try {
    try {
      snapshot = await loadSnapshot(CONFIG.apiBaseUrl + CONFIG.telemetryEndpoint);
      source = "api";
    } catch {
      try {
        snapshot = await loadSnapshot(CONFIG.fallbackJsonPath);
        source = "json";
      } catch { /* Show an explicit unavailable state, not a stale live badge. */ }
    }
    state.source = source;
    state.bankData = snapshot?.banks || { bankA: [], bankB: [], bankC: [] };
    state.globalTransactions = snapshot?.global || [];
    const label = source === "api" ? "API snapshot · not verified live"
      : source === "json" ? "Demo data · saved JSON" : "Records unavailable";
    byId("backendStatusPill").textContent = label;
    byId("backendStatusPill").className = "pill pill-gray";
    byId("snapshotStatus").textContent = source === "api"
      ? " API records received; freshness, model execution and deployment protections are not verified by this page."
      : source === "json" ? " Saved sample records loaded. This is not a live model connection."
        : " Could not load record snapshots. The illustrative walkthrough still works.";
    // Deliberately ignore data.scenario, data.metrics and privacy/security claims.
    // Missing and empty lists replace the previous snapshot; no mixed stale banks.
    updateBankView();
    updateOverviewView();
  } finally { state.fetching = false; }
}
function setupListeners() {
  for (const [id, page] of [["tabBtnInfo", "info"], ["tabBtnBank", "bank"], ["tabBtnOverview", "overview"]])
    byId(id).addEventListener("click", () => switchPage(page));
  for (const [id, scenario] of [["btnScenarioAttack", "attack"], ["btnScenarioPayroll", "payroll"]])
    byId(id).addEventListener("click", () => { state.scenario = scenario; updateInfoView(); });
  for (const [id, mode] of [["btnGateValid", "valid"], ["btnGateTampered", "tampered"], ["btnGatePlaintext", "plaintext"]])
    byId(id).addEventListener("click", () => { state.gateMode = mode; updateInfoView(); });
  byId("sigmaSlider").addEventListener("input", event => {
    state.sigma = Math.min(1.5, Math.max(0.1, Number(event.target.value) || 0.8));
    generateNoiseSample(); updateInfoView();
  });
  byId("btnRehashPayload").addEventListener("click", () => { generateNoiseSample(); updateInfoView(); });
  for (const [id, bank] of [["btnBankA", "bankA"], ["btnBankB", "bankB"], ["btnBankC", "bankC"]])
    byId(id).addEventListener("click", () => { state.selectedBank = bank; state.bankTableFilter = "all"; updateBankView(); });
  for (const button of byId("bankTableFilters").querySelectorAll("button"))
    button.addEventListener("click", () => { state.bankTableFilter = button.dataset.filter; updateBankView(); });
  byId("globalSearchInput").addEventListener("input", event => { state.globalSearch = event.target.value; renderGlobalTable(); });
  byId("globalStatusSelect").addEventListener("change", event => { state.globalStatusFilter = event.target.value; renderGlobalTable(); });
  byId("globalBankSelect").addEventListener("change", event => { state.globalBankFilter = event.target.value; renderGlobalTable(); });
}
async function init() {
  setupListeners(); generateNoiseSample(); updateInfoView(); switchPage("info");
  updateBankView(); updateOverviewView();
  await fetchBackendTelemetry();
  setInterval(fetchBackendTelemetry, CONFIG.pollIntervalMs);
}
document.addEventListener("DOMContentLoaded", init);
