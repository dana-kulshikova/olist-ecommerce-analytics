-- OLIST E-COMMERCE | SQL DATA QUALITY & BUSINESS ANALYSIS
-- Database: PostgreSQL | Schema: public
-- Purpose: reproducible exploratory analysis and Power BI KPI validation
-- All queries in this file are READ-ONLY.
-- Reconstructed from project work; some queries are newly organized for publication.
-- Run one SELECT statement at a time in DBeaver (Ctrl+Enter).
--
-- Publication edits (three queries; everything else is unchanged):
--   Query 01: reads olist_order_reviews_cleaned, the table that exists in the database.
--   Queries 13 and 14: compare calendar dates, matching the corrected Power BI measure.
--     An order delivered on its estimated date now counts as on time at any time of day.

-- 01. DATASET ROW COUNTS
SELECT 'orders' AS dataset, COUNT(*) AS row_count FROM public.olist_orders_dataset
UNION ALL SELECT 'order_items', COUNT(*) FROM public.olist_order_items_dataset
UNION ALL SELECT 'payments', COUNT(*) FROM public.olist_order_payments_dataset
UNION ALL SELECT 'customers', COUNT(*) FROM public.olist_customers_dataset
UNION ALL SELECT 'products', COUNT(*) FROM public.olist_products_dataset
UNION ALL SELECT 'sellers', COUNT(*) FROM public.olist_sellers_dataset
UNION ALL SELECT 'geolocation', COUNT(*) FROM public.olist_geolocation_dataset
UNION ALL SELECT 'reviews', COUNT(*) FROM public.olist_order_reviews_cleaned
UNION ALL SELECT 'category_translation', COUNT(*) FROM public.product_category_name_translation;

-- 02. ORDER STATUS DISTRIBUTION
SELECT order_status, COUNT(*) AS order_count
FROM public.olist_orders_dataset
GROUP BY order_status
ORDER BY order_count DESC;

-- 03. DELIVERED ORDER SHARE (previously used in project)
SELECT COUNT(*) AS total_orders, COUNT(*) FILTER (WHERE order_status = 'delivered') AS delivered_orders, ROUND(100.0 * COUNT(*) FILTER (WHERE order_status = 'delivered') / NULLIF(COUNT(*), 0), 2) AS delivery_rate_pct
FROM public.olist_orders_dataset;

-- 04. MISSING KEY ORDER TIMESTAMPS
SELECT COUNT(*) AS total_orders, COUNT(*) FILTER (WHERE order_approved_at IS NULL) AS missing_approval, COUNT(*) FILTER (WHERE order_delivered_carrier_date IS NULL) AS missing_carrier_delivery, COUNT(*) FILTER (WHERE order_delivered_customer_date IS NULL) AS missing_customer_delivery, COUNT(*) FILTER (WHERE order_estimated_delivery_date IS NULL) AS missing_estimated_delivery
FROM public.olist_orders_dataset;

-- 05. DELIVERED ORDERS MISSING ACTUAL DELIVERY DATE
SELECT COUNT(*) AS delivered_missing_delivery_date
FROM public.olist_orders_dataset
WHERE order_status = 'delivered' AND order_delivered_customer_date IS NULL;

-- 06. DATE-SEQUENCE QUALITY CHECKS
SELECT COUNT(*) FILTER (WHERE order_approved_at < order_purchase_timestamp) AS approval_before_purchase, COUNT(*) FILTER (WHERE order_delivered_carrier_date < order_purchase_timestamp) AS carrier_before_purchase, COUNT(*) FILTER (WHERE order_delivered_customer_date < order_purchase_timestamp) AS customer_delivery_before_purchase, COUNT(*) FILTER (WHERE order_delivered_customer_date < order_delivered_carrier_date) AS customer_delivery_before_carrier
FROM public.olist_orders_dataset;

-- 07. DUPLICATE ORDER IDS IN ORDERS TABLE
SELECT order_id, COUNT(*) AS occurrences
FROM public.olist_orders_dataset
GROUP BY order_id
HAVING COUNT(*) > 1
ORDER BY occurrences DESC;

-- 08. ORPHAN ORDER ITEMS (REFERENTIAL QUALITY)
SELECT COUNT(*) AS order_items_without_matching_order
FROM public.olist_order_items_dataset i
LEFT JOIN public.olist_orders_dataset o ON o.order_id = i.order_id
WHERE o.order_id IS NULL;

-- 09. PRODUCT SALES AND AOV: DELIVERED ORDERS ONLY
-- Aggregate items by order BEFORE joining, to avoid duplicated order-level revenue.
WITH order_sales AS (
SELECT o.order_id, o.order_status, SUM(i.price) AS product_sales, SUM(i.freight_value) AS freight_value, COUNT(i.order_item_id) AS items_count
FROM public.olist_orders_dataset o
JOIN public.olist_order_items_dataset i ON i.order_id = o.order_id
GROUP BY o.order_id, o.order_status
)
SELECT COUNT(*) AS delivered_orders_with_items, ROUND(SUM(product_sales)::numeric, 2) AS total_product_sales_brl, ROUND(AVG(product_sales)::numeric, 2) AS average_order_value_brl, ROUND(SUM(freight_value)::numeric, 2) AS freight_value_brl
FROM order_sales
WHERE order_status = 'delivered';

