"""Step 8: compares the independent recomputation with the project's stored outputs and documents.

Unlike independent_recompute.py, this file does read project outputs, because comparing is its job.
It calculates no new statistics apart from re-deriving labels and summary counts from stored rows.

Usage: python python/audit/compare_with_stored.py <independent-orders-csv> <clean-load-export-folder> <raw-csv-folder> <output-json>
"""
import json
import pathlib
import sys

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "processed"
ORDERS, CLEAN, RAW, TARGET = map(pathlib.Path, sys.argv[1:5])
I = json.loads((OUT / "independent_audit_results.json").read_text(encoding="utf-8"))
A = json.loads((OUT / "class_a_results.json").read_text(encoding="utf-8"))["results"]
Bfull = json.loads((OUT / "class_b_results.json").read_text(encoding="utf-8"))
B = Bfull["results"]
S = json.loads((OUT / "sensitivity_results.json").read_text(encoding="utf-8"))
report = {}
assert I["bootstrap_replicates"] == 500, "results file is not the 500-replicate run"

# ---------------------------------------------------------------- 1. Order-level comparison
mine = pd.read_csv(ORDERS, keep_default_na=False, na_values=[""], dtype={"seller": str})
stored = pd.read_csv(OUT / "analysis_orders.csv", keep_default_na=False, na_values=[""], dtype={"primary_seller_id": str})
export = pd.read_csv(OUT / "orders_analysis.csv", keep_default_na=False, na_values=[""], usecols=["order_id", "latest_review_answered_ts", "latest_review_created_ts", "earliest_review_score", "latest_shipping_limit_ts"])
m = mine.merge(stored, left_on="id", right_on="order_id", how="outer", indicator=True, validate="one_to_one").merge(export, on="order_id", how="left")
norm_band = {"0-100 km": "0-100", "100-300 km": "100-300", "300-600 km": "300-600", "600-1,000 km": "600-1000", "1,000-2,000 km": "1000-2000", "2,000+ km": "2000+"}
norm_delay = {"1-3 days": "1-3", "4-7 days": "4-7", "8-14 days": "8-14", "15+ days": "15+"}


def differs(a, b):
    return int(((a != b) & ~(a.isna() & b.isna())).sum())


handover_stored = np.where(pd.to_datetime(m["carrier_ts"]) > pd.to_datetime(m["latest_shipping_limit_ts"]), "late", "ontime")
rows = {
    "orders_only_on_one_side": int((m["_merge"] != "both").sum()), "state": differs(m["state"], m["customer_state"]), "primary_seller": differs(m["seller"], m["primary_seller_id"]), "seller_state": differs(m["seller_state"], m["primary_seller_state"]),
    "month": differs(m["month"], m["purchase_month"]), "late": differs(m["late_x"], m["late_y"]), "days_late": differs(m["days_late_x"], m["days_late_y"]), "delay_band": differs(m["delay"], m["delay_band"].map(norm_delay)),
    "items": differs(m["n"], m["items_count"]), "sales_over_0.005": int((np.abs(m["sales"] - m["product_sales"]) > 0.005).sum()), "freight_over_0.005": int((np.abs(m["freight"] - m["freight_value"]) > 0.005).sum()),
    "multi_seller": differs(m["multi_seller_x"].astype(float), m["multi_seller_y"].astype(float)), "same_state": differs(m["same_state"].astype(float), m["same_state_seller"].astype(float)), "single_seller": differs(m["single"].astype(bool), m["single_seller"].astype(bool)),
    "distance_present": differs(m["distance"].notna(), m["distance_km"].notna()), "distance_band": differs(m["band"], m["distance_band"].map(norm_band)), "distance_largest_km_difference": float(np.nanmax(np.abs(m["distance"] - m["distance_km"]))),
    "category": differs(m["category"], m["primary_category"]), "category_group": differs(m["category_group_x"], m["category_group_y"]), "state_group": differs(m["state_group_x"], m["state_group_y"]), "valid": differs(m["valid_x"].astype(bool), m["valid_y"].astype(bool)),
    "score_latest": differs(m["score"].astype(float), m["latest_review_score"].astype(float)), "score_earliest": differs(m["score_first"].astype(float), m["earliest_review_score"].astype(float)),
    "answered_ts": differs(m["answered"], m["latest_review_answered_ts"]), "created_ts": differs(m["created"], m["latest_review_created_ts"]), "purchase_ts": differs(m["p"], m["purchase_ts"]), "handover_on_valid": int(((m["handover"] != handover_stored) & m["valid_x"].astype(bool)).sum()),
}
answered_gap = (pd.to_datetime(m["latest_review_answered_ts"]) - pd.to_datetime(m["answered"])).dt.total_seconds() / 60
rows["answered_ts_differences_minutes"] = answered_gap[answered_gap.fillna(0) != 0].round(0).value_counts().to_dict()
has_review = m["latest_review_answered_ts"].notna()
stored_before = pd.to_datetime(m["latest_review_answered_ts"]) < pd.to_datetime(m["delivered_ts"])
rows["answer_timing_changed_by_shift"] = int((has_review & (stored_before != m["timing"].eq("before"))).sum())
report["order_level"] = rows

