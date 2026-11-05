"""Validates the PostgreSQL export against the locked KPIs and the source CSV files.

Reads only local files in data/processed/ and the raw CSV folder. Doesn't connect to any
database, and writes nothing. Requires the packages in requirements.txt.

Usage: python python/validate_export.py [path-to-raw-csv-folder]
"""
import pathlib
import sys

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
TS = ["purchase_ts", "approved_ts", "carrier_ts", "delivered_ts", "estimated_ts"]
SOURCE = dict(zip(TS, ["order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date",
                       "order_delivered_customer_date", "order_estimated_delivery_date"]))
problems = []


def section(title):
    print(f"\n{'=' * 4} {title}")


def check(label, passed, detail=""):
    print(f"  {'PASS' if passed else 'FAIL'}  {label}{f'  ({detail})' if detail else ''}")
    if not passed:
        problems.append(label)


section("1. EXPORT FILES")
for name in ("validation.csv", "orders_analysis.csv", "zip_positions.csv", "timestamp_checks.csv"):
    path = OUT / name
    data = path.read_bytes()
    print(f"  {name:24}{len(data) / 1024:>10,.0f} KB  BOM {data.startswith(bytes([0xEF, 0xBB, 0xBF]))}  "
          f"status lines {data.count(chr(10).encode() + b'COPY ')}")
    check(f"{name} has no status lines", b"\nCOPY " not in data and b"\nBEGIN" not in data and b"\nROLLBACK" not in data)

export = pd.read_csv(OUT / "orders_analysis.csv", dtype=str, keep_default_na=False, na_values=[""])
for column in ["product_sales", "freight_value", "payment_total", "items_count", "seller_count", "review_count",
               "latest_review_score", "earliest_review_score", "latest_review_id_rows", "earliest_review_id_rows"]:
    export[column] = pd.to_numeric(export[column])
times = export[TS + ["latest_shipping_limit_ts", "latest_review_created_ts", "latest_review_answered_ts",
                     "earliest_review_created_ts", "earliest_review_answered_ts"]].apply(pd.to_datetime)
export["valid"] = export["valid_delivery_dates"].map({"t": True, "f": False, "true": True, "false": False})

section("2. LOCKED KPIS")
val = pd.read_csv(OUT / "validation.csv").set_index("metric")["value"]
delivered = export["order_status"].eq("delivered")
dated = delivered & times["delivered_ts"].notna()
on_time = dated & times["delivered_ts"].dt.normalize().le(times["estimated_ts"].dt.normalize())
late = dated & times["delivered_ts"].dt.normalize().gt(times["estimated_ts"].dt.normalize())
valid = delivered & export["valid"]
days = (times["delivered_ts"].dt.normalize() - times["purchase_ts"].dt.normalize()).dt.days
sales = export.loc[delivered, "product_sales"].sum()
recomputed = {
    "delivered_orders": int(delivered.sum()), "delivered_with_date": int(dated.sum()),
    "on_time_orders": int(on_time.sum()), "late_orders": int(late.sum()),
    "on_time_rate_pct": round(100 * on_time.sum() / dated.sum(), 2), "total_product_sales": round(sales, 2),
    "average_order_value": round(sales / delivered.sum(), 2), "average_delivery_days": round(days[valid].mean(), 2),
}
locked = {"delivered_orders": 96478, "delivered_with_date": 96470, "on_time_orders": 89936, "late_orders": 6534,
          "on_time_rate_pct": 93.23, "total_product_sales": 13221498.11, "average_order_value": 137.04,
          "average_delivery_days": 12.5}
for metric, target in locked.items():
    tolerance = 0.05 if metric == "average_delivery_days" else 0.005
    passed = abs(val[metric] - target) <= tolerance and abs(recomputed[metric] - target) <= tolerance
    check(f"{metric}: locked {target:,}", passed, f"validation.csv {val[metric]:,}; recalculated from rows {recomputed[metric]:,}")
check("orders in view 99,441", val["orders_in_view"] == 99441 and len(export) == 99441)
check("order IDs unique", export["order_id"].is_unique)
check("valid_delivery_dates FALSE 197", val["valid_delivery_dates_false"] == 197 and (delivered & ~export["valid"]).sum() == 197)

