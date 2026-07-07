"""Drive a real Kubernetes cluster to measure Service load-balancing skew under
HTTP keep-alive. Applies manifests/hostnames.yaml, then via kubectl exec into the
client pod: (1) a new-connection baseline, and (2) a keep-alive sweep where each
of K persistent connections is pinned by conntrack to one backend. Records each
connection's pinned pod to results/hits.jsonl.

kubectl uses the current context/namespace; nothing operating-environment-specific
is in this file.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

KS = [1, 2, 4, 8]
TRIALS = 30
M = 3                       # requests per keep-alive connection (confirms pinning)
BASELINE_N = 200           # new-connection baseline requests
ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "manifests" / "hostnames.yaml"
SVC = "http://hostnames/"


def kubectl(*args: str, timeout: int = 120) -> str:
    return subprocess.run(["kubectl", *args], capture_output=True, text=True,
                          timeout=timeout, check=True).stdout


def exec_curl(shell: str) -> list[str]:
    out = subprocess.run(
        ["kubectl", "exec", "curlcli", "--", "sh", "-c", shell],
        capture_output=True, text=True, timeout=120, check=True).stdout
    return [ln.strip() for ln in out.splitlines() if ln.strip()]


def keepalive_conn() -> str:
    """One persistent connection issuing M requests; returns its pinned pod."""
    urls = " ".join([SVC] * M)
    pods = exec_curl(f"curl -s -w '\\n' {urls}")
    return pods[0] if pods else ""


def main() -> int:
    print("applying manifest...")
    kubectl("apply", "-f", str(MANIFEST))
    kubectl("wait", "--for=condition=ready", "pod", "-l", "app=hostnames",
            "--timeout=180s", timeout=200)
    kubectl("wait", "--for=condition=ready", "pod/curlcli", "--timeout=120s", timeout=140)

    rows: list[dict[str, object]] = []

    # new-connection baseline
    base = exec_curl(
        f"for i in $(seq {BASELINE_N}); do curl -s --no-keepalive -w '\\n' {SVC}; done")
    rows.append({"mode": "newconn", "pods": base})
    print(f"  baseline: {len(base)} requests, {len(set(base))} distinct pods")

    # keep-alive K-sweep
    for k in KS:
        for t in range(TRIALS):
            conn_pods = [keepalive_conn() for _ in range(k)]
            rows.append({"mode": "keepalive", "K": k, "trial": t, "conn_pods": conn_pods})
        print(f"  keepalive K={k}: {TRIALS} trials done")

    out = ROOT / "results" / "hits.jsonl"
    with open(out, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print(f"wrote {len(rows)} rows -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
