# Sensitivity Results

**Status: Step 7 results for review.** Primary Class A and Class B estimates, definitions, screening criteria and labels are unchanged. All results are observational associations. The independent audit (Step 8) is in [independent_audit.md](independent_audit.md), with a remediation addendum that lists open items. The robustness labels below have been approved, and the A6 and A7 wording was revised after the audit.

Reproduced by `python/analysis/sensitivity.py` and `python/analysis/sensitivity_supplement.py`, which use `python/analysis/sensitivity_common.py`.

## How to read this

These are three separate questions, and a finding can differ on each:

| Question | Where it's answered | What it means |
|---|---|---|
| **Statistical significance** | Primary evidence labels, in `hypothesis_log.md` | Is the effect distinguishable from zero after Holm correction? |
| **Practical importance** | Researcher-defined screening criteria, not business-validated targets | Is it large enough to discuss? |
| **Robustness** | This document | Does the conclusion hold under other reasonable choices? |

Only review, timestamp and structure checks can decide a robustness label. Different-question checks (S5, S6, S8, S9) change what's being asked, so they're interpreted rather than treated as failures. Required exploratory checks don't count as confirmation, and their influence on a label is stated openly.

## Robustness summary, A1–A7

Ranges cover alternative estimates in percentage points. A1's label-deciding range includes the required SP-seller checks.

| ID | Primary evidence label (unchanged) | Primary estimate | Range: label-deciding checks | Range: different-question checks | **Robustness** |
|---|---|---:|---:|---:|---|
| A1 | Supported | +7.46 | 7.04 to 9.46 | 3.57 to 8.17 | **Robust** |
| A2 | Supported | +51.04 | 49.09 to 52.49 | 42.98 to 57.27 | **Robust as an observational association; answer timing is an important limitation** |
| A3 | Inconclusive | +42.10 | 39.85 to 45.44 | 32.27 to 42.05 | **Unresolved** |
| A4 | Unsupported | +0.59 | 0.39 to 0.59 | −1.34 to 2.15 | **Robustly unsupported under the prespecified comparison** |
| A5 | Supported, close to the criterion | +2.16 | 2.01 to 2.27 | 0.88 to 2.91 | **Sensitive; judgement incorporates an exploratory state-adjusted check** |
| A6 | Detectable, not practically important | +6.97 | 6.32 to 7.14 | 3.40 to 7.41 | **Below the practical-importance criterion in all tested point estimates; uncertainty intervals sometimes reach the criterion** |
| A7 | Detectable, not practically important | 3.69 | 3.23 to 3.75 | 2.93 to 3.70 | **Below the practical-importance criterion in all tested point estimates; uncertainty intervals reach the criterion** |

| ID | Label-deciding runs | Direction reversed | Relation of interval to zero changed | Crossed the criterion |
|---|---:|---:|---:|---:|
| A1 | 14 | 0 | 0 | 0 |
| A2 | 12 | 0 | 0 | 0 |
| A3 | 10 | 0 | 0 | 0 |
| A4 | 10 | 0 | 0 | 0 |
| A5 | 10 | 0 | 0 | 0 |
| A6 | 6 | 0 | 0 | 0 |
| A7 | 9 | 0 | 0 | 0 |

### Why each label

- **A1, robust.** RJ stays higher in every run. The required SP-seller checks give larger gaps, from +8.92 to +9.46 points, so limited overlap didn't create the result. Excluding peak months shrinks it to +3.57 points (2.54 to 4.60), which is still above the 2-point criterion. The size depends on the period, and the direction doesn't.
- **A2, robust as an observational association.** Data-handling choices barely move it. Review answer timing is an important interpretive limitation, and it's an exploratory split: +10.01 points (8.40 to 11.62) when late reviews have an answer timestamp after the recorded delivery, and +69.98 points (68.53 to 71.42) when it's before. Both stay above the 5-point criterion. The headline figure shouldn't be read as the effect on a received order.
- **A3, unresolved.** The evidence label stays Inconclusive. The overall rise from 1–3 to 15+ days is stable across data-handling checks, but within answer-timing groups it mostly disappears: −2.42 points (−7.11 to 2.28) before arrival, and +4.84 points (−5.04 to 14.72) for 8–14 against 1–3 days after arrival. The drop at 15+ days also goes away when deliveries over 60 days are excluded (−0.66 points, −4.06 to 2.75). Timing and delay length are too closely linked to separate them here.
- **A4, robustly unsupported under the prespecified comparison.** The estimate stays below the criterion, with an interval including zero, in every label-deciding run. Different-question checks are less settled: −1.34 points (−2.11 to −0.56) excluding peak months, and +2.15 points (1.13 to 3.16) excluding purchases from July 2018, which is above the criterion. This doesn't show that distance has no relationship with lateness across all periods, only that this fixed comparison adds little once state is known.
- **A5, sensitive.** The Supported evidence label is preserved, and **this judgement incorporates an exploratory state-adjusted check**, as an explicit exception to the label-deciding rule. Under that rule alone, it would read as robust, but only just: estimates run from 2.01 to 2.27 against a 2-point criterion, and every interval straddles it. Adding customer state, an exploratory check, gives +0.97 points (−0.01 to 1.94), and excluding peak months gives +0.88 points (0.17 to 1.59). In the larger bootstrap, 66.0% of replicates reach the criterion. Freight may partly reflect destination and period, which the data can't settle.
- **A6, below the practical-importance criterion in all tested point estimates; uncertainty intervals sometimes reach the criterion.** The gap stays below 10 points in every run, with a split-half gap near 6 points. Its interval reaches 10 points in the primary result (2.48 to 10.66), at 2,000 replicates (2.70 to 10.40) and in 4 of the 6 label-deciding runs. The result is also sensitive to peak-month selection: excluding peak months, it falls to +3.40 points (−0.49 to 8.15), and its split-half gap of 2.20 is close to the 2.15 expected with no real seller differences. 7 sellers remain above the funnel limit in that run, so seller differences don't vanish entirely.
- **A7, below the practical-importance criterion in all tested point estimates; uncertainty intervals reach the criterion.** The spread stays below 5 points in every run. Its interval reaches 5 points in the primary result (2.88 to 6.90), at 2,000 replicates (3.03 to 6.32) and in all 8 label-deciding runs that have an interval. Statistical detectability is less stable: the joint test gives p = 0.054 when deliveries over 60 days are excluded, and the lowest-rate and highest-rate categories change when peak months are excluded.

## Exploratory findings under sensitivity testing (Class B)

These remain **exploratory**. Their stability doesn't make them confirmed.

| ID | Finding | Primary estimate | Range across all runs | Assessment |
|---|---|---:|---:|---|
| B1 | Peak vs other months late rate | +10.68 | 9.76 to 11.60 | Stable, but the months were selected using the outcome |
| B2 | Widening of RJ's gap in peak months | +20.42 | 18.11 to 21.69 | Stable; the gap in other months stays at 2.65 to 3.43 |
| B3 | Late, answered before arrival, vs on time | +70.07 | 62.29 to 71.10 | Stable |
| B3 | Late, answered after arrival, vs on time | +9.94 | 6.69 to 17.61 | Direction stable; size depends on definitions |
| B4 | Delay length within timing groups | See table below | See table below | **Sensitive to the timing definition** |
| B5 | Late handover, before 25 April 2018 | +13.39 | 11.67 to 15.47 | Stable |
| B5 | Late handover, from 25 April 2018 | +18.13 | 14.13 to 21.32 | Stable in size; still misses the 500-order part of the criterion in the primary run |
| B6 | Multi-item vs single item | +12.67 | 10.82 to 13.61 | Stable |
| B7 | On-time orders' share of low ratings | 67.54% | 63.31% to 77.58% | Stable, and higher without peak months |

## Unexpected findings

1. **B4 depends on how timing is defined.** Using the review answer timestamp, low ratings barely change between delay bands before the recorded delivery: 78.85%, 81.51%, 82.36% and 78.88%. Using review creation date (S9), they rise: 59.84%, 71.80%, 80.21% and 78.35%. Review creation date is when the survey record was created, and the answer timestamp is when the answer was recorded. A review created before delivery can have an answer recorded after it, and S9's later group includes reviews created on the delivery date. **Neither is definitive evidence of when a customer formed or submitted the rating**, so the reading that delay length adds little can't be stated without this caveat.
2. **Seller concentration is largely a peak-month pattern.** Excluding peak months, the A6 split-half gap falls from 6.03 to 2.20 points, close to the 2.15 expected by chance.
3. **Freight's association weakens with customer state.** A5 drops from +2.16 to +0.97 points, and its interval reaches zero. With state in the model, only the step from the lowest to the second quartile remains (+1.01 points, 0.33 to 1.70).
4. **Distance changes sign with the period.** The A4 comparison is −1.34 points excluding peak months, and +2.15 points excluding purchases from July 2018.
5. **The drop at 15+ days comes from very long deliveries.** Excluding deliveries over 60 days, the A3 step from 8–14 to 15+ days changes from −3.80 to −0.66 points, and its interval includes zero.
6. **RJ's gap is larger under the overlap checks, not smaller.** Limiting to SP sellers gives +9.46 points against +7.46 in the primary model, which suggests the primary adjustment for same-state sellers may absorb part of the gap.
7. **More replicates didn't settle A5, A6 or A7.** Their intervals still straddle the criteria at 2,000 replicates, so this reflects real uncertainty, not bootstrap noise.

## Required checks

### A1: SP-seller overlap

| Check | RJ orders | RJ late | SP orders | SP late | Adjusted RJ–SP difference | 95% interval |
|---|---:|---:|---:|---:|---:|---:|
| SP sellers only | 8,021 | 1,143 | 30,264 | 1,420 | +9.46 | 8.02 to 10.90 |
| SP sellers, overlapping distance bands | 7,993 | 1,141 | 14,523 | 700 | +9.44 | 8.21 to 10.66 |
| Out-of-state sellers only, both states | 11,201 | 1,439 | 9,576 | 392 | +8.92 | 7.88 to 9.96 |
| 300–1,000 km only | 9,783 | 1,294 | 13,886 | 581 | +9.46 | 8.05 to 10.86 |

Bands with at least 30 orders from each state among SP sellers: 100-300 km, 300-600 km, 600-1,000 km. The same-state term equals customer state for SP sellers, so it's removed from X1a to X1c, and this is stated in each run. Sparse distance levels remain in X1a and X1c: 7 orders and 43 orders.

| Distance, SP sellers only | RJ orders | SP orders |
|---|---:|---:|
| 0-100 km | 21 | 15,741 |
| 100-300 km | 502 | 8,899 |
| 300-600 km | 6,504 | 5,563 |
| 600-1,000 km | 987 | 61 |
| 1,000-2,000 km | 7 | 0 |
| 2,000+ km | 0 | 0 |

### A5: customer state added (exploratory)

This doesn't change the A5 definition or result.

| Comparison | Adjusted difference | 95% interval |
|---|---:|---:|
| Highest vs lowest quartile | +0.97 | −0.01 to 1.94 |
| Q2 vs lowest | +1.01 | 0.33 to 1.70 |
| Q3 vs Q2 | −0.03 | −0.57 to 0.50 |
| Highest vs Q3 | −0.01 | −0.66 to 0.63 |

### A2 and A3: answer timing (exploratory)

| Check | Comparison | Orders | Adjusted difference | 95% interval |
|---|---|---:|---:|---:|
| A2 with late orders answered after arrival only | Late vs on time | 91,351 | +10.01 | 8.40 to 11.62 |
| A2 with late orders answered before arrival only | Late vs on time | 93,916 | +69.98 | 68.53 to 71.42 |
| A2 with all reviews answered after arrival | Late vs on time | 91,171 | +10.04 | 8.43 to 11.65 |
| A3 with reviews answered before arrival; multi-seller term removed because of separation | 15+ vs 1-3 days | 4,473 | −2.42 | −7.11 to 2.28 |
| A3 with reviews answered before arrival; multi-seller term removed because of separation | 4-7 vs 1-3 days | 4,473 | +3.02 | −1.37 to 7.41 |
| A3 with reviews answered before arrival; multi-seller term removed because of separation | 8-14 vs 4-7 days | 4,473 | −0.16 | −2.76 to 2.44 |
| A3 with reviews answered before arrival; multi-seller term removed because of separation | 15+ vs 8-14 days | 4,473 | −5.27 | −8.55 to −1.99 |
| A3 with reviews answered after arrival; 15+ days has under 30 reviews; category removed because of too few events | 8-14 vs 1-3 days | 1,889 | +4.84 | −5.04 to 14.72 |
| A3 with reviews answered after arrival; 15+ days has under 30 reviews; category removed because of too few events | 4-7 vs 1-3 days | 1,889 | +1.59 | −2.98 to 6.17 |
| A3 with reviews answered after arrival; 15+ days has under 30 reviews; category removed because of too few events | 8-14 vs 4-7 days | 1,889 | +3.25 | −7.72 to 14.22 |

