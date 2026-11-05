# Data

This repository doesn't include the source data. Download it from Kaggle:

**[Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)**, provided by Olist and licensed under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).

## Setup

Extract the archive into `data/raw/`. That folder is ignored by Git, so the CSV files stay on your machine.

| File | Rows | Used by the dashboard |
|---|---:|---|
| `olist_orders_dataset.csv` | 99,441 | Yes |
| `olist_customers_dataset.csv` | 99,441 | Yes |
| `olist_order_items_dataset.csv` | 112,650 | Yes |
| `olist_order_payments_dataset.csv` | 103,886 | In the view, not in a KPI |
| `olist_order_reviews_dataset.csv` | 99,224 | No |
| `olist_products_dataset.csv` | 32,951 | No |
| `olist_sellers_dataset.csv` | 3,095 | No |
| `olist_geolocation_dataset.csv` | 1,000,163 | No |
| `product_category_name_translation.csv` | 71 | No |

Running `python/clean_reviews.py` creates `olist_order_reviews_cleaned.csv` in the same folder. The database imports this file rather than the original reviews file.

## Changes made to the data

The review text was flattened to one line per review. The other files were loaded as published. Olist's order data was then aggregated to order level in the `bi_orders` view.
