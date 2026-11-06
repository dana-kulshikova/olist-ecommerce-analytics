# Power BI Validation

This document records how the two-page dashboard and its review data were checked. Every result is labelled by its source:

| Source | Meaning |
|---|---|
| **SQL** | Read-only queries run with `psql` on the project database. Outputs were saved and reviewed |
| **Export** | A row-by-row script comparison against the audited export `data/processed/orders_analysis.csv` (not in the repository) |
| **Files** | Automated checks of the PBIP files: parsing, IDs, field references, layout, hashes |
| **Runtime** | DAX queries run in Power BI Desktop by the author, with results reported back. Not re-run during packaging |
| **Visual** | Manual inspection of the rendered report in Power BI Desktop |

None of these is an independent review: the same author built and checked the work. The research audit's own limits are in [independent_audit.md](independent_audit.md).

## 1. Review view: `public.bi_order_reviews` (SQL, Export)

The view is defined in [sql/05_create_bi_order_reviews.sql](../sql/05_create_bi_order_reviews.sql).

**Before creating it** (SQL, read-only):

| Check | Result |
|---|---|
| Existing object named `bi_order_reviews` | None |
| Review table | 99,224 rows; 0 NULL review IDs, order IDs, scores, answer timestamps or creation dates |
| Review IDs used on several rows | 789 IDs on 1,603 rows, as in [data_quality_assessment.md](data_quality_assessment.md) |
| Orders with several reviews | 547 |
| Full ranking ties (same order, answer timestamp, creation date and review ID) | 0, so the selection is deterministic |
| Proposed selection against the `sql/04` selection, compared by `review_id` | 98,673 each; 0 differences in either direction |

**The view itself:**

| Check | Expected | Result | Source |
|---|---:|---:|---|
| Rows | 98,673 | 98,673 | SQL |
| Distinct order IDs | 98,673 | 98,673 | SQL |
| Duplicate rows; NULL order IDs, scores or answer timestamps | 0 | 0 | SQL |
| Orders in `bi_orders` without a review | 768 | 768 | SQL |
| Review rows without a matching order | 0 | 0 | SQL |
| View against the `sql/04` selection (4 duplicate-sensitive directions) | 0 | 0 | SQL |
| Orders matched against the audited export | 98,673 | 98,673; 0 export-only, 0 view-only | Export |
| Score, answer-timestamp, creation-date and NULL mismatches | 0 | 0 | Export |

Score distribution in the view: 11,363 one-star, 3,131 two-star, 8,133 three-star, 19,038 four-star and 57,008 five-star reviews. No documented target exists for this distribution.

**Database integrity** (SQL). The `bi_orders` definition fingerprint, and the content fingerprints and row counts of `bi_orders` and the review table, were identical before and after the view was created. The only new object in schema `public` was `bi_order_reviews`. Other tables were checked by the object list only, not by content.

## 2. Delivery and review populations (SQL)

| Metric | Expected | Result |
|---|---:|---:|
| Delivered orders | 96,478 | 96,478 |
| Delivered with a delivery date | 96,470 | 96,470 |
| On time | 89,936 | 89,936 |
| Late | 6,534 | 6,534 |
| On-time rate | 93.23% | 93.23% |
| Delivered orders flagged by `valid_delivery_dates` | 197 | 197 |
| Of those, with a delivery date | 189 | 189 |
| Valid for stage timing | 96,281 | 96,281 |
| Flagged, with a delivery date and a review | 188 | 188 |
| Delivered with a date but no estimated date | 0 | 0 |
| Reviewed delivered orders | 95,824 | 95,824 |
| Low-rated (1–2 stars) | 12,272 | 12,272 (12.81%) |

| Group | Reviewed | Low-rated | Low-rating share |
|---|---:|---:|---:|
| On time | 89,443 | 8,289 | 9.27% |
| Late, answered before delivery | 4,473 | 3,612 | 80.75% |
| Late, answered after delivery | 1,908 | 371 | 19.44% |
| On time, single item | 80,407 | 6,067 | 7.55% |
| On time, multi-item | 9,036 | 2,222 | 24.59% |
| Late, single item | 5,889 | 3,657 | 62.10% |
| Late, multi-item | 492 | 326 | 66.26% |

No reviewed delivered order has an answer timestamp equal to its delivery timestamp, so the "before" and "after" boundary doesn't affect any order. All figures match [hypothesis_log.md](hypothesis_log.md).

## 3. Power BI model

**After importing the view** (Runtime):

| Check | Expected | Result |
|---|---:|---:|
| Orders rows and distinct IDs | 99,441 | 99,441 |
| Review rows and distinct IDs | 98,673 | 98,673 |
| Orphan reviews | 0 | 0 (blank) |
| Orders without a review | 768 | 768 |
| Total Orders, On-Time Delivery Rate, Average Delivery Time, Total Product Sales, Average Order Value | Unchanged | 96,478; 0.93227; 12.5069; 13,221,498.11; 137.0416 |