# Documented counts, from the independent table and the raw files
valid = mine["valid"].astype(bool)
flagged = mine[~valid]
days = (pd.to_datetime(mine["d"]).dt.normalize() - pd.to_datetime(mine["p"]).dt.normalize()).dt.days
customers = pd.read_csv(RAW / "olist_customers_dataset.csv", dtype=str)
sellers = pd.read_csv(RAW / "olist_sellers_dataset.csv", dtype=str)
geo = pd.read_csv(RAW / "olist_geolocation_dataset.csv", dtype={"geolocation_zip_code_prefix": str})
geo = geo[geo["geolocation_lat"].between(-34, 6) & geo["geolocation_lng"].between(-74, -34)]
zips = set(geo["geolocation_zip_code_prefix"])
raw_orders = pd.read_csv(RAW / "olist_orders_dataset.csv", parse_dates=["order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date", "order_delivered_customer_date"])
delivered = raw_orders[raw_orders["order_status"] == "delivered"]
base_customer = delivered[delivered["order_delivered_customer_date"].notna()].merge(customers, on="customer_id")
report["documented_counts"] = {"flagged_in_base": len(flagged), "flagged_with_review (doc 188)": int(flagged["score"].notna().sum()), "over_60_days (doc was 288, corrected to 298)": int((days > 60).sum()), "multi_seller_excluded (doc 1275)": int((~mine["single"].astype(bool)).sum()),
                               "single_no_position (doc 471)": int((mine["single"].astype(bool) & mine["distance"].isna()).sum()), "customer_rows_no_position": int((~customers["customer_zip_code_prefix"].isin(zips)).sum()), "customer_prefixes_no_position": int(customers.loc[~customers["customer_zip_code_prefix"].isin(zips), "customer_zip_code_prefix"].nunique()),
                               "base_orders_customer_no_position": int((~base_customer["customer_zip_code_prefix"].isin(zips)).sum()), "seller_rows_no_position (doc 7)": int((~sellers["seller_zip_code_prefix"].isin(zips)).sum()),
                               "carrier_before_approval_delivered (doc 1350)": int((delivered["order_delivered_carrier_date"] < delivered["order_approved_at"]).sum()), "carrier_before_approval_all_status": int((raw_orders["order_delivered_carrier_date"] < raw_orders["order_approved_at"]).sum()),
                               "on_time_answered_before (doc 180)": int(((mine["late"] == 0) & (mine["timing"] == "before")).sum())}
late_rev = mine[(mine["late"] == 1) & mine["score"].notna()]
report["timing_by_band"] = {b: {"reviews": int((late_rev["delay"] == b).sum()), "answer_before_pct": round(100 * (late_rev.loc[late_rev["delay"] == b, "timing"] == "before").mean(), 1), "created_before_pct": round(100 * (late_rev.loc[late_rev["delay"] == b, "timing_created"] == "before").mean(), 1)} for b in ("1-3", "4-7", "8-14", "15+")}
rj = mine[mine["single"].astype(bool) & mine["distance"].notna() & (mine["state"] == "RJ")]
peak = rj["month"].isin(["2017-11", "2018-02", "2018-03"])
report["rj_late_orders"] = {"all": int(rj["late"].sum()), "excluding_peak": int(rj.loc[~peak, "late"].sum()), "in_peak": int(rj.loc[peak, "late"].sum())}
win = mine[mine["c"].notna()].copy()
for col in ("c", "d", "p"):
    win[col] = pd.to_datetime(win[col])
