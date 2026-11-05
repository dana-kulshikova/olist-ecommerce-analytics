"""Stage 2, steps 1-3: model checks and the seven Class A tests.

Reads data/processed/analysis_orders.csv and writes data/processed/class_a_results.json, which
Git ignores. Results are observational associations, and provisional until the sensitivity
analyses are complete.

Risk differences are standardised from logistic models. Intervals come from a seller-level
cluster bootstrap, resampling sellers through frequency weights on the same design matrix.

Usage: python python/analysis/class_a.py [replicates]
"""
import json
import pathlib
import sys
import time

import numpy as np
import pandas as pd
import scipy.linalg as sla
import scipy.stats as ss
import statsmodels.api as sm
from scipy.special import expit

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "processed"
SEED = 20261105
REPLICATES = int(sys.argv[1]) if len(sys.argv) > 1 else 500
SIMULATIONS = 5000
MIN_ORDERS, MIN_EVENTS = 30, 10

# Criteria from docs/methodology.md: researcher-defined screening criteria, not business targets.
LATE_POINTS, LATE_ORDERS = 2.0, 500
LOW_POINTS, SCORE_POINTS, CONCENTRATION_POINTS, CATEGORY_POINTS = 5.0, 0.25, 10.0, 5.0
DISTANCE_BANDS = ["0-100 km", "100-300 km", "300-600 km", "600-1,000 km", "1,000-2,000 km", "2,000+ km"]
DELAY_BANDS = ["1-3 days", "4-7 days", "8-14 days", "15+ days"]

data = pd.read_csv(OUT / "analysis_orders.csv", keep_default_na=False,
                   na_values=[""], dtype={"primary_seller_id": str})
results, checks = {}, {}
seeds = iter(np.random.SeedSequence(SEED).spawn(20))


def log(message):
    print(message, flush=True)


def wilson(k, n, z=1.959964):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - m) / d, (c + m) / d)


def merge_months(frame, outcome):
    """Merges sparse months forward into the next month, and a sparse final group backward."""
    table = frame.groupby("purchase_month")[outcome].agg(["size", "sum"]).sort_index()
    groups, current, totals = {}, [], [0, 0]
    labelled = []
    for month, row in table.iterrows():
        current.append(month)
        totals = [totals[0] + int(row["size"]), totals[1] + int(row["sum"])]
        non_events = totals[0] - totals[1]
        if totals[0] >= MIN_ORDERS and totals[1] >= MIN_EVENTS and non_events >= MIN_EVENTS:
            labelled.append(list(current))
            current, totals = [], [0, 0]
    if current:
        if labelled:
            labelled[-1].extend(current)
        else:
            labelled.append(list(current))
    for members in labelled:
        name = members[0] if len(members) == 1 else f"{members[0]} to {members[-1]}"
        for month in members:
            groups[month] = name
    return frame["purchase_month"].map(groups), [g for g in labelled if len(g) > 1]


def collapse_sparse(frame, column, outcome):
    """Merges sparse covariate levels into 'other', and reports them."""
    table = frame.groupby(column)[outcome].agg(["size", "sum"])
    sparse = table[(table["size"] < MIN_ORDERS) | (table["sum"] < MIN_EVENTS) | (table["size"] - table["sum"] < MIN_EVENTS)]
    if sparse.empty:
        return frame[column], []
    return frame[column].where(~frame[column].isin(sparse.index), "other"), sorted(map(str, sparse.index))


