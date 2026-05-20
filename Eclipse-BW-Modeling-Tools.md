# ติดตั้ง BW Modeling Tools บน Eclipse

คู่มือติดตั้ง Front-End Component ของ BW Modeling Tools สำหรับ SAP BW/4HANA และ SAP BW powered by SAP HANA

## ข้อกำหนดเบื้องต้น

- Eclipse 2026-03 (เช่น Eclipse IDE for Java Developers)
- ดาวน์โหลด Eclipse ได้จาก https://www.eclipse.org/downloads/

## ขั้นตอนการติดตั้ง

### 1. เปิด Install New Software

ใน Eclipse เลือกเมนู **Help > Install New Software...**

### 2. เพิ่ม Update Site

ในช่อง **Work with:** พิมพ์ URL ต่อไปนี้แล้วกด Enter:

```
https://tools.hana.ondemand.com/2026-03
```

รอจนกว่ารายการ Feature จะแสดงขึ้นมา

### 3. เลือก Feature ที่ต้องการ

เลือก checkbox ของ:

> **Modeling Tools for SAP BW/4HANA and SAP BW powered by SAP HANA**

จากนั้นกด **Next**

### 4. ตรวจสอบรายการที่จะติดตั้ง

หน้าถัดไปจะแสดงรายการ Feature และ Dependencies ทั้งหมดที่จะถูกติดตั้ง  
ตรวจสอบแล้วกด **Next**

### 5. ยืนยัน License

อ่านและยืนยัน License Agreement จากนั้นกด **Finish** เพื่อเริ่มการติดตั้ง

> Eclipse จะดาวน์โหลดและติดตั้ง Plugin โดยอัตโนมัติ  
> หลังจากติดตั้งเสร็จ Eclipse จะแนะนำให้ Restart — กด **Restart Now**

## สรุปขั้นตอน

| ขั้นตอน | การดำเนินการ |
|---|---|
| 1 | Help > Install New Software... |
| 2 | เพิ่ม URL: `https://tools.hana.ondemand.com/2026-03` |
| 3 | เลือก **Modeling Tools for SAP BW/4HANA and SAP BW powered by SAP HANA** |
| 4 | Next → Next |
| 5 | ยืนยัน License → Finish |
| 6 | Restart Eclipse |
