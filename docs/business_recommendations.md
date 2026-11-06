# Business Recommendations

**Status: approved.** Prepared from commit `d7c88c7` on `case-study-upgrade`. Based only on historical Olist data from 2016 to 2018. It describes what the data supports and what a business would need to check next. It isn't a diagnosis of current operations.

## 1. Executive Summary

**The challenge.** Most delivered orders arrived on time (93.23%), but lateness and low ratings aren't evenly spread. Treating them as one delivery problem would point management at the wrong work: delivery timing doesn't account for most low ratings, and some delivery gaps are far larger in a few months than in the rest of the data.

**What the data shows most clearly**

- **Rio de Janeiro customers.** Their orders were late more often than São Paulo customers' orders, by about 7 points after accounting for measured differences. The gap was about 23 points in three high-lateness months and 3 points in other months. Those months were picked from the data, so the split still needs testing on new data.
- **Lateness and low ratings.** These are strongly linked, but the size of the link depends on when the review was recorded. In an exploratory split, it's about 70 points when the answer was recorded before delivery and about 10 points when it was recorded after.
- **On-time orders.** Among reviewed delivered orders, they hold two-thirds of low ratings, partly because there are so many of them. A late order is still far more likely to be rated low.
- **Multi-item orders.** They receive more low ratings even when they arrive on time. This is an exploratory pattern, and the data doesn't explain it.
- **Seller handover.** Late handover goes with late delivery, but most late orders had an on-time recorded handover. A recording change in April 2018 limits this evidence.

**Decisions management could consider**

1. Investigate late delivery to Rio de Janeiro customers first, starting with orders from São Paulo sellers, before funding any logistics change.
2. Report low ratings separately for on-time orders and for late orders recorded before and after delivery, and find out why on-time orders are rated low.
3. Confirm what the carrier timestamp records before using handover data to manage sellers.
4. Find out what goes wrong on multi-item orders before designing a fix.

**What not to prioritise yet.** Seller concentration, product categories, freight cost and delivery distance don't currently justify a dedicated programme. Section 4 explains why, including where the evidence remains uncertain.

**Measuring success.** No single metric is enough. On-time rate can rise simply because promises get longer, so it must be read with promised time, actual time and customer ratings. Targets should be agreed after measuring a current baseline.

**Important limits.** All findings are observational, so none of them shows a cause. No result has been tested on an independent sample. The data has no carrier, route, weather, stock or customer-service records, and it excludes undelivered orders. None of the four recommendations is ready for operational rollout, and this document makes no estimate of savings or return.

## 2. Business Context and Scope

**Business question.** Where should a marketplace focus its delivery and customer-experience work, and what evidence does it need before acting?

**Data.** The analysis base is 96,470 delivered orders with a delivery date. Review results cover 95,824 of them, and some results use narrower samples, stated where they matter. Exact definitions are in [methodology.md](methodology.md).

**Out of scope.** New statistical analysis, forecasts, savings or return estimates, budgets, staffing, timelines and targets. Business owners are illustrative, because no real Olist team was consulted.

## 3. Evidence and Interpretation Framework

| Evidence class | Meaning | What it can support here |
|---|---|---|
| **Class A: prespecified** | Questions fixed before adjusted estimates were calculated, though unadjusted figures had been previewed. Labels remain provisional in the log | Supported and robust: an action or experiment. Supported and sensitive: an experiment, with the caveat. Unsupported or inconclusive: no action |
| **Class B: exploratory** | Questions shaped by looking at the data | Investigation or pilot design, never confirmation |
| **Class C: descriptive** | Measurements with no hypothesis test | Context only |
| **Sensitivity results** | Whether conclusions hold under other reasonable choices | Qualifies confidence. Doesn't confirm a finding |

The screening criteria (2 points and 500 late orders for late rate, 5 points for low ratings) are researcher-defined, not business-validated. A real business would set its own thresholds.

These six questions are answered separately because a finding can do well on one and poorly on another.

| Finding | Statistically detected? | Above screening criterion? | Business relevance | Actionable now? | Ready to implement? | Shows a cause? |
|---|---|---|---|---|---|---|
| **A1** RJ against SP | Yes | Yes | High | Investigate only: no route or carrier data | No | No |
| **A2** Lateness and low ratings | Yes | Yes | High | Change reporting and investigate | No | No |
| **B5** Late handover | Exploratory p-values, uncorrected | Before 25 April 2018 yes; later period misses the order minimum | Medium | Check data, then monitor | No | No, and the link is partly built into how lateness is measured |
| **B6** Multi-item orders | Exploratory p-values, uncorrected | Yes | Medium | Investigate only: no shipment data | No | No |

## 4. Prioritisation Matrix

Ratings are qualitative judgements, with no numerical scores. Effect size alone doesn't set priority. A2's estimate is far larger than A1's, yet both rank High: A1 points to an identifiable customer segment, while A2's size depends heavily on answer timing.

| Recommendation | Evidence strength | Practical relevance | Actionability | Measurement feasibility | Implementation complexity | Main limitation |
|---|---|---|---|---|---|---|
| **R1** Geographic delivery | High for the RJ gap; Medium for the peak-month pattern | High | Medium | High for outcomes; Low for mechanisms | High for any logistics change | No carrier, route or capacity data; peak months chosen from the outcome |
| **R2** Low-rating diagnosis | High for the association; Low for its size on received orders | High | Medium | Medium | Low for reporting; Medium for diagnosis | Review timestamps don't show when opinions were formed |
| **R3** Handover monitoring | Medium to Low | Medium | Medium | Low until timestamps are validated | Low for monitoring | 25 April 2018 timestamp change; link partly built in |
| **R4** Multi-item experience | Medium | Medium | Low to Medium | High for outcomes; Low for mechanisms | Medium | No shipment-level data |

