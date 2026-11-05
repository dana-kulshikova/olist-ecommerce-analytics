"""Stage 2, steps 4-5: Class B exploratory questions, with answer timing first.

All results are exploratory and observational. They can suggest what to investigate or test, and
don't confirm anything. Class A results and definitions aren't changed. Writes
data/processed/class_b_results.json, which Git ignores.

Usage: python python/analysis/class_b.py [replicates]
"""
import json
import sys
import time

import numpy as np
import pandas as pd

from modeling import DELAY_BANDS, OUT, SEED, Logit, interval, load_orders, rate_row, risk, seller_weights, wilson

REPLICATES = int(sys.argv[1]) if len(sys.argv) > 1 else 500
seeds = iter(np.random.SeedSequence([SEED, 2]).spawn(30))
data = load_orders()
results, checks = {}, {}
LATE_POINTS, LATE_ORDERS, LOW_POINTS = 2.0, 500, 5.0
A2_ESTIMATE = round(json.loads((OUT / "class_a_results.json").read_text(encoding="utf-8"))["results"]["A2"]["estimate"], 2)
A2_CATEGORICAL = ["purchase_month", "state_group", "item_band", "category_group"]
A2_NUMERIC = ["log_order_value", "multi_seller"]


def timed(label):
    print(f"[{time.strftime('%H:%M:%S')}] {label}", flush=True)


def pattern(estimate, ci, criterion, orders_ok=True):
    if ci[0] > 0 and estimate >= criterion and orders_ok:
        return "Pattern observed"
    if ci[1] < 0 and -estimate >= criterion and orders_ok:
        return "Pattern observed, opposite direction"
    if ci[0] > 0 and estimate >= criterion:
        return f"Meets the percentage-point criterion; misses the minimum of {LATE_ORDERS} late orders"
    if ci[0] > 0 or ci[1] < 0:
        return "Small pattern, below the screening criterion"
    return "Not observed"


reviewed = data[data["has_review"]].copy()

# ------------------------------------------------------------------ B3
timed("B3")
GROUPS = ["on time", "late, answered before arrival", "late, answered after arrival"]
b3_frame = reviewed.copy()
before_column, after_column = "timing=before", "timing=after"


def timing_columns(frame):
    return pd.DataFrame({before_column: frame["delivery_timing"].eq(GROUPS[1]).astype(float),
                         after_column: frame["delivery_timing"].eq(GROUPS[2]).astype(float)}, index=frame.index)


b3 = Logit("B3", b3_frame, "low_rating", A2_CATEGORICAL, A2_NUMERIC, extra=timing_columns)
worlds = {GROUPS[0]: b3.counterfactual({before_column: 0, after_column: 0}),
          GROUPS[1]: b3.counterfactual({before_column: 1, after_column: 0}),
          GROUPS[2]: b3.counterfactual({before_column: 0, after_column: 1})}
rates = {name: risk(b3.beta, X) for name, X in worlds.items()}


def b3_stat(beta, w):
    r = {name: risk(beta, X, w) for name, X in worlds.items()}
    return [r[GROUPS[1]] - r[GROUPS[0]], r[GROUPS[2]] - r[GROUPS[0]], r[GROUPS[1]] - r[GROUPS[2]]]


boot = b3.bootstrap(b3_stat, REPLICATES, next(seeds))
distribution = {}
for name, part in b3_frame.groupby("delivery_timing"):
    distribution[name] = {str(int(k)): round(100 * v, 2) for k, v in part["latest_review_score"].value_counts(normalize=True).sort_index().items()}
