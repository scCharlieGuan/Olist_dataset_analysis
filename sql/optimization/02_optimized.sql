SELECT COUNT(*) AS orders FROM raw_orders
WHERE order_status='delivered'
 AND order_purchase_timestamp>=@bench_start
 AND order_purchase_timestamp<@bench_end;
