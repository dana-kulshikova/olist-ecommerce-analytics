# Hypothesis Log

Results recorded under the plan in [analysis_plan.md](analysis_plan.md) and [methodology.md](methodology.md). Results are reproduced by `python/analysis/build_dataset.py` and `python/analysis/class_a.py`.

## Status

| Item | Status |
|---|---|
| Class A statistical evidence | Complete, and **provisional** |
| Robustness (16 sensitivity analyses) | **Not yet assessed** |
| Class B exploratory questions | Complete, **exploratory**, and not yet tested for robustness |
| Class C descriptive context | Complete |
| Independent cross-check of results | Not yet run |

**How to read this log.** A label here describes what the primary analysis shows. It doesn't say whether the finding holds under other reasonable choices, because that hasn't been tested. All results are observational associations, not causal effects. The data was also previewed before the plan was written, so no result is fully independent confirmation. Screening criteria are researcher-defined, not business-validated targets.

## Class A summary

| ID | Question | Adjusted effect | 95% interval | Holm p | Screening criterion | Provisional label | Robustness |
|---|---|---:|---:|---:|---:|---|---|
| A1 | RJ against SP late rate | +7.46 points | 5.88 to 9.13 | 4.28e-26 | 2 points, 500+ late orders | Supported | Not assessed |
| A2 | Late against on-time low ratings | +51.04 points | 49.58 to 52.28 | Below 1e-300 | 5 points | Supported | Not assessed |
| A3 | Longer delays and low ratings | +42.10 points (15+ against 1–3 days) | 39.04 to 45.22 | 2.79e-121 | 5 points between each adjacent band | Inconclusive | Not assessed |
| A4 | 600–1,000 km against 0–100 km late rate | +0.59 points | −0.49 to 1.50 | 0.257 | 2 points, 500+ late orders | Unsupported | Not assessed |
| A5 | Highest against lowest freight quartile late rate | +2.16 points | 1.27 to 3.01 | 3.20e-06 | 2 points, 500+ late orders | Supported, close to the criterion | Not assessed |
| A6 | Top 10% of sellers: late share minus order share | +6.97 points | 2.48 to 10.66 | 0.0006 | 10 points | Detectable, not practically important | Not assessed |
| A7 | Spread between categories' late rates | 3.69 points | 2.88 to 6.90 | 0.0201 | 5 points | Detectable, not practically important | Not assessed |

Holm correction covers these seven tests. A2's raw p-value is too small for the software to represent, so it's shown as below 1e-300.

**Flagged for a higher-replication bootstrap:** A5, A6 and A7, because their intervals straddle the screening criterion. A7's Holm p-value also lies between 0.01 and 0.10. A4's interval includes zero, so it was flagged automatically, but its upper limit is clearly below the criterion, so a re-check is low priority.

## Results by question

### A1. RJ compared with SP

| Group | Orders | Late orders | Unadjusted late rate (95% interval) | Adjusted late rate |
|---|---:|---:|---:|---:|
| RJ | 12,144 | 1,484 | 12.22% (11.65 to 12.81) | 12.03% |
| SP | 39,840 | 1,812 | 4.55% (4.35 to 4.76) | 4.57% |

- **Adjusted risk difference:** +7.46 points (5.88 to 9.13). **Odds ratio:** 2.99 (2.45 to 3.66).
- **Practical significance:** the whole interval is above the 2-point criterion, with 1,484 late RJ orders in the sample.
- **Limited overlap:** only 7.8% of RJ orders have an in-state seller, compared with 76.0% of SP orders. Their distances also differ, as the table below shows. The model therefore relies on its assumptions where RJ and SP orders look little alike. **The planned check restricted to SP sellers and overlapping distance bands is required before this finding can be treated as robust.**

| Distance | RJ orders | SP orders |
|---|---:|---:|
| 0–100 km | 807 | 15,763 |
| 100–300 km | 909 | 9,702 |
| 300–600 km | 7,297 | 11,765 |
| 600–1,000 km | 2,486 | 2,121 |
| 1,000–2,000 km | 590 | 235 |
| 2,000+ km | 55 | 254 |

**Plain reading:** RJ customers' orders are more often late than SP customers', even after accounting for the measured differences. The data doesn't show why.

### A2. Late delivery and low ratings

| Group | Reviewed orders | Low ratings | Unadjusted low-rating share (95% interval) | Adjusted share | Mean score |
|---|---:|---:|---:|---:|---:|
| Late | 6,381 | 3,983 | 62.42% (61.22 to 63.60) | 60.34% | 2.27 |
| On time | 89,443 | 8,289 | 9.27% (9.08 to 9.46) | 9.30% | 4.29 |

| Score | 1 star | 2 stars | 3 stars | 4 stars | 5 stars |
|---|---:|---:|---:|---:|---:|
| Late | 53.77% | 8.65% | 10.88% | 10.17% | 16.53% |
| On time | 6.62% | 2.65% | 8.07% | 20.39% | 62.27% |

