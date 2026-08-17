"""Study B 半实时本地桥接（thin bridge）—— 托管采集器 HTML + 转发生成请求。

设计目标（见 docs/specs/study-B-collector-live.md §2/§4/§5/§9）：

* **只监听 127.0.0.1**（不对外，规避 CORS 且不暴露到网络）。
* GET ``/`` 返回生成好的采集器 HTML（浏览器同源访问，避免 file:// 直连被 CORS 拦）。
* POST ``/api/generate`` 接收 ``{condition, task_id, stop_id|prompt_text}``，在 **服务端**
  组装最终 message，转发到本地 OpenAI 兼容代理 ``http://localhost:8313/v1/chat/completions``，
  回 ``{output_text, model_id, params_hash}``。

**公平性硬约束（§5，审计逐条核验）**：滑块每一档 = 一段 **冻结的、通用的单维风格预设**
（只做语气/正式度位移），**严禁编码任务成功条件**（如"≤40 字 / 纯素 / 不用感叹号"）。
两条件都送 **同一 base 素材 + 同目标**；差异只在"控制方式"：滑块用冻结预设、自写条件用
参与者 prompt。预设文本 **只存服务端、绝不回显给前端**（模拟潜控件的不透明性）。

**安全边界**：模型白名单 + 冻结参数（temperature=0, max_tokens=512）；只接受已知
``task_id`` / ``stop_id``；未知输入一律拒绝。

**诚实边界**：任务/素材均为虚构；模型输出是 **数据**，不是"答案键"。桥接不落任何数据库，
生成结果只在内存并回给浏览器；每人一份 JSON 导出。协议未冻结 → 数据 exploratory。

Status: RED pre-freeze DRAFT 工具。纯标准库，无第三方依赖。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable

# 让本脚本无论从哪里启动都能 import 同目录下的生成器模块。
sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_studyB_live as collector  # noqa: E402

# --- 冻结项（协议冻结时锁定；改动须重走 audit）--------------------------------

BRIDGE_VERSION = "studyB-bridge-0.1.0-draft"

# 只监听本地回环地址；桥接不得对外暴露。
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8899

# 上游本地 OpenAI 兼容代理（owner 的 Copilot 代理）。
UPSTREAM_URL = "http://localhost:8313/v1/chat/completions"
UPSTREAM_TIMEOUT_SECONDS = 60

# 模型白名单（冻结时锁定为单一 id）+ 冻结采样参数。
DEFAULT_MODEL_ID = "gpt-4o-mini"
MODEL_WHITELIST = frozenset({"gpt-4o-mini"})
FROZEN_TEMPERATURE = 0
FROZEN_MAX_TOKENS = 512

# 组装模型输入用的系统指令（两条件完全一致，保证对称）。
SYSTEM_INSTRUCTION = (
    "You are assisting with a fictional, illustrative writing task. Use the "
    "provided context and apply the additional instruction. Return only the "
    "requested text."
)

# 任务集（服务端真相）。**构念效度关键约束（修 A）**：任务成功条件（如 vegan / <40 词 /
# friendly / 不用感叹号）属 ``participant_goal``，**只在参与者 UI 展示、永不自动进模型输入**。
# 这里的 ``model_context`` 只含中性的"写什么" + 待处理素材（**不含任何成功条件字样**），两条件
# 都送它；唯一差别 = 滑块的冻结风格预设 vs 参与者自写 prompt。这样：滑块条件模型拿不到成功
# 条件（天然可能漏 vegan/字数 —— 正是要暴露的滑块局限）；自写条件能否传达成功条件取决于
# 参与者会不会写。若把成功条件自动喂给两边，滑块就靠"系统替它说明要求"作弊，两条件失去区分度。
#
# ``presets`` 只做通用语气/正式度位移，绝不编码任务成功条件。
# ``task_id`` / ``stop_id`` 必须与 generate_studyB_live.py 的参与者侧元数据一致。
FROZEN_TASKS: dict[str, dict[str, Any]] = {
    "draftA-recipe-blurb": {
        # 中性上下文（"写什么" + 产品事实素材），两条件共享、原样送模型。
        # **不含成功条件**：无 "vegan"/"40 words"/"friendly"/"exclamation" 等字样。
        "model_context": (
            "Write a short product blurb for the fictional 'Sunrise Oat Bar', a "
            "snack. Product facts: made of rolled oats, chopped dates, almond "
            "butter, and sunflower seeds; chewy texture, lightly sweet; sold in "
            "packs of six. All product facts are invented for a research example."
        ),
        # 滑块档位的冻结风格预设：**仅通用语气/正式度位移**，绝不编码任务成功条件。
        # 注意：档位描述刻意避开任何成功条件字样（尤其 "friendly" —— 它与
        # participant_goal 的"friendly tone"要求重叠，故不入预设，保持纯正式度轴）。
        "presets": {
            "s1": "Write in a very casual, relaxed, conversational tone.",
            "s2": "Write in a casual, easygoing tone.",
            "s3": "Write in a neutral, balanced, even-handed tone.",
            "s4": "Write in a polished, refined tone.",
            "s5": "Write in a formal, professional tone.",
        },
    },
}


class RequestError(ValueError):
    """请求不合法（未知 task/stop、缺字段、非白名单模型等）。"""

    def __init__(self, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.status = status


class UpstreamError(RuntimeError):
    """转发到 8313 失败（不通/超时/响应异常）。"""


def params_hash(model_id: str) -> str:
    """对冻结参数集算稳定哈希，写入导出供复现。"""
    canonical = json.dumps(
        {
            "model": model_id,
            "temperature": FROZEN_TEMPERATURE,
            "max_tokens": FROZEN_MAX_TOKENS,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def _resolve_model(payload: dict[str, Any]) -> str:
    """解析并校验模型 id（缺省用默认；非白名单一律拒绝）。"""
    model_id = payload.get("model_id", DEFAULT_MODEL_ID)
    if not isinstance(model_id, str) or model_id not in MODEL_WHITELIST:
        raise RequestError(f"model_id not in whitelist: {model_id!r}")
    return model_id


def validate_request(payload: Any) -> dict[str, Any]:
    """校验前端请求，返回规范化后的字段。未知输入一律拒绝。"""
    if not isinstance(payload, dict):
        raise RequestError("request body must be a JSON object")

    condition = payload.get("condition")
    if condition not in {"slider", "own_prompt"}:
        raise RequestError(f"unknown condition: {condition!r}")

    task_id = payload.get("task_id")
    if task_id not in FROZEN_TASKS:
        raise RequestError(f"unknown task_id: {task_id!r}")

    model_id = _resolve_model(payload)

    result: dict[str, Any] = {
        "condition": condition,
        "task_id": task_id,
        "model_id": model_id,
        "stop_id": None,
        "prompt_text": None,
    }

    if condition == "slider":
        stop_id = payload.get("stop_id")
        if stop_id not in FROZEN_TASKS[task_id]["presets"]:
            raise RequestError(f"unknown stop_id: {stop_id!r}")
        result["stop_id"] = stop_id
    else:  # own_prompt
        prompt_text = payload.get("prompt_text")
        if not isinstance(prompt_text, str) or not prompt_text.strip():
            raise RequestError("own_prompt requires non-empty prompt_text")
        # 冻结长度上限，防止把整篇内容塞进"prompt"绕过研究对象。
        if len(prompt_text) > 4000:
            raise RequestError("prompt_text too long")
        result["prompt_text"] = prompt_text.strip()

    return result


def assemble_messages(
    condition: str,
    task_id: str,
    stop_id: str | None,
    prompt_text: str | None,
) -> list[dict[str, str]]:
    """在服务端组装最终 message（两条件结构对称）。

    两条件都送同一 ``model_context``（中性上下文 + 素材，**不含任务成功条件**）+ 一个
    "附加指令"块。附加指令块：滑块 = 冻结风格预设（按 stop_id 取，不回显前端）；自写 =
    参与者 prompt。**任务成功条件（participant_goal）永不由本函数注入**——只有当参与者
    自己把它写进 own_prompt 时才会经其 prompt_text 进入模型。
    """
    task = FROZEN_TASKS[task_id]
    if condition == "slider":
        assert stop_id is not None
        additional = task["presets"][stop_id]
    else:
        assert prompt_text is not None
        additional = prompt_text

    user_content = (
        f"Context:\n{task['model_context']}\n\n"
        f"Additional instruction:\n{additional}"
    )
    return [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        {"role": "user", "content": user_content},
    ]


def call_upstream(messages: list[dict[str, str]], model_id: str) -> str:
    """转发到本地 8313 代理并抽取 output_text。失败抛 UpstreamError。"""
    body = json.dumps(
        {
            "model": model_id,
            "temperature": FROZEN_TEMPERATURE,
            "max_tokens": FROZEN_MAX_TOKENS,
            "messages": messages,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        UPSTREAM_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=UPSTREAM_TIMEOUT_SECONDS) as response:
            parsed = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise UpstreamError(f"upstream request failed: {error}") from error
    except json.JSONDecodeError as error:
        raise UpstreamError(f"upstream returned non-JSON: {error}") from error

    try:
        output_text = parsed["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise UpstreamError(f"unexpected upstream response shape: {error}") from error
    if not isinstance(output_text, str):
        raise UpstreamError("upstream output_text is not a string")
    return output_text


def generate_endpoint(
    payload: Any,
    forward: Callable[[list[dict[str, str]], str], str] = call_upstream,
) -> dict[str, Any]:
    """/api/generate 的纯逻辑：校验 → 组装 → 转发 → 结构化返回。

    ``forward`` 可注入，便于单测以本地 stub 替换（单测绝不真打 8313）。
    """
    fields = validate_request(payload)
    messages = assemble_messages(
        fields["condition"], fields["task_id"], fields["stop_id"], fields["prompt_text"]
    )
    output_text = forward(messages, fields["model_id"])
    return {
        "output_text": output_text,
        "model_id": fields["model_id"],
        "params_hash": params_hash(fields["model_id"]),
        "bridge_version": BRIDGE_VERSION,
    }


class _Handler(BaseHTTPRequestHandler):
    server_version = "studyB-live-bridge/0.1"

    # 生成一次 HTML 缓存在类上（同一进程复用）。
    html_bytes: bytes = b""

    def _send_json(self, status: int, obj: dict[str, Any]) -> None:
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802 (stdlib naming)
        if self.path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(self.html_bytes)))
            self.end_headers()
            self.wfile.write(self.html_bytes)
        else:
            self._send_json(404, {"error": "not_found", "detail": self.path})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/generate":
            self._send_json(404, {"error": "not_found", "detail": self.path})
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            self._send_json(400, {"error": "bad_request", "detail": "invalid length"})
            return
        raw = self.rfile.read(length) if length > 0 else b""
        try:
            payload = json.loads(raw.decode("utf-8")) if raw else {}
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_json(400, {"error": "bad_request", "detail": "invalid JSON"})
            return
        try:
            result = generate_endpoint(payload)
        except RequestError as error:
            self._send_json(error.status, {"error": "invalid_request", "detail": str(error)})
            return
        except UpstreamError as error:
            # 8313 不通/超时 → 结构化错误，前端提示"生成失败，请重试"，不崩。
            self._send_json(502, {"error": "generation_failed", "detail": str(error)})
            return
        self._send_json(200, result)

    def log_message(self, fmt: str, *args: Any) -> None:  # 静默默认访问日志
        return


def make_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> ThreadingHTTPServer:
    """构造仅绑定 host 的 HTTP server（默认 127.0.0.1）。"""
    # 纵深防御：桥接会代理到本机 Copilot 代理，绝不允许对外暴露。
    assert host in ("127.0.0.1", "localhost"), f"bridge must bind loopback only, got {host!r}"
    _Handler.html_bytes = collector.build_html().encode("utf-8")
    return ThreadingHTTPServer((host, port), _Handler)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    # 强制只监听回环地址；不提供 --host 以避免误绑 0.0.0.0。
    args = parser.parse_args(argv)
    server = make_server(DEFAULT_HOST, args.port)
    url = f"http://{DEFAULT_HOST}:{args.port}/"
    print(f"Study B live bridge ({BRIDGE_VERSION})")
    print(f"  serving collector at {url}")
    print(f"  forwarding to {UPSTREAM_URL} (model whitelist: {sorted(MODEL_WHITELIST)})")
    print("  press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopping bridge...")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
