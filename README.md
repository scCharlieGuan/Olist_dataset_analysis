# 基于 MySQL 的电商经营与履约分析

用 Olist 巴西电商历史订单回答三个问题：经营表现如何变化、配送问题集中在哪里、配送延迟与客户差评有何关联。核心清洗、关联、聚合、窗口计算均在 **MySQL SQL** 中完成；Python 只负责配置、CSV 导入、流程编排、结果导出和可视化。

本项目是可运行的第一版工程。`examples/real_run/` 保存本次真实数据结果，`examples/synthetic_report.html` 是独立的**合成样例**。完整 Olist 原始数据需要自行下载；本次验证范围见 [VALIDATION.md](docs/VALIDATION.md)，业务发现见 [FINDINGS.md](docs/FINDINGS.md)。

## 快速开始

### 1. 使用现有 Conda `ml` 环境

在项目根目录运行（Windows PowerShell、Anaconda Prompt 均可）：

```shell
conda run -n ml python --version
conda run -n ml python -m pip install -e ".[dev]"
```

需要 Python 3.10 及以上。已有 `ml` 环境时无需重建；如果尚不存在，先运行 `conda env create -f environment.yml`，然后继续。`environment.yml` 供新环境使用，不要求修改你现有环境中的其他项目。

### 2. 准备 MySQL 与配置

推荐 **MySQL 8.4 LTS**，最低 8.0.18；不以 MariaDB 代替 MySQL。复制 `.env.example` 为 `.env`，修改数据库、用户和密码。

已有 MySQL：由管理员一次性创建专用数据库及用户（密码自行替换，默认配置数据库名如下）：

```mysql
CREATE DATABASE olist_analytics CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;
CREATE USER 'olist'@'localhost' IDENTIFIED BY 'your_local_password';
GRANT SELECT, INSERT, CREATE, CREATE VIEW, SHOW VIEW, DROP, INDEX, ALTER
  ON olist_analytics.* TO 'olist'@'localhost';
```

请按实际连接地址配置用户的 host 匹配规则。此用户只用于本地专用数据库；`ANALYZE TABLE` 需要 SELECT、INSERT，`CREATE OR REPLACE VIEW` 需要 DROP 权限。流程不会自动创建数据库或删除已有业务数据。

如果安装了 Docker，也可以直接运行：

```shell
docker compose up -d --wait
```

Compose 从 `.env` 创建数据库和项目用户，并把端口只绑定到本机。首次启动后修改 `.env` 不会修改已有数据卷里的数据库密码；请通过 MySQL 修改账户或使用另一套新数据库配置。

### 3. 下载官方 CSV

数据来源：[Olist Brazilian E-Commerce Public Dataset / Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)。解压到 `data/raw/`，保留文件原名。默认需要以下八个文件：

| 文件 | 粒度 |
| --- | --- |
| `olist_orders_dataset.csv` | 一笔订单 |
| `olist_order_items_dataset.csv` | 订单中的一条商品明细 |
| `olist_order_payments_dataset.csv` | 订单的一条支付记录 |
| `olist_order_reviews_dataset.csv` | 一条评价记录，不能假定每单只有一条 |
| `olist_customers_dataset.csv` | `customer_id`，非唯一自然人 |
| `olist_products_dataset.csv` | 一件商品 |
| `olist_sellers_dataset.csv` | 一个卖家 |
| `product_category_name_translation.csv` | 一个葡语品类的英文映射 |

第九个 `olist_geolocation_dataset.csv` 为可选，不影响本版分析。需要时添加 `--include-geo` 导入。地理表的邮编前缀不唯一，不能直接关联到订单表后汇总金额。本版用客户州进行地区分析。

### 4. 一次运行

```shell
conda run -n ml python -m olist_analytics run
```

依次执行建表 → 全量导入 → 原始数据质量检查 → 建视图 → 金额对账 → 12 个分析查询 → CSV 与离线 HTML 报告。

打开 `reports/report.html`；图表已嵌入文件，查看报告无需启动服务。`reports/` 同时包含 12 份 CSV、质量检查和导入/分析清单。金额以 BRL 表示，比率为 0–1，空值不会被写成 0。

默认只分析购买时间在 **\[2017-01-01, 2018-09-01)**  的订单，包含 2017 年 1 月至 2018 年 8 月。此范围用于避开明显的边缘月份，**不是数据完整性的证明**。第 12 个查询始终检查全量数据覆盖；可根据审计结果修改 `.env`。不要据此把 2018 年 8 月末尚未交付的订单误判为业务流失。

### 5. 分阶段执行及重复运行

```shell
conda run -n ml python -m olist_analytics init
conda run -n ml python -m olist_analytics import
conda run -n ml python -m olist_analytics build
conda run -n ml python -m olist_analytics check
conda run -n ml python -m olist_analytics analyze
conda run -n ml python -m olist_analytics report
conda run -n ml python -m olist_analytics benchmark
```

`run`/`import` **要求所有 raw 表为空**，避免重复追加。导入成功后只需重复 `build`、`analyze`、`report`；不要再次 `run`。需要重新导入时，建立新数据库并更新 `.env`。导入事务失败会回滚全部数据，不会留下半批订单；建表 DDL 本身会提交，这是 MySQL 的行为。

可指定 `--data-dir`、`--output-dir`。相对路径相对于项目根目录，绝对路径也支持。`--root` 用于显式指定含 `sql/`、`.env` 的项目目录。推荐保留源码目录并以 `pip install -e` 安装，本版不发布独立 wheel。

