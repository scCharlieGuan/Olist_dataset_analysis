CREATE TABLE IF NOT EXISTS raw_order_items (
  raw_row_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `order_id` CHAR(32) NULL,
  `order_item_id` INT NULL,
  `product_id` CHAR(32) NULL,
  `seller_id` CHAR(32) NULL,
  `shipping_limit_date` DATETIME NULL,
  `price` DECIMAL(14,2) NULL,
  `freight_value` DECIMAL(14,2) NULL,
  KEY idx_source_key (`order_id`,`order_item_id`),
  KEY idx_product_id (`product_id`),
  KEY idx_seller_id (`seller_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;
