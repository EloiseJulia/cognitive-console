param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

$PaperDir = $PSScriptRoot
$BuildDir = Join-Path $PaperDir "build"
$MainTex = Join-Path $PaperDir "main.tex"

function Resolve-Executable {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [string[]]$ExtraPaths = @()
    )

    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }

    foreach ($path in $ExtraPaths) {
        if ($path -and (Test-Path $path)) {
            return $path
        }
    }

    return $null
}

$MiKTeXBin = Join-Path $env:LOCALAPPDATA "Programs\MiKTeX\miktex\bin\x64"
$Pdflatex = Resolve-Executable "pdflatex.exe" @(
    (Join-Path $MiKTeXBin "pdflatex.exe"),
    (Join-Path $env:ProgramFiles "MiKTeX\miktex\bin\x64\pdflatex.exe")
)
$Bibtex = Resolve-Executable "bibtex.exe" @(
    (Join-Path $MiKTeXBin "bibtex.exe"),
    (Join-Path $env:ProgramFiles "MiKTeX\miktex\bin\x64\bibtex.exe")
)
$Initexmf = Resolve-Executable "initexmf.exe" @(
    (Join-Path $MiKTeXBin "initexmf.exe"),
    (Join-Path $env:ProgramFiles "MiKTeX\miktex\bin\x64\initexmf.exe")
)
$Tectonic = Resolve-Executable "tectonic.exe" @(
    (Join-Path $PaperDir "..\..\tools\tectonic.exe")
)

if ($Clean -and (Test-Path $BuildDir)) {
    Remove-Item -Recurse -Force $BuildDir
}
New-Item -ItemType Directory -Force -Path $BuildDir | Out-Null

if ($Pdflatex -and $Bibtex) {
    if ($Initexmf) {
        & $Initexmf --set-config-value "[MPM]AutoInstall=1" | Out-Null
    }

    Push-Location $PaperDir
    try {
        & $Pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -output-directory="$BuildDir" "main.tex"
        & $Bibtex (Join-Path "build" "main")
        & $Pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -output-directory="$BuildDir" "main.tex"
        & $Pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -output-directory="$BuildDir" "main.tex"
    }
    finally {
        Pop-Location
    }
}
elseif ($Tectonic) {
    & $Tectonic --outdir "$BuildDir" "$MainTex"
}
else {
    throw "No supported LaTeX engine found. Install MiKTeX (pdflatex+bibtex) or place tectonic.exe at tools\tectonic.exe."
}

$Pdf = Join-Path $BuildDir "main.pdf"
if (!(Test-Path $Pdf)) {
    throw "Expected PDF was not produced: $Pdf"
}

Write-Host "Wrote $Pdf"
