# RUN_ON_A800.md — pure-compute Phase-0 run on a borrowed A800 (D-0020)

This is a **step-by-step operator runbook** for a borrowed A800 SSH session. The
code is already implemented and CPU-smoke-tested; the A800 session is **pure
compute** — do NOT debug here. Total disk stays **< 70 GB** (hard ceiling) and
**everything is deleted afterwards** (models, caches, venv, clone) keeping only
the small results.

**Expected disk:** ~15 GB for the Qwen2.5-7B-Instruct weights + a few GB for the
venv/torch-CUDA → **~25 GB total for one model**, well under the 70 GB ceiling.
The runner's disk guard measures `HF_HOME` + venv at several points — before the
run, **after the model is loaded/downloaded (between C1 and C2b)**, and after
C2b — and **aborts (raises `DiskBudgetError`, non-zero exit) if the measured
footprint is at/over the ceiling** at those checkpoints. It cannot interrupt a
single download mid-stream, but it stops the run before the next expensive step
once the footprint crosses the budget.

**Expected wall-clock (A800, 7B, fp16):** roughly **10–25 min** for C1 (a few
forward passes/axis over ~40 pairs + 16 strong + 10 neutral prompts × 4 axes) +
**5–15 min** for C2b (a handful of short generations/axis). Budget **≤ 1 GPU-hour**
including the ~5 min model download. Times are honest estimates; the runner
records true wall-clock.

---

## 0. Prereqs on the box
```bash
nvidia-smi        # note the CUDA version → pick the matching torch wheel below
python3 --version # need >= 3.10
```

## 1. Clone the repo (repo is ~1 MB; models download fresh on the box)
```bash
cd /scratch                       # or any large scratch partition
git clone https://github.com/EloiseJulia/cognitive-console.git
cd cognitive-console
git checkout feature/5-gpu-c1-c2b # or main once merged
```

## 2. Create a venv
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

## 3. Install torch (CUDA build matching the A800), then the rest
Pick the `cuXXX` index that matches `nvidia-smi` (e.g. cu121 for CUDA 12.1):
```bash
pip install torch --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements-gpu.txt
pip install -e .                  # installs the cognitive_console package
```

## 4. Point HF_HOME at scratch (so all downloads land in the delete-after dir)
```bash
export HF_HOME=/scratch/hf_home
mkdir -p "$HF_HOME"
```

## 5. Download the model (Qwen2.5-7B-Instruct, Apache-2.0, ungated, ~15 GB)
```bash
huggingface-cli download Qwen/Qwen2.5-7B-Instruct --exclude "*.gguf"
```
(Optional — the runner will download it automatically on first use if you skip this.)

## 6. Run the unified Phase-0 runner (C1 facade + C2b reachability)
```bash
python scripts/run_gpu_phase0.py \
  --model Qwen/Qwen2.5-7B-Instruct \
  --hf-home "$HF_HOME" \
  --venv "$PWD/.venv" \
  --disk-budget-gb 60 --disk-ceiling-gb 70
```
This writes `results/gpu_7b_<date>/` containing:
- `c1/`  — C1 facade JSON + summary + registry + manifest
- `c2b/` — C2b reachability JSON + summary + registry + manifest
- `run_summary.json` — combined EXPLORATORY summary + honest wall-clock + disk.

The prompt ceiling uses the **FULL authored strong-prompt set** (default
`--n-strong 16` = all 16 static prompts/axis in `data/strongest_prompts/*.jsonl`;
best-of these, **NOT OPRO** — a conservative UNDER-estimate of true prompt reach).

The runner **disk-guards** `HF_HOME` + venv before the run, again **after the
model is loaded (between C1 and C2b)**, and after C2b; at the post-load and
post-run checkpoints it **aborts with a non-zero exit if the footprint is at/over
the 70 GB ceiling**. All outputs are `valid_for_paper=false`, protocol NOT frozen.

## 7. Copy the (small) results back to your machine
From your LOCAL machine:
```bash
scp -r <user>@<a800-host>:/scratch/cognitive-console/results/gpu_7b_<date> ./
```
(Only the KB-sized JSON/markdown/registry come back — never the model weights.)

---