## 文件结构

```text
olist-mysql-analytics/
  README.md
  environment.yml            # ml 环境配置
  pyproject.toml             # 依赖、可编辑安装、命令入口
  .env.example               # 数据库、日期范围、最小样本量
  compose.yml                # 可选 MySQL 8.4 服务
  src/olist_analytics/
    config.py                # 配置验证
    catalog.py               # CSV 字段、类型、逻辑键定义
    db.py                    # 连接、版本要求、严格 SQL 模式
    ingest.py                # 流式导入、精确金额、哈希、事务
    pipeline.py              # SQL 编排、质量闸门、结果清单
    benchmark.py             # 执行计划与真实计时
    report.py                # 离线图表与表格报告
    cli.py                   # 统一命令入口
  sql/
    01_...09_*.sql           # 保留源字段的 raw 表，不静默删除重复数据
    20_reviews_latest.sql    # 订单级评价清洗视图
    21_order_fact.sql        # 订单级分析视图
    22_order_category.sql    # 订单×品类视图
    quality/                 # 主键、外键、时间、金额对账
    analysis/                # 12 个业务分析查询
    optimization/            # 等价基线和可索引查询
  docs/                      # 表关系、指标字典、验证与优化说明
  tests/                     # 导入测试、SQL 语义测试、MySQL 集成测试
  examples/                  # 真实数据输出与独立的合成样例报告
  data/raw/                  # 自行下载，不提交原始数据
  reports/                   # 本机运行生成，不提交输出与凭据
```

## 分析内容

| SQL | 回答的问题 | 主要能力 |
| --- | --- | --- |
| 01 | 月订单、GMV、运费、客单价、环比 | 递归月份表、CTE、LAG、NULLIF |
| 02 | 各状态订单规模和覆盖 | 条件聚合、窗口分母 |
| 03 | 品类 GMV 贡献和排名 | 多表关联、预聚合、DENSE_RANK |
| 04 | 每月头部品类 | 分区排名 |
| 05 | 月配送延迟率及排除样本 | 日期运算、条件聚合 |
| 06 | 客户州配送表现 | JOIN、样本量筛选 |
| 07 | 卖家参与订单及单卖家敏感性 | 去重桥接、条件分母 |
| 08 | 延迟区间与差评率 | CASE、评价覆盖率 |
| 09 | 品类内的延迟与差评关系 | 分层比较 |
| 10 | 同州同月迟到与准时订单差评差值 | 多维分层、组内比较 |
| 11 | 支付金额与商品加运费对账 | 精确 DECIMAL、差异审计 |
| 12 | 数据全集时间与状态覆盖 | 分析边界审计 |

在 MySQL 客户端单独执行 SQL 时，先设置相同的会话变量：

```sql
SET @start_date='2017-01-01', @end_date='2018-09-01', @min_orders=30;
-- 然后执行所选 sql/analysis/*.sql 文件
```

完整定义见 [指标字典](docs/METRICS.md)；模型与表关系见 [数据模型](docs/DATA_MODEL.md)。

## 结果验证与优化

```shell
conda run -n ml python -m unittest discover -s tests -v
conda run -n ml python -m ruff check src tests
```

默认测试包含 MySQL 方言解析和转换到 DuckDB 后的合成样例验证；这**不等同于真实 MySQL 集成测试**。启用原生集成测试的方法见 [验证说明](docs/VALIDATION.md)。

`benchmark` 分别测量改写前后以及加索引前后的查询，输出 `EXPLAIN ANALYZE`、逐次耗时与中位数到 `reports/benchmark.json`。实验索引完成后自动删除，不假定一定更快。方法和限制见 [优化实验](docs/OPTIMIZATION.md)。

## 数据局限与后续分析

- 已交付 GMV 按历史快照中的最终状态筛选，下单月份只是分组依据；它不是当时可实时知道的月度指标。数据没有可靠的退款、平台抽佣和成本信息，不能计算平台营收或利润。
- 延迟分析排除未交付或缺失/不合理时间的订单，存在选择偏差；后续可另做未交付订单与取消分析。按日期计算是运营口径，不代表精确到小时的 SLA。
- 评价有缺失、多次提交和回应时点差异。只使用最新评价；差评率分母为已评价订单。调查可能在预计交付日期到达后触发，评价也可能早于最终收货。
- 卖家组包含共同履约订单，送达时间是订单级；不能把迟到责任直接归给卖家。品类组也可能重叠，评价是整单体验而非单品评分。
- 同月同州、品类分层可以帮助检查人群构成差异，仍不能把相关性解释成因果关系。小样本筛选不等于置信区间；后续可增加区间估计。
- 数据为 2016—2018 年的历史样本，不能据此推断当前电商表现或推广到其他平台。

本次真实数据的三组初步业务结论见 [FINDINGS.md](docs/FINDINGS.md)，均链接到可核对的查询与 CSV；调整指标口径或数据版本后，应重新运行并更新结论。

## 来源与许可

- [Olist 官方数据发布页](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)：数据使用应遵守其 **CC BY-NC-SA 4.0** 许可及归属要求；本项目不重新分发原始数据。代码生成不改变原始数据许可。
- [MySQL EXPLAIN 文档](https://dev.mysql.com/doc/refman/8.4/en/explain.html)
- [MySQL CREATE VIEW 文档](https://dev.mysql.com/doc/refman/8.4/en/create-view.html)
