"""Shared definitions for the sensitivity analyses: scenarios, model specifications and result recording.

Primary Class A and Class B results and definitions aren't changed. Sensitivity runs use standard
errors clustered by seller, with a delta-method interval for standardised risk differences, as
approved in the plan. Larger bootstraps cover A5, A6 and A7. Every run is written out, including
failed or contradictory ones. Results are observational.

Imported by sensitivity.py and sensitivity_supplement.py. Reads no database.
"""
import json
import pathlib
import sys
import time

import numpy as np
import pandas as pd
import scipy.stats as ss
import statsmodels.api as sm
from scipy.special import expit

from modeling import BOUNDARY, DELAY_BANDS, MIN_ORDERS, OUT, ROOT, SEED, Logit, interval, load_orders, risk

RAW = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "raw"
LARGE = int(sys.argv[2]) if len(sys.argv) > 2 else 2000
DISTANCE_BANDS = ["0-100 km", "100-300 km", "300-600 km", "600-1,000 km", "1,000-2,000 km", "2,000+ km"]
QUARTILES = ["Q1 lowest", "Q2", "Q3", "Q4 highest"]
TIMING = ["on time", "late, answered before arrival", "late, answered after arrival"]
PEAK = {"2017-11", "2018-02", "2018-03"}
CRITERIA = {"A1": 2.0, "A2": 5.0, "A3": 5.0, "A4": 2.0, "A5": 2.0, "A6": 10.0, "A7": 5.0,
            "B2": 2.0, "B3 before": 5.0, "B3 after": 5.0, "B5 before": 2.0, "B5 from": 2.0, "B6": 5.0, "B1": 2.0}
Z = 1.959964
started = time.time()
rows, failures_log = [], []
seed_root = np.random.SeedSequence([SEED, 7])
seeds = iter(seed_root.spawn(40))


def timed(label):
    print(f"[{time.strftime('%H:%M:%S')} +{(time.time() - started) / 60:.1f}m] {label}", flush=True)


def haversine(lat1, lng1, lat2, lng2):
    lat1, lng1, lat2, lng2 = map(np.radians, (lat1, lng1, lat2, lng2))
    h = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lng2 - lng1) / 2) ** 2
    return 6371.0088 * 2 * np.arcsin(np.sqrt(h))


def band_distance(series):
    return pd.cut(series, [-0.001, 100, 300, 600, 1000, 2000, np.inf], labels=DISTANCE_BANDS, right=False).astype(object)


# ---------------------------------------------------------------- base table
base = load_orders()
extra = pd.read_csv(OUT / "orders_analysis.csv", keep_default_na=False, na_values=[""], dtype={"customer_zip_code_prefix": str, "primary_seller_zip_prefix": str},
                    usecols=["order_id", "customer_zip_code_prefix", "primary_seller_zip_prefix", "first_item_category", "review_count", "earliest_review_score", "earliest_review_created_ts",
                             "earliest_review_answered_ts", "latest_review_id_rows", "earliest_review_id_rows"],
                    parse_dates=["earliest_review_created_ts", "earliest_review_answered_ts"])
base = base.merge(extra, on="order_id", how="left", validate="one_to_one")
base["first_item_category"] = base["first_item_category"].fillna("unknown").replace("", "unknown")
base["answered_ts"] = base["latest_review_answered_ts"]
base["created_ts"] = base["latest_review_created_ts"]
base["stage_ok"] = base["valid"]
base["peak"] = base["purchase_month"].isin(PEAK)
named = base.loc[base["primary_category"].ne("unknown"), "primary_category"].value_counts()
CATEGORY_LEVELS = sorted(named[named.ge(1000)].index)
positions = pd.read_csv(OUT / "zip_positions.csv", dtype={"zip_prefix": str}).set_index("zip_prefix")


def refresh_reviews(frame):
    """Rebuilds review-derived fields after a scenario changes them."""
    has = frame["has_review"]
    frame["low_rating"] = np.where(has, frame["latest_review_score"].le(2).astype(float), np.nan)
    before = frame["answered_ts"] < frame["delivered_ts"]
    frame["answer_timing"] = np.where(has, np.where(before, "before arrival", "after arrival"), None)
    timing = np.where(frame["late"].eq(0), TIMING[0], np.where(before, TIMING[1], TIMING[2]))
    frame["delivery_timing"] = pd.Series(timing, index=frame.index).where(has, None)
    return frame