class Model:
    """Logistic model with one categorical exposure, reference-coded."""

    def __init__(self, name, frame, outcome, exposure, reference, levels, categorical, numeric, merge_month=True):
        self.name, self.outcome, self.exposure, self.reference = name, outcome, exposure, reference
        frame = frame.copy().reset_index(drop=True)
        self.report = {"orders": int(len(frame)), "events": int(frame[outcome].sum()), "merged_months": [], "merged_levels": {}}
        for column in categorical:
            if column == "purchase_month" and merge_month:
                frame[column], merged = merge_months(frame, outcome)
                self.report["merged_months"] = merged
            else:
                frame[column], merged = collapse_sparse(frame, column, outcome)
                if merged:
                    self.report["merged_levels"][column] = merged
        self.frame, self.levels = frame, levels
        parts = [pd.Series(1.0, index=frame.index, name="const")]
        self.level_columns = {}
        for level in levels:
            if level != reference:
                column = f"{exposure}={level}"
                parts.append((frame[exposure] == level).astype(float).rename(column))
                self.level_columns[level] = column
        for column in categorical:
            dummies = pd.get_dummies(frame[column], prefix=column, prefix_sep="=", dtype=float)
            parts.append(dummies.drop(columns=dummies.sum().idxmax()))
        for column in numeric:
            parts.append(frame[column].astype(float))
        self.design = pd.concat(parts, axis=1)
        self.columns = list(self.design.columns)
        self.X = self.design.to_numpy(dtype=float)
        self.y = frame[outcome].to_numpy(dtype=float)
        self.level_index = {level: self.columns.index(col) for level, col in self.level_columns.items()}
        self.other_index = [i for i, col in enumerate(self.columns) if i not in self.level_index.values()]
        self.groups = frame["primary_seller_id"].to_numpy()
        self.cluster_codes, self.clusters = pd.factorize(self.groups)
        self.report["parameters"] = len(self.columns)
        self.report["sellers"] = int(len(self.clusters))
        self.report["events_per_parameter"] = round(self.report["events"] / len(self.columns), 1)
        self.report["non_events_per_parameter"] = round((self.report["orders"] - self.report["events"]) / len(self.columns), 1)
        self.report["exposure_groups"] = {str(k): {"orders": int(v["size"]), "events": int(v["sum"])}
                                          for k, v in frame.groupby(exposure)[outcome].agg(["size", "sum"]).iterrows()}
        self.fit()

    def irls(self, weights=None, start=None, tolerance=1e-7, max_iterations=50):
        if weights is None:
            X, y, w = self.X, self.y, np.ones_like(self.y)
        else:
            keep = weights > 0
            X, y, w = self.X[keep], self.y[keep], weights[keep]
        beta = np.zeros(X.shape[1]) if start is None else start.copy()
        ridge = 1e-9 * np.eye(X.shape[1])
        for iteration in range(1, max_iterations + 1):
            eta = np.clip(X @ beta, -30, 30)
            mu = expit(eta)
            variance = np.clip(mu * (1 - mu), 1e-10, None)
            weight = w * variance
            working = eta + (y - mu) / variance
            A = (X * weight[:, None]).T @ X + ridge
            b = (X * weight[:, None]).T @ working
            try:
                new = sla.solve(A, b, assume_a="pos", check_finite=False)
            except (sla.LinAlgError, ValueError):
                return beta, False, iteration
            if np.max(np.abs(new - beta)) < tolerance:
                return new, True, iteration
            beta = new
        return beta, False, max_iterations

    def fit(self):
        self.beta, converged, iterations = self.irls()
        wrapped = sm.GLM(self.y, self.design, family=sm.families.Binomial()).fit(
            cov_type="cluster", cov_kwds={"groups": self.cluster_codes})
        self.wald = wrapped
        self.report.update({
            "converged": bool(converged and wrapped.converged), "iterations": int(iterations),
            "largest_abs_coefficient": round(float(np.max(np.abs(self.beta))), 2),
            "largest_standard_error": round(float(wrapped.bse.max()), 2),
            "agreement_with_statsmodels": float(np.max(np.abs(self.beta - wrapped.params.to_numpy()))),
            "condition_number": float(np.linalg.cond(self.X / np.where(self.X.std(axis=0) > 0, self.X.std(axis=0), 1.0))),
        })

    def rates(self, beta, weights=None):
        """Standardised risk at each exposure level, in percentage points."""
        keep = np.ones(len(self.y), bool) if weights is None else weights > 0
        w = np.ones(keep.sum()) if weights is None else weights[keep]
        base = self.X[keep][:, self.other_index] @ beta[self.other_index]
        out = {}
        for level in self.levels:
            shift = 0.0 if level == self.reference else beta[self.level_index[level]]
            out[level] = 100 * float(np.average(expit(base + shift), weights=w))
        return out

    def bootstrap(self, statistic, replicates, seed):
        rng = np.random.default_rng(seed)
        estimates, failures = [], 0
        n = len(self.clusters)
        for replicate in range(replicates):
            counts = rng.multinomial(n, np.full(n, 1 / n))
            weights = counts[self.cluster_codes].astype(float)
            beta, converged, _ = self.irls(weights=weights, start=self.beta, tolerance=1e-6)
            if not converged or np.max(np.abs(beta)) > 25:
                failures += 1
                continue
            estimates.append(statistic(self.rates(beta, weights)))
        self.report["bootstrap_replicates"] = replicates
        self.report["bootstrap_failures"] = failures
        self.report["bootstrap_failure_pct"] = round(100 * failures / replicates, 2)
        self.report["bootstrap_reliable"] = failures / replicates <= 0.05
        return np.array(estimates)

    def contrast_test(self, level, against=None):
        names = self.wald.params.index
        L = np.zeros(len(names))
        L[names.get_loc(self.level_columns[level])] = 1
        if against is not None and against != self.reference:
            L[names.get_loc(self.level_columns[against])] = -1
        estimate = float(L @ self.wald.params.to_numpy())
        se = float(np.sqrt(L @ self.wald.cov_params().to_numpy() @ L))
        z = estimate / se
        return {"log_odds": estimate, "se": se, "z": z, "p": float(2 * ss.norm.sf(abs(z))),
                "odds_ratio": float(np.exp(estimate)), "or_low": float(np.exp(estimate - 1.959964 * se)), "or_high": float(np.exp(estimate + 1.959964 * se))}


