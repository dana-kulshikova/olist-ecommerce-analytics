# Independent Technical Audit (Step 8)

**Status: reviewed. Corrections were approved and are recorded in the remediation addendum and follow-up below.** Audited commit: `e06158e` on `case-study-upgrade`. No existing code, dataset or document was changed. Issues are reported here and not corrected. All results remain observational associations.

*Everything above the [remediation addendum](#remediation-addendum-2026-11-05) is the original audit result, including its counts: 39 PASS, 14 FAIL and 6 NEEDS INVESTIGATION. The statement that nothing was changed describes the audit itself. Later corrections are recorded only in the addendum.*

## Summary

- **The numbers hold.** All eight KPIs and every point estimate compared were reproduced from the raw CSV files by separately written code. The largest difference across 60 compared estimates was 0.004, consistent with rounding of the stored values.
- **The data table holds.** 23 derived fields match on all 96,470 base orders. The only timestamp differences are the known 60-minute shifts, and they change no answer-timing group.
- **Evidence labels hold.** A1–A7 labels re-derived from the independent figures match the stored labels.
- **No FAIL affects an estimate, interval or evidence label.** The FAIL items are documentation, wording or presentation errors. The largest factual one is a stated count of 288 long deliveries, where the code excludes 298.
- **The main open question is wording.** "Robustly below the practical-importance criterion" holds for A6 and A7 point estimates, but their intervals still reach the criterion. A5's intervals straddling its criterion was treated as a reason for caution, so the two are handled differently.

## How independent these checks are

| Code | Type | What it means |
|---|---|---|
| **IND** | Independent recomputation | Separate code reading only the raw CSVs. It imports nothing from `python/analysis/`, reads no exports or stored results, and doesn't use pandas or statsmodels. It has its own solver, clustered covariance and row-resampling bootstrap, and a different seed |
| **REP** | Reproduction | The project's own SQL, run on a throwaway PostgreSQL cluster loaded from the raw CSVs. This tests the SQL on clean data, and isn't a separate calculation |
| **CMP** | Comparison | Stored outputs or documents compared with each other or with IND results |
| **INS** | Inspection | Reading code or documents. Nothing was recalculated |

**Limits on independence:**

- **Same author.** The same AI assistant wrote the project code and this audit, in the same project. The independence is in the implementation, not the reviewer. A misreading shared by the plan and both implementations would not be detected. A review by another person would add something this audit can't.
- **Shared specifications.** Model definitions were taken from `analysis_plan.md`, and the sensitivity scenarios were re-implemented after reading the project code.
- **Shared library.** The IND code uses numpy, plus scipy for one chi-square tail probability (A7).

## Limitations of the audit

| Limitation | Effect |
|---|---|
| **The live database couldn't be queried.** No credentials were available or sought | Stored exports were tested indirectly: a clean load of the raw CSVs reproduces them, apart from explained differences (T6) |
| **Power BI wasn't run.** DAX was read, not executed | Measures are checked by inspection only (T10) |
| **Not everything was recomputed.** Selection was risk-prioritised | See "Not independently reproduced" below |
| **Some follow-up scripts are outside the repository.** The throwaway load, three follow-ups and the fingerprint checks ran from the scratchpad | This is the same weakness reported in C7, and it can be fixed the same way |
| **Bootstrap draws differ by design.** Different seeds and code give different draws | Interval bounds are compared for agreement, not equality |

## Audit table

Severity describes the effect on the case study. **None of these changes a reported estimate.**

### Data, joins and SQL

| ID | Check | Verdict | Type | Method and evidence | Discrepancy | Limitation |
|---|---|---|---|---|---:|---|
| T1 | Source files available | PASS | IND | 9 source CSVs plus the cleaned reviews file were read. Cleaned reviews match the original on all 99,224 rows for the analysis fields | None | Text fields were not compared |
| T2 | Keys and grain | PASS | IND | 99,441 orders, with 0 duplicate order, customer, seller, product, translation or order-item keys. 0 orphan items, reviews or payments | None | The database itself has no enforced keys |
| T3 | Join duplication | PASS | IND, INS | Joining items directly to payments would give 117,601 rows and R$14,209,115.34, against the correct R$13,591,643.70 across all statuses. `bi_orders` aggregates both first and returns 99,441 rows, one per order | None | |
| T4 | Missing records | PASS | IND | 775 orders have no items, none of them delivered. 1 delivered order has no payment, and payment totals aren't used in KPIs. 610 products have blank categories. 2 category names have no translation, on 24 item rows, and keep their Portuguese names | None | 256 delivered orders differ from price plus freight by over R$0.05. Not relevant to these KPIs, but payments shouldn't be treated as equal to sales |
| T5 | Analysis table, row by row | PASS | IND, CMP | 23 derived fields, including late, delay band, primary seller, category, distance band and scores, compared on all 96,470 base orders: 0 mismatches. Largest distance difference 0.0004 km | 21 answer and 3 purchase timestamps differ by exactly 60 minutes (see D3) | |
| T6 | Export SQL on clean data | PASS | REP | `sql/04` run on a clean load. 23 columns identical. `validation.csv` and `zip_positions.csv` identical | Explained: 1,415 and 1,416 blank categories against `unknown`, which the loader treats alike; 47 timestamp cells, each exactly 60 minutes; 1 extra row in `timestamp_checks.csv` (D3) | Not the live database |
| T7 | View definition | PASS | REP | The view from `sql/01` and the view from `sql/02` have the same `pg_get_viewdef` hash on the throwaway cluster | None | The live view was compared earlier from user-pasted output, not in this step |
| T8 | Analysis queries | PASS | REP, INS | `sql/03` ran without errors. The Q13 and Q14 filter `delivered >= purchase` removes 0 delivered orders | None | Results were not all compared line by line. Q13 and Q14 were verified earlier by the user |
| T9 | `sql/02` content | FAIL, minor | INS | The file ends with a leftover timestamp diagnostic `SELECT` after the view definition, which its header doesn't mention | Not a calculation issue | Harmless and read-only |
| T10 | Power BI measures | NEEDS INVESTIGATION, minor | INS | KPI definitions read as matching SQL. Two empty measures remain (`Measure`, `Measure 2`). The on-time measure has no validity filter, by design, and average delivery time does | Not executed | Power BI wasn't run. The planned new page will need its own check |
| T11 | Live database | NEEDS INVESTIGATION, minor | Not possible | See limitations. Indirect evidence is strong (T6) | Not assessed directly | Only a query by the user can close this |

### Locked KPIs (independent, from raw CSVs)

| ID | KPI | Locked | Independent | Verdict |
|---|---|---:|---:|---|
| K1 | Delivered orders | 96,478 | 96,478 | PASS |
| K2 | Delivered with a date | 96,470 | 96,470 | PASS |
| K3 | On-time orders | 89,936 | 89,936 | PASS |
| K4 | Late orders | 6,534 | 6,534 | PASS |
| K5 | On-time rate | 93.23% | 93.23% | PASS |
| K6 | Total product sales | R$ 13,221,498.11 | R$ 13,221,498.11 | PASS |
| K7 | Average order value | R$ 137.04 | R$ 137.04 | PASS |
| K8 | Average delivery time | 12.5 days | 12.5069 days | PASS |

Sales were summed with exact decimals. K8 is 12.51 at two decimals, and the locked value is stated to one. Sales and order value use 96,478 orders, while delivery rates use 96,470.

### Analysis code and statistics

| ID | Check | Verdict | Type | Method and evidence | Discrepancy | Limitation |
|---|---|---|---|---|---:|---|
| C1 | Model specifications and adjustment sets | PASS | IND, INS | Re-implemented from the plan. Term and order counts match: A1 30 terms, A2 54, A3 54, A4 40, A5 31, A7 57. Reasoned departures in B4 and X3 are documented | None | Shared-reading risk (see above) |
| C2 | Denominators | PASS | IND | 96,470 base; 95,824 reviewed; 6,381 late and reviewed; 94,724 with distance; 51,984 RJ and SP; 83,514 in A7; 94,558 stage-eligible with distance; 201 sellers in A6, top 21 | None | |
| C3 | Missing-data handling | PASS | IND | 646 unreviewed, 1,275 multi-seller and 471 no-position orders are excluded where documented. 279 customers and 7 sellers have no position | None | |
| C4 | Clustered errors and Wald tests | PASS | IND | Own CR1 sandwich. Delta intervals match, for example A1 5.80 to 9.11 and A2 49.61 to 52.47. p-values agree after Holm | None | Dependence within customers isn't modelled: 5,921 delivered orders come from repeat customers. Already disclosed |
| C5 | Bootstrap | PASS | IND | Sellers resampled with their actual rows, against frequency weights in the project. Agreement below | Largest bound difference 0.68, within simulation noise at 500 replicates (see the table below) | Month merges, quartile cuts, peak months and category groups are fixed across replicates, so intervals are conditional on them and could be slightly narrow |
| C6 | Holm correction | PASS | IND | Recomputed from independent p-values: A1 4.28e-26, A3 2.79e-121, A5 3.20e-06, A7 0.0201, A4 0.257 | A6 differs (C8) | One-sided A6 test mixed with two-sided tests, already disclosed |
| C7 | Reproducibility of documents | NEEDS INVESTIGATION | INS | Scripts in the repo produce the JSON results. The generators and checkers that wrote tables into the documents exist only in a temporary folder | Not numeric | A reviewer can reproduce the numbers, but not the document tables, from the repo. The full run also needs a database export |
| C8 | A6 p-value resolution | FAIL, minor | IND, CMP | The stored raw p is 1/5001, the smallest possible value at 5,000 draws, so Holm 0.0006 is a limit and not a measured value. At 2,000 draws the same floor gives raw 0.0005 and Holm 0.0015 | 0.0006 against 0.0015, from simulation count only | The conclusion is unchanged. It should read "at most" |
| C9 | Sparse-group rule wording | FAIL, minor | INS | The plan says under 30 orders or under 10 events. The code also requires 10 non-events | Stricter than documented | The log mentions it in one place only |
| C10 | `collapse_sparse` | FAIL, minor | IND, INS | With one sparse level it relabels that level as "other" without merging, though its docstring says it merges. Reproduced for the B4 before-arrival 3+ items level (69 orders, 8 non-low). Disclosed for B4, but X3d uses the same model with no such note | Previously measured effect at most 0.04 points | The effect wasn't re-measured for X3d, which is structurally the same model |
| C11 | Separation and thin terms | PASS | IND | B4 before-arrival multi-seller: 3 of 3 orders are low-rated, confirmed. Models converge after the documented removal. In the 500-replicate A3 bootstrap, 1 replicate failed; at 2,000, 2 failed (0.1%). Stored: 0 of 500. All are well below the 5% flag | Small; different draws | `class_a.py` has no thin-term diagnostic. A3's multi-seller term rests on at least 12 orders (derived from B4 counts) |
| C12 | "Largest coefficient" wording | FAIL, minor | CMP | The log says the corrected B4 model's largest coefficient is 1.74. That figure includes the intercept. The largest non-intercept coefficient is 1.02 | 1.74 against 1.02 | The diagnostic conclusion is unaffected |
| C13 | Code cleanliness | FAIL, minor | INS | Hard-coded `a2_estimate_for_context: 51.04` and `PEAK` months; both match computed values. Dead code: `_ = np`, `_ = (ss, TIMING, diagnostics)`, and unused variables in `sensitivity_common.py`. `class_a.py` and `modeling.py` duplicate logic | None numerically | Hard-coded values wouldn't update if the data changed |

### Dates and timestamps

| ID | Check | Verdict | Type | Method and evidence | Discrepancy | Limitation |
|---|---|---|---|---|---:|---|
| D1 | Creation date against answer timestamp | PASS | IND | Primary timing uses the answer timestamp; S9 uses creation date. 0 answers precede creation. All four B4 rows are reproduced under both definitions | None | 85 creation values aren't at midnight; S9 compares dates, so this has no effect |
| D2 | 25 April 2018 discontinuity | PASS | IND | Median carrier hour 19 on 24 April and 13 on 25 April; evening share 74% and 3%. Within 14 days either side, carrier 19 to 13, while delivery (18) and purchase (15) don't move. 69,129 and 27,152 stage-eligible orders; 67,983 and 26,575 with distance | None | Cause unknown. Late-handover share also moves, from 7.51% to 4.77% within that window, so **B5 estimates shouldn't be compared across periods** |
| D3 | Daylight-saving shift | PASS | IND, REP, CMP | Source values in Spain's missing hours: 3 purchase, 2 approval, 21 review answers. All stored values are exactly 60 minutes later. **0 of 95,824 answer-timing groups change**, and 0 purchase months. One order appears approved before purchase only as stored | None | The mechanism remains unproven |
| D4 | 197 flagged sequences | PASS | IND | 165 carrier before purchase (163 under 3 hours, all from the boundary; 2 larger), 23 delivery before carrier, 7 no delivery date, 1 no delivery or carrier date, 1 no carrier date. No overlaps. 189 in the base, 3 late, 188 reviewed, 96,281 eligible | None | |
| D5 | Long-delivery count | FAIL | IND, CMP | `methodology.md:126` and `data_quality_assessment.md:107` state 288 orders. The code uses 298 (the S15 order count agrees), and an independent count gives 298 | **288 against 298** | The source of 288 wasn't found. Other definitions give 283, 294, 295, 306 and 317. S15 results themselves are correct |
| D6 | S9 "after delivery" wording | FAIL, minor | IND | This group means created on or after the delivery **date**, so it includes same-day creation. 198 late reviews in it have an answer timestamp before delivery | Label imprecise | Figures are correct |
| D7 | Timing and delay are almost inseparable | NEEDS INVESTIGATION | IND | Creation before delivery by band: 20.8%, 90.7%, 99.9%, 100%. Answer before delivery: 22.5%, 77.3%, 96.1%, 98.6%. Median creation is 1 day after delivery for on-time orders; for late orders, 2 days after the estimated date and 4 days before delivery | Not numeric | This pattern could fit surveys being triggered by delivery or shortly after the promised date, but the data can't confirm that, and it isn't documented. The docs say the two are "closely linked", which is accurate, and S9 comparisons beyond 4–7 days have almost nothing to compare with |

### Leakage, selection and interpretation

| ID | Check | Verdict | Type | Method and evidence | Discrepancy | Limitation |
|---|---|---|---|---|---:|---|
| L1 | Data leakage | PASS | INS | No predictive model is trained. No Class A covariate is recorded after the outcome. Month merging uses the outcome only to assess sparsity | None | Freight, same-state seller and late handover may be mediators, so adjusting for them changes what's measured. Already disclosed for freight |
| L2 | Selection: reviews and non-delivery | NEEDS INVESTIGATION | IND | Unreviewed: 2.34% of late and 0.55% of on-time orders. S12 bounds cover those 646 orders. **No check bounds undelivered orders**: 2,971 orders aren't in the base, 2,841 orders outside delivered status have reviews, and non-delivery is 3.91% in RJ and 2.98% in SP | Not numeric | Disclosed as a limitation, but not quantified. Non-delivery in peak months (2.96%) is close to other months (2.89%) |
| L3 | Splitting by answer timing | PASS | IND, INS | X3a, X3b, B3 and B4 split on something recorded after lateness occurs. The docs say so, and don't read these as effects on a received order | None | Remains a selection risk in any reading |
| L4 | Peak-month selection | PASS | IND | The written rule selects exactly 2017-11, 2018-02 and 2018-03 | None | Selected using the outcome, already disclosed. S8a removes high-late months by construction |
| L5 | Sparse categories in A7 | PASS | IND | 21 categories; the smallest has 30 sellers. Spread 3.69, baby against luggage_accessories. Cramér's V 0.031 | None | The extreme pair is itself selected, already disclosed |
| L6 | B5 pattern text | FAIL, minor | CMP | The stored JSON text for B5 from 25 April says "Small pattern, below the screening criterion" for +18.13 points. Only the 500-order requirement fails (470). The log explains this correctly | Text only | Affects the JSON, not the log |
| L7 | Causal language | PASS | INS | Results are described as observational, and the A2 headline is qualified | None | Keep checking in Step 9 |

### Robustness labels and document accuracy

| ID | Check | Verdict | Type | Method and evidence | Discrepancy | Limitation |
|---|---|---|---|---|---:|---|
| R1 | Robustness table counts | PASS | CMP | Recounted from stored rows. Runs 14, 12, 10, 10, 10, 6, 9; every range matches; 0 reversals, 0 zero-relation changes and 0 criterion crossings on headline contrasts | None | Counts only the headline contrast. For A3, the 15+ vs 8–14 step does change under S15, and the text says so. A7's joint test passes 0.05 under S15, also stated |
| R2 | A1 "Robust" | PASS | IND, CMP | X1a–d reproduced, +8.92 to +9.46. S8a +3.57 reproduced. RJ has 629 late orders excluding peak months, above 500 | None | +7.46 averages very different periods: +23.46 in peak months and +3.04 otherwise. B2 reports this; the headline shouldn't be quoted alone |
| R3 | A2 qualified "Robust" | PASS | IND, CMP | X3a +10.01 and X3b +69.98 reproduced. The label names the limitation | None | |
| R4 | A3 "Unresolved" | PASS | IND, CMP | X3d −2.42, X3e +4.84 and S15 −0.66 reproduced. Inconclusive re-derived | 15+ vs 8–14: stored −6.94 to −0.26; independent −7.31 to −0.29 at 2,000 replicates | The upper bound is close to zero, and one 500-replicate run reached +0.10. **Don't claim a fall at 15+ days** |
| R5 | A4 qualified "Robustly unsupported" | PASS | IND, CMP | +0.59, without state +2.47, 2,000+ km +2.52, S8a −1.34 and S8c +2.15 reproduced. The label is limited to the prespecified comparison | None | Unadjusted late rates rise across bands, 4.50% to 12.08%. The docs state that distance isn't ruled out |
| R6 | A5 "Sensitive" | PASS | IND, CMP | X2 +0.97 (−0.01 to 1.94) and S8a +0.88 reproduced. The exception to the label rule is documented | None | The 66.0% share of replicates reaching the criterion wasn't reproduced |
| R7 | A6 and A7 "Robustly below the practical-importance criterion" | NEEDS INVESTIGATION | IND, CMP | True of every point estimate. But intervals reach the criterion in 4 of 6 A6 label-deciding runs and all 8 A7 runs with a real interval. Primary upper bounds: A6 10.66, A7 6.90. Independent: 3.9% of A6 replicates reach 10 points. Stored: 25.8% of A7 replicates reach 5 points, or 12.3% with the pair fixed | Wording, not numbers | **Inconsistent treatment:** A5 straddling its criterion counted toward caution, while A6 and A7 straddling is described as "robustly below". A6 is reasonably supported; A7 less so |
| R8 | Separating evidence, importance and robustness | PASS | INS | The docs explain these as three questions and keep the labels apart | None | Apart from R7 |
| R9 | "Unsupported" definition | FAIL, minor | INS, CMP | The methodology includes "whole interval below the criterion". The code labels on the point estimate and zero. An interval above zero and wholly below the criterion would fit two labels | No current result is affected | Definition gap only |
| R10 | S13a A7 interval | FAIL, minor | CMP | `sensitivity_results.md:376` shows "3.25 to 3.25". This is a point estimate with no interval, and the note explaining it isn't in the table | Display | The JSON has the note |
| R11 | S5b band label | FAIL, minor | INS | Under "2 or more days late", the band labelled "1-3 days" contains only 2–3 days, and the tables don't say so | Label | Different-question check; no label depends on it |
| R12 | Rounding between documents | FAIL, minor | CMP | A6: exact 6.9653 is 6.97 in the log and 6.96 in the sensitivity results. B1: exact 10.6850 is 10.68 in the log and 10.69 in the sensitivity results. Both come from rounding twice | 0.01 | |
| R13 | Stale status text | FAIL, minor | INS | `methodology.md` still says "The main analysis hasn't been run yet", and its "Completed" list stops before the analysis | Text | README still awaits its planned rewrite, which isn't a defect at this stage |

## Independently reproduced results

Independent values use the IND code. Bootstrap values use 500 replicates with a different seed, unless stated.

| Result | Stored estimate | Independent | Stored interval | Independent interval | Label re-derived |
|---|---:|---:|---:|---:|---|
| A1 RJ vs SP | +7.46 | +7.458 | 5.88 to 9.13 | 6.03 to 9.14 | Supported |
| A2 late vs on time | +51.04 | +51.039 | 49.58 to 52.28 | 49.68 to 52.54 | Supported |
| A3 15+ vs 1–3 days | +42.10 | +42.100 | 39.04 to 45.22 | 38.51 to 45.51 (2,000) | Inconclusive |
| A3 4–7 vs 1–3 days | +34.72 | +34.717 | | 31.63 to 37.86 (2,000) | |
| A3 8–14 vs 4–7 days | +11.18 | +11.183 | 8.19 to 14.21 | 8.28 to 14.33 (2,000) | |
| A3 15+ vs 8–14 days | −3.80 | −3.800 | −6.94 to −0.26 | −7.31 to −0.29 (2,000) | |
| A4 600–1,000 vs 0–100 km | +0.59 | +0.591 | −0.49 to 1.50 | −0.42 to 1.60 (delta) | Unsupported |
| A5 top vs bottom freight | +2.16 | +2.164 | 1.27 to 3.01 | 1.24 to 3.01 | Supported |
| A6 concentration gap | +6.97 | +6.965 | 2.48 to 10.66 | 2.82 to 10.42 (2,000) | Detectable |
| A7 category spread | 3.69 | 3.690 | 2.88 to 6.90 | Not bootstrapped | Detectable |
| B3 late, before vs on time | +70.07 | +70.074 | 68.49 to 71.45 | 68.55 to 71.51 | Exploratory |
| B3 late, after vs on time | +9.94 | +9.940 | 8.26 to 11.62 | 8.42 to 11.56 | Exploratory |

| Other reproduced figures | Stored | Independent |
|---|---:|---:|
| A1 odds ratio | 2.99 | 2.992 |
| A2 odds ratio | 17.00 | 17.001 |
| A3 adjusted band rates | 33.83, 68.54, 79.73, 75.93 | 33.83, 68.54, 79.73, 75.93 |
| A6 top late and order share | 41.98%, 35.01% | 41.98%, 35.01% |
| A6 split-half; null gap | 6.00; 2.41 | 6.02; 2.44 |
| A6 sellers above and below the funnel | 12, 4 | 12, 4 |
| A7 joint test p | 0.010 | 0.0100 |
| B4 before-arrival rates | 78.85, 81.51, 82.36, 78.88 | 78.85, 81.51, 82.36, 78.88 |
| B4 after-arrival rates | 18.59, 20.45, 26.32 | 18.59, 20.45, 26.32 |
| B4 S9 rates, created before delivery | 59.84, 71.80, 80.21, 78.35 | 59.84, 71.80, 80.21, 78.35 |
| B4 adjusted, before arrival | +3.02, −0.16, −5.27 | +3.018, −0.164, −5.272 |
| B4 adjusted, after arrival | +1.59, +3.25 | +1.592, +3.250 |
| B1 peak and other late rate | 15.15%, 4.46% | 15.15%, 4.46% |
| B2 gaps and difference | 23.46, 3.04, 20.42 | 23.463, 3.040, 20.423 |
| B5 before and from 25 April | +13.39, +18.13 | +13.389, +18.129 |
| B6 | +12.67 | +12.672 |
| B7 on-time share of low ratings | 67.54% | 67.54% |
| Growth, Jan–Aug orders | 21,997 to 52,777 | 21,997 to 52,777 |
| Growth, Jan–Aug sales | R$2,993,277.13 to R$7,217,172.24 | Same |
| Volume share of growth | 99.2% | 99.2% |

| Key sensitivity results | Stored | Independent |
|---|---:|---:|
| A1 X1a, X1b, X1c, X1d | +9.46, +9.44, +8.92, +9.46 | +9.463, +9.439, +8.919, +9.456 |
| A1 S8a | +3.57 | +3.574 |
| A2 X3a, X3b | +10.01, +69.98 | +10.011, +69.977 |
| A2 S1a | +50.99 | +50.986 |
| A3 X3d, X3e | −2.42, +4.84 | −2.419, +4.842 |
| A3 S15, 15+ vs 8–14 | −0.66 | −0.656 |
| A4 S8a, S8c | −1.34, +2.15 | −1.337, +2.147 |
| A5 X2, S8a | +0.97, +0.88 | +0.966, +0.884 |
| A6 S8a estimate | +3.40 | +3.396 |
| A6 S8a interval | −0.49 to 8.15 | −1.04 to 7.47 (2,000) |
| A7 S15 spread; joint p | 3.23; 0.054 | 3.232; 0.054 |

**Numerical discrepancies:** only those in D5 (288 against 298), C8 (A6 Holm p, simulation floor), C12 (1.74 against 1.02) and R12 (rounding by 0.01), plus simulation noise in bootstrap bounds. At 500 replicates, seven bounds differ by more than 0.25 points, the largest 0.68 (A3, 15+ vs 8–14). Six of those seven were rechecked at 2,000 replicates and came within 0.37 of the stored values. The seventh, A2's upper bound (0.26), wasn't rechecked. No difference changes a label.

**One error was in the audit itself.** A first version of the comparison reported 646 answer-timing changes from the daylight-saving shift. This was a null-comparison bug in the checker, since 646 is the number of unreviewed orders. The corrected value is 0, confirmed by a separate follow-up and a retest.

## Not independently reproduced

- **Sensitivity scenarios:** S1b, S2, S3, S4, S5, S6, S7, S10, S11, S12, S13, S14 and S16 were counted from stored rows, not recomputed. Row-level table agreement lowers the risk, but doesn't eliminate it.
- **Intervals:** bootstrap intervals for B1, B2, B5, B6 and B7, the A7 bootstrap, and the 2,000-replicate shares for A5 and A7.
- **Secondary statistics:** mean score differences, Wilson intervals, variance inflation and condition numbers.
- **Class C:** only growth, base sales, late-order sales and the SP and RJ late share were recomputed. The rest was inspected.
- **Live systems:** the database and Power BI.

## Issues to resolve before Step 9

| Priority | Issue | Decision or action needed |
|---|---|---|
| **Decide** | R7: wording of the A6 and A7 labels | Keep, or reword. This changes an approved label's wording, not its evidence |
| **Correct** | D5, R13, R12, R10, R11, D6, C12, C8, C9, R9, L6, T9: documentation and text errors | Approve corrections as a separate change |
| **Carry into Step 9** | D2, D7, R2, R4, L2 | Don't compare B5 across periods; don't state a survey trigger as fact; don't quote A1's +7.46 without the period split; don't claim a fall at 15+ days; state that undelivered orders aren't bounded |
| **Optional** | C7, C10, C13, T10, T11 | Bring document generators into the repo; tidy code; run a small user-side query. None of these is blocking |

## Reproducing this audit

```powershell
.\.venv\Scripts\python.exe -B python\audit\independent_recompute.py <raw-folder> 500
.\.venv\Scripts\python.exe -B python\audit\independent_recompute.py <raw-folder> 2 <orders-csv>
py -I -B python\audit\raw_integrity_checks.py <raw-folder> <output-json>
.\.venv\Scripts\python.exe -B python\audit\bootstrap_precision_check.py <orders-csv> <output-json> 2000
.\.venv\Scripts\python.exe -B python\audit\compare_with_stored.py <orders-csv> <clean-load-folder> <raw-folder> <output-json>
```

The second command writes the order table and stops before fitting models. `compare_with_stored.py` needs the exports from running `sql/04` on a clean load, and the project's stored results.

## Remediation addendum (2026-11-05)

**Status: corrections reviewed and approved for the audit commit.** C13 and the remaining L6 change are a separate change. This addendum records corrections made after the audit. It doesn't change the historical verdicts above.

### FAIL items

| ID | Issue | Status | What changed | Pending, and why |
|---|---|---|---|---|
| D5 | 288 against 298 long deliveries | Resolved | `methodology.md` and `data_quality_assessment.md` now say 298, with the definition. The only remaining 288 is the change-log entry describing the correction | The source of 288 is still unknown |
| C8 | A6 p-value at the simulation limit | Resolved | The log says "at most 0.0006" and separates the original 5,000-draw limits from the audit's 2,000-draw limits | None |
| C9 | Sparse-group rule | Resolved | `analysis_plan.md` now includes the 10 non-event condition | None |
| C12 | Coefficient description | Resolved | The log gives 1.02, or 1.74 including the intercept | None |
| D6 | S9 timing definition | Resolved | S9 groups renamed, with the same-date rule, the 198 reviews and the link to delay length stated | None |
| R9 | Overlapping label definitions | Resolved | `methodology.md` definitions rewritten to match the applied rule, including A3's. All seven labels are unchanged under the new wording | None |
| R10 | S13a A7 interval | Resolved | Now shows "Not estimated" | None |
| R11 | S5b delay band | Resolved | Comparisons relabelled 2–3 days, with a note on the B4 column | None |
| R12 | Double rounding | Resolved, with a limit | A6 is 6.97 and B1 is 10.68 in both documents | 34 other sensitivity rows have a third decimal of 5, so their two-decimal display could be off by 0.01. Exact values aren't stored. These rows have no primary figure to conflict with |
| R13 | Stale status text | Resolved | Status text updated in `methodology.md`, `hypothesis_log.md` and `sensitivity_results.md` | None |
| T9 | Leftover `SELECT` in `sql/02` | Resolved | Removed, with the edit noted in the file header. No repository file refers to it | None |
| C10 | `collapse_sparse` | Partly resolved | Docstrings, `analysis_plan.md`, the log and the sensitivity diagnostics now describe the relabelling. No executable code changed | Logic is unchanged. Merging would change B4 and X3d estimates, so no logic change is recommended |
| L6 | B5 pattern text | Partly resolved | The log explains the correct reading, and a code comment was added | The stored JSON still has the old text. Changing it needs a code change and re-run, as a separate change |
| C13 | Code cleanliness | Pending | Nothing changed | Removing code or replacing hard-coded values is a separate change |

**Totals:** 11 resolved, 2 partly resolved, 1 pending.

### Approved robustness wording

- **A6:** "Below the practical-importance criterion in all tested point estimates; uncertainty intervals sometimes reach the criterion."
- **A7:** "Below the practical-importance criterion in all tested point estimates; uncertainty intervals reach the criterion."

The earlier qualifiers, sensitivity to peak-month selection (A6) and weaker detectability under some restrictions (A7), moved from the labels into the explanations. Evidence labels, estimates, intervals, definitions and criteria are unchanged.

### NEEDS INVESTIGATION items (all six retained)

| ID | Item | Current position |
|---|---|---|
| R7 | A6 and A7 wording | The approved wording is applied, and the item stays listed until that wording is reviewed |
| D7 | Timing and delay are almost inseparable | Numbers are now stated for S9. No survey trigger is claimed, and the mechanism remains unknown |
| L2 | Selection from reviews and non-delivery | Unchanged. No check bounds undelivered orders |
| C7 | Document generators outside the repo | Unchanged. Those generators now predate these corrections, so re-running them would overwrite the corrections |
| T10 | Power BI measures not executed | Unchanged |
| T11 | Live database not queried | Unchanged |

### Correction to the audit

C10 says X3d has "no such note". `sensitivity_results.md` already listed the sparse 3+ items level in X3d, so the level was disclosed. What wasn't disclosed was that the level is relabelled without being combined. The original finding is preserved above.

### Verification

| Check | Method | Result |
|---|---|---|
| Analysis code behaviour | Syntax trees compared with `e06158e`, ignoring docstrings and comments, for all 8 scripts in `python/analysis/` | Identical, so the analysis wasn't re-run |
| Stored results | Checksums of all 12 files in `data/processed/` before and after | Unchanged |
| KPIs, Class A, Class B and key sensitivity | Comparison re-run: 92 rows, 7 evidence labels and the robustness recount | Identical to the first comparison. All 8 KPIs still match |
| Document numbers | Numbers in old and new text compared, per document | The only corrected values are 288 to 298, 6.96 to 6.97, 10.69 to 10.68, the S13a interval and the 2–3 day labels. Other new numbers repeat existing results or come from this audit |
| Document cells | Checkers updated to derive corrected values from source results and the independent order table | 2,633 sensitivity cells, 288 and 591 log cells, and 89 claim checks all pass. As a negative control, the same checkers fail on the previous documents at the corrected cells. These checkers are outside the repository, as in C7 |
| Edited `sql/02` | Run on a throwaway database loaded from the raw CSVs, then deleted | View hash unchanged, `bff8c7ff86818c0a3ce94fed5ce024cb`. `sql/04` still reproduces the same exports |
| Protected files | Fingerprints | 10 raw files and 54 backup files unchanged. Working Power BI file unchanged during this step |

The independent recomputation wasn't re-run, because its inputs and logic didn't change.

## Follow-up (2026-11-05): C13 and L6

This follow-up records the separate change the addendum above refers to. It updates the status of L6 and C13 from that addendum. The original findings and counts are unchanged.

### Status changes

| ID | Issue | Status | What changed | Pending, and why |
|---|---|---|---|---|
| L6 | B5 pattern text | Resolved | `class_b.py` now reports "Meets the percentage-point criterion; misses the minimum of 500 late orders" when an estimate meets the point criterion but misses the order requirement. The re-run stored this text for B5 from 25 April 2018, and the log quotes it | None |
| C13 | Code cleanliness | Partly resolved | Confirmed dead code removed from `descriptive.py`, `sensitivity_supplement.py` and `sensitivity_common.py`. `class_b.py` reads the A2 context value from `class_a_results.json`, still 51.04. `sensitivity_common.py` now stops with an error if `PEAK` differs from the written peak-month rule. 3 more unused imports found by a later scan were removed: `pd` from `descriptive.py`, and `BOUNDARY` and `MIN_ORDERS` from `class_b.py` | `PEAK` remains written in the code, now with that check. `class_a.py` and `modeling.py` still duplicate logic, because changing Class A logic was out of scope |

**Totals across the 14 FAIL items:** 12 resolved, 2 partly resolved (C10, C13), 0 pending.

`class_b.py` now depends on `class_a_results.json`, so `class_a.py` has to run first. The peak-month check passes on the correct set and raises an error when a month is removed from `PEAK`.

### Output comparison

`descriptive.py`, `class_b.py`, `sensitivity_supplement.py` and `sensitivity.py` were re-run with fixed seeds, using 8 threads. Outputs were compared exactly with a copy taken beforehand, with no tolerance.

| File | Values compared | Result |
|---|---|---|
| `class_b_results.json` | 842, or 822 without empty containers | 7 changed: the B5 text and 6 p-values. The other 701 numeric values and 93 of 94 text values are identical |
| `descriptive_results.json` | 456 | Byte-identical |
| `sensitivity_results.json` | 8,367 | Byte-identical |
| `sensitivity_supplement.json` | 1,534 | Byte-identical |
| Other 8 files in `data/processed/` | Not re-run | Byte-identical, including `class_a_results.json` |

So the B5 text isn't the only change in the stored Class B file. The 8-thread results were kept, because the differences don't affect any conclusion.

The 3 extra unused imports were removed after this re-run, so the stored results weren't regenerated from the final code. Syntax trees before and after that removal are identical apart from the removed names.

### P-value control

**What was tested.** The 6 values are analytic Wald p-values, not simulated ones. Each tests whether one logistic regression coefficient is zero (B2 and B6 interactions, B3, both B5 periods, B6), using the coefficient divided by its seller-clustered standard error, with a two-sided normal p-value. They have no replicate count or simulation resolution, and the bootstrap doesn't feed into them. The simulated A6 p-value is a separate result and was neither re-run nor changed.

**Largest relative difference:** 1.6 in a trillion (1.62e-12). The implied test statistics differ by less than 1e-13.

| Control, using `class_b.py` at 2 bootstrap replicates on an isolated copy | Result |
|---|---|
| Previous code, 4 threads, against the earlier stored p-values | 0 of 7 differ |
| Changed code, 4 threads, against the earlier stored p-values | 0 of 7 differ |
| Previous code, 8 threads, against the re-run stored p-values | 0 of 7 differ |
| Changed code, 8 threads, against the re-run stored p-values | 0 of 7 differ |
| Repeat runs at 8 threads, for each code version | 0 of 7 differ |
| Previous against changed code at 1, 4 and 8 threads, whole file | 1 of 822 values differs at each setting: the B5 text |

**Conclusion.** The code change altered only the B5 text. The 6 p-value differences come from the thread count, which changes floating-point rounding. The earlier file matches a 4-thread run exactly. Because the controls used 2 replicates, they test the p-values and the effect of the code. The 500-replicate intervals are covered by the output comparison above.

**Limit.** These controls ran on one machine. No estimate, interval or label changed in this comparison. Those values are stored rounded, so differences this small wouldn't normally show. The p-values are the only Class B values stored at full precision.

### Reproducibility

- **Thread counts:** the current stored Class B results were generated with 8 threads. The earlier version was generated with 4.
- **Analytic Wald p-values:** these can differ slightly at full precision between thread counts, because the floating-point operations behind them are carried out differently. In this comparison, the largest relative difference was 1.62e-12.
- **A6's simulated p-value:** this is a different kind of result. It comes from a seeded simulation, and its reported value is a limit set by the number of draws: at most 0.0002 raw and 0.0006 after Holm with 5,000 draws. The differences above say nothing about the precision of that limit.
- **What can't be claimed:** byte-for-byte reproducibility across thread configurations. Repeat runs matched exactly at 8 threads on this machine, but no other machine was tested. The scripts don't set a thread count, and the repository doesn't record one, so a re-run may differ in these full-precision p-values.

**Stored zero.** The B3 p-value for late orders answered before arrival is stored as `0.0`. Its test statistic is about 69.7, so the true value is too small for the number format. It should be read as extremely small, not as zero.