# ---------------------------------------------------------------- scenarios: each returns a changed copy
def s_primary(f):
    return f


def s1_earliest(f):
    f["latest_review_score"] = f["earliest_review_score"]
    f["answered_ts"] = f["earliest_review_answered_ts"]
    f["created_ts"] = f["earliest_review_created_ts"]
    return refresh_reviews(f)


def s1_single_review(f):
    f["has_review"] = f["has_review"] & f["review_count"].eq(1)
    return refresh_reviews(f)


def s2_no_repeated(f):
    f["has_review"] = f["has_review"] & f["latest_review_id_rows"].eq(1)
    return refresh_reviews(f)


def s3_drop_all(f):
    return f[f["valid"]].copy()


def s3_drop_delivery_first(f):
    keep = ~(f["delivered_ts"] < f["carrier_ts"])
    f = f[keep].copy()
    f["stage_ok"] = f["carrier_ts"].notna() & (f["delivered_ts"] >= f["carrier_ts"])
    return f


def s3_drop_carrier_first(f):
    keep = ~(f["carrier_ts"] < f["purchase_ts"])
    f = f[keep].copy()
    f["stage_ok"] = f["carrier_ts"].notna() & (f["carrier_ts"] >= f["purchase_ts"])
    return f


orders_raw = pd.read_csv(RAW / "olist_orders_dataset.csv", usecols=["order_id", "order_purchase_timestamp"], parse_dates=["order_purchase_timestamp"]).set_index("order_id")
reviews_raw = pd.read_csv(RAW / "olist_order_reviews_dataset.csv", usecols=["review_id", "order_id", "review_creation_date", "review_answer_timestamp"], parse_dates=["review_creation_date", "review_answer_timestamp"])
csv_latest = reviews_raw.sort_values(["review_answer_timestamp", "review_creation_date", "review_id"], ascending=False).drop_duplicates("order_id").set_index("order_id")["review_answer_timestamp"]


def s4_csv_values(f):
    f["purchase_ts"] = f["order_id"].map(orders_raw["order_purchase_timestamp"])
    answered = f["order_id"].map(csv_latest)
    f["answered_ts"] = answered.where(f["has_review"], f["answered_ts"])
    f["handover_days"] = (f["carrier_ts"] - f["purchase_ts"]).dt.total_seconds() / 86400
    return refresh_reviews(f)


affected_ids = set(base.loc[base["order_id"].map(orders_raw["order_purchase_timestamp"]).ne(base["purchase_ts"]), "order_id"])
answer_diff = base["has_review"] & base["order_id"].map(csv_latest).ne(base["latest_review_answered_ts"])
affected_ids |= set(base.loc[answer_diff, "order_id"])


def s4_exclude(f):
    return f[~f["order_id"].isin(affected_ids)].copy()


def s5_timestamp(f):
    f["late"] = (f["delivered_ts"] > f["estimated_ts"]).astype(int)
    return refresh_reviews(f)


def s5_two_days(f):
    f["late"] = f["days_late"].ge(2).astype(int)
    f["delay_band"] = f["delay_band"].where(f["days_late"].ge(2), None)
    return refresh_reviews(f)


def s7_primary_seller(f):
    c = positions.reindex(f["customer_zip_code_prefix"])
    s = positions.reindex(f["primary_seller_zip_prefix"])
    f["distance_km"] = haversine(c["median_lat"].to_numpy(), c["median_lng"].to_numpy(), s["median_lat"].to_numpy(), s["median_lng"].to_numpy())
    f["distance_band"] = band_distance(f["distance_km"])
    f["single_seller"] = True
    return f


def s8_no_peak(f):
    return f[~f["peak"]].copy()


def s8_no_2016(f):
    return f[f["purchase_month"] >= "2017-01"].copy()


def s8_before_july(f):
    return f[f["purchase_month"] < "2018-07"].copy()


