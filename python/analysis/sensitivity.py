"""Stage 2, step 7: the 16 planned sensitivity analyses, required extra checks and larger bootstraps.

Primary Class A and Class B results and definitions aren't changed. Every run is written out,
including failed or contradictory ones. Results are observational. Checks for B4, B7, and for B1,
B2 and B5 not covered here are in sensitivity_supplement.py.

Writes data/processed/sensitivity_results.json, which Git ignores. Reads no database.

Usage: python python/analysis/sensitivity.py [raw-csv-folder] [large-bootstrap-replicates]
"""
from sensitivity_common import *  # noqa: F403

# ---------------------------------------------------------------- run: baseline
timed("baseline re-fit of the primary models")
primary = base.copy()
models0 = {}
for h in ("A1", "A2", "A3", "A4", "A5", "B3", "B6"):
    models0[h], _, _ = run_spec(h, primary.copy(), "S0", "baseline", "baseline", "Primary specification with delta-method interval")
spec_a7_run(primary.copy(), "S0", "baseline", "baseline", "Primary specification with delta-method interval")
run_a6(primary.copy(), "S0", "baseline", "baseline", "Primary specification")
b2_run(primary.copy(), "S0", "baseline", "baseline", "Primary specification with delta-method interval")
b5_run(primary.copy(), "S0", "baseline", "baseline", "Primary specification with delta-method interval")
unadjusted_b(primary.copy(), "S0", "baseline", "Primary specification")

# ---------------------------------------------------------------- run: planned scenarios
for scenario_id, plan_id, group, label, function, targets in SCENARIOS:
    timed(f"{scenario_id}: {label}")
    frame = function(base.copy())
    for target in targets:
        try:
            if target in SPECS:
                run_spec(target, frame.copy(), scenario_id, plan_id, group, label)
            elif target == "A7":
                spec_a7_run(frame.copy(), scenario_id, plan_id, group, label)
            elif target == "A6":
                run_a6(frame.copy(), scenario_id, plan_id, group, label)
            elif target == "B2":
                b2_run(frame.copy(), scenario_id, plan_id, group, label)
            elif target == "B5":
                b5_run(frame.copy(), scenario_id, plan_id, group, label)
        except Exception as error:
            failures_log.append({"run": f"{target} {scenario_id}", "error": repr(error)[:300]})
            rows.append({"hypothesis": target, "scenario": scenario_id, "plan_check": plan_id, "group": group, "label": label, "contrast": "failed", "estimate": None, "ci": None, "p": None, "diagnostics": None, "note": repr(error)[:300], "failed": True})
    unadjusted_b(frame, scenario_id, group, label)

# S13: model form
timed("S13: linear probability model and robust errors")
for hypothesis in ("A1", "A2", "A3", "A4", "A5", "B3", "B6"):
    s, outcome, exposure, levels, reference, categorical, numeric, contrasts = SPECS[hypothesis](base.copy())
    model, _ = fit_spec(f"{hypothesis} S13", s, outcome, exposure, levels, reference, categorical, numeric, contrasts)
    for name, value in fit_lpm(model, levels, reference, exposure, contrasts).items():
        record(hypothesis, "S13a", "S13", "structure", "Linear probability model", name, value, model)
    _, out = fit_spec(f"{hypothesis} S13b", s, outcome, exposure, levels, reference, categorical, numeric, contrasts, "HC1")
    for name, value in out.items():
        record(hypothesis, "S13b", "S13", "structure", "Heteroskedasticity-robust errors, not clustered", name, value, model)
spec_a7_run(base.copy(), "S13a", "S13", "structure", "Linear probability model", lpm=True)
spec_a7_run(base.copy(), "S13b", "S13", "structure", "Heteroskedasticity-robust errors, not clustered", cov_type="HC1")

