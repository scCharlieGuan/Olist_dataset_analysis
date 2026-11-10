-- Monetary comparisons use DECIMAL, not floating point. One violation = reconciliation failed.
SELECT 'fact_one_row_per_order' AS check_name, 'FAIL' AS severity,
 (SELECT COUNT(*) FROM v_order_fact) <> (SELECT COUNT(*) FROM raw_orders) AS violations
UNION ALL
SELECT 'fact_distinct_orders', 'FAIL',
 (SELECT COUNT(*) FROM v_order_fact) <> (SELECT COUNT(DISTINCT order_id) FROM v_order_fact)
UNION ALL
SELECT 'item_gmv_reconciliation', 'FAIL',
 ABS(COALESCE((SELECT SUM(price) FROM raw_order_items),0) -
     COALESCE((SELECT SUM(item_gmv) FROM v_order_fact),0)) > 0.005
UNION ALL
SELECT 'freight_reconciliation', 'FAIL',
 ABS(COALESCE((SELECT SUM(freight_value) FROM raw_order_items),0) -
     COALESCE((SELECT SUM(freight_value) FROM v_order_fact),0)) > 0.005
UNION ALL
SELECT 'payment_reconciliation', 'FAIL',
 ABS(COALESCE((SELECT SUM(payment_value) FROM raw_order_payments),0) -
     COALESCE((SELECT SUM(payment_value) FROM v_order_fact),0)) > 0.005
UNION ALL
SELECT 'category_gmv_reconciliation', 'FAIL',
 ABS(COALESCE((SELECT SUM(price) FROM raw_order_items),0) -
     COALESCE((SELECT SUM(item_gmv) FROM v_order_category),0)) > 0.005
UNION ALL
SELECT 'delivered_without_items', 'WARN',
 (SELECT COUNT(*) FROM v_order_fact WHERE order_status='delivered' AND item_count=0)
UNION ALL
SELECT 'item_payment_gap_over_one_cent', 'WARN',
 (SELECT COUNT(*) FROM v_order_fact WHERE item_count>0 AND payment_count>0
    AND ABS(item_gmv+freight_value-payment_value)>0.01);
