"""Shared helpers for the exploratory analysis: data loading, sparse-group handling and logistic models.

Uses the same rules as class_a.py: months and covariate levels with under 30 orders, or under 10
events or non-events, are merged. Risk differences are standardised, and intervals use a
seller-level cluster bootstrap applied through frequency weights.
"""
import pathlib

import numpy as np
import pandas as pd
import scipy.linalg as sla
import statsmodels.api as sm
from scipy.special import expit

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "processed"
SEED = 20261105
MIN_ORDERS, MIN_EVENTS = 30, 10
BOUNDARY = pd.Timestamp("2018-04-25")
DELAY_BANDS = ["1-3 days", "4-7 days", "8-14 days", "15+ days"]


def load_orders():
    """Analysis table plus the timestamps that exploratory questions need."""
    table = pd.read_csv(OUT / "analysis_orders.csv", keep_default_na=False, na_values=[""], dtype={"primary_seller_id": str},
                        parse_dates=["purchase_ts", "carrier_ts", "delivered_ts", "estimated_ts"])
    extra = pd.read_csv(OUT / "orders_analysis.csv", usecols=["order_id", "latest_shipping_limit_ts", "latest_review_answered_ts", "latest_review_created_ts"],
                        keep_default_na=False, na_values=[""], parse_dates=["latest_shipping_limit_ts", "latest_review_answered_ts", "latest_review_created_ts"])
    table = table.merge(extra, on="order_id", how="left", validate="one_to_one")
    answered_before = table["latest_review_answered_ts"] < table["delivered_ts"]
    table["answer_timing"] = np.where(table["has_review"], np.where(answered_before, "before arrival", "after arrival"), None)
    table["delivery_timing"] = np.where(table["late"].eq(0), "on time", np.where(answered_before, "late, answered before arrival", "late, answered after arrival"))
    table.loc[~table["has_review"], "delivery_timing"] = None
    table["multi_item"] = np.where(table["items_count"].ge(2), "multi-item", "single item")
    table["multi_seller"] = table["multi_seller"].astype(float)
    table["same_state_seller"] = table["same_state_seller"].astype(float)
    table["promise_days"] = (table["estimated_ts"].dt.normalize() - table["purchase_ts"].dt.normalize()).dt.days
    table["seller_late"] = np.where(table["carrier_ts"] > table["latest_shipping_limit_ts"], "late handover", "on-time handover")
    table["handover_days"] = (table["carrier_ts"] - table["purchase_ts"]).dt.total_seconds() / 86400
    table["later_stage_days"] = (table["delivered_ts"] - table["carrier_ts"]).dt.total_seconds() / 86400
    table["carrier_period"] = np.where(table["carrier_ts"] >= BOUNDARY, "from 25 Apr 2018", "before 25 Apr 2018")
    return table


def wilson(k, n, z=1.959964):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (100 * (c - m) / d, 100 * (c + m) / d)


def rate_row(part, outcome):
    k, n = int(part[outcome].sum()), len(part)
    if n < MIN_ORDERS:
        return {"orders": n, "events": None, "rate": None, "low": None, "high": None, "note": "under 30 orders, not reported"}
    low, high = wilson(k, n)
    return {"orders": n, "events": k, "rate": round(100 * k / n, 2), "low": round(low, 2), "high": round(high, 2)}


def merge_months(frame, outcome):
    table = frame.groupby("purchase_month")[outcome].agg(["size", "sum"]).sort_index()
    labelled, current, totals = [], [], [0, 0]
    for month, row in table.iterrows():
        current.append(month)
        totals = [totals[0] + int(row["size"]), totals[1] + int(row["sum"])]
        if totals[0] >= MIN_ORDERS and totals[1] >= MIN_EVENTS and totals[0] - totals[1] >= MIN_EVENTS:
            labelled.append(list(current))
            current, totals = [], [0, 0]
    if current:
        if labelled:
            labelled[-1].extend(current)
        else:
            labelled.append(list(current))
    mapping = {m: (g[0] if len(g) == 1 else f"{g[0]} to {g[-1]}") for g in labelled for m in g}
    return frame["purchase_month"].map(mapping), [g for g in labelled if len(g) > 1]


def collapse_sparse(frame, column, outcome):
    """Relabels sparse levels as 'other', and reports them. A lone sparse level is only renamed, so it stays separate."""
    table = frame.groupby(column)[outcome].agg(["size", "sum"])
    sparse = table[(table["size"] < MIN_ORDERS) | (table["sum"] < MIN_EVENTS) | (table["size"] - table["sum"] < MIN_EVENTS)]
    if sparse.empty:
        return frame[column], []
    return frame[column].where(~frame[column].isin(sparse.index), "other"), sorted(map(str, sparse.index))


