SELECT purchase_month, COUNT(*) AS delivered_orders,
 SUM(delivery_eligible) AS eligible_orders,
 SUM(delivery_eligible=0) AS excluded_orders,
 COALESCE(SUM(is_late),0) AS late_orders, ROUND(AVG(is_late),4) AS late_rate,
 ROUND(AVG(delivery_days),2) AS avg_delivery_days,
 ROUND(AVG(CASE WHEN is_late=1 THEN delay_days END),2) AS avg_days_among_late
FROM v_order_fact
WHERE order_status='delivered' AND order_purchase_timestamp>=@start_date
 AND order_purchase_timestamp<@end_date
GROUP BY purchase_month ORDER BY purchase_month;
