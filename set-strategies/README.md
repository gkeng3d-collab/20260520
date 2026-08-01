# All strategy SET — เพิ่ม 4 กลยุทธ์ (20260801 v2)

`All_strategy_SET_20260801_v2.ipynb` คือสมุด Colab **"All strategy SET 20260801"** ฉบับเดิมทั้งหมด
บวก cell ใหม่ 3 cell ที่เพิ่ม 4 กลยุทธ์ยอดนิยมจาก TradingView โดย**ไม่แก้โค้ดเดิมแม้แต่บรรทัดเดียว**

## วิธีใช้

1. เปิด [Google Colab](https://colab.research.google.com) → `File` → `Upload notebook` → เลือกไฟล์นี้
2. `Runtime` → `Run all` เหมือนเดิมทุกอย่าง — cell ใหม่จะอ่านข้อมูลจาก cache `_ALL_D` ที่ loop หลักดึงไว้แล้ว (ไม่ยิง TradingView เพิ่ม)
3. คอลัมน์ใหม่ ~37 คอลัมน์จะถูก merge เข้า `StockL_df` และติดไปในไฟล์ export (`listSET_YYYYMMDD.xlsx` / `.parquet`) พร้อมคำอธิบายในชีต Metadata อัตโนมัติ

## กลยุทธ์ที่เพิ่ม (คำนวณเองล้วน ไม่ต้องติดตั้งไลบรารีเพิ่ม)

| กลยุทธ์ | คอลัมน์หลัก | ความหมาย |
|---|---|---|
| **SuperTrend (10, 3)** | `ST_dir`, `ST_line`, `ST_gap%`, `ST_flip_up_TF`, `ST_bars_in_trend` | ทิศทางเทรนด์จาก ATR + เส้น trailing stop |
| **Squeeze Momentum** (LazyBear) | `SQZ_on_TF`, `SQZ_bars_on`, `SQZ_fired_up_TF`, `SQZ_mom` | Bollinger หดเข้าใน Keltner = บีบตัวสะสมพลัง รอระเบิดทิศทาง |
| **Smart Money Concepts** (พื้นฐาน) | `SMC_trend`, `SMC_event` (BOS/CHoCH), `SMC_FVG_bull_*`, `SMC_OB_bull_*`, `SMC_in_FVG_bull_TF` | โครงสร้างราคา: ทะลุ swing (BOS/CHoCH), โซน Fair Value Gap และ Order Block ที่ยังไม่ถูกใช้ |
| **Cumulative Volume Delta** | `CVD_delta_ratio20`, `CVD_slope20`, `CVD_div_bull_TF`, `CVD_div_bear_TF` | แรงซื้อ-ขายสุทธิสะสม + divergence (ประมาณจาก OHLCV เพราะข้อมูลรายวันไม่มี tick) |
| **คะแนนรวม** | `STRAT4_SCORE` (0–100) | น้ำหนักโปร่งใส แก้ได้ใน cell |

## Cell ที่เพิ่ม (ตำแหน่งใน notebook)

- **Cell 22** (ก่อน cell export): นิยามฟังก์ชัน + วนคำนวณทุกหุ้นจาก `_ALL_D` + merge เข้า `StockL_df` + ลงทะเบียนคำอธิบายคอลัมน์เข้า `_META_EXACT` — รันซ้ำได้ ไม่เกิดคอลัมน์ซ้ำ
- **Cell 25**: ตัวอย่างคัดกรอง 8 แบบ (ST เพิ่งพลิกขึ้น / เพิ่งคลายบีบ / CHoCH up / ราคาย่อเข้าโซน FVG-OB / CVD สะสม ฯลฯ)
- **Cell 26**: `graph_strat4('PTT')` — กราฟแท่งเทียน + เส้น SuperTrend + โซน FVG/OB + จุด BOS/CHoCH + แผง Squeeze + แผง CVD

> ⚠️ เพื่อการศึกษาเท่านั้น ไม่ใช่คำแนะนำในการลงทุน · SMC เป็นเวอร์ชันพื้นฐาน (swing ±5 แท่ง ยืนยันแบบไม่มองอนาคต) อาจให้ผลต่างจากสคริปต์ LuxAlgo เต็มรูปแบบ
