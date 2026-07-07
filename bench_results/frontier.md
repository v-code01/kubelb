# kubelb frontier (regenerate with tools/analyze.py)
#
# Service load-balancing across N backend replicas. newconn = one fresh
# TCP connection per request; keepalive K = K persistent connections, each
# pinned by conntrack to one backend. coverage = distinct replicas hit;
# starved = replicas with zero load; gini of per-replica load (0 uniform,
# (N-1)/N max). occupancy law = N*(1-(1-1/N)^K).

replicas 4
newconn requests 200 coverage 4/4 gini 0.0800
keepalive K 1 trials 30 mean_coverage 1.000 occupancy_expected 1.000 coverage_dev 0.000 mean_gini 0.7500 mean_starved 3.000
keepalive K 2 trials 30 mean_coverage 1.700 occupancy_expected 1.750 coverage_dev 0.029 mean_gini 0.5750 mean_starved 2.300
keepalive K 4 trials 30 mean_coverage 2.600 occupancy_expected 2.734 coverage_dev 0.049 mean_gini 0.4333 mean_starved 1.400
keepalive K 8 trials 30 mean_coverage 3.600 occupancy_expected 3.600 coverage_dev 0.000 mean_gini 0.2833 mean_starved 0.400