## Larger bootstraps

2,000 seller-level replicates, seed 20261105, compared with the 500-replicate primary intervals.

| ID | Estimate | 500 replicates | 2,000 replicates | Replicates reaching the criterion | Failed replicates |
|---|---:|---:|---:|---:|---:|
| A5 | +2.16 | 1.27 to 3.01 | 1.29 to 3.02 | 66.0% | 0 |
| A6 | +6.97 | 2.48 to 10.66 | 2.70 to 10.40 | Not calculated | 0 |
| A7, re-selecting the pair | 3.69 | 2.88 to 6.90 | 3.03 to 6.32 | 25.8% | 0 |
| A7, fixed pair (baby, luggage_accessories) | 3.69 | Not run | 1.52 to 5.92 | 12.3% | 0 |

## Full results by hypothesis

Sensitivity intervals use errors clustered by seller with a delta-method interval, except where the label says otherwise. "Change" compares with the baseline re-fit of the primary model. "Mean score" rows are in stars, not points.

### A1. RJ compared with SP

| Check | Type | Alternative | Comparison | Orders | Events | Estimate | 95% interval | Change |
|---|---|---|---|---:|---:|---:|---:|---:|
| S0 | Baseline | Primary specification with delta-method interval | RJ vs SP | 51,984 | 3,296 | +7.46 | 5.80 to 9.11 | — |
| S3a | Timestamp | All flagged orders excluded | RJ vs SP | 51,912 | 3,294 | +7.48 | 5.82 to 9.14 | +0.02 |
| S3b | Timestamp | Only delivery-before-carrier excluded | RJ vs SP | 51,981 | 3,296 | +7.46 | 5.80 to 9.12 | +0.00 |
| S3c | Timestamp | Only carrier-before-purchase excluded | RJ vs SP | 51,916 | 3,295 | +7.46 | 5.81 to 9.12 | +0.00 |
| S4b | Timestamp | Affected orders excluded | RJ vs SP | 51,967 | 3,295 | +7.46 | 5.80 to 9.11 | −0.00 |
| S5a | Different question | Full timestamp, previous logic | RJ vs SP | 51,984 | 4,028 | +8.17 | 6.26 to 10.07 | +0.71 |
| S5b | Different question | 2 or more days late | RJ vs SP | 51,984 | 2,869 | +6.76 | 5.32 to 8.21 | −0.69 |
| S7 | Structure | Multi-seller orders assigned to primary seller | RJ vs SP | 52,706 | 3,304 | +7.43 | 5.79 to 9.07 | −0.03 |
| S8a | Different question | Excluding peak months | RJ vs SP | 40,888 | 1,768 | +3.57 | 2.54 to 4.60 | −3.88 |
| S8b | Different question | Excluding 2016 | RJ vs SP | 51,851 | 3,293 | +7.51 | 5.85 to 9.17 | +0.05 |
| S8c | Different question | Excluding purchases from July 2018 | RJ vs SP | 44,819 | 2,854 | +7.90 | 6.23 to 9.57 | +0.44 |
| S10a | Structure | Mean ZIP position | RJ vs SP | 51,984 | 3,296 | +7.46 | 5.80 to 9.11 | +0.00 |
| S10b | Structure | Excluding distances above the 99th percentile (2,483 km) | RJ vs SP | 51,981 | 3,296 | +7.46 | 5.81 to 9.12 | +0.00 |
| S15 | Timestamp | Excluding deliveries over 60 days | RJ vs SP | 51,836 | 3,148 | +7.04 | 5.43 to 8.64 | −0.42 |
| S13a | Structure | Linear probability model | RJ vs SP | 51,984 | 3,296 | +7.59 | 6.26 to 8.92 | +0.13 |
| S13b | Structure | Heteroskedasticity-robust errors, not clustered | RJ vs SP | 51,984 | 3,296 | +7.46 | 6.71 to 8.20 | +0.00 |
| X1a | Structure | SP sellers only; same-state term removed because it equals customer state here | RJ vs SP | 38,285 | 2,563 | +9.46 | 8.02 to 10.90 | +2.00 |
| X1b | Structure | SP sellers, overlapping distance bands only; same-state term removed | RJ vs SP | 22,516 | 1,841 | +9.44 | 8.21 to 10.66 | +1.98 |
| X1c | Structure | Out-of-state sellers only, for both customer states; same-state term removed | RJ vs SP | 20,777 | 1,831 | +8.92 | 7.88 to 9.96 | +1.46 |
| X1d | Structure | 300-1,000 km only, the bands where both states have many orders | RJ vs SP | 23,669 | 1,875 | +9.46 | 8.05 to 10.86 | +2.00 |

### A2. Late delivery and low ratings

| Check | Type | Alternative | Comparison | Orders | Events | Estimate | 95% interval | Change |
|---|---|---|---|---:|---:|---:|---:|---:|
| S0 | Baseline | Primary specification with delta-method interval | Late vs on time | 95,824 | 12,272 | +51.04 | 49.61 to 52.47 | — |
| S1a | Review | Earliest review | Late vs on time | 95,824 | 12,262 | +50.99 | 49.55 to 52.42 | −0.05 |
| S1b | Review | Excluding orders with several reviews | Late vs on time | 95,299 | 12,189 | +51.00 | 49.57 to 52.43 | −0.04 |
| S2 | Review | Excluding repeated review IDs | Late vs on time | 94,645 | 12,025 | +51.11 | 49.69 to 52.53 | +0.07 |
| S4b | Timestamp | Affected orders excluded | Late vs on time | 95,800 | 12,269 | +51.08 | 49.64 to 52.51 | +0.04 |
| S5a | Different question | Full timestamp, previous logic | Late vs on time | 95,824 | 12,272 | +42.98 | 41.61 to 44.34 | −8.06 |
| S5b | Different question | 2 or more days late | Late vs on time | 95,824 | 12,272 | +57.27 | 55.75 to 58.79 | +6.23 |
| S8a | Different question | Excluding peak months | Late vs on time | 75,132 | 8,341 | +47.76 | 45.95 to 49.56 | −3.28 |
| S8b | Different question | Excluding 2016 | Late vs on time | 95,560 | 12,228 | +51.01 | 49.58 to 52.44 | −0.03 |
| S8c | Different question | Excluding purchases from July 2018 | Late vs on time | 83,376 | 11,076 | +52.47 | 50.97 to 53.98 | +1.43 |
| S11a | Structure | First item's category | Late vs on time | 95,824 | 12,272 | +51.04 | 49.61 to 52.47 | +0.00 |
| S11b | Structure | Excluding unknown category | Late vs on time | 94,475 | 12,049 | +50.97 | 49.51 to 52.42 | −0.07 |
| S12a | Review | Unreviewed: late all low, on time none low | Late vs on time | 96,470 | 12,425 | +52.00 | 50.59 to 53.41 | +0.96 |
| S12b | Review | Unreviewed: late none low, on time all low | Late vs on time | 96,470 | 12,765 | +49.09 | 47.67 to 50.51 | −1.95 |
| S15 | Timestamp | Excluding deliveries over 60 days | Late vs on time | 95,541 | 12,086 | +50.96 | 49.49 to 52.43 | −0.08 |
| S16 | Review | Excluding reviews created before the purchase date | Late vs on time | 95,821 | 12,270 | +51.04 | 49.61 to 52.47 | +0.00 |
| S13a | Structure | Linear probability model | Late vs on time | 95,824 | 12,272 | +52.49 | 51.13 to 53.85 | +1.45 |
| S13b | Structure | Heteroskedasticity-robust errors, not clustered | Late vs on time | 95,824 | 12,272 | +51.04 | 49.76 to 52.32 | +0.00 |
| S6a | Different question | 1 star only | Late vs on time | 95,824 | 9,351 | +44.67 | 43.24 to 46.10 | −6.37 |
| S6b | Different question | 1-3 stars | Late vs on time | 95,824 | 20,188 | +54.17 | 52.74 to 55.61 | +3.14 |
| S6c | Different question | Mean score difference, in stars | Late vs on time | 95,824 | 12,272 | −1.98 | −2.03 to −1.93 | — |
| X3a | Exploratory | A2 with late orders answered after arrival only | Late vs on time | 91,351 | 8,660 | +10.01 | 8.40 to 11.62 | −41.03 |
| X3b | Exploratory | A2 with late orders answered before arrival only | Late vs on time | 93,916 | 11,901 | +69.98 | 68.53 to 71.42 | +18.94 |
| X3c | Exploratory | A2 with all reviews answered after arrival | Late vs on time | 91,171 | 8,629 | +10.04 | 8.43 to 11.65 | −41.00 |

### A3. Longer delays and low ratings

