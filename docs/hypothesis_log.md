# Hypothesis Log

Results recorded under the plan in [analysis_plan.md](analysis_plan.md) and [methodology.md](methodology.md). Results are reproduced by `python/analysis/build_dataset.py` and `python/analysis/class_a.py`.

## Status

| Item | Status |
|---|---|
| Class A statistical evidence | Complete, and **provisional** |
| Robustness (16 sensitivity analyses) | **Not yet assessed** |
| Class B exploratory questions | Not yet run |
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

## Next steps

1. Run Class B exploratory questions, including answer timing (B3 and B4).
2. Run the descriptive context.
3. Run the sensitivity analyses, including the SP-seller check for A1 and the labelled A5 check with customer state.
4. Run higher-replication bootstraps for A5, A6 and A7.
5. Assign robustness labels and cross-check key results against SQL and the source CSVs.
