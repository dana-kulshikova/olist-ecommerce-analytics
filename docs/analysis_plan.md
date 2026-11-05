# Analysis Plan: Technical Reference

The technical companion to [methodology.md](methodology.md), which explains the labels, screening criteria, data rules and limitations. Class A questions are pre-specified, Class B are exploratory and Class C are descriptive.

## What was previewed

A read-only scan of the source CSVs previewed these unadjusted results before this plan was written:

- Late rates by state, month, seller, category and distance band
- Review scores by delivery status, delay band, answer timing and item count
- Seller handover status and stage durations
- Sales by order volume and average order value

It used no regression, adjusted estimates or sensitivity analysis. Those remain unknown until the main analysis. New analysis ideas arising later are logged as Class B, with the date added.

## Metric expressions

Column names are shortened here.

| Metric | PostgreSQL | Python (pandas) | Power BI (DAX) |
|---|---|---|---|
| Delivered with a date | `order_status = 'delivered' AND order_delivered_customer_date IS NOT NULL` | `status.eq("delivered") & delivered.notna()` | `[order_status] = "delivered"`, `NOT(ISBLANK([order_delivered_customer_date]))` |
| On time | `delivered::date <= estimated::date` | `delivered.dt.normalize() <= estimated.dt.normalize()` | `INT([delivered]) <= INT([estimated])` |
| Late | `delivered::date > estimated::date` | `delivered.dt.normalize() > estimated.dt.normalize()` | `INT([delivered]) > INT([estimated])` |
| Days late | `delivered::date - estimated::date` | `(delivered.dt.normalize() - estimated.dt.normalize()).dt.days` | `INT([delivered]) - INT([estimated])` |
| Low rating | `review_score <= 2` | `score.le(2)` | `[review_score] <= 2` |
| Answered before arrival | `review_answer_timestamp < delivered` | `answered.lt(delivered)` | `[review_answer_timestamp] < [delivered]` |

New Power BI measures must return the same values as SQL and Python, and they'll be documented with their filter behaviour in `dax_measures.md`.

## Additional data rules

- **Several reviews:** latest answered, then latest created, then review ID.
- **Several sellers:** for clustering only, an order belongs to the seller of its highest-priced item. Nothing is divided between sellers.
- **Category ties:** the highest-priced item, then the lowest item number.
- **Distance:** median ZIP-prefix positions, within Brazil's bounds.
- **Stage timing:** provisional exclusions are in `methodology.md` until the 197 flagged orders have been investigated. That work covers types and overlap, gap sizes and times of day, source against stored values, and clustering by month, seller and state.

## Statistical conventions

- **Reported for every hypothesis:** group sizes, effect size, 95% confidence interval and a business interpretation. P-values are secondary and never decide a result alone.
- **Rates:** Wilson 95% intervals.
- **Adjusted differences:** logistic regression, converted by standardisation to an adjusted risk difference in percentage points, with odds ratios as a secondary measure.
- **Uncertainty in models:** standard errors clustered by seller, since orders from one seller aren't independent. Risk-difference intervals use a seller-level cluster bootstrap with 500 replicates and a fixed random seed.
- **Multiple testing:** Holm correction across the seven Class A tests. Class B results don't enter this family, and their p-values are unadjusted and descriptive.

## Class A: pre-specified questions

### A1. RJ late rate compared with SP

- **Prediction:** RJ is higher after adjustment.
- **Outcome:** late (yes or no).
- **Groups:** customers in RJ and SP, single-seller orders with a distance.
- **Method:** logistic regression adjusted for distance band, purchase month, item count, order value and whether seller and customer share a state. Freight is left out because it may lie on the path being studied.
- **Effect size:** adjusted risk difference, with odds ratio as secondary.
- **Confidence interval:** cluster bootstrap for the risk difference; clustered standard errors for the odds ratio.
- **Screening criterion:** 2 points and at least 500 late orders.
- **Note:** RJ customers are rarely served by in-state sellers, so overlap is limited. A check restricted to SP sellers and to overlapping distance bands is required.

### A2. Late delivery and low ratings

- **Prediction:** late orders have a higher low-rating share.
- **Outcome:** low rating; the full score distribution and mean score are also reported.
- **Groups:** late and on-time orders with a review.
- **Method:** logistic regression adjusted for purchase month, customer state, item count, order value, category group and multi-seller status.
- **Effect size:** adjusted risk difference, with mean score difference and odds ratio as secondary.
- **Confidence interval:** cluster bootstrap.
- **Screening criterion:** 5 points of low-rating share.
- **Note:** B3 shows why this overall result must be read alongside answer timing.

### A3. Longer delays and worse ratings

