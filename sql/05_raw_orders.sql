CREATE TABLE IF NOT EXISTS raw_orders (
  raw_row_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `order_id` CHAR(32) NULL,
  `customer_id` CHAR(32) NULL,
  `order_status` VARCHAR(20) NULL,
  `order_purchase_timestamp` DATETIME NULL,
  `order_approved_at` DATETIME NULL,
  `order_delivered_carrier_date` DATETIME NULL,
  `order_delivered_customer_date` DATETIME NULL,
  `order_estimated_delivery_date` DATETIME NULL,
  KEY idx_source_key (`order_id`),
  KEY idx_customer_id (`customer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;
