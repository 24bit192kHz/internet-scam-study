#!/usr/bin/env python3
"""Render docs/index.html, docs/fiber.html, docs/mobile.html from build2 outputs."""
import csv, json, os
from urllib.parse import urlparse

BASE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(BASE, "docs")
D = os.path.join(DOCS, "data")

def load(name):
    with open(os.path.join(D, name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def fnum(v):
    try:
        return float(v) if v not in (None, "") else None
    except ValueError:
        return None

fiber = load("fiber_country.csv")
mobile = load("mobile_country.csv")
fops = load("fiber_ops.csv")
mops = load("mobile_ops.csv")
stats = json.load(open(os.path.join(D, "stats.json")))

# per-iso operator source links
def src_by_iso(rows):
    d = {}
    for r in rows:
        u = (r.get("source_url") or "").strip()
        if u and u != "knowledge":
            d.setdefault(r["iso3"], []).append(u)
    return d
fsrc, msrc = src_by_iso(fops), src_by_iso(mops)

REGIONS = ["Africa", "Asia", "Europe", "North America", "South America", "Oceania"]
COLORS = {"Africa": "#ff7b72", "Asia": "#ffbd2e", "Europe": "#58a6ff",
          "North America": "#3fd68c", "South America": "#d2a8ff",
          "Oceania": "#79c0ff"}

CSS = """
:root{--bg:#0d1117;--panel:#161b22;--fg:#e6edf3;--dim:#8b949e;--red:#ff5f56;
--amber:#ffbd2e;--green:#3fd68c;--border:#30363d}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);
font:14px/1.5 -apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
header{padding:26px 32px 6px}h1{margin:0 0 6px;font-size:25px;letter-spacing:-.5px}
nav a{color:#58a6ff;text-decoration:none;margin-right:16px;font-size:13px}
nav a.cur{color:var(--fg);font-weight:700;border-bottom:2px solid #58a6ff;
padding-bottom:2px}
.sub{color:var(--dim);max-width:1150px}
.stats{display:flex;gap:14px;flex-wrap:wrap;padding:16px 32px 4px}
.stat{background:var(--panel);border:1px solid var(--border);border-radius:10px;
padding:11px 16px;min-width:150px}.stat b{display:block;font-size:23px}
.stat span{color:var(--dim);font-size:11.5px}
.red b{color:var(--red)}.green b{color:var(--green)}.amber b{color:var(--amber)}
.grid{display:grid;gap:16px;padding:14px 32px}
.grid.two{grid-template-columns:1fr 1fr}
@media(max-width:1100px){.grid.two{grid-template-columns:1fr}}
.card{background:var(--panel);border:1px solid var(--border);border-radius:12px;
padding:8px}.card h2{font-size:15px;margin:6px 8px 0}
.card p{font-size:12px;color:var(--dim);margin:2px 8px 4px}
.controls{padding:4px 32px 0;display:flex;gap:10px;align-items:center;flex-wrap:wrap}
select,button{background:#21262d;color:var(--fg);border:1px solid var(--border);
border-radius:6px;padding:6px 10px;font-size:13px;cursor:pointer}
select:hover,button:hover{border-color:#58a6ff}
.tblwrap{padding:8px 32px 40px;overflow-x:auto}
table{border-collapse:collapse;font-size:12.5px;width:100%}
th,td{padding:6px 9px;text-align:right;border-bottom:1px solid #21262d;
white-space:nowrap}
th:first-child,td:first-child,th.l,td.l{text-align:left}
th{cursor:pointer;color:var(--dim);font-size:11px;text-transform:uppercase;
letter-spacing:.4px;position:sticky;top:0;background:var(--panel)}
th:hover{color:#58a6ff}
tbody tr:hover{background:#1c2128}
.pill{padding:1px 8px;border-radius:20px;font-size:11px;background:#21262d;
color:var(--dim)}
.ok{color:var(--green)}.warn{color:var(--amber)}.bad{color:var(--red)}
a{color:#58a6ff}footer{color:var(--dim);font-size:12px;padding:0 32px 40px}
.exp{font-size:11px;color:var(--dim)}
"""

def page(title, nav_cur, header_html, body_html, extra_js=""):
    nav = [("index.html", "🏠 Overview"), ("fiber.html", "🌐 Fiber study"),
           ("mobile.html", "📱 Mobile 4G/5G"), ("saudi.html", "🇸🇦 Saudi vs peers")]
    navhtml = "".join(
        f'<a href="{h}"{" class=cur" if h==nav_cur else ""}>{t}</a>' for h, t in nav)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>{title}</title>
<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
<style>{CSS}</style></head><body>
<header><h1>{title}</h1>
<nav>{navhtml}</nav>
<div class="sub">{header_html}</div></header>
{body_html}
<footer>Data: 195 UN countries, operator-level, Sep-2026 FX · World Bank 2024
(GDP/GNI per capita) · Economist Big Mac 2026-07-01 · every plan row carries a
source URL (<a href="data/sources.csv">sources.csv</a>) · built by
build2.py + render_pages.py · DSL excluded by design.</footer>
<script>{extra_js}</script>
</body></html>"""

def json_rows(rows, keys):
    out = []
    for r in rows:
        o = {}
        for k in keys:
            v = r.get(k)
            if k in ("iso3", "country", "region", "operators", "fup_summary"):
                o[k] = v
            else:
                fv = fnum(v)
                o[k] = fv if fv is not None else None
        out.append(o)
    return json.dumps(out, separators=(",", ":"))

# ---------------- FIBER PAGE ----------------
fiber_keys = ["iso3", "country", "region", "n_ops", "operators", "avg_price",
              "avg_down", "avg_up", "ppm", "gni", "gdp", "bigmac", "monthly_inc",
              "pct_income", "price_bigmacs", "vs_median", "pop"]
fjson = json_rows(fiber, fiber_keys)

fiber_stats = f"""
<div class="stat red"><b>{stats.get('n_fiber_countries','—')}</b><span>countries with
operator-averaged fiber</span></div>
<div class="stat"><b>{stats.get('n_fiber_ops','—')}</b><span>operator plans averaged
(≈3 per country)</span></div>
<div class="stat amber"><b>${stats.get('med_fiber','—')}</b><span>median country avg
200M fiber plan /mo</span></div>
<div class="stat amber"><b>${stats.get('med_ppm','—')}</b><span>median $ per
Mbps</span></div>
<div class="stat green"><b>{stats.get('n_sources','—')}</b><span>source citations
across both studies</span></div>
"""

fiber_body = f"""
<div class="stats">{fiber_stats}</div>
<div class="controls">
 <label>Region:</label><select id="regionSel"><option value="">All regions</option></select>
 <label>X axis:</label>
 <select id="xsel">
  <option value="gni">GNI per capita (income)</option>
  <option value="gdp">GDP per capita</option>
  <option value="bigmac">Big Mac price $</option>
 </select>
</div>
<div class="grid two">
 <div class="card"><h2>Fiber price vs national income</h2>
 <p>Each bubble = one country's AVERAGE of its 3 operators' nearest-200 Mbps plan
 (down/up recorded). Log X. Dashed line = 2% of monthly income (A4AI fair-share).</p>
 <div id="c1"></div></div>
 <div class="card"><h2>$ per Mbps vs income</h2>
 <p>Unit-price efficiency: what 1 Mbps of fiber costs in each country
 (avg price ÷ avg download speed of the 3 plans).</p>
 <div id="c2"></div></div>
</div>
<div class="grid">
 <div class="card"><h2>Full fiber table — click headers to sort</h2>
 <p>operators = the companies averaged · src = per-operator source links</p>
 <div style="overflow-x:auto"><table id="ftbl"><thead><tr>
 <th class="l">Country</th><th class="l">Region</th><th>Ops</th>
 <th class="l">Operators averaged</th><th>avg $/mo</th><th>↓ avg</th><th>↑ avg</th>
 <th>$/Mbps</th><th>vs median</th><th>GNI $</th><th>GDP $</th>
 <th>% income</th><th>BigMacs</th><th class="l">src</th></tr></thead>
 <tbody></tbody></table></div></div>
</div>
"""

fiber_js = f"""
const FIBER={fjson};
const R2C={json.dumps(COLORS)};
function traces(){{const v=document.getElementById('regionSel').value;
const d=FIBER.filter(x=>(!v||x.region===v)&&x.gni&&x.avg_price);
const byR={{}};d.forEach(x=>(byR[x.region]=byR[x.region]||[]).push(x));
return Object.entries(byR).map(([r,ds])=>({{name:r,type:'scatter',mode:'markers',
 x:ds.map(x=>x.gni),y:ds.map(x=>x.avg_price),
 text:ds.map(x=>x.country+'<br>'+x.operators+'<br>'+x.avg_down+'↓ / '+x.avg_up+'↑'
  +' · $'+x.ppm+'/Mbps · '+x.pct_income+'% of income'),
 marker:{{color:R2C[r],opacity:.85,size:ds.map(x=>Math.max(8,Math.sqrt(x.pop||1)*2.2)),
 line:{{width:1,color:'#0d1117'}}}},
 hovertemplate:'%{{text}}<extra></extra>'}}))}}
function pptraces(){{const v=document.getElementById('regionSel').value;
const d=FIBER.filter(x=>(!v||x.region===v)&&x.gni&&x.ppm);
const byR={{}};d.forEach(x=>(byR[x.region]=byR[x.region]||[]).push(x));
return Object.entries(byR).map(([r,ds])=>({{name:r,type:'scatter',mode:'markers',
 x:ds.map(x=>x.gni),y:ds.map(x=>x.ppm),
 text:ds.map(x=>x.country+' · $'+x.avg_price+'/mo · '+x.avg_down+'↓'),
 marker:{{color:R2C[r],opacity:.85,size:ds.map(x=>Math.max(8,Math.sqrt(x.pop||1)*2.2))}},
 hovertemplate:'%{{text}}<extra></extra>'}}))}}
const base={{paper_bgcolor:'#161b22',plot_bgcolor:'#161b22',font:{{color:'#e6edf3',size:12}},
 margin:{{l:66,r:14,t:8,b:52}},xaxis:{{type:'log',gridcolor:'#21262d',title:'GNI per capita $ (log)'}},
 yaxis:{{type:'log',gridcolor:'#21262d',title:'fiber plan $/mo (avg of 3 ops)',rangemode:'tozero'}},
 legend:{{orientation:'h',y:1.14,font:{{size:11}}}},hovermode:'closest'}};
function xTitle(k){{return k==='gni'?'GNI per capita $ (log)':k==='gdp'?'GDP per capita $ (log)':'Big Mac price $ (log)'}}
function drawC1(){{const k=document.getElementById('xsel').value;
const v=document.getElementById('regionSel').value;
const d=FIBER.filter(x=>(!v||x.region===v)&&x[k]&&x.avg_price);
const byR={{}};d.forEach(x=>(byR[x.region]=byR[x.region]||[]).push(x));
const tr=Object.entries(byR).map(([r,ds])=>({{name:r,type:'scatter',mode:'markers',
 x:ds.map(x=>x[k]),y:ds.map(x=>x.avg_price),
 text:ds.map(x=>x.country+'<br>'+x.operators+'<br>'+x.avg_down+'↓ / '+x.avg_up+'↑'
  +' · $'+x.ppm+'/Mbps · '+x.pct_income+'% of income'),
 marker:{{color:R2C[r],opacity:.85,size:ds.map(x=>Math.max(8,Math.sqrt(x.pop||1)*2.2)),
 line:{{width:1,color:'#0d1117'}}}},hovertemplate:'%{{text}}<extra></extra>'}}));
const shapes=k==='gni'?[
 {{type:'line',x0:0,x1:1,xref:'paper',y0:120,y1:2400,line:{{color:'#ffbd2e',width:1.5,dash:'dash'}}}}]:[];
const ly={{...base,yaxis:{{...base.yaxis}},xaxis:{{...base.xaxis,title:xTitle(k)}},
 shapes,annotations:k==='gni'?[{{x:.02,y:2400,xref:'paper',yref:'y',text:'2% of monthly income',
 showarrow:false,font:{{color:'#ffbd2e',size:10}}}}]:[]}};
Plotly.react('c1',tr,ly,{{responsive:true,displayModeBar:false}})}}
function drawC2(){{const t=pptraces();
const l2={{paper_bgcolor:'#161b22',plot_bgcolor:'#161b22',font:{{color:'#e6edf3',size:12}},
 margin:{{l:66,r:14,t:8,b:52}},
 xaxis:{{type:'log',gridcolor:'#21262d',title:'GNI per capita $ (log)'}},
 yaxis:{{type:'log',gridcolor:'#21262d',title:'$ per Mbps (avg price ÷ avg ↓)',
   rangemode:'tozero'}},
 legend:{{orientation:'h',y:1.14,font:{{size:11}}}},hovermode:'closest'}};
Plotly.react('c2',t,l2,{{responsive:true,displayModeBar:false}})}}
function redraw(){{drawC1();drawC2();frender()}}
document.getElementById('xsel').onchange=redraw;
document.getElementById('regionSel').onchange=frender;
redraw();

// table
const SRC={json.dumps(fsrc)};
const tb=document.querySelector('#ftbl tbody');
let fsort={{k:'avg_price',dir:-1}};
function fval(r,k){{const v=r[k];if(v===''||v==null)return null;
const n=parseFloat(v);return isNaN(n)?v:n}}
function frender(){{
 const v=document.getElementById('regionSel').value;
 let rows=FIBER.filter(r=>!v||r.region===v);
 rows.sort((a,b)=>{{const x=fval(a,fsort.k),y=fval(b,fsort.k);
  if(x==null)return 1;if(y==null)return -1;
  return (typeof x==='string'?x.localeCompare(y):x-y)*fsort.dir}});
 tb.innerHTML=rows.map(r=>{{const s=(SRC[r.iso3]||[]);
  const links=s.slice(0,3).map((u,i)=>`<a href="${{u}}" target="_blank" rel="noopener">${{i+1}}</a>`).join(' ');
  const cls=(n)=>n>2?'bad':n>1?'warn':'ok';
  return `<tr><td class="l">${{r.country}}</td><td class="l"><span class="pill">${{r.region}}</span></td>
  <td>${{r.n_ops}}</td><td class="l exp">${{r.operators}}</td>
  <td><b>${{r.avg_price}}</b></td><td>${{r.avg_down||'–'}}</td><td>${{r.avg_up||'–'}}</td>
  <td>${{r.ppm||'–'}}</td><td class="${{cls(r.vs_median)}}">${{r.vs_median||'–'}}×</td>
  <td>${{r.gni?Number(r.gni).toLocaleString():'–'}}</td>
  <td>${{r.gdp?Number(r.gdp).toLocaleString():'–'}}</td>
  <td class="${{r.pct_income>2?'bad':r.pct_income>1?'warn':'ok'}}">${{r.pct_income||'–'}}%</td>
  <td>${{r.price_bigmacs||'–'}}</td><td class="l">${{links||'–'}}</td></tr>`}}).join('')}}
frender();
document.querySelectorAll('#ftbl th').forEach((th,i)=>th.onclick=()=>{{
 const keys=['country','region','n_ops','operators','avg_price','avg_down','avg_up',
 'ppm','vs_median','gni','gdp','pct_income','price_bigmacs','src'];
 const k=keys[i];if(k==='src')return;
 fsort=(fsort.k===k)?{{k,dir:-fsort.dir}}:{{k,dir:-1}};frender()}});
{region_filters_js(['c1','c2']) if False else ''}
"""

# region filter wiring (simple, explicit)
fiber_js += """
document.getElementById('regionSel').addEventListener('change', frender);
"""

fiber_html = page(
    "🌐 Fiber Study — what 200 Mbps really costs in 195 countries", "fiber.html",
    "Average of each country's <b>3 major operators</b>' nearest-to-200 Mbps fiber "
    "plan (Saudi = STC + Mobily + Zain + Salam). Real ↓/↑ speeds recorded. "
    "<b>DSL excluded.</b> Compared against World Bank GDP & GNI per capita and the "
    "Big Mac index. Every row links its sources.",
    fiber_body, fiber_js)
open(os.path.join(DOCS, "fiber.html"), "w", encoding="utf-8").write(fiber_html)

# ---------------- MOBILE PAGE ----------------
mobile_keys = ["iso3", "country", "region", "n_ops", "operators", "avg_10gb",
               "per_gb", "pct_income", "unlim_yes", "unlim_throttled", "unlim_no",
               "avg_unlimited_price", "fiveg_share", "fup_summary", "gni", "gdp",
               "bigmac", "price_bigmacs", "pop"]
mjson = json_rows(mobile, mobile_keys)

mobile_stats = f"""
<div class="stat red"><b>{stats.get('n_mobile_countries','—')}</b><span>countries with
operator-level mobile data</span></div>
<div class="stat"><b>{stats.get('n_mobile_ops','—')}</b><span>operator plans
(≈3 per country)</span></div>
<div class="stat amber"><b>${stats.get('med_per_gb','—')}</b><span>median price per
GB (10 GB plans)</span></div>
<div class="stat red"><b>{stats.get('pct_truly_unlim','—')}%</b><span>countries where
most operators are truly unlimited</span></div>
<div class="stat amber"><b>{stats.get('pct_unlim_any','—')}%</b><span>countries with at
least one unlimited offer</span></div>
"""

mobile_body = f"""
<div class="stats">{mobile_stats}</div>
<div class="controls">
 <label>Region:</label><select id="regionSel"><option value="">All regions</option></select>
</div>
<div class="grid two">
 <div class="card"><h2>Price per GB vs income</h2>
 <p>Avg prepaid ~10 GB price across 3 MNOs ÷ 10. Log-log. World median marked.</p>
 <div id="m1"></div></div>
 <div class="card"><h2>Is "unlimited" real? — FUP shares vs income</h2>
 <p>Share of each country's 3 operators by unlimited type:
 <span class="ok">truly unlimited</span> ·
 <span class="warn">unlimited with FUP/throttle</span> ·
 <span class="bad">no unlimited plan</span>.</p>
 <div id="m2"></div></div>
</div>
<div class="grid">
 <div class="card"><h2>5G availability vs income</h2>
 <p>% of the country's sampled operators offering 5G.</p><div id="m3" style="max-width:900px"></div></div>
</div>
<div class="grid">
 <div class="card"><h2>Full mobile table — FUP policies spelled out (click headers to sort)</h2>
 <div style="overflow-x:auto"><table id="mtbl"><thead><tr>
 <th class="l">Country</th><th class="l">Region</th><th>Ops</th>
 <th class="l">Operators</th><th>10GB $</th><th>$/GB</th><th>% income</th>
 <th class="ok">truly unl %</th><th class="warn">FUP %</th><th class="bad">none %</th>
 <th>unl plan $</th><th>5G %</th><th class="l">FUP policy (published)</th>
 <th class="l">src</th></tr></thead><tbody></tbody></table></div></div>
</div>
"""

mobile_js = f"""
const MOB={mjson};
const MSRC={json.dumps(msrc)};
const R2C={json.dumps(COLORS)};
const regsel=document.getElementById('regionSel');
const base={{paper_bgcolor:'#161b22',plot_bgcolor:'#161b22',font:{{color:'#e6edf3',size:12}},
 margin:{{l:66,r:14,t:8,b:52}},xaxis:{{type:'log',gridcolor:'#21262d',title:'GNI per capita $ (log)'}},
 legend:{{orientation:'h',y:1.14,font:{{size:11}}}},hovermode:'closest'}};
function drawM1(){{
 const v=regsel.value;
 const d=MOB.filter(x=>(!v||x.region===v)&&x.gni&&x.per_gb);
 const byR={{}};d.forEach(x=>(byR[x.region]=byR[x.region]||[]).push(x));
 const tr=Object.entries(byR).map(([r,ds])=>({{name:r,type:'scatter',mode:'markers',
  x:ds.map(x=>x.gni),y:ds.map(x=>x.per_gb),
  text:ds.map(x=>x.country+' · 10GB $'+x.avg_10gb+' · '+x.pct_income+'% of income'
   +'<br>'+x.unlim_yes+'% truly unlimited / '+x.unlim_throttled+'% FUP / '+x.unlim_no+'% none'),
  marker:{{color:R2C[r],opacity:.85,size:ds.map(x=>Math.max(8,Math.sqrt(x.pop||1)*2.2))}},
  hovertemplate:'%{{text}}<extra></extra>'}}));
 const ly={{...base,yaxis:{{type:'log',gridcolor:'#21262d',title:'$ per GB (log)',rangemode:'tozero'}}}};
 Plotly.react('m1',tr,ly,{{responsive:true,displayModeBar:false}})}}
function drawM2(){{
 const v=regsel.value;
 const d=MOB.filter(x=>(!v||x.region===v)&&x.gni).slice()
   .sort((a,b)=>a.gni-b.gni);
 const traces=[
  {{name:'truly unlimited',type:'bar',x:d.map(x=>x.country),y:d.map(x=>x.unlim_yes),
    marker:{{color:'#3fd68c'}},hovertemplate:'%{{x}}: %{{y}}% truly unlimited<extra></extra>'}},
  {{name:'unlimited w/ FUP',type:'bar',x:d.map(x=>x.country),y:d.map(x=>x.unlim_throttled),
    marker:{{color:'#ffbd2e'}},hovertemplate:'%{{x}}: %{{y}}% throttled/FUP<extra></extra>'}},
  {{name:'no unlimited',type:'bar',x:d.map(x=>x.country),y:d.map(x=>x.unlim_no),
    marker:{{color:'#ff5f56'}},hovertemplate:'%{{x}}: %{{y}}% none<extra></extra>'}}];
 const ly={{paper_bgcolor:'#161b22',plot_bgcolor:'#161b22',font:{{color:'#e6edf3',size:11}},
  margin:{{l:50,r:14,t:8,b:110}},barmode:'stack',
  xaxis:{{gridcolor:'#21262d',tickangle:-60,tickfont:{{size:9}}}},
  yaxis:{{gridcolor:'#21262d',title:'% of sampled operators',rangemode:'tozero'}},
  legend:{{orientation:'h',y:1.16}},height:430}};
 Plotly.react('m2',traces,ly,{{responsive:true,displayModeBar:false}})}}
function drawM3(){{
 const v=regsel.value;
 const d=MOB.filter(x=>(!v||x.region===v)&&x.gni&&x.fiveg_share!=null);
 const byR={{}};d.forEach(x=>(byR[x.region]=byR[x.region]||[]).push(x));
 const tr=Object.entries(byR).map(([r,ds])=>({{name:r,type:'scatter',mode:'markers',
  x:ds.map(x=>x.gni),y:ds.map(x=>x.fiveg_share),
  text:ds.map(x=>x.country+' · '+x.operators),
  marker:{{color:R2C[r],opacity:.85,size:ds.map(x=>Math.max(8,Math.sqrt(x.pop||1)*2.2))}},
  hovertemplate:'%{{text}}<extra></extra>'}}));
 const ly={{...base,yaxis:{{gridcolor:'#21262d',title:'% operators with 5G',
   range:[-5,105]}}}};
 Plotly.react('m3',tr,ly,{{responsive:true,displayModeBar:false}})}}
const mtb=document.querySelector('#mtbl tbody');
let msort={{k:'per_gb',dir:-1}};
function mval(r,k){{const v=r[k];if(v===''||v==null)return null;
 const n=parseFloat(v);return isNaN(n)?v:n}}
function mrender(){{
 const v=regsel.value;
 let rows=MOB.filter(r=>!v||r.region===v);
 rows.sort((a,b)=>{{const x=mval(a,msort.k),y=mval(b,msort.k);
  if(x==null)return 1;if(y==null)return -1;
  return (typeof x==='string'?x.localeCompare(y):x-y)*msort.dir}});
 mtb.innerHTML=rows.map(r=>{{const s=(MSRC[r.iso3]||[]);
  const links=s.slice(0,3).map((u,i)=>`<a href="${{u}}" target="_blank" rel="noopener">${{i+1}}</a>`).join(' ');
  return `<tr><td class="l">${{r.country}}</td><td class="l"><span class="pill">${{r.region}}</span></td>
  <td>${{r.n_ops}}</td><td class="l exp">${{r.operators}}</td>
  <td><b>${{r.avg_10gb||'–'}}</b></td><td>${{r.per_gb||'–'}}</td>
  <td class="${{r.pct_income>1?'bad':r.pct_income>0.4?'warn':'ok'}}">${{r.pct_income||'–'}}%</td>
  <td class="ok">${{r.unlim_yes}}%</td><td class="warn">${{r.unlim_throttled}}%</td>
  <td class="bad">${{r.unlim_no}}%</td>
  <td>${{r.avg_unlimited_price||'–'}}</td><td>${{r.fiveg_share}}%</td>
  <td class="l exp">${{(r.fup_summary||'–').replace(/;;/g,' · ')}}</td>
  <td class="l">${{links||'–'}}</td></tr>`}}).join('')}}
document.querySelectorAll('#mtbl th').forEach((th,i)=>{{
 const keys=['country','region','n_ops','operators','avg_10gb','per_gb','pct_income',
 'unlim_yes','unlim_throttled','unlim_no','avg_unlimited_price','fiveg_share',
 'fup_summary','src'];
 const k=keys[i];if(k==='src')return;
 th.onclick=()=>{{msort=(msort.k===k)?{{k,dir:-msort.dir}}:{{k,dir:-1}};mrender()}}}});
function redrawAll(){{drawM1();drawM2();drawM3();mrender()}}
regsel.onchange=redrawAll;
redrawAll();
"""

mobile_html = page(
    "📱 Mobile 4G/5G Study — GB per dollar, unlimited & fair-use policies",
    "mobile.html",
    "Per-country average of <b>3 mobile operators'</b> prepaid ~10 GB price, plus "
    "per-operator truth: is \"unlimited\" <b>truly unlimited</b>, throttled after a "
    "published <b>fair-use threshold</b>, or nonexistent? 5G coverage share included. "
    "Every FUP cell quotes the operator's published policy; sources linked per row.",
    mobile_body, mobile_js)
open(os.path.join(DOCS, "mobile.html"), "w", encoding="utf-8").write(mobile_html)

# ---------------- INDEX ----------------
worst_f = fiber[:10] if fiber else []
worst_m = [r for r in mobile if r["per_gb"]][:10]
def mini(rows, cols, labels):
    tr = ""
    for r in rows:
        tds = "".join(f"<td>{r.get(c) if r.get(c) not in (None,'') else '–'}</td>"
                      for c in cols)
        tr += f'<tr><td class="l"><b>{r["country"]}</b></td>{tds}</tr>'
    head = "".join(f'<th class="l">{l}</th>' for l in labels)
    return f"<table><thead><tr><th>Country</th>{head}</tr></thead><tbody>{tr}</tbody></table>"

index_body = f"""
<div class="stats">
 <div class="stat"><b>195</b><span>countries studied (all UN states)</span></div>
 <div class="stat"><b>{stats.get('n_fiber_ops','—')} + {stats.get('n_mobile_ops','—')}</b>
 <span>fiber + mobile operator plans</span></div>
 <div class="stat amber"><b>${stats.get('med_fiber','—')}</b><span>median 200M fiber
 plan (3-op average)</span></div>
 <div class="stat amber"><b>${stats.get('med_per_gb','—')}</b><span>median $/GB mobile</span></div>
 <div class="stat red"><b>{stats.get('n_sources','—')}</b><span>source URLs in
 sources.csv</span></div>
</div>
<div class="grid two">
 <div class="card" style="padding:18px">
  <h2>🌐 <a href="fiber.html">Fiber study</a> — DSL dropped</h2>
  <p>Each country's price = average of its 3 major operators' nearest-200 Mbps plan
  (STC+Mobily+Zain+Salam for Saudi). Charts: price vs GNI/GDP/Big Mac switchable,
  $/Mbps efficiency, 2%-of-income fair line, sortable table with per-operator
  sources.</p>
  <p><a href="fiber.html">Open fiber charts →</a> ·
  <a href="data/fiber_country.csv">fiber_country.csv</a> ·
  <a href="data/fiber_ops.csv">fiber_ops.csv (raw)</a></p>
 </div>
 <div class="card" style="padding:18px">
  <h2>📱 <a href="mobile.html">Mobile 4G/5G study</a> — GB/$, unlimited, FUP</h2>
  <p>Price per GB vs income, unlimited-type shares (truly unlimited / FUP-throttled /
  none) per country, 5G availability, and the full published fair-use policy text
  for every operator — sorted, sourced.</p>
  <p><a href="mobile.html">Open mobile charts →</a> ·
  <a href="data/mobile_country.csv">mobile_country.csv</a> ·
  <a href="data/mobile_ops.csv">mobile_ops.csv (raw)</a></p>
 </div>
</div>
<div class="grid two">
 <div class="card"><h2>💸 Top 10 most expensive fiber (3-op avg)</h2>{mini(worst_f,
   ['avg_price','avg_down','avg_up','pct_income'], ['$','↓','↑','%inc'])}</div>
 <div class="card"><h2>📉 Top 10 priciest mobile $/GB</h2>{mini(worst_m,
   ['per_gb','avg_10gb','pct_income'], ['$/GB','10GB $','%inc'])}</div>
</div>
<div class="grid"><div class="card" style="padding:14px 18px">
 <h2>Methodology</h2>
 <p class="sub" style="max-width:none">195 UN countries (+PSE, VAT) · fiber price =
 average of 3 real operators' nearest-to-200 Mbps consumer tier (actual ↓/↑ recorded;
 where 4 majors exist, e.g. KSA incl. Salam, all 4 are averaged) · mobile price =
 average of 3 MNOs' prepaid ~10 GB / 30 d · unlimited ∈
 yes | throttled (FUP threshold published) | no, with the operator's own policy text ·
 Sep-2026 FX · economics = World Bank 2024 GDP & GNI per capita (GNI = avg income) +
 Economist Big Mac 2026-07-01 · <b>DSL excluded from this study</b> ·
 every operator row in <a href="data/sources.csv">sources.csv</a> carries its URL;
 knowledge-only rows are marked as such.</p>
</div></div>
"""
index_html = page(
    "📊 Internet Scam Study — fiber & mobile prices vs what people earn",
    "index.html",
    "Two studies from one 195-country operator-level dataset: what <b>200 Mbps fiber</b> "
    "costs when you average each country's 3 big ISPs, and what <b>10 GB of mobile</b> "
    "costs — with the truth about \"unlimited\" plans and fair-use policies. "
    "Plotted against GDP, GNI per capita and the Big Mac.",
    index_body, "")
open(os.path.join(DOCS, "index.html"), "w", encoding="utf-8").write(index_html)
index_html = page(
    "📊 Internet Scam Study — fiber & mobile prices vs what people earn",
    "index.html",
    "Two studies from one 195-country operator-level dataset: what <b>200 Mbps fiber</b> "
    "costs when you average each country's 3 big ISPs, and what <b>10 GB of mobile</b> "
    "costs — with the truth about \"unlimited\" plans and fair-use policies. "
    "Plotted against GDP, GNI per capita and the Big Mac. "
    "New: <a href=\"saudi.html\">🇸🇦 Saudi Arabia vs similar-income peers</a>.",
    index_body, "")
open(os.path.join(DOCS, "index.html"), "w", encoding="utf-8").write(index_html)
open(os.path.join(DOCS, ".nojekyll"), "w").close()

# ---------------- SAUDI PAGE ----------------
import statistics as _st

def _f(r, k):
    try:
        return float(r.get(k)) if r.get(k) not in (None, "") else None
    except (ValueError, TypeError):
        return None

peers = [r for r in fiber if (g := _f(r, "gni")) and 25000 <= g <= 55000]
peers.sort(key=lambda r: -(_f(r, "avg_price") or 0))
_mob = {r["iso3"]: r for r in mobile}
_ksu_f = next(r for r in fiber if r["iso3"] == "SAU")
_ksu_m = _mob["SAU"]
_peer_f = [r for r in peers if r["iso3"] != "SAU"]
_med_f = _st.median([_f(r, "avg_price") for r in _peer_f])
_med_gb = _st.median([_f(_mob[r["iso3"]], "per_gb") for r in _peer_f
                      if r["iso3"] in _mob and _f(_mob[r["iso3"]], "per_gb")])
_med_inc_f = _st.median([_f(r, "pct_income") for r in _peer_f if _f(r, "pct_income")])
_med_inc_m = _st.median([_f(_mob[r["iso3"]], "pct_income") for r in _peer_f
                         if r["iso3"] in _mob and _f(_mob[r["iso3"]], "pct_income")])
_kf, _km = _f(_ksu_f, "avg_price"), _f(_ksu_m, "per_gb")

def _fmt(v, d=2):
    return "–" if v is None else f"{v:.{d}f}"

sau_ops_f = [r for r in fops if r.get("iso3") == "SAU"]
sau_ops_m = [r for r in mops if r.get("iso3") == "SAU"]

def _link(u):
    u = (u or "").strip()
    if not u or u == "knowledge":
        return "–"
    d = urlparse(u).netloc.replace("www.", "")
    return f'<a href="{u}" target="_blank" rel="noopener">{d}</a>'

f_rows = []
for r in peers:
    p, sau = _f(r, "avg_price"), r["iso3"] == "SAU"
    m = _mob.get(r["iso3"], {})
    f_rows.append(
        f'<tr{" class=ksu" if sau else ""}><td class="l"><b>{r["country"]}'
        f'{" 🇸🇦" if sau else ""}</b></td>'
        f'<td>{r["n_ops"]}</td><td>{_fmt(p)}</td>'
        f'<td>{r["avg_down"] or "–"}↓/{r["avg_up"] or "–"}↑</td>'
        f'<td>{r["ppm"] or "–"}</td>'
        f'<td>{_fmt(_f(r, "gni"), 0)}</td>'
        f'<td class="{"bad" if (_f(r,"pct_income") or 0) > 2 else "warn" if (_f(r,"pct_income") or 0) > 1 else "ok"}>'
        f'{_fmt(_f(r, "pct_income"))}%</td>'
        f'<td>{"—" if sau else f"{p / _kf:.2f}×"}</td></tr>')

m_sorted = sorted(peers, key=lambda r: -(_f(_mob.get(r["iso3"], {}), "per_gb") or 0))
m_rows = []
for r in m_sorted:
    x = _mob.get(r["iso3"], {})
    g, sau = _f(x, "per_gb"), r["iso3"] == "SAU"
    m_rows.append(
        f'<tr{" class=ksu" if sau else ""}><td class="l"><b>{r["country"]}'
        f'{" 🇸🇦" if sau else ""}</b></td>'
        f'<td>{x.get("n_ops", "–")}</td><td>{_fmt(_f(x, "avg_10gb"))}</td>'
        f'<td>{_fmt(g, 3)}</td>'
        f'<td class="ok">{x.get("unlim_yes", "–")}%</td>'
        f'<td class="warn">{x.get("unlim_throttled", "–")}%</td>'
        f'<td class="bad">{x.get("unlim_no", "–")}%</td>'
        f'<td>{_fmt(_f(x, "avg_unlimited_price"))}</td>'
        f'<td>{x.get("fiveg_share", "–")}%</td>'
        f'<td>{"—" if sau else (f"{g / _km:.2f}×" if g else "–")}</td></tr>')

op_f = "".join(
    f'<tr><td class="l"><b>{o["operator"]}</b></td><td class="l">{o["plan_name"]}</td>'
    f'<td>{o["speed_down_mbps"] or "–"}↓/{o["speed_up_mbps"] or "–"}↑</td>'
    f'<td><b>${o["price_usd_month"] or "–"}</b></td><td class="l">{_link(o["source_url"])}</td>'
    f'<td class="l exp">{o["notes"][:140]}</td></tr>' for o in sau_ops_f)
op_m = "".join(
    f'<tr><td class="l"><b>{o["operator"]}</b></td><td>{o["network"]}</td>'
    f'<td><b>${o["ten_gb_price_usd"] or "–"}</b></td>'
    f'<td>${o["unlimited_offer_usd"] or "–"}</td>'
    f'<td class="{"ok" if o["unlimited"]=="yes" else "warn" if o["unlimited"]=="throttled" else "bad"}">'
    f'{o["unlimited"]}</td><td class="l exp">{o["fup_policy"]}</td>'
    f'<td class="l">{_link(o["source_url"])}</td></tr>' for o in sau_ops_m)

sau_body = f"""
<div class="stats">
 <div class="stat red"><b>${_fmt(_kf)}/mo</b><span>KSA fiber (STC+Mobily+Zain+Salam avg,
  {_ksu_f["avg_down"]}↓/{_ksu_f["avg_up"]}↑) vs peer median ${_med_f} {_kf / _med_f:.1f}×</span></div>
 <div class="stat red"><b>${_fmt(_km, 3)}/GB</b><span>KSA mobile vs peer median
  ${_med_gb:.3f} {_km / _med_gb:.1f}×</span></div>
 <div class="stat amber"><b>{_fmt(_f(_ksu_f, "pct_income"))}%</b><span>of Saudi monthly
  income on fiber (peer median {_med_inc_f:.2f}%, fair line 2%)</span></div>
 <div class="stat amber"><b>${_fmt(_f(_ksu_m, "avg_unlimited_price"))}</b><span>cheapest
  Saudi unlimited plan (STC/Mobily/Zain/Salam avg)</span></div>
</div>
<style>.ksu td{{background:#1c2a1c;font-weight:600}}</style>
<div class="grid"><div class="card" style="padding:14px 18px">
<h2>Verdict — how scammed is Saudi Arabia?</h2>
<p class="sub" style="max-width:none">Peer group = <b>{len(peers)} countries with GNI
per capita $25k–$55k</b> (Gulf + Europe + Korea/Japan + Canada …). KSA fiber costs
<b>${_fmt(_kf)} vs peer median ${_med_f} = {_kf / _med_f:.1f}×</b> and eats
<b>{_fmt(_f(_ksu_f, "pct_income"))}% of monthly income vs {_med_inc_f:.2f}% peer median</b>
(above the 2% fair line). Mobile: <b>${_fmt(_km, 3)}/GB vs ${_med_gb:.3f} peer median =
{_km / _med_gb:.1f}×</b>. Upload is the structural gap: KSA avg
<b>{_ksu_f["avg_up"]}↑ on {_ksu_f["avg_down"]}↓ (1:{float(_ksu_f["avg_down"]) / float(_ksu_f["avg_up"]):.1f})</b>
while peers like Spain (400/400), France (500/500), Japan (800/800) are symmetric.
Bright spots: 100% truly-unlimited mobile (no FUP games) and 100% 5G across all four operators.</p>
</div></div>
<div class="grid two">
 <div class="card"><h2>KSA fiber price vs peers (same income band)</h2>
 <p>Red dashed = KSA level. Log X.</p><div id="s1"></div></div>
 <div class="card"><h2>KSA $/GB vs peers</h2><p>Red dashed = KSA level. Log X.</p>
 <div id="s2"></div></div>
</div>
<div class="grid"><div class="card">
<h2>TABLE 1 — Fiber: Saudi Arabia vs {len(peers)} similar-income countries</h2>
<p>avg $/mo = mean of each country's ~3 operators' nearest-200 Mbps plan ·
multiple = country price ÷ KSA price</p>
<div style="overflow-x:auto"><table><thead><tr>
<th class="l">Country</th><th>Ops</th><th>avg $/mo</th><th>↓/↑ avg</th><th>$/Mbps</th>
<th>GNI $</th><th>% income</th><th>vs KSA</th></tr></thead><tbody>
{"".join(f_rows)}</tbody></table></div></div></div>
<div class="grid"><div class="card">
<h2>KSA fiber, operator by operator (the average above)</h2>
<div style="overflow-x:auto"><table><thead><tr>
<th class="l">Operator</th><th class="l">Plan</th><th>↓/↑</th><th>$/mo</th>
<th class="l">Source</th><th class="l">Notes</th></tr></thead><tbody>
{op_f}</tbody></table></div></div></div>
<div class="grid"><div class="card">
<h2>TABLE 2 — Mobile: Saudi Arabia vs similar-income countries</h2>
<p>10GB $ = mean of 3 MNOs' prepaid ~10 GB · multiple = country $/GB ÷ KSA $/GB</p>
<div style="overflow-x:auto"><table><thead><tr>
<th class="l">Country</th><th>Ops</th><th>10GB $</th><th>$/GB</th>
<th class="ok">truly %</th><th class="warn">FUP %</th><th class="bad">none %</th>
<th>unl plan $</th><th>5G %</th><th>vs KSA</th></tr></thead><tbody>
{"".join(m_rows)}</tbody></table></div></div></div>
<div class="grid"><div class="card">
<h2>KSA mobile, operator by operator</h2>
<div style="overflow-x:auto"><table><thead><tr>
<th class="l">Operator</th><th>Net</th><th>10GB $</th><th>Unl $</th><th>Unlimited?</th>
<th class="l">FUP policy (published)</th><th class="l">Source</th></tr></thead><tbody>
{op_m}</tbody></table></div></div></div>
"""

_MOB_JSON = json.dumps({r["iso3"]: {k: (_mob[r["iso3"]].get(k)
    if r["iso3"] in _mob else None) for k in ("per_gb", "avg_10gb", "country")}
    for r in peers})

sau_js = f"""
const PEERS={json_rows(peers, fiber_keys)};
const MOB={_MOB_JSON};
const base={{paper_bgcolor:'#161b22',plot_bgcolor:'#161b22',font:{{color:'#e6edf3',size:12}},
margin:{{l:60,r:14,t:8,b:52}},xaxis:{{type:'log',gridcolor:'#21262d',title:'GNI per capita $ (log)'}},
hovermode:'closest'}};
(function(){{
const d=PEERS.filter(x=>x.gni&&x.avg_price);
const col=d.map(x=>x.iso3==='SAU'?'#ff5f56':'#58a6ff');
const sz=d.map(x=>x.iso3==='SAU'?18:10);
Plotly.react('s1',[{{type:'scatter',mode:'markers',x:d.map(x=>x.gni),y:d.map(x=>x.avg_price),
text:d.map(x=>x.country+' $'+x.avg_price+' ('+x.avg_down+'↓/'+x.avg_up+'↑)'),
marker:{{color:col,size:sz}},hovertemplate:'%{{text}}<extra></extra>'}}],
{{...base,yaxis:{{type:'log',gridcolor:'#21262d',title:'fiber $/mo'}},
shapes:[{{type:'line',x0:0,x1:1,xref:'paper',y0:{_kf},y1:{_kf},
line:{{color:'#ff5f56',width:1.5,dash:'dash'}}}}],
annotations:[{{x:.98,y:{_kf},xref:'paper',yref:'y',text:'KSA ${_fmt(_kf)}',
showarrow:false,xanchor:'right',font:{{color:'#ff5f56',size:11}}}}]}},
{{responsive:true,displayModeBar:false}});
const d2=PEERS.filter(x=>x.gni&&MOB[x.iso3]&&MOB[x.iso3].per_gb);
const c2=d2.map(x=>x.iso3==='SAU'?'#ff5f56':'#3fd68c');
const s2=d2.map(x=>x.iso3==='SAU'?18:10);
Plotly.react('s2',[{{type:'scatter',mode:'markers',
x:d2.map(x=>x.gni),y:d2.map(x=>MOB[x.iso3].per_gb),
text:d2.map(x=>x.country+' $'+MOB[x.iso3].per_gb+'/GB'),
marker:{{color:c2,size:s2}},hovertemplate:'%{{text}}<extra></extra>'}}],
{{...base,yaxis:{{type:'log',gridcolor:'#21262d',title:'$/GB (log)'}},
shapes:[{{type:'line',x0:0,x1:1,xref:'paper',y0:{_km},y1:{_km},
line:{{color:'#ff5f56',width:1.5,dash:'dash'}}}}],
annotations:[{{x:.98,y:{_km},xref:'paper',yref:'y',text:'KSA ${_fmt(_km, 3)}',
showarrow:false,xanchor:'right',font:{{color:'#ff5f56',size:11}}}}]}},
{{responsive:true,displayModeBar:false}});
}})();
"""

sau_html = page(
    "🇸🇦 Saudi Arabia vs similar-income countries — fiber & mobile",
    "saudi.html",
    "KSA (STC + Mobily + Zain + Salam averaged) against "
    f"<b>{len(peers)} countries earning $25k–$55k per person</b>: what each pays for "
    "fiber and mobile, and the scam multiple vs Saudi prices. Two tables + operator breakdowns.",
    sau_body, sau_js)
open(os.path.join(DOCS, "saudi.html"), "w", encoding="utf-8").write(sau_html)
print("saudi peers:", len(peers))

print("wrote:", sorted(os.listdir(DOCS)))
print("fiber rows:", len(fiber), "mobile rows:", len(mobile))
