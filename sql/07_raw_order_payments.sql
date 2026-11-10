CREATE TABLE IF NOT EXISTS raw_order_payments (
  raw_row_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `order_id` CHAR(32) NULL,
  `payment_sequential` INT NULL,
  `payment_type` VARCHAR(30) NULL,
  `payment_installments` INT NULL,
  `payment_value` DECIMAL(14,2) NULL,
  KEY idx_source_key (`order_id`,`payment_sequential`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;
