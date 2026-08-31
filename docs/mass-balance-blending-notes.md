# Mass Balance (Blending) — โน้ตเตรียมคุย Consultant

เป้าหมาย: ได้ **tcode + ชื่อ table + วิธีคิด** ที่ชัดเจน เพื่อเอาไปทำ database ของตัวเอง

---

## 1. พรุ่งนี้ต้องได้อะไรกลับมา (3 ข้อ)

1. **tcode** ที่ user ใช้ดู mass balance ของ blend จริง ๆ ในงานประจำวัน
2. **table + field** ที่อยู่หลัง tcode นั้น (ตัวจริง ไม่ใช่แค่ชื่อรายงาน)
3. **วิธีคิด**: mat in / mat out / gain-loss คิดจาก movement type ไหน หน่วยอะไร ตัดยอด ณ จุดไหน

ถ้าได้ครบ 3 ข้อนี้ = ทำ database ต่อเองได้

---

## 2. เล่าให้ consult ฟังก่อน (สั้น ๆ)

> "ผมจะทำ database ของ mass balance ฝั่ง blending เอง เพื่อทำรายงาน/วิเคราะห์ต่อ
> ตอนนี้ผมยังไม่รู้ว่าเลข mass balance ที่ user ดูอยู่ มันมาจากหน้าจอไหนใน SAP
> ผมขอ 3 อย่าง: tcode ที่ user ใช้จริง, table+field ที่อยู่ข้างหลัง, และวิธีคิดตัวเลข
> ผมไม่ได้จะแก้อะไรใน SAP แค่ขอ read/extract"

**ย้ำให้ชัด**: ขอ *table* ไม่ใช่ขอ *report* — เพราะ report เอาไปต่อ database ไม่ได้

---

## 3. Mass balance ของ blending "มาจากไหน" — มีได้ 4 ชั้น

ถามให้ได้ว่าโรงงานเราใช้ชั้นไหนเป็นตัวจริง

| ชั้น | คืออะไร | tcode ดู |
|---|---|---|
| 1. **Recipe / BOM** | สูตรตั้งต้น (planned) | `C203` (master recipe, PP-PI) / `CS03` (BOM) |
| 2. **Material Quantity Calculation (MQC)** | สูตรคำนวณ ที่ใช้ค่า batch (density, %assay) มาคิดปริมาณ component | ใน `COR3` → เมนู Goto → Material Quantity Calculation |
| 3. **Process Order** | แผนของ order นั้น ๆ (component overview) | `COR3` / `CO03` |
| 4. **Actual goods movement** | ของจริงที่เบิก-รับ = mass balance ตัวจริง | `MB51`, `COOISPI` |

> **คำถามหลักที่ต้องถาม**: "เลข mass balance ที่ user ดู มาจากชั้นไหน — planned จาก order หรือ actual จาก goods movement?"
> ถ้าตอบไม่ตรงกับทั้ง 4 ชั้น → แปลว่ามาจาก **Z-report หรือระบบนอก** (blend optimizer / LIMS / DCS) ต้องขอ interface spec แทน

---

## 4. Mat In / Mat Out คิดยังไง

ทั้งคู่มาจาก **material document ตัวเดียวกัน** ต่างกันที่ movement type

| | คืออะไร | Movement type | tcode |
|---|---|---|---|
| **Mat In** | component ที่เบิกเข้า blend | `261` (เบิกเข้า order), `262` = กลับรายการ | `MB51` filter ด้วยเลข order |
| **Mat Out** | product ที่รับออกจาก blend | `101` (GR เข้า stock), `102` = กลับรายการ, `531` (by-product / co-product) | `MB51` filter ด้วยเลข order |
| **Loss / Gain** | ส่วนต่าง | คำนวณเอง | — |

**สูตร (ต่อ 1 process order):**

```
MAT IN   = Σ MENGE (BWART 261) − Σ MENGE (BWART 262)
MAT OUT  = Σ MENGE (BWART 101) − Σ MENGE (BWART 102) + Σ MENGE (BWART 531)
GAIN/LOSS = MAT OUT − MAT IN
LOSS %    = (MAT IN − MAT OUT) / MAT IN × 100
```