diff_before = rates[GROUPS[1]] - rates[GROUPS[0]]
diff_after = rates[GROUPS[2]] - rates[GROUPS[0]]
results["B3"] = {
    "question": "Answer timing and low ratings",
    "unadjusted": {name: rate_row(b3_frame[b3_frame["delivery_timing"].eq(name)], "low_rating") for name in GROUPS},
    "mean_scores": {name: round(float(b3_frame.loc[b3_frame["delivery_timing"].eq(name), "latest_review_score"].mean()), 3) for name in GROUPS},
    "score_distribution_pct": distribution, "adjusted_rates": {k: round(v, 2) for k, v in rates.items()},
    "late_answered_before_vs_on_time": {"estimate": round(diff_before, 2), "ci": interval(boot[:, 0]), "odds_ratio": b3.odds_ratio(before_column), "mean_score": b3.mean_score_difference(before_column), "pattern": pattern(diff_before, interval(boot[:, 0]), LOW_POINTS)},
    "late_answered_after_vs_on_time": {"estimate": round(diff_after, 2), "ci": interval(boot[:, 1]), "odds_ratio": b3.odds_ratio(after_column), "mean_score": b3.mean_score_difference(after_column), "pattern": pattern(diff_after, interval(boot[:, 1]), LOW_POINTS)},
    "before_vs_after_among_late": {"estimate": round(rates[GROUPS[1]] - rates[GROUPS[2]], 2), "ci": interval(boot[:, 2])},
    "a2_estimate_for_context": A2_ESTIMATE,
    "on_time_answered_before_arrival": int((reviewed["late"].eq(0) & reviewed["answer_timing"].eq("before arrival")).sum()),
    "share_of_late_reviews_answered_before": round(100 * (reviewed["late"].eq(1) & reviewed["answer_timing"].eq("before arrival")).sum() / reviewed["late"].sum(), 2),
}
checks["B3"] = b3.report

# ------------------------------------------------------------------ B4
timed("B4")
late_reviews = reviewed[reviewed["late"].eq(1)].copy()
composition = pd.crosstab(late_reviews["delay_band"], late_reviews["answer_timing"]).reindex(DELAY_BANDS)
composition["share_before_pct"] = (100 * composition["before arrival"] / composition.sum(axis=1)).round(2)
b4 = {"composition_by_delay_band": composition.to_dict("index"), "by_timing": {}}
PAIRS = [("4-7 days", "1-3 days"), ("8-14 days", "4-7 days"), ("15+ days", "8-14 days")]
for timing, part in late_reviews.groupby("answer_timing"):
    part = part.copy()
    bands = {band: rate_row(part[part["delay_band"].eq(band)], "low_rating") for band in DELAY_BANDS}
    usable = [band for band in DELAY_BANDS if bands[band]["rate"] is not None]
    # Unadjusted differences between adjacent reportable bands, with a seller-level bootstrap.
    codes, uniques = pd.factorize(part["primary_seller_id"])
    y = part["low_rating"].to_numpy()
    band = part["delay_band"].to_numpy()
    rng = np.random.default_rng(next(seeds))
    samples = {f"{a} vs {b}": [] for a, b in PAIRS if a in usable and b in usable}
    for _ in range(REPLICATES):
        w = seller_weights(codes, len(uniques), rng)
        rate = {}
        for name in usable:
            mask = band == name
            rate[name] = 100 * np.sum(w[mask] * y[mask]) / np.sum(w[mask]) if np.sum(w[mask]) > 0 else np.nan
        for a, b in PAIRS:
            key = f"{a} vs {b}"
            if key in samples:
                samples[key].append(rate[a] - rate[b])
    pairs = {}
    for a, b in PAIRS:
        key = f"{a} vs {b}"
        if key in samples:
            values = np.array(samples[key], float)
            values = values[~np.isnan(values)]
            estimate = round(bands[a]["rate"] - bands[b]["rate"], 2)
            ci = interval(values)
            pairs[key] = {"unadjusted_difference": estimate, "ci": ci, "pattern": pattern(estimate, ci, LOW_POINTS)}
    # Adjusted model only where events per term allow it; the adjustment set is reduced first, and this is reported.
    adjusted = {"note": None}
    pool = part[part["delay_band"].isin(usable)].copy()
    sets = [(A2_CATEGORICAL, A2_NUMERIC, "full A2 set"), (["purchase_month", "state_group", "item_band"], ["log_order_value", "multi_seller"], "without category"),
            (["purchase_month", "item_band"], ["log_order_value"], "without category, state and multi-seller")]
    if timing == "before arrival":
        # All 3 multi-seller orders in this group are low-rated, so the multi-seller term is separated:
        # its coefficient grows without limit (17.31 after 23 iterations) and carries no usable information.
        # It's removed from this model only. The band estimates barely change without it.
        sets[0] = (A2_CATEGORICAL, ["log_order_value"], "A2 set without the multi-seller term, because of separation")
    chosen = None
    for categorical, numeric, label in sets:
        def extra(frame, names=tuple(usable[1:])):
            return pd.DataFrame({f"band={name}": frame["delay_band"].eq(name).astype(float) for name in names}, index=frame.index)
        candidate = Logit(f"B4 {timing}", pool, "low_rating", categorical, numeric, extra=extra)
        if candidate.report["events_per_parameter"] >= 10 and candidate.report["non_events_per_parameter"] >= 10:
            chosen = (candidate, label)
            break
    if chosen is None:
        adjusted["note"] = "Too few events for an adjusted model"
    else:
        model, label = chosen
        names = usable[1:]
        worlds_b = {usable[0]: model.counterfactual({f"band={n}": 0 for n in names})}
        for name in names:
            worlds_b[name] = model.counterfactual({f"band={n}": (1 if n == name else 0) for n in names})
        band_rates = {k: risk(model.beta, X) for k, X in worlds_b.items()}
        keys = [(a, b) for a, b in PAIRS if a in usable and b in usable]

        def stat(beta, w, keys=tuple(keys), worlds_b=worlds_b):
            r = {k: risk(beta, X, w) for k, X in worlds_b.items()}
            return [r[a] - r[b] for a, b in keys]

        draws = model.bootstrap(stat, REPLICATES, next(seeds))
        adjusted = {"adjustment_set": label, "rates": {k: round(v, 2) for k, v in band_rates.items()},
                    "pairs": {f"{a} vs {b}": {"estimate": round(band_rates[a] - band_rates[b], 2), "ci": interval(draws[:, i])} for i, (a, b) in enumerate(keys)}}
        checks[f"B4 {timing}"] = model.report
    pooled = part[part["delay_band"].isin(["8-14 days", "15+ days"])]
    b4["by_timing"][timing] = {"bands": bands, "unadjusted_pairs": pairs, "adjusted": adjusted, "pooled_8_plus_days": rate_row(pooled, "low_rating")}