- **Adjusted risk difference:** +51.04 points (49.58 to 52.28). **Odds ratio:** 17.00 (15.67 to 18.45).
- **Adjusted mean score difference:** −1.98 (−2.03 to −1.93), which exceeds the 0.25-point criterion.
- **Practical significance:** the whole interval is far above the 5-point criterion.
- **Possible answer-timing bias:** the feasibility scan suggested that many reviews on late orders were answered before the order arrived. This result can therefore mix two situations: customers still waiting for an order, and customers rating an order received late. It shouldn't be read as the effect of a late delivery on how customers rate a received order. The split by answer timing is B3, which hasn't run.
- **Selection:** results cover reviewed orders only, and undelivered orders are excluded.

**Plain reading:** lateness and low ratings go together strongly, but this figure may overstate the link for customers who had already received their order.

### A3. Longer delays and low ratings

| Days late | Reviewed orders | Low ratings | Unadjusted share (95% interval) | Adjusted share |
|---|---:|---:|---:|---:|
| 1–3 | 1,852 | 595 | 32.13% (30.04 to 34.29) | 33.83% |
| 4–7 | 1,748 | 1,183 | 67.68% (65.45 to 69.83) | 68.54% |
| 8–14 | 1,446 | 1,159 | 80.15% (78.02 to 82.13) | 79.73% |
| 15+ | 1,335 | 1,046 | 78.35% (76.06 to 80.48) | 75.93% |

| Comparison | Adjusted difference | 95% interval | Meets the 5-point criterion? |
|---|---:|---:|---|
| 4–7 against 1–3 days | +34.72 points | 31.77 to 37.83 | Yes |
| 8–14 against 4–7 days | +11.18 points | 8.19 to 14.21 | Yes |
| 15+ against 8–14 days | −3.80 points | −6.94 to −0.26 | **No: opposite direction** |
| 15+ against 1–3 days | +42.10 points | 39.04 to 45.22 | Overall comparison |

- **Trend across ordered bands:** odds ratio 2.05 per band, Holm p 2.79e-121.
- **Non-monotonic pattern:** low ratings rise sharply through 8–14 days, then don't continue rising. The prediction of progressively worse ratings fails at the final step, so the label is **Inconclusive** under the strict criterion that every adjacent step must meet it. The clear overall rise isn't in doubt, but the "keeps getting worse" pattern isn't shown.
- **Interpretation limit:** the longest delays may have more reviews answered before arrival, so this pattern may partly reflect answer timing. B4 will look at this.
- **Selection:** this analysis uses late orders with a review only.

**Plain reading:** the first few days of lateness are associated with the largest jump in low ratings, and the share then levels off at around 76–80%.

### A4. Distance and late delivery

| Distance | Orders | Late orders | Unadjusted rate (95% interval) | Adjusted rate |
|---|---:|---:|---:|---:|
| 0–100 km | 17,694 | 797 | 4.50% (4.21 to 4.82) | 6.10% |
| 100–300 km | 13,155 | 690 | 5.25% (4.88 to 5.64) | 6.59% |
| 300–600 km | 31,032 | 2,122 | 6.84% (6.56 to 7.12) | 6.81% |
| 600–1,000 km | 17,664 | 1,271 | 7.20% (6.82 to 7.59) | 6.69% |
| 1,000–2,000 km | 9,608 | 923 | 9.61% (9.03 to 10.21) | 7.06% |
| 2,000+ km | 5,571 | 673 | 12.08% (11.25 to 12.96) | 8.62% |

- **Fixed comparison, 600–1,000 km against 0–100 km:** +0.59 points (−0.49 to 1.50), odds ratio 1.11 (0.93 to 1.33).
- **Without customer state in the model:** +2.47 points, odds ratio 1.60 (1.39 to 1.84). The plan required this to be reported. It has no bootstrap interval.
- **Practical significance:** the whole adjusted interval is below the 2-point criterion.
- **Interpretation limit:** state and distance overlap heavily, so this doesn't show that distance is irrelevant. It shows that this comparison adds little once state is known. The 2,000+ km band is higher, but it isn't the fixed comparison.

**Plain reading:** in this comparison, distance adds little once the customer's state is taken into account.

### A5. Freight cost and late delivery

| Freight quartile | Freight range (R$) | Orders | Late orders | Unadjusted rate (95% interval) | Adjusted rate |
|---|---:|---:|---:|---:|---:|
| Lowest | 0.00–13.75 | 23,722 | 1,043 | 4.40% (4.14 to 4.67) | 5.20% |
| Second | 13.75–17.06 | 23,736 | 1,654 | 6.97% (6.65 to 7.30) | 7.17% |
| Third | 17.06–23.64 | 23,604 | 1,840 | 7.80% (7.46 to 8.14) | 7.33% |
| Highest | 23.64–1,794.96 | 23,662 | 1,939 | 8.19% (7.85 to 8.55) | 7.36% |