# S6: low-rating definition
timed("S6: low-rating definitions")
for scenario_id, label, threshold in (("S6a", "1 star only", 1), ("S6b", "1-3 stars", 3)):
    frame = base.copy()
    frame["low_rating"] = np.where(frame["has_review"], frame["latest_review_score"].le(threshold).astype(float), np.nan)
    for hypothesis in ("A2", "A3", "B3", "B6"):
        run_spec(hypothesis, frame.copy(), scenario_id, "S6", "different", label)
for hypothesis in ("A2", "A3", "B3", "B6"):
    s, outcome, exposure, levels, reference, categorical, numeric, contrasts = SPECS[hypothesis](base.copy())
    model, _ = fit_spec(f"{hypothesis} S6c", s, outcome, exposure, levels, reference, categorical, numeric, contrasts)
    fit = sm.OLS(model.frame["latest_review_score"].astype(float), model.design).fit(cov_type="cluster", cov_kwds={"groups": model.codes})
    for name, a, b in contrasts:
        L = np.zeros(len(fit.params))
        if a != reference:
            L[list(fit.params.index).index(f"{exposure}={a}")] = 1
        if b != reference:
            L[list(fit.params.index).index(f"{exposure}={b}")] = -1
        est, se = float(L @ fit.params.to_numpy()), float(np.sqrt(L @ fit.cov_params().to_numpy() @ L))
        rows.append({"hypothesis": hypothesis, "scenario": "S6c", "plan_check": "S6", "group": "different", "label": "Mean score difference, in stars", "contrast": name, "estimate": round(est, 3), "ci": [round(est - Z * se, 3), round(est + Z * se, 3)], "p": float(2 * ss.norm.sf(abs(est / se))), "diagnostics": diagnostics(model), "note": "In stars, not points. Screening criterion 0.25 stars.", "failed": False})

# S14: carrier timestamp period
timed("S14: carrier timestamp period")
frame = base.copy()
frame["purchase_split"] = np.where(frame["purchase_ts"] >= "2018-04-01", "from April 2018 purchases", "before April 2018 purchases")
b5_run(frame, "S14a", "S14", "timestamp", "Purchase-month split", period_column="purchase_split")
window = (frame["carrier_ts"] >= BOUNDARY - pd.Timedelta(days=14)) & (frame["carrier_ts"] < BOUNDARY + pd.Timedelta(days=14))
b5_run(frame[~window].copy(), "S14b", "S14", "timestamp", "Excluding carrier dates within 14 days of the boundary")
frame["all_period"] = "pooled"
b5_run(frame, "S14c", "S14", "timestamp", "One pooled period", period_column="all_period", note="Mixes the two timestamp patterns")

# Required A1 overlap checks
timed("Required A1 overlap checks")
sp_sellers = base[base["primary_seller_state"].eq("SP") & base["single_seller"] & base["distance_km"].notna() & base["customer_state"].isin(["RJ", "SP"])].copy()
overlap_table = pd.crosstab(sp_sellers["distance_band"], sp_sellers["customer_state"]).reindex(DISTANCE_BANDS).fillna(0).astype(int)
overlap_bands = overlap_table[(overlap_table["RJ"] >= MIN_ORDERS) & (overlap_table["SP"] >= MIN_ORDERS)].index.tolist()
REQUIRED = {"sp_seller_overlap_table": overlap_table.to_dict("index"), "overlap_bands_used": overlap_bands}
contrast = [("RJ vs SP", "RJ", "SP")]
for scenario_id, label, frame in (
        ("X1a", "SP sellers only; same-state term removed because it equals customer state here", sp_sellers),
        ("X1b", "SP sellers, overlapping distance bands only; same-state term removed", sp_sellers[sp_sellers["distance_band"].isin(overlap_bands)]),
        ("X1c", "Out-of-state sellers only, for both customer states; same-state term removed", base[base["single_seller"] & base["distance_km"].notna() & base["customer_state"].isin(["RJ", "SP"]) & base["same_state_seller"].eq(0)]),
        ("X1d", "300-1,000 km only, the bands where both states have many orders", base[base["single_seller"] & base["distance_band"].isin(["300-600 km", "600-1,000 km"]) & base["customer_state"].isin(["RJ", "SP"])])):
    numeric = ["log_order_value"] if scenario_id != "X1d" else ["log_order_value", "same_state_seller"]
    model, out = fit_spec(f"A1 {scenario_id}", frame.copy(), "late", "customer_state", ["SP", "RJ"], "SP", ["distance_band", "purchase_month", "item_band"], numeric, contrast)
    record("A1", scenario_id, "Required", "structure", label, "RJ vs SP", out["RJ vs SP"], model)
    part = frame
    REQUIRED[scenario_id] = {state: {"orders": int(part["customer_state"].eq(state).sum()), "late": int(part.loc[part["customer_state"].eq(state), "late"].sum())} for state in ("RJ", "SP")}

