param(
  [ValidateSet("xelatex")]
  [string]$Engine = "xelatex",
  [switch]$Build,
  [switch]$WithSpine,
  [switch]$Report
)

$ErrorActionPreference = "Stop"
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Script:FailCount = 0
$Script:WarnCount = 0
$Script:ManualCount = 0
$Script:Results = @()

function Add-Result {
  param(
    [ValidateSet("OK", "UYARI", "FAIL", "MANUEL")]
    [string]$Status,
    [string]$Message
  )
  $Script:Results += [pscustomobject]@{ Status = $Status; Message = $Message }
  switch ($Status) {
    "OK" { Write-Host "[OK] $Message" -ForegroundColor Green }
    "UYARI" { $Script:WarnCount++; Write-Host "[UYARI] $Message" -ForegroundColor Yellow }
    "FAIL" { $Script:FailCount++; Write-Host "[FAIL] $Message" -ForegroundColor Red }
    "MANUEL" { $Script:ManualCount++; Write-Host "[MANUEL] $Message" -ForegroundColor Cyan }
  }
}

function Convert-PlainTeXText {
  param([string]$Text)
  $text = $Text
  $text = $text -replace "(?s)%.*?(\r?\n)", " "
  $text = $text -replace "\\textbf\{([^{}]*)\}", '$1'
  $text = $text -replace "\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^{}]*\})?", " "
  $text = $text -replace "[{}\\]", " "
  $text = $text -replace "\s+", " "
  return $text.Trim()
}

function Get-PlainTeXText {
  param([string]$Path)
  return Convert-PlainTeXText (Get-Content -LiteralPath $Path -Raw -Encoding UTF8)
}

function Get-WordCount {
  param([string]$Text)
  $matches = [regex]::Matches($Text, "[\p{L}\p{N}]+")
  return $matches.Count
}

