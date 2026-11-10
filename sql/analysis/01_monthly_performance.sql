-- Zero-order months are retained. First-month and zero-denominator growth = NULL.
WITH RECURSIVE months AS (
 SELECT CAST(@start_date AS DATE) AS month_start
 UNION ALL
 SELECT DATE_ADD(month_start, INTERVAL 1 MONTH) FROM months
 WHERE DATE_ADD(month_start, INTERVAL 1 MONTH) < @end_date
), monthly AS (
 SELECT purchase_month, COUNT(*) AS orders, SUM(item_gmv) AS item_gmv,
        SUM(freight_value) AS freight_value, SUM(payment_value) AS payment_value
 FROM v_order_fact
 WHERE commerce_eligible=1 AND order_purchase_timestamp>=@start_date
   AND order_purchase_timestamp<@end_date
 GROUP BY purchase_month
), dense AS (
 SELECT m.month_start, COALESCE(a.orders,0) AS orders,
        COALESCE(a.item_gmv,0) AS item_gmv, COALESCE(a.freight_value,0) AS freight_value,
        COALESCE(a.payment_value,0) AS payment_value
 FROM months m LEFT JOIN monthly a ON m.month_start=a.purchase_month
), previous AS (
 SELECT dense.*, LAG(orders) OVER (ORDER BY month_start) AS previous_orders,
        LAG(item_gmv) OVER (ORDER BY month_start) AS previous_gmv FROM dense
)
SELECT *, ROUND(item_gmv/NULLIF(orders,0),2) AS avg_order_value,
       ROUND(orders/NULLIF(previous_orders,0)-1,4) AS order_mom,
       ROUND(item_gmv/NULLIF(previous_gmv,0)-1,4) AS gmv_mom
FROM previous ORDER BY month_start;
