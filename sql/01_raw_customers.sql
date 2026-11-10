CREATE TABLE IF NOT EXISTS raw_customers (
  raw_row_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `customer_id` CHAR(32) NULL,
  `customer_unique_id` CHAR(32) NULL,
  `customer_zip_code_prefix` VARCHAR(5) NULL,
  `customer_city` VARCHAR(255) NULL,
  `customer_state` CHAR(2) NULL,
  KEY idx_source_key (`customer_id`),
  KEY idx_customer_unique_id (`customer_unique_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;
