"""Build the self-contained, unsigned V3 stepwise offline study."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from cognitive_console.button_board_stepwise import materials

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "deploy" / "stepwise" / "offline" / "button-board-stepwise-offline.html"
CSS_PATH = ROOT / "src" / "cognitive_console" / "button_board_stepwise" / "static" / "study.css"
LOCALES = ("en", "zh-Hans")
PRIVATE_KEY_PARTS = (
    "expected",
    "comparison_rule",
    "required_readings",
    "required_scope_dimensions",
    "scope_correct",
    "gaa_correct",
    "strict_correct",
    "correctness",
)
HONESTY = {
    "en": (
        "Fictional illustrative materials; unsigned offline return depends on honest "
        "submission; exploratory pilot only; protocol is not frozen. The consent draft "
        "contains placeholders and must be finalized by the advisor/ethics reviewer "
        "before formal recruitment."
    ),
    "zh-Hans": (
        "示意/虚构材料；无服务器签名，依赖参与者诚实回传；仅用于 exploratory pilot；"
        "协议未冻结。知情同意草案仍含占位符，正式招募前须由导师/伦理审查定稿。"
    ),
}


def _assert_public_keys(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = key.lower()
            if any(part in lowered for part in PRIVATE_KEY_PARTS):
                raise ValueError(f"private key leaked at {path}.{key}")
            _assert_public_keys(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _assert_public_keys(item, f"{path}[{index}]")


def build_payload() -> dict[str, Any]:
    _, _, private_keys = materials.validated_sources()
    hashes = materials.material_hashes()
    locale_payloads: dict[str, Any] = {}
    for locale in LOCALES:
        bundle = materials.common_materials(locale)
        common = bundle["common"]
        if locale == "en":
            common["formal_intro"]["feedback"] = (
                "Formal trials do not reveal whether an answer is right. "
                "Any of the four destinations may apply."
            )
        export_copy = common.get("export")
        if isinstance(export_copy, dict):
            if locale == "en":
                export_copy["download_json"] = "Download unsigned JSON"
                export_copy["download_csv"] = "Download unsigned CSV"
            else:
                export_copy["download_json"] = "下载未签名 JSON"
                export_copy["download_csv"] = "下载未签名 CSV"
        save_exit = common.get("save_exit")
        if isinstance(save_exit, dict) and "body" in save_exit:
            save_exit["body"] = (
                "This offline page cannot resume. Submitted choices stay in an "
                "unsigned local export; nothing is uploaded."
                if locale == "en"
                else "离线页面不能继续。已提交选择保存在本地未签名导出中；不会上传。"
            )
        locale_payloads[locale] = {
            "metadata": materials.locale_bundle_metadata(locale),
            "common": common,
            "demonstration": bundle["demonstration"],
            "questions": {
                str(step): materials.question_material(locale, step)
                for step in range(1, 7)
            },
            "honesty_notice": HONESTY[locale],
        }

    packets = []
    for cell in range(24):
        sequence_id = f"BBS11-{cell // 2 + 1:02d}"
        ab_variant = "A" if cell % 2 == 0 else "B"
        plan = materials.planned_trials(sequence_id, ab_variant, str(cell))
        packet = {
            "allocation_cell": cell,
            "sequence_id": sequence_id,
            "ab_variant": ab_variant,
            "locales": {},
        }
        for locale in LOCALES:
            slots = []
            for row in plan:
                scene = materials.scene_material(locale, row["scene_id"])
                _assert_public_keys(scene)
                scope_by_id = {option["id"]: option for option in scene["scope_options"]}
                if set(scope_by_id) != set(row["scope_order_ids"]):
                    raise ValueError("scope option order does not match public scene")
                scene["scope_options"] = [
                    scope_by_id[option_id] for option_id in row["scope_order_ids"]
                ]
                slots.append(
                    {
                        "slot_index": row["slot_index"],
                        "position": row["position"],
                        "scene_id": row["scene_id"],
                        "variant_id": (
                            ab_variant if row["scene_id"].startswith("AB1-") else None
                        ),
                        "scope_order_ids": list(row["scope_order_ids"]),
                        "scene": scene,
                    }
                )
            packet["locales"][locale] = slots
        packets.append(packet)

    payload = {
        "export_schema": "microstudy-export-offline-stepwise-v1",
        "signed": False,
        "materials_version": materials.common_materials("en")["materials_version"],
        **hashes,
        "ab_invariance_hash": private_keys["ab_invariance_hash"],
        "locales": locale_payloads,
        "packets": packets,
    }
    _assert_public_keys(payload)
    return payload


HTML_TEMPLATE = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Offline stepwise button-board activity</title>
<style>__CSS__
.offline-warning{padding:12px;border:2px solid #9a6700;background:#fff8c5}.hidden{display:none!important}
.inline-note{font-size:.9rem;color:#59636e}.choice button{width:100%;text-align:left}.choice.selected{outline:3px solid #0969da}
.downloads{display:flex;gap:12px;flex-wrap:wrap}.reflection-grid{display:grid;gap:12px}.reflection-grid label{font-weight:650}
</style>
</head>
<body>
<header id="site-header"><strong>V3 Stepwise — Offline</strong><span id="fiction-banner"></span></header>
<main id="app"><noscript>This file requires JavaScript enabled.</noscript></main>
<footer id="site-footer"><span>Unsigned offline exploratory pilot</span><button id="language-button" class="secondary" type="button">中文 / English</button></footer>
<script id="study-data" type="application/json">__DATA__</script>
<script>
'use strict';
const DATA=JSON.parse(document.querySelector('#study-data').textContent);
const CONSENT_COPY={
 "zh-Hans":{heading:"研究知情同意书（草案）",body:[
  {title:"研究目的",text:"这是一项匿名的小规模学术研究，了解普通人如何判断界面上标注了某种功能的按钮。研究由 [研究者姓名 / 院系（待填写）] 开展。"},
  {title:"你需要做什么",text:"你将阅读若干虚构的“试用记录”卡片，并逐个判断某个按钮应当放到哪里。全程大约 [约 X 分钟（待填写）]。所有产品、按钮和试用记录都是虚构示意，不代表任何真实产品或其功效。"},
  {title:"自愿参与与退出",text:"参与完全自愿。你可以在任何时候关闭页面退出，不会有任何不利影响；即使不完成，也不会受到任何评价。"},
  {title:"匿名与隐私",text:"本研究不收集你的姓名、联系方式、账号或任何可识别你身份的信息。系统只记录你在本页面内做出的选择，以及一个随机生成的临时编号（仅用于区分不同作答）。"},
  {title:"数据的用途与保存",text:"去标识化的作答数据将用于学术研究分析，并可能以汇总形式在学术论文或报告中发表；不会公开任何能识别到个人的信息。数据的保存与管理遵循 [数据保存方案 / 期限（待填写）]。"},
  {title:"风险与获益",text:"本研究没有已知风险。[报酬 / 学分说明（待填写；如无补偿请注明）]。你的参与将帮助我们了解普通用户对这类判断的理解。"},
  {title:"伦理审查与联系方式",text:"本研究已通过 [伦理审查机构名称 / 批准编号（待填写）] 的审查。如对本研究有任何疑问，可联系 [研究者姓名 / 邮箱（待填写）]；如对参与者权益有疑问，可联系 [伦理委员会联系方式（待填写）]。"},
  {title:"知情同意声明",text:"勾选下方选项即表示：我已阅读并理解以上信息，我已年满 [年龄门槛，如 18（待填写）] 周岁，自愿参加本研究，并知道我可以随时退出。"}],
  agree:"我已阅读并理解以上信息，自愿参加本研究。",start:"同意并开始",decline:"我不同意 / 退出",declined:"感谢你的时间。你已退出，本页面未记录任何回答，可以直接关闭窗口。"},
 en:{heading:"Research informed-consent form (draft)",body:[
  {title:"Purpose of the study",text:"This is an anonymous, small academic study of how ordinary people judge on-screen buttons that are labelled with some function. It is conducted by [researcher name / department (to be completed)]."},
  {title:"What you will do",text:"You will read a series of fictional “trial record” cards and decide, one at a time, where a button should go. The whole task takes about [about X minutes (to be completed)]. All products, buttons, and trial records are fictional examples and do not represent any real product or its effects."},
  {title:"Voluntary participation and withdrawal",text:"Participation is entirely voluntary. You may close the page and withdraw at any time with no adverse consequence; you will not be evaluated even if you do not finish."},
  {title:"Anonymity and privacy",text:"This study does not collect your name, contact details, account, or any information that could identify you. The system records only the choices you make on this page, plus a randomly generated temporary identifier used solely to distinguish separate submissions."},
  {title:"How the data is used and stored",text:"De-identified responses will be used for academic research analysis and may be published in aggregate form in academic papers or reports; no individually identifiable information will be disclosed. Storage and handling follow [data-retention plan / period (to be completed)]."},
  {title:"Risks and benefits",text:"There are no known risks in this study. [Compensation / course-credit statement (to be completed; state if there is none)]. Your participation helps us understand how ordinary users reason about such judgements."},
  {title:"Ethics review and contact",text:"This study has been approved by [ethics review body / approval number (to be completed)]. For questions about the study, contact [researcher name / email (to be completed)]; for questions about your rights as a participant, contact [ethics committee contact (to be completed)]."},
  {title:"Statement of consent",text:"By ticking the box below I confirm that: I have read and understood the information above, I am at least [age threshold, e.g. 18 (to be completed)] years old, I take part voluntarily, and I understand I may withdraw at any time."}],
  agree:"I have read and understood the information above and volunteer to take part.",start:"Agree and begin",decline:"I do not agree / Exit",declined:"Thank you for your time. You have exited; no answers were recorded and you may close this window."}
};
const app={locale:'zh-Hans',packet:null,trials:[],index:0,step:1,phase:'consent',label:'',submission_id:null,started:null,finished:null,attention:null,reflection:{hardest:null,confusing:null,amount:null,pace:null}};
const root=document.querySelector('#app');
const now=()=>Math.max(0,Date.now()-new Date(app.started).getTime());
const uuid=()=>(self.crypto&&crypto.randomUUID)?crypto.randomUUID():'10000000-1000-4000-8000-100000000000'.replace(/[018]/g,c=>(c^Math.random()*16>>c/4).toString(16));
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const loc=()=>DATA.locales[app.locale]; const common=()=>loc().common;
function shell(body){document.documentElement.lang=app.locale;document.querySelector('#fiction-banner').textContent=loc().honesty_notice;root.innerHTML=`<p class="offline-warning">${esc(loc().honesty_notice)}</p>${body}`;window.scrollTo(0,0)}
function renderConsent(){const c=CONSENT_COPY[app.locale];shell(`<section class="panel"><h1>${esc(c.heading)}</h1><label>${app.locale==='zh-Hans'?'参与者编号/昵称（可留空；不要填写真实姓名）':'Participant code/nickname (optional; do not enter your real name)'}<input id="label" maxlength="80"></label><section class="consent">${c.body.map(x=>`<h3>${esc(x.title)}</h3><p>${esc(x.text)}</p>`).join('')}<label class="consent-agree"><input id="agree" type="checkbox"> ${esc(c.agree)}</label></section><div class="actions"><button id="begin" disabled>${esc(c.start)}</button><button id="decline" class="secondary">${esc(c.decline)}</button></div></section>`);document.querySelector('#agree').onchange=e=>document.querySelector('#begin').disabled=!e.target.checked;document.querySelector('#begin').onclick=start;document.querySelector('#decline').onclick=()=>shell(`<section class="panel"><h1>${esc(c.declined)}</h1></section>`)}
function start(){app.label=document.querySelector('#label').value.trim();app.submission_id=uuid();app.started=new Date().toISOString();app.packet=DATA.packets[Math.floor(Math.random()*DATA.packets.length)];app.trials=app.packet.locales[app.locale].map(slot=>({slot_index:slot.slot_index,scene_id:slot.scene_id,variant_id:slot.variant_id,position:slot.position,planned:true,presented:false,step_presented:[],step_selected_option_id:[],step_presented_option_order:[],step_shown_at_relative:[],step_answered_at_relative:[],participant_exit_step:null,participant_derived_state:null,scope_selected_id:null,completion_status:'not_started',materials_version:DATA.materials_version}));app.phase='demo';renderDemo()}
function renderCard(scene){const l=common().labels,c=scene.card;return `<article class="record-card"><h2>${esc(scene.title)}</h2><dl class="record-grid">${[['situation',l.situation],['goal',l.goal],['existing',l.existing],['new_item',l.new_item]].map(([k,n])=>`<div class="record-row"><dt>${esc(n)}</dt><dd>${esc(c[k])}</dd></div>`).join('')}<div class="record-row"><dt>${esc(l.record)}</dt><dd><ul class="fact-list">${c.facts.map(x=>`<li>${esc(x)}</li>`).join('')}</ul></dd></div></dl></article>`}
function renderDemo(){const d=loc().demonstration;let steps=d.worked_steps.map(s=>`<div class="worked-step"><h2>${app.locale==='zh-Hans'?'步骤':'Step'} ${s.step}</h2><p><b>${esc(s.question)}</b></p><ul>${s.options.map(o=>`<li>${esc(o.text)}${o.demonstrated?' ✓':''}</li>`).join('')}</ul><p>${esc(s.why)}</p></div>`).join('');shell(`<section class="panel"><p class="progress">${esc(common().progress.demonstration)}</p>${renderCard(d.scene)}<div class="demonstration-card">${steps}<p><b>${esc(d.destination.label)}</b> — ${esc(d.destination.description)}</p><p>${esc(d.why)}</p><button id="ack">${app.locale==='zh-Hans'?'我已读完示范，开始正式题':'I have read the example; begin formal trials'}</button></div></section>`);document.querySelector('#ack').onclick=beginTrial}
function slot(){return app.packet.locales[app.locale][app.index]} function trial(){return app.trials[app.index]}
function beginTrial(){const t=trial();t.presented=true;t.completion_status='in_progress';app.step=1;presentStep(1);renderTrial()}
function optionsFor(step){if(step===6)return slot().scene.scope_options;return loc().questions[String(step)].options}
function presentStep(step){const t=trial();if(!t.step_presented.includes(step)){t.step_presented.push(step);t.step_presented_option_order.push(optionsFor(step).map(x=>x.id));t.step_shown_at_relative.push(now())}}
function route(path){for(let i=0;i<path.length;i++){const step=i+1,a=path[i];if(step===1){if(a==='INFO')return {done:true,state:'DIAGNOSTIC'};if(a!=='CONTROL')throw Error('invalid step 1')}if(step===2){if(a==='NOT_COMPARED')return {done:true,state:'UNRESOLVED'};if(a!=='COMPARED')throw Error('invalid step 2')}if(step===3){if(a==='NOT_BETTER')return {done:true,state:'WITHHELD'};if(a!=='BETTER')throw Error('invalid step 3')}if(step===4){if(a==='HARM')return {done:true,state:'WITHHELD'};if(a!=='NO_HARM')throw Error('invalid step 4')}if(step===5){if(a==='SCOPE_MISSING')return {done:true,state:'UNRESOLVED'};if(a!=='SCOPE_WRITTEN')throw Error('invalid step 5')}if(step===6)return {done:true,state:'SUPPORTED'}}return {done:false,next:path.length+1,state:null}}
function renderTrial(){const t=trial(),s=slot(),q=loc().questions[String(app.step)],opts=optionsFor(app.step),answered=t.step_selected_option_id.map((a,i)=>`<button class="secondary step-summary" data-revise="${i+1}">${app.locale==='zh-Hans'?'修改':'Revise'} ${i+1}: ${esc(a)}</button>`).join('');shell(`<section class="panel"><p class="progress">${esc(common().progress.formal.replace('{current}',String(app.index+1)))}</p><div class="study-layout"><div class="trial-column">${renderCard(s.scene)}${answered?`<div class="answered-steps">${answered}</div>`:''}<div class="question-card"><div class="question-heading">${app.locale==='zh-Hans'?'步骤':'Step'} ${app.step}</div><fieldset><legend>${esc(q.prompt)}</legend><div class="choice-list">${opts.map(o=>`<label class="choice"><input type="radio" name="answer" value="${esc(o.id)}"><span>${esc(o.text)}</span></label>`).join('')}</div></fieldset><p id="error" class="error"></p><button id="submit">${esc(common().actions.submit)}</button></div></div></div></section>`);document.querySelectorAll('[data-revise]').forEach(b=>b.onclick=()=>revise(Number(b.dataset.revise)));document.querySelector('#submit').onclick=submitAnswer}
function submitAnswer(){const selected=document.querySelector('input[name="answer"]:checked');if(!selected){document.querySelector('#error').textContent=common().actions.choice_required;return}const t=trial();t.step_selected_option_id.push(selected.value);t.step_answered_at_relative.push(now());const routed=route(t.step_selected_option_id);if(routed.done){t.participant_exit_step=app.step;t.participant_derived_state=routed.state;t.scope_selected_id=app.step===6?selected.value:null;t.completion_status='complete';renderResult()}else{app.step=routed.next;presentStep(app.step);renderTrial()}}
function revise(step){const t=trial(),cut=step-1;t.step_presented=t.step_presented.slice(0,cut);t.step_selected_option_id=t.step_selected_option_id.slice(0,cut);t.step_presented_option_order=t.step_presented_option_order.slice(0,cut);t.step_shown_at_relative=t.step_shown_at_relative.slice(0,cut);t.step_answered_at_relative=t.step_answered_at_relative.slice(0,cut);t.participant_exit_step=null;t.participant_derived_state=null;t.scope_selected_id=null;t.completion_status='in_progress';app.step=step;presentStep(step);renderTrial()}
function renderResult(){const t=trial();const states=['SUPPORTED','DIAGNOSTIC','WITHHELD','UNRESOLVED'];const d=common().destinations[states.indexOf(t.participant_derived_state)];shell(`<section class="panel"><p class="progress">${esc(common().progress.formal.replace('{current}',String(app.index+1)))}</p><div class="result-card"><p>${esc(common().labels.result)}</p><p class="result-destination">${esc(d.label)}</p><p>${esc(d.description)}</p><button id="next">${esc(common().actions.continue)}</button><button id="revise-last" class="secondary">${esc(common().actions.back)}</button></div></section>`);document.querySelector('#revise-last').onclick=()=>revise(t.participant_exit_step);document.querySelector('#next').onclick=()=>{app.index++;if(app.index<6)beginTrial();else renderAttention()}}
function renderAttention(){const a=common().attention,q=loc().questions['1'];shell(`<section class="panel"><p class="progress">${esc(common().progress.attention)}</p><h1>${esc(a.heading)}</h1><p>${esc(a.instruction)}</p><fieldset><legend>${esc(q.prompt)}</legend>${q.options.map(o=>`<label class="choice"><input type="radio" name="attention" value="${esc(o.id)}"> ${esc(o.text)}</label>`).join('')}</fieldset><p id="error" class="error"></p><button id="attention-next">${esc(common().actions.continue)}</button></section>`);document.querySelector('#attention-next').onclick=()=>{const x=document.querySelector('input[name="attention"]:checked');if(!x){document.querySelector('#error').textContent=common().actions.choice_required;return}app.attention=x.value;renderReflection()}}
function renderReflection(){const r=common().reflection;const controls=['hardest','confusing','amount','pace'].map(k=>`<label>${esc(r[k])}<select id="r-${k}"><option value=""></option>${r.options[k].map(o=>`<option value="${esc(o.id)}">${esc(o.text)}</option>`).join('')}</select></label>`).join('');shell(`<section class="panel"><p class="progress">${esc(common().progress.reflection)}</p><h1>${esc(r.heading)}</h1><div class="reflection-grid">${controls}</div><button id="finish">${esc(r.submit)}</button></section>`);document.querySelector('#finish').onclick=()=>{Object.keys(app.reflection).forEach(k=>app.reflection[k]=document.querySelector('#r-'+k).value||null);app.finished=new Date().toISOString();renderComplete()}}
function makeExport(){const meta=loc().metadata;return {export_schema:DATA.export_schema,signed:false,submission_id:app.submission_id,honesty_notice:loc().honesty_notice,materials_version:DATA.materials_version,canonical_materials_hash:DATA.canonical_materials_hash,locale_bundle_version:meta.locale_bundle_version,locale_bundle_hash:meta.locale_bundle_hash,ab_invariance_hash:DATA.ab_invariance_hash,selected_locale:app.locale,allocation_cell:app.packet.allocation_cell,sequence_id:app.packet.sequence_id,ab_variant:app.packet.ab_variant,participant_label:app.label,client_started_at:app.started,client_finished_at:app.finished,demonstration_status:'acknowledged',attention_selected_id:app.attention,reflection_choice_ids:app.reflection,completion_status:app.trials.every(t=>t.completion_status==='complete')?'complete':'partial',trials:app.trials}}
function csvSafe(value){let s=value==null?'':(typeof value==='object'?JSON.stringify(value):String(value));if(/^[=+\-@]/.test(s))s="'"+s;return '"'+s.replaceAll('"','""')+'"'}
function makeCsv(){const e=makeExport(),session=['export_schema','signed','submission_id','selected_locale','allocation_cell','sequence_id','ab_variant','participant_label','completion_status'],fields=Object.keys(e.trials[0]),headers=session.concat(fields);const rows=[headers.map(csvSafe).join(',')];for(const t of e.trials)rows.push(headers.map(k=>csvSafe(k in t?t[k]:e[k])).join(','));return '\ufeff'+rows.join('\r\n')+'\r\n'}
function download(name,text,type){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([text],{type}));a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)}
function renderComplete(){const ex=common().export;shell(`<section class="panel"><h1>${esc(ex.heading)}</h1><p>${esc(ex.debrief)}</p><p class="offline-warning">${esc(loc().honesty_notice)}</p><p>${app.locale==='zh-Hans'?'请同时下载 JSON 与 CSV，并按 owner 指示诚实回传。文件未签名，页面不显示成绩。':'Download both JSON and CSV and return them honestly as instructed by the owner. Files are unsigned and no score is shown.'}</p><div class="downloads"><button id="json">${app.locale==='zh-Hans'?'下载未签名 JSON':'Download unsigned JSON'}</button><button id="csv">${app.locale==='zh-Hans'?'下载未签名 CSV':'Download unsigned CSV'}</button></div></section>`);const base=`stepwise-offline-cell-${String(app.packet.allocation_cell+1).padStart(2,'0')}`;document.querySelector('#json').onclick=()=>download(base+'.json',JSON.stringify(makeExport(),null,2)+'\n','application/json');document.querySelector('#csv').onclick=()=>download(base+'.csv',makeCsv(),'text/csv;charset=utf-8')}
document.querySelector('#language-button').onclick=()=>{if(app.started)return;app.locale=app.locale==='zh-Hans'?'en':'zh-Hans';renderConsent()};renderConsent();
</script>
</body>
</html>
'''


def generate(output: Path = DEFAULT_OUTPUT) -> Path:
    payload = build_payload()
    data_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    data_json = data_json.replace("</", "<\\/")
    html = HTML_TEMPLATE.replace("__CSS__", CSS_PATH.read_text(encoding="utf-8")).replace(
        "__DATA__", data_json
    )
    lowered = html.lower()
    leaked = [term for term in PRIVATE_KEY_PARTS if term in lowered]
    if leaked:
        raise ValueError(f"generated HTML contains private key terms: {leaked}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8", newline="\n")
    reread = output.read_text(encoding="utf-8")
    if reread != html:
        raise ValueError("generated HTML read-back mismatch")
    display_path = output.relative_to(ROOT) if output.is_relative_to(ROOT) else output
    print(f"generated {display_path} ({len(html.encode('utf-8'))} bytes); private-key self-check PASS")
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    generate(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