| Check | Type | Alternative | Comparison | Orders | Events | Estimate | 95% interval | Change |
|---|---|---|---|---:|---:|---:|---:|---:|
| S0 | Baseline | Primary specification with delta-method interval | 15+ vs 1-3 days | 6,381 | 3,983 | +42.10 | 38.77 to 45.43 | — |
| S0 | Baseline | Primary specification with delta-method interval | 4-7 vs 1-3 days | 6,381 | 3,983 | +34.72 | 31.66 to 37.77 | — |
| S0 | Baseline | Primary specification with delta-method interval | 8-14 vs 4-7 days | 6,381 | 3,983 | +11.18 | 8.14 to 14.22 | — |
| S0 | Baseline | Primary specification with delta-method interval | 15+ vs 8-14 days | 6,381 | 3,983 | −3.80 | −7.16 to −0.44 | — |
| S1a | Review | Earliest review | 15+ vs 1-3 days | 6,381 | 3,979 | +41.91 | 38.60 to 45.23 | −0.19 |
| S1a | Review | Earliest review | 4-7 vs 1-3 days | 6,381 | 3,979 | +34.50 | 31.43 to 37.56 | −0.22 |
| S1a | Review | Earliest review | 8-14 vs 4-7 days | 6,381 | 3,979 | +11.35 | 8.30 to 14.40 | +0.17 |
| S1a | Review | Earliest review | 15+ vs 8-14 days | 6,381 | 3,979 | −3.93 | −7.28 to −0.59 | −0.13 |
| S1b | Review | Excluding orders with several reviews | 15+ vs 1-3 days | 6,353 | 3,962 | +42.01 | 38.65 to 45.37 | −0.09 |
| S1b | Review | Excluding orders with several reviews | 4-7 vs 1-3 days | 6,353 | 3,962 | +34.55 | 31.46 to 37.63 | −0.17 |
| S1b | Review | Excluding orders with several reviews | 8-14 vs 4-7 days | 6,353 | 3,962 | +11.46 | 8.43 to 14.49 | +0.28 |
| S1b | Review | Excluding orders with several reviews | 15+ vs 8-14 days | 6,353 | 3,962 | −4.00 | −7.38 to −0.62 | −0.20 |
| S2 | Review | Excluding repeated review IDs | 15+ vs 1-3 days | 6,301 | 3,929 | +42.41 | 39.07 to 45.76 | +0.31 |
| S2 | Review | Excluding repeated review IDs | 4-7 vs 1-3 days | 6,301 | 3,929 | +34.74 | 31.66 to 37.82 | +0.03 |
| S2 | Review | Excluding repeated review IDs | 8-14 vs 4-7 days | 6,301 | 3,929 | +11.55 | 8.51 to 14.60 | +0.37 |
| S2 | Review | Excluding repeated review IDs | 15+ vs 8-14 days | 6,301 | 3,929 | −3.88 | −7.28 to −0.49 | −0.08 |
| S4b | Timestamp | Affected orders excluded | 15+ vs 1-3 days | 6,378 | 3,983 | +42.02 | 38.70 to 45.35 | −0.08 |
| S4b | Timestamp | Affected orders excluded | 4-7 vs 1-3 days | 6,378 | 3,983 | +34.65 | 31.61 to 37.70 | −0.06 |
| S4b | Timestamp | Affected orders excluded | 8-14 vs 4-7 days | 6,378 | 3,983 | +11.18 | 8.13 to 14.21 | −0.01 |
| S4b | Timestamp | Affected orders excluded | 15+ vs 8-14 days | 6,378 | 3,983 | −3.81 | −7.17 to −0.44 | −0.01 |
| S5b | Different question | 2 or more days late | 15+ vs 2-3 days | 5,561 | 3,822 | +32.27 | 28.20 to 36.35 | −9.83 |
| S5b | Different question | 2 or more days late | 4-7 vs 2-3 days | 5,561 | 3,822 | +24.91 | 21.04 to 28.77 | −9.81 |
| S5b | Different question | 2 or more days late | 8-14 vs 4-7 days | 5,561 | 3,822 | +11.19 | 8.19 to 14.18 | +0.01 |
| S5b | Different question | 2 or more days late | 15+ vs 8-14 days | 5,561 | 3,822 | −3.82 | −7.14 to −0.50 | −0.02 |
| S8a | Different question | Excluding peak months | 15+ vs 1-3 days | 3,286 | 1,870 | +41.09 | 36.48 to 45.70 | −1.01 |
| S8a | Different question | Excluding peak months | 4-7 vs 1-3 days | 3,286 | 1,870 | +34.27 | 30.39 to 38.16 | −0.44 |
| S8a | Different question | Excluding peak months | 8-14 vs 4-7 days | 3,286 | 1,870 | +10.49 | 6.14 to 14.84 | −0.69 |
| S8a | Different question | Excluding peak months | 15+ vs 8-14 days | 3,286 | 1,870 | −3.68 | −8.84 to 1.48 | +0.12 |
| S8b | Different question | Excluding 2016 | 15+ vs 1-3 days | 6,378 | 3,981 | +42.05 | 38.71 to 45.38 | −0.05 |
| S8b | Different question | Excluding 2016 | 4-7 vs 1-3 days | 6,378 | 3,981 | +34.70 | 31.64 to 37.75 | −0.02 |
| S8b | Different question | Excluding 2016 | 8-14 vs 4-7 days | 6,378 | 3,981 | +11.18 | 8.14 to 14.22 | +0.00 |
| S8b | Different question | Excluding 2016 | 15+ vs 8-14 days | 6,378 | 3,981 | −3.83 | −7.20 to −0.47 | −0.03 |
| S8c | Different question | Excluding purchases from July 2018 | 15+ vs 1-3 days | 5,796 | 3,719 | +41.81 | 38.35 to 45.27 | −0.29 |
| S8c | Different question | Excluding purchases from July 2018 | 4-7 vs 1-3 days | 5,796 | 3,719 | +33.25 | 30.04 to 36.46 | −1.47 |
| S8c | Different question | Excluding purchases from July 2018 | 8-14 vs 4-7 days | 5,796 | 3,719 | +12.25 | 9.16 to 15.34 | +1.07 |
| S8c | Different question | Excluding purchases from July 2018 | 15+ vs 8-14 days | 5,796 | 3,719 | −3.69 | −7.08 to −0.31 | +0.11 |
| S12c | Review | Unreviewed late orders all low | 15+ vs 1-3 days | 6,534 | 4,136 | +42.28 | 39.02 to 45.55 | +0.18 |
| S12c | Review | Unreviewed late orders all low | 4-7 vs 1-3 days | 6,534 | 4,136 | +34.90 | 31.85 to 37.95 | +0.18 |
| S12c | Review | Unreviewed late orders all low | 8-14 vs 4-7 days | 6,534 | 4,136 | +10.74 | 7.74 to 13.73 | −0.45 |
| S12c | Review | Unreviewed late orders all low | 15+ vs 8-14 days | 6,534 | 4,136 | −3.35 | −6.62 to −0.08 | +0.45 |
| S12d | Review | Unreviewed late orders none low | 15+ vs 1-3 days | 6,534 | 3,983 | +39.85 | 36.47 to 43.23 | −2.25 |
| S12d | Review | Unreviewed late orders none low | 4-7 vs 1-3 days | 6,534 | 3,983 | +33.10 | 30.11 to 36.10 | −1.61 |
| S12d | Review | Unreviewed late orders none low | 8-14 vs 4-7 days | 6,534 | 3,983 | +11.47 | 8.48 to 14.45 | +0.28 |
| S12d | Review | Unreviewed late orders none low | 15+ vs 8-14 days | 6,534 | 3,983 | −4.72 | −8.14 to −1.30 | −0.92 |
| S15 | Timestamp | Excluding deliveries over 60 days | 15+ vs 1-3 days | 6,101 | 3,798 | +45.44 | 42.07 to 48.81 | +3.34 |
| S15 | Timestamp | Excluding deliveries over 60 days | 4-7 vs 1-3 days | 6,101 | 3,798 | +34.64 | 31.59 to 37.69 | −0.07 |
| S15 | Timestamp | Excluding deliveries over 60 days | 8-14 vs 4-7 days | 6,101 | 3,798 | +11.45 | 8.37 to 14.54 | +0.27 |
| S15 | Timestamp | Excluding deliveries over 60 days | 15+ vs 8-14 days | 6,101 | 3,798 | −0.66 | −4.06 to 2.75 | +3.14 |
| S16 | Review | Excluding reviews created before the purchase date | 15+ vs 1-3 days | 6,381 | 3,983 | +42.10 | 38.77 to 45.43 | +0.00 |
| S16 | Review | Excluding reviews created before the purchase date | 4-7 vs 1-3 days | 6,381 | 3,983 | +34.72 | 31.66 to 37.77 | +0.00 |
| S16 | Review | Excluding reviews created before the purchase date | 8-14 vs 4-7 days | 6,381 | 3,983 | +11.18 | 8.14 to 14.22 | +0.00 |
| S16 | Review | Excluding reviews created before the purchase date | 15+ vs 8-14 days | 6,381 | 3,983 | −3.80 | −7.16 to −0.44 | +0.00 |
| S13a | Structure | Linear probability model | 15+ vs 1-3 days | 6,381 | 3,983 | +42.09 | 38.84 to 45.34 | −0.01 |
| S13a | Structure | Linear probability model | 4-7 vs 1-3 days | 6,381 | 3,983 | +34.80 | 31.75 to 37.84 | +0.08 |
| S13a | Structure | Linear probability model | 8-14 vs 4-7 days | 6,381 | 3,983 | +11.14 | 8.07 to 14.21 | −0.04 |
| S13a | Structure | Linear probability model | 15+ vs 8-14 days | 6,381 | 3,983 | −3.85 | −7.08 to −0.62 | −0.05 |
| S13b | Structure | Heteroskedasticity-robust errors, not clustered | 15+ vs 1-3 days | 6,381 | 3,983 | +42.10 | 38.77 to 45.43 | +0.00 |
| S13b | Structure | Heteroskedasticity-robust errors, not clustered | 4-7 vs 1-3 days | 6,381 | 3,983 | +34.72 | 31.67 to 37.77 | +0.00 |
| S13b | Structure | Heteroskedasticity-robust errors, not clustered | 8-14 vs 4-7 days | 6,381 | 3,983 | +11.18 | 8.18 to 14.19 | +0.00 |
| S13b | Structure | Heteroskedasticity-robust errors, not clustered | 15+ vs 8-14 days | 6,381 | 3,983 | −3.80 | −6.96 to −0.64 | +0.00 |
| S6a | Different question | 1 star only | 15+ vs 1-3 days | 6,381 | 3,431 | +39.53 | 36.11 to 42.95 | −2.57 |
| S6a | Different question | 1 star only | 4-7 vs 1-3 days | 6,381 | 3,431 | +32.92 | 29.94 to 35.89 | −1.80 |
| S6a | Different question | 1 star only | 8-14 vs 4-7 days | 6,381 | 3,431 | +10.48 | 7.17 to 13.80 | −0.70 |
| S6a | Different question | 1 star only | 15+ vs 8-14 days | 6,381 | 3,431 | −3.87 | −7.57 to −0.17 | −0.07 |
| S6b | Different question | 1-3 stars | 15+ vs 1-3 days | 6,381 | 4,677 | +37.09 | 34.06 to 40.12 | −5.01 |
| S6b | Different question | 1-3 stars | 4-7 vs 1-3 days | 6,381 | 4,677 | +29.36 | 26.27 to 32.44 | −5.36 |
| S6b | Different question | 1-3 stars | 8-14 vs 4-7 days | 6,381 | 4,677 | +10.49 | 7.86 to 13.11 | −0.70 |
| S6b | Different question | 1-3 stars | 15+ vs 8-14 days | 6,381 | 4,677 | −2.75 | −5.33 to −0.17 | +1.05 |
| S6c | Different question | Mean score difference, in stars | 15+ vs 1-3 days | 6,381 | 3,983 | −1.42 | −1.52 to −1.32 | — |
| S6c | Different question | Mean score difference, in stars | 4-7 vs 1-3 days | 6,381 | 3,983 | −1.16 | −1.26 to −1.06 | — |
| S6c | Different question | Mean score difference, in stars | 8-14 vs 4-7 days | 6,381 | 3,983 | −0.38 | −0.48 to −0.28 | — |
| S6c | Different question | Mean score difference, in stars | 15+ vs 8-14 days | 6,381 | 3,983 | +0.12 | 0.02 to 0.22 | — |
| X3d | Exploratory | A3 with reviews answered before arrival; multi-seller term removed because of separation | 15+ vs 1-3 days | 4,473 | 3,612 | −2.42 | −7.11 to 2.28 | −44.52 |
| X3d | Exploratory | A3 with reviews answered before arrival; multi-seller term removed because of separation | 4-7 vs 1-3 days | 4,473 | 3,612 | +3.02 | −1.37 to 7.41 | −31.70 |
| X3d | Exploratory | A3 with reviews answered before arrival; multi-seller term removed because of separation | 8-14 vs 4-7 days | 4,473 | 3,612 | −0.16 | −2.76 to 2.44 | −11.35 |
| X3d | Exploratory | A3 with reviews answered before arrival; multi-seller term removed because of separation | 15+ vs 8-14 days | 4,473 | 3,612 | −5.27 | −8.55 to −1.99 | −1.47 |
| X3e | Exploratory | A3 with reviews answered after arrival; 15+ days has under 30 reviews; category removed because of too few events | 8-14 vs 1-3 days | 1,889 | 363 | +4.84 | −5.04 to 14.72 | — |
| X3e | Exploratory | A3 with reviews answered after arrival; 15+ days has under 30 reviews; category removed because of too few events | 4-7 vs 1-3 days | 1,889 | 363 | +1.59 | −2.98 to 6.17 | −33.12 |
| X3e | Exploratory | A3 with reviews answered after arrival; 15+ days has under 30 reviews; category removed because of too few events | 8-14 vs 4-7 days | 1,889 | 363 | +3.25 | −7.72 to 14.22 | −7.93 |

### A4. Distance and late delivery

