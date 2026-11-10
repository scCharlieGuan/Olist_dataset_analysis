"""Source contracts shared by schema generation, ingestion and synthetic tests.

Source primary keys are audited, not enforced here: retaining duplicate rows makes
quality defects inspectable. raw_row_id identifies a source record, NOT a business entity.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Source:
    name: str
    filename: str
    columns: tuple[tuple[str, str], ...]
    key: tuple[str, ...] = ()
    optional: bool = False


ID = "CHAR(32)"
ZIP = "VARCHAR(5)"
SOURCES = (
    Source(
        "customers",
        "olist_customers_dataset.csv",
        (
            ("customer_id", ID),
            ("customer_unique_id", ID),
            ("customer_zip_code_prefix", ZIP),
            ("customer_city", "VARCHAR(255)"),
            ("customer_state", "CHAR(2)"),
        ),
        ("customer_id",),
    ),
    Source(
        "products",
        "olist_products_dataset.csv",
        (
            ("product_id", ID),
            ("product_category_name", "VARCHAR(100)"),
            ("product_name_lenght", "INT"),
            ("product_description_lenght", "INT"),
            ("product_photos_qty", "INT"),
            ("product_weight_g", "INT"),
            ("product_length_cm", "INT"),
            ("product_height_cm", "INT"),
            ("product_width_cm", "INT"),
        ),
        ("product_id",),
    ),
    Source(
        "sellers",
        "olist_sellers_dataset.csv",
        (
            ("seller_id", ID),
            ("seller_zip_code_prefix", ZIP),
            ("seller_city", "VARCHAR(255)"),
            ("seller_state", "CHAR(2)"),
        ),
        ("seller_id",),
    ),
    Source(
        "category_translation",
        "product_category_name_translation.csv",
        (
            ("product_category_name", "VARCHAR(100)"),
            ("product_category_name_english", "VARCHAR(100)"),
        ),
        ("product_category_name",),
    ),
    Source(
        "orders",
        "olist_orders_dataset.csv",
        (
            ("order_id", ID),
            ("customer_id", ID),
            ("order_status", "VARCHAR(20)"),
            ("order_purchase_timestamp", "DATETIME"),
            ("order_approved_at", "DATETIME"),
            ("order_delivered_carrier_date", "DATETIME"),
            ("order_delivered_customer_date", "DATETIME"),
            ("order_estimated_delivery_date", "DATETIME"),
        ),
        ("order_id",),
    ),
    Source(
        "order_items",
        "olist_order_items_dataset.csv",
        (
            ("order_id", ID),
            ("order_item_id", "INT"),
            ("product_id", ID),
            ("seller_id", ID),
            ("shipping_limit_date", "DATETIME"),
            ("price", "DECIMAL(14,2)"),
            ("freight_value", "DECIMAL(14,2)"),
        ),
        ("order_id", "order_item_id"),
    ),
    Source(
        "order_payments",
        "olist_order_payments_dataset.csv",
        (
            ("order_id", ID),
            ("payment_sequential", "INT"),
            ("payment_type", "VARCHAR(30)"),
            ("payment_installments", "INT"),
            ("payment_value", "DECIMAL(14,2)"),
        ),
        ("order_id", "payment_sequential"),
    ),
    Source(
        "order_reviews",
        "olist_order_reviews_dataset.csv",
        (
            ("review_id", ID),
            ("order_id", ID),
            ("review_score", "INT"),
            ("review_comment_title", "TEXT"),
            ("review_comment_message", "TEXT"),
            ("review_creation_date", "DATETIME"),
            ("review_answer_timestamp", "DATETIME"),
        ),
    ),
    Source(
        "geolocation",
        "olist_geolocation_dataset.csv",
        (
            ("geolocation_zip_code_prefix", ZIP),
            ("geolocation_lat", "DOUBLE"),
            ("geolocation_lng", "DOUBLE"),
            ("geolocation_city", "VARCHAR(255)"),
            ("geolocation_state", "CHAR(2)"),
        ),
        optional=True,
    ),
)


def schema_sql(source: Source) -> str:
    columns = ["raw_row_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY"]
    columns.extend(f"`{name}` {dtype} NULL" for name, dtype in source.columns)
    if source.key:
        columns.append("KEY idx_source_key (" + ",".join(f"`{c}`" for c in source.key) + ")")
    # Join indexes are deliberately nonunique; DQ is responsible for business keys.
    for name, _ in source.columns:
        if name.endswith("_id") and name not in source.key:
            columns.append(f"KEY idx_{name} (`{name}`)")
    return (
        f"CREATE TABLE IF NOT EXISTS raw_{source.name} (\n  "
        + ",\n  ".join(columns)
        + "\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;\n"
    )