def interval(values):
    return [float(np.percentile(values, 2.5)), float(np.percentile(values, 97.5))]


def unadjusted(frame, group, outcome):
    table = {}
    for level, part in frame.groupby(group):
        k, n = int(part[outcome].sum()), len(part)
        low, high = wilson(k, n)
        table[str(level)] = {"orders": n, "events": k, "rate": round(100 * k / n, 2), "low": round(100 * low, 2), "high": round(100 * high, 2)}
    return table


def timed(label):
    log(f"[{time.strftime('%H:%M:%S')}] {label}")


# ---------------------------------------------------------------- sample definitions
with_distance = data[data["single_seller"] & data["distance_km"].notna()].copy()
reviewed = data[data["has_review"]].copy()
checks["samples"] = {"base": len(data), "single_seller_with_distance": len(with_distance), "reviewed": len(reviewed),
                     "excluded_multi_seller": int((~data["single_seller"]).sum()),
                     "excluded_no_position": int((data["single_seller"] & data["distance_km"].isna()).sum())}

# Related predictors, for the model checks.
numeric_view = with_distance.assign(log_freight=np.log1p(with_distance["freight_value"]), log_distance=np.log1p(with_distance["distance_km"]))
variables = ["log_order_value", "log_freight", "items_count", "log_distance", "same_state_seller"]
correlation = numeric_view[variables].corr().to_numpy()
checks["variance_inflation"] = {name: round(float(value), 2) for name, value in zip(variables, np.diag(np.linalg.inv(correlation)))}
checks["predictor_correlations"] = numeric_view[variables].corr().round(2).to_dict()

# ---------------------------------------------------------------- A1
timed("A1")
a1_frame = with_distance[with_distance["customer_state"].isin(["RJ", "SP"])].copy()
a1 = Model("A1", a1_frame, "late", "customer_state", "SP", ["SP", "RJ"],
           ["distance_band", "purchase_month", "item_band"], ["log_order_value", "same_state_seller"])
a1_rates = a1.rates(a1.beta)
a1_boot = a1.bootstrap(lambda r: r["RJ"] - r["SP"], REPLICATES, next(seeds))
overlap = pd.crosstab(a1_frame["distance_band"], a1_frame["customer_state"]).reindex(DISTANCE_BANDS).fillna(0).astype(int)
same_state = a1_frame.groupby("customer_state")["same_state_seller"].mean().round(4).to_dict()
results["A1"] = {
    "question": "RJ late rate compared with SP", "predicted": "RJ higher", "unit": "points",
    "unadjusted": unadjusted(a1_frame, "customer_state", "late"), "adjusted_rates": a1_rates,
    "estimate": a1_rates["RJ"] - a1_rates["SP"], "ci": interval(a1_boot), "test": a1.contrast_test("RJ"),
    "late_orders_in_segment": int(a1_frame.loc[a1_frame["customer_state"].eq("RJ"), "late"].sum()),
    "overlap_orders_by_distance": overlap.to_dict(), "same_state_share": same_state,
}
checks["A1"] = a1.report

# ---------------------------------------------------------------- A4
timed("A4")
a4 = Model("A4", with_distance, "late", "distance_band", "0-100 km", DISTANCE_BANDS,
           ["purchase_month", "state_group", "item_band"], ["log_order_value"])
