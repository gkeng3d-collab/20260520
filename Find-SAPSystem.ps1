# Find-SAPSystem.ps1
# ค้นหาระบบ SAP ใน profile ของเครื่องนี้ (เช่น zimp_d01) ว่ามีอยู่จริงหรือไม่
#
# ตัวอย่าง:
#   .\Find-SAPSystem.ps1 -Name zimp_d01     # หาเฉพาะที่ตรง (รองรับ wildcard เช่น *d01*)
#   .\Find-SAPSystem.ps1 -All               # แสดงทุกระบบที่มีใน profile

param(
    [string]$Name,
    [switch]$All,
    [string[]]$ExtraFile
)

if (-not $Name -and -not $All) {
    Write-Error "ต้องระบุ -Name <ชื่อระบบ> หรือ -All"
    exit 1
}

$sapCommonDir = "$env:APPDATA\SAP\Common"

# แสดงตาราง โดยกำหนดความกว้างเอง (กัน Format-Table ไม่พิมพ์อะไรตอน output ถูก redirect)
function Show-SystemTable {
    param([object[]]$Rows)
    ($Rows | Format-Table Name, SystemId, Server, Group, Router, Workspace, File -AutoSize |
        Out-String -Width 250) | Write-Host
}

# รวบรวมไฟล์ profile ที่จะตรวจ
$xmlFiles = New-Object System.Collections.Generic.List[string]
foreach ($f in @("$sapCommonDir\SAPUILandscape.xml", "$sapCommonDir\SAPUILandscapeGlobal.xml")) {
    if (Test-Path $f) { $xmlFiles.Add((Resolve-Path $f).Path) }
}
foreach ($f in $ExtraFile) {
    if (Test-Path $f) { $xmlFiles.Add((Resolve-Path $f).Path) }
    else { Write-Warning "ไม่พบไฟล์ที่ระบุ: $f" }
}

# ไฟล์ที่ถูก include ไว้ (central landscape บน share) มักเก็บระบบส่วนกลางเช่นระบบ BW
foreach ($f in @($xmlFiles)) {
    try { $doc = [xml](Get-Content $f -Raw) } catch { continue }
    foreach ($inc in $doc.SelectNodes("//Include")) {
        $url = $inc.url
        if ($url -and $url -notmatch '^(https?|ftp)://') {
            $p = $url -replace '^file:[\\/]{0,3}', ''
            $p = [Environment]::ExpandEnvironmentVariables($p)
            if (Test-Path $p) {
                $rp = (Resolve-Path $p).Path
                if (-not $xmlFiles.Contains($rp)) { $xmlFiles.Add($rp) }
            } else {
                Write-Warning "Include ที่เข้าถึงไม่ได้ (ระบบอาจอยู่ในไฟล์นี้): $url"
            }
        } elseif ($url) {
            Write-Warning "Include เป็น URL ตรวจจากไฟล์ในเครื่องไม่ได้: $url"
        }
    }
}

if ($xmlFiles.Count -eq 0) {
    Write-Warning "ไม่พบ SAPUILandscape.xml ใน $sapCommonDir (ยังไม่เคยเปิด SAP Logon บนเครื่องนี้?)"
}

$systems = @()

