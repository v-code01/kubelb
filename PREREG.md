# Pre-registration: kubelb

Committed to git BEFORE the benchmark is run. Not edited afterward.

## What is measured

On a real single-node Kubernetes cluster (minikube, iptables kube-proxy), N = 4
hostname-reporting pods behind a ClusterIP Service, hit by an in-cluster curl
client. A "connection" is a curl invocation reusing one TCP connection for M
requests; conntrack pins it to one backend pod, recorded as its assigned pod.
Conditions: new-conn baseline (each request a fresh connection), and keep-alive
with K persistent connections for K in {1, 2, 4, 8}. Each keep-alive cell is
repeated over >= 30 trials. Metrics: per-pod load Gini, number of distinct pods
covered, number of starved (zero-load) replicas, and measured coverage vs the
occupancy law N*(1-(1-1/N)^K).

## Predictions

**P1 - new connections are fair.** The new-conn baseline has Gini < 0.15 and hits
all N pods. *Falsifier:* new-conn Gini >= 0.15 or coverage < N.

**P2 - one keep-alive connection pins to one pod.** K=1 coverage is exactly 1 and
the load Gini is maximal. *Falsifier:* K=1 coverage > 1.

**P3 - coverage follows the occupancy law and starvation persists past K=N.** Mean
coverage over K keep-alive connections matches N*(1-(1-1/N)^K) within tolerance and
stays below N for K up to 8 (twice the replica count). *Falsifier:* mean coverage
reaches N at K <= N, or deviates from the occupancy law by more than 25%.

**P4 - the skew is connection pinning, not balancer bias.** At matched total
request volume, new-conn is near-uniform while keep-alive is severely skewed; the
only difference is connection reuse. *Falsifier:* keep-alive Gini is not materially
higher than new-conn Gini.

## Commitment

P2 (a persistent connection pins all its traffic to one replica) and P3 (coverage
follows the occupancy law, so starvation persists even with more connections than
replicas) are the headline. Results are reported as-is, including any falsified
prediction.