| Check | Type | Alternative | Comparison | Orders | Events | Estimate | 95% interval | Change |
|---|---|---|---|---:|---:|---:|---:|---:|
| S0 | Baseline | Primary specification with delta-method interval | 600-1,000 vs 0-100 km | 94,724 | 6,476 | +0.59 | −0.42 to 1.60 | — |
| S0 | Baseline | Primary specification with delta-method interval | 2,000+ vs 0-100 km | 94,724 | 6,476 | +2.52 | 0.22 to 4.82 | — |
| S3a | Timestamp | All flagged orders excluded | 600-1,000 vs 0-100 km | 94,558 | 6,473 | +0.59 | −0.42 to 1.60 | +0.00 |
| S3a | Timestamp | All flagged orders excluded | 2,000+ vs 0-100 km | 94,558 | 6,473 | +2.52 | 0.21 to 4.82 | −0.00 |
| S3b | Timestamp | Only delivery-before-carrier excluded | 600-1,000 vs 0-100 km | 94,720 | 6,476 | +0.59 | −0.42 to 1.60 | +0.00 |
| S3b | Timestamp | Only delivery-before-carrier excluded | 2,000+ vs 0-100 km | 94,720 | 6,476 | +2.52 | 0.22 to 4.82 | +0.00 |
| S3c | Timestamp | Only carrier-before-purchase excluded | 600-1,000 vs 0-100 km | 94,563 | 6,474 | +0.59 | −0.42 to 1.61 | +0.00 |
| S3c | Timestamp | Only carrier-before-purchase excluded | 2,000+ vs 0-100 km | 94,563 | 6,474 | +2.52 | 0.22 to 4.82 | +0.00 |
| S4b | Timestamp | Affected orders excluded | 600-1,000 vs 0-100 km | 94,700 | 6,473 | +0.58 | −0.43 to 1.60 | −0.01 |
| S4b | Timestamp | Affected orders excluded | 2,000+ vs 0-100 km | 94,700 | 6,473 | +2.52 | 0.21 to 4.82 | −0.00 |
| S5a | Different question | Full timestamp, previous logic | 600-1,000 vs 0-100 km | 94,724 | 7,757 | −0.32 | −1.52 to 0.87 | −0.92 |
| S5a | Different question | Full timestamp, previous logic | 2,000+ vs 0-100 km | 94,724 | 7,757 | +1.88 | −0.81 to 4.57 | −0.64 |
| S5b | Different question | 2 or more days late | 600-1,000 vs 0-100 km | 94,724 | 5,656 | +1.05 | 0.13 to 1.98 | +0.46 |
| S5b | Different question | 2 or more days late | 2,000+ vs 0-100 km | 94,724 | 5,656 | +2.92 | 0.70 to 5.15 | +0.40 |
| S7 | Structure | Multi-seller orders assigned to primary seller | 600-1,000 vs 0-100 km | 95,993 | 6,489 | +0.59 | −0.41 to 1.59 | +0.00 |
| S7 | Structure | Multi-seller orders assigned to primary seller | 2,000+ vs 0-100 km | 95,993 | 6,489 | +2.49 | 0.20 to 4.77 | −0.03 |
| S8a | Different question | Excluding peak months | 600-1,000 vs 0-100 km | 74,220 | 3,341 | −1.34 | −2.11 to −0.56 | −1.93 |
| S8a | Different question | Excluding peak months | 2,000+ vs 0-100 km | 74,220 | 3,341 | +0.48 | −1.64 to 2.59 | −2.04 |
| S8b | Different question | Excluding 2016 | 600-1,000 vs 0-100 km | 94,460 | 6,473 | +0.58 | −0.43 to 1.59 | −0.01 |
| S8b | Different question | Excluding 2016 | 2,000+ vs 0-100 km | 94,460 | 6,473 | +2.52 | 0.21 to 4.83 | −0.00 |
| S8c | Different question | Excluding purchases from July 2018 | 600-1,000 vs 0-100 km | 82,476 | 5,882 | +2.15 | 1.13 to 3.16 | +1.56 |
| S8c | Different question | Excluding purchases from July 2018 | 2,000+ vs 0-100 km | 82,476 | 5,882 | +4.16 | 2.06 to 6.25 | +1.64 |
| S10a | Structure | Mean ZIP position | 600-1,000 vs 0-100 km | 94,724 | 6,476 | +0.58 | −0.42 to 1.59 | −0.01 |
| S10a | Structure | Mean ZIP position | 2,000+ vs 0-100 km | 94,724 | 6,476 | +2.55 | 0.24 to 4.85 | +0.03 |
| S10b | Structure | Excluding distances above the 99th percentile (2,483 km) | 600-1,000 vs 0-100 km | 93,776 | 6,382 | +0.58 | −0.43 to 1.59 | −0.02 |
| S10b | Structure | Excluding distances above the 99th percentile (2,483 km) | 2,000+ vs 0-100 km | 93,776 | 6,382 | +2.79 | 0.53 to 5.04 | +0.27 |
| S15 | Timestamp | Excluding deliveries over 60 days | 600-1,000 vs 0-100 km | 94,429 | 6,185 | +0.43 | −0.55 to 1.40 | −0.16 |
| S15 | Timestamp | Excluding deliveries over 60 days | 2,000+ vs 0-100 km | 94,429 | 6,185 | +1.99 | −0.31 to 4.30 | −0.53 |
| S13a | Structure | Linear probability model | 600-1,000 vs 0-100 km | 94,724 | 6,476 | +0.39 | −0.56 to 1.34 | −0.20 |
| S13a | Structure | Linear probability model | 2,000+ vs 0-100 km | 94,724 | 6,476 | +2.78 | 0.38 to 5.19 | +0.26 |
| S13b | Structure | Heteroskedasticity-robust errors, not clustered | 600-1,000 vs 0-100 km | 94,724 | 6,476 | +0.59 | −0.01 to 1.20 | +0.00 |
| S13b | Structure | Heteroskedasticity-robust errors, not clustered | 2,000+ vs 0-100 km | 94,724 | 6,476 | +2.52 | 1.34 to 3.70 | +0.00 |

### A5. Freight cost and late delivery

| Check | Type | Alternative | Comparison | Orders | Events | Estimate | 95% interval | Change |
|---|---|---|---|---:|---:|---:|---:|---:|
| S0 | Baseline | Primary specification with delta-method interval | Highest vs lowest quartile | 94,724 | 6,476 | +2.16 | 1.31 to 3.02 | — |
| S3a | Timestamp | All flagged orders excluded | Highest vs lowest quartile | 94,558 | 6,473 | +2.18 | 1.32 to 3.04 | +0.01 |
| S3b | Timestamp | Only delivery-before-carrier excluded | Highest vs lowest quartile | 94,720 | 6,476 | +2.16 | 1.31 to 3.02 | +0.00 |
| S3c | Timestamp | Only carrier-before-purchase excluded | Highest vs lowest quartile | 94,563 | 6,474 | +2.18 | 1.32 to 3.04 | +0.01 |
| S4b | Timestamp | Affected orders excluded | Highest vs lowest quartile | 94,700 | 6,473 | +2.16 | 1.30 to 3.02 | −0.01 |
| S5a | Different question | Full timestamp, previous logic | Highest vs lowest quartile | 94,724 | 7,757 | +2.06 | 1.12 to 3.01 | −0.10 |
| S5b | Different question | 2 or more days late | Highest vs lowest quartile | 94,724 | 5,656 | +2.00 | 1.23 to 2.78 | −0.16 |
| S7 | Structure | Multi-seller orders assigned to primary seller | Highest vs lowest quartile | 95,993 | 6,489 | +2.27 | 1.44 to 3.10 | +0.11 |
| S8a | Different question | Excluding peak months | Highest vs lowest quartile | 74,220 | 3,341 | +0.88 | 0.17 to 1.59 | −1.28 |
| S8b | Different question | Excluding 2016 | Highest vs lowest quartile | 94,460 | 6,473 | +2.20 | 1.34 to 3.05 | +0.03 |
| S8c | Different question | Excluding purchases from July 2018 | Highest vs lowest quartile | 82,476 | 5,882 | +2.91 | 2.01 to 3.81 | +0.74 |
| S10a | Structure | Mean ZIP position | Highest vs lowest quartile | 94,724 | 6,476 | +2.17 | 1.31 to 3.02 | +0.00 |
| S10b | Structure | Excluding distances above the 99th percentile (2,483 km) | Highest vs lowest quartile | 93,776 | 6,382 | +2.12 | 1.25 to 2.98 | −0.05 |
| S15 | Timestamp | Excluding deliveries over 60 days | Highest vs lowest quartile | 94,429 | 6,185 | +2.04 | 1.22 to 2.86 | −0.13 |
| S13a | Structure | Linear probability model | Highest vs lowest quartile | 94,724 | 6,476 | +2.01 | 1.10 to 2.92 | −0.15 |
| S13b | Structure | Heteroskedasticity-robust errors, not clustered | Highest vs lowest quartile | 94,724 | 6,476 | +2.16 | 1.53 to 2.80 | +0.00 |
| X2 | Exploratory | Customer state added, labelled exploratory. Doesn't change the A5 definition or result | Highest vs lowest quartile | 94,724 | 6,476 | +0.97 | −0.01 to 1.94 | −1.20 |
| X2 | Exploratory | Customer state added: step between quartiles | Q2 vs lowest | 94,724 | 6,476 | +1.01 | 0.33 to 1.70 | — |
| X2 | Exploratory | Customer state added: step between quartiles | Q3 vs Q2 | 94,724 | 6,476 | −0.03 | −0.57 to 0.50 | — |
| X2 | Exploratory | Customer state added: step between quartiles | Highest vs Q3 | 94,724 | 6,476 | −0.01 | −0.66 to 0.63 | — |

### A6. Seller concentration

| Check | Type | Alternative | Comparison | Orders | Events | Estimate | 95% interval | Change |
|---|---|---|---|---:|---:|---:|---:|---:|
| S0 | Baseline | Primary specification | Top 10% late share minus order share | 56,579 | 3,909 | +6.97 | 2.45 to 9.98 | — |
| S3a | Timestamp | All flagged orders excluded | Top 10% late share minus order share | 56,303 | 3,894 | +6.32 | 2.05 to 10.19 | −0.64 |
| S3b | Timestamp | Only delivery-before-carrier excluded | Top 10% late share minus order share | 56,575 | 3,909 | +6.97 | 2.89 to 9.95 | +0.00 |
| S3c | Timestamp | Only carrier-before-purchase excluded | Top 10% late share minus order share | 56,307 | 3,894 | +6.32 | 2.76 to 9.89 | −0.65 |
| S4b | Timestamp | Affected orders excluded | Top 10% late share minus order share | 56,568 | 3,906 | +6.97 | 2.72 to 10.39 | +0.01 |
| S5a | Different question | Full timestamp, previous logic | Top 10% late share minus order share | 56,579 | 4,631 | +6.32 | 2.42 to 10.00 | −0.65 |
| S5b | Different question | 2 or more days late | Top 10% late share minus order share | 56,579 | 3,427 | +7.41 | 2.34 to 10.60 | +0.44 |
| S7 | Structure | Multi-seller orders assigned to primary seller | Top 10% late share minus order share | 57,687 | 3,941 | +7.05 | 2.84 to 10.29 | +0.08 |
| S8a | Different question | Excluding peak months | Top 10% late share minus order share | 39,892 | 1,737 | +3.40 | −0.49 to 8.15 | −3.57 |
| S8b | Different question | Excluding 2016 | Top 10% late share minus order share | 56,482 | 3,908 | +6.97 | 2.29 to 10.27 | +0.00 |
| S8c | Different question | Excluding purchases from July 2018 | Top 10% late share minus order share | 49,470 | 3,572 | +5.83 | 1.85 to 10.21 | −1.14 |
| S15 | Timestamp | Excluding deliveries over 60 days | Top 10% late share minus order share | 56,419 | 3,749 | +7.14 | 2.74 to 10.61 | +0.17 |

### A7. Category differences

| Check | Type | Alternative | Comparison | Orders | Events | Estimate | 95% interval | Change |
|---|---|---|---|---:|---:|---:|---:|---:|
| S0 | Baseline | Primary specification with delta-method interval | Spread: baby vs luggage_accessories | 83,514 | 5,760 | +3.69 | 1.58 to 5.80 | — |
| S3a | Timestamp | All flagged orders excluded | Spread: baby vs luggage_accessories | 83,366 | 5,757 | +3.68 | 1.57 to 5.80 | −0.01 |
| S3b | Timestamp | Only delivery-before-carrier excluded | Spread: baby vs luggage_accessories | 83,510 | 5,760 | +3.69 | 1.58 to 5.80 | +0.00 |
| S3c | Timestamp | Only carrier-before-purchase excluded | Spread: baby vs luggage_accessories | 83,371 | 5,758 | +3.68 | 1.57 to 5.79 | −0.01 |
| S4b | Timestamp | Affected orders excluded | Spread: baby vs luggage_accessories | 83,493 | 5,758 | +3.69 | 1.58 to 5.80 | +0.00 |
| S5a | Different question | Full timestamp, previous logic | Spread: baby vs luggage_accessories | 83,514 | 6,870 | +3.46 | 0.98 to 5.94 | −0.23 |
| S5b | Different question | 2 or more days late | Spread: baby vs luggage_accessories | 83,514 | 5,035 | +3.35 | 1.37 to 5.33 | −0.34 |
| S8a | Different question | Excluding peak months | Spread: office_furniture vs fashion_bags_accessories | 65,218 | 2,935 | +2.93 | 0.76 to 5.10 | — |
| S8b | Different question | Excluding 2016 | Spread: baby vs luggage_accessories | 83,276 | 5,757 | +3.70 | 1.58 to 5.82 | +0.01 |
| S8c | Different question | Excluding purchases from July 2018 | Spread: baby vs luggage_accessories | 73,039 | 5,261 | +3.56 | 1.17 to 5.95 | −0.13 |
| S11a | Structure | First item's category | Spread: baby vs luggage_accessories | 83,515 | 5,761 | +3.75 | 1.61 to 5.88 | +0.06 |
| S11b | Structure | Excluding unknown category | Spread: baby vs luggage_accessories | 83,514 | 5,760 | +3.69 | 1.58 to 5.80 | +0.00 |
| S15 | Timestamp | Excluding deliveries over 60 days | Spread: baby vs luggage_accessories | 83,246 | 5,496 | +3.23 | 1.11 to 5.35 | −0.46 |
| S13a | Structure | Linear probability model | Spread: baby vs luggage_accessories | 83,514 | 5,760 | +3.25 | Not estimated | −0.44 |
| S13b | Structure | Heteroskedasticity-robust errors, not clustered | Spread: baby vs luggage_accessories | 83,514 | 5,760 | +3.69 | 1.95 to 5.43 | +0.00 |

