param(
  [ValidateSet("xelatex")]
  [string]$Engine = "xelatex",
  [switch]$WithSpine
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$PackageRoot = Join-Path $Root "teslim"
$OutDir = Join-Path $PackageRoot $Stamp

function Copy-IfExists {
  param(
    [string]$Source,
    [string]$Destination
  )
  if (Test-Path -LiteralPath $Source) {
    Copy-Item -LiteralPath $Source -Destination $Destination -Force
  }
}

Push-Location $Root
try {
  $controlArgs = @("-ExecutionPolicy", "Bypass", "-File", ".\kontrol.ps1", "-Build", "-Engine", $Engine, "-Report")
  if ($WithSpine) { $controlArgs += "-WithSpine" }
  & powershell @controlArgs
  if ($LASTEXITCODE -ne 0) {
    throw "Otomatik kontrol FAIL sonucu verdi; teslim paketi olusturulmadi."
  }
  & powershell -ExecutionPolicy Bypass -File ".\eksik-bilgiler.ps1"
  if ($LASTEXITCODE -ne 0) {
    throw "Eksik bilgi raporu olusturulamadi."
  }

  New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
  Copy-IfExists -Source "tez.pdf" -Destination (Join-Path $OutDir "tez.pdf")
  Copy-IfExists -Source "sirt-kapak.pdf" -Destination (Join-Path $OutDir "sirt-kapak.pdf")
  Copy-IfExists -Source "kontrol-raporu.md" -Destination (Join-Path $OutDir "kontrol-raporu.md")
  Copy-IfExists -Source "kontrol-raporu.json" -Destination (Join-Path $OutDir "kontrol-raporu.json")
  Copy-IfExists -Source "eksik-bilgiler.md" -Destination (Join-Path $OutDir "eksik-bilgiler.md")
  Copy-IfExists -Source "yazim-denetimi-raporu.md" -Destination (Join-Path $OutDir "yazim-denetimi-raporu.md")
  Copy-IfExists -Source "pdf-unicode-raporu.md" -Destination (Join-Path $OutDir "pdf-unicode-raporu.md")
  Copy-IfExists -Source "tex-on-kontrol-raporu.md" -Destination (Join-Path $OutDir "tex-on-kontrol-raporu.md")
  Copy-IfExists -Source "yazim-denetimi-ozet.json" -Destination (Join-Path $OutDir "yazim-denetimi-ozet.json")
  Copy-IfExists -Source "yazim-denetimi-ayarlar.json" -Destination (Join-Path $OutDir "yazim-denetimi-ayarlar.json")
  Copy-IfExists -Source "KONTROL_LISTESI.md" -Destination (Join-Path $OutDir "KONTROL_LISTESI.md")
  Copy-IfExists -Source "UYGUNLUK_NOTLARI.md" -Destination (Join-Path $OutDir "UYGUNLUK_NOTLARI.md")

  $sourceDir = Join-Path $OutDir "kaynak"
  New-Item -ItemType Directory -Force -Path $sourceDir | Out-Null
  $sourcePatterns = @("*.tex", "*.cls", "*.bst", "*.bib", "*.json", "*.ps1", "*.md")
  foreach ($pattern in $sourcePatterns) {
    Get-ChildItem -LiteralPath $Root -File -Filter $pattern | Where-Object {
      $_.Name -notlike "kontrol-raporu.*"
    } | ForEach-Object {
      Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $sourceDir $_.Name) -Force
    }
  }
  if (Test-Path -LiteralPath "assets") {
    Copy-Item -LiteralPath "assets" -Destination (Join-Path $sourceDir "assets") -Recurse -Force
  }

  $zipPath = Join-Path $OutDir "kaynak.zip"
  if (Test-Path -LiteralPath $zipPath) { Remove-Item -LiteralPath $zipPath -Force }
  Compress-Archive -Path (Join-Path $sourceDir "*") -DestinationPath $zipPath -Force

  $summary = @(
    "# Teslim paketi",
    "",
    "Tarih: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
    "Motor: $Engine",
    "Sirt kapak: $([bool]$WithSpine)",
    "",
    "Dosyalar:",
    "- tez.pdf",
    "- sirt-kapak.pdf",
    "- kontrol-raporu.md",
    "- kontrol-raporu.json",
    "- eksik-bilgiler.md",
    "- yazim-denetimi-raporu.md",
    "- pdf-unicode-raporu.md",
    "- tex-on-kontrol-raporu.md",
    "- yazim-denetimi-ozet.json",
    "- yazim-denetimi-ayarlar.json",
    "- KONTROL_LISTESI.md",
    "- UYGUNLUK_NOTLARI.md",
    "- kaynak.zip",
    "",
    "Not: kontrol raporundaki UYARI ve MANUEL satirlari gercek tez bilgileriyle son kez kontrol edilmelidir."
  )
  Set-Content -LiteralPath (Join-Path $OutDir "TESLIM_NOTU.md") -Value $summary -Encoding UTF8

  Write-Host "Teslim paketi hazirlandi: $OutDir"
} finally {
  Pop-Location
}