a4_rates = a4.rates(a4.beta)
a4_boot = a4.bootstrap(lambda r: r["600-1,000 km"] - r["0-100 km"], REPLICATES, next(seeds))
a4_without_state = Model("A4 without state", with_distance, "late", "distance_band", "0-100 km", DISTANCE_BANDS,
                         ["purchase_month", "item_band"], ["log_order_value"])
without_rates = a4_without_state.rates(a4_without_state.beta)
results["A4"] = {
    "question": "Distance and late delivery", "predicted": "Longer distance higher", "unit": "points",
    "unadjusted": unadjusted(with_distance, "distance_band", "late"), "adjusted_rates": a4_rates,
    "estimate": a4_rates["600-1,000 km"] - a4_rates["0-100 km"], "ci": interval(a4_boot), "test": a4.contrast_test("600-1,000 km"),
    "late_orders_in_segment": int(with_distance.loc[with_distance["distance_band"].eq("600-1,000 km"), "late"].sum()),
    "without_state_adjustment": {"rates": without_rates, "estimate": without_rates["600-1,000 km"] - without_rates["0-100 km"], "test": a4_without_state.contrast_test("600-1,000 km")},
}
checks["A4"] = a4.report
checks["A4_without_state"] = a4_without_state.report

# ---------------------------------------------------------------- A5
timed("A5")
a5_frame = with_distance.copy()
a5_frame["freight_quartile"], freight_edges = pd.qcut(a5_frame["freight_value"], 4, labels=["Q1 lowest", "Q2", "Q3", "Q4 highest"], retbins=True)
a5_frame["freight_quartile"] = a5_frame["freight_quartile"].astype(object)
QUARTILES = ["Q1 lowest", "Q2", "Q3", "Q4 highest"]
a5 = Model("A5", a5_frame, "late", "freight_quartile", "Q1 lowest", QUARTILES,
           ["distance_band", "purchase_month", "item_band"], ["log_order_value"])
a5_rates = a5.rates(a5.beta)
a5_boot = a5.bootstrap(lambda r: r["Q4 highest"] - r["Q1 lowest"], REPLICATES, next(seeds))
results["A5"] = {
    "question": "Freight cost and late delivery", "predicted": "Higher freight higher", "unit": "points",
    "unadjusted": unadjusted(a5_frame, "freight_quartile", "late"), "adjusted_rates": a5_rates,
    "estimate": a5_rates["Q4 highest"] - a5_rates["Q1 lowest"], "ci": interval(a5_boot), "test": a5.contrast_test("Q4 highest"),
    "late_orders_in_segment": int(a5_frame.loc[a5_frame["freight_quartile"].eq("Q4 highest"), "late"].sum()),
    "freight_edges": [round(float(x), 2) for x in freight_edges],
}
checks["A5"] = a5.report

# ---------------------------------------------------------------- A6
timed("A6")
single = data[data["single_seller"]].copy()
month_rate = single.groupby("purchase_month")["late"].mean()
single["expected"] = single["purchase_month"].map(month_rate)
single["variance"] = single["expected"] * (1 - single["expected"])
sellers = single.groupby("primary_seller_id").agg(orders=("late", "size"), late=("late", "sum"), expected=("expected", "sum"), variance=("variance", "sum"))
eligible = sellers[sellers["orders"].ge(100)].sort_index()
top_count = int(np.ceil(0.10 * len(eligible)))


def concentration(orders, late, count):
    order = np.lexsort((np.arange(len(late)), -late))[:count]
    return 100 * (late[order].sum() / late.sum() - orders[order].sum() / orders.sum())


orders_array, late_array = eligible["orders"].to_numpy(float), eligible["late"].to_numpy(float)
gap = concentration(orders_array, late_array, top_count)
rng = np.random.default_rng(next(seeds))
boot_gaps = []
for _ in range(REPLICATES):
    picks = rng.integers(0, len(eligible), len(eligible))
    boot_gaps.append(concentration(orders_array[picks], late_array[picks], top_count))