# Required labelled A5 check with customer state
timed("Exploratory A5 check with customer state")
s, outcome, exposure, levels, reference, categorical, numeric, contrasts = spec_a5(base.copy(), add_state=True)
model, out = fit_spec("A5 X2", s, outcome, exposure, levels, reference, categorical, numeric, contrasts)
for name, value in out.items():
    record("A5", "X2", "Required, exploratory", "exploratory", "Customer state added, labelled exploratory. Doesn't change the A5 definition or result", name, value, model)
for name, a, b in (("Q2 vs lowest", "Q2", QUARTILES[0]), ("Q3 vs Q2", "Q3", "Q2"), ("Highest vs Q3", QUARTILES[3], "Q3")):
    model2, out2 = fit_spec("A5 X2 steps", s, outcome, exposure, levels, reference, categorical, numeric, [(name, a, b)])
    record("A5", "X2", "Required, exploratory", "exploratory", "Customer state added: step between quartiles", name, out2[name], model2)

# Required answer-timing checks for A2 and A3
timed("Required answer-timing checks")
frame = base[base["has_review"]].copy()
for scenario_id, label, keep in (("X3a", "A2 with late orders answered after arrival only", frame["late"].eq(0) | frame["answer_timing"].eq("after arrival")),
                                 ("X3b", "A2 with late orders answered before arrival only", frame["late"].eq(0) | frame["answer_timing"].eq("before arrival")),
                                 ("X3c", "A2 with all reviews answered after arrival", frame["answer_timing"].eq("after arrival"))):
    run_spec("A2", frame[keep].copy(), scenario_id, "Required, exploratory", "exploratory", label)
late_after = frame[frame["late"].eq(1) & frame["answer_timing"].eq("after arrival")]
late_before = frame[frame["late"].eq(1) & frame["answer_timing"].eq("before arrival")]
for scenario_id, label, part, numeric in (("X3d", "A3 with reviews answered before arrival; multi-seller term removed because of separation", late_before, ["log_order_value"]),):
    model, out = fit_spec(f"A3 {scenario_id}", part.copy(), "low_rating", "delay_band", DELAY_BANDS, "1-3 days", ["purchase_month", "state_group", "item_band", "category_group"], numeric,
                          [("15+ vs 1-3 days", "15+ days", "1-3 days"), ("4-7 vs 1-3 days", "4-7 days", "1-3 days"), ("8-14 vs 4-7 days", "8-14 days", "4-7 days"), ("15+ vs 8-14 days", "15+ days", "8-14 days")])
    for name, value in out.items():
        record("A3", scenario_id, "Required, exploratory", "exploratory", label, name, value, model)
usable = late_after[late_after["delay_band"].isin(["1-3 days", "4-7 days", "8-14 days"])].copy()
model, out = fit_spec("A3 X3e", usable, "low_rating", "delay_band", ["1-3 days", "4-7 days", "8-14 days"], "1-3 days", ["purchase_month", "state_group", "item_band"], ["log_order_value", "multi_seller"],
                      [("8-14 vs 1-3 days", "8-14 days", "1-3 days"), ("4-7 vs 1-3 days", "4-7 days", "1-3 days"), ("8-14 vs 4-7 days", "8-14 days", "4-7 days")])
for name, value in out.items():
    record("A3", "X3e", "Required, exploratory", "exploratory", "A3 with reviews answered after arrival; 15+ days has under 30 reviews; category removed because of too few events", name, value, model)

