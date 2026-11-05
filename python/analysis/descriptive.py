"""Stage 2, step 6: Class C descriptive context. Measurements only, with no hypothesis tests.

Covers delivered orders with a delivery date. Late rates are shown beside absolute counts, and
growth compares the same months. Writes data/processed/descriptive_results.json, which Git ignores.
"""
import json

import numpy as np
import pandas as pd

from modeling import OUT, load_orders

data = load_orders()
out = {}

monthly = data.groupby("purchase_month").agg(orders=("late", "size"), sales=("product_sales", "sum"), late=("late", "sum"),
                                             median_promise_days=("promise_days", "median"), median_actual_days=("delivery_days", "median")).reset_index()
monthly["aov"] = (monthly["sales"] / monthly["orders"]).round(2)
monthly["sales"] = monthly["sales"].round(2)
monthly["late_rate_pct"] = (100 * monthly["late"] / monthly["orders"]).round(2)
out["monthly"] = monthly.to_dict("records")

first = data[data["purchase_ts"].dt.year.eq(2017) & data["purchase_ts"].dt.month.le(8)]
second = data[data["purchase_ts"].dt.year.eq(2018) & data["purchase_ts"].dt.month.le(8)]
s1, s2, n1, n2 = first["product_sales"].sum(), second["product_sales"].sum(), len(first), len(second)
a1, a2 = s1 / n1, s2 / n2
out["growth_jan_aug"] = {"sales_2017": round(s1, 2), "sales_2018": round(s2, 2), "orders_2017": n1, "orders_2018": n2, "aov_2017": round(a1, 2), "aov_2018": round(a2, 2),
                         "sales_change": round(s2 - s1, 2), "sales_change_pct": round(100 * (s2 / s1 - 1), 1), "orders_change_pct": round(100 * (n2 / n1 - 1), 1), "aov_change_pct": round(100 * (a2 / a1 - 1), 2),
                         "volume_effect": round((n2 - n1) * a1, 2), "order_value_effect": round((a2 - a1) * n2, 2), "volume_share_of_change_pct": round(100 * (n2 - n1) * a1 / (s2 - s1), 1)}

reviewed = data[data["has_review"]]
total_sales, total_late, total_low = data["product_sales"].sum(), data["late"].sum(), reviewed["low_rating"].sum()
state = data.groupby("customer_state").agg(orders=("late", "size"), sales=("product_sales", "sum"), late=("late", "sum"),
                                           median_promise_days=("promise_days", "median"), median_actual_days=("delivery_days", "median"))
state["low_ratings"] = reviewed.groupby("customer_state")["low_rating"].sum().astype(int)
state["reviewed"] = reviewed.groupby("customer_state").size()
state["late_rate_pct"] = (100 * state["late"] / state["orders"]).round(2)
state["low_rate_pct"] = (100 * state["low_ratings"] / state["reviewed"]).round(2)
state["sales_share_pct"] = (100 * state["sales"] / total_sales).round(2)
state["late_share_pct"] = (100 * state["late"] / total_late).round(2)
state["low_share_pct"] = (100 * state["low_ratings"] / total_low).round(2)
state["orders_share_pct"] = (100 * state["orders"] / len(data)).round(2)
state["late_sales"] = data[data["late"].eq(1)].groupby("customer_state")["product_sales"].sum().round(2)
state = state.sort_values("late", ascending=False)
state["sales"] = state["sales"].round(2)
out["priority_view_by_state"] = state.head(12).reset_index().to_dict("records")
out["state_concentration"] = {"top3_sales_share_pct": round(100 * data.groupby("customer_state")["product_sales"].sum().nlargest(3).sum() / total_sales, 2),
                              "top3_late_share_pct": round(100 * state["late"].nlargest(3).sum() / total_late, 2),
                              "sp_rj_late_share_pct": round(100 * state.loc[["SP", "RJ"], "late"].sum() / total_late, 2),
                              "sp_rj_orders_share_pct": round(100 * state.loc[["SP", "RJ"], "orders"].sum() / len(data), 2),
                              "states": int(state.shape[0])}

category = data.groupby("primary_category").agg(orders=("late", "size"), sales=("product_sales", "sum"), late=("late", "sum"))
category["sales_share_pct"] = (100 * category["sales"] / total_sales).round(2)
category["late_rate_pct"] = (100 * category["late"] / category["orders"]).round(2)
category["sales"] = category["sales"].round(2)
out["top_categories_by_sales"] = category.sort_values("sales", ascending=False).head(10).reset_index().to_dict("records")

out["promise_vs_actual"] = {"median_promise_days": float(data["promise_days"].median()), "median_actual_days": float(data["delivery_days"].median()),
                            "median_days_early": float((-data["days_late"]).median()), "orders_early_by_7plus_days_pct": round(100 * data["days_late"].le(-7).mean(), 2)}
out["exposure"] = {"orders": len(data), "late_orders": int(total_late), "late_rate_pct": round(100 * data["late"].mean(), 2),
                   "late_order_sales": round(float(data.loc[data["late"].eq(1), "product_sales"].sum()), 2), "late_sales_share_pct": round(100 * data.loc[data["late"].eq(1), "product_sales"].sum() / total_sales, 2),
                   "total_sales_in_base": round(float(total_sales), 2), "reviewed": len(reviewed), "low_ratings": int(total_low), "low_rate_pct": round(100 * reviewed["low_rating"].mean(), 2)}
out["seasonality_note"] = "At most one complete year of data, so no seasonal claim is made."
(OUT / "descriptive_results.json").write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
print("descriptive done")
_ = np