### B1. Peak months (exploratory)

| Check | Type | Alternative | Comparison | Orders | Events | Estimate | 95% interval | Change |
|---|---|---|---|---:|---:|---:|---:|---:|
| S0 | Baseline | Primary specification | Peak vs other months late rate | 96,470 | 6,534 | +10.68 | Not available | — |
| S3a | Timestamp | All flagged orders excluded | Peak vs other months late rate | 96,281 | 6,531 | +10.68 | Not available | −0.01 |
| S4b | Timestamp | Affected orders excluded | Peak vs other months late rate | 96,446 | 6,531 | +10.69 | Not available | +0.00 |
| S5a | Different question | Full timestamp, previous logic | Peak vs other months late rate | 96,470 | 7,826 | +11.60 | Not available | +0.92 |
| S5b | Different question | 2 or more days late | Peak vs other months late rate | 96,470 | 5,709 | +9.76 | Not available | −0.92 |
| S8b | Different question | Excluding 2016 | Peak vs other months late rate | 96,203 | 6,531 | +10.67 | Not available | −0.01 |
| S8c | Different question | Excluding purchases from July 2018 | Peak vs other months late rate | 83,963 | 5,933 | +10.75 | Not available | +0.07 |
| S15 | Timestamp | Excluding deliveries over 60 days | Peak vs other months late rate | 96,172 | 6,240 | +10.44 | Not available | −0.25 |
| S3b | Timestamp | Only delivery-before-carrier excluded | Peak vs other months late rate | 96,447 | 6534 | +10.68 | Not available | — |
| S3c | Timestamp | Only carrier-before-purchase excluded | Peak vs other months late rate | 96,305 | 6532 | +10.68 | Not available | — |

### B2. RJ in peak months (exploratory)

| Check | Type | Alternative | Comparison | Orders | Events | Estimate | 95% interval | Change |
|---|---|---|---|---:|---:|---:|---:|---:|
| S0 | Baseline | Primary specification with delta-method interval | Difference between the two gaps | 51,984 | 3,296 | +20.42 | 16.84 to 24.01 | — |
| S0 | Baseline | Primary specification with delta-method interval | Gap in peak months | 51,984 | 3,296 | +23.46 | 19.23 to 27.70 | — |
| S0 | Baseline | Primary specification with delta-method interval | Gap in other months | 51,984 | 3,296 | +3.04 | 1.98 to 4.11 | — |
| S3a | Timestamp | All flagged orders excluded | Difference between the two gaps | 51,912 | 3,294 | +20.41 | 16.83 to 24.00 | −0.01 |
| S3a | Timestamp | All flagged orders excluded | Gap in peak months | 51,912 | 3,294 | +23.47 | 19.23 to 27.71 | +0.00 |
| S3a | Timestamp | All flagged orders excluded | Gap in other months | 51,912 | 3,294 | +3.06 | 1.99 to 4.12 | +0.02 |
| S3b | Timestamp | Only delivery-before-carrier excluded | Difference between the two gaps | 51,981 | 3,296 | +20.42 | 16.84 to 24.01 | +0.00 |
| S3b | Timestamp | Only delivery-before-carrier excluded | Gap in peak months | 51,981 | 3,296 | +23.46 | 19.23 to 27.70 | +0.00 |
| S3b | Timestamp | Only delivery-before-carrier excluded | Gap in other months | 51,981 | 3,296 | +3.04 | 1.98 to 4.11 | +0.00 |
| S3c | Timestamp | Only carrier-before-purchase excluded | Difference between the two gaps | 51,916 | 3,295 | +20.40 | 16.82 to 23.98 | −0.02 |
| S3c | Timestamp | Only carrier-before-purchase excluded | Gap in peak months | 51,916 | 3,295 | +23.45 | 19.21 to 27.68 | −0.02 |
| S3c | Timestamp | Only carrier-before-purchase excluded | Gap in other months | 51,916 | 3,295 | +3.04 | 1.98 to 4.11 | +0.00 |
| S5a | Different question | Full timestamp, previous logic | Difference between the two gaps | 51,984 | 4,028 | +21.69 | 17.92 to 25.45 | +1.26 |
| S5a | Different question | Full timestamp, previous logic | Gap in peak months | 51,984 | 4,028 | +25.11 | 20.55 to 29.68 | +1.65 |
| S5a | Different question | Full timestamp, previous logic | Gap in other months | 51,984 | 4,028 | +3.43 | 2.15 to 4.71 | +0.39 |
| S5b | Different question | 2 or more days late | Difference between the two gaps | 51,984 | 2,869 | +19.11 | 15.63 to 22.58 | −1.32 |
| S5b | Different question | 2 or more days late | Gap in peak months | 51,984 | 2,869 | +21.76 | 17.80 to 25.72 | −1.70 |
| S5b | Different question | 2 or more days late | Gap in other months | 51,984 | 2,869 | +2.65 | 1.76 to 3.55 | −0.39 |
| S8b | Different question | Excluding 2016 | Difference between the two gaps | 51,851 | 3,293 | +20.43 | 16.84 to 24.02 | +0.01 |
| S8b | Different question | Excluding 2016 | Gap in peak months | 51,851 | 3,293 | +23.50 | 19.26 to 27.75 | +0.04 |
| S8b | Different question | Excluding 2016 | Gap in other months | 51,851 | 3,293 | +3.08 | 2.01 to 4.15 | +0.04 |
| S8c | Different question | Excluding purchases from July 2018 | Difference between the two gaps | 44,819 | 2,854 | +18.11 | 14.71 to 21.50 | −2.31 |
| S8c | Different question | Excluding purchases from July 2018 | Gap in peak months | 44,819 | 2,854 | +21.54 | 17.53 to 25.55 | −1.92 |
| S8c | Different question | Excluding purchases from July 2018 | Gap in other months | 44,819 | 2,854 | +3.43 | 2.40 to 4.46 | +0.39 |
| S15 | Timestamp | Excluding deliveries over 60 days | Difference between the two gaps | 51,836 | 3,148 | +19.77 | 16.20 to 23.33 | −0.65 |
| S15 | Timestamp | Excluding deliveries over 60 days | Gap in peak months | 51,836 | 3,148 | +22.55 | 18.37 to 26.74 | −0.91 |
| S15 | Timestamp | Excluding deliveries over 60 days | Gap in other months | 51,836 | 3,148 | +2.78 | 1.76 to 3.81 | −0.26 |
| S13a | Structure | Linear probability model | Difference between the two gaps | 51,984 | 3296 | +20.51 | 17.75 to 23.27 | — |
| S13a | Structure | Linear probability model | Gap in peak months | 51,984 | 3296 | +23.58 | 20.47 to 26.69 | — |
| S13a | Structure | Linear probability model | Gap in other months | 51,984 | 3296 | +3.07 | 2.04 to 4.10 | — |
| S13b | Structure | Heteroskedasticity-robust errors, not clustered | Gap in peak months | 51,984 | 3296 | +23.46 | 21.37 to 25.55 | — |
| S13b | Structure | Heteroskedasticity-robust errors, not clustered | Gap in other months | 51,984 | 3296 | +3.04 | 2.42 to 3.66 | — |

### B3. Answer timing (exploratory)

| Check | Type | Alternative | Comparison | Orders | Events | Estimate | 95% interval | Change |
|---|---|---|---|---:|---:|---:|---:|---:|
| S0 | Baseline | Primary specification with delta-method interval | B3 before | 95,824 | 12,272 | +70.07 | 68.63 to 71.52 | — |
| S0 | Baseline | Primary specification with delta-method interval | B3 after | 95,824 | 12,272 | +9.94 | 8.34 to 11.54 | — |
| S1a | Review | Earliest review | B3 before | 95,824 | 12,262 | +69.95 | 68.48 to 71.42 | −0.12 |
| S1a | Review | Earliest review | B3 after | 95,824 | 12,262 | +9.93 | 8.34 to 11.53 | −0.01 |
| S1b | Review | Excluding orders with several reviews | B3 before | 95,299 | 12,189 | +70.08 | 68.63 to 71.53 | +0.00 |
| S1b | Review | Excluding orders with several reviews | B3 after | 95,299 | 12,189 | +9.91 | 8.31 to 11.52 | −0.03 |
| S2 | Review | Excluding repeated review IDs | B3 before | 94,645 | 12,025 | +70.31 | 68.92 to 71.69 | +0.23 |
| S2 | Review | Excluding repeated review IDs | B3 after | 94,645 | 12,025 | +9.92 | 8.29 to 11.54 | −0.02 |
| S4a | Timestamp | Source CSV timestamps | B3 before | 95,824 | 12,272 | +70.07 | 68.63 to 71.52 | +0.00 |
| S4a | Timestamp | Source CSV timestamps | B3 after | 95,824 | 12,272 | +9.94 | 8.34 to 11.54 | +0.00 |
| S4b | Timestamp | Affected orders excluded | B3 before | 95,800 | 12,269 | +70.08 | 68.64 to 71.52 | +0.01 |
| S4b | Timestamp | Affected orders excluded | B3 after | 95,800 | 12,269 | +9.98 | 8.38 to 11.58 | +0.04 |
| S5a | Different question | Full timestamp, previous logic | B3 before | 95,824 | 12,272 | +70.06 | 68.62 to 71.51 | −0.01 |
| S5a | Different question | Full timestamp, previous logic | B3 after | 95,824 | 12,272 | +7.52 | 6.24 to 8.80 | −2.42 |
| S5b | Different question | 2 or more days late | B3 before | 95,824 | 12,272 | +69.92 | 68.48 to 71.36 | −0.15 |
| S5b | Different question | 2 or more days late | B3 after | 95,824 | 12,272 | +10.55 | 8.29 to 12.80 | +0.61 |
| S8a | Different question | Excluding peak months | B3 before | 75,132 | 8,341 | +67.70 | 65.75 to 69.66 | −2.37 |
| S8a | Different question | Excluding peak months | B3 after | 75,132 | 8,341 | +11.33 | 9.10 to 13.57 | +1.39 |
| S8b | Different question | Excluding 2016 | B3 before | 95,560 | 12,228 | +70.05 | 68.61 to 71.50 | −0.02 |
| S8b | Different question | Excluding 2016 | B3 after | 95,560 | 12,228 | +9.93 | 8.33 to 11.53 | −0.01 |
| S8c | Different question | Excluding purchases from July 2018 | B3 before | 83,376 | 11,076 | +70.52 | 69.08 to 71.96 | +0.45 |
| S8c | Different question | Excluding purchases from July 2018 | B3 after | 83,376 | 11,076 | +10.06 | 8.30 to 11.81 | +0.12 |
| S9 | Different question | Survey creation date instead of answer timestamp | B3 before | 95,824 | 12,272 | +64.19 | 62.74 to 65.64 | −5.88 |
| S9 | Different question | Survey creation date instead of answer timestamp | B3 after, created on or after the delivery date | 95,824 | 12,272 | +15.59 | 13.56 to 17.61 | +5.65 |
| S15 | Timestamp | Excluding deliveries over 60 days | B3 before | 95,541 | 12,086 | +71.10 | 69.65 to 72.55 | +1.03 |
| S15 | Timestamp | Excluding deliveries over 60 days | B3 after | 95,541 | 12,086 | +9.95 | 8.35 to 11.55 | +0.01 |
| S16 | Review | Excluding reviews created before the purchase date | B3 before | 95,821 | 12,270 | +70.08 | 68.63 to 71.52 | +0.00 |
| S16 | Review | Excluding reviews created before the purchase date | B3 after | 95,821 | 12,270 | +9.94 | 8.34 to 11.54 | +0.00 |
| S13a | Structure | Linear probability model | B3 before | 95,824 | 12,272 | +71.08 | 69.71 to 72.46 | +1.01 |
| S13a | Structure | Linear probability model | B3 after | 95,824 | 12,272 | +10.12 | 8.50 to 11.74 | +0.18 |
| S13b | Structure | Heteroskedasticity-robust errors, not clustered | B3 before | 95,824 | 12,272 | +70.07 | 68.80 to 71.35 | +0.00 |
| S13b | Structure | Heteroskedasticity-robust errors, not clustered | B3 after | 95,824 | 12,272 | +9.94 | 8.19 to 11.69 | +0.00 |
| S6a | Different question | 1 star only | B3 before | 95,824 | 9,351 | +62.29 | 60.67 to 63.91 | −7.79 |
| S6a | Different question | 1 star only | B3 after | 95,824 | 9,351 | +6.69 | 5.23 to 8.15 | −3.25 |
| S6b | Different question | 1-3 stars | B3 before | 95,824 | 20,188 | +71.06 | 69.80 to 72.31 | +0.98 |
| S6b | Different question | 1-3 stars | B3 after | 95,824 | 20,188 | +17.61 | 15.55 to 19.66 | +7.67 |
| S6c | Different question | Mean score difference, in stars | B3 before | 95,824 | 12,272 | −2.60 | −2.65 to −2.56 | — |
| S6c | Different question | Mean score difference, in stars | B3 after | 95,824 | 12,272 | −0.56 | −0.62 to −0.50 | — |