# Larger bootstraps
timed(f"Larger bootstraps, {LARGE} replicates")
large = {}
frame = with_distance(base.copy())
frame["freight_quartile"] = pd.qcut(frame["freight_value"], 4, labels=QUARTILES).astype(object)
model_a5 = Logit("A5 large", frame, "late", ["distance_band", "purchase_month", "item_band"], ["log_order_value"], extra=categorical_exposure(frame, "freight_quartile", QUARTILES, QUARTILES[0]))
columns = {v: f"freight_quartile={v}" for v in QUARTILES[1:]}
hi = model_a5.counterfactual({c: (1.0 if v == QUARTILES[3] else 0.0) for v, c in columns.items()})
lo = model_a5.counterfactual({c: 0.0 for c in columns.values()})
point = risk(model_a5.beta, hi) - risk(model_a5.beta, lo)
draws = model_a5.bootstrap(lambda beta, w: [risk(beta, hi, w) - risk(beta, lo, w)], LARGE, next(seeds))
large["A5"] = {"estimate": round(point, 3), "ci": interval(draws[:, 0]), "share_at_or_above_criterion_pct": round(100 * float(np.mean(draws[:, 0] >= 2.0)), 1), "replicates": LARGE, "failures": model_a5.report["bootstrap_failures"]}
timed("A5 large done")
a6 = a6_stats(base.copy(), next(seeds), replicates=LARGE, simulations=5000)
large["A6"] = {"estimate": round(a6["estimate"], 3), "ci": a6["ci"], "p": a6["p"], "replicates": LARGE, "failures": 0, "split_half": a6["split_half"], "null_mean": a6["null_mean"]}
timed("A6 large done")
s = with_distance(base.copy())
s = s[s["primary_category"].isin(CATEGORY_LEVELS)].copy()
biggest = s["primary_category"].value_counts().idxmax()
model_a7 = Logit("A7 large", s, "late", ["purchase_month", "state_group", "distance_band"], [], extra=categorical_exposure(s, "primary_category", CATEGORY_LEVELS, biggest))
cols_a7 = {v: f"primary_category={v}" for v in CATEGORY_LEVELS if v != biggest}
worlds_a7 = {v: model_a7.counterfactual({c: (1.0 if k == v else 0.0) for k, c in cols_a7.items()}) for v in CATEGORY_LEVELS}
rates_a7 = {v: risk(model_a7.beta, X) for v, X in worlds_a7.items()}
hi7, lo7 = max(rates_a7, key=rates_a7.get), min(rates_a7, key=rates_a7.get)


def a7_stat(beta, w):
    r = {v: risk(beta, X, w) for v, X in worlds_a7.items()}
    return [max(r.values()) - min(r.values()), r[hi7] - r[lo7]]


draws = model_a7.bootstrap(a7_stat, LARGE, next(seeds))
large["A7"] = {"estimate": round(rates_a7[hi7] - rates_a7[lo7], 3), "ci_reselecting_pair": interval(draws[:, 0]), "ci_fixed_pair": interval(draws[:, 1]), "share_at_or_above_criterion_reselecting_pct": round(100 * float(np.mean(draws[:, 0] >= 5.0)), 1), "share_at_or_above_criterion_fixed_pair_pct": round(100 * float(np.mean(draws[:, 1] >= 5.0)), 1),
               "pair": [hi7, lo7], "replicates": LARGE, "failures": model_a7.report["bootstrap_failures"]}
timed("A7 large done")

output = {"seed": SEED, "large_replicates": LARGE, "extreme_distance_km": EXTREME_KM, "affected_orders_excluded_in_s4b": len(affected_ids), "failures": failures_log, "required": REQUIRED, "large_bootstrap": large, "rows": rows}
(OUT / "sensitivity_results.json").write_text(json.dumps(output, indent=1, default=str), encoding="utf-8")
timed(f"done: {len(rows)} result rows, {len(failures_log)} failures")
