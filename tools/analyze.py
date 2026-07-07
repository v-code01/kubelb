"""Analyze results/hits.jsonl: the new-connection baseline fairness, and per-K
keep-alive coverage, Gini, starvation, and the measured-vs-occupancy-law fit.
Writes bench_results/frontier.md."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import kubelb as kb  # noqa: E402

KS = [1, 2, 4, 8]


def _s(x: object) -> str:
    assert isinstance(x, str)
    return x


def load() -> list[dict[str, object]]:
    path = Path(__file__).resolve().parent.parent / "results" / "hits.jsonl"
    return [json.loads(x) for x in open(path) if x.strip()]


def as_pods(x: object) -> list[str]:
    assert isinstance(x, list)
    return [_s(p) for p in x]


def as_conns(x: object) -> list[object]:
    assert isinstance(x, list)
    return list(x)


def main() -> int:
    rows = load()
    base = as_pods(next(r["pods"] for r in rows if r["mode"] == "newconn"))
    replicas = sorted(set(base))
    n = len(replicas)

    lines: list[str] = [
        "# kubelb frontier (regenerate with tools/analyze.py)",
        "#",
        "# Service load-balancing across N backend replicas. newconn = one fresh",
        "# TCP connection per request; keepalive K = K persistent connections, each",
        "# pinned by conntrack to one backend. coverage = distinct replicas hit;",
        "# starved = replicas with zero load; gini of per-replica load (0 uniform,",
        "# (N-1)/N max). occupancy law = N*(1-(1-1/N)^K).",
        "",
        f"replicas {n}",
    ]

    bc = Counter(base)
    base_counts = [bc[p] for p in replicas]
    lines.append(f"newconn requests {len(base)} coverage {kb.coverage(base)}/{n} "
                 f"gini {kb.gini(base_counts):.4f}")

    # intra-connection pinning: fraction of connections whose M requests all hit
    # one pod (measured, not assumed).
    conns_all = [as_pods(c) for r in rows if r["mode"] == "keepalive"
                 for c in as_conns(r["conns"])]
    pinned = sum(1 for c in conns_all if len(set(c)) == 1)
    lines.append(f"pinning connections {len(conns_all)} all_same_pod {pinned} "
                 f"rate {pinned/len(conns_all):.4f}")

    for k in KS:
        trials = [r for r in rows if r["mode"] == "keepalive" and r["K"] == k]
        covs, ginis, starves = [], [], []
        for r in trials:
            reps = [as_pods(c)[0] for c in as_conns(r["conns"])]  # each conn's pinned pod
            c = Counter(reps)
            counts = [c[p] for p in replicas]
            covs.append(kb.coverage(reps))
            ginis.append(kb.gini(counts))
            starves.append(kb.starved(counts))
        t = len(trials)
        mean_cov = sum(covs) / t
        exp = kb.occupancy_expected(n, k)
        lines.append(
            f"keepalive K {k} trials {t} mean_coverage {mean_cov:.3f} "
            f"occupancy_expected {exp:.3f} coverage_dev {abs(mean_cov-exp)/exp:.3f} "
            f"mean_gini {sum(ginis)/t:.4f} mean_starved {sum(starves)/t:.3f}")

    out = Path(__file__).resolve().parent.parent / "bench_results" / "frontier.md"
    out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
