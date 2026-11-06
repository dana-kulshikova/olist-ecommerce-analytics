# DAX Measures

Generated from `powerbi/Olist_Ecommerce_Dashboard.SemanticModel/definition/tables/`, so every expression below is an exact copy of the saved model. Validation results are in [powerbi_validation.md](powerbi_validation.md).

The model has two imported tables: `public bi_orders` (one row per order, all statuses) and `public bi_order_reviews` (one row per order with a selected review). See [data_model.md](data_model.md).

## Contents

- [Overview page measures](#overview-page-measures)
- [Delivery measures](#delivery-measures)
- [Review measures](#review-measures)
- [Helper measures for the charts](#helper-measures-for-the-charts)
- [Calculated columns](#calculated-columns)
- [Shared rules](#shared-rules)
- [Zero events and missing data](#zero-events-and-missing-data)
- [The on-time correction](#the-on-time-correction)
- [Removed placeholder measures](#removed-placeholder-measures)

## Overview page measures

These measures were built for the first page. On-Time Delivery Rate later gained the zero-event change described below; the others are unchanged.

### Total Product Sales

Item prices on delivered orders. Excludes freight.

Format string: `"R$ "#,##0.00`

```dax
CALCULATE(
    SUM('public bi_orders'[product_sales]),
    'public bi_orders'[order_status] = "delivered")
```

### Total Orders

Distinct delivered orders, so cancelled or in-progress orders aren't counted. Includes the 8 delivered orders with no delivery date.

Format string: `#,##0`

```dax
CALCULATE(
    DISTINCTCOUNT('public bi_orders'[order_id]),
    'public bi_orders'[order_status] = "delivered"
)
```

### Average Order Value

Product sales per delivered order.

Format string: `"R$ "#,##0.00`

```dax
DIVIDE(
    [Total Product Sales],
    [Total Orders]
)
```

### Average Delivery Time

Mean calendar days from purchase to customer delivery, on delivered orders with `valid_delivery_dates` = TRUE. `DATEDIFF(DAY)` counts calendar-day boundaries, so it can differ slightly from a fractional-day calculation (query 12 in `sql/03_data_quality_and_analysis.sql`).

Format string: `0.0 "days"`

```dax
CALCULATE(
    AVERAGEX(
        'public bi_orders',
        DATEDIFF(
            'public bi_orders'[order_purchase_timestamp],
            'public bi_orders'[order_delivered_customer_date],
            DAY
        )
    ),
    'public bi_orders'[order_status] = "delivered",
    'public bi_orders'[valid_delivery_dates] = TRUE()
)
```

### On-Time Delivery Rate

Delivered on or before the estimated calendar date, over delivered orders with a delivery date. Corrected during the project; see below. Its `CALCULATE` filters replace any outside filter on `order_status` and on the two date columns, so it isn't meant to be sliced by those columns.

The numerator ends in `+ 0`, so a selection where every delivered order was late shows 0.00% rather than a blank. When there are no delivered orders, the denominator is blank and `DIVIDE` still returns blank.

Format string: `0.00%;-0.00%;0.00%`

```dax
DIVIDE(
    CALCULATE(
        COUNTROWS('public bi_orders'),
        'public bi_orders'[order_status] = "delivered",
        NOT(ISBLANK('public bi_orders'[order_delivered_customer_date])),
        INT('public bi_orders'[order_delivered_customer_date]) <= INT('public bi_orders'[order_estimated_delivery_date])
    ) + 0,
    CALCULATE(
        COUNTROWS('public bi_orders'),
        'public bi_orders'[order_status] = "delivered",
        NOT(ISBLANK('public bi_orders'[order_delivered_customer_date]))
    )
)
```

### Key Takeaways

Earlier text summary. The hidden table on the Overview page still uses it; the visible panel uses cards bound directly to the measures.

```dax
"• R$ " & FORMAT([Total Product Sales] / 1000000, "#,##0.00") & "M in total product sales across "
& FORMAT([Total Orders], "#,##0") & " orders."
& UNICHAR(10) & UNICHAR(10)
& "• Average order value: R$ "
& FORMAT([Average Order Value], "#,##0.00") & "."
& UNICHAR(10) & UNICHAR(10)
& "• Average delivery time: "
& FORMAT([Average Delivery Time], "0.00") & " days."
& UNICHAR(10) & UNICHAR(10)
& "• On-time delivery rate: "
& FORMAT([On-Time Delivery Rate], "0.00%") & "."
```

### Top State by Sales

Added for the Key Takeaways panel. Responds to the date slicer.

```dax
VAR TopStateRow =
    TOPN(
        1,
        ADDCOLUMNS(
            VALUES('public bi_orders'[customer_state]),
            "@Sales", [Total Product Sales]
        ),
        [@Sales], DESC
    )
RETURN
    IF(
        NOT(ISBLANK([Total Product Sales])),
        MAXX(TopStateRow, 'public bi_orders'[customer_state])
    )
```

### Top State Sales Share

The leading state's share of sales in the current filter context. Responds to the date slicer.

Format string: `0.0%`

```dax
VAR TopStateSales =
    MAXX(
        VALUES('public bi_orders'[customer_state]),
        [Total Product Sales]
    )
RETURN
    DIVIDE(TopStateSales, [Total Product Sales])
```

## Delivery measures

Added for the Delivery & Customer Experience page, in `public bi_orders`. They use `KEEPFILTERS`, so slicers and visual filters are kept rather than replaced. The population is delivered orders with a recorded delivery date (96,470), which includes the 189 delivered orders flagged by `valid_delivery_dates`: late status uses only the delivery and estimated dates, so those flags matter only for stage timing.

### Delivered Orders With Date

Delivered orders with a recorded delivery date. The denominator for every delivery rate on the page. Orders with no delivery date are excluded.

Format string: `0`

```dax
CALCULATE (
    COUNTROWS ( 'public bi_orders' ),
    KEEPFILTERS ( 'public bi_orders'[order_status] = "delivered" ),
    KEEPFILTERS (
        NOT ISBLANK ( 'public bi_orders'[order_delivered_customer_date] )
    )
)
```

### Late Orders

Orders delivered after the estimated calendar date. `INT()` compares calendar days, the same comparison as `::date` in SQL and `.normalize()` in Python. Format `#,0` shows thousands separators.

It returns 0 when delivered orders with a date exist but none is late, and blank when there are no such orders. Late Delivery Rate therefore shows 0.00% for a selection with no late orders. Non-zero results are unchanged.

Format string: `#,0`

```dax
VAR DeliveredWithDate = [Delivered Orders With Date]
RETURN
    IF (
        NOT ISBLANK ( DeliveredWithDate ),
        CALCULATE (
            [Delivered Orders With Date],
            KEEPFILTERS (
                INT ( 'public bi_orders'[order_delivered_customer_date] )
                > INT ( 'public bi_orders'[order_estimated_delivery_date] )
            )
        ) + 0
    )
```

### Late Delivery Rate

Late Orders ÷ Delivered Orders With Date. Unlike the On-Time Delivery Rate, it keeps outside filters, so the two add up to 100% only when no status or delivery-date filter is applied, as on the dashboard.

Format string: `0.00%;-0.00%;0.00%`

```dax
DIVIDE (
    [Late Orders],
    [Delivered Orders With Date]
)
```

### Median Promised Days

Median calendar days from purchase to the estimated delivery date, over delivered orders with a delivery date. `DATEDIFF(DAY)` counts day boundaries, so it equals the difference between calendar dates; it isn't elapsed time. `MEDIANX` averages the two middle values for an even count.

Format string: `0.0`

```dax
MEDIANX (
    FILTER (
        'public bi_orders',
        'public bi_orders'[order_status] = "delivered"
            && NOT ISBLANK (
                'public bi_orders'[order_delivered_customer_date]
            )
    ),
    DATEDIFF (
        'public bi_orders'[order_purchase_timestamp],
        'public bi_orders'[order_estimated_delivery_date],
        DAY
    )
)
```

### Median Actual Days

Median calendar days from purchase to delivery, on the same population. Unlike Average Delivery Time (a mean on valid dates only), it includes flagged orders, matching the research definition.

Format string: `0.0`

```dax
MEDIANX (
    FILTER (
        'public bi_orders',
        'public bi_orders'[order_status] = "delivered"
            && NOT ISBLANK (
                'public bi_orders'[order_delivered_customer_date]
            )
    ),
    DATEDIFF (
        'public bi_orders'[order_purchase_timestamp],
        'public bi_orders'[order_delivered_customer_date],
        DAY
    )
)
```

### Not Delivered Share

Orders with any status other than delivered ÷ all orders. Deliberately wider than the delivery base, as a guardrail for orders the base leaves out. It mixes cancelled and unavailable orders with statuses that may still have been open when the data ended, such as shipped.

Format string: `0.00%;-0.00%;0.00%`

```dax
DIVIDE (
    CALCULATE (
        COUNTROWS ( 'public bi_orders' ),
        KEEPFILTERS (
            'public bi_orders'[order_status] <> "delivered"
        )
    ),
    COUNTROWS ( 'public bi_orders' )
)
```

## Review measures

In `public bi_order_reviews`. Filters on `public bi_orders` columns reach the review table through the single-direction relationship. Orders with no review aren't counted, and aren't treated as low ratings.

### Reviewed Orders

Orders with a selected review score whose order is delivered with a delivery date. The denominator for every review rate.

Format string: `0`

```dax
CALCULATE (
    COUNTROWS ( 'public bi_order_reviews' ),
    KEEPFILTERS (
        NOT ISBLANK (
            'public bi_order_reviews'[latest_review_score]
        )
    ),
    KEEPFILTERS (
        'public bi_orders'[order_status] = "delivered"
    ),
    KEEPFILTERS (
        NOT ISBLANK (
            'public bi_orders'[order_delivered_customer_date]
        )
    )
)
```

### Low-Rated Orders

Reviewed Orders rated 1 or 2 stars. Blank scores can't qualify, because Reviewed Orders already excludes them.

It returns 0 when reviewed orders exist but none is low-rated, and blank when there are no reviewed orders. Low-Rating Share therefore shows 0.00% rather than a blank. Non-zero results are unchanged.

Format string: `0`

```dax
VAR ReviewedOrders = [Reviewed Orders]
RETURN
    IF (
        NOT ISBLANK ( ReviewedOrders ),
        CALCULATE (
            [Reviewed Orders],
            KEEPFILTERS (
                'public bi_order_reviews'[latest_review_score] <= 2
            )
        ) + 0
    )
```

### Low-Rating Share

Low-Rated Orders ÷ Reviewed Orders.

Format string: `0.00%;-0.00%;0.00%`

```dax
DIVIDE (
    [Low-Rated Orders],
    [Reviewed Orders]
)
```

### Review Key Check

Hidden integrity check: rows minus distinct order IDs in the review table. It must be 0, confirming one selected review per order.

Format string: `0`

```dax
COUNTROWS ( 'public bi_order_reviews' )
    - DISTINCTCOUNT ( 'public bi_order_reviews'[order_id] )
```

## Helper measures for the charts

Three hidden measures in `public bi_orders` control which rows the Delivery page's charts show and how their bars are coloured. They don't change any figure, and no card displays them. [data_model.md](data_model.md#filtering-behaviour) describes how the charts use them.

### State Full-Period Orders

Delivered orders with a date for each state over the whole period. `ALLEXCEPT` keeps only the customer-state filter, so purchase-date slicers, month selections and the automatic date tables are ignored. The state chart's Top 12 filter ranks states by this measure. Its top 12 are exactly the states with 1,000+ delivered orders: the 12th, CE, has 1,279 and the 13th, PA, has 946.

Format string: `0`

```dax
CALCULATE (
    [Delivered Orders With Date],
    ALLEXCEPT ( 'public bi_orders', 'public bi_orders'[customer_state] )
)
```

### Month Coverage Orders

Delivered orders with a date in each month, across all customer states. Removing the state filter means a state selection doesn't change which months appear. The month and line charts show months where this is at least 100, which leaves out only September and December 2016, with 1 order each.

Format string: `0`

```dax
CALCULATE (
    [Delivered Orders With Date],
    REMOVEFILTERS ( 'public bi_orders'[customer_state] )
)
```

### Sample Bar Colour

The bar colour on the month and state charts, set from the delivered orders behind each bar in the current selection: pale grey below 30 (a very small sample), light blue from 30 to 99 (a small sample), and the standard blue from 100. It's blank when there are no delivered orders, so it can't create a bar.

```dax
VAR DeliveredWithDate = [Delivered Orders With Date]
RETURN
    SWITCH (
        TRUE (),
        ISBLANK ( DeliveredWithDate ), BLANK (),
        DeliveredWithDate < 30, "#B4BDCA",
        DeliveredWithDate < 100, "#8FB1E6",
        "#2463C5"
    )
```

## Calculated columns

All four are in `public bi_order_reviews`, so `public bi_orders` has no added columns.

### Delivery Review Group

Blank for review rows that aren't delivered orders with a delivery date and a score. Otherwise, on time or late by calendar date, then late reviews split by whether the review **answer timestamp** is earlier than the recorded delivery timestamp. The answer timestamp records when the answer was recorded; it isn't evidence of when the customer submitted the review, formed an opinion or received the order. Equal timestamps count as after delivery, matching the strict `<` in the research. A missing answer timestamp gets its own label instead of being guessed: in DAX, `BLANK < date` is TRUE. No row currently has that label.

```dax
VAR st = RELATED ( 'public bi_orders'[order_status] )
VAR d = RELATED ( 'public bi_orders'[order_delivered_customer_date] )
VAR e = RELATED ( 'public bi_orders'[order_estimated_delivery_date] )
VAR a = 'public bi_order_reviews'[latest_review_answered_ts]
RETURN
    SWITCH (
        TRUE (),
        st <> "delivered"
            || ISBLANK ( d )
            || ISBLANK ( 'public bi_order_reviews'[latest_review_score] ), BLANK (),
        INT ( d ) <= INT ( e ), "On time",
        ISBLANK ( a ), "Late, answer time missing",
        a < d, "Late, answered before delivery",
        "Late, answered after delivery"
    )
```

### Order Type

Multi-item means two or more item rows (`items_count`, a count of item rows in `bi_orders`). It doesn't mean distinct products or sellers.

```dax
VAR n = RELATED ( 'public bi_orders'[items_count] )
RETURN
    IF (
        n >= 2,
        "Multi-item",
        IF ( n = 1, "Single item" )
    )
```

### Delivery Status

Combines the two late timing groups into one Late category, for comparing order types by delivery status.

```dax
SWITCH (
    TRUE (),
    ISBLANK ( 'public bi_order_reviews'[Delivery Review Group] ), BLANK (),
    'public bi_order_reviews'[Delivery Review Group] = "On time", "On time",
    "Late"
)
```

### Delivery Review Label

A shorter display name for each Delivery Review Group value, used as the category axis of the review-timing chart so its labels aren't cut off. It maps values one to one and doesn't change any classification. Rows with a blank group stay blank.

```dax
SWITCH (
    'public bi_order_reviews'[Delivery Review Group],
    "Late, answered before delivery", "Late — before delivery",
    "Late, answered after delivery", "Late — after delivery",
    "Late, answer time missing", "Late — answer time missing",
    "On time", "On time",
    BLANK ()
)
```

## Shared rules

| Rule | Applies to |
|---|---|
| Late = delivery calendar date after the estimated calendar date | Late Orders, Late Delivery Rate, Delivery Review Group, On-Time Delivery Rate |
| Base = delivered status with a delivery date (96,470 orders) | All delivery and review measures except Not Delivered Share and Total Orders |
| The 189 flagged delivered orders with a delivery date stay in | All of the above. Only Average Delivery Time uses `valid_delivery_dates` |
| Days are calendar days (`DATEDIFF(DAY)`), not elapsed hours | Median Promised Days, Median Actual Days, Average Delivery Time |
| Low rating = latest selected review scored 1 or 2 | Low-Rated Orders, Low-Rating Share |
| Missing reviews are excluded, not counted as low | All review measures |

These are descriptive, unadjusted figures. The adjusted research estimates shown in the dashboard's Research Findings panel are fixed text from [hypothesis_log.md](hypothesis_log.md); no measure recalculates them.

## Zero events and missing data

A count of rows that match nothing returns blank in DAX, not 0. Before this change, a selection with delivered orders but no late ones showed Late Orders and Late Delivery Rate as `--`, next to an on-time rate of 100.00%. Three measures now separate the two cases:

| Situation | Example | Shown |
|---|---|---|
| Orders exist, none late | AC customers, March 2018: 2 delivered, 0 late | Late Orders 0, Late Delivery Rate 0.00% |
| Reviews exist, none low-rated | AC customers, March 2018: 2 reviewed, 0 low-rated | Low-Rated Orders 0, Low-Rating Share 0.00% |
| Orders exist, all late | SP customers, September 2016: 1 delivered, late | On-Time Delivery Rate 0.00% |
| No delivered orders | SP customers, September 2018 | Blank (`--` on cards; no bar on charts) |

Each change applies only when the measure's base population exists, so blank still means there's no data. Every non-zero result is unchanged.

## The on-time correction

The original numerator compared the two columns directly:

```dax
'public bi_orders'[order_delivered_customer_date] <= 'public bi_orders'[order_estimated_delivery_date]
```

This caused two errors:

1. Estimated dates are stored at midnight, so 1,292 orders delivered on the estimated day counted as late.
2. In DAX, `BLANK <= date` is TRUE, so 8 delivered orders with no delivery date counted as on time.

| | On-time orders | Delivered orders with a date | Rate |
|---|---:|---:|---:|
| Before | 88,652 | 96,470 | 91.90% |
| After | 89,936 | 96,470 | 93.23% |

The corrected result was confirmed in the Power BI engine and independently from the source CSV.

## Removed placeholder measures

`Measure` and `Measure 2` were empty placeholders left from the original training file. They had no expression, and no measure, column, visual, filter or tooltip referred to them, so they were removed from the model.
