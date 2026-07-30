# แผนเรียนรู้ Microsoft Fabric (Roadmap 8 สัปดาห์)

แผนฝึกฝนจากศูนย์จนใช้งานจริงได้ เน้นลงมือทำ (hands-on) ทุกสัปดาห์ ใช้เวลาประมาณ 5–8 ชม./สัปดาห์

## Microsoft Fabric คืออะไร (สรุปสั้น)

Fabric คือแพลตฟอร์ม analytics แบบ **SaaS ตัวเดียวจบ** ของ Microsoft ที่รวมงานข้อมูลทั้งวงจร
ตั้งแต่ดึงข้อมูล แปลงข้อมูล เก็บ วิเคราะห์ ไปจนถึงทำรายงาน โดยทุกอย่างเก็บลงที่เดียวกันคือ **OneLake**
(เปรียบเสมือน "OneDrive สำหรับข้อมูล" — เก็บเป็น Delta/Parquet format เดียว ทุก engine ใช้ร่วมกันได้)

| Workload | ใช้ทำอะไร | ทักษะหลัก |
|---|---|---|
| Data Factory | ดึง/ย้ายข้อมูล (Pipeline, Dataflow Gen2) | GUI + แนวคิด ETL |
| Data Engineering | แปลงข้อมูลด้วย Spark Notebook, Lakehouse | PySpark, SQL |
| Data Warehouse | คลังข้อมูลแบบ T-SQL เต็มรูปแบบ | SQL |
| Real-Time Intelligence | ข้อมูล streaming, Eventstream, KQL | KQL |
| Data Science | สร้าง/เทรน ML model, MLflow | Python |
| Databases | SQL database แบบ transactional ใน Fabric | SQL |
| Power BI | Semantic model + รายงาน (โหมด Direct Lake) | DAX, data modeling |

## ก่อนเริ่ม: พื้นฐานที่ควรมี

- **SQL** — SELECT, JOIN, GROUP BY (จำเป็นที่สุด)
- **Python เบื้องต้น** — พอสำหรับ PySpark (อ่าน/เขียน DataFrame)
- **แนวคิด data modeling** — star schema, fact/dimension
- Power BI พื้นฐาน (ถ้าเคยใช้จะไปเร็วขึ้นมาก)

ถ้ายังไม่แน่น ให้ปูพื้น SQL ก่อน 1–2 สัปดาห์ แล้วค่อยเริ่มแผนนี้ ส่วน Python ไปเก็บระหว่างทางได้

## เตรียมสนามซ้อม (ฟรี)