near = win[(win["c"] >= "2018-04-11") & (win["c"] < "2018-05-09")]
report["boundary_window_median_hour"] = {period: {"carrier": float(g["c"].dt.hour.median()), "delivery": float(g["d"].dt.hour.median()), "purchase": float(g["p"].dt.hour.median()), "orders": len(g), "late_handover_pct": round(100 * (g["handover"] == "late").mean(), 2)} for period, g in near.groupby(near["c"] >= "2018-04-25")}

# ---------------------------------------------------------------- 2. Clean-load SQL against the stored exports
clean, real = [pd.read_csv(p / "orders_analysis.csv", dtype=str, keep_default_na=False).set_index("order_id").sort_index() for p in (CLEAN / "data" / "processed", OUT)]
assert list(clean.index) == list(real.index)
cells = {c: int((clean[c] != real[c]).sum()) for c in clean.columns if c in real.columns}
report["clean_load_vs_stored_export"] = {"rows": [len(clean), len(real)], "columns_with_differences": {k: v for k, v in cells.items() if v}, "columns_identical": sum(v == 0 for v in cells.values())}
for name in ("validation.csv", "timestamp_checks.csv", "zip_positions.csv"):
    a, b = (CLEAN / "data" / "processed" / name).read_bytes(), (OUT / name).read_bytes()
    report["clean_load_vs_stored_export"][name + " identical"] = a.replace(b"\r\n", b"\n") == b.replace(b"\r\n", b"\n")
za, zb = [pd.read_csv(p / "zip_positions.csv", dtype={"zip_prefix": str}).set_index("zip_prefix").sort_index() for p in (CLEAN / "data" / "processed", OUT)]
report["clean_load_vs_stored_export"]["zip_largest_median_difference"] = float(max(np.abs(za["median_lat"] - zb["median_lat"]).max(), np.abs(za["median_lng"] - zb["median_lng"]).max()))
report["clean_load_vs_stored_export"]["zip_rows"] = [len(za), len(zb)]

# ---------------------------------------------------------------- 3. Results table
results = []


def add(name, mine_value, stored_value, kind="point"):
    results.append({"result": name, "independent": mine_value, "stored": stored_value, "difference": None if mine_value is None or stored_value is None else round(mine_value - stored_value, 3), "kind": kind})


R, K = I["results"], I["sensitivity"]
for h, key in (("A1", "A1"), ("A2", "A2"), ("A4", "A4"), ("A5", "A5")):
    add(f"{h} estimate", R[key]["estimate"], A[h]["estimate"])
    add(f"{h} odds ratio", R[key]["test"]["odds_ratio"], A[h]["test"]["odds_ratio"])
    add(f"{h} Holm p (log10)", None if R["holm"][h] == 0 else float(np.log10(R["holm"][h])), None if A[h]["holm_p"] == 0 else float(np.log10(A[h]["holm_p"])), "test")
    if "bootstrap" in R[key]:
        add(f"{h} interval low", R[key]["bootstrap"]["low"], A[h]["ci"][0], "bootstrap")
        add(f"{h} interval high", R[key]["bootstrap"]["high"], A[h]["ci"][1], "bootstrap")
add("A3 15+ vs 1-3", R["A3"]["pairs"]["15+ vs 1-3"]["estimate"], A["A3"]["estimate"])
add("A3 Holm p (log10)", float(np.log10(R["holm"]["A3"])), float(np.log10(A["A3"]["holm_p"])), "test")
for a, b in (("4-7", "1-3"), ("8-14", "4-7"), ("15+", "8-14"), ("15+", "1-3")):
    p = A["A3"]["pairs"][f"{a} days vs {b} days"]
    q = R["A3"]["pairs"][f"{a} vs {b}"]
    add(f"A3 {a} vs {b}", q["estimate"], p["estimate"])
    add(f"A3 {a} vs {b} low", q["boot_low"], p["ci"][0], "bootstrap")
    add(f"A3 {a} vs {b} high", q["boot_high"], p["ci"][1], "bootstrap")
