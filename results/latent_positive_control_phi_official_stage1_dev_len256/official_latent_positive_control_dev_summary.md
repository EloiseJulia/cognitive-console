# Official Stolfo Latent Positive Control — Stage-1 DEV

- experiment_id: `E-0017e-phi3-official-stolfo-positive-control-stage1-dev-length-rerun`
- valid_for_paper: `False`
- official repo commit: `9dac937ef6fc3e483b1efc13863deeb03ec38dbe`
- model: `phi-3` @ `f39ac1d28e925b323eae81227eaba4464caced4e`
- task: IFEval `keywords:existence`, DEV n=`40`
- max generation length: `256`
- source layers used: `[24, 26, 28]`; selected layer `28`
- selected α: `80.0`
- baseline compliance: `0.275000`
- prompt compliance: `0.875000`
- steer compliance: `0.650000`
- primary steer-baseline: `0.375000` CI `0.175000, 0.575000`; sanity_pass=`True`
- secondary steer-prompt: `-0.225000` CI `-0.400000, -0.050000`
- coherence: steer g=`0.033661`, baseline g0=`0.028536`, ok=`True`
- truncation: baseline `0.700000`, prompt `0.675000`, steer `0.725000`
- mean generated tokens: baseline `208.50`, prompt `202.57`, steer `207.95`
- best any weight: layer `28`, α `100.0`, Δ `0.400000`, selectable=`True`

No TEST item was generated or scored.