### B5. Handover, before 25 April 2018 (exploratory)

| Check | Type | Alternative | Comparison | Orders | Events | Estimate | 95% interval | Change |
|---|---|---|---|---:|---:|---:|---:|---:|
| S0 | Baseline | Primary specification with delta-method interval | Late vs on-time handover, before 25 Apr 2018 | 67,983 | 5,276 | +13.39 | 11.79 to 14.98 | — |
| S3a | Timestamp | All flagged orders excluded | Late vs on-time handover, before 25 Apr 2018 | 67,983 | 5,276 | +13.39 | 11.79 to 14.98 | +0.00 |
| S3b | Timestamp | Only delivery-before-carrier excluded | Late vs on-time handover, before 25 Apr 2018 | 67,984 | 5,276 | +13.39 | 11.79 to 14.98 | +0.00 |
| S3c | Timestamp | Only carrier-before-purchase excluded | Late vs on-time handover, before 25 Apr 2018 | 67,987 | 5,276 | +13.39 | 11.79 to 14.98 | −0.00 |
| S4a | Timestamp | Source CSV timestamps | Late vs on-time handover, before 25 Apr 2018 | 67,983 | 5,276 | +13.39 | 11.79 to 14.98 | +0.00 |
| S4b | Timestamp | Affected orders excluded | Late vs on-time handover, before 25 Apr 2018 | 67,959 | 5,273 | +13.40 | 11.80 to 15.00 | +0.01 |
| S5a | Different question | Full timestamp, previous logic | Late vs on-time handover, before 25 Apr 2018 | 67,983 | 6,082 | +15.47 | 13.70 to 17.23 | +2.08 |
| S5b | Different question | 2 or more days late | Late vs on-time handover, before 25 Apr 2018 | 67,983 | 4,670 | +11.67 | 10.20 to 13.14 | −1.72 |
| S7 | Structure | Multi-seller orders assigned to primary seller | Late vs on-time handover, before 25 Apr 2018 | 68,779 | 5,288 | +13.40 | 11.82 to 14.99 | +0.01 |
| S8a | Different question | Excluding peak months | Late vs on-time handover, before 25 Apr 2018 | 47,482 | 2,143 | +11.77 | 10.23 to 13.31 | −1.62 |
| S8b | Different question | Excluding 2016 | Late vs on-time handover, before 25 Apr 2018 | 67,723 | 5,273 | +13.46 | 11.86 to 15.07 | +0.07 |
| S8c | Different question | Excluding purchases from July 2018 | Late vs on-time handover, before 25 Apr 2018 | 67,983 | 5,276 | +13.39 | 11.79 to 14.98 | +0.00 |
| S15 | Timestamp | Excluding deliveries over 60 days | Late vs on-time handover, before 25 Apr 2018 | 67,711 | 5,008 | +12.97 | 11.40 to 14.54 | −0.42 |
| S14a | Timestamp | Purchase-month split | Late vs on-time handover, before April 2018 purchases | 63,266 | 5,067 | +13.82 | 12.16 to 15.47 | — |
| S14b | Timestamp | Excluding carrier dates within 14 days of the boundary | Late vs on-time handover, before 25 Apr 2018 | 64,865 | 5,147 | +13.72 | 12.10 to 15.34 | +0.33 |
| S13a | Structure | Linear probability model | Late vs on-time handover, before 25 Apr 2018 | 67,983 | 5276 | +13.91 | 12.26 to 15.57 | — |
| S13b | Structure | Heteroskedasticity-robust errors, not clustered | Late vs on-time handover, before 25 Apr 2018 | 67,983 | 5276 | +13.39 | 12.43 to 14.35 | — |

### B5. Handover, from 25 April 2018 (exploratory)

| Check | Type | Alternative | Comparison | Orders | Events | Estimate | 95% interval | Change |
|---|---|---|---|---:|---:|---:|---:|---:|
| S0 | Baseline | Primary specification with delta-method interval | Late vs on-time handover, from 25 Apr 2018 | 26,575 | 1,197 | +18.13 | 15.27 to 20.99 | — |
| S3a | Timestamp | All flagged orders excluded | Late vs on-time handover, from 25 Apr 2018 | 26,575 | 1,197 | +18.13 | 15.27 to 20.99 | +0.00 |
| S3b | Timestamp | Only delivery-before-carrier excluded | Late vs on-time handover, from 25 Apr 2018 | 26,735 | 1,199 | +18.13 | 15.27 to 20.99 | +0.00 |
| S3c | Timestamp | Only carrier-before-purchase excluded | Late vs on-time handover, from 25 Apr 2018 | 26,575 | 1,197 | +18.13 | 15.27 to 20.99 | +0.00 |
| S4a | Timestamp | Source CSV timestamps | Late vs on-time handover, from 25 Apr 2018 | 26,575 | 1,197 | +18.13 | 15.27 to 20.99 | +0.00 |
| S4b | Timestamp | Affected orders excluded | Late vs on-time handover, from 25 Apr 2018 | 26,575 | 1,197 | +18.13 | 15.27 to 20.99 | +0.00 |
| S5a | Different question | Full timestamp, previous logic | Late vs on-time handover, from 25 Apr 2018 | 26,575 | 1,671 | +21.32 | 17.96 to 24.67 | +3.19 |
| S5b | Different question | 2 or more days late | Late vs on-time handover, from 25 Apr 2018 | 26,575 | 984 | +15.38 | 12.62 to 18.14 | −2.75 |
| S7 | Structure | Multi-seller orders assigned to primary seller | Late vs on-time handover, from 25 Apr 2018 | 27,025 | 1,198 | +18.05 | 15.20 to 20.89 | −0.08 |
| S8a | Different question | Excluding peak months | Late vs on-time handover, from 25 Apr 2018 | 26,572 | 1,195 | +18.07 | 15.21 to 20.93 | −0.06 |
| S8b | Different question | Excluding 2016 | Late vs on-time handover, from 25 Apr 2018 | 26,575 | 1,197 | +18.13 | 15.27 to 20.99 | +0.00 |
| S8c | Different question | Excluding purchases from July 2018 | Late vs on-time handover, from 25 Apr 2018 | 14,407 | 604 | +14.13 | 11.15 to 17.10 | −4.00 |
| S15 | Timestamp | Excluding deliveries over 60 days | Late vs on-time handover, from 25 Apr 2018 | 26,552 | 1,174 | +18.08 | 15.21 to 20.96 | −0.05 |
| S14a | Timestamp | Purchase-month split | Late vs on-time handover, from April 2018 purchases | 31,292 | 1,406 | +16.95 | 14.27 to 19.62 | — |
| S14b | Timestamp | Excluding carrier dates within 14 days of the boundary | Late vs on-time handover, from 25 Apr 2018 | 23,327 | 1,075 | +17.75 | 14.65 to 20.84 | −0.38 |
| S13a | Structure | Linear probability model | Late vs on-time handover, from 25 Apr 2018 | 26,575 | 1197 | +18.73 | 15.37 to 22.08 | — |
| S13b | Structure | Heteroskedasticity-robust errors, not clustered | Late vs on-time handover, from 25 Apr 2018 | 26,575 | 1197 | +18.13 | 16.49 to 19.77 | — |

### B5. Handover, pooled across the timestamp change (exploratory)

| Check | Type | Alternative | Comparison | Orders | Events | Estimate | 95% interval | Change |
|---|---|---|---|---:|---:|---:|---:|---:|
| S14c | Timestamp | One pooled period | Late vs on-time handover, pooled | 94,558 | 6,473 | +14.62 | 13.03 to 16.20 | — |

### B6. Multi-item orders (exploratory)

| Check | Type | Alternative | Comparison | Orders | Events | Estimate | 95% interval | Change |
|---|---|---|---|---:|---:|---:|---:|---:|
| S0 | Baseline | Primary specification with delta-method interval | B6 | 95,824 | 12,272 | +12.67 | 11.47 to 13.88 | — |
| S1a | Review | Earliest review | B6 | 95,824 | 12,262 | +12.69 | 11.49 to 13.88 | +0.01 |
| S1b | Review | Excluding orders with several reviews | B6 | 95,299 | 12,189 | +12.66 | 11.46 to 13.87 | −0.01 |
| S2 | Review | Excluding repeated review IDs | B6 | 94,645 | 12,025 | +12.68 | 11.46 to 13.90 | +0.01 |
| S4a | Timestamp | Source CSV timestamps | B6 | 95,824 | 12,272 | +12.67 | 11.47 to 13.88 | +0.00 |
| S4b | Timestamp | Affected orders excluded | B6 | 95,800 | 12,269 | +12.65 | 11.45 to 13.86 | −0.02 |
| S5a | Different question | Full timestamp, previous logic | B6 | 95,824 | 12,272 | +12.68 | 11.47 to 13.88 | +0.00 |
| S5b | Different question | 2 or more days late | B6 | 95,824 | 12,272 | +12.66 | 11.46 to 13.86 | −0.01 |
| S8a | Different question | Excluding peak months | B6 | 75,132 | 8,341 | +11.43 | 10.19 to 12.67 | −1.24 |
| S8b | Different question | Excluding 2016 | B6 | 95,560 | 12,228 | +12.67 | 11.48 to 13.87 | −0.00 |
| S8c | Different question | Excluding purchases from July 2018 | B6 | 83,376 | 11,076 | +13.25 | 11.97 to 14.53 | +0.58 |
| S9 | Different question | Survey creation date instead of answer timestamp | B6 | 95,824 | 12,272 | +12.65 | 11.45 to 13.85 | −0.02 |
| S15 | Timestamp | Excluding deliveries over 60 days | B6 | 95,541 | 12,086 | +12.71 | 11.50 to 13.93 | +0.04 |
| S16 | Review | Excluding reviews created before the purchase date | B6 | 95,821 | 12,270 | +12.67 | 11.47 to 13.88 | +0.00 |
| S13a | Structure | Linear probability model | B6 | 95,824 | 12,272 | +12.77 | 11.60 to 13.94 | +0.09 |
| S13b | Structure | Heteroskedasticity-robust errors, not clustered | B6 | 95,824 | 12,272 | +12.67 | 11.76 to 13.58 | +0.00 |
| S6a | Different question | 1 star only | B6 | 95,824 | 9,351 | +10.82 | 9.79 to 11.85 | −1.85 |
| S6b | Different question | 1-3 stars | B6 | 95,824 | 20,188 | +13.61 | 12.27 to 14.96 | +0.94 |
| S6c | Different question | Mean score difference, in stars | B6 | 95,824 | 12,272 | −0.48 | −0.52 to −0.43 | — |

### B4. Delay length within timing groups (exploratory)

Rates are unadjusted. Under 30 reviews isn't reported.