def s9_survey_date(f):
    before = f["created_ts"].dt.normalize() < f["delivered_ts"].dt.normalize()
    has = f["has_review"]
    f["answer_timing"] = np.where(has, np.where(before, "before arrival", "after arrival"), None)
    timing = np.where(f["late"].eq(0), TIMING[0], np.where(before, TIMING[1], TIMING[2]))
    f["delivery_timing"] = pd.Series(timing, index=f.index).where(has, None)
    return f


def s10_mean_position(f):
    c = positions.reindex(f["customer_zip_code_prefix"])
    s = positions.reindex(f["primary_seller_zip_prefix"])
    distance = haversine(c["mean_lat"].to_numpy(), c["mean_lng"].to_numpy(), s["mean_lat"].to_numpy(), s["mean_lng"].to_numpy())
    f["distance_km"] = np.where(f["single_seller"], distance, np.nan)
    f["distance_band"] = band_distance(f["distance_km"])
    return f


EXTREME_KM = float(base.loc[base["distance_km"].notna(), "distance_km"].quantile(0.99))


def s10_no_extreme(f):
    return f[~(f["distance_km"] > EXTREME_KM)].copy()


def s11_first_item(f):
    f["primary_category"] = f["first_item_category"]
    named_first = f.loc[f["first_item_category"].ne("unknown"), "first_item_category"].value_counts()
    top = set(named_first.head(15).index)
    f["category_group"] = np.where(f["first_item_category"].eq("unknown"), "unknown", np.where(f["first_item_category"].isin(top), f["first_item_category"], "other"))
    return f


def s11_no_unknown(f):
    return f[f["primary_category"].ne("unknown")].copy()


def s12_bound(late_low, on_time_low):
    def apply(f):
        missing = ~f["has_review"]
        value = np.where(f["late"].eq(1), float(late_low), float(on_time_low))
        f["low_rating"] = np.where(missing, value, f["low_rating"])
        f["latest_review_score"] = np.where(missing, np.where(value == 1, 1.0, 5.0), f["latest_review_score"])
        f["has_review"] = True
        return f
    return apply


def s15_no_long(f):
    return f[~(f["delivery_days"] > 60)].copy()


def s16_no_early_review(f):
    f["has_review"] = f["has_review"] & ~(f["created_ts"].dt.normalize() < f["purchase_ts"].dt.normalize())
    return refresh_reviews(f)


A_LATE = ["A1", "A4", "A5", "A7"]
A_REVIEW = ["A2", "A3"]
B_LATE = ["B2", "B5"]
B_REVIEW = ["B3", "B6"]
SCENARIOS = [
    ("S1a", "S1", "review", "Earliest review", s1_earliest, A_REVIEW + B_REVIEW),
    ("S1b", "S1", "review", "Excluding orders with several reviews", s1_single_review, A_REVIEW + B_REVIEW),
    ("S2", "S2", "review", "Excluding repeated review IDs", s2_no_repeated, A_REVIEW + B_REVIEW),
    ("S3a", "S3", "timestamp", "All flagged orders excluded", s3_drop_all, A_LATE + ["A6"] + B_LATE),
    ("S3b", "S3", "timestamp", "Only delivery-before-carrier excluded", s3_drop_delivery_first, A_LATE + ["A6"] + B_LATE),
    ("S3c", "S3", "timestamp", "Only carrier-before-purchase excluded", s3_drop_carrier_first, A_LATE + ["A6"] + B_LATE),
    ("S4a", "S4", "timestamp", "Source CSV timestamps", s4_csv_values, ["B3", "B5", "B6"]),
    ("S4b", "S4", "timestamp", "Affected orders excluded", s4_exclude, A_LATE + A_REVIEW + ["A6", "B3", "B5", "B6"]),
    ("S5a", "S5", "different", "Full timestamp, previous logic", s5_timestamp, A_LATE + ["A2", "A6", "B2", "B3", "B5", "B6"]),
    ("S5b", "S5", "different", "2 or more days late", s5_two_days, A_LATE + A_REVIEW + ["A6", "B2", "B3", "B5", "B6"]),
    ("S7", "S7", "structure", "Multi-seller orders assigned to primary seller", s7_primary_seller, ["A1", "A4", "A5", "A6", "B5"]),
    ("S8a", "S8", "different", "Excluding peak months", s8_no_peak, A_LATE + A_REVIEW + ["A6", "B3", "B5", "B6"]),
    ("S8b", "S8", "different", "Excluding 2016", s8_no_2016, A_LATE + A_REVIEW + ["A6", "B2", "B3", "B5", "B6"]),
    ("S8c", "S8", "different", "Excluding purchases from July 2018", s8_before_july, A_LATE + A_REVIEW + ["A6", "B2", "B3", "B5", "B6"]),
    ("S9", "S9", "different", "Survey creation date instead of answer timestamp", s9_survey_date, ["B3", "B6"]),
    ("S10a", "S10", "structure", "Mean ZIP position", s10_mean_position, ["A1", "A4", "A5"]),
    ("S10b", "S10", "structure", f"Excluding distances above the 99th percentile ({EXTREME_KM:,.0f} km)", s10_no_extreme, ["A1", "A4", "A5"]),
    ("S11a", "S11", "structure", "First item's category", s11_first_item, ["A2", "A7"]),
    ("S11b", "S11", "structure", "Excluding unknown category", s11_no_unknown, ["A2", "A7"]),
    ("S12a", "S12", "review", "Unreviewed: late all low, on time none low", s12_bound(1, 0), ["A2"]),
    ("S12b", "S12", "review", "Unreviewed: late none low, on time all low", s12_bound(0, 1), ["A2"]),
    ("S12c", "S12", "review", "Unreviewed late orders all low", s12_bound(1, 0), ["A3"]),
    ("S12d", "S12", "review", "Unreviewed late orders none low", s12_bound(0, 0), ["A3"]),
    ("S15", "S15", "timestamp", "Excluding deliveries over 60 days", s15_no_long, A_LATE + A_REVIEW + ["A6", "B2", "B3", "B5", "B6"]),
    ("S16", "S16", "review", "Excluding reviews created before the purchase date", s16_no_early_review, A_REVIEW + B_REVIEW),
]


