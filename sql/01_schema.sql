-- Structure of the ecommerce_bi database, exported with:
--   pg_dump --schema-only --no-owner --no-privileges
-- Publication edit: removed the two psql-only session marker lines added by pg_dump.
-- The tables have no primary keys, foreign keys or indexes.

--
-- PostgreSQL database dump
--

-- Dumped from database version 17.11
-- Dumped by pg_dump version 17.11

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: olist_customers_dataset; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.olist_customers_dataset (
    customer_id character varying(50),
    customer_unique_id character varying(50),
    customer_zip_code_prefix character varying(10),
    customer_city character varying(50),
    customer_state character varying(50)
);


--
-- Name: olist_order_items_dataset; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.olist_order_items_dataset (
    order_id character varying(50),
    order_item_id integer,
    product_id character varying(50),
    seller_id character varying(50),
    shipping_limit_date timestamp without time zone,
    price numeric(12,2),
    freight_value numeric(12,2)
);


--
-- Name: olist_order_payments_dataset; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.olist_order_payments_dataset (
    order_id character varying(50),
    payment_sequential integer,
    payment_type character varying(50),
    payment_installments integer,
    payment_value numeric(12,2)
);


--
-- Name: olist_orders_dataset; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.olist_orders_dataset (
    order_id character varying(50),
    customer_id character varying(50),
    order_status character varying(50),
    order_purchase_timestamp timestamp without time zone,
    order_approved_at timestamp without time zone,
    order_delivered_carrier_date timestamp without time zone,
    order_delivered_customer_date timestamp without time zone,
    order_estimated_delivery_date timestamp without time zone
);


--
-- Name: bi_orders; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.bi_orders AS
 WITH items AS (
         SELECT olist_order_items_dataset.order_id,
            sum(olist_order_items_dataset.price) AS product_sales,
            sum(olist_order_items_dataset.freight_value) AS freight_value,
            count(*) AS items_count
           FROM public.olist_order_items_dataset
          GROUP BY olist_order_items_dataset.order_id
        ), payments AS (
         SELECT olist_order_payments_dataset.order_id,
            sum(olist_order_payments_dataset.payment_value) AS payment_total
           FROM public.olist_order_payments_dataset
          GROUP BY olist_order_payments_dataset.order_id
        )
 SELECT o.order_id,
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
    COALESCE(i.product_sales, (0)::numeric) AS product_sales,
    COALESCE(i.freight_value, (0)::numeric) AS freight_value,
    COALESCE(i.items_count, (0)::bigint) AS items_count,
    p.payment_total,
        CASE
            WHEN ((o.order_delivered_carrier_date >= o.order_purchase_timestamp) AND (o.order_delivered_customer_date >= o.order_delivered_carrier_date)) THEN true
            ELSE false
        END AS valid_delivery_dates
   FROM (((public.olist_orders_dataset o
     LEFT JOIN public.olist_customers_dataset c ON (((o.customer_id)::text = (c.customer_id)::text)))
     LEFT JOIN items i ON (((o.order_id)::text = (i.order_id)::text)))
     LEFT JOIN payments p ON (((o.order_id)::text = (p.order_id)::text)));


--
-- Name: olist_geolocation_dataset; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.olist_geolocation_dataset (
    geolocation_zip_code_prefix character varying(10),
    geolocation_lat real,
    geolocation_lng real,
    geolocation_city character varying(50),
    geolocation_state character varying(50)
);


--
-- Name: olist_order_reviews_cleaned; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.olist_order_reviews_cleaned (
    review_id character varying(50),
    order_id character varying(50),
    review_score integer,
    review_comment_title text,
    review_comment_message text,
    review_creation_date timestamp without time zone,
    review_answer_timestamp timestamp without time zone
);


--
-- Name: olist_products_dataset; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.olist_products_dataset (
    product_id character varying(50),
    product_category_name character varying(50),
    product_name_lenght integer,
    product_description_lenght integer,
    product_photos_qty integer,
    product_weight_g integer,
    product_length_cm integer,
    product_height_cm integer,
    product_width_cm integer
);


--
-- Name: olist_sellers_dataset; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.olist_sellers_dataset (
    seller_id character varying(50),
    seller_zip_code_prefix character varying(10),
    seller_city character varying(50),
    seller_state character varying(50)
);


--
-- Name: product_category_name_translation; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.product_category_name_translation (
    product_category_name character varying(50),
    product_category_name_english character varying(50)
);


--
-- PostgreSQL database dump complete
--

