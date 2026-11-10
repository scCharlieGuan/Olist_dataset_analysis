-- Grain: exactly one order_id. Aggregate both one-to-many sides BEFORE joining.
CREATE OR REPLACE VIEW v_order_fact AS
WITH items AS (
 SELECT order_id, COUNT(*) AS item_count, COUNT(DISTINCT seller_id) AS seller_count,
        SUM(price) AS item_gmv, SUM(freight_value) AS freight_value
 FROM raw_order_items GROUP BY order_id
), payments AS (
 SELECT order_id, COUNT(*) AS payment_count, SUM(payment_value) AS payment_value
 FROM raw_order_payments GROUP BY order_id
), base AS (
 SELECT o.order_id, o.order_status, o.order_purchase_timestamp,
        o.order_approved_at, o.order_delivered_carrier_date,
        o.order_delivered_customer_date, o.order_estimated_delivery_date,
        CAST(CONCAT(YEAR(o.order_purchase_timestamp), '-',
             LPAD(CAST(MONTH(o.order_purchase_timestamp) AS CHAR), 2, '0'), '-01') AS DATE) AS purchase_month,
        c.customer_unique_id, c.customer_state,
        COALESCE(i.item_count, 0) AS item_count, COALESCE(i.seller_count, 0) AS seller_count,
        COALESCE(i.item_gmv, 0) AS item_gmv, COALESCE(i.freight_value, 0) AS freight_value,
        COALESCE(p.payment_count, 0) AS payment_count,
        COALESCE(p.payment_value, 0) AS payment_value,
        r.review_score, r.review_id,
        CASE WHEN o.order_status = 'delivered'
          AND o.order_delivered_customer_date IS NOT NULL
          AND o.order_estimated_delivery_date IS NOT NULL
          AND o.order_delivered_customer_date >= o.order_purchase_timestamp
          AND o.order_estimated_delivery_date >= o.order_purchase_timestamp
          THEN 1 ELSE 0 END AS delivery_eligible
 FROM raw_orders o
 LEFT JOIN raw_customers c ON o.customer_id = c.customer_id
 LEFT JOIN items i ON o.order_id = i.order_id
 LEFT JOIN payments p ON o.order_id = p.order_id
 LEFT JOIN v_reviews_latest r ON o.order_id = r.order_id
)
SELECT base.*,
 CASE WHEN order_status = 'delivered' AND item_count > 0 THEN 1 ELSE 0 END AS commerce_eligible,
 CASE WHEN delivery_eligible = 1 THEN
      DATEDIFF(order_delivered_customer_date, order_estimated_delivery_date) END AS delay_days_signed,
 CASE WHEN delivery_eligible = 1 THEN GREATEST(
      DATEDIFF(order_delivered_customer_date, order_estimated_delivery_date), 0) END AS delay_days,
 CASE WHEN delivery_eligible = 1 THEN
      CASE WHEN DATE(order_delivered_customer_date) > DATE(order_estimated_delivery_date)
           THEN 1 ELSE 0 END END AS is_late,
 CASE WHEN delivery_eligible = 1 THEN
      DATEDIFF(order_delivered_customer_date, order_purchase_timestamp) END AS delivery_days,
 CASE WHEN review_score BETWEEN 1 AND 5 THEN
      CASE WHEN review_score <= 2 THEN 1 ELSE 0 END END AS is_bad_review
FROM base;
