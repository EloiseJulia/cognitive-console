"""Typed fact registry, generator, and validator for the V11 stepwise study."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "button_board_stepwise_v11"
MATERIALS_PATH = DATA_DIR / "materials.json"
SEQUENCES_PATH = DATA_DIR / "sequences.json"
DERIVED_KEYS_PATH = DATA_DIR / "derived_keys.json"

SOURCE_SCHEMA_VERSION = "microstudy-button-board-stepwise-source-v1"
MATERIAL_SCHEMA_VERSION = "microstudy-button-board-stepwise-v11-bilingual"
MATERIALS_VERSION = "v11.1-stepwise-20260813-draft"
SEQUENCE_SCHEMA_VERSION = "microstudy-button-board-stepwise-sequences-v1"
EXPORT_SCHEMA_VERSION = "microstudy-export-v7-stepwise-bilingual-signed"
ANALYSIS_VERSION = "button-board-stepwise-gaa-v1"
LOCALES = ("en", "zh-Hans")
FORMAL_SLOTS = ("AB1", "F2", "F3", "F4", "F5", "F6")
FORMAL_SCENE_IDS = ("AB1-A", "AB1-B", "F2", "F3", "F4", "F5", "F6")
STATES = ("SUPPORTED", "DIAGNOSTIC", "WITHHELD", "UNRESOLVED")


def bi(en: str, zh: str) -> dict[str, str]:
    return {"en": en, "zh-Hans": zh}


def dim(
    dimension_id: str,
    label_en: str,
    label_zh: str,
    value_id: str,
    value_en: str,
    value_zh: str,
) -> dict[str, Any]:
    return {
        "id": dimension_id,
        "label": bi(label_en, label_zh),
        "value_id": value_id,
        "value": bi(value_en, value_zh),
    }


def alt(
    option_id: str,
    dimension_id: str | None = None,
    value_id: str | None = None,
    value_en: str | None = None,
    value_zh: str | None = None,
) -> dict[str, Any]:
    return {
        "id": option_id,
        "override": (
            {}
            if dimension_id is None
            else {
                dimension_id: {
                    "value_id": value_id,
                    "value": bi(str(value_en), str(value_zh)),
                }
            }
        ),
    }


def comparison(
    design: str,
    *,
    old_rounds: int | None,
    new_rounds: int | None,
    old_successes: int | None,
    new_successes: int | None,
    paired_rounds: int | None,
    alignment_dimensions: list[tuple[str, str, str]],
) -> dict[str, Any]:
    """Use one method-map schema for paired, single-method, and information cards."""
    return {
        "design": design,
        "paired_rounds": paired_rounds,
        "methods": {
            "existing": {
                "rounds": old_rounds,
                "denominator": old_rounds,
                "successes": old_successes,
            },
            "new": {
                "rounds": new_rounds,
                "denominator": new_rounds,
                "successes": new_successes,
            },
        },
        "alignment_dimensions": [
            {"id": row_id, "label": bi(en, zh)}
            for row_id, en, zh in alignment_dimensions
        ],
    }


DISCLAIMER = bi(
    "All products, buttons, and trial records are fictional examples and do not "
    "represent real product effects.",
    "所有产品、按钮和试用记录均为虚构示意，不代表真实产品功效。",
)

DESTINATIONS = [
    {
        "id": "dest-use",
        "state": "SUPPORTED",
        "label": bi("Use area", "常用区"),
        "description": bi(
            "It may be used only with an exact “Only when…” label.",
            "能用，但必须贴准确的“仅在……”标签。",
        ),
    },
    {
        "id": "dest-info",
        "state": "DIAGNOSTIC",
        "label": bi("Info card", "信息牌"),
        "description": bi(
            "Use it to view a condition, not as a button that changes the outcome.",
            "只用来看情况，不当成改变结果的按钮。",
        ),
    },
    {
        "id": "dest-off",
        "state": "WITHHELD",
        "label": bi("Leave it off", "不装"),
        "description": bi(
            "Do not place it on this button board.",
            "不放到这块按钮板上。",
        ),
    },
    {
        "id": "dest-check",
        "state": "UNRESOLVED",
        "label": bi("Check again", "再看看"),
        "description": bi(
            "Keep it pending until the record contains what is needed.",
            "记录还不够，先放待定盒。",
        ),
    },
]

STEP_OPTIONS = {
    1: [
        {"id": "INFO", "text": bi("Shows or reports the current condition", "只显示或告诉当前情况")},
        {"id": "CONTROL", "text": bi("Performs an action intended to change the outcome", "执行一个动作，目的是改变目标结果")},
    ],
    2: [
        {"id": "COMPARED", "text": bi("Both methods were tested as stated", "两种做法按记录比较过")},
        {"id": "NOT_COMPARED", "text": bi("No / the card does not show that", "没有／卡片看不出来")},
    ],
    3: [
        {"id": "BETTER", "text": bi("The new item met the goal more often", "新东西达到目标的次数更多")},
        {"id": "NOT_BETTER", "text": bi("The count was equal or lower", "次数一样或更少")},
    ],
    4: [
        {"id": "HARM", "text": bi("Yes, the stated other outcome was impaired", "是，卡片写出的另一件事受损")},
        {"id": "NO_HARM", "text": bi("No stated impairment occurred", "没有出现卡片写出的受损")},
    ],
    5: [
        {"id": "SCOPE_WRITTEN", "text": bi("Every required dimension has a value", "每个要求维度都有具体值")},
        {"id": "SCOPE_MISSING", "text": bi("At least one required value is unstated", "至少一个要求值未注明")},
    ],
}

QUESTIONS = {
    1: bi(
        "Does the new item show a condition, or perform an action intended to "
        "change the stated target outcome?",
        "这张卡里的新东西，是用来【看情况】，还是按下后会【执行一个动作，目的是改变上面的目标结果】？",
    ),
    2: bi(
        "Did the card test both methods for the stated number of rounds under "
        "the listed matched conditions?",
        "卡片有没有按上面写出的相同条件，让两种做法各做规定轮次？",
    ),
    3: bi(
        "Using only the defined goal and equal denominators, did the new item "
        "meet the goal more often, or equally/less often?",
        "只看定义的目标和相同分母：新东西达到目标的次数更多，还是一样／更少？",
    ),
    4: bi(
        "While using the new item, did another explicitly stated important "
        "outcome become impaired?",
        "使用新东西时，是否出现卡片明确写出的另一重要事情受损？",
    ),
    5: bi(
        "Does every required scope dimension have a concrete recorded value?",
        "卡片为这题规定的关键范围维度，是否每一项都有具体值？",
    ),
    6: bi(
        "Which “Only when…” label matches the card dimension by dimension? "
        "Every option is equally detailed; do not invent unstated conditions.",
        "哪条“仅在……”与卡片逐维一致？每项同样详细；卡片未写的内容不能自行补上。",
    ),
}

CHECKLIST = [
    bi(
        "Does it show a condition, or perform an action intended to change the target outcome?",
        "它只是显示情况，还是会执行动作来改变目标结果？",
    ),
    bi(
        "Were both methods compared under the stated matched conditions?",
        "有没有按卡片写出的相同条件比较两种做法？",
    ),
    bi(
        "With equal denominators, did the new method meet the goal more often?",
        "在相同分母中，新做法达到目标的次数更多吗？",
    ),
    bi(
        "Did it impair another explicitly stated important outcome?",
        "有没有损坏另一件卡片明确写出的重要事情？",
    ),
    bi(
        "Are all required scope dimensions stated?",
        "卡片要求的关键范围维度是否全部写出？",
    ),
    bi(
        "Does the “Only when…” label match every recorded dimension?",
        "“仅在……”是否与卡片逐维一致？",
    ),
]

COMMON = {
    "language_name": bi("English", "简体中文"),
    "title": bi("Stepwise fictional button board", "一步一问虚构按钮板"),
    "draft": bi(
        "DRAFT — owner-local preview only — not open for recruitment",
        "DRAFT — 仅供所有者本地预览 — 尚未开放招募",
    ),
    "welcome": {
        "heading": bi("Sort fictional trial cards one step at a time", "一步一步整理虚构试用卡"),
        "goal": bi(
            "Use an always-visible fictional trial card and answer one small "
            "question at a time to place each item where its evidence supports.",
            "看着始终显示的虚构试用卡，一次回答一个小问题，把新东西整理到证据支持的去处。",
        ),
        "steps": bi(
            "1 practice, 6 formal scenarios, and 1 read-the-instruction check.",
            "1 个练习、6 个正式场景、1 个阅读检查。",
        ),
        "open_book": bi(
            "You do not need to memorize rules. The card and reference panel stay visible.",
            "不用记规则，卡片和参考区会一直显示。",
        ),
        "card_only": bi(
            "Use only the page record; do not add everyday experience.",
            "只按卡片，不补充生活经验。",
        ),
        "privacy": bi(
            "Use an anonymous code. There is no free text and submitted answers cannot be recovered.",
            "使用匿名代码，不收自由文本，提交后不能恢复作答。",
        ),
        "participant_label": bi("Anonymous code", "匿名代码"),
        "participant_help": bi(
            "Use 1–64 letters, numbers, dots, underscores, or hyphens.",
            "请输入 1–64 个字母、数字、点、下划线或连字符。",
        ),
        "start": bi("Start", "开始"),
    },
    "tutorial": {
        "heading": bi("One idea and the stepwise controls", "一条直觉和一步一问操作"),
        "intuition": bi(
            "A button responding does not mean it meets the stated goal more "
            "often than the existing method.",
            "按钮会动或有反应，不等于它比原来的做法更常达到明确目标。",
        ),
        "operation": bi(
            "Read the card, choose one answer, and the next applicable question "
            "will appear. A branch may end early. You can go back and change "
            "any answered step before continuing to the next scenario.",
            "读记录后选择一个答案，页面只显示下一个适用问题；有些分支会提前结束。"
            "进入下一题前，你可以返回并修改任意已答步骤。",
        ),
        "show_practice": bi("Open the practice card", "打开练习卡"),
    },
    "formal_intro": {
        "heading": bi("Formal scenarios", "正式场景"),
        "guard": bi(
            "Use only the record shown. Do not add information from the item "
            "name, everyday knowledge, or personal preference.",
            "请只读页面上的记录。不要根据产品名称、生活常识或个人偏好补充信息。",
        ),
        "feedback": bi(
            "Formal trials do not show correctness. Any of the four destinations may apply.",
            "正式题不会告诉你答得对不对，四个去处都可能正确。",
        ),
        "begin": bi("Begin formal scenarios", "开始正式场景"),
    },
    "labels": {
        "situation": bi("Situation", "情境"),
        "goal": bi("Target", "目标"),
        "existing": bi("What you originally did", "你原来怎么做"),
        "new_item": bi("New function", "新功能"),
        "record": bi("Trial record", "试用记录"),
        "reference_destinations": bi("Four destinations", "四个去处"),
        "reference_checklist": bi("How to think", "怎么想"),
        "path": bi("Your reasoning path", "你的推理路径"),
        "answered_steps": bi("Answered steps", "已答步骤"),
        "result": bi("Based on your answers, place it in:", "根据你的回答放进："),
    },
    "actions": {
        "submit": bi("Choose and continue", "选择并继续"),
        "continue": bi("Continue", "继续"),
        "back": bi("Previous step", "上一步"),
        "change_step": bi("Change step {step}: {answer}", "修改第 {step} 步：{answer}"),
        "choice_required": bi("Choose one answer before continuing.", "继续前请选择一项。"),
    },
    "progress": {
        "practice": bi("Practice", "练习"),
        "formal": bi("Formal scenario {current} of 6", "正式场景 {current}/6"),
        "attention": bi("Read-the-instruction check", "阅读检查"),
        "reflection": bi("Optional reflection", "可选反思"),
    },
    "attention": {
        "heading": bi("Read-the-instruction check", "阅读检查"),
        "instruction": bi(
            "This item only checks whether you read the instruction. For the "
            "first question, select “Shows or reports the current condition.”",
            "这题只检查你有没有读到说明。第一个问题请选择“只显示或告诉当前情况”。",
        ),
    },
    "reflection": {
        "heading": bi("Optional structured reflection", "可选结构化反思"),
        "hardest": bi("Which step was hardest to read?", "哪一步最难读准？"),
        "confusing": bi("Which destinations were easiest to confuse?", "哪两个去处最易混淆？"),
        "amount": bi("How was the amount of page text?", "页面文字如何？"),
        "pace": bi("How was the one-question-at-a-time pace?", "一次一问的速度如何？"),
        "submit": bi("Finish", "完成"),
    },
    "export": {
        "heading": bi("Activity complete", "活动结束"),
        "debrief": bi(
            "You did not test real products. This activity records how you apply "
            "evidence thresholds to fictional cards; it does not measure real-world benefit.",
            "你没有测试真实产品。本活动只记录你如何按虚构证据门槛整理卡片，不测量产品是否改善生活。",
        ),
        "download_json": bi("Download signed JSON", "下载签名 JSON"),
        "download_csv": bi("Download signed CSV", "下载签名 CSV"),
        "finish": bi("Clear this page", "清除此页面"),
        "manual": bi("Downloads are manual. No score is shown.", "下载需手动操作，页面不显示成绩。"),
    },
    "save_exit": {
        "button": bi("End and prepare partial export", "结束并准备部分导出"),
        "heading": bi("End this local activity?", "结束本地活动？"),
        "body": bi(
            "The session cannot resume. Submitted choices will be frozen in a "
            "signed partial export; nothing downloads automatically.",
            "本次活动不能继续。已提交选择会冻结在签名部分导出中；页面不会自动下载。",
        ),
        "cancel": bi("Cancel", "取消"),
        "confirm": bi("Prepare partial export", "准备部分导出"),
    },
    "errors": {
        "generic": bi("The local request failed. Please try again.", "本地请求失败，请重试。"),
        "download": bi("Download failed. Both buttons remain available.", "下载失败，两个按钮仍可使用。"),
        "desktop": bi(
            "Desktop preview required below 1024 CSS pixels.",
            "宽度低于 1024 CSS 像素时需要桌面预览。",
        ),
    },
}


def scene(
    scene_id: str,
    *,
    title: dict[str, str],
    situation: dict[str, str],
    goal: dict[str, str],
    existing: dict[str, str],
    new_item: dict[str, str],
    nature: str,
    action_fact: dict[str, str],
    comparison_rule: dict[str, Any],
    harm_checks: list[dict[str, Any]],
    scope_dimensions: list[dict[str, Any]],
    scope_options: list[dict[str, Any]],
    observation: dict[str, Any] | None = None,
    comparison_fact: dict[str, str] | None = None,
    extra_facts: list[dict[str, Any]] | None = None,
    feedback: dict[str, str] | None = None,
    variant_id: str | None = None,
) -> dict[str, Any]:
    return {
        "scene_id": scene_id,
        "variant_id": variant_id,
        "title": title,
        "situation": situation,
        "goal": goal,
        "existing": existing,
        "new_item": new_item,
        "nature": nature,
        "action_fact": action_fact,
        "comparison_rule": comparison_rule,
        "harm_checks": harm_checks,
        "scope_dimensions": scope_dimensions,
        "scope_options": scope_options,
        "observation": observation,
        "comparison_fact": comparison_fact,
        "extra_facts": extra_facts or [],
        "feedback": feedback,
    }


PRACTICE = scene(
    "P1",
    title=bi("Sock-finding drawer button", "抽屉找袜按钮"),
    situation=bi(
        "Retrieve a pair of socks in a specified color from a divided drawer.",
        "从分格抽屉中取出指定颜色的一双袜子。",
    ),
    goal=bi(
        "“Correct within 20 seconds” means both socks match the specified color.",
        "“20 秒内取对”指两只袜子都与指定颜色相同。",
    ),
    existing=bi(
        "Read the front color labels, then search one compartment at a time.",
        "看抽屉前的颜色标签，再逐格寻找。",
    ),
    new_item=bi(
        "Pressing the matching color button moves one possible compartment to the front.",
        "按下对应颜色的按钮后，一个可能的分格会被推到抽屉前面。",
    ),
    nature="control",
    action_fact=bi(
        "The new button moved one compartment to the front in 10/10 rounds.",
        "新按钮在 10/10 轮中都把一个分格推到抽屉前面。",
    ),
    comparison_rule=comparison(
        "paired_same_conditions",
        old_rounds=10,
        new_rounds=10,
        old_successes=8,
        new_successes=6,
        paired_rounds=10,
        alignment_dimensions=[
            ("drawer_contents", "drawer contents", "抽屉内容"),
            ("sock_placement", "sock placement", "袜子摆放"),
            ("target_color", "target color", "指定颜色"),
            ("time_limit", "20-second limit", "20 秒限制"),
        ],
    ),
    comparison_fact=bi(
        "The 10 paired rounds used the same drawer contents, sock placement, "
        "target color, and 20-second limit; method order or side alternated.",
        "共 10 个配对轮；每轮的抽屉内容、袜子摆放、指定颜色和 20 秒限制相同，"
        "做法顺序或左右位置轮换。",
    ),
    harm_checks=[
        {
            "id": "caught_sock",
            "label": bi("sock caught by a compartment edge", "袜子被分格边缘卡住"),
            "count": 0,
            "fact": bi(
                "A sock was caught by a compartment edge in {count}/{denominator} rounds",
                "袜子被分格边缘卡住 {count}/{denominator}",
            ),
        },
        {
            "id": "pushed_out",
            "label": bi("sock left the drawer", "袜子被推出抽屉"),
            "count": 0,
            "fact": bi(
                "A sock left the drawer in {count}/{denominator} rounds",
                "袜子被推出抽屉 {count}/{denominator}",
            ),
        },
    ],
    scope_dimensions=[
        dim("drawer", "drawer", "抽屉", "trial_drawer", "this trial drawer", "此次抽屉"),
        dim("labels", "labels", "标签", "current_six", "current six color labels", "当前 6 个颜色标签"),
        dim("operator", "operator", "操作者", "self", "self only", "仅限本人"),
    ],
    scope_options=[
        alt("p1-s-q7"),
        alt("p1-s-k2", "drawer", "home_drawer", "the home drawer", "家中抽屉"),
        alt("p1-s-m8", "labels", "any_six", "any six color labels", "任意 6 个颜色标签"),
    ],
    feedback=bi(
        "The new button acted in all ten rounds, but the target occurred in "
        "6/10 rounds, compared with 8/10 for the original method. This feedback "
        "applies only to this practice record.",
        "新按钮十次都执行了动作，但“20 秒内取对”为 6/10，原办法为 8/10。"
        "本反馈只针对这条练习记录。",
    ),
)


def ab_scene(scene_id: str, variant_id: str, old_successes: int, new_successes: int) -> dict[str, Any]:
    return scene(
        scene_id,
        variant_id=variant_id,
        title=bi("Receipt-folder page-finder button", "票据文件夹找页按钮"),
        situation=bi(
            "Retrieve a receipt with an exact number from a household receipt folder.",
            "从一本家庭票据文件夹中找出指定编号的票据。",
        ),
        goal=bi(
            "“Found within 30 seconds” means retrieving the receipt with the exact number.",
            "“30 秒内找到”指取出编号完全相同的票据。",
        ),
        existing=bi(
            "Read the month dividers, then turn the pages one at a time.",
            "先看月份分隔页，再逐页翻找。",
        ),
        new_item=bi(
            "Entering the receipt number makes the edge of one possible page extend by 2 cm.",
            "输入票据编号后，一个可能的页面边缘会伸出 2 厘米。",
        ),
        nature="control",
        action_fact=bi(
            "The new button extended one possible page edge in 10/10 rounds.",
            "新按钮在 10/10 轮中都让一个可能的页面边缘伸出。",
        ),
        comparison_rule=comparison(
            "paired_same_conditions",
            old_rounds=10,
            new_rounds=10,
            old_successes=old_successes,
            new_successes=new_successes,
            paired_rounds=10,
            alignment_dimensions=[
                ("receipt_contents", "receipt contents", "票据内容"),
                ("page_order", "page order", "页面顺序"),
                ("target_receipt", "target receipt", "目标票据"),
                ("desk_lamp", "desk lamp", "桌面灯"),
                ("time_limit", "30-second limit", "30 秒限制"),
            ],
        ),
        comparison_fact=bi(
            "The 10 paired rounds used the same receipt contents, page order, "
            "target receipt, desk lamp, and 30-second limit; method order or side alternated.",
            "共 10 个配对轮；每轮的票据内容、页面顺序、目标票据、桌面灯和 30 秒限制相同，"
            "做法顺序或左右位置轮换。",
        ),
        harm_checks=[
            {
                "id": "tear", "label": bi("receipt torn", "票据撕裂"), "count": 0,
                "fact": bi("Receipt torn: {count}/{denominator}", "票据撕裂 {count}/{denominator}"),
            },
            {
                "id": "divider", "label": bi("month divider covered", "月份分隔页被遮住"), "count": 0,
                "fact": bi(
                    "month divider covered: {count}/{denominator}",
                    "月份分隔页被遮住 {count}/{denominator}",
                ),
            },
            {
                "id": "drop", "label": bi("receipt fell out", "票据掉出"), "count": 0,
                "fact": bi("receipt fell out: {count}/{denominator}", "票据掉出 {count}/{denominator}"),
            },
        ],
        scope_dimensions=[
            dim("folder", "folder", "文件夹", "tested_folder", "this tested folder", "此次文件夹"),
            dim("receipts", "receipts", "票据", "past_30_days", "past 30 days", "近 30 天"),
            dim("light", "light", "照明", "desk_lamp_on", "desk lamp on", "桌灯开启"),
            dim("operator", "operator", "操作者", "self", "self only", "仅限本人"),
        ],
        scope_options=[
            alt("ab1-s-m4"),
            alt("ab1-s-r9", "folder", "home_folder", "the home folder", "家中文件夹"),
            alt("ab1-s-k2", "receipts", "past_90_days", "past 90 days", "近 90 天"),
        ],
    )


AB1_A = ab_scene("AB1-A", "A", 5, 8)
AB1_B = ab_scene("AB1-B", "B", 8, 7)

F2 = scene(
    "F2",
    title=bi("Pot-soil dry/wet display", "花盆土壤干湿显示屏"),
    situation=bi(
        "View whether the topsoil in a windowsill pot is currently dry or wet.",
        "查看窗台花盆的表层土壤当前偏干还是偏湿。",
    ),
    goal=bi(
        "Use the words on an independent moisture strip at the fixed marked position as the reference.",
        "以固定标记位置的独立湿度条文字作为当前状态的参照。",
    ),
    existing=bi(
        "Insert the independent strip at the marked position and read its words.",
        "把独立湿度条插到标记位置并读取文字。",
    ),
    new_item=bi(
        "The display shows “dry” or “wet.” Its back has only a mounting bracket "
        "and display, with no connection to a pump, drain valve, or fan.",
        "显示屏会显示“偏干”或“偏湿”；背面只有固定支架和显示屏，没有连接水泵、排水阀或风扇。",
    ),
    nature="info",
    action_fact=bi(
        "The display showed text on all 14 checks and had no connection to an actuator.",
        "显示屏在 14 次查看中都显示了文字，且没有连接任何执行装置。",
    ),
    comparison_rule=comparison(
        "not_applicable_information_item",
        old_rounds=None,
        new_rounds=None,
        old_successes=None,
        new_successes=None,
        paired_rounds=None,
        alignment_dimensions=[],
    ),
    observation={"checks": 14, "matches": 12, "days": 7},
    harm_checks=[
        {
            "id": "drain", "label": bi("drainage hole covered", "遮挡排水孔"), "count": 0,
            "fact": bi(
                "Drainage hole covered: {count}/{denominator}",
                "遮挡排水孔 {count}/{denominator}",
            ),
        },
        {
            "id": "leaf", "label": bi("leaf touched", "碰到叶片"), "count": 0,
            "fact": bi("leaf touched: {count}/{denominator}", "碰到叶片 {count}/{denominator}"),
        },
    ],
    scope_dimensions=[
        dim("pot", "pot", "花盆", "trial_pot", "trial pot", "此次花盆"),
        dim("location", "location", "位置", "this_sill", "this sill", "这个窗台"),
        dim("soil", "soil", "盆土", "same_soil", "same soil", "同种盆土"),
    ],
    scope_options=[
        alt("f2-s-v6"),
        alt("f2-s-a3", "pot", "home_pot", "home pot", "家中花盆"),
        alt("f2-s-n8", "location", "any_sill", "any sill", "任一窗台"),
    ],
)

F3 = scene(
    "F3",
    title=bi("Three-app notification button for reading", "阅读时关闭三个应用通知的按钮"),
    situation=bi("Read continuously on a phone for 20 minutes at night.", "晚上在手机上连续阅读 20 分钟。"),
    goal=bi(
        "No pop-up from the three specified ordinary apps appears during the 20 minutes.",
        "20 分钟内，屏幕不出现三个指定普通应用的弹窗。",
    ),
    existing=bi(
        "Turn off notifications for the three apps one by one before reading.",
        "阅读前逐个关闭这三个应用的通知。",
    ),
    new_item=bi(
        "Pressing the button once changes the notification settings for all three apps.",
        "按一次按钮，会同时修改这三个应用的通知设置。",
    ),
    nature="control",
    action_fact=bi(
        "The new button wrote all three app settings in 10/10 rounds.",
        "新按钮在 10/10 轮中都写入了三个应用的设置。",
    ),
    comparison_rule=comparison(
        "paired_same_conditions",
        old_rounds=10,
        new_rounds=10,
        old_successes=6,
        new_successes=9,
        paired_rounds=10,
        alignment_dimensions=[
            ("article", "saved article", "保存文章"),
            ("settings", "initial app settings", "应用初始设置"),
            ("wifi", "Wi-Fi", "Wi‑Fi"),
            ("time_limit", "20-minute limit", "20 分钟时限"),
            ("call_minute", "scheduled-call minute", "测试来电分钟点"),
        ],
    ),
    comparison_fact=bi(
        "The 10 paired rounds used the same saved article, initial app settings, "
        "Wi-Fi, 20-minute limit, and scheduled-call minute; method order or side alternated.",
        "共 10 个配对轮；每轮的保存文章、应用初始设置、Wi‑Fi、20 分钟时限和测试来电分钟点相同，"
        "做法顺序或左右位置轮换。",
    ),
    harm_checks=[
        {
            "id": "priority_call",
            "label": bi(
                "test-contact call produced neither ring nor screen indicator",
                "测试联系人来电既无铃声也无屏幕提示",
            ),
            "count": 3,
            "fact": bi(
                "The call from the test contact specified in this record produced "
                "neither a ring nor a screen indicator in {count}/{denominator} rounds",
                "这条记录指定的测试联系人来电，在 {count}/{denominator} 轮中既没有铃声，也没有屏幕提示",
            ),
        },
    ],
    scope_dimensions=[
        dim("device", "device", "设备", "own_phone", "own phone", "本人手机"),
        dim("application", "application", "应用", "current_app", "current app", "当前应用"),
        dim("network", "network", "网络", "home_wifi", "home Wi-Fi", "家中 Wi‑Fi"),
        dim("time", "time", "时间", "21_23", "21 to 23", "21–23 时"),
    ],
    scope_options=[
        alt("f3-s-p5"),
        alt("f3-s-c2", "device", "any_phone", "any phone", "任意手机"),
        alt("f3-s-t8", "time", "19_23", "19 to 23", "19–23 时"),
    ],
    extra_facts=[
        {
            "id": "priority_definition",
            "text": bi(
                "Before the trial, this record stated that the test contact’s "
                "scheduled call had to produce a ring or screen indicator.",
                "试用前，这条记录已说明：该测试联系人按安排打来时，必须出现铃声或屏幕提示。",
            ),
        }
    ],
)

F4 = scene(
    "F4",
    title=bi("Targeted insole airflow button", "鞋垫定点送风按钮"),
    situation=bi(
        "Treat a wet marked region of an insole after rain.",
        "雨后处理鞋内一块标记区域的潮湿鞋垫。",
    ),
    goal=bi(
        "After 30 minutes, a new white tissue pressed on the marked region for "
        "five seconds has no visible water mark.",
        "30 分钟后，用新白纸巾按压标记区域 5 秒，纸巾上没有可见水印。",
    ),
    existing=bi(
        "Remove the insole and place it in front of a table fan for 30 minutes.",
        "取出鞋垫，在桌面风扇前吹 30 分钟。",
    ),
    new_item=bi(
        "Pressing the button sends air to the marked region for 30 minutes.",
        "按下按钮后，向标记区域送风 30 分钟。",
    ),
    nature="control",
    action_fact=bi(
        "The new button sent air for 30 minutes in 10/10 rounds.",
        "新按钮在 10/10 轮中都送风 30 分钟。",
    ),
    comparison_rule=comparison(
        "single_method_record",
        old_rounds=0,
        new_rounds=10,
        old_successes=None,
        new_successes=8,
        paired_rounds=0,
        alignment_dimensions=[],
    ),
    harm_checks=[
        {
            "id": "scorch", "label": bi("scorch mark", "焦痕"), "count": 0,
            "fact": bi("Scorch mark: {count}/{denominator}", "焦痕 {count}/{denominator}"),
        },
        {
            "id": "shape", "label": bi("deformation", "变形"), "count": 0,
            "fact": bi("deformation: {count}/{denominator}", "变形 {count}/{denominator}"),
        },
        {
            "id": "fade", "label": bi("upper color loss", "鞋面褪色"), "count": 0,
            "fact": bi("upper color loss: {count}/{denominator}", "鞋面褪色 {count}/{denominator}"),
        },
    ],
    scope_dimensions=[
        dim("shoes", "shoes", "鞋", "tested_pair", "this pair", "这双鞋"),
        dim("insole", "insole", "鞋垫", "tested_insole", "this insole", "这块鞋垫"),
        dim("region", "region", "区域", "marked_region", "this marked region", "这个标记区域"),
    ],
    scope_options=[
        alt("f4-s-h7"),
        alt("f4-s-b3", "shoes", "any_pair", "any pair", "任一双鞋"),
        alt("f4-s-z6", "region", "any_region", "any marked region", "任意标记区域"),
    ],
    extra_facts=[
        {
            "id": "image_source",
            "text": bi(
                "Both process photographs also came from new-button rounds, at minute 0 and minute 30.",
                "两张过程照片也都来自新按钮轮次，分别拍摄于第 0 分钟和第 30 分钟。",
            ),
        }
    ],
)

F5 = scene(
    "F5",
    title=bi("Clothing static-treatment button", "衣物静电处理按钮"),
    situation=bi("Reduce clothing contact with the arm before dressing.", "穿衣前减少衣物贴在手臂上的静电。"),
    goal=bi(
        "One minute after dressing, a flat paper card can pass between the sleeve and bare arm.",
        "穿上后 1 分钟，一张平直纸片能从袖子与裸露手臂之间穿过。",
    ),
    existing=bi("Wipe the inside of the garment once with a damp cotton cloth.", "用微湿棉布在衣物内侧擦一次。"),
    new_item=bi(
        "After the device is attached to the garment, pressing its button releases "
        "one pulse at the attachment position.",
        "把装置固定在衣物上后，按下按钮会在固定位置释放一次脉冲。",
    ),
    nature="control",
    action_fact=bi(
        "The new button released one pulse in 12/12 rounds.",
        "新按钮在 12/12 轮中都释放了一次脉冲。",
    ),
    comparison_rule=comparison(
        "paired_same_conditions",
        old_rounds=12,
        new_rounds=12,
        old_successes=7,
        new_successes=10,
        paired_rounds=12,
        alignment_dimensions=[
            ("material", "material", "材质"),
            ("garment", "garment type", "衣物类型"),
            ("pretreatment", "pretreatment", "预处理"),
            ("placement", "placement", "摆放"),
            ("wearing", "wearing method", "穿着方式"),
            ("timing", "test timing", "测试时间"),
        ],
    ),
    comparison_fact=bi(
        "The 12 paired rounds matched material, garment type, pretreatment, "
        "placement, wearing method, and test timing within each pair; method order or side alternated.",
        "共 12 个配对轮；每轮的材质、衣物类型、预处理、摆放、穿着方式和测试时间相互匹配，"
        "做法顺序或左右位置轮换。",
    ),
    harm_checks=[
        {
            "id": "water", "label": bi("water mark", "水痕"), "count": 0,
            "fact": bi("Water mark: {count}/{denominator}", "水痕 {count}/{denominator}"),
        },
        {
            "id": "thread", "label": bi("pulled thread", "拉线"), "count": 0,
            "fact": bi("pulled thread: {count}/{denominator}", "拉线 {count}/{denominator}"),
        },
        {
            "id": "skin", "label": bi("skin red mark", "皮肤红印"), "count": 0,
            "fact": bi("skin red mark: {count}/{denominator}", "皮肤红印 {count}/{denominator}"),
        },
    ],
    scope_dimensions=[
        dim("place", "place", "地点", "home", "at home", "仅在家中"),
        dim("material", "material", "材质", "missing", "not stated", "未注明"),
        dim("garment_type", "type", "类型", "missing", "not stated", "未注明"),
        dim("humidity", "humidity", "湿度", "missing", "not stated", "未注明"),
        dim("clip", "button attachment position", "固定位置", "missing", "not stated", "未注明"),
    ],
    scope_options=[
        alt("f5-s-u4"),
        alt("f5-s-c8", "material", "cotton_item", "cotton garment", "棉质衣物"),
        alt("f5-s-l2", "garment_type", "long_sleeve", "long-sleeve garment", "长袖衣物"),
    ],
)

F6 = scene(
    "F6",
    title=bi("Bathroom-mirror airflow button", "浴室镜面送风按钮"),
    situation=bi(
        "View the marked central region of a bathroom mirror after washing.",
        "洗漱后看清浴室镜面中央的标记区域。",
    ),
    goal=bi(
        "Within 60 seconds, read all four 12 mm characters from one metre away, "
        "and still read all four at minute 5.",
        "启动后 60 秒内，从 1 米外读出标记区域后的四个 12 mm 字符，并在第 5 分钟仍能全部读出。",
    ),
    existing=bi("Wipe the marked region once with a dry microfibre cloth.", "用干燥超细纤维布擦一次标记区域。"),
    new_item=bi(
        "Pressing the button sends air to the marked region for five minutes.",
        "按下按钮后，向标记区域送风 5 分钟。",
    ),
    nature="control",
    action_fact=bi(
        "The new button sent air for five minutes in 14/14 rounds.",
        "新按钮在 14/14 轮中都送风 5 分钟。",
    ),
    comparison_rule=comparison(
        "paired_same_conditions",
        old_rounds=14,
        new_rounds=14,
        old_successes=8,
        new_successes=13,
        paired_rounds=14,
        alignment_dimensions=[
            ("mirror", "mirror", "镜面"),
            ("region", "central 20×20 cm region", "中央 20×20 cm 区域"),
            ("characters", "characters", "字符"),
            ("water", "38–40°C water", "38–40°C 用水"),
            ("fog", "initial fogging procedure", "起始雾化步骤"),
            ("fan", "exhaust-fan-off state", "排风扇关闭状态"),
            ("times", "observation times", "计时点"),
        ],
    ),
    comparison_fact=bi(
        "The 14 paired rounds used the same mirror, central 20×20 cm region, "
        "characters, 38–40°C water, initial fogging procedure, exhaust-fan-off "
        "state, and observation times; method order or side alternated.",
        "共 14 个配对轮；每轮的镜面、中央 20×20 cm 区域、字符、38–40°C 用水、"
        "起始雾化步骤、排风扇关闭状态和计时点相同，做法顺序或左右位置轮换。",
    ),
    harm_checks=[
        {
            "id": "water_mark", "label": bi("water mark", "水痕"), "count": 0,
            "fact": bi("Water mark: {count}/{denominator}", "水痕 {count}/{denominator}"),
        },
        {
            "id": "frame", "label": bi("mirror frame moved", "镜框移动"), "count": 0,
            "fact": bi("mirror frame moved: {count}/{denominator}", "镜框移动 {count}/{denominator}"),
        },
        {
            "id": "cover", "label": bi("characters covered", "字符被遮住"), "count": 0,
            "fact": bi("characters covered: {count}/{denominator}", "字符被遮住 {count}/{denominator}"),
        },
    ],
    scope_dimensions=[
        dim("mirror", "mirror", "镜面", "tested_mirror", "this mirror", "此次镜面"),
        dim("region", "region", "区域", "central_20", "central 20×20 cm", "中央 20×20 cm"),
        dim("water", "water temperature", "水温", "38_40", "38–40°C", "38–40°C"),
        dim("fan", "exhaust fan", "排风扇", "off", "off", "关闭"),
    ],
    scope_options=[
        alt("f6-s-r6"),
        alt("f6-s-m1", "mirror", "any_mirror", "any mirror", "任意镜面"),
        alt("f6-s-t9", "water", "35_40", "35–40°C", "35–40°C"),
    ],
)

FORMAL_SCENES = [AB1_A, AB1_B, F2, F3, F4, F5, F6]

REFLECTION_OPTIONS = {
    "hardest": [
        (f"step-{index}", bi(f"Step {index}", f"第 {index} 步"))
        for index in range(1, 7)
    ] + [("skip", bi("Prefer not to answer", "不回答"))],
    "confusing": [
        ("use-info", bi("Use area and Info card", "常用区和信息牌")),
        ("use-check", bi("Use area and Check again", "常用区和再看看")),
        ("off-check", bi("Leave it off and Check again", "不装和再看看")),
        ("info-check", bi("Info card and Check again", "信息牌和再看看")),
        ("skip", bi("Prefer not to answer", "不回答")),
    ],
    "amount": [
        ("too-little", bi("Too little", "太少")),
        ("about-right", bi("About right", "正好")),
        ("too-much", bi("Too much", "太多")),
        ("skip", bi("Prefer not to answer", "不回答")),
    ],
    "pace": [
        ("too-slow", bi("Too slow", "太慢")),
        ("about-right", bi("About right", "正好")),
        ("too-fast", bi("Too fast", "太快")),
        ("skip", bi("Prefer not to answer", "不回答")),
    ],
}


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _scope_vectors(scene_row: dict[str, Any]) -> list[dict[str, Any]]:
    base = {
        row["id"]: {"value_id": row["value_id"], "value": copy.deepcopy(row["value"])}
        for row in scene_row["scope_dimensions"]
    }
    options = []
    for definition in scene_row["scope_options"]:
        vector = copy.deepcopy(base)
        for dimension_id, replacement in definition["override"].items():
            if dimension_id not in vector:
                raise ValueError(f"unknown scope dimension in {scene_row['scene_id']}")
            vector[dimension_id] = copy.deepcopy(replacement)
        options.append({"id": definition["id"], "vector": vector})
    return options


def derive_structured_fields(scene_row: dict[str, Any]) -> dict[str, Any]:
    if any(
        key in scene_row
        for key in (
            "expected_answer_by_step",
            "expected_exit_answer",
            "expected_decisive_step",
            "expected_state",
            "strict_correct",
            "gaa_correct",
            "compared",
            "better",
            "harm",
            "scope_written",
            "scope_correct",
        )
    ):
        raise ValueError("derived fields must not be hand-entered")
    rule = scene_row["comparison_rule"]
    old = rule["methods"]["existing"]
    new = rule["methods"]["new"]
    nature = scene_row["nature"]
    if nature == "info":
        compared = None
        better = None
    else:
        compared = bool(
            rule["design"] == "paired_same_conditions"
            and old["denominator"]
            and new["denominator"]
        )
        better = (
            new["successes"] > old["successes"]
            if compared
            else None
        )
    harm = any(row["count"] > 0 for row in scene_row["harm_checks"])
    scope_written = all(
        row["value_id"] != "missing" for row in scene_row["scope_dimensions"]
    )
    required = {
        row["id"]: row["value_id"] for row in scene_row["scope_dimensions"]
    }
    matching = [
        row["id"]
        for row in _scope_vectors(scene_row)
        if {key: value["value_id"] for key, value in row["vector"].items()}
        == required
    ]
    if len(matching) != 1:
        raise ValueError(f"scope option must have one faithful vector: {scene_row['scene_id']}")
    return {
        "nature": nature,
        "compared": compared,
        "better": better,
        "harm": harm,
        "scope_written": scope_written,
        "scope_correct": matching[0],
        "comparison_rule": copy.deepcopy(rule),
        "required_scope_dimensions": required,
        "required_readings": {
            "1": ["action_fact"],
            "2": ["comparison_design", "method_rounds", "alignment_dimensions"],
            "3": ["method_successes"],
            "4": ["harm_checks"],
            "5": ["scope_values"],
            "6": ["scope_option_vectors"],
        },
    }


def derive_expected(scene_row: dict[str, Any]) -> dict[str, Any]:
    fields = derive_structured_fields(scene_row)
    answers: dict[str, str] = {
        "1": "INFO" if fields["nature"] == "info" else "CONTROL"
    }
    if answers["1"] == "INFO":
        pass
    else:
        answers["2"] = "COMPARED" if fields["compared"] is True else "NOT_COMPARED"
        if answers["2"] == "COMPARED":
            answers["3"] = "BETTER" if fields["better"] is True else "NOT_BETTER"
            if answers["3"] == "BETTER":
                answers["4"] = "HARM" if fields["harm"] is True else "NO_HARM"
                if answers["4"] == "NO_HARM":
                    answers["5"] = (
                        "SCOPE_WRITTEN"
                        if fields["scope_written"] is True
                        else "SCOPE_MISSING"
                    )
                    if answers["5"] == "SCOPE_WRITTEN":
                        answers["6"] = fields["scope_correct"]
    decisive = max(int(step) for step in answers)
    exit_answer = answers[str(decisive)]
    if exit_answer == "INFO":
        state = "DIAGNOSTIC"
    elif exit_answer in {"NOT_COMPARED", "SCOPE_MISSING"}:
        state = "UNRESOLVED"
    elif exit_answer in {"NOT_BETTER", "HARM"}:
        state = "WITHHELD"
    elif decisive == 6:
        state = "SUPPORTED"
    else:
        raise ValueError(f"cannot derive state for {scene_row['scene_id']}")
    return {
        **fields,
        "expected_answer_by_step": answers,
        "expected_exit_answer": exit_answer,
        "expected_decisive_step": decisive,
        "expected_state": state,
    }


def route_participant(path: list[dict[str, Any]]) -> dict[str, Any]:
    if not path:
        return {"done": False, "next_step": 1, "state": None}
    answers = {int(row["step"]): row["answer"] for row in path}
    expected_step = 1
    while expected_step in answers:
        answer = answers[expected_step]
        if expected_step == 1:
            if answer == "INFO":
                return {"done": True, "next_step": None, "state": "DIAGNOSTIC"}
            if answer != "CONTROL":
                raise ValueError("invalid step 1 answer")
        elif expected_step == 2:
            if answer == "NOT_COMPARED":
                return {"done": True, "next_step": None, "state": "UNRESOLVED"}
            if answer != "COMPARED":
                raise ValueError("invalid step 2 answer")
        elif expected_step == 3:
            if answer == "NOT_BETTER":
                return {"done": True, "next_step": None, "state": "WITHHELD"}
            if answer != "BETTER":
                raise ValueError("invalid step 3 answer")
        elif expected_step == 4:
            if answer == "HARM":
                return {"done": True, "next_step": None, "state": "WITHHELD"}
            if answer != "NO_HARM":
                raise ValueError("invalid step 4 answer")
        elif expected_step == 5:
            if answer == "SCOPE_MISSING":
                return {"done": True, "next_step": None, "state": "UNRESOLVED"}
            if answer != "SCOPE_WRITTEN":
                raise ValueError("invalid step 5 answer")
        elif expected_step == 6:
            if not isinstance(answer, str):
                raise ValueError("invalid scope answer")
            return {"done": True, "next_step": None, "state": "SUPPORTED"}
        expected_step += 1
    return {"done": False, "next_step": expected_step, "state": None}


def _fact_rows(scene_row: dict[str, Any]) -> list[dict[str, Any]]:
    rule = scene_row["comparison_rule"]
    old = rule["methods"]["existing"]
    new = rule["methods"]["new"]
    facts = [{"id": "action_fact", "text": copy.deepcopy(scene_row["action_fact"])}]
    if rule["design"] == "paired_same_conditions":
        align_en = ", ".join(row["label"]["en"] for row in rule["alignment_dimensions"])
        align_zh = "、".join(row["label"]["zh-Hans"] for row in rule["alignment_dimensions"])
        facts.extend(
            [
                {
                    "id": "comparison_design",
                    "text": copy.deepcopy(scene_row["comparison_fact"])
                    if scene_row["comparison_fact"] is not None
                    else bi(
                        f"{rule['paired_rounds']} paired rounds used the same {align_en}; "
                        "method order or side alternated.",
                        f"共 {rule['paired_rounds']} 个配对轮；每轮的{align_zh}相同，"
                        "做法顺序或左右位置轮换。",
                    ),
                },
                {
                    "id": "method_rounds",
                    "text": bi(
                        f"The original method and new button each had {old['denominator']} rounds.",
                        f"原办法和新按钮各做 {old['denominator']} 轮。",
                    ),
                },
                {
                    "id": "method_successes",
                    "text": bi(
                        f"The original method met the target in {old['successes']}/{old['denominator']} rounds; "
                        f"the new button did so in {new['successes']}/{new['denominator']}.",
                        f"原办法 {old['successes']}/{old['denominator']} 轮达到目标；"
                        f"新按钮 {new['successes']}/{new['denominator']} 轮达到目标。",
                    ),
                },
            ]
        )
    elif rule["design"] == "single_method_record":
        facts.extend(
            [
                {
                    "id": "comparison_design",
                    "text": bi(
                        "The record table has separate columns for the original method and the new button.",
                        "记录表分别列出“原办法”和“新按钮”两栏。",
                    ),
                },
                {
                    "id": "method_rounds",
                    "text": bi(
                        f"The original-method column contains {old['rounds']} rounds; "
                        f"the new-button column contains {new['rounds']} rounds. "
                        "No round used the original method.",
                        f"“原办法”栏是 {old['rounds']} 轮；“新按钮”栏是 {new['rounds']} 轮，"
                        "没有任何一轮使用原办法。",
                    ),
                },
                {
                    "id": "method_successes",
                    "text": bi(
                        f"The new button met the tissue criterion in {new['successes']}/{new['denominator']} rounds.",
                        f"新按钮 {new['successes']}/{new['denominator']} 轮达到纸巾标准。",
                    ),
                },
            ]
        )
    elif rule["design"] == "not_applicable_information_item":
        observation = scene_row["observation"]
        facts.extend(
            [
                {
                    "id": "observation_count",
                    "text": bi(
                        f"Across {observation['days']} days, {observation['matches']} of "
                        f"{observation['checks']} displays matched the independent strip.",
                        f"七天共查看 {observation['checks']} 次，其中 {observation['matches']} 次与独立湿度条文字相同。",
                    ),
                }
            ]
        )
    else:
        raise ValueError(f"unknown comparison design: {rule['design']}")
    denominator = new["rounds"] or scene_row.get("observation", {}).get("checks", 0)
    harm_en = "; ".join(
        row.get("fact", bi(
            f"{row['label']['en']}: {{count}}/{{denominator}}",
            f"{row['label']['zh-Hans']} {{count}}/{{denominator}}",
        ))["en"].format(count=row["count"], denominator=denominator)
        for row in scene_row["harm_checks"]
    )
    harm_zh = "；".join(
        row.get("fact", bi(
            f"{row['label']['en']}: {{count}}/{{denominator}}",
            f"{row['label']['zh-Hans']} {{count}}/{{denominator}}",
        ))["zh-Hans"].format(count=row["count"], denominator=denominator)
        for row in scene_row["harm_checks"]
    )
    facts.append({"id": "harm_checks", "text": bi(harm_en + ".", harm_zh + "。")})
    facts.extend(copy.deepcopy(scene_row["extra_facts"]))
    scope_en = " | ".join(
        f"{row['label']['en']}={row['value']['en']}" for row in scene_row["scope_dimensions"]
    )
    scope_zh = "｜".join(
        f"{row['label']['zh-Hans']}={row['value']['zh-Hans']}" for row in scene_row["scope_dimensions"]
    )
    facts.append(
        {
            "id": "scope_values",
            "text": bi(f"Recorded scope | {scope_en}.", f"范围记录｜{scope_zh}。"),
        }
    )
    return facts


def _scope_public(scene_row: dict[str, Any], locale: str) -> list[dict[str, Any]]:
    dimensions = {row["id"]: row for row in scene_row["scope_dimensions"]}
    output = []
    for option_row in _scope_vectors(scene_row):
        segments = []
        for dimension_id in dimensions:
            source = dimensions[dimension_id]
            value = option_row["vector"][dimension_id]["value"][locale]
            segments.append(
                {
                    "label": source["label"][locale],
                    "value": value,
                }
            )
        separator = " | "
        prefix = "Only when | " if locale == "en" else "仅在｜"
        text = prefix + separator.join(
            f"{row['label']}={row['value']}" for row in segments
        )
        output.append({"id": option_row["id"], "text": text, "segments": segments})
    return output


def _public_scene(scene_row: dict[str, Any], locale: str) -> dict[str, Any]:
    return {
        "display_id": "AB1" if scene_row["scene_id"].startswith("AB1-") else scene_row["scene_id"],
        "variant_id": scene_row["variant_id"],
        "title": scene_row["title"][locale],
        "card": {
            "situation": scene_row["situation"][locale],
            "goal": scene_row["goal"][locale],
            "existing": scene_row["existing"][locale],
            "new_item": scene_row["new_item"][locale],
            "facts": [row["text"][locale] for row in _fact_rows(scene_row)],
        },
        "scope_options": _scope_public(scene_row, locale),
    }


def _localized(value: Any, locale: str) -> Any:
    if isinstance(value, dict):
        if set(value) == set(LOCALES) and all(isinstance(value[key], str) for key in LOCALES):
            return value[locale]
        return {key: _localized(item, locale) for key, item in value.items()}
    if isinstance(value, list):
        return [_localized(item, locale) for item in value]
    return value


def _common(locale: str) -> dict[str, Any]:
    common = _localized(COMMON, locale)
    common["disclaimer"] = DISCLAIMER[locale]
    common["destinations"] = [
        {
            "id": row["id"],
            "label": row["label"][locale],
            "description": row["description"][locale],
        }
        for row in DESTINATIONS
    ]
    common["checklist"] = [row[locale] for row in CHECKLIST]
    common["questions"] = {
        str(step): {
            "prompt": QUESTIONS[step][locale],
            "options": [
                {"id": row["id"], "text": row["text"][locale]}
                for row in STEP_OPTIONS.get(step, [])
            ],
        }
        for step in range(1, 7)
    }
    common["reflection"]["options"] = {
        key: [{"id": row_id, "text": text[locale]} for row_id, text in rows]
        for key, rows in REFLECTION_OPTIONS.items()
    }
    return common


def ab_invariance_hash() -> str:
    def strip(row: dict[str, Any]) -> dict[str, Any]:
        value = copy.deepcopy(row)
        value.pop("scene_id", None)
        value.pop("variant_id", None)
        for method in value["comparison_rule"]["methods"].values():
            method.pop("successes", None)
        return value

    left = canonical_json_bytes(strip(AB1_A))
    right = canonical_json_bytes(strip(AB1_B))
    if left != right:
        raise ValueError("AB1 non-manipulated fields differ")
    return hashlib.sha256(left).hexdigest()


def _williams_orders(n: int = 6) -> list[list[int]]:
    first = [0]
    low, high = 1, n - 1
    while len(first) < n:
        first.append(low)
        low += 1
        if len(first) < n:
            first.append(high)
            high -= 1
    rows = [[(value + shift) % n for value in first] for shift in range(n)]
    return rows + [list(reversed(row)) for row in rows]


def generate_sequences() -> dict[str, Any]:
    return {
        "schema_version": SEQUENCE_SCHEMA_VERSION,
        "materials_version": MATERIALS_VERSION,
        "allocation_cycle": {
            "cells_per_locale": 24,
            "sequence_count": 12,
            "ab_variants": ["A", "B"],
            "rule": "paired cells per sequence; A then B; successful starts only",
        },
        "sequences": [
            {
                "sequence_id": f"BBS11-{index + 1:02d}",
                "slots": [
                    {
                        "position": position,
                        "scene_slot": FORMAL_SLOTS[scene_index],
                    }
                    for position, scene_index in enumerate(order, 1)
                ],
            }
            for index, order in enumerate(_williams_orders())
        ],
    }


def generate_materials() -> tuple[dict[str, Any], dict[str, Any]]:
    invariance = ab_invariance_hash()
    keys = {
        "schema_version": "microstudy-button-board-stepwise-derived-v1",
        "materials_version": MATERIALS_VERSION,
        "source_schema_version": SOURCE_SCHEMA_VERSION,
        "ab_invariance_hash": invariance,
        "practice": derive_expected(PRACTICE),
        "scenes": {
            row["scene_id"]: derive_expected(row) for row in FORMAL_SCENES
        },
        "attention": {"expected_answer": "INFO"},
    }
    locales = {
        locale: {
            "language_name": COMMON["language_name"][locale],
            "common": _common(locale),
            "practice": {
                **_public_scene(PRACTICE, locale),
                "feedback": PRACTICE["feedback"][locale],
            },
            "scenes": {
                row["scene_id"]: _public_scene(row, locale) for row in FORMAL_SCENES
            },
        }
        for locale in LOCALES
    }
    materials = {
        "schema_version": MATERIAL_SCHEMA_VERSION,
        "source_schema_version": SOURCE_SCHEMA_VERSION,
        "materials_version": MATERIALS_VERSION,
        "export_schema_version": EXPORT_SCHEMA_VERSION,
        "analysis_version": ANALYSIS_VERSION,
        "ab_invariance_hash": invariance,
        "formal_scene_ids": list(FORMAL_SCENE_IDS),
        "locale_contract": {
            "version": "button-board-stepwise-locale-contract-v1",
            "supported": list(LOCALES),
            "fallback": None,
            "auto_detect": False,
            "selected_locale_locked": True,
            "human_semantic_review": "UNVERIFIED_PRE_RECRUITMENT",
        },
        "render_contract": {
            "desktop_minimum_width_px": 1024,
            "desktop_viewports": [[1280, 800], [1440, 900]],
            "zoom_levels": [1, 2],
            "sticky_reference_width_px": 300,
            "one_question_at_a_time": True,
            "formal_correctness_feedback": False,
        },
        "locales": locales,
    }
    return materials, keys


def locale_manifest(materials: dict[str, Any]) -> dict[str, dict[str, str]]:
    return {
        locale: {
            "locale_bundle_version": f"{MATERIALS_VERSION}-{locale}",
            "locale_bundle_hash": hashlib.sha256(
                canonical_json_bytes(materials["locales"][locale])
            ).hexdigest(),
        }
        for locale in LOCALES
    }


def write_generated_materials() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    materials, keys = generate_materials()
    for path, value in (
        (MATERIALS_PATH, materials),
        (SEQUENCES_PATH, generate_sequences()),
        (DERIVED_KEYS_PATH, keys),
    ):
        path.write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def load_sources() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    return tuple(
        json.loads(path.read_text(encoding="utf-8"))
        for path in (MATERIALS_PATH, SEQUENCES_PATH, DERIVED_KEYS_PATH)
    )  # type: ignore[return-value]


def material_hashes() -> dict[str, str]:
    return {
        "canonical_materials_hash": hashlib.sha256(MATERIALS_PATH.read_bytes()).hexdigest(),
        "sequences_hash": hashlib.sha256(SEQUENCES_PATH.read_bytes()).hexdigest(),
        "derived_keys_hash": hashlib.sha256(DERIVED_KEYS_PATH.read_bytes()).hexdigest(),
    }


def _participant_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [text for item in value.values() for text in _participant_strings(item)]
    if isinstance(value, list):
        return [text for item in value for text in _participant_strings(item)]
    return []


def _normalize_zh(text: str) -> str:
    return re.sub(r"[\s｜|=，。、“”‘’：:；;·]", "", text)


def _english_words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9]+(?:[-–][A-Za-z0-9]+)*", text)


def _validate_scope_options(scene_row: dict[str, Any]) -> None:
    vectors = _scope_vectors(scene_row)
    fields = derive_structured_fields(scene_row)
    correct = next(row for row in vectors if row["id"] == fields["scope_correct"])
    expected_dimensions = [row["id"] for row in scene_row["scope_dimensions"]]
    for row in vectors:
        if list(row["vector"]) != expected_dimensions:
            raise ValueError(f"scope dimension order changed in {scene_row['scene_id']}")
        distance = sum(
            row["vector"][key]["value_id"] != correct["vector"][key]["value_id"]
            for key in expected_dimensions
        )
        if row["id"] != correct["id"] and distance != 1:
            raise ValueError(f"scope distractor must differ by one dimension in {scene_row['scene_id']}")
    for locale in LOCALES:
        public = _scope_public(scene_row, locale)
        if locale == "en":
            lengths = [len(_english_words(row["text"])) for row in public]
            if len(set(lengths)) != 1:
                raise ValueError(f"English scope word counts differ in {scene_row['scene_id']}")
        else:
            lengths = [len(_normalize_zh(row["text"])) for row in public]
            if max(lengths) - min(lengths) > 1:
                raise ValueError(f"Chinese scope lengths differ in {scene_row['scene_id']}")
        if len({len(row["segments"]) for row in public}) != 1:
            raise ValueError(f"scope dimension counts differ in {scene_row['scene_id']}")


def _validate_fact_consistency(scene_row: dict[str, Any]) -> None:
    facts = _fact_rows(scene_row)
    text = {locale: " ".join(row["text"][locale] for row in facts) for locale in LOCALES}
    rule = scene_row["comparison_rule"]
    for locale in LOCALES:
        for alignment in rule["alignment_dimensions"]:
            if alignment["label"][locale] not in text[locale]:
                raise ValueError(f"alignment fact missing in {scene_row['scene_id']}/{locale}")
        for dimension in scene_row["scope_dimensions"]:
            if dimension["value"][locale] not in text[locale]:
                raise ValueError(f"scope fact missing in {scene_row['scene_id']}/{locale}")
        for method in rule["methods"].values():
            for key in ("rounds", "successes"):
                value = method[key]
                if value is not None and str(value) not in text[locale]:
                    raise ValueError(f"comparison number missing in {scene_row['scene_id']}/{locale}")
    public = {
        locale: _public_scene(scene_row, locale)["card"]["facts"]
        for locale in LOCALES
    }
    for locale in LOCALES:
        if public[locale] != [row["text"][locale] for row in facts]:
            raise ValueError(f"card and fact registry diverged in {scene_row['scene_id']}/{locale}")


def _validate_neutral_text(materials: dict[str, Any]) -> None:
    banned = {
        "en": (
            "supported", "diagnostic", "withheld", "unresolved", "use area",
            "info card", "leave it off", "check again", "verdict", "superior",
            "successful", "failed", "better method",
        ),
        "zh-Hans": (
            "SUPPORTED", "DIAGNOSTIC", "WITHHELD", "UNRESOLVED", "常用区",
            "信息牌", "不装", "再看看", "暖", "温暖", "高情商", "智能", "聪明",
            "懂你", "更强", "更高级", "更优", "优化", "提升体验", "自然", "舒服",
            "省心", "有用", "有效", "效果好", "安全", "可靠", "稳定", "准确",
            "清楚", "快速", "正常", "合适", "合理", "成功", "失败", "表现好",
            "差不多", "明显", "经常", "通常", "很多", "很少", "结论",
        ),
    }
    for locale in LOCALES:
        for scene_id, row in materials["locales"][locale]["scenes"].items():
            card = " ".join(
                [
                    row["card"]["situation"],
                    row["card"]["goal"],
                    row["card"]["existing"],
                    row["card"]["new_item"],
                    *row["card"]["facts"],
                ]
            ).lower()
            if any(term.lower() in card for term in banned[locale]):
                raise ValueError(f"ambiguous or conclusion term in {scene_id}/{locale}")


def validate_sequences(sequences: dict[str, Any]) -> dict[str, Any]:
    if sequences != generate_sequences():
        raise ValueError("generated sequences are not current")
    rows = sequences["sequences"]
    if len(rows) != 12:
        raise ValueError("exactly 12 sequences required")
    cells: Counter[tuple[str, int]] = Counter()
    for sequence in rows:
        if {row["scene_slot"] for row in sequence["slots"]} != set(FORMAL_SLOTS):
            raise ValueError("sequence must contain each formal slot once")
        for row in sequence["slots"]:
            cells[row["scene_slot"], row["position"]] += 1
    if len(cells) != 36 or set(cells.values()) != {2}:
        raise ValueError("scene position balance failed")
    return {"sequence_count": 12, "scene_position_cells": 36}


def validate_materials(*, require_files_current: bool = True) -> dict[str, Any]:
    materials, keys = generate_materials()
    sequences = generate_sequences()
    if require_files_current:
        actual_materials, actual_sequences, actual_keys = load_sources()
        if actual_materials != materials:
            raise ValueError("generated public materials are not current")
        if actual_sequences != sequences:
            raise ValueError("generated sequences are not current")
        if actual_keys != keys:
            raise ValueError("generated derived keys are not current")
    sequence_report = validate_sequences(sequences)
    for row in [PRACTICE, *FORMAL_SCENES]:
        _validate_scope_options(row)
        _validate_fact_consistency(row)
        derived = derive_expected(row)
        if derive_expected(row) != derived:
            raise ValueError("expected derivation is not deterministic")
        if route_participant(
            [
                {"step": int(step), "answer": answer}
                for step, answer in derived["expected_answer_by_step"].items()
            ]
        )["state"] != derived["expected_state"]:
            raise ValueError(f"router and expected derivation differ in {row['scene_id']}")
        rule = derived["comparison_rule"]
        old, new = rule["methods"]["existing"], rule["methods"]["new"]
        if rule["design"] == "paired_same_conditions":
            if not (
                old["denominator"] == new["denominator"] == rule["paired_rounds"]
                and rule["paired_rounds"] > 0
                and rule["alignment_dimensions"]
            ):
                raise ValueError(f"paired schema invalid in {row['scene_id']}")
        if rule["design"] == "single_method_record":
            if not (
                old == {"rounds": 0, "denominator": 0, "successes": None}
                and new["rounds"] == new["denominator"] == 10
                and new["successes"] == 8
                and derived["compared"] is False
                and derived["better"] is None
            ):
                raise ValueError("single-method schema assertion failed")
    _validate_neutral_text(materials)
    if materials["ab_invariance_hash"] != ab_invariance_hash():
        raise ValueError("AB1 invariance hash mismatch")
    if keys["scenes"]["AB1-A"]["expected_state"] != "SUPPORTED":
        raise ValueError("AB1-A must derive SUPPORTED")
    if keys["scenes"]["AB1-B"]["expected_state"] != "WITHHELD":
        raise ValueError("AB1-B must derive WITHHELD")
    for variant in ("A", "B"):
        ids = [f"AB1-{variant}", "F2", "F3", "F4", "F5", "F6"]
        if set(keys["scenes"][scene_id]["expected_state"] for scene_id in ids) != set(STATES):
            raise ValueError(f"four-state coverage failed for AB1-{variant}")
    if set(materials["locales"]) != set(LOCALES):
        raise ValueError("locale parity failed")
    for locale in LOCALES:
        if set(materials["locales"][locale]["scenes"]) != set(FORMAL_SCENE_IDS):
            raise ValueError(f"scene parity failed for {locale}")
    public_text = json.dumps(materials, ensure_ascii=False)
    for forbidden in (
        "expected_answer_by_step", "expected_exit_answer", "expected_decisive_step",
        "expected_state", "nature", "compared", "better", "harm", "scope_written",
        "scope_correct", "comparison_rule", "required_readings",
        "required_scope_dimensions", "gaa_correct", "strict_correct",
    ):
        if f'"{forbidden}"' in public_text:
            raise ValueError(f"private key leaked into public materials: {forbidden}")
    manifest = locale_manifest(materials)
    return {
        "status": "PASS",
        "source_schema_version": SOURCE_SCHEMA_VERSION,
        "schema_version": MATERIAL_SCHEMA_VERSION,
        "materials_version": MATERIALS_VERSION,
        "sequence_schema_version": SEQUENCE_SCHEMA_VERSION,
        "export_schema_version": EXPORT_SCHEMA_VERSION,
        "analysis_version": ANALYSIS_VERSION,
        "formal_scene_count": 6,
        "variant_scene_count": 2,
        "ab_invariance_hash": keys["ab_invariance_hash"],
        "state_mapping": {
            row["scene_id"]: keys["scenes"][row["scene_id"]]["expected_state"]
            for row in FORMAL_SCENES
        },
        "locale_manifest": manifest,
        **sequence_report,
    }


@lru_cache(maxsize=1)
def validated_sources() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    validate_materials()
    return load_sources()


def main() -> int:
    print(json.dumps(validate_materials(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