- **Adjusted risk difference, highest against lowest:** +2.16 points (1.27 to 3.01). **Odds ratio:** 1.47 (1.26 to 1.72).
- **Practical significance:** the estimate is just above the 2-point criterion, and the interval straddles it. **Flagged for a higher-replication check.**
- **Interpretation limits:** nearly all of the rise is between the lowest and second quartiles. The fixed A5 model doesn't adjust for customer state, so freight may partly reflect destination. Freight also reflects weight, size and route, so this doesn't show that freight itself affects lateness.
- **Planned exploratory check:** a version adding customer state will run at step 7. It's labelled exploratory, and it doesn't change this result or its definition.

**Plain reading:** the lowest-freight orders are less often late, but higher freight beyond that shows little further change.

### A6. Seller concentration

| Measure | Result |
|---|---:|
| Sellers with at least 100 orders | 201 (59.43% of single-seller orders) |
| Orders and late orders among them | 56,579 and 3,909 |
| Top 10% by late orders | 21 sellers |
| Their share of late orders | 41.98% |
| Their share of orders | 35.01% |
| Gap | +6.97 points (2.48 to 10.66) |
| Gap expected with no real seller differences | 2.41 points (97.5th percentile 3.98) |
| Gap ranking on one half and measuring on the other | 6.00 points (range 4.39 to 7.61) |
| Sellers above the funnel limit | 12 |
| Sellers below the funnel limit | 4 |
| Sellers outside the limits expected by chance | 0.4 |

- **Test:** one-sided simulation with 5,000 draws, with a smallest possible p-value near 0.0002. Raw p 0.0002, Holm p 0.0006.
- **Practical significance:** the estimate is below the 10-point criterion, and the interval straddles it. **Flagged for a higher-replication check.**
- **Selection-related uncertainty:** ranking sellers by late orders in the same data flatters the top group, and even equal sellers would show a gap of about 2.41 points. The bootstrap re-ranks sellers in each replicate, so its interval can also be inflated. The split-half figure is the fairer guide to the size of the gap.
- **Interpretation limit:** a seller's result can reflect routes and customers served, not only the seller's own performance.

**Plain reading:** seller differences exist, and 12 sellers perform clearly worse than expected for their months. But concentration is below the screening criterion, so targeting a few sellers isn't shown to be a broad solution.

### A7. Category differences

- **Orders:** 83,514 single-seller orders with a distance, in 21 categories with at least 1,000 orders. Orders with an `unknown` category are excluded.
- **Adjusted spread:** 3.69 points (2.88 to 6.90), from 4.86% (luggage accessories) to 8.55% (baby).
- **Unadjusted spread:** 4.03 points. **Cramér's V:** 0.031.
- **Test:** clustered joint Wald test across 20 category terms, raw p 0.0100, Holm p 0.0201.
- **Practical significance:** the estimate is below the 5-point criterion, and the interval straddles it. **Flagged for a higher-replication check.**
- **Selection-related uncertainty:** the spread picks the highest and lowest categories afresh in each replicate, which pushes the replicates upward. That's why the estimate sits near the low end of its interval. The upper limit should be read with care.

| Category | Orders | Unadjusted late rate | Adjusted late rate |
|---|---:|---:|---:|
| Highest adjusted: baby | 2,709 | 8.23% | 8.55% |
| Largest: bed_bath_table | 8,883 | 7.63% | 7.99% |
| Lowest adjusted: luggage_accessories | 1,001 | 4.20% | 4.86% |

**Plain reading:** categories differ only modestly, so category isn't a strong lens for prioritising delivery improvements.

## Model diagnostics

Bootstrap: 500 seller-level replicates, seed 20261105, with no failed replicates in any model. A6 uses its own seller-level resampling.

| Model | Orders | Events | Terms | Events per term | Sellers | Converged | Condition number | Largest standard error |
|---|---:|---:|---:|---:|---:|---|---:|---:|
| A1 | 51,984 | 3,296 | 30 | 109.9 | 2,586 | Yes | 37.5 | 0.54 |
| A2 | 95,824 | 12,272 | 54 | 227.3 | 2,954 | Yes | 36.9 | 0.25 |
| A3 | 6,381 | 3,983 | 54 | 73.8 | 1,254 | Yes | 35.1 | 0.72 |
| A4 | 94,724 | 6,476 | 40 | 161.9 | 2,941 | Yes | 34.9 | 0.25 |
| A5 | 94,724 | 6,476 | 31 | 208.9 | 2,941 | Yes | 36.8 | 0.25 |
| A7 | 83,514 | 5,760 | 57 | 101.1 | 2,558 | Yes | 12.6 | 0.26 |

- **KPIs:** all eight locked KPIs reproduced from the analysis table, and separately from the raw CSVs.
- **Solver check:** coefficients agree with `statsmodels` to about 1e-10.
- **Reproducibility:** a second run with the same seed matched the first on all compared results.
- **Related predictors:** highest variance inflation 2.44 (log distance), with a correlation of −0.74 between log distance and same-state seller.
- **Merged sparse months:** early periods only, as planned. No state or category level was merged.
- **Non-events per term:** lowest in A3, at 44.4.
- **Exclusions from distance-based models:** 1,275 multi-seller orders and 471 single-seller orders with no ZIP position.

