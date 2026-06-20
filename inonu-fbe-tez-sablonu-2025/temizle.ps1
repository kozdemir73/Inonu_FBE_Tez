param(
  [switch]$All
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

$latexExtensions = @(
  ".aux", ".bbl", ".bcf", ".blg", ".fdb_latexmk", ".fls", ".lof", ".log",
  ".lot", ".out", ".run.xml", ".synctex.gz", ".toc", ".xdv"
)

Push-Location $Root
try {
  $removed = @()
  $candidates = Get-ChildItem -LiteralPath $Root -File | Where-Object {
    ($_.Name -match "^(tez|sirt-kapak|tez-xelatex)\.") -and
    ($latexExtensions -contains $_.Extension -or $_.Name -like "*.run.xml" -or $_.Name -like "*.synctex.gz")
  }

  if ($All) {
    $candidates += Get-ChildItem -LiteralPath $Root -File -Filter "kontrol-raporu.*"
  }

  foreach ($file in $candidates | Sort-Object FullName -Unique) {
    $fullRoot = [System.IO.Path]::GetFullPath($Root)
    $fullFile = [System.IO.Path]::GetFullPath($file.FullName)
    if (-not $fullFile.StartsWith($fullRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
      throw "Klasor disinda dosya silme reddedildi: $fullFile"
    }
    Remove-Item -LiteralPath $fullFile -Force
    $removed += $file.Name
  }

  if ($removed.Count -eq 0) {
    Write-Host "Temizlenecek ara dosya bulunmadi."
  } else {
    Write-Host "Temizlenen dosyalar:"
    $removed | ForEach-Object { Write-Host "  $_" }
  }
} finally {
  Pop-Location
}