function Test-Command {
  param([string]$Name)
  return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Convert-ForSearch {
  param([string]$Text)
  $value = $Text.ToUpperInvariant()
  $replacements = @{
    ([string][char]0x0130) = "I"
    ([string][char]0x0131) = "I"
    ([string][char]0x00D6) = "O"
    ([string][char]0x00DC) = "U"
    ([string][char]0x015E) = "S"
    ([string][char]0x00C7) = "C"
    ([string][char]0x011E) = "G"
  }
  foreach ($key in $replacements.Keys) {
    $value = $value.Replace($key, $replacements[$key])
  }
  $normalized = $value.Normalize([Text.NormalizationForm]::FormD)
  $chars = foreach ($ch in $normalized.ToCharArray()) {
    if ([Globalization.CharUnicodeInfo]::GetUnicodeCategory($ch) -ne [Globalization.UnicodeCategory]::NonSpacingMark) { $ch }
  }
  return (-join $chars)
}

function Get-MacroLine {
  param(
    [string]$Path,
    [string]$Name
  )
  $pattern = "^\s*\\$Name\{"
  $line = Get-Content -LiteralPath $Path -Encoding UTF8 | Where-Object { $_ -match $pattern } | Select-Object -First 1
  if ($line) { return $line.Trim() }
  return $null
}

function Get-BibField {
  param(
    [string]$Body,
    [string]$Name
  )
  $pattern = "(?is)\b$Name\s*=\s*(\{(?<value>.*?)\}|`"(?<value>.*?)`"|(?<value>[^,\r\n]+))"
  $match = [regex]::Match($Body, $pattern)
  if ($match.Success) { return $match.Groups["value"].Value.Trim() }
  return $null
}

Push-Location $Root
try {
  Write-Host "Inonu FBE tez uygunluk otomatik kontrolu" -ForegroundColor White
  Write-Host "Klasor: $Root"

  $requiredFiles = @(
    "tez.tex", "inonutez.cls", "build.ps1", "sirt-kapak.tex",
    "sirt-kapak-guncelle.ps1", "ozet.tex", "abstract.tex",
    "tesekkur.tex", "etik-beyan.tex", "ozgecmis.tex", "kilavuz-notlari\KONTROL_LISTESI.md",
    "kilavuz-notlari\UYGUNLUK_NOTLARI.md", "temizle.ps1", "teslim-hazirla.ps1",
    "tez-bilgileri.example.json", "tez-bilgileri-uygula.ps1", "eksik-bilgiler.ps1"
  )
  $missingFiles = @($requiredFiles | Where-Object { -not (Test-Path -LiteralPath $_) })
  if ($missingFiles.Count -eq 0) { Add-Result "OK" "Zorunlu sablon kaynak dosyalari bulundu." }
  else { Add-Result "FAIL" "Eksik zorunlu sablon dosyalari: $($missingFiles -join ', ')" }

  if ((Test-Path -LiteralPath "assets\iu-fbe-amblem.png") -or (Test-Path -LiteralPath "assets\iu-fbe-amblem.pdf")) {
    Add-Result "OK" "Kapak icin FBE amblem/logo varligi bulundu."
  } else {
    Add-Result "UYARI" "assets klasorunde iu-fbe-amblem.png/pdf bulunamadi; kapak logosu kontrol edilmeli."
  }

  if ($Build) {
    $args = @("-ExecutionPolicy", "Bypass", "-File", ".\build.ps1", "-Engine", $Engine)
    if ($WithSpine) { $args += "-WithSpine" }
    & powershell @args
    if ($LASTEXITCODE -ne 0) {
      Add-Result "FAIL" "Derleme dogrulama scripti hata verdi."
    } else {
      Add-Result "OK" "Derleme dogrulama scripti basariyla tamamlandi."
    }
  }

  if (Test-Path "tez.pdf") {
    Add-Result "OK" "Ana PDF bulundu: tez.pdf"
  } else {
    Add-Result "FAIL" "Ana PDF bulunamadi. Once tez.tex derlenmeli."
  }

  if ($WithSpine) {
    if (Test-Path "sirt-kapak.pdf") { Add-Result "OK" "Sirt kapak PDF bulundu." }
    else { Add-Result "UYARI" "Sirt kapak istenmis ama sirt-kapak.pdf bulunamadi." }
  }

  if (Test-Path "tez.log") {
    $critical = Select-String -Path "tez.log" -Pattern "Fatal|Emergency|Undefined control sequence|LaTeX Error:|Package .* Error:|Missing \\begin\{document\}|macro parameter character|TeX capacity exceeded|Runaway argument|Missing \$ inserted|Paragraph ended before"
    $warnings = Select-String -Path "tez.log" -Pattern "Overfull \\hbox|Overfull \\vbox|LaTeX Warning: Citation|undefined references|Font Warning|Missing character"
    if ($critical) { Add-Result "FAIL" "Kritik LaTeX log hatalari var. build.ps1 ile ayrintili bakilmali." }
    elseif ($warnings) { Add-Result "UYARI" "LaTeX logunda gozden gecirilecek uyarilar var; PDF yine de uretildi." }
    else { Add-Result "OK" "Kritik LaTeX log hatasi veya onemli uyari bulunmadi." }
  } else {
    Add-Result "UYARI" "tez.log bulunamadi; log kontrolu yapilamadi."
  }

  $pdfText = ""
  if ((Test-Path "tez.pdf") -and (Test-Command "pdftotext")) {
    $pdfTextPath = Join-Path $env:TEMP ("tez-pdf-text-" + [guid]::NewGuid().ToString() + ".txt")
    try {
      & pdftotext -enc UTF-8 "tez.pdf" $pdfTextPath
      $pdfText = Get-Content -LiteralPath $pdfTextPath -Raw -Encoding UTF8
    } finally {
      if (Test-Path -LiteralPath $pdfTextPath) {
        Remove-Item -LiteralPath $pdfTextPath -Force -ErrorAction SilentlyContinue
      }
    }
    $pdfSearchText = Convert-ForSearch $pdfText
    $required = @( "INONU UNIVERSITESI", "FEN BILIMLERI ENSTITUSU", "KABUL VE ONAY", "ICINDEKILER", "TESEKKUR VE ONSOZ", "OZET", "ABSTRACT", "SEKILLER DIZINI", "TABLOLAR DIZINI", "KAYNAKLAR" )
    foreach ($item in $required) {
      if ($pdfSearchText -match [regex]::Escape($item)) { Add-Result "OK" "Teslim oncesi: PDF metninde '$item' bulundu." }
      else { Add-Result "UYARI" "Teslim oncesi: PDF metninde '$item' bulunamadi veya farkli yazildi." }
    }
    if ($pdfSearchText -match "SIMGELER" -or $pdfSearchText -match "KISALTMALAR") {
      Add-Result "OK" "Teslim oncesi: Simgeler/kisaltmalar dizini PDF metninde gorunuyor."
    } elseif (Test-Path "simgeler-ve-kisaltmalar.tex") {
      Add-Result "UYARI" "Teslim oncesi: Simgeler ve kisaltmalar dosyasi var ama PDF metninde baslik gorunmedi."
    }
    if ($pdfText -match "Ã|Ä|Å|�") {
      Add-Result "UYARI" "Teslim oncesi: PDF metninde karakter bozulmasi isareti olabilir; yazim denetimindeki PDF karakter kontrolune bakin."
    } else {
      Add-Result "OK" "Teslim oncesi: PDF metninde yaygin karakter bozulmasi isareti gorunmedi."
    }

    if ($pdfText -match "\d+\.\d+\.\d+\.\d+") {
      Add-Result "UYARI" "Icindekiler veya metinde dorduncu derece numarali baslik gorunuyor olabilir; kilavuza gore icindekilerde yer almamali."
    } else {
      Add-Result "OK" "PDF metninde dorduncu derece numarali baslik kalibi gorunmedi."
    }
  } elseif (-not (Test-Command "pdftotext")) {
    Add-Result "UYARI" "pdftotext bulunamadi; PDF metin kontrolu atlandi."
  }

  if ((Test-Path "tez.pdf") -and (Test-Command "pdfinfo")) {
    $pagesLine = (& pdfinfo "tez.pdf" | Select-String -Pattern "^Pages:")
    if ($pagesLine) { Add-Result "OK" "Ana PDF sayfa bilgisi okunabildi: $($pagesLine.Line.Trim())" }
    else { Add-Result "UYARI" "Ana PDF sayfa bilgisi okunamadi." }
  }

  if ((Test-Path "tez.pdf") -and (Test-Command "pdffonts")) {
    $fonts = & pdffonts "tez.pdf"
    if ($fonts -match "Calibri|Carlito") { Add-Result "OK" "PDF font listesinde Calibri/Carlito bulundu." }
    else { Add-Result "UYARI" "PDF font listesinde Calibri/Carlito gorunmedi." }
    $fontRows = $fonts | Where-Object { $_ -match "^\S+\s+\S+" -and $_ -notmatch "^name\s+" -and $_ -notmatch "^-+" }
    $notEmbedded = @($fontRows | Where-Object { $_ -match "\sno\s+(yes|no)\s+(yes|no)\s+\d+\s+\d+\s*$" })
    if ($notEmbedded.Count -gt 0) { Add-Result "UYARI" "Gomulu olmayan font olabilir; pdffonts ciktisi kontrol edilmeli." }
    else { Add-Result "OK" "pdffonts ciktisinda gomulu olmayan font isareti gorulmedi." }
  }

  $texFiles = Get-ChildItem -File -Filter "*.tex"
  $placeholderPattern = "GG/AA/YYYY|YYYY/KK|123456789|Ad\{\\i\} SOYADI|Name SURNAME|Department Name|Programme Name|TEZ\\.?IN SAVUNULDU|MONTH YEAR|Varsa Unvan"
  $placeholderHits = $texFiles | Select-String -Pattern $placeholderPattern
  if ($placeholderHits) {
    $placeholderSummary = @(
      $placeholderHits |
      Select-Object -First 8 |
      ForEach-Object { "$(Split-Path -Leaf $_.Path):$($_.LineNumber)" }
    )
    Add-Result "UYARI" "Ornek/yer tutucu bilgiler kalmis olabilir: $($placeholderSummary -join ', ')"
    $placeholderHits | ForEach-Object { Write-Host "       $($_.Path):$($_.LineNumber) $($_.Line.Trim())" }
  } else {
    Add-Result "OK" "Yaygin yer tutucu degerleri bulunmadi."
  }

  if (Test-Path -LiteralPath "sirt-kapak.tex") {
    $spineMismatch = @()
    foreach ($macro in @("yazar", "baslik", "kapakyili", "kapaksehri")) {
      $mainLine = Get-MacroLine -Path "tez.tex" -Name $macro
      $spineLine = Get-MacroLine -Path "sirt-kapak.tex" -Name $macro
      if ($mainLine -and $spineLine -and $mainLine -ne $spineLine) {
        $spineMismatch += $macro
      }
    }
    if ($spineMismatch.Count -eq 0) {
      Add-Result "OK" "Sirt kapak bilgileri ana tez bilgileriyle uyumlu gorunuyor."
    } else {
      Add-Result "UYARI" "Sirt kapakta ana tezle farkli alanlar var: $($spineMismatch -join ', '). sirt-kapak-guncelle.ps1 calistirilabilir."
    }
  }

  foreach ($abstractFile in @("ozet.tex", "abstract.tex")) {
    if (Test-Path $abstractFile) {
      $plain = Get-PlainTeXText $abstractFile
      $words = Get-WordCount $plain
      if ($words -le 250) { Add-Result "OK" "$abstractFile kelime sayisi yaklasik $words; 250 siniri icinde." }
      else { Add-Result "UYARI" "$abstractFile kelime sayisi yaklasik $words; 250 sinirini asiyor olabilir." }

      $raw = Get-Content -LiteralPath $abstractFile -Raw -Encoding UTF8
      if ($raw -match "\\(cite|parencite|textcite|includegraphics|begin\{figure\}|begin\{table\})") {
        Add-Result "UYARI" "$abstractFile icinde kaynak/sekil/tablo komutu olabilir."
      } else {
        Add-Result "OK" "$abstractFile icinde kaynak/sekil/tablo komutu bulunmadi."
      }

      $keywordLine = ($raw -split "\r?\n" | Where-Object { $_ -match "\\textbf\{(Anahtar Kelimeler|Keywords):?\}" } | Select-Object -First 1)
      if ($keywordLine) {
        Add-Result "OK" "$abstractFile anahtar kelime satiri iceriyor."
        $keywordText = Convert-PlainTeXText $keywordLine
        $keywordText = $keywordText -replace "^(Anahtar Kelimeler|Keywords)\s*:?\s*", ""
        $keywords = @($keywordText -split "," | ForEach-Object { $_.Trim() } | Where-Object { $_ })
        if ($keywords.Count -ge 3 -and $keywords.Count -le 5) {
          Add-Result "OK" "$abstractFile anahtar kelime sayisi $($keywords.Count); kilavuz araliginda."
        } else {
          Add-Result "UYARI" "$abstractFile anahtar kelime sayisi $($keywords.Count); 3-5 araligi kontrol edilmeli."
        }
        $sortedKeywords = @($keywords | Sort-Object { Convert-ForSearch $_ })
        $isSorted = $true
        for ($i = 0; $i -lt $keywords.Count; $i++) {
          if ((Convert-ForSearch $keywords[$i]) -ne (Convert-ForSearch $sortedKeywords[$i])) { $isSorted = $false }
        }
        if ($isSorted) { Add-Result "OK" "$abstractFile anahtar kelimeleri alfabetik gorunuyor." }
        else { Add-Result "UYARI" "$abstractFile anahtar kelimeleri alfabetik sirada gorunmuyor." }
      } else {
        $macroName = if ($abstractFile -eq "ozet.tex") { "anahtarkelimeler" } else { "keywords" }
        $macroLine = Get-MacroLine -Path "tez.tex" -Name $macroName
        if ($macroLine) { Add-Result "OK" "$abstractFile anahtar kelimeleri tez.tex icindeki \ $macroName makrosundan aliniyor." }
        else { Add-Result "UYARI" "$abstractFile anahtar kelime satiri icermiyor ve tez.tex icinde \ $macroName makrosu bulunamadi." }
      }
    }
  }

  $allTex = ($texFiles | ForEach-Object { Get-Content -LiteralPath $_.FullName -Raw -Encoding UTF8 }) -join "`n"
  $citationKeys = [System.Collections.Generic.HashSet[string]]::new()
  foreach ($m in [regex]::Matches($allTex, "\\(?:cite|parencite|textcite|citep|citet)\*?(?:\[[^\]]*\])*\{([^{}]+)\}")) {
    foreach ($key in ($m.Groups[1].Value -split ",")) {
      $cleanKey = $key.Trim()
      if ($cleanKey -and -not $cleanKey.StartsWith("#")) { [void]$citationKeys.Add($cleanKey) }
    }
  }

  $bibFiles = Get-ChildItem -File -Filter "*.bib"
  $bibKeys = [System.Collections.Generic.HashSet[string]]::new()
  $bibEntries = @()
  foreach ($bib in $bibFiles) {
    $bibText = Get-Content -LiteralPath $bib.FullName -Raw -Encoding UTF8
    foreach ($m in [regex]::Matches($bibText, "@\w+\s*\{\s*([^,\s]+)")) {
      [void]$bibKeys.Add($m.Groups[1].Value.Trim())
    }
    foreach ($m in [regex]::Matches($bibText, "(?ms)@\w+\s*\{\s*([^,\s]+)\s*,(.*?)(?=^\s*@|\z)")) {
      $bibEntries += [pscustomobject]@{
        Key = $m.Groups[1].Value.Trim()
        Body = $m.Groups[2].Value
        File = $bib.Name
      }
    }
  }
  if ($citationKeys.Count -gt 0 -and $bibKeys.Count -gt 0) {
    $missing = @($citationKeys | Where-Object { -not $bibKeys.Contains($_) })
    if ($missing.Count -eq 0) { Add-Result "OK" "Metin ici atif anahtarlari .bib dosyalarinda bulundu." }
    else { Add-Result "FAIL" "Bib dosyasinda bulunmayan atif anahtarlari: $($missing -join ', ')" }
    $unusedBib = @($bibKeys | Where-Object { -not $citationKeys.Contains($_) } | Select-Object -First 25)
    if ($unusedBib.Count -gt 0) {
      Add-Result "UYARI" "Metinde atif verilmeyen bib kayitlari olabilir: $($unusedBib -join ', ')"
    } else {
      Add-Result "OK" "Bib dosyasindaki kayitlar metin icinde kullanilmis gorunuyor."
    }
  } else {
    Add-Result "UYARI" "Atif veya bib anahtari bulunamadi; kaynak kontrolu sinirli kaldi."
  }

  if (Test-Path "tez.bbl") {
    if ((Get-Item -LiteralPath "tez.bbl").Length -gt 0) {
      Add-Result "OK" "Teslim oncesi: Kaynakca cikti dosyasi tez.bbl olusmus gorunuyor."
    } else {
      Add-Result "UYARI" "Teslim oncesi: tez.bbl var ama bos gorunuyor; kaynakca derlemesi kontrol edilmeli."
    }
  } elseif ($citationKeys.Count -gt 0 -or $bibKeys.Count -gt 0) {
    Add-Result "UYARI" "Teslim oncesi: tez.bbl bulunamadi; kaynakca derlemesi tamamlanmamis olabilir."
  }

  if ($bibEntries.Count -gt 0) {
    $missingAuthor = @()
    $missingTitle = @()
    $missingYear = @()
    $badDoi = @()
    $badUrl = @()
    foreach ($entry in $bibEntries) {
      $author = Get-BibField -Body $entry.Body -Name "author"
      $editor = Get-BibField -Body $entry.Body -Name "editor"
      $title = Get-BibField -Body $entry.Body -Name "title"
      $year = Get-BibField -Body $entry.Body -Name "year"
      $date = Get-BibField -Body $entry.Body -Name "date"
      $doi = Get-BibField -Body $entry.Body -Name "doi"
      $url = Get-BibField -Body $entry.Body -Name "url"
      if (-not $author -and -not $editor) { $missingAuthor += $entry.Key }
      if (-not $title) { $missingTitle += $entry.Key }
      if (-not $year -and -not $date) { $missingYear += $entry.Key }
      if ($doi -and ($doi -notmatch "^10\.\S+/.+" -or $doi -match "\s")) { $badDoi += $entry.Key }
      if ($url -and $url -notmatch "^(https?|doi):") { $badUrl += $entry.Key }
    }
    if ($missingAuthor.Count -eq 0) { Add-Result "OK" "Kaynakca kontrolu: Bib kayitlarinda yazar/editor alani genel olarak dolu." }
    else { Add-Result "UYARI" "Kaynakca kontrolu: yazar/editor alani eksik gorunen kayitlar: $((@($missingAuthor) | Select-Object -First 20) -join ', ')" }
    if ($missingTitle.Count -eq 0) { Add-Result "OK" "Kaynakca kontrolu: Bib kayitlarinda baslik alani genel olarak dolu." }
    else { Add-Result "UYARI" "Kaynakca kontrolu: baslik alani eksik gorunen kayitlar: $((@($missingTitle) | Select-Object -First 20) -join ', ')" }
    if ($missingYear.Count -eq 0) { Add-Result "OK" "Kaynakca kontrolu: Bib kayitlarinda yil/tarih alani genel olarak dolu." }
    else { Add-Result "UYARI" "Kaynakca kontrolu: yil/tarih alani eksik gorunen kayitlar: $((@($missingYear) | Select-Object -First 20) -join ', ')" }
    if ($badDoi.Count -gt 0) { Add-Result "UYARI" "Kaynakca kontrolu: DOI bicimi supheli kayitlar: $((@($badDoi) | Select-Object -First 20) -join ', ')" }
    else { Add-Result "OK" "Kaynakca kontrolu: DOI alanlarinda yaygin bicim sorunu gorunmedi." }
    if ($badUrl.Count -gt 0) { Add-Result "UYARI" "Kaynakca kontrolu: URL bicimi supheli kayitlar: $((@($badUrl) | Select-Object -First 20) -join ', ')" }
    else { Add-Result "OK" "Kaynakca kontrolu: URL alanlarinda yaygin bicim sorunu gorunmedi." }
  }

  $labelKeys = [System.Collections.Generic.HashSet[string]]::new()
  foreach ($m in [regex]::Matches($allTex, "\\label\{([^{}]+)\}")) {
    [void]$labelKeys.Add($m.Groups[1].Value.Trim())
  }
  $refKeys = [System.Collections.Generic.HashSet[string]]::new()
  foreach ($m in [regex]::Matches($allTex, "\\(?:ref|eqref|pageref|autoref|nameref)\*?\{([^{}]+)\}")) {
    foreach ($key in ($m.Groups[1].Value -split ",")) {
      $cleanKey = $key.Trim()
      if ($cleanKey) { [void]$refKeys.Add($cleanKey) }
    }
  }
  if ($refKeys.Count -gt 0) {
    $missingRefs = @($refKeys | Where-Object { -not $labelKeys.Contains($_) })
    if ($missingRefs.Count -eq 0) { Add-Result "OK" "Metin ici ref/eqref hedefleri tanimli gorunuyor." }
    else { Add-Result "FAIL" "Tanimli olmayan ref/eqref hedefleri: $($missingRefs -join ', ')" }
  } else {
    Add-Result "UYARI" "Metin ici ref/eqref bulunamadi; sekil/tablo/denklem gonderimleri elle kontrol edilmeli."
  }

  $objectLabelKeys = [System.Collections.Generic.HashSet[string]]::new()
  $unlabeledObjects = 0
  foreach ($m in [regex]::Matches($allTex, "(?s)\\begin\{(figure|table|equation|align|gather|multline)\*?\}(.*?)\\end\{\1\*?\}")) {
    $body = $m.Groups[2].Value
    $labelMatch = [regex]::Match($body, "\\label\{([^{}]+)\}")
    if ($labelMatch.Success) {
      [void]$objectLabelKeys.Add($labelMatch.Groups[1].Value.Trim())
    } else {
      $unlabeledObjects++
    }
  }
  if ($objectLabelKeys.Count -gt 0) {
    $unreferencedObjects = @($objectLabelKeys | Where-Object { -not $refKeys.Contains($_) } | Select-Object -First 25)
    if ($unreferencedObjects.Count -eq 0) { Add-Result "OK" "Etiketli sekil/tablo/denklem nesneleri metinde aniliyor gorunuyor." }
    else { Add-Result "UYARI" "Metinde anilmayan sekil/tablo/denklem etiketleri olabilir: $($unreferencedObjects -join ', ')" }
  }
  if ($unlabeledObjects -gt 0) {
    Add-Result "UYARI" "$unlabeledObjects sekil/tablo/denklem ortami label icermiyor olabilir."
  }

  $captionWarnings = @()
  foreach ($m in [regex]::Matches($allTex, "\\caption\{([^{}]+)\}")) {
    $caption = (Convert-PlainTeXText $m.Groups[1].Value).Trim()
    if ($caption.EndsWith(".")) { $captionWarnings += $caption }
  }
  if ($captionWarnings.Count -gt 0) {
    Add-Result "UYARI" "Nokta ile biten sekil/tablo basligi olabilir; ilk ornek: $($captionWarnings[0])"
  } else {
    Add-Result "OK" "Sekil/tablo basliklarinda sonda nokta otomatik taramada gorunmedi."
  }

  if ($allTex -match "\\chapter\{G\\.?IR\\.?I\\.?S\}[\s\S]*?\\section\{") {
    Add-Result "UYARI" "GIRIS bolumunde alt baslik olabilir; kilavuza gore kontrol edilmeli."
  } else {
    Add-Result "OK" "GIRIS bolumunde otomatik taramada alt baslik gorunmedi."
  }

  Add-Result "MANUEL" "Kapak ve sirt kapakta uzun baslik tasmasi son PDF uzerinden gozle kontrol edilmeli."
  Add-Result "MANUEL" "Juri, tarih, karar numarasi ve resmi bilgiler Enstitu/Danisman bilgileriyle karsilastirilmali."
  Add-Result "MANUEL" "APA 7 ayrintilari ve akademik icerik danismanla son PDF uzerinden kontrol edilmeli."
  Add-Result "MANUEL" "Etik ve uretken yapay zeka beyaninin gercek kullanim durumunu yansittigi teyit edilmeli."

  if ($Report) {
    $reportDir = Join-Path $Root "raporlar"
    if (-not (Test-Path -LiteralPath $reportDir)) {
      New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
    }
    $reportJson = Join-Path $reportDir "kontrol-raporu.json"
    $reportMd = Join-Path $reportDir "kontrol-raporu.md"
    $summary = [pscustomobject]@{
      Folder = $Root
      Engine = $Engine
      Build = [bool]$Build
      WithSpine = [bool]$WithSpine
      Fail = $Script:FailCount
      Warning = $Script:WarnCount
      Manual = $Script:ManualCount
      Results = $Script:Results
    }
    $summary | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $reportJson -Encoding UTF8
    $md = @("# Inonu FBE otomatik kontrol raporu", "", "Klasor: $Root", "Motor: $Engine", "", "Ozet: $Script:FailCount FAIL, $Script:WarnCount UYARI, $Script:ManualCount MANUEL", "")
    foreach ($item in $Script:Results) {
      $md += "- [$($item.Status)] $($item.Message)"
    }
    Set-Content -LiteralPath $reportMd -Value $md -Encoding UTF8
    Add-Result "OK" "Rapor dosyalari yazildi: raporlar/kontrol-raporu.json, raporlar/kontrol-raporu.md"
  }

  Write-Host ""
  Write-Host "Ozet: $Script:FailCount FAIL, $Script:WarnCount UYARI, $Script:ManualCount MANUEL kontrol." -ForegroundColor White
  if ($Script:FailCount -gt 0) { exit 1 }
} finally {
  Pop-Location
}