- **Prediction:** low-rating share rises with delay length.
- **Outcome:** low rating.
- **Groups:** late orders with a review in the bands 1–3, 4–7, 8–14 and 15+ days late.
- **Method:** logistic trend across ordered bands, adjusted as in A2, with band estimates alongside.
- **Effect size:** adjusted risk difference between adjacent bands and between 15+ and 1–3 days.
- **Confidence interval:** cluster bootstrap.
- **Screening criterion:** 5 points between adjacent bands.

### A4. Distance and late delivery

- **Prediction:** longer distance is linked to a higher late rate.
- **Outcome:** late.
- **Groups:** distance bands 0–100, 100–300, 300–600, 600–1,000, 1,000–2,000 and 2,000+ km, on single-seller orders.
- **Method:** logistic regression adjusted for purchase month, customer state, item count and order value.
- **Effect size:** adjusted risk difference between 600–1,000 km and 0–100 km, with the full band profile.
- **Confidence interval:** cluster bootstrap.
- **Screening criterion:** 2 points and at least 500 late orders.
- **Note:** adjusting for customer state removes some distance variation, so the result is also reported without it.

### A5. Freight cost and late delivery

- **Prediction:** higher freight is linked to a higher late rate.
- **Outcome:** late.
- **Groups:** freight quartiles.
- **Method:** logistic regression adjusted for distance band, purchase month, item count and order value.
- **Effect size:** adjusted risk difference between the highest and lowest quartiles.
- **Confidence interval:** cluster bootstrap.
- **Screening criterion:** 2 points and at least 500 late orders.
- **Note:** freight reflects weight, size and route, so a link doesn't show that freight itself affects delivery.

### A6. Seller concentration

- **Prediction:** a small share of sellers holds a disproportionate share of late orders.
- **Outcome:** late orders per seller, on single-seller orders.
- **Groups:** the top 10% of sellers with at least 100 orders, ranked by late orders, against the remaining ones.
- **Method:** concentration analysis, plus a funnel check of each seller's observed and expected late orders given purchase month.
- **Effect size:** late-order share minus order share; number of sellers outside the funnel limits.
- **Confidence interval:** seller-level bootstrap.
- **Screening criterion:** a gap of 10 points.
- **Note:** ranking on the same data flatters the top group, so sellers are also ranked on one half of the orders and evaluated on the other.

### A7. Category differences

- **Prediction:** late rates differ materially between categories.
- **Outcome:** late.
- **Groups:** categories with at least 1,000 orders.
- **Method:** logistic regression adjusted for purchase month, customer state and distance band.
- **Effect size:** spread between the highest and lowest adjusted rates; Cramér's V for the unadjusted table.
- **Confidence interval:** cluster bootstrap for the spread.
- **Screening criterion:** a 5-point spread.

## Class B: exploratory

These were shaped by the preview or raised afterwards. They can suggest what to investigate and test, but they can't confirm anything.

### B1. Late orders are concentrated in peak months

- **Outcome:** late.
- **Groups:** peak months, defined as at least 100 orders and a late rate of 10% or more, against other months. This rule was written after seeing the data, and it selects Nov 2017, Feb 2018 and Mar 2018.
- **Method:** monthly rates and shares.
- **Effect size:** share of late orders minus share of orders; rate difference.
- **Confidence interval:** Wilson for monthly rates; bootstrap for shares.
- **Screening criterion:** 2 points and at least 500 late orders.

### B2. RJ's gap changes between peak and other months

- **Outcome:** late.
- **Groups:** RJ and SP customers, in peak and other months.
- **Method:** the A1 model with a state-by-peak interaction, plus an SP-seller comparison of RJ, MG, PR, ES and BA.
- **Effect size:** adjusted RJ–SP difference in each period, and the difference between those differences.
- **Confidence interval:** cluster bootstrap.
- **Screening criterion:** 2 points of change and at least 500 late orders.

### B3. Answer timing and low ratings

- **Outcome:** low rating.
- **Groups:** on-time orders; late orders answered before arrival; late orders answered after arrival.
- **Method:** the A2 model, with those three groups in place of late status.
- **Effect size:** adjusted risk differences against on-time orders; mean score difference.
- **Confidence interval:** cluster bootstrap.
- **Screening criterion:** 5 points.
- **Note:** the groups are self-selected, and answer timing is linked to delay length, so this isn't a clean experiment.

### B4. Delay bands split by answer timing

- **Outcome:** low rating.
- **Groups:** the A3 delay bands, separately for answers before and after arrival.
- **Method:** band estimates with intervals. Trends only where group sizes allow it.
- **Effect size:** risk difference between adjacent bands within each timing group.
- **Confidence interval:** Wilson and cluster bootstrap.
- **Screening criterion:** 5 points.
- **Note:** long-delay reviews answered after arrival are few (19 at 15+ days in the preview), so these bands may stay inconclusive.

