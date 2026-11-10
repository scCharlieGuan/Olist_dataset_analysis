-- Grain: order_id x category. Orders can belong to several categories.
CREATE OR REPLACE VIEW v_order_category AS
SELECT i.order_id,
       COALESCE(t.product_category_name_english,
                CONCAT('pt:', p.product_category_name), 'unknown') AS category,
       COUNT(*) AS item_count, SUM(i.price) AS item_gmv, SUM(i.freight_value) AS freight_value
FROM raw_order_items i
LEFT JOIN raw_products p ON i.product_id = p.product_id
LEFT JOIN raw_category_translation t ON p.product_category_name = t.product_category_name
GROUP BY i.order_id,
         COALESCE(t.product_category_name_english,
                  CONCAT('pt:', p.product_category_name), 'unknown');
