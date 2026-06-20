param(
  [ValidateSet("pdf", "xelatex")]
  [string]$Engine = "xelatex",
  [switch]$Build,
  [switch]$WithSpine
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Templates = @(
  "inonu-fbe-tez-sablonu-2025"
)

$failures = 0
foreach ($template in $Templates) {
  $templateRoot = Join-Path $Root $template
  Write-Host ""
  Write-Host "== $template ==" -ForegroundColor White
  Push-Location $templateRoot
  try {
    $args = @("-ExecutionPolicy", "Bypass", "-File", ".\kontrol.ps1", "-Engine", $Engine, "-Report")
    if ($Build) { $args += "-Build" }
    if ($WithSpine) { $args += "-WithSpine" }
    & powershell @args
    if ($LASTEXITCODE -ne 0) { $failures++ }
  } finally {
    Pop-Location
  }
}

if ($failures -gt 0) {
  throw "$failures kontrolde FAIL sonucu var."
}

Write-Host ""
Write-Host "Sablon kontrolu tamamlandi." -ForegroundColor Green
