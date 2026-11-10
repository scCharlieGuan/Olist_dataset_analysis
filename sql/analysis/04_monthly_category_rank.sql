WITH monthly AS (
 SELECT f.purchase_month, c.category, SUM(c.item_gmv) AS item_gmv
 FROM v_order_category c JOIN v_order_fact f ON c.order_id=f.order_id
 WHERE f.commerce_eligible=1 AND f.order_purchase_timestamp>=@start_date
   AND f.order_purchase_timestamp<@end_date
 GROUP BY f.purchase_month, c.category
), ranked AS (
 SELECT *, DENSE_RANK() OVER (PARTITION BY purchase_month ORDER BY item_gmv DESC) AS gmv_rank
 FROM monthly
)
SELECT * FROM ranked WHERE gmv_rank<=5 ORDER BY purchase_month, gmv_rank, category;