foreach ($file in $xmlFiles) {
    try {
        $doc = [xml](Get-Content $file -Raw)
    } catch {
        Write-Warning "อ่านไฟล์ไม่ได้: $file"
        continue
    }

    # ตาราง lookup: message server / router / workspace
    $msMap = @{}
    foreach ($ms in $doc.SelectNodes("//Messageserver")) { $msMap[$ms.uuid] = "$($ms.host):$($ms.port)" }
    $rtMap = @{}
    foreach ($rt in $doc.SelectNodes("//Router")) { $rtMap[$rt.uuid] = $rt.router }
    $wsMap = @{}
    foreach ($ws in $doc.SelectNodes("//Workspaces/Workspace")) {
        foreach ($item in $ws.SelectNodes(".//Item")) {
            if (-not $item.serviceid) { continue }
            # ไล่ชื่อ folder ย้อนขึ้นไปจนถึง Workspace เพื่อให้เห็นว่าอยู่ folder ไหน
            $path = @()
            $parent = $item.ParentNode
            while ($parent -and $parent.LocalName -ne "Workspaces") {
                if ($parent.name) { $path = @($parent.name) + $path }
                $parent = $parent.ParentNode
            }
            $label = $path -join " / "
            if ($wsMap.ContainsKey($item.serviceid)) { $wsMap[$item.serviceid] += "; $label" }
            else { $wsMap[$item.serviceid] = $label }
        }
    }

    foreach ($svc in $doc.SelectNodes("//Services/Service")) {
        $target = if ($svc.server) { $svc.server }
                  elseif ($svc.msid -and $msMap.ContainsKey($svc.msid)) { $msMap[$svc.msid] }
                  else { "" }
        $systems += [pscustomobject]@{
            Name       = $svc.name
            SystemId   = $svc.systemid
            Server     = $target
            Group      = $svc.group
            Router     = if ($svc.routerid -and $rtMap.ContainsKey($svc.routerid)) { $rtMap[$svc.routerid] } else { "" }
            Workspace  = if ($wsMap.ContainsKey($svc.uuid)) { $wsMap[$svc.uuid] } else { "(ไม่อยู่ใน workspace ใด)" }
            File       = Split-Path $file -Leaf
        }
    }
}

# saplogon.ini (SAP GUI รุ่นเก่า) - ค้นแบบข้อความ
$iniPath = "C:\Program Files (x86)\SAP\FrontEnd\SAPgui\saplogon.ini"
$iniHits = @()
if (Test-Path $iniPath) {
    $pattern = if ($All) { "." } else { [regex]::Escape($Name) -replace '\\\*', '.*' }
    $iniHits = Select-String -Path $iniPath -Pattern $pattern -AllMatches -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "ไฟล์ profile ที่ตรวจ:" -ForegroundColor Cyan
if ($xmlFiles.Count -gt 0) { $xmlFiles | ForEach-Object { Write-Host "  - $_" } } else { Write-Host "  (ไม่มี)" }
if (Test-Path $iniPath) { Write-Host "  - $iniPath" }
Write-Host ""
Write-Host "พบระบบทั้งหมด $($systems.Count) รายการ" -ForegroundColor Cyan

if ($All) {
    Show-SystemTable ($systems | Sort-Object Name)
    exit 0
}

$wildcard = if ($Name -match '[\*\?]') { $Name } else { "*$Name*" }
$found = $systems | Where-Object { $_.Name -like $wildcard -or $_.SystemId -like $wildcard }

Write-Host ""
if ($found) {
    Write-Host "พบ '$Name' ใน profile:" -ForegroundColor Green
    Show-SystemTable $found
} else {
    Write-Host "ไม่พบ '$Name' ใน profile ของเครื่องนี้" -ForegroundColor Red
    $sid = ($Name -split '[_\-\s]')[-1]
    if ($sid -and $sid -ne $Name) {
        $near = $systems | Where-Object { $_.Name -like "*$sid*" -or $_.SystemId -like "*$sid*" }
        if ($near) {
            Write-Host "แต่พบรายการที่ใกล้เคียง (SID '$sid'):" -ForegroundColor Yellow
            Show-SystemTable $near
        }
    }
    Write-Host "ดูรายการทั้งหมดด้วย: .\Find-SAPSystem.ps1 -All" -ForegroundColor Cyan
}

if ($iniHits) {
    Write-Host "พบข้อความที่ตรงใน saplogon.ini (SAP GUI รุ่นเก่า):" -ForegroundColor Yellow
    $iniHits | Select-Object -First 20 | ForEach-Object { Write-Host "  บรรทัด $($_.LineNumber): $($_.Line.Trim())" }
}
