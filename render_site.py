#!/usr/bin/env python3
"""Render the static site (Arabic at docs/, English at docs/en/) from build2 outputs.

Charts are plain SVG generated here (no chart library); JS is only for the
country picker, tooltips, table sort/search and region chips.
"""
import csv, json, math, os, statistics, html
from urllib.parse import urlparse

BASE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(BASE, "docs")
D = os.path.join(DOCS, "data")
RAW = os.path.join(BASE, "data")
HOME_ISO = "SAU"
FAIR = 2.0  # % of monthly income (ITU/A4AI affordability target)


def load(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def f(v):
    try:
        return float(v) if v not in (None, "") else None
    except ValueError:
        return None


esc = html.escape

fiber = {r["iso3"]: r for r in load(os.path.join(D, "fiber_country.csv"))}
mobile = {r["iso3"]: r for r in load(os.path.join(D, "mobile_country.csv"))}
fops = load(os.path.join(D, "fiber_ops.csv"))
mops = load(os.path.join(D, "mobile_ops.csv"))
stats = json.load(open(os.path.join(D, "stats.json")))
econ = {r["iso3"]: r for r in load(os.path.join(RAW, "economics.csv"))}
names_ar = {r["iso3"]: r["name_ar"] for r in load(os.path.join(RAW, "names_ar.csv"))}
iso2s = {r["iso3"]: r["iso2"] for r in load(os.path.join(RAW, "names_ar.csv"))}
meta = {r["iso3"]: r for r in load(os.path.join(RAW, "countries_195.csv"))}

REGIONS = ["Asia", "Africa", "Europe", "North America", "South America", "Oceania"]

# ---------------------------------------------------------------- strings
T = {
"ar": dict(
    dir="rtl", title="فاتورة الإنترنت مقابل الدخل",
    desc="دراسة لأسعار الألياف والجوال في 195 دولة، بمتوسط أكبر 3 مشغّلين في كل دولة، مقارنةً بدخل الفرد.",
    nav_home="الرئيسية", nav_fiber="الألياف", nav_mobile="الجوال", nav_sau="السعودية مقابل نظيراتها",
    nav_method="المنهجية والمصادر", other_lang="English", other_lang_code="en",
    pick="اختر دولة",
    regions={"Asia": "آسيا", "Africa": "أفريقيا", "Europe": "أوروبا", "North America": "أمريكا الشمالية",
             "South America": "أمريكا الجنوبية", "Oceania": "أوقيانوسيا"},
    all_regions="كل المناطق",
    usd="$", per_mo="شهرياً", mbps="ميغابت", gb="غيغابايت",
    fair_line="حدّ الإنصاف 2٪ من الدخل",
    strip_fiber_h="كم تأكل باقة الألياف من الدخل الشهري",
    strip_fiber_p="كل نقطة دولة: متوسط سعر باقة الألياف الأقرب إلى 200 ميغابت لدى أكبر مشغّليها، كنسبة من متوسط دخل الفرد الشهري (مقياس لوغاريتمي). الأحمر فوق حدّ 2٪.",
    strip_mobile_h="كم يأكل 10 غيغابايت جوال من الدخل الشهري",
    strip_mobile_p="كل نقطة دولة: متوسط كلفة 10 غيغابايت على الأقل لمدة شهر لدى أكبر مشغّليها، كنسبة من الدخل الشهري.",
    scatter_h="السعر مقابل الدخل",
    scatter_p="محور أفقي: دخل الفرد السنوي (GNI). محور رأسي: سعر الألياف الشهري. كلاهما لوغاريتمي. الدول الغنية تدفع أكثر بالدولار لكن أقل من دخلها.",
    x_gni="دخل الفرد السنوي $", y_fiber="سعر الألياف $ / شهر", y_gb="سعر 1 غيغابايت $",
    table_h="كل الدول", search="ابحث عن دولة أو مشغّل",
    th_country="الدولة", th_price="السعر $", th_speed="السرعة", th_pct="٪ من الدخل", th_ppm="$ لكل ميغابت",
    th_gni="الدخل السنوي $", th_ops="المشغّلون", th_vs="مقابل النظراء", th_flags="ملاحظات",
    th_gb="$ / غيغابايت", th_10="10 غيغابايت $", th_unl="غير محدود", th_5g="5G", th_unlp="أرخص غير محدود $",
    flag_ops="أقل من 3 مشغّلين", flag_est="دخل تقديري", flag_old="دخل قديم", flag_unv="أسعار غير موثّقة",
    ops_h="تفاصيل المشغّلين والمصادر", src="المصدر", plan="الباقة", fup="سياسة الاستخدام العادل",
    unl_yes="غير محدود فعلاً", unl_thr="محدود بعد حد", unl_no="لا يوجد",
    footer="البيانات: أسعار المشغّلين المنشورة، البنك الدولي (دخل الفرد)، مؤشر بيغ ماك (The Economist). الشيفرة والبيانات على GitHub.",
    repo="المستودع",
),
"en": dict(
    dir="ltr", title="Internet bill vs income",
    desc="Fiber and mobile prices in 195 countries, averaged over each country's 3 biggest operators, compared with income per person.",
    nav_home="Home", nav_fiber="Fiber", nav_mobile="Mobile", nav_sau="Saudi vs peers",
    nav_method="Method & sources", other_lang="العربية", other_lang_code="ar",
    pick="Pick a country",
    regions={r: r for r in REGIONS}, all_regions="All regions",
    usd="$", per_mo="/mo", mbps="Mbps", gb="GB",
    fair_line="2% of income fairness line",
    strip_fiber_h="How much of a monthly income a fiber plan takes",
    strip_fiber_p="Each dot is a country: the average price of the plan nearest 200 Mbps at its biggest operators, as a share of average monthly income per person (log scale). Red is above 2%.",
    strip_mobile_h="How much of a monthly income 10 GB of mobile data takes",
    strip_mobile_p="Each dot is a country: the average cost of getting at least 10 GB for a month at its biggest operators, as a share of monthly income.",
    scatter_h="Price against income",
    scatter_p="Across: income per person per year (GNI). Up: monthly fiber price. Both log. Rich countries pay more dollars but a smaller share of income.",
    x_gni="Income per person / year $", y_fiber="Fiber $ / month", y_gb="$ per GB",
    table_h="All countries", search="Search a country or operator",
    th_country="Country", th_price="Price $", th_speed="Speed", th_pct="% of income", th_ppm="$ per Mbps",
    th_gni="Income / year $", th_ops="Operators", th_vs="vs peers", th_flags="Notes",
    th_gb="$ / GB", th_10="10 GB $", th_unl="Unlimited", th_5g="5G", th_unlp="Cheapest unlimited $",
    flag_ops="fewer than 3 operators", flag_est="estimated income", flag_old="old income data", flag_unv="unverified prices",
    ops_h="Operators and sources", src="source", plan="Plan", fup="Fair-use policy",
    unl_yes="truly unlimited", unl_thr="throttled after a cap", unl_no="none",
    footer="Data: published operator prices, World Bank (income per person), The Economist Big Mac index. Code and data on GitHub.",
    repo="repository",
),
}


STATUS = {
    "ar": dict(verified="مطابق للمصدر", corrected="صُحّح", new="أُضيف", unverified="غير مؤكَّد",
               unsourced="بلا مصدر، خارج المتوسط", not_offered="لا يقدّم الخدمة"),
    "en": dict(verified="verified", corrected="corrected", new="added", unverified="not re-confirmed",
               unsourced="no source, not averaged", not_offered="not offered"),
}


def name(iso, lang):
    if lang == "ar":
        return names_ar.get(iso) or meta.get(iso, {}).get("country", iso)
    return meta.get(iso, {}).get("country", iso)


def money(v, nd=2):
    if v is None:
        return "–"
    if v >= 100:
        return f"{v:,.0f}"
    return f"{v:,.{nd}f}"


def pct(v):
    if v is None:
        return "–"
    return f"{v:.1f}%" if v < 10 else f"{v:.0f}%"


# ---------------------------------------------------------------- per-country model
def gni_info(iso):
    e = econ.get(iso, {})
    g = f(e.get("gni_per_capita_usd"))
    note = e.get("gni_note") or "missing"
    yr = e.get("gni_year") or ""
    old = bool(yr) and int(yr) < 2023
    return g, note, yr, old


def verified_share(rows):
    st = [r.get("status") for r in rows if r.get("status")]
    if not st:
        return None
    ok = sum(1 for s in st if s in ("verified", "corrected", "new"))
    return ok / len(st)


ops_f, ops_m = {}, {}
for r in fops:
    ops_f.setdefault(r["iso3"], []).append(r)
for r in mops:
    ops_m.setdefault(r["iso3"], []).append(r)

C = {}
for iso, m in meta.items():
    g, note, yr, old = gni_info(iso)
    fr, mr = fiber.get(iso), mobile.get(iso)
    c = dict(iso=iso, region=m["region"], gni=g, gni_note=note, gni_year=yr, gni_old=old)
    if fr:
        c.update(fp=f(fr["avg_price"]), fd=f(fr["avg_down"]), fu=f(fr["avg_up"]),
                 fpct=f(fr["pct_income"]), fppm=f(fr["ppm"]), fn=int(fr["n_ops"]))
    if mr and f(mr.get("per_gb")):
        c.update(mgb=f(mr["per_gb"]), m10=f(mr["avg_10gb"]), mpct=f(mr["pct_income"]),
                 mn=int(mr["n_ops"]), uy=int(mr["unlim_yes"]), ut=int(mr["unlim_throttled"]),
                 un=int(mr["unlim_no"]), up=f(mr["avg_unlimited_price"]), g5=int(mr["fiveg_share"]))
    c["fv"] = verified_share(ops_f.get(iso, []))
    c["mv"] = verified_share(ops_m.get(iso, []))
    C[iso] = c


def peers(iso, key):
    """Countries with income within x1.5 (widened to x2 if fewer than 8) that have `key`."""
    g = C[iso]["gni"]
    if not g:
        return []
    for k in (1.5, 2.0, 3.0):
        p = [c for i, c in C.items() if i != iso and c.get("gni") and c.get(key) is not None
             and g / k <= c["gni"] <= g * k]
        if len(p) >= 8:
            return p
    return p


for iso, c in C.items():
    for key, pk in (("fp", "f"), ("mgb", "m")):
        p = peers(iso, key)
        if c.get(key) is not None and len(p) >= 5:
            medp = statistics.median(x[key] for x in p)
            c[pk + "peer_n"] = len(p)
            c[pk + "peer_med"] = medp
            c[pk + "mult"] = c[key] / medp if medp else None
            c[pk + "peer_lo"] = min(x["gni"] for x in p)
            c[pk + "peer_hi"] = max(x["gni"] for x in p)
            pa = [x for x in p if (x.get(pk + "v") or 0) >= 0.5]
            if len(pa) >= 5 and (c.get(pk + "v") or 0) >= 0.5:
                ma = statistics.median(x[key] for x in pa)
                c[pk + "mult_aud"] = c[key] / ma
                c[pk + "peer_aud_n"] = len(pa)


# ---------------------------------------------------------------- SVG charts
def logx(v, lo, hi, x0, x1):
    v = min(max(v, lo), hi)
    return x0 + (math.log10(v) - math.log10(lo)) / (math.log10(hi) - math.log10(lo)) * (x1 - x0)


def tick_fmt(v):
    if v >= 1000:
        return f"{v/1000:g}k"
    return f"{v:g}"


_clip = [0]


def flag_defs():
    _clip[0] += 1
    cid = f"fc{_clip[0]}"
    return cid, (f'<defs><clipPath id="{cid}" clipPathUnits="objectBoundingBox">'
                 f'<circle cx=".5" cy=".5" r=".5"/></clipPath></defs>')


def flag_mark(c, x, y, cls, cid, lang, region=False):
    """a round flag with a coloured ring (red above the 2% line, teal below)"""
    iso2 = (iso2s.get(c["iso"]) or "").lower()
    pre = "" if lang == "ar" else "../"
    reg = f' data-region="{esc(c["region"])}"' if region else ""
    return (f'<g class="{cls}" data-iso="{c["iso"]}"{reg} data-x="{x:.1f}" data-y="{y:.1f}">'
            f'<circle class="ring" cx="{x:.1f}" cy="{y:.1f}" r="9"/>'
            f'<image href="{pre}assets/flags/{iso2}.webp" x="{x-7.5:.1f}" y="{y-7.5:.1f}" width="15" height="15" '
            f'clip-path="url(#{cid})" preserveAspectRatio="xMidYMid slice"/></g>')


def strip_svg(key, lang, ticks, lo, hi, unit="%"):
    t = T[lang]
    W, lane, top, left, right = 900, 70, 18, 128, 20
    cid, defs = flag_defs()
    H = top + lane * len(REGIONS) + 40
    x0, x1 = left, W - right
    parts = [f'<svg class="chart strip" data-kind="{key[0]}" viewBox="0 0 {W} {H}" role="img" '
             f'aria-label="{esc(t["strip_fiber_h"] if key=="fpct" else t["strip_mobile_h"])}">' + defs]
    for v in ticks:
        x = logx(v, lo, hi, x0, x1)
        parts.append(f'<line class="grid" x1="{x:.1f}" x2="{x:.1f}" y1="{top}" y2="{H-34}"/>'
                     f'<text class="tick" x="{x:.1f}" y="{H-16}" text-anchor="middle">{tick_fmt(v)}{unit}</text>')
    xf = logx(FAIR, lo, hi, x0, x1)
    parts.append(f'<line class="fair" x1="{xf:.1f}" x2="{xf:.1f}" y1="{top-6}" y2="{H-34}"/>')
    for i, reg in enumerate(REGIONS):
        y = top + lane * i + lane / 2
        parts.append(f'<line class="lane" x1="{x0}" x2="{x1}" y1="{y:.1f}" y2="{y:.1f}"/>'
                     f'<text class="lab" x="{left-12}" y="{y+5:.1f}" text-anchor="end">{esc(t["regions"][reg])}</text>')
        pts = sorted([c for c in C.values() if c["region"] == reg and c.get(key)], key=lambda c: c[key])
        for j, c in enumerate(pts):
            x = logx(c[key], lo, hi, x0, x1)
            dy = ((j % 3) - 1) * 17  # deterministic 3-row jitter so neighbouring flags separate
            cls = "dot over" if c[key] > FAIR else "dot under"
            parts.append(flag_mark(c, x, y + dy, cls, cid, lang))
    parts.append("</svg>")
    return "".join(parts)


def scatter_svg(ykey, lang, ylo, yhi, yticks, ylabel):
    t = T[lang]
    W, H, l, r, tp, b = 900, 520, 70, 20, 16, 56
    xlo, xhi = 300, 250000
    xt = [500, 1000, 3000, 10000, 30000, 100000]
    cid, defs = flag_defs()
    parts = [f'<svg class="chart scatter" data-kind="{"f" if ykey=="fp" else "m"}" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(t["scatter_h"])}">' + defs]
    for v in xt:
        x = logx(v, xlo, xhi, l, W - r)
        parts.append(f'<line class="grid" x1="{x:.1f}" x2="{x:.1f}" y1="{tp}" y2="{H-b}"/>'
                     f'<text class="tick" x="{x:.1f}" y="{H-b+20}" text-anchor="middle">{tick_fmt(v)}</text>')
    for v in yticks:
        y = H - b - (logx(v, ylo, yhi, 0, H - b - tp))
        parts.append(f'<line class="grid" x1="{l}" x2="{W-r}" y1="{y:.1f}" y2="{y:.1f}"/>'
                     f'<text class="tick" x="{l-8}" y="{y+4:.1f}" text-anchor="end">{tick_fmt(v)}</text>')
    # 2%-of-income line: price = 0.02 * gni / 12 (fiber only)
    if ykey == "fp":
        pts = []
        for gx in (xlo, xhi):
            p = FAIR / 100 * gx / 12
            pts.append((logx(gx, xlo, xhi, l, W - r), H - b - logx(p, ylo, yhi, 0, H - b - tp)))
        parts.append(f'<line class="fair" x1="{pts[0][0]:.1f}" y1="{pts[0][1]:.1f}" x2="{pts[1][0]:.1f}" y2="{pts[1][1]:.1f}"/>')
    for c in sorted(C.values(), key=lambda c: c["iso"] == HOME_ISO):
        if not (c.get(ykey) and c.get("gni")):
            continue
        x = logx(c["gni"], xlo, xhi, l, W - r)
        y = H - b - logx(c[ykey], ylo, yhi, 0, H - b - tp)
        over = (c.get("fpct") if ykey == "fp" else c.get("mpct")) or 0
        cls = "dot over" if over > FAIR else "dot under"
        parts.append(flag_mark(c, x, y, cls, cid, lang, region=True))
    parts.append(f'<text class="axis" x="{(l+W-r)/2:.0f}" y="{H-8}" text-anchor="middle">{esc(t["x_gni"])}</text>'
                 f'<text class="axis" transform="translate(16 {(tp+H-b)/2:.0f}) rotate(-90)" text-anchor="middle">{esc(ylabel)}</text>')
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------- page chrome
def page(lang, slug, title, body, extra_head=""):
    t = T[lang]
    pre = "" if lang == "ar" else "../"
    other = (f"en/{slug}" if lang == "ar" else f"../{slug}")
    nav = [("index.html", t["nav_home"]), ("fiber.html", t["nav_fiber"]),
           ("mobile.html", t["nav_mobile"]), ("saudi.html", t["nav_sau"]),
           ("method.html", t["nav_method"])]
    navh = "".join(f'<a href="{h}"{" aria-current=page" if h == slug else ""}>{esc(n)}</a>' for h, n in nav)
    return f"""<!doctype html>
<html lang="{lang}" dir="{t['dir']}">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(t['desc'])}">
<link rel="stylesheet" href="{pre}assets/fonts.css"><link rel="stylesheet" href="{pre}assets/site.css">
{extra_head}</head>
<body>
<header class="top"><a class="brand" href="index.html">{esc(t['title'])}</a>
<nav aria-label="primary">{navh}</nav>
<a class="lang" href="{other}" hreflang="{t['other_lang_code']}">{esc(t['other_lang'])}</a></header>
<main>
{body}
</main>
<footer><p>{esc(t['footer'])} <a href="https://github.com/24bit192kHz/internet-scam-study">{esc(t['repo'])}</a></p></footer>
<div id="tip" role="status" hidden></div>
<script>window.LANG="{lang}";</script>
<script src="{pre}assets/data.js"></script><script src="{pre}assets/site.js"></script>
</body></html>"""


def flags(c, kind, lang):
    t = T[lang]
    out = []
    n = c.get("fn" if kind == "f" else "mn")
    if n is not None and n < 3:
        out.append(t["flag_ops"])
    if c["gni_note"] in ("est", "gdp-fallback"):
        out.append(t["flag_est"])
    elif c["gni_old"]:
        out.append(t["flag_old"] + f" ({c['gni_year']})")
    v = c.get("fv" if kind == "f" else "mv")
    if v is not None and v < 0.5:
        out.append(t["flag_unv"])
    return out


def vs_cell(m):
    if m is None:
        return '<td data-v="">–</td>'
    cls = "hi" if m >= 1.25 else ("lo" if m <= 0.8 else "")
    return f'<td data-v="{m:.3f}" class="{cls}"><bdi dir="ltr">{m:.1f}×</bdi></td>'


def num_td(v, txt=None):
    if v is None:
        return '<td data-v="">–</td>'
    return f'<td data-v="{v}"><bdi dir="ltr">{txt if txt is not None else v}</bdi></td>'


def fiber_table(lang, isos=None):
    t = T[lang]
    rows = []
    for c in sorted(C.values(), key=lambda c: -(c.get("fpct") or -1)):
        if c.get("fp") is None or (isos and c["iso"] not in isos):
            continue
        fl = flags(c, "f", lang)
        sp = f'{c["fd"]:.0f}' + (f'/{c["fu"]:.0f}' if c.get("fu") else "") if c.get("fd") else "–"
        rows.append(
            f'<tr data-iso="{c["iso"]}" data-region="{esc(c["region"])}"{" class=home" if c["iso"]==HOME_ISO else ""}>'
            f'<th scope="row">{esc(name(c["iso"], lang))}</th>'
            + num_td(c["fp"], money(c["fp"])) + num_td(c.get("fd"), sp)
            + num_td(c.get("fpct"), pct(c.get("fpct"))) + num_td(c.get("fppm"), money(c.get("fppm"), 3))
            + num_td(c.get("gni"), money(c.get("gni"))) + vs_cell(c.get("fmult"))
            + f'<td class="fl">{esc(" · ".join(fl))}</td></tr>')
    head = "".join(f'<th scope="col" data-sort="{k}">{esc(t[k])}</th>' for k in
                   ("th_country", "th_price", "th_speed", "th_pct", "th_ppm", "th_gni", "th_vs", "th_flags"))
    return (f'<div class="tablewrap"><table class="data sortable"><thead><tr>{head}</tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>')


def mobile_table(lang, isos=None):
    t = T[lang]
    rows = []
    for c in sorted(C.values(), key=lambda c: -(c.get("mpct") or -1)):
        if c.get("mgb") is None or (isos and c["iso"] not in isos):
            continue
        fl = flags(c, "m", lang)
        unl = (t["unl_yes"] if c["uy"] >= 50 else t["unl_thr"] if c["uy"] + c["ut"] >= 50 else t["unl_no"])
        rows.append(
            f'<tr data-iso="{c["iso"]}" data-region="{esc(c["region"])}"{" class=home" if c["iso"]==HOME_ISO else ""}>'
            f'<th scope="row">{esc(name(c["iso"], lang))}</th>'
            + num_td(c["mgb"], money(c["mgb"], 2)) + num_td(c.get("m10"), money(c.get("m10")))
            + num_td(c.get("mpct"), pct(c.get("mpct"))) + f'<td>{esc(unl)}</td>'
            + num_td(c.get("up"), money(c.get("up"))) + num_td(c.get("g5"), f'{c.get("g5")}%')
            + vs_cell(c.get("mmult")) + f'<td class="fl">{esc(" · ".join(fl))}</td></tr>')
    head = "".join(f'<th scope="col">{esc(t[k])}</th>' for k in
                   ("th_country", "th_gb", "th_10", "th_pct", "th_unl", "th_unlp", "th_5g", "th_vs", "th_flags"))
    return (f'<div class="tablewrap"><table class="data sortable"><thead><tr>{head}</tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>')


def domain(u):
    return (urlparse(u).netloc or u).replace("www.", "")


def ops_details(kind, lang, isos=None):
    t = T[lang]
    src = ops_f if kind == "f" else ops_m
    out = []
    for iso in sorted(src, key=lambda i: name(i, lang)):
        if isos and iso not in isos:
            continue
        lis = []
        for o in src[iso]:
            u = (o.get("source_url") or "").strip()
            link = (f'<a href="{esc(u)}" rel="noopener nofollow" dir="ltr">{esc(domain(u))}</a>'
                    if u.startswith("http") else f'<span class="muted">{esc(u or "—")}</span>')
            if kind == "f":
                price = f(o.get("price_usd_month"))
                body = (f'<bdi>{esc(o.get("plan_name") or "")}</bdi> · '
                        f'<bdi dir="ltr">{esc(o.get("speed_down_mbps") or "?")}/{esc(o.get("speed_up_mbps") or "?")}</bdi> {t["mbps"]} · '
                        f'<b><bdi dir="ltr">${money(price) if price else "–"}</bdi></b>')
            else:
                price = f(o.get("ten_gb_price_usd"))
                body = (f'<b><bdi dir="ltr">${money(price) if price else "–"}</bdi></b> / 10 {t["gb"]} · '
                        f'{esc(t["unl_yes"] if o.get("unlimited")=="yes" else t["unl_thr"] if o.get("unlimited")=="throttled" else t["unl_no"])}'
                        + (f'<br><span class="muted">{esc(t["fup"])}: <bdi>{esc(o.get("fup_policy") or "")}</bdi></span>'
                           if o.get("fup_policy") else ""))
            st = o.get("status") or ""
            lis.append(f'<li><span class="op" dir="auto">{esc(o.get("operator") or "")}</span> {body} '
                       f'<span class="src">{esc(t["src"])}: {link}</span>'
                       + (f' <span class="st st-{esc(st)}">{esc(STATUS[lang].get(st, st))}</span>' if st else "") + "</li>")
        out.append(f'<details data-iso="{iso}"><summary>{esc(name(iso, lang))} '
                   f'<span class="muted">({len(src[iso])})</span></summary><ul>{"".join(lis)}</ul></details>')
    return f'<div class="opsgrid">{"".join(out)}</div>'


def region_chips(lang):
    t = T[lang]
    b = [f'<button type="button" class="chip" aria-pressed="true" data-region="">{esc(t["all_regions"])}</button>']
    b += [f'<button type="button" class="chip" aria-pressed="false" data-region="{esc(r)}">{esc(t["regions"][r])}</button>'
          for r in REGIONS]
    return f'<div class="chips" role="group">{"".join(b)}</div>'


def picker(lang):
    t = T[lang]
    opts = sorted(C, key=lambda i: name(i, lang))
    o = "".join(f'<option value="{i}"{" selected" if i == HOME_ISO else ""}>{esc(name(i, lang))}</option>' for i in opts)
    return f'<label class="picker"><span>{esc(t["pick"])}</span><select id="country">{o}</select></label>'


# ---------------------------------------------------------------- pages
def s(lang, ar, en):
    return ar if lang == "ar" else en


def index_page(lang):
    t = T[lang]
    n_f = sum(1 for c in C.values() if c.get("fp") is not None)
    n_m = sum(1 for c in C.values() if c.get("mgb") is not None)
    body = f"""
<section class="hero" aria-live="polite">
{picker(lang)}
<p class="lede" id="lede"></p>
<p class="stamp" id="stamp" hidden><span id="stampnum"></span><span id="stamplab"></span></p>
<p class="lede2" id="lede2"></p>
</section>
<section>
<h2>{esc(t['strip_fiber_h'])}</h2>
<p class="note">{esc(t['strip_fiber_p'])}</p>
<figure class="scroll">{strip_svg('fpct', lang, [0.3, 1, 2, 5, 10, 30, 100], 0.1, 200)}
<figcaption><span class="key over"></span>{esc(s(lang,'فوق 2٪ من الدخل','above 2% of income'))}
<span class="key under"></span>{esc(s(lang,'تحت 2٪','below 2%'))}
<span class="key fairk"></span>{esc(t['fair_line'])}</figcaption></figure>
</section>
<section class="cols">
<a class="door" href="fiber.html"><h2>{esc(t['nav_fiber'])}</h2>
<p>{esc(s(lang, f'{n_f} دولة لها أسعار ألياف موثّقة، بمتوسط أكبر 3 مشغّلين لكل دولة وأقرب باقة إلى 200 ميغابت.',
             f'{n_f} countries with fiber prices, averaging the plan nearest 200 Mbps at each country’s 3 biggest operators.'))}</p></a>
<a class="door" href="mobile.html"><h2>{esc(t['nav_mobile'])}</h2>
<p>{esc(s(lang, f'{n_m} دولة: سعر الغيغابايت، وهل «غير محدود» غير محدود فعلاً، ونص سياسة الاستخدام العادل لكل مشغّل.',
             f'{n_m} countries: price per GB, whether “unlimited” really is, and each operator’s fair-use policy text.'))}</p></a>
<a class="door" href="saudi.html"><h2>{esc(t['nav_sau'])}</h2>
<p>{esc(s(lang, 'STC وموبايلي وزين وسلام مقارنةً بالدول ذات الدخل المشابه.',
             'STC, Mobily, Zain and Salam against countries with similar income.'))}</p></a>
</section>"""
    return page(lang, "index.html", t["title"], body)


def fiber_page(lang):
    t = T[lang]
    body = f"""
<section class="pagehead"><h1>{esc(s(lang,'الألياف: ماذا تكلّف 200 ميغابت تقريباً','Fiber: what about 200 Mbps costs'))}</h1>
<p class="note">{esc(s(lang,
 'لكل دولة نأخذ من أكبر 3 مشغّلين (4 إن وُجد) الباقة المنزلية الأقرب إلى 200 ميغابت ثم نحسب المتوسط. الصفوف التي أُعيد فحصها في نوفمبر 2026 بالسعر المعلن دون عروض مؤقتة؛ الصفوف غير المؤكَّدة تحتفظ بقيمتها السابقة ومُعلَّمة في الجدول. DSL مستبعد.',
 'For each country we take the home plan nearest 200 Mbps at the 3 biggest operators (4 where they exist) and average them. Rows re-checked in November 2026 use the regular price without temporary promos; rows that could not be re-confirmed keep their earlier value and are flagged in the table. DSL is excluded.'))}</p></section>
<section><h2>{esc(t['strip_fiber_h'])}</h2>
<figure class="scroll">{strip_svg('fpct', lang, [0.3, 1, 2, 5, 10, 30, 100], 0.1, 200)}</figure></section>
<section><h2>{esc(t['scatter_h'])}</h2><p class="note">{esc(t['scatter_p'])}</p>
{region_chips(lang)}
<figure class="scroll">{scatter_svg('fp', lang, 2, 400, [3, 10, 30, 100, 300], t['y_fiber'])}</figure></section>
<section><h2>{esc(t['table_h'])}</h2>
<input class="search" type="search" placeholder="{esc(t['search'])}" aria-label="{esc(t['search'])}">
{fiber_table(lang)}</section>
<section><h2>{esc(t['ops_h'])}</h2>{ops_details('f', lang)}</section>"""
    return page(lang, "fiber.html", f"{t['nav_fiber']} · {t['title']}", body)


def mobile_page(lang):
    t = T[lang]
    body = f"""
<section class="pagehead"><h1>{esc(s(lang,'الجوال: سعر الغيغابايت وحقيقة «غير محدود»','Mobile: price per GB and the truth about “unlimited”'))}</h1>
<p class="note">{esc(s(lang,
 'لكل دولة وأكبر 3 مشغّلين فيها: كم يكلّف الحصول على 10 غيغابايت على الأقل لمدة شهر بباقة مسبقة الدفع. الباقة الأكبر من 10 غيغابايت تُحسب بسعرها كاملاً، والأصغر تُضاعَف حتى 10. «غير محدود فعلاً» يعني عدم نشر حد تُخفَّض بعده السرعة.',
 'For each country and its 3 biggest operators: what it costs to get at least 10 GB for a month on prepaid. A bundle bigger than 10 GB counts at its full price; a smaller one is multiplied up to 10 GB. “Truly unlimited” means no published cap after which speed is cut.'))}</p></section>
<section><h2>{esc(t['strip_mobile_h'])}</h2><p class="note">{esc(t['strip_mobile_p'])}</p>
<figure class="scroll">{strip_svg('mpct', lang, [0.1, 0.3, 1, 2, 5, 10, 30, 100], 0.05, 200)}</figure></section>
<section><h2>{esc(s(lang,'سعر الغيغابايت مقابل الدخل','Price per GB against income'))}</h2>
{region_chips(lang)}
<figure class="scroll">{scatter_svg('mgb', lang, 0.01, 20, [0.03, 0.1, 0.3, 1, 3, 10], t['y_gb'])}</figure></section>
<section><h2>{esc(t['table_h'])}</h2>
<input class="search" type="search" placeholder="{esc(t['search'])}" aria-label="{esc(t['search'])}">
{mobile_table(lang)}</section>
<section><h2>{esc(t['ops_h'])}</h2>{ops_details('m', lang)}</section>"""
    return page(lang, "mobile.html", f"{t['nav_mobile']} · {t['title']}", body)


def saudi_page(lang):
    t = T[lang]
    c = C[HOME_ISO]
    pf = {x["iso"] for x in peers(HOME_ISO, "fp")} | {HOME_ISO}
    pm = {x["iso"] for x in peers(HOME_ISO, "mgb")} | {HOME_ISO}
    lo, hi = c.get("fpeer_lo"), c.get("fpeer_hi")
    body = f"""
<section class="pagehead"><h1>{esc(s(lang,'السعودية مقابل الدول ذات الدخل المشابه','Saudi Arabia against similar-income countries'))}</h1>
<p class="note">{esc(s(lang,
 f'النظراء: الدول التي يقع دخل الفرد فيها بين {money(lo)} و{money(hi)} دولار سنوياً (ضمن 1.5 ضعف دخل السعودية {money(c["gni"])} دولار). العمود «مقابل النظراء» يقسم سعر الدولة على وسيط نظرائها.',
 f'Peers: countries with income per person between ${money(lo)} and ${money(hi)} a year (within 1.5× of Saudi Arabia’s ${money(c["gni"])}). “vs peers” divides a country’s price by its peers’ median.'))}</p></section>
<section class="hero compact" aria-live="polite"><input type="hidden" id="country" value="{HOME_ISO}">
<p class="lede" id="lede"></p><p class="stamp" id="stamp" hidden><span id="stampnum"></span><span id="stamplab"></span></p>
<p class="lede2" id="lede2"></p></section>
<section><h2>{esc(s(lang,'الألياف','Fiber'))}</h2>{fiber_table(lang, pf)}</section>
<section><h2>{esc(s(lang,'الجوال','Mobile'))}</h2>{mobile_table(lang, pm)}</section>
<section><h2>{esc(s(lang,'مشغّلو السعودية','Saudi operators'))}</h2>
<h3>{esc(s(lang,'الألياف','Fiber'))}</h3>{ops_details('f', lang, {HOME_ISO})}
<h3>{esc(s(lang,'الجوال','Mobile'))}</h3>{ops_details('m', lang, {HOME_ISO})}</section>"""
    return page(lang, "saudi.html", f"{t['nav_sau']} · {t['title']}", body)


def method_page(lang):
    t = T[lang]
    st_rows = [r.get("status") for r in fops + mops if r.get("status")]
    from collections import Counter
    sc = Counter(st_rows)
    doms = Counter(domain(r["source_url"]) for r in fops + mops
                   if (r.get("source_url") or "").startswith("http")
                   and r.get("status") not in ("unsourced", "not_offered"))
    top = "".join(f'<li><bdi dir="ltr">{esc(d)}</bdi> <span class="muted">{n}</span></li>' for d, n in doms.most_common(30))
    n_est = [name(i, lang) for i, c in C.items() if c["gni_note"] in ("est", "gdp-fallback")]
    n_old = [f'{name(i, lang)} ({c["gni_year"]})' for i, c in C.items() if c["gni_old"] and c["gni_note"] == "wb"]
    audit = ""
    if sc:
        lab = STATUS[lang]
        audit = ("<ul>" + "".join(f'<li>{esc(lab.get(k, k))}: <bdi dir="ltr">{v}</bdi></li>' for k, v in sc.most_common()) + "</ul>")
    files = ["fiber_country.csv", "mobile_country.csv", "fiber_ops.csv", "mobile_ops.csv", "sources.csv", "stats.json"]
    pre = "" if lang == "ar" else "../"
    body = f"""
<section class="pagehead prose"><h1>{esc(t['nav_method'])}</h1>
<h2>{esc(s(lang,'ماذا نقيس','What is measured'))}</h2>
<p>{esc(s(lang,
 'الألياف: لكل دولة، الباقة المنزلية الأقرب إلى 200 ميغابت لدى أكبر 3 مشغّلين (4 إن وُجد رابع كبير)، بالسعر الشهري المعلن. الجوال: كلفة الحصول على 10 غيغابايت على الأقل لمدة شهر بباقة مسبقة الدفع لدى أكبر 3 شبكات (الباقة الأكبر تُحسب بسعرها كاملاً، والأصغر تُضاعَف حتى 10 إن لم يتجاوز ذلك ضعفين)، مع وجود باقة غير محدودة وحدّها المنشور ووجود 5G. سعر الدولة هو المتوسط البسيط لمشغّليها. النظراء: الدول التي يقع دخل الفرد فيها ضمن 1.5 ضعف (تتسع حتى يبلغ عددها 8 على الأقل).',
 'Fiber: for each country, the home plan nearest 200 Mbps at the 3 biggest operators (4 where a fourth major exists), at the published monthly price. Mobile: what it costs to get at least 10 GB for a month on prepaid at the 3 biggest networks (a bigger bundle counts at full price, a smaller one is multiplied up to 10 GB when that needs at most 2×), plus whether an unlimited plan exists, its published cap, and 5G. The country figure is the plain average of its operators. Peers: countries with income per person within 1.5× (widened until there are at least 8).'))}</p>
<h2>{esc(s(lang,'الدخل والعملات','Income and currencies'))}</h2>
<p>{esc(s(lang,
 'الدخل: نصيب الفرد من الدخل القومي (GNI، طريقة أطلس) من البنك الدولي، آخر سنة متاحة لكل دولة. الدخل الشهري = السنوي ÷ 12. الصفوف المُعاد فحصها حُوّلت إلى الدولار بسعر صرف واحد بتاريخ 18 نوفمبر 2026 (data/fx.csv)؛ الصفوف غير المؤكَّدة تبقى بسعر صرف سبتمبر 2026 المذكور في ملاحظاتها. عملات بلا سعر صرف واحد ذي معنى (الريال اليمني، الليرة السورية، الوون الكوري الشمالي، جنيه جنوب السودان، الجنيه السوداني، البيزو الكوبي) لم تُحوَّل.',
 'Income: GNI per capita (Atlas method) from the World Bank, latest year available for each country. Monthly income = yearly ÷ 12. Re-checked rows are converted to dollars with one exchange-rate snapshot of 18 November 2026 (data/fx.csv); rows that could not be re-confirmed keep the September 2026 rate stated in their notes. Currencies with no single meaningful rate (YER, SYP, KPW, SSP, SDG, CUP) are not converted.'))}</p>
<p>{esc(s(lang,'دخل تقديري أو بديل:','Estimated or fallback income:'))} {esc('، '.join(n_est) if lang=='ar' else ', '.join(n_est))}</p>
<p>{esc(s(lang,'دخل من سنة أقدم من 2023:','Income older than 2023:'))} {esc('، '.join(n_old) if lang=='ar' else ', '.join(n_old))}</p>
<h2>{esc(s(lang,'التدقيق','Audit'))}</h2>
<p>{esc(s(lang,'أُعيد فحص كل صف مشغّل مقابل صفحة الأسعار المنشورة. يُقبل السعر الجديد فقط إذا ظهر في نص صفحة جُلبت فعلاً من موقع المصدر نفسه. الصفوف التي لا مصدر لها أو مصدرها ويكيبيديا فقط تبقى في الملفات لكنها لا تدخل في أي متوسط. بعض الأسعار منشورة دون ضريبة القيمة المضافة وذُكر ذلك في ملاحظاتها. حالة الصفوف:','Every operator row was re-checked against the published tariff page. A new price is accepted only if it appears in text actually fetched from the source site itself. Rows with no source, or only Wikipedia, stay in the files but never enter an average. A few prices are published excluding VAT; their notes say so. Row status:'))}</p>
{audit}
<h2>{esc(s(lang,'الملفات','Files'))}</h2>
<ul>{''.join(f'<li><a href="{pre}data/{x}" dir="ltr">{x}</a></li>' for x in files)}</ul>
<h2>{esc(s(lang,'أكثر النطاقات استشهاداً','Most cited domains'))}</h2><ul class="cols3">{top}</ul>
</section>"""
    return page(lang, "method.html", f"{t['nav_method']} · {t['title']}", body)


# ---------------------------------------------------------------- data.js for the picker / tooltips
def data_js():
    keep = ("fp", "fd", "fpct", "fn", "fmult", "fpeer_med", "fpeer_n", "fmult_aud", "fpeer_aud_n", "mmult_aud", "mpeer_aud_n", "mgb", "m10", "mpct", "mmult",
            "mpeer_med", "mpeer_n", "gni", "gni_note", "gni_year", "region", "uy", "ut")
    out = {}
    for iso, c in C.items():
        d = {k: (round(c[k], 4) if isinstance(c[k], float) else c[k]) for k in keep if c.get(k) is not None}
        d["ar"] = name(iso, "ar")
        d["en"] = name(iso, "en")
        out[iso] = d
    return "window.C=" + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";"


os.makedirs(os.path.join(DOCS, "assets"), exist_ok=True)
os.makedirs(os.path.join(DOCS, "en"), exist_ok=True)
with open(os.path.join(DOCS, "assets", "data.js"), "w", encoding="utf-8") as fh:
    fh.write(data_js())
for lang, outdir in (("ar", DOCS), ("en", os.path.join(DOCS, "en"))):
    for fn, fnc in (("index.html", index_page), ("fiber.html", fiber_page), ("mobile.html", mobile_page),
                    ("saudi.html", saudi_page), ("method.html", method_page)):
        with open(os.path.join(outdir, fn), "w", encoding="utf-8") as fh:
            fh.write(fnc(lang))
open(os.path.join(DOCS, ".nojekyll"), "w").close()
print("rendered ar + en:", sum(1 for c in C.values() if c.get("fp")), "fiber,",
      sum(1 for c in C.values() if c.get("mgb")), "mobile countries")
