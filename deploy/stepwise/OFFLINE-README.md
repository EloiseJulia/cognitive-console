# V3 stepwise 离线单文件版（owner 手册）

## 边界与 gate（先读）

- 所有产品、按钮和试用记录均为**示意/虚构材料**，不代表真实产品或功效。
- 这是**无服务器、无数据库、无数字签名**的离线采集；文件带 `signed: false`，真实性依赖参与者诚实回传，不能与签名版混析。
- 当前数据仅属于 **exploratory pilot**；协议未冻结，单个参与者不代表整体，不得升级为 confirmatory 核心证据。
- 知情同意仍是双语**草案**，含研究者、时长、保存期限、补偿、伦理批准和年龄等占位符。正式招募前必须由导师/伦理审查完成定稿并确认许可、隐私与保存方案。
- 合并前仍须独立敌对审计：检查答案泄漏、owner 判分对拍、schema 隔离、材料逻辑指纹不变。

## 1. 生成并自检

从仓库根目录运行（Windows PowerShell）：

```powershell
$env:PYTHONPATH = "src"
python scripts\generate_stepwise_offline.py
```

产物为：

`deploy\stepwise\offline\button-board-stepwise-offline.html`（已随仓库提交，可直接取用；改材料后重跑生成器会更新它）

生成器使用可信 Python 材料接口，只允许公开字段进入 24 个分配题包；写盘后会重新读取，并对私有答案键执行 fail-closed 检查。

## 2. 分发与回收

1. 将上面的**单个 HTML** 文件发给志愿者；不需要安装软件或连接服务器。
2. 志愿者在桌面浏览器本地打开文件，选择语言、阅读并勾选知情同意草案 gate。
3. 页面随机分配 24 格之一，完成示范、6 个逐步场景、阅读检查和可选结构化反思。
4. 完成页分别点击“下载未签名 JSON”和“下载未签名 CSV”。请参与者将**两个文件**原样回传，不要编辑。
5. owner 将 JSON 放进一个仅含本轮回收 JSON 的目录。CSV 用于人工查看；正式汇总以 JSON 为输入。

不要公开 owner 端仓库、汇总脚本或包含私有判分键的材料。回收渠道、访问权限、保留期限和删除程序须遵循导师/伦理批准后的方案。

## 3. owner 离线汇总

```powershell
$env:PYTHONPATH = "src"
python scripts\aggregate_stepwise_offline.py path\to\returned-json --out-dir path\to\summary
```

输出：

- `participants.csv`：每位参与者一行；
- `per_trial.csv`：每个 trial 一行，含参考状态、实际状态、逐步匹配和时长；
- `summary.json`：与可信 `analysis.analyze()` 结构对齐的聚合，加上接受、跳过与告警清单。

CSV 为 UTF-8 BOM，并对可能触发电子表格公式的单元格加 `'` 前缀。汇总器会拒绝错误 schema、签名版 v8、缺失 `submission_id`、材料 hash/version、locale hash、A/B hash 或 allocation 身份不一致的文件。每份导出在本地生成一个随机 `submission_id`（知情同意中已说明其用途）；若同一 `submission_id` 出现多次（例如同一文件被重复回传），汇总器只计入首次、其余记入 skipped，避免静默重复计数。它按原始逐步答案重建路径；派生状态不一致时以重建值判分并记录告警。

## 4. 每轮必须保存的核验记录

- 使用的代码 commit 与生成 HTML 的材料 hash；
- 收到的原始文件只读副本及文件 hash（不要覆盖不可再生数据）；
- 汇总 stdout、`summary.json` 的 skipped/warnings；
- 本轮 exploratory 身份、招募许可与数据处理决定；
- 合并前测试、指纹、generator-current 与独立 audit 结论。
