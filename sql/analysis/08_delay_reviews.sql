WITH buckets AS (
 SELECT *, CASE WHEN delay_days=0 THEN '0_on_time'
 WHEN delay_days<=3 THEN '1_late_1_3'
 WHEN delay_days<=7 THEN '2_late_4_7'
 WHEN delay_days<=14 THEN '3_late_8_14' ELSE '4_late_15_plus' END AS delay_bucket
 FROM v_order_fact WHERE delivery_eligible=1
  AND order_purchase_timestamp>=@start_date AND order_purchase_timestamp<@end_date
)
SELECT delay_bucket, COUNT(*) AS eligible_orders,
 COUNT(review_score) AS reviewed_orders, COALESCE(SUM(is_bad_review),0) AS bad_reviews,
 ROUND(AVG(is_bad_review),4) AS bad_review_rate,
 ROUND(COUNT(review_score)/COUNT(*),4) AS review_coverage,
 ROUND(AVG(review_score),2) AS avg_review_score
FROM buckets GROUP BY delay_bucket ORDER BY delay_bucket;
