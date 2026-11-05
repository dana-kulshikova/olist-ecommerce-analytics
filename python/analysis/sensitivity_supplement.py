"""Stage 2, step 7: planned sensitivity checks for the remaining exploratory results.

Covers B4 and B7 under the review, late-definition and period checks, B1 under S3, and B2, B4 and
B5 under S13. Results are exploratory and observational. Primary results aren't changed. Unadjusted
B4 differences use a linear model on the delay bands with errors clustered by seller.

Writes data/processed/sensitivity_supplement.json, which Git ignores. Reads no database.

Usage: python python/analysis/sensitivity_supplement.py [raw-csv-folder]
"""
import json

import numpy as np
import pandas as pd
import scipy.stats as ss
import statsmodels.api as sm

import sensitivity_common as sc
from sensitivity_common import DELAY_BANDS, MIN_ORDERS, OUT, TIMING, Z, base, delta_rd, diagnostics, fit_lpm, fit_spec, with_distance
from modeling import Logit

B4_ROWS, B7_ROWS, OTHER_ROWS, NOT_APPLICABLE = [], [], [], []
PAIRS = [("4-7 days", "1-3 days"), ("8-14 days", "4-7 days"), ("15+ days", "8-14 days")]


def low_threshold(threshold):
    def apply(f):
        f["low_rating"] = np.where(f["has_review"], f["latest_review_score"].le(threshold).astype(float), np.nan)
        return f
    return apply


SCENARIOS = [
    ("S0", "baseline", "Primary definitions", sc.s_primary),
    ("S1a", "S1", "Earliest review", sc.s1_earliest),
    ("S1b", "S1", "Excluding orders with several reviews", sc.s1_single_review),
    ("S2", "S2", "Excluding repeated review IDs", sc.s2_no_repeated),
    ("S4a", "S4", "Source CSV timestamps", sc.s4_csv_values),
    ("S4b", "S4", "Affected orders excluded", sc.s4_exclude),
    ("S5a", "S5", "Full timestamp, previous logic", sc.s5_timestamp),
    ("S5b", "S5", "2 or more days late", sc.s5_two_days),
    ("S6a", "S6", "1 star only", low_threshold(1)),
    ("S6b", "S6", "1-3 stars", low_threshold(3)),
    ("S8a", "S8", "Excluding peak months", sc.s8_no_peak),
    ("S8b", "S8", "Excluding 2016", sc.s8_no_2016),
    ("S8c", "S8", "Excluding purchases from July 2018", sc.s8_before_july),
    ("S9", "S9", "Survey creation date instead of answer timestamp", sc.s9_survey_date),
    ("S15", "S15", "Excluding deliveries over 60 days", sc.s15_no_long),
    ("S16", "S16", "Excluding reviews created before the purchase date", sc.s16_no_early_review),
]


def rate_cell(part):
    n = len(part)
    if n < MIN_ORDERS:
        return {"orders": n, "low": None, "rate": None}
    return {"orders": n, "low": int(part["low_rating"].sum()), "rate": round(100 * part["low_rating"].mean(), 2)}


def b4_pairs(part, outcome="low_rating"):
    """Unadjusted differences between adjacent delay bands with at least 30 reviews, clustered by seller."""
    usable = [b for b in DELAY_BANDS if (part["delay_band"] == b).sum() >= MIN_ORDERS]
    if len(usable) < 2:
        return {}
    sample = part[part["delay_band"].isin(usable)]
    design = pd.DataFrame({"const": 1.0, **{b: sample["delay_band"].eq(b).astype(float) for b in usable[1:]}}, index=sample.index)
    codes = pd.factorize(sample["primary_seller_id"])[0]
    fit = sm.OLS(sample[outcome].astype(float), design).fit(cov_type="cluster", cov_kwds={"groups": codes})
    scale = 1 if outcome == "latest_review_score" else 100
    out = {}
    for a, b in PAIRS:
        if a in usable and b in usable:
            L = np.zeros(len(design.columns))
            L[list(design.columns).index(a)] = 1
            if b != usable[0]:
                L[list(design.columns).index(b)] = -1
            est = float(L @ fit.params.to_numpy())
            se = float(np.sqrt(L @ fit.cov_params().to_numpy() @ L))
            out[f"{a} vs {b}"] = {"estimate": round(scale * est, 3), "ci": [round(scale * (est - Z * se), 3), round(scale * (est + Z * se), 3)]}
    return out


