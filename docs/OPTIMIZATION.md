# 查询优化实验

## 目的

选用已交付订单在指定 7 天购买区间内的计数，验证函数包裹时间字段和可索引范围条件的差异，并测量复合索引的影响。它是一个真实、常见的经营查询组成部分；不声称代表全部 12 个复杂分析的性能。

基线：`DATE(order_purchase_timestamp) >= @bench_start`。改写：直接比较时间字段，`order_purchase_timestamp >= @bench_start AND order_purchase_timestamp < @bench_end`。边界均为日期的午夜，两者在本实验中语义相同。

## 运行

完成导入后，在空闲、无并发写入的数据库上运行：

```shell
conda run -n ml python -m olist_analytics benchmark
```

范围为 `ANALYSIS_START` 开始的前 7 天，结束不超过 `ANALYSIS_END`。每个阶段：预热一次、保留 `EXPLAIN ANALYZE`、每种查询计时 7 次并轮换顺序，比较所有输出一致性。

| 阶段 | 查询 | 实验索引 |
| --- | --- | --- |
| before_index | DATE 基线及直接范围条件 | 无实验索引，记录原有索引 |
| after_index | 相同两种查询 | `(order_status, order_purchase_timestamp)` |

这样可以分别观察改写、索引和两者结合后的变化，而不是将所有差异归因于某个因素。

输出 `reports/benchmark.json` 包含服务器版本、原有索引、实际范围、两条查询结果、执行计划、每次耗时和中位数。实验索引名称固定为 `idx_benchmark_status_purchase`：如果已存在则拒绝运行；执行结束后在 `finally` 中删除本次创建的索引。如果进程被强制终止，索引可能残留，需自行检查后处理。不要在运行期间修改此索引。

## 如何写入展示报告

以下为本次 MySQL 8.4.7 在官方数据上的真实测量，购买区间为 `[2017-01-01, 2017-01-08)`；四种情况均返回 40 笔已交付订单。证据保存在 `examples/real_run/benchmark.json`，你本机的实验将写入 `reports/benchmark.json`。

| 阶段 | 查询 | 执行计划关键节点 | 实际扫描/返回行 | 7 次中位耗时 ms |
| --- | --- | --- | --- | --- |
| 前 | DATE 基线 | Table scan | 扫描 99,441，过滤后 40 | 32.078 |
| 前 | 范围条件 | Table scan | 扫描 99,441，过滤后 40 | 29.802 |
| 后 | DATE 基线 | Covering index lookup | 索引读入 96,478，过滤后 40 | 29.351 |
| 后 | 范围条件 | Covering index range scan | 范围读入 40，返回 40 | 0.372 |

本次只有改写条件未明显减少扫描；复合索引与直接范围条件结合后显著减少了读取行数。DATE 基线在加索引后仍需扫描大量已交付订单，因此单纯加索引不能代替可索引的过滤条件。此结果只支持该查询、范围与环境下的结论。

计时包括 Python 驱动和网络往返，为热缓存下客户端墙钟时间；`EXPLAIN ANALYZE` 自带的服务端计时也有测量开销。样本很小时差异可能主要来自噪声。索引不保证被优化器采用，也不保证更快；若没有收益，应如实说明选择性、缓存、样本规模和原有索引的影响。

创建/删除索引属于 DDL，会隐式提交；不要在尚未提交的其他业务事务里调用此实验。该命令只应在专用分析数据库运行。
