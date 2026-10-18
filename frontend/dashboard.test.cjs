// Run with: node --test frontend/dashboard.test.cjs
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const html = fs.readFileSync(path.join(__dirname, 'index.html'), 'utf8');
const script = fs.readFileSync(path.join(__dirname, 'app.js'), 'utf8');
const fixture = JSON.parse(fs.readFileSync(path.join(__dirname, 'data/live_data.json'), 'utf8'));

function harness() {
  function element() {
    const classes = new Set();
    return { textContent: '', innerHTML: '', className: '', dataset: {}, handlers: {}, attributes: {},
      classList: { toggle(name, on) { on ? classes.add(name) : classes.delete(name); }, contains(name) { return classes.has(name); } },
      setAttribute(name, value) { this.attributes[name] = value; },
      addEventListener(name, fn) { this.handlers[name] = fn; },
      click() { return this.handlers.click?.({ target: this }); },
    };
  }
  const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map(match => match[1]);
  assert.equal(ids.length, new Set(ids).size, 'unique DOM IDs');
  const elements = Object.fromEntries(ids.map(id => [id, element()]));
  const filters = ['all', 'frozen', 'suspicious', 'cleared'].map(filter => Object.assign(element(), { dataset: { filter } }));
  elements.bankTableFilters.querySelectorAll = () => filters;
  const context = vm.createContext({
    window: {}, document: { getElementById(id) { assert.ok(elements[id], 'existing DOM ID: ' + id); return elements[id]; }, addEventListener() {} },
    Intl, Math, AbortSignal, setInterval() {},
    fetch: async url => ({ ok: !url.includes('/api/'), json: async () => structuredClone(fixture) }),
  });
  vm.runInContext(script, context);
  return { elements, filters, context, run: code => vm.runInContext(code, context) };
}

test('saved JSON is labelled demo data and never overwrites the selected scenario', async () => {
  const h = harness();
  await h.run('init()');
  assert.match(h.elements.backendStatusPill.textContent, /Demo data/);
  assert.equal(h.run('state.scenario'), 'attack'); // fixture.scenario is payroll
  assert.match(h.elements.svgContainer.innerHTML, /High-risk transfer/);
  assert.equal(h.elements.btnScenarioAttack.attributes['aria-pressed'], 'true');
  h.elements.btnScenarioPayroll.click();
  await h.run('fetchBackendTelemetry()');
  assert.equal(h.run('state.scenario'), 'payroll');
  assert.match(h.elements.svgContainer.innerHTML, /Normal salary payments/);
  assert.match(h.elements.scenarioBankCards.innerHTML, /12,000/);
  assert.equal(h.elements.kpiOutcome.textContent, 'Clear');
});

test('both gate rejection modes suppress decisions in both scenarios', async () => {
  const h = harness(); await h.run('init()');
  for (const scenario of ['btnScenarioAttack', 'btnScenarioPayroll']) {
    h.elements[scenario].click();
    for (const mode of ['btnGateTampered', 'btnGatePlaintext']) {
      h.elements[mode].click();
      assert.equal(h.elements.kpiOutcome.textContent, 'No decision');
      assert.match(h.elements.coordinatorDecisionCard.innerHTML, /No model result or payment instruction/);
      assert.match(h.elements.svgContainer.innerHTML, /no decision issued/);
      assert.equal(h.elements.payloadJsonDisplay.classList.contains('hidden'), true);
    }
    h.elements.btnGateValid.click();
    assert.equal(h.elements.kpiOutcome.textContent, scenario === 'btnScenarioAttack' ? 'Review' : 'Clear');
  }
});

test('bank counts, filters and totals are calculated from the same rows', async () => {
  const h = harness(); await h.run('init()');
  assert.equal(h.elements.bankKpiVolume.textContent, '$13,000.00');
  assert.equal(h.elements.bankKpiCleared.textContent, 3);
  assert.equal(h.filters[3].textContent, 'Clear (3)');
  h.filters[3].click();
  assert.equal((h.elements.bankTableBody.innerHTML.match(/<tr>/g) || []).length, 3);
  h.elements.btnBankB.click();
  assert.equal(h.run('state.bankTableFilter'), 'all');
  assert.equal(h.elements.bankKpiStopped.textContent, 4);
  assert.equal(h.filters[0].textContent, 'All (6)');
  assert.equal(h.filters[1].textContent, 'Hold (4)');
  h.filters[2].click();
  assert.match(h.elements.bankTableBody.innerHTML, /No matching records/);
});