**Measures and calculated columns** (Runtime): a consolidated query of **49 checks** was run in DAX query view. **49 passed and 0 failed**, with counts required to match exactly and rates to within 0.00005. It covered:
- the 10 new measures and the 3 flagged-order counts;
- all review groups and order-type cells (counts and shares);
- the blank and missing-answer group rows (2,849 and 0);
- RJ and SP filters (base, late, not-delivered share, low-rated);
- a November 2017 purchase-date filter (7,288 orders, 904 late, medians 23 and 13 days);
- three checks that review-side filters leave delivery measures unchanged;
- the five Overview KPIs.

The query is reproduced in the appendix.

**Delivery Status column** (Runtime): On time, 89,443 reviewed with 8,289 low-rated (9.27%); Late, 6,381 reviewed with 3,983 low-rated (62.42%). These match A2's unadjusted figures in the hypothesis log.

**Model files** (Files):
- 9 tables; 7 relationships, including the review relationship (many-to-one, single direction, active).
- These model changes have been made since the 49-check run:
  - Late Orders' format string changed from `0` to `#,0`.
  - A display column, Delivery Review Label, was added, so the review-timing chart's category labels fit. It maps each Delivery Review Group value to a shorter name, one to one.
  - Two empty placeholder measures from the original training file, `Measure` and `Measure 2`, were removed. Nothing referred to them.
  - Late Orders, Low-Rated Orders and On-Time Delivery Rate now return 0 instead of blank for zero events, and three hidden helper measures were added. See section 5.
- Apart from those three zero-event changes, every DAX expression that was validated is unchanged.
- **The 49 checks were re-run after the zero-event changes: 49 passed, 0 failed.** The changes return 0 instead of blank only where the base population exists, so none of the 49 targets was affected. See section 5.

## 4. Report (Files, Visual)

| Check | Result | Source |
|---|---|---|
| Pages | 2: Overview and Delivery & Customer Experience, both 1920 × 1080 | Files |
| Visuals | 33 on Overview (1 hidden), 18 on page 2; 51 unique IDs | Files |
| JSON | All report files parse | Files |
| Field and measure references on page 2 | 18, including the three helper measures, all present in the model | Files |
| Page-2 layout | Every visual inside the canvas, no overlaps | Files |
| Overview page | 33 of 34 files identical to the original project; see the note below | Files |
| KPI values on both pages | As expected (below) | Visual |
| Slicers | State and purchase-date slicers filter the page | Visual |
| RJ selected | 1,495 late orders, 12.11% late rate | Visual |
| November 2017 selected | 904 late orders, 12.40% late rate | Visual |
| Review charts C4 and C5 | Don't filter the KPI cards | Visual |
| Customer state chart | All 12 states with 1,000+ delivered orders visible, including RJ and SP | Visual |
| Research Findings panel and notes | Fully visible, without scrolling or clipping | Visual |
| Review-timing chart (C4) | All three category labels fully readable after switching to Delivery Review Label | Visual |
| Order type chart (C5) | Horizontal bars; all four data labels separate and readable | Visual |

| Overview | Value | Delivery & Customer Experience | Value |
|---|---:|---|---:|
| Total Product Sales | R$ 13.22M | On-Time Delivery Rate | 93.23% |
| Total Orders | 96,478 | Late Orders | 6,534 |
| Average Order Value | R$ 137.04 | Late Delivery Rate | 6.77% |
| Average Delivery Time | 12.5 days | Median Promised Days | 24.0 |
| On-Time Delivery Rate | 93.23% | Median Actual Days | 10.0 |
| | | Low-Rating Share | 12.81% |

**Overview title note.** When the working copy was saved, Power BI rewrote the Overview title's text-box file. It swapped the order of two properties and wrote the colour `#142C4E` in lowercase. The title renders the same, so the rewritten file is kept in this repository.

**Final layout fixes.** Two changes fixed layout problems in earlier captures:
- **C4:** two category labels were cut short. The chart now uses the Delivery Review Label display column.
- **C5:** two data labels overlapped. The chart now uses horizontal bars.

Neither change affects any value. Adding the display column needed a refresh of the review table from the local database in Power BI Desktop; the database itself wasn't changed. The screenshot in `screenshots/06_delivery_customer_experience.png` shows the page with nothing selected. It was captured before the update in section 5, so the Notes in it don't yet include the final sentence about sample-size shading. With nothing selected, every bar is standard blue, so nothing else differs.

## 5. Interactions and sample-size update (Files, Visual, Runtime)

**Why it was needed.** Manual testing of the Delivery page found three problems. None was a calculation error: card values for a selected month matched the research, for example March 2018 at 1,328 late orders, 18.96%, and medians of 22 and 13 days.
- **Cross-highlighting on rate charts.** With no interaction settings, clicking a month cross-highlighted the state and review charts and collapsed the line chart. On a rate chart, a part-shaded bar looks like a share of the bar, but it's a different rate drawn over the full-period one.
- **Sample-size rules evaluated inside each selection.** The 100- and 1,000-order chart filters were recalculated for every selection:
  - within any single month, only SP had 1,000+ delivered orders (plus RJ in November 2017);
  - 15 states never reach 100 orders in a month.

  So filtering by month or state left charts with one bar, or empty.
- **Zero events shown as `--`.** A count of nothing is blank in DAX. For example, AC customers in March 2018 had 2 delivered orders and none late.