# ---------------------------------------------------------------- estimation
def diagnostics(model):
    r = model.report
    return {"orders": r["orders"], "events": r["events"], "terms": r["parameters"], "sellers": r["sellers"], "events_per_term": r["events_per_parameter"], "non_events_per_term": r["non_events_per_parameter"],
            "converged": r["converged"], "iterations": r["iterations"], "largest_coefficient": r["largest_abs_coefficient"], "largest_se": r["largest_standard_error"], "condition": r["condition_number"],
            "thin_terms": list(r["thin_terms"].keys()), "still_sparse": r["levels_still_sparse_after_merging"], "merged_levels": r["merged_levels"]}


def delta_rd(beta, cov, Xa, Xb, mask=None):
    """Standardised risk difference in points, with a delta-method interval."""
    keep = np.ones(len(Xa), bool) if mask is None else mask
    pa, pb = expit(Xa[keep] @ beta), expit(Xb[keep] @ beta)
    grad = ((pa * (1 - pa))[:, None] * Xa[keep] - (pb * (1 - pb))[:, None] * Xb[keep]).mean(axis=0)
    est = pa.mean() - pb.mean()
    se = np.sqrt(grad @ cov @ grad)
    return 100 * float(est), 100 * float(se), [100 * float(est - Z * se), 100 * float(est + Z * se)]


def categorical_exposure(frame, column, levels, reference):
    def extra_columns(f):
        return pd.DataFrame({f"{column}={v}": f[column].eq(v).astype(float) for v in levels if v != reference}, index=f.index)
    return extra_columns


