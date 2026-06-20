param(
    [string]$Workdir = "",
    [switch]$CheckOnly
)

$ErrorActionPreference = "Stop"

try {
    $utf8 = [System.Text.UTF8Encoding]::new($false)
    [Console]::OutputEncoding = $utf8
    $OutputEncoding = $utf8
} catch {
    # Older PowerShell versions may not allow changing every encoding surface.
}

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$ReportDir = Join-Path $Root ".tez-gui-yedekler"
$Report = Join-Path $ReportDir "guncelleme-raporu-$Stamp.md"
$BackupDir = Join-Path $ReportDir "guncelleme-yedegi-$Stamp"
$Lines = New-Object System.Collections.Generic.List[string]
$Git = $null

function Add-Line([string]$Text) {
    $Lines.Add($Text) | Out-Null
    Write-Host $Text
}

function Save-Report {
    New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
    Set-Content -LiteralPath $Report -Value $Lines -Encoding UTF8
    Write-Host ""
    Write-Host "Rapor: $Report"
}

function Resolve-GitCommand {
    $cmd = Get-Command git -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    $candidates = @(
        "$env:ProgramFiles\Git\cmd\git.exe",
        "$env:ProgramFiles\Git\bin\git.exe",
        "${env:ProgramFiles(x86)}\Git\cmd\git.exe",
        "${env:ProgramFiles(x86)}\Git\bin\git.exe",
        "$env:LOCALAPPDATA\Programs\Git\cmd\git.exe",
        "$env:LOCALAPPDATA\Programs\Git\bin\git.exe"
    )
    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate)) {
            return $candidate
        }
    }
    $githubDesktop = Join-Path $env:LOCALAPPDATA "GitHubDesktop"
    if (Test-Path -LiteralPath $githubDesktop) {
        $desktopGit = Get-ChildItem -LiteralPath $githubDesktop -Directory -Filter "app-*" -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending |
            ForEach-Object { Join-Path $_.FullName "resources\app\git\cmd\git.exe" } |
            Where-Object { Test-Path -LiteralPath $_ } |
            Select-Object -First 1
        if ($desktopGit) { return $desktopGit }
    }
    return $null
}

function Test-GitRef([string]$Ref) {
    & $Git rev-parse --verify --quiet $Ref *> $null
    return ($LASTEXITCODE -eq 0)
}

function Invoke-GitNoPrompt([string[]]$Arguments) {
    $oldPrompt = $env:GIT_TERMINAL_PROMPT
    $oldGcm = $env:GCM_INTERACTIVE
    $oldAskpass = $env:GIT_ASKPASS
    $oldErrorAction = $ErrorActionPreference
    try {
        $ErrorActionPreference = "Continue"
        $env:GIT_TERMINAL_PROMPT = "0"
        $env:GCM_INTERACTIVE = "Never"
        $env:GIT_ASKPASS = "echo"
        try {
            & $Git -c credential.helper= -c core.askPass= @Arguments 2>&1 | Out-Null
            return $LASTEXITCODE
        } catch {
            return 1
        }
    } finally {
        $ErrorActionPreference = $oldErrorAction
        if ($null -eq $oldPrompt) { Remove-Item Env:\GIT_TERMINAL_PROMPT -ErrorAction SilentlyContinue } else { $env:GIT_TERMINAL_PROMPT = $oldPrompt }
        if ($null -eq $oldGcm) { Remove-Item Env:\GCM_INTERACTIVE -ErrorAction SilentlyContinue } else { $env:GCM_INTERACTIVE = $oldGcm }
        if ($null -eq $oldAskpass) { Remove-Item Env:\GIT_ASKPASS -ErrorAction SilentlyContinue } else { $env:GIT_ASKPASS = $oldAskpass }
    }
}

function Get-PublicUpdateUrls([string]$RemoteUrl) {
    $urls = New-Object System.Collections.Generic.List[string]
    if ($RemoteUrl) { $urls.Add($RemoteUrl.Trim()) | Out-Null }
    $defaultUrl = "https://github.com/kozdemir73/Inonu_FBE_Tez.git"
    if (-not ($urls -contains $defaultUrl)) { $urls.Add($defaultUrl) | Out-Null }
    return $urls
}

