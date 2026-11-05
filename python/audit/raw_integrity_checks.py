"""Step 8: data-integrity checks on the raw CSV files, independent of the project's analysis code.

Uses only the standard library. Reads the raw folder, and writes one JSON file to the path given.
Doesn't read data/processed/.

Usage: python python/audit/raw_integrity_checks.py <raw-csv-folder> <output-json>
"""
import collections
import csv
import json
import pathlib
import sys
from datetime import datetime, timedelta
from decimal import Decimal

RAW, OUTPUT = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
FMT = "%Y-%m-%d %H:%M:%S"


def read(name):
    with open(RAW / name, encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def when(value):
    return datetime.strptime(value, FMT) if value else None


orders, items, customers, sellers = read("olist_orders_dataset.csv"), read("olist_order_items_dataset.csv"), read("olist_customers_dataset.csv"), read("olist_sellers_dataset.csv")
products, translation, reviews, payments = read("olist_products_dataset.csv"), read("product_category_name_translation.csv"), read("olist_order_reviews_dataset.csv"), read("olist_order_payments_dataset.csv")
out = {}

# Keys and joins
order_ids = {r["order_id"] for r in orders}
customer_ids = collections.Counter(r["customer_id"] for r in customers)
seller_ids = collections.Counter(r["seller_id"] for r in sellers)
product_ids = collections.Counter(r["product_id"] for r in products)
translated = collections.Counter(r["product_category_name"] for r in translation)
item_keys = collections.Counter((r["order_id"], r["order_item_id"]) for r in items)
out["keys"] = {
    "row_counts": {"orders": len(orders), "items": len(items), "customers": len(customers), "sellers": len(sellers), "products": len(products), "translation": len(translation), "reviews": len(reviews), "payments": len(payments)},
    "duplicate_order_ids": len(orders) - len(order_ids), "duplicate_customer_ids": sum(v > 1 for v in customer_ids.values()), "duplicate_seller_ids": sum(v > 1 for v in seller_ids.values()),
    "duplicate_product_ids": sum(v > 1 for v in product_ids.values()), "duplicate_translation_keys": sum(v > 1 for v in translated.values()), "duplicate_item_keys": sum(v > 1 for v in item_keys.values()),
    "items_without_order": sum(r["order_id"] not in order_ids for r in items), "items_without_seller": sum(r["seller_id"] not in seller_ids for r in items), "items_without_product": sum(r["product_id"] not in product_ids for r in items),
    "orders_without_customer": sum(r["customer_id"] not in customer_ids for r in orders), "reviews_without_order": sum(r["order_id"] not in order_ids for r in reviews), "payments_without_order": sum(r["order_id"] not in order_ids for r in payments),
}

# Categories
blank = sum(not r["product_category_name"] for r in products)
untranslated = sorted({r["product_category_name"] for r in products if r["product_category_name"] and r["product_category_name"] not in translated})
product_name = {r["product_id"]: r["product_category_name"] for r in products}
out["categories"] = {"products_blank": blank, "names_without_translation": untranslated, "item_rows_with_untranslated_name": sum(product_name.get(r["product_id"]) in untranslated for r in items)}

# Values
status = collections.Counter(r["order_status"] for r in orders)
delivered = [r for r in orders if r["order_status"] == "delivered"]
delivered_ids = {r["order_id"] for r in delivered}
item_ids = {r["order_id"] for r in items}
order_total = collections.defaultdict(Decimal)
for r in items:
    order_total[r["order_id"]] += Decimal(r["price"]) + Decimal(r["freight_value"])
payment_total = collections.defaultdict(Decimal)
for r in payments:
    payment_total[r["order_id"]] += Decimal(r["payment_value"])
mismatch = [o for o in delivered_ids if o in payment_total and abs(order_total[o] - payment_total[o]) > Decimal("0.05")]
out["values"] = {"status": dict(status), "delivered_without_items": len(delivered_ids - item_ids), "delivered_without_payments": len(delivered_ids - set(payment_total)), "zero_or_negative_price_rows": sum(Decimal(r["price"]) <= 0 for r in items), "zero_freight_rows": sum(Decimal(r["freight_value"]) == 0 for r in items),
                 "delivered_payment_differs_from_price_plus_freight": len(mismatch), "all_orders_without_items": len(order_ids - item_ids), "estimated_date_missing_delivered": sum(not r["order_estimated_delivery_date"] for r in delivered), "non_midnight_estimated": sum(not r["order_estimated_delivery_date"].endswith("00:00:00") for r in delivered)}

# The 197 flagged sequences, with overlaps counted rather than assumed away
flags = collections.Counter()
detail = {"carrier_before_purchase_gap_under_3h": 0, "carrier_before_purchase_gap_3h_or_more": 0, "under_3h_from_boundary": 0, "under_3h_before_boundary": 0, "approved_before_purchase": 0}
flagged = {}
boundary = datetime(2018, 4, 25)
for r in delivered:
    p, a, c, d, e = map(when, (r["order_purchase_timestamp"], r["order_approved_at"], r["order_delivered_carrier_date"], r["order_delivered_customer_date"], r["order_estimated_delivery_date"]))
    names = []
    if d is None:
        names.append("no delivery date")
    if c is None:
        names.append("no carrier date")
    if c and c < p:
        names.append("carrier before purchase")
        gap = p - c
        detail["carrier_before_purchase_gap_under_3h" if gap < timedelta(hours=3) else "carrier_before_purchase_gap_3h_or_more"] += 1
        if gap < timedelta(hours=3):
            detail["under_3h_from_boundary" if c >= boundary else "under_3h_before_boundary"] += 1
    if c and d and d < c:
        names.append("delivery before carrier")
    if d and d < p:
        names.append("delivery before purchase")
    if a and a < p:
        detail["approved_before_purchase"] += 1
    if names:
        flags[" + ".join(names)] += 1
        flagged[r["order_id"]] = (names, d, e)
in_base = {k: v for k, v in flagged.items() if v[1] is not None}
out["flagged"] = {"combinations": dict(flags), "total": len(flagged), "in_base": len(in_base), "late_in_base": sum(v[1].date() > v[2].date() for v in in_base.values()), "stage_eligible": sum(1 for r in delivered if r["order_delivered_customer_date"]) - len(in_base), **detail}

# Reviews
review_per_order = collections.Counter(r["order_id"] for r in reviews)
review_id_rows = collections.Counter(r["review_id"] for r in reviews)
full_ties = collections.Counter((r["order_id"], r["review_answer_timestamp"], r["review_creation_date"]) for r in reviews)
by_order = collections.defaultdict(list)
for r in reviews:
    by_order[r["order_id"]].append(r)
differs = sum(len({r["review_score"] for r in v}) > 1 for v in by_order.values() if len(v) > 1)
purchase = {r["order_id"]: when(r["order_purchase_timestamp"]) for r in orders}
out["reviews"] = {"rows": len(reviews), "orders_with_review": len(by_order), "orders_with_several": sum(v > 1 for v in review_per_order.values()), "several_with_different_scores": differs, "review_ids_on_several_rows": sum(v > 1 for v in review_id_rows.values()),
                  "same_order_answer_and_created_ties": sum(v > 1 for v in full_ties.values()), "answer_before_created": sum(when(r["review_answer_timestamp"]) < when(r["review_creation_date"]) for r in reviews), "created_not_midnight": sum(not r["review_creation_date"].endswith("00:00:00") for r in reviews),
                  "created_before_purchase_date": sum(when(r["review_creation_date"]).date() < purchase[r["order_id"]].date() for r in reviews), "score_outside_1_5": sum(r["review_score"] not in {"1", "2", "3", "4", "5"} for r in reviews), "on_delivered_orders": sum(r["order_id"] in delivered_ids for r in reviews)}
cleaned_path = RAW / "olist_order_reviews_cleaned.csv"
if cleaned_path.exists():
    with open(cleaned_path, encoding="utf-8", newline="") as handle:
        cleaned = list(csv.DictReader(handle, escapechar="\\", doublequote=False))
    fields = ("review_id", "order_id", "review_score", "review_creation_date", "review_answer_timestamp")
    out["reviews"]["cleaned_rows"] = len(cleaned)
    out["reviews"]["cleaned_rows_differing_on_analysis_fields"] = sum(any(a[f] != b[f] for f in fields) for a, b in zip(reviews, cleaned))

# Spain's missing hours in the source
HOURS = ((datetime(2017, 3, 26, 2), datetime(2017, 3, 26, 3)), (datetime(2018, 3, 25, 2), datetime(2018, 3, 25, 3)))


def missing_hour(value):
    t = when(value)
    return bool(t) and any(a <= t < b for a, b in HOURS)


out["missing_hours"] = {"purchase": sum(missing_hour(r["order_purchase_timestamp"]) for r in orders), "approved": sum(missing_hour(r["order_approved_at"]) for r in orders), "carrier": sum(missing_hour(r["order_delivered_carrier_date"]) for r in orders), "delivered": sum(missing_hour(r["order_delivered_customer_date"]) for r in orders),
                        "review_answer_rows": sum(missing_hour(r["review_answer_timestamp"]) for r in reviews), "review_answer_orders": len({r["order_id"] for r in reviews if missing_hour(r["review_answer_timestamp"])}), "shipping_limit": sum(missing_hour(r["shipping_limit_date"]) for r in items)}

# Undelivered orders by purchase month, for survivorship
months = collections.defaultdict(lambda: [0, 0])
for r in orders:
    m = r["order_purchase_timestamp"][:7]
    months[m][0] += 1
    months[m][1] += r["order_status"] != "delivered"
out["undelivered_by_month"] = {m: {"orders": v[0], "undelivered": v[1], "pct": round(100 * v[1] / v[0], 2)} for m, v in sorted(months.items())}
OUTPUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
print(json.dumps(out, indent=1))
