CREATE TABLE IF NOT EXISTS raw_geolocation (
  raw_row_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `geolocation_zip_code_prefix` VARCHAR(5) NULL,
  `geolocation_lat` DOUBLE NULL,
  `geolocation_lng` DOUBLE NULL,
  `geolocation_city` VARCHAR(255) NULL,
  `geolocation_state` CHAR(2) NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;
