// Render a web page in headless Chromium and print its visible text (for JS-rendered tariff pages).
// Usage: node tools/render_text.mjs <url> [regex]   - with regex, print only matching lines (+-1 line context)
import { createRequire } from 'module';
import { globSync } from 'fs';
const require = createRequire('/home/btw/test/fiber-tracker/');
const { chromium } = require('playwright-core');
const exe = globSync('/home/btw/.cache/ms-playwright/chromium_headless_shell-1248/*/chrome-headless-shell')[0];
const [, , url, pat] = process.argv;
if (!url) { console.error('usage: render_text.mjs <url> [regex]'); process.exit(2); }
const b = await chromium.launch({ executablePath: exe, headless: true });
try {
  const pg = await b.newPage({ userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36', locale: 'en-US' });
  const resp = await pg.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await pg.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
  for (let i = 0; i < 4; i++) { await pg.mouse.wheel(0, 2500); await pg.waitForTimeout(500); }
  let text = await pg.evaluate(() => document.body ? document.body.innerText : '');
  const lines = text.split('\n').map(s => s.replace(/\s+/g, ' ').trim()).filter(Boolean);
  let out = lines;
  if (pat) {
    const re = new RegExp(pat, 'i'); const keep = new Set();
    lines.forEach((l, i) => { if (re.test(l)) { keep.add(i - 1); keep.add(i); keep.add(i + 1); } });
    out = lines.filter((_, i) => keep.has(i));
  }
  console.log(`URL: ${pg.url()} (HTTP ${resp ? resp.status() : '?'})`);
  console.log(out.join('\n').slice(0, 12000));
} catch (e) { console.log('RENDER ERROR: ' + e.message.split('\n')[0]); }
finally { await b.close(); }