eligible_orders = single[single["primary_seller_id"].isin(eligible.index)]
seller_month = eligible_orders.groupby(["primary_seller_id", "purchase_month"]).size().rename("n").reset_index()
seller_month["p"] = seller_month["purchase_month"].map(month_rate)
seller_month["code"] = pd.Categorical(seller_month["primary_seller_id"], categories=eligible.index).codes
rng = np.random.default_rng(next(seeds))
null_gaps = np.empty(SIMULATIONS)
for simulation in range(SIMULATIONS):
    draws = rng.binomial(seller_month["n"].to_numpy(), seller_month["p"].to_numpy())
    null_gaps[simulation] = concentration(orders_array, np.bincount(seller_month["code"].to_numpy(), weights=draws, minlength=len(eligible)), top_count)
p_a6 = float((1 + np.sum(null_gaps >= gap)) / (SIMULATIONS + 1))
z = (eligible["late"] - eligible["expected"]) / np.sqrt(eligible["variance"])
rng = np.random.default_rng(next(seeds))
order_seller = eligible_orders["primary_seller_id"].to_numpy()
order_late = eligible_orders["late"].to_numpy(float)
codes = pd.Categorical(order_seller, categories=eligible.index).codes
split_gaps = []
for _ in range(200):
    half = rng.random(len(order_late)) < 0.5
    first_late = np.bincount(codes[half], weights=order_late[half], minlength=len(eligible))
    second_late = np.bincount(codes[~half], weights=order_late[~half], minlength=len(eligible))
    second_orders = np.bincount(codes[~half], minlength=len(eligible)).astype(float)
    chosen = np.lexsort((np.arange(len(eligible)), -first_late))[:top_count]
    split_gaps.append(100 * (second_late[chosen].sum() / second_late.sum() - second_orders[chosen].sum() / second_orders.sum()))
ranked = np.lexsort((np.arange(len(late_array)), -late_array))[:top_count]
results["A6"] = {
    "question": "Seller concentration of late orders", "predicted": "Disproportionate share", "unit": "points",
    "estimate": gap, "ci": interval(boot_gaps), "test": {"p": p_a6, "method": f"simulation, {SIMULATIONS} draws, one-sided"},
    "eligible_sellers": int(len(eligible)), "top_sellers": top_count,
    "top_late_share": round(100 * late_array[ranked].sum() / late_array.sum(), 2), "top_order_share": round(100 * orders_array[ranked].sum() / orders_array.sum(), 2),
    "eligible_orders": int(orders_array.sum()), "eligible_late": int(late_array.sum()),
    "eligible_share_of_single_seller_orders": round(100 * orders_array.sum() / len(single), 2),
    "null_gap_mean": round(float(null_gaps.mean()), 2), "null_gap_97_5": round(float(np.percentile(null_gaps, 97.5)), 2),
    "split_half_gap_mean": round(float(np.mean(split_gaps)), 2), "split_half_gap_range": [round(float(np.percentile(split_gaps, 2.5)), 2), round(float(np.percentile(split_gaps, 97.5)), 2)],
    "sellers_above_funnel": int((z > 3.09).sum()), "sellers_below_funnel": int((z < -3.09).sum()),
    "expected_outside_funnel_by_chance": round(0.002 * len(eligible), 1),
}
checks["A6"] = {"eligible_sellers": int(len(eligible)), "orders": int(orders_array.sum()), "late": int(late_array.sum()),
                "smallest_seller_orders": int(orders_array.min()), "sellers_excluded_under_100": int(len(sellers) - len(eligible)),
                "bootstrap_replicates": REPLICATES, "simulations": SIMULATIONS}