class Logit:
    """Logistic model on a prepared design, with counterfactual designs for standardisation."""

    def __init__(self, name, frame, outcome, categorical, numeric, extra=None):
        self.name = name
        self.frame = frame.copy().reset_index(drop=True)
        self.report = {"orders": len(self.frame), "events": int(self.frame[outcome].sum()), "merged_months": [], "merged_levels": {}}
        parts = [pd.Series(1.0, index=self.frame.index, name="const")]
        for column in categorical:
            if column == "purchase_month":
                self.frame[column], merged = merge_months(self.frame, outcome)
                self.report["merged_months"] = merged
            else:
                self.frame[column], merged = collapse_sparse(self.frame, column, outcome)
                if merged:
                    self.report["merged_levels"][column] = merged
            dummies = pd.get_dummies(self.frame[column], prefix=column, prefix_sep="=", dtype=float)
            parts.append(dummies.drop(columns=dummies.sum().idxmax()))
        for column in numeric:
            parts.append(self.frame[column].astype(float))
        if extra is not None:
            parts.append(extra(self.frame))
        self.design = pd.concat(parts, axis=1)
        self.columns = list(self.design.columns)
        self.X = self.design.to_numpy(dtype=float)
        self.y = self.frame[outcome].to_numpy(dtype=float)
        self.codes, uniques = pd.factorize(self.frame["primary_seller_id"])
        self.n_clusters = len(uniques)
        self.report.update({"parameters": len(self.columns), "sellers": self.n_clusters,
                            "events_per_parameter": round(self.report["events"] / len(self.columns), 1),
                            "non_events_per_parameter": round((self.report["orders"] - self.report["events"]) / len(self.columns), 1)})
        self.beta, converged, iterations = self._irls()
        self.wald = sm.GLM(self.y, self.design, family=sm.families.Binomial()).fit(cov_type="cluster", cov_kwds={"groups": self.codes})
        scale = self.X.std(axis=0)
        self.report.update({"converged": bool(converged and self.wald.converged), "iterations": int(iterations),
                            "largest_abs_coefficient": round(float(np.max(np.abs(self.beta))), 2),
                            "largest_standard_error": round(float(self.wald.bse.max()), 2),
                            "condition_number": round(float(np.linalg.cond(self.X / np.where(scale > 0, scale, 1.0))), 1)})
        # Diagnostics only: these don't change any estimate.
        coefficients = pd.Series(self.beta, index=self.columns).drop("const")
        self.report["largest_coefficients"] = {k: round(float(coefficients[k]), 2) for k in coefficients.abs().sort_values(ascending=False).head(3).index}
        thin = {}
        for column in self.columns:
            values = self.design[column].to_numpy()
            if column != "const" and set(np.unique(values)) <= {0.0, 1.0}:
                inside = values == 1
                events, non_events = int(self.y[inside].sum()), int(inside.sum() - self.y[inside].sum())
                if events < 5 or non_events < 5:
                    thin[column] = {"orders": int(inside.sum()), "events": events, "non_events": non_events}
        self.report["thin_terms"] = thin
        still_sparse = {}
        for column in categorical:
            table = self.frame.groupby(column)[outcome].agg(["size", "sum"])
            sparse = table[(table["size"] < MIN_ORDERS) | (table["sum"] < MIN_EVENTS) | (table["size"] - table["sum"] < MIN_EVENTS)]
            if not sparse.empty:
                still_sparse[column] = {str(k): {"orders": int(v["size"]), "events": int(v["sum"])} for k, v in sparse.iterrows()}
        self.report["levels_still_sparse_after_merging"] = still_sparse

    def _irls(self, weights=None, start=None, tolerance=1e-7, max_iterations=50):
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
            A = (X * weight[:, None]).T @ X + ridge
            b = (X * weight[:, None]).T @ (eta + (y - mu) / variance)
            try:
                new = sla.solve(A, b, assume_a="pos", check_finite=False)
            except (sla.LinAlgError, ValueError):
                return beta, False, iteration
            if np.max(np.abs(new - beta)) < tolerance:
                return new, True, iteration
            beta = new
        return beta, False, max_iterations

    def counterfactual(self, changes):
        """Design matrix with named columns set to fixed values or arrays."""
        X = self.X.copy()
        for column, value in changes.items():
            X[:, self.columns.index(column)] = value
        return X

    def bootstrap(self, statistic, replicates, seed):
        """statistic(beta, weights) returns a list of numbers. Weights are 1 for the point estimate."""
        rng = np.random.default_rng(seed)
        estimates, failures = [], 0
        for _ in range(replicates):
            counts = rng.multinomial(self.n_clusters, np.full(self.n_clusters, 1 / self.n_clusters))
            weights = counts[self.codes].astype(float)
            beta, converged, _ = self._irls(weights=weights, start=self.beta, tolerance=1e-6)
            if not converged or np.max(np.abs(beta)) > 25:
                failures += 1
                continue
            estimates.append(statistic(beta, weights))
        self.report.update({"bootstrap_replicates": replicates, "bootstrap_failures": failures,
                            "bootstrap_failure_pct": round(100 * failures / replicates, 2), "bootstrap_reliable": failures / replicates <= 0.05})
        return np.array(estimates, dtype=float)

    def odds_ratio(self, column):
        i = list(self.wald.params.index).index(column)
        estimate, se = float(self.wald.params.iloc[i]), float(self.wald.bse.iloc[i])
        return {"odds_ratio": round(float(np.exp(estimate)), 3), "low": round(float(np.exp(estimate - 1.959964 * se)), 3),
                "high": round(float(np.exp(estimate + 1.959964 * se)), 3), "p": float(self.wald.pvalues.iloc[i])}

    def mean_score_difference(self, column):
        fit = sm.OLS(self.frame["latest_review_score"].astype(float), self.design).fit(cov_type="cluster", cov_kwds={"groups": self.codes})
        low, high = fit.conf_int().loc[column]
        return {"difference": round(float(fit.params[column]), 3), "low": round(float(low), 3), "high": round(float(high), 3)}


def risk(beta, X, weights=None, mask=None):
    """Standardised risk, in percent."""
    keep = np.ones(len(X), bool) if mask is None else mask.copy()
    w = np.ones(len(X)) if weights is None else weights
    keep &= w > 0
    return 100 * float(np.average(expit(X[keep] @ beta), weights=w[keep]))


def interval(values):
    return [round(float(np.percentile(values, 2.5)), 2), round(float(np.percentile(values, 97.5)), 2)]


def seller_weights(codes, count, rng):
    return rng.multinomial(count, np.full(count, 1 / count))[codes].astype(float)
