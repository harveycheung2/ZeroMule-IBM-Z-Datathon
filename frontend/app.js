/**
 * ZeroMule — Interactive Frontend Logic for Fraud & Mule Ring Detection
 * Architecture: Directed-GIN, Salted PSI, Differential Privacy on IBM LinuxONE (s390x)
 * Design System: Apple WWDC Principles (Response, Interruption, Physical Feedback)
 */

document.addEventListener('DOMContentLoaded', () => {
  // =========================================================================
  // 1. Interactive Tab Switching & Dynamic AML Enclave Chart Updates
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

  // AML Datasets per Tab
  const tabDatasets = {
    flow: {
      bars: [
        { x: 35, y: 105, h: 15, class: 'bar-primary' },
        { x: 150, y: 108, h: 12, class: 'bar-primary' },
        { x: 260, y: 110, h: 10, class: 'bar-primary' },
        { x: 370, y: 120, h: 92, class: 'bar-accent' },
        { x: 470, y: 108, h: 12, class: 'bar-primary' },
        { x: 560, y: 90, h: 30, class: 'bar-light' }
      ],
      spline: "M 46 112 Q 100 110, 161 114 T 271 115 T 382 205 T 481 114 T 571 105",
      dots: [
        { cx: 46, cy: 112, r: 3.5, label: "Oct 25", val: "$34,200 Screened", sub: "Risk: 0.08 • Benign" },
        { cx: 161, cy: 114, r: 3.5, label: "Nov 25", val: "$41,500 Screened", sub: "Risk: 0.12 • Benign" },
        { cx: 271, cy: 115, r: 3.5, label: "Dec 25", val: "$58,900 Screened", sub: "Risk: 0.15 • Normal" },
        { cx: 382, cy: 205, r: 4.5, label: "Jan 26", val: "$280,000 Ring #104", sub: "Risk: 0.94 • FROZEN (<25ms)", crit: true },
        { cx: 481, cy: 114, r: 3.5, label: "Feb 26", val: "$36,400 Screened", sub: "Risk: 0.09 • Clear" },
        { cx: 571, cy: 105, r: 3.5, label: "Mar 26", val: "$48,100 Screened", sub: "Risk: 0.07 • Clear" }
      ],
      summary: [
        { label: "Total Screened", val: "1,284,520", unit: "tx" },
        { label: "Boundary Intersections", val: "744", unit: "nodes" },
        { label: "Laundering Prevented", val: "$540,200", unit: "USD" },
        { label: "P99 Inference SLA", val: "24.8", unit: "ms" }
      ]
    },
    mules: {
      bars: [
        { x: 35, y: 80, h: 40, class: 'bar-primary' },
        { x: 150, y: 70, h: 50, class: 'bar-primary' },
        { x: 260, y: 65, h: 55, class: 'bar-primary' },
        { x: 370, y: 40, h: 80, class: 'bar-accent' },
        { x: 470, y: 55, h: 65, class: 'bar-primary' },
        { x: 560, y: 60, h: 60, class: 'bar-light' }
      ],
      spline: "M 46 80 Q 100 75, 161 70 T 271 65 T 382 40 T 481 55 T 571 60",
      dots: [
        { cx: 46, cy: 80, r: 3.5, label: "Oct 25", val: "6 Mule Cycles", sub: "Cross-Bank PR-AUC: 0.88" },
        { cx: 161, cy: 70, r: 3.5, label: "Nov 25", val: "8 Mule Cycles", sub: "Cross-Bank PR-AUC: 0.89" },
        { cx: 271, cy: 65, r: 3.5, label: "Dec 25", val: "9 Mule Cycles", sub: "Cross-Bank PR-AUC: 0.89" },
        { cx: 382, cy: 40, r: 4.5, label: "Jan 26", val: "14 Mule Cycles Intercepted", sub: "Ring Solved: 95.6% Recall", crit: true },
        { cx: 481, cy: 55, r: 3.5, label: "Feb 26", val: "6 Mule Cycles", sub: "Cross-Bank PR-AUC: 0.90" },
        { cx: 571, cy: 60, r: 3.5, label: "Mar 26", val: "5 Mule Cycles", sub: "Cross-Bank PR-AUC: 0.91" }
      ],
      summary: [
        { label: "Active Rings Solved", val: "48", unit: "rings" },
        { label: "Mule Ring Recall", val: "95.6%", unit: "resolved" },
        { label: "Isolated Bank Miss Rate", val: "78.2%", unit: "blind spot" },
        { label: "Model PR-AUC", val: "0.892", unit: "enclave" }
      ]
    },
    boundaries: {
      bars: [
        { x: 35, y: 95, h: 25, class: 'bar-primary' },
        { x: 150, y: 90, h: 30, class: 'bar-primary' },
        { x: 260, y: 85, h: 35, class: 'bar-primary' },
        { x: 370, y: 75, h: 45, class: 'bar-accent' },
        { x: 470, y: 90, h: 30, class: 'bar-primary' },
        { x: 560, y: 85, h: 35, class: 'bar-light' }
      ],
      spline: "M 46 95 Q 100 92, 161 90 T 271 85 T 382 75 T 481 90 T 571 85",
      dots: [
        { cx: 46, cy: 95, r: 3.5, label: "Oct 25", val: "112 Intersections", sub: "Salted HMAC-SHA256 Match" },
        { cx: 161, cy: 90, r: 3.5, label: "Nov 25", val: "128 Intersections", sub: "Salted HMAC-SHA256 Match" },
        { cx: 271, cy: 85, r: 3.5, label: "Dec 25", val: "144 Intersections", sub: "Salted HMAC-SHA256 Match" },
        { cx: 382, cy: 75, r: 4.5, label: "Jan 26", val: "182 Intersections", sub: "Peak Smurfing Overlap", crit: true },
        { cx: 481, cy: 90, r: 3.5, label: "Feb 26", val: "96 Intersections", sub: "Salted HMAC-SHA256 Match" },
        { cx: 571, cy: 85, r: 3.5, label: "Mar 26", val: "82 Intersections", sub: "Salted HMAC-SHA256 Match" }
      ],
      summary: [
        { label: "Boundary Counterparties", val: "744", unit: "hashes" },
        { label: "PII Exposed", val: "0", unit: "bytes (Zero-Leak)" },
        { label: "DP Perturbation (ε)", val: "1.42 / 2.0", unit: "RDP" },
        { label: "PSI Set Match Time", val: "1.18", unit: "ms" }
      ]
    },
    latencies: {
      bars: [
        { x: 35, y: 115, h: 10, class: 'bar-primary' },
        { x: 150, y: 116, h: 8, class: 'bar-primary' },
        { x: 260, y: 95, h: 25, class: 'bar-primary' },
        { x: 370, y: 70, h: 50, class: 'bar-accent' },
        { x: 470, y: 110, h: 12, class: 'bar-primary' },
        { x: 560, y: 65, h: 55, class: 'bar-light' }
      ],
      spline: "M 46 115 Q 100 115, 161 116 T 271 95 T 382 70 T 481 110 T 571 65",
      dots: [
        { cx: 46, cy: 115, r: 3.5, label: "Stage 1: PSI", val: "1.18 ms (P99)", sub: "Cryptographic Lookup" },
        { cx: 161, cy: 116, r: 3.5, label: "Stage 2: DP", val: "0.42 ms (P99)", sub: "L2 Clip & Noise" },
        { cx: 271, cy: 95, r: 3.5, label: "Stage 3: GAT", val: "6.80 ms (P99)", sub: "Boundary Attention" },
        { cx: 382, cy: 70, r: 4.5, label: "Stage 4: Head", val: "4.10 ms (P99)", sub: "Contrastive MLP Head", crit: true },
        { cx: 481, cy: 110, r: 3.5, label: "Stage 5: Fair", val: "0.10 ms (P99)", sub: "Equalized-Odds Gate" },
        { cx: 571, cy: 65, r: 3.5, label: "Roundtrip", val: "24.80 ms (P99)", sub: "Target < 30ms PASSED" }
      ],
      summary: [
        { label: "P50 Round-Trip", val: "13.45", unit: "ms" },
        { label: "P90 Latency", val: "19.20", unit: "ms" },
        { label: "P99 Hardware SLA", val: "24.80", unit: "ms (< 30ms)" },
        { label: "LinuxONE Platform", val: "s390x", unit: "CPACF SIMD" }
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
  // 2. Interactive AI Assistant / Enclave AML Copilot
  // =========================================================================
  const chatInput = document.getElementById('chatInput');
  const chatSendBtn = document.getElementById('chatSendBtn');
  const chatLog = document.getElementById('chatLog');
  const promptChips = document.querySelectorAll('.prompt-chip');
  const modelPickerBtn = document.getElementById('modelPickerBtn');
  const modelDropdownMenu = document.getElementById('modelDropdownMenu');
  const selectedModelLabel = document.getElementById('selectedModelLabel');
  const modelOptions = document.querySelectorAll('.model-option');

  // ZeroMule AML Domain Knowledge Base
  const aiKnowledgeBase = {
    ring104: "Mule Ring #104 was flagged within 24.8ms on IBM LinuxONE: 4 accounts cycled $280,000 across Bank A -> Bank B -> Bank C with a 0.94 Directed-GIN anomaly score. Equalized-Odds thresholding confirmed zero elderly false-positive lockouts, holding illicit funds prior to inter-bank clearing.",
    psi: "Salted HMAC-SHA256 PSI computes cryptographic hash intersections across participant ledgers using an ephemeral salt agreed upon via key exchange. Participating banks never broadcast internal account IDs, customer balances, or PII—only blind boundary hashes match in the secure enclave.",
    fairness: "ZeroMule applies Equalized-Odds threshold calibration on the NeurIPS Bank Account Fraud (BAF) suite. This calibrates group-specific decision gates: |FPR(Senior >= 65) - FPR(Standard)| <= 0.015. Senior accounts are shielded from scam lockouts with an empirical parity gap of only 0.2%.",
    latency: "Hardware profiling on IBM LinuxONE (s390x) verifies: Stage 1 (PSI: 1.18ms) + Stage 2 (DP Noise: 0.42ms) + Stage 3 (GAT + Contrastive Head: 11.85ms) = 24.8ms P99 roundtrip. This strictly satisfies the 30ms pre-settlement SLA constraint.",
    default: "Enclave Telemetry active on IBM LinuxONE s390x Secure Execution. Differential Privacy budget: ε=1.42 / 2.0 (δ=10⁻⁵). 48 multi-bank circular rings solved with zero PII leakage."
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
    if (lower.includes('104') || lower.includes('frozen') || lower.includes('mule ring')) {
      responseText = aiKnowledgeBase.ring104;
    } else if (lower.includes('psi') || lower.includes('pii') || lower.includes('leakage') || lower.includes('hash')) {
      responseText = aiKnowledgeBase.psi;
    } else if (lower.includes('fairness') || lower.includes('senior') || lower.includes('elderly') || lower.includes('parity')) {
      responseText = aiKnowledgeBase.fairness;
    } else if (lower.includes('latency') || lower.includes('s390x') || lower.includes('sla') || lower.includes('speed')) {
      responseText = aiKnowledgeBase.latency;
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
      appendChatMessage('ai', "Enclave Telemetry Audit: 48 cross-bank laundering rings identified. Equalized-Odds calibration maintains elderly disparity gap at 0.2% (Target SLA <= 1.5%).");
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
