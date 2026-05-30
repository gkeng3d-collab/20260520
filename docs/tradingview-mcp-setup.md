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

## ⚡ คำสั่งพร้อมรัน (ทดสอบบนเครื่องตัวเอง)

หลัง `npm install -g tradingview-mcp-server` แล้ว รันใน terminal ได้เลย:

```bash
# หุ้นไทยที่ราคาเพิ่งตัดขึ้นเหนือ EMA 200 วันนี้ เรียงตามวอลุ่ม
tradingview-cli screen stocks \
  --markets thailand \
  --filters '[{"field":"close","operator":"crosses_above","value":"EMA200"}]' \
  --columns name --columns close --columns change --columns volume --columns RSI \
  --sort-by volume --sort-order desc --limit 25 -f table
```

> หมายเหตุจากการทดสอบ: `tradingview-cli fields --asset-type stock` คืน MA แบบ curated
> มาแค่ `SMA50`, `SMA200`, `EMA10` แต่ scanner API จริงรับ field `EMA200` ได้ —
> ถ้าเคส `EMA200` คืน error/ว่าง ให้สลับไปใช้ `SMA200` (Simple MA 200) เป็น fallback:
>
> ```bash
> tradingview-cli screen stocks --markets thailand \
>   --filters '[{"field":"close","operator":"crosses_above","value":"SMA200"}]' \
>   --columns name --columns close --columns change --columns volume \
>   --sort-by volume --sort-order desc --limit 25 -f table
> ```

## 🎯 สูตร "Quality Breakout" (กรองสัญญาณหลอก)

เบรก EMA 200 + ยืนยันด้วยโมเมนตัมและสภาพคล่อง — ลดหุ้นเบรกหลอก/เด้งสั้น:

```bash
tradingview-cli screen stocks \
  --markets thailand \
  --filters '[
    {"field":"close","operator":"crosses_above","value":"EMA200"},
    {"field":"RSI","operator":"greater","value":50},
    {"field":"market_cap_basic","operator":"greater","value":3000000000},
    {"field":"average_volume_90d_calc","operator":"greater","value":1000000}
  ]' \
  --columns name --columns close --columns change --columns RSI \
  --columns volume --columns average_volume_90d_calc --columns market_cap_basic \
  --sort-by volume --sort-order desc --limit 25 -f table
```

เกณฑ์ที่ใส่ (ปรับเลขได้ตามสไตล์):

| เงื่อนไข | ค่า | เหตุผล |
|----------|-----|--------|
| `close crosses_above EMA200` | — | ราคาเพิ่งเบรกขึ้นเหนือเส้น |
| `RSI > 50` | 50 | โมเมนตัมเป็นบวก ยืนยันแรงซื้อ |
| `market_cap_basic > 3,000,000,000` | 3 พันล้านบาท | ตัดหุ้นเล็ก/ปั่นออก |
| `average_volume_90d_calc > 1,000,000` | 1 ล้านหุ้น/วัน | มีสภาพคล่องพอเข้าออก |

> ปรับจูนได้: เน้น growth → เพิ่ม `{"field":"change","operator":"greater","value":2}` (วันนี้ +2% ขึ้น);
> เน้นปลอดภัย → ดัน `market_cap_basic` เป็น `10000000000` (หมื่นล้าน);
> อยากได้ตัวเพิ่งเริ่ม → จำกัด `{"field":"RSI","operator":"in_range","value":[50,65]}` กัน overbought

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
| **`403 Forbidden`** | TradingView บล็อก IP ของ cloud/datacenter (เช่นรันบน Claude Code เวอร์ชัน web/เซิร์ฟเวอร์คลาวด์) — **รันบนเครื่องตัวเอง (residential IP) จะผ่าน** ไม่ใช่ปัญหา config |
