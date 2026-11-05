-- Olist E-Commerce Analytics | Read-only export for the delivery and satisfaction analysis
-- Database: PostgreSQL (ecommerce_bi). Run with psql from the repository root, as described in
-- docs/analysis_plan.md. Output goes to data/processed/, which Git ignores.
--
-- This script changes nothing: it runs inside a READ ONLY transaction and ends with ROLLBACK.
-- It contains no review text. Timestamps are exported as text, so client display settings
-- can't alter them.
--
-- Rules follow docs/methodology.md. On several reviews, both the latest answered and the
-- earliest review are exported. "Primary item" means the highest-priced item, then the lowest
-- item number.

\set ON_ERROR_STOP on
BEGIN TRANSACTION READ ONLY;

-- 1. Validation figures, compared with the locked KPI values before any analysis
\o data/processed/validation.csv
COPY (
    WITH sales AS (
        SELECT
            order_status,
            order_id,
            product_sales,
            valid_delivery_dates,
            order_purchase_timestamp,
            order_delivered_customer_date,
            order_estimated_delivery_date
        FROM public.bi_orders
    ),
    delivered AS (
        SELECT * FROM sales WHERE order_status = 'delivered'
    ),
    dated AS (
        SELECT * FROM delivered WHERE order_delivered_customer_date IS NOT NULL
    )
    SELECT 'orders_in_view' AS metric, COUNT(*)::numeric AS value FROM sales
    UNION ALL SELECT 'delivered_orders', COUNT(*) FROM delivered
    UNION ALL SELECT 'delivered_with_date', COUNT(*) FROM dated
    UNION ALL SELECT 'on_time_orders', COUNT(*) FILTER (WHERE order_delivered_customer_date::date <= order_estimated_delivery_date::date) FROM dated
    UNION ALL SELECT 'late_orders', COUNT(*) FILTER (WHERE order_delivered_customer_date::date > order_estimated_delivery_date::date) FROM dated
    UNION ALL SELECT 'on_time_rate_pct', ROUND(100.0 * COUNT(*) FILTER (WHERE order_delivered_customer_date::date <= order_estimated_delivery_date::date) / COUNT(*), 2) FROM dated
    UNION ALL SELECT 'total_product_sales', ROUND(SUM(product_sales), 2) FROM delivered
    UNION ALL SELECT 'average_order_value', ROUND(SUM(product_sales) / COUNT(DISTINCT order_id), 2) FROM delivered
    UNION ALL SELECT 'average_delivery_days', ROUND(AVG(order_delivered_customer_date::date - order_purchase_timestamp::date), 2) FROM delivered WHERE valid_delivery_dates
    UNION ALL SELECT 'valid_delivery_dates_false', COUNT(*) FILTER (WHERE NOT valid_delivery_dates) FROM delivered
) TO STDOUT WITH (FORMAT csv, HEADER true);

