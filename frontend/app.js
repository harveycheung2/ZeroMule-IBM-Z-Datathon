/**
 * ZeroMule — Interactive Frontend Logic
 * Design System: Apple WWDC Principles (Response, Interruption, Physical Feedback)
 */

document.addEventListener('DOMContentLoaded', () => {
  // =========================================================================
  // 1. Interactive Tab Switching & Dynamic Chart Updates
  // =========================================================================
  const reportTabs = document.querySelectorAll('.report-tab');
  const chartBarsGroup = document.getElementById('chartBarsGroup');
  const splinePath = document.getElementById('chartSplinePath');
  const chartTooltip = document.getElementById('chartTooltip');
  const tooltipHeader = document.getElementById('tooltipHeader');
  const tooltipValue = document.getElementById('tooltipValue');
  const tooltipSub = document.getElementById('tooltipSub');
  const chartCanvasArea = document.getElementById('chartCanvasArea');

  // Datasets per tab
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
        { cx: 46, cy: 112, r: 3.5, label: "Oct 25", val: "-15 tCO2e", sub: "Standard Flow" },
        { cx: 161, cy: 114, r: 3.5, label: "Nov 25", val: "-12 tCO2e", sub: "Standard Flow" },
        { cx: 271, cy: 115, r: 3.5, label: "Dec 25", val: "-10 tCO2e", sub: "Standard Flow" },
        { cx: 382, cy: 205, r: 4.5, label: "Jan 2026", val: "-480 tCO2e (Intercepted)", sub: "Mule Ring #104 • 24.8ms P99", crit: true },
        { cx: 481, cy: 114, r: 3.5, label: "Feb 2026", val: "-12 tCO2e", sub: "Stabilized Flow" },
        { cx: 571, cy: 105, r: 3.5, label: "Mar 2026", val: "+30 tCO2e (Cleared)", sub: "Benign Inbound" }
      ]
    },
    reductions: {
      bars: [
        { x: 35, y: 80, h: 40, class: 'bar-primary' },
        { x: 150, y: 70, h: 50, class: 'bar-primary' },
        { x: 260, y: 65, h: 55, class: 'bar-primary' },
        { x: 370, y: 50, h: 70, class: 'bar-accent' },
        { x: 470, y: 45, h: 75, class: 'bar-primary' },
        { x: 560, y: 40, h: 80, class: 'bar-light' }
      ],
      spline: "M 46 80 Q 100 75, 161 70 T 271 65 T 382 50 T 481 45 T 571 40",
      dots: [
        { cx: 46, cy: 80, r: 3.5, label: "Oct 25", val: "40 tCO2e Reduction", sub: "Optimized Baseline" },
        { cx: 161, cy: 70, r: 3.5, label: "Nov 25", val: "50 tCO2e Reduction", sub: "Process Efficiency" },
        { cx: 271, cy: 65, r: 3.5, label: "Dec 25", val: "55 tCO2e Reduction", sub: "Optimized Baseline" },
        { cx: 382, cy: 50, r: 4.5, label: "Jan 2026", val: "70 tCO2e Reduction", sub: "Peak Efficiency" },
        { cx: 481, cy: 45, r: 3.5, label: "Feb 2026", val: "75 tCO2e Reduction", sub: "Maintained Savings" },
        { cx: 571, cy: 40, r: 3.5, label: "Mar 2026", val: "80 tCO2e Reduction", sub: "Target Reached" }
      ]
    },
    offsets: {
      bars: [
        { x: 35, y: 95, h: 25, class: 'bar-primary' },
        { x: 150, y: 90, h: 30, class: 'bar-primary' },
        { x: 260, y: 85, h: 35, class: 'bar-primary' },
        { x: 370, y: 120, h: 35, class: 'bar-accent' },
        { x: 470, y: 90, h: 30, class: 'bar-primary' },
        { x: 560, y: 80, h: 40, class: 'bar-light' }
      ],
      spline: "M 46 95 Q 100 92, 161 90 T 271 85 T 382 145 T 481 90 T 571 80",
      dots: [
        { cx: 46, cy: 95, r: 3.5, label: "Oct 25", val: "120 tCO2e Offset", sub: "Certified Green Credits" },
        { cx: 161, cy: 90, r: 3.5, label: "Nov 25", val: "140 tCO2e Offset", sub: "Solar Investment" },
        { cx: 271, cy: 85, r: 3.5, label: "Dec 25", val: "160 tCO2e Offset", sub: "Wind Capacity" },
        { cx: 382, cy: 145, r: 4.5, label: "Jan 2026", val: "220 tCO2e Offset", sub: "High Activity Buffer" },
        { cx: 481, cy: 90, r: 3.5, label: "Feb 2026", val: "150 tCO2e Offset", sub: "Certified Credits" },
        { cx: 571, cy: 80, r: 3.5, label: "Mar 2026", val: "180 tCO2e Offset", sub: "Sustained Compliance" }
      ]
    },
    transfers: {
      bars: [
        { x: 35, y: 110, h: 10, class: 'bar-primary' },
        { x: 150, y: 110, h: 10, class: 'bar-primary' },
        { x: 260, y: 105, h: 15, class: 'bar-primary' },
        { x: 370, y: 120, h: 80, class: 'bar-accent' },
        { x: 470, y: 112, h: 8, class: 'bar-primary' },
        { x: 560, y: 100, h: 20, class: 'bar-light' }
      ],
      spline: "M 46 110 Q 100 110, 161 110 T 271 105 T 382 195 T 481 112 T 571 100",
      dots: [
        { cx: 46, cy: 110, r: 3.5, label: "Oct 25", val: "$14,000 Volume", sub: "Cross-Bank ACH" },
        { cx: 161, cy: 110, r: 3.5, label: "Nov 25", val: "$18,500 Volume", sub: "Cross-Bank Wire" },
        { cx: 271, cy: 105, r: 3.5, label: "Dec 25", val: "$22,000 Volume", sub: "Inter-Bank Fedwire" },
        { cx: 382, cy: 195, r: 4.5, label: "Jan 2026", val: "$280,000 Smurfed Ring", sub: "Pre-Settlement Scam Freeze", crit: true },
        { cx: 481, cy: 112, r: 3.5, label: "Feb 2026", val: "$16,200 Volume", sub: "Normal Velocity" },
        { cx: 571, cy: 100, r: 3.5, label: "Mar 2026", val: "$31,000 Volume", sub: "Settled Clear" }
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

        chartTooltip.style.left = `${Math.min(Math.max(ptX - 60, 10), rect.width - 150)}px`;
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

          chartTooltip.style.left = `${Math.min(Math.max(ptX - 60, 10), rect.width - 150)}px`;
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
  // 2. Interactive AI Assistant / Chat Copilot
  // =========================================================================
  const chatInput = document.getElementById('chatInput');
  const chatSendBtn = document.getElementById('chatSendBtn');
  const chatLog = document.getElementById('chatLog');
  const promptChips = document.querySelectorAll('.prompt-chip');
  const modelPickerBtn = document.getElementById('modelPickerBtn');
  const modelDropdownMenu = document.getElementById('modelDropdownMenu');
  const selectedModelLabel = document.getElementById('selectedModelLabel');
  const modelOptions = document.querySelectorAll('.model-option');

  // Intelligent Context-Aware AI Responses
  const aiKnowledgeBase = {
    travel: "Analysis indicates a 14% increase in Travel-related scope emissions due to global executive roadshows in Q1. In ZeroMule's cross-bank lens, cross-border counterparty travel bookings correlated with rapid multi-hop wire settlement transfers.",
    scope3: "Scope 3 emissions rose primarily due to external supply chain manufacturing updates in Category 1 (Purchased Goods). Mitigation actions include supplier compliance audits and automated differential privacy accounting.",
    ring104: "Mule Ring #104 was flagged within 24.8ms on IBM LinuxONE: 4 accounts cycled $280,000 across Bank A -> Bank B -> Bank C with a 0.94 Directed-GIN anomaly score. Equalized-Odds thresholding confirmed zero elderly false-positive freeze.",
    default: "Telemetry verified on IBM Z / LinuxONE Secure Execution Enclave. All cryptographic PSI lookups completed in 1.18ms with active Rényi Differential Privacy budget (ε=2.0, δ=1e-5)."
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
    if (lower.includes('travel')) {
      responseText = aiKnowledgeBase.travel;
    } else if (lower.includes('scope 3') || lower.includes('quarter')) {
      responseText = aiKnowledgeBase.scope3;
    } else if (lower.includes('ring') || lower.includes('spike') || lower.includes('104')) {
      responseText = aiKnowledgeBase.ring104;
    }

    // Simulate Natural AI Response Typing
    setTimeout(() => {
      appendChatMessage('ai', responseText);
    }, 350);
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
