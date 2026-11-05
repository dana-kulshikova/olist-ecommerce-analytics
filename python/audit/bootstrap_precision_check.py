"""Step 8: higher-replicate check of the intervals where the first independent bootstrap differed most.

Reads only the order table written by independent_recompute.py, and shares no code with python/analysis/.
Resamples sellers and their actual rows, with its own solver, and first confirms the A3 point estimates.

Usage: python python/audit/bootstrap_precision_check.py <independent-orders-csv> <output-json> [replicates]
"""
import collections
import csv
import json
import math
import random
import sys

import numpy as np

SOURCE, TARGET = sys.argv[1:3]
REPS = int(sys.argv[3]) if len(sys.argv) > 3 else 2000
with open(SOURCE, encoding="utf-8", newline="") as handle:
    rows = list(csv.DictReader(handle))
for r in rows:
    r["late"] = int(r["late"])
PEAK = {"2017-11", "2018-02", "2018-03"}
late_reviews = [r for r in rows if r["late"] and r["score"]]
y = np.array([float(float(r["score"]) <= 2) for r in late_reviews])

# Month groups: at least 30 orders, 10 events and 10 non-events; leftovers join the previous group.
tally = collections.defaultdict(lambda: [0, 0.0])
for r, v in zip(late_reviews, y):
    tally[r["month"]][0] += 1
    tally[r["month"]][1] += v
groups, current, n, k = [], [], 0, 0.0
for month in sorted(tally):
    current.append(month)
    n += tally[month][0]
    k += tally[month][1]
    if n >= 30 and k >= 10 and n - k >= 10:
        groups.append(current)
        current, n, k = [], 0, 0.0
if current:
    groups[-1] += current
month_group = {m: g[0] for g in groups for m in g}


def dummies(values):
    counts = collections.Counter(values)
    common = counts.most_common(1)[0][0]
    return [np.array([float(v == level) for v in values]) for level in sorted(counts) if level != common]


band_names = ["1-3", "4-7", "8-14", "15+"]
band_cols = [np.array([float(r["delay"] == b) for r in late_reviews]) for b in band_names[1:]]
item = ["1" if int(r["n"]) == 1 else ("2" if int(r["n"]) == 2 else "3+") for r in late_reviews]
other = [np.ones(len(y))] + dummies([month_group[r["month"]] for r in late_reviews]) + dummies([r["state_group"] for r in late_reviews]) + dummies(item) + dummies([r["category_group"] for r in late_reviews])
other += [np.array([math.log(float(r["sales"])) for r in late_reviews]), np.array([float(r["multi_seller"]) for r in late_reviews])]
X = np.column_stack(band_cols + other)
codes = {s: i for i, s in enumerate(sorted({r["seller"] for r in late_reviews}))}
members = [[] for _ in codes]
for i, r in enumerate(late_reviews):
    members[codes[r["seller"]]].append(i)
members = [np.array(m) for m in members]


def fit(index, start):
    beta = start.copy()
    Xs, ys = X[index], y[index]
    for _ in range(60):
        mu = 1 / (1 + np.exp(-np.clip(Xs @ beta, -35, 35)))
        w = np.clip(mu * (1 - mu), 1e-12, None)
        step = np.linalg.lstsq((Xs * w[:, None]).T @ Xs, Xs.T @ (ys - mu), rcond=None)[0]
        beta = beta + step
        if np.max(np.abs(step)) < 1e-6:
            return beta, True
    return beta, False


def band_rates(beta, index):
    base = X[index][:, 3:] @ beta[3:]
    out = [100 * np.mean(1 / (1 + np.exp(-base)))]
    for j in range(3):
        out.append(100 * np.mean(1 / (1 + np.exp(-(base + beta[j])))))
    return out


everyone = np.arange(len(y))
beta0, ok = fit(everyone, np.zeros(X.shape[1]))
point = band_rates(beta0, everyone)
rng = np.random.default_rng(424242)
draws, failed = [], 0
for _ in range(REPS):
    picks = rng.integers(0, len(members), len(members))
    index = np.concatenate([members[g] for g in picks])
    beta, ok = fit(index, beta0)
    if not ok or np.max(np.abs(beta)) > 25:
        failed += 1
        continue
    r = band_rates(beta, index)
    draws.append([r[1] - r[0], r[2] - r[1], r[3] - r[2], r[3] - r[0]])
draws = np.array(draws)
result = {"replicates": REPS, "failed": failed, "a3_terms": X.shape[1], "a3_rates": [round(v, 2) for v in point], "a3": {}}
for j, name in enumerate(("4-7 vs 1-3", "8-14 vs 4-7", "15+ vs 8-14", "15+ vs 1-3")):
    result["a3"][name] = {"low": round(float(np.percentile(draws[:, j], 2.5)), 2), "high": round(float(np.percentile(draws[:, j], 97.5)), 2), "share_at_or_above_zero_pct": round(100 * float(np.mean(draws[:, j] >= 0)), 2)}


def concentration(sample, seed):
    per = collections.defaultdict(lambda: [0, 0])
    for r in sample:
        if r["single"] == "True":
            per[r["seller"]][0] += 1
            per[r["seller"]][1] += r["late"]
    table = [per[s] for s in sorted(per) if per[s][0] >= 100]
    top = math.ceil(0.10 * len(table))

    def gap(items):
        ranked = sorted(range(len(items)), key=lambda j: (-items[j][1], j))[:top]
        return 100 * (sum(items[j][1] for j in ranked) / sum(i[1] for i in items) - sum(items[j][0] for j in ranked) / sum(i[0] for i in items))

    picker = random.Random(seed)
    values = sorted(gap([table[picker.randrange(len(table))] for _ in table]) for _ in range(REPS))
    return {"estimate": round(gap(table), 3), "low": round(values[int(0.025 * REPS)], 2), "high": round(values[int(0.975 * REPS)], 2), "share_at_or_above_10_pct": round(100 * sum(v >= 10 for v in values) / REPS, 1), "share_at_or_below_zero_pct": round(100 * sum(v <= 0 for v in values) / REPS, 1)}


result["a6"] = concentration(rows, 11)
result["a6_excluding_peak"] = concentration([r for r in rows if r["month"] not in PEAK], 12)
with open(TARGET, "w", encoding="utf-8") as handle:
    json.dump(result, handle, indent=1)
print(json.dumps(result, indent=1))