| Model | Months merged |
|---|---|
| A1 | Sept 2016, Oct 2016 and Jan 2017 |
| A2 | Sept–Oct 2016; Dec 2016–Jan 2017 |
| A3 | Sept 2016, Oct 2016, Jan 2017 and Feb 2017 |
| A4, A5, A7 | Sept 2016 to Jan 2017 |

## General limitations

- **Observational data:** there's no randomisation, and no carrier, route, weather, stock or customer-service data. Unmeasured differences may explain any association.
- **Previewed data:** unadjusted results were seen before this plan was written, and the screening criteria were set after that preview.
- **Dependence:** intervals account for seller clustering, but not for dependence within customers, regions or time, so they may be somewhat narrow.
- **Test types:** A6 uses a one-sided simulation, and the other tests use two-sided Wald tests.
- **Implementation of A3's criterion:** the plan set 5 points "between adjacent bands" without saying how to combine them. The analysis code applied the strict reading, requiring every adjacent step to meet it, before results were seen. This was documented only after the results were known, and it's kept unchanged.

## Exploratory findings (Class B)

**Status: exploratory, observational and not yet tested for robustness.** These questions were shaped by looking at the data. They can suggest what to investigate or test, but they don't confirm anything. They don't change any Class A estimate, criterion or label above. P-values aren't corrected for multiple comparisons.

Labels here are "pattern observed" or "not observed", never "confirmed". All intervals come from 500 seller-level bootstrap replicates, seed 20261105, unless stated otherwise. Reproduced by `python/analysis/class_b.py`.

### B3. Answer timing and low ratings

| Group | Reviewed orders | Low ratings | Unadjusted share (95% interval) | Adjusted share | Mean score |
|---|---:|---:|---:|---:|---:|
| On time | 89,443 | 8,289 | 9.27% (9.08 to 9.46) | 9.28% | 4.29 |
| Late, answered before arrival | 4,473 | 3,612 | 80.75% (79.57 to 81.88) | 79.36% | 1.65 |
| Late, answered after arrival | 1,908 | 371 | 19.44% (17.73 to 21.28) | 19.22% | 3.72 |

| Group | 1 star | 2 stars | 3 stars | 4 stars | 5 stars |
|---|---:|---:|---:|---:|---:|
| On time | 6.62% | 2.65% | 8.07% | 20.39% | 62.27% |
| Late, answered before arrival | 70.94% | 9.81% | 8.61% | 4.36% | 6.28% |
| Late, answered after arrival | 13.52% | 5.92% | 16.19% | 23.79% | 40.57% |

| Compared with on-time orders | Adjusted difference | 95% interval | Odds ratio (95% interval) | Mean score difference (95% interval) | Exploratory label |
|---|---:|---:|---:|---:|---|
| Late, answered before arrival | +70.07 points | 68.49 to 71.45 | 44.18 (39.72 to 49.15) | −2.60 (−2.65 to −2.56) | Pattern observed |
| Late, answered after arrival | +9.94 points | 8.26 to 11.62 | 2.43 (2.18 to 2.71) | −0.56 (−0.62 to −0.50) | Pattern observed |

- **Answered before arrival:** 70.10% of reviews on late orders. Only 180 on-time reviews were answered before arrival.
- **What this means for A2:** A2's +51.04 points combines these two groups. The A2 label stands, but it shouldn't be read as the effect of lateness on how customers rate a received order. For reviews answered after arrival, the adjusted difference is about 10 points.
- **Limits of answer timing:** these groups are self-selected, so customers who answered early may differ from those who didn't. Most after-arrival reviews on late orders come from short delays, so that estimate mostly describes short delays. The label depends on recorded delivery timestamps, and the data doesn't show what customers knew or expected when they answered.

**Plain reading:** most low ratings on late orders came from customers who hadn't yet received their order. Customers who answered after arrival still rated late orders worse than on-time ones, but far less so.

### B4. Delay length within each answer-timing group

| Days late | Reviews before arrival | Reviews after arrival | Share before arrival | Low share, before arrival (95% interval) | Low share, after arrival (95% interval) |
|---:|---:|---:|---:|---:|---:|
| 1–3 | 416 | 1,436 | 22.46% | 78.85% (74.67 to 82.50) | 18.59% (16.67 to 20.69) |
| 4–7 | 1,352 | 396 | 77.35% | 81.51% (79.35 to 83.49) | 20.45% (16.77 to 24.70) |
| 8–14 | 1,389 | 57 | 96.06% | 82.36% (80.27 to 84.28) | 26.32% (16.65 to 38.98) |
| 15+ | 1,316 | 19 | 98.58% | 78.88% (76.59 to 81.00) | Not reported: under 30 reviews |

