"""Structured source, generator, and validator for the V10 button-board study."""

from __future__ import annotations

import copy
import hashlib
import json
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "microstudy_button_board_v10"
MATERIALS_PATH = DATA_DIR / "materials.json"
SEQUENCES_PATH = DATA_DIR / "sequences.json"
DERIVED_KEYS_PATH = DATA_DIR / "derived_keys.json"

SOURCE_SCHEMA_VERSION = "microstudy-button-board-source-v1"
MATERIAL_SCHEMA_VERSION = "microstudy-button-board-v10-bilingual"
MATERIALS_VERSION = "v10-button-board-20260812-draft"
SEQUENCE_SCHEMA_VERSION = "microstudy-button-board-sequences-v1"
EXPORT_SCHEMA_VERSION = "microstudy-export-v7-button-board-raw-signed"
ANALYSIS_VERSION = "button-board-gaa-v2"
LOCALES = ("en", "zh-Hans")
FORMAL_SLOTS = ("FAB", "F3", "F4", "F5", "F6", "F7")
FORMAL_SCENE_IDS = ("F1", "F2", "F3", "F4", "F5", "F6", "F7")
Q1_STATES = (
    "Q1_SUPPORTED",
    "Q1_DIAGNOSTIC",
    "Q1_WITHHELD",
    "Q1_UNRESOLVED",
)
Q1_PUBLIC_IDS = {
    "Q1_SUPPORTED": "board-use",
    "Q1_DIAGNOSTIC": "board-info",
    "Q1_WITHHELD": "board-off",
    "Q1_UNRESOLVED": "board-check",
}


def bi(en: str, zh: str) -> dict[str, str]:
    return {"en": en, "zh-Hans": zh}


def option(option_id: str, tag: str, en: str, zh: str) -> dict[str, Any]:
    return {"id": option_id, "tag": tag, "text": bi(en, zh)}


DISCLAIMER = bi(
    "All products, buttons, and trial records shown here are fictional examples "
    "for this activity only. They do not represent real product effects or "
    "benefits.",
    "本页所有产品、按钮和试用记录均为虚构示意，仅用于本次判断，不代表任何真实"
    "产品功效，也不说明这些按钮真的有用。",
)

Q1_OPTIONS = [
    {
        "id": Q1_PUBLIC_IDS["Q1_SUPPORTED"],
        "state": "Q1_SUPPORTED",
        "label": bi("Use area", "常用区"),
        "description": bi(
            "Put it here and attach the “Only when…” label supported by the card.",
            "放进这里，并贴上卡片支持的“仅在……”标签。",
        ),
    },
    {
        "id": Q1_PUBLIC_IDS["Q1_DIAGNOSTIC"],
        "state": "Q1_DIAGNOSTIC",
        "label": bi("Info card", "信息牌"),
        "description": bi(
            "Keep it for checking what is happening, not as a button that changes "
            "the result.",
            "留作查看情况，不把它当成改变结果的按钮。",
        ),
    },
    {
        "id": Q1_PUBLIC_IDS["Q1_WITHHELD"],
        "state": "Q1_WITHHELD",
        "label": bi("Leave it off", "不装"),
        "description": bi(
            "Do not put this item on the board.",
            "这块按钮板上不装这个东西。",
        ),
    },
    {
        "id": Q1_PUBLIC_IDS["Q1_UNRESOLVED"],
        "state": "Q1_UNRESOLVED",
        "label": bi("Check again", "再看看"),
        "description": bi(
            "Put it in the waiting box until the records are clearer.",
            "先放进待定盒，等记录更清楚再决定。",
        ),
    },
]

