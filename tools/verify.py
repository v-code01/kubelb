"""Independent verification of the kubelb findings, sharing no code with src or
analyze.py. Re-reads results/hits.jsonl, recomputes the baseline fairness and the
per-K keep-alive coverage / Gini / starvation and the occupancy-law fit with its
own arithmetic, and re-asserts:

  P1  new connections are fair: baseline Gini < 0.15 and coverage = N.
  P2  one keep-alive connection pins to one pod: every connection's M requests all
      hit a single pod (measured pinning rate == 1), so K=1 coverage == 1.
  P3  coverage follows the occupancy law N*(1-(1-1/N)^K) within 25% and stays
      below N for K up to 8.
  P4  the skew is connection pinning: keep-alive Gini far exceeds the baseline.

Exit non-zero on mismatch.
"""
from __future__ import annotations

import json
import sys
from collections import Counter

KS = [1, 2, 4, 8]


def gini(counts: list[int]) -> float:
    total = sum(counts)
    n = len(counts)
    if total == 0 or n == 0:
        return 0.0
    s = sorted(counts)
    weighted = sum(i * v for i, v in enumerate(s, start=1))
    return (2.0 * weighted) / (n * total) - (n + 1.0) / n


def occ(n: int, k: int) -> float:
    return n * (1.0 - (1.0 - 1.0 / n) ** k)


def main() -> int:
    rows = [json.loads(x) for x in open("results/hits.jsonl") if x.strip()]
    base = next(r["pods"] for r in rows if r["mode"] == "newconn")
    replicas = sorted(set(base))
    n = len(replicas)
    ok = True

    bc = Counter(base)
    base_gini = gini([bc[p] for p in replicas])
    base_cov = len(set(base))
    p1 = base_gini < 0.15 and base_cov == n
    print(f"  [P1] baseline gini {base_gini:.3f} (<0.15), coverage {base_cov}/{n} = {p1}")
    ok = ok and p1

    # measured intra-connection pinning across every connection
    conns_all = [c for r in rows if r["mode"] == "keepalive" for c in r["conns"]]
    pin_rate = sum(1 for c in conns_all if len(set(c)) == 1) / len(conns_all)

    cov: dict[int, float] = {}
    gin: dict[int, float] = {}
    for k in KS:
        trials = [r for r in rows if r["mode"] == "keepalive" and r["K"] == k]
        covs = [len({c[0] for c in r["conns"]}) for r in trials]
        ginis = []
        for r in trials:
            counts = Counter(c[0] for c in r["conns"])
            ginis.append(gini([counts[p] for p in replicas]))
        cov[k] = sum(covs) / len(covs)
        gin[k] = sum(ginis) / len(ginis)

    p2 = pin_rate == 1.0 and cov[1] == 1.0
    print(f"  [P2] measured pinning rate {pin_rate:.3f} == 1 and K=1 coverage "
          f"{cov[1]:.3f} == 1 = {p2}")
    ok = ok and p2

    dev = {k: abs(cov[k] - occ(n, k)) / occ(n, k) for k in KS}
    fit = all(dev[k] < 0.25 for k in KS)
    below = all(cov[k] < n for k in KS)
    p3 = fit and below
    for k in KS:
        print(f"  [P3] K={k} coverage {cov[k]:.2f} vs occupancy {occ(n,k):.2f} "
              f"(dev {dev[k]*100:.1f}%, < N={n}: {cov[k] < n})")
    print(f"  [P3] occupancy-law fit < 25% at all K and coverage < N throughout = {p3}")
    ok = ok and p3

    p4 = gin[1] > 5 * base_gini and gin[8] > base_gini
    print(f"  [P4] keepalive gini K1 {gin[1]:.3f} / K8 {gin[8]:.3f} vs baseline "
          f"{base_gini:.3f} (pinning skew = {p4})")
    ok = ok and p4

    if ok:
        print("VERIFY OK: new connections balance fairly (gini ~0.1, full coverage) but every "
              "keep-alive connection pins all its requests to one replica (measured pinning rate "
              "1.0); coverage of K connections follows the occupancy law N*(1-(1-1/N)^K) and stays "
              "below N even at K=8 (2x replicas), so persistent-connection clients starve replicas "
              "- recomputed independently.")
        return 0
    print("VERIFY FAILED", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
