"""构建 Study B **半实时**采集器（single-file HTML；显示真实模型输出）。

与解耦离线版（``generate_studyB_offline.py``，不显示输出）的区别（见
docs/specs/study-B-collector-live.md）：主任务的两个条件都会 ``fetch('/api/generate')``
经本地桥接（``run_studyB_live.py``）向 8313 代理取 **真实模型输出并显示**，允许重生成、
记录生成次数。其余（consent / covariates / probe / convenience / attention）沿用离线版语义。

**硬契约（审计）**：participant payload / DOM / ARIA / export **不含** ``expected`` /
``correct*`` / ``answer_key`` / ``rubric`` / 任何 Q 值 **键名**。模型输出文本是 **数据**，
不是"答案键"。滑块预设文本 **不在本 HTML 内**（只存服务端桥接，前端 view-source 看不到）。

**自包含**：不 import / 不触碰 V3 button_board_stepwise 包、其冻结答案或 materials v11.3。

Status: 伦理已批（owner 2026-08-17）；协议未冻结 → 所收数据 exploratory。RED DRAFT。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "deploy" / "studyB" / "live" / "studyB-collector-live.html"

EXPORT_SCHEMA = "microstudy-export-live-studyB-v1"
INSTRUMENT_VERSION = "studyB-collector-live-0.1.0-draft"
CONSENT_COPY_VERSION = "studyB-consent-live-1.0"
BRIDGE_VERSION = "studyB-bridge-0.1.0-draft"

# 参与者侧"零答案键"启发式自检（关键词 denylist）。它只能抓已知词，不是结构保证；
# 真正的结构保证在 owner 侧 aggregate_studyB_live.py（精确字段集 + 标量守卫）。
FORBIDDEN_TERMS = (
    "expected",
    "answer_key",
    "answerkey",
    "rubric",
    "gold_answer",
    "ground_truth",
    "correct_answer",
    "correctanswer",
)

HONESTY = {
    "en": (
        "Fictional / illustrative materials only. This study DISPLAYS AI-generated "
        "example outputs. Exploratory pilot; the protocol is NOT frozen. One "
        "participant does not represent any population. This tool draws NO "
        "user-benefit conclusion. Unsigned local return depends on honest submission."
    ),
    "zh-Hans": (
        "示意/虚构材料。本研究会显示 AI 生成的示例输出。仅用于 exploratory pilot；协议未冻结。"
        "单个参与者不代表任何人群。本工具不作任何 user-benefit 结论。无服务器签名，依赖参与者诚实回传。"
    ),
}

CONSENT_COPY = {
    "en": {
        "heading": "Research informed-consent form",
        "body": [
            {
                "title": "Purpose of the study",
                "text": (
                    "This is an anonymous, small academic study of how people "
                    "approach open-ended tasks with two kinds of control: an "
                    "on-screen setting (slider) versus writing their own natural-"
                    "language instruction (prompt)."
                ),
            },
            {
                "title": "What you will do",
                "text": (
                    "You will answer a short background questionnaire, write one "
                    "instruction for a warm-up task, and then work through a "
                    "fictional task. For the main task you will try two ways of "
                    "steering an assistant and SEE the AI-generated example output "
                    "for each, then answer a few subjective questions. The whole "
                    "task takes about 15 minutes. All tasks and materials are "
                    "fictional examples; the displayed outputs are AI-generated "
                    "illustrations, not advice."
                ),
            },
            {
                "title": "Voluntary participation and withdrawal",
                "text": (
                    "Participation is entirely voluntary. You may close the page "
                    "and withdraw at any time with no adverse consequence; you will "
                    "not be evaluated even if you do not finish."
                ),
            },
            {
                "title": "Anonymity and privacy",
                "text": (
                    "This study does not collect your name, contact details, "
                    "account, or any information that could identify you. The system "
                    "records only what you type and choose on this page (including "
                    "the example outputs you generate), plus a randomly generated "
                    "temporary identifier used solely to distinguish separate "
                    "submissions. All inference runs locally on the researcher's "
                    "machine. Please do not type any personal or identifying "
                    "information into the free-text boxes."
                ),
            },
            {
                "title": "How the data is used and stored",
                "text": (
                    "De-identified responses will be used for academic research "
                    "analysis and may be published in aggregate form; no "
                    "individually identifiable information will be disclosed. "
                    "They are stored on the researcher's local encrypted device "
                    "and deleted within 2 years of publication."
                ),
            },
            {
                "title": "Risks and benefits",
                "text": (
                    "There are no known risks in this study. Your participation "
                    "helps us understand how people reason about these two kinds "
                    "of control."
                ),
            },
            {
                "title": "Statement of consent",
                "text": (
                    "By ticking the box below I confirm that: I have read and "
                    "understood the information above, I take part voluntarily, "
                    "and I understand I may withdraw at any time."
                ),
            },
        ],
        "agree": (
            "I have read and understood the information above and volunteer to "
            "take part."
        ),
        "start": "Agree and begin",
        "decline": "I do not agree / Exit",
        "declined": (
            "Thank you for your time. You have exited; no answers were recorded "
            "and you may close this window."
        ),
    },
    "zh-Hans": {
        "heading": "研究知情同意书",
        "body": [
            {
                "title": "研究目的",
                "text": (
                    "这是一项匿名的小规模学术研究，了解人们在开放式任务中如何使用两种控制方式："
                    "界面上的设置（滑块）与自己撰写自然语言指令（prompt）。"
                ),
            },
            {
                "title": "你需要做什么",
                "text": (
                    "你将回答一份简短的背景问卷，为一个热身任务写一条指令，然后完成一个虚构任务。"
                    "在主任务中，你会尝试两种引导助手的方式，并会看到每种方式对应的 AI 生成示例输出，"
                    "再回答几道主观问题。全程大约 15 分钟。所有任务与材料都是虚构示意；"
                    "显示的输出是 AI 生成的示意内容，并非建议。"
                ),
            },
            {
                "title": "自愿参与与退出",
                "text": (
                    "参与完全自愿。你可以在任何时候关闭页面退出，不会有任何不利影响；"
                    "即使不完成，也不会受到任何评价。"
                ),
            },
            {
                "title": "匿名与隐私",
                "text": (
                    "本研究不收集你的姓名、联系方式、账号或任何可识别你身份的信息。系统只记录"
                    "你在本页面内输入与选择的内容（包括你生成的示例输出），以及一个随机生成的临时编号"
                    "（仅用于区分不同作答）。所有推理均在研究者本地机器上运行。"
                    "请不要在自由文本框中填写任何个人或可识别身份的信息。"
                ),
            },
            {
                "title": "数据的用途与保存",
                "text": (
                    "去标识化的作答数据将用于学术研究分析，并可能以汇总形式发表；不会公开任何"
                    "能识别到个人的信息。数据存放在研究者本地加密设备，并在论文发表后 2 年内删除。"
                ),
            },
            {
                "title": "风险与获益",
                "text": (
                    "本研究没有已知风险。你的参与将帮助我们了解人们如何看待这两种控制方式。"
                ),
            },
            {
                "title": "知情同意声明",
                "text": (
                    "勾选下方选项即表示：我已阅读并理解以上信息，"
                    "自愿参加本研究，并知道我可以随时退出。"
                ),
            },
        ],
        "agree": "我已阅读并理解以上信息，自愿参加本研究。",
        "start": "同意并开始",
        "decline": "我不同意 / 退出",
        "declined": "感谢你的时间。你已退出，本页面未记录任何回答，可以直接关闭窗口。",
    },
}

# --- Prompt 写作探针（虚构；不出模型输出；不现场判分）------------------------
PROBE = {
    "task_id": "probe-draft-notice",
    "goal": {
        "en": (
            "Quick warm-up (fictional, about 1 minute). Write ONE plain instruction "
            "telling an assistant how to rewrite the notice below so it: (a) is at "
            "most 60 words, and (b) sounds warm and encouraging. Just one line is "
            "enough — keep it quick, but try to write it as clearly as you can. This "
            "warm-up shows no output; we only record your instruction."
        ),
        "zh-Hans": (
            "快速热身（虚构，约 1 分钟）。写一条简单指令，告诉助手把下面的通知改写为："
            "(a) 不超过 60 字，(b) 语气温暖鼓励。写一条就行，别花太久，但请尽量写清楚。"
            "此热身不显示输出，我们只记录你的指令。"
        ),
    },
    "source_material": {
        "en": (
            "[FICTIONAL NOTICE] The volunteer orientation will be held on March 3 "
            "in Room 214. The 8am shuttle bus has been cancelled. Please arrive by "
            "9:30am. Bring a photo of your favourite plant."
        ),
        "zh-Hans": (
            "[虚构通知] 志愿者说明会将于 3 月 3 日在 214 房间举行。上午 8 点的班车已取消。"
            "请于上午 9:30 前到场。请带一张你最喜欢的植物的照片。"
        ),
    },
}

# --- 主任务（1 个配对任务；虚构占位，最终任务集须单独冻结）------------------
# 注意：task_id 与 slider.stops 的 id 必须与 run_studyB_live.py 的 FROZEN_TASKS 一致；
# 风格预设 **文本** 只存服务端桥接，本处只放参与者可见的档位标签。
#
# **构念效度（修 A）**：``goal`` + ``requirements`` = participant_goal（成功条件：vegan /
# <40 词 / friendly / 不用感叹号）。它 **只在参与者 UI 展示、也记录进导出（是给人看的目标，
# 不是答案键）**，但 **永不自动进模型输入** —— 生成时前端只发 {condition, task_id, stop_id|
# prompt_text} 给桥接，桥接用中性 model_context（不含成功条件）组装。只有参与者自己把成功
# 条件写进 own_prompt 时，它才经其 prompt_text 进入模型。滑块条件模型永远拿不到成功条件。
TASKS = [
    {
        "task_id": "draftA-recipe-blurb",
        "title": {
            "en": "DRAFT Task A — product blurb (fictional)",
            "zh-Hans": "草案任务 A —— 产品简介（虚构）",
        },
        "goal": {
            "en": (
                "DRAFT / fictional. Produce a short blurb for the fictional "
                "'Sunrise Oat Bar'. It should mention it is vegan, be under 40 "
                "words, and sound friendly but not use exclamation marks."
            ),
            "zh-Hans": (
                "草案/虚构。为虚构产品「日出燕麦棒」写一段简短简介。需说明它是纯素，"
                "不超过 40 字，语气友好但不用感叹号。"
            ),
        },
        "requirements": [
            {"en": "Mentions it is vegan", "zh-Hans": "说明是纯素"},
            {"en": "Under 40 words", "zh-Hans": "不超过 40 字"},
            {"en": "Friendly tone, no exclamation marks", "zh-Hans": "语气友好，不用感叹号"},
        ],
        "slider": {
            "label": {
                "en": "Tone / formality setting",
                "zh-Hans": "语气 / 正式度设置",
            },
            "help": {
                "en": (
                    "An opaque control that shifts the assistant's tone. Pick a "
                    "setting, then generate to see the AI output. The exact preset "
                    "behind each stop is hidden (like a latent control)."
                ),
                "zh-Hans": (
                    "一个会调节助手语气的不透明控件。选一档后点生成即可看到 AI 输出。"
                    "每一档背后的具体预设是隐藏的（模拟潜控件）。"
                ),
            },
            "stops": [
                {"id": "s1", "label": {"en": "Very casual", "zh-Hans": "非常随意"}},
                {"id": "s2", "label": {"en": "Casual", "zh-Hans": "随意"}},
                {"id": "s3", "label": {"en": "Neutral", "zh-Hans": "中性"}},
                {"id": "s4", "label": {"en": "Polished", "zh-Hans": "考究"}},
                {"id": "s5", "label": {"en": "Formal", "zh-Hans": "正式"}},
            ],
        },
    },
]

# --- 协变量问卷（通用 AI 熟练度；仅协变量，不分组；已精简为 2 题，D-0135）------
# 分组 **不** 来自本页任何自评；分组由客观写-prompt 能力（热身探针，事后评分）判定。
COVARIATES = [
    {
        "id": "usage_frequency",
        "prompt": {
            "en": "How often do you use AI assistants (e.g. chatbots)?",
            "zh-Hans": "你使用 AI 助手（如聊天机器人）的频率？",
        },
        "options": [
            {"id": "never", "label": {"en": "Never", "zh-Hans": "从不"}},
            {"id": "rarely", "label": {"en": "Rarely", "zh-Hans": "很少"}},
            {"id": "monthly", "label": {"en": "A few times a month", "zh-Hans": "每月几次"}},
            {"id": "weekly", "label": {"en": "A few times a week", "zh-Hans": "每周几次"}},
            {"id": "daily", "label": {"en": "Daily", "zh-Hans": "每天"}},
        ],
    },
    {
        "id": "self_rating",
        "prompt": {
            "en": "Overall, how would you rate your own skill with AI assistants? (1 = novice, 5 = expert)",
            "zh-Hans": "总体而言，你如何评价自己使用 AI 助手的熟练度？（1=新手，5=专家）",
        },
        "scale": {"min": 1, "max": 5},
    },
]

# --- 便利轴：短 TLX/Likert + willingness（现在有意义，因为看过两边输出）-----
CONVENIENCE = {
    "tlx": [
        {
            "id": "tlx_effort",
            "prompt": {
                "en": "Effort: how hard did you have to work? (1 = very low, 7 = very high)",
                "zh-Hans": "努力程度：你需要多努力？（1=很低，7=很高）",
            },
            "scale": {"min": 1, "max": 7},
        },
    ],
    "likert": [
        {
            "id": "likert_effort",
            "prompt": {
                "en": "The slider felt low-effort to use. (1 = strongly disagree, 5 = strongly agree)",
                "zh-Hans": "滑块用起来很省力。（1=非常不同意，5=非常同意）",
            },
            "scale": {"min": 1, "max": 5},
        },
        {
            "id": "likert_discoverability",
            "prompt": {
                "en": "I could tell what the slider was doing. (1 = strongly disagree, 5 = strongly agree)",
                "zh-Hans": "我能看出滑块在做什么。（1=非常不同意，5=非常同意）",
            },
            "scale": {"min": 1, "max": 5},
        },
    ],
    "willingness": {
        "prompt": {
            "en": "Having seen both outputs, which would you be more willing to use for tasks like these?",
            "zh-Hans": "在看过两边的输出后，对于这类任务你更愿意使用哪一种？",
        },
        "options": [
            {"id": "slider", "label": {"en": "The slider", "zh-Hans": "滑块"}},
            {"id": "own_prompt", "label": {"en": "Writing my own prompt", "zh-Hans": "自己写 prompt"}},
        ],
        "reason_prompt": {
            "en": "Why? (optional, free text — do not include personal information)",
            "zh-Hans": "为什么？（选填，自由文本——请勿填写个人信息）",
        },
    },
}

# --- 注意力检查（instructed-response；不把指定项作为答案键存储）-------------
ATTENTION = {
    "instruction": {
        "en": "Attention check: to show you are reading, please select 'Purple'.",
        "zh-Hans": "注意力检查：为表明你在认真阅读，请选择「紫色」。",
    },
    "prompt": {
        "en": "Which option are you instructed to pick?",
        "zh-Hans": "你被要求选择哪个选项？",
    },
    "options": [
        {"id": "red", "label": {"en": "Red", "zh-Hans": "红色"}},
        {"id": "green", "label": {"en": "Green", "zh-Hans": "绿色"}},
        {"id": "purple", "label": {"en": "Purple", "zh-Hans": "紫色"}},
        {"id": "blue", "label": {"en": "Blue", "zh-Hans": "蓝色"}},
    ],
}


def build_payload() -> dict[str, Any]:
    """组装嵌入 HTML 的静态 DATA（不含任何预设文本 / 答案键 / Q 值）。"""
    payload = {
        "export_schema": EXPORT_SCHEMA,
        "signed": False,
        "instrument_version": INSTRUMENT_VERSION,
        "consent_copy_version": CONSENT_COPY_VERSION,
        "bridge_version": BRIDGE_VERSION,
        "honesty_notice": HONESTY,
        "consent_copy": CONSENT_COPY,
        "probe": PROBE,
        "tasks": TASKS,
        "covariates": COVARIATES,
        "convenience": CONVENIENCE,
        "attention": ATTENTION,
    }
    _assert_no_forbidden(payload)
    return payload


def _assert_no_forbidden(value: Any, path: str = "$") -> None:
    """若任何禁用词泄漏进 payload（键或字符串），立即失败。"""
    if isinstance(value, dict):
        for key, item in value.items():
            if any(term in str(key).lower() for term in FORBIDDEN_TERMS):
                raise ValueError(f"forbidden term in key at {path}.{key}")
            _assert_no_forbidden(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _assert_no_forbidden(item, f"{path}[{index}]")
    elif isinstance(value, str):
        if any(term in value.lower() for term in FORBIDDEN_TERMS):
            raise ValueError(f"forbidden term in string at {path}")


HTML_TEMPLATE = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Study B collector (live, unsigned, DRAFT)</title>
<style>
:root{color-scheme:light}
*{box-sizing:border-box}
body{font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;margin:0;line-height:1.5;color:#1f2328;background:#f6f8fa}
header#site-header{padding:12px 16px;background:#24292f;color:#fff;display:flex;flex-direction:column;gap:6px}
header#site-header strong{font-size:1rem}
#fiction-banner{font-size:.85rem;color:#ffd8a8}
main#app{max-width:760px;margin:0 auto;padding:16px}
footer#site-footer{max-width:760px;margin:0 auto;padding:16px;display:flex;justify-content:space-between;align-items:center;gap:12px;color:#59636e;font-size:.85rem}
.panel{background:#fff;border:1px solid #d0d7de;border-radius:8px;padding:20px;margin-bottom:16px}
h1{font-size:1.3rem;margin-top:0}
h2{font-size:1.1rem}
h3{font-size:1rem;margin-bottom:.2rem}
.offline-warning{padding:12px;border:2px solid #9a6700;background:#fff8c5;border-radius:6px;margin-bottom:16px;font-size:.9rem}
.hidden{display:none!important}
.inline-note{font-size:.9rem;color:#59636e}
label{display:block;margin:8px 0;font-weight:600}
input[type=text],textarea,select{width:100%;padding:8px;border:1px solid #d0d7de;border-radius:6px;font:inherit;font-weight:400}
textarea{min-height:120px;resize:vertical}
.choice-list{display:flex;flex-direction:column;gap:6px}
.choice{display:flex;gap:8px;align-items:flex-start;font-weight:400;border:1px solid #d0d7de;border-radius:6px;padding:8px;cursor:pointer}
.choice input{width:auto;margin-top:3px}
.scale-row{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0}
.scale-row label{display:flex;flex-direction:column;align-items:center;font-weight:400;border:1px solid #d0d7de;border-radius:6px;padding:6px 10px;cursor:pointer;gap:2px}
button{font:inherit;font-weight:600;padding:9px 16px;border:1px solid #1f883d;background:#1f883d;color:#fff;border-radius:6px;cursor:pointer}
button.secondary{background:#f6f8fa;color:#24292f;border-color:#d0d7de}
button:disabled{opacity:.5;cursor:not-allowed}
.actions{display:flex;gap:12px;flex-wrap:wrap;margin-top:16px}
.error{color:#cf222e;min-height:1.2em;font-weight:600}
.record-card{background:#f6f8fa;border:1px solid #d0d7de;border-radius:6px;padding:12px;margin:12px 0}
.requirements li{margin:4px 0}
.progress{color:#59636e;font-size:.85rem;margin-top:0}
.slider-track{display:flex;gap:0;margin:12px 0;flex-wrap:wrap}
.slider-stop{flex:1 1 0;min-width:80px;text-align:center;border:1px solid #d0d7de;padding:8px 4px;cursor:pointer;background:#fff}
.slider-stop.selected{outline:3px solid #0969da;font-weight:700;background:#ddf4ff}
.downloads{display:flex;gap:12px;flex-wrap:wrap;margin-top:12px}
.output-card{background:#eef6ff;border:1px solid #b6d7ff;border-radius:6px;padding:12px;margin:12px 0;white-space:pre-wrap;word-break:break-word}
.gen-count{font-size:.85rem;color:#59636e}
</style>
</head>
<body>
<header id="site-header"><strong>Study B — Semi-Live Local Collector (DRAFT, unsigned)</strong><span id="fiction-banner"></span></header>
<main id="app"><noscript>This file requires JavaScript enabled.</noscript></main>
<footer id="site-footer"><span>Anonymous academic study · fictional materials · local inference</span><button id="language-button" class="secondary" type="button">中文 / English</button></footer>
<script id="study-data" type="application/json">__DATA__</script>
<script>
'use strict';
const DATA=JSON.parse(document.querySelector('#study-data').textContent);
const app={
  locale:'zh-Hans',phase:'consent',submission_id:null,started:null,finished:null,
  consent_agreed:false,consent_agreed_at:null,
  model_id:null,params_hash:null,bridge_version:null,
  covariates:{},
  probe:{prompt_text:'',started_at_relative:null,committed_at_relative:null,char_count:0,edit_count:0},
  order:{seed:null,sequence:[]},
  taskIndex:0,condIndex:0,
  tasks:[],
  convenience:{tlx_effort:null,likert_effort:null,likert_discoverability:null,willingness_choice:null,willingness_reason:''},
  attention:{selected_id:null},
  _scratch:{}
};
const root=document.querySelector('#app');
const T=t=>t[app.locale];
const zh=()=>app.locale==='zh-Hans';
const now=()=>app.started?Math.max(0,Date.now()-new Date(app.started).getTime()):0;
const uuid=()=>(self.crypto&&crypto.randomUUID)?crypto.randomUUID():'10000000-1000-4000-8000-100000000000'.replace(/[018]/g,c=>(c^Math.random()*16>>c/4).toString(16));
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function mulberry32(a){return function(){a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return ((t^t>>>14)>>>0)/4294967296}}
function shell(body){document.documentElement.lang=app.locale;document.querySelector('#fiction-banner').textContent=T(DATA.honesty_notice);root.innerHTML=`<p class="offline-warning">${esc(T(DATA.honesty_notice))}</p>${body}`;window.scrollTo(0,0)}

// 调用本地桥接 /api/generate 取真实输出；失败抛错，调用方提示重试。
async function callGenerate(payload){
  const res=await fetch('/api/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  let data=null;
  try{data=await res.json()}catch(e){throw new Error('bad_response')}
  if(!res.ok||!data||typeof data.output_text!=='string'){throw new Error((data&&data.detail)||'generation_failed')}
  // 首次成功生成时锁定模型/参数元数据。
  app.model_id=app.model_id||data.model_id;
  app.params_hash=app.params_hash||data.params_hash;
  app.bridge_version=app.bridge_version||data.bridge_version;
  return data;
}

function renderConsent(){
  const c=DATA.consent_copy[app.locale];
  shell(`<section class="panel"><h1>${esc(c.heading)}</h1>
    <div class="consent">${c.body.map(x=>`<h3>${esc(x.title)}</h3><p>${esc(x.text)}</p>`).join('')}</div>
    <label class="choice"><input id="agree" type="checkbox"> <span>${esc(c.agree)}</span></label>
    <div class="actions"><button id="begin" disabled>${esc(c.start)}</button><button id="decline" class="secondary">${esc(c.decline)}</button></div></section>`);
  document.querySelector('#agree').onchange=e=>document.querySelector('#begin').disabled=!e.target.checked;
  document.querySelector('#begin').onclick=start;
  document.querySelector('#decline').onclick=()=>shell(`<section class="panel"><h1>${esc(c.declined)}</h1></section>`);
}

function start(){
  app.consent_agreed=true;
  app.submission_id=uuid();
  app.started=new Date().toISOString();
  app.consent_agreed_at=app.started;
  app.order.seed=Math.floor(Math.random()*1000000000);
  const rng=mulberry32(app.order.seed);
  const idx=DATA.tasks.map((_,i)=>i);
  for(let i=idx.length-1;i>0;i--){const j=Math.floor(rng()*(i+1));[idx[i],idx[j]]=[idx[j],idx[i]]}
  app.order.sequence=idx.map(i=>({task_id:DATA.tasks[i].task_id,condition_order:rng()<0.5?'slider_first':'prompt_first'}));
  app.tasks=app.order.sequence.map(s=>({
    task_id:s.task_id,condition_order:s.condition_order,
    slider:{final_stop_id:null,final_output_text:null,settings_explored:0,generations:[],started_at_relative:null,committed_at_relative:null},
    own_prompt:{prompt_text:'',char_count:0,edit_count:0,final_output_text:null,generations:[],started_at_relative:null,committed_at_relative:null}
  }));
  app.phase='covariates';renderCovariates();
}

function scaleRow(id,scale,current){
  let out='<div class="scale-row">';
  for(let v=scale.min;v<=scale.max;v++){out+=`<label class="scale-opt"><input type="radio" name="${id}" value="${v}"${current===v?' checked':''}><span>${v}</span></label>`}
  return out+'</div>';
}

function renderCovariates(){
  const rows=DATA.covariates.map(q=>{
    if(q.scale)return `<div class="q"><p><b>${esc(T(q.prompt))}</b></p>${scaleRow(q.id,q.scale,app.covariates[q.id])}</div>`;
    return `<div class="q"><p><b>${esc(T(q.prompt))}</b></p><div class="choice-list">${q.options.map(o=>`<label class="choice"><input type="radio" name="${q.id}" value="${esc(o.id)}"${app.covariates[q.id]===o.id?' checked':''}> <span>${esc(T(o.label))}</span></label>`).join('')}</div></div>`;
  }).join('');
  shell(`<section class="panel"><p class="progress">${zh()?'背景问卷（协变量）':'Background questionnaire (covariate)'}</p>
    <p class="inline-note">${zh()?'以下仅作协变量，不用于分组。':'For covariate use only; does not define any group.'}</p>
    ${rows}<p id="error" class="error"></p><div class="actions"><button id="next">${zh()?'继续':'Continue'}</button></div></section>`);
  document.querySelector('#next').onclick=()=>{
    for(const q of DATA.covariates){
      const sel=document.querySelector(`input[name="${q.id}"]:checked`);
      if(!sel){document.querySelector('#error').textContent=zh()?'请回答所有问题。':'Please answer every question.';return}
      app.covariates[q.id]=q.scale?Number(sel.value):sel.value;
    }
    app.phase='probe';renderProbe();
  };
}

function renderProbe(){
  const p=DATA.probe;
  shell(`<section class="panel"><p class="progress">${zh()?'Prompt 写作探针':'Prompt-writing probe'}</p>
    <h1>${zh()?'热身：写一条指令':'Warm-up: write one instruction'}</h1>
    <p>${esc(T(p.goal))}</p>
    <div class="record-card"><b>${zh()?'素材':'Material'}:</b><p>${esc(T(p.source_material))}</p></div>
    <label>${zh()?'你的指令（一条 prompt）':'Your instruction (one prompt)'}<textarea id="probe"></textarea></label>
    <p class="inline-note">${zh()?'此热身不评分、不显示输出。':'Warm-up is not scored and shows no output.'}</p>
    <p id="error" class="error"></p><div class="actions"><button id="next">${zh()?'提交并继续':'Submit and continue'}</button></div></section>`);
  const ta=document.querySelector('#probe');ta.value=app.probe.prompt_text;
  app.probe.started_at_relative=app.probe.started_at_relative??now();
  ta.oninput=()=>{app.probe.edit_count++;app.probe.prompt_text=ta.value};
  document.querySelector('#next').onclick=()=>{
    const text=ta.value.trim();
    if(!text){document.querySelector('#error').textContent=zh()?'请写一条指令。':'Please write one instruction.';return}
    app.probe.prompt_text=text;app.probe.char_count=text.length;app.probe.committed_at_relative=now();
    app.phase='tasks';app.taskIndex=0;app.condIndex=0;renderTaskStep();
  };
}

function taskDef(task_id){return DATA.tasks.find(t=>t.task_id===task_id)}

function renderTaskStep(){
  if(app.taskIndex>=app.tasks.length){app.phase='convenience';renderConvenience();return}
  const rec=app.tasks[app.taskIndex];
  const def=taskDef(rec.task_id);
  const order=rec.condition_order==='slider_first'?['slider','own_prompt']:['own_prompt','slider'];
  const cond=order[app.condIndex];
  const goalCard=`<h1>${esc(T(def.title))}</h1><p>${esc(T(def.goal))}</p>
    <div class="record-card"><b>${zh()?'需满足':'Requirements'}:</b><ul class="requirements">${def.requirements.map(r=>`<li>${esc(T(r))}</li>`).join('')}</ul></div>`;
  const progress=`<p class="progress">${zh()?'任务':'Task'} ${app.taskIndex+1}/${app.tasks.length} · ${zh()?'条件':'Condition'} ${app.condIndex+1}/2</p>`;
  if(cond==='slider'){renderSlider(rec,def,progress,goalCard)}else{renderOwnPrompt(rec,def,progress,goalCard)}
}

function renderSlider(rec,def,progress,goalCard){
  const s=def.slider;rec.slider.started_at_relative=rec.slider.started_at_relative??now();
  const stops=s.stops.map(st=>`<div class="slider-stop" data-id="${esc(st.id)}">${esc(T(st.label))}</div>`).join('');
  shell(`<section class="panel">${progress}${goalCard}
    <h2>${zh()?'方式：滑块条件':'Way: slider condition'}</h2>
    <p><b>${esc(T(s.label))}</b></p><p class="inline-note">${esc(T(s.help))}</p>
    <div class="slider-track" id="slider">${stops}</div>
    <div class="actions"><button id="gen" disabled>${zh()?'生成输出':'Generate output'}</button></div>
    <p class="gen-count" id="gencount"></p>
    <div id="output"></div>
    <p id="error" class="error"></p>
    <div class="actions"><button id="commit" disabled>${zh()?'满意，继续':'Looks good, continue'}</button></div></section>`);
  const explored=new Set();
  const genBtn=document.querySelector('#gen');const commitBtn=document.querySelector('#commit');
  const refreshCount=()=>{document.querySelector('#gencount').textContent=(zh()?'已生成次数：':'Generations: ')+rec.slider.generations.length};
  refreshCount();
  document.querySelectorAll('#slider .slider-stop').forEach(el=>el.onclick=()=>{
    document.querySelectorAll('#slider .slider-stop').forEach(x=>x.classList.remove('selected'));
    el.classList.add('selected');rec.slider._current=el.dataset.id;explored.add(el.dataset.id);rec.slider.settings_explored=explored.size;genBtn.disabled=false;
  });
  genBtn.onclick=async()=>{
    if(!rec.slider._current)return;
    genBtn.disabled=true;const label=genBtn.textContent;genBtn.textContent=zh()?'生成中…':'Generating…';
    document.querySelector('#error').textContent='';
    try{
      const data=await callGenerate({condition:'slider',task_id:rec.task_id,stop_id:rec.slider._current});
      rec.slider.generations.push({stop_id:rec.slider._current,output_text:data.output_text,at_relative:now()});
      rec.slider.final_stop_id=rec.slider._current;rec.slider.final_output_text=data.output_text;
      document.querySelector('#output').innerHTML=`<div class="output-card">${esc(data.output_text)}</div>`;
      commitBtn.disabled=false;refreshCount();
    }catch(e){document.querySelector('#error').textContent=zh()?'生成失败，请重试。':'Generation failed, please retry.'}
    finally{genBtn.textContent=label;genBtn.disabled=false}
  };
  commitBtn.onclick=()=>{
    if(rec.slider.generations.length===0){document.querySelector('#error').textContent=zh()?'请先生成一次输出。':'Please generate at least once.';return}
    rec.slider.committed_at_relative=now();advanceCondition();
  };
}

function renderOwnPrompt(rec,def,progress,goalCard){
  rec.own_prompt.started_at_relative=rec.own_prompt.started_at_relative??now();
  shell(`<section class="panel">${progress}${goalCard}
    <h2>${zh()?'方式：自己写 prompt 条件':'Way: own-prompt condition'}</h2>
    <label>${zh()?'写一条 prompt 达成上面的目标':'Write one prompt to achieve the goal above'}<textarea id="ownp"></textarea></label>
    <div class="actions"><button id="gen" disabled>${zh()?'生成输出':'Generate output'}</button></div>
    <p class="gen-count" id="gencount"></p>
    <div id="output"></div>
    <p id="error" class="error"></p>
    <div class="actions"><button id="commit" disabled>${zh()?'满意，继续':'Looks good, continue'}</button></div></section>`);
  const ta=document.querySelector('#ownp');ta.value=rec.own_prompt.prompt_text;
  const genBtn=document.querySelector('#gen');const commitBtn=document.querySelector('#commit');
  const refreshCount=()=>{document.querySelector('#gencount').textContent=(zh()?'已生成次数：':'Generations: ')+rec.own_prompt.generations.length};
  refreshCount();
  ta.oninput=()=>{rec.own_prompt.edit_count++;rec.own_prompt.prompt_text=ta.value;genBtn.disabled=ta.value.trim().length===0};
  genBtn.disabled=ta.value.trim().length===0;
  genBtn.onclick=async()=>{
    const text=ta.value.trim();if(!text)return;
    genBtn.disabled=true;const label=genBtn.textContent;genBtn.textContent=zh()?'生成中…':'Generating…';
    document.querySelector('#error').textContent='';
    try{
      const data=await callGenerate({condition:'own_prompt',task_id:rec.task_id,prompt_text:text});
      rec.own_prompt.generations.push({prompt_text:text,output_text:data.output_text,at_relative:now()});
      rec.own_prompt.prompt_text=text;rec.own_prompt.char_count=text.length;rec.own_prompt.final_output_text=data.output_text;
      document.querySelector('#output').innerHTML=`<div class="output-card">${esc(data.output_text)}</div>`;
      commitBtn.disabled=false;refreshCount();
    }catch(e){document.querySelector('#error').textContent=zh()?'生成失败，请重试。':'Generation failed, please retry.'}
    finally{genBtn.textContent=label;genBtn.disabled=ta.value.trim().length===0}
  };
  commitBtn.onclick=()=>{
    if(rec.own_prompt.generations.length===0){document.querySelector('#error').textContent=zh()?'请先生成一次输出。':'Please generate at least once.';return}
    const text=ta.value.trim();
    if(!text){document.querySelector('#error').textContent=zh()?'请写一条 prompt。':'Please write one prompt.';return}
    rec.own_prompt.prompt_text=text;rec.own_prompt.char_count=text.length;rec.own_prompt.committed_at_relative=now();advanceCondition();
  };
}

function advanceCondition(){
  if(app.condIndex===0){app.condIndex=1;renderTaskStep();return}
  app.condIndex=0;app.taskIndex++;renderTaskStep();
}

function renderConvenience(){
  const c=DATA.convenience;
  const tlx=c.tlx.map(q=>`<div class="q"><p><b>${esc(T(q.prompt))}</b></p>${scaleRow(q.id,q.scale,app.convenience[q.id])}</div>`).join('');
  const lik=c.likert.map(q=>`<div class="q"><p><b>${esc(T(q.prompt))}</b></p>${scaleRow(q.id,q.scale,app.convenience[q.id])}</div>`).join('');
  const w=c.willingness;
  shell(`<section class="panel"><p class="progress">${zh()?'主观评分（便利轴）':'Subjective ratings (convenience)'}</p>
    <h1>${zh()?'几道主观问题':'A few subjective questions'}</h1>
    ${tlx}${lik}
    <div class="q"><p><b>${esc(T(w.prompt))}</b></p><div class="choice-list">${w.options.map(o=>`<label class="choice"><input type="radio" name="willingness" value="${esc(o.id)}"> <span>${esc(T(o.label))}</span></label>`).join('')}</div></div>
    <label>${esc(T(w.reason_prompt))}<textarea id="reason"></textarea></label>
    <p id="error" class="error"></p><div class="actions"><button id="next">${zh()?'继续':'Continue'}</button></div></section>`);
  document.querySelector('#next').onclick=()=>{
    for(const q of c.tlx.concat(c.likert)){
      const sel=document.querySelector(`input[name="${q.id}"]:checked`);
      if(!sel){document.querySelector('#error').textContent=zh()?'请完成所有评分。':'Please complete all ratings.';return}
      app.convenience[q.id]=Number(sel.value);
    }
    const wsel=document.querySelector('input[name="willingness"]:checked');
    if(!wsel){document.querySelector('#error').textContent=zh()?'请选择你更愿意用的方式。':'Please choose which you would use.';return}
    app.convenience.willingness_choice=wsel.value;
    app.convenience.willingness_reason=document.querySelector('#reason').value.trim();
    app.phase='attention';renderAttention();
  };
}

function renderAttention(){
  const a=DATA.attention;
  shell(`<section class="panel"><p class="progress">${zh()?'注意力检查':'Attention check'}</p>
    <p>${esc(T(a.instruction))}</p>
    <div class="q"><p><b>${esc(T(a.prompt))}</b></p><div class="choice-list">${a.options.map(o=>`<label class="choice"><input type="radio" name="attention" value="${esc(o.id)}"> <span>${esc(T(o.label))}</span></label>`).join('')}</div></div>
    <p id="error" class="error"></p><div class="actions"><button id="next">${zh()?'完成':'Finish'}</button></div></section>`);
  document.querySelector('#next').onclick=()=>{
    const sel=document.querySelector('input[name="attention"]:checked');
    if(!sel){document.querySelector('#error').textContent=zh()?'请选择一个选项。':'Please select an option.';return}
    app.attention.selected_id=sel.value;
    app.finished=new Date().toISOString();
    app.phase='complete';renderComplete();
  };
}

function completionStatus(){
  const tasksDone=app.tasks.length>0&&app.tasks.every(t=>t.slider.committed_at_relative!=null&&t.own_prompt.committed_at_relative!=null);
  const done=app.consent_agreed&&app.probe.committed_at_relative!=null&&tasksDone&&app.convenience.willingness_choice!=null&&app.attention.selected_id!=null;
  return done?'complete':'partial';
}

function makeExport(){
  return {
    export_schema:DATA.export_schema,
    signed:false,
    submission_id:app.submission_id,
    honesty_notice:T(DATA.honesty_notice),
    instrument_version:DATA.instrument_version,
    bridge_version:app.bridge_version,
    model_id:app.model_id,
    params_hash:app.params_hash,
    selected_locale:app.locale,
    consent_agreed:app.consent_agreed,
    consent_agreed_at:app.consent_agreed_at,
    consent_copy_version:DATA.consent_copy_version,
    client_started_at:app.started,
    client_finished_at:app.finished,
    completion_status:completionStatus(),
    covariates:app.covariates,
    probe:{prompt_text:app.probe.prompt_text,started_at_relative:app.probe.started_at_relative,committed_at_relative:app.probe.committed_at_relative,char_count:app.probe.char_count,edit_count:app.probe.edit_count},
    task_order:app.order,
    tasks:app.tasks.map(t=>({
      task_id:t.task_id,condition_order:t.condition_order,
      slider:{
        final_stop_id:t.slider.final_stop_id,final_output_text:t.slider.final_output_text,
        settings_explored:t.slider.settings_explored,
        generations:t.slider.generations.map(g=>({stop_id:g.stop_id,output_text:g.output_text,at_relative:g.at_relative})),
        started_at_relative:t.slider.started_at_relative,committed_at_relative:t.slider.committed_at_relative
      },
      own_prompt:{
        prompt_text:t.own_prompt.prompt_text,char_count:t.own_prompt.char_count,edit_count:t.own_prompt.edit_count,
        final_output_text:t.own_prompt.final_output_text,
        generations:t.own_prompt.generations.map(g=>({prompt_text:g.prompt_text,output_text:g.output_text,at_relative:g.at_relative})),
        started_at_relative:t.own_prompt.started_at_relative,committed_at_relative:t.own_prompt.committed_at_relative
      }
    })),
    convenience:app.convenience,
    attention:app.attention
  };
}

function download(name,text,type){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([text],{type}));a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)}

function renderComplete(){
  shell(`<section class="panel"><h1>${zh()?'完成 —— 请回传':'Done — please return'}</h1>
    <p>${zh()?'感谢参与。请下载 JSON 并按 owner 指示诚实回传。文件未签名，页面不显示任何成绩或结果。':'Thank you. Download the JSON and return it honestly as instructed by the owner. Files are unsigned and no score or result is shown.'}</p>
    <p class="offline-warning">${esc(T(DATA.honesty_notice))}</p>
    <div class="downloads"><button id="json">${zh()?'下载 JSON':'Download JSON'}</button></div></section>`);
  const base=`studyB-live-${app.submission_id.slice(0,8)}`;
  document.querySelector('#json').onclick=()=>download(base+'.json',JSON.stringify(makeExport(),null,2)+'\n','application/json');
}

document.querySelector('#language-button').onclick=()=>{if(app.started)return;app.locale=app.locale==='zh-Hans'?'en':'zh-Hans';renderConsent()};
renderConsent();
</script>
</body>
</html>
'''


def build_html() -> str:
    """构建并返回采集器 HTML 字符串（桥接托管时直接调用；含禁用词自检）。"""
    payload = build_payload()
    data_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    data_json = data_json.replace("</", "<\\/")
    html = HTML_TEMPLATE.replace("__DATA__", data_json)
    lowered = html.lower()
    leaked = [term for term in FORBIDDEN_TERMS if term in lowered]
    if leaked:
        raise ValueError(f"generated HTML contains forbidden terms: {leaked}")
    return html


def generate(output: Path = DEFAULT_OUTPUT) -> Path:
    html = build_html()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8", newline="\n")
    reread = output.read_text(encoding="utf-8")
    if reread != html:
        raise ValueError("generated HTML read-back mismatch")
    display_path = output.relative_to(ROOT) if output.is_relative_to(ROOT) else output
    print(
        f"generated {display_path} ({len(html.encode('utf-8'))} bytes); "
        "forbidden-term self-check PASS"
    )
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    generate(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
