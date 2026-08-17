# Official Stolfo Latent Positive Control — Stage-1 DEV

- experiment_id: `E-0017b-official-stolfo-latent-positive-control-stage1-dev`
- valid_for_paper: `False`
- official repo commit: `9dac937ef6fc3e483b1efc13863deeb03ec38dbe`
- model: `phi-3` @ `f39ac1d28e925b323eae81227eaba4464caced4e`
- task: IFEval `keywords:existence`, DEV n=`40`
- source layers used: `[24, 26, 28]`; selected layer `26`
- selected α: `100.0`
- baseline compliance: `0.150000`
- prompt compliance: `0.450000`
- steer compliance: `0.250000`
- primary steer-baseline: `0.100000` CI `0.000000, 0.225000`; sanity_pass=`True`
- secondary steer-prompt: `-0.200000` CI `-0.400000, 0.000000`
- coherence: steer g=`0.000000`, baseline g0=`0.000000`, ok=`True`
- best any weight: layer `26`, α `100.0`, Δ `0.100000`, selectable=`True`

No TEST item was generated or scored.
