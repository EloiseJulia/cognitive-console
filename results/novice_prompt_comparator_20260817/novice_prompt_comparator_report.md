# Simulated-Novice Prompt Comparator Report

**valid_for_paper=false**; **anchor calibration gate NOT passed**; exploratory bridge only.

- aggregate_commit: `d20090876ec5227a5a3666747abe7240dcf58428`
- experiment group: `NOVICE-PROMPT-COMPARATOR-20260817-FROZEN`
- seeds: prompt_generation `20260817`; comparator `20260723`
- model/revision: `Qwen/Qwen2.5-7B-Instruct` / `a09a35458c702b33eeacc393d103063234e8bc28`
- runtime_prompt_set_sha256: `sha256:ff45994261c785e51a122c272bd1650bf76d52b8770917d6f7df89426e24c126`
- local_checkout_prompt_set_sha256: `sha256:4526a2980f14de6fe22279e16ec2cad7b7d0e1cb6de4ff3ffddebc62501a1cbf`
- fewshot_sha256: `sha256:6790d2cce463b534e4de8e067a147eb5b5b39833007088c58b30a4b68e1849bd`
- comparator GPU-hours (cell wall sum): `2.7503`
- GPU cards: GPU1 for CAA deliberation/skepticism; GPU0 for CAA uncertainty and all ITI cells after GPU1 became occupied by a pre-existing worker.

## Corpus/license gate

Selected corpus: `OpenAssistant/oasst1`; license `Apache-2.0`; URL https://huggingface.co/datasets/OpenAssistant/oasst1. Apache-2.0 license grants reproduction, derivative works, public display, sublicense, and distribution; no Johnny/CC BY-NC examples used.

## Cell results

| method | axis | experiment_id | run code_commit | Δ steer−novice | 98.33% CI | coherence | status | format compliance | novice−best analogue | GPU-h |
|---|---|---|---|---:|---|---|---|---:|---:|---:|
| caa | deliberation | `novice-prompt-comparator-58951ae9-0001` | `af1a6680` | +0.0081 | [-0.0642, +0.0684] | true | no | 1.0000 | +0.0069 | 0.7811 |
| caa | skepticism | `novice-prompt-comparator-3da9a9b9-0001` | `89cf1b3f` | -0.0000 | [-0.0784, +0.0659] | true | no | 1.0000 | -0.0800 | 0.3278 |
| caa | uncertainty_awareness | `novice-prompt-comparator-9eb1a5a7-0001` | `77e900a2` | -0.0151 | [-0.0777, +0.0477] | true | no | 0.9983 | -0.2126 | 0.2566 |
| iti | deliberation | `novice-prompt-comparator-1f352dc2-0001` | `f56399ab` | -0.4569 | [-0.5679, -0.3495] | false | invalid/coherence_failed | 1.0000 | +0.0069 | 0.7648 |
| iti | skepticism | `novice-prompt-comparator-26e04e8d-0001` | `97dd573c` | -0.0200 | [-0.1327, +0.0752] | true | no | 1.0000 | -0.0800 | 0.3507 |
| iti | uncertainty_awareness | `novice-prompt-comparator-8b5a5d58-0001` | `33a00c6e` | +0.1098 | [+0.0067, +0.2147] | true | PASS | 0.9983 | -0.2126 | 0.2693 |

Coherence-failed cells are marked `invalid/coherence_failed` and must not be interpreted as real behavioral harm.

## Few-shot examples used verbatim