## 8. CLEANUP (delete EVERYTHING except the results you already copied)
Run this on the A800 **after** step 7 confirms the results are safely on your machine:
```bash
# 1. deactivate + remove the venv
deactivate 2>/dev/null || true

# 2. delete the HuggingFace cache (the ~15 GB of weights)
rm -rf "$HF_HOME"

# 3. delete the clone (venv + code + local results copy)
cd /scratch
rm -rf /scratch/cognitive-console

# 4. verify nothing large is left behind
du -sh /scratch/hf_home /scratch/cognitive-console 2>/dev/null || echo "clean"
df -h /scratch
```
After cleanup the borrowed box holds **none** of our models, caches, venv, or
clone — only the small results now live on your machine.

---

## 9. C2b QUALIFIED ADJUDICATION (FROZEN prereg §4/§5) — separate A800 run

This is the **qualified** C2b behavioral-gap adjudication, run against the FROZEN
pre-registration `docs/ledgers/prereg-c2b-adjudication.md` (§4 decision rule, §5
parameters). It is a **separate, later** run from the exploratory Phase-0 pilot
above. The criteria are LOCKED — do not pass overriding thresholds.

**Frozen parameters (do NOT change):** δ=0.05; N = deliberation 60 / skepticism 60
/ uncertainty 80; k=5 samples/item; α grid {2,4,6,8,12,16,24}; DEV≈1/3 selects+freezes
the best-of-16 prompt AND α; TEST≈2/3 adjudicates; paired ITEM-cluster bootstrap
B≥10000; per-axis CI at 1−0.05/3 (Bonferroni); coherence ≤1.5× baseline; three-tier
verdict (≥2 pass STRONG_GO / 1 CONDITIONAL_GO+replication / 0 KILL_PLAN_D).

### 9a. CPU / 1.5B smoke (offline, do this BEFORE the A800)
```bash
# (i) OFFLINE no-torch pipeline smoke — runs the WHOLE adjudication on the bundled
#     fixtures with a synthetic backend and emits a real verdict artifact:
python scripts/run_c2b_adjudication.py --backend synthetic --bootstrap-b 10000
# (ii) real-model generation smoke on the cached Qwen2.5-1.5B (CPU is slow; small B):
python scripts/run_c2b_adjudication.py --backend hf --model Qwen/Qwen2.5-1.5B-Instruct \
  --use-fixture --n-items 4 --bootstrap-b 2000
```

### 9b. The real 7B adjudication on the A800
Do steps 0–5 above (venv, torch-CUDA, `pip install -e .`, `HF_HOME`, model download),
then run the **real** task sets (drop `--use-fixture`; the real loaders download the
frozen GSM8K test split etc.) at the full frozen bootstrap:
```bash
python scripts/run_c2b_adjudication.py \
  --backend hf --model Qwen/Qwen2.5-7B-Instruct \
  --bootstrap-b 10000 --seed 20260723 \
  --hf-home "$HF_HOME" --venv "$PWD/.venv" \
  --disk-budget-gb 60 --disk-ceiling-gb 70
```
This re-derives the **C1 chosen non-degenerate layer per axis on THIS model** (never
hardcoded) + the CAA unit direction there, disk-guards `HF_HOME`+venv (pre-run, after
the model loads, after the run), writes
`results/c2b_adjudication_hf_<date>/` with `c2b_adjudication_results.json`, a human
`c2b_adjudication_summary.md` (verdict table), a registry row and an artifact
manifest, and prints the **verdict**.

**Data-license gate (AGENTS.md §5):** the real skepticism/uncertainty loaders are
`NotImplementedError` stubs with a documented assembly recipe — building/redistributing
those sets must clear the human data-license gate BEFORE the A800 run. GSM8K (MIT) is
clear. Until the gate clears, run those two axes on `--use-fixture` or authored items.

**Expected wall-clock (A800, 7B, fp16):** dominated by generation:
N_items × k(5) × ~5 cells/axis (best-prompt + α-grid on DEV, prompt+steer+baseline+conflict
on TEST) × 3 axes, ~64–256 new tokens each. Rough estimate **~1.5–3 GPU-hours** for the
full 60/60/80-item run at k=5 (the bootstrap itself is CPU-cheap, seconds). The runner
records the true wall-clock. Budget ≤ 1 GPU-hour if you cap `--n-items`/`--max-new-tokens`
for a reduced pilot (mark it as such — a reduced N is NOT the frozen N).

**EXPLORATORY until this A800 run:** every synthetic/1.5B/CPU run is `valid_for_paper=false`.
The 7B run is the confirmatory adjudication against the frozen criteria; a CONDITIONAL_GO
triggers the pre-registered single-axis REPLICATION (new DEV/TEST draw, new seed) before
any scope-narrowed claim.
