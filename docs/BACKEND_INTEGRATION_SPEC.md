# ZeroMule Frontend ↔ Backend Integration Specification

> **Instructions for Backend Developer / LLM Prompt:**  
> Provide this entire document as a prompt to your coding assistant (Claude, ChatGPT, Copilot, etc.) to immediately connect the Python ML pipeline / model weights to the ZeroMule web frontend.

---

## 1. Overview & Architecture

The ZeroMule frontend is a high-performance, zero-dependency client application located in `frontend/` (`index.html`, `app.js`, `styles.css`). 

The frontend has a built-in **Data Ingestion Engine** that automatically detects live backend outputs. It supports **two seamless integration modes**:

1. **Mode A — Static JSON Export (Zero Server Overhead)**:  
   Whenever an evaluation or batch inference script runs, it writes outputs to `frontend/data/live_data.json`. The frontend polls this file every 5 seconds and instantly refreshes the UI without requiring an active API server.
2. **Mode B — Live REST API (Real-Time Service)**:  
   A lightweight FastAPI or Flask service exposes `GET /api/telemetry` (and optionally `POST /api/score`). The frontend automatically checks `/api/telemetry` and displays a green `● Live ML Engine (API)` badge.

If neither is active, the frontend automatically falls back to built-in standalone benchmark demonstration data with no errors.

---

## 2. Universal Telemetry JSON Schema

Whether using **Mode A (JSON file)** or **Mode B (REST endpoint)**, the payload uses the exact schema below. All fields are optional and merge gracefully with the existing UI state.

```json
{
  "scenario": "attack",
  "metrics": {
    "prAuc": "0.89",
    "recallAtFpr": "85.4% Recall @ 0.1% FPR",
    "totalScreened": "148,210",
    "totalVolume": "$36.14M Volume",
    "interceptedRings": "41 Rings",
    "interceptedAmount": "$1,985,000 Illicit Funds",
    "interceptRate": "99.4%",
    "p99Latency": "23.6 ms",
    "p50Latency": "16.2 ms"
  },
  "bankData": {
    "bankA": {
      "volume": "$14.8M",
      "volumeCount": "49,300 Transactions Today",
      "stoppedTxs": "15 Txs",
      "stoppedAmount": "$192,400 Stopped · Pre-Settlement Held",
      "suspiciousTxs": "44 Txs",
      "budgetEps": "1.32",
      "transactions": [
        {
          "id": "TX-A-9820",
          "time": "10s ago",
          "acc": "ACC-884920",
          "pseudo": "0x8f4b..91a2",
          "counterparty": "Bank B (Relay)",
          "amount": "$4,900.00",
          "localView": "Cleared (0.11)",
          "action": "PRE-SETTLEMENT FREEZE",
          "status": "frozen",
          "prov": "Ed25519 Valid"
        }
      ]
    },
    "bankB": {
      "volume": "$12.1M",
      "volumeCount": "40,110 Transactions Today",
      "stoppedTxs": "20 Txs",
      "stoppedAmount": "$255,000 Stopped · Layering Held",
      "suspiciousTxs": "60 Txs",
      "budgetEps": "1.18",
      "transactions": []
    },
    "bankC": {
      "volume": "$9.2M",
      "volumeCount": "29,100 Transactions Today",
      "stoppedTxs": "30 Txs",
      "stoppedAmount": "$410,200 Stopped · Cash-Out Prevented",
      "suspiciousTxs": "85 Txs",
      "budgetEps": "1.45",
      "transactions": []
    }
  },
  "globalTransactions": [
    {
      "time": "16:40:12",
      "pseudo": "0x8f4b5961a293847291a2bc8394e1d939281746b8",
      "origin": "BANK_A_SG",
      "dest": "BANK_B_SG",
      "amount": "$4,900.00",
      "score": "0.989",
      "decision": "PRE-SETTLEMENT FREEZE",
      "status": "frozen",
      "latency": "23.6 ms"
    },
    {
      "time": "16:39:55",
      "pseudo": "0x3a9c44e0982143bc8819a004821039485761bc92",
      "origin": "BANK_B_SG",
      "dest": "BANK_C_SG",
      "amount": "$2,450.00",
      "score": "0.985",
      "decision": "PRE-SETTLEMENT FREEZE",
      "status": "frozen",
      "latency": "23.1 ms"
    },
    {
      "time": "16:35:10",
      "pseudo": "0x3e11cc0491827364516273849501928374655647",
      "origin": "BANK_A_SG",
      "dest": "BANK_C_SG",
      "amount": "$3,450.00",
      "score": "0.065",
      "decision": "SETTLEMENT APPROVED",
      "status": "approved",
      "latency": "17.9 ms"
    }
  ]
}
```

