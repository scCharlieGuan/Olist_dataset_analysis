SELECT 'customers_nonempty' AS check_name, 'FAIL' AS severity, (SELECT IF(COUNT(*)=0,1,0) FROM raw_customers) AS violations
UNION ALL
SELECT 'customers_duplicate_key' AS check_name, 'FAIL' AS severity, (SELECT COUNT(*) FROM (SELECT customer_id FROM raw_customers GROUP BY customer_id HAVING COUNT(*) > 1) d) AS violations
UNION ALL
SELECT 'customers_missing_key' AS check_name, 'FAIL' AS severity, (SELECT COUNT(*) FROM raw_customers WHERE customer_id IS NULL OR TRIM(customer_id) = '') AS violations
UNION ALL
SELECT 'products_nonempty' AS check_name, 'FAIL' AS severity, (SELECT IF(COUNT(*)=0,1,0) FROM raw_products) AS violations
UNION ALL
SELECT 'products_duplicate_key' AS check_name, 'FAIL' AS severity, (SELECT COUNT(*) FROM (SELECT product_id FROM raw_products GROUP BY product_id HAVING COUNT(*) > 1) d) AS violations
UNION ALL
SELECT 'products_missing_key' AS check_name, 'FAIL' AS severity, (SELECT COUNT(*) FROM raw_products WHERE product_id IS NULL OR TRIM(product_id) = '') AS violations
UNION ALL
SELECT 'sellers_nonempty' AS check_name, 'FAIL' AS severity, (SELECT IF(COUNT(*)=0,1,0) FROM raw_sellers) AS violations
UNION ALL
SELECT 'sellers_duplicate_key' AS check_name, 'FAIL' AS severity, (SELECT COUNT(*) FROM (SELECT seller_id FROM raw_sellers GROUP BY seller_id HAVING COUNT(*) > 1) d) AS violations
UNION ALL
SELECT 'sellers_missing_key' AS check_name, 'FAIL' AS severity, (SELECT COUNT(*) FROM raw_sellers WHERE seller_id IS NULL OR TRIM(seller_id) = '') AS violations
UNION ALL
SELECT 'category_translation_nonempty' AS check_name, 'FAIL' AS severity, (SELECT IF(COUNT(*)=0,1,0) FROM raw_category_translation) AS violations
UNION ALL
SELECT 'category_translation_duplicate_key' AS check_name, 'FAIL' AS severity, (SELECT COUNT(*) FROM (SELECT product_category_name FROM raw_category_translation GROUP BY product_category_name HAVING COUNT(*) > 1) d) AS violations
UNION ALL
SELECT 'category_translation_missing_key' AS check_name, 'FAIL' AS severity, (SELECT COUNT(*) FROM raw_category_translation WHERE product_category_name IS NULL OR TRIM(product_category_name) = '') AS violations
UNION ALL
SELECT 'orders_nonempty' AS check_name, 'FAIL' AS severity, (SELECT IF(COUNT(*)=0,1,0) FROM raw_orders) AS violations
UNION ALL
SELECT 'orders_duplicate_key' AS check_name, 'FAIL' AS severity, (SELECT COUNT(*) FROM (SELECT order_id FROM raw_orders GROUP BY order_id HAVING COUNT(*) > 1) d) AS violations
UNION ALL
SELECT 'orders_missing_key' AS check_name, 'FAIL' AS severity, (SELECT COUNT(*) FROM raw_orders WHERE order_id IS NULL OR TRIM(order_id) = '') AS violations
UNION ALL
SELECT 'order_items_nonempty' AS check_name, 'FAIL' AS severity, (SELECT IF(COUNT(*)=0,1,0) FROM raw_order_items) AS violations
UNION ALL
SELECT 'order_items_duplicate_key' AS check_name, 'FAIL' AS severity, (SELECT COUNT(*) FROM (SELECT order_id, order_item_id FROM raw_order_items GROUP BY order_id, order_item_id HAVING COUNT(*) > 1) d) AS violations
UNION ALL
SELECT 'order_items_missing_key' AS check_name, 'FAIL' AS severity, (SELECT COUNT(*) FROM raw_order_items WHERE order_id IS NULL OR TRIM(order_id) = '' OR order_item_id IS NULL) AS violations
UNION ALL
SELECT 'order_payments_nonempty' AS check_name, 'FAIL' AS severity, (SELECT IF(COUNT(*)=0,1,0) FROM raw_order_payments) AS violations
UNION ALL
SELECT 'order_payments_duplicate_key' AS check_name, 'FAIL' AS severity, (SELECT COUNT(*) FROM (SELECT order_id, payment_sequential FROM raw_order_payments GROUP BY order_id, payment_sequential HAVING COUNT(*) > 1) d) AS violations
UNION ALL
SELECT 'order_payments_missing_key' AS check_name, 'FAIL' AS severity, (SELECT COUNT(*) FROM raw_order_payments WHERE order_id IS NULL OR TRIM(order_id) = '' OR payment_sequential IS NULL) AS violations
UNION ALL
SELECT 'order_reviews_nonempty' AS check_name, 'FAIL' AS severity, (SELECT IF(COUNT(*)=0,1,0) FROM raw_order_reviews) AS violations
UNION ALL
SELECT 'orders_customer_id_orphan' AS check_name, 'FAIL' AS severity, (SELECT COUNT(*) FROM raw_orders c LEFT JOIN raw_customers p ON c.customer_id=p.customer_id WHERE p.raw_row_id IS NULL) AS violations
UNION ALL
SELECT 'order_items_order_id_orphan' AS check_name, 'FAIL' AS severity, (SELECT COUNT(*) FROM raw_order_items c LEFT JOIN raw_orders p ON c.order_id=p.order_id WHERE p.raw_row_id IS NULL) AS violations
UNION ALL
SELECT 'order_items_product_id_orphan' AS check_name, 'FAIL' AS severity, (SELECT COUNT(*) FROM raw_order_items c LEFT JOIN raw_products p ON c.product_id=p.product_id WHERE p.raw_row_id IS NULL) AS violations
UNION ALL
SELECT 'order_items_seller_id_orphan' AS check_name, 'FAIL' AS severity, (SELECT COUNT(*) FROM raw_order_items c LEFT JOIN raw_sellers p ON c.seller_id=p.seller_id WHERE p.raw_row_id IS NULL) AS violations
UNION ALL
SELECT 'order_payments_order_id_orphan' AS check_name, 'FAIL' AS severity, (SELECT COUNT(*) FROM raw_order_payments c LEFT JOIN raw_orders p ON c.order_id=p.order_id WHERE p.raw_row_id IS NULL) AS violations
UNION ALL
SELECT 'order_reviews_order_id_orphan' AS check_name, 'FAIL' AS severity, (SELECT COUNT(*) FROM raw_order_reviews c LEFT JOIN raw_orders p ON c.order_id=p.order_id WHERE p.raw_row_id IS NULL) AS violations
UNION ALL
SELECT 'missing_purchase_time' AS check_name, 'FAIL' AS severity, (SELECT COUNT(*) FROM raw_orders WHERE order_purchase_timestamp IS NULL) AS violations
UNION ALL
SELECT 'unknown_order_status' AS check_name, 'FAIL' AS severity, (SELECT COUNT(*) FROM raw_orders WHERE order_status IS NULL OR order_status NOT IN ('created','approved','invoiced','processing','shipped','delivered','unavailable','canceled')) AS violations
UNION ALL
SELECT 'invalid_item_amount' AS check_name, 'FAIL' AS severity, (SELECT COUNT(*) FROM raw_order_items WHERE price IS NULL OR freight_value IS NULL OR price<0 OR freight_value<0 OR order_item_id<1) AS violations
UNION ALL
SELECT 'invalid_payment' AS check_name, 'FAIL' AS severity, (SELECT COUNT(*) FROM raw_order_payments WHERE payment_value IS NULL OR payment_value<0 OR payment_sequential<1 OR payment_installments IS NULL OR payment_installments<0) AS violations
UNION ALL
SELECT 'invalid_review_score' AS check_name, 'FAIL' AS severity, (SELECT COUNT(*) FROM raw_order_reviews WHERE review_score IS NULL OR review_score NOT BETWEEN 1 AND 5 OR review_id IS NULL) AS violations
UNION ALL
SELECT 'missing_customer_unique_id' AS check_name, 'WARN' AS severity, (SELECT COUNT(*) FROM raw_customers WHERE customer_unique_id IS NULL OR TRIM(customer_unique_id)='') AS violations
UNION ALL
SELECT 'multiple_reviews_per_order' AS check_name, 'WARN' AS severity, (SELECT COUNT(*) FROM (SELECT order_id FROM raw_order_reviews GROUP BY order_id HAVING COUNT(*)>1) d) AS violations
UNION ALL
SELECT 'reused_review_id' AS check_name, 'WARN' AS severity, (SELECT COUNT(*) FROM (SELECT review_id FROM raw_order_reviews GROUP BY review_id HAVING COUNT(*)>1) d) AS violations
UNION ALL
SELECT 'missing_item_shipping_limit' AS check_name, 'WARN' AS severity, (SELECT COUNT(*) FROM raw_order_items WHERE shipping_limit_date IS NULL) AS violations
UNION ALL
SELECT 'missing_approval_time' AS check_name, 'WARN' AS severity, (SELECT COUNT(*) FROM raw_orders WHERE order_status='delivered' AND order_approved_at IS NULL) AS violations
UNION ALL
SELECT 'missing_carrier_time' AS check_name, 'WARN' AS severity, (SELECT COUNT(*) FROM raw_orders WHERE order_status='delivered' AND order_delivered_carrier_date IS NULL) AS violations
UNION ALL
SELECT 'missing_delivery_time' AS check_name, 'WARN' AS severity, (SELECT COUNT(*) FROM raw_orders WHERE order_status='delivered' AND (order_delivered_customer_date IS NULL OR order_estimated_delivery_date IS NULL)) AS violations
UNION ALL
SELECT 'invalid_delivery_chronology' AS check_name, 'WARN' AS severity, (SELECT COUNT(*) FROM raw_orders WHERE order_delivered_customer_date<order_purchase_timestamp OR order_estimated_delivery_date<order_purchase_timestamp OR order_approved_at<order_purchase_timestamp OR order_delivered_carrier_date<order_purchase_timestamp OR order_delivered_customer_date<order_delivered_carrier_date) AS violations
UNION ALL
SELECT 'missing_customer_state' AS check_name, 'WARN' AS severity, (SELECT COUNT(*) FROM raw_customers WHERE customer_state IS NULL OR TRIM(customer_state)='') AS violations
UNION ALL
SELECT 'unmapped_product_category' AS check_name, 'WARN' AS severity, (SELECT COUNT(*) FROM raw_products p LEFT JOIN raw_category_translation t ON p.product_category_name=t.product_category_name WHERE t.raw_row_id IS NULL) AS violations;
