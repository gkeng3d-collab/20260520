# Import-SAPProfile.ps1
# นำเข้า SAP GUI Profile จาก folder ที่กำหนด

param(
    [Parameter(Mandatory)]
    [string]$Source
)

$sapCommonDir    = "$env:APPDATA\SAP\Common"
$sapLandscapeDst = "$sapCommonDir\SAPUILandscape.xml"
$sapLogonIniDst  = "C:\Program Files (x86)\SAP\FrontEnd\SAPgui\saplogon.ini"

if (-not (Test-Path $Source)) {
    Write-Error "ไม่พบ folder ต้นทาง: $Source"
    exit 1
}

$landscapeSrc = Join-Path $Source "SAPUILandscape.xml"
$logonIniSrc  = Join-Path $Source "saplogon.ini"

if (Test-Path $landscapeSrc) {
    if (-not (Test-Path $sapCommonDir)) {
        New-Item -ItemType Directory -Path $sapCommonDir | Out-Null
    }
    # สำรองของเดิมก่อน
    if (Test-Path $sapLandscapeDst) {
        Copy-Item $sapLandscapeDst "$sapLandscapeDst.bak" -Force
        Write-Host "สำรองไฟล์เดิมไว้ที่: $sapLandscapeDst.bak" -ForegroundColor Yellow
    }
    Copy-Item $landscapeSrc -Destination $sapLandscapeDst -Force
    Write-Host "Import SAPUILandscape.xml สำเร็จ" -ForegroundColor Green
}

if (Test-Path $logonIniSrc) {
    if (Test-Path $sapLogonIniDst) {
        Copy-Item $sapLogonIniDst "$sapLogonIniDst.bak" -Force
        Write-Host "สำรองไฟล์เดิมไว้ที่: $sapLogonIniDst.bak" -ForegroundColor Yellow
    }
    Copy-Item $logonIniSrc -Destination $sapLogonIniDst -Force
    Write-Host "Import saplogon.ini สำเร็จ" -ForegroundColor Green
}

Write-Host "`nเปิด SAP Logon ใหม่เพื่อให้ระบบอัปเดต" -ForegroundColor Cyan