add("A4 without state", R["A4"]["without_state"]["estimate"], A["A4"]["without_state_adjustment"]["estimate"])
add("A6 estimate", R["A6"]["estimate"], A["A6"]["estimate"])
add("A6 interval low", R["A6"]["ci"][0], A["A6"]["ci"][0], "bootstrap")
add("A6 interval high", R["A6"]["ci"][1], A["A6"]["ci"][1], "bootstrap")
add("A6 split-half", R["A6"]["split_half"], A["A6"]["split_half_gap_mean"], "simulation")
add("A6 null mean", R["A6"]["null_mean"], A["A6"]["null_gap_mean"], "simulation")
add("A6 raw p", R["A6"]["p"], A["A6"]["test"]["p"], "simulation")
add("A6 Holm p", R["holm"]["A6"], A["A6"]["holm_p"], "simulation")
add("A7 spread", R["A7"]["spread"], A["A7"]["estimate"])
add("A7 joint p", R["A7"]["joint_p"], A["A7"]["test"]["p"], "test")
add("A7 Holm p", R["holm"]["A7"], A["A7"]["holm_p"], "test")
add("A7 Cramer's V", R["A7"]["cramers_v"], A["A7"]["cramers_v"])
b3b, b3a = B["B3"]["late_answered_before_vs_on_time"], B["B3"]["late_answered_after_vs_on_time"]
for tag, mine_part, part in (("before", R["B3"]["before"], b3b), ("after", R["B3"]["after"], b3a)):
    add(f"B3 {tag}", mine_part["estimate"], part["estimate"])
    add(f"B3 {tag} low", mine_part["boot_low"], part["ci"][0], "bootstrap")
    add(f"B3 {tag} high", mine_part["boot_high"], part["ci"][1], "bootstrap")
timing = B["B4"]["by_timing"]
for g, tname in (("answer_before", "before arrival"), ("answer_after", "after arrival")):
    for band in ("1-3", "4-7", "8-14", "15+"):
        add(f"B4 {g} {band} rate", R["B4"]["rates"][g][band]["rate"], timing[tname]["bands"][f"{band} days"]["rate"])
for a, b in (("4-7", "1-3"), ("8-14", "4-7"), ("15+", "8-14")):
    add(f"B4 adjusted before {a} vs {b}", R["B4"]["adjusted_before"][f"{a} vs {b}"]["estimate"], timing["before arrival"]["adjusted"]["pairs"][f"{a} days vs {b} days"]["estimate"])
for a, b in (("4-7", "1-3"), ("8-14", "4-7")):
    add(f"B4 adjusted after {a} vs {b}", R["B4"]["adjusted_after"][f"{a} vs {b}"]["estimate"], timing["after arrival"]["adjusted"]["pairs"][f"{a} days vs {b} days"]["estimate"])
add("B1 peak rate", R["B1"]["peak"]["rate"], B["B1"]["peak_rate"])
add("B1 other rate", R["B1"]["other"]["rate"], B["B1"]["other_rate"])
add("B1 late share", R["B1"]["late_share"], B["B1"]["late_share_pct"])
add("B2 peak gap", R["B2"]["gap_peak"]["estimate"], B["B2"]["adjusted_gap_peak"]["estimate"])
add("B2 other gap", R["B2"]["gap_other"]["estimate"], B["B2"]["adjusted_gap_other"]["estimate"])
add("B2 difference", R["B2"]["difference"], B["B2"]["difference_of_gaps"]["estimate"])
period = {"before": "before 25 Apr 2018", "from": "from 25 Apr 2018"}
for tag, name in period.items():
    add(f"B5 {tag}", R["B5"][tag]["estimate"], B["B5"]["periods"][name]["adjusted_difference"]["estimate"])
add("B6", R["B6"]["estimate"], B["B6"]["adjusted_difference"]["estimate"])
add("B7 on-time share", R["B7"]["on_time_share"], B["B7"]["on_time_all"]["share_of_low_ratings_pct"])