| Adjusted comparison | Before arrival | 95% interval | After arrival | 95% interval |
|---|---:|---:|---:|---:|
| 4–7 against 1–3 days | +3.02 points | −1.28 to 7.75 | +1.59 points | −2.81 to 6.13 |
| 8–14 against 4–7 days | −0.16 points | −2.92 to 2.42 | +3.25 points | −7.26 to 14.45 |
| 15+ against 8–14 days | −5.27 points | −8.84 to −1.91 | Not estimated | Too few reviews |

- **Late orders answered after arrival, 8 or more days late:** 76 reviews, 30.26% (21.09 to 41.33). This is too few to judge long delays.
- **What this means for A3:** the share answered before arrival rises sharply with delay. Within each timing group, no step shows a clear rise of 5 points or more. So A3's rise is consistent with a change in who answered before arrival, rather than a steady worsening within either group. The A3 label and results don't change. This can't separate the two explanations, because timing and delay length are closely linked.
- **Adjustment sets differ:** the before-arrival model uses the A2 set without the multi-seller term, and the after-arrival model drops category because it has too few events. They shouldn't be compared as if they were the same model.
- **Model correction:** see "Exploratory model checks" below.

**Plain reading:** once answer timing is separated out, delay length shows little clear change within either group, and the data is too thin to judge long delays after arrival.

### B1. Late orders in peak months

**Limit of data-selected months:** the rule (at least 100 orders and a late rate of 10% or more) was written after seeing the data, and it selects Nov 2017, Feb 2018 and Mar 2018. Because these months were chosen for their high late rates, some concentration is guaranteed. The size of the concentration is the informative part, not its existence.

| Group | Orders | Late orders | Late rate | Share of orders | Share of late orders |
|---|---:|---:|---:|---:|---:|
| Peak months | 20,846 | 3,158 | 15.15% | 21.61% | 48.33% |
| Other months | 75,624 | 3,376 | 4.46% | 78.39% | 51.67% |

- **Late-rate difference:** +10.68 points (9.63 to 11.73). **Exploratory label:** Pattern observed.
- **Late share minus order share:** +26.72 points (24.57 to 28.95).

| Purchase month | Orders | Late orders | Late rate (95% interval) | Share of all late orders |
|---|---:|---:|---:|---:|
| 2016-10 | 265 | 2 | 0.75% (0.21 to 2.71) | 0.03% |
| 2017-01 | 750 | 22 | 2.93% (1.94 to 4.40) | 0.34% |
| 2017-02 | 1,653 | 49 | 2.96% (2.25 to 3.90) | 0.75% |
| 2017-03 | 2,546 | 116 | 4.56% (3.81 to 5.44) | 1.78% |
| 2017-04 | 2,303 | 151 | 6.56% (5.62 to 7.64) | 2.31% |
| 2017-05 | 3,545 | 106 | 2.99% (2.48 to 3.60) | 1.62% |
| 2017-06 | 3,135 | 95 | 3.03% (2.49 to 3.69) | 1.45% |
| 2017-07 | 3,872 | 108 | 2.79% (2.32 to 3.36) | 1.65% |
| 2017-08 | 4,193 | 122 | 2.91% (2.44 to 3.46) | 1.87% |
| 2017-09 | 4,150 | 182 | 4.39% (3.80 to 5.05) | 2.79% |
| 2017-10 | 4,478 | 187 | 4.18% (3.63 to 4.80) | 2.86% |
| 2017-11 (peak) | 7,288 | 904 | 12.40% (11.67 to 13.18) | 13.84% |
| 2017-12 | 5,513 | 411 | 7.46% (6.79 to 8.18) | 6.29% |
| 2018-01 | 7,069 | 403 | 5.70% (5.18 to 6.27) | 6.17% |
| 2018-02 (peak) | 6,555 | 926 | 14.13% (13.30 to 14.99) | 14.17% |
| 2018-03 (peak) | 7,003 | 1,328 | 18.96% (18.06 to 19.90) | 20.32% |
| 2018-04 | 6,798 | 306 | 4.50% (4.03 to 5.02) | 4.68% |
| 2018-05 | 6,749 | 443 | 6.56% (6.00 to 7.18) | 6.78% |
| 2018-06 | 6,096 | 71 | 1.16% (0.92 to 1.47) | 1.09% |
| 2018-07 | 6,156 | 208 | 3.38% (2.96 to 3.86) | 3.18% |
| 2018-08 | 6,351 | 393 | 6.19% (5.62 to 6.81) | 6.01% |

Sept and Dec 2016 have one order each and aren't shown.

**Plain reading:** nearly half of all late orders come from three months. The data doesn't show why.

### B2. RJ's gap in peak and other months

| Customer state | Peak months: orders | Peak months: late rate (95% interval) | Other months: orders | Other months: late rate (95% interval) |
|---|---:|---:|---:|---:|
| RJ | 2,715 | 31.49% (29.77 to 33.26) | 9,429 | 6.67% (6.18 to 7.19) |
| SP | 8,381 | 8.03% (7.47 to 8.63) | 31,459 | 3.62% (3.42 to 3.83) |

