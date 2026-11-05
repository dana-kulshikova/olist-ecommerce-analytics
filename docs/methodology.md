# Methodology

**Status: approved plan. The main analysis hasn't been run yet.**

This document explains how the case study reaches its conclusions and how much weight they can bear. The exact hypothesis definitions and statistical details are in [analysis_plan.md](analysis_plan.md), and results will be recorded in `hypothesis_log.md`.

## The question

What factors are associated with delivery delays in this Brazilian marketplace, how are delays related to customer satisfaction, and where should the business prioritise operational improvements?

## What the results can and can't show

- **Results show associations, not causes.** The data is observational, with no experiments and no carrier, route, weather, stock or customer-service data. Recommendations are therefore framed as actions to test.
- **The data was inspected before this plan was written.** The project has one dataset with no holdout sample. Earlier project work published state late rates, and a feasibility scan previewed unadjusted late rates and review scores. Adjusted estimates hadn't been calculated.
- **So no result is fully independent confirmation.** Even where a result is labelled "supported", it means the evidence is consistent with the hypothesis under this plan. It isn't causal proof.

## How findings are labelled

| Type | What it means | How it's described |
|---|---|---|
| **Pre-specified question** | Set in the project brief before the feasibility scan, with the analysis fixed before it runs. Unadjusted figures were already previewed | Supported, unsupported or inconclusive |
| **Exploratory** | The idea came from, or was shaped by, looking at the data | "Pattern observed" or "not observed". It suggests what to investigate, and never counts as confirmation |
| **Descriptive** | A measurement, such as sales by month | Reported as a measurement |

## The questions

**Pre-specified**

| ID | Question |
|---|---|
| A1 | Is RJ's late rate higher than SP's after accounting for other differences? |
| A2 | Do late orders receive more low ratings? |
| A3 | Do longer delays bring more low ratings? |
| A4 | Is longer distance linked to more late orders? |
| A5 | Is higher freight cost linked to more late orders? |
| A6 | Do a few sellers hold a disproportionate share of late orders? |
| A7 | Do late rates differ materially between product categories? |

**Exploratory**

| ID | Question |
|---|---|
| B1 | Are late orders concentrated in particular months? |
| B2 | Does RJ's gap change between peak months and other months? |
| B3 | Do low ratings differ by whether customers answered before or after the order arrived? |
| B4 | Does the link between delay length and ratings hold within those answer-timing groups? |
| B5 | How do seller handover delays and the later delivery stage each relate to lateness? |
| B6 | Do multi-item orders receive more low ratings after accounting for other factors? |
| B7 | How many low ratings fall on orders that arrived on time? |

**Descriptive:** sales trends, volume against order value, geographic and category concentration, promised against actual delivery times, and a business priority view. There's at most one complete year of data, so no seasonal claim will be made.

## How strong a finding must be

Each finding is judged on two separate questions.

**1. What does the main analysis show?**

| Label | Meaning |
|---|---|
| **Supported** | The effect is in the predicted direction, its 95% confidence interval excludes zero, it holds after correcting for multiple tests, and it meets the practical screening criterion |
| **Detectable, not practically important** | The effect is statistically clear, but below the screening criterion |
| **Unsupported** | The effect is absent, in the opposite direction, or its whole interval lies below the criterion |
| **Inconclusive** | The evidence is too uncertain to judge |

**2. How much does it depend on reasonable analytical choices?**

| Label | Meaning |
|---|---|
| **Robust** | Direction and practical conclusion hold across the sensitivity analyses, even if the size moves somewhat |
| **Sensitive** | Direction holds, but the size or practical conclusion depends on a reasonable choice. Reported with its range and the choice that matters |
| **Not robust** | Direction reverses or the effect disappears under a reasonable choice. The headline becomes inconclusive |

For every sensitivity analysis, the changes in effect size, direction and uncertainty are reported. A minor variation doesn't dismiss a finding, and judgement calls are explained.

### Practical screening criteria

These are **researcher-defined screening criteria, not business-validated targets**. They were chosen after seeing the preview, to separate effects worth discussing from trivial ones. A real business would set its own thresholds based on costs and priorities.

| Outcome | Screening criterion |
|---|---|
| Late rate | 2 percentage points and at least 500 late orders in the segment |
| Low-rating share | 5 percentage points |
| Mean review score | 0.25 points |
| Seller concentration | Late-order share exceeds order share by 10 points |
| Category spread | 5 points between the highest and lowest adjusted rates |

## Consistent metric definitions

Existing KPIs keep their definitions and values. The analysis must first reproduce these figures, or stop until any difference is explained.

| Metric | Value (all data) |
|---|---:|
| Delivered orders | 96,478 |
| Delivered orders with a date | 96,470 |
| On-time orders | 89,936 |
| Late orders | 6,534 |
| On-Time Delivery Rate | 93.23% |
| Total Product Sales | R$ 13,221,498.11 |
| Average Order Value | R$ 137.04 |
| Average Delivery Time | 12.5 days |

| Term | Definition, used the same way in SQL, Python and Power BI |
|---|---|
| Analysis base | Delivered orders with a delivery date |
| Late | Delivered after the estimated calendar date |
| On time | Delivered on or before the estimated calendar date |
| Low rating | 1 or 2 stars |
| Answered before arrival | The review answer timestamp is earlier than the delivery timestamp |

The exact expressions for each tool are in [analysis_plan.md](analysis_plan.md#metric-expressions).

## Data handling rules

| Situation | Rule |
|---|---|
| Several reviews on one order | Use the latest answered review. The earliest review is tested as a sensitivity check |
| Review IDs repeated across orders | Keep them, since each order has its own link. Excluding them is tested |
| Several sellers on one order | Keep them in order-level results. Leave them out of seller, route and distance analysis, and report how many |
| Handover delay | Carrier handover after the latest item's shipping limit |
| Later delivery stage | Called the **handover-to-delivery stage**. It isn't attributed to carriers, because the data can't separate carrier performance from other causes |
| Multi-item order | Two or more item rows |
| Category | The highest-priced item's category; missing values are labelled `unknown` |
| Distance | Approximate straight-line distance between ZIP-prefix positions, not route distance |
| Small groups | Sellers need at least 100 orders to be ranked. Groups under 30 aren't reported |
| Data source | PostgreSQL read-only exports are primary, cross-checked against the source CSVs |

**Invalid date sequences (provisional):** 197 delivered orders have `valid_delivery_dates = FALSE`. They're being investigated to separate genuine inconsistencies from possible timestamp or time zone effects. For now, they stay in late rates and are left out of stage timing. This rule will be confirmed or changed here, with reasons, before the main analysis.

## Known limitations

- **Reviewers may differ from non-reviewers**, and answering after arrival is itself selective.
- **Undelivered orders are excluded**, though cancellations and non-delivery may be the worst experiences.
- **Lateness depends on the promise.** A longer estimate makes an order less likely to count as late.
- **One marketplace, one period.** Results may not generalise beyond 2016–2018 or to other marketplaces.

## Order of work

1. Investigate the 197 flagged orders, and confirm the rule above.
2. Build the read-only SQL dataset, export it, and reproduce the KPI figures exactly.
3. Run the pre-specified questions, then the exploratory and descriptive work, then the sensitivity analyses.
4. Cross-check key results between SQL and Python.
5. Record every result, including unsupported ones, in `hypothesis_log.md`.

## Changes to this plan

Any change after approval is listed here with its date and reason, including whether results were already known.

| Date | Change | Reason | Made after seeing results? |
|---|---|---|---|
| | None yet | | |