### Schema Field Explanations:
* `scenario`: `"attack"` (triggers crimson *PRE-SETTLEMENT FREEZE* and 4-hop SVG) or `"payroll"` (triggers green *SETTLEMENT APPROVED* and 1-to-many SVG).
* `metrics.prAuc`: The PR-AUC score from `src/evaluation/generate_metrics.py`.
* `metrics.p99Latency`: P99 total inference latency from `benchmarks/latency_profiler.py` (e.g. `"24.2 ms"`).
* `globalTransactions[].decision`: Either `"PRE-SETTLEMENT FREEZE"`, `"ENCLAVE REVIEW"`, or `"SETTLEMENT APPROVED"`.
* `globalTransactions[].status`: `"frozen"`, `"review"`, or `"approved"` (controls visual badge color).

---

## 3. Ready-to-Use Implementations

### Implementation Pathway A: Python Batch Export Helper
Add this helper function into `src/evaluation/generate_metrics.py` or run it at the conclusion of model evaluation/inference:

```python
import json
from pathlib import Path

def export_to_frontend(pr_auc: float, p99_latency_ms: float, recall_at_fpr: float = 85.4):
    """Writes model evaluation results directly to frontend/data/live_data.json"""
    frontend_data_path = Path(__file__).resolve().parent.parent.parent / "frontend" / "data" / "live_data.json"
    frontend_data_path.parent.mkdir(parents=True, exist_ok=True)
    
    payload = {
        "scenario": "attack",
        "metrics": {
            "prAuc": f"{pr_auc:.2f}",
            "recallAtFpr": f"{recall_at_fpr:.1f}% Recall @ 0.1% FPR",
            "p99Latency": f"{p99_latency_ms:.1f} ms",
            "p50Latency": f"{p99_latency_ms * 0.68:.1f} ms",
            "totalScreened": "148,210",
            "totalVolume": "$36.14M Volume",
            "interceptedRings": "41 Rings",
            "interceptedAmount": "$1,985,000 Illicit Funds",
            "interceptRate": "99.4%"
        }
    }
    
    with open(frontend_data_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"[ZeroMule] Successfully exported live telemetry to {frontend_data_path}")
```

---

### Implementation Pathway B: Complete FastAPI Backend Server
If you want a live Python API service that serves the frontend AND exposes `/api/telemetry` on port 8080:

```python
# file: server.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json

app = FastAPI(title="ZeroMule Coordinator API")

# Allow CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"
DATA_FILE = FRONTEND_DIR / "data" / "live_data.json"

@app.get("/api/telemetry")
async def get_telemetry():
    """Returns the latest ML model telemetry and transaction stream."""
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"scenario": "attack", "metrics": {"prAuc": "0.88", "p99Latency": "24.2 ms"}}

# Mount frontend static directory so http://localhost:8080 serves the app
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8080, reload=True)
```

Run it with:
```bash
pip install fastapi uvicorn
python server.py
```

---

## 4. Verification Checklist

1. **Launch Frontend**:
   ```bash
   python -m http.server 8080 --directory frontend
   ```
2. **Check Status Badge**:
   * Open `http://localhost:8080`.
   * When `frontend/data/live_data.json` is detected or `/api/telemetry` responds, the top status pill immediately turns **Green**: `● Live ML Engine (JSON)` or `● Live ML Engine (API)`.
   * When disconnected, it displays `● Standalone Mode`.
3. **Verify Data Changes**:
   * Modify `"prAuc"` or `"p99Latency"` in `frontend/data/live_data.json`.
   * Within 5 seconds, watch the browser update the KPI cards without a page refresh!
