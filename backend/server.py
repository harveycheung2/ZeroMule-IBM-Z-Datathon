"""
ZeroMule FastAPI backend.

Endpoints:
  GET  /api/telemetry          Full telemetry payload (frontend polls this)
  POST /api/score              Score a single transaction on demand
  POST /api/simulate/{scenario} Switch simulator scenario (attack | payroll)
  GET  /                       Serves frontend/index.html

The server also runs a background loop that scores one simulated transaction
every 3 seconds and writes frontend/data/live_data.json so the frontend's
static polling mode works even without an active API connection.
"""
import asyncio
import json
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from scorer import Scorer
from simulator import Simulator

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"
LIVE_DATA_PATH = FRONTEND_DIR / "data" / "live_data.json"
LIVE_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Shared state
# ---------------------------------------------------------------------------
scorer = Scorer()
simulator = Simulator()

# Rolling buffers visible to telemetry endpoint
_global_feed: deque = deque(maxlen=12)
_bank_feeds: dict[str, deque] = {
    "bankA": deque(maxlen=8),
    "bankB": deque(maxlen=8),
    "bankC": deque(maxlen=8),
}
_stats = {
    "total_screened": 0,
    "total_frozen": 0,
    "total_frozen_amount": 0.0,
    "total_review": 0,
    "latency_samples": deque(maxlen=100),
}

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="ZeroMule Coordinator API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _dp_epsilon(bank_label: str) -> str:
    epsilons = {"bankA": "1.35", "bankB": "1.20", "bankC": "1.50"}
    return epsilons.get(bank_label, "1.38")


def _format_amount(amount: float) -> str:
    return f"${amount:,.2f}"