def fit_spec(tag, frame, outcome, exposure, levels, reference, categorical, numeric, contrasts, cov_type="cluster"):
    """Fits one logistic model, returning each requested contrast. Failures are reported, not hidden."""
    try:
        model = Logit(tag, frame, outcome, categorical, numeric, extra=categorical_exposure(frame, exposure, levels, reference))
    except Exception as error:  # reported as a failed run, never dropped silently
        failures_log.append({"run": tag, "error": repr(error)[:200]})
        return None, {name: None for name, _, _ in contrasts}
    columns = {v: f"{exposure}={v}" for v in levels if v != reference}
    worlds = {}
    for level in levels:
        worlds[level] = model.counterfactual({c: (1.0 if v == level else 0.0) for v, c in columns.items()})
    if cov_type == "cluster":
        beta, cov = model.wald.params.to_numpy(), model.wald.cov_params().to_numpy()
        pvals = model.wald
    else:
        robust = sm.GLM(model.y, model.design, family=sm.families.Binomial()).fit(cov_type=cov_type)
        beta, cov = robust.params.to_numpy(), robust.cov_params().to_numpy()
        pvals = robust
    out = {}
    names = list(model.design.columns)
    for name, a, b in contrasts:
        est, se, ci = delta_rd(beta, cov, worlds[a], worlds[b])
        out[name] = {"estimate": est, "se": se, "ci": ci, "p": float(2 * ss.norm.sf(abs(est / se))) if se > 0 else None}
    return model, out


def fit_lpm(model, levels, reference, exposure, contrasts):
    fit = sm.OLS(model.y, model.design).fit(cov_type="cluster", cov_kwds={"groups": model.codes})
    out = {}
    for name, a, b in contrasts:
        L = np.zeros(len(fit.params))
        if a != reference:
            L[list(fit.params.index).index(f"{exposure}={a}")] = 1
        if b != reference:
            L[list(fit.params.index).index(f"{exposure}={b}")] = -1
        est = float(L @ fit.params.to_numpy())
        se = float(np.sqrt(L @ fit.cov_params().to_numpy() @ L))
        out[name] = {"estimate": 100 * est, "se": 100 * se, "ci": [100 * (est - Z * se), 100 * (est + Z * se)], "p": float(2 * ss.norm.sf(abs(est / se)))}
    return out


def with_distance(f):
    return f[f["single_seller"] & f["distance_km"].notna()].copy()


def reviewed(f):
    return f[f["has_review"]].copy()


def spec_a1(f):
    s = with_distance(f)
    s = s[s["customer_state"].isin(["RJ", "SP"])].copy()
    return s, "late", "customer_state", ["SP", "RJ"], "SP", ["distance_band", "purchase_month", "item_band"], ["log_order_value", "same_state_seller"], [("RJ vs SP", "RJ", "SP")]


def spec_a4(f):
    s = with_distance(f)
    levels = [b for b in DISTANCE_BANDS if b in set(s["distance_band"])]
    return s, "late", "distance_band", levels, "0-100 km", ["purchase_month", "state_group", "item_band"], ["log_order_value"], [("600-1,000 vs 0-100 km", "600-1,000 km", "0-100 km"), ("2,000+ vs 0-100 km", "2,000+ km", "0-100 km")] if "2,000+ km" in levels else [("600-1,000 vs 0-100 km", "600-1,000 km", "0-100 km")]


def spec_a5(f, add_state=False):
    s = with_distance(f)
    s["freight_quartile"] = pd.qcut(s["freight_value"], 4, labels=QUARTILES).astype(object)
    categorical = ["distance_band", "purchase_month", "item_band"] + (["state_group"] if add_state else [])
    return s, "late", "freight_quartile", QUARTILES, QUARTILES[0], categorical, ["log_order_value"], [("Highest vs lowest quartile", QUARTILES[3], QUARTILES[0])]


def spec_a2(f):
    s = reviewed(f)
    s["status"] = np.where(s["late"].eq(1), "late", "on time")
    return s, "low_rating", "status", ["on time", "late"], "on time", ["purchase_month", "state_group", "item_band", "category_group"], ["log_order_value", "multi_seller"], [("Late vs on time", "late", "on time")]


def spec_a3(f):
    s = reviewed(f)
    s = s[s["late"].eq(1) & s["delay_band"].notna()].copy()
    contrasts = [("15+ vs 1-3 days", "15+ days", "1-3 days"), ("4-7 vs 1-3 days", "4-7 days", "1-3 days"), ("8-14 vs 4-7 days", "8-14 days", "4-7 days"), ("15+ vs 8-14 days", "15+ days", "8-14 days")]
    return s, "low_rating", "delay_band", DELAY_BANDS, "1-3 days", ["purchase_month", "state_group", "item_band", "category_group"], ["log_order_value", "multi_seller"], contrasts