section("3. EXPORT AGAINST SOURCE CSVS: ORDERS")
orders = pd.read_csv(RAW / "olist_orders_dataset.csv", dtype=str, keep_default_na=False, na_values=[""]).set_index("order_id")
exp = export.set_index("order_id")
check("same order IDs", set(orders.index) == set(exp.index))
check("order status identical", exp["order_status"].reindex(orders.index).eq(orders["order_status"]).all())
frames = []
for column, source_column in SOURCE.items():
    stored = pd.to_datetime(exp[column].reindex(orders.index))
    source = pd.to_datetime(orders[source_column])
    both_missing = stored.isna() & source.isna()
    differs = ~both_missing & ~(stored == source)
    print(f"  {source_column:34} values {source.notna().sum():>7,}  differ {int(differs.sum()):>3}")
    if differs.any():
        frames.append(pd.DataFrame({"column": source_column, "source": source[differs], "stored": stored[differs],
                                    "shift_minutes": (stored[differs] - source[differs]).dt.total_seconds() / 60}))
order_diffs = pd.concat(frames) if frames else pd.DataFrame()
if len(order_diffs):
    print("  order timestamp differences:")
    print(order_diffs.reset_index().assign(order_id=lambda d: d["order_id"].str[:10]).to_string(index=False))

section("4. EXPORT AGAINST SOURCE CSVS: ITEMS, PAYMENTS, CUSTOMERS, SELLERS")
items = pd.read_csv(RAW / "olist_order_items_dataset.csv", parse_dates=["shipping_limit_date"])
payments = pd.read_csv(RAW / "olist_order_payments_dataset.csv")
customers = pd.read_csv(RAW / "olist_customers_dataset.csv", dtype=str)
sellers = pd.read_csv(RAW / "olist_sellers_dataset.csv", dtype=str).set_index("seller_id")
agg = items.groupby("order_id").agg(sales=("price", "sum"), freight=("freight_value", "sum"), n=("price", "size"),
                                    sellers=("seller_id", "nunique"), limit=("shipping_limit_date", "max"))
check("product_sales identical", np.isclose(exp["product_sales"].reindex(agg.index), agg["sales"], atol=0.005).all())
check("freight_value identical", np.isclose(exp["freight_value"].reindex(agg.index), agg["freight"], atol=0.005).all())
check("items_count identical", exp["items_count"].reindex(agg.index).eq(agg["n"]).all())
check("seller_count identical", exp["seller_count"].reindex(agg.index).eq(agg["sellers"]).all())
limit_stored = pd.to_datetime(exp["latest_shipping_limit_ts"].reindex(agg.index))
limit_diff = ~limit_stored.eq(agg["limit"])
print(f"  shipping limit differences: {int(limit_diff.sum())}")
missing_items = ~exp.index.isin(agg.index)
check("orders with no items have zero sales", exp.loc[missing_items, "product_sales"].eq(0).all(), f"{int(missing_items.sum())} orders")
paid = payments.groupby("order_id")["payment_value"].sum()
check("payment_total identical", np.isclose(exp["payment_total"].reindex(paid.index), paid, atol=0.005).all(), f"missing in source {int((~exp.index.isin(paid.index)).sum())}")
order_customer = orders["customer_id"].map(customers.set_index("customer_id")["customer_state"])
check("customer state identical", exp["customer_state"].reindex(orders.index).eq(order_customer).all())
order_zip = orders["customer_id"].map(customers.set_index("customer_id")["customer_zip_code_prefix"])
check("customer ZIP prefix identical", exp["customer_zip_code_prefix"].reindex(orders.index).eq(order_zip).all())
top = items.sort_values(["order_id", "price", "order_item_id"], ascending=[True, False, True]).drop_duplicates("order_id").set_index("order_id")
check("primary seller identical", exp["primary_seller_id"].reindex(top.index).eq(top["seller_id"]).all())
check("primary seller state identical", exp["primary_seller_state"].reindex(top.index).eq(top["seller_id"].map(sellers["seller_state"])).all())
check("primary seller ZIP identical", exp["primary_seller_zip_prefix"].reindex(top.index).eq(top["seller_id"].map(sellers["seller_zip_code_prefix"])).all())

