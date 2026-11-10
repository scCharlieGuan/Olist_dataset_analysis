CREATE TABLE IF NOT EXISTS raw_category_translation (
  raw_row_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `product_category_name` VARCHAR(100) NULL,
  `product_category_name_english` VARCHAR(100) NULL,
  KEY idx_source_key (`product_category_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;
