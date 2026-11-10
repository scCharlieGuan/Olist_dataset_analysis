CREATE TABLE IF NOT EXISTS raw_order_reviews (
  raw_row_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `review_id` CHAR(32) NULL,
  `order_id` CHAR(32) NULL,
  `review_score` INT NULL,
  `review_comment_title` TEXT NULL,
  `review_comment_message` TEXT NULL,
  `review_creation_date` DATETIME NULL,
  `review_answer_timestamp` DATETIME NULL,
  KEY idx_review_id (`review_id`),
  KEY idx_order_id (`order_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;
