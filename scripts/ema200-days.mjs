#!/usr/bin/env node
// ema200-days.mjs
// นับว่าหุ้นไทยแต่ละตัว "ปิดเหนือ EMA 200 ติดต่อกันมากี่วันแล้ว" (เบรกมากี่วัน)
//
// ใช้งาน:
//   npm install yahoo-finance2
//   node ema200-days.mjs CPALL SIRI DCC NCAP WIIK
//   (ไม่ใส่ ticker = ใช้ลิสต์ตัวอย่างด้านล่าง)
//
// หมายเหตุ: ใส่แค่ชื่อหุ้น เช่น CPALL สคริปต์จะเติม ".BK" ให้เอง (ตลาดไทยบน Yahoo)

import yahooFinance from 'yahoo-finance2';

// ปิด log กวนๆ ของ yahoo-finance2
yahooFinance.suppressNotices?.(['yahooSurvey']);

const PERIOD = 200; // EMA 200

const DEFAULT_TICKERS = ['CPALL', 'SIRI', 'NCAP', 'WIIK', 'DCC', 'SECURE'];

function ema(values, period) {
  if (values.length < period) return [];
  const k = 2 / (period + 1);
  const out = new Array(values.length).fill(null);
  // seed ด้วย SMA ของ period แรก
  let prev = values.slice(0, period).reduce((a, b) => a + b, 0) / period;
  out[period - 1] = prev;
  for (let i = period; i < values.length; i++) {
    prev = values[i] * k + prev * (1 - k);
    out[i] = prev;
  }
  return out;
}

async function analyze(ticker) {
  const symbol = ticker.includes('.') ? ticker : `${ticker}.BK`;
  const period1 = new Date();
  period1.setFullYear(period1.getFullYear() - 3); // ดึงย้อนหลัง 3 ปี ให้ EMA200 นิ่ง

  const res = await yahooFinance.chart(symbol, { period1, interval: '1d' });
  const quotes = (res.quotes || []).filter((q) => q.close != null);
  if (quotes.length < PERIOD + 1) {
    return { ticker, error: `ข้อมูลไม่พอ (${quotes.length} วัน)` };
  }

  const closes = quotes.map((q) => q.close);
  const emaArr = ema(closes, PERIOD);

  // เดินจากวันล่าสุดย้อนกลับ นับวันที่ปิด "เหนือ" EMA200 ติดต่อกัน
  const last = closes.length - 1;
  const aboveNow = closes[last] > emaArr[last];

  let streak = 0;
  let crossIdx = -1;
  for (let i = last; i >= 0 && emaArr[i] != null; i--) {
    const above = closes[i] > emaArr[i];
    if (above === aboveNow) {
      streak++;
      crossIdx = i;
    } else break;
  }

  const lastClose = closes[last];
  const lastEma = emaArr[last];
  const pctVsEma = ((lastClose - lastEma) / lastEma) * 100;
  const crossDate = quotes[crossIdx]?.date;

  return {
    ticker,
    close: lastClose,
    ema200: lastEma,
    pctVsEma,
    state: aboveNow ? 'เหนือ EMA200' : 'ใต้ EMA200',
    days: streak,                       // ปิดเหนือ/ใต้ ติดต่อกันกี่วัน
    since: crossDate ? crossDate.toISOString().slice(0, 10) : '-',
  };
}

async function main() {
  const tickers = process.argv.slice(2);
  const list = tickers.length ? tickers : DEFAULT_TICKERS;

  const rows = [];
  for (const t of list) {
    try {
      rows.push(await analyze(t));
    } catch (e) {
      rows.push({ ticker: t, error: e.message });
    }
    await new Promise((r) => setTimeout(r, 300)); // กัน rate limit
  }

  // เรียง: ตัวที่ "เพิ่งเบรก" (อยู่เหนือ + days น้อย) ขึ้นก่อน
  rows.sort((a, b) => {
    if (a.error || b.error) return a.error ? 1 : -1;
    const aUp = a.state.startsWith('เหนือ') ? 0 : 1;
    const bUp = b.state.startsWith('เหนือ') ? 0 : 1;
    if (aUp !== bUp) return aUp - bUp;
    return a.days - b.days;
  });

  console.log('\n' + 'หุ้น'.padEnd(10) + 'ราคา'.padEnd(10) + 'EMA200'.padEnd(12) +
    '%ห่างเส้น'.padEnd(12) + 'สถานะ'.padEnd(14) + 'กี่วัน'.padEnd(8) + 'ตั้งแต่');
  console.log('-'.repeat(78));
  for (const r of rows) {
    if (r.error) {
      console.log(r.ticker.padEnd(10) + `⚠️  ${r.error}`);
      continue;
    }
    console.log(
      r.ticker.padEnd(10) +
      r.close.toFixed(2).padEnd(10) +
      r.ema200.toFixed(2).padEnd(12) +
      (r.pctVsEma >= 0 ? '+' : '') + r.pctVsEma.toFixed(1) + '%'.padEnd(8) +
      ('  ' + r.state).padEnd(14) +
      String(r.days).padEnd(8) +
      r.since
    );
  }
  console.log('\nหมายเหตุ: "กี่วัน" = จำนวนวันทำการที่ปิดเหนือ/ใต้ EMA200 ติดต่อกัน');
  console.log('ตัวที่อยู่ "เหนือ EMA200" และเลขวันน้อย = เพิ่งเบรกขึ้นล่าสุด\n');
}

main();
