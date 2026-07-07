"""Pure helpers for the Service load-balancing study: Gini of per-pod load,
distinct-pod coverage, starved-replica count, and the occupancy-law expectation
for how many of N replicas K independent connections cover. No I/O."""
from __future__ import annotations


def gini(counts: list[int]) -> float:
    """Gini coefficient of a load distribution: 0 = perfectly uniform, (n-1)/n =
    all load on one replica. Returns 0 for an all-zero distribution."""
    total = sum(counts)
    n = len(counts)
    if total == 0 or n == 0:
        return 0.0
    s = sorted(counts)
    cum = 0
    weighted = 0
    for i, v in enumerate(s, start=1):
        cum += v
        weighted += i * v
    # standard Gini via the ordered formula
    return (2.0 * weighted) / (n * total) - (n + 1.0) / n


def coverage(pods: list[str]) -> int:
    """Number of distinct non-empty pod identities."""
    return len({p for p in pods if p})


def starved(counts: list[int]) -> int:
    """Number of replicas that received zero load."""
    return sum(1 for c in counts if c == 0)


def occupancy_expected(n: int, k: int) -> float:
    """Expected number of the N replicas hit by K independent uniform connections:
    n*(1-(1-1/n)^k) (the classic occupancy / coupon-collector expectation)."""
    return n * (1.0 - (1.0 - 1.0 / n) ** k)