COMMON = {
    "language_name": bi("English", "简体中文"),
    "title": bi("My fictional button board", "我的虚构按钮板"),
    "draft": bi(
        "DRAFT — owner-local preview only — not open for recruitment",
        "DRAFT — 仅供所有者本地预览 — 尚未开放招募",
    ),
    "privacy_short": bi(
        "Local, anonymous code, no free text",
        "本地运行、匿名代码、无自由文本",
    ),
    "welcome": {
        "heading": bi("Sort your button board", "整理你的按钮板"),
        "goal": bi(
            "Use only each fictional trial card to decide where the new item "
            "belongs on the button board.",
            "请只看每张虚构试用卡，决定新东西应该放进按钮板的哪一格。",
        ),
        "steps": bi(
            "1 practice card, 6 formal cards, and 1 read-the-instruction check.",
            "1 个练习、6 个正式场景、1 个看说明检查。",
        ),
        "fiction_note": bi(
            "There are no real product tests here, and you should not guess from "
            "everyday experience.",
            "这里没有真实产品测试，也不要求按生活经验猜测。",
        ),
        "local_note": bi(
            "This page runs locally. It uses an anonymous code, asks no free-text "
            "questions, and cannot resume after closing.",
            "页面在本地运行，使用匿名代码，不收自由文本，关闭后不能继续作答。",
        ),
        "participant_label": bi("Anonymous code", "匿名代码"),
        "participant_help": bi(
            "Use 1–64 letters, numbers, dots, underscores, or hyphens.",
            "请输入 1–64 个字母、数字、点、下划线或连字符。",
        ),
        "start": bi("Start", "开始"),
    },
    "tutorial": {
        "heading": bi("One idea and how to use the board", "一个直觉和按钮板操作"),
        "frame_1_heading": bi("One idea", "一个直觉"),
        "frame_1": bi(
            "A button responding does not mean it works better than your existing "
            "simple method.",
            "按钮有反应，不等于它比你原来的简单办法更好。",
        ),
        "frame_1_demo": bi(
            "Example display only: the new button lights on several rounds, while "
            "two side-by-side columns show raw completion counts.",
            "仅作操作示意：新按钮在若干轮亮起，旁边两列只显示两种办法的原始完成"
            "次数。",
        ),
        "frame_2_heading": bi("Board actions", "按钮板操作"),
        "frame_2": bi(
            "Stamp one equal-sized place. The stamp then locks. Next choose an "
            "“Only when…” label and the statement that mattered most. Moving on "
            "prevents changes.",
            "给一个等大的格子盖章，盖章后锁定；接着选择“仅在……”标签和最关键的"
            "理由；进入下一张卡后不能修改。",
        ),
        "frame_3_heading": bi("Static alternative", "静态替代"),
        "frame_3": bi(
            "Static sequence: read the card → stamp one place → lock → attach one "
            "boundary label → choose one reason → continue.",
            "静态顺序：读卡片 → 给一格盖章 → 锁定 → 贴一张范围标签 → 选择一条"
            "理由 → 继续。",
        ),
        "show_practice": bi("Open the practice card", "打开练习卡"),
    },
    "formal_intro": {
        "heading": bi("Formal cards", "正式卡片"),
        "guard": bi(
            "Even if a record differs from your own experience, use only the "
            "trial cards shown here. Do not add information that is not on the "
            "cards.",
            "即使这些记录和你的生活经验不同，也只能按页面上的试用卡判断。不要"
            "补充卡片外的信息。",
        ),
        "notes": bi(
            "All four placements may appear. Formal cards give no correctness "
            "feedback. Similar raw counts still require a card-based choice. "
            "Stamp first; after it locks, choose a boundary label and the most "
            "important statement. You cannot go back after continuing.",
            "四种放法都可能出现。正式题不告知对错。原始次数相近时也只能按卡片"
            "判断。先盖章；锁定后选择范围标签和最关键理由；继续后不能返回。",
        ),
        "begin": bi("Begin formal cards", "开始正式卡片"),
    },
    "record_labels": {
        "situation": bi("Everyday situation", "日常情境"),
        "goal": bi("What you want to do", "想完成什么"),
        "existing": bi("Existing simple method", "原来的简单办法"),
        "new_item": bi("New item", "新东西"),
        "respond": bi("Did it respond?", "有反应吗？"),
        "comparison": bi(
            "Side-by-side under the same conditions",
            "相同条件下并排比较",
        ),
        "amount": bi("Days and trials recorded", "记录了多少天、多少次"),
        "effects": bi("Any other effects?", "有没有别的影响"),
        "conditions": bi(
            "Conditions in which it was tried",
            "试用发生在哪些情况",
        ),
    },
    "questions": {
        "q1": bi(
            "Where should this new item go on your button board?",
            "这个新东西应该放进按钮板的哪一格？",
        ),
        "scope": bi(
            "Which “Only when…” label best matches the trial card? Do not add "
            "conditions not shown on the card.",
            "哪张“仅在……”标签最贴合试用卡？不要补充卡片外的条件。",
        ),
        "reason": bi(
            "Which statement matters most for the choice you just made?",
            "哪一条最能决定你刚才的选择？",
        ),
        "stamp": bi("Stamp and lock", "盖章并锁定"),
        "submit_scope": bi("Attach this label", "贴上这张标签"),
        "submit_reason": bi("Submit and continue", "提交并继续"),
        "locked": bi(
            "Your stamp is locked. It cannot be changed.",
            "你的盖章已锁定，不能修改。",
        ),
        "choice_required": bi("Choose one option before continuing.", "继续前请选择一项。"),
    },
    "progress": {
        "practice": bi("Practice card", "练习卡"),
        "formal": bi("Formal card {current} of 6", "正式卡片 {current}/6"),
        "attention": bi("Read-the-instruction check", "看说明检查"),
        "reflection": bi("Optional reflection", "可选反思"),
    },
    "attention": {
        "heading": bi("Read-the-instruction check", "看说明检查"),
        "instruction": bi(
            "This item only checks whether you read the instruction. Stamp "
            "“Check again” and choose “The card directly asks for this.”",
            "这题只检查你有没有读到这里。请给“再看看”盖章，并选择“卡片直接要求"
            "这样做”。",
        ),
        "reason_prompt": bi("Why did you use that stamp?", "为什么这样盖章？"),
        "submit_q1": bi("Lock this stamp", "锁定盖章"),
        "submit_reason": bi("Submit check", "提交检查"),
    },
    "reflection": {
        "heading": bi("Optional reflection", "可选反思"),
        "helpful": bi(
            "Which kind of record most often helped you decide?",
            "哪类记录最常帮助你决定？",
        ),
        "confusing": bi(
            "Which two places were easiest to confuse?",
            "哪两个位置最容易混淆？",
        ),
        "amount": bi("How was the amount of page text?", "页面文字量如何？"),
        "skip": bi("Prefer not to answer", "不回答"),
        "submit": bi("Finish", "完成"),
    },
    "export": {
        "heading": bi("Activity complete", "活动结束"),
        "debrief": bi(
            "You did not test real products. This activity records how you sort "
            "fictional trial cards; it does not measure whether products improve "
            "people’s lives.",
            "你刚才没有测试真实产品。本活动只记录你如何整理虚构试用卡，不测量"
            "这些产品是否真的改善生活。",
        ),
        "download_json": bi("Download signed JSON", "下载签名 JSON"),
        "download_csv": bi("Download signed CSV", "下载签名 CSV"),
        "finish": bi("Clear this page", "清除此页面"),
        "manual": bi(
            "Downloads are manual. No performance feedback is shown.",
            "下载需手动操作，页面不显示表现反馈。",
        ),
        "complete_product": bi("Complete signed export", "完整签名导出"),
        "partial_product": bi("Partial signed export", "部分签名导出"),
    },
    "save_exit": {
        "button": bi("End and prepare partial export", "结束并准备部分导出"),
        "heading": bi("End this local activity?", "结束本地活动？"),
        "body": bi(
            "This session cannot resume. Submitted choices will be frozen in a "
            "signed partial export; unfinished choices stay missing. Nothing "
            "downloads automatically.",
            "本次活动不能继续。已提交选择会冻结在签名部分导出中，未完成选择保持"
            "缺失；页面不会自动下载。",
        ),
        "cancel": bi("Cancel", "取消"),
        "confirm": bi("Prepare partial export", "准备部分导出"),
    },
    "errors": {
        "generic": bi("The local request failed. Please try again.", "本地请求失败，请重试。"),
        "download": bi(
            "Download failed. Both download buttons remain available.",
            "下载失败，两个下载按钮仍可使用。",
        ),
        "desktop": bi(
            "Desktop preview required. This DRAFT is blocked below 1280 CSS "
            "pixels until a responsive human review is completed.",
            "需要桌面预览。在完成人工响应式审核前，本 DRAFT 会阻止宽度低于 "
            "1280 CSS 像素的设备。",
        ),
    },
}


def record(
    *,
    situation: dict[str, str],
    goal: dict[str, str],
    existing: dict[str, str],
    new_item: dict[str, str],
    respond: dict[str, str],
    comparison: dict[str, str] | None,
    amount: dict[str, str],
    effects: dict[str, str],
    conditions: dict[str, str],
) -> dict[str, Any]:
    return {
        "situation": situation,
        "goal": goal,
        "existing": existing,
        "new_item": new_item,
        "respond": respond,
        "comparison": comparison,
        "amount": amount,
        "effects": effects,
        "conditions": conditions,
    }


PRACTICE = {
    "scene_id": "P1",
    "title": bi("Wardrobe dampness card", "衣柜潮气提示牌"),
    "read_status": "usable",
    "paired_comparison": {"mode": "missing"},
    "quality_status": "pass",
    "scope_status": "exact",
    "record": record(
        situation=bi(
            "A wardrobe sometimes becomes damp.",
            "衣柜有时返潮。",
        ),
        goal=bi(
            "Know whether the wardrobe is currently damp or normal.",
            "知道衣柜里现在偏潮还是正常。",
        ),
        existing=bi(
            "Open the door and check with a separate humidity strip.",
            "打开柜门，用独立湿度纸查看。",
        ),
        new_item=bi("Dampness card.", "潮气提示牌。"),
        respond=bi(
            "It displayed a label on all six checks across six days.",
            "六天查看六次，提示牌六次都显示了文字。",
        ),
        comparison=bi(
            "It matched the separate strip on five of six checks; no trial tested "
            "it changing wardrobe dampness.",
            "六次中有五次与独立湿度纸的“偏潮/正常”一致；没有安排它改变衣柜潮气"
            "的试用。",
        ),
        amount=bi("Six checks across six days.", "六天共查看六次。"),
        effects=bi(
            "It did not block the door in any check.",
            "六次均未挡住柜门。",
        ),
        conditions=bi(
            "This wardrobe, the same shelf and this card.",
            "该衣柜、同一层搁板、这张提示牌。",
        ),
    ),
    "scope_options": [
        option(
            "P1-S-A",
            "exact",
            "Only in this wardrobe, on the same shelf, using this card.",
            "仅在该衣柜、同一层搁板、使用这张提示牌。",
        ),
        option(
            "P1-S-B",
            "expanded",
            "Only in every wardrobe at home and in every season.",
            "仅在家中所有衣柜和所有季节。",
        ),
        option(
            "P1-S-C",
            "overbroad",
            "Only in this wardrobe, regardless of shelf or dampness card.",
            "仅在该衣柜，不限制搁板或提示牌。",
        ),
        option(
            "P1-S-D",
            "scope_missing",
            "The record is too incomplete to name any wardrobe trial boundary.",
            "记录不足以写出任何衣柜试用范围。",
        ),
    ],
    "reason_options": [
        option(
            "P1-R-A",
            "RESPONSE_ONLY",
            "Six displays appeared, so the card must already have changed the "
            "wardrobe dampness.",
            "六次都有文字显示，因此它已经改变了衣柜里的潮气。",
        ),
        option(
            "P1-R-B",
            "READ_WITHOUT_CONTROL_COMPARISON",
            "Five displays matched the strip, but the record did not test changing "
            "wardrobe dampness.",
            "五次显示与湿度纸一致，但记录没有测试它改变潮气。",
        ),
        option(
            "P1-R-C",
            "DISCARD_NARROW_RECORD",
            "The record used one wardrobe, so none of the display observations "
            "should be read at all.",
            "记录只来自一个衣柜，因此所有显示观察都不应该读取。",
        ),
        option(
            "P1-R-D",
            "EVERYDAY_GUESS",
            "Wardrobes often need airing, so everyday experience should replace "
            "the entire trial card.",
            "家中衣柜通常需要通风，因此应让生活经验替代整张试用卡。",
        ),
    ],
    "feedback": bi(
        "This practice card recorded whether the display matched a humidity "
        "strip, but it did not test the card changing wardrobe dampness.",
        "这张练习卡记录了提示牌与湿度纸的显示是否一致，但没有安排它改变衣柜潮气"
        "的试用。",
    ),
}


