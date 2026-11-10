SELECT order_status, COUNT(*) AS orders,
 ROUND(COUNT(*)/SUM(COUNT(*)) OVER (),4) AS order_share,
 SUM(item_gmv) AS item_amount, SUM(payment_value) AS payment_amount,
 SUM(item_count=0) AS orders_without_items
FROM v_order_fact
WHERE order_purchase_timestamp>=@start_date AND order_purchase_timestamp<@end_date
GROUP BY order_status ORDER BY orders DESC;
