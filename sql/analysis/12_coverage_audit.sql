-- All dates, all statuses: audit the coverage excluded by the configured analysis cohort.
SELECT purchase_month, COUNT(*) AS all_orders,
 SUM(commerce_eligible) AS commerce_orders, SUM(delivery_eligible) AS delivery_orders,
 SUM(review_score IS NOT NULL) AS reviewed_orders,
 SUM(order_purchase_timestamp>=@start_date AND order_purchase_timestamp<@end_date) AS selected_orders,
 MIN(order_purchase_timestamp) AS first_purchase, MAX(order_purchase_timestamp) AS last_purchase
FROM v_order_fact GROUP BY purchase_month ORDER BY purchase_month;
