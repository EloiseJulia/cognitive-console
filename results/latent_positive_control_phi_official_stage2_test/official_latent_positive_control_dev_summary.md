# Official Stolfo Latent Positive Control — Stage-2 TEST

- experiment_id: `E-0017f-phi3-official-stolfo-positive-control-stage2-test-once`
- valid_for_paper: `False`
- official repo commit: `9dac937ef6fc3e483b1efc13863deeb03ec38dbe`
- model: `phi-3` @ `f39ac1d28e925b323eae81227eaba4464caced4e`
- task: IFEval `keywords:existence`, TEST n=`45`
- max generation length: `1024`
- source layers used: `[28]`; selected layer `28`
- selected α: `80.0`
- baseline compliance: `0.200000`
- prompt compliance: `0.866667`
- steer compliance: `0.422222`
- primary steer-baseline: `0.222222` CI `0.088889, 0.377778`; sanity_pass=`True`
- secondary steer-prompt: `-0.444444` CI `-0.644444, -0.244444`
- coherence: steer g=`0.102290`, baseline g0=`0.061064`, ok=`True`
- truncation: baseline `0.044444`, prompt `0.000000`, steer `0.066667`
- mean generated tokens: baseline `327.40`, prompt `332.07`, steer `372.76`
- best any weight: layer `28`, α `80.0`, Δ `0.222222`, selectable=`True`

- Stage-2 verdict: `PASS`
