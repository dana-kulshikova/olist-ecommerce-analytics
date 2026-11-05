"""Investigates delivered orders with invalid date sequences, and related data quality issues.

Uses the source CSV files and only reads them. Requires the packages in requirements.txt.
These results describe the source data. Comparing them with stored PostgreSQL values is a
separate step.

Usage: python python/investigate_date_sequences.py [path-to-raw-csv-folder]
"""
import pathlib
import sys

import numpy as np
import pandas as pd

DEFAULT_RAW = pathlib.Path(__file__).resolve().parent.parent / "data" / "raw"
raw = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_RAW

TIMESTAMPS = ["order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date",
              "order_delivered_customer_date", "order_estimated_delivery_date"]
orders = pd.read_csv(raw / "olist_orders_dataset.csv", parse_dates=TIMESTAMPS)
customers = pd.read_csv(raw / "olist_customers_dataset.csv", dtype={"customer_zip_code_prefix": str})
items = pd.read_csv(raw / "olist_order_items_dataset.csv", parse_dates=["shipping_limit_date"])
sellers = pd.read_csv(raw / "olist_sellers_dataset.csv", dtype={"seller_zip_code_prefix": str})
products = pd.read_csv(raw / "olist_products_dataset.csv")
translation = pd.read_csv(raw / "product_category_name_translation.csv")
reviews = pd.read_csv(raw / "olist_order_reviews_dataset.csv",
                      parse_dates=["review_creation_date", "review_answer_timestamp"])
geo = pd.read_csv(raw / "olist_geolocation_dataset.csv", dtype={"geolocation_zip_code_prefix": str})

P, A, C, D, E = TIMESTAMPS
delivered = orders[orders["order_status"].eq("delivered")].merge(customers, on="customer_id", how="left")
per_order = items.groupby("order_id").agg(limit=("shipping_limit_date", "max"), first_seller=("seller_id", "first"),
                                          sales=("price", "sum"), sellers=("seller_id", "nunique")).reset_index()
delivered = delivered.merge(per_order, on="order_id", how="left")
delivered["valid"] = (delivered[C].notna() & delivered[D].notna()
                      & delivered[C].ge(delivered[P]) & delivered[D].ge(delivered[C]))
delivered["late"] = delivered[D].dt.normalize().gt(delivered[E].dt.normalize())
flagged = delivered[~delivered["valid"]].copy()


def section(title):
    print(f"\n{'=' * 4} {title}")


section("1. WHAT THE FLAG CONTAINS")
print(f"delivered orders {len(delivered):,}; valid_delivery_dates FALSE {len(flagged):,}")
types = pd.DataFrame({
    "missing_delivery": flagged[D].isna(),
    "missing_carrier": flagged[C].isna(),
    "carrier_before_purchase": flagged[C].lt(flagged[P]),
    "delivery_before_carrier": flagged[D].lt(flagged[C]),
})
print(types.sum().to_string())
print("combinations:")
print(types.value_counts().rename("orders").to_frame().to_string())
print(f"all orders, any status: carrier before purchase {orders[C].lt(orders[P]).sum()}; delivery before carrier {orders[D].lt(orders[C]).sum()}")
print("carrier-before-purchase orders by status:")
print(orders[orders[C].lt(orders[P])]["order_status"].value_counts().to_string())

carrier_first = flagged[flagged[C].lt(flagged[P])].copy()
carrier_first["gap_hours"] = (carrier_first[P] - carrier_first[C]).dt.total_seconds() / 3600
delivery_first = flagged[flagged[D].lt(flagged[C])].copy()
delivery_first["gap_hours"] = (delivery_first[C] - delivery_first[D]).dt.total_seconds() / 3600

BANDS = [0, 1, 3, 6, 12, 24, 72, 168, 720, 100000]
LABELS = ["under 1h", "1-3h", "3-6h", "6-12h", "12-24h", "1-3d", "3-7d", "7-30d", "30d+"]
section("2. GAP SIZES")
for label, frame in (("carrier before purchase", carrier_first), ("delivery before carrier", delivery_first)):
    print(f"{label}: n={len(frame)}, median {frame['gap_hours'].median():.2f}h, max {frame['gap_hours'].max():.1f}h, same calendar date {(frame[C].dt.date == (frame[P] if label.startswith('carrier') else frame[D]).dt.date).sum()}")
    print(pd.cut(frame["gap_hours"], BANDS, labels=LABELS, right=False).value_counts(sort=False).to_string())