- `91a934ba-cfb8-4ca9-84d0-232b43ad13ab`: Can you explain contrastive learning in machine learning in simple terms for someone new to the field of ML?
- `345ef82e-70f1-4824-9d73-db2ce00573a7`: I didn't understand how pulling and pushing works. What are we pulling or pushing? And how does it work in terms of code or maths?
- `18705268-f16a-48f6-a007-82b7c5e4c17a`: Can you clarify the analogy? I'm not following the notation or vocabulary used in the example.
- `7cce4047-8f87-42c4-9d75-a590c02be5b1`: I want to start doing astrophotography as a hobby, any suggestions what could i do?
- `816f3b2a-932a-4b7f-9d18-c76946d2e097`: Can you tell me more?  What would you recommend as a basic set of equipment to get started with?  How much will it cost?
- `e6f29f10-0859-4201-98e2-5ab02422e476`: my brother looked over my shoulder and saw this conversation. could you explain this conversation to someone with no prior knowledge of the subject
- `6d2b7e04-b0d2-4d12-9a32-2a1fe0e0bb94`: What are some potential simulations that I could run?
- `0816f92a-077f-4521-acf9-563cea553ad5`: Uhh, could you please properly format the code within a code block? Also enable python syntax highlighting.  Additionally, provide an example where this could be useful.

## Generated novice prompts used verbatim

### deliberation

- `novice-deliberation-01` (seed 20260818): Please slow down and walk me through the solution step-by-step before giving the final answer.
- `novice-deliberation-02` (seed 20260819): Please take your time to walk me through the steps and double-check the calculations before giving me the final answer.
- `novice-deliberation-03` (seed 20260820): Please break it down step by step and double-check the calculations before giving the final answer.
- `novice-deliberation-04` (seed 20260821): Please go slow and check my work carefully. Can you also give me the final numeric answer?
- `novice-deliberation-05` (seed 20260822): Please walk me through the steps slowly and double-check the calculations before giving me the final answer.
- `novice-deliberation-06` (seed 20260823): Please take your time to explain each step clearly and double-check the calculations before giving me the final answer.
- `novice-deliberation-07` (seed 20260824): Please slow down and walk me through the steps to make sure I understand before giving the final answer.
- `novice-deliberation-08` (seed 20260825): Can you walk me through this step-by-step and make sure I understand each part before moving on? I'd also like the final numeric answer if possible.
- `novice-deliberation-09` (seed 20260826): Can you walk me through this step-by-step and make sure I understand each part before we move on? I'd also like the final numeric answer if possible.
- `novice-deliberation-10` (seed 20260827 duplicate_of_prior=true): Please slow down and walk me through the solution step-by-step before giving the final answer.
- `novice-deliberation-11` (seed 20260828): Can you walk me through this step by step and make sure I understand each part before we move on?
- `novice-deliberation-12` (seed 20260829): Can you walk me through this step by step and make sure I understand each part before moving on? Also, please provide the final numeric answer at the end.
- `novice-deliberation-13` (seed 20260830): Please go step-by-step and double-check your work before giving the final answer.
- `novice-deliberation-14` (seed 20260831): Please walk me through the solution step-by-step and double-check the calculations before giving the final answer.
- `novice-deliberation-15` (seed 20260832): Can you walk me through this step-by-step and make sure I understand each part before moving on? Also, can you provide the final numeric answer at the end?
- `novice-deliberation-16` (seed 20260833 duplicate_of_prior=true): Please break it down step by step and double-check the calculations before giving the final answer.

### skepticism

