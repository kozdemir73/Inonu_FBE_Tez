param(
  [string]$Config = ".\tez-bilgileri.json",
  [switch]$WhatIf
)

$ErrorActionPreference = "Stop"
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

function Get-JsonArray {
  param(
    [object]$ConfigObject,
    [string]$Name
  )
  if (-not ($ConfigObject.PSObject.Properties.Name -contains $Name)) { return $null }
  $value = $ConfigObject.$Name
  if ($null -eq $value) { return $null }
  return @($value)
}

function Convert-ToMacroLine {
  param(
    [string]$Name,
    [object[]]$Values
  )
  $parts = $Values | ForEach-Object {
    $value = [string]$_
    $value = [regex]::Replace($value.Trim(), "\s+", " ")
    "{${value}}"
  }
  return "\" + $Name + ($parts -join "")
}

function Get-MacroEndIndex {
  param(
    [string[]]$Lines,
    [int]$Start
  )
  $depth = 0
  $started = $false
  for ($i = $Start; $i -lt $Lines.Count; $i++) {
    $line = $Lines[$i]
    for ($j = 0; $j -lt $line.Length; $j++) {
      $ch = $line[$j]
      if ($ch -eq '\') {
        $j++
        continue
      }
      if ($ch -eq '{') {
        $depth++
        $started = $true
      } elseif ($ch -eq '}') {
        $depth--
        if ($started -and $depth -le 0) {
          return $i
        }
      }
    }
  }
  return $Start
}

function Get-OrphanContinuationEndIndex {
  param(
    [string[]]$Lines,
    [int]$End
  )
  $index = $End
  while (($index + 1) -lt $Lines.Count) {
    $next = $Lines[$index + 1].Trim()
    if (-not $next) { break }
    if ($next -match "^\\[A-Za-z]+") { break }
    if ($next -match "\}$") {
      $index++
      continue
    }
    break
  }
  return $index
}

Push-Location $Root
try {
  if (-not (Test-Path -LiteralPath $Config)) {
    throw "Bilgi dosyasi bulunamadi: $Config. Baslangic icin tez-bilgileri.example.json dosyasini tez-bilgileri.json olarak kopyalayip duzenleyin."
  }

  $configObject = Get-Content -LiteralPath $Config -Raw -Encoding UTF8 | ConvertFrom-Json
  $macroNames = @(
    "yazar", "ogrencino", "unvan", "anabilimdali", "programi", "tarih",
    "tarihKucuk", "tezyoneticisi", "tezyoneticisiENG", "esdanismani",
    "esdanismaniENG", "bapdestegi", "baslik", "title", "anahtarkelimeler", "keywords", "tezvermetarih", "tezsavunmatarih",
    "kapakyili", "kapaksehri", "oy", "yonetimkurulukarar", "juriBir",
    "juriIki", "juriUc", "juriDort", "juriBes", "EnstituMuduru"
  )

  $lines = Get-Content -LiteralPath "tez.tex" -Encoding UTF8
  $changes = @()
  for ($i = 0; $i -lt $lines.Count; $i++) {
    foreach ($macro in $macroNames) {
      if ($lines[$i] -match "^\s*\\$macro\{") {
        $values = Get-JsonArray -ConfigObject $configObject -Name $macro
        if ($null -ne $values) {
          $newLine = Convert-ToMacroLine -Name $macro -Values $values
          $endIndex = Get-MacroEndIndex -Lines $lines -Start $i
          $endIndex = Get-OrphanContinuationEndIndex -Lines $lines -End $endIndex
          $oldBlock = ($lines[$i..$endIndex] -join "`n").Trim()
          if ($oldBlock -ne $newLine) {
            $changes += [pscustomobject]@{
              Line = $i + 1
              Macro = $macro
              Old = $oldBlock
              New = $newLine
            }
            $before = @()
            $after = @()
            if ($i -gt 0) { $before = $lines[0..($i - 1)] }
            if ($endIndex -lt ($lines.Count - 1)) { $after = $lines[($endIndex + 1)..($lines.Count - 1)] }
            $lines = @($before) + @($newLine) + @($after)
          }
        }
        break
      }
    }
  }

  if ($changes.Count -eq 0) {
    Write-Host "Uygulanacak degisiklik bulunamadi."
  } else {
    Write-Host "Bulunan degisiklikler:"
    $changes | ForEach-Object {
      Write-Host "  $($_.Line): \ $($_.Macro)"
      Write-Host "    - $($_.Old)"
      Write-Host "    + $($_.New)"
    }
  }

  if ($WhatIf) {
    Write-Host "WhatIf: tez.tex degistirilmedi."
  } else {
    Set-Content -LiteralPath "tez.tex" -Value $lines -Encoding UTF8
    & powershell -ExecutionPolicy Bypass -File ".\sirt-kapak-guncelle.ps1"
    if ($LASTEXITCODE -ne 0) { throw "sirt-kapak.tex guncellenemedi." }
    Write-Host "tez.tex ve sirt-kapak.tex bilgi dosyasina gore guncellendi."
  }
} finally {
  Pop-Location
}