section("3. TIME ZONE AND CLOCK-CHANGE PATTERNS")
for label, frame in (("carrier before purchase", carrier_first), ("delivery before carrier", delivery_first)):
    minutes = (frame["gap_hours"] * 60) % 60
    near_whole = ((minutes <= 2) | (minutes >= 58)).sum()
    print(f"{label}: gaps within 2 minutes of a whole hour {near_whole} of {len(frame)} (about {len(frame) * 4 / 60:.1f} expected by chance)")
    for hours in (1, 2, 3, 4, 5, 6):
        print(f"   gap within 5 min of {hours}h: {((frame['gap_hours'] - hours).abs() <= 5 / 60).sum()}")

CHANGES = {"Europe/Madrid": ["2016-10-30", "2017-03-26", "2017-10-29", "2018-03-25", "2018-10-28"],
           "America/Sao_Paulo": ["2016-10-16", "2017-02-19", "2017-10-15", "2018-02-18", "2018-11-04"]}
for zone, days in CHANGES.items():
    dates = pd.to_datetime(days)
    for label, frame, column in (("carrier before purchase", carrier_first, P), ("delivery before carrier", delivery_first, D)):
        near = sum(((frame[column].dt.normalize() - day).abs() <= pd.Timedelta(days=1)).sum() for day in dates)
        print(f"{zone}: {label} within 1 day of a clock change: {near}")
print("hour of day, carrier-before-purchase carrier timestamps (flagged share vs all delivered):")
hour_flagged = carrier_first[C].dt.hour.value_counts(normalize=True).sort_index()
hour_all = delivered[C].dt.hour.value_counts(normalize=True).sort_index()
print(pd.DataFrame({"flagged": hour_flagged, "all": hour_all}).fillna(0).round(3).T.to_string())
print("hour of day, delivery-before-carrier delivery timestamps:")
print(delivery_first[D].dt.hour.value_counts().sort_index().to_dict())

section("4. CLUSTERING")
for label, frame in (("carrier before purchase", carrier_first), ("delivery before carrier", delivery_first)):
    month = frame[P].dt.to_period("M").value_counts().sort_index()
    print(f"{label} by purchase month: {month.to_dict()}")
    print(f"   by customer state, top 5: {frame['customer_state'].value_counts().head(5).to_dict()}")
    seller = frame["first_seller"].value_counts()
    print(f"   distinct sellers {seller.size}; top seller {seller.iloc[0] if len(seller) else 0} orders; top 5 sellers hold {seller.head(5).sum()}")
all_month = delivered[P].dt.to_period("M").value_counts()
rate = (carrier_first[P].dt.to_period("M").value_counts() / all_month).dropna().sort_values(ascending=False)
print("carrier-before-purchase rate, highest months:", {str(k): f"{v:.2%}" for k, v in rate.head(4).items()})

section("5. EFFECT ON VALIDATED KPIS")
base = delivered[delivered[D].notna()]
print(f"base {len(base):,}; late {base['late'].sum():,}; late rate {base['late'].mean():.4%}")
kept = base[base["valid"]]
print(f"excluding flagged: base {len(kept):,}; late {kept['late'].sum():,}; late rate {kept['late'].mean():.4%}")
print(f"flagged orders in base {(~base['valid']).sum()}; late among them {base.loc[~base['valid'], 'late'].sum()}")
for label, frame in (("carrier before purchase", carrier_first), ("delivery before carrier", delivery_first)):
    print(f"   {label}: late {frame['late'].sum()} of {len(frame)}")
print(f"sales in flagged orders R$ {flagged['sales'].sum():,.2f} ({flagged['sales'].sum() / delivered['sales'].sum():.3%})")
days_all = (base[D].dt.normalize() - base[P].dt.normalize()).dt.days
print(f"mean delivery days, base {days_all.mean():.4f}; valid only {days_all[base['valid']].mean():.4f}")

section("6. OTHER SEQUENCE AND COMPLETENESS CHECKS (delivered orders)")
checks = {
    "approval missing": delivered[A].isna(),
    "carrier date missing": delivered[C].isna(),
    "carrier before approval": delivered[C].lt(delivered[A]),
    "delivery before approval": delivered[D].lt(delivered[A]),
    "approved before purchase": delivered[A].lt(delivered[P]),
    "estimated date before purchase": delivered[E].lt(delivered[P]),
    "shipping limit before purchase": delivered["limit"].lt(delivered[P]),
    "no item rows": delivered["limit"].isna(),
    "delivery over 60 days": (delivered[D] - delivered[P]).dt.days.gt(60),
}
for label, mask in checks.items():
    print(f"{label:34}{int(mask.sum()):>7,}")