**What changed** (8 PBIP files; layout unchanged):

| Area | Change |
|---|---|
| Delivery-page interactions | 12 settings: the month, line and state charts filter each other, the cards and both review charts. The line chart highlights the month chart. Review charts still affect nothing. See [data_model.md](data_model.md#filtering-behaviour) |
| Overview interactions | 4 settings: the two monthly charts don't filter each other, and clicking a month filters the Top 10 states chart |
| Month and line charts | Filter "Delivered Orders With Date ≥ 100" replaced by Month Coverage Orders ≥ 100 (a national rule) and Delivered Orders With Date ≥ 1 |
| State chart | Filter "≥ 1,000" replaced by Top 12 states by State Full-Period Orders and Delivered Orders With Date ≥ 1 |
| Sample-size warning | Month and state bars coloured by Sample Bar Colour: grey under 30 orders, light blue 30–99, standard blue 100+. Delivered-order count added to the line chart's tooltip |
| Measures | Zero-event handling in Late Orders, Low-Rated Orders and On-Time Delivery Rate; three hidden helper measures. See [dax_measures.md](dax_measures.md) |
| Notes text | One sentence explaining the shading, the 12 states and month coverage |

The thresholds keep their values, 100 and 1,000. They now decide only which rows can appear, and they no longer change with a selection. Reliability is shown by shading, not by removing data.

**Checks:**

| Check | Result | Source |
|---|---|---|
| Files changed against the previous release | Exactly the 8 approved files | Files |
| Pages and visuals | Both pages, 51 visuals; positions, sizes and all other settings unchanged | Files |
| Interactions | Previous settings plus exactly the approved ones; all IDs valid, no duplicates | Files |
| Measures | 3 changed (the zero-event fixes) and 3 added (hidden helpers); none removed | Files |
| Relationships | File byte-identical; 7 relationships | Files |
| References | All 25 field and measure references in visuals and visual filters, on both pages, exist in the model | Files |
| Colour rule | Uses the per-data-point selector defined in the published PBIR formatting schema | Files |
| Notes length | Estimated at 3 lines in the 74-pixel box from Segoe UI font metrics | Files |
| Manual test checklist | Reported by the author as working as expected | Visual |
| DAX checks 1–85 (appendix), run by the author in DAX query view after the update | **85 passed, 0 failed:** original checks 49 of 49, zero-event checks 18 of 18, helper-measure checks 18 of 18 | Runtime |

The manual test checklist covered:
- the baseline values;
- March 2018: the same 12 states, with CE first at 50.54% on 93 orders, shaded light blue;
- clicking the line chart; clicking RJ and CE;
- the AL, AC and RR slicer selections (RR shows 17 of 21 months, with the other 4 absent, not 0%);
- a slicer combined with a month click, and AC with March 2018 showing 0 late orders;
- review-chart clicks, clearing selections, the Research Findings panel, the Notes text and the Overview page.

Expected values came from the order export.

## 6. Research integrity

The second page keeps two kinds of result apart:

- **Charts and cards** are descriptive, unadjusted measures. They respond to slicers and chart selections.
- **The Research Findings panel** is fixed text from the analysis in [hypothesis_log.md](hypothesis_log.md). It doesn't respond to slicers or chart selections:
  - A1 (RJ against SP customers, +7.46 points) and A2 (late against on-time orders, +51.04 points) are prespecified, adjusted estimates labelled **Supported (provisional)**.
  - B6 (multi-item orders, +12.67 points) and B7 (67.54% of low ratings on on-time orders) are **exploratory**.

All of these are observational associations, not causal effects. RJ against SP compares customer states and doesn't measure a shipping route. The data is historical (2016–2018), not current performance.

**Open limitations, carried from the research audit:**
- The audit items still marked NEEDS INVESTIGATION in [independent_audit.md](independent_audit.md) stay open: R7, D7, L2, C7, T10 and T11.
- Running the measures in Power BI Desktop and querying the database here were checks by the author, not independent verification. They don't close T10 or T11.
- The final months may be incomplete, because orders still in transit when the data ended aren't included.
- Carrier timestamps change on 25 April 2018, so handover timing isn't shown.

## Appendix: runtime validation query

The 49-check query, run in DAX query view. Each row compares a result with its documented target.

<details>
<summary>Show the query</summary>

```dax
EVALUATE
VAR OnTimeGroup = "On time"
VAR LateGroups = { "Late, answered before delivery", "Late, answered after delivery", "Late, answer time missing" }
VAR Nov2017 = FILTER ( ALL ( 'public bi_orders'[order_purchase_timestamp] ),
        'public bi_orders'[order_purchase_timestamp] >= DATE ( 2017, 11, 1 ) && 'public bi_orders'[order_purchase_timestamp] < DATE ( 2017, 12, 1 ) )
VAR Checks = UNION (
    ROW ( "check", "01 delivered with date", "actual", [Delivered Orders With Date] + 0, "expected", 96470, "tol", 0 ),
    ROW ( "check", "02 late orders", "actual", [Late Orders] + 0, "expected", 6534, "tol", 0 ),
    ROW ( "check", "03 late rate", "actual", [Late Delivery Rate] + 0, "expected", 0.0677, "tol", 0.00005 ),
    ROW ( "check", "04 median promised days", "actual", [Median Promised Days] + 0, "expected", 24, "tol", 0 ),
    ROW ( "check", "05 median actual days", "actual", [Median Actual Days] + 0, "expected", 10, "tol", 0 ),
    ROW ( "check", "06 not delivered share", "actual", [Not Delivered Share] + 0, "expected", 0.0298, "tol", 0.00005 ),
    ROW ( "check", "07 reviewed orders", "actual", [Reviewed Orders] + 0, "expected", 95824, "tol", 0 ),
    ROW ( "check", "08 low-rated orders", "actual", [Low-Rated Orders] + 0, "expected", 12272, "tol", 0 ),
    ROW ( "check", "09 low-rating share", "actual", [Low-Rating Share] + 0, "expected", 0.1281, "tol", 0.00005 ),
    ROW ( "check", "10 review key check", "actual", [Review Key Check] + 0, "expected", 0, "tol", 0 ),
    ROW ( "check", "11 flagged delivered", "actual", CALCULATE ( COUNTROWS ( 'public bi_orders' ), 'public bi_orders'[order_status] = "delivered", 'public bi_orders'[valid_delivery_dates] = FALSE () ) + 0, "expected", 197, "tol", 0 ),
    ROW ( "check", "12 flagged with date", "actual", CALCULATE ( [Delivered Orders With Date], 'public bi_orders'[valid_delivery_dates] = FALSE () ) + 0, "expected", 189, "tol", 0 ),
    ROW ( "check", "13 valid for stage timing", "actual", CALCULATE ( [Delivered Orders With Date], 'public bi_orders'[valid_delivery_dates] = TRUE () ) + 0, "expected", 96281, "tol", 0 ),
    ROW ( "check", "14 on time: low-rated", "actual", CALCULATE ( [Low-Rated Orders], 'public bi_order_reviews'[Delivery Review Group] = OnTimeGroup ) + 0, "expected", 8289, "tol", 0 ),
    ROW ( "check", "15 on time: low share", "actual", CALCULATE ( [Low-Rating Share], 'public bi_order_reviews'[Delivery Review Group] = OnTimeGroup ) + 0, "expected", 0.0927, "tol", 0.00005 ),
    ROW ( "check", "16 late before: low-rated", "actual", CALCULATE ( [Low-Rated Orders], 'public bi_order_reviews'[Delivery Review Group] = "Late, answered before delivery" ) + 0, "expected", 3612, "tol", 0 ),
    ROW ( "check", "17 late before: low share", "actual", CALCULATE ( [Low-Rating Share], 'public bi_order_reviews'[Delivery Review Group] = "Late, answered before delivery" ) + 0, "expected", 0.8075, "tol", 0.00005 ),
    ROW ( "check", "18 late after: low-rated", "actual", CALCULATE ( [Low-Rated Orders], 'public bi_order_reviews'[Delivery Review Group] = "Late, answered after delivery" ) + 0, "expected", 371, "tol", 0 ),
    ROW ( "check", "19 late after: low share", "actual", CALCULATE ( [Low-Rating Share], 'public bi_order_reviews'[Delivery Review Group] = "Late, answered after delivery" ) + 0, "expected", 0.1944, "tol", 0.00005 ),
    ROW ( "check", "20 on-time single: low-rated", "actual", CALCULATE ( [Low-Rated Orders], 'public bi_order_reviews'[Delivery Review Group] = OnTimeGroup, 'public bi_order_reviews'[Order Type] = "Single item" ) + 0, "expected", 6067, "tol", 0 ),
    ROW ( "check", "21 on-time single: low share", "actual", CALCULATE ( [Low-Rating Share], 'public bi_order_reviews'[Delivery Review Group] = OnTimeGroup, 'public bi_order_reviews'[Order Type] = "Single item" ) + 0, "expected", 0.0755, "tol", 0.00005 ),
    ROW ( "check", "22 on-time multi: low-rated", "actual", CALCULATE ( [Low-Rated Orders], 'public bi_order_reviews'[Delivery Review Group] = OnTimeGroup, 'public bi_order_reviews'[Order Type] = "Multi-item" ) + 0, "expected", 2222, "tol", 0 ),
    ROW ( "check", "23 on-time multi: low share", "actual", CALCULATE ( [Low-Rating Share], 'public bi_order_reviews'[Delivery Review Group] = OnTimeGroup, 'public bi_order_reviews'[Order Type] = "Multi-item" ) + 0, "expected", 0.2459, "tol", 0.00005 ),
    ROW ( "check", "24 late single: low-rated", "actual", CALCULATE ( [Low-Rated Orders], 'public bi_order_reviews'[Delivery Review Group] IN LateGroups, 'public bi_order_reviews'[Order Type] = "Single item" ) + 0, "expected", 3657, "tol", 0 ),
    ROW ( "check", "25 late single: low share", "actual", CALCULATE ( [Low-Rating Share], 'public bi_order_reviews'[Delivery Review Group] IN LateGroups, 'public bi_order_reviews'[Order Type] = "Single item" ) + 0, "expected", 0.6210, "tol", 0.00005 ),
    ROW ( "check", "26 late multi: low-rated", "actual", CALCULATE ( [Low-Rated Orders], 'public bi_order_reviews'[Delivery Review Group] IN LateGroups, 'public bi_order_reviews'[Order Type] = "Multi-item" ) + 0, "expected", 326, "tol", 0 ),
    ROW ( "check", "27 late multi: low share", "actual", CALCULATE ( [Low-Rating Share], 'public bi_order_reviews'[Delivery Review Group] IN LateGroups, 'public bi_order_reviews'[Order Type] = "Multi-item" ) + 0, "expected", 0.6626, "tol", 0.00005 ),
    ROW ( "check", "28 blank group rows", "actual", COUNTROWS ( FILTER ( 'public bi_order_reviews', ISBLANK ( 'public bi_order_reviews'[Delivery Review Group] ) ) ) + 0, "expected", 2849, "tol", 0 ),
    ROW ( "check", "29 answer-missing group rows", "actual", COUNTROWS ( FILTER ( 'public bi_order_reviews', 'public bi_order_reviews'[Delivery Review Group] = "Late, answer time missing" ) ) + 0, "expected", 0, "tol", 0 ),
    ROW ( "check", "30 RJ base", "actual", CALCULATE ( [Delivered Orders With Date], 'public bi_orders'[customer_state] = "RJ" ) + 0, "expected", 12350, "tol", 0 ),
    ROW ( "check", "31 RJ late", "actual", CALCULATE ( [Late Orders], 'public bi_orders'[customer_state] = "RJ" ) + 0, "expected", 1495, "tol", 0 ),
    ROW ( "check", "32 RJ not delivered", "actual", CALCULATE ( [Not Delivered Share], 'public bi_orders'[customer_state] = "RJ" ) + 0, "expected", 0.0391, "tol", 0.00005 ),
    ROW ( "check", "33 RJ low-rated", "actual", CALCULATE ( [Low-Rated Orders], 'public bi_orders'[customer_state] = "RJ" ) + 0, "expected", 2238, "tol", 0 ),
    ROW ( "check", "34 SP base", "actual", CALCULATE ( [Delivered Orders With Date], 'public bi_orders'[customer_state] = "SP" ) + 0, "expected", 40494, "tol", 0 ),
    ROW ( "check", "35 SP late", "actual", CALCULATE ( [Late Orders], 'public bi_orders'[customer_state] = "SP" ) + 0, "expected", 1820, "tol", 0 ),
    ROW ( "check", "36 SP not delivered", "actual", CALCULATE ( [Not Delivered Share], 'public bi_orders'[customer_state] = "SP" ) + 0, "expected", 0.0298, "tol", 0.00005 ),
    ROW ( "check", "37 SP low-rated", "actual", CALCULATE ( [Low-Rated Orders], 'public bi_orders'[customer_state] = "SP" ) + 0, "expected", 4303, "tol", 0 ),
    ROW ( "check", "38 Nov 2017 base", "actual", CALCULATE ( [Delivered Orders With Date], Nov2017 ) + 0, "expected", 7288, "tol", 0 ),
    ROW ( "check", "39 Nov 2017 late", "actual", CALCULATE ( [Late Orders], Nov2017 ) + 0, "expected", 904, "tol", 0 ),
    ROW ( "check", "40 Nov 2017 median promised", "actual", CALCULATE ( [Median Promised Days], Nov2017 ) + 0, "expected", 23, "tol", 0 ),
    ROW ( "check", "41 Nov 2017 median actual", "actual", CALCULATE ( [Median Actual Days], Nov2017 ) + 0, "expected", 13, "tol", 0 ),
    ROW ( "check", "42 review filter: delivered with date", "actual", CALCULATE ( [Delivered Orders With Date], 'public bi_order_reviews'[latest_review_score] = 1 ) + 0, "expected", 96470, "tol", 0 ),
    ROW ( "check", "43 review filter: late orders", "actual", CALCULATE ( [Late Orders], 'public bi_order_reviews'[Delivery Review Group] = OnTimeGroup ) + 0, "expected", 6534, "tol", 0 ),
    ROW ( "check", "44 review filter: total orders", "actual", CALCULATE ( [Total Orders], 'public bi_order_reviews'[Order Type] = "Multi-item" ) + 0, "expected", 96478, "tol", 0 ),
    ROW ( "check", "45 KPI total orders", "actual", [Total Orders] + 0, "expected", 96478, "tol", 0 ),
    ROW ( "check", "46 KPI on-time rate", "actual", [On-Time Delivery Rate] + 0, "expected", 0.9323, "tol", 0.00005 ),
    ROW ( "check", "47 KPI average delivery days", "actual", [Average Delivery Time] + 0, "expected", 12.5069, "tol", 0.00005 ),
    ROW ( "check", "48 KPI product sales", "actual", [Total Product Sales] + 0, "expected", 13221498.11, "tol", 0.005 ),
    ROW ( "check", "49 KPI average order value", "actual", [Average Order Value] + 0, "expected", 137.04, "tol", 0.005 )
)
RETURN
    ADDCOLUMNS ( Checks, "result", IF ( ABS ( [actual] - [expected] ) <= [tol], "PASS", "FAIL" ) )
ORDER BY [check]
```

</details>

Sources for the targets:
- RJ and SP figures: the state view in [hypothesis_log.md](hypothesis_log.md) and audit item L2.
- November 2017 figures: the log's B1 and promise tables.
- Derived targets, calculated from documented counts: 0.0677, 0.0298 overall, and 2,849.

### Checks 50–67: zero events

Added with the zero-event changes. Result: 18 passed, 0 failed. A result of −1 means the measure returned blank, so blank and 0 can be told apart.

<details>
<summary>Show the query</summary>

```dax
EVALUATE
VAR Mar2018 = FILTER ( ALL ( 'public bi_orders'[order_purchase_timestamp] ),
        'public bi_orders'[order_purchase_timestamp] >= DATE ( 2018, 3, 1 ) && 'public bi_orders'[order_purchase_timestamp] < DATE ( 2018, 4, 1 ) )
VAR Sep2016 = FILTER ( ALL ( 'public bi_orders'[order_purchase_timestamp] ),
        'public bi_orders'[order_purchase_timestamp] >= DATE ( 2016, 9, 1 ) && 'public bi_orders'[order_purchase_timestamp] < DATE ( 2016, 10, 1 ) )
VAR Sep2018 = FILTER ( ALL ( 'public bi_orders'[order_purchase_timestamp] ),
        'public bi_orders'[order_purchase_timestamp] >= DATE ( 2018, 9, 1 ) && 'public bi_orders'[order_purchase_timestamp] < DATE ( 2018, 10, 1 ) )
VAR Checks = UNION (
    ROW ( "check", "50 AC Mar 2018 delivered with date", "actual", VAR x = CALCULATE ( [Delivered Orders With Date], 'public bi_orders'[customer_state] = "AC", Mar2018 ) RETURN IF ( ISBLANK ( x ), -1, x ), "expected", 2, "tol", 0 ),
    ROW ( "check", "51 AC Mar 2018 late orders is 0", "actual", VAR x = CALCULATE ( [Late Orders], 'public bi_orders'[customer_state] = "AC", Mar2018 ) RETURN IF ( ISBLANK ( x ), -1, x ), "expected", 0, "tol", 0 ),
    ROW ( "check", "52 AC Mar 2018 late rate is 0", "actual", VAR x = CALCULATE ( [Late Delivery Rate], 'public bi_orders'[customer_state] = "AC", Mar2018 ) RETURN IF ( ISBLANK ( x ), -1, x ), "expected", 0, "tol", 0 ),
    ROW ( "check", "53 AC Mar 2018 on-time rate", "actual", VAR x = CALCULATE ( [On-Time Delivery Rate], 'public bi_orders'[customer_state] = "AC", Mar2018 ) RETURN IF ( ISBLANK ( x ), -1, x ), "expected", 1, "tol", 0 ),
    ROW ( "check", "54 AC Mar 2018 reviewed orders", "actual", VAR x = CALCULATE ( [Reviewed Orders], 'public bi_orders'[customer_state] = "AC", Mar2018 ) RETURN IF ( ISBLANK ( x ), -1, x ), "expected", 2, "tol", 0 ),
    ROW ( "check", "55 AC Mar 2018 low-rated is 0", "actual", VAR x = CALCULATE ( [Low-Rated Orders], 'public bi_orders'[customer_state] = "AC", Mar2018 ) RETURN IF ( ISBLANK ( x ), -1, x ), "expected", 0, "tol", 0 ),
    ROW ( "check", "56 AC Mar 2018 low-rating share is 0", "actual", VAR x = CALCULATE ( [Low-Rating Share], 'public bi_orders'[customer_state] = "AC", Mar2018 ) RETURN IF ( ISBLANK ( x ), -1, x ), "expected", 0, "tol", 0 ),
    ROW ( "check", "57 SP Sep 2016 late orders", "actual", VAR x = CALCULATE ( [Late Orders], 'public bi_orders'[customer_state] = "SP", Sep2016 ) RETURN IF ( ISBLANK ( x ), -1, x ), "expected", 1, "tol", 0 ),
    ROW ( "check", "58 SP Sep 2016 on-time rate is 0", "actual", VAR x = CALCULATE ( [On-Time Delivery Rate], 'public bi_orders'[customer_state] = "SP", Sep2016 ) RETURN IF ( ISBLANK ( x ), -1, x ), "expected", 0, "tol", 0 ),
    ROW ( "check", "59 SP Sep 2018 late orders blank", "actual", VAR x = CALCULATE ( [Late Orders], 'public bi_orders'[customer_state] = "SP", Sep2018 ) RETURN IF ( ISBLANK ( x ), -1, x ), "expected", -1, "tol", 0 ),
    ROW ( "check", "60 SP Sep 2018 late rate blank", "actual", VAR x = CALCULATE ( [Late Delivery Rate], 'public bi_orders'[customer_state] = "SP", Sep2018 ) RETURN IF ( ISBLANK ( x ), -1, x ), "expected", -1, "tol", 0 ),
    ROW ( "check", "61 SP Sep 2018 on-time rate blank", "actual", VAR x = CALCULATE ( [On-Time Delivery Rate], 'public bi_orders'[customer_state] = "SP", Sep2018 ) RETURN IF ( ISBLANK ( x ), -1, x ), "expected", -1, "tol", 0 ),
    ROW ( "check", "62 SP Sep 2018 low-rated blank", "actual", VAR x = CALCULATE ( [Low-Rated Orders], 'public bi_orders'[customer_state] = "SP", Sep2018 ) RETURN IF ( ISBLANK ( x ), -1, x ), "expected", -1, "tol", 0 ),
    ROW ( "check", "63 SP Sep 2018 low-rating share blank", "actual", VAR x = CALCULATE ( [Low-Rating Share], 'public bi_orders'[customer_state] = "SP", Sep2018 ) RETURN IF ( ISBLANK ( x ), -1, x ), "expected", -1, "tol", 0 ),
    ROW ( "check", "64 SP Sep 2018 median actual blank", "actual", VAR x = CALCULATE ( [Median Actual Days], 'public bi_orders'[customer_state] = "SP", Sep2018 ) RETURN IF ( ISBLANK ( x ), -1, x ), "expected", -1, "tol", 0 ),
    ROW ( "check", "65 states with a late-orders value", "actual", COUNTROWS ( FILTER ( VALUES ( 'public bi_orders'[customer_state] ), NOT ISBLANK ( [Late Orders] ) ) ) + 0, "expected", 27, "tol", 0 ),
    ROW ( "check", "66 Mar 2018 late orders blank only without orders", "actual", CALCULATE ( COUNTROWS ( FILTER ( VALUES ( 'public bi_orders'[customer_state] ), ISBLANK ( [Late Orders] ) <> ISBLANK ( [Delivered Orders With Date] ) ) ), Mar2018 ) + 0, "expected", 0, "tol", 0 ),
    ROW ( "check", "67 review labels low-rated blank only without reviews", "actual", COUNTROWS ( FILTER ( VALUES ( 'public bi_order_reviews'[Delivery Review Label] ), ISBLANK ( [Low-Rated Orders] ) <> ISBLANK ( [Reviewed Orders] ) ) ) + 0, "expected", 0, "tol", 0 )
)
RETURN
    ADDCOLUMNS ( Checks, "result", IF ( ABS ( [actual] - [expected] ) <= [tol], "PASS", "FAIL" ) )
ORDER BY [check]
```

</details>

### Checks 68–85: helper measures

Added with the interaction and sample-size update. Result: 18 passed, 0 failed. Text and blank results are converted to 1 for a match and 0 otherwise. `LocalDateTable_3e939c76…` is the automatic date table for `order_purchase_timestamp`; a month click on a chart filters it.

<details>
<summary>Show the query</summary>

```dax
EVALUATE
VAR Mar2018 = FILTER ( ALL ( 'public bi_orders'[order_purchase_timestamp] ),
        'public bi_orders'[order_purchase_timestamp] >= DATE ( 2018, 3, 1 ) && 'public bi_orders'[order_purchase_timestamp] < DATE ( 2018, 4, 1 ) )
VAR Sep2018 = FILTER ( ALL ( 'public bi_orders'[order_purchase_timestamp] ),
        'public bi_orders'[order_purchase_timestamp] >= DATE ( 2018, 9, 1 ) && 'public bi_orders'[order_purchase_timestamp] < DATE ( 2018, 10, 1 ) )
VAR Core12 = "BA,CE,DF,ES,GO,MG,PE,PR,RJ,RS,SC,SP"
VAR Checks = UNION (
    ROW ( "check", "68 CE full-period orders", "actual", CALCULATE ( [State Full-Period Orders], 'public bi_orders'[customer_state] = "CE" ) + 0, "expected", 1279, "tol", 0 ),
    ROW ( "check", "69 CE full-period ignores purchase-date filter", "actual", CALCULATE ( [State Full-Period Orders], 'public bi_orders'[customer_state] = "CE", Mar2018 ) + 0, "expected", 1279, "tol", 0 ),
    ROW ( "check", "70 CE full-period ignores date-table filter", "actual", CALCULATE ( [State Full-Period Orders], 'public bi_orders'[customer_state] = "CE",
        'LocalDateTable_3e939c76-13e6-4603-bcd3-a0a9f96e9114'[Year] = 2018, 'LocalDateTable_3e939c76-13e6-4603-bcd3-a0a9f96e9114'[MonthNo] = 3 ) + 0, "expected", 1279, "tol", 0 ),
    ROW ( "check", "71 SP full-period orders", "actual", CALCULATE ( [State Full-Period Orders], 'public bi_orders'[customer_state] = "SP" ) + 0, "expected", 40494, "tol", 0 ),
    ROW ( "check", "72 month coverage, AL + Mar 2018 (date table)", "actual", CALCULATE ( [Month Coverage Orders], 'public bi_orders'[customer_state] = "AL",
        'LocalDateTable_3e939c76-13e6-4603-bcd3-a0a9f96e9114'[Year] = 2018, 'LocalDateTable_3e939c76-13e6-4603-bcd3-a0a9f96e9114'[MonthNo] = 3 ) + 0, "expected", 7003, "tol", 0 ),
    ROW ( "check", "73 month coverage, Mar 2018, no state", "actual", CALCULATE ( [Month Coverage Orders], Mar2018 ) + 0, "expected", 7003, "tol", 0 ),
    ROW ( "check", "74 Top 12 with no filter", "actual", IF ( CONCATENATEX ( TOPN ( 12, VALUES ( 'public bi_orders'[customer_state] ), [State Full-Period Orders] ), 'public bi_orders'[customer_state], ",", 'public bi_orders'[customer_state], ASC ) = Core12, 1, 0 ), "expected", 1, "tol", 0 ),
    ROW ( "check", "75 Top 12 under Mar 2018 (same 12)", "actual", IF ( CALCULATE ( CONCATENATEX ( TOPN ( 12, VALUES ( 'public bi_orders'[customer_state] ), [State Full-Period Orders] ), 'public bi_orders'[customer_state], ",", 'public bi_orders'[customer_state], ASC ), Mar2018 ) = Core12, 1, 0 ), "expected", 1, "tol", 0 ),
    ROW ( "check", "76 Top 12 when AL is selected", "actual", IF ( CALCULATE ( CONCATENATEX ( TOPN ( 12, VALUES ( 'public bi_orders'[customer_state] ), [State Full-Period Orders] ), 'public bi_orders'[customer_state], ",", 'public bi_orders'[customer_state], ASC ), 'public bi_orders'[customer_state] = "AL" ) = "AL", 1, 0 ), "expected", 1, "tol", 0 ),
    ROW ( "check", "77 colour AC Mar 2018 (2 orders) pale grey", "actual", IF ( CALCULATE ( [Sample Bar Colour], 'public bi_orders'[customer_state] = "AC", Mar2018 ) = "#B4BDCA", 1, 0 ), "expected", 1, "tol", 0 ),
    ROW ( "check", "78 colour CE Mar 2018 (93 orders) light blue", "actual", IF ( CALCULATE ( [Sample Bar Colour], 'public bi_orders'[customer_state] = "CE", Mar2018 ) = "#8FB1E6", 1, 0 ), "expected", 1, "tol", 0 ),
    ROW ( "check", "79 colour SP Mar 2018 standard", "actual", IF ( CALCULATE ( [Sample Bar Colour], 'public bi_orders'[customer_state] = "SP", Mar2018 ) = "#2463C5", 1, 0 ), "expected", 1, "tol", 0 ),
    ROW ( "check", "80 colour SP Sep 2018 (no delivered orders) blank", "actual", IF ( ISBLANK ( CALCULATE ( [Sample Bar Colour], 'public bi_orders'[customer_state] = "SP", Sep2018 ) ), 1, 0 ), "expected", 1, "tol", 0 ),
    ROW ( "check", "81 monthly-chart months, no state", "actual", COUNTROWS ( FILTER ( SUMMARIZE ( 'LocalDateTable_3e939c76-13e6-4603-bcd3-a0a9f96e9114', [Year], [MonthNo] ),
        [Month Coverage Orders] >= 100 && [Delivered Orders With Date] >= 1 ) ) + 0, "expected", 21, "tol", 0 ),
    ROW ( "check", "82 monthly-chart months, AL", "actual", CALCULATE ( COUNTROWS ( FILTER ( SUMMARIZE ( 'LocalDateTable_3e939c76-13e6-4603-bcd3-a0a9f96e9114', [Year], [MonthNo] ),
        [Month Coverage Orders] >= 100 && [Delivered Orders With Date] >= 1 ) ), 'public bi_orders'[customer_state] = "AL" ) + 0, "expected", 21, "tol", 0 ),
    ROW ( "check", "83 AL months under 30 orders", "actual", CALCULATE ( COUNTROWS ( FILTER ( SUMMARIZE ( 'LocalDateTable_3e939c76-13e6-4603-bcd3-a0a9f96e9114', [Year], [MonthNo] ),
        [Month Coverage Orders] >= 100 && [Delivered Orders With Date] >= 1 && [Delivered Orders With Date] < 30 ) ), 'public bi_orders'[customer_state] = "AL" ) + 0, "expected", 20, "tol", 0 ),
    ROW ( "check", "84 monthly-chart months, RR (4 months blank)", "actual", CALCULATE ( COUNTROWS ( FILTER ( SUMMARIZE ( 'LocalDateTable_3e939c76-13e6-4603-bcd3-a0a9f96e9114', [Year], [MonthNo] ),
        [Month Coverage Orders] >= 100 && [Delivered Orders With Date] >= 1 ) ), 'public bi_orders'[customer_state] = "RR" ) + 0, "expected", 17, "tol", 0 ),
    ROW ( "check", "85 CE Mar 2018 late rate", "actual", CALCULATE ( [Late Delivery Rate], 'public bi_orders'[customer_state] = "CE", Mar2018 ) + 0, "expected", 0.5054, "tol", 0.00005 )
)
RETURN
    ADDCOLUMNS ( Checks, "result", IF ( ABS ( [actual] - [expected] ) <= [tol], "PASS", "FAIL" ) )
ORDER BY [check]
```

</details>

Sources for checks 50–85: expected values were calculated from the order export `data/processed/orders_analysis.csv`, using the same definitions as the measures.
