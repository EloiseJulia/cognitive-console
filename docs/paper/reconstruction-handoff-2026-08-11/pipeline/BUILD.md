# Build `reframed.tex`

Run from the parent workspace (`when consensus`):

```powershell
Copy-Item "new paper folder\CC references - Copy.bib" `
  "new paper folder\reframed-references.bib" -Force

pandoc "new paper folder\pipeline\CONDITIONAL_PAPER.md" `
  --from=markdown+raw_html+raw_tex+tex_math_dollars `
  --to=latex `
  --lua-filter="new paper folder\pipeline\conditional_to_latex.lua" `
  --template="new paper folder\pipeline\iui_conditional.template.tex" `
  --wrap=preserve `
  -o "new paper folder\reframed.tex"
```

Compile from `new paper folder`:

```powershell
$texbin = "$env:LOCALAPPDATA\Programs\MiKTeX\miktex\bin\x64"
$env:PATH = "$texbin;$env:PATH"

pdflatex --enable-installer --interaction=nonstopmode --halt-on-error reframed.tex
bibtex reframed
pdflatex --enable-installer --interaction=nonstopmode --halt-on-error reframed.tex
pdflatex --enable-installer --interaction=nonstopmode --halt-on-error reframed.tex
```

## Current Draft State

- `reframed.tex` is generated; edit `pipeline/CONDITIONAL_PAPER.md`, not the generated TeX body.
- Conditional Title/Abstract are in `pipeline/iui_conditional.template.tex` and must be rewritten after pending-study branch integration.
- Missing implementation facts remain explicit in Method prose and `CONDITIONAL_ASSEMBLY_AUDIT.md`; the rendered draft contains no red gap markers.
- Human and prompt+steer result sections intentionally contain no result.
- Final clean build on 2026-08-11: 16 pages, 5 labeled equations, 1 TikZ flow figure, 5 evidence tables, 1 generated calibration figure, and 2 substantive appendices; no undefined references, overfull boxes, or substantive LaTeX warnings.
- Current citation baseline: 26 unique cited keys, 0 missing from the 39-entry bibliography. The restored Mishra, Heyman, and Sprejer citations are used only to bound internal non-surjectivity, trained-method, and capability--behavior interpretations. Several checks are explicitly abstract/page-level, and broader literature search remains incomplete. `lee2004trust` and `schemmer2023appropriate` remain checked bibliography candidates but are not cited.
