# kubelb: a Kubernetes Service starves replicas under keep-alive

A Kubernetes `Service` balances load with kube-proxy DNAT rules: each *new* TCP
connection is sent to a random backend pod. But that choice is fixed for the life
of the connection (conntrack), so **every request on a persistent HTTP keep-alive
connection lands on the same pod**. Inference clients - OpenAI-style SDKs, gRPC,
HTTP/2, connection pools - deliberately reuse long-lived connections, so a handful
of them pin all their traffic onto a handful of replicas and starve the rest,
while the per-request balancer still looks perfectly fair. This measures the skew
on a real cluster and shows it follows an exact occupancy law.

Real single-node Kubernetes (minikube, iptables kube-proxy), 4 hostname-reporting
pods behind a ClusterIP Service, an in-cluster curl client.

## Pre-registration

Four predictions were committed to git (`PREREG.md`) before the run: (P1) new
connections are fair; (P2) one keep-alive connection pins to one pod; (P3)
coverage of K connections follows the occupancy law `N*(1-(1-1/N)^K)` and
starvation persists past K=N; (P4) the skew is connection pinning, not balancer
bias. **All four held.**

## Results

N = 4 replicas. A "connection" is a curl invocation reusing one TCP connection;
conntrack pins all its requests to one backend. Keep-alive cells are 30 trials.

```
  new connection per request (200 requests):
    coverage 4/4 replicas    Gini 0.08    -> fair

  keep-alive, K persistent connections:
    K   mean coverage   occupancy law   Gini    replicas starved (of 4)
    1      1.00            1.00          0.75         3.0
    2      1.70            1.75          0.58         2.3
    4      2.60            2.73          0.43         1.4
    8      3.60            3.60          0.28         0.4
```

1. **New connections are fair. (P1, held.)** With a fresh connection per request,
   the 200 requests spread across all 4 replicas with a Gini of 0.08 - kube-proxy
   does randomize per connection, exactly as designed.

2. **One keep-alive connection pins to one pod. (P2, held.)** A single persistent
   connection sends **100% of its requests to one replica**: coverage 1 of 4, Gini
   0.75 (the maximum for 4 backends), the other 3 replicas idle. The balancer never
   gets a second chance to choose, because there is only one connection.

3. **Coverage follows the occupancy law, and starvation persists past K=N.
   (P3, held - the headline.)** The number of replicas that receive any traffic
   from K independent connections is the classic occupancy expectation
   `N*(1-(1-1/N)^K)`, and the measurement matches it almost exactly: 1.00 vs 1.00,
   1.70 vs 1.75, 2.60 vs 2.73, 3.60 vs 3.60 (within 5%). Because connections collide
   on replicas (a birthday problem), **coverage stays below N even at K=8 - twice
   as many connections as replicas still leaves ~0.4 replicas idle on average and a
   Gini of 0.28**, far from balanced. You cannot fix L4 starvation by adding
   clients; the collisions scale with you.

4. **The skew is connection pinning, not balancer bias. (P4, held.)** At matched
   request volume the only difference between the fair 0.08 Gini and the skewed
   0.28-0.75 Gini is whether the connection was reused. kube-proxy is not
   imbalanced; persistent connections simply defeat per-connection randomization.

## The one-line finding

On a real Kubernetes Service, new connections balance fairly (Gini 0.08) but each
keep-alive connection pins 100% of its requests to one replica, and the number of
replicas covered by K persistent connections follows the occupancy law
`N*(1-(1-1/N)^K)` - so it stays below N even at twice the replica count (3.6 of 4
covered at K=8), which is exactly why L4 Service balancing starves inference
replicas whose clients hold long-lived connections, and why per-request (L7)
balancing is needed.

## Reproduce

```
./reproduce.sh     # analyze + independently verify from committed hits (no cluster)
```

`results/hits.jsonl` records each connection's pinned replica. `tools/verify.py`
re-reads it, recomputes the Gini, coverage, starvation, and occupancy-law fit with
its own arithmetic (no shared code with `src` or `analyze.py`), and re-asserts
every threshold. To regenerate on a real cluster: `python tools/run_bench.py` with
kubectl pointed at a running Kubernetes cluster (see `manifests/hostnames.yaml`).

## Limitations and falsifiers

- One cluster (minikube, single node), iptables kube-proxy mode, ClusterIP
  Service, HTTP/1.1 keep-alive, N=4 replicas, 30 trials/cell. This isolates the
  connection-pinning effect; IPVS mode or an L7 proxy would rebalance differently
  (that is the point - use them).
- The unit of load is the connection; M=3 requests per connection only confirm the
  pinning (all M hit one pod, observed).
- **Falsifier (did not fire):** had keep-alive requests been re-balanced
  per-request, coverage would reach N quickly and the Gini would match the 0.08
  baseline; instead one connection pins to one pod and coverage follows the
  occupancy law.

MIT licensed. Backends are attributed by the pod name they return; all counts are
exact. No LLM judgement.
