-- Same output as optimized query. DATE() prevents a simple timestamp range lookup.
SELECT COUNT(*) AS orders FROM raw_orders
WHERE order_status='delivered'
 AND DATE(order_purchase_timestamp)>=@bench_start
 AND DATE(order_purchase_timestamp)<@bench_end;