-- 10. MONTHLY DELIVERED PRODUCT SALES
WITH order_sales AS (
SELECT o.order_id, o.order_purchase_timestamp, o.order_status, SUM(i.price) AS product_sales
FROM public.olist_orders_dataset o
JOIN public.olist_order_items_dataset i ON i.order_id = o.order_id
GROUP BY o.order_id, o.order_purchase_timestamp, o.order_status
)
SELECT DATE_TRUNC('month', order_purchase_timestamp) AS sales_month, COUNT(*) AS delivered_orders, ROUND(SUM(product_sales)::numeric, 2) AS product_sales_brl
FROM order_sales
WHERE order_status = 'delivered'
GROUP BY DATE_TRUNC('month', order_purchase_timestamp)
ORDER BY sales_month;

-- 11. TOP 10 CUSTOMER STATES BY DELIVERED PRODUCT SALES
WITH order_sales AS (
SELECT o.order_id, o.customer_id, o.order_status, SUM(i.price) AS product_sales
FROM public.olist_orders_dataset o
JOIN public.olist_order_items_dataset i ON i.order_id = o.order_id
GROUP BY o.order_id, o.customer_id, o.order_status
)
SELECT c.customer_state, COUNT(*) AS delivered_orders, ROUND(SUM(os.product_sales)::numeric, 2) AS product_sales_brl
FROM order_sales os
JOIN public.olist_customers_dataset c ON c.customer_id = os.customer_id
WHERE os.order_status = 'delivered'
GROUP BY c.customer_state
ORDER BY product_sales_brl DESC
LIMIT 10;

-- 12. AVERAGE DELIVERY TIME (VALID DELIVERED ORDERS)
-- EXTRACT(EPOCH) measures fractional days; DAX DATEDIFF(DAY) counts day boundaries,
-- so results may differ slightly from the Power BI KPI.
SELECT ROUND(AVG(EXTRACT(EPOCH FROM (order_delivered_customer_date - order_purchase_timestamp)) / 86400.0)::numeric, 2) AS avg_delivery_days
FROM public.olist_orders_dataset
WHERE order_status = 'delivered' AND order_delivered_customer_date IS NOT NULL AND order_delivered_customer_date >= order_purchase_timestamp;

-- 13. ON-TIME DELIVERY RATE (VALID DELIVERED ORDERS)
SELECT COUNT(*) AS valid_delivered_orders, COUNT(*) FILTER (WHERE order_delivered_customer_date::date <= order_estimated_delivery_date::date) AS on_time_orders, ROUND(100.0 * COUNT(*) FILTER (WHERE order_delivered_customer_date::date <= order_estimated_delivery_date::date) / NULLIF(COUNT(*), 0), 2) AS on_time_rate_pct
FROM public.olist_orders_dataset
WHERE order_status = 'delivered' AND order_delivered_customer_date IS NOT NULL AND order_estimated_delivery_date IS NOT NULL AND order_delivered_customer_date >= order_purchase_timestamp;

-- 14. LATE DELIVERY RATE BY CUSTOMER STATE
SELECT c.customer_state, COUNT(*) AS valid_delivered_orders, COUNT(*) FILTER (WHERE o.order_delivered_customer_date::date > o.order_estimated_delivery_date::date) AS late_orders, ROUND(100.0 * COUNT(*) FILTER (WHERE o.order_delivered_customer_date::date > o.order_estimated_delivery_date::date) / NULLIF(COUNT(*), 0), 2) AS late_rate_pct
FROM public.olist_orders_dataset o
JOIN public.olist_customers_dataset c ON c.customer_id = o.customer_id
WHERE o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL AND o.order_estimated_delivery_date IS NOT NULL AND o.order_delivered_customer_date >= o.order_purchase_timestamp
GROUP BY c.customer_state
ORDER BY valid_delivered_orders DESC;

-- 15. POWER BI SOURCE VALIDATION
-- Existing PostgreSQL view public.bi_orders was created during data preparation.
SELECT COUNT(*) AS bi_order_rows, COUNT(DISTINCT order_id) AS unique_order_ids
FROM public.bi_orders;

-- 16. POWER BI SALES VALIDATION
SELECT COUNT(*) FILTER (WHERE order_status = 'delivered') AS delivered_orders, ROUND(SUM(product_sales) FILTER (WHERE order_status = 'delivered')::numeric, 2) AS delivered_product_sales_brl, ROUND(AVG(product_sales) FILTER (WHERE order_status = 'delivered')::numeric, 2) AS average_delivered_order_value_brl
FROM public.bi_orders;

-- 17. POWER BI DELIVERY FLAG VALIDATION
SELECT valid_delivery_dates, COUNT(*) AS orders
FROM public.bi_orders
WHERE order_status = 'delivered'
GROUP BY valid_delivery_dates
ORDER BY valid_delivery_dates;

-- END OF READ-ONLY ANALYSIS
