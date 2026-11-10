-- One row per order. NULL timestamps sort last in MySQL DESC order.
CREATE OR REPLACE VIEW v_reviews_latest AS
SELECT order_id, review_id, review_score, review_creation_date, review_answer_timestamp
FROM (
 SELECT r.*, ROW_NUMBER() OVER (
  PARTITION BY order_id
  ORDER BY review_answer_timestamp DESC, review_creation_date DESC,
           review_id DESC, raw_row_id DESC
 ) AS review_rank
 FROM raw_order_reviews r
) ranked
WHERE review_rank = 1;
