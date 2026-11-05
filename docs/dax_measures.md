# DAX Measures

Generated from `powerbi/Olist_Ecommerce_Dashboard.SemanticModel/definition/tables/public bi_orders.tmdl`, so the expressions below are exact copies.

## Total Product Sales

Item prices on delivered orders. Excludes freight.

Format string: `"R$ "#,##0.00`

```dax
CALCULATE(
    SUM('public bi_orders'[product_sales]),
    'public bi_orders'[order_status] = "delivered")
```

## Total Orders

Distinct delivered orders, so cancelled or in-progress orders aren't counted.

Format string: `#,##0`

```dax
CALCULATE(
    DISTINCTCOUNT('public bi_orders'[order_id]),
    'public bi_orders'[order_status] = "delivered"
)
```

## Average Order Value

Product sales per delivered order.

Format string: `"R$ "#,##0.00`

```dax
DIVIDE(
    [Total Product Sales],
    [Total Orders]
)
```

## Average Delivery Time

Purchase to customer delivery on delivered orders with `valid_delivery_dates` = TRUE. `DATEDIFF(DAY)` counts calendar-day boundaries, so it can differ slightly from a fractional-day calculation (query 12 in `sql/03_data_quality_and_analysis.sql`).

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

## On-Time Delivery Rate

Delivered on or before the estimated calendar date. Corrected during the project; see below.

Format string: `0.00%;-0.00%;0.00%`

```dax
DIVIDE(
    CALCULATE(
        COUNTROWS('public bi_orders'),
        'public bi_orders'[order_status] = "delivered",
        NOT(ISBLANK('public bi_orders'[order_delivered_customer_date])),
        INT('public bi_orders'[order_delivered_customer_date]) <= INT('public bi_orders'[order_estimated_delivery_date])
    ),
    CALCULATE(
        COUNTROWS('public bi_orders'),
        'public bi_orders'[order_status] = "delivered",
        NOT(ISBLANK('public bi_orders'[order_delivered_customer_date]))
    )
)
```

## Key Takeaways

Earlier text summary. The hidden table on the report page still uses it; the visible panel uses cards bound directly to the measures.

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

## Top State by Sales

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

## Top State Sales Share

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

## Empty measures

`Measure` and `Measure 2` have no expression and aren't used by any visual. They remain in the model because this repository is an exact copy of the working project.
