-- Stratification helps expose mix differences but does NOT identify a causal effect.
SELECT purchase_month, COALESCE(customer_state,'unknown') AS customer_state,
 COUNT(CASE WHEN is_late=0 THEN review_score END) AS ontime_reviewed,
 COUNT(CASE WHEN is_late=1 THEN review_score END) AS late_reviewed,
 ROUND(AVG(CASE WHEN is_late=0 THEN is_bad_review END),4) AS ontime_bad_rate,
 ROUND(AVG(CASE WHEN is_late=1 THEN is_bad_review END),4) AS late_bad_rate,
 ROUND(AVG(CASE WHEN is_late=1 THEN is_bad_review END)
      -AVG(CASE WHEN is_late=0 THEN is_bad_review END),4) AS bad_rate_difference
FROM v_order_fact
WHERE delivery_eligible=1 AND order_purchase_timestamp>=@start_date
 AND order_purchase_timestamp<@end_date
GROUP BY purchase_month, COALESCE(customer_state,'unknown')
HAVING COUNT(CASE WHEN is_late=0 THEN review_score END)>=@min_orders
 AND COUNT(CASE WHEN is_late=1 THEN review_score END)>=@min_orders
ORDER BY purchase_month, customer_state;