| Recommendation | Investigation priority | Implementation readiness | Recommended next step |
|---|---|---|---|
| **R1** | High | Low: no intervention is supported yet | Investigation |
| **R2** | High | Medium for split reporting; Low for any intervention | Data-quality improvement and investigation |
| **R3** | Medium | Medium for monitoring after validation; Low for any intervention | Data-quality improvement, then monitoring |
| **R4** | Medium | Low | Investigation |

A high investigation priority doesn't mean a solution is ready to deploy. Next steps run from data-quality validation and investigation, through monitoring and pilot testing, to operational intervention and scaling. None of the four recommendations has reached pilot testing, intervention or scaling.

**Recommended sequence**

1. **Shared measurement first.** R1 to R4 all depend on consistent definitions, so agree them before comparing anything.
2. **R1 and R2 together.** They rest on the strongest evidence and need different teams.
3. **R4 next.** It can reuse the reason classification built for R2.
4. **R3 monitoring once timestamps are understood.** Monitoring an unvalidated field could mislead seller decisions.

**Findings that don't justify a dedicated programme**

| Finding | Result | Decision it supports | What it doesn't show |
|---|---|---|---|
| **A6** Seller concentration | +6.97 points (2.48 to 10.66) against a 10-point criterion. Detectable, not practically important | Don't assume targeting a few sellers is a broad solution. The 12 sellers above the funnel limit can be reviewed case by case under R3 | The interval reaches the criterion, so practical importance isn't excluded |
| **A7** Category spread | 3.69 points (2.88 to 6.90) against a 5-point criterion. Detectable, not practically important | Don't build a category-led delivery programme | The interval reaches the criterion, and detection weakens in restricted samples (p = 0.054 excluding deliveries over 60 days) |
| **A5** Freight | +2.16 points (1.27 to 3.01). Supported, close to the criterion, and sensitive | Don't treat freight as an operational lever. Keep freight charged as a guardrail, not as a measure of logistics cost | With customer state added, +0.97 (−0.01 to 1.94). This doesn't show freight has no link with lateness |
| **A4** Distance | +0.59 points (−0.49 to 1.50). Unsupported, for the fixed 600–1,000 km against 0–100 km comparison | Don't prioritise this comparison | Distance isn't ruled out: without state in the model it's +2.47, and the 2,000+ km band is +2.52 (0.22 to 4.82) |
| **A3** Delay length | 15+ against 1–3 days, +42.10 points (39.04 to 45.22). Inconclusive and unresolved | Don't set a "days late" threshold for satisfaction yet | A steady worsening isn't shown, and neither is a fall at 15+ days |

**No fifth recommendation.** Two descriptive candidates were considered:

- **Sales growth** (+141.1% from January to August, 99.2% from order volume) has no distinct action behind it and doesn't support a forecast.
- **Promise calibration** is more useful: the median promise is 24 days against 10 days actual, and 78.93% of orders arrive 7 or more days early. It has no outcome test of its own, and promises are already covered as a dimension of R1 and as a required companion to every delivery KPI. It's treated that way below.

## 5. Detailed Business Recommendations

### R1. Investigate late delivery to Rio de Janeiro customers, starting with orders from São Paulo sellers

**Next step: investigation.** A pilot is possible later, only if a mechanism is supported.

**Business problem.** RJ holds 22.88% of late orders with 12.80% of orders (Class C). In the A1 sample, about two-thirds of RJ orders come from SP sellers (8,021 of 12,144), and only 7.8% have an in-state seller, compared with 76.0% of SP orders. RJ's late orders are also concentrated in time: 57.61% of those in the comparison sample fall in three months.

**Supporting evidence**

