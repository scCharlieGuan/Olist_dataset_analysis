-- An order involving two sellers contributes once to EACH seller. Not additive.
-- Restricting to single-seller orders is a sensitivity check, not causal attribution.
WITH seller_orders AS (
 SELECT DISTINCT seller_id, order_id FROM raw_order_items
)
SELECT s.seller_id, s.seller_state, COUNT(*) AS participating_orders,
 SUM(f.is_late) AS late_orders, ROUND(AVG(f.is_late),4) AS late_rate,
 ROUND(AVG(CASE WHEN f.is_late=1 THEN f.delay_days END),2) AS avg_days_among_late,
 SUM(f.seller_count=1) AS single_seller_orders,
 ROUND(AVG(CASE WHEN f.seller_count=1 THEN f.is_late END),4) AS single_seller_late_rate
FROM seller_orders so
JOIN raw_sellers s ON so.seller_id=s.seller_id
JOIN v_order_fact f ON so.order_id=f.order_id
WHERE f.delivery_eligible=1 AND f.order_purchase_timestamp>=@start_date
 AND f.order_purchase_timestamp<@end_date
GROUP BY s.seller_id, s.seller_state HAVING COUNT(*)>=@min_orders
ORDER BY late_rate DESC, participating_orders DESC;
