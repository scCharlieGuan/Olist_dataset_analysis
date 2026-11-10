SELECT purchase_month, COUNT(*) AS delivered_orders,
 SUM(payment_count=0) AS orders_without_payment,
 SUM(item_gmv) AS item_gmv, SUM(freight_value) AS freight_value,
 SUM(payment_value) AS payment_value,
 SUM(payment_value-item_gmv-freight_value) AS net_gap,
 SUM(ABS(payment_value-item_gmv-freight_value)>0.01) AS orders_with_gap
FROM v_order_fact
WHERE commerce_eligible=1 AND order_purchase_timestamp>=@start_date
 AND order_purchase_timestamp<@end_date
GROUP BY purchase_month ORDER BY purchase_month;
