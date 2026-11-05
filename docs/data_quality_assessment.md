# Data Quality Assessment

The dataset was loaded into PostgreSQL and checked for completeness, uniqueness, referential integrity, date logic and financial reconciliation. Original records were kept, and exceptions are handled by rules in the view and in each KPI.

Figures can be reproduced in two ways:

- `sql/03_data_quality_and_analysis.sql` runs against the database.
- `python/verify_figures.py` runs against the source CSV. It also covers the checks that have no saved SQL query.

## Results

### Uniqueness and references

| Check | Result |
|---|---:|
| Duplicate `order_id` values | 0 |
| Order items without a matching order | 0 |
| Payments without a matching order | 0 |
| Orders without a matching customer | 0 |

The database has no primary or foreign keys, so these results come from queries rather than enforced constraints.

### Date logic

| Check | Orders |
|---|---:|
| Carrier handover before purchase | 166 |
| Customer delivery before carrier handover | 23 |
| Customer delivery before purchase | 0 |
| Delivered status with no delivery date | 8 |
| Approval before purchase, source CSV | 0 |
| Approval before purchase, PostgreSQL | 1 (see below) |

The largest carrier-before-purchase gap is 171 days, and that value is already in the source CSV.

**Handling:** `bi_orders` sets `valid_delivery_dates` to FALSE when dates are missing or out of sequence, which applies to 197 of the 96,478 delivered orders. `Average Delivery Time` uses only orders where the flag is TRUE.

### Financial reconciliation

| Item | Value |
|---|---:|
| Total payments | R$ 16,008,872.12 |
| Items plus freight | R$ 15,843,553.24 |
| Difference | R$ 165,318.88 |
| Payments on the 775 orders with no item records | R$ 162,591.95 |
| Net difference on orders with items | R$ 2,726.93 |

This explains where the difference arises arithmetically. It doesn't show that any payment is wrong.

2,961 orders have more than one payment record, with a maximum of 29. Joining payments directly to items would inflate financial totals, so `bi_orders` aggregates each table to order level before joining.

### Review cleaning

`python/clean_reviews.py` processed 99,224 reviews and kept every row. It flattened 3,852 text fields containing line breaks or null characters. It found no invalid scores or dates.

## Daylight-saving timestamp discrepancy

Query 06 reports one order approved before purchase in PostgreSQL, while the source CSV contains none. Order `32b8249f810186f4cd9179daabc1f1dd` shows why:

| Layer | Purchase time |
|---|---|
| Source CSV | 2018-03-25 02:56:02 |
| PostgreSQL stored value, read as text | 2018-03-25 03:56:02 |

The approval time is 03:10:20, so the stored purchase time now falls after it. In Spain, 02:00-03:00 didn't exist that night because of the clock change. The columns are `timestamp without time zone`, and the session time zone is `Europe/Madrid`.

**Confirmed:**

- Values in the missing hours on 26 March 2017 and 25 March 2018 no longer appear in `order_purchase_timestamp` or `order_approved_at`. The CSV has 3 and 2 such values, and PostgreSQL has 0.
- PostgreSQL keeps the literal `'2018-03-25 02:56:02'::timestamp` as 02:56:02 when cast to text.
- DBeaver displays that same literal as 03:56:02, so values in this hour should be checked with `::text`.

**Not proven:** the exact step that changed the stored values. The data was loaded through DBeaver's CSV import on a machine set to Madrid time, and DBeaver's display behaviour makes a client-side conversion during that import the leading explanation. A controlled test import has not been run.

**Impact:** in a simulation applying the one-hour shift to the source CSV, 4 of 99,441 orders contain an affected value. Sales, order counts, months, `valid_delivery_dates`, delivery days and on-time results don't change. Only the approval-before-purchase check changes, from 0 to 1. Up to 21 review answer timestamps may also be affected, but the dashboard doesn't use them.

**Handling:** the database records were kept unchanged. Future imports should set an explicit time zone or use a load method without time zone conversion.
