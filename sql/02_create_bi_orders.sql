-- Olist E-Commerce Analytics | Order-level view consumed by Power BI
-- Database: PostgreSQL (ecommerce_bi). Grain: one row per order_id.
-- This is the original project script. Its logic matches the live view, confirmed
-- with pg_get_viewdef('public.bi_orders', true).
-- A missing date makes the CASE condition NULL, so it falls to ELSE FALSE.
-- Delivered-status filtering happens in the Power BI measures, not here.

CREATE OR REPLACE VIEW public.bi_orders AS
WITH items AS(
SELECT
order_id,
SUM(price) AS product_sales,
SUM(freight_value) AS freight_value,
COUNT(*) AS items_count
FROM public.olist_order_items_dataset
GROUP BY order_id
),
payments AS(
SELECT
order_id,
SUM(payment_value) AS payment_total
FROM public.olist_order_payments_dataset
GROUP BY order_id
)
SELECT
o.order_id,
o.customer_id,
c.customer_unique_id,
c.customer_state,
c.customer_city,
o.order_status,
o.order_purchase_timestamp,
o.order_approved_at,
o.order_delivered_carrier_date,
o.order_delivered_customer_date,
o.order_estimated_delivery_date,
COALESCE(i.product_sales,0) AS product_sales,
COALESCE(i.freight_value,0) AS freight_value,
COALESCE(i.items_count,0) AS items_count,
p.payment_total,
CASE
WHEN o.order_delivered_carrier_date>=o.order_purchase_timestamp
AND o.order_delivered_customer_date>=o.order_delivered_carrier_date
THEN TRUE
ELSE FALSE
END AS valid_delivery_dates
FROM public.olist_orders_dataset o
LEFT JOIN public.olist_customers_dataset c ON o.customer_id=c.customer_id
LEFT JOIN items i ON o.order_id=i.order_id
LEFT JOIN payments p ON o.order_id=p.order_id;

SELECT
(SELECT COUNT(*) FROM public.olist_orders_dataset
WHERE (order_purchase_timestamp >= '2017-03-26 02:00' AND order_purchase_timestamp < '2017-03-26 03:00')
OR (order_purchase_timestamp >= '2018-03-25 02:00' AND order_purchase_timestamp < '2018-03-25 03:00')) AS purchase_in_missing_hour,
(SELECT COUNT(*) FROM public.olist_orders_dataset
WHERE (order_approved_at >= '2017-03-26 02:00' AND order_approved_at < '2017-03-26 03:00')
OR (order_approved_at >= '2018-03-25 02:00' AND order_approved_at < '2018-03-25 03:00')) AS approved_in_missing_hour,
(SELECT order_purchase_timestamp::text FROM public.olist_orders_dataset
WHERE order_id = 'afc1e4183307b101e5e2dbdd876a213f') AS control_order_purchase,
('2018-03-25 02:56:02'::timestamp)::text AS literal_as_text,
'2018-03-25 02:56:02'::timestamp AS literal_as_timestamp;
