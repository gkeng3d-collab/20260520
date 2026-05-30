# Refactor notes — All_strategy_SET_refactored.ipynb

โน้ตสรุปการ refactor ลดโค้ดซ้ำของ notebook screener หุ้น SET
ไฟล์ใหม่: `All_strategy_SET_refactored.ipynb` (อ้างอิงจากต้นฉบับ `All_strategy_SET_20250901.ipynb`)

## ทำอะไรบ้าง

แทนที่ฟังก์ชัน feature-engineering ที่เขียนซ้ำ ๆ ด้วยเวอร์ชันที่ขับด้วย loop +
helper กลาง โดย **ไม่แตะ logic ส่วนอื่น** (loop ดึงข้อมูล, strategy flags,
กราฟ, การ export ยังเหมือนเดิมทุกอย่าง)

ฟังก์ชันที่ถูก refactor (11 ตัว):

| ฟังก์ชัน | วิธีเดิม | วิธีใหม่ |
|---|---|---|
| `addtableMA` | เขียน MA/std/Gap/SD ทีละ window | loop `W_MA` |
| `addtableVol` | VolMA/VolMax/shift ทีละบรรทัด | loop `W_VOL` × `VOL_SHIFTS` |
| `addtablereturn` | ma/std ทีละ window | loop `W_RET` |
| `addtableMin` / `addtableMax` | ~140 บรรทัด/ตัว | `_add_px_family(... how='min'/'max', with_ma=True)` |
| `addtablelow` / `addtablehigh` | ~110 บรรทัด/ตัว | `_add_px_family(... with_ma=False)` |
| `addtableMinMaxptc` / `addtablehighlowptc` | %/shift ทีละบรรทัด | `_add_pct_family(...)` |
| `addtablefibonacci_ptc` | Range/as_of/fibo ทีละ window | loop `W_FIB` |
| `addtablebreakHL` | Break + shift ทีละบรรทัด | loop `W_BRK` |

Helper กลางที่เพิ่มเข้ามา: `_w`, `_add_shifts`, `_add_px_family`, `_add_pct_family`
และค่าคงที่ window/shift (`W_MA`, `W_VOL`, `W_RET`, `W_PX`, `W_PCT`, `W_FIB`,
`W_BRK`, `PX_SHIFTS`, `VOL_SHIFTS`)

**ผลลด:** cell หลัก 2,457 → 1,604 บรรทัด (−853, ~35%)

## การตรวจสอบความถูกต้อง

ทดสอบ offline แบบไม่ต้องต่อเน็ต โดยรันฟังก์ชัน "เดิม" เทียบกับ "ใหม่" บนข้อมูล
OHLCV สุ่ม แล้วเทียบค่าทุกคอลัมน์ที่ใช้ร่วมกัน:

```
shared columns : 867
value mismatches: 0      ← ทุกคอลัมน์เดิมให้ค่าตรงกัน 100%
```

## ส่วนต่างของชุดคอลัมน์ (โดยตั้งใจ)

เวอร์ชันใหม่ใช้ grid สม่ำเสมอ (ครบทุกคู่ window × shift) จึงต่างจากเดิมเล็กน้อย
— เป็นการ "เติมช่องที่ของเดิมลืมใส่" ไม่ใช่การเปลี่ยนค่า:

- **ลบ 1 คอลัมน์:** `BreakPMax40-25` — เป็นคอลัมน์ที่เกิดจากบั๊ก copy-paste ในต้นฉบับ
  (ตั้งชื่อ `-25` แต่จริง ๆ `.shift(5)`) และไม่มีโค้ดส่วนไหนเรียกใช้ต่อ
- **เพิ่ม 46 คอลัมน์:** เติม grid ให้ครบ เช่น `PMin600-5`, `PMax600-60`,
  `PLow600-1`, `PHIGH40-100`, `VolMax-2_05`, `retune_chg_ma20std` ฯลฯ

ทุกคอลัมน์ที่ logic/กราฟ/strategy เดิมอ้างถึง ยังอยู่ครบและค่าตรงเดิม → ผลการ
คัดกรองหุ้นเหมือนเดิม ต่างแค่ไฟล์ Excel ที่ export จะมีคอลัมน์เพิ่มขึ้น 46 ลด 1

## หมายเหตุ

- การ refactor นี้เน้น "ลดโค้ดซ้ำ" อย่างเดียว **ยังไม่ได้แก้บั๊ก logic** ที่พบ
  ในรีวิว (เช่น `CDC == 'TRUE'`, `candle_Bullish_Harami`, Donchian 25/60/200,
  MCDX RSI30, `addtableEMA` ที่ `EMA26-x` ใช้ `EMA25`) — ฟังก์ชันเหล่านั้นคงไว้
  ตามเดิมเพื่อไม่ให้พฤติกรรมเปลี่ยน หากต้องการแก้แยกเป็นงานถัดไปได้
- ยังไม่ได้รันกับข้อมูลจริงผ่าน tvDatafeed (สภาพแวดล้อมนี้ไม่มี network/Colab)
  การตรวจสอบทั้งหมดทำบนข้อมูลสังเคราะห์