for scenario_id, plan_id, label, function in SCENARIOS:
    sc.timed(f"{scenario_id}: {label}")
    frame = function(base.copy())
    reviews = frame[frame["has_review"]].copy()
    late_reviews = reviews[reviews["late"].eq(1) & reviews["delay_band"].notna()]
    for timing in ("before arrival", "after arrival"):
        part = late_reviews[late_reviews["answer_timing"].eq(timing)]
        B4_ROWS.append({"scenario": scenario_id, "plan_check": plan_id, "label": label, "timing": timing,
                        "bands": {b: rate_cell(part[part["delay_band"].eq(b)]) for b in DELAY_BANDS}, "pairs": b4_pairs(part)})
    composition = {b: round(100 * (late_reviews.loc[late_reviews["delay_band"].eq(b), "answer_timing"].eq("before arrival")).mean(), 2) if (late_reviews["delay_band"].eq(b)).any() else None for b in DELAY_BANDS}
    B4_ROWS[-1]["share_before_by_band"] = composition
    B4_ROWS[-2]["share_before_by_band"] = composition
    low = reviews["low_rating"].to_numpy()
    late = reviews["late"].to_numpy()
    multi = reviews["multi_item"].eq("multi-item").to_numpy()
    total = low.sum()
    cells = {"on time, single item": (late == 0) & ~multi, "on time, multi-item": (late == 0) & multi, "late, single item": (late == 1) & ~multi, "late, multi-item": (late == 1) & multi}
    B7_ROWS.append({"scenario": scenario_id, "plan_check": plan_id, "label": label, "reviewed": len(reviews), "low_ratings": int(total), "on_time_share_pct": round(100 * low[late == 0].sum() / total, 2),
                    "cells": {k: {"reviewed": int(m.sum()), "low": int(low[m].sum()), "share_pct": round(100 * low[m].sum() / total, 2), "rate_pct": round(100 * low[m].mean(), 2) if m.sum() else None} for k, m in cells.items()}})

# B4 mean score, S6c
reviews = base[base["has_review"]].copy()
late_reviews = reviews[reviews["late"].eq(1) & reviews["delay_band"].notna()]
for timing in ("before arrival", "after arrival"):
    part = late_reviews[late_reviews["answer_timing"].eq(timing)]
    B4_ROWS.append({"scenario": "S6c", "plan_check": "S6", "label": "Mean score difference, in stars", "timing": timing, "bands": {}, "pairs": b4_pairs(part, "latest_review_score")})

# B1 under the remaining S3 alternatives
for scenario_id, label, function in (("S3b", "Only delivery-before-carrier excluded", sc.s3_drop_delivery_first), ("S3c", "Only carrier-before-purchase excluded", sc.s3_drop_carrier_first)):
    f = function(base.copy())
    y, peak = f["late"].to_numpy(float), f["peak"].to_numpy()
    OTHER_ROWS.append({"hypothesis": "B1", "scenario": scenario_id, "plan_check": "S3", "label": label, "contrast": "Peak vs other months late rate", "estimate": round(100 * (y[peak].mean() - y[~peak].mean()), 3), "ci": None,
                       "orders": len(f), "late": int(y.sum()), "late_share_in_peak_pct": round(100 * y[peak].sum() / y.sum(), 2), "order_share_in_peak_pct": round(100 * peak.mean(), 2)})

# S13 for B2
s = with_distance(base.copy())
s = s[s["customer_state"].isin(["RJ", "SP"])].copy()


def b2_columns(f):
    rj = f["customer_state"].eq("RJ").astype(float)
    return pd.DataFrame({"RJ": rj, "RJ x peak": rj * f["peak"].astype(float)}, index=f.index)


model = Logit("B2 S13", s, "late", ["distance_band", "purchase_month", "item_band"], ["log_order_value", "same_state_seller"], extra=b2_columns)
fit = sm.OLS(model.y, model.design).fit(cov_type="cluster", cov_kwds={"groups": model.codes})
names = list(fit.params.index)
for contrast, weights in (("Difference between the two gaps", {"RJ x peak": 1}), ("Gap in peak months", {"RJ": 1, "RJ x peak": 1}), ("Gap in other months", {"RJ": 1})):
    L = np.zeros(len(names))
    for name, value in weights.items():
        L[names.index(name)] = value
    est, se = float(L @ fit.params.to_numpy()), float(np.sqrt(L @ fit.cov_params().to_numpy() @ L))
    OTHER_ROWS.append({"hypothesis": "B2", "scenario": "S13a", "plan_check": "S13", "label": "Linear probability model", "contrast": contrast, "estimate": round(100 * est, 3), "ci": [round(100 * (est - Z * se), 3), round(100 * (est + Z * se), 3)], "orders": len(s), "late": int(s["late"].sum())})
robust = sm.GLM(model.y, model.design, family=sm.families.Binomial()).fit(cov_type="HC1")
flag = model.frame["peak"].to_numpy(bool)
rj = model.counterfactual({"RJ": 1.0, "RJ x peak": flag.astype(float)})
sp = model.counterfactual({"RJ": 0.0, "RJ x peak": 0.0})
beta, cov = robust.params.to_numpy(), robust.cov_params().to_numpy()
for contrast, mask in (("Gap in peak months", flag), ("Gap in other months", ~flag)):
    est, se, ci = delta_rd(beta, cov, rj, sp, mask)
    OTHER_ROWS.append({"hypothesis": "B2", "scenario": "S13b", "plan_check": "S13", "label": "Heteroskedasticity-robust errors, not clustered", "contrast": contrast, "estimate": round(est, 3), "ci": [round(x, 3) for x in ci], "orders": len(s), "late": int(s["late"].sum())})

