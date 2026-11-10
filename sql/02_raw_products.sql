CREATE TABLE IF NOT EXISTS raw_products (
  raw_row_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `product_id` CHAR(32) NULL,
  `product_category_name` VARCHAR(100) NULL,
  `product_name_lenght` INT NULL,
  `product_description_lenght` INT NULL,
  `product_photos_qty` INT NULL,
  `product_weight_g` INT NULL,
  `product_length_cm` INT NULL,
  `product_height_cm` INT NULL,
  `product_width_cm` INT NULL,
  KEY idx_source_key (`product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;