gap = (delivered[A] - delivered[C]).dt.total_seconds() / 3600
gap = gap[delivered[C].lt(delivered[A])]
print(f"carrier before approval: median {gap.median():.2f}h, 90th percentile {gap.quantile(.9):.1f}h")
stage = delivered[delivered["valid"]]
print(f"estimated window: midnight estimated values {(delivered[E] == delivered[E].dt.normalize()).mean():.2%}")
print(f"carrier hour exactly on the hour share {(delivered[C].dt.minute.eq(0) & delivered[C].dt.second.eq(0)).mean():.3%}")
print(f"seller late to carrier, valid orders: {stage[C].gt(stage['limit']).sum():,} of {len(stage):,}")

section("7. REVIEW CHECKS")
print(f"review rows {len(reviews):,}; orders {reviews['order_id'].nunique():,}; orders with several reviews {(reviews['order_id'].value_counts() > 1).sum()}")
print(f"max reviews on one order {reviews['order_id'].value_counts().max()}")
print(f"review IDs used on several rows {(reviews['review_id'].value_counts() > 1).sum()}; rows affected {reviews['review_id'].isin(reviews['review_id'].value_counts().loc[lambda s: s > 1].index).sum()}")
print(f"exact duplicate rows {reviews.duplicated().sum()}; answer before creation {reviews['review_answer_timestamp'].lt(reviews['review_creation_date']).sum()}")
print(f"missing answer {reviews['review_answer_timestamp'].isna().sum()}; score outside 1-5 {(~reviews['review_score'].between(1, 5)).sum()}")
joined = reviews.merge(orders[["order_id", P, D, "order_status"]], on="order_id", how="left")
print(f"reviews on orders that aren't delivered {joined['order_status'].ne('delivered').sum():,}")
print(f"reviews created before purchase {joined['review_creation_date'].lt(joined[P].dt.normalize()).sum()}")
several = reviews[reviews.duplicated("order_id", keep=False)]
spread = several.groupby("order_id")["review_score"].agg(lambda s: s.max() - s.min())
print(f"orders with several reviews whose scores differ {(spread > 0).sum()} of {len(spread)}; low-rating status differs {(several.groupby('order_id')['review_score'].agg(lambda s: (s <= 2).nunique()) > 1).sum()}")
print(f"delivered orders with no review {(~delivered['order_id'].isin(reviews['order_id'])).sum():,}")

section("8. PRODUCT, CATEGORY AND LOCATION CHECKS")
item_products = items.merge(products[["product_id", "product_category_name"]], on="product_id", how="left")
print(f"items with no product match {item_products['product_category_name'].isna().sum():,} rows; product rows with no category {products['product_category_name'].isna().sum()}")
untranslated = sorted(set(products["product_category_name"].dropna()) - set(translation["product_category_name"]))
print(f"categories with no English translation: {untranslated}")
print(f"items with price zero or less {(items['price'] <= 0).sum()}; freight of zero {(items['freight_value'] == 0).sum():,}")
inside = geo["geolocation_lat"].between(-34, 6) & geo["geolocation_lng"].between(-74, -34)
print(f"geolocation rows outside Brazil's bounds {(~inside).sum()}")
zips = set(geo.loc[inside, "geolocation_zip_code_prefix"])
print(f"customer ZIP prefixes without a position: {(~customers['customer_zip_code_prefix'].isin(zips)).sum():,} customers")
print(f"seller ZIP prefixes without a position: {(~sellers['seller_zip_code_prefix'].isin(zips)).sum():,} sellers")
zip_state = geo.groupby("geolocation_zip_code_prefix")["geolocation_state"].agg(lambda s: s.mode().iat[0])
matched = customers["customer_zip_code_prefix"].map(zip_state)
print(f"customers whose state differs from their ZIP's most common state {matched.notna().sum() and (matched.notna() & matched.ne(customers['customer_state'])).sum()}")
print(f"multi-seller delivered orders {(delivered['sellers'] > 1).sum():,}")
print(f"purchases from July 2018 onward among delivered: {delivered[P].ge('2018-07-01').sum():,}; orders from then not delivered: {(orders[P].ge('2018-07-01') & orders['order_status'].ne('delivered')).sum():,}")
status_by_month = orders.assign(month=orders[P].dt.to_period("M"), done=orders["order_status"].eq("delivered")).groupby("month")["done"].agg(["size", "mean"])
print("delivered share by purchase month, 2018 onward:")
print(status_by_month.loc["2018-01":].round(4).to_string())