def fab_scene(scene_id: str, variant_id: str, old: int, new: int, first_old: int,
              first_new: int, second_old: int, second_new: int) -> dict[str, Any]:
    return {
        "scene_id": scene_id,
        "variant_id": variant_id,
        "display_id": "FAB",
        "title": bi("Receipt-folder page-finder tab", "票夹寻页扣"),
        "read_status": "usable",
        "paired_comparison": {
            "mode": "paired",
            "trials": 10,
            "raw_counts": {
                "old_success": old,
                "new_success": new,
                "blocks": [
                    {"old_success": first_old, "new_success": first_new},
                    {"old_success": second_old, "new_success": second_new},
                ],
            },
        },
        "quality_status": "pass",
        "scope_status": "exact",
        "record": record(
            situation=bi(
                "Find a named receipt in a household receipt folder.",
                "从一本家庭票夹中找指定票据。",
            ),
            goal=bi(
                "Find the named receipt within 30 seconds.",
                "三十秒内找到指定票据。",
            ),
            existing=bi(
                "Use month dividers and then turn pages.",
                "使用月份分隔签后逐页翻找。",
            ),
            new_item=bi(
                "Page-finder tab; after entering a receipt code, it lights beside "
                "a candidate page.",
                "票夹寻页扣；键入票据编号后在候选页旁亮灯。",
            ),
            respond=bi(
                "It lit beside a candidate page in eight of ten rounds.",
                "十轮中有八轮亮起候选页灯。",
            ),
            comparison=None,
            amount=bi(
                "Ten paired rounds using two replica folders.",
                "使用两本复刻票夹完成十组配对。",
            ),
            effects=bi(
                "It did not cover a month divider or move or omit a receipt in "
                "any round.",
                "十轮均未遮住原月份签，也未移动或遗漏票据。",
            ),
            conditions=bi(
                "This 40-page folder, receipts from the last 30 days, desk light "
                "on and the same user.",
                "这本四十页票夹、近三十天票据、桌面灯开启、本人操作。",
            ),
        ),
        "pairing": bi(
            "Each round used two replica folders with identical contents and page "
            "order, the same target, lighting and 30-second limit; left and right "
            "positions alternated.",
            "每轮使用内容和页序相同的两本复刻票夹，相同票据、相同照明、相同三十秒"
            "限制；左右位置轮换。",
        ),
        "comparison_template": bi(
            "Across ten rounds, the month dividers completed the task within 30 "
            "seconds in {old} rounds, and the tab did so in {new}. The first five "
            "rounds were {first_old} and {first_new}; the last five were "
            "{second_old} and {second_new}.",
            "十轮中，月份分隔签在 {old} 轮于三十秒内找到票据；寻页扣在 {new} 轮"
            "于三十秒内找到票据。前五轮分别为 {first_old} 次和 {first_new} 次，"
            "后五轮分别为 {second_old} 次和 {second_new} 次。",
        ),
        "scope_options": [
            option(
                "FAB-S-A",
                "overbroad",
                "Only with this folder and last-30-day receipts, regardless of "
                "lighting or user.",
                "仅在这本票夹和近三十天票据，不限制照明或操作者。",
            ),
            option(
                "FAB-S-B",
                "expanded",
                "Only with every folder at home, last-30-day receipts and the "
                "desk light on.",
                "仅在家中所有票夹、近三十天票据、桌面灯开启。",
            ),
            option(
                "FAB-S-C",
                "exact",
                "Only with this 40-page folder, last-30-day receipts, desk light "
                "on and the same user.",
                "仅在这本四十页票夹、近三十天票据、桌面灯开启、本人操作。",
            ),
            option(
                "FAB-S-D",
                "scope_missing",
                "The record does not identify the folder, receipt, lighting or "
                "user boundary.",
                "记录不足以写出设备、票据、照明和操作者范围。",
            ),
        ],
        "reason_options": [
            option(
                "FAB-R-A",
                "POSITIVE_SAFE_SCOPED",
                "Under the same conditions, the tab completed more rounds, with "
                "effects and trial boundaries recorded.",
                "相同条件下新扣完成次数更高，其他影响和试用边界也有记录。",
            ),
            option(
                "FAB-R-B",
                "RESOLVED_NO_SUPERIORITY",
                "Under the same conditions, the tab did not complete more rounds "
                "than the month-divider method.",
                "相同条件下新扣完成次数没有高于月份分隔签的完成次数。",
            ),
            option(
                "FAB-R-C",
                "RESPONSE_ONLY",
                "The tab lit in eight rounds, so the paired completion counts do "
                "not need to be considered.",
                "寻页扣有八轮亮灯，因此不需要再读取两种办法的完成次数。",
            ),
            option(
                "FAB-R-D",
                "EVERYDAY_GUESS",
                "Month dividers are familiar, so everyday preference should "
                "replace the paired record shown on the card.",
                "月份分隔签是常见做法，因此应让日常偏好替代卡片上的配对记录。",
            ),
        ],
    }


F1 = fab_scene("F1", "F1", 5, 8, 3, 4, 2, 4)
F2 = fab_scene("F2", "F2", 8, 7, 4, 4, 4, 3)

F3 = {
    "scene_id": "F3",
    "title": bi("Soil-status tile", "盆土状态片"),
    "read_status": "usable",
    "paired_comparison": {"mode": "missing"},
    "quality_status": "pass",
    "scope_status": "exact",
    "record": record(
        situation=bi(
            "Check whether soil in a windowsill pot is currently dry or damp.",
            "查看窗台花盆里的土现在偏干还是偏湿。",
        ),
        goal=bi("See the soil’s current condition.", "看见当前土壤状态。"),
        existing=bi(
            "Touch the topsoil at the same location.",
            "用手指碰同一位置的表土。",
        ),
        new_item=bi("Soil-status tile.", "盆土状态片。"),
        respond=bi(
            "It displayed text on all 14 checks across seven days.",
            "七天查看十四次，状态片十四次均显示文字。",
        ),
        comparison=bi(
            "Twelve displays matched the touch record; no trial used each method "
            "to guide watering and then compared outcomes.",
            "十二次显示与当时的手指触土记录一致；没有安排两种办法分别指导浇水后"
            "再比较结果。",
        ),
        amount=bi("Fourteen checks across seven days.", "七天共查看十四次。"),
        effects=bi(
            "It did not block drainage or touch leaves in any check.",
            "十四次均未挡住排水孔或碰到叶片。",
        ),
        conditions=bi(
            "This pot, this windowsill position and the same soil type.",
            "该花盆、该窗台位置、同一种盆土。",
        ),
    ),
    "scope_options": [
        option(
            "F3-S-A",
            "expanded",
            "Only with every pot and every soil type at home.",
            "仅在家中所有花盆和所有盆土。",
        ),
        option(
            "F3-S-B",
            "overbroad",
            "Only with this pot, regardless of position or soil type.",
            "仅在该花盆，不限制位置或盆土。",
        ),
        option(
            "F3-S-C",
            "scope_missing",
            "The record does not identify the pot, position or soil boundary.",
            "记录不足以写出花盆、位置或盆土范围。",
        ),
        option(
            "F3-S-D",
            "exact",
            "Only with this pot, this windowsill position and this soil type.",
            "仅在该花盆、该窗台位置、同一种盆土。",
        ),
    ],
    "reason_options": [
        option(
            "F3-R-A",
            "ASSUME_CONTROL",
            "Twelve displays matched, so the tile must already have changed later "
            "watering outcomes.",
            "十二次显示一致，因此状态片已经改变了后续浇水结果。",
        ),
        option(
            "F3-R-B",
            "DISCARD_NARROW_RECORD",
            "The record covers one pot, so none of the display observations should "
            "be used at all.",
            "记录只覆盖一个花盆，因此所有显示观察都不应该使用。",
        ),
        option(
            "F3-R-C",
            "NO_EFFECTS_MEANS_CONTROL",
            "No other effect appeared, so the tile has already improved every "
            "later watering result.",
            "没有发现其他影响，因此已经说明它改善了之后的每次浇水结果。",
        ),
        option(
            "F3-R-D",
            "READ_WITHOUT_CONTROL_COMPARISON",
            "The record shows moisture displays, but it does not compare changed "
            "watering outcomes.",
            "记录说明它能显示干湿，但没有比较它能否改变浇水结果。",
        ),
    ],
}