# ---------------------------------------------------------------- A7
timed("A7")
base_counts = data.loc[data["primary_category"].ne("unknown"), "primary_category"].value_counts()
big_categories = sorted(base_counts[base_counts.ge(1000)].index)
a7_frame = with_distance[with_distance["primary_category"].isin(big_categories)].copy()
biggest = a7_frame["primary_category"].value_counts().idxmax()
a7 = Model("A7", a7_frame, "late", "primary_category", biggest, big_categories, ["purchase_month", "state_group", "distance_band"], [])
a7_rates = a7.rates(a7.beta)
a7_boot = a7.bootstrap(lambda r: max(r.values()) - min(r.values()), REPLICATES, next(seeds))
terms = [i for i, name in enumerate(a7.wald.params.index) if name.startswith("primary_category=")]
b = a7.wald.params.to_numpy()[terms]
V = a7.wald.cov_params().to_numpy()[np.ix_(terms, terms)]
stat = float(b @ np.linalg.solve(V, b))
p_a7 = float(ss.chi2.sf(stat, len(terms)))
table = pd.crosstab(a7_frame["primary_category"], a7_frame["late"]).to_numpy()
chi2 = ss.chi2_contingency(table, correction=False)[0]
cramers = float(np.sqrt(chi2 / table.sum()))
results["A7"] = {
    "question": "Category differences in late rates", "predicted": "Material differences", "unit": "points",
    "unadjusted": unadjusted(a7_frame, "primary_category", "late"), "adjusted_rates": a7_rates,
    "estimate": max(a7_rates.values()) - min(a7_rates.values()), "ci": interval(a7_boot),
    "test": {"p": p_a7, "method": f"clustered joint Wald, {len(terms)} terms", "chi2": stat},
    "highest": max(a7_rates, key=a7_rates.get), "lowest": min(a7_rates, key=a7_rates.get),
    "cramers_v": round(cramers, 4), "categories": len(big_categories),
    "unadjusted_spread": round(float(max(v["rate"] for v in unadjusted(a7_frame, "primary_category", "late").values()) - min(v["rate"] for v in unadjusted(a7_frame, "primary_category", "late").values())), 2),
}
checks["A7"] = a7.report

# ---------------------------------------------------------------- A2
timed("A2")
a2_frame = reviewed.copy()
a2_frame["status"] = np.where(a2_frame["late"].eq(1), "late", "on time")
a2_frame["multi_seller"] = a2_frame["multi_seller"].astype(float)
A2_CATEGORICAL = ["purchase_month", "state_group", "item_band", "category_group"]
A2_NUMERIC = ["log_order_value", "multi_seller"]
a2 = Model("A2", a2_frame, "low_rating", "status", "on time", ["on time", "late"], A2_CATEGORICAL, A2_NUMERIC)
a2_rates = a2.rates(a2.beta)
a2_boot = a2.bootstrap(lambda r: r["late"] - r["on time"], REPLICATES, next(seeds))
ols_design = a2.design.copy()
score_fit = sm.OLS(a2.frame["latest_review_score"].astype(float), ols_design).fit(cov_type="cluster", cov_kwds={"groups": a2.cluster_codes})
late_col = a2.level_columns["late"]
distribution = {status: {str(int(k)): round(100 * v, 2) for k, v in part["latest_review_score"].value_counts(normalize=True).sort_index().items()} for status, part in a2_frame.groupby("status")}
means = a2_frame.groupby("status")["latest_review_score"].mean()
results["A2"] = {
    "question": "Late delivery and low ratings", "predicted": "Late higher", "unit": "points",
    "unadjusted": unadjusted(a2_frame, "status", "low_rating"), "adjusted_rates": a2_rates,
    "estimate": a2_rates["late"] - a2_rates["on time"], "ci": interval(a2_boot), "test": a2.contrast_test("late"),
    "score_distribution_pct": distribution, "unadjusted_mean_scores": {k: round(float(v), 3) for k, v in means.items()},
    "adjusted_mean_score_difference": round(float(score_fit.params[late_col]), 3),
    "adjusted_mean_score_ci": [round(float(x), 3) for x in score_fit.conf_int().loc[late_col]],
    "late_orders_with_review": int(a2_frame["late"].sum()),
}
checks["A2"] = a2.report

# ---------------------------------------------------------------- A3
timed("A3")
a3_frame = reviewed[reviewed["late"].eq(1)].copy()
a3_frame["multi_seller"] = a3_frame["multi_seller"].astype(float)
a3 = Model("A3", a3_frame, "low_rating", "delay_band", "1-3 days", DELAY_BANDS, A2_CATEGORICAL, A2_NUMERIC)
a3_rates = a3.rates(a3.beta)
PAIRS = [("4-7 days", "1-3 days"), ("8-14 days", "4-7 days"), ("15+ days", "8-14 days"), ("15+ days", "1-3 days")]
a3_boot = a3.bootstrap(lambda r: [r[a] - r[b] for a, b in PAIRS], REPLICATES, next(seeds))
trend_frame = a3.frame.copy()
trend_design = a3.design.drop(columns=list(a3.level_columns.values())).copy()
trend_design["band_score"] = trend_frame["delay_band"].map({band: i for i, band in enumerate(DELAY_BANDS)}).astype(float)
trend = sm.GLM(a3.y, trend_design, family=sm.families.Binomial()).fit(cov_type="cluster", cov_kwds={"groups": a3.cluster_codes})
pairs = {}
for index, (a, b) in enumerate(PAIRS):
    pairs[f"{a} vs {b}"] = {"estimate": a3_rates[a] - a3_rates[b], "ci": interval(a3_boot[:, index]), "test": a3.contrast_test(a, b)}
