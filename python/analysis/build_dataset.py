"""Stage 2, step 0: builds the order-level analysis table and reproduces the locked KPIs.

Reads the PostgreSQL export in data/processed/ and writes data/processed/analysis_orders.csv,
which Git ignores. KPIs are also recalculated separately from the raw CSV files. Any mismatch
stops the work. Connects to no database.

Usage: python python/analysis/build_dataset.py [path-to-raw-csv-folder]
"""
import pathlib
import sys

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "processed"
RAW = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "raw"

LOCKED = {"delivered_orders": 96478, "delivered_with_date": 96470, "on_time_orders": 89936, "late_orders": 6534,
          "on_time_rate_pct": 93.23, "total_product_sales": 13221498.11, "average_order_value": 137.04,
          "average_delivery_days": 12.5}
DISTANCE_BANDS = ["0-100 km", "100-300 km", "300-600 km", "600-1,000 km", "1,000-2,000 km", "2,000+ km"]
DELAY_BANDS = ["1-3 days", "4-7 days", "8-14 days", "15+ days"]
TIME_COLUMNS = ["purchase_ts", "approved_ts", "carrier_ts", "delivered_ts", "estimated_ts", "latest_shipping_limit_ts",
                "latest_review_created_ts", "latest_review_answered_ts", "earliest_review_created_ts", "earliest_review_answered_ts"]


def haversine_km(lat1, lng1, lat2, lng2):
    lat1, lng1, lat2, lng2 = map(np.radians, (lat1, lng1, lat2, lng2))
    h = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lng2 - lng1) / 2) ** 2
    return 6371.0088 * 2 * np.arcsin(np.sqrt(h))


export = pd.read_csv(OUT / "orders_analysis.csv", dtype={"customer_zip_code_prefix": str, "primary_seller_zip_prefix": str},
                     keep_default_na=False, na_values=[""])
for column in TIME_COLUMNS:
    export[column] = pd.to_datetime(export[column])
export["valid"] = export["valid_delivery_dates"].astype(str).str.lower().map({"t": True, "true": True, "f": False, "false": False})

# Approved rule: blank and NULL categories are both "unknown".
for column in ("primary_category", "first_item_category"):
    export[column] = export[column].fillna("unknown").replace("", "unknown")

delivered = export["order_status"].eq("delivered")
base = export[delivered & export["delivered_ts"].notna()].copy()

# Delivery status, using calendar dates as in the corrected Power BI measure.
base["late"] = base["delivered_ts"].dt.normalize().gt(base["estimated_ts"].dt.normalize()).astype(int)
base["days_late"] = (base["delivered_ts"].dt.normalize() - base["estimated_ts"].dt.normalize()).dt.days
base["delay_band"] = pd.cut(base["days_late"], [0, 3, 7, 14, np.inf], labels=DELAY_BANDS, right=True).astype(object)
base["delivery_days"] = (base["delivered_ts"].dt.normalize() - base["purchase_ts"].dt.normalize()).dt.days
base["purchase_month"] = base["purchase_ts"].dt.strftime("%Y-%m")

# Order characteristics.
base["item_band"] = np.select([base["items_count"].eq(1), base["items_count"].eq(2)], ["1 item", "2 items"], "3+ items")
base["log_order_value"] = np.log(base["product_sales"])
base["multi_seller"] = base["seller_count"].gt(1).astype(int)
base["single_seller"] = base["seller_count"].eq(1)
base["same_state_seller"] = base["customer_state"].eq(base["primary_seller_state"]).astype(int)

# Distance: single-seller orders with a position at both ends.
positions = pd.read_csv(OUT / "zip_positions.csv", dtype={"zip_prefix": str}).set_index("zip_prefix")
customer = positions.reindex(base["customer_zip_code_prefix"])
seller = positions.reindex(base["primary_seller_zip_prefix"])
distance = haversine_km(customer["median_lat"].to_numpy(), customer["median_lng"].to_numpy(),
                        seller["median_lat"].to_numpy(), seller["median_lng"].to_numpy())
base["distance_km"] = np.where(base["single_seller"], distance, np.nan)
base["distance_band"] = pd.cut(base["distance_km"], [-0.001, 100, 300, 600, 1000, 2000, np.inf], labels=DISTANCE_BANDS, right=False).astype(object)

# Groupings fixed in docs/analysis_plan.md.
state_counts = base["customer_state"].value_counts()
base["state_group"] = base["customer_state"].where(base["customer_state"].map(state_counts).ge(1000), "other")
named = base.loc[base["primary_category"].ne("unknown"), "primary_category"].value_counts()
top_categories = set(named.head(15).index)
base["category_group"] = np.where(base["primary_category"].eq("unknown"), "unknown",
                                  np.where(base["primary_category"].isin(top_categories), base["primary_category"], "other"))

