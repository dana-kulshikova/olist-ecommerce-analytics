"""Step 8: independent recomputation of the key results from the raw CSV files only.

This file deliberately shares no code with python/analysis/. It doesn't read data/processed/ exports
or stored results, and it doesn't use pandas or statsmodels. It uses the csv module, numpy, scipy for
one chi-square tail probability, and its own logistic solver, cluster-robust covariance and
row-resampling bootstrap. Model specifications are
taken from docs/analysis_plan.md and re-implemented here. Comparison with stored results is a
separate step, in compare_with_stored.py.

Writes data/processed/independent_audit_results.json, which Git ignores.

Usage: python python/audit/independent_recompute.py <raw-csv-folder> [bootstrap-replicates]
"""
import collections
import csv
import json
import math
import pathlib
import random
import statistics
import sys
import time
from datetime import datetime, timedelta
from decimal import Decimal

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
RAW = pathlib.Path(sys.argv[1])
REPS = int(sys.argv[2]) if len(sys.argv) > 2 else 200
SEED = 8675309  # deliberately different from the project's seed
FMT = "%Y-%m-%d %H:%M:%S"
Z = 1.959964
started = time.time()
out = {"seed": SEED, "bootstrap_replicates": REPS, "method": "stdlib csv, numpy, own Newton solver, own CR1 cluster covariance, row-resampling bootstrap"}


def note(text):
    print(f"[{(time.time() - started) / 60:5.1f}m] {text}", flush=True)


def read(name):
    with open(RAW / name, encoding="utf-8-sig", newline="") as handle:
        yield from csv.DictReader(handle)


def when(value):
    return datetime.strptime(value, FMT) if value else None


# ------------------------------------------------------------------ 1. KPIs from raw files, with exact decimals
note("reading raw files")
orders_raw = list(read("olist_orders_dataset.csv"))
items_raw = list(read("olist_order_items_dataset.csv"))
customers = {r["customer_id"]: (r["customer_state"], r["customer_zip_code_prefix"]) for r in read("olist_customers_dataset.csv")}
sellers = {r["seller_id"]: (r["seller_state"], r["seller_zip_code_prefix"]) for r in read("olist_sellers_dataset.csv")}
products = {r["product_id"]: r["product_category_name"] for r in read("olist_products_dataset.csv")}
english = {r["product_category_name"]: r["product_category_name_english"] for r in read("product_category_name_translation.csv")}
reviews_raw = list(read("olist_order_reviews_dataset.csv"))
payments_raw = list(read("olist_order_payments_dataset.csv"))

price_total = collections.defaultdict(Decimal)
for row in items_raw:
    price_total[row["order_id"]] += Decimal(row["price"])
delivered_rows = [r for r in orders_raw if r["order_status"] == "delivered"]
dated_rows = [r for r in delivered_rows if r["order_delivered_customer_date"]]
on_time = sum(when(r["order_delivered_customer_date"]).date() <= when(r["order_estimated_delivery_date"]).date() for r in dated_rows)
sales = sum((price_total[r["order_id"]] for r in delivered_rows), Decimal(0))
day_counts = []
for r in delivered_rows:
    p, c, d = when(r["order_purchase_timestamp"]), when(r["order_delivered_carrier_date"]), when(r["order_delivered_customer_date"])
    if c and d and p <= c <= d:
        day_counts.append((d.date() - p.date()).days)
out["kpis"] = {"delivered_orders": len(delivered_rows), "delivered_with_date": len(dated_rows), "on_time_orders": on_time, "late_orders": len(dated_rows) - on_time,
               "on_time_rate_pct": round(100 * on_time / len(dated_rows), 2), "total_product_sales": float(sales),
               "average_order_value": round(float(sales) / len(delivered_rows), 2), "average_delivery_days": round(sum(day_counts) / len(day_counts), 4)}

# ------------------------------------------------------------------ 2. Grain and joins
order_ids = [r["order_id"] for r in orders_raw]
item_orders = {r["order_id"] for r in items_raw}
pay_orders = {r["order_id"] for r in payments_raw}
pay_counts = collections.Counter(r["order_id"] for r in payments_raw)
item_counts = collections.Counter(r["order_id"] for r in items_raw)
naive_join_rows = sum(item_counts[o] * pay_counts[o] for o in item_counts)
naive_price = sum(Decimal(r["price"]) * pay_counts[r["order_id"]] for r in items_raw if r["order_id"] in pay_counts)
item_total = sum(Decimal(r["price"]) for r in items_raw)
out["grain"] = {"orders": len(order_ids), "unique_order_ids": len(set(order_ids)), "orders_without_items": len(set(order_ids) - item_orders), "orders_without_payments": len(set(order_ids) - pay_orders),
                "orders_without_customer": sum(r["customer_id"] not in customers for r in orders_raw), "items_without_order": len(item_orders - set(order_ids)),
                "item_rows": len(items_raw), "payment_rows": len(payments_raw), "item_payment_naive_join_rows": naive_join_rows, "price_total_correct": float(item_total), "price_total_if_joined_naively": float(naive_price),
                "unique_customer_ids": len({r["customer_id"] for r in orders_raw})}
unique_ids = {r["customer_id"]: r["customer_unique_id"] for r in read("olist_customers_dataset.csv")}
per_person = collections.Counter(unique_ids[r["customer_id"]] for r in delivered_rows)
out["grain"]["delivered_orders_from_repeat_customers"] = sum(v for v in per_person.values() if v > 1)
out["grain"]["unique_customers_delivered"] = len(per_person)

# ------------------------------------------------------------------ 3. Date sequences
categories = collections.Counter()
for r in delivered_rows:
    p, c, d = when(r["order_purchase_timestamp"]), when(r["order_delivered_carrier_date"]), when(r["order_delivered_customer_date"])
    if d is None:
        categories["no delivery date"] += 1
    elif c is None:
        categories["carrier missing, delivery present"] += 1
    elif c < p:
        categories["carrier before purchase"] += 1
    elif d < c:
        categories["delivery before carrier"] += 1
    else:
        categories["valid"] += 1