F4 = {
    "scene_id": "F4",
    "title": bi("Quiet-reading notification tab", "静读通知扣"),
    "read_status": "usable",
    "paired_comparison": {
        "mode": "paired",
        "trials": 10,
        "raw_counts": {
            "old_success": 6,
            "new_success": 9,
            "blocks": [{"old_success": 6, "new_success": 9}],
        },
    },
    "quality_status": "fail",
    "scope_status": "exact",
    "record": record(
        situation=bi(
            "Read continuously on a phone for 20 minutes at night.",
            "晚上在手机上连续阅读二十分钟。",
        ),
        goal=bi(
            "Avoid interruption by ordinary app pop-ups for 20 minutes.",
            "二十分钟内不被普通应用弹窗打断。",
        ),
        existing=bi(
            "Turn off notifications for three ordinary apps before reading.",
            "开始前逐个关闭三个普通应用的通知。",
        ),
        new_item=bi(
            "Quiet-reading notification tab.",
            "静读通知扣。",
        ),
        respond=bi(
            "It changed notification settings on all ten nights.",
            "十晚中十晚都改变了通知设置。",
        ),
        comparison=bi(
            "The existing method completed 20 minutes on six nights; the tab did "
            "so on nine.",
            "原办法有六晚完成二十分钟；新扣有九晚完成二十分钟。",
        ),
        amount=bi("Ten matched nights.", "十个配对夜晚。"),
        effects=bi(
            "A pre-marked priority-contact test call was scheduled each night; "
            "with the tab, three calls produced neither a ring nor an on-screen "
            "indicator.",
            "十晚均安排一通预先标记的优先联系人测试来电；使用新扣时有三晚没有"
            "铃声，也没有屏幕提示点。",
        ),
        conditions=bi(
            "The same phone and reading app, home Wi-Fi and 21:00–23:00.",
            "本人手机、当前阅读应用、家中 Wi-Fi、21:00–23:00。",
        ),
    ),
    "scope_options": [
        option(
            "F4-S-A",
            "overbroad",
            "Only on this phone at night, regardless of app or network.",
            "仅在本人手机和夜间，不限制应用或网络。",
        ),
        option(
            "F4-S-B",
            "exact",
            "Only on this phone and reading app, home Wi-Fi and 21:00–23:00.",
            "仅在本人手机、当前阅读应用、家中 Wi-Fi、21:00–23:00。",
        ),
        option(
            "F4-S-C",
            "expanded",
            "Only on every phone, this reading app, home Wi-Fi and 21:00–23:00.",
            "仅在所有手机、当前阅读应用、家中 Wi-Fi、21:00–23:00。",
        ),
        option(
            "F4-S-D",
            "scope_missing",
            "The record does not identify the phone, app, network or time.",
            "记录不足以写出手机、应用、网络或时间范围。",
        ),
    ],
    "reason_options": [
        option(
            "F4-R-A",
            "TARGET_COUNT_ONLY",
            "The tab completed nine nights, so the target count is enough to "
            "ignore every other record.",
            "新扣有九晚完成目标，因此只看目标次数便可忽略其他记录。",
        ),
        option(
            "F4-R-B",
            "COHERENCE_FAIL",
            "In the same record, three priority calls had no alert, affecting "
            "another important task.",
            "同一批记录中三次优先来电没有提示，另一件重要事情受到影响。",
        ),
        option(
            "F4-R-C",
            "SCOPE_ERASES_EFFECT",
            "Once the phone and nighttime are named, missing priority calls no "
            "longer count as an effect.",
            "写明本人手机和夜间后，漏掉优先来电便不再属于其他影响。",
        ),
        option(
            "F4-R-D",
            "RESPONSE_ONLY",
            "The setting changed every night, so only the response count should "
            "replace all paired and effect records.",
            "每晚都改变通知设置，因此反应次数应替代全部配对记录和影响记录。",
        ),
    ],
}

F5 = {
    "scene_id": "F5",
    "title": bi("Mirror-clearing tile", "镜面清雾片"),
    "read_status": "usable",
    "paired_comparison": {
        "mode": "paired",
        "trials": 4,
        "raw_counts": {
            "old_success": 2,
            "new_success": 3,
            "blocks": [
                {"old_success": 0, "new_success": 2},
                {"old_success": 2, "new_success": 1},
            ],
        },
    },
    "quality_status": "pass",
    "scope_status": "exact",
    "record": record(
        situation=bi(
            "See a marked central area of a bathroom mirror after washing.",
            "洗漱后看清浴室镜面中央的标记区域。",
        ),
        goal=bi(
            "Become clear within 60 seconds and remain clear for five minutes.",
            "六十秒内清楚，并保持五分钟。",
        ),
        existing=bi(
            "Wipe the marked area with a dry microfiber cloth.",
            "用干燥超细纤维布擦拭标记区域。",
        ),
        new_item=bi("Mirror-clearing tile.", "镜面清雾片。"),
        respond=bi(
            "Airflow appeared in all four rounds across two days.",
            "两天共四轮，四轮都出现了气流。",
        ),
        comparison=bi(
            "In two sunny midday rounds, the tile met the target twice and the "
            "cloth zero times; in two humid evening rounds, the tile did so once "
            "and the cloth twice.",
            "晴天中午两轮，新片达到目标两次、布达到零次；潮湿晚间两轮，新片达到"
            "目标一次、布达到两次。",
        ),
        amount=bi("Four paired rounds across two days.", "两天共四组配对。"),
        effects=bi(
            "It left no water marks and did not move the frame.",
            "四轮均未留下水痕或移动镜框。",
        ),
        conditions=bi(
            "This mirror and marked area, at sunny midday and humid evening.",
            "该镜子、标记区域、晴天中午和潮湿晚间。",
        ),
    ),
    "scope_options": [
        option(
            "F5-S-A",
            "exact",
            "Only on the marked area of this mirror, at sunny midday and humid "
            "evening.",
            "仅在该镜子的标记区域、晴天中午和潮湿晚间。",
        ),
        option(
            "F5-S-B",
            "expanded",
            "Only on every mirror at home, at sunny midday and humid evening.",
            "仅在家中所有镜子、晴天中午和潮湿晚间。",
        ),
        option(
            "F5-S-C",
            "overbroad",
            "Only in this bathroom, regardless of mirror, area or time.",
            "仅在该浴室，不限制镜子、区域或时段。",
        ),
        option(
            "F5-S-D",
            "scope_missing",
            "The record does not identify the mirror, area or time boundary.",
            "记录不足以写出镜子、区域或时段范围。",
        ),
    ],
    "reason_options": [
        option(
            "F5-R-A",
            "COMPARISON_UNCLEAR",
            "There are four pairs and the direction changes by time, so the "
            "current record is insufficient.",
            "只有四组且两个时段方向不同，因此现有记录仍然不足。",
        ),
        option(
            "F5-R-B",
            "TOTAL_ONLY",
            "The tile completed three of four rounds, so it must be stable across "
            "every time condition.",
            "新片四次完成三次，因此已经说明它在每个时段都很稳定。",
        ),
        option(
            "F5-R-C",
            "NO_EFFECTS_ERASE_MIXED",
            "No other effect was recorded, so the small time-dependent direction "
            "change can be ignored.",
            "没有记录其他影响，因此可以忽略少量且随时段变化的方向。",
        ),
        option(
            "F5-R-D",
            "SCOPE_REPLACES_DATA",
            "The trial boundary is specific, so the boundary text can replace "
            "more paired observations across both times.",
            "试用范围写得具体，因此范围文字可以替代两个时段的更多配对观察。",
        ),
    ],
}