results["A3"] = {
    "question": "Longer delays and low ratings", "predicted": "Rising with delay", "unit": "points",
    "unadjusted": unadjusted(a3_frame, "delay_band", "low_rating"), "adjusted_rates": a3_rates, "pairs": pairs,
    "estimate": pairs["15+ days vs 1-3 days"]["estimate"], "ci": pairs["15+ days vs 1-3 days"]["ci"],
    "test": {"p": float(trend.pvalues["band_score"]), "method": "clustered Wald trend across ordered bands",
             "per_band_log_odds": float(trend.params["band_score"]), "odds_ratio_per_band": float(np.exp(trend.params["band_score"])), "converged": bool(trend.converged)},
}
checks["A3"] = a3.report

# ---------------------------------------------------------------- Holm correction and labels
ORDER = ["A1", "A2", "A3", "A4", "A5", "A6", "A7"]
p_values = np.array([results[h]["test"]["p"] for h in ORDER])
ranking = np.argsort(p_values)
adjusted = np.empty(len(ORDER))
running = 0.0
for position, index in enumerate(ranking):
    running = max(running, min(1.0, p_values[index] * (len(ORDER) - position)))
    adjusted[index] = running
for hypothesis, value in zip(ORDER, adjusted):
    results[hypothesis]["holm_p"] = float(value)

CRITERIA = {"A1": LATE_POINTS, "A2": LOW_POINTS, "A3": LOW_POINTS, "A4": LATE_POINTS, "A5": LATE_POINTS, "A6": CONCENTRATION_POINTS, "A7": CATEGORY_POINTS}
NEEDS_ORDERS = {"A1", "A4", "A5"}
for hypothesis in ORDER:
    entry = results[hypothesis]
    criterion, estimate, (low, high) = CRITERIA[hypothesis], entry["estimate"], entry["ci"]
    holm_ok = entry["holm_p"] < 0.05
    orders_ok = hypothesis not in NEEDS_ORDERS or entry["late_orders_in_segment"] >= LATE_ORDERS
    if hypothesis == "A3":
        adjacent = [entry["pairs"][f"{a} vs {b}"] for a, b in PAIRS[:3]]
        all_adjacent = all(p["ci"][0] > 0 and p["estimate"] >= criterion for p in adjacent)
        entry["adjacent_pairs_meeting_criterion"] = sum(p["ci"][0] > 0 and p["estimate"] >= criterion for p in adjacent)
        if holm_ok and all_adjacent:
            label = "Supported"
        elif estimate <= 0 or not holm_ok:
            label = "Unsupported"
        else:
            label = "Inconclusive"
    elif estimate <= 0 or (low <= 0 and estimate < criterion):
        label = "Unsupported"
    elif low > 0 and holm_ok and estimate >= criterion and orders_ok:
        label = "Supported"
    elif low > 0 and holm_ok and (estimate < criterion or not orders_ok):
        label = "Detectable, not practically important"
    else:
        label = "Inconclusive"
    entry["criterion"] = criterion
    entry["label"] = label + " (provisional)"
    entry["interval_vs_criterion"] = "above" if low >= criterion else ("below" if high < criterion else "straddles")
    flags = []
    if low < criterion <= high or low <= criterion < high:
        flags.append("interval straddles the screening criterion")
    if abs(estimate - criterion) <= 0.2 * criterion:
        flags.append("estimate within 20% of the criterion")
    if 0.01 <= entry["holm_p"] <= 0.10:
        flags.append("Holm p between 0.01 and 0.10")
    if low <= 0 <= high:
        flags.append("interval includes zero")
    report = checks.get(hypothesis, {})
    if report.get("bootstrap_failure_pct", 0) > 1:
        flags.append("bootstrap failure rate above 1%")
    entry["recheck_flags"] = flags
    entry["recheck_with_more_replicates"] = bool(flags)

output = {"seed": SEED, "replicates": REPLICATES, "simulations": SIMULATIONS, "results": results, "checks": checks}
(OUT / "class_a_results.json").write_text(json.dumps(output, indent=1, default=str), encoding="utf-8")
timed("done")
