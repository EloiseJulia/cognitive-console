$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$pandoc = Get-Command pandoc -ErrorAction SilentlyContinue
if (-not $pandoc) {
    $localPandoc = Join-Path $env:LOCALAPPDATA 'Pandoc\pandoc.exe'
    if (-not (Test-Path $localPandoc)) {
        throw 'Pandoc was not found on PATH or under LOCALAPPDATA\Pandoc.'
    }
    $pandocPath = $localPandoc
} else {
    $pandocPath = $pandoc.Source
}

$texbin = Join-Path $env:LOCALAPPDATA 'Programs\MiKTeX\miktex\bin\x64'
$pdflatex = Join-Path $texbin 'pdflatex.exe'
$bibtex = Join-Path $texbin 'bibtex.exe'
if (-not (Test-Path $pdflatex) -or -not (Test-Path $bibtex)) {
    throw 'MiKTeX pdflatex/bibtex were not found in the expected local installation.'
}

& $pandocPath (Join-Path $root 'pipeline\CONDITIONAL_PAPER.md') `
    '--from=markdown+raw_html+raw_tex+tex_math_dollars' `
    '--to=latex' `
    "--lua-filter=$(Join-Path $root 'pipeline\conditional_to_latex.lua')" `
    "--template=$(Join-Path $root 'pipeline\iui_conditional.template.tex')" `
    '--wrap=preserve' `
    '-o' (Join-Path $root 'reframed.tex')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Push-Location $root
try {
    & $pdflatex '--enable-installer' '--interaction=nonstopmode' '--halt-on-error' 'reframed.tex'
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $bibtex 'reframed'
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $pdflatex '--enable-installer' '--interaction=nonstopmode' '--halt-on-error' 'reframed.tex'
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $pdflatex '--enable-installer' '--interaction=nonstopmode' '--halt-on-error' 'reframed.tex'
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
