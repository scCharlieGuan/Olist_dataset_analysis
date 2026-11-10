# 验证与复现

验证日期：2026-11-03。执行环境为 Python 3.12.14，使用隔离的 MySQL Community Server **8.4.7**。本环境没有 Conda；交付的命令与环境配置面向你的 `ml` 环境，未声称已经访问或运行你电脑上的 `ml`。

本次实际依赖版本：PyMySQL 1.2.3、python-dotenv 1.2.4、matplotlib 3.10.8、DuckDB 2.0.0、SQLGlot 30.27.0、Ruff 0.17.3。DuckDB 与 SQLGlot 仅用于开发期测试，生产分析通过 PyMySQL 连接 MySQL。

## 自动化测试

15 项测试全部通过，包括在 MySQL 8.4.7 上直接执行原始 SQL 的集成测试，没有将 MariaDB 或 SQLite 当成 MySQL。

| 层次 | 验证内容 |
| --- | --- |
| Python 导入 | 空值、前导零、整数小数形式、精确金额、多行文本、拒绝截断/舍入 |
| 事务编排 | 成功提交、后续 CSV 出错回滚、拒绝重复追加 |
| SQL 方言 | 所有 SQL 文件按 MySQL 方言解析，每文件一条语句 |
| 合成样例语义 | 多商品×多支付不放大金额、最新评价、同日送达、缺失预计时间 |
| 时间与分母 | 无订单月份补零、首月/零分母环比、评价覆盖率与已评价分母 |
| 质量闸门 | 重复维度键被识别；订单、品类、商品、支付汇总守恒 |
| 报告 | 来源标记、HTML 转义、CSV 被篡改时拒绝生成 |
| 原生 MySQL | 建表、导入、建视图、质量校验、12 查询、HTML、EXPLAIN ANALYZE、索引清理 |

DuckDB/SQLGlot 的测试用于快速语义回归，不替代原生 MySQL 测试。集成测试在独立空数据库上加载六笔合成订单，结束时删除这些测试行；不会删除数据库或表。

## 在你的机器上运行测试

普通测试不需要 MySQL：

```shell
conda run -n ml python -m unittest discover -s tests -v
conda run -n ml python -m ruff check src tests
```

没有开启原生集成测试时，测试输出会有 1 个 skipped，属于预期。

原生集成测试必须使用**专门的空数据库**，数据库名以 `_test` 结尾。先由管理员创建 `olist_analytics_test` 并赋予测试用户相应权限；测试用户还需 DELETE 权限以清理自己插入的行。请勿指向已经导入真实数据的数据库。

PowerShell：

```powershell
$env:MYSQL_DATABASE="olist_analytics_test"
$env:RUN_MYSQL_TESTS="1"
conda run -n ml python -m unittest discover -s tests -v
Remove-Item Env:RUN_MYSQL_TESTS
Remove-Item Env:MYSQL_DATABASE
```

Bash：

```bash
MYSQL_DATABASE=olist_analytics_test RUN_MYSQL_TESTS=1 conda run -n ml python -m unittest discover -s tests -v
```

其他连接配置取自 `.env` 或你显式导出的变量；环境变量优先，密码不进入源码和测试日志。

## 真实数据验证

数据来自 Olist 在 Kaggle 的官方公开下载，使用本次实际取得的版本，不假定其他镜像/版本行数相同。8 个核心文件通过严格类型转换；未把地理表加入本版经营分析。

| 文件对应实体 | 本次行数 |
| --- | ---: |
| customers | 99,441 |
| products | 32,951 |
| sellers | 3,095 |
| category_translation | 71 |
| orders | 99,441 |
| order_items | 112,650 |
| order_payments | 103,886 |
| order_reviews | 99,224 |

完整源文件 SHA-256 及实际结果清单见 `examples/real_run/import_manifest.json` 和 `analysis_manifest.json`。真实数据输出与合成样例分开保存。原始 CSV 不随项目重新分发。

本次 51 条质量检查中所有 FAIL 条件均为 0，以下 WARN 保留用于解释口径：

| 检查 | 数量 | 说明 |
| --- | ---: | --- |
| 一单多次评价 | 547 | 按订单计组，最新评价视图处理 |
| review_id 重复 | 789 | 按重复 ID 分组计数，不把其当全局唯一主键 |
| 已交付订单缺审批时间 | 14 | 不影响本版实际/预计日期的比较 |
| 已交付订单缺承运时间 | 2 | 记录为质量问题 |
| 已交付订单缺送达/预计时间 | 8 | 从配送指标分母排除 |
| 日期顺序异常 | 189 | 全状态的 OR 条件计行；不等于排除 189 笔已交付订单 |
| 商品品类未匹配翻译 | 623 | 包含缺品类，保留葡语回退或 unknown |
| 商品加运费与支付差额超过 0.01 BRL | 303 | 有商品且有支付订单，全数据范围；不强制修改金额 |

## 边界

- 本版验证一次性导入和离线只读分析，未测试多人并发写入、生产部署和迁移流程。
- 原生测试版本是 8.4.7；要求的最低版本 8.0.18 未另行实测。
- 可选 geolocation 的坐标转换有单元覆盖，但未在 MySQL 导入整张可选地理表做全量测试。
- 性能只以当前机器与固定范围的真实测量为证据，不代表你的 Windows/MySQL 硬件配置。
