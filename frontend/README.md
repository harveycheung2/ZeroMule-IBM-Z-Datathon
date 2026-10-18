# Dashboard preview and checks

From the repository root:

```sh
python3 -m http.server 8080 --bind 127.0.0.1 --directory frontend
```

Open http://127.0.0.1:8080 and hard-refresh after edits. No Streamlit process or
package install is needed for this frontend.

Run the dependency-free regression checks with Node.js 18 or newer:

```sh
node --check frontend/app.js
node --test frontend/dashboard.test.cjs
git diff --check
```

## What the views represent

- **Money Flow** is a browser-only, synthetic walkthrough. Selection, descriptions,
  graph and simulated outcome share one local state. Snapshot polling cannot
  overwrite that selection. Both rejected-data modes suppress a decision.
- **Single Bank View** and **Screening Overview** show their respective record
  snapshots. The legacy JSON includes different record sets, so these are labelled
  separately, not reconciled into a fabricated complete ledger. Each view derives
  its cards, charts and filters from the same rows. Counts describe the full
  snapshot before filtering. Transfers marked for hold are not a count of rings,
  confirmed fraud, prevented losses or detection accuracy.
- The API endpoint remains `/api/telemetry` (optionally prefixed by
  `window.ZEROMULE_API_BASE`). Failed or malformed responses fall back to
  `data/live_data.json`. Saved JSON is explicitly labelled **Demo data**. An API
  response is labelled **API snapshot**, not proof of live inference or freshness.
  Missing/empty record lists clear previous rows. Complete failure shows an
  unavailable state. Concurrent polls are skipped; fetches time out after 4 seconds.
- Legacy aggregate metrics, privacy budgets, scenario labels, signature assertions
  and latency fields from the source are deliberately not displayed as verified
  results. Transaction text is escaped before rendering; unsupported statuses and
  malformed amounts remain unknown rather than being shown as clear or zero.

## Evidence boundaries

The noise slider is a mathematical illustration using browser randomness, not a
production privacy mechanism. There is no fabricated epsilon calculation, bank
secret, cryptographic fallback or pretend signature in the frontend. The coded ID
is explicitly a demonstration placeholder and remains stable when noise changes.
No backend privacy or model implementation is changed by this UI work.

The separately labelled LinuxONE benchmark was supplied by the team:

- Timestamp: 2026-10-18T00:05:45.277104+00:00
- Commit: `d5d51311a9f2fa2b8f1f79828c38aacb851b46c6`
- s390x CPU, Python 3.12.15, PyTorch 2.11.0+cpu, 3 threads
- 250 synthetic trials, 24 nodes, 32 edges; random weights, no trained checkpoint
- Median 3.8045965193305165 ms; P99 6.04593634372577 ms
- Log on server: `/home/linux1/zeromule-benchmark.mxK76T/run.log`

This is historical synthetic-compute evidence, not the current UI's latency or an
accuracy result. It excludes network, durable privacy-budget enforcement,
signature verification and settlement. Secure Execution and mutual TLS remain
unverified here. Keep the original run log with the submission evidence.

## Manual review before recording

1. Switch high-risk / salary scenarios. Wait beyond the five-second poll; verify
   the selected button, descriptions and graph still agree.
2. Test both rejected-data buttons in both scenarios, then return to Expected data.
3. Move the noise slider and regenerate a sample; the coded ID should stay stable.
4. Switch all three banks and each decision filter. Compare counts with rows.
5. Combine overview search, bank and decision filters; check empty results.
6. Check narrow and desktop widths. Small screens may scroll the graph/table
   horizontally within their cards; the whole page should not overflow.
7. Confirm saved JSON is not presented as live and no real customer data is used.

The regression suite uses a lightweight DOM harness; visual browser review is
still needed. It is not a backend integration or security certification test.