### B5. Seller handover and the later delivery stage

- **Outcome:** late; handover days and handover-to-delivery days.
- **Groups:** orders with a late and an on-time seller handover.
- **Method:** the A4 model with handover status added; median stage times on valid date sequences.
- **Effect size:** adjusted risk difference; share of all late orders from each group; difference in median stage days.
- **Confidence interval:** cluster bootstrap.
- **Screening criterion:** 2 points and at least 500 late orders.
- **Note:** this describes which stage a delay is linked to. It doesn't identify who caused it or attribute anything to carriers.

### B6. Multi-item orders and low ratings

- **Outcome:** low rating.
- **Groups:** multi-item and single-item orders with a review.
- **Method:** logistic regression adjusted for late status, answer timing, purchase month, customer state, order value, category group and multi-seller status. Includes a check of whether the gap differs between late and on-time orders.
- **Effect size:** adjusted risk difference; mean score difference.
- **Confidence interval:** cluster bootstrap.
- **Screening criterion:** 5 points.
- **Note:** the data has no shipment-level detail, so reasons such as split deliveries can't be tested here. Items, sellers and order value are related, so these will be checked for overlap.

### B7. Low ratings on on-time orders

- **Outcome:** share of all low ratings.
- **Groups:** on-time and late orders; multi-item and single-item orders within them.
- **Method:** share breakdown.
- **Effect size:** share of low ratings by group, in orders and percentage points.
- **Confidence interval:** bootstrap.
- **Screening criterion:** at least 10% of all low ratings.

## Class C: descriptive

| Topic | Measurement | Guardrail |
|---|---|---|
| Sales trend | Monthly sales and orders | Sparse 2016 and incomplete late 2018 flagged |
| Growth | Jan–Aug 2017 to Jan–Aug 2018, split into order-volume and order-value effects | Same months only, on delivered orders |
| Geographic concentration | Sales and late orders by state | Rates shown beside absolute counts |
| Category performance | Sales, orders and late orders | Top categories with sample sizes |
| Promise and delivery | Estimated window and actual duration by state and month | Lateness is measured against the promise, so this is context and not a driver test |
| Seasonality | Month-by-month pattern | One complete year at most, so no seasonal claim will be made |
| Priority view | Late rate, late orders, low ratings and sales by state | Exposure figures only, with no estimated savings or ROI |

## Sensitivity analyses

Each result reports the alternative estimate, its interval, and the change in size and direction from the primary analysis, then receives a robustness label as defined in `methodology.md`.

| ID | Choice tested | Primary | Alternatives | Applies to |
|---|---|---|---|---|
| S1 | Several reviews | Latest answered | Earliest review; excluding orders with several reviews | All review results |
| S2 | Repeated review IDs | Kept | Excluded | All review results |
| S3 | Invalid date sequences | Per `methodology.md` after investigation | Excluded everywhere; only delivery-before-carrier excluded; only carrier-before-purchase excluded | Late-rate and stage results |
| S4 | Daylight-saving shift | PostgreSQL values | Source CSV values; the affected orders excluded | Timing results |
| S5 | Late definition | Calendar date | Full timestamp (previous logic); 2 or more days late | All late results |
| S6 | Low rating | 1–2 stars | 1 star only; 1–3 stars; mean score | All review results |
| S7 | Several sellers | Excluded from seller and distance analysis | Assigned to the highest-priced item's seller | A1, A4, A5, A6, B5 |
| S8 | Period | All months | Excluding peak months; excluding 2016; excluding purchases from July 2018 onward, as late orders may not have been delivered yet | All late and review results |
| S9 | Answer timing | Answer timestamp | Survey creation date | B3, B4, B6 |
| S10 | Distance | Median position | Mean position; excluding extreme distances | A1, A4, A5 |
| S11 | Category | Highest-priced item | First item; excluding `unknown` | A2, A7 |
| S12 | Missing reviews | Reviewed orders only | Best- and worst-case bounds for unreviewed orders | A2, A3 |
| S13 | Model form | Logistic with clustered errors | Linear probability model; heteroskedasticity-robust errors | All adjusted results |

Some alternatives test a definition rather than a neutral variation. Excluding peak months, for example, asks a different question, and its result is interpreted that way.

## Reproducible environment

The project uses Python 3.13. `requirements.txt` pins every package, including indirect dependencies, and contains no pre-releases. A clean environment built from this file was verified to match the working one.

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
```

`python/clean_reviews.py` and `python/verify_figures.py` still need only the standard library. The virtual environment and analysis exports are ignored by Git.
