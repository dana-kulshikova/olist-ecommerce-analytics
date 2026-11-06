-- Olist E-Commerce Analytics | Latest answered review per order, for the Power BI review table
-- Database: PostgreSQL (ecommerce_bi). Run after sql/01_schema.sql and the review import.
--
-- Purpose: one row per order that has a review, carrying the review selected by the same rule the
-- analysis export uses (sql/04_delivery_analysis.sql, ranked_reviews, latest_rank = 1):
--   1. latest review_answer_timestamp
--   2. then latest review_creation_date
--   3. then highest review_id
-- The ORDER BY is kept exactly as in sql/04, including PostgreSQL's default NULLS FIRST for DESC.
--
-- Source: public.olist_order_reviews_cleaned (review_id, order_id, review_score, review_creation_date,
-- review_answer_timestamp). Reads only; changes no table. public.bi_orders is not touched.
-- review_id IS NOT NULL reproduces sql/04's inner join to review_id_use, which drops NULL review IDs.
-- order_id IS NOT NULL drops nothing sql/04 could use, since a NULL order_id can't match an order.
--
-- Output columns:
--   order_id                   character varying, one row per order (unique by construction)
--   latest_review_score        integer, 1 to 5
--   latest_review_answered_ts  timestamp without time zone. When the review answer was recorded,
--                              not necessarily when the customer submitted the review.
--
-- Validated on the project database (docs/powerbi_validation.md): 98,673 rows and 98,673 distinct
-- order IDs; 768 orders in bi_orders have no review; 0 review rows without a matching order;
-- 0 differences, by review_id, from the sql/04 selection; 0 differences in score, answer timestamp
-- or creation date from the audited export, across all 98,673 orders.
--
-- CREATE VIEW, not CREATE OR REPLACE, so an existing object is never overwritten. To check first:
--   SELECT to_regclass('public.bi_order_reviews');   -- NULL means the view doesn't exist yet

CREATE VIEW public.bi_order_reviews AS
WITH ranked_reviews AS (
    SELECT
        r.order_id,
        r.review_score,
        r.review_answer_timestamp,
        ROW_NUMBER() OVER (
            PARTITION BY r.order_id
            ORDER BY
                r.review_answer_timestamp DESC,
                r.review_creation_date DESC,
                r.review_id DESC
        ) AS latest_rank
    FROM public.olist_order_reviews_cleaned r
    WHERE r.review_id IS NOT NULL
      AND r.order_id IS NOT NULL
)
SELECT
    order_id,
    review_score AS latest_review_score,
    review_answer_timestamp AS latest_review_answered_ts
FROM ranked_reviews
WHERE latest_rank = 1;
