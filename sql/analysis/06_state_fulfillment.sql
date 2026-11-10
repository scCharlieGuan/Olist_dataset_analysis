SELECT COALESCE(customer_state,'unknown') AS customer_state,
 COUNT(*) AS eligible_orders, SUM(is_late) AS late_orders,
 ROUND(AVG(is_late),4) AS late_rate, ROUND(AVG(delivery_days),2) AS avg_delivery_days,
 ROUND(AVG(CASE WHEN is_late=1 THEN delay_days END),2) AS avg_days_among_late
FROM v_order_fact
WHERE delivery_eligible=1 AND order_purchase_timestamp>=@start_date
 AND order_purchase_timestamp<@end_date
GROUP BY COALESCE(customer_state,'unknown') HAVING COUNT(*)>=@min_orders
ORDER BY late_rate DESC, eligible_orders DESC;