F6 = {
    "scene_id": "F6",
    "title": bi("Anti-static clothing clip", "衣物除静电夹"),
    "read_status": "usable",
    "paired_comparison": {
        "mode": "paired",
        "trials": 12,
        "raw_counts": {
            "old_success": 7,
            "new_success": 10,
            "blocks": [
                {"old_success": 4, "new_success": 5},
                {"old_success": 3, "new_success": 5},
            ],
        },
    },
    "quality_status": "pass",
    "scope_status": "scope_missing",
    "record": record(
        situation=bi(
            "Reduce static cling on clothing before dressing.",
            "穿衣前减少衣物贴在手臂上的静电。",
        ),
        goal=bi(
            "Avoid cling to the arm within one minute of dressing.",
            "穿上后一分钟内不再贴住手臂。",
        ),
        existing=bi(
            "Wipe the inside once with a slightly damp cotton cloth.",
            "用微湿的棉布在衣物内侧擦一次。",
        ),
        new_item=bi("Anti-static clothing clip.", "衣物除静电夹。"),
        respond=bi(
            "It produced a short vibration in all 12 rounds.",
            "十二轮中十二轮都发出一次短振动。",
        ),
        comparison=bi(
            "Across 12 pairs, the cloth met the target in seven and the clip in "
            "ten; the first six were four and five, and the last six three and "
            "five.",
            "十二组配对中，棉布有七组达到目标，新夹有十组达到目标；前六组分别为"
            "四次和五次，后六组分别为三次和五次。",
        ),
        amount=bi("Twelve paired rounds at home.", "在家中完成十二组配对。"),
        effects=bi(
            "It caused no water mark, pulled thread or skin redness.",
            "十二轮均未留下水痕、拉线或皮肤红印。",
        ),
        conditions=bi(
            "The record only says “12 rounds at home”; it does not identify "
            "fabric, humidity, clothing type or clip position.",
            "记录只写“在家中试了十二轮”；没有记录衣物材质、湿度、衣物类型或夹放"
            "位置。",
        ),
    ),
    "scope_options": [
        option(
            "F6-S-A",
            "invented",
            "Only on cotton tops, in low humidity and inside the cuff.",
            "仅在纯棉上衣、低湿度、袖口内侧使用。",
        ),
        option(
            "F6-S-B",
            "expanded",
            "Only on all clothing and in every humidity condition at home.",
            "仅在家中所有衣物和所有湿度条件下使用。",
        ),
        option(
            "F6-S-C",
            "scope_missing",
            "The record is insufficient to specify fabric, humidity, clothing "
            "type and clip position.",
            "记录不足以写出材质、湿度、衣物类型和夹放位置的完整标签。",
        ),
        option(
            "F6-S-D",
            "invented",
            "Only on sweaters and synthetic clothing, with the clip at the collar "
            "in dry rooms.",
            "仅在毛衣和化纤衣物上、干燥房间内夹在衣领位置使用。",
        ),
    ],
    "reason_options": [
        option(
            "F6-R-A",
            "GENERALIZE_COUNTS",
            "Twelve pairs were ten versus seven, so the result can be used on "
            "every unrecorded kind of clothing.",
            "十二组是十次对七次，因此可直接用于各种未记录的衣物。",
        ),
        option(
            "F6-R-B",
            "NO_EFFECTS_ERASE_SCOPE",
            "No marks or redness appeared, so the conditions of the trial no "
            "longer need to be known.",
            "没有发现水痕或红印，因此无需知道试用发生在哪些条件。",
        ),
        option(
            "F6-R-C",
            "POSITIVE_SCOPE_UNSPECIFIED",
            "The paired direction is clear, but key trial conditions are missing "
            "from the boundary.",
            "配对结果方向清楚，但关键试用条件缺失，无法写出完整边界。",
        ),
        option(
            "F6-R-D",
            "RESPONSE_ONLY",
            "All twelve rounds produced vibration, so the missing fabric, "
            "humidity, clothing and position details do not matter.",
            "十二次都出现短振动，因此缺少材质、湿度、衣物类型和夹放位置都不重要。",
        ),
    ],
}

F7 = {
    "scene_id": "F7",
    "title": bi("Meal-box reheating tab", "饭盒回温扣"),
    "read_status": "usable",
    "paired_comparison": {
        "mode": "paired",
        "trials": 14,
        "raw_counts": {
            "old_success": 8,
            "new_success": 13,
            "blocks": [
                {"old_success": 4, "new_success": 6},
                {"old_success": 4, "new_success": 7},
            ],
        },
    },
    "quality_status": "pass",
    "scope_status": "exact",
    "record": record(
        situation=bi(
            "Reheat a refrigerated rice-and-vegetable meal box.",
            "给冷藏米饭和蔬菜饭盒回温。",
        ),
        goal=bi(
            "Reach the marked centre temperature without drying the edges.",
            "中心达到标记温度，同时边缘不变干。",
        ),
        existing=bi(
            "Use a two-minute timer, pausing once to stir.",
            "普通两分钟计时，中途暂停并搅拌一次。",
        ),
        new_item=bi("Meal-box reheating tab.", "饭盒回温扣。"),
        respond=bi(
            "It adjusted the pause timing on all 14 meals.",
            "十四顿饭中十四次都调整了暂停时间。",
        ),
        comparison=bi(
            "Across 14 matched boxes and portions, the existing method met the "
            "target in eight and the tab in 13; two family members each ran seven "
            "pairs, with tab counts of six and seven and existing-method counts "
            "of four and four.",
            "十四组相同饭盒和份量中，原办法八组达到目标，新扣十三组达到目标；两位"
            "家人各做七组，新扣分别为六次和七次，原办法均为四次。",
        ),
        amount=bi("Fourteen paired meals.", "十四组配对饭盒。"),
        effects=bi(
            "No pair caused a trip, overflow, burnt edge or missed completion "
            "alert.",
            "十四组均未跳闸、溢出、出现焦边或漏掉结束提醒。",
        ),
        conditions=bi(
            "This microwave, this 650 mL glass box, refrigerated rice with "
            "vegetables, 300–350 g and medium power.",
            "该微波炉、该 650 mL 玻璃饭盒、冷藏米饭加蔬菜、300–350 g、中档。",
        ),
    ),
    "scope_options": [
        option(
            "F7-S-A",
            "overbroad",
            "Only with this microwave and glass box, regardless of food, portion "
            "or power.",
            "仅在该微波炉和玻璃饭盒，不限制食物、份量或档位。",
        ),
        option(
            "F7-S-B",
            "expanded",
            "Only with every microwave, a 650 mL box and 300–350 g of food.",
            "仅在所有微波炉、650 mL 饭盒、300–350 g 食物上。",
        ),
        option(
            "F7-S-C",
            "scope_missing",
            "The record does not identify the device, box, food, portion or "
            "power boundary.",
            "记录不足以写出设备、容器、食物、份量或档位范围。",
        ),
        option(
            "F7-S-D",
            "exact",
            "Only with this microwave and box, refrigerated rice with vegetables, "
            "300–350 g and medium power.",
            "仅在该微波炉、该饭盒、冷藏米饭加蔬菜、300–350 g、中档。",
        ),
    ],
    "reason_options": [
        option(
            "F7-R-A",
            "RESPONSE_ONLY",
            "The timing changed in all 14 meals, so the two completion counts do "
            "not need to be read.",
            "十四次都调整暂停时间，因此不需要读取两种办法的完成次数。",
        ),
        option(
            "F7-R-B",
            "POSITIVE_SAFE_SCOPED",
            "Under the same conditions it was 13 versus eight, with effects and "
            "trial boundaries recorded.",
            "相同条件下是十三次对八次，其他影响和试用边界也有记录。",
        ),
        option(
            "F7-R-C",
            "GENERALIZE_USERS",
            "Two family members ran the pairs, so the record applies to every "
            "device, food, portion and power setting.",
            "两位家人都参加了试用，因此记录适用于所有设备、食物、份量和档位。",
        ),
        option(
            "F7-R-D",
            "DISCARD_NARROW_RECORD",
            "One meal-box content was tested, so none of the paired observations "
            "can support any card-based judgment.",
            "只测试一种饭盒内容，因此全部配对观察都不能支持任何卡片判断。",
        ),
    ],
}