| Adjusted RJ–SP comparison | Difference | 95% interval |
|---|---:|---:|
| Peak months | +23.46 points | 19.64 to 27.50 |
| Other months | +3.04 points | 2.09 to 4.19 |
| Difference between the two gaps | +20.42 points | 17.08 to 24.03 |

- **Exploratory label:** Pattern observed. **Interaction odds ratio:** 2.78 (2.29 to 3.38).
- **Exposure:** 855 late RJ orders in this sample fall in peak months, which is 57.61% of RJ's late orders here.
- **Limits:** the peak months were selected from the data, and A1's overlap limits apply here too.

| SP sellers delivering to | Peak months: orders | Peak months: late rate (95% interval) | Other months: orders | Other months: late rate (95% interval) |
|---|---:|---:|---:|---:|
| RJ | 1,843 | 37.66% (35.47 to 39.89) | 6,205 | 7.30% (6.68 to 7.97) |
| ES | 329 | 29.18% (24.53 to 34.31) | 1,115 | 7.53% (6.13 to 9.23) |
| BA | 510 | 24.51% (20.98 to 28.42) | 1,768 | 9.73% (8.43 to 11.20) |
| MG | 1,663 | 14.67% (13.05 to 16.45) | 5,663 | 2.60% (2.21 to 3.04) |
| PR | 670 | 12.99% (10.65 to 15.74) | 2,407 | 2.12% (1.62 to 2.78) |
| SP | 6,321 | 8.08% (7.44 to 8.78) | 23,992 | 3.81% (3.57 to 4.06) |

**Plain reading:** the RJ gap is present in both periods, but it's much larger in the peak months. The route table is unadjusted, and the data doesn't explain the difference.

### B5. Seller handover and the later delivery stage

Stage timing is split by the carrier date of 25 April 2018, because carrier timestamps change abruptly on that date. **The two periods shouldn't be compared directly on stage timing.** Only single-seller orders with a distance and valid date sequences are included.

| Period | Handover | Orders | Late orders | Late rate (95% interval) | Share of period's late orders | Share of period's orders | Median handover days | Median handover-to-delivery days |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Before 25 April 2018 | Late | 6,478 | 1,337 | 20.64% (19.67 to 21.64) | 25.34% | 9.53% | 7.88 | 8.06 |
| Before 25 April 2018 | On time | 61,505 | 3,939 | 6.40% (6.21 to 6.60) | 74.66% | 90.47% | 2.18 | 7.94 |
| From 25 April 2018 | Late | 2,149 | 470 | 21.87% (20.17 to 23.67) | 39.26% | 8.09% | 6.91 | 5.47 |
| From 25 April 2018 | On time | 24,426 | 727 | 2.98% (2.77 to 3.20) | 60.74% | 91.91% | 1.70 | 5.48 |

| Period | Orders | Late orders | Adjusted late rate: late handover | Adjusted late rate: on-time handover | Adjusted difference | 95% interval | Odds ratio (95% interval) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Before 25 April 2018 | 67,983 | 5,276 | 19.83% | 6.44% | +13.39 points | 11.88 to 14.97 | 4.17 (3.67 to 4.75) |
| From 25 April 2018 | 26,575 | 1,197 | 21.12% | 2.99% | +18.13 points | 15.25 to 20.86 | 9.63 (7.86 to 11.81) |

- **Before 25 April 2018:** pattern observed. 1,337 late orders in the late-handover group.
- **From 25 April 2018:** the difference is large, but this period misses the 500-late-order part of the screening criterion, with 470 late orders in that group.
- **Limits:** this describes which stage is linked to lateness. It doesn't show who caused a delay, and nothing here is attributed to carriers. A late handover also leaves less of the promised time for later stages, so some link is expected from how lateness is measured. The cause of the 25 April change is unknown.

**Plain reading:** orders handed over late are far more often late, but most late orders had an on-time handover.

### B6. Multi-item orders and low ratings

| Group | Reviewed orders | Low ratings | Low share (95% interval) |
|---|---:|---:|---:|
| Single item | 86,296 | 9,724 | 11.27% (11.06 to 11.48) |
| Multi-item | 9,528 | 2,548 | 26.74% (25.86 to 27.64) |
| Single item, on time | 80,407 | 6,067 | 7.55% (7.36 to 7.73) |
| Multi-item, on time | 9,036 | 2,222 | 24.59% (23.71 to 25.49) |
| Single item, late | 5,889 | 3,657 | 62.10% (60.85 to 63.33) |
| Multi-item, late | 492 | 326 | 66.26% (61.97 to 70.30) |
| 2 items | 7,319 | 1,859 | 25.40% (24.42 to 26.41) |
| 3+ items | 2,209 | 689 | 31.19% (29.29 to 33.15) |

| Adjusted comparison, multi-item against single item | Difference | 95% interval |
|---|---:|---:|
| All reviewed orders | +12.67 points | 11.26 to 13.76 |
| On-time orders | +13.03 points | 11.73 to 14.10 |
| Late orders | +6.83 points | 3.13 to 10.54 |

