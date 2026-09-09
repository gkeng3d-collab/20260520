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

## ตรวจสอบว่ามีระบบที่ต้องการอยู่ใน profile หรือไม่

ใช้ตรวจว่าเครื่องนี้เห็นระบบที่ต้องการ (เช่นระบบ BW ชื่อ `zimp_d01`) แล้วหรือยัง

```powershell
# หาระบบตามชื่อ / SID (รองรับ wildcard เช่น *d01*)
.\Find-SAPSystem.ps1 -Name zimp_d01

# แสดงทุกระบบที่มีใน profile
.\Find-SAPSystem.ps1 -All

# ตรวจจากไฟล์ที่ export ไว้ (ยังไม่ import ก็ตรวจได้)
.\Find-SAPSystem.ps1 -Name zimp_d01 -ExtraFile "D:\SAP_Profile_Backup\SAPUILandscape.xml"
```

สคริปต์จะตรวจทั้ง `SAPUILandscape.xml`, `SAPUILandscapeGlobal.xml`, ไฟล์ที่ถูก `Include`
(landscape ส่วนกลางบน share ซึ่งมักเก็บระบบอย่าง BW ไว้) และ `saplogon.ini` ของ SAP GUI รุ่นเก่า
แล้วแสดงชื่อระบบ, SID, message server / application server, logon group, SAProuter และ folder ที่อยู่

> ถ้า `Include` ชี้ไป share ที่เข้าถึงไม่ได้ สคริปต์จะเตือน — ระบบที่หาไม่เจออาจอยู่ในไฟล์นั้น

## วิธีย้ายด้วยตนเอง (Manual)

1. เปิด Run (`Win+R`) พิมพ์ `%APPDATA%\SAP\Common`
2. Copy `SAPUILandscape.xml`
3. บนเครื่องใหม่ วางไฟล์ที่ `%APPDATA%\SAP\Common\`
4. เปิด SAP Logon ใหม่