FORMAL_SCENES = [F1, F2, F3, F4, F5, F6, F7]

ATTENTION = {
    "scene_id": "AC1",
    "requested_state": "Q1_UNRESOLVED",
    "reason_options": [
        option(
            "AC1-R-A",
            "response",
            "Because the button responded.",
            "因为按钮有反应。",
        ),
        option(
            "AC1-R-B",
            "direct_instruction",
            "Because this card directly asks for it.",
            "因为本卡直接要求这样做。",
        ),
        option(
            "AC1-R-C",
            "changed_record",
            "Because it changed the record.",
            "因为它改变了记录。",
        ),
        option(
            "AC1-R-D",
            "displayed_status",
            "Because it displayed a status.",
            "因为它显示了状态。",
        ),
    ],
}

REFLECTION_OPTIONS = {
    "helpful": [
        ("paired_counts", bi("Side-by-side completion counts", "并排完成次数")),
        ("other_effects", bi("Other effects", "其他影响")),
        ("conditions", bi("Trial conditions", "试用情况")),
        ("response", bi("Whether it responded", "是否有反应")),
        ("skip", bi("Prefer not to answer", "不回答")),
    ],
    "confusing": [
        ("use_info", bi("Use area and Info card", "常用区和信息牌")),
        ("use_check", bi("Use area and Check again", "常用区和再看看")),
        ("off_check", bi("Leave it off and Check again", "不装和再看看")),
        ("info_check", bi("Info card and Check again", "信息牌和再看看")),
        ("skip", bi("Prefer not to answer", "不回答")),
    ],
    "amount": [
        ("too_little", bi("Too little", "太少")),
        ("about_right", bi("About right", "正好")),
        ("too_much", bi("Too much", "太多")),
        ("skip", bi("Prefer not to answer", "不回答")),
    ],
}


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def derive_comparison(scene: dict[str, Any]) -> str:
    paired = scene["paired_comparison"]
    mode = paired["mode"]
    if mode == "missing":
        return "missing"
    if mode != "paired":
        raise ValueError(f"invalid comparison mode for {scene['scene_id']}")
    trials = paired["trials"]
    counts = paired["raw_counts"]
    blocks = counts["blocks"]
    directions = {
        (block["new_success"] > block["old_success"])
        - (block["new_success"] < block["old_success"])
        for block in blocks
    }
    directions.discard(0)
    if len(directions) > 1:
        return "mixed"
    if trials < 8:
        return "thin"
    if counts["new_success"] - counts["old_success"] >= 2:
        return "decisive_positive"
    if counts["new_success"] <= counts["old_success"]:
        return "decisive_negative"
    return "thin"


def derive_q1_state(inputs: dict[str, str]) -> str:
    comparison = inputs["comparison"]
    if inputs["quality_status"] == "fail" or comparison == "decisive_negative":
        return "Q1_WITHHELD"
    if (
        comparison == "decisive_positive"
        and inputs["quality_status"] == "pass"
        and inputs["scope_status"] == "exact"
    ):
        return "Q1_SUPPORTED"
    if inputs["read_status"] == "usable" and comparison == "missing":
        return "Q1_DIAGNOSTIC"
    return "Q1_UNRESOLVED"


def derive_reason_class(inputs: dict[str, str], state: str) -> str:
    if state == "Q1_SUPPORTED":
        return "POSITIVE_SAFE_SCOPED"
    if state == "Q1_DIAGNOSTIC":
        return "READ_WITHOUT_CONTROL_COMPARISON"
    if state == "Q1_WITHHELD":
        if inputs["quality_status"] == "fail":
            return "COHERENCE_FAIL"
        return "RESOLVED_NO_SUPERIORITY"
    if inputs["comparison"] in {"mixed", "thin"}:
        return "COMPARISON_UNCLEAR"
    if (
        inputs["comparison"] == "decisive_positive"
        and inputs["scope_status"] == "scope_missing"
    ):
        return "POSITIVE_SCOPE_UNSPECIFIED"
    raise ValueError(f"no reason route for {inputs}")


def derive_scene_keys(scene: dict[str, Any]) -> dict[str, Any]:
    inputs = {
        "read_status": scene["read_status"],
        "comparison": derive_comparison(scene),
        "quality_status": scene["quality_status"],
        "scope_status": scene["scope_status"],
    }
    state = derive_q1_state(inputs)
    reason_class = derive_reason_class(inputs, state)
    reasons = [
        row["id"] for row in scene["reason_options"] if row["tag"] == reason_class
    ]
    scope_tag = "scope_missing" if scene["scope_status"] == "scope_missing" else "exact"
    scopes = [
        row["id"] for row in scene["scope_options"] if row["tag"] == scope_tag
    ]
    if len(reasons) != 1 or len(scopes) != 1:
        raise ValueError(f"non-unique derived option for {scene['scene_id']}")
    return {
        **inputs,
        "q1_state": state,
        "paper_state": {
            "Q1_SUPPORTED": "S",
            "Q1_DIAGNOSTIC": "D",
            "Q1_WITHHELD": "W",
            "Q1_UNRESOLVED": "U",
        }[state],
        "reason_class": reason_class,
        "correct_reason_id": reasons[0],
        "correct_scope_id": scopes[0],
        "scope_gate_required": (
            inputs["comparison"] == "decisive_positive"
            and inputs["quality_status"] == "pass"
        ),
    }


def _localized(value: Any, locale: str) -> Any:
    if isinstance(value, dict):
        if set(value) == set(LOCALES) and all(
            isinstance(value[key], str) for key in LOCALES
        ):
            return value[locale]
        return {key: _localized(item, locale) for key, item in value.items()}
    if isinstance(value, list):
        return [_localized(item, locale) for item in value]
    return value


def _public_options(rows: list[dict[str, Any]], locale: str) -> list[dict[str, str]]:
    return [{"id": row["id"], "text": row["text"][locale]} for row in rows]


def _comparison_text(scene: dict[str, Any], locale: str) -> str:
    if scene["record"]["comparison"] is not None:
        return scene["record"]["comparison"][locale]
    counts = scene["paired_comparison"]["raw_counts"]
    first, second = counts["blocks"]
    rendered = scene["comparison_template"][locale].format(
        old=counts["old_success"],
        new=counts["new_success"],
        first_old=first["old_success"],
        first_new=first["new_success"],
        second_old=second["old_success"],
        second_new=second["new_success"],
    )
    return f"{scene['pairing'][locale]} {rendered}"


def _public_scene(scene: dict[str, Any], locale: str) -> dict[str, Any]:
    record_copy = {
        key: value[locale] if value is not None else _comparison_text(scene, locale)
        for key, value in scene["record"].items()
    }
    return {
        "display_id": scene.get("display_id", scene["scene_id"]),
        "title": scene["title"][locale],
        "record": record_copy,
        "scope_options": _public_options(scene["scope_options"], locale),
        "reason_options": _public_options(scene["reason_options"], locale),
    }