out["date_sequences"] = dict(categories)

# ------------------------------------------------------------------ 4. Order table
note("building order table")
geo = collections.defaultdict(lambda: ([], []))
for r in read("olist_geolocation_dataset.csv"):
    la, lo = float(r["geolocation_lat"]), float(r["geolocation_lng"])
    if -34 <= la <= 6 and -74 <= lo <= -34:
        geo[r["geolocation_zip_code_prefix"]][0].append(la)
        geo[r["geolocation_zip_code_prefix"]][1].append(lo)
median_position = {z: (statistics.median(a), statistics.median(b)) for z, (a, b) in geo.items()}
del geo
items_by_order = collections.defaultdict(list)
for r in items_raw:
    items_by_order[r["order_id"]].append((int(r["order_item_id"]), float(r["price"]), float(r["freight_value"]), r["seller_id"], r["product_id"], when(r["shipping_limit_date"])))
reviews_by_order = collections.defaultdict(list)
for r in reviews_raw:
    reviews_by_order[r["order_id"]].append((when(r["review_answer_timestamp"]), when(r["review_creation_date"]), r["review_id"], int(r["review_score"])))


def km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371.0088 * 2 * math.asin(math.sqrt(h))


def category_name(product):
    raw_name = products.get(product, "")
    if not raw_name:
        return "unknown"
    return english.get(raw_name, raw_name)


def distance_band(d):
    if d is None:
        return None
    for limit, label in ((100, "0-100"), (300, "100-300"), (600, "300-600"), (1000, "600-1000"), (2000, "1000-2000")):
        if d < limit:
            return label
    return "2000+"


rows = []
for r in dated_rows:
    its = items_by_order[r["order_id"]]
    assert its, "delivered order with no items"
    primary = sorted(its, key=lambda x: (-x[1], x[0]))[0]
    first = sorted(its, key=lambda x: x[0])[0]
    seller_set = {x[3] for x in its}
    state, customer_zip = customers[r["customer_id"]]
    seller_state, seller_zip = sellers[primary[3]]
    p, a, c, d, e = map(when, (r["order_purchase_timestamp"], r["order_approved_at"], r["order_delivered_carrier_date"], r["order_delivered_customer_date"], r["order_estimated_delivery_date"]))
    distance = None
    if len(seller_set) == 1 and customer_zip in median_position and seller_zip in median_position:
        distance = km(median_position[customer_zip], median_position[seller_zip])
    rv = reviews_by_order.get(r["order_id"], [])
    latest = max(rv, key=lambda x: (x[0], x[1], x[2])) if rv else None
    earliest = min(rv, key=lambda x: (x[0], x[1], x[2])) if rv else None
    n_items = len(its)
    days_late = (d.date() - e.date()).days
    rows.append(dict(id=r["order_id"], state=state, seller=primary[3], seller_state=seller_state, month=p.strftime("%Y-%m"), p=p, c=c, d=d, e=e, late=int(d.date() > e.date()), days_late=days_late,
                     sales=sum(x[1] for x in its), freight=sum(x[2] for x in its), n=n_items, item_band="1" if n_items == 1 else ("2" if n_items == 2 else "3+"), multi_seller=float(len(seller_set) > 1), single=len(seller_set) == 1,
                     same_state=float(state == seller_state), distance=distance, band=distance_band(distance), category=category_name(primary[4]), limit=max(x[5] for x in its), valid=bool(c and p <= c <= d),
                     score=latest[3] if latest else None, answered=latest[0] if latest else None, created=latest[1] if latest else None, score_first=earliest[3] if earliest else None, answered_first=earliest[0] if earliest else None,
                     delay=None if days_late <= 0 else ("1-3" if days_late <= 3 else ("4-7" if days_late <= 7 else ("8-14" if days_late <= 14 else "15+")))))
PEAK = {"2017-11", "2018-02", "2018-03"}
state_size = collections.Counter(x["state"] for x in rows)
named = collections.Counter(x["category"] for x in rows if x["category"] != "unknown")
top15 = {k for k, _ in named.most_common(15)}
for x in rows:
    x["state_group"] = x["state"] if state_size[x["state"]] >= 1000 else "other"
    x["category_group"] = x["category"] if x["category"] in top15 or x["category"] == "unknown" else "other"
    x["log_value"] = math.log(x["sales"])
    x["peak"] = x["month"] in PEAK
    x["multi_item"] = "multi" if x["n"] >= 2 else "single"
    x["low"] = None if x["score"] is None else float(x["score"] <= 2)
    x["timing"] = None if x["score"] is None else ("before" if x["answered"] < x["d"] else "after")
    x["timing_created"] = None if x["score"] is None else ("before" if x["created"].date() < x["d"].date() else "after")
    x["handover"] = "late" if x["c"] and x["c"] > x["limit"] else "ontime"
    x["group3"] = None if x["score"] is None else ("ontime" if not x["late"] else ("late_before" if x["timing"] == "before" else "late_after"))
out["table"] = {"orders": len(rows), "late": sum(x["late"] for x in rows), "single_with_distance": sum(x["distance"] is not None for x in rows), "reviewed": sum(x["score"] is not None for x in rows), "unknown_category": sum(x["category"] == "unknown" for x in rows)}