results["B4"] = b4

# ------------------------------------------------------------------ B1
timed("B1")
monthly = data.groupby("purchase_month")["late"].agg(orders="size", late="sum").sort_index()
monthly["rate"] = (100 * monthly["late"] / monthly["orders"]).round(2)
limits = [wilson(int(r.late), int(r.orders)) for r in monthly.itertuples()]
monthly["low"], monthly["high"] = [round(a, 2) for a, _ in limits], [round(b, 2) for _, b in limits]
monthly["share_of_late_pct"] = (100 * monthly["late"] / monthly["late"].sum()).round(2)
peak_months = monthly[(monthly["orders"] >= 100) & (monthly["rate"] >= 10)].index.tolist()
data["peak"] = data["purchase_month"].isin(peak_months)
peak = data["peak"].to_numpy()
y = data["late"].to_numpy(float)
codes, uniques = pd.factorize(data["primary_seller_id"])
rng = np.random.default_rng(next(seeds))
draws = []
for _ in range(REPLICATES):
    w = seller_weights(codes, len(uniques), rng)
    late_share = 100 * np.sum(w[peak] * y[peak]) / np.sum(w * y)
    order_share = 100 * np.sum(w[peak]) / np.sum(w)
    rate_gap = 100 * (np.sum(w[peak] * y[peak]) / np.sum(w[peak]) - np.sum(w[~peak] * y[~peak]) / np.sum(w[~peak]))
    draws.append([late_share - order_share, rate_gap])
draws = np.array(draws)
peak_late, peak_orders = int(y[peak].sum()), int(peak.sum())
rate_gap = 100 * (y[peak].mean() - y[~peak].mean())
results["B1"] = {
    "question": "Late orders concentrated in peak months", "rule": "at least 100 orders and a late rate of 10% or more, written after seeing the data",
    "peak_months": peak_months, "monthly": monthly.reset_index().to_dict("records"),
    "peak_orders": peak_orders, "peak_late": peak_late, "other_orders": int((~peak).sum()), "other_late": int(y[~peak].sum()),
    "peak_rate": round(100 * y[peak].mean(), 2), "other_rate": round(100 * y[~peak].mean(), 2),
    "order_share_pct": round(100 * peak_orders / len(y), 2), "late_share_pct": round(100 * peak_late / y.sum(), 2),
    "share_gap": {"estimate": round(100 * peak_late / y.sum() - 100 * peak_orders / len(y), 2), "ci": interval(draws[:, 0])},
    "rate_difference": {"estimate": round(rate_gap, 2), "ci": interval(draws[:, 1]), "pattern": pattern(rate_gap, interval(draws[:, 1]), LATE_POINTS, peak_late >= LATE_ORDERS)},
}