function Read-LocalVersion {
    $versionFile = Join-Path $Root "VERSION"
    if (Test-Path -LiteralPath $versionFile) {
        $value = (Get-Content -LiteralPath $versionFile -Raw -ErrorAction SilentlyContinue).Trim()
        if ($value) { return $value }
    }
    return "bilinmiyor"
}

function Read-RemoteVersion([string]$Ref) {
    $value = (& $Git show "$Ref`:VERSION" 2>$null)
    if ($LASTEXITCODE -eq 0 -and $value) {
        return ($value -join "`n").Trim()
    }
    $guiSource = (& $Git show "$Ref`:tez_yonetim_gui.py" 2>$null)
    if ($LASTEXITCODE -eq 0 -and $guiSource) {
        $match = [regex]::Match(($guiSource -join "`n"), 'APP_VERSION\s*=\s*["'']([^"'']+)["'']')
        if ($match.Success) { return $match.Groups[1].Value.Trim() }
    }
    return "bilinmiyor"
}

function Convert-VersionText([string]$Text) {
    if (-not $Text -or $Text -eq "bilinmiyor") { return $null }
    $clean = $Text.Trim()
    if ($clean.StartsWith("v", [System.StringComparison]::OrdinalIgnoreCase)) {
        $clean = $clean.Substring(1)
    }
    $parts = @($clean -split "\.")
    while ($parts.Count -lt 3) { $parts += "0" }
    $numeric = ($parts | ForEach-Object {
        if ($_ -match "^\d+") { $Matches[0] } else { "0" }
    }) -join "."
    try { return [version]$numeric } catch { return $null }
}

function Compare-VersionText([string]$LocalVersion, [string]$RemoteVersion) {
    $localParsed = Convert-VersionText $LocalVersion
    $remoteParsed = Convert-VersionText $RemoteVersion
    if ($null -eq $localParsed -or $null -eq $remoteParsed) {
        if ($LocalVersion -eq $RemoteVersion) { return 0 }
        return $null
    }
    return $localParsed.CompareTo($remoteParsed)
}

function Get-ChangeSummary([string]$FromRef, [string]$ToRef) {
    $commits = @(& $Git log --oneline --max-count=8 "$FromRef..$ToRef" 2>$null)
    $files = @(& $Git diff --name-only "$FromRef..$ToRef" 2>$null)
    $summary = New-Object System.Collections.Generic.List[string]

    if ($commits.Count -gt 0) {
        $summary.Add("Öne çıkan kayıtlar:") | Out-Null
        foreach ($commit in $commits) { $summary.Add("- $commit") | Out-Null }
    }

    if ($files.Count -gt 0) {
        $guiFiles = @($files | Where-Object { $_ -match 'tez_yonetim_gui\.py|\.ps1$|VERSION|README|\.md$' })
        $templateFiles = @($files | Where-Object { $_ -match 'inonu-fbe-tez-sablonu-2025/.*\.(tex|cls|bib)$' })
        $otherFiles = @($files | Where-Object { $guiFiles -notcontains $_ -and $templateFiles -notcontains $_ })
        $summary.Add("") | Out-Null
        $summary.Add("Değişecek dosya grupları:") | Out-Null
        if ($guiFiles.Count -gt 0) { $summary.Add("- Panel ve yardımcı komutlar: $($guiFiles.Count) dosya") | Out-Null }
        if ($templateFiles.Count -gt 0) { $summary.Add("- Tez şablonu dosyaları: $($templateFiles.Count) dosya") | Out-Null }
        if ($otherFiles.Count -gt 0) { $summary.Add("- Diğer destek dosyaları: $($otherFiles.Count) dosya") | Out-Null }
    }

    if ($summary.Count -eq 0) {
        $summary.Add("- Sürüm değişikliği bulundu, fakat ayrıntılı değişiklik listesi okunamadı.") | Out-Null
    }
    return $summary
}

function Backup-Workdir {
    param([string]$Source)
    if (-not $Source -or -not (Test-Path -LiteralPath $Source)) { return "" }
    New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
    $leaf = Split-Path -Leaf $Source
    if (-not $leaf) { $leaf = "calisma-klasoru" }
    $target = Join-Path $BackupDir $leaf
    Copy-Item -LiteralPath $Source -Destination $target -Recurse -Force
    return $target
}

