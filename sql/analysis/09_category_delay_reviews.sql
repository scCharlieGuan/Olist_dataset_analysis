-- One order is counted once per category; category groups are overlapping populations.
WITH segmented AS (
 SELECT c.category, f.review_score, f.is_bad_review,
        CASE WHEN delay_days=0 THEN '0_on_time'
 WHEN delay_days<=3 THEN '1_late_1_3'
 WHEN delay_days<=7 THEN '2_late_4_7'
 WHEN delay_days<=14 THEN '3_late_8_14' ELSE '4_late_15_plus' END AS delay_bucket
 FROM v_order_category c JOIN v_order_fact f ON c.order_id=f.order_id
 WHERE f.delivery_eligible=1 AND f.order_purchase_timestamp>=@start_date
  AND f.order_purchase_timestamp<@end_date
)
SELECT category, delay_bucket, COUNT(*) AS eligible_orders,
 COUNT(review_score) AS reviewed_orders, COALESCE(SUM(is_bad_review),0) AS bad_reviews,
 ROUND(AVG(is_bad_review),4) AS bad_review_rate,
 ROUND(COUNT(review_score)/COUNT(*),4) AS review_coverage
FROM segmented GROUP BY category, delay_bucket
HAVING COUNT(review_score)>=@min_orders
ORDER BY category, delay_bucket;