def stored_row(h, scenario, contrast):
    hit = [r for r in S["rows"] if r["hypothesis"] == h and r["scenario"] == scenario and r["contrast"].startswith(contrast)]
    return hit[0]["estimate"] if hit else None


for name, value, h, scenario, contrast in (("X1a", K["X1a_A1_SP_sellers"], "A1", "X1a", "RJ"), ("X1b", K["X1b_A1_overlap"], "A1", "X1b", "RJ"), ("X1c", K["X1c_A1_out_of_state"], "A1", "X1c", "RJ"), ("X1d", K["X1d_A1_300_1000km"], "A1", "X1d", "RJ"),
                                           ("X2", K["X2_A5_with_state"], "A5", "X2", "Highest"), ("X3a", K["X3a_A2_after"], "A2", "X3a", "Late"), ("X3b", K["X3b_A2_before"], "A2", "X3b", "Late"), ("X3d", K["X3d_A3_before_15_vs_1_3"], "A3", "X3d", "15+ vs 1-3"), ("X3e", K["X3e_A3_after_8_14_vs_1_3"], "A3", "X3e", "8-14 vs 1-3"),
                                           ("S8a A1", K["S8a_A1"], "A1", "S8a", "RJ"), ("S8a A4", K["S8a_A4"], "A4", "S8a", "600"), ("S8a A5", K["S8a_A5"], "A5", "S8a", "Highest"), ("S8c A4", K["S8c_A4"], "A4", "S8c", "600"), ("S15 A3 15+ vs 8-14", K["S15_A3_15_vs_8_14"], "A3", "S15", "15+ vs 8-14"), ("S1a A2", K["S1a_A2_earliest"], "A2", "S1a", "Late"),
                                           ("S9 B3 before", K["S9_B3_before"], "B3 before", "S9", "B3 before"), ("S9 B3 after", K["S9_B3_after"], "B3 after", "S9", "B3 after")):
    add(name, value["estimate"], stored_row(h.split()[0], scenario, contrast), "sensitivity")
add("S8a A6", R["S8a_A6"]["estimate"], stored_row("A6", "S8a", "Top"), "sensitivity")
add("S15 A7 spread", R["S15_A7"]["spread"], stored_row("A7", "S15", "Spread"), "sensitivity")
report["results"] = results
points = [r for r in results if r["kind"] in ("point", "sensitivity") and r["difference"] is not None]
boots = [r for r in results if r["kind"] == "bootstrap"]
report["results_summary"] = {"point_compared": len(points), "point_largest_abs_difference": max(abs(r["difference"]) for r in points), "bootstrap_compared": len(boots), "bootstrap_largest_abs_difference": max(abs(r["difference"]) for r in boots), "unresolved_rows": [r["result"] for r in results if r["stored"] is None]}
report["large_differences"] = [r for r in results if r["difference"] is not None and abs(r["difference"]) > (0.02 if r["kind"] in ("point", "sensitivity") else 0.25)]

# ---------------------------------------------------------------- 4. Evidence labels re-derived from independent figures
CRIT = {"A1": 2, "A2": 5, "A4": 2, "A5": 2}
labels = {}
for h in CRIT:
    r = R[h]
    low = r.get("bootstrap", {"low": r["ci"][0]})["low"]
    holm_ok = R["holm"][h] < 0.05
    if r["estimate"] <= 0 or (low <= 0 and r["estimate"] < CRIT[h]):
        label = "Unsupported"
    elif low > 0 and holm_ok and r["estimate"] >= CRIT[h]:
        label = "Supported"
    else:
        label = "other"
    labels[h] = {"independent": label, "stored": A[h]["label"]}
adj = [R["A3"]["pairs"][k] for k in ("4-7 vs 1-3", "8-14 vs 4-7", "15+ vs 8-14")]
labels["A3"] = {"independent": "Supported" if all(p["estimate"] >= 5 and p["boot_low"] > 0 for p in adj) else "Inconclusive", "stored": A["A3"]["label"]}
labels["A6"] = {"independent": "Detectable" if R["A6"]["ci"][0] > 0 and R["holm"]["A6"] < 0.05 and R["A6"]["estimate"] < 10 else "other", "stored": A["A6"]["label"]}
labels["A7"] = {"independent": "Detectable" if R["holm"]["A7"] < 0.05 and R["A7"]["spread"] < 5 else "other", "stored": A["A7"]["label"]}
report["labels"] = labels

