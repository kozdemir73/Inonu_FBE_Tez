param()

$ErrorActionPreference = "Stop"
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

function Get-RequiredLine {
  param(
    [string[]]$Lines,
    [string]$Pattern,
    [string]$Description
  )
  $line = $Lines | Where-Object { $_ -match $Pattern } | Select-Object -First 1
  if (-not $line) { throw "$Description satiri tez.tex icinde bulunamadi." }
  return $line.Trim()
}

Push-Location $Root
try {
  $lines = Get-Content -LiteralPath "tez.tex" -Encoding UTF8
  $documentClass = Get-RequiredLine -Lines $lines -Pattern "^\s*\\documentclass" -Description "documentclass"
  if ($documentClass -match "\\documentclass\[([^\]]*)\]\{inonutez\}") {
    $options = @($matches[1] -split "," | ForEach-Object { $_.Trim() } | Where-Object { $_ })
    if ($options -notcontains "sirtkapak") { $options += "sirtkapak" }
    $documentClass = "\documentclass[$($options -join ',')]{inonutez}"
  } else {
    throw "tez.tex icindeki documentclass satiri beklenen bicimde degil."
  }

  $yazar = Get-RequiredLine -Lines $lines -Pattern "^\s*\\yazar\{" -Description "yazar"
  $baslik = Get-RequiredLine -Lines $lines -Pattern "^\s*\\baslik\{" -Description "baslik"
  $kapakYili = Get-RequiredLine -Lines $lines -Pattern "^\s*\\kapakyili\{" -Description "kapakyili"
  $kapakSehri = Get-RequiredLine -Lines $lines -Pattern "^\s*\\kapaksehri\{" -Description "kapaksehri"

  $content = @(
    "% Cilt/sirt kapagi icin otomatik uretilen ayri derleme dosyasi.",
    "% Bu dosyayi elle duzenlemek yerine sirt-kapak-guncelle.ps1 calistirin.",
    "% Ana tez PDF'ine dahil edilmez.",
    $documentClass,
    "\usepackage[sfdefault]{carlito}",
    "",
    $yazar,
    $baslik,
    $kapakYili,
    $kapakSehri,
    "",
    "\begin{document}",
    "\end{document}"
  )

  Set-Content -LiteralPath "sirt-kapak.tex" -Value $content -Encoding UTF8
  Write-Host "sirt-kapak.tex tez.tex bilgilerinden guncellendi."
} finally {
  Pop-Location
}