**ข้อควรระวัง 3 อย่าง (ต้องถาม consult):**

1. **เครื่องหมาย** — อย่าดูแค่ movement type ให้ใช้ field `SHKZG` แทน
   (`S` = debit/รับเข้า, `H` = credit/จ่ายออก) ปลอดภัยกว่าและครอบคลุม movement type แปลก ๆ
2. **หน่วย** — `MENGE`/`MEINS` = base unit, `ERFMG`/`ERFME` = หน่วยที่คีย์เข้าไป
   ถ้า blend เป็นของเหลว ต้องถามว่า mass balance ทำที่ **KG หรือ L** และแปลงด้วย density ตัวไหน
3. **movement type อื่นที่ต้องนับด้วยหรือเปล่า** — `551/552` (scrap), `309/311` (transfer/re-blend), `701/702` (ปรับ physical inventory)
   ถ้าไม่นับ ตัวเลข gain/loss จะเพี้ยน

---

## 5. Table ที่น่าจะต้องใช้ (เอาไปยืนยันกับ consult)

### กลุ่ม goods movement — ตัวหลักของ mass balance
| Table | คืออะไร | Field สำคัญ |
|---|---|---|
| `MKPF` | Material document — header | MBLNR, MJAHR, BUDAT (posting date), BLDAT |
| `MSEG` | Material document — item | MBLNR, ZEILE, BWART, MATNR, WERKS, LGORT, CHARG, MENGE, MEINS, ERFMG, ERFME, SHKZG, **AUFNR** |

> **ถามให้ชัด: ระบบเป็น ECC หรือ S/4HANA?**
> ถ้าเป็น S/4 ตัวจริงคือ table **`MATDOC`** ส่วน MKPF/MSEG กลายเป็น compatibility view — select ได้แต่ performance/field ต่างกัน

### กลุ่ม process order
| Table | คืออะไร |
|---|---|
| `AUFK` | Order master (AUFNR, AUART order type, WERKS) |
| `AFKO` | Order header PP (GAMNG = ปริมาณสั่งผลิต, PLNBEZ = material) |
| `AFPO` | Order item (MATNR, PSMNG = สั่ง, WEMNG = รับแล้ว, CHARG) |
| `RESB` | **Component / reservation** = mat in ฝั่ง *planned* (BDMNG = ต้องการ, ENMNG = เบิกไปแล้ว) |
| `AFRU` | Confirmation (GMNG = yield, XMNG = scrap) |

### กลุ่ม recipe / BOM (planned)
`PLKO` / `PLPO` / `PLMZ` (recipe header / operation / component allocation), `MAST` / `STKO` / `STPO` (BOM)

### กลุ่ม batch + คุณสมบัติ (density, %assay — ตัวที่ใช้แปลงหน่วย)
| Table | คืออะไร |
|---|---|
| `MCH1` / `MCHA` / `MCHB` | Batch master / batch ต่อ plant / batch stock |
| `AUSP` | **ค่า characteristic ของ batch** (density, sulfur, %) ← ตัวนี้สำคัญมากสำหรับ blending |
| `CABN` / `CAWN` | นิยาม characteristic |
| `KSSK` / `KLAH` | ผูก object เข้ากับ class |

### ที่ผมยังไม่ชัวร์ — ต้องให้ consult บอก
- **table ของ Material Quantity Calculation (MQC)** — สูตร mass balance ตัวจริงอยู่ตรงนี้ ขอชื่อ table ตรง ๆ
- **Batch-specific UoM (BSUoM)** — ถ้าใช้ density ต่อ batch แปลง L↔KG ค่า conversion เก็บที่ table ไหน
- **IS-Oil** — ถ้าโรงงานใช้ IS-Oil จะมี quantity conversion (ASTM @15°C, weight in air/vacuum) เป็นอีกชุด table ต่างหาก ต้องถามว่า "หน่วยไหนคือ system of record"

---