# ---------------------------------------------------------------- 5. Robustness table re-derived from stored rows
HEAD = {"A1": ("RJ vs SP", 2), "A2": ("Late vs on time", 5), "A3": ("15+ vs 1-3 days", 5), "A4": ("600-1,000 vs 0-100 km", 2), "A5": ("Highest vs lowest quartile", 2), "A6": ("Top 10%", 10), "A7": ("Spread", 5)}
SCHECK = {"review", "timestamp", "structure"}
robust = {}
for h, (contrast, crit) in HEAD.items():
    runs = [r for r in S["rows"] if r["hypothesis"] == h and r["contrast"].startswith(contrast) and not r["failed"]]
    base = next(r for r in runs if r["scenario"] == "S0")
    deciding = [r for r in runs if r["group"] in SCHECK]
    different = [r for r in runs if r["group"] == "different" and "star" not in r["label"].lower()]
    e0, c0 = base["estimate"], base["ci"]
    robust[h] = {"label_deciding_runs": len(deciding), "range": [min(r["estimate"] for r in deciding), max(r["estimate"] for r in deciding)], "different_question_range": [min(r["estimate"] for r in different), max(r["estimate"] for r in different)] if different else None,
                 "reversed": sum(np.sign(r["estimate"]) != np.sign(e0) for r in deciding), "zero_relation_changed": sum((r["ci"][0] <= 0 <= r["ci"][1]) != (c0[0] <= 0 <= c0[1]) for r in deciding if r["ci"]), "crossed_criterion": sum((r["estimate"] >= crit) != (e0 >= crit) for r in deciding),
                 "intervals_reaching_criterion": sum(r["ci"][0] <= crit <= r["ci"][1] for r in deciding if r["ci"]), "zero_width_intervals": sum(r["ci"][0] == r["ci"][1] for r in deciding if r["ci"])}
report["robustness_recount"] = robust
adjacent = [r for r in S["rows"] if r["hypothesis"] == "A3" and r["contrast"] == "15+ vs 8-14 days" and r["group"] in SCHECK]
report["a3_15_vs_8_14_zero_relation_in_label_runs"] = [r["scenario"] for r in adjacent if r["ci"][0] <= 0 <= r["ci"][1]]
report["a7_label_runs_joint_p_over_05"] = [r["scenario"] for r in S["rows"] if r["hypothesis"] == "A7" and r["group"] in SCHECK and r["p"] is not None and r["p"] > 0.05]
report["failures_in_stored_sensitivity"] = S["failures"]
report["bootstrap_failures_stored"] = {k: v.get("bootstrap_failures") for k, v in json.loads((OUT / "class_a_results.json").read_text(encoding="utf-8"))["checks"].items() if isinstance(v, dict) and "bootstrap_failures" in v}
report["rounding"] = {"A6_estimate_exact": A["A6"]["estimate"], "B1_rate_difference_stored": B["B1"]["rate_difference"]["estimate"], "B1_exact": 100 * (3158 / 20846 - 3376 / 75624), "B1_stored_row": stored_row("B1", "S0", "Peak"), "A6_stored_row": stored_row("A6", "S0", "Top")}
report["b5_from_pattern_text"] = B["B5"]["periods"]["from 25 Apr 2018"]["adjusted_difference"]["pattern"]
report["stored_thin_terms"] = {k: v.get("thin_terms") for k, v in Bfull["checks"].items() if v.get("thin_terms")}
report["stored_still_sparse"] = {k: v.get("levels_still_sparse_after_merging") for k, v in Bfull["checks"].items() if v.get("levels_still_sparse_after_merging")}
TARGET.write_text(json.dumps(report, indent=1, default=str), encoding="utf-8")
print(json.dumps({k: v for k, v in report.items() if k != "results"}, indent=1, default=str))
