# Study B —— 半实时本地采集器（LIVE）owner 运行手册

> 🔴 pre-freeze DRAFT。伦理已批（owner 2026-08-17），但 **采数据前** 仍须过 spec §12
> 未清项（协议冻结 + MDE 预注册、预设冻结 + 独立 audit、隐私方案、本实现 audit）。
> 协议未冻结 → 所收数据一律 **exploratory**。

本工具是 spec `docs/specs/study-B-collector-live.md` 的实现：主任务两条件都会显示 **真实模型
输出**（经本地桥接转发到你已有的 Copilot 代理 `http://localhost:8313`），无需数据库。

## 组成

| 文件 | 作用 |
|---|---|
| `scripts/run_studyB_live.py` | 本地桥接：托管采集器 HTML + `POST /api/generate` 转发到 8313（**只监听 127.0.0.1**，模型白名单 + 冻结参数 + 服务端冻结预设）。 |
| `scripts/generate_studyB_live.py` | 生成单页采集器 HTML（`deploy/studyB/live/studyB-collector-live.html`）。 |
| `scripts/aggregate_studyB_live.py` | 汇总回收的 JSON → `participants.csv` / `tasks.csv` / `generations.csv` / `summary.json`。 |

## 前置

1. 你的本地 Copilot 代理已在 `http://localhost:8313`（OpenAI 兼容）运行，且 `gpt-4o-mini`
   + `temperature=0` 可用。
2. Python 3.12。桥接与生成器 **纯标准库**，无需额外安装。

## 一条命令启动

```powershell
Set-Location "C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\.worktrees\studyB-live"
python scripts\run_studyB_live.py            # 默认端口 8899
# 或指定端口： python scripts\run_studyB_live.py --port 9001
```

启动后终端会打印链接（形如 `http://127.0.0.1:8899/`）。桥接会 **在启动时自动生成最新 HTML**，
无需先手动跑生成器（若想单独产出 HTML 文件，可跑 `python scripts\generate_studyB_live.py`）。

## 参与者流程

1. 在同一台机器的浏览器打开打印出的 `http://127.0.0.1:<port>/` 链接。
2. 参与者按页面完成：consent → 背景问卷 → prompt 热身（不出输出）→ 主任务（滑块 / 自写
   两条件，**都会点"生成输出"看到真实 AI 输出**，可多次重生成）→ 主观评分 → 注意力检查。
3. 结束页点 **"下载 JSON"**，得到一份 `studyB-live-XXXXXXXX.json`。
4. 请参与者按你的指示 **诚实回传** 该 JSON（本工具不落库、不自动上传）。

## 收数据 + 汇总

把回收到的所有 `*.json` 放进一个目录（如 `returns\`），然后：

```powershell
python scripts\aggregate_studyB_live.py returns --out-dir out
```

产物（`out\`）：
- `participants.csv` —— 一行/人（含 `model_id` / `params_hash`）。
- `tasks.csv` —— 一行/人×任务；含 **空** `q_slider_pending` / `q_own_prompt_pending` /
  `d_paired_pending`（事后 Q 评分回填）。
- `generations.csv` —— **一行/次生成**；`output_text` 单列保存（供事后 Q 批量评分取用）。
- `summary.json` —— accepted / skipped / warnings + `q_scoring.computed_here=false` + `model_id`。

## 安全 / 诚实边界

- 桥接 **只监听 127.0.0.1**，不对外；只接受已知 `task_id` / `stop_id`；模型白名单
  （默认仅 `gpt-4o-mini`）+ 冻结参数（`temperature=0`, `max_tokens=512`）。
- 滑块每一档背后是一段 **冻结的、通用的单维风格预设**，只做语气/正式度位移，**绝不编码
  任务成功条件**（纯素/字数/感叹号等）；预设文本 **只存服务端，不回显给前端**。
- 8313 不通/超时时，`/api/generate` 回结构化错误，前端提示"生成失败，请重试"，不崩。
- 模型输出是 **数据**，不是"答案键"；导出 / DOM / CSV 均无 `expected` / `correct*` /
  `answer_key` / `rubric` / Q 值 **键名**。
- 任务/素材虚构；单人不代表整体；协议未冻结 → exploratory，**不得**直接当 confirmatory
  去镜像模型侧 0/12。

## 停止

在运行桥接的终端按 `Ctrl+C`。
