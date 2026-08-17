# Official Stolfo Latent Positive Control — Stage-1 DEV

- experiment_id: `E-0017b-official-stolfo-latent-positive-control-stage1-dev`
- valid_for_paper: `False`
- official repo commit: `9dac937ef6fc3e483b1efc13863deeb03ec38dbe`
- model: `Qwen/Qwen2.5-7B-Instruct` @ `a09a35458c702b33eeacc393d103063234e8bc28`
- task: IFEval `keywords:existence`, DEV n=`40`
- source layers used: `[26]`; selected layer `26`
- selected α: `2.0`
- baseline compliance: `0.225000`
- prompt compliance: `0.775000`
- steer compliance: `0.225000`
- primary steer-baseline: `0.000000` CI `0.000000, 0.000000`; sanity_pass=`False`
- secondary steer-prompt: `-0.550000` CI `-0.725000, -0.350000`
- coherence: steer g=`0.012482`, baseline g0=`0.012394`, ok=`True`
- best diagnostic any α: layer `26`, α `2.0`, Δ `0.000000`, selectable=`True`

No TEST item was generated or scored.