## 6. วิธีหา tcode / table ด้วยตัวเอง (ไม่ต้องรอ consult)

### ดู tcode ของหน้าจอที่เปิดอยู่
1. เมนู **System → Status** → ดูช่อง `Transaction` (บอก program + screen ด้วย)
2. เปิดโชว์ถาวร: คลิกลูกศรที่ **status bar มุมล่างขวา** → เลือก `Transaction`
3. หน้า SAP Easy Access: **Extras → Settings → ติ๊ก "Display technical names"** จะเห็น tcode ข้างชื่อเมนูทุกอัน
4. ค้นหา tcode จากคำ: `SE93` หรือเปิด table `TSTCT` ผ่าน `SE16N`

### ดู table/field ที่อยู่หลังช่องบนหน้าจอ ← **อันนี้ใช้บ่อยสุด**
> คลิกที่ช่องนั้น → กด **F1** → กดปุ่ม **Technical Information** (ไอคอนค้อน/ประแจ)
> จะบอก **Table name + Field name** ตรง ๆ

### เปิดดูข้อมูลใน table
- `SE16N` (ดีสุด, export Excel ได้) / `SE16` / `SE11` (ดู structure)
- `ST05` (SQL trace) — เปิด trace แล้วกดรายงาน จะเห็นว่ารายงานนั้นยิงไป table ไหนบ้าง (ถ้ามีสิทธิ์)

### คำสั่ง command field
`/n<tcode>` เปิดใหม่ · `/o<tcode>` เปิด session ใหม่ · `/i` ปิด session · `/nend` ออก

---

## 7. เรื่อง "เอาข้อมูลออกไปทำ database" — ถามเรื่องนี้ด้วย

อย่าจบแค่ table ให้ถามวิธีดึงออกด้วย เพราะ manual export ทุกวันมันไม่ยั่งยืน

ทางเลือกเรียงจากง่าย→ดี:
1. `SE16N` export Excel — ทำมือ ใช้ทดสอบ logic ช่วงแรกได้
2. **CDS View / OData service** — วิธีมาตรฐานบน S/4 ขอให้ consult ชี้ว่ามี view สำเร็จรูปไหม
3. **BW extractor** — ถ้ามี BW อยู่แล้ว: `2LIS_03_BF` (material movement), `2LIS_04_P_COMP` (order component) มันคือ mass balance สำเร็จรูปเลย
4. **SAP Datasphere / RFC / flat file job** — ถ้าจะทำ automate

**สิทธิ์ที่ต้องขอ**: `SE16N` (หรือ SE16) display + `S_TABU_DIS` สำหรับ table group ที่เกี่ยวข้อง

---

## 8. Checklist คำถาม — ถือไปถามพรุ่งนี้

- [ ] ระบบเป็น **ECC หรือ S/4HANA**? (ชี้ขาดว่าใช้ MSEG หรือ MATDOC)
- [ ] Blending ใช้ **Process Order (PP-PI)** หรือ **Production Order (discrete)**?
- [ ] มีการใช้ **Material Quantity Calculation** ไหม? ถ้ามี สูตรเก็บที่ table ไหน?
- [ ] เปิดใช้ **IS-Oil** หรือเปล่า? mass balance ยึด **KG หรือ L @15°C**?
- [ ] ใช้ **batch-specific UoM** ไหม? density ต่อ batch เก็บที่ไหน?
- [ ] **tcode ที่ user ใช้ดู mass balance จริง ๆ** คืออะไร?
- [ ] tcode นั้นเป็น standard หรือ **Z-report**? ถ้า Z → ขอ **ชื่อ program + source ของ table**
- [ ] movement type ที่ต้องนับเข้า mass balance มีอะไรบ้าง? (นอกจาก 261/101/531)
- [ ] มีระบบนอก (blend optimizer / LIMS / DCS) ยิงข้อมูลเข้ามาไหม? ถ้ามี ขอ interface spec
- [ ] ขอสิทธิ์ **SE16N display** ได้ไหม? ถ้าไม่ได้ ให้ extract ทางไหนแทน?