- **A1:** orders delivered to customers in RJ against customers in SP, +7.46 points (5.88 to 9.13), on 51,984 single-seller orders with a known distance. ([hypothesis_log.md, A1](hypothesis_log.md#a1-rj-compared-with-sp))
- **B2:** adjusted gap of +23.46 points (19.64 to 27.50) in peak months and +3.04 points (2.09 to 4.19) in other months. ([hypothesis_log.md, B2](hypothesis_log.md#b2-rjs-gap-in-peak-and-other-months))
- **Sensitivity:** +8.92 to +9.46 points in the four required overlap checks, including SP sellers only, and +3.57 points (2.54 to 4.60) excluding peak months. ([sensitivity_results.md](sensitivity_results.md#a1-sp-seller-overlap))
- **Unadjusted late rates for single-seller orders from SP sellers, by customer state (Class B):**

| Customer state | Peak months: late rate (orders) | Other months: late rate (orders) |
|---|---:|---:|
| RJ | 37.66% (1,843) | 7.30% (6,205) |
| ES | 29.18% (329) | 7.53% (1,115) |
| BA | 24.51% (510) | 9.73% (1,768) |
| MG | 14.67% (1,663) | 2.60% (5,663) |
| SP | 8.08% (6,321) | 3.81% (23,992) |

This table groups orders by seller state and customer state. It doesn't describe a transport route: the data has no carrier, dispatch or route records.

**Evidence classification and robustness.** A1 is Class A, Supported (provisional) and Robust. The direction never reverses, but the size depends on the period. B2 and the seller-state table are Class B, and the peak months were selected using the outcome, so some concentration is built in and the pattern has no independent validation. +7.46 shouldn't be quoted without the period split.

**Business interpretation.** A1 compares customer states. It doesn't identify a transport route, and it doesn't show that geography itself causes delay. The unadjusted table suggests the pattern isn't unique to RJ: orders from SP sellers to ES and BA customers also have much higher late rates in the selected months, and outside them BA's rate is higher than RJ's. Volume alone doesn't obviously explain the peaks: January and March 2018 had similar orders (7,069 and 7,003) but late rates of 5.70% and 18.96%, with median promises of 26 and 22 days and median actual times of 12 and 13 days. These are descriptive comparisons, not explanations.

**Proposed management action.** Review orders from SP sellers to RJ, ES and BA customers in November 2017 and February to March 2018, then repeat the comparison on current data. Treat seller location, order mix, demand, promise setting, logistics capacity and carrier allocation as hypotheses to test.

**Management decision supported.** *Which customer segment should logistics investigate first, and is there enough evidence to design a pilot?* Start with orders from SP sellers to RJ customers: they're about two-thirds of RJ orders in the A1 sample and have the highest selected-month late rate in the table above. Decide whether a real gap would call for a promise change, a capacity change or no action.

**Illustrative owner.** Logistics and Operations, supported by BI.

**Implementation approach**

1. Measure the same customer-state and seller-state view on current data, using the shared definitions.
2. Write the high-lateness rule before looking at the new period, then check whether the pattern recurs.
3. Add carrier, route and capacity records for the priority segments.
4. Separate two questions: did delivery take longer, or was the promise shorter?

**KPIs** (defined in section 6)

- **Leading:** K7 overdue open orders, K2 promised time.
- **Lagging:** K6 state-pair late rate, K1 on-time rate.
- **Guardrails:** measurable now: K3 actual time, K4 early-delivery share, K5 freight charged, K9 low-rating share. Needs validation: K8 non-delivery rate. Real logistics cost needs new data.

**Qualitative expected benefit.** Investigation effort focused on the largest observed gap, and less risk of funding a logistics change for what may be a promise-setting problem. No size of benefit can be estimated from this data.

**Validation approach.** Test on a period not used to choose the peak months. If a pilot is justified, compare treated segments or periods with a comparison group where feasible, and read the results alongside promised and actual time.

**Decision criteria.** Set thresholds with management before reading the new data.

- **Move to pilot design** if the gap persists on consistent definitions, a specific mechanism has operational support, and the gap isn't explained by promise setting.
- **Revise** if the gap is mainly about promises. The question then becomes how promises are set.
- **Stop** if the gap doesn't appear in current data, or no mechanism can be addressed.

**Risks and limitations.** Limited overlap between RJ and SP orders means the model relies on its assumptions, although the overlap checks give larger gaps. Orders with any status other than delivered are 3.91% in RJ and 2.98% in SP. This is an untested audit measure, and these orders aren't in the results. The pattern doesn't repeat within the data: February and March 2017 had late rates of 2.96% and 4.56%, against 14.13% and 18.96% a year later, so no seasonal claim can be made.

### R2. Separate delivery-related low ratings from other customer-experience issues

**Next step: data-quality improvement and investigation.**

**Business problem.** A single low-rating figure mixes different situations. Late orders have a far higher low-rating share, yet 67.54% of low ratings among reviewed delivered orders fall on on-time orders. Delivery timing alone doesn't account for most low ratings.

**Supporting evidence**

- **A2:** late against on-time, +51.04 points (49.58 to 52.28); unadjusted 62.42% against 9.27%. ([hypothesis_log.md, A2](hypothesis_log.md#a2-late-delivery-and-low-ratings))
- **B3:** late orders answered before recorded delivery, +70.07 points (68.49 to 71.45); answered after, +9.94 points (8.26 to 11.62). 70.10% of reviews on late orders were answered before recorded delivery. ([hypothesis_log.md, B3](hypothesis_log.md#b3-answer-timing-and-low-ratings))
- **B7:** on-time orders hold 8,289 of 12,272 low ratings, or 67.54% (65.86 to 69.20). On-time single-item orders alone hold 49.44%. ([hypothesis_log.md, B7](hypothesis_log.md#b7-where-low-ratings-fall))
- **A3 and B4:** the rise with delay length is unresolved, and it depends on the timing definition. ([sensitivity_results.md](sensitivity_results.md#unexpected-findings))

**Evidence classification and robustness.** A2 is Class A, Supported (provisional), and robust as an observational association, with answer timing as an important limitation. B3 and B7 are Class B. B7 is a share of counts, so it partly reflects how many on-time orders there are. A3 is Inconclusive and unresolved, so no steady rise with delay length is claimed.

**Business interpretation.** Lateness is strongly associated with low ratings, but +51.04 points isn't the effect of a late delivery on a received order. Reviews answered before recorded delivery may reflect waiting, an expected date having passed, or something else. The timing pattern could fit surveys being triggered by delivery or shortly after the promised date, but the data can't confirm that. The large group of on-time low ratings is unexplained, and it shouldn't be assumed to have one cause. The data doesn't say whether product, seller, communication or other issues lie behind it.

**Proposed management action.** Report low ratings by delivery status and answer timing, document how surveys are triggered, and classify the reasons behind a sample of on-time low ratings.

**Management decision supported.** *Which customer-experience issue should be examined first, and can review scores be used as a delivery KPI as they stand?* Decide whether to open a separate workstream for on-time low ratings, and whether review scores need a timing split before appearing in delivery reporting.

**Illustrative owner.** Customer Experience and Quality, supported by BI.

**Implementation approach**

1. Add the three-group view to reporting.
2. Ask the survey owner how and when surveys are sent, and record the answer.
3. Assess coverage and quality of the review title and comment fields, which exist in the source data but weren't analysed.
4. Classify a sample of low-rated on-time orders by reason, with a second reviewer checking agreement.
5. Link complaints and returns if such data can be obtained.

**KPIs**

- **Leading:** K10 share of late-order reviews answered before delivery, K11 low ratings with a validated reason.
- **Lagging:** K9 low-rating share by group.
- **Guardrails:** measurable now: K12 review coverage. Needs validation: K8 non-delivery rate.

**Qualitative expected benefit.** A clearer view of which low ratings delivery work could plausibly affect, and less risk of crediting or blaming delivery for unrelated dissatisfaction.

**Validation approach.** Check classifications with a second reviewer. Compare answer and creation timing on current data. Test whether a mechanism recurs in a later period before designing a pilot.

**Decision criteria**

- **Open a workstream** if a reason accounts for a clear share of classified on-time low ratings, and an owner can act on it.
- **Revise** if comments cover too few low ratings: collect a structured reason at the point of review first.
- **Stop** the diagnosis if no reason stands out after a reasonable sample. Keep the split reporting.

**Risks and limitations.** Neither timestamp shows when a customer formed or submitted a rating, or whether they had received the order. Reviewers may differ from non-reviewers: 2.34% of late orders and 0.55% of on-time orders have no review. Changing the survey trigger could change scores without any change in experience. Undelivered orders, possibly the worst experiences, aren't covered.

### R3. Validate handover data, then monitor seller handover

**Next step: data-quality improvement, then monitoring.** No seller or carrier intervention is recommended from this evidence.

**Business problem.** Handover happens before final delivery, so it could give an earlier signal of risk. But the recorded data has a known break, its meaning hasn't been validated, and it doesn't separate seller and carrier responsibility.

**Supporting evidence** ([hypothesis_log.md, B5](hypothesis_log.md#b5-seller-handover-and-the-later-delivery-stage)). The sample is single-seller orders with a known distance and valid date sequences.

| Period, shown separately | Adjusted difference, late against on-time handover | Late orders in the late-handover group | Late-handover share of orders | On-time handover share of late orders | Median handover-to-delivery days: late and on-time handover |
|---|---:|---:|---:|---:|---:|
| Before 25 April 2018 | +13.39 points (11.88 to 14.97) | 1,337 | 9.53% | 74.66% | 8.06 and 7.94 |
| From 25 April 2018 | +18.13 points (15.25 to 20.86) | 470 | 8.09% | 60.74% | 5.47 and 5.48 |

The later period's stored result reads: "Meets the percentage-point criterion; misses the minimum of 500 late orders".

**Evidence classification and robustness.** Class B, exploratory. Estimates are stable in size across runs (11.67 to 15.47 and 14.13 to 21.32), but stability doesn't confirm them. **The two periods can't be compared:** carrier timestamps change abruptly on 25 April 2018, the cause is unknown, and the difference between the estimates isn't evidence of any change in operational performance.

**Business interpretation.** Late handover is a possible warning sign, not yet validated, and not a full explanation. Most late orders in both periods had an on-time recorded handover, so handover alone can't account for them. Within each period, the unadjusted median later stage took about the same time whether handover was late or on time. Some link is also expected by construction, because a late handover leaves less of the promised time. This doesn't show who caused a delay, and nothing here can be attributed to sellers or carriers.

**Proposed management action.** Establish what the carrier timestamp records and what changed on 25 April 2018. Then monitor handover by customer state and, for single-seller orders, by seller, with stage time alongside it.

**Management decision supported.** *Is recorded handover reliable enough to use in seller management, and which process should be monitored?* If it isn't, fix the data first. If it is, decide whether to monitor sellers on it, and which sellers merit a case review.

**Illustrative owner.** Seller Operations and Logistics.

**Implementation approach**

1. Trace how the carrier date is created, using system owners and the 163 small-gap carrier-before-purchase orders from that date onward.
2. Define handover against the latest shipping limit, as in the analysis, excluding invalid date sequences.
3. Report monthly without comparing across any timestamp change.
4. Use A6's 12 sellers above the funnel limit only as a starting list for case review, since a seller's result can reflect routes and customers. 7 remain above it when peak months are excluded.

**KPIs**

- **Leading:** K13 late-handover share.
- **Lagging:** K14 share of late orders with an on-time handover, K6 state-pair late rate.
- **Guardrails:** measurable now: K3 actual time. Needs validation: K15 time allowed for handover.

**Qualitative expected benefit.** A possible earlier signal of delivery risk, resting on data whose meaning is understood.

**Validation approach.** Reconcile recorded dates with carrier or system records. Then test whether late handover gives useful warning in a later period, reporting how many late orders it would miss.

**Decision criteria**

- **Begin monitoring** once the timestamp's meaning is documented and stable.
- **Consider a seller pilot** only if handover also adds warning value in a later period, and the sellers concerned can influence it.
- **Stop or revise** if the timestamp can't be validated. Rely on total delivery time and late status, which don't use the carrier date.

**Risks and limitations.** Penalising sellers on an unvalidated field could be unfair and could shift behaviour without helping customers. Bootstrap intervals for B5 weren't independently reproduced, although the point estimates were.

### R4. Find out what goes wrong on multi-item orders

**Next step: investigation.**

**Business problem.** Multi-item orders are 9.94% of reviewed orders but hold about 21% of low ratings, and the gap appears on orders that arrive on time.

**Supporting evidence** ([hypothesis_log.md, B6](hypothesis_log.md#b6-multi-item-orders-and-low-ratings))

- **Adjusted difference:** +12.67 points (11.26 to 13.76); on-time orders +13.03 (11.73 to 14.10); late orders +6.83 (3.13 to 10.54).
- **Unadjusted, on-time orders:** 24.59% multi-item against 7.55% single-item.
- **By item count, unadjusted:** 25.40% for 2 items and 31.19% for 3 or more.
- **Exposure:** on-time multi-item orders hold 18.11% of all low ratings (B7).

**Evidence classification and robustness.** Class B, exploratory and observational, labelled "Pattern observed". The estimate is stable across sensitivity runs (10.82 to 13.61), but that doesn't confirm it. Many comparisons were made without correction, so some patterns may arise by chance.

**Business interpretation.** This pattern may matter because it appears on on-time orders as well as late ones, so delivery-speed work may not address it. Possible mechanisms are missing or incomplete items, packaging, shipment coordination, customer communication and fulfilment complexity. **All of these are unverified hypotheses.** The data has no shipment-level detail. Only 13.23% of multi-item orders have several sellers, but this doesn't rule out split shipments from one seller.

**Proposed management action.** Examine a sample of low-rated multi-item orders against a comparable set of single-item orders, and gather shipment and missing-item evidence before designing any change.

**Management decision supported.** *What evidence is needed before launching a pilot?* Decide whether multi-item orders merit their own workstream, and which of the suspected issues to examine first.

**Illustrative owner.** Fulfilment and Customer Experience.

**Implementation approach**

1. Use R2's reason classification, split by item count.
2. Check whether review comments mention missing items or separate arrivals.
3. Obtain shipment counts per order and missing-item reports from operational systems.

**KPIs**

- **Leading:** K17 split or incomplete fulfilment rate, K11 validated reasons for multi-item orders.
- **Lagging:** K16 on-time low-rating share, multi-item against single-item.
- **Guardrails:** measurable now: K18 multi-item share of orders, K12 review coverage.

**Qualitative expected benefit.** A clearer understanding of an issue that delivery metrics alone wouldn't reveal, and a better-targeted test if one is justified.

**Validation approach.** Establish whether suspected problems occur more often on multi-item orders, and whether orders with those problems have more low ratings. If a pilot follows, compare with a similar group where feasible.

**Decision criteria**

- **Design a pilot** if one mechanism is measurable, more common on multi-item orders, linked to low ratings and addressable.
- **Revise** if several mechanisms appear: address the most frequent and measurable first.
- **Stop** if the gap doesn't recur in current data, or no mechanism stands out.

**Risks and limitations.** Item count is related to sellers and order value, and the model adjusts for them only as measured. Any change shouldn't discourage customers from larger baskets. B6's interval and on-time and late splits weren't independently reproduced, although the +12.67 estimate was.

## 6. KPI and Measurement Framework

**Availability:** **Direct** means directly measurable from fields in the verified exports. **Transform** means it requires additional transformation or validation. **New** means it requires new operational data. Each KPI has one availability class: 11 Direct, 5 Transform and 2 New.

**Rules that apply to all 18 KPIs**

- **Status.** These are proposals, and none is an operational measure yet. Only K1 is an existing locked project KPI. Frequencies are for management to confirm.
- **Unit.** Every KPI is measured per order. Item rows are never counted as orders. K5 and K18 use order-level totals, and K17 would need shipment records rolled up to the order.
- **Base.** Base orders have delivered status and a delivery date. An undelivered order is neither late nor on time. Only K7 and K8 cover undelivered orders, intentionally, so they aren't invisible. The 8 delivered orders with no date are in neither group.
- **Reviews.** Review KPIs use base orders with a review, taking the latest answered review per order. An order with no review is excluded, not counted as low. K12 measures how many there are. Any future review with no answer timestamp should be left out of the timing groups.
- **Timestamps.** K13 to K15 use valid-date orders only, because they rely on the carrier date or shipping limit. The 189 flagged orders stay in the other KPIs, which don't use those fields.
- **Sellers.** K6 and any seller view use single-seller orders. The 1,275 multi-seller orders aren't divided between sellers.
- **Periods.** Numerator and denominator use the same purchase month. Review KPIs need time for reviews to arrive before a month is read.

### Shared delivery set

| KPI | Purpose | Numerator or calculation | Denominator | Unit | Frequency | Availability | Limitation |
|---|---|---|---|---|---|---|---|
| **K1** On-time rate | Lagging: promise kept | Base orders delivered on or before the estimated calendar date | Base orders | % | Monthly | Direct | Depends on the promise |
| **K2** Promised time | Leading for R1; guardrail on K1 | Median of estimated date minus purchase date, in calendar days | None: median of base orders | Days | Monthly | Direct | Delivered orders only. Can change for reasons unrelated to logistics |
| **K3** Actual time | Guardrail: real speed | Median of delivery date minus purchase date, in calendar days | None: median of base orders | Days | Monthly | Direct | The locked KPI of 12.5 days is a mean on valid dates, so the two must not be mixed |
| **K4** Early-delivery share | Guardrail: promise padding | Base orders delivered 7 or more days before the estimated date | Base orders | % | Monthly | Direct | The 7-day line is descriptive, not a validated standard |
| **K5** Freight charged | Guardrail: charge to the customer | Sum of order-level `freight_value` | Base orders | R$ per order | Monthly | Direct | A charge to customers, not a logistics cost. True cost isn't available and would need new data |

### R1: geography

| KPI | Purpose | Numerator or calculation | Denominator | Unit | Frequency | Availability | Limitation |
|---|---|---|---|---|---|---|---|
| **K6** State-pair late rate | Lagging: segment outcome | Late single-seller base orders for a seller state and customer state | Single-seller base orders for that pair | % | Monthly; weekly during high-volume periods | Direct | Not a transport route. Unadjusted, and small pairs are noisy |
| **K7** Overdue open orders | Leading: early sign of lateness | Open orders past their estimated date at the snapshot | Open orders at the snapshot, by customer state | % | Weekly | New | Needs dated snapshots: the data holds one status per order. "Open" must be defined and exclude cancelled orders |
| **K8** Non-delivery rate | Guardrail: outcomes the base excludes | Orders with any status other than delivered | All orders, by customer state and purchase month | % | Monthly | Transform | Wider than the base, intentionally. Mixes cancelled and unavailable orders with statuses that may still be open, such as shipped, which need separating |

### R2: customer experience

| KPI | Purpose | Numerator or calculation | Denominator | Unit | Frequency | Availability | Limitation |
|---|---|---|---|---|---|---|---|
| **K9** Low-rating share by group | Lagging: customer outcome | Orders rated 1 or 2 stars in each group: on time, late answered before delivery, late answered after delivery | Reviewed base orders in that group | % | Monthly, by purchase month | Direct | Groups are self-selected. Timing doesn't show when a rating was formed |
| **K10** Late reviews answered before delivery | Leading: survey timing | Reviewed late orders with an answer timestamp before the delivery timestamp | Reviewed late orders | % | Monthly | Direct | Doesn't show when an opinion was formed, whether the order had been received, or what triggered the review |
| **K11** Low ratings with a validated reason | Leading: diagnostic coverage | Sampled low-rated orders given a reason from their comment and confirmed by a second reviewer | All sampled low-rated orders, including those with no comment | % | Each review cycle | Transform | Comment coverage hasn't been assessed. Adding complaints or returns would need new data, and isn't part of this definition |
| **K12** Review coverage | Guardrail: selection | Base orders with a review | Base orders, separately for late and on time | % | Monthly | Direct | Non-reviewers' views can't be observed |

### R3: handover

| KPI | Purpose | Numerator or calculation | Denominator | Unit | Frequency | Availability | Limitation |
|---|---|---|---|---|---|---|---|
| **K13** Late-handover share | Leading: possible early signal | Valid-date orders with a carrier date after the order's latest shipping limit | Valid-date base orders | % | Monthly | Transform | Not validated for monitoring, and not comparable across 25 April 2018. Doesn't separate seller and carrier responsibility. Wider than B5's sample, to cover all valid-date orders |
| **K14** Late orders with on-time handover | Lagging: how much handover misses | Late valid-date orders with an on-time handover | Late valid-date orders | % | Monthly | Transform | Same limits as K13 |
| **K15** Time allowed for handover | Guardrail: limit padding | Median of latest shipping limit minus purchase date, in calendar days | None: median of valid-date orders | Days | Monthly | Transform | Hasn't been reported or validated in this project. Uses the latest limit across an order's items |

### R4: multi-item orders

| KPI | Purpose | Numerator or calculation | Denominator | Unit | Frequency | Availability | Limitation |
|---|---|---|---|---|---|---|---|
| **K16** On-time low-rating share by order type | Lagging: multi-item gap | Low-rated on-time orders of each type: multi-item and single-item | Reviewed on-time orders of that type | %, with the gap in points | Monthly | Direct | Unadjusted. Adjusted checks are periodic analysis |
| **K17** Split or incomplete fulfilment | Leading: suspected mechanism | Multi-item orders with more than one shipment or a reported missing item | Multi-item orders with shipment records | % | Monthly | New | No shipment records exist in this data. A missing record must not count as a single shipment |
| **K18** Multi-item share | Guardrail: basket behaviour | Base orders with two or more item rows | Base orders | % | Monthly | Direct | Also moves with assortment and promotions |

### Historical reference values, not baselines

These describe 2016 to 2018. **They aren't baselines for an intervention.** A real pilot needs a current baseline measured on these definitions, and any target should come from management agreement and a feasibility assessment.

| KPI | Historical value | Note |
|---|---:|---|
| Delivered orders; with a date | 96,478; 96,470 | Locked project KPIs |
| On-time; late | 89,936; 6,534 | Locked project KPIs |
| K1 On-time rate | 93.23% | Promise fell in late 2018, so this isn't a stable standard |
| Average delivery time | 12.5 days | Mean on valid dates |
| K2 Median promised time; K3 median actual time | 24 days; 10 days | Across all periods |
| K4 Early by 7 or more days | 78.93% | |
| K10 Late reviews answered before delivery | 70.10% | |
| Multi-item share of reviewed orders | 9.94% | K18 uses all base orders, so this is a different denominator |

### How these KPIs could improve without real improvement

| KPI | How it could improve falsely | Read it with |
|---|---|---|
| **K1** On-time rate, **K6** state-pair late rate | Longer promises reduce "late" orders without faster delivery | K2, K3, K4 and K9. From November 2017 to August 2018, monthly median promises ranged from 14 to 28 days and median actual time from 7 to 14 days |
| **K2** Promised time | Shorter promises look better to customers but may create lateness | K1, K3, K9 |
| **K3** Actual time | Speed may be bought through higher freight charges or logistics spending, or through excluding difficult orders | K5 for charges and K8 for excluded orders. Real logistics cost needs new data, so it can't be checked today |
| **K9** Low-rating share | Changing when surveys are sent can move scores without changing experience | K10, K12. Record any change to the survey process |
| **K13** Late-handover share | Longer shipping limits, or a change in how the date is recorded | K15, K3 and any timestamp change log |
| **K16** Multi-item gap | Discouraging multi-item baskets or changing how orders are counted | K18, K12 |

**Rule for delivery reporting:** K1 is never reported alone. It appears with K2, K3, K5 and K9, all measurable now, and with K8 once validated.

## 7. Implementation and Validation Roadmap

Phases are ordered by evidence, not by date. No timeline, budget or staffing is proposed, and each phase needs management approval.

| Phase | Work | Possible from the historical data | Needs current access and stakeholder approval | Exit condition |
|---|---|---|---|---|
| **1. Monitoring and investigation** | Agree KPI definitions, build the split low-rating and state-pair views, and identify priority segments | Definitions, state-pair tables, three-group ratings, comment coverage check | Current baselines on the same definitions | Definitions agreed; current gaps measured |
| **2. Mechanism validation** | Test suspected explanations. Trace the carrier timestamp, document the survey trigger, classify reasons, gather shipment and capacity records | Early reason classification from historical comments | Carrier, route, capacity, shipment, survey and complaint data | A specific mechanism is supported, or none is |
| **3. Pilot design and evaluation** | Only where justified. Define the target population, intervention, success indicators, guardrails, evaluation approach and criteria for continuing or revising | Nothing: the data can only suggest candidates | Everything. A controlled comparison where feasible, without assuming one is available | Pre-agreed criteria read at the end of the pilot |
| **4. Scale, revise or stop** | Broaden only if the pilot and its guardrails support it | Nothing | Management decision on current evidence | Documented decision |

## 8. Risks, Limitations and Open Questions

### Unresolved audit items

None of these is resolved by this document. IDs in this table are audit items, so R7 here isn't a recommendation.

| Item | What it is | Material to recommendations? | Treatment here |
|---|---|---|---|
| **R7** | A6 and A7 wording | Yes, for what's deprioritised | The approved wording is applied, and the item stays listed until that wording is reviewed. Point estimates are below the criteria and intervals reach them, so neither finding is called negligible |
| **D7** | Answer timing and delay length are almost inseparable | Yes, for recommendation R2 | No survey trigger is stated as fact. Documenting it is an R2 action, and A3 stays unresolved |
| **L2** | Undelivered orders aren't bounded | Yes, for recommendations R1 and R2 | Disclosed, with K8 as a guardrail. 2,971 orders are outside the base, and no check bounds their effect. Orders with any status other than delivered are 3.91% in RJ and 2.98% in SP |
| **C7** | Document generators are outside the repository | Low | The main figures here were checked against stored results, which those generators don't produce. Document tables can't yet be regenerated from the repository |
| **T10** | Power BI measures weren't executed | Not for the evidence; yes before any dashboard use | KPI definitions come from the methodology, SQL and Python. Measures need running before they support monitoring |
| **T11** | The live database wasn't queried | Low | Stored exports were tested indirectly through a clean load of the raw files. This isn't verification of the live database |

### Other qualifications

- **Observational interpretation.** There's no randomisation. Unmeasured differences may explain any association.
- **No independent sample.** The data was previewed before the plan was written, and there's no holdout.
- **Survey timing.** Neither the answer timestamp nor the creation date shows when a customer formed or submitted a rating.
- **Timestamp discontinuity.** Handover and handover-to-delivery timing aren't comparable across 25 April 2018, and the cause is unknown. Late status and total delivery time don't use the carrier date.
- **Peak months.** They were chosen using the outcome, with at most one complete year of data, so no seasonal claim is made.
- **Scope of the audit.** The audit compared results using separately written code on the raw files, but the same AI assistant wrote the project code and the audit. A misreading shared by both wouldn't be detected, and human review would add something it can't. It didn't examine the live database or run Power BI. Several sensitivity scenarios and some bootstrap intervals weren't independently recomputed.
- **Statistical reproducibility.** The stored Class B results were generated with 8 threads and the earlier version with 4. Six analytic Wald p-values differ at full precision, with no change to any estimate, interval or label. No recommendation depends on those digits, and exact byte-for-byte reproducibility across thread configurations isn't claimed.
- **Simulation resolution.** A6's p-value comes from a simulation. It's an upper limit set by the number of draws (raw at most 0.0002, Holm at most 0.0006, at 5,000 draws), not an exact value and not zero.
- **Generalisation.** One marketplace, one period. These results may not apply beyond 2016 to 2018.

### Open questions for a real operator

1. How are review surveys triggered, and did this change over time?
2. What does the carrier date record, and what changed on 25 April 2018?
3. How are delivery promises set, and why did they fall in late 2018?
4. What capacity, carrier or demand changes occurred in November 2017 and February to March 2018?
5. How often do multi-item orders ship separately or arrive incomplete?
6. What do undelivered orders look like, and would including them change any priority?

## 9. Evidence Traceability Table

Sources: **Log** is [hypothesis_log.md](hypothesis_log.md), **Sens** is [sensitivity_results.md](sensitivity_results.md), **Audit** is [independent_audit.md](independent_audit.md). JSON files are stored outputs in `data/processed/`. Values are points unless stated. Audit item IDs are written as "audit R2", to separate them from recommendations. "Reproduced" means independently recomputed in the audit. "Not recomputed" means the audit doesn't list it among reproduced figures.

| ID | Value | Source | Class | Robustness qualification | Audit limitation | Used in |
|---|---|---|---|---|---|---|
| KPIs | 96,478; 96,470; 89,936; 6,534; 93.23%; 12.5 days | `methodology.md`; Audit, locked KPI table | Locked KPI | Not applicable | Reproduced from raw files; live database and Power BI not verified | Section 6 |
| A1 | +7.46 (5.88 to 9.13) | Log A1; `class_a_results.json` | A, Supported (provisional) | Robust; size depends on period | Reproduced. Audit R2: don't quote without the period split | R1 |
| A1 overlap | +8.92 to +9.46; 7.8% and 76.0% in-state; about two-thirds of RJ orders from SP sellers (8,021 of 12,144, derived) | Sens A1; Log A1 | A, required exploratory check | Doesn't count as confirmation | Gaps reproduced; shares not recomputed | R1 |
| A1 S8a | +3.57 (2.54 to 4.60) | Log robustness; Sens | A, sensitivity | Different-question check | Estimate reproduced | R1 |
| B2 | +23.46 (19.64 to 27.50); +3.04 (2.09 to 4.19) | Log B2; `class_b_results.json` | B | Peak months selected from outcome; range for the difference 18.11 to 21.69 | Estimates reproduced; intervals not recomputed | R1 |
| B2 exposure | 57.61% of RJ late orders in peak months (855) | Log B2; `class_b_results.json` | B | Sample of RJ and SP orders | Not recomputed | R1 |
| B2 seller-state table | See R1 table. Single-seller orders, with no distance requirement | Log B2; `class_b_results.json` | B | Unadjusted | Not recomputed | R1 |
| State view | RJ 22.88% of late orders; 12.80% of orders | Log Class C; `descriptive_results.json` | C | Descriptive | Inspected, not recomputed | R1 |
| Monthly | Jan 2018: 7,069 orders, 5.70%, 26 and 12 days. Mar 2018: 7,003, 18.96%, 22 and 13 days. Feb and Mar 2017: 2.96%, 4.56%. Feb 2018: 14.13% | Log B1 and Class C | C, B | Descriptive comparison | Inspected, not recomputed | R1 |
| Audit L2 | 3.91% and 2.98% with any status other than delivered; 2,971 outside base | Audit L2; `independent_audit_results.json` | Audit measure | Not a tested difference | Open item | R1, R2 |
| A2 | +51.04 (49.58 to 52.28); 62.42% and 9.27% | Log A2; `class_a_results.json` | A, Supported (provisional) | Robust as an observational association; answer timing is an important limitation | Reproduced | R2 |
| B3 | +70.07 (68.49 to 71.45); +9.94 (8.26 to 11.62) | Log B3; `class_b_results.json` | B | Stable; after-arrival size depends on definitions (6.69 to 17.61) | Reproduced. D7 open | R2 |
| B3 share | 70.10% | Log B3; `class_b_results.json` | B | Recorded timestamps only | Not recomputed | R2, K10 |
| B7 | 67.54% (65.86 to 69.20); 8,289 of 12,272; 49.44% | Log B7; `class_b_results.json` | B | Share of counts; range 63.31% to 77.58% | 67.54% reproduced; intervals not recomputed | R2 |
| Coverage | 2.34% and 0.55% unreviewed | Audit L2 | Audit measure | Not a tested difference | Reproduced | R2 |
| A3 | +42.10 (39.04 to 45.22) | Log A3; `class_a_results.json` | A, Inconclusive (provisional) | Unresolved | Reproduced. Audit R4: don't claim a fall at 15+ days | Section 4 |
| A4 | +0.59 (−0.49 to 1.50); +2.47; +2.52 (0.22 to 4.82) | Log A4; `class_a_results.json`; Log robustness | A, Unsupported (provisional) | Robustly unsupported under the prespecified comparison | Reproduced | Section 4 |
| A5 | +2.16 (1.27 to 3.01); +0.97 (−0.01 to 1.94) | Log A5; Sens A5 | A, Supported (provisional), close to criterion | Sensitive; judgement incorporates an exploratory check | Reproduced | Section 4 |
| A6 | +6.97 (2.48 to 10.66); 12 above funnel; 7 excluding peak | Log A6; Sens; `class_a_results.json` | A, Detectable, not practically important (provisional) | Below criterion in all tested point estimates; intervals sometimes reach it | Reproduced; audit R7 open; p-value is a simulation limit | Section 4, R3 |
| A7 | 3.69 (2.88 to 6.90); p = 0.054 restricted | Log A7; `class_a_results.json` | A, Detectable, not practically important (provisional) | Below criterion in all tested point estimates; intervals reach it | Estimate reproduced; bootstrap not recomputed; audit R7 open | Section 4 |
| B5 before | +13.39 (11.88 to 14.97); 1,337; 9.53%; 74.66%; 8.06 and 7.94 | Log B5; `class_b_results.json` | B | Stable, 11.67 to 15.47; not comparable across periods | Estimate reproduced; interval and stage figures not recomputed | R3 |
| B5 from | +18.13 (15.25 to 20.86); 470; 8.09%; 60.74%; 5.47 and 5.48 | Log B5; `class_b_results.json` | B | Stable, 14.13 to 21.32; misses the 500-order minimum | Estimate reproduced; interval and stage figures not recomputed; audit D2 | R3 |
| Timestamps | 163 small-gap orders; change on 25 April 2018 | `data_quality_assessment.md`; Audit D2, D4 | Data quality | Cause unknown | Reproduced | R3 |
| B6 | +12.67 (11.26 to 13.76); +13.03 (11.73 to 14.10); +6.83 (3.13 to 10.54) | Log B6; `class_b_results.json` | B | Stable, 10.82 to 13.61 | +12.67 reproduced; intervals and splits not recomputed | R4 |
| B6 detail | 24.59% and 7.55%; 25.40% and 31.19%; 9.94%; 13.23% | Log B6; `class_b_results.json` | B | Unadjusted | Not recomputed | R4 |
| B6 and B7 share | About 21% (2,548 of 12,272, derived); 18.11% | Log B6 and B7 | B | Share of counts | Not recomputed | R4 |
| Promise | 24 and 10 days; 78.93% early by 7+ days; monthly medians 14 to 28 and 7 to 14 days, Nov 2017 to Aug 2018 | Log Class C; `descriptive_results.json` | C | Descriptive; promise not stable | Inspected, not recomputed | Section 4, 6 |
| Populations | 95,824 reviewed; 51,984 in A1; 96,281 valid-date; 1,275 multi-seller | Log diagnostics; `methodology.md`; Audit C2, C3, D4 | Definitions | Not applicable | Reproduced | Sections 2, 5, 6 |
| Growth | +141.1%; 99.2% from volume | Log Class C; `descriptive_results.json` | C | Descriptive; not a forecast | Reproduced | Section 4 |

## 10. Conclusion

This analysis doesn't justify rolling out a solution. Its value is in directing the next decisions, and in showing where not to start. Each recommendation states what would move it forward, change it or stop it, and those decisions need current data and management's own thresholds.