def spec_b3(f):
    s = reviewed(f)
    return s, "low_rating", "delivery_timing", TIMING, TIMING[0], ["purchase_month", "state_group", "item_band", "category_group"], ["log_order_value", "multi_seller"], [("B3 before", TIMING[1], TIMING[0]), ("B3 after", TIMING[2], TIMING[0])]


def spec_b6(f):
    s = reviewed(f)
    return s, "low_rating", "multi_item", ["single item", "multi-item"], "single item", ["purchase_month", "state_group", "category_group", "delivery_timing"], ["log_order_value", "multi_seller"], [("B6", "multi-item", "single item")]


SPECS = {"A1": spec_a1, "A2": spec_a2, "A3": spec_a3, "A4": spec_a4, "A5": spec_a5, "B3": spec_b3, "B6": spec_b6}


def record(hypothesis, scenario_id, plan_id, group, label, contrast, value, model, note=""):
    rows.append({"hypothesis": hypothesis, "scenario": scenario_id, "plan_check": plan_id, "group": group, "label": label, "contrast": contrast,
                 "estimate": None if value is None else round(value["estimate"], 3), "ci": None if value is None else [round(x, 3) for x in value["ci"]], "p": None if value is None else value.get("p"),
                 "diagnostics": None if model is None else diagnostics(model), "note": note, "failed": value is None})


def run_spec(hypothesis, frame, scenario_id, plan_id, group, label, cov_type="cluster", note=""):
    s, outcome, exposure, levels, reference, categorical, numeric, contrasts = SPECS[hypothesis](frame)
    model, out = fit_spec(f"{hypothesis} {scenario_id}", s, outcome, exposure, levels, reference, categorical, numeric, contrasts, cov_type)
    for name, value in out.items():
        record(hypothesis, scenario_id, plan_id, group, label, name, value, model, note)
    return model, s, (outcome, exposure, levels, reference, contrasts)


def spec_a7_run(frame, scenario_id, plan_id, group, label, cov_type="cluster", note="", lpm=False):
    s = with_distance(frame)
    counts = s.loc[s["primary_category"].ne("unknown"), "primary_category"]
    levels_all = base.loc[base["primary_category"].ne("unknown"), "primary_category"].value_counts() if frame["primary_category"].equals(base.reindex(frame.index)["primary_category"]) else frame.loc[frame["primary_category"].ne("unknown"), "primary_category"].value_counts()
    levels = sorted(levels_all[levels_all.ge(1000)].index)
    s = s[s["primary_category"].isin(levels)].copy()
    biggest = s["primary_category"].value_counts().idxmax()
    model = Logit(f"A7 {scenario_id}", s, "late", ["purchase_month", "state_group", "distance_band"], [], extra=categorical_exposure(s, "primary_category", levels, biggest))
    columns = {v: f"primary_category={v}" for v in levels if v != biggest}
    worlds = {v: model.counterfactual({c: (1.0 if k == v else 0.0) for k, c in columns.items()}) for v in levels}
    beta = model.wald.params.to_numpy()
    cov = model.wald.cov_params().to_numpy() if cov_type == "cluster" else sm.GLM(model.y, model.design, family=sm.families.Binomial()).fit(cov_type=cov_type).cov_params().to_numpy()
    if lpm:
        fit = sm.OLS(model.y, model.design).fit(cov_type="cluster", cov_kwds={"groups": model.codes})
        values = {v: 0.0 if v == biggest else 100 * float(fit.params[f"primary_category={v}"]) for v in levels}
        high, low = max(values, key=values.get), min(values, key=values.get)
        value = {"estimate": values[high] - values[low], "ci": [values[high] - values[low], values[high] - values[low]], "p": None}
        record("A7", scenario_id, plan_id, group, label, f"Spread: {high} vs {low}", value, model, "Point estimate only; no interval for the selected pair")
        return model
    rates = {v: risk(beta, worlds[v]) for v in levels}
    high, low = max(rates, key=rates.get), min(rates, key=rates.get)
    est, se, ci = delta_rd(beta, cov, worlds[high], worlds[low])
    terms = [i for i, name in enumerate(model.design.columns) if name.startswith("primary_category=")]
    b, V = beta[terms], cov[np.ix_(terms, terms)]
    p = float(ss.chi2.sf(float(b @ np.linalg.solve(V, b)), len(terms)))
    record("A7", scenario_id, plan_id, group, label, f"Spread: {high} vs {low}", {"estimate": est, "ci": ci, "p": p}, model, "Interval ignores selection of the extreme pair; p is the joint test " + note)
    return model


