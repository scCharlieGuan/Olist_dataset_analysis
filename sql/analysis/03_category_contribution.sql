WITH categories AS (
 SELECT c.category, COUNT(*) AS orders_containing_category,
        SUM(c.item_count) AS item_count, SUM(c.item_gmv) AS item_gmv
 FROM v_order_category c JOIN v_order_fact f ON c.order_id=f.order_id
 WHERE f.commerce_eligible=1 AND f.order_purchase_timestamp>=@start_date
   AND f.order_purchase_timestamp<@end_date
 GROUP BY c.category
)
SELECT *, DENSE_RANK() OVER (ORDER BY item_gmv DESC) AS gmv_rank,
 ROUND(item_gmv/NULLIF(SUM(item_gmv) OVER (),0),4) AS gmv_share
FROM categories ORDER BY gmv_rank, category;
