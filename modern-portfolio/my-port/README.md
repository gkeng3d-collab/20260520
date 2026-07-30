# พอร์ตหุ้น SET ของฉัน — ทำ MPT

`holdings.csv` ในโฟลเดอร์นี้คือพอร์ตปัจจุบัน (8 ตัว):
BLC 400, SISB 200, SPALI 100, AIT 200, DCC 1100, LHHOTEL 200, SECURE 300, INETREIT 200 หุ้น/หน่วย

## ขั้นที่ 1 — ดึงราคาย้อนหลัง (รันบนเครื่องตัวเอง)

สภาพแวดล้อม Claude Code บนเว็บออกอินเทอร์เน็ตไปหาแหล่งข้อมูลราคาหุ้นไม่ได้
(Yahoo/SET ถูก network policy บล็อก) จึงต้องรันขั้นนี้บนเครื่องคุณเอง —
ใช้ Python เปล่า ๆ ไม่ต้องติดตั้งอะไรเพิ่ม:

```bash
cd modern-portfolio
python fetch_yahoo.py --holdings my-port/holdings.csv --suffix .BK --out my-port/prices.csv
```

ได้ `my-port/prices.csv` = ราคาปิดปรับปันผล (adjusted close) รายวันย้อนหลัง 3 ปี
ของทั้ง 8 ตัว โดยช่วงข้อมูลจะเริ่มจากวันที่ทุกตัวมีข้อมูลครบ
(BLC เพิ่งเข้าตลาดกลางปี 2023 จึงเป็นตัวกำหนดจุดเริ่ม)

> REIT อย่าง LHHOTEL/INETREIT จ่ายปันผลสูง — การใช้ adjusted close
> ทำให้ผลตอบแทนรวมปันผลถูกนับแล้ว ไม่โดนกดต่ำเกินจริง

## ขั้นที่ 2 — รัน MPT

```bash
pip install -r requirements.txt   # ครั้งแรกครั้งเดียว: numpy scipy matplotlib

# 1) สำรวจ: ผลตอบแทน/ความเสี่ยง/correlation รายตัว
python mpt.py analyze my-port/prices.csv --rf 0.015

# 2) พอร์ตที่ดีที่สุดตามทฤษฎี (คุมไม่ให้ตัวใดเกิน 30%)
python mpt.py optimize my-port/prices.csv --rf 0.015 --max-weight 0.30

# 3) เส้น efficient frontier + กราฟ
python mpt.py frontier my-port/prices.csv --rf 0.015 --max-weight 0.30 \
    --plot my-port/frontier.png --out my-port/frontier.csv

# 4) แผนซื้อ/ขายจริง ปัดเป็น board lot 100 หุ้น ข้ามรายการจิ๋วกว่า 500 บาท
python mpt.py rebalance my-port/prices.csv --holdings my-port/holdings.csv \
    --rf 0.015 --max-weight 0.30 --lot 100 --min-trade 500

# อยากเติมเงินเข้าพอร์ตพร้อม rebalance: เพิ่ม --cash 10000
```

`--rf 0.015` ≈ ผลตอบแทนพันธบัตรไทยระยะสั้น (ปรับได้ตามจริง)
`--max-weight 0.30` กันพอร์ตกระจุกตัวเกินไป — ถอดออกถ้าอยากเห็นคำตอบดิบของ optimizer

## ทางลัด

ถ้าไม่อยากรันเอง: อัปโหลด/วางไฟล์ `prices.csv` (หรือ export ราคาจากโบรกเกอร์
เป็น CSV คอลัมน์ date + ราคาปิดรายตัว) กลับมาในแชท แล้วให้ Claude รันให้ทั้งหมดได้เลย

## ข้อควรระวังเฉพาะพอร์ตนี้

- **ประวัติสั้น**: BLC เข้าตลาด มิ.ย. 2023 → ข้อมูลร่วมกัน ~3 ปี ค่าประมาณจึงหยาบ
- **สภาพคล่องต่ำ**: SECURE, INETREIT, LHHOTEL ซื้อขายเบาบาง ราคาบางวันไม่ขยับ
  → volatility/correlation ที่วัดได้อาจต่ำกว่าจริง (stale prices)
- **ผลลัพธ์ optimizer ไวต่อข้อมูล** โดยเฉพาะ expected return — ใช้เป็นกรอบตัดสินใจ
  ไม่ใช่คำสั่งซื้อขายอัตโนมัติ และไม่ใช่คำแนะนำการลงทุน
