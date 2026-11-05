"""Reproduces the figures quoted in this repository from the source CSV files.

Written during publication, not part of the original analysis. It exists so the
findings without a saved SQL query (such as the payment reconciliation) can be
checked by anyone. It only reads files and uses no external packages.

Usage: python python/verify_figures.py [path-to-raw-csv-folder]
"""
import collections
import csv
import pathlib
import sys
from datetime import datetime, timedelta
from decimal import Decimal

DEFAULT_RAW = pathlib.Path(__file__).resolve().parent.parent / "data" / "raw"
raw = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_RAW
FORMAT = "%Y-%m-%d %H:%M:%S"
PURCHASE, APPROVED, CARRIER, DELIVERED, ESTIMATED = (
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
)
# Spain's spring clock changes: the local hour 02:00-03:00 did not exist on these dates.
MISSING_HOURS = [datetime(2017, 3, 26, 2), datetime(2018, 3, 25, 2)]
HOUR = timedelta(hours=1)


def read(name):
    with open(raw / name, encoding="utf-8-sig", newline="") as handle:
        yield from csv.DictReader(handle)


def parse(value):
    return datetime.strptime(value, FORMAT) if value else None


def in_missing_hour(value):
    return value is not None and any(start <= value < start + HOUR for start in MISSING_HOURS)


def shifted(value):
    return value + HOUR if in_missing_hour(value) else value


orders = list(read("olist_orders_dataset.csv"))
customers = {row["customer_id"]: row["customer_state"] for row in read("olist_customers_dataset.csv")}
items = list(read("olist_order_items_dataset.csv"))
payments = list(read("olist_order_payments_dataset.csv"))
for order in orders:
    for column in (PURCHASE, APPROVED, CARRIER, DELIVERED, ESTIMATED):
        order[column] = parse(order[column])

print("ROW COUNTS")
for path in sorted(raw.glob("*_dataset.csv")) + [raw / "product_category_name_translation.csv"]:
    print(f"  {path.name:42}{sum(1 for _ in read(path.name)):>11,}")

print("\nDATE LOGIC (source CSV)")
print("  approved before purchase    ", sum(1 for o in orders if o[APPROVED] and o[APPROVED] < o[PURCHASE]))
print("  carrier before purchase     ", sum(1 for o in orders if o[CARRIER] and o[CARRIER] < o[PURCHASE]))
print("  delivered before purchase   ", sum(1 for o in orders if o[DELIVERED] and o[DELIVERED] < o[PURCHASE]))
print("  delivered before carrier    ", sum(1 for o in orders if o[DELIVERED] and o[CARRIER] and o[DELIVERED] < o[CARRIER]))
print("  delivered with no date      ", sum(1 for o in orders if o["order_status"] == "delivered" and not o[DELIVERED]))
gaps = [(o[PURCHASE] - o[CARRIER]).total_seconds() / 86400 for o in orders if o[CARRIER] and o[CARRIER] < o[PURCHASE]]
print(f"  largest carrier-before-purchase gap: {max(gaps):.1f} days")

print("\nUNIQUENESS AND REFERENCES")
order_ids = {o["order_id"] for o in orders}
print("  duplicate order_ids         ", len(orders) - len(order_ids))
print("  items without an order      ", sum(1 for i in items if i["order_id"] not in order_ids))
print("  payments without an order   ", sum(1 for p in payments if p["order_id"] not in order_ids))
print("  orders without a customer   ", sum(1 for o in orders if o["customer_id"] not in customers))

print("\nPAYMENT RECONCILIATION")
paid = collections.defaultdict(Decimal)
payment_rows = collections.Counter()
for payment in payments:
    paid[payment["order_id"]] += Decimal(payment["payment_value"])
    payment_rows[payment["order_id"]] += 1
item_value = collections.defaultdict(Decimal)
sales = collections.defaultdict(Decimal)
for item in items:
    item_value[item["order_id"]] += Decimal(item["price"]) + Decimal(item["freight_value"])
    sales[item["order_id"]] += Decimal(item["price"])
total_paid, total_items = sum(paid.values()), sum(item_value.values())
no_items = order_ids - set(item_value)
paid_no_items = sum(paid.get(order_id, Decimal(0)) for order_id in no_items)
print(f"  total payments              R$ {total_paid:,}")
print(f"  items plus freight          R$ {total_items:,}")
print(f"  difference                  R$ {total_paid - total_items:,}")
print(f"  orders without items           {len(no_items)}  (payments R$ {paid_no_items:,})")
print(f"  remaining net difference    R$ {total_paid - total_items - paid_no_items:,}")
print(f"  orders with several payments   {sum(1 for n in payment_rows.values() if n > 1):,}  (maximum {max(payment_rows.values())})")

print("\nORDER STATUS")
for status, count in collections.Counter(o["order_status"] for o in orders).most_common():
    print(f"  {status:14}{count:>7,}")