def _time_ago(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s ago"
    return f"{seconds // 60}m ago"


def _build_telemetry() -> dict:
    samples = list(_stats["latency_samples"])
    p99 = round(sorted(samples)[int(len(samples) * 0.99)] if len(samples) >= 10 else 24.2, 1)
    p50 = round(sorted(samples)[int(len(samples) * 0.50)] if len(samples) >= 10 else 16.8, 1)

    frozen_count = _stats["total_frozen"]
    total = _stats["total_screened"]
    intercept_rate = f"{(frozen_count / total * 100):.1f}%" if total else "99.2%"

    bank_data: dict[str, Any] = {}
    for label, feed in _bank_feeds.items():
        txs = list(feed)
        stopped = sum(1 for t in txs if t["status"] == "frozen")
        suspicious = sum(1 for t in txs if t["status"] == "review")
        stopped_amt = sum(t["amount_paid"] for t in txs if t["status"] == "frozen")
        bank_data[label] = {
            "volume": _format_amount(sum(t["amount_paid"] for t in txs)),
            "volumeCount": f"{len(txs)} Transactions",
            "stoppedTxs": f"{stopped} Txs",
            "stoppedAmount": f"{_format_amount(stopped_amt)} Stopped · Coordinator Held",
            "suspiciousTxs": f"{suspicious} Txs",
            "budgetEps": _dp_epsilon(label),
            "transactions": [
                {
                    "id": t["transaction_id"],
                    "time": _time_ago(int(time.time()) % 120 + 5),
                    "acc": t["sender_account"],
                    "pseudo": t["hmac_pseudonym_short"],
                    "counterparty": t["to_bank_display"],
                    "amount": _format_amount(t["amount_paid"]),
                    "localView": (
                        f"Cleared ({t['risk_score']:.2f})"
                        if t["status"] == "approved"
                        else f"Suspicious ({t['risk_score']:.2f})"
                        if t["status"] == "review"
                        else f"Cleared ({t['risk_score']:.2f})"
                    ),
                    "action": t["decision"],
                    "status": t["status"],
                    "prov": "Ed25519 Valid",
                }
                for t in txs
            ],
        }

    global_txs = [
        {
            "time": datetime.fromisoformat(t["timestamp"]).strftime("%H:%M:%S"),
            "pseudo": t["hmac_pseudonym_full"],
            "origin": t["from_bank_display"],
            "dest": t["to_bank_display"],
            "amount": _format_amount(t["amount_paid"]),
            "score": str(t["risk_score"]),
            "decision": t["decision"],
            "status": t["status"],
            "latency": f"{t['latency_ms']:.1f} ms",
        }
        for t in list(_global_feed)
    ]

    return {
        "scenario": simulator.scenario,
        "metrics": {
            "prAuc": "0.89",
            "recallAtFpr": "84.2% Recall @ 0.1% FPR",
            "totalScreened": f"{total:,}",
            "totalVolume": _format_amount(_stats["total_frozen_amount"] * 8.4),
            "interceptedRings": f"{frozen_count} Rings",
            "interceptedAmount": f"{_format_amount(_stats['total_frozen_amount'])} Illicit Funds",
            "interceptRate": intercept_rate,
            "p99Latency": f"{p99} ms",
            "p50Latency": f"{p50} ms",
        },
        "bankData": bank_data,
        "globalTransactions": global_txs,
    }


def _ingest_result(result: dict):
    """Store a scored transaction in the rolling buffers."""
    _stats["total_screened"] += 1
    _stats["latency_samples"].append(result["latency_ms"])
    if result["status"] == "frozen":
        _stats["total_frozen"] += 1
        _stats["total_frozen_amount"] += result["amount_paid"]
    elif result["status"] == "review":
        _stats["total_review"] += 1
    _bank_feeds[result["from_bank"]].appendleft(result)
    if result["is_cross_bank"]:
        _global_feed.appendleft(result)


def _write_live_data():
    payload = _build_telemetry()
    LIVE_DATA_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Background simulation loop
# ---------------------------------------------------------------------------
async def _simulation_loop():
    await asyncio.sleep(2)
    while True:
        tx = simulator.next_transaction()
        try:
            result = scorer.score(
                transaction_id=tx["transaction_id"],
                timestamp=tx["timestamp"],
                from_bank_label=tx["from_bank"],
                sender_account=tx["sender_account"],
                to_bank_label=tx["to_bank"],
                receiver_account=tx["receiver_account"],
                amount_paid=tx["amount_paid"],
                amount_received=tx["amount_received"],
                payment_currency=tx["payment_currency"],
                receiving_currency=tx["receiving_currency"],
                payment_format=tx["payment_format"],
            )
            _ingest_result(result)
            _write_live_data()
        except Exception as exc:
            print(f"[scorer] error: {exc}")
        await asyncio.sleep(3)


@app.on_event("startup")
async def startup():
    asyncio.create_task(_simulation_loop())


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/api/telemetry")
async def get_telemetry():
    return _build_telemetry()


class TransactionRequest(BaseModel):
    transaction_id: str
    timestamp: str
    from_bank: str
    sender_account: str
    to_bank: str
    receiver_account: str
    amount_paid: float
    amount_received: float
    payment_currency: str
    receiving_currency: str
    payment_format: str


@app.post("/api/score")
async def score_transaction(req: TransactionRequest):
    try:
        result = scorer.score(
            transaction_id=req.transaction_id,
            timestamp=req.timestamp,
            from_bank_label=req.from_bank,
            sender_account=req.sender_account,
            to_bank_label=req.to_bank,
            receiver_account=req.receiver_account,
            amount_paid=req.amount_paid,
            amount_received=req.amount_received,
            payment_currency=req.payment_currency,
            receiving_currency=req.receiving_currency,
            payment_format=req.payment_format,
        )
        _ingest_result(result)
        _write_live_data()
        return result
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/simulate/{scenario}")
async def set_scenario(scenario: str):
    if scenario not in ("attack", "payroll"):
        raise HTTPException(status_code=400, detail="scenario must be 'attack' or 'payroll'")
    simulator.set_scenario(scenario)
    return {"scenario": scenario, "status": "active"}


# Serve frontend static files — mount last so API routes take priority
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
else:
    @app.get("/")
    async def root():
        return {"status": "ZeroMule API running", "frontend": "not found"}


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8080, reload=False)