section("5. EXPORT AGAINST SOURCE CSVS: REVIEWS")
review_cols = ["review_creation_date", "review_answer_timestamp"]
reviews = pd.read_csv(RAW / "olist_order_reviews_dataset.csv", parse_dates=review_cols)
order_keys = ["review_answer_timestamp", "review_creation_date", "review_id"]
latest = reviews.sort_values(order_keys, ascending=False).drop_duplicates("order_id").set_index("order_id")
earliest = reviews.sort_values(order_keys).drop_duplicates("order_id").set_index("order_id")
counts = reviews["order_id"].value_counts()
check("orders with reviews 98,673", exp["latest_review_score"].notna().sum() == 98673 and set(exp.index[exp["latest_review_score"].notna()]) == set(latest.index))
score_latest = exp["latest_review_score"].reindex(latest.index)
score_earliest = exp["earliest_review_score"].reindex(earliest.index)
print(f"  latest score differs from source: {int((score_latest != latest['review_score']).sum())}; earliest: {int((score_earliest != earliest['review_score']).sum())}")
check("latest review score identical", (score_latest == latest["review_score"]).all())
check("earliest review score identical", (score_earliest == earliest["review_score"]).all())
check("review_count identical", exp["review_count"].reindex(counts.index).eq(counts).all())
id_rows = reviews["review_id"].map(reviews["review_id"].value_counts())
latest_rows = latest.assign(rows=reviews.groupby("review_id")["review_id"].transform("size").groupby(reviews["review_id"]).first().reindex(latest["review_id"]).values)["rows"]
check("repeated-ID counts identical", exp["latest_review_id_rows"].reindex(latest.index).eq(latest_rows).all())
review_diffs = []
for name, frame, created, answered in (("latest", latest, "latest_review_created_ts", "latest_review_answered_ts"),
                                       ("earliest", earliest, "earliest_review_created_ts", "earliest_review_answered_ts")):
    for label, stored_col, source_col in (("created", created, "review_creation_date"), ("answered", answered, "review_answer_timestamp")):
        stored = pd.to_datetime(exp[stored_col].reindex(frame.index))
        differs = ~stored.eq(frame[source_col])
        print(f"  {name} review {label}: values {len(frame):,}, differ {int(differs.sum())}")
        if differs.any():
            review_diffs.append(pd.DataFrame({"which": name, "field": label, "source": frame.loc[differs, source_col], "stored": stored[differs]}))
if review_diffs:
    joined = pd.concat(review_diffs)
    joined["shift_minutes"] = (joined["stored"] - joined["source"]).dt.total_seconds() / 60
    print("  review timestamp differences by shift:", joined["shift_minutes"].value_counts().to_dict())
    print("  by date:", joined["source"].dt.date.astype(str).value_counts().to_dict())
    tied = reviews.merge(joined.reset_index()[["order_id"]].drop_duplicates(), on="order_id")
    print(f"  affected orders {joined.index.nunique()}")

section("6. CLOCK-CHANGE PREDICTION")
GAPS = [pd.Timestamp("2017-03-26 02:00"), pd.Timestamp("2018-03-25 02:00")]
HOUR = pd.Timedelta(hours=1)


def in_gap(series):
    return series.notna() & sum(((series >= g) & (series < g + HOUR)) for g in GAPS).astype(bool)


source_times = {c: pd.to_datetime(orders[SOURCE[c]]) for c in TS}
predicted = {c: int(in_gap(source_times[c]).sum()) for c in TS}
print(f"  source values inside the missing hours: {predicted}")
found = {c: int(in_gap(pd.to_datetime(exp[c].reindex(orders.index))).sum()) for c in TS}
print(f"  stored values inside the missing hours: {found}")
expected_diff = sum(predicted.values())
check("stored differences equal predicted clock-change values", len(order_diffs) == expected_diff, f"{len(order_diffs)} differences; predicted {expected_diff}")
if len(order_diffs):
    check("every order difference is exactly +60 minutes", order_diffs["shift_minutes"].eq(60).all())
    check("every differing source value lies in a missing hour", in_gap(order_diffs["source"]).all())
gap_diff = [c for c in TS if in_gap(pd.to_datetime(exp[c].reindex(orders.index))).any()]
print(f"  columns still holding values in those hours: {gap_diff or 'none'}")