- `novice-skepticism-01` (seed 20261818): Please make sure the answer is based on solid facts and not just a guess.
- `novice-skepticism-02` (seed 20261819): Please ensure the answer is well-supported and doesn't stretch the facts.
- `novice-skepticism-03` (seed 20261820): Please make sure the answer is well-supported and doesn't stretch the facts.
- `novice-skepticism-04` (seed 20261821): Please make sure the answer is well-supported and doesn't stretch the facts before choosing.
- `novice-skepticism-05` (seed 20261822): Please make sure the answer is based on solid facts and reasoning before selecting it.
- `novice-skepticism-06` (seed 20261823 duplicate_of_prior=true): Please ensure the answer is well-supported and doesn't stretch the facts.
- `novice-skepticism-07` (seed 20261824): Please ensure the answers are well-supported and avoid assumptions.
- `novice-skepticism-08` (seed 20261825): Please make sure the answer is well-supported and doesn't stretch the facts too much.
- `novice-skepticism-09` (seed 20261826): Please ensure each answer is solid and well-founded before choosing one.
- `novice-skepticism-10` (seed 20261827): Please ensure the answers are well-supported and not based on shaky assumptions.
- `novice-skepticism-11` (seed 20261828): Please make sure the answer is well-supported and logically sound before selecting it.
- `novice-skepticism-12` (seed 20261829): Please make sure the answer is based on solid facts before choosing.
- `novice-skepticism-13` (seed 20261830): Please make sure the answer is logically sound before choosing.
- `novice-skepticism-14` (seed 20261831 duplicate_of_prior=true): Please ensure the answer is well-supported and doesn't stretch the facts.
- `novice-skepticism-15` (seed 20261832 duplicate_of_prior=true): Please make sure the answer is well-supported and logically sound before selecting it.
- `novice-skepticism-16` (seed 20261833): Please choose the most accurate and well-supported answer.

### uncertainty_awareness

- `novice-uncertainty_awareness-01` (seed 20262818): I'm not very familiar with this topic, so could you please explain it in simple terms and give me an idea of how confident you are about your answer? 70%
- `novice-uncertainty_awareness-02` (seed 20262819): I'm not very familiar with this topic, so could you explain it in simple terms? 20%
- `novice-uncertainty_awareness-03` (seed 20262820): I'm not very sure about this topic, could you give me a clear explanation? 80%
- `novice-uncertainty_awareness-04` (seed 20262821): Could you please explain it in simpler terms and include your confidence level in the answer? 80%
- `novice-uncertainty_awareness-05` (seed 20262822): I'm not very familiar with this topic, so could you explain it in simple terms and give me an idea of how confident you are in your answer? 70%
- `novice-uncertainty_awareness-06` (seed 20262823): Can you make sure to include how sure you are about your answer? I'm not very familiar with this topic, so an estimate of how confident you are would be really helpful. 70%
- `novice-uncertainty_awareness-07` (seed 20262824): Could you give me an honest idea of how sure you are about your answer? Like, what percent chance do you have that you got it right?
- `novice-uncertainty_awareness-08` (seed 20262825): Can you give me a clear explanation and maybe a simple example? I'm not very familiar with the topic, so keeping it straightforward would be great. 70% confident.
- `novice-uncertainty_awareness-09` (seed 20262826): I'm not very familiar with this topic, so could you give me a straightforward explanation and a confidence level of about 70%?
- `novice-uncertainty_awareness-10` (seed 20262827): I'm not very familiar with this topic and would appreciate a straightforward explanation. My understanding is about 70%.
- `novice-uncertainty_awareness-11` (seed 20262828): I'm not very familiar with this topic and would appreciate a straightforward explanation. My understanding is about 70% sure.
- `novice-uncertainty_awareness-12` (seed 20262829): I'm not very familiar with this topic, so could you explain it in simple terms and include your confidence level? 50%
- `novice-uncertainty_awareness-13` (seed 20262830): Can you explain this in simpler terms and give me an idea of how sure you are about your answer? 80% confident.
- `novice-uncertainty_awareness-14` (seed 20262831): Can you explain this in simpler terms and give me an idea of how sure you are about your answer? 70% confident.
- `novice-uncertainty_awareness-15` (seed 20262832): I'm not very familiar with this topic and would appreciate a clear explanation with simple terms. My understanding is about 70%.
- `novice-uncertainty_awareness-16` (seed 20262833): Can you explain this in simpler terms and give me an idea of how sure you are about your answer? 70% confident

## Hard caveat

These prompts are AI-generated novice-style prompts. They are not calibrated against real novice prompts and cannot enter Abstract/Contributions as confirmatory evidence.