# ------------------------------------------------------------------ B2
timed("B2")
with_distance = data[data["single_seller"] & data["distance_km"].notna()].copy()
b2_frame = with_distance[with_distance["customer_state"].isin(["RJ", "SP"])].copy()


def b2_columns(frame):
    rj = frame["customer_state"].eq("RJ").astype(float)
    return pd.DataFrame({"RJ": rj, "RJ x peak": rj * frame["peak"].astype(float)}, index=frame.index)


b2 = Logit("B2", b2_frame, "late", ["distance_band", "purchase_month", "item_band"], ["log_order_value", "same_state_seller"], extra=b2_columns)
peak_flag = b2.frame["peak"].to_numpy(bool)
rj_world = b2.counterfactual({"RJ": 1.0, "RJ x peak": peak_flag.astype(float)})
sp_world = b2.counterfactual({"RJ": 0.0, "RJ x peak": 0.0})


def gaps(beta, w=None):
    peak_gap = risk(beta, rj_world, w, peak_flag) - risk(beta, sp_world, w, peak_flag)
    other_gap = risk(beta, rj_world, w, ~peak_flag) - risk(beta, sp_world, w, ~peak_flag)
    return [peak_gap, other_gap, peak_gap - other_gap]


point = gaps(b2.beta)
draws = b2.bootstrap(lambda beta, w: gaps(beta, w), REPLICATES, next(seeds))
segment = {}
for state in ("RJ", "SP"):
    for label, flag in (("peak months", True), ("other months", False)):
        segment[f"{state}, {label}"] = rate_row(b2_frame[b2_frame["customer_state"].eq(state) & b2_frame["peak"].eq(flag)], "late")
sp_seller = data[data["single_seller"] & data["primary_seller_state"].eq("SP")]
routes = {}
for state in ("SP", "RJ", "MG", "PR", "ES", "BA"):
    for label, flag in (("peak months", True), ("other months", False)):
        routes[f"SP sellers to {state}, {label}"] = rate_row(sp_seller[sp_seller["customer_state"].eq(state) & sp_seller["peak"].eq(flag)], "late")
rj_peak_late = int(b2_frame.loc[b2_frame["customer_state"].eq("RJ") & b2_frame["peak"], "late"].sum())
results["B2"] = {
    "question": "RJ gap in peak and other months", "unadjusted": segment, "sp_seller_routes": routes,
    "adjusted_gap_peak": {"estimate": round(point[0], 2), "ci": interval(draws[:, 0])},
    "adjusted_gap_other": {"estimate": round(point[1], 2), "ci": interval(draws[:, 1])},
    "difference_of_gaps": {"estimate": round(point[2], 2), "ci": interval(draws[:, 2]), "pattern": pattern(point[2], interval(draws[:, 2]), LATE_POINTS, rj_peak_late >= LATE_ORDERS)},
    "interaction_odds_ratio": b2.odds_ratio("RJ x peak"), "rj_late_orders_in_peak": rj_peak_late,
    "rj_share_of_its_late_orders_in_peak_pct": round(100 * rj_peak_late / b2_frame.loc[b2_frame["customer_state"].eq("RJ"), "late"].sum(), 2),
    "note": "Odds ratio is on the log-odds scale and can differ in direction from the risk difference.",
}
checks["B2"] = b2.report