def _public_q1(locale: str) -> list[dict[str, str]]:
    return [
        {
            "id": row["id"],
            "label": row["label"][locale],
            "description": row["description"][locale],
        }
        for row in Q1_OPTIONS
    ]


def ab_invariance_hash() -> str:
    def strip(scene: dict[str, Any]) -> dict[str, Any]:
        value = copy.deepcopy(scene)
        value.pop("scene_id", None)
        value.pop("variant_id", None)
        value["paired_comparison"].pop("raw_counts", None)
        return value

    left = canonical_json_bytes(strip(F1))
    right = canonical_json_bytes(strip(F2))
    if left != right:
        raise ValueError("F1/F2 non-manipulated fields differ")
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


def _q1_order_sets(sequence_index: int) -> list[list[str]]:
    states = list(Q1_PUBLIC_IDS.values())
    rotations = [states[index:] + states[:index] for index in range(4)]
    extra = sequence_index % 4
    reversed_states = list(reversed(states))
    return rotations + [
        states[extra:] + states[:extra],
        reversed_states[extra:] + reversed_states[:extra],
    ]


def generate_sequences() -> dict[str, Any]:
    sequences = []
    for sequence_index, order in enumerate(_williams_orders()):
        q1_orders = _q1_order_sets(sequence_index)
        sequences.append(
            {
                "sequence_id": f"BB10-{sequence_index + 1:02d}",
                "slots": [
                    {
                        "position": position,
                        "scene_slot": FORMAL_SLOTS[scene_index],
                        "q1_order": q1_orders[position - 1],
                    }
                    for position, scene_index in enumerate(order, 1)
                ],
            }
        )
    return {
        "schema_version": SEQUENCE_SCHEMA_VERSION,
        "materials_version": MATERIALS_VERSION,
        "allocation_cycle": {
            "cells_per_locale": 24,
            "sequence_count": 12,
            "ab_variants": ["F1", "F2"],
            "rule": "paired cells per sequence; F1 then F2; success-only",
        },
        "sequences": sequences,
    }


def generate_materials() -> tuple[dict[str, Any], dict[str, Any]]:
    invariance = ab_invariance_hash()
    keys = {
        "schema_version": "microstudy-button-board-derived-keys-v1",
        "materials_version": MATERIALS_VERSION,
        "source_schema_version": SOURCE_SCHEMA_VERSION,
        "ab_invariance_hash": invariance,
        "practice": derive_scene_keys(PRACTICE),
        "scenes": {
            scene["scene_id"]: derive_scene_keys(scene) for scene in FORMAL_SCENES
        },
        "attention": {
            "q1_state": ATTENTION["requested_state"],
            "correct_reason_id": next(
                row["id"]
                for row in ATTENTION["reason_options"]
                if row["tag"] == "direct_instruction"
            ),
        },
    }
    locales = {}
    for locale in LOCALES:
        common = _localized(COMMON, locale)
        common["disclaimer"] = DISCLAIMER[locale]
        common["q1_options"] = _public_q1(locale)
        common["attention"]["reason_options"] = _public_options(
            ATTENTION["reason_options"], locale
        )
        common["reflection"]["options"] = {
            key: [{"id": row_id, "text": text[locale]} for row_id, text in rows]
            for key, rows in REFLECTION_OPTIONS.items()
        }
        locales[locale] = {
            "language_name": COMMON["language_name"][locale],
            "common": common,
            "practice": {
                **_public_scene(PRACTICE, locale),
                "feedback": PRACTICE["feedback"][locale],
            },
            "scenes": {
                scene["scene_id"]: _public_scene(scene, locale)
                for scene in FORMAL_SCENES
            },
        }
    materials = {
        "schema_version": MATERIAL_SCHEMA_VERSION,
        "source_schema_version": SOURCE_SCHEMA_VERSION,
        "materials_version": MATERIALS_VERSION,
        "export_schema_version": EXPORT_SCHEMA_VERSION,
        "analysis_version": ANALYSIS_VERSION,
        "ab_invariance_hash": invariance,
        "locale_contract": {
            "version": "button-board-locale-contract-v1",
            "supported": list(LOCALES),
            "fallback": None,
            "auto_detect": False,
            "selected_locale_locked": True,
            "human_semantic_review": "UNVERIFIED_PRE_RECRUITMENT",
        },
        "render_contract": {
            "desktop_minimum_width_px": 1280,
            "desktop_viewports": [[1280, 800], [1440, 900]],
            "zoom_levels": [1, 2],
            "equal_q1_cells": True,
            "color_or_checkmark_cues": False,
            "formal_feedback": False,
        },
        "formal_scene_ids": list(FORMAL_SCENE_IDS),
        "locales": locales,
    }
    return materials, keys


def canonical_locale_bytes(bundle: dict[str, Any]) -> bytes:
    return canonical_json_bytes(bundle)


def locale_manifest(materials: dict[str, Any]) -> dict[str, dict[str, str]]:
    return {
        locale: {
            "locale_bundle_version": f"{MATERIALS_VERSION}-{locale}",
            "locale_bundle_hash": hashlib.sha256(
                canonical_locale_bytes(materials["locales"][locale])
            ).hexdigest(),
        }
        for locale in LOCALES
    }


def write_generated_materials() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    materials, keys = generate_materials()
    sequences = generate_sequences()
    for path, value in (
        (MATERIALS_PATH, materials),
        (SEQUENCES_PATH, sequences),
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
        "canonical_materials_hash": hashlib.sha256(
            MATERIALS_PATH.read_bytes()
        ).hexdigest(),
        "sequences_hash": hashlib.sha256(SEQUENCES_PATH.read_bytes()).hexdigest(),
        "derived_keys_hash": hashlib.sha256(
            DERIVED_KEYS_PATH.read_bytes()
        ).hexdigest(),
    }


def _participant_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [
            text
            for item in value.values()
            for text in _participant_strings(item)
        ]
    if isinstance(value, list):
        return [text for item in value for text in _participant_strings(item)]
    return []


def validate_sequences(sequences: dict[str, Any]) -> dict[str, Any]:
    if sequences != generate_sequences():
        raise ValueError("generated sequence file is not current")
    rows = sequences["sequences"]
    if len(rows) != 12:
        raise ValueError("exactly 12 sequences are required")
    scene_positions: Counter[tuple[str, int]] = Counter()
    q1_positions: Counter[tuple[str, int]] = Counter()
    for sequence in rows:
        slots = sequence["slots"]
        if len(slots) != 6 or {row["scene_slot"] for row in slots} != set(
            FORMAL_SLOTS
        ):
            raise ValueError("every sequence must contain six unique formal slots")
        per_sequence: Counter[tuple[str, int]] = Counter()
        for slot in slots:
            scene_positions[slot["scene_slot"], slot["position"]] += 1
            if sorted(slot["q1_order"]) != sorted(Q1_PUBLIC_IDS.values()):
                raise ValueError("Q1 order is not a permutation")
            for position, option_id in enumerate(slot["q1_order"], 1):
                q1_positions[option_id, position] += 1
                per_sequence[option_id, position] += 1
        for option_id in Q1_PUBLIC_IDS.values():
            counts = [per_sequence[option_id, position] for position in range(1, 5)]
            if max(counts) - min(counts) > 1:
                raise ValueError("Q1 grid positions are not balanced per sequence")
    if set(scene_positions.values()) != {2} or len(scene_positions) != 36:
        raise ValueError("formal scene-position balance failed")
    if set(q1_positions.values()) != {18} or len(q1_positions) != 16:
        raise ValueError("Q1 grid position balance failed")
    return {
        "sequence_count": len(rows),
        "scene_position_cells": len(scene_positions),
        "q1_position_cells": len(q1_positions),
    }