section("7. TIMESTAMP CHECKS FILE")
checks = pd.read_csv(OUT / "timestamp_checks.csv", dtype=str, keep_default_na=False, na_values=[""]).set_index("order_id")
check("198 rows", len(checks) == 198, f"{len(checks)} rows")
parsed = checks.apply(lambda s: pd.to_datetime(s) if s.name.endswith("_ts") else s)
early_approval = parsed["approved_ts"] < parsed["purchase_ts"]
print(f"  approved before purchase: {int(early_approval.sum())}: {[i[:10] for i in checks.index[early_approval]]}")
check("exactly 1 approved before purchase, order 32b8249f", early_approval.sum() == 1 and checks.index[early_approval][0].startswith("32b8249f"))
categories = {
    "carrier before purchase": parsed["carrier_ts"] < parsed["purchase_ts"],
    "delivery before carrier": parsed["delivered_ts"] < parsed["carrier_ts"],
    "no delivery date": parsed["delivered_ts"].isna(),
    "carrier missing, delivery present": parsed["carrier_ts"].isna() & parsed["delivered_ts"].notna(),
}
for label, mask in categories.items():
    print(f"  {label:36}{int(mask.sum()):>4}")
flagged_only = sum(categories.values()).astype(bool)
check("197 flagged plus 1 approval-only order", flagged_only.sum() == 197 and (early_approval & ~flagged_only).sum() == 1)
source_flag = pd.to_datetime(orders["order_delivered_carrier_date"])
check("category counts 165, 23, 8, 1", [int(m.sum()) for m in categories.values()] == [165, 23, 8, 1])
flag_ids = set(exp.index[delivered.values & ~exp["valid"].values])
check("timestamp file holds the same 197 orders as the flag", flag_ids == set(checks.index[flagged_only]))

section("8. APRIL 2018 PATTERN IN STORED VALUES")
have = delivered & times["carrier_ts"].notna()
stored = pd.DataFrame({"purchase": times["purchase_ts"], "carrier": times["carrier_ts"], "approved": times["approved_ts"]})[have]
stored["month"] = stored["purchase"].dt.to_period("M")
stored["handover_hours"] = (stored["carrier"] - stored["purchase"]).dt.total_seconds() / 3600
profile = stored[stored["month"] >= pd.Period("2017-10")].groupby("month").agg(
    orders=("carrier", "size"),
    carrier_before_purchase=("handover_hours", lambda s: int((s < 0).sum())),
    midday=("carrier", lambda s: round(s.dt.hour.between(12, 15).mean() * 100, 1)),
    evening=("carrier", lambda s: round(s.dt.hour.between(17, 23).mean() * 100, 1)),
    median_hour=("carrier", lambda s: float(s.dt.hour.median())),
    median_handover_h=("handover_hours", lambda s: round(s.median(), 1)),
)
print(profile.to_string())
source_profile = pd.DataFrame({"purchase": source_times["purchase_ts"], "carrier": source_times["carrier_ts"]}).reindex(orders.index)
source_profile = source_profile[orders["order_status"].eq("delivered") & source_profile["carrier"].notna()]
source_table = source_profile.assign(month=source_profile["purchase"].dt.to_period("M"))
same = source_table[source_table["month"] >= pd.Period("2017-10")].groupby("month")["carrier"].agg(lambda s: round(s.dt.hour.between(17, 23).mean() * 100, 1))
check("monthly pattern identical to the source CSV", same.eq(profile["evening"]).all())
print("  by first carrier date (not purchase date), month of carrier timestamp:")
by_carrier = stored.assign(carrier_month=stored["carrier"].dt.to_period("M"))
carrier_profile = by_carrier[by_carrier["carrier_month"].between(pd.Period("2018-02"), pd.Period("2018-06"))].groupby("carrier_month")["carrier"].agg(
    orders="size", midday=lambda s: round(s.dt.hour.between(12, 15).mean() * 100, 1), evening=lambda s: round(s.dt.hour.between(17, 23).mean() * 100, 1))
print(carrier_profile.to_string())
day = by_carrier[by_carrier["carrier"].between("2018-04-01", "2018-05-15")].assign(date=lambda d: d["carrier"].dt.date)
daily = day.groupby("date")["carrier"].agg(orders="size", median_hour=lambda s: float(s.dt.hour.median()), evening=lambda s: round(s.dt.hour.between(17, 23).mean() * 100))
print("  daily carrier timestamps, April to mid-May 2018:")
print(daily.to_string())
others = pd.DataFrame({c: times[c].dt.hour for c in ["purchase_ts", "approved_ts", "delivered_ts"]})[have]
others["era"] = np.where(stored["purchase"].ge("2018-04-01"), "from Apr 2018", "before Apr 2018")
print("  median hour of the other timestamps, by period (a change in only the carrier field would leave these flat):")
print(others.groupby("era").median().to_string())