# ------------------------------------------------------------------ B5
timed("B5")
b5 = {"periods": {}}
stage = with_distance[with_distance["valid"]].copy()
b5["eligible_orders"] = int(len(stage))
for period, part in stage.groupby("carrier_period"):
    part = part.copy()

    def handover_column(frame):
        return pd.DataFrame({"late handover": frame["seller_late"].eq("late handover").astype(float)}, index=frame.index)

    model = Logit(f"B5 {period}", part, "late", ["distance_band", "purchase_month", "state_group", "item_band"], ["log_order_value"], extra=handover_column)
    yes = model.counterfactual({"late handover": 1.0})
    no = model.counterfactual({"late handover": 0.0})
    estimate = risk(model.beta, yes) - risk(model.beta, no)
    draws = model.bootstrap(lambda beta, w: [risk(beta, yes, w) - risk(beta, no, w)], REPLICATES, next(seeds))
    ci = interval(draws[:, 0])
    table = {}
    for group, g in part.groupby("seller_late"):
        table[group] = {**rate_row(g, "late"), "share_of_period_late_pct": round(100 * g["late"].sum() / part["late"].sum(), 2), "share_of_period_orders_pct": round(100 * len(g) / len(part), 2),
                        "median_handover_days": round(float(g["handover_days"].median()), 2), "median_later_stage_days": round(float(g["later_stage_days"].median()), 2)}
    late_in_group = int(part.loc[part["seller_late"].eq("late handover"), "late"].sum())
    b5["periods"][period] = {
        "orders": len(part), "late": int(part["late"].sum()), "groups": table, "adjusted_rates": {"late handover": round(risk(model.beta, yes), 2), "on-time handover": round(risk(model.beta, no), 2)},
        "adjusted_difference": {"estimate": round(estimate, 2), "ci": ci, "pattern": pattern(estimate, ci, LATE_POINTS, late_in_group >= LATE_ORDERS)}, "odds_ratio": model.odds_ratio("late handover"),
        "late_orders_in_late_handover_group": late_in_group, "median_stage_days_all": {"handover": round(float(part["handover_days"].median()), 2), "later_stage": round(float(part["later_stage_days"].median()), 2), "total_purchase_to_delivery": round(float(part["delivery_days"].median()), 2)},
    }
    checks[f"B5 {period}"] = model.report
results["B5"] = b5

# ------------------------------------------------------------------ B6
timed("B6")
b6_frame = reviewed.copy()


def b6_columns(frame):
    multi = frame["multi_item"].eq("multi-item").astype(float)
    return pd.DataFrame({"multi-item": multi}, index=frame.index)


b6 = Logit("B6", b6_frame, "low_rating", ["purchase_month", "state_group", "category_group", "delivery_timing"], ["log_order_value", "multi_seller"], extra=b6_columns)
multi_world, single_world = b6.counterfactual({"multi-item": 1.0}), b6.counterfactual({"multi-item": 0.0})
on_time_flag = b6.frame["late"].eq(0).to_numpy()


def b6_stat(beta, w=None):
    overall = risk(beta, multi_world, w) - risk(beta, single_world, w)
    on_time = risk(beta, multi_world, w, on_time_flag) - risk(beta, single_world, w, on_time_flag)
    late = risk(beta, multi_world, w, ~on_time_flag) - risk(beta, single_world, w, ~on_time_flag)
    return [overall, on_time, late]


point = b6_stat(b6.beta)
draws = b6.bootstrap(lambda beta, w: b6_stat(beta, w), REPLICATES, next(seeds))


def b6_interaction(frame):
    multi = frame["multi_item"].eq("multi-item").astype(float)
    return pd.DataFrame({"multi-item": multi, "multi-item x late": multi * frame["late"].astype(float)}, index=frame.index)


b6_i = Logit("B6 interaction", b6_frame, "low_rating", ["purchase_month", "state_group", "category_group", "delivery_timing"], ["log_order_value", "multi_seller"], extra=b6_interaction)
i_multi = b6_i.counterfactual({"multi-item": 1.0, "multi-item x late": b6_i.frame["late"].astype(float).to_numpy()})
i_single = b6_i.counterfactual({"multi-item": 0.0, "multi-item x late": 0.0})
flag = b6_i.frame["late"].eq(0).to_numpy()
strat = {"on time": round(risk(b6_i.beta, i_multi, None, flag) - risk(b6_i.beta, i_single, None, flag), 2), "late": round(risk(b6_i.beta, i_multi, None, ~flag) - risk(b6_i.beta, i_single, None, ~flag), 2)}
draws_i = b6_i.bootstrap(lambda beta, w: [risk(beta, i_multi, w, flag) - risk(beta, i_single, w, flag), risk(beta, i_multi, w, ~flag) - risk(beta, i_single, w, ~flag)], REPLICATES, next(seeds))
item_groups = {}
for label, mask in (("1 item", b6_frame["items_count"].eq(1)), ("2 items", b6_frame["items_count"].eq(2)), ("3+ items", b6_frame["items_count"].ge(3))):
    item_groups[label] = rate_row(b6_frame[mask], "low_rating")
