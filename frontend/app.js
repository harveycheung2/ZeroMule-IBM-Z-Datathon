/**
 * ZeroMule — Interactive Frontend Logic for Privacy Release Boundary & Enclave Inference
 * Implementation: BankPrivacyExporter, Persistent SQLite RDP Ledger, Ed25519 Signatures, EnclaveAggregator
 * Architecture Reference: docs/privacy-architecture.md
 * Design System: Apple WWDC Principles (Response, Interruption, Physical Feedback)
 */

document.addEventListener('DOMContentLoaded', () => {
  // =========================================================================
  // 1. Interactive Tab Switching & Dynamic Privacy Release Chart Updates
  // =========================================================================
  const reportTabs = document.querySelectorAll('.report-tab');
  const chartBarsGroup = document.getElementById('chartBarsGroup');
  const splinePath = document.getElementById('chartSplinePath');
  const chartTooltip = document.getElementById('chartTooltip');
  const tooltipHeader = document.getElementById('tooltipHeader');
  const tooltipValue = document.getElementById('tooltipValue');
  const tooltipSub = document.getElementById('tooltipSub');
  const chartCanvasArea = document.getElementById('chartCanvasArea');

  // Summary Cell Elements
  const summaryCells = document.querySelectorAll('.summary-metric-cell');

  // Privacy Datasets per Tab
  const tabDatasets = {
    flow: {
      bars: [
        { x: 35, y: 160, h: 50, class: 'bar-primary' },
        { x: 150, y: 130, h: 80, class: 'bar-primary' },
        { x: 260, y: 110, h: 100, class: 'bar-primary' },
        { x: 370, y: 80, h: 130, class: 'bar-accent' },
        { x: 470, y: 60, h: 150, class: 'bar-primary' },
        { x: 560, y: 45, h: 165, class: 'bar-light' }
      ],
      spline: "M 46 160 Q 100 145, 161 130 T 271 110 T 382 80 T 481 60 T 571 45",
      dots: [
        { cx: 46, cy: 160, r: 3.5, label: "1. Local Encode", val: "Raw Ledgers Kept Local", sub: "Directed-GIN • No PII Export" },
        { cx: 161, cy: 130, r: 3.5, label: "2. Clip & Reserve", val: "SQLite Atomic Lock", sub: "Frobenius Norm • ε <= 2.0 Check" },
        { cx: 271, cy: 110, r: 3.5, label: "3. Gaussian Noise", val: "OS-Random Noise", sub: "std = 2 * C * sigma" },
        { cx: 382, cy: 80, r: 4.5, label: "4. Ed25519 Sign", val: "Versioned Payload Signed", sub: "Allowlisted Edges Only", crit: true },
        { cx: 481, cy: 60, r: 3.5, label: "5. Strict Validate", val: "Pinned Key Verification", sub: "Reject Extra Metadata & Plaintext" },
        { cx: 571, cy: 45, r: 3.5, label: "6. GAT Score >= 0.5", val: "Flagged High-Risk Edges", sub: "Pseudonymous Risk Scored" }
      ],
      summary: [
        { label: "Bank-wide DP Budget", val: "1.42 / 2.0", unit: "ε" },
        { label: "SQLite Ledger State", val: "Atomic", unit: "Persistent" },
        { label: "Ed25519 Provenance", val: "Pinned", unit: "Verified" },
        { label: "Coordinator Schema", val: "Allowlist", unit: "Only" }
      ]
    },
    budget: {
      bars: [
        { x: 35, y: 180, h: 30, class: 'bar-primary' },
        { x: 150, y: 150, h: 60, class: 'bar-primary' },
        { x: 260, y: 120, h: 90, class: 'bar-primary' },
        { x: 370, y: 95, h: 115, class: 'bar-accent' },
        { x: 470, y: 75, h: 135, class: 'bar-primary' },
        { x: 560, y: 68, h: 142, class: 'bar-light' }
      ],
      spline: "M 46 180 Q 100 165, 161 150 T 271 120 T 382 95 T 481 75 T 571 68",
      dots: [
        { cx: 46, cy: 180, r: 3.5, label: "Release 1", val: "ε = 0.32 (δ = 1e-5)", sub: "SQLite Persistent Commit" },
        { cx: 161, cy: 150, r: 3.5, label: "Release 2", val: "ε = 0.65 (δ = 1e-5)", sub: "Rényi DP Order Composition" },
        { cx: 271, cy: 120, r: 3.5, label: "Release 3", val: "ε = 0.98 (δ = 1e-5)", sub: "SQLite Persistent Commit" },
        { cx: 382, cy: 95, r: 4.5, label: "Release 4", val: "ε = 1.25 (δ = 1e-5)", sub: "All Workers Shared Ledger", crit: true },
        { cx: 481, cy: 75, r: 3.5, label: "Release 5", val: "ε = 1.38 (δ = 1e-5)", sub: "Conservative Grid Bound" },
        { cx: 571, cy: 68, r: 3.5, label: "Current State", val: "ε = 1.42 / 2.0 (Cap)", sub: "Exceeding Rejects Atomically" }
      ],
      summary: [
        { label: "Current Bank ε", val: "1.42 / 2.0", unit: "RDP" },
        { label: "Target Delta", val: "1e-5", unit: "Gaussian" },
        { label: "Persistence Engine", val: "SQLite", unit: "WAL Atomic" },
        { label: "Exhaustion Action", val: "Fail-Closed", unit: "Atomic Reject" }
      ]
    },
    hmac: {
      bars: [
        { x: 35, y: 140, h: 70, class: 'bar-primary' },
        { x: 150, y: 130, h: 80, class: 'bar-primary' },
        { x: 260, y: 115, h: 95, class: 'bar-primary' },
        { x: 370, y: 90, h: 120, class: 'bar-accent' },
        { x: 470, y: 105, h: 105, class: 'bar-primary' },
        { x: 560, y: 120, h: 90, class: 'bar-light' }
      ],
      spline: "M 46 140 Q 100 135, 161 130 T 271 115 T 382 90 T 481 105 T 571 120",
      dots: [
        { cx: 46, cy: 140, r: 3.5, label: "Bank A Silo", val: "248 Boundary Pseudonyms", sub: "Key: ZEROMULE_HMAC_KEY_B64" },
        { cx: 161, cy: 130, r: 3.5, label: "Bank B Silo", val: "312 Boundary Pseudonyms", sub: "Shared High-Entropy Secret" },
        { cx: 271, cy: 115, r: 3.5, label: "Bank C Silo", val: "184 Boundary Pseudonyms", sub: "Common Account Namespace" },
        { cx: 382, cy: 90, r: 4.5, label: "Enclave Intersection", val: "744 Intersected Nodes", sub: "Coordinator Receives No Key", crit: true },
        { cx: 481, cy: 105, r: 3.5, label: "Connectivity Graph", val: "Reveals Topology Only", sub: "Conditional DP Guarantee" },
        { cx: 571, cy: 120, r: 3.5, label: "Raw Customer IDs", val: "0 Exposed", sub: "Allowlist Hash Only" }
      ],
      summary: [
        { label: "Matched Pseudonyms", val: "744", unit: "endpoints" },
        { label: "Coordinator Key State", val: "0 bits", unit: "Key Never Sent" },
        { label: "Topology Roster", val: "Disclosed", unit: "Connectivity" },
        { label: "Raw PII Released", val: "0", unit: "bytes" }
      ]
    },
    validation: {
      bars: [
        { x: 35, y: 150, h: 60, class: 'bar-primary' },
        { x: 150, y: 150, h: 60, class: 'bar-primary' },
        { x: 260, y: 150, h: 60, class: 'bar-primary' },
        { x: 370, y: 120, h: 90, class: 'bar-accent' },
        { x: 470, y: 130, h: 80, class: 'bar-primary' },
        { x: 560, y: 90, h: 120, class: 'bar-light' }
      ],
      spline: "M 46 150 Q 100 150, 161 150 T 271 150 T 382 120 T 481 130 T 571 90",
      dots: [
        { cx: 46, cy: 150, r: 3.5, label: "Bank A Signature", val: "Ed25519 Verified", sub: "Pinned Public Key Check" },
        { cx: 161, cy: 150, r: 3.5, label: "Bank B Signature", val: "Ed25519 Verified", sub: "Pinned Public Key Check" },
        { cx: 271, cy: 150, r: 3.5, label: "Bank C Signature", val: "Ed25519 Verified", sub: "Pinned Public Key Check" },
        { cx: 382, cy: 120, r: 4.5, label: "Schema Validation", val: "Strict Schema Enforced", sub: "Rejects Extra Fields / Plaintext", crit: true },
        { cx: 481, cy: 130, r: 3.5, label: "Payload Receipts", val: "Valid Privacy Receipt", sub: "One Release per Request" },
        { cx: 571, cy: 90, r: 3.5, label: "Boundary GAT", val: "Risk Scores >= 0.5 Flagged", sub: "Averages Shared Vectors" }
      ],
      summary: [
        { label: "Signed Releases", val: "3 / 3", unit: "Validated" },
        { label: "Unsigned/Plaintext", val: "Rejected", unit: "Strict Schema" },
        { label: "Sensitivity Bound", val: "||H||F <= 2C", unit: "Frobenius" },
        { label: "Flag Threshold", val: "Score >= 0.5", unit: "Enclave GAT" }
      ]
    }
  };

  let currentTab = 'flow';

  function renderChart(tabKey) {
    const data = tabDatasets[tabKey] || tabDatasets.flow;
    currentTab = tabKey;

    // Render bars
    let barsHtml = '';
    data.bars.forEach((b, i) => {
      barsHtml += `<rect x="${b.x}" y="${b.y}" width="22" height="${b.h}" rx="3" class="bar-fill ${b.class}" data-idx="${i}"></rect>`;
    });
    chartBarsGroup.innerHTML = barsHtml;

    // Update spline
    splinePath.setAttribute('d', data.spline);

    // Update summary cells
    if (data.summary && summaryCells.length === 4) {
      data.summary.forEach((item, idx) => {
        const cell = summaryCells[idx];
        const labelEl = cell.querySelector('.cell-label');
        const valEl = cell.querySelector('.cell-val');
        if (labelEl) labelEl.textContent = item.label;
        if (valEl) {
          valEl.innerHTML = `${item.val} <span class="unit">${item.unit}</span>`;
        }
      });
    }

    // Update or re-bind hoverable dots
    const existingDots = chartCanvasArea.querySelectorAll('.spline-dot');
    existingDots.forEach(d => d.remove());

    const svg = document.getElementById('mainChartSvg');
    data.dots.forEach((dot, idx) => {
      const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      circle.setAttribute("cx", dot.cx);
      circle.setAttribute("cy", dot.cy);
      circle.setAttribute("r", dot.r);
      circle.setAttribute("class", `spline-dot ${dot.crit ? 'dot-critical' : ''}`);

      circle.addEventListener('mouseenter', (e) => {
        const rect = chartCanvasArea.getBoundingClientRect();
        const ptX = (dot.cx / 600) * rect.width;
        const ptY = (dot.cy / 240) * rect.height;

        tooltipHeader.textContent = dot.label;
        tooltipValue.textContent = dot.val;
        tooltipSub.textContent = dot.sub;

        chartTooltip.style.left = `${Math.min(Math.max(ptX - 60, 10), rect.width - 160)}px`;
        chartTooltip.style.top = `${Math.max(ptY - 55, 10)}px`;
        chartTooltip.classList.add('visible');
      });

      circle.addEventListener('mouseleave', () => {
        chartTooltip.classList.remove('visible');
      });

      svg.appendChild(circle);
    });

    // Also bind hover to the bars
    const barRects = chartBarsGroup.querySelectorAll('.bar-fill');
    barRects.forEach(bar => {
      bar.addEventListener('mouseenter', () => {
        const idx = parseInt(bar.getAttribute('data-idx'));
        const dot = data.dots[idx];
        if (dot) {
          const rect = chartCanvasArea.getBoundingClientRect();
          const ptX = (dot.cx / 600) * rect.width;
          const ptY = (dot.cy / 240) * rect.height;

          tooltipHeader.textContent = dot.label;
          tooltipValue.textContent = dot.val;
          tooltipSub.textContent = dot.sub;

          chartTooltip.style.left = `${Math.min(Math.max(ptX - 60, 10), rect.width - 160)}px`;
          chartTooltip.style.top = `${Math.max(ptY - 55, 10)}px`;
          chartTooltip.classList.add('visible');
        }
      });

      bar.addEventListener('mouseleave', () => {
        chartTooltip.classList.remove('visible');
      });
    });
  }

  // Handle Tab Clicks
  reportTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      reportTabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const tabName = tab.getAttribute('data-tab-name');
      renderChart(tabName);
    });
  });

  // Initial Chart Render
  renderChart('flow');


  // =========================================================================
  // 2. Interactive AI Assistant / Enclave Privacy Copilot
  // =========================================================================
  const chatInput = document.getElementById('chatInput');
  const chatSendBtn = document.getElementById('chatSendBtn');
  const chatLog = document.getElementById('chatLog');
  const promptChips = document.querySelectorAll('.prompt-chip');
  const modelPickerBtn = document.getElementById('modelPickerBtn');
  const modelDropdownMenu = document.getElementById('modelDropdownMenu');
  const selectedModelLabel = document.getElementById('selectedModelLabel');
  const modelOptions = document.querySelectorAll('.model-option');

  // Exact Knowledge Base Matching New Privacy Release Policy
  const aiKnowledgeBase = {
    sqlite: "A persistent bank-wide SQLite ledger atomically reserves privacy budget before generating OS-random Gaussian noise. All workers, models and key rotations share that ledger. If an export would cause cumulative epsilon to exceed 2.0 at delta 1e-5, it is atomically rejected. Failures after reservation still consume budget.",
    ed25519: "Each bank holds an independent Ed25519 private signing key, and the coordinator pins its public verification key. The bank signs a versioned payload containing only pseudonymous embeddings, allowlisted edges, bank identity and a privacy receipt. Amounts, timestamps, labels and arbitrary metadata are excluded. Signatures establish bank provenance; they do not prove that a compromised bank applied noise or enforced its budget.",
    hmac: "Banks share a high-entropy HMAC matching key so the same account produces the same pseudonym across institutions; the coordinator never receives that key. Matching reveals equality and connectivity; raw account IDs, balances, and transaction attributes remain strictly local to each bank.",
    flow: "The 5-step protected inference flow: 1. Local Directed-GIN encodes private transactions. 2. BankPrivacyExporter clips whole-batch Frobenius norm and atomically reserves budget in SQLite before adding OS-random Gaussian noise. 3. Bank signs the versioned allowlisted payload with Ed25519. 4. EnclaveAggregator verifies signatures against pinned keys, strict schemas, and vector dimensions. 5. Coordinator runs boundary GAT and flags scores at or above 0.5.",
    disclaimer: "This repository simulates an enclave in Python; hardware attestation must be supplied and verified externally. The DP bound covers embedding values conditional on a disclosed roster/topology; HMAC matching reveals connectivity. SQLite does not prevent privileged filesystem rollback. Benchmark figures are historical demonstration metrics.",
    default: "Banks protect data before export: runtime HMAC keys pseudonymize endpoints, whole-batch clipping and OS-random Gaussian noise protect embedding values, and a persistent SQLite ledger atomically rejects releases exceeding epsilon 2.0 at delta 1e-5. Raw ledgers and model weights remain bank-local."
  };

  function appendChatMessage(sender, text) {
    const msg = document.createElement('div');
    msg.className = `chat-msg ${sender === 'user' ? 'chat-msg-user' : 'chat-msg-ai'}`;
    msg.textContent = text;
    chatLog.appendChild(msg);
    chatLog.scrollTop = chatLog.scrollHeight;
  }

  function handleSendQuery(queryText) {
    const text = queryText || chatInput.value.trim();
    if (!text) return;

    // Append User Message
    appendChatMessage('user', text);
    if (!queryText) chatInput.value = '';

    // Determine Response
    let responseText = aiKnowledgeBase.default;
    const lower = text.toLowerCase();
    if (lower.includes('sqlite') || lower.includes('budget') || lower.includes('reserve') || lower.includes('persist')) {
      responseText = aiKnowledgeBase.sqlite;
    } else if (lower.includes('ed25519') || lower.includes('sign') || lower.includes('pinned') || lower.includes('provenance')) {
      responseText = aiKnowledgeBase.ed25519;
    } else if (lower.includes('hmac') || lower.includes('matching key') || lower.includes('pseudonym') || lower.includes('pii')) {
      responseText = aiKnowledgeBase.hmac;
    } else if (lower.includes('flow') || lower.includes('pipeline') || lower.includes('steps')) {
      responseText = aiKnowledgeBase.flow;
    } else if (lower.includes('attestation') || lower.includes('disclaimer') || lower.includes('benchmark')) {
      responseText = aiKnowledgeBase.disclaimer;
    }

    // Simulate Natural AI Response Typing
    setTimeout(() => {
      appendChatMessage('ai', responseText);
    }, 280);
  }

  // Click on Suggested Prompt Chips
  promptChips.forEach(chip => {
    chip.addEventListener('click', () => {
      const query = chip.getAttribute('data-query');
      handleSendQuery(query);
    });
  });

  // Submit on Send Button
  chatSendBtn.addEventListener('click', () => handleSendQuery());

  // Submit on Enter Key (Shift+Enter for newline)
  chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendQuery();
    }
  });

  // Model Picker Dropdown
  modelPickerBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    modelDropdownMenu.classList.toggle('visible');
  });

  modelOptions.forEach(opt => {
    opt.addEventListener('click', () => {
      modelOptions.forEach(o => o.classList.remove('active'));
      opt.classList.add('active');
      const modelName = opt.getAttribute('data-model');
      selectedModelLabel.textContent = modelName;
      modelDropdownMenu.classList.remove('visible');
    });
  });

  document.addEventListener('click', () => {
    modelDropdownMenu.classList.remove('visible');
  });


  // =========================================================================
  // 3. Navigation & Dismissible Alerts
  // =========================================================================
  const closeAlertBtn = document.getElementById('closeAlert');
  const complianceCard = document.getElementById('complianceCard');

  if (closeAlertBtn && complianceCard) {
    closeAlertBtn.addEventListener('click', () => {
      complianceCard.style.opacity = '0';
      complianceCard.style.transform = 'scale(0.95)';
      setTimeout(() => {
        complianceCard.style.display = 'none';
      }, 200);
    });
  }

  // Details button toast
  const detailsBtn = document.getElementById('detailsBtn');
  if (detailsBtn) {
    detailsBtn.addEventListener('click', () => {
      appendChatMessage('ai', "Privacy Policy: Raw ledgers, model checkpoints and unperturbed embeddings remain bank-local. The coordinator enforces pinned Ed25519 public keys, strict schemas, and flags scores >= 0.5.");
    });
  }

  // Keyboard shortcut '/' to focus search
  document.addEventListener('keydown', (e) => {
    if (e.key === '/' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA') {
      e.preventDefault();
      const searchInput = document.querySelector('.search-input');
      if (searchInput) searchInput.focus();
    }
  });
});
