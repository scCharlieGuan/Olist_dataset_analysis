CREATE TABLE IF NOT EXISTS raw_sellers (
  raw_row_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `seller_id` CHAR(32) NULL,
  `seller_zip_code_prefix` VARCHAR(5) NULL,
  `seller_city` VARCHAR(255) NULL,
  `seller_state` CHAR(2) NULL,
  KEY idx_source_key (`seller_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;