# Optional third argument: write the order table for row-by-row comparison, then stop before any model runs.
if len(sys.argv) > 3:
    fields = ["id", "state", "seller", "seller_state", "month", "late", "days_late", "delay", "sales", "freight", "n", "multi_seller", "single", "same_state", "distance", "band", "category", "category_group", "state_group", "valid", "score", "score_first", "answered", "created", "timing", "timing_created", "handover", "p", "c", "d", "e"]
    with open(sys.argv[3], "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    note(f"order table written, {len(rows)} rows")
    sys.exit(0)


# ------------------------------------------------------------------ 5. Own logistic machinery
def merge_periods(sample, outcome):
    """Documented rule: a month group needs 30 orders, 10 events and 10 non-events; leftovers join the previous group."""
    tally = collections.defaultdict(lambda: [0, 0])
    for x in sample:
        tally[x["month"]][0] += 1
        tally[x["month"]][1] += x[outcome]
    groups, current, n, k = [], [], 0, 0
    for month in sorted(tally):
        current.append(month)
        n += tally[month][0]
        k += tally[month][1]
        if n >= 30 and k >= 10 and n - k >= 10:
            groups.append(current)
            current, n, k = [], 0, 0
    if current:
        if groups:
            groups[-1] = groups[-1] + current
        else:
            groups.append(current)
    return {m: g[0] for g in groups for m in g}


def collapse(values, ys):
    tally = collections.defaultdict(lambda: [0, 0.0])
    for v, y in zip(values, ys):
        tally[v][0] += 1
        tally[v][1] += y
    sparse = {v for v, (n, k) in tally.items() if n < 30 or k < 10 or n - k < 10}
    return ["other" if v in sparse else v for v in values], sorted(map(str, sparse))


class Fit:
    def __init__(self, sample, outcome, exposure, reference, categorical, numeric, extra=None, outcome_key=None):
        self.sample = sample
        y = np.array([float(x[outcome]) for x in sample])
        names, columns = ["const"], [np.ones(len(sample))]
        self.merged = {}
        self.exposure_columns = {}
        if exposure is not None:
            levels = sorted({x[exposure] for x in sample})
            for level in levels:
                if level != reference:
                    names.append(f"{exposure}={level}")
                    columns.append(np.array([float(x[exposure] == level) for x in sample]))
                    self.exposure_columns[level] = len(names) - 1
            self.levels = levels
        for column in categorical:
            if column == "month":
                mapping = merge_periods(sample, outcome)
                values = [mapping[x["month"]] for x in sample]
            else:
                values, sparse = collapse([x[column] for x in sample], y)
                if sparse:
                    self.merged[column] = sparse
            counts = collections.Counter(values)
            base_level = counts.most_common(1)[0][0]
            for level in sorted(counts, key=str):
                if level != base_level:
                    names.append(f"{column}={level}")
                    columns.append(np.array([float(v == level) for v in values]))
        for column in numeric:
            names.append(column)
            columns.append(np.array([float(x[column]) for x in sample]))
        if extra:
            for name, function in extra.items():
                names.append(name)
                columns.append(np.array([float(function(x)) for x in sample]))
        self.names, self.X, self.y = names, np.column_stack(columns), y
        self.index = {n: i for i, n in enumerate(names)}
        seller_ids = {s: i for i, s in enumerate(sorted({x["seller"] for x in sample}))}
        self.cluster = np.array([seller_ids[x["seller"]] for x in sample])
        self.G = len(seller_ids)
        self.beta, self.iterations, self.converged = self.newton(self.X, self.y, np.zeros(self.X.shape[1]))
        self.cov = self.sandwich()

    @staticmethod
    def newton(X, y, start, tolerance=1e-8, limit=60):
        beta = start.copy()
        for iteration in range(1, limit + 1):
            eta = np.clip(X @ beta, -35, 35)
            mu = 1 / (1 + np.exp(-eta))
            w = np.clip(mu * (1 - mu), 1e-12, None)
            step = np.linalg.lstsq((X * w[:, None]).T @ X, X.T @ (y - mu), rcond=None)[0]
            beta = beta + step
            if np.max(np.abs(step)) < tolerance:
                return beta, iteration, True
        return beta, limit, False

    def sandwich(self):
        eta = self.X @ self.beta
        mu = 1 / (1 + np.exp(-eta))
        w = mu * (1 - mu)
        bread = np.linalg.pinv((self.X * w[:, None]).T @ self.X)
        scores = self.X * (self.y - mu)[:, None]
        by_cluster = np.zeros((self.G, self.X.shape[1]))
        np.add.at(by_cluster, self.cluster, scores)
        meat = by_cluster.T @ by_cluster
        n, k = self.X.shape
        factor = (self.G / (self.G - 1)) * ((n - 1) / (n - k))
        return factor * bread @ meat @ bread

    def world(self, level):
        X = self.X.copy()
        for name, column in self.exposure_columns.items():
            X[:, column] = 1.0 if name == level else 0.0
        return X

    def rate(self, X, beta=None, rows_index=None):
        beta = self.beta if beta is None else beta
        X = X if rows_index is None else X[rows_index]
        return 100 * float(np.mean(1 / (1 + np.exp(-(X @ beta)))))

    def contrast(self, Xa, Xb, mask=None):
        Xa, Xb = (Xa, Xb) if mask is None else (Xa[mask], Xb[mask])
        pa, pb = 1 / (1 + np.exp(-(Xa @ self.beta))), 1 / (1 + np.exp(-(Xb @ self.beta)))
        grad = ((pa * (1 - pa))[:, None] * Xa - (pb * (1 - pb))[:, None] * Xb).mean(axis=0)
        est, se = pa.mean() - pb.mean(), math.sqrt(grad @ self.cov @ grad)
        return {"estimate": round(100 * float(est), 3), "ci": [round(100 * float(est - Z * se), 3), round(100 * float(est + Z * se), 3)]}

    def wald_coefficient(self, name):
        i = self.index[name]
        z = self.beta[i] / math.sqrt(self.cov[i, i])
        return {"z": round(float(z), 3), "p": 2 * 0.5 * math.erfc(abs(z) / math.sqrt(2)), "odds_ratio": round(math.exp(self.beta[i]), 3)}

    def wald_contrast(self, a, b=None):
        L = np.zeros(len(self.names))
        L[self.index[a]] = 1
        if b:
            L[self.index[b]] = -1
        est, se = float(L @ self.beta), math.sqrt(float(L @ self.cov @ L))
        z = est / se
        return {"z": round(z, 3), "p": math.erfc(abs(z) / math.sqrt(2)), "odds_ratio": round(math.exp(est), 3)}

    def diagnostics(self):
        return {"orders": len(self.y), "events": int(self.y.sum()), "terms": len(self.names), "sellers": self.G, "converged": self.converged, "iterations": self.iterations, "largest_coefficient": round(float(np.max(np.abs(self.beta[1:]))), 2), "merged": self.merged}

    def bootstrap(self, statistic, reps, seed):
        rng = np.random.default_rng(seed)
        members = [np.flatnonzero(self.cluster == g) for g in range(self.G)]
        results, failed = [], 0
        for _ in range(reps):
            picks = rng.integers(0, self.G, self.G)
            index = np.concatenate([members[g] for g in picks])
            beta, _, ok = self.newton(self.X[index], self.y[index], self.beta, tolerance=1e-6)
            if not ok or np.max(np.abs(beta)) > 25:
                failed += 1
                continue
            results.append(statistic(beta, index))
        values = np.array(results)
        return np.percentile(values, 2.5, axis=0).round(3).tolist(), np.percentile(values, 97.5, axis=0).round(3).tolist(), failed


def share(sample, key):
    n = len(sample)
    k = sum(x[key] for x in sample)
    return {"orders": n, "events": int(k), "rate": round(100 * k / n, 2) if n else None}


seed_stream = iter(range(SEED, SEED + 1000))
with_distance = [x for x in rows if x["distance"] is not None]
reviewed = [x for x in rows if x["score"] is not None]
R = {}
A2_CATS, A2_NUMS = ["month", "state_group", "item_band", "category_group"], ["log_value", "multi_seller"]


def boot_rd(fit, Xa, Xb, label):
    lo, hi, failed = fit.bootstrap(lambda b, i: fit.rate(Xa, b, i) - fit.rate(Xb, b, i), REPS, next(seed_stream))
    return {"low": lo, "high": hi, "failed": failed, "label": label}


# ------------------------------------------------------------------ 6. Class A
note("A1")
a1 = [x for x in with_distance if x["state"] in ("RJ", "SP")]
m = Fit(a1, "late", "state", "SP", ["band", "month", "item_band"], ["log_value", "same_state"])
Xa, Xb = m.world("RJ"), m.world("SP")
R["A1"] = {**m.contrast(Xa, Xb), "bootstrap": boot_rd(m, Xa, Xb, "A1"), "test": m.wald_coefficient("state=RJ"), "unadjusted": {s: share([x for x in a1 if x["state"] == s], "late") for s in ("RJ", "SP")}, "adjusted": {"RJ": round(m.rate(Xa), 2), "SP": round(m.rate(Xb), 2)}, "diagnostics": m.diagnostics()}

note("A2")
for x in reviewed:
    x["status"] = "late" if x["late"] else "ontime"
m = Fit(reviewed, "low", "status", "ontime", A2_CATS, A2_NUMS)
Xa, Xb = m.world("late"), m.world("ontime")
R["A2"] = {**m.contrast(Xa, Xb), "bootstrap": boot_rd(m, Xa, Xb, "A2"), "test": m.wald_coefficient("status=late"), "unadjusted": {s: share([x for x in reviewed if x["status"] == s], "low") for s in ("late", "ontime")}, "adjusted": {"late": round(m.rate(Xa), 2), "ontime": round(m.rate(Xb), 2)}, "diagnostics": m.diagnostics()}

note("A3")
late_reviews = [x for x in reviewed if x["late"]]
m = Fit(late_reviews, "low", "delay", "1-3", A2_CATS, A2_NUMS)
worlds = {b: m.world(b) for b in ("1-3", "4-7", "8-14", "15+")}
pairs = [("4-7", "1-3"), ("8-14", "4-7"), ("15+", "8-14"), ("15+", "1-3")]
lo, hi, failed = m.bootstrap(lambda b, i: [m.rate(worlds[a], b, i) - m.rate(worlds[c], b, i) for a, c in pairs], REPS, next(seed_stream))
score = {"1-3": 0.0, "4-7": 1.0, "8-14": 2.0, "15+": 3.0}
for x in late_reviews:
    x["band_score"] = score[x["delay"]]
trend = Fit(late_reviews, "low", None, None, A2_CATS, A2_NUMS + ["band_score"])
R["A3"] = {"rates": {b: round(m.rate(w), 2) for b, w in worlds.items()}, "pairs": {f"{a} vs {c}": {**m.contrast(worlds[a], worlds[c]), "boot_low": lo[j], "boot_high": hi[j]} for j, (a, c) in enumerate(pairs)}, "bootstrap_failed": failed, "trend": trend.wald_coefficient("band_score"), "unadjusted": {b: share([x for x in late_reviews if x["delay"] == b], "low") for b in score}, "diagnostics": m.diagnostics()}

note("A4")
m = Fit(with_distance, "late", "band", "0-100", ["month", "state_group", "item_band"], ["log_value"])
R["A4"] = {**m.contrast(m.world("600-1000"), m.world("0-100")), "test": m.wald_coefficient("band=600-1000"), "far_band": m.contrast(m.world("2000+"), m.world("0-100")), "unadjusted": {b: share([x for x in with_distance if x["band"] == b], "late") for b in ("0-100", "100-300", "300-600", "600-1000", "1000-2000", "2000+")}, "diagnostics": m.diagnostics()}
m2 = Fit(with_distance, "late", "band", "0-100", ["month", "item_band"], ["log_value"])
R["A4"]["without_state"] = m2.contrast(m2.world("600-1000"), m2.world("0-100"))

note("A5")
values = sorted(x["freight"] for x in with_distance)
cuts = [np.percentile(values, q) for q in (25, 50, 75)]
for x in with_distance:
    x["freight_q"] = "Q1" if x["freight"] <= cuts[0] else ("Q2" if x["freight"] <= cuts[1] else ("Q3" if x["freight"] <= cuts[2] else "Q4"))
m = Fit(with_distance, "late", "freight_q", "Q1", ["band", "month", "item_band"], ["log_value"])
Xa, Xb = m.world("Q4"), m.world("Q1")
boot = boot_rd(m, Xa, Xb, "A5")
R["A5"] = {**m.contrast(Xa, Xb), "bootstrap": boot, "test": m.wald_coefficient("freight_q=Q4"), "cuts": [round(float(c), 2) for c in cuts], "unadjusted": {q: share([x for x in with_distance if x["freight_q"] == q], "late") for q in ("Q1", "Q2", "Q3", "Q4")}, "adjusted": {q: round(m.rate(m.world(q)), 2) for q in ("Q1", "Q2", "Q3", "Q4")}, "diagnostics": m.diagnostics()}


# ------------------------------------------------------------------ A6
def a6(sample, seed, reps=500, simulations=2000):
    random_gen = random.Random(seed)
    months = collections.defaultdict(lambda: [0, 0])
    for x in sample:
        months[x["month"]][0] += 1
        months[x["month"]][1] += x["late"]
    rate = {k: v[1] / v[0] for k, v in months.items()}
    per = collections.defaultdict(list)
    for x in sample:
        per[x["seller"]].append(x)
    eligible = sorted(s for s, v in per.items() if len(v) >= 100)
    top = math.ceil(0.10 * len(eligible))

    def gap(counts):
        ranked = sorted(range(len(counts)), key=lambda j: (-counts[j][1], j))[:top]
        late_total = sum(c[1] for c in counts)
        order_total = sum(c[0] for c in counts)
        return 100 * (sum(counts[j][1] for j in ranked) / late_total - sum(counts[j][0] for j in ranked) / order_total)

    observed = [(len(per[s]), sum(x["late"] for x in per[s])) for s in eligible]
    point = gap(observed)
    boots = sorted(gap([observed[random_gen.randrange(len(observed))] for _ in observed]) for _ in range(reps))
    grid = [[(k, c) for k, c in collections.Counter(x["month"] for x in per[s]).items()] for s in eligible]
    rng = np.random.default_rng(seed)
    higher, nulls = 0, []
    for _ in range(simulations):
        draws = [(observed[j][0], int(sum(rng.binomial(c, rate[k]) for k, c in grid[j]))) for j in range(len(eligible))]
        value = gap(draws)
        nulls.append(value)
        higher += value >= point
    splits = []
    for _ in range(100):
        rank_side, test_side = [], []
        for s in eligible:
            a_l = b_l = b_n = 0
            for x in per[s]:
                if random_gen.random() < 0.5:
                    a_l += x["late"]
                else:
                    b_l += x["late"]
                    b_n += 1
            rank_side.append(a_l)
            test_side.append((b_n, b_l))
        chosen = sorted(range(len(eligible)), key=lambda j: (-rank_side[j], j))[:top]
        splits.append(100 * (sum(test_side[j][1] for j in chosen) / sum(t[1] for t in test_side) - sum(test_side[j][0] for j in chosen) / sum(t[0] for t in test_side)))
    above = below = 0
    for s in eligible:
        expected = sum(rate[x["month"]] for x in per[s])
        variance = sum(rate[x["month"]] * (1 - rate[x["month"]]) for x in per[s])
        z = (sum(x["late"] for x in per[s]) - expected) / math.sqrt(variance)
        above += z > 3.09
        below += z < -3.09
    ranked = sorted(range(len(observed)), key=lambda j: (-observed[j][1], j))[:top]
    return {"estimate": round(point, 3), "ci": [round(boots[int(0.025 * reps)], 3), round(boots[int(0.975 * reps)], 3)], "p": (1 + higher) / (simulations + 1), "sellers": len(eligible), "top": top, "null_mean": round(sum(nulls) / len(nulls), 2), "split_half": round(sum(splits) / len(splits), 2), "above_funnel": above, "below_funnel": below,
            "late_share": round(100 * sum(observed[j][1] for j in ranked) / sum(o[1] for o in observed), 2), "order_share": round(100 * sum(observed[j][0] for j in ranked) / sum(o[0] for o in observed), 2)}


note("A6")
single = [x for x in rows if x["single"]]
R["A6"] = a6(single, next(seed_stream))
R["S8a_A6"] = a6([x for x in single if not x["peak"]], next(seed_stream), reps=300, simulations=500)


# ------------------------------------------------------------------ A7
def a7(sample):
    big = {k for k, v in named.items() if v >= 1000}
    part = [x for x in sample if x["category"] in big]
    reference = collections.Counter(x["category"] for x in part).most_common(1)[0][0]
    fit = Fit(part, "late", "category", reference, ["month", "state_group", "band"], [])
    rates = {c: fit.rate(fit.world(c)) for c in fit.levels}
    high, low = max(rates, key=rates.get), min(rates, key=rates.get)
    terms = [i for n, i in fit.index.items() if n.startswith("category=")]
    b, V = fit.beta[terms], fit.cov[np.ix_(terms, terms)]
    chi = float(b @ np.linalg.solve(V, b))
    from scipy.stats import chi2
    table = collections.Counter((x["category"], x["late"]) for x in part)
    n = len(part)
    totals_c, totals_l = collections.Counter(x["category"] for x in part), collections.Counter(x["late"] for x in part)
    pearson = sum((table[(c, l)] - totals_c[c] * totals_l[l] / n) ** 2 / (totals_c[c] * totals_l[l] / n) for c in totals_c for l in totals_l)
    return {"spread": round(rates[high] - rates[low], 3), "high": high, "low": low, "high_rate": round(rates[high], 2), "low_rate": round(rates[low], 2), "joint_p": float(chi2.sf(chi, len(terms))), "chi2": round(chi, 2), "cramers_v": round(math.sqrt(pearson / n), 4), "categories": len(big), "orders": n, "smallest_category_sellers": min(len({x["seller"] for x in part if x["category"] == c}) for c in big), "diagnostics": fit.diagnostics()}


note("A7")
R["A7"] = a7(with_distance)
R["S15_A7"] = a7([x for x in with_distance if x["days_late"] is not None and (x["d"].date() - x["p"].date()).days <= 60])

# Holm, from these independently computed p-values
p_values = {"A1": R["A1"]["test"]["p"], "A2": R["A2"]["test"]["p"], "A3": R["A3"]["trend"]["p"], "A4": R["A4"]["test"]["p"], "A5": R["A5"]["test"]["p"], "A6": R["A6"]["p"], "A7": R["A7"]["joint_p"]}
ordered = sorted(p_values, key=p_values.get)
holm, running = {}, 0.0
for position, key in enumerate(ordered):
    running = max(running, min(1.0, p_values[key] * (len(ordered) - position)))
    holm[key] = running
R["holm"] = holm

# ------------------------------------------------------------------ 7. Class B and key sensitivity results
note("B3")
m = Fit(reviewed, "low", "group3", "ontime", A2_CATS, A2_NUMS)
wb, wa, wo = m.world("late_before"), m.world("late_after"), m.world("ontime")
lo, hi, failed = m.bootstrap(lambda b, i: [m.rate(wb, b, i) - m.rate(wo, b, i), m.rate(wa, b, i) - m.rate(wo, b, i)], REPS, next(seed_stream))
R["B3"] = {"before": {**m.contrast(wb, wo), "boot_low": lo[0], "boot_high": hi[0]}, "after": {**m.contrast(wa, wo), "boot_low": lo[1], "boot_high": hi[1]}, "failed": failed, "unadjusted": {g: share([x for x in reviewed if x["group3"] == g], "low") for g in ("ontime", "late_before", "late_after")}, "diagnostics": m.diagnostics()}

note("B4")
band_rates = {}
for label, key in (("answer", "timing"), ("created", "timing_created")):
    for timing in ("before", "after"):
        part = [x for x in late_reviews if x[key] == timing]
        band_rates[f"{label}_{timing}"] = {b: (lambda sub: {"orders": len(sub), "rate": round(100 * sum(x["low"] for x in sub) / len(sub), 2) if len(sub) >= 30 else None})([x for x in part if x["delay"] == b]) for b in ("1-3", "4-7", "8-14", "15+")}
R["B4"] = {"rates": band_rates}
part = [x for x in late_reviews if x["timing"] == "before"]
m = Fit(part, "low", "delay", "1-3", A2_CATS, ["log_value"])
ws = {b: m.world(b) for b in ("1-3", "4-7", "8-14", "15+")}
R["B4"]["adjusted_before"] = {f"{a} vs {c}": m.contrast(ws[a], ws[c]) for a, c in pairs}
R["B4"]["diagnostics_before"] = m.diagnostics()
multi_in_before = [x for x in part if x["multi_seller"] == 1]
R["B4"]["multi_seller_before"] = {"orders": len(multi_in_before), "low": int(sum(x["low"] for x in multi_in_before))}
part = [x for x in late_reviews if x["timing"] == "after" and x["delay"] != "15+"]
m = Fit(part, "low", "delay", "1-3", ["month", "state_group", "item_band"], A2_NUMS)
ws = {b: m.world(b) for b in ("1-3", "4-7", "8-14")}
R["B4"]["adjusted_after"] = {f"{a} vs {c}": m.contrast(ws[a], ws[c]) for a, c in (("4-7", "1-3"), ("8-14", "4-7"), ("8-14", "1-3"))}
R["B4"]["diagnostics_after"] = m.diagnostics()

note("B1, B2, B5, B6, B7")
R["B1"] = {"peak": share([x for x in rows if x["peak"]], "late"), "other": share([x for x in rows if not x["peak"]], "late"), "late_share": round(100 * sum(x["late"] for x in rows if x["peak"]) / sum(x["late"] for x in rows), 2), "order_share": round(100 * sum(x["peak"] for x in rows) / len(rows), 2)}
monthly = collections.defaultdict(lambda: [0, 0])
for x in rows:
    monthly[x["month"]][0] += 1
    monthly[x["month"]][1] += x["late"]
R["B1"]["rule_selects"] = sorted(k for k, v in monthly.items() if v[0] >= 100 and v[1] / v[0] >= 0.10)
m = Fit(a1, "late", None, None, ["band", "month", "item_band"], ["log_value", "same_state"], extra={"RJ": lambda x: x["state"] == "RJ", "RJxpeak": lambda x: x["state"] == "RJ" and x["peak"]})
flag = np.array([x["peak"] for x in a1])
Xr, Xs = m.X.copy(), m.X.copy()
Xr[:, m.index["RJ"]], Xr[:, m.index["RJxpeak"]] = 1.0, flag.astype(float)
Xs[:, m.index["RJ"]], Xs[:, m.index["RJxpeak"]] = 0.0, 0.0
R["B2"] = {"gap_peak": m.contrast(Xr, Xs, flag), "gap_other": m.contrast(Xr, Xs, ~flag), "difference": round(m.contrast(Xr, Xs, flag)["estimate"] - m.contrast(Xr, Xs, ~flag)["estimate"], 3), "interaction": m.wald_coefficient("RJxpeak")}
BOUNDARY = datetime(2018, 4, 25)
stage = [x for x in with_distance if x["valid"]]
R["B5"] = {"eligible": len(stage)}
for period, part in (("before", [x for x in stage if x["c"] < BOUNDARY]), ("from", [x for x in stage if x["c"] >= BOUNDARY])):
    m = Fit(part, "late", "handover", "ontime", ["band", "month", "state_group", "item_band"], ["log_value"])
    late_group = [x for x in part if x["handover"] == "late"]
    on_group = [x for x in part if x["handover"] == "ontime"]
    R["B5"][period] = {**m.contrast(m.world("late"), m.world("ontime")), "orders": len(part), "late_group": share(late_group, "late"), "ontime_group": share(on_group, "late"), "late_share_from_late_group": round(100 * sum(x["late"] for x in late_group) / sum(x["late"] for x in part), 2),
                       "median_handover_days": {"late": round(statistics.median((x["c"] - x["p"]).total_seconds() / 86400 for x in late_group), 2), "ontime": round(statistics.median((x["c"] - x["p"]).total_seconds() / 86400 for x in on_group), 2)}}
m = Fit(reviewed, "low", "multi_item", "single", ["month", "state_group", "category_group", "group3"], ["log_value", "multi_seller"])
R["B6"] = {**m.contrast(m.world("multi"), m.world("single")), "unadjusted": {g: share([x for x in reviewed if x["multi_item"] == g], "low") for g in ("single", "multi")}, "diagnostics": m.diagnostics()}
low_total = sum(x["low"] for x in reviewed)
R["B7"] = {"total_low": int(low_total), "on_time_share": round(100 * sum(x["low"] for x in reviewed if not x["late"]) / low_total, 2), "cells": {f"{'late' if la else 'ontime'}_{g}": round(100 * sum(x["low"] for x in reviewed if x["late"] == la and x["multi_item"] == g) / low_total, 2) for la in (0, 1) for g in ("single", "multi")}}

note("key sensitivity results")
K = {}
sp_sellers = [x for x in a1 if x["seller_state"] == "SP"]
m = Fit(sp_sellers, "late", "state", "SP", ["band", "month", "item_band"], ["log_value"])
K["X1a_A1_SP_sellers"] = {**m.contrast(m.world("RJ"), m.world("SP")), "diagnostics": m.diagnostics()}
counts = collections.Counter((x["band"], x["state"]) for x in sp_sellers)
overlap = [b for b in ("0-100", "100-300", "300-600", "600-1000", "1000-2000", "2000+") if counts[(b, "RJ")] >= 30 and counts[(b, "SP")] >= 30]
part = [x for x in sp_sellers if x["band"] in overlap]
m = Fit(part, "late", "state", "SP", ["band", "month", "item_band"], ["log_value"])
K["X1b_A1_overlap"] = {**m.contrast(m.world("RJ"), m.world("SP")), "bands": overlap, "orders": len(part)}
part = [x for x in a1 if x["same_state"] == 0]
m = Fit(part, "late", "state", "SP", ["band", "month", "item_band"], ["log_value"])
K["X1c_A1_out_of_state"] = {**m.contrast(m.world("RJ"), m.world("SP")), "orders": len(part)}
part = [x for x in rows if x["single"] and x["band"] in ("300-600", "600-1000") and x["state"] in ("RJ", "SP")]
m = Fit(part, "late", "state", "SP", ["band", "month", "item_band"], ["log_value", "same_state"])
K["X1d_A1_300_1000km"] = {**m.contrast(m.world("RJ"), m.world("SP")), "orders": len(part)}
m = Fit(with_distance, "late", "freight_q", "Q1", ["band", "month", "item_band", "state_group"], ["log_value"])
K["X2_A5_with_state"] = {**m.contrast(m.world("Q4"), m.world("Q1")), "q2_vs_q1": m.contrast(m.world("Q2"), m.world("Q1"))}
for name, condition in (("X3a_A2_after", lambda x: not x["late"] or x["timing"] == "after"), ("X3b_A2_before", lambda x: not x["late"] or x["timing"] == "before")):
    part = [x for x in reviewed if condition(x)]
    m = Fit(part, "low", "status", "ontime", A2_CATS, A2_NUMS)
    K[name] = {**m.contrast(m.world("late"), m.world("ontime")), "orders": len(part)}
part = [x for x in late_reviews if x["timing"] == "before"]
m = Fit(part, "low", "delay", "1-3", A2_CATS, ["log_value"])
K["X3d_A3_before_15_vs_1_3"] = m.contrast(m.world("15+"), m.world("1-3"))
part = [x for x in late_reviews if x["timing"] == "after" and x["delay"] != "15+"]
m = Fit(part, "low", "delay", "1-3", ["month", "state_group", "item_band"], A2_NUMS)
K["X3e_A3_after_8_14_vs_1_3"] = m.contrast(m.world("8-14"), m.world("1-3"))
no_peak = [x for x in with_distance if not x["peak"]]
part = [x for x in no_peak if x["state"] in ("RJ", "SP")]
m = Fit(part, "late", "state", "SP", ["band", "month", "item_band"], ["log_value", "same_state"])
K["S8a_A1"] = m.contrast(m.world("RJ"), m.world("SP"))
m = Fit(no_peak, "late", "band", "0-100", ["month", "state_group", "item_band"], ["log_value"])
K["S8a_A4"] = m.contrast(m.world("600-1000"), m.world("0-100"))
values2 = sorted(x["freight"] for x in no_peak)
cuts2 = [np.percentile(values2, q) for q in (25, 50, 75)]
for x in no_peak:
    x["fq2"] = "Q1" if x["freight"] <= cuts2[0] else ("Q2" if x["freight"] <= cuts2[1] else ("Q3" if x["freight"] <= cuts2[2] else "Q4"))
m = Fit(no_peak, "late", "fq2", "Q1", ["band", "month", "item_band"], ["log_value"])
K["S8a_A5"] = m.contrast(m.world("Q4"), m.world("Q1"))
part = [x for x in with_distance if x["month"] < "2018-07"]
m = Fit(part, "late", "band", "0-100", ["month", "state_group", "item_band"], ["log_value"])
K["S8c_A4"] = m.contrast(m.world("600-1000"), m.world("0-100"))
part = [x for x in late_reviews if (x["d"].date() - x["p"].date()).days <= 60]
m = Fit(part, "low", "delay", "1-3", A2_CATS, A2_NUMS)
K["S15_A3_15_vs_8_14"] = m.contrast(m.world("15+"), m.world("8-14"))
for x in reviewed:
    x["low_first"] = float(x["score_first"] <= 2)
m = Fit(reviewed, "low_first", "status", "ontime", A2_CATS, A2_NUMS)
K["S1a_A2_earliest"] = m.contrast(m.world("late"), m.world("ontime"))
m = Fit([x for x in reviewed], "low", "group3", "ontime", A2_CATS, A2_NUMS)
for x in reviewed:
    x["group3c"] = "ontime" if not x["late"] else ("late_before" if x["timing_created"] == "before" else "late_after")
m = Fit(reviewed, "low", "group3c", "ontime", A2_CATS, A2_NUMS)
K["S9_B3_before"] = m.contrast(m.world("late_before"), m.world("ontime"))
K["S9_B3_after"] = m.contrast(m.world("late_after"), m.world("ontime"))
out["results"], out["sensitivity"] = R, K

# ------------------------------------------------------------------ 8. Review timing, carrier change, selection
note("process checks")
lags = collections.defaultdict(list)
for x in reviewed:
    group = "late" if x["late"] else "on time"
    lags[group + ", created minus delivered"].append((x["created"].date() - x["d"].date()).days)
    lags[group + ", created minus estimated"].append((x["created"].date() - x["e"].date()).days)
    lags[group + ", answered minus created"].append((x["answered"] - x["created"]).total_seconds() / 86400)
timing_cross = collections.Counter((x["timing_created"], x["timing"]) for x in late_reviews)
out["review_timing"] = {"median_lags_days": {k: round(statistics.median(v), 2) for k, v in lags.items()}, "created_vs_answer_among_late": {f"created {a}, answered {b}": timing_cross[(a, b)] for a in ("before", "after") for b in ("before", "after")},
                        "late_answer_before_created": sum(x["answered"] < x["created"] for x in reviewed), "created_time_not_midnight": sum(x["created"].time() != datetime.min.time() for x in reviewed)}
for label, part in (("created_before_answered_after", [x for x in late_reviews if x["timing_created"] == "before" and x["timing"] == "after"]), ("created_before_answered_before", [x for x in late_reviews if x["timing_created"] == "before" and x["timing"] == "before"]), ("created_after", [x for x in late_reviews if x["timing_created"] == "after"])):
    out["review_timing"][label] = {"orders": len(part), "low_rate": round(100 * sum(x["low"] for x in part) / len(part), 2) if part else None}

daily = collections.defaultdict(list)
for x in rows:
    if x["c"] and datetime(2018, 4, 16) <= x["c"] < datetime(2018, 5, 5):
        daily[x["c"].date().isoformat()].append(x["c"].hour)
out["carrier_change"] = {day: {"orders": len(v), "median_hour": statistics.median(v), "evening_pct": round(100 * sum(17 <= h <= 23 for h in v) / len(v))} for day, v in sorted(daily.items())}
small = [x for x in rows if x["c"] and x["c"] < x["p"] and (x["p"] - x["c"]) < timedelta(hours=3)]
out["carrier_small_gap"] = {"orders": len(small), "first_carrier_date": min(x["c"] for x in small).isoformat(), "from_boundary": sum(x["c"] >= BOUNDARY for x in small)}
period_hours = {}
for label, part in (("before", [x for x in rows if x["c"] and x["c"] < BOUNDARY]), ("from", [x for x in rows if x["c"] and x["c"] >= BOUNDARY])):
    period_hours[label] = {"purchase": statistics.median(x["p"].hour for x in part), "delivery": statistics.median(x["d"].hour for x in part), "carrier": statistics.median(x["c"].hour for x in part), "orders": len(part)}
out["carrier_change_other_fields"] = period_hours

selection = {}
all_status = collections.defaultdict(lambda: [0, 0])
for r in orders_raw:
    s = customers[r["customer_id"]][0]
    all_status[s][0] += 1
    all_status[s][1] += r["order_status"] == "delivered"
selection["not_delivered_pct"] = {s: round(100 * (1 - all_status[s][1] / all_status[s][0]), 2) for s in ("SP", "RJ", "MG", "BA")}
peak_rows = [r for r in orders_raw if r["order_purchase_timestamp"][:7] in PEAK]
other_rows = [r for r in orders_raw if r["order_purchase_timestamp"][:7] not in PEAK and "2017-01" <= r["order_purchase_timestamp"][:7] <= "2018-08"]
selection["not_delivered_peak_pct"] = round(100 * sum(r["order_status"] != "delivered" for r in peak_rows) / len(peak_rows), 2)
selection["not_delivered_other_pct"] = round(100 * sum(r["order_status"] != "delivered" for r in other_rows) / len(other_rows), 2)
missing_late = sum(1 for x in rows if x["score"] is None and x["late"])
missing_on = sum(1 for x in rows if x["score"] is None and not x["late"])
selection["unreviewed"] = {"late": missing_late, "on_time": missing_on, "late_share_unreviewed_pct": round(100 * missing_late / sum(x["late"] for x in rows), 2), "on_time_share_unreviewed_pct": round(100 * missing_on / sum(1 - x["late"] for x in rows), 2)}
selection["reviews_on_undelivered_orders"] = sum(1 for o, v in reviews_by_order.items() for r in orders_raw[:0]) if False else sum(r["order_status"] != "delivered" and r["order_id"] in reviews_by_order for r in orders_raw)
out["selection"] = selection
sizes = collections.Counter(x["seller"] for x in rows)
out["clusters"] = {"sellers": len(sizes), "largest_seller_orders": max(sizes.values()), "largest_seller_share_pct": round(100 * max(sizes.values()) / len(rows), 2), "sellers_under_10_orders": sum(v < 10 for v in sizes.values())}
out["runtime_minutes"] = round((time.time() - started) / 60, 1)
(ROOT / "data" / "processed" / "independent_audit_results.json").write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
note("done")
