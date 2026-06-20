param(
  [ValidateSet("pdf", "xelatex")]
  [string]$Engine = "xelatex",
  [switch]$WithSpine
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Templates = @(
  "inonu-fbe-tez-sablonu-2025"
)

foreach ($template in $Templates) {
  $templateRoot = Join-Path $Root $template
  Write-Host ""
  Write-Host "== $template teslim paketi ==" -ForegroundColor White
  Push-Location $templateRoot
  try {
    $args = @("-ExecutionPolicy", "Bypass", "-File", ".\teslim-hazirla.ps1", "-Engine", $Engine)
    if ($WithSpine) { $args += "-WithSpine" }
    & powershell @args
    if ($LASTEXITCODE -ne 0) {
      throw "$template icin teslim paketi olusturulamadi."
    }
    & powershell -ExecutionPolicy Bypass -File ".\temizle.ps1"
  } finally {
    Pop-Location
  }
}

Write-Host ""
Write-Host "Teslim paketi hazirlandi." -ForegroundColor Green