# S13 for B5, within each carrier-date period
stage = with_distance(base.copy())
stage = stage[stage["stage_ok"]].copy()
for period, part in stage.groupby("carrier_period"):
    def hand(f):
        return pd.DataFrame({"late handover": f["seller_late"].eq("late handover").astype(float)}, index=f.index)

    model = Logit(f"B5 S13 {period}", part, "late", ["distance_band", "purchase_month", "state_group", "item_band"], ["log_order_value"], extra=hand)
    fit = sm.OLS(model.y, model.design).fit(cov_type="cluster", cov_kwds={"groups": model.codes})
    est, se = float(fit.params["late handover"]), float(fit.bse["late handover"])
    tag = "B5 before" if "before" in period else "B5 from"
    OTHER_ROWS.append({"hypothesis": tag, "scenario": "S13a", "plan_check": "S13", "label": "Linear probability model", "contrast": f"Late vs on-time handover, {period}", "estimate": round(100 * est, 3), "ci": [round(100 * (est - Z * se), 3), round(100 * (est + Z * se), 3)], "orders": len(part), "late": int(part["late"].sum())})
    robust = sm.GLM(model.y, model.design, family=sm.families.Binomial()).fit(cov_type="HC1")
    est, se, ci = delta_rd(robust.params.to_numpy(), robust.cov_params().to_numpy(), model.counterfactual({"late handover": 1.0}), model.counterfactual({"late handover": 0.0}))
    OTHER_ROWS.append({"hypothesis": tag, "scenario": "S13b", "plan_check": "S13", "label": "Heteroskedasticity-robust errors, not clustered", "contrast": f"Late vs on-time handover, {period}", "estimate": round(est, 3), "ci": [round(x, 3) for x in ci], "orders": len(part), "late": int(part["late"].sum())})

# S13 for the adjusted B4 models
late_reviews = reviews[reviews["late"].eq(1) & reviews["delay_band"].notna()].copy()
for timing, categorical, numeric, levels in (("before arrival", ["purchase_month", "state_group", "item_band", "category_group"], ["log_order_value"], DELAY_BANDS),
                                             ("after arrival", ["purchase_month", "state_group", "item_band"], ["log_order_value", "multi_seller"], DELAY_BANDS[:3])):
    part = late_reviews[late_reviews["answer_timing"].eq(timing) & late_reviews["delay_band"].isin(levels)].copy()
    contrasts = [(f"{a} vs {b}", a, b) for a, b in PAIRS if a in levels and b in levels]
    model, cluster = fit_spec(f"B4 {timing}", part, "low_rating", "delay_band", levels, levels[0], categorical, numeric, contrasts)
    for name, value in cluster.items():
        OTHER_ROWS.append({"hypothesis": "B4", "scenario": "S0", "plan_check": "baseline", "label": f"Adjusted, {timing}, clustered delta interval", "contrast": name, "estimate": round(value["estimate"], 3), "ci": [round(x, 3) for x in value["ci"]], "orders": len(part), "late": None})
    for name, value in fit_lpm(model, levels, levels[0], "delay_band", contrasts).items():
        OTHER_ROWS.append({"hypothesis": "B4", "scenario": "S13a", "plan_check": "S13", "label": f"Linear probability model, {timing}", "contrast": name, "estimate": round(value["estimate"], 3), "ci": [round(x, 3) for x in value["ci"]], "orders": len(part), "late": None})
    _, robust = fit_spec(f"B4 {timing} HC", part, "low_rating", "delay_band", levels, levels[0], categorical, numeric, contrasts, "HC1")
    for name, value in robust.items():
        OTHER_ROWS.append({"hypothesis": "B4", "scenario": "S13b", "plan_check": "S13", "label": f"Heteroskedasticity-robust errors, {timing}", "contrast": name, "estimate": round(value["estimate"], 3), "ci": [round(x, 3) for x in value["ci"]], "orders": len(part), "late": None})

NOT_APPLICABLE = [
    {"check": "S5a", "result": "A3", "reason": "Delay bands use whole days late, so orders delivered on the estimated date stay out of the bands. The timestamp definition can't change A3."},
    {"check": "S8a", "result": "B1 and B2", "reason": "These results compare peak with other months, so excluding peak months removes the comparison."},
    {"check": "S8c", "result": "B5 before 25 April 2018", "reason": "All these orders were purchased before July 2018, so the estimate is unchanged by construction."},
    {"check": "S6, S9, S12, S16", "result": "A1, A4, A5, A6, A7, B1, B2, B5", "reason": "These results don't use reviews."},
    {"check": "S13", "result": "A6, B1, B7", "reason": "These don't use a regression model."},
    {"check": "S7, S10", "result": "A2, A3, B3, B4, B6, B7", "reason": "These results don't use seller assignment or distance."},
]
output = {"b4": B4_ROWS, "b7": B7_ROWS, "other": OTHER_ROWS, "not_applicable": NOT_APPLICABLE}
(OUT / "sensitivity_supplement.json").write_text(json.dumps(output, indent=1, default=str), encoding="utf-8")
sc.timed("supplement done")
_ = (ss, TIMING, diagnostics)