# Latest answered review is primary.
base["has_review"] = base["latest_review_score"].notna()
base["low_rating"] = np.where(base["has_review"], base["latest_review_score"].le(2).astype(float), np.nan)

keep = ["order_id", "primary_seller_id", "customer_state", "state_group", "purchase_month", "purchase_ts", "carrier_ts", "delivered_ts", "estimated_ts",
        "valid", "late", "days_late", "delay_band", "delivery_days", "product_sales", "log_order_value", "freight_value", "items_count",
        "item_band", "seller_count", "multi_seller", "single_seller", "primary_seller_state", "same_state_seller", "distance_km", "distance_band",
        "primary_category", "category_group", "has_review", "latest_review_score", "low_rating"]
base[keep].to_csv(OUT / "analysis_orders.csv", index=False)

# KPI check 1: from the analysis table and the export.
all_delivered = export[delivered]
late_orders = int(base["late"].sum())
sales = all_delivered["product_sales"].sum()
from_table = {
    "delivered_orders": len(all_delivered), "delivered_with_date": len(base), "on_time_orders": len(base) - late_orders, "late_orders": late_orders,
    "on_time_rate_pct": round(100 * (len(base) - late_orders) / len(base), 2), "total_product_sales": round(sales, 2),
    "average_order_value": round(sales / len(all_delivered), 2), "average_delivery_days": round(base.loc[base["valid"], "delivery_days"].mean(), 2),
}

# KPI check 2: separately from the raw CSV files, sharing no calculations with the table above.
orders = pd.read_csv(RAW / "olist_orders_dataset.csv", parse_dates=["order_purchase_timestamp", "order_delivered_carrier_date", "order_delivered_customer_date", "order_estimated_delivery_date"])
prices = pd.read_csv(RAW / "olist_order_items_dataset.csv", usecols=["order_id", "price"])
raw_delivered = orders[orders["order_status"] == "delivered"]
raw_dated = raw_delivered[raw_delivered["order_delivered_customer_date"].notna()]
raw_on_time = (raw_dated["order_delivered_customer_date"].dt.date <= raw_dated["order_estimated_delivery_date"].dt.date).sum()
raw_sales = prices[prices["order_id"].isin(raw_delivered["order_id"])]["price"].sum()
sequence = (raw_delivered["order_delivered_carrier_date"] >= raw_delivered["order_purchase_timestamp"]) & (raw_delivered["order_delivered_customer_date"] >= raw_delivered["order_delivered_carrier_date"])
raw_valid = raw_delivered[sequence]
raw_days = (raw_valid["order_delivered_customer_date"].dt.normalize() - raw_valid["order_purchase_timestamp"].dt.normalize()).dt.days
from_raw = {
    "delivered_orders": len(raw_delivered), "delivered_with_date": len(raw_dated), "on_time_orders": int(raw_on_time), "late_orders": int(len(raw_dated) - raw_on_time),
    "on_time_rate_pct": round(100 * raw_on_time / len(raw_dated), 2), "total_product_sales": round(raw_sales, 2),
    "average_order_value": round(raw_sales / len(raw_delivered), 2), "average_delivery_days": round(raw_days.mean(), 2),
}

print("KPI                        locked          analysis table      raw CSVs")
failed = []
for metric, target in LOCKED.items():
    tolerance = 0.05 if metric == "average_delivery_days" else 0.005
    good = abs(from_table[metric] - target) <= tolerance and abs(from_raw[metric] - target) <= tolerance
    print(f"{metric:24}{target:>14,}{from_table[metric]:>18,}{from_raw[metric]:>16,}   {'PASS' if good else 'FAIL'}")
    if not good:
        failed.append(metric)
if failed:
    sys.exit(f"STOP: KPI mismatch {failed}")

print(f"\nanalysis table: {len(base):,} orders, {len(keep)} columns")
print(f"single-seller {int(base['single_seller'].sum()):,}; multi-seller {int((~base['single_seller']).sum()):,}")
print(f"with a distance {int(base['distance_km'].notna().sum()):,}; single-seller without {int((base['single_seller'] & base['distance_km'].isna()).sum()):,}")
print(f"with a review {int(base['has_review'].sum()):,}; without {int((~base['has_review']).sum()):,}")
print(f"category 'unknown' {int(base['primary_category'].eq('unknown').sum()):,}; 'other' group {int(base['category_group'].eq('other').sum()):,}")
print(f"state groups: {sorted(base['state_group'].unique())}")
print(f"top 15 categories: {sorted(top_categories)}")
print(f"purchase months {base['purchase_month'].nunique()}: smallest {base['purchase_month'].value_counts().tail(4).to_dict()}")
print(f"distance range {base['distance_km'].min():.1f} to {base['distance_km'].max():.1f} km; order value zero or less {int((base['product_sales'] <= 0).sum())}")
print("step 0 passed")