1. เปิด **Fabric trial 60 วัน** ที่ [app.fabric.microsoft.com](https://app.fabric.microsoft.com)
   — ต้องใช้ work/school account (Microsoft 365 ขององค์กร) ดูขั้นตอนที่
   [Fabric trial](https://learn.microsoft.com/fabric/fundamentals/fabric-trial)
2. ถ้าไม่มี account องค์กร: ซื้อ capacity **F2 แบบ pay-as-you-go** ใน Azure (ถูกสุด จ่ายรายชั่วโมง
   และกด **pause** ตอนไม่ใช้เพื่อประหยัดได้)
3. หาข้อมูลซ้อมมือ: Fabric มี sample dataset ในตัว (เช่น NYC Taxi, Wide World Importers)
   หรือใช้ข้อมูลจาก [Kaggle](https://www.kaggle.com/datasets)

> เคล็ดลับ: trial มีอายุ 60 วัน ≈ แผน 8 สัปดาห์พอดี เปิด trial วันที่เริ่มสัปดาห์ที่ 1 เลย

## Roadmap 8 สัปดาห์

| สัปดาห์ | หัวข้อ | ผลลัพธ์ที่จับต้องได้ |
|---|---|---|
| 1 | ภาพรวม Fabric + OneLake + Workspace | สร้าง workspace แรก, เข้าใจ item ทุกชนิด |
| 2 | Lakehouse + Delta Lake + Shortcut | Lakehouse ที่มีข้อมูลจริง query ได้ |
| 3 | Data Factory: Pipeline + Dataflow Gen2 | pipeline ดึงข้อมูลอัตโนมัติตาม schedule |
| 4 | Spark Notebook + Medallion Architecture | ชั้น Bronze/Silver/Gold ครบ |
| 5 | Data Warehouse + Semantic Model | warehouse + star schema พร้อมใช้ |
| 6 | Power BI + Direct Lake | dashboard เชื่อมข้อมูลจาก OneLake ตรง ๆ |
| 7 | Real-Time Intelligence + Data Science เบื้องต้น | dashboard แบบ real-time จาก Eventstream |
| 8 | Governance + CI/CD + โปรเจกต์จบ | โปรเจกต์ end-to-end 1 ชิ้น |

### สัปดาห์ 1 — ภาพรวม + OneLake + Workspace

เป้าหมาย: เข้าใจว่าแต่ละ workload คืออะไร ต่างกันยังไง และของทุกอย่างอยู่บน OneLake

- [ ] เรียน module แรก ๆ ของ learning path
      [Get started with Microsoft Fabric](https://learn.microsoft.com/training/paths/get-started-fabric/)
- [ ] สร้าง workspace, ลองสร้าง item ทีละชนิด (Lakehouse, Warehouse, Notebook, Pipeline) ให้เห็นหน้าตา
- [ ] ติดตั้ง **OneLake file explorer** บน Windows แล้วดูว่าไฟล์ใน OneLake โผล่เหมือน OneDrive
- [ ] ทำความเข้าใจคำว่า capacity / CU (Capacity Unit) คร่าว ๆ

### สัปดาห์ 2 — Lakehouse + Delta Lake + Shortcut

เป้าหมาย: เข้าใจหัวใจของ Fabric คือ Lakehouse (Files + Tables) และ Delta format

- [ ] สร้าง Lakehouse, upload ไฟล์ CSV เข้า **Files** แล้วแปลงเป็น **Table** (Delta)
- [ ] ลอง query ผ่าน **SQL analytics endpoint** ของ Lakehouse
- [ ] สร้าง **Shortcut** ชี้ไปข้อมูลที่อื่น (เช่น Lakehouse อื่น หรือ ADLS/S3 ถ้ามี) — เข้าใจว่า
      shortcut = ไม่ copy ข้อมูล
- [ ] อ่านแนวคิด Delta Lake: transaction log, time travel, `OPTIMIZE`

### สัปดาห์ 3 — Data Factory: Pipeline + Dataflow Gen2

เป้าหมาย: ดึงข้อมูลเข้า Fabric ได้เองแบบอัตโนมัติ

- [ ] สร้าง **Data pipeline** ใช้ Copy activity ดึงข้อมูลจาก sample source ลง Lakehouse
- [ ] สร้าง **Dataflow Gen2** (Power Query) ทำ transform เบา ๆ เช่น เปลี่ยน type, filter, merge
- [ ] ตั้ง **schedule** ให้ pipeline รันเองทุกวัน + ลองดู run history / monitoring
- [ ] เข้าใจว่าเมื่อไหร่ใช้ Pipeline (ย้ายข้อมูลหนัก ๆ, orchestration) เมื่อไหร่ใช้ Dataflow
      (transform แบบ low-code) และรู้จัก **Mirroring** (sync ฐานข้อมูลภายนอกเข้า OneLake แบบ near real-time)

### สัปดาห์ 4 — Spark Notebook + Medallion Architecture

เป้าหมาย: แปลงข้อมูลด้วย PySpark และจัดชั้นข้อมูลแบบ Bronze/Silver/Gold

- [ ] เขียน Notebook อ่านไฟล์ดิบ (Bronze) → clean/dedupe (Silver) → aggregate เป็นตารางพร้อมใช้ (Gold)
- [ ] ฝึกคำสั่งหลัก: `spark.read`, `df.write.format("delta").saveAsTable()`, `filter`, `groupBy`, `join`
- [ ] ลองสลับเขียนเป็น **Spark SQL** (`%%sql`) ในเซลล์เดียวกัน
- [ ] เรียกใช้ Notebook จาก Pipeline (orchestrate) ให้รันต่อกันเป็น flow เดียว

### สัปดาห์ 5 — Data Warehouse + Semantic Model

เป้าหมาย: สร้างคลังข้อมูลแบบ T-SQL และ model สำหรับทำรายงาน

- [ ] สร้าง **Warehouse**, สร้างตาราง fact/dimension ด้วย T-SQL (`CREATE TABLE`, `INSERT`, `CTAS`)
- [ ] ลอง query ข้าม item: Warehouse query ตารางใน Lakehouse ได้เลย (three-part name)
- [ ] เข้าใจความต่าง **Lakehouse vs Warehouse** (Spark-first vs T-SQL-first) — ข้อสอบและงานจริงถามบ่อย
- [ ] สร้าง **Semantic model**: กำหนด relationship, measure พื้นฐานด้วย DAX (`SUM`, `CALCULATE`)

### สัปดาห์ 6 — Power BI + Direct Lake

เป้าหมาย: ทำ dashboard ที่อ่านข้อมูลจาก OneLake ตรง ๆ ไม่ต้อง import

- [ ] สร้างรายงานจาก semantic model สัปดาห์ที่ 5 (bar, line, card, slicer)
- [ ] เข้าใจ 3 โหมด: **Import vs DirectQuery vs Direct Lake** — จุดขายของ Fabric คือ Direct Lake
- [ ] ฝึก DAX เพิ่ม: measure ประเภท time intelligence (YTD, MoM)
- [ ] แชร์รายงาน + ลองดูผ่านมือถือ

### สัปดาห์ 7 — Real-Time Intelligence + Data Science เบื้องต้น

เป้าหมาย: รู้จักฝั่ง streaming และ ML พอเห็นภาพ

- [ ] สร้าง **Eventstream** จาก sample data (เช่น bicycle/taxi stream) ลง **Eventhouse (KQL database)**
- [ ] เขียน **KQL** พื้นฐาน: `take`, `where`, `summarize`, `render`
- [ ] สร้าง **Real-Time Dashboard** + ตั้ง alert ด้วย **Activator** (เช่น ค่าเกิน threshold ให้แจ้งเตือน)
- [ ] ฝั่ง Data Science: เปิด Notebook เทรน model ง่าย ๆ ด้วย scikit-learn + log ด้วย **MLflow** experiment

### สัปดาห์ 8 — Governance + CI/CD + โปรเจกต์จบ

เป้าหมาย: ทำงานแบบมืออาชีพและมีผลงาน 1 ชิ้น

- [ ] เรียนเรื่อง **workspace roles** (Admin/Member/Contributor/Viewer), item permission, sensitivity label
- [ ] ลอง **Git integration** (เชื่อม workspace กับ GitHub/Azure DevOps) และ **Deployment pipeline**
      (Dev → Test → Prod)
- [ ] เปิด **Capacity Metrics app** ดูว่าอะไรกิน CU เยอะ
- [ ] ทำ **โปรเจกต์จบ** (ดูหัวข้อถัดไป) แล้วเขียนสรุปลง README/blog — ได้ทั้งความเข้าใจและ portfolio

## โปรเจกต์ฝึกมือแนะนำ (เลือก 1 ทำให้จบ)

1. **Sales Analytics end-to-end** — ดึงไฟล์ยอดขาย (CSV/API) ด้วย Pipeline → Medallion ใน Lakehouse
   → Semantic model → Dashboard ยอดขายรายเดือน/สาขา + YoY
2. **Real-time IoT/Log monitor** — Eventstream รับข้อมูล sensor หรือ log → KQL → Real-Time Dashboard
   + Activator แจ้งเตือนเมื่อผิดปกติ
3. **ข้อมูลเปิดไทย** — ดึงข้อมูลจาก [data.go.th](https://data.go.th) (เช่น อุบัติเหตุ, คุณภาพอากาศ,
   ท่องเที่ยว) มาทำ dashboard เชิงลึก 1 เรื่อง

ทั้ง 3 โปรเจกต์ใช้ workload ครบตั้งแต่ ingest → transform → model → visualize ซึ่งคือสิ่งที่งานจริงต้องการ

## ใบเซอร์ที่เกี่ยวข้อง (แนะนำให้สอบหลังจบแผน)

| ใบเซอร์ | เหมาะกับ | หมายเหตุ |
|---|---|---|
| [DP-600 Fabric Analytics Engineer](https://learn.microsoft.com/credentials/certifications/fabric-analytics-engineer-associate/) | สาย analytics/BI (semantic model, warehouse, รายงาน) | ตัวหลักของ Fabric สายวิเคราะห์ |
| [DP-700 Fabric Data Engineer](https://learn.microsoft.com/credentials/certifications/fabric-data-engineer-associate/) | สาย data engineering (ingest, transform, Spark, streaming) | ตัวหลักสาย engineer |
| PL-300 Power BI Data Analyst | สายรายงาน/DAX เป็นหลัก | ปูทางก่อน DP-600 ได้ |

- แต่ละหน้า cert มี **Practice Assessment ฟรี** — ทำวนจนได้ >80% ค่อยสอบจริง
- เรียนจบแผน 8 สัปดาห์นี้ = ครอบคลุมเนื้อหา DP-600/DP-700 ไปแล้วส่วนใหญ่ เหลือเก็บรายละเอียดจาก
  study guide ในหน้า cert อีก 1–2 สัปดาห์

## แหล่งเรียนรู้รวม

- **เอกสารหลัก**: [learn.microsoft.com/fabric](https://learn.microsoft.com/fabric/) —
  โดยเฉพาะ [End-to-end tutorials](https://learn.microsoft.com/fabric/fundamentals/end-to-end-tutorials)
  ทำตามได้ทีละขั้น
- **Learning path ฟรี**: [Get started with Microsoft Fabric](https://learn.microsoft.com/training/paths/get-started-fabric/)
- **Community**: [community.fabric.microsoft.com](https://community.fabric.microsoft.com) — ถามตอบ + งาน
  community เยอะ
- **ตามฟีเจอร์ใหม่**: [blog.fabric.microsoft.com](https://blog.fabric.microsoft.com) — Fabric ออกของใหม่
  ทุกเดือน อ่าน monthly update ให้ติดนิสัย
- **YouTube**: ช่อง *Guy in a Cube* (Power BI/Fabric) และ *Learn Microsoft Fabric with Will*
  (สอน Fabric ตรง ๆ มี roadmap/DP-600 series)

## เคล็ดลับให้เก่งเร็ว

1. **ลงมือทำ > ดูคลิป** — ทุกหัวข้อต้องจบที่ "ของที่สร้างเอง" ใน workspace ไม่ใช่แค่ดูเข้าใจ
2. **ใช้ข้อมูลที่ตัวเองสนใจ** — จะทนทำจนจบมากกว่าใช้ sample อย่างเดียว
3. **จดเป็น cheat sheet ของตัวเอง** — เช่น ตารางเทียบ Lakehouse vs Warehouse vs Eventhouse
   ว่าเมื่อไหร่ใช้อะไร (คำถามยอดฮิตทั้งในข้อสอบและงานจริง)
4. **อย่าหลงไปทุกฟีเจอร์** — Fabric กว้างมาก ยึดเส้นทางหลัก ingest → transform → model → report
   ให้แน่นก่อน แล้วค่อยแตกไป Real-Time / Data Science / Copilot
5. **เข้า community/ตอบกระทู้** — การอธิบายให้คนอื่นเข้าใจคือวิธีเช็คว่าเราเข้าใจจริง