| Check | Alternative | Timing | 1–3 days | 4–7 days | 8–14 days | 15+ days |
|---|---|---|---:|---:|---:|---:|
| S0 | Primary definitions | before arrival | 78.85% (n=416) | 81.51% (n=1,352) | 82.36% (n=1,389) | 78.88% (n=1,316) |
| S0 | Primary definitions | after arrival | 18.59% (n=1,436) | 20.45% (n=396) | 26.32% (n=57) | Not reported (n=19) |
| S1a | Earliest review | before arrival | 78.71% (n=418) | 81.30% (n=1,353) | 82.36% (n=1,389) | 78.72% (n=1,316) |
| S1a | Earliest review | after arrival | 18.62% (n=1,434) | 20.25% (n=395) | 26.32% (n=57) | Not reported (n=19) |
| S1b | Excluding orders with several reviews | before arrival | 78.85% (n=416) | 81.41% (n=1,345) | 82.50% (n=1,383) | 78.79% (n=1,306) |
| S1b | Excluding orders with several reviews | after arrival | 18.58% (n=1,432) | 20.25% (n=395) | 26.32% (n=57) | Not reported (n=19) |
| S2 | Excluding repeated review IDs | before arrival | 79.41% (n=408) | 81.42% (n=1,335) | 82.52% (n=1,373) | 78.95% (n=1,292) |
| S2 | Excluding repeated review IDs | after arrival | 18.39% (n=1,425) | 20.36% (n=393) | 26.79% (n=56) | Not reported (n=19) |
| S4a | Source CSV timestamps | before arrival | 78.85% (n=416) | 81.51% (n=1,352) | 82.36% (n=1,389) | 78.88% (n=1,316) |
| S4a | Source CSV timestamps | after arrival | 18.59% (n=1,436) | 20.45% (n=396) | 26.32% (n=57) | Not reported (n=19) |
| S4b | Affected orders excluded | before arrival | 78.85% (n=416) | 81.51% (n=1,352) | 82.36% (n=1,389) | 78.88% (n=1,316) |
| S4b | Affected orders excluded | after arrival | 18.63% (n=1,433) | 20.45% (n=396) | 26.32% (n=57) | Not reported (n=19) |
| S5a | Full timestamp, previous logic | before arrival | 78.85% (n=416) | 81.51% (n=1,352) | 82.36% (n=1,389) | 78.88% (n=1,316) |
| S5a | Full timestamp, previous logic | after arrival | 18.59% (n=1,436) | 20.45% (n=396) | 26.32% (n=57) | Not reported (n=19) |
| S5b | 2 or more days late | before arrival | 79.24% (n=395) | 81.51% (n=1,352) | 82.36% (n=1,389) | 78.88% (n=1,316) |
| S5b | 2 or more days late | after arrival | 19.00% (n=637) | 20.45% (n=396) | 26.32% (n=57) | Not reported (n=19) |
| S6a | 1 star only | before arrival | 67.79% (n=416) | 71.60% (n=1,352) | 72.57% (n=1,389) | 69.53% (n=1,316) |
| S6a | 1 star only | after arrival | 12.74% (n=1,436) | 14.14% (n=396) | 22.81% (n=57) | Not reported (n=19) |
| S6b | 1-3 stars | before arrival | 87.98% (n=416) | 89.50% (n=1,352) | 91.07% (n=1,389) | 87.84% (n=1,316) |
| S6b | 1-3 stars | after arrival | 34.89% (n=1,436) | 36.62% (n=396) | 38.60% (n=57) | Not reported (n=19) |
| S8a | Excluding peak months | before arrival | 75.00% (n=212) | 78.39% (n=731) | 78.05% (n=647) | 75.14% (n=539) |
| S8a | Excluding peak months | after arrival | 18.63% (n=875) | 20.51% (n=234) | 28.57% (n=35) | Not reported (n=13) |
| S8b | Excluding 2016 | before arrival | 78.85% (n=416) | 81.51% (n=1,352) | 82.36% (n=1,389) | 78.84% (n=1,314) |
| S8b | Excluding 2016 | after arrival | 18.61% (n=1,435) | 20.45% (n=396) | 26.32% (n=57) | Not reported (n=19) |
| S8c | Excluding purchases from July 2018 | before arrival | 81.20% (n=367) | 81.69% (n=1,207) | 82.99% (n=1,317) | 79.39% (n=1,276) |
| S8c | Excluding purchases from July 2018 | after arrival | 19.82% (n=1,211) | 19.71% (n=350) | 25.49% (n=51) | Not reported (n=17) |
| S9 | Survey creation date instead of answer timestamp | before delivery date | 59.84% (n=386) | 71.80% (n=1,585) | 80.21% (n=1,445) | 78.35% (n=1,335) |
| S9 | Survey creation date instead of answer timestamp | on or after delivery date | 24.83% (n=1,466) | 27.61% (n=163) | Not reported (n=1) | Not reported (n=0) |
| S15 | Excluding deliveries over 60 days | before arrival | 78.85% (n=416) | 81.50% (n=1,351) | 82.47% (n=1,386) | 81.91% (n=1,045) |
| S15 | Excluding deliveries over 60 days | after arrival | 18.61% (n=1,435) | 20.45% (n=396) | 26.32% (n=57) | Not reported (n=15) |
| S16 | Excluding reviews created before the purchase date | before arrival | 78.85% (n=416) | 81.51% (n=1,352) | 82.36% (n=1,389) | 78.88% (n=1,316) |
| S16 | Excluding reviews created before the purchase date | after arrival | 18.59% (n=1,436) | 20.45% (n=396) | 26.32% (n=57) | Not reported (n=19) |

**S5b band:** under "2 or more days late", the 1–3 days column contains only orders 2–3 days late.

**S9 groups use calendar dates.** "Before delivery date" means the review was created on an earlier date than the delivery. "On or after delivery date" includes reviews created on the delivery date itself, so 198 late reviews in this group have an answer timestamp before the recorded delivery. Creation date is also closely tied to delay length: 20.8%, 90.7%, 99.9% and 100% of late reviews in the four delay bands were created before the delivery date, so the later group has almost no reviews beyond 7 days late. Neither definition shows when a customer formed or submitted a rating.

| Check | Alternative | Timing | Comparison | Difference | 95% interval |
|---|---|---|---|---:|---:|
| S0 | Primary definitions | before arrival | 4-7 days vs 1-3 days | +2.66 | −1.85 to 7.18 |
| S0 | Primary definitions | before arrival | 8-14 days vs 4-7 days | +0.85 | −1.79 to 3.49 |
| S0 | Primary definitions | before arrival | 15+ days vs 8-14 days | −3.49 | −6.60 to −0.38 |
| S0 | Primary definitions | after arrival | 4-7 days vs 1-3 days | +1.86 | −2.59 to 6.31 |
| S0 | Primary definitions | after arrival | 8-14 days vs 4-7 days | +5.86 | −6.13 to 17.85 |
| S1a | Earliest review | before arrival | 4-7 days vs 1-3 days | +2.59 | −1.89 to 7.07 |
| S1a | Earliest review | before arrival | 8-14 days vs 4-7 days | +1.06 | −1.60 to 3.72 |
| S1a | Earliest review | before arrival | 15+ days vs 8-14 days | −3.64 | −6.71 to −0.56 |
| S1a | Earliest review | after arrival | 4-7 days vs 1-3 days | +1.63 | −2.82 to 6.08 |
| S1a | Earliest review | after arrival | 8-14 days vs 4-7 days | +6.06 | −5.93 to 18.06 |
| S1b | Excluding orders with several reviews | before arrival | 4-7 days vs 1-3 days | +2.57 | −1.96 to 7.09 |
| S1b | Excluding orders with several reviews | before arrival | 8-14 days vs 4-7 days | +1.09 | −1.54 to 3.72 |
| S1b | Excluding orders with several reviews | before arrival | 15+ days vs 8-14 days | −3.71 | −6.82 to −0.60 |
| S1b | Excluding orders with several reviews | after arrival | 4-7 days vs 1-3 days | +1.68 | −2.77 to 6.13 |
| S1b | Excluding orders with several reviews | after arrival | 8-14 days vs 4-7 days | +6.06 | −5.93 to 18.06 |
| S2 | Excluding repeated review IDs | before arrival | 4-7 days vs 1-3 days | +2.01 | −2.51 to 6.54 |
| S2 | Excluding repeated review IDs | before arrival | 8-14 days vs 4-7 days | +1.10 | −1.57 to 3.77 |
| S2 | Excluding repeated review IDs | before arrival | 15+ days vs 8-14 days | −3.57 | −6.72 to −0.43 |
| S2 | Excluding repeated review IDs | after arrival | 4-7 days vs 1-3 days | +1.97 | −2.49 to 6.43 |
| S2 | Excluding repeated review IDs | after arrival | 8-14 days vs 4-7 days | +6.43 | −5.71 to 18.57 |
| S4a | Source CSV timestamps | before arrival | 4-7 days vs 1-3 days | +2.66 | −1.85 to 7.18 |
| S4a | Source CSV timestamps | before arrival | 8-14 days vs 4-7 days | +0.85 | −1.79 to 3.49 |
| S4a | Source CSV timestamps | before arrival | 15+ days vs 8-14 days | −3.49 | −6.60 to −0.38 |
| S4a | Source CSV timestamps | after arrival | 4-7 days vs 1-3 days | +1.86 | −2.59 to 6.31 |
| S4a | Source CSV timestamps | after arrival | 8-14 days vs 4-7 days | +5.86 | −6.13 to 17.85 |
| S4b | Affected orders excluded | before arrival | 4-7 days vs 1-3 days | +2.66 | −1.85 to 7.18 |
| S4b | Affected orders excluded | before arrival | 8-14 days vs 4-7 days | +0.85 | −1.79 to 3.49 |
| S4b | Affected orders excluded | before arrival | 15+ days vs 8-14 days | −3.49 | −6.60 to −0.38 |
| S4b | Affected orders excluded | after arrival | 4-7 days vs 1-3 days | +1.82 | −2.62 to 6.27 |
| S4b | Affected orders excluded | after arrival | 8-14 days vs 4-7 days | +5.86 | −6.13 to 17.85 |
| S5a | Full timestamp, previous logic | before arrival | 4-7 days vs 1-3 days | +2.66 | −1.85 to 7.18 |
| S5a | Full timestamp, previous logic | before arrival | 8-14 days vs 4-7 days | +0.85 | −1.79 to 3.49 |
| S5a | Full timestamp, previous logic | before arrival | 15+ days vs 8-14 days | −3.49 | −6.60 to −0.38 |
| S5a | Full timestamp, previous logic | after arrival | 4-7 days vs 1-3 days | +1.86 | −2.59 to 6.31 |
| S5a | Full timestamp, previous logic | after arrival | 8-14 days vs 4-7 days | +5.86 | −6.13 to 17.85 |
| S5b | 2 or more days late | before arrival | 4-7 days vs 2-3 days | +2.27 | −2.33 to 6.86 |
| S5b | 2 or more days late | before arrival | 8-14 days vs 4-7 days | +0.85 | −1.79 to 3.49 |
| S5b | 2 or more days late | before arrival | 15+ days vs 8-14 days | −3.49 | −6.60 to −0.38 |
| S5b | 2 or more days late | after arrival | 4-7 days vs 2-3 days | +1.46 | −3.57 to 6.49 |
| S5b | 2 or more days late | after arrival | 8-14 days vs 4-7 days | +5.86 | −6.14 to 17.86 |
| S6a | 1 star only | before arrival | 4-7 days vs 1-3 days | +3.81 | −1.25 to 8.87 |
| S6a | 1 star only | before arrival | 8-14 days vs 4-7 days | +0.97 | −2.21 to 4.15 |
| S6a | 1 star only | before arrival | 15+ days vs 8-14 days | −3.04 | −6.49 to 0.41 |
| S6a | 1 star only | after arrival | 4-7 days vs 1-3 days | +1.40 | −2.54 to 5.34 |
| S6a | 1 star only | after arrival | 8-14 days vs 4-7 days | +8.67 | −2.51 to 19.84 |
| S6b | 1-3 stars | before arrival | 4-7 days vs 1-3 days | +1.52 | −1.95 to 4.98 |
| S6b | 1-3 stars | before arrival | 8-14 days vs 4-7 days | +1.58 | −0.56 to 3.71 |
| S6b | 1-3 stars | before arrival | 15+ days vs 8-14 days | −3.23 | −5.48 to −0.98 |
| S6b | 1-3 stars | after arrival | 4-7 days vs 1-3 days | +1.73 | −3.81 to 7.26 |
| S6b | 1-3 stars | after arrival | 8-14 days vs 4-7 days | +1.98 | −11.55 to 15.51 |
| S8a | Excluding peak months | before arrival | 4-7 days vs 1-3 days | +3.39 | −3.06 to 9.83 |
| S8a | Excluding peak months | before arrival | 8-14 days vs 4-7 days | −0.33 | −4.36 to 3.70 |
| S8a | Excluding peak months | before arrival | 15+ days vs 8-14 days | −2.91 | −7.77 to 1.94 |
| S8a | Excluding peak months | after arrival | 4-7 days vs 1-3 days | +1.88 | −3.79 to 7.56 |
| S8a | Excluding peak months | after arrival | 8-14 days vs 4-7 days | +8.06 | −7.51 to 23.63 |
| S8b | Excluding 2016 | before arrival | 4-7 days vs 1-3 days | +2.66 | −1.85 to 7.18 |
| S8b | Excluding 2016 | before arrival | 8-14 days vs 4-7 days | +0.85 | −1.79 to 3.49 |
| S8b | Excluding 2016 | before arrival | 15+ days vs 8-14 days | −3.52 | −6.63 to −0.40 |
| S8b | Excluding 2016 | after arrival | 4-7 days vs 1-3 days | +1.85 | −2.60 to 6.30 |
| S8b | Excluding 2016 | after arrival | 8-14 days vs 4-7 days | +5.86 | −6.13 to 17.85 |
| S8c | Excluding purchases from July 2018 | before arrival | 4-7 days vs 1-3 days | +0.49 | −4.27 to 5.25 |
| S8c | Excluding purchases from July 2018 | before arrival | 8-14 days vs 4-7 days | +1.30 | −1.44 to 4.04 |
| S8c | Excluding purchases from July 2018 | before arrival | 15+ days vs 8-14 days | −3.60 | −6.75 to −0.46 |
| S8c | Excluding purchases from July 2018 | after arrival | 4-7 days vs 1-3 days | −0.10 | −4.79 to 4.58 |
| S8c | Excluding purchases from July 2018 | after arrival | 8-14 days vs 4-7 days | +5.78 | −6.69 to 18.25 |
| S9 | Survey creation date instead of answer timestamp | before delivery date | 4-7 days vs 1-3 days | +11.95 | 6.65 to 17.26 |
| S9 | Survey creation date instead of answer timestamp | before delivery date | 8-14 days vs 4-7 days | +8.41 | 5.46 to 11.36 |
| S9 | Survey creation date instead of answer timestamp | before delivery date | 15+ days vs 8-14 days | −1.86 | −5.04 to 1.33 |
| S9 | Survey creation date instead of answer timestamp | on or after delivery date | 4-7 days vs 1-3 days | +2.78 | −4.64 to 10.20 |
| S15 | Excluding deliveries over 60 days | before arrival | 4-7 days vs 1-3 days | +2.65 | −1.87 to 7.16 |
| S15 | Excluding deliveries over 60 days | before arrival | 8-14 days vs 4-7 days | +0.97 | −1.68 to 3.62 |
| S15 | Excluding deliveries over 60 days | before arrival | 15+ days vs 8-14 days | −0.55 | −3.65 to 2.55 |
| S15 | Excluding deliveries over 60 days | after arrival | 4-7 days vs 1-3 days | +1.85 | −2.60 to 6.30 |
| S15 | Excluding deliveries over 60 days | after arrival | 8-14 days vs 4-7 days | +5.86 | −6.13 to 17.85 |
| S16 | Excluding reviews created before the purchase date | before arrival | 4-7 days vs 1-3 days | +2.66 | −1.85 to 7.18 |
| S16 | Excluding reviews created before the purchase date | before arrival | 8-14 days vs 4-7 days | +0.85 | −1.79 to 3.49 |
| S16 | Excluding reviews created before the purchase date | before arrival | 15+ days vs 8-14 days | −3.49 | −6.60 to −0.38 |
| S16 | Excluding reviews created before the purchase date | after arrival | 4-7 days vs 1-3 days | +1.86 | −2.59 to 6.31 |
| S16 | Excluding reviews created before the purchase date | after arrival | 8-14 days vs 4-7 days | +5.86 | −6.13 to 17.85 |
| S6c | Mean score difference, in stars | before arrival | 4-7 days vs 1-3 days | −0.08 | −0.22 to 0.05 |
| S6c | Mean score difference, in stars | before arrival | 8-14 days vs 4-7 days | −0.04 | −0.12 to 0.04 |
| S6c | Mean score difference, in stars | before arrival | 15+ days vs 8-14 days | +0.11 | 0.02 to 0.20 |
| S6c | Mean score difference, in stars | after arrival | 4-7 days vs 1-3 days | −0.05 | −0.21 to 0.10 |
| S6c | Mean score difference, in stars | after arrival | 8-14 days vs 4-7 days | −0.17 | −0.59 to 0.26 |
| S0 | Adjusted, before arrival, clustered delta interval | Adjusted | 4-7 days vs 1-3 days | +3.02 | −1.37 to 7.41 |
| S0 | Adjusted, before arrival, clustered delta interval | Adjusted | 8-14 days vs 4-7 days | −0.16 | −2.76 to 2.44 |
| S0 | Adjusted, before arrival, clustered delta interval | Adjusted | 15+ days vs 8-14 days | −5.27 | −8.55 to −1.99 |
| S13a | Linear probability model, before arrival | Adjusted | 4-7 days vs 1-3 days | +3.16 | −1.36 to 7.69 |
| S13a | Linear probability model, before arrival | Adjusted | 8-14 days vs 4-7 days | −0.29 | −2.95 to 2.38 |
| S13a | Linear probability model, before arrival | Adjusted | 15+ days vs 8-14 days | −5.07 | −8.25 to −1.89 |
| S13b | Heteroskedasticity-robust errors, before arrival | Adjusted | 4-7 days vs 1-3 days | +3.02 | −1.26 to 7.30 |
| S13b | Heteroskedasticity-robust errors, before arrival | Adjusted | 8-14 days vs 4-7 days | −0.16 | −2.98 to 2.65 |
| S13b | Heteroskedasticity-robust errors, before arrival | Adjusted | 15+ days vs 8-14 days | −5.27 | −8.36 to −2.19 |
| S0 | Adjusted, after arrival, clustered delta interval | Adjusted | 4-7 days vs 1-3 days | +1.59 | −2.98 to 6.17 |
| S0 | Adjusted, after arrival, clustered delta interval | Adjusted | 8-14 days vs 4-7 days | +3.25 | −7.72 to 14.22 |
| S13a | Linear probability model, after arrival | Adjusted | 4-7 days vs 1-3 days | +1.59 | −2.90 to 6.08 |
| S13a | Linear probability model, after arrival | Adjusted | 8-14 days vs 4-7 days | +3.61 | −7.80 to 15.03 |
| S13b | Heteroskedasticity-robust errors, after arrival | Adjusted | 4-7 days vs 1-3 days | +1.59 | −2.86 to 6.04 |
| S13b | Heteroskedasticity-robust errors, after arrival | Adjusted | 8-14 days vs 4-7 days | +3.25 | −7.41 to 13.91 |

