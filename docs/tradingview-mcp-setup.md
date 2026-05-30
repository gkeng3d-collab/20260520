# TradingView MCP Server — คู่มือติดตั้ง (Claude Code, local)

MCP server สำหรับดึง **TradingView Screener** อัตโนมัติ — สแกนหุ้นตามเงื่อนไขเทคนิคได้
เช่น "หุ้นไทยที่ราคาเพิ่งเบรกขึ้นเหนือ EMA 200"

- Package: [`tradingview-mcp-server`](https://www.npmjs.com/package/tradingview-mcp-server)
  (unofficial, [GitHub](https://github.com/fiale-plus/tradingview-mcp-server))
- **ไม่ต้องใช้ API key** — เรียกผ่าน public scanner API ของ TradingView
- รองรับ stocks / forex / crypto / ETF, 100+ screener fields

> ⚠️ Disclaimer: เป็น MCP ของ community (ไม่ใช่ของ TradingView อย่างเป็นทางการ)
> ใช้ public API ที่อาจเปลี่ยน/จำกัด rate ได้ ข้อมูลที่ได้ใช้เพื่อประกอบการตัดสินใจ
> ไม่ใช่คำแนะนำการลงทุน — ควร verify กราฟจริงก่อนเทรดทุกครั้ง

---

## ความต้องการของระบบ

- **Node.js ≥ 18** (มากับ `npx`) — เช็คด้วย `node -v`
- Claude Code CLI ติดตั้งบนเครื่อง

## การติดตั้ง

ไฟล์ [`.mcp.json`](../.mcp.json) ถูก commit ไว้ใน repo นี้แล้ว (project-scoped) เพราะฉะนั้น:

1. Pull branch นี้ลงเครื่องตัวเอง
2. เปิด Claude Code ในโฟลเดอร์ repo นี้:
   ```bash
   cd 20260520
   claude
   ```
3. ครั้งแรก Claude Code จะ **เด้งถามอนุมัติ project MCP server** — กด **Yes / approve**
   (เป็นกลไกความปลอดภัยของ project-scoped MCP)
4. เช็คว่าเชื่อมต่อสำเร็จ:
   ```
   /mcp
   ```
   ควรเห็น `tradingview` สถานะ connected พร้อม tools เช่น
   `screen_stocks`, `list_fields`, `get_market_metainfo`, `get_ta_summary` ฯลฯ

### ทางเลือก: ติดตั้งแบบ global (ไม่อยากใช้ npx ทุกครั้ง)

```bash
npm install -g tradingview-mcp-server
```
แล้วแก้ `command` ใน `.mcp.json` เป็น `"tradingview-mcp-server"` และตัด `args` ออก

### ทางเลือก: เพิ่มผ่านคำสั่ง (แทน .mcp.json)

```bash
claude mcp add tradingview -- npx -y tradingview-mcp-server@latest
```

---

## วิธีหาหุ้นไทยที่ "เพิ่งเบรก EMA 200"

ใน Claude Code (หลังเชื่อม MCP แล้ว) พิมพ์ prompt ประมาณนี้ได้เลย:

> ใช้ tradingview screener หาหุ้นไทยที่ราคา (close) เพิ่ง crosses_above EMA 200
> วันนี้ เรียงตาม volume เอามาสัก 20 ตัว พร้อม % เปลี่ยนแปลงและ RSI

### โครงสร้าง filter ที่ใช้ (อ้างอิง)

ตลาดไทยใช้ `"market": "thailand"` (TradingView scanner ใช้ country slug แบบนี้:
`america`, `thailand`, `japan`, ...)

```jsonc
// screen_stocks
{
  "market": "thailand",
  "filters": [
    { "field": "close", "operator": "crosses_above", "value": "EMA200" },
    { "field": "volume", "operator": "greater", "value": 1000000 }
  ],
  "columns": ["name", "close", "change", "volume", "RSI", "EMA200"],
  "sort": { "field": "volume", "order": "desc" },
  "limit": 20
}
```

Operators ที่เกี่ยวข้อง:
- `crosses_above` — ราคาเพิ่งตัดขึ้นเหนือเส้น (สิ่งที่เราต้องการ)
- `crosses_below` — ตัดลง
- `greater` / `less` — มากกว่า / น้อยกว่า

### ⚠️ ก่อนใช้จริง ให้ยืนยันชื่อ field ของตลาดไทยก่อน

ชื่อ field ที่แน่นอน (เช่น `EMA200` vs `EMA200|1D`) อาจต่างกันตาม timeframe/ตลาด
ให้รันสองตัวนี้ก่อนเพื่อเช็คชื่อจริง แล้วค่อยปรับ filter:

> เรียก `get_market_metainfo` ด้วย market=thailand
> และ `list_fields` เพื่อดูชื่อ field EMA/SMA ที่ใช้ได้จริงของตลาดไทย

---

## Troubleshooting

| อาการ | สาเหตุ / วิธีแก้ |
|-------|-----------------|
| `/mcp` ไม่เห็น tradingview | ยังไม่ได้ approve project MCP — รีสตาร์ต Claude Code แล้วกดอนุมัติ |
| connect ไม่ติด / timeout | เช็ค `node -v` ≥ 18, เช็คเน็ต, ลอง `npx -y tradingview-mcp-server@latest` ใน terminal ตรงๆ |
| ไม่มีผลลัพธ์หุ้นไทย | ชื่อ field ผิด — รัน `list_fields` / `get_market_metainfo` (market=thailand) เพื่อดูชื่อจริง |
| โดน rate limit | ปรับ `RATE_LIMIT_RPM` ใน `.mcp.json` ให้ต่ำลง หรือเพิ่ม `CACHE_TTL_SECONDS` |
