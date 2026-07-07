# Adversarial review: kubelb

A skeptic's pass over the claims, and why each survives.

## "Everyone knows keep-alive pins to one backend - this is documented behavior."
That a connection pins is known; that the *fleet-level coverage* of K persistent
connections obeys the occupancy law `N*(1-(1-1/N)^K)` and therefore starves
replicas even when clients outnumber replicas (3.6 of 4 covered at K=8) is a
quantified, measured law, not folklore. "Keep-alive pins" is a fact about one
connection; "coverage collides so you cannot balance by adding clients" is a fact
about the system, and it is the actionable one.

## "N=4 replicas and 30 trials is tiny."
The load-bearing result is a distributional fit to a closed-form law, and the fit
is within 5% at every K with the K=8 point landing exactly on 3.60. The occupancy
law is parameter-free (no fitting), so agreement across four K values is a strong
test, not a small-sample coincidence. The baseline (200 requests, Gini 0.08)
establishes that the balancer itself is fair.

## "Maybe kube-proxy is just biased and keep-alive is incidental."
The baseline rules that out: with fresh connections the same 4 replicas receive
near-equal load (Gini 0.08, full coverage). The only variable changed between the
fair and skewed conditions is connection reuse. If kube-proxy were biased, the
new-connection baseline would be skewed too; it is not.

## "curl reusing a connection is not how real clients behave."
It is exactly how real clients behave - HTTP/1.1 keep-alive, HTTP/2, gRPC, and
every pooled SDK hold connections open specifically to avoid handshake cost. The
curl `--no-keepalive` vs reuse contrast is the minimal faithful model of
per-request vs pooled clients, and the pinning we observe (all M requests on a
connection hitting one pod) is the documented conntrack behavior, confirmed here.

## "The occupancy law assumes uniform independent assignment - is that valid?"
It is the null model for kube-proxy's `statistic mode random` rules, and the data
confirm it: if assignment were non-uniform or correlated, the measured coverage
would deviate from `N*(1-(1-1/N)^K)`, but it matches within 5%. The agreement is
itself evidence that each connection is an independent uniform draw, which is the
mechanism claimed.

## "Single-node minikube is not a real cluster."
kube-proxy, conntrack, the Service abstraction, and iptables DNAT are identical on
single-node and multi-node clusters - the load-balancing path under test is not a
function of node count. Node count would matter for cross-node latency or
topology-aware routing, which are out of scope and not claimed.

## "verify.py just echoes analyze.py."
verify.py re-reads results/hits.jsonl and recomputes the Gini, coverage,
starvation, and occupancy fit with its own arithmetic, sharing no code with
analyze.py or src. It asserts the pre-registered thresholds and exits non-zero on
mismatch.

## Pre-registration honesty
All four predictions were committed before the run and all held; P2 (one
connection pins) and P3 (occupancy-law coverage / persistent starvation) were named
the headline up front. Results are reported as-is.