section("9. CATEGORY AND LOCATION FIELDS")
print(f"  primary category 'unknown', all orders {int(export['primary_category'].eq('unknown').sum()):,}; delivered with a date {int((export['primary_category'].eq('unknown') & dated).sum()):,}")
check("no orders lost through category joins", len(export) == 99441)
zips = pd.read_csv(OUT / "zip_positions.csv", dtype={"zip_prefix": str}).set_index("zip_prefix")
geo = pd.read_csv(RAW / "olist_geolocation_dataset.csv", dtype={"geolocation_zip_code_prefix": str})
inside = geo[geo["geolocation_lat"].between(-34, 6) & geo["geolocation_lng"].between(-74, -34)]
med = inside.groupby("geolocation_zip_code_prefix")[["geolocation_lat", "geolocation_lng"]].median()
check("ZIP prefix count identical", set(med.index) == set(zips.index), f"{len(zips):,}")
print(f"  largest median position difference from a CSV-based calculation: {(zips['median_lat'] - med['geolocation_lat']).abs().max():.5f} degrees latitude, {(zips['median_lng'] - med['geolocation_lng']).abs().max():.5f} longitude")
base_cust = exp.loc[dated.values]
print(f"  orders in base with no customer position {int((~base_cust['customer_zip_code_prefix'].isin(zips.index)).sum()):,}; no seller position {int((base_cust['primary_seller_zip_prefix'].notna() & ~base_cust['primary_seller_zip_prefix'].isin(zips.index)).sum()):,}")

section("10. MISSING CATEGORY VALUES")
products = pd.read_csv(RAW / "olist_products_dataset.csv", dtype=str)
blank_primary = export["primary_category"].isna()
blank_first = export["first_item_category"].isna()
print(f"  primary category: blank {int(blank_primary.sum()):,}, 'unknown' {int(export['primary_category'].eq('unknown').sum()):,}")
print(f"  first-item category: blank {int(blank_first.sum()):,}, 'unknown' {int(export['first_item_category'].eq('unknown').sum()):,}")
print(f"  in the base: blank primary category {int((blank_primary & dated).sum()):,}; blank first-item category {int((blank_first & dated).sum()):,}")
source_item = items.sort_values(["order_id", "price", "order_item_id"], ascending=[True, False, True]).drop_duplicates("order_id").merge(products[["product_id", "product_category_name"]], on="product_id", how="left").set_index("order_id")
source_missing = source_item["product_category_name"].isna()
stored_blank = exp["primary_category"].reindex(source_item.index).isna()
check("blank stored categories are the same orders as missing source categories", source_missing.eq(stored_blank).all(), f"{int(source_missing.sum()):,} orders")
check("no other field is unexpectedly blank", export[["order_status", "customer_state", "purchase_ts", "estimated_ts"]].notna().all().all())

section("11. EFFECT OF THE 60-MINUTE SHIFTS")
shifted_ids = set(order_diffs.index) if len(order_diffs) else set()
print(f"  orders with a shifted order timestamp: {len(shifted_ids)}")
src = pd.DataFrame({c: pd.to_datetime(orders[SOURCE[c]]) for c in TS})
sto = pd.DataFrame({c: pd.to_datetime(exp[c].reindex(orders.index)) for c in TS})
src_late = src["delivered_ts"].dt.normalize() > src["estimated_ts"].dt.normalize()
sto_late = sto["delivered_ts"].dt.normalize() > sto["estimated_ts"].dt.normalize()
print(f"  late status changes: {int((src_late != sto_late).sum())}")
month_change = src["purchase_ts"].dt.to_period("M") != sto["purchase_ts"].dt.to_period("M")
print(f"  purchase month changes: {int(month_change.sum())}; purchase date changes: {int((src['purchase_ts'].dt.date != sto['purchase_ts'].dt.date).sum())}")
def sequence_ok(t):
    return t["carrier_ts"].notna() & t["delivered_ts"].notna() & (t["carrier_ts"] >= t["purchase_ts"]) & (t["delivered_ts"] >= t["carrier_ts"])