- **Exploratory label:** Pattern observed. **Odds ratio:** 3.04 (2.78 to 3.33). **Mean score difference:** −0.48 (−0.52 to −0.43).
- **Overlap:** 13.23% of multi-item orders have several sellers. Median order value is R$ 135.00 for multi-item orders and R$ 79.90 for single-item orders. The correlation between item count and logged order value is 0.18.
- **Limits:** the data has no shipment-level detail, so reasons such as split deliveries can't be tested here. Item count is related to sellers and order value, and the model adjusts for them only as measured.

**Plain reading:** multi-item orders get more low ratings, even when they arrive on time. The data doesn't explain why.

### B7. Where low ratings fall

Total low ratings: 12,272, from 95,824 reviewed orders.

| Group | Reviewed orders | Low ratings | Share of all low ratings (95% interval) | Low share within group |
|---|---:|---:|---:|---:|
| On time, single item | 80,407 | 6,067 | 49.44% (47.25 to 51.63) | 7.55% |
| Late, single item | 5,889 | 3,657 | 29.80% (28.23 to 31.43) | 62.10% |
| On time, multi-item | 9,036 | 2,222 | 18.11% (16.32 to 19.71) | 24.59% |
| Late, multi-item | 492 | 326 | 2.66% (2.31 to 3.00) | 66.26% |

All on-time orders together hold 8,289 low ratings, or 67.54% (65.86 to 69.20). This is a share of counts, so it reflects how many on-time orders there are. A late order is still far more likely to get a low rating.

**Plain reading:** most low ratings are on orders that arrived on time, so delivery timing alone doesn't account for them.

## Descriptive context (Class C)

**Measurements only, with no hypothesis tests.** These cover the 96,470 delivered orders with a delivery date. Sales in this base total R$ 13,220,248.93, slightly below the R$ 13,221,498.11 KPI, which also includes the 8 delivered orders with no delivery date. Reproduced by `python/analysis/descriptive.py`.

### Sales growth, January to August

| Measure | 2017 | 2018 | Change |
|---|---:|---:|---:|
| Sales | R$ 2,993,277.13 | R$ 7,217,172.24 | +141.1% |
| Orders | 21,997 | 52,777 | +139.9% |
| Average order value | R$ 136.08 | R$ 136.75 | +0.49% |

Of the R$ 4,223,895.11 change, order volume accounts for R$ 4,188,437.97 (99.2%) and order value for R$ 35,457.14. This uses matching months only.

### State priority view

Exposure figures only, with no estimated savings. Ranked by late orders.

| State | Orders | Share of orders | Late orders | Late rate | Share of late orders | Low ratings | Share of low ratings | Sales | Sales on late orders |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| SP | 40,494 | 41.98% | 1,820 | 4.49% | 27.85% | 4,303 | 35.06% | R$ 5,066,562.98 | R$ 269,383.42 |
| RJ | 12,350 | 12.80% | 1,495 | 12.11% | 22.88% | 2,238 | 18.24% | R$ 1,759,651.13 | R$ 215,415.46 |
| MG | 11,354 | 11.77% | 519 | 4.57% | 7.94% | 1,326 | 10.81% | R$ 1,552,481.83 | R$ 75,837.49 |
| BA | 3,256 | 3.38% | 396 | 12.16% | 6.06% | 549 | 4.47% | R$ 493,584.14 | R$ 62,058.74 |
| RS | 5,344 | 5.54% | 325 | 6.08% | 4.97% | 635 | 5.17% | R$ 728,718.47 | R$ 43,968.03 |
| SC | 3,546 | 3.68% | 291 | 8.21% | 4.45% | 457 | 3.72% | R$ 507,012.13 | R$ 38,103.95 |
| ES | 1,995 | 2.07% | 214 | 10.73% | 3.28% | 272 | 2.22% | R$ 268,643.45 | R$ 34,907.68 |
| PR | 4,923 | 5.10% | 199 | 4.04% | 3.05% | 533 | 4.34% | R$ 666,063.51 | R$ 29,504.05 |

SP and RJ together hold 54.78% of orders and 50.73% of late orders. Across all states, late orders total 6,534 and hold 7.46% of sales (R$ 985,924.34).

### Largest categories by sales

| Category | Orders | Sales | Share of sales | Late orders | Late rate |
|---|---:|---:|---:|---:|---:|
| health_beauty | 8,613 | R$ 1,233,813.10 | 9.33% | 649 | 7.54% |
| watches_gifts | 5,476 | R$ 1,166,874.18 | 8.83% | 406 | 7.41% |
| bed_bath_table | 9,184 | R$ 1,024,243.76 | 7.75% | 687 | 7.48% |
| sports_leisure | 7,492 | R$ 954,346.89 | 7.22% | 494 | 6.59% |
| computers_accessories | 6,511 | R$ 888,482.99 | 6.72% | 417 | 6.40% |

### Promised and actual delivery