def concentration(orders, late, count):
    order = np.lexsort((np.arange(len(late)), -late))[:count]
    return 100 * (late[order].sum() / late.sum() - orders[order].sum() / orders.sum())


def a6_stats(frame, seed, replicates=500, simulations=1000):
    single = frame[frame["single_seller"]].copy()
    month_rate = single.groupby("purchase_month")["late"].mean()
    single["expected"] = single["purchase_month"].map(month_rate)
    single["variance"] = single["expected"] * (1 - single["expected"])
    table = single.groupby("primary_seller_id").agg(orders=("late", "size"), late=("late", "sum"), expected=("expected", "sum"), variance=("variance", "sum"))
    eligible = table[table["orders"].ge(100)].sort_index()
    count = int(np.ceil(0.10 * len(eligible)))
    n, y = eligible["orders"].to_numpy(float), eligible["late"].to_numpy(float)
    gap = concentration(n, y, count)
    rng = np.random.default_rng(seed)
    boot = [concentration(n[p], y[p], count) for p in (rng.integers(0, len(eligible), len(eligible)) for _ in range(replicates))]
    subset = single[single["primary_seller_id"].isin(eligible.index)]
    grid = subset.groupby(["primary_seller_id", "purchase_month"]).size().rename("n").reset_index()
    grid["p"] = grid["purchase_month"].map(month_rate)
    grid["code"] = pd.Categorical(grid["primary_seller_id"], categories=eligible.index).codes
    null = np.empty(simulations)
    for i in range(simulations):
        draws = rng.binomial(grid["n"].to_numpy(), grid["p"].to_numpy())
        null[i] = concentration(n, np.bincount(grid["code"].to_numpy(), weights=draws, minlength=len(eligible)), count)
    codes = pd.Categorical(subset["primary_seller_id"], categories=eligible.index).codes
    late_values = subset["late"].to_numpy(float)
    splits = []
    for _ in range(100):
        half = rng.random(len(late_values)) < 0.5
        first = np.bincount(codes[half], weights=late_values[half], minlength=len(eligible))
        second = np.bincount(codes[~half], weights=late_values[~half], minlength=len(eligible))
        second_n = np.bincount(codes[~half], minlength=len(eligible)).astype(float)
        chosen = np.lexsort((np.arange(len(eligible)), -first))[:count]
        splits.append(100 * (second[chosen].sum() / second.sum() - second_n[chosen].sum() / second_n.sum()))
    z = (eligible["late"] - eligible["expected"]) / np.sqrt(eligible["variance"])
    return {"estimate": gap, "ci": interval(boot), "p": float((1 + np.sum(null >= gap)) / (simulations + 1)), "sellers": len(eligible), "top": count, "orders": int(n.sum()), "late": int(y.sum()),
            "null_mean": round(float(null.mean()), 2), "split_half": round(float(np.mean(splits)), 2), "above_funnel": int((z > 3.09).sum()), "below_funnel": int((z < -3.09).sum())}


def run_a6(frame, scenario_id, plan_id, group, label, note=""):
    r = a6_stats(frame, next(seeds))
    rows.append({"hypothesis": "A6", "scenario": scenario_id, "plan_check": plan_id, "group": group, "label": label, "contrast": "Top 10% late share minus order share",
                 "estimate": round(r["estimate"], 3), "ci": [round(x, 3) for x in r["ci"]], "p": r["p"], "diagnostics": {k: r[k] for k in ("sellers", "top", "orders", "late", "null_mean", "split_half", "above_funnel", "below_funnel")}, "note": note, "failed": False})