### B7. Where low ratings fall (exploratory)

| Check | Alternative | Reviewed | Low ratings | On-time share | On time, single item | On time, multi-item | Late, single item | Late, multi-item |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| S0 | Primary definitions | 95,824 | 12,272 | 67.54% | 49.44% | 18.11% | 29.80% | 2.66% |
| S1a | Earliest review | 95,824 | 12,262 | 67.55% | 49.38% | 18.17% | 29.79% | 2.66% |
| S1b | Excluding orders with several reviews | 95,299 | 12,189 | 67.50% | 49.41% | 18.09% | 29.84% | 2.67% |
| S2 | Excluding repeated review IDs | 94,645 | 12,025 | 67.33% | 49.21% | 18.11% | 29.99% | 2.69% |
| S4a | Source CSV timestamps | 95,824 | 12,272 | 67.54% | 49.44% | 18.11% | 29.80% | 2.66% |
| S4b | Affected orders excluded | 95,800 | 12,269 | 67.54% | 49.44% | 18.09% | 29.81% | 2.66% |
| S5a | Full timestamp, previous logic | 95,824 | 12,272 | 66.25% | 48.38% | 17.87% | 30.86% | 2.89% |
| S5b | 2 or more days late | 95,824 | 12,272 | 68.86% | 50.50% | 18.36% | 28.74% | 2.40% |
| S6a | 1 star only | 95,824 | 9,351 | 63.31% | 44.78% | 18.53% | 33.61% | 3.08% |
| S6b | 1-3 stars | 95,824 | 20,188 | 76.83% | 61.57% | 15.27% | 21.34% | 1.83% |
| S8a | Excluding peak months | 75,132 | 8,341 | 77.58% | 57.98% | 19.60% | 20.57% | 1.85% |
| S8b | Excluding 2016 | 95,560 | 12,228 | 67.44% | 49.35% | 18.10% | 29.90% | 2.66% |
| S8c | Excluding purchases from July 2018 | 83,376 | 11,076 | 66.42% | 48.28% | 18.14% | 30.83% | 2.74% |
| S9 | Survey creation date instead of answer timestamp | 95,824 | 12,272 | 67.54% | 49.44% | 18.11% | 29.80% | 2.66% |
| S15 | Excluding deliveries over 60 days | 95,541 | 12,086 | 68.58% | 50.19% | 18.38% | 28.81% | 2.61% |
| S16 | Excluding reviews created before the purchase date | 95,821 | 12,270 | 67.54% | 49.43% | 18.11% | 29.80% | 2.66% |

## Coverage of the 16 planned checks

| Check | Choice tested | Type | Runs recorded |
|---|---|---|---:|
| S1 | Several reviews | Review | 22 |
| S2 | Repeated review IDs | Review | 11 |
| S3 | Invalid date sequences | Timestamp | 36 |
| S4 | Daylight-saving shift | Timestamp | 28 |
| S5 | Late definition | Different question | 42 |
| S6 | Low-rating definition | Different question | 32 |
| S7 | Several sellers | Structure | 7 |
| S8 | Period | Different question | 65 |
| S9 | Answer timing | Different question | 6 |
| S10 | Distance | Structure | 8 |
| S11 | Category | Structure | 4 |
| S12 | Missing reviews | Review | 10 |
| S13 | Model form | Structure | 45 |
| S14 | Carrier timestamp period | Timestamp | 5 |
| S15 | Long deliveries | Timestamp | 23 |
| S16 | Reviews created before purchase | Review | 11 |

**Not applicable:**

| Check | Result | Reason |
|---|---|---|
| S5a | A3 | Delay bands use whole days late, so orders delivered on the estimated date stay out of the bands. The timestamp definition can't change A3. |
| S8a | B1 and B2 | These results compare peak with other months, so excluding peak months removes the comparison. |
| S8c | B5 before 25 April 2018 | All these orders were purchased before July 2018, so the estimate is unchanged by construction. |
| S6, S9, S12, S16 | A1, A4, A5, A6, A7, B1, B2, B5 | These results don't use reviews. |
| S13 | A6, B1, B7 | These don't use a regression model. |
| S7, S10 | A2, A3, B3, B4, B6, B7 | These results don't use seller assignment or distance. |

## Model diagnostics

- **Runs:** 325 result rows in the main script, plus 26 in the supplement, with 0 failed runs and 0 errors.
- **Convergence:** 305 of 305 model rows converged. The largest coefficient in any model is 4.06, and no separation was detected.
- **Bootstrap failures:** 0 in the 2,000-replicate model bootstraps.
- **Baseline:** re-fitting each primary model reproduces its primary estimate. Delta-method intervals are close to the primary bootstrap intervals, except A7, where the bootstrap re-selects the extreme pair.
- **Thin term:** the multi-seller term in all A3 models rests on few orders with fewer than 5 events or non-events. Its coefficient is stable, and it's kept as defined.
- **Sparse levels, reported and kept:** distance levels in X1a and X1c, and 3+ items in X3d. Each is relabelled "other" without being combined with another level.
- **Specification differences, stated in each run:** the same-state term is removed where it can't be estimated (X1a, X1b, X1c), the multi-seller term in X3d, and category in X3e. Failed or awkward runs weren't dropped.
- **S13a for A7:** the linear model gives a point estimate only, with no interval for the selected pair.

## Limitations

- **Observational results:** none of these checks can establish cause. They test sensitivity to analytical choices, not unmeasured differences.
- **Analytical choices are bounded:** other reasonable choices exist that weren't tested.
- **No correction across sensitivity runs:** intervals and p-values in sensitivity runs are unadjusted.
- **Delta-method intervals:** these are approximations, and they ignore selection of the extreme pair in A7.
- **Exploratory checks influence one label:** A5's label draws on the exploratory state check, and the reasoning is stated above.
- **Review timestamps:** answer timing is self-selected and closely linked to delay length. Neither the answer timestamp nor the creation date is definitive evidence of when a customer formed or submitted a rating, and the two give different pictures for B4.
- **Peak months:** they were selected using the outcome, so S8a results also reflect that choice.
- **Independent audit:** see [independent_audit.md](independent_audit.md), including the checks it didn't recompute.

## Hypothesis log

The approved labels and caveats are recorded in [hypothesis_log.md](hypothesis_log.md). No Class A estimate, definition, criterion or evidence label changed.