-- 2. One row per order, for all statuses
\o data/processed/orders_analysis.csv
COPY (
    WITH ranked_items AS (
        SELECT
            i.order_id,
            i.seller_id,
            i.product_id,
            ROW_NUMBER() OVER (PARTITION BY i.order_id ORDER BY i.price DESC, i.order_item_id ASC) AS price_rank,
            ROW_NUMBER() OVER (PARTITION BY i.order_id ORDER BY i.order_item_id ASC) AS item_rank
        FROM public.olist_order_items_dataset i
    ),
    item_summary AS (
        SELECT
            order_id,
            COUNT(DISTINCT seller_id) AS seller_count,
            MAX(shipping_limit_date) AS latest_shipping_limit
        FROM public.olist_order_items_dataset
        GROUP BY order_id
    ),
    review_id_use AS (
        SELECT review_id, COUNT(*) AS rows_using_id
        FROM public.olist_order_reviews_cleaned
        GROUP BY review_id
    ),
    ranked_reviews AS (
        SELECT
            r.order_id,
            r.review_score,
            r.review_creation_date,
            r.review_answer_timestamp,
            u.rows_using_id,
            COUNT(*) OVER (PARTITION BY r.order_id) AS review_count,
            ROW_NUMBER() OVER (PARTITION BY r.order_id
                ORDER BY r.review_answer_timestamp DESC, r.review_creation_date DESC, r.review_id DESC) AS latest_rank,
            ROW_NUMBER() OVER (PARTITION BY r.order_id
                ORDER BY r.review_answer_timestamp ASC, r.review_creation_date ASC, r.review_id ASC) AS earliest_rank
        FROM public.olist_order_reviews_cleaned r
        JOIN review_id_use u ON u.review_id = r.review_id
    )
    SELECT
        b.order_id,
        b.order_status,
        b.customer_state,
        c.customer_zip_code_prefix,
        b.order_purchase_timestamp::text AS purchase_ts,
        b.order_approved_at::text AS approved_ts,
        b.order_delivered_carrier_date::text AS carrier_ts,
        b.order_delivered_customer_date::text AS delivered_ts,
        b.order_estimated_delivery_date::text AS estimated_ts,
        b.product_sales,
        b.freight_value,
        b.items_count,
        b.payment_total,
        b.valid_delivery_dates,
        s.seller_count,
        s.latest_shipping_limit::text AS latest_shipping_limit_ts,
        primary_item.seller_id AS primary_seller_id,
        seller.seller_state AS primary_seller_state,
        seller.seller_zip_code_prefix AS primary_seller_zip_prefix,
        COALESCE(t1.product_category_name_english, p1.product_category_name, 'unknown') AS primary_category,
        COALESCE(t2.product_category_name_english, p2.product_category_name, 'unknown') AS first_item_category,
        latest.review_count,
        latest.review_score AS latest_review_score,
        latest.review_creation_date::text AS latest_review_created_ts,
        latest.review_answer_timestamp::text AS latest_review_answered_ts,
        latest.rows_using_id AS latest_review_id_rows,
        earliest.review_score AS earliest_review_score,
        earliest.review_creation_date::text AS earliest_review_created_ts,
        earliest.review_answer_timestamp::text AS earliest_review_answered_ts,
        earliest.rows_using_id AS earliest_review_id_rows
    FROM public.bi_orders b
    LEFT JOIN public.olist_customers_dataset c ON c.customer_id = b.customer_id
    LEFT JOIN item_summary s ON s.order_id = b.order_id
    LEFT JOIN ranked_items primary_item ON primary_item.order_id = b.order_id AND primary_item.price_rank = 1
    LEFT JOIN ranked_items first_item ON first_item.order_id = b.order_id AND first_item.item_rank = 1
    LEFT JOIN public.olist_sellers_dataset seller ON seller.seller_id = primary_item.seller_id
    LEFT JOIN public.olist_products_dataset p1 ON p1.product_id = primary_item.product_id
    LEFT JOIN public.olist_products_dataset p2 ON p2.product_id = first_item.product_id
    LEFT JOIN public.product_category_name_translation t1 ON t1.product_category_name = p1.product_category_name
    LEFT JOIN public.product_category_name_translation t2 ON t2.product_category_name = p2.product_category_name
    LEFT JOIN ranked_reviews latest ON latest.order_id = b.order_id AND latest.latest_rank = 1
    LEFT JOIN ranked_reviews earliest ON earliest.order_id = b.order_id AND earliest.earliest_rank = 1
    ORDER BY b.order_id
) TO STDOUT WITH (FORMAT csv, HEADER true);

-- 3. Position of each ZIP prefix, within Brazil's bounds, for approximate distance
\o data/processed/zip_positions.csv
COPY (
    SELECT
        geolocation_zip_code_prefix AS zip_prefix,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY geolocation_lat) AS median_lat,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY geolocation_lng) AS median_lng,
        AVG(geolocation_lat) AS mean_lat,
        AVG(geolocation_lng) AS mean_lng,
        COUNT(*) AS points
    FROM public.olist_geolocation_dataset
    WHERE geolocation_lat BETWEEN -34 AND 6
      AND geolocation_lng BETWEEN -74 AND -34
    GROUP BY geolocation_zip_code_prefix
    ORDER BY geolocation_zip_code_prefix
) TO STDOUT WITH (FORMAT csv, HEADER true);

-- 4. Delivered orders with date sequence issues, as stored, for comparison with the source CSV
\o data/processed/timestamp_checks.csv
COPY (
    SELECT
        order_id,
        order_purchase_timestamp::text AS purchase_ts,
        order_approved_at::text AS approved_ts,
        order_delivered_carrier_date::text AS carrier_ts,
        order_delivered_customer_date::text AS delivered_ts
    FROM public.olist_orders_dataset
    WHERE order_status = 'delivered'
      AND (order_delivered_carrier_date < order_purchase_timestamp
           OR order_delivered_customer_date < order_delivered_carrier_date
           OR order_delivered_carrier_date IS NULL
           OR order_delivered_customer_date IS NULL
           OR order_approved_at < order_purchase_timestamp)
    ORDER BY order_id
) TO STDOUT WITH (FORMAT csv, HEADER true);

\o
ROLLBACK;