section("9. DID THE CARRIER TIMESTAMP CHANGE IN APRIL 2018?")
have = delivered[delivered[C].notna()].copy()
have["month"] = have[P].dt.to_period("M")
have["handover_hours"] = (have[C] - have[P]).dt.total_seconds() / 3600
have["era"] = np.where(have[P].ge("2018-04-01"), "from Apr 2018", "before Apr 2018")
for era, frame in have.groupby("era"):
    hours = frame[C].dt.hour
    print(f"{era}: n={len(frame):,}; carrier before purchase {frame[C].lt(frame[P]).sum()}; "
          f"handover under 3h {frame['handover_hours'].between(0, 3).mean():.3%}; median handover {frame['handover_hours'].median():.1f}h; "
          f"carrier time between 12:00 and 15:59 {hours.between(12, 15).mean():.1%}; between 17:00 and 23:59 {hours.between(17, 23).mean():.1%}")
print("monthly carrier-timestamp profile, 2017-10 onward:")
profile = have[have["month"] >= pd.Period("2017-10")].groupby("month").agg(
    orders=("order_id", "size"),
    carrier_before_purchase=("handover_hours", lambda s: int((s < 0).sum())),
    handover_under_3h=("handover_hours", lambda s: round(s.between(0, 3).mean() * 100, 2)),
    midday_share=(C, lambda s: round(s.dt.hour.between(12, 15).mean() * 100, 1)),
    evening_share=(C, lambda s: round(s.dt.hour.between(17, 23).mean() * 100, 1)),
    median_hour=(C, lambda s: float(s.dt.hour.median())),
)
print(profile.to_string())
before_approval = have[have[C].lt(have[A])]
print("carrier before approval by purchase period:", before_approval["era"].value_counts().to_dict())
print("carrier before approval, monthly from 2018-01:",
      {str(k): int(v) for k, v in before_approval[before_approval["month"] >= pd.Period("2018-01")]["month"].value_counts().sort_index().items()})
print("carrier-before-purchase orders excluding gaps of 3h or more:",
      int(((have["handover_hours"] < 0) & (have["handover_hours"] > -3)).sum()))

section("10. RECONCILIATION OF THE FLAGGED ORDERS")
reviewed = delivered["order_id"].isin(reviews["order_id"])
masks = {
    "no delivery date, carrier present": delivered[D].isna() & delivered[C].notna(),
    "no delivery date, no carrier date": delivered[D].isna() & delivered[C].isna(),
    "carrier date missing, delivery present": delivered[D].notna() & delivered[C].isna(),
    "carrier before purchase": delivered[C].lt(delivered[P]),
    "delivery before carrier": delivered[D].lt(delivered[C]),
}
assigned = pd.Series(0, index=delivered.index)
for label, mask in masks.items():
    in_base = delivered[D].notna() & mask
    print(f"{label:42} orders {int(mask.sum()):>4}  in base {int(in_base.sum()):>4}  late {int(delivered.loc[in_base, 'late'].sum()):>3}  with review {int((mask & reviewed).sum()):>4}")
    assigned += mask.astype(int)
print(f"orders in more than one category: {int((assigned > 1).sum())}")
print(f"orders in a category: {int((assigned > 0).sum())}; flagged: {len(flagged)}; flagged without a category: {int(((assigned == 0) & ~delivered['valid']).sum())}; category but not flagged: {int(((assigned > 0) & delivered['valid']).sum())}")
in_base = delivered[D].notna()
print(f"delivered {len(delivered):,} = base {int(in_base.sum()):,} + outside base {int((~in_base).sum())}")
print(f"flagged {len(flagged)} = in base {int((in_base & ~delivered['valid']).sum())} + outside base {int((~in_base & ~delivered['valid']).sum())}")
print(f"base {int(in_base.sum()):,} = stage-timing eligible {int((in_base & delivered['valid']).sum()):,} + excluded from stage timing {int((in_base & ~delivered['valid']).sum())}")
print(f"late in base {int(delivered.loc[in_base, 'late'].sum()):,} = eligible {int(delivered.loc[in_base & delivered['valid'], 'late'].sum()):,} + excluded {int(delivered.loc[in_base & ~delivered['valid'], 'late'].sum())}")
print(f"flagged orders kept in review analysis: {int((in_base & ~delivered['valid'] & reviewed).sum())} of {int((in_base & ~delivered['valid']).sum())} in the base")
eligible = delivered[in_base & delivered["valid"]]
print("stage-timing orders by purchase period:",
      {"before Apr 2018": int(eligible[P].lt("2018-04-01").sum()), "from Apr 2018": int(eligible[P].ge("2018-04-01").sum()),
       "Apr 2018 only": int((eligible[P].ge("2018-04-01") & eligible[P].lt("2018-05-01")).sum())})
