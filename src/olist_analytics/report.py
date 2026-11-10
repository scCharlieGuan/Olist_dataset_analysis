"""Offline HTML report. Business calculations remain in SQL, charts use exported CSVs."""

import base64
import csv
import json
from html import escape
from io import BytesIO
from pathlib import Path

LABELS = {
    "01_monthly_performance": "月度经营表现（BRL）",
    "02_order_status": "订单状态与经营覆盖",
    "03_category_contribution": "品类交易额贡献",
    "04_monthly_category_rank": "每月品类排名",
    "05_monthly_fulfillment": "月度履约",
    "06_state_fulfillment": "客户州配送表现",
    "07_seller_fulfillment": "卖家参与订单的履约表现",
    "08_delay_reviews": "延迟区间与评价",
    "09_category_delay_reviews": "品类内延迟与评价",
    "10_state_month_review_comparison": "同月同州的评价比较",
    "11_payment_reconciliation": "支付对账",
    "12_coverage_audit": "全数据时间覆盖审计",
}


def make_report(output: Path) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    manifest_path = output / "analysis_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    # A manifest is also the publication gate: never report a partially failed export.
    from .ingest import sha256

    if manifest.get("quality_sha256"):
        if sha256(output / "quality.json") != manifest["quality_sha256"]:
            raise RuntimeError("Quality results changed after export; rerun analyze")

    tables = {}
    for query in manifest["queries"]:
        path = output / f"{query['name']}.csv"
        if sha256(path) != query["csv_sha256"]:
            raise RuntimeError("CSVs changed after export; rerun analyze before report")
        with path.open(encoding="utf-8-sig", newline="") as stream:
            tables[query["name"]] = list(csv.DictReader(stream))
    if not any(tables.values()):
        raise RuntimeError("No analysis rows to report")

    def chart(rows, x, y, title, ylabel, percent=False):
        if not rows:
            return "<p>没有满足口径的数据。</p>"
        labels = [r[x] for r in rows]
        # NULL metrics remain gaps, not misleading zeros.
        values = [float(r[y]) if r[y] else float("nan") for r in rows]
        fig, ax = plt.subplots(figsize=(10, 3.5), layout="constrained")
        ax.bar(labels, values, color="#217c91")
        ax.set(title=title, ylabel=ylabel)
        ax.tick_params(axis="x", rotation=60)
        if percent:
            from matplotlib.ticker import PercentFormatter

            ax.yaxis.set_major_formatter(PercentFormatter(1))
        image = BytesIO()
        fig.savefig(image, format="png", dpi=130)
        plt.close(fig)
        return (
            '<img alt="'
            + escape(title)
            + '" src="data:image/png;base64,'
            + base64.b64encode(image.getvalue()).decode()
            + '">'
        )

    body = [
        "<h1>基于 MySQL 的电商经营与履约分析</h1>",
        f"<p>下单时间范围：[{escape(manifest['start_inclusive'])}, "
        f"{escape(manifest['end_exclusive'])})；最小分组样本：{manifest['min_orders']}。"
        f"生成时间（UTC）：{escape(manifest['generated_at_utc'])}</p>",
        "<p>GMV = 已交付且有商品明细订单的商品金额，不含运费；不是平台营收。"
        "配送延迟按自然日判定。差评 = 最新有效评价为 1–2 星，分母仅包含已评价订单。"
        "订单级评价无法定位某件商品；卖家及品类分组可能重叠，订单数不能直接相加。"
        "数据为历史快照，交付状态按快照确定；延迟与差评的比较仅表示相关性。</p>",
    ]
    origin = manifest.get("import_manifest", {}).get("data_origin", "unknown")
    if origin == "synthetic":
        body.insert(
            1,
            "<p style='background:#fff0cd;padding:16px'><strong>"
            "合成样例验证：本页全部数值来自人工构造的测试数据，不是 Olist 真实经营结论。"
            "</strong></p>",
        )
    elif origin == "unknown":
        body.insert(1, "<p>本次导出未关联导入清单，数据来源尚未追溯。</p>")
    body += [
        chart(
            tables["01_monthly_performance"],
            "month_start",
            "item_gmv",
            "Monthly delivered merchandise GMV",
            "BRL",
        ),
        chart(
            tables["05_monthly_fulfillment"],
            "purchase_month",
            "late_rate",
            "Late delivery rate by purchase month",
            "Rate",
            True,
        ),
        chart(
            tables["08_delay_reviews"],
            "delay_bucket",
            "bad_review_rate",
            "Bad review rate by delivery delay",
            "Rate",
            True,
        ),
    ]
    body.append(
        "<p>表格最多预览 50 行，完整结果见同目录 CSV；空值不等于 0。"
        "低样本组已按 SQL 口径筛选，未展示组仍可在完整查询中进一步审计。</p>"
    )
    for name, rows in tables.items():
        body.append(f"<h2>{escape(LABELS.get(name, name))}</h2>")
        if not rows:
            body.append("<p>没有满足筛选条件的数据。</p>")
            continue
        headers = rows[0].keys()
        body.append(
            "<div class='scroll'><table><thead><tr>"
            + "".join(f"<th>{escape(k)}</th>" for k in headers)
            + "</tr></thead><tbody>"
        )
        for row in rows[:50]:
            body.append(
                "<tr>" + "".join(f"<td>{escape(v or '—')}</td>" for v in row.values()) + "</tr>"
            )
        body.append("</tbody></table></div>")
    quality_path = output / "quality.json"
    if quality_path.exists():
        checks = json.loads(quality_path.read_text(encoding="utf-8"))
        body.append("<h2>数据质量检查</h2><ul>")
        for check in checks:
            body.append(
                f"<li>{escape(check['severity'])} {escape(check['check_name'])}: "
                f"{check['violations']}</li>"
            )
        body.append("</ul>")
    body.append(
        '<p>数据来源：<a href="https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce">'
        "Olist / Kaggle</a>，数据许可 CC BY-NC-SA 4.0，以来源页面为准。</p>"
    )
    html = (
        """<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Olist 电商分析</title><style>
body{font:16px/1.65 system-ui,sans-serif;max-width:1160px;margin:36px auto;padding:0 22px;color:#163347}
h1,h2{color:#15566a}img{max-width:100%;height:auto}.scroll{overflow-x:auto}
table{border-collapse:collapse;font-size:13px;width:100%}th,td{padding:7px 10px;border:1px solid #d4e2e8;white-space:nowrap}
th{background:#e8f1f4;text-align:left}tr:nth-child(even){background:#f5f8fa}
</style><body>"""
        + "\n".join(body)
        + "</body></html>"
    )
    path = output / "report.html"
    path.write_text(html, encoding="utf-8")
    return path
