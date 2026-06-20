param(
  [ValidateSet("xelatex")]
  [string]$Engine = "xelatex",
  [switch]$WithSpine
)

$ErrorActionPreference = "Stop"
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$CriticalPattern = "Fatal|Emergency|Undefined control sequence|LaTeX Error:|Package .* Error:|Missing \\begin\{document\}|macro parameter character|TeX capacity exceeded|Runaway argument|Missing \$ inserted|Paragraph ended before"

function Invoke-ThesisBuild {
  param(
    [string]$Target,
    [string[]]$LatexmkArgs,
    [string]$LogFile
  )

  Write-Host "Building $Target..."
  & latexmk @LatexmkArgs
  if ($LASTEXITCODE -ne 0) {
    throw "latexmk failed for $Target."
  }

  $matches = Select-String -Path $LogFile -Pattern $CriticalPattern
  if ($matches) {
    $matches | ForEach-Object { Write-Host $_.Line }
    throw "Critical LaTeX log messages found for $Target."
  }
}

Push-Location $Root
try {
  Invoke-ThesisBuild -Target "tez.tex (XeLaTeX)" -LatexmkArgs @("-xelatex", "-interaction=nonstopmode", "tez.tex") -LogFile "tez.log"

  if ($WithSpine) {
    & powershell -ExecutionPolicy Bypass -File ".\sirt-kapak-guncelle.ps1"
    if ($LASTEXITCODE -ne 0) {
      throw "sirt-kapak.tex otomatik guncellenemedi."
    }
    Invoke-ThesisBuild -Target "sirt-kapak.tex" -LatexmkArgs @("-pdf", "-interaction=nonstopmode", "sirt-kapak.tex") -LogFile "sirt-kapak.log"
  }

  Write-Host "Build verification completed."
} finally {
  Pop-Location
}
