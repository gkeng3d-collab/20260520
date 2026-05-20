# SAP GUI Profile Migration

ย้าย SAP GUI Profile (รายการ SAP Systems) จากเครื่องเดิมไปเครื่องใหม่

## ที่อยู่ไฟล์ Profile

| เวอร์ชัน | ไฟล์ | ที่อยู่ |
|---|---|---|
| SAP GUI 7.40+ | `SAPUILandscape.xml` | `%APPDATA%\SAP\Common\` |
| SAP GUI เก่า | `saplogon.ini` | `C:\Program Files (x86)\SAP\FrontEnd\SAPgui\` |

## วิธีใช้งาน

### 1. Export จากเครื่องเดิม

```powershell
# Export ไปยัง Desktop (default)
.\Export-SAPProfile.ps1

# หรือกำหนด folder เอง
.\Export-SAPProfile.ps1 -Destination "D:\Backup\SAP"
```

### 2. Copy ไฟล์ไปเครื่องใหม่

นำ folder ที่ได้จาก Export ไปวางบนเครื่องใหม่ (USB / Network Share / Cloud)

### 3. Import บนเครื่องใหม่

```powershell
.\Import-SAPProfile.ps1 -Source "D:\SAP_Profile_Backup"
```

> สคริปต์จะสำรองไฟล์เดิม (`.bak`) ก่อนทับทุกครั้ง

## วิธีย้ายด้วยตนเอง (Manual)

1. เปิด Run (`Win+R`) พิมพ์ `%APPDATA%\SAP\Common`
2. Copy `SAPUILandscape.xml`
3. บนเครื่องใหม่ วางไฟล์ที่ `%APPDATA%\SAP\Common\`
4. เปิด SAP Logon ใหม่