def b2_run(frame, scenario_id, plan_id, group, label):
    s = with_distance(frame)
    s = s[s["customer_state"].isin(["RJ", "SP"])].copy()

    def cols(f):
        rj = f["customer_state"].eq("RJ").astype(float)
        return pd.DataFrame({"RJ": rj, "RJ x peak": rj * f["peak"].astype(float)}, index=f.index)

    model = Logit(f"B2 {scenario_id}", s, "late", ["distance_band", "purchase_month", "item_band"], ["log_order_value", "same_state_seller"], extra=cols)
    flag = model.frame["peak"].to_numpy(bool)
    rj = model.counterfactual({"RJ": 1.0, "RJ x peak": flag.astype(float)})
    sp = model.counterfactual({"RJ": 0.0, "RJ x peak": 0.0})
    beta, cov = model.wald.params.to_numpy(), model.wald.cov_params().to_numpy()
    p_est, _, p_ci = delta_rd(beta, cov, rj, sp, flag)
    o_est, _, o_ci = delta_rd(beta, cov, rj, sp, ~flag)
    pa, pb, oa, ob = expit(rj[flag] @ beta), expit(sp[flag] @ beta), expit(rj[~flag] @ beta), expit(sp[~flag] @ beta)
    g = ((pa * (1 - pa))[:, None] * rj[flag] - (pb * (1 - pb))[:, None] * sp[flag]).mean(axis=0) - ((oa * (1 - oa))[:, None] * rj[~flag] - (ob * (1 - ob))[:, None] * sp[~flag]).mean(axis=0)
    se = 100 * np.sqrt(g @ cov @ g)
    est = p_est - o_est
    record("B2", scenario_id, plan_id, group, label, "Difference between the two gaps", {"estimate": est, "ci": [est - Z * se, est + Z * se], "p": float(2 * ss.norm.sf(abs(est / se)))}, model)
    record("B2", scenario_id, plan_id, group, label, "Gap in peak months", {"estimate": p_est, "ci": p_ci, "p": None}, model)
    record("B2", scenario_id, plan_id, group, label, "Gap in other months", {"estimate": o_est, "ci": o_ci, "p": None}, model)


def b5_run(frame, scenario_id, plan_id, group, label, period_column="carrier_period", periods=None, note=""):
    s = with_distance(frame)
    s = s[s["stage_ok"]].copy()
    s["seller_late"] = np.where(s["carrier_ts"] > s["latest_shipping_limit_ts"], "late handover", "on-time handover")
    for period, part in s.groupby(period_column):
        if periods and period not in periods:
            continue
        tag = "B5 before" if ("before" in str(period).lower()) else ("B5 from" if ("from" in str(period).lower()) else "B5 pooled")

        def cols(f):
            return pd.DataFrame({"late handover": f["seller_late"].eq("late handover").astype(float)}, index=f.index)

        model = Logit(f"{tag} {scenario_id}", part, "late", ["distance_band", "purchase_month", "state_group", "item_band"], ["log_order_value"], extra=cols)
        yes, no = model.counterfactual({"late handover": 1.0}), model.counterfactual({"late handover": 0.0})
        beta, cov = model.wald.params.to_numpy(), model.wald.cov_params().to_numpy()
        est, se, ci = delta_rd(beta, cov, yes, no)
        record(tag, scenario_id, plan_id, group, label, f"Late vs on-time handover, {period}", {"estimate": est, "ci": ci, "p": float(2 * ss.norm.sf(abs(est / se)))}, model, note)


def unadjusted_b(frame, scenario_id, group, label):
    """B1, B4 and B7 are descriptive, so they're recalculated directly."""
    late = frame["late"].to_numpy(float)
    if scenario_id in {"S0", "S3a", "S4b", "S5a", "S5b", "S8b", "S8c", "S15"}:
        peak = frame["peak"].to_numpy()
        if peak.sum() and (~peak).sum():
            est = 100 * (late[peak].mean() - late[~peak].mean())
            rows.append({"hypothesis": "B1", "scenario": scenario_id, "plan_check": scenario_id[:3].rstrip("abcd"), "group": group, "label": label, "contrast": "Peak vs other months late rate",
                         "estimate": round(est, 3), "ci": None, "p": None, "diagnostics": {"orders": len(frame), "late": int(late.sum()), "late_share_in_peak_pct": round(100 * late[peak].sum() / late.sum(), 2), "order_share_in_peak_pct": round(100 * peak.mean(), 2)}, "note": "Unadjusted, no interval", "failed": False})