test('overview ignores invented aggregate metrics and supports combined filters', async () => {
  const h = harness(); await h.run('init()');
  assert.equal(h.elements.overviewScreenedValue.textContent, 4);
  assert.match(h.elements.overviewVolumeBadge.textContent, /14,700.00/);
  assert.equal(h.elements.overviewInterceptedRings.textContent, '2 transfers');
  assert.equal(h.elements.overviewInterceptRate.textContent, '50.0%');
  h.elements.globalStatusSelect.handlers.change({ target: { value: 'frozen' } });
  h.elements.globalBankSelect.handlers.change({ target: { value: 'BANK_B' } });
  assert.equal((h.elements.globalTableBody.innerHTML.match(/<tr>/g) || []).length, 2);
  h.elements.globalSearchInput.handlers.input({ target: { value: 'no such record' } });
  assert.match(h.elements.globalTableBody.innerHTML, /No matching records/);
});

test('API snapshot is not called live; empty snapshots clear stale records', async () => {
  const h = harness(); await h.run('init()');
  h.context.fetch = async () => ({ ok: true, json: async () => ({ globalTransactions: [] }) });
  await h.run('fetchBackendTelemetry()');
  assert.equal(h.elements.backendStatusPill.textContent, 'API snapshot · not verified live');
  assert.equal(h.elements.overviewScreenedValue.textContent, 0);
  assert.equal(h.elements.overviewInterceptRate.textContent, '—');
  assert.equal(h.elements.bankKpiVolumeSub.textContent, '0 records in this snapshot');
});

test('malformed API falls back; total failure clears old snapshots explicitly', async () => {
  const h = harness(); await h.run('init()');
  h.context.fetch = async url => ({ ok: true, json: async () => url.includes('/api/') ? { bankData: { bankA: { transactions: null } } } : fixture });
  await h.run('fetchBackendTelemetry()');
  assert.match(h.elements.backendStatusPill.textContent, /Demo data/);
  h.context.fetch = async () => { throw new Error('offline'); };
  await h.run('fetchBackendTelemetry()');
  assert.equal(h.elements.backendStatusPill.textContent, 'Records unavailable');
  assert.equal(h.elements.overviewScreenedValue.textContent, 0);
  assert.match(h.elements.snapshotStatus.textContent, /walkthrough still works/);
});

test('snapshot fields are escaped and unknown decisions or amounts stay unknown', async () => {
  const h = harness();
  const row = { origin: '<img src=x onerror=alert(1)>', dest: 'BANK_B_SG', pseudo: "'><svg onload=alert(1)>", status: 'anything', amount: 'garbage' };
  h.context.fetch = async () => ({ ok: true, json: async () => ({ globalTransactions: [row] }) });
  await h.run('init()');
  assert.doesNotMatch(h.elements.globalTableBody.innerHTML, /<img|<svg/);
  assert.match(h.elements.globalTableBody.innerHTML, /&lt;img/);
  assert.match(h.elements.globalTableBody.innerHTML, /Not supplied/);
  assert.match(h.elements.overviewVolumeBadge.textContent, /Amount unavailable/);
});

test('noise sample changes without generating a fake epsilon or signature', async () => {
  const h = harness(); await h.run('init()');
  const before = h.elements.payloadJsonDisplay.textContent;
  h.elements.sigmaSlider.handlers.input({ target: { value: '1.50' } });
  const after = JSON.parse(h.elements.payloadJsonDisplay.textContent);
  assert.notEqual(h.elements.payloadJsonDisplay.textContent, before);
  assert.equal(after.noise_scale, 1.5);
  assert.equal(after.coded_id, 'demo-pseudonym-01');
  assert.equal(after.clipped_noisy_summary.length, 4);
  assert.equal(after.clipped_noisy_summary.every(Number.isFinite), true);
  assert.match(after.signature, /Not generated or verified/);
  assert.doesNotMatch(h.elements.payloadJsonDisplay.textContent, /local_epsilon/);
});

test('visible copy separates benchmark evidence from unsupported claims', () => {
  assert.match(html, /3.80 ms median · 6.05 ms P99/);
  assert.match(html, /randomly initialized weights/);
  assert.match(html, /Excludes network/);
  assert.doesNotMatch(html + script, /98\.6%|84\.2%|Gatekeeper Active|Live ML Engine|Enclave Inference SLA/);
});