def _validate_banned_text(materials: dict[str, Any]) -> None:
    banned_records = {
        "en": (
            "supported", "diagnostic", "withheld", "unresolved", "use area",
            "info card", "leave it off", "check again", " win ", " tie ",
            " lose ", "verdict", "superior",
        ),
        "zh-Hans": (
            "SUPPORTED", "DIAGNOSTIC", "WITHHELD", "UNRESOLVED",
            "常用区", "信息牌", "不装", "再看看", "赢", "平", "输", "胜", "败",
            "没比过", "还看不清", "结论", "应安装",
        ),
    }
    banned_reasons = {
        "en": (
            "supported", "diagnostic", "withheld", "unresolved", "use area",
            "info card", "leave it off", "check again",
        ),
        "zh-Hans": (
            "SUPPORTED", "DIAGNOSTIC", "WITHHELD", "UNRESOLVED",
            "常用区", "信息牌", "不装", "再看看",
        ),
    }
    for locale in LOCALES:
        for scene_id, scene in materials["locales"][locale]["scenes"].items():
            record_text = " ".join(scene["record"].values())
            padded = f" {record_text.lower()} "
            if any(term.lower() in padded for term in banned_records[locale]):
                raise ValueError(f"formal record leakage in {scene_id}/{locale}")
            reason_text = " ".join(row["text"] for row in scene["reason_options"])
            if any(
                term.lower() in reason_text.lower()
                for term in banned_reasons[locale]
            ):
                raise ValueError(f"formal reason leakage in {scene_id}/{locale}")
        tutorial = json.dumps(
            materials["locales"][locale]["common"]["tutorial"],
            ensure_ascii=False,
        ).lower()
        forbidden_tutorial = (
            "decisive_positive", "coherence", "scope_missing", "router",
            "完整四态", "判定树",
        )
        if any(term.lower() in tutorial for term in forbidden_tutorial):
            raise ValueError(f"tutorial router leakage in {locale}")
        feedback = materials["locales"][locale]["practice"]["feedback"].lower()
        if any(term.lower() in feedback for term in banned_reasons[locale]):
            raise ValueError(f"practice feedback state leakage in {locale}")
        participant_text = " ".join(
            _participant_strings(materials["locales"][locale])
        ).lower()
        technical_terms = (
            (" artificial intelligence ", " ai ", " statistics ", " statistical ",
             " analysis ", " model ", " algorithm ")
            if locale == "en"
            else ("人工智能", "统计", "分析", "模型", "算法")
        )
        padded_participant_text = f" {participant_text} "
        if any(term in padded_participant_text for term in technical_terms):
            raise ValueError(f"technical terminology leaked in {locale}")


def _validate_option_lengths(keys: dict[str, Any]) -> dict[str, Any]:
    reports = []
    for scene in [PRACTICE, *FORMAL_SCENES]:
        correct = (
            keys["practice"]["correct_reason_id"]
            if scene["scene_id"] == "P1"
            else keys["scenes"][scene["scene_id"]]["correct_reason_id"]
        )
        for locale in LOCALES:
            lengths = {row["id"]: len(row["text"][locale]) for row in scene["reason_options"]}
            minimum, maximum = min(lengths.values()), max(lengths.values())
            if minimum == 0 or maximum / minimum > 1.65:
                raise ValueError(f"reason length imbalance in {scene['scene_id']}/{locale}")
            if lengths[correct] >= maximum:
                raise ValueError(
                    f"correct reason is longest in {scene['scene_id']}/{locale}"
                )
            reports.append(
                {
                    "scene_id": scene["scene_id"],
                    "locale": locale,
                    "min": minimum,
                    "max": maximum,
                    "correct": lengths[correct],
                }
            )
    return {"reason_length_reports": reports}


def validate_materials(*, require_files_current: bool = True) -> dict[str, Any]:
    generated_materials, generated_keys = generate_materials()
    generated_sequences = generate_sequences()
    if require_files_current:
        actual_materials, actual_sequences, actual_keys = load_sources()
        if actual_materials != generated_materials:
            raise ValueError("generated materials file is not current")
        if actual_sequences != generated_sequences:
            raise ValueError("generated sequence file is not current")
        if actual_keys != generated_keys:
            raise ValueError("generated keys file is not current")
    materials, keys = generated_materials, generated_keys
    sequence_report = validate_sequences(generated_sequences)
    expected_states = {
        "P1": "Q1_DIAGNOSTIC",
        "F1": "Q1_SUPPORTED",
        "F2": "Q1_WITHHELD",
        "F3": "Q1_DIAGNOSTIC",
        "F4": "Q1_WITHHELD",
        "F5": "Q1_UNRESOLVED",
        "F6": "Q1_UNRESOLVED",
        "F7": "Q1_SUPPORTED",
    }
    actual_states = {
        "P1": keys["practice"]["q1_state"],
        **{
            scene_id: row["q1_state"]
            for scene_id, row in keys["scenes"].items()
        },
    }
    if actual_states != expected_states:
        raise ValueError(f"router mapping changed: {actual_states}")
    required_routes = {
        ("decisive_positive", "exact", "Q1_SUPPORTED"),
        ("decisive_positive", "scope_missing", "Q1_UNRESOLVED"),
        ("decisive_negative", "exact", "Q1_WITHHELD"),
        ("missing", "exact", "Q1_DIAGNOSTIC"),
        ("mixed", "exact", "Q1_UNRESOLVED"),
    }
    routes = {
        (row["comparison"], row["scope_status"], row["q1_state"])
        for row in [keys["practice"], *keys["scenes"].values()]
    }
    if not required_routes <= routes:
        raise ValueError("required router coverage is incomplete")
    if keys["scenes"]["F4"]["reason_class"] != "COHERENCE_FAIL":
        raise ValueError("positive plus coherence failure must route to W")
    if not all(
        keys["scenes"][scene_id]["scope_gate_required"]
        for scene_id in ("F1", "F6", "F7")
    ):
        raise ValueError("scope gate coverage changed")
    if any(
        keys["scenes"][scene_id]["scope_gate_required"]
        for scene_id in ("F2", "F3", "F4", "F5")
    ):
        raise ValueError("scope gate applied outside frozen positive-pass routes")
    if materials["ab_invariance_hash"] != ab_invariance_hash():
        raise ValueError("A/B invariance hash mismatch")
    if set(materials["locales"]) != set(LOCALES):
        raise ValueError("locale set changed")
    for locale in LOCALES:
        bundle = materials["locales"][locale]
        if set(bundle["scenes"]) != set(FORMAL_SCENE_IDS):
            raise ValueError(f"scene parity failed for {locale}")
        if [row["id"] for row in bundle["common"]["q1_options"]] != list(
            Q1_PUBLIC_IDS.values()
        ):
            raise ValueError(f"Q1 stable-ID parity failed for {locale}")
        for scene in bundle["scenes"].values():
            if len(scene["scope_options"]) != 4 or len(scene["reason_options"]) != 4:
                raise ValueError("every formal Q2 block must have four options")
            if set(scene["record"]) != {
                "situation", "goal", "existing", "new_item", "respond",
                "comparison", "amount", "effects", "conditions",
            }:
                raise ValueError("neutral record card fields changed")
    _validate_banned_text(materials)
    length_report = _validate_option_lengths(keys)
    public_text = json.dumps(materials, ensure_ascii=False)
    for forbidden in (
        "correct_reason_id", "correct_scope_id", "q1_state", "paper_state",
        "reason_class", "scope_gate_required", "quality_status", "read_status",
        "decisive_positive", "decisive_negative",
    ):
        if forbidden in public_text:
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
        "state_distribution_by_variant": {
            "F1": dict(
                Counter(
                    keys["scenes"][scene_id]["paper_state"]
                    for scene_id in ("F1", "F3", "F4", "F5", "F6", "F7")
                )
            ),
            "F2": dict(
                Counter(
                    keys["scenes"][scene_id]["paper_state"]
                    for scene_id in ("F2", "F3", "F4", "F5", "F6", "F7")
                )
            ),
        },
        "router_mapping": actual_states,
        "scope_gate_scenes": ["F1", "F6", "F7"],
        "ab_invariance_hash": keys["ab_invariance_hash"],
        "locale_manifest": manifest,
        **sequence_report,
        **length_report,
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