The median promise is 24 days, and the median actual delivery is 10 days. 78.93% of orders arrive 7 or more days early. The median promise also falls in late 2018, so lateness isn't measured against a stable standard.

| Purchase month | Orders | Sales | Average order value | Median promised days | Median actual days |
|---|---:|---:|---:|---:|---:|
| 2017-11 | 7,288 | R$ 987,648.07 | R$ 135.52 | 23 | 13 |
| 2017-12 | 5,513 | R$ 726,033.19 | R$ 131.69 | 28 | 13 |
| 2018-01 | 7,069 | R$ 924,645.00 | R$ 130.80 | 26 | 12 |
| 2018-02 | 6,555 | R$ 826,437.13 | R$ 126.08 | 25 | 14 |
| 2018-03 | 7,003 | R$ 953,356.25 | R$ 136.14 | 22 | 13 |
| 2018-04 | 6,798 | R$ 973,534.09 | R$ 143.21 | 24 | 9 |
| 2018-05 | 6,749 | R$ 977,544.69 | R$ 144.84 | 22 | 9 |
| 2018-06 | 6,096 | R$ 855,591.97 | R$ 140.35 | 28 | 8 |
| 2018-07 | 6,156 | R$ 867,486.47 | R$ 140.92 | 20 | 7 |
| 2018-08 | 6,351 | R$ 838,576.64 | R$ 132.04 | 14 | 7 |

**Seasonality:** there's at most one complete year of data, so no seasonal claim is made.

## Exploratory model checks

| Model | Orders | Events | Terms | Events per term | Non-events per term | Iterations | Condition number | Largest standard error | Failed replicates |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| B3 | 95,824 | 12,272 | 55 | 223.1 | 1519.1 | 6 | 36.9 | 0.26 | 0 of 500 |
| B4 before arrival | 4,473 | 3,612 | 52 | 69.5 | 16.6 | 6 | 39.1 | 0.39 | 0 of 500 |
| B4 after arrival | 1,889 | 363 | 29 | 12.5 | 52.6 | 6 | 29.3 | 0.75 | 0 of 500 |
| B2 | 51,984 | 3,296 | 31 | 106.3 | 1570.6 | 9 | 37.5 | 0.53 | 0 of 500 |
| B5 before 25 Apr 2018 | 67,983 | 5,276 | 37 | 142.6 | 1694.8 | 8 | 33.4 | 0.25 | 0 of 500 |
| B5 from 25 Apr 2018 | 26,575 | 1,197 | 26 | 46.0 | 976.1 | 8 | 30.5 | 0.42 | 0 of 500 |
| B6 | 95,824 | 12,272 | 54 | 227.3 | 1547.3 | 6 | 36.9 | 0.26 | 0 of 500 |
| B6 interaction | 95,824 | 12,272 | 55 | 223.1 | 1519.1 | 6 | 36.9 | 0.26 | 0 of 500 |

- **Separation corrected (B4, before arrival).** All 3 multi-seller orders in this group have low ratings, so that term can't be estimated: its coefficient reached 17.31 after 23 iterations. The term was removed from this model only, because it carries no usable information there and left the model unstable. After the correction, the model needs 6 iterations, and its largest coefficient is 1.74. Band estimates moved by at most 0.03 points. Every other result was identical between runs.
- **Thin term kept (B4, after arrival).** The multi-seller term rests on 9 orders, with 6 low ratings and 3 others. Its coefficient is stable, so it's kept and reported.
- **Sparse level remains (B4, before arrival).** The 3+ items level has 69 orders and 8 non-low ratings, below the rule of 10. The merging step relabels it as "other" without combining it, because item count has no other group to merge with. Merging it with the 2-item level changes the band differences by at most 0.04 points, so it has no practical effect and the approved model is kept.
- **Adjustment differences:** B6 leaves out item count, because that's its exposure. B4's two models use different adjustment sets, as noted above. B1, B7 and B4's unadjusted differences use no regression.
- **Merged levels:** sparse early months in all models. In B4, state levels CE, DF and PE are merged after arrival, and DF before arrival.
- **Reproducibility:** results come directly from the saved scripts, with a fixed seed.

## Exploratory limitations

- **Observational results:** there's no randomisation, and no carrier, route, weather, stock or customer-service data. Associations here may reflect unmeasured differences.
- **Review answer timing:** answer timing is self-selected and closely linked to delay length. Customers who answered before arrival may differ from those who answered after, and the groups can't be treated as comparable.
- **Data-selected peak months:** the months were chosen using the outcome, so concentration is partly built in, and the rule may not apply to other periods.
- **Multiple comparisons:** many comparisons were made, without correction, so some patterns may arise by chance.
- **Robustness:** none of these findings has yet had sensitivity testing.

## Next steps

1. Run the sensitivity analyses, including the SP-seller check for A1 and the labelled A5 check with customer state.
2. Run higher-replication bootstraps for A5, A6 and A7.
3. Assign robustness labels and cross-check key results against SQL and the source CSVs.
4. Review findings before developing recommendations.
