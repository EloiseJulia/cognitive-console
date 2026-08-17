# Latent Positive Control — Stage-1 DEV Summary

- experiment_id: `E-0017-latent-behavioral-positive-control-stage1-dev`
- valid_for_paper: `False`
- model: `Qwen/Qwen2.5-7B-Instruct` @ `a09a35458c702b33eeacc393d103063234e8bc28`
- keyword verifier: whole-word `blue` inclusion
- selected source_layer_idx: `5` (HF hidden-state layer `6`)
- selected alpha: `2.0`
- baseline DEV compliance: `0.000000`
- prompt DEV compliance: `0.666667`
- steer DEV compliance: `0.000000`
- primary DEV steer-baseline: `0.000000` CI `0.000000, 0.000000`; sanity_pass=`False`
- secondary DEV steer-prompt: `-0.666667` CI `-0.916667, -0.333333`
- coherence: steer g=`0.000000`, baseline g0=`0.001701`, ok=`True`

No TEST item was generated or scored in this Stage-1 run.