delivered = [o for o in orders if o["order_status"] == "delivered"]
dated = [o for o in delivered if o[DELIVERED]]
on_time = sum(1 for o in dated if o[DELIVERED].date() <= o[ESTIMATED].date())
valid = [o for o in delivered if o[CARRIER] and o[DELIVERED] and o[PURCHASE] <= o[CARRIER] <= o[DELIVERED]]
total_sales = sum(sales[o["order_id"]] for o in delivered)
days = [(o[DELIVERED].date() - o[PURCHASE].date()).days for o in valid]

print("\nHEADLINE KPIS (delivered orders)")
print(f"  total product sales         R$ {total_sales:,}")
print(f"  delivered orders               {len(delivered):,}  ({len(delivered) / len(orders):.2%} of all orders)")
print(f"  average order value         R$ {total_sales / len(delivered):,.2f}")
print(f"  average delivery time          {sum(days) / len(days):.2f} days")
print(f"  on-time delivery rate          {on_time:,} / {len(dated):,} = {on_time / len(dated):.2%}")
print(f"  valid_delivery_dates           TRUE {len(valid):,}, FALSE {len(delivered) - len(valid)}")

print("\nDELIVERED PRODUCT SALES BY PURCHASE MONTH")
month_sales, month_orders = collections.Counter(), collections.Counter()
for order in delivered:
    key = order[PURCHASE].strftime("%Y-%m")
    month_sales[key] += sales[order["order_id"]]
    month_orders[key] += 1
for key in sorted(month_sales):
    print(f"  {key}  R$ {month_sales[key]:>12,.2f}  {month_orders[key]:>6,} orders")

print("\nCUSTOMER STATES: TOP 10 BY PRODUCT SALES")
state_sales, state_dated, state_late = collections.Counter(), collections.Counter(), collections.Counter()
for order in delivered:
    state = customers[order["customer_id"]]
    state_sales[state] += sales[order["order_id"]]
    if order[DELIVERED]:
        state_dated[state] += 1
        state_late[state] += order[DELIVERED].date() > order[ESTIMATED].date()
running = Decimal(0)
for state, value in state_sales.most_common(10):
    running += value
    print(f"  {state}  R$ {value:>13,.2f}  share {value / total_sales:7.2%}  cumulative {running / total_sales:7.2%}"
          f"  late {state_late[state] / state_dated[state]:7.2%}")

print("\nLATE DELIVERY RATE: STATES WITH AT LEAST 1,000 DELIVERED ORDERS")
rates = sorted(((state_late[s] / state_dated[s], s, state_dated[s]) for s in state_dated if state_dated[s] >= 1000), reverse=True)
for rate, state, count in rates:
    print(f"  {state}  {rate:7.2%}  ({count:,} orders)")

print("\nDAYLIGHT-SAVING SIMULATION (one-hour shift of values in the missing hours)")
for name, columns in (
    ("olist_orders_dataset.csv", (PURCHASE, APPROVED, CARRIER, DELIVERED, ESTIMATED)),
    ("olist_order_items_dataset.csv", ("shipping_limit_date",)),
    ("olist_order_reviews_dataset.csv", ("review_creation_date", "review_answer_timestamp")),
):
    rows = orders if name == "olist_orders_dataset.csv" else list(read(name))
    for column in columns:
        values = (row[column] if name == "olist_orders_dataset.csv" else parse(row[column]) for row in rows)
        print(f"  {column:34}{sum(1 for value in values if in_missing_hour(value)):>4} value(s)")


def delivery_flag(values):
    return bool(values[CARRIER] and values[DELIVERED] and values[PURCHASE] <= values[CARRIER] <= values[DELIVERED])


def on_time_flag(values):
    return bool(values[DELIVERED] and values[ESTIMATED] and values[DELIVERED].date() <= values[ESTIMATED].date())


def delivery_days(values):
    return (values[DELIVERED].date() - values[PURCHASE].date()).days if values[DELIVERED] else None


affected = flipped_flag = flipped_on_time = flipped_days = moved_date = 0
flipped_approval = []
for order in orders:
    moved = {key: shifted(order[key]) for key in (PURCHASE, APPROVED, CARRIER, DELIVERED, ESTIMATED)}
    if all(moved[key] == order[key] for key in moved):
        continue
    affected += 1
    flipped_flag += delivery_flag(order) != delivery_flag(moved)
    flipped_on_time += on_time_flag(order) != on_time_flag(moved)
    flipped_days += delivery_days(order) != delivery_days(moved)
    moved_date += order[PURCHASE].date() != moved[PURCHASE].date()
    if order[APPROVED] and (order[APPROVED] < order[PURCHASE]) != (moved[APPROVED] < moved[PURCHASE]):
        flipped_approval.append(order["order_id"])
print(f"  orders with a shifted value        {affected}")
print(f"  purchase date changes              {moved_date}")
print(f"  valid_delivery_dates changes       {flipped_flag}")
print(f"  on-time result changes             {flipped_on_time}")
print(f"  delivery-day changes               {flipped_days}")
print(f"  approval-before-purchase changes   {flipped_approval}")
