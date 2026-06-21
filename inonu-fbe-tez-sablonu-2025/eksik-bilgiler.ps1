param(
  [string]$Output = ".\eksik-bilgiler.md"
)

$ErrorActionPreference = "Stop"
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

$Checks = @(
  @{ File = "tez.tex"; Pattern = "123456789"; Label = "Ogrenci numarasi" },
  @{ File = "tez.tex"; Pattern = "\(Varsa Unvan\)"; Label = "Varsa mezuniyet/unvan bilgisi" },
  @{ File = "tez.tex"; Pattern = "Anab\{\\\.i\}l\{\\\.i\}m Dal\{\\i\} Ad\{\\i\}|Department Name"; Label = "Ana bilim dali / department" },
  @{ File = "tez.tex"; Pattern = "Program Ad\{\\i\}|Programme Name"; Label = "Program adi / programme" },
  @{ File = "tez.tex"; Pattern = "TEZ\\\.IN SAVUNULDU|MONTH YEAR OF DEFENSE|Month year of defense"; Label = "Savunma ayi/yili" },
  @{ File = "tez.tex"; Pattern = "GG/AA/YYYY|YYYY/KK"; Label = "Enstitu Yonetim Kurulu tarihi ve karar numarasi" },
  @{ File = "tez.tex"; Pattern = "Ad\{\\i\} SOYADI|Name SURNAME"; Label = "Danisman/juri/Enstitu Muduru adlari" },
  @{ File = "tez.tex"; Pattern = "INONU UNIVERSITY THESIS TEMPLATE|TEZ \\c\{S\}ABLONU"; Label = "Turkce ve Ingilizce tez basligi" },
  @{ File = "ozgecmis.tex"; Pattern = "Ad\{\\i\} SOYADI"; Label = "Ozgecmis ad soyad" }
)

Push-Location $Root
try {
  $rows = @()
  foreach ($check in $Checks) {
    if (Test-Path -LiteralPath $check.File) {
      $matches = Select-String -Path $check.File -Pattern $check.Pattern
      foreach ($match in $matches) {
        $rows += [pscustomobject]@{
          Label = $check.Label
          File = $check.File
          Line = $match.LineNumber
          Text = $match.Line.Trim()
        }
      }
    }
  }

  $content = @(
    "# Eksik veya teyit gerektiren bilgiler",
    "",
    "Bu rapor otomatik uretilir. Gercek tez bilgileri girildikten sonra tekrar calistirilabilir.",
    "",
    "Onerilen is akisi:",
    "",
    "1. tez-bilgileri.example.json dosyasini tez-bilgileri.json olarak kopyalayin.",
    "2. Asagidaki alanlari resmi/danisman onayli bilgilerle doldurun.",
    "3. tez-bilgileri-uygula.ps1 -Config .\tez-bilgileri.json -WhatIf ile on izleme yapin.",
    "4. tez-bilgileri-uygula.ps1 -Config .\tez-bilgileri.json ile uygulayin.",
    "5. kontrol.ps1 -Build -Engine xelatex -WithSpine -Report ile denetleyin.",
    "",
    "## Otomatik bulunan alanlar",
    ""
  )

  if ($rows.Count -eq 0) {
    $content += "Otomatik taramada eksik veya ornek olarak birakilmis bilgi bulunmadi."
  } else {
    foreach ($row in $rows) {
      $content += "- [ ] $($row.Label) - $($row.File):$($row.Line)"
      $content += ("  - " + $row.Text)
    }
  }

  $content += @(
    "",
    "## Elle teyit edilecekler",
    "",
    "- [ ] Kapak ve sirt kapakta uzun baslik tasmasi yok.",
    "- [ ] Juri, tarih, karar numarasi ve Enstitu Muduru bilgileri resmi belgelerle uyumlu.",
    "- [ ] Ozet ve abstract gercek tezin amac, yontem, bulgu ve sonucunu yansitiyor.",
    "- [ ] Anahtar kelimeler gercek tez konusuna uygun ve alfabetik.",
    "- [ ] APA 7 kaynak bicimi ve akademik icerik danisman/enstitu beklentisine uygun.",
    "- [ ] Etik ve uretken yapay zeka beyan metni gercek kullanim durumunu yansitiyor."
  )
  $content += "- [ ] Son teslim paketi teslim-hazirla.ps1 -Engine xelatex -WithSpine ile uretildi."

  Set-Content -LiteralPath $Output -Value $content -Encoding UTF8
  Write-Host "Eksik bilgi raporu yazildi: $Output"
  Write-Host "Bulunan otomatik madde sayisi: $($rows.Count)"
} finally {
  Pop-Location
}