multi_rows = b6_frame["multi_item"].eq("multi-item")
results["B6"] = {
    "question": "Multi-item orders and low ratings",
    "unadjusted": {name: rate_row(b6_frame[b6_frame["multi_item"].eq(name)], "low_rating") for name in ("single item", "multi-item")},
    "unadjusted_by_status": {f"{item}, {status}": rate_row(b6_frame[b6_frame["multi_item"].eq(item) & b6_frame["late"].eq(code)], "low_rating")
                             for item in ("single item", "multi-item") for status, code in (("on time", 0), ("late", 1))},
    "by_item_count": item_groups,
    "adjusted_difference": {"estimate": round(point[0], 2), "ci": interval(draws[:, 0]), "pattern": pattern(point[0], interval(draws[:, 0]), LOW_POINTS)},
    "odds_ratio": b6.odds_ratio("multi-item"), "mean_score": b6.mean_score_difference("multi-item"),
    "with_interaction": {"difference_on_time": {"estimate": strat["on time"], "ci": interval(draws_i[:, 0])}, "difference_late": {"estimate": strat["late"], "ci": interval(draws_i[:, 1])}, "interaction_odds_ratio": b6_i.odds_ratio("multi-item x late")},
    "overlap": {"multi_item_orders": int(multi_rows.sum()), "multi_item_share_pct": round(100 * multi_rows.mean(), 2),
                "multi_seller_among_multi_item_pct": round(100 * b6_frame.loc[multi_rows, "multi_seller"].mean(), 2),
                "multi_seller_among_single_item_pct": round(100 * b6_frame.loc[~multi_rows, "multi_seller"].mean(), 2),
                "median_value_single": round(float(b6_frame.loc[~multi_rows, "product_sales"].median()), 2), "median_value_multi": round(float(b6_frame.loc[multi_rows, "product_sales"].median()), 2),
                "correlation_items_log_value": round(float(b6_frame["items_count"].corr(b6_frame["log_order_value"])), 3)},
}
checks["B6"] = b6.report
checks["B6 interaction"] = b6_i.report

# ------------------------------------------------------------------ B7
timed("B7")
low = reviewed["low_rating"].to_numpy()
status = reviewed["late"].to_numpy()
multi = reviewed["multi_item"].eq("multi-item").to_numpy()
codes, uniques = pd.factorize(reviewed["primary_seller_id"])
cells = {"on time, single item": (status == 0) & ~multi, "on time, multi-item": (status == 0) & multi, "late, single item": (status == 1) & ~multi, "late, multi-item": (status == 1) & multi}
rng = np.random.default_rng(next(seeds))
samples = {name: [] for name in cells}
samples["on time, all"] = []
for _ in range(REPLICATES):
    w = seller_weights(codes, len(uniques), rng)
    total = np.sum(w * low)
    for name, mask in cells.items():
        samples[name].append(100 * np.sum(w[mask] * low[mask]) / total)
    samples["on time, all"].append(100 * np.sum((w * low)[status == 0]) / total)
total_low = low.sum()
b7 = {"total_low_ratings": int(total_low), "total_reviewed": int(len(low)), "groups": {}}
for name, mask in cells.items():
    share = 100 * low[mask].sum() / total_low
    b7["groups"][name] = {"reviewed": int(mask.sum()), "low_ratings": int(low[mask].sum()), "share_of_low_ratings_pct": round(share, 2), "ci": interval(samples[name]),
                          "low_rate_within_group_pct": round(100 * low[mask].mean(), 2), "pattern": "Observed at the 10% screening level" if share >= 10 else "Below the 10% screening level"}
b7["on_time_all"] = {"low_ratings": int(low[status == 0].sum()), "share_of_low_ratings_pct": round(100 * low[status == 0].sum() / total_low, 2), "ci": interval(samples["on time, all"])}
results["B7"] = b7

output = {"class": "B, exploratory", "seed": SEED, "replicates": REPLICATES, "results": results, "checks": checks}
(OUT / "class_b_results.json").write_text(json.dumps(output, indent=1, default=str), encoding="utf-8")
timed("done")
