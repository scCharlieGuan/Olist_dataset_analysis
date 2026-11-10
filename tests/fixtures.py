"""Tiny synthetic input designed to expose fan-out, calendar, review and NULL mistakes.

These are NOT records from Olist. Never describe these rows as empirical findings.
"""

import csv
from pathlib import Path

from olist_analytics.catalog import SOURCES


def fixture_rows():
    def ident(n):
        return f"{n:032x}"

    a, b, c, d, e, f = [ident(i) for i in range(1, 7)]
    s1, s2, p1, p2 = [ident(i) for i in range(100, 104)]
    rows = {s.name: [] for s in SOURCES}
    for i, order_id in enumerate([a, b, c, d, e, f], 1):
        customer = ident(200 + i)
        rows["customers"].append(
            dict(
                customer_id=customer,
                customer_unique_id=ident(300 + i),
                customer_zip_code_prefix="01234",
                customer_city="test_city",
                customer_state="SP",
            )
        )
        purchase = "2017-03-01 10:00:00" if order_id == c else f"2017-01-{i:02} 10:00:00"
        delivered = {
            a: "2017-01-05 12:00:00",
            b: "2017-01-04 18:00:00",
            c: "2017-03-05 12:00:00",
            d: "",
            e: "2017-01-07 12:00:00",
            f: "2017-01-09 12:00:00",
        }[order_id]
        promised = {
            a: "2017-01-04 00:00:00",
            b: "2017-01-04 00:00:00",
            c: "",
            d: "",
            e: "2017-01-08 00:00:00",
            f: "2017-01-08 00:00:00",
        }[order_id]
        rows["orders"].append(
            dict(
                order_id=order_id,
                customer_id=customer,
                order_status="canceled" if order_id == d else "delivered",
                order_purchase_timestamp=purchase,
                order_approved_at=purchase,
                order_delivered_carrier_date=purchase,
                order_delivered_customer_date=delivered,
                order_estimated_delivery_date=promised,
            )
        )
    rows["sellers"] = [
        dict(seller_id=s, seller_zip_code_prefix="01234", seller_city="test", seller_state="SP")
        for s in [s1, s2]
    ]
    rows["products"] = [
        dict(product_id=p, product_category_name=cat) for p, cat in [(p1, "cat_a"), (p2, "cat_b")]
    ]
    rows["category_translation"] = [
        dict(product_category_name=c, product_category_name_english=c) for c in ["cat_a", "cat_b"]
    ]
    for order, seq, p, s, price, freight in [
        (a, 1, p1, s1, "100.00", "10.00"),
        (a, 2, p2, s2, "50.00", "5.00"),
        (b, 1, p1, s1, "50.00", "5.00"),
        (c, 1, p2, s2, "20.00", "2.00"),
        (f, 1, p1, s1, "0.00", "0.00"),
    ]:
        rows["order_items"].append(
            dict(
                order_id=order,
                order_item_id=str(seq),
                product_id=p,
                seller_id=s,
                shipping_limit_date="2017-01-10 00:00:00",
                price=price,
                freight_value=freight,
            )
        )
    for order, seq, value in [
        (a, 1, "100.00"),
        (a, 2, "65.00"),
        (b, 1, "55.00"),
        (c, 1, "22.00"),
        (f, 1, "0.00"),
    ]:
        rows["order_payments"].append(
            dict(
                order_id=order,
                payment_sequential=str(seq),
                payment_type="credit_card",
                payment_installments="1",
                payment_value=value,
            )
        )
    for i, (order, score, timestamp) in enumerate(
        [
            (a, "5", "2017-01-05 13:00:00"),
            (a, "2", "2017-01-06 13:00:00"),
            (b, "5", "2017-01-05 13:00:00"),
            (f, "1", "2017-01-10 13:00:00"),
        ],
        1,
    ):
        rows["order_reviews"].append(
            dict(
                review_id=ident(400 + i),
                order_id=order,
                review_score=score,
                review_creation_date=timestamp,
                review_answer_timestamp=timestamp,
                review_comment_message="synthetic, quoted\nmultiline",
            )
        )
    return rows


def write_fixture(directory: Path):
    directory.mkdir(parents=True, exist_ok=True)
    rows = fixture_rows()
    for source in SOURCES:
        if source.optional:
            continue
        with (directory / source.filename).open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=[n for n, _ in source.columns])
            writer.writeheader()
            for row in rows[source.name]:
                writer.writerow(row)
    (directory / "SYNTHETIC_DATA.txt").write_text(
        "SYNTHETIC TEST DATA ONLY. Not Olist empirical data.\n", encoding="utf-8"
    )
