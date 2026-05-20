# Export-SAPProfile.ps1
# ส่งออก SAP GUI Profile ไปยัง folder ที่กำหนด

param(
    [string]$Destination = "$env:USERPROFILE\Desktop\SAP_Profile_Backup"
)

$sapLandscapePath = "$env:APPDATA\SAP\Common\SAPUILandscape.xml"
$sapLogonIniPath  = "C:\Program Files (x86)\SAP\FrontEnd\SAPgui\saplogon.ini"

if (-not (Test-Path $Destination)) {
    New-Item -ItemType Directory -Path $Destination | Out-Null
}

$exported = @()

if (Test-Path $sapLandscapePath) {
    Copy-Item $sapLandscapePath -Destination $Destination
    $exported += "SAPUILandscape.xml"
}

if (Test-Path $sapLogonIniPath) {
    Copy-Item $sapLogonIniPath -Destination $Destination
    $exported += "saplogon.ini"
}

if ($exported.Count -eq 0) {
    Write-Warning "ไม่พบไฟล์ SAP GUI Profile บนเครื่องนี้"
} else {
    Write-Host "Export สำเร็จ: $($exported -join ', ')" -ForegroundColor Green
    Write-Host "บันทึกที่: $Destination" -ForegroundColor Cyan
}
