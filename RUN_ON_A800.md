# RUN_ON_A800.md — pure-compute Phase-0 run on a borrowed A800 (D-0020)

This is a **step-by-step operator runbook** for a borrowed A800 SSH session. The
code is already implemented and CPU-smoke-tested; the A800 session is **pure
compute** — do NOT debug here. Total disk stays **< 70 GB** (hard ceiling) and
**everything is deleted afterwards** (models, caches, venv, clone) keeping only
the small results.

**Expected disk:** ~15 GB for the Qwen2.5-7B-Instruct weights + a few GB for the
venv/torch-CUDA → **~25 GB total for one model**, well under the 70 GB ceiling.
The runner's disk guard aborts before crossing 70 GB regardless.

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

The runner **disk-guards** `HF_HOME` + venv before and after and **aborts before
exceeding 70 GB**. All outputs are `valid_for_paper=false`, protocol NOT frozen.

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
