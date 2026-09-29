"""Render 6-panel dashboard PNG from data/logs.jsonl (contract: config/dashboard.yaml)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = Path(__file__).resolve().parents[1]
LOG = REPO / "data" / "logs.jsonl"
OUT = REPO / "submission" / "evidence" / "11-dashboard-overview.png"


def load():
    recs = []
    for line in LOG.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                recs.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return recs


def pct(vals, p):
    if not vals:
        return 0
    s = sorted(vals)
    idx = max(0, min(len(s) - 1, round((p / 100) * len(s) + 0.5) - 1))
    return s[idx]


def main():
    recs = load()
    resp = [r for r in recs if r.get("event") == "response_sent"]
    recv = [r for r in recs if r.get("event") == "request_received"]
    fail = [r for r in recs if r.get("event") == "request_failed"]
    lat = [r.get("latency_ms", 0) or 0 for r in resp]
    ttft = [r.get("ttft_ms", 0) or 0 for r in resp]
    cost = [r.get("cost_usd", 0) or 0 for r in resp]
    tin = [r.get("tokens_in", 0) or 0 for r in resp]
    tout = [r.get("tokens_out", 0) or 0 for r in resp]
    qual = [r.get("quality_score", 0) or 0 for r in resp]
    ok_tool = sum(1 for r in recs if r.get("tool_success") is True)
    tot_tool = sum(1 for r in recs if r.get("tool_success") is not None)
    err_rate = 100 * len(fail) / max(1, len(recv))
    retr_ok = 100 * ok_tool / max(1, tot_tool)

    fig, ax = plt.subplots(2, 3, figsize=(15, 8))
    fig.suptitle("K4-L3A Day 13 Monitoring & LLMOps — 60m window, refresh 30s", fontsize=13)

    a = ax[0, 0]
    a.set_title(f"Latency P50/P95/P99 + TTFT (ms)\nP50={pct(lat,50)} P95={pct(lat,95)} P99={pct(lat,99)} TTFT_P95={pct(ttft,95)}")
    a.bar(["P50", "P95", "P99", "TTFT_P95"], [pct(lat, 50), pct(lat, 95), pct(lat, 99), pct(ttft, 95)])
    a.axhline(3000, linestyle="--")
    a.set_ylabel("ms")
    a.text(0.5, 3050, "SLO 3000ms", fontsize=8)

    a = ax[0, 1]
    a.set_title(f"Traffic (count={len(recv)}, rpm>=1)")
    a.bar(["request_received", "response_sent", "request_failed"], [len(recv), len(resp), len(fail)])
    a.set_ylabel("requests")

    a = ax[0, 2]
    a.set_title(f"Errors: rate={err_rate:.1f}% (SLO<=2%) retr_ok={retr_ok:.0f}% (>=90%)")
    a.bar(["error_rate%", "retrieval_ok%"], [err_rate, retr_ok])
    a.axhline(2, linestyle="--")
    a.set_ylabel("percent")

    a = ax[1, 0]
    a.set_title(f"Cost total=${sum(cost):.4f} (SLO<=2.5/day)")
    a.plot(cost, marker="o")
    a.set_ylabel("USD")
    a.set_xlabel("request idx")

    a = ax[1, 1]
    a.set_title(f"Tokens in={sum(tin)} out={sum(tout)} (SLO<=50000)")
    a.bar(["tokens_in", "tokens_out"], [sum(tin), sum(tout)])
    a.set_ylabel("tokens")

    a = ax[1, 2]
    vals = qual if qual else [0]
    a.set_title(f"Quality mean={sum(vals)/len(vals):.2f} (SLO>=0.75)")
    a.plot(vals, marker="o")
    a.axhline(0.75, linestyle="--")
    a.set_ylabel("0..1")
    a.set_xlabel("request idx")

    fig.tight_layout()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=110)
    print(f"saved {OUT} from {len(recs)} log records")


if __name__ == "__main__":
    main()