print(f"  valid_delivery_dates changes: {int((sequence_ok(src) != sequence_ok(sto)).sum())}")
answer_source = latest["review_answer_timestamp"]
answer_stored = pd.to_datetime(exp["latest_review_answered_ts"].reindex(latest.index))
delivered_source = src["delivered_ts"].reindex(latest.index)
delivered_stored = sto["delivered_ts"].reindex(latest.index)
flips = ((answer_source < delivered_source) != (answer_stored < delivered_stored))
print(f"  answered-before-arrival label changes (latest review): {int(flips.sum())}")
answer_source_e = earliest["review_answer_timestamp"]
answer_stored_e = pd.to_datetime(exp["earliest_review_answered_ts"].reindex(earliest.index))
print(f"  answered-before-arrival label changes (earliest review): {int(((answer_source_e < src['delivered_ts'].reindex(earliest.index)) != (answer_stored_e < sto['delivered_ts'].reindex(earliest.index))).sum())}")
print(f"  low-rating label differences from source (latest review): {int(((score_latest <= 2) != (latest['review_score'] <= 2)).sum())}")

section("12. WHERE THE CARRIER-TIME CHANGE FALLS")
stored_d = pd.DataFrame({"purchase": times["purchase_ts"], "carrier": times["carrier_ts"], "delivered": times["delivered_ts"],
                         "limit": times["latest_shipping_limit_ts"], "valid": export["valid"], "late": late})[delivered & times["carrier_ts"].notna()]
before_purchase = stored_d[stored_d["carrier"] < stored_d["purchase"]]
small = before_purchase[(before_purchase["purchase"] - before_purchase["carrier"]) < pd.Timedelta(hours=3)]
print(f"  small-gap carrier-before-purchase orders {len(small)}; first carrier date {small['carrier'].min()}; last {small['carrier'].max()}")
print(f"  of those, carrier date from 2018-04-25: {int((small['carrier'] >= '2018-04-25').sum())}")
print(f"  larger-gap orders: {before_purchase[(before_purchase['purchase'] - before_purchase['carrier']) >= pd.Timedelta(hours=3)]['carrier'].dt.date.astype(str).tolist()}")
stored_d["weekday"] = stored_d["carrier"].dt.day_of_week < 5
week = stored_d[stored_d["weekday"]]
for label, frame in (("weekdays, 10-24 Apr", week[week["carrier"].between("2018-04-10", "2018-04-24 23:59:59")]),
                     ("weekdays, 25 Apr-9 May", week[week["carrier"].between("2018-04-25", "2018-05-09 23:59:59")])):
    minutes = frame["carrier"].dt.hour * 60 + frame["carrier"].dt.minute
    print(f"  {label}: n={len(frame):,}; median time {int(minutes.median() // 60):02d}:{int(minutes.median() % 60):02d}; 25th-75th percentile {int(minutes.quantile(.25) // 60):02d}:{int(minutes.quantile(.25) % 60):02d}-{int(minutes.quantile(.75) // 60):02d}:{int(minutes.quantile(.75) % 60):02d}")
stage = stored_d[stored_d["valid"]].copy()
stage["handover_h"] = (stage["carrier"] - stage["purchase"]).dt.total_seconds() / 3600
stage["transit_h"] = (stage["delivered"] - stage["carrier"]).dt.total_seconds() / 3600
stage["carrier_day_period"] = np.where(stage["carrier"] >= "2018-04-25", "carrier from 25 Apr 2018", "carrier before 25 Apr 2018")
stage["purchase_period"] = np.where(stage["purchase"] >= "2018-04-01", "purchase from Apr 2018", "purchase before Apr 2018")
print(pd.crosstab(stage["purchase_period"], stage["carrier_day_period"]).to_string())
print(stage.groupby("carrier_day_period").agg(orders=("late", "size"), median_handover_h=("handover_h", "median"), median_transit_h=("transit_h", "median"),
      seller_late_pct=("carrier", lambda s: round(100 * (s > stage.loc[s.index, "limit"]).mean(), 2)), late_pct=("late", lambda s: round(100 * s.mean(), 2))).round(1).to_string())

section("RESULT")
print("  ALL CHECKS PASSED" if not problems else f"  {len(problems)} CHECK(S) FAILED:")
for item in problems:
    print("   -", item)
