# C2b Behavioral Reachability Pilot — EXPLORATORY (protocol NOT frozen)

- model: `Qwen/Qwen2.5-7B-Instruct`
- alphas: [4.0, 8.0, 16.0]   n_strong: 16   max_new_tokens: 128
- valid_for_paper: **False**
- prompt ceiling definition: prompt ceiling = best-of-16 static authored prompts, NOT OPRO — an UNDER-estimate of true prompt reach (conservative for the C2b comparison)
- Behavior measured by CRUDE lexical proxies (experiments.behavior), NOT validated instruments. EXPLORATORY — no frozen verdict.

> **HONESTY CAVEAT (audit):** C2b uses crude lexical/length proxies that share a basis with the steering direction; these numbers are an EXPLORATORY lexical-shift signal ONLY and CANNOT support a 'latent reaches beyond the bounded-prompt ceiling' claim without an orthogonal non-lexical proxy + variance estimate. focus/deliberation are length-confounded; focus is untrustworthy. Single greedy sample per cell — do not over-read small margins.

## Does latent steering reach behavior BEYOND the bounded prompt ceiling?

| axis | layer | prompt ceiling | steer-only max | beyond? | margin | unstable layer? | conflict winner (max α) |
|---|---|---|---|---|---|---|---|
| deliberation | 20 | 1.000 | 0.105 | no | -0.895 | ok | prompt |
| skepticism | 20 | 0.982 | 0.500 | no | -0.482 | ok | prompt |
| uncertainty_awareness | 20 | 0.881 | 0.500 | no | -0.381 | ok | latent |
| focus | 16 | 0.965 | 0.975 | YES | +0.010 | ok | prompt |

- axes where steer reaches beyond the prompt ceiling: 1/4 (headline EXCLUDES 0 axis/axes on an unstable C1 layer; 4 axes total)
- 'axes where steer reaches beyond ceiling' EXCLUDES axes with c2b_on_unstable_layer=true (unstable/unconfirmed C1 layer); those axes are still recorded but never counted in the headline.

## Conflict landings (prompt UP vs latent steer DOWN)

| axis | α | prompt pole | steer pole | behavior | landing (raw) | winner |
|---|---|---|---|---|---|---|
| deliberation | 4.0 | 1.000 | 0.105 | 1.000 | -0.000 | prompt |
| deliberation | 8.0 | 1.000 | 0.095 | 1.000 | -0.000 | prompt |
| deliberation | 16.0 | 1.000 | 0.055 | 0.533 | 0.494 | prompt |
| skepticism | 4.0 | 0.982 | 0.500 | 0.818 | 0.341 | prompt |
| skepticism | 8.0 | 0.982 | 0.500 | 0.924 | 0.120 | prompt |
| skepticism | 16.0 | 0.982 | 0.500 | 0.818 | 0.341 | prompt |
| uncertainty_awareness | 4.0 | 0.881 | 0.500 | 0.500 | 1.000 | latent |
| uncertainty_awareness | 8.0 | 0.881 | 0.500 | 0.269 | 1.607 | latent |
| uncertainty_awareness | 16.0 | 0.881 | 0.500 | 0.378 | 1.322 | latent |
| focus | 4.0 | 0.965 | 0.895 | 0.950 | 0.214 | prompt |
| focus | 8.0 | 0.965 | 0.895 | 0.945 | 0.286 | prompt |
| focus | 16.0 | 0.965 | 0.815 | 0.945 | 0.133 | prompt |