function Restore-Workdir {
    param([string]$Backup, [string]$Target)
    if (-not $Backup -or -not $Target) { return }
    if (-not (Test-Path -LiteralPath $Backup)) { return }
    if (Test-Path -LiteralPath $Target) {
        Remove-Item -LiteralPath $Target -Recurse -Force
    }
    Copy-Item -LiteralPath $Backup -Destination $Target -Recurse -Force
}

Push-Location $Root
try {
    Add-Line "# Güncelleme Özeti"
    Add-Line ""
    Add-Line "Tarih: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    Add-Line "Panel klasörü: $Root"
    if ($Workdir) { Add-Line "Tez çalışma klasörü: $Workdir" }
    Add-Line ""

    $Git = Resolve-GitCommand
    if (-not $Git) {
        Add-Line "Durum: Güncelleme yapılamadı."
        Add-Line "Neden: Git bulunamadı."
        Add-Line "Çözüm: Git for Windows veya GitHub Desktop kurulabilir. GitHub hesabı zorunlu değildir; public güncelleme deposunu okumak için yalnızca git.exe gerekir."
        Save-Report
        exit 2
    }

    $inside = (& $Git rev-parse --is-inside-work-tree 2>$null)
    if ($LASTEXITCODE -ne 0 -or $inside.Trim() -ne "true") {
        Add-Line "Durum: Güncelleme yapılamadı."
        Add-Line "Neden: Bu klasör bir Git deposu değil."
        Save-Report
        exit 2
    }

    $branch = (& $Git rev-parse --abbrev-ref HEAD).Trim()
    $localVersion = Read-LocalVersion
    $localHead = (& $Git rev-parse --short HEAD).Trim()
    $headFull = (& $Git rev-parse HEAD).Trim()

    $remoteUrl = (& $Git remote get-url origin 2>$null)
    if ($LASTEXITCODE -ne 0 -or -not $remoteUrl) {
        Add-Line "Durum: Güncelleme yapılamadı."
        Add-Line "Neden: GitHub bağlantısı (origin) tanımlı değil."
        Save-Report
        exit 2
    }

    Add-Line "GitHub kontrol ediliyor..."
    Add-Line "Uzak depo: $remoteUrl"
    $fetchCode = Invoke-GitNoPrompt -Arguments @("fetch", "--prune", "origin")
    if ($fetchCode -ne 0) {
        foreach ($publicUrl in (Get-PublicUpdateUrls $remoteUrl)) {
            if (-not $publicUrl -or $publicUrl -eq "origin") { continue }
            Add-Line "Anonim okuma deneniyor: $publicUrl"
            $fetchCode = Invoke-GitNoPrompt -Arguments @(
                "fetch",
                "--prune",
                $publicUrl,
                "+refs/heads/*:refs/remotes/origin/*"
            )
            if ($fetchCode -eq 0) {
                break
            }
        }
    }
    if ($fetchCode -ne 0) {
        Add-Line "Durum: Güncelleme yapılamadı."
        Add-Line "Neden: Güncelleme deposu herkese açık okunamadı veya internet bağlantısı yok."
        Add-Line "Not: Öğrencilerin GitHub hesabı olması gerekmez; bunun için güncelleme deposu public olmalı ya da kurumsal açık indirme adresi kullanılmalıdır."
        Add-Line "Kontrol: Tarayıcıda https://github.com/kozdemir73/Inonu_FBE_Tez adresi oturum açmadan görünmüyorsa öğrenciler güncelleme alamaz."
        Save-Report
        exit 2
    }

    $upstream = (& $Git rev-parse --abbrev-ref --symbolic-full-name "@{u}" 2>$null)
    if ($LASTEXITCODE -ne 0 -or -not $upstream) {
        if (Test-GitRef "origin/$branch") {
            $upstream = "origin/$branch"
        } elseif (Test-GitRef "origin/main") {
            $upstream = "origin/main"
        } elseif (Test-GitRef "origin/master") {
            $upstream = "origin/master"
        } else {
            Add-Line "Durum: Güncelleme yapılamadı."
            Add-Line "Neden: Güncellenecek GitHub dalı bulunamadı."
            Save-Report
            exit 2
        }
    }

    $upstream = $upstream.Trim()
    $upstreamFull = (& $Git rev-parse $upstream).Trim()
    $remoteHead = (& $Git rev-parse --short $upstream).Trim()
    $remoteVersion = Read-RemoteVersion $upstream
    $versionCompare = Compare-VersionText $localVersion $remoteVersion

    Add-Line "Sürüm: $localVersion -> $remoteVersion"
    Add-Line "Kayıt: $localHead -> $remoteHead"
    Add-Line ""

    if ($headFull -eq $upstreamFull) {
        Add-Line "Durum: Panel zaten güncel."
        Add-Line "Dosyalara dokunulmadı."
        Save-Report
        exit 0
    }

    if ($null -ne $versionCompare -and $versionCompare -gt 0) {
        Add-Line "Durum: Güncelleme uygulanmadı."
        Add-Line "Neden: Yerel sürüm GitHub sürümünden daha yeni görünüyor."
        Save-Report
        exit 3
    }

    $mergeBase = (& $Git merge-base HEAD $upstream).Trim()
    if ($mergeBase -ne $headFull) {
        Add-Line "Durum: Otomatik güncelleme uygulanmadı."
        Add-Line "Neden: Yerel klasörde GitHub ile otomatik birleştirilemeyecek kayıt farkı var."
        Add-Line "Dosyalarınız korunması için işlem durduruldu."
        Save-Report
        exit 3
    }

    Add-Line "Bu güncellemede görünen başlıca değişiklikler:"
    foreach ($line in (Get-ChangeSummary $headFull $upstream)) {
        Add-Line $line
    }
    Add-Line ""

    $dirty = @(& $Git status --porcelain)
    if ($dirty.Count -gt 0) {
        $backupPath = Backup-Workdir $Workdir
        Add-Line "Durum: Güncelleme uygulanmadı."
        Add-Line "Neden: Yerelde kaydedilmemiş dosya değişiklikleri var."
        Add-Line "Tez dosyalarınız ezilmedi."
        if ($backupPath) { Add-Line "Yedek alındı: $backupPath" }
        Add-Line ""
        Add-Line "Öneri: Önce mevcut tez dosyalarınızı kaydedin. İsterseniz bu klasörü ayrı bir yere kopyalayıp sonra güncellemeyi tekrar deneyin."
        Save-Report
        exit 4
    }

    if ($CheckOnly) {
        Add-Line "Durum: Güncelleme hazır."
        Add-Line "Bu ekranda yalnızca bilgi verildi; henüz dosyalara dokunulmadı."
        Save-Report
        exit 0
    }

    $backupForRestore = Backup-Workdir $Workdir
    if ($backupForRestore) {
        Add-Line "Güvenlik yedeği alındı: $backupForRestore"
    }

    Add-Line "Güncelleme uygulanıyor..."
    & $Git merge --ff-only $upstream
    if ($LASTEXITCODE -ne 0) {
        Add-Line "Güncelleme sırasında sorun oluştu. Eski duruma dönülüyor..."
        & $Git reset --hard $headFull *> $null
        Restore-Workdir $backupForRestore $Workdir
        Add-Line "Durum: Güncelleme başarısız oldu; eski klasör geri getirildi."
        Save-Report
        exit 2
    }

    $newVersion = Read-LocalVersion
    $newHead = (& $Git rev-parse --short HEAD).Trim()
    Add-Line "Durum: Güncelleme tamamlandı."
    Add-Line "Yeni sürüm: $newVersion"
    Add-Line "Yeni kayıt: $newHead"
    Add-Line "Tez dosyalarınız için yedek korundu."
    Save-Report
    exit 0
} catch {
    Add-Line "Beklenmeyen bir sorun oluştu. Eski duruma dönülmeye çalışılıyor..."
    try {
        if ($headFull -and $Git) { & $Git reset --hard $headFull *> $null }
        if ($backupForRestore) { Restore-Workdir $backupForRestore $Workdir }
        Add-Line "Durum: Güncelleme tamamlanmadı; alınan yedek geri yüklendi."
    } catch {
        Add-Line "Durum: Geri yükleme sırasında da sorun oluştu. Yedek klasörünü kontrol edin: $BackupDir"
    }
    Add-Line "Neden: $($_.Exception.Message)"
    Save-Report
    exit 2
} finally {
    Pop-Location
}
