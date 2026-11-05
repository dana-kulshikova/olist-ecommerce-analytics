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
| Carrier handover before purchase | 166 (165 delivered, 1 shipped) |
| Customer delivery before carrier handover | 23 |
| Customer delivery before purchase | 0 |
| Delivered status with no delivery date | 8 |
| Approval before purchase, source CSV | 0 |
| Approval before purchase, PostgreSQL | 1 (see below) |

The largest carrier-before-purchase gap is 171 days, and that value is already in the source CSV.

**Handling:** `bi_orders` sets `valid_delivery_dates` to FALSE when dates are missing or out of sequence, which applies to 197 of the 96,478 delivered orders. `Average Delivery Time` uses only orders where the flag is TRUE.

### Investigation of the 197 flagged orders

**Status: verified from the source CSVs with `python/investigate_date_sequences.py`, and against stored PostgreSQL values with `python/validate_export.py`.**

| Type | Orders | Late | Evidence | Assessment |
|---|---:|---:|---|---|
| Carrier before purchase, gap under 3 hours | 163 | Part of the 2 below | All from April 2018 onward, and clustered with a change in carrier timestamps | Possible recording effect; cause unknown |
| Carrier before purchase, larger gap | 2 | 2 across all 165 | Gaps of several days, up to 171 days | Likely genuine inconsistency |
| Delivery before carrier | 23 | 0 | Median gap about 40 hours, from 2016–2017, with 11 in July 2017 and no clock-change pattern | Likely genuine inconsistency |
| No delivery date | 8 | Not applicable | One also has no carrier date | Missing data, outside the analysis base |
| Carrier date missing, delivery present | 1 | 1 | Single order | Missing data |

**Effect on results:** the late rate is 6.7731% with the flagged orders and 6.7833% without them. They hold 0.183% of sales. None of the validated KPIs depends on removing them.

**Reconciliation:** the categories don't overlap, and together they account for every flagged order.

| Delivered orders | Orders | Late |
|---|---:|---:|
| All delivered orders | 96,478 | Not applicable |
| Outside the base: no delivery date | 8 | Not applicable |
| Analysis base | 96,470 | 6,534 |
| Flagged orders in the base (165 + 23 + 1) | 189 | 3 |
| Eligible for stage timing | 96,281 | 6,531 |

All 197 flagged orders = 189 in the base + 8 outside it.

### Change in carrier timestamps on 25 April 2018

Stored carrier timestamps change overnight, and the source CSVs show the same pattern.

| Carrier date | Orders | Median hour | Share between 17:00 and 23:59 |
|---|---:|---:|---:|
| 23 Apr 2018 | 349 | 19 | 85% |
| 24 Apr 2018 | 402 | 19 | 74% |
| 25 Apr 2018 | 333 | 13 | 3% |
| 26 Apr 2018 | 301 | 13 | 2% |
| 27 Apr 2018 | 311 | 14 | 3% |

- All 163 small-gap carrier-before-purchase orders have a carrier date from 25 April 2018 onward.
- Only the carrier field changes. Median purchase hour stays at 15, approval moves from 13 to 14 and delivery from 17 to 18.
- On weekdays the median carrier time moves from 19:28 to 14:00, and the middle 50% of times narrows from 17:15–21:58 to 12:12–15:05, so it isn't a simple fixed clock offset.
- Carrier handover before payment approval also rises, with 121 orders purchased before April 2018 and 1,229 from then on.
- The change doesn't fall on a Spanish or Brazilian clock-change date, and it's larger than one hour.

**The cause is unknown.** The data can't show whether this reflects a recording change, a time zone change or a genuine operational change, and the analysis doesn't attribute it to any of them. **Handover and handover-to-delivery timings aren't directly comparable across 25 April 2018.** Total delivery time and late status are unaffected, because they don't use the carrier date.

### PostgreSQL export compared with the source CSVs

| Check | Result |
|---|---|
| Eight locked KPIs | All match, both in `validation.csv` and recalculated from exported rows |
| Orders, items, payments, customers, sellers and ZIP positions | Identical |
| Latest and earliest review scores | Identical across 98,673 orders |
| Purchase timestamps | 3 of 99,441 differ |
| Approval timestamps | 2 of 99,281 differ |
| Latest and earliest review answer timestamps | 21 orders differ in each |
| Carrier, delivery, estimated, shipping-limit and review-creation dates | No differences |
| `timestamp_checks.csv` | 198 rows: the 197 flagged orders plus the approval-before-purchase order |
| Missing categories | Stored as blank text rather than NULL, on the same 1,415 orders as the source |

Every timestamp difference is exactly +60 minutes, on a value inside the missing daylight-saving hours described below. None of them changes a late status, purchase date, `valid_delivery_dates` value, answer-timing label or low-rating label.

### Other checks

| Check | Result | Proposed handling |
|---|---:|---|
| Carrier before approval | 1,350 delivered orders | Keep; don't calculate approval-to-carrier time |
| Delivery before approval | 61 delivered orders | Keep; no late-status effect |
| Approval missing | 14 delivered orders | Keep; approval isn't used in late status |
| Delivery over 60 days | 288 delivered orders | Keep, and test their influence |
| Orders with several reviews | 547; 202 with differing scores, 96 changing low-rating status | Latest answered, with earliest as a sensitivity check |
| Review IDs on several rows | 789 IDs, 1,603 rows | Keep, and test excluding them |
| Reviews created before the purchase date | 64 | Keep, and test excluding them |
| Delivered orders with no review | 646 | Outside review analysis; test bounds |
| Item rows with no category | 1,603 | Treat blank and NULL as `unknown` in Python |
| Categories with no English name | 2 | Keep the original name |
| Customers and sellers with no ZIP position | 279 customers, 7 sellers; 265 and 213 orders in the base | Leave out of distance analysis and report |
| Geolocation rows outside Brazil's bounds | 42 | Exclude from positions |
| Item rows with zero freight | 383 | Keep |

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

**Impact:** comparing the PostgreSQL export with the source CSVs confirms that 4 of 99,441 orders contain an affected value, plus review answer timestamps on 21 orders. Sales, order counts, months, `valid_delivery_dates`, delivery days, on-time results and review labels don't change. Only the approval-before-purchase check changes, from 0 to 1.

**Handling:** the database records were kept unchanged. Future imports should set an explicit time zone or use a load method without time zone conversion.
