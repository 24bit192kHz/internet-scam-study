#!/usr/bin/env python3
"""Build the multi-chart static site (docs/) from operator-level fiber + mobile CSVs.
Fiber study: avg of ~3 operators' nearest-200Mbps plans per country (DSL dropped).
Mobile study: 10GB price, $/GB, unlimited flags, FUP policies per operator.
Country economics: World Bank GDP/GNI p.c. + Economist Big Mac."""
import csv, json, os, glob, statistics, re
from urllib.parse import urlparse

BASE = os.path.dirname(os.path.abspath(__file__))
# canonical inputs live in the repo: data/{countries_195,economics,bigmac,
# fiber_ops,mobile_ops}.csv
DATA = os.path.join(BASE, "data")
DOCS = os.path.join(BASE, "docs")
os.makedirs(os.path.join(DOCS, "data"), exist_ok=True)

def load(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def num(v):
    try:
        return float(str(v).replace(",", "")) if v not in (None, "") else None
    except ValueError:
        return None

countries = load(os.path.join(DATA, "countries_195.csv"))
econ = {r["iso3"]: r for r in load(os.path.join(DATA, "economics.csv"))}
bigmac = {r["iso_a3"]: r for r in load(os.path.join(DATA, "bigmac.csv"))
          if r["iso_a3"] != "EUZ"}
meta = {r["iso3"]: r for r in countries}

# GNI basis comes from data/economics.csv (tools/fetch_econ.py): latest World
# Bank year per country, gni_note = wb | gdp-fallback | est
def gni_with_note(e, iso):
    return num(e.get("gni_per_capita_usd")), (e.get("gni_note") or "missing")

# ---- load operator-level files ---------------------------------------
fiber_ops, mobile_ops = [], []
for f in sorted(glob.glob(os.path.join(DATA, "fiber_ops*.csv"))):
    fiber_ops += [r for r in load(f) if r.get("iso3")]
for f in sorted(glob.glob(os.path.join(DATA, "mobile_ops*.csv"))):
    mobile_ops += [r for r in load(f) if r.get("iso3")]

# dedupe (iso3, operator) keeping first
def dedupe(rows, keyfields):
    seen, out = set(), []
    for r in rows:
        k = tuple((r.get(x) or "").strip().lower() for x in keyfields)
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    return out
fiber_ops = dedupe(fiber_ops, ("iso3", "operator"))
mobile_ops = dedupe(mobile_ops, ("iso3", "operator"))

# rows with no URL (or only Wikipedia) are kept in the ops CSVs for reference but
# never enter a country average: a price needs a citable source
CONFIRMED = ("verified", "corrected", "new")


def counts(r):
    # only prices confirmed against a fetched operator/source page count
    return (r.get("status") or "") in CONFIRMED

# ---- country-level fiber: AVERAGE OF THE 3 COMPANIES ------------------
fiber_by_iso = {}
for r in fiber_ops:
    fiber_by_iso.setdefault(r["iso3"], []).append(r)

fiber_country = []
for iso, ops in fiber_by_iso.items():
    ops = [o for o in ops if counts(o) and num(o.get("price_usd_month"))]
    prices = [num(o["price_usd_month"]) for o in ops]
    downs = [num(o["speed_down_mbps"]) for o in ops if num(o.get("speed_down_mbps"))]
    ups = [num(o["speed_up_mbps"]) for o in ops if num(o.get("speed_up_mbps"))]
    if not prices:
        continue
    m = meta.get(iso, {})
    e = econ.get(iso, {})
    bm = num((bigmac.get(iso) or {}).get("usd_price"))
    gni, gni_note = gni_with_note(e, iso)
    gdp = num(e.get("gdp_per_capita_usd"))
    avg_price = statistics.mean(prices)
    avg_down = statistics.mean(downs) if downs else None
    avg_up = statistics.mean(ups) if ups else None
    fiber_country.append(dict(
        iso3=iso, country=m.get("country", iso), region=m.get("region", ""),
        pop=num(m.get("population_millions")), n_ops=len(ops),
        operators=" | ".join(o["operator"] for o in ops),
        avg_price=round(avg_price, 2),
        avg_down=round(avg_down, 0) if avg_down else None,
        avg_up=round(avg_up, 0) if avg_up else None,
        ppm=round(avg_price / avg_down, 4) if avg_down else None,
        gni=gni, gni_note=gni_note, gdp=gdp, bigmac=bm,
        monthly_inc=round(gni / 12, 2) if gni else None,
        pct_income=round(100 * avg_price / (gni / 12), 2) if gni else None,
        price_bigmacs=round(avg_price / bm, 2) if bm else None,
        vs_median=None,  # filled below
    ))
med_fiber = (statistics.median([r["avg_price"] for r in fiber_country])
             if fiber_country else None)
for r in fiber_country:
    r["vs_median"] = round(r["avg_price"] / med_fiber, 2) if med_fiber else None
fiber_country.sort(key=lambda r: (-(r["avg_price"] or 0), r["iso3"]))

# ---- country-level mobile --------------------------------------------
mobile_by_iso = {}
for r in mobile_ops:
    mobile_by_iso.setdefault(r["iso3"], []).append(r)

mobile_country = []
for iso, ops in mobile_by_iso.items():
    t10 = [num(o["ten_gb_price_usd"]) for o in ops if counts(o) and num(o.get("ten_gb_price_usd"))]
    unm = [(o.get("unlimited") or "").strip().lower() for o in ops]
    yes = sum(1 for u in unm if u == "yes")
    thr = sum(1 for u in unm if u == "throttled")
    no = sum(1 for u in unm if u == "no")
    fiveg = sum(1 for o in ops if (o.get("5g") or "").strip().lower() == "yes")
    ups = [num(o["unlimited_offer_usd"]) for o in ops
           if num(o.get("unlimited_offer_usd"))]
    m = meta.get(iso, {})
    e = econ.get(iso, {})
    bm = num((bigmac.get(iso) or {}).get("usd_price"))
    gni, gni_note = gni_with_note(e, iso)
    gdp = num(e.get("gdp_per_capita_usd"))
    avg10 = statistics.mean(t10) if t10 else None
    n = len(ops) or 1
    mobile_country.append(dict(
        iso3=iso, country=m.get("country", iso), region=m.get("region", ""),
        pop=num(m.get("population_millions")),
        n_ops=sum(1 for o in ops if counts(o) and num(o.get("ten_gb_price_usd"))),
        operators=" | ".join(o["operator"] for o in ops),
        avg_10gb=round(avg10, 2) if avg10 else None,
        per_gb=round(avg10 / 10, 3) if avg10 else None,
        pct_income=round(100 * avg10 / (gni / 12), 2) if (avg10 and gni) else None,
        unlim_yes=round(100 * yes / n), unlim_throttled=round(100 * thr / n),
        unlim_no=round(100 * no / n),
        avg_unlimited_price=round(statistics.mean(ups), 2) if ups else None,
        fiveg_share=round(100 * fiveg / n),
        fup_summary=" ;; ".join(sorted({(o.get("fup_policy") or "?") for o in ops})),
        gni=gni, gni_note=gni_note, gdp=gdp, bigmac=bm,
        price_bigmacs=round(avg10 / bm, 3) if (avg10 and bm) else None,
    ))
mobile_country.sort(key=lambda r: (-(r["per_gb"] or 0), r["iso3"]))

# ---- sources ----------------------------------------------------------
all_sources = []
for kind, rows in (("fiber", fiber_ops), ("mobile", mobile_ops)):
    for r in rows:
        u = (r.get("source_url") or "").strip()
        if u.startswith("http") and counts(r):
            all_sources.append(dict(kind=kind, iso3=r["iso3"],
                                    operator=r.get("operator", ""), url=u))
src_domains = {}
for s in all_sources:
    d = urlparse(s["url"]).netloc or s["url"]
    src_domains[d] = src_domains.get(d, 0) + 1

def write_csv(name, rows, cols):
    path = os.path.join(DOCS, "data", name)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return name

def clean(rows, keys):
    out = []
    for r in rows:
        out.append({k: ("" if r.get(k) is None else r.get(k)) for k in keys})
    return out

fiber_cols = ["iso3", "country", "region", "n_ops", "operators", "avg_price",
              "avg_down", "avg_up", "ppm", "gni", "gni_note", "gdp", "bigmac", "monthly_inc",
              "pct_income", "price_bigmacs", "vs_median", "pop"]
mobile_cols = ["iso3", "country", "region", "n_ops", "operators", "avg_10gb",
               "per_gb", "pct_income", "unlim_yes", "unlim_throttled", "unlim_no",
               "avg_unlimited_price", "fiveg_share", "fup_summary",
               "gni", "gni_note", "gdp", "bigmac", "price_bigmacs", "pop"]
write_csv("fiber_country.csv", clean(fiber_country, fiber_cols), fiber_cols)
write_csv("mobile_country.csv", clean(mobile_country, mobile_cols), mobile_cols)

# operator-level dumps (raw, for the repo / full transparency): every canonical column
for name, rows in (("fiber_ops.csv", fiber_ops), ("mobile_ops.csv", mobile_ops)):
    cols = list(rows[0].keys())
    rows = [r for r in rows if counts(r)]  # publish confirmed rows only
    with open(os.path.join(DOCS, "data", name), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader()
        for r in sorted(rows, key=lambda x: (x["iso3"], x["operator"].lower())): w.writerow(r)
with open(os.path.join(DOCS, "data", "sources.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["kind", "iso3", "operator", "url"])
    w.writeheader()
    for s in sorted(all_sources, key=lambda x: (x["kind"], x["iso3"])): w.writerow(s)

def med(vals):
    vals = [v for v in vals if v]
    return round(statistics.median(vals), 4) if vals else None

stats = dict(
    n_fiber_countries=len(fiber_country),
    n_mobile_countries=sum(1 for r in mobile_country if r["avg_10gb"]),
    n_fiber_ops=len(fiber_ops), n_mobile_ops=len(mobile_ops),
    n_sources=len(all_sources),
    status_fiber={k: sum(1 for r in fiber_ops if (r.get("status") or "first-pass") == k)
                  for k in sorted({r.get("status") or "first-pass" for r in fiber_ops})},
    status_mobile={k: sum(1 for r in mobile_ops if (r.get("status") or "first-pass") == k)
                   for k in sorted({r.get("status") or "first-pass" for r in mobile_ops})},
    med_fiber=med_fiber,
    med_ppm=med([r["ppm"] for r in fiber_country]),
    med_per_gb=med([r["per_gb"] for r in mobile_country]),
    pct_unlim_any=round(100 * sum(1 for r in mobile_country
                                  if r["unlim_yes"] + r["unlim_throttled"] > 0)
                        / len(mobile_country)) if mobile_country else 0,
    econ_year=max(int(e["gni_year"]) for e in econ.values() if e.get("gni_year")),
    pct_truly_unlim=round(100 * sum(1 for r in mobile_country
                                    if r["unlim_yes"] >= 50) / len(mobile_country))
                      if mobile_country else 0,
)
with open(os.path.join(DOCS, "data", "stats.json"), "w") as f:
    json.dump(dict(stats, src_domains=src_domains), f, indent=2)

print(json.dumps(stats, indent=2))
print("top src domains:", sorted(src_domains.items(), key=lambda x: -x[1])[:8])
print("fiber ops without source URL:",
      sum(1 for r in fiber_ops if (r.get("source_url") or "knowledge") == "knowledge"))
print("mobile ops without source URL:",
      sum(1 for r in mobile_ops if (r.get("source_url") or "knowledge") == "knowledge"))

# ---- README headline block ---------------------------------------------
def _readme():
    p = os.path.join(BASE, "README.md")
    if not os.path.exists(p):
        return
    s = open(p, encoding="utf-8").read()
    a, b = "<!-- stats:start -->", "<!-- stats:end -->"
    if a not in s or b not in s:
        return
    sf, sm = stats["status_fiber"], stats["status_mobile"]
    def st(d):
        return ", ".join(f"{k} {v}" for k, v in sorted(d.items(), key=lambda x: -x[1]))
    fair = sum(1 for r in fiber_country if r["pct_income"] is not None and r["pct_income"] <= 2)
    block = (f"\n- **{stats['n_fiber_countries']}** countries with a fiber price, "
             f"**{stats['n_mobile_countries']}** with a mobile price "
             f"({stats['n_fiber_ops']} fiber + {stats['n_mobile_ops']} mobile operator rows, "
             f"{stats['n_sources']} source URLs).\n"
             f"- Median fiber plan: **${stats['med_fiber']:.2f}/month**; median **${stats['med_ppm']:.3f} per Mbps**.\n"
             f"- Fiber within 2 % of monthly income in **{fair} of {len(fiber_country)}** countries.\n"
             f"- Median mobile price: **${stats['med_per_gb']:.2f} per GB**; "
             f"{stats['pct_unlim_any']} % of countries sell some unlimited plan, "
             f"{stats['pct_truly_unlim']} % one without a published throttle.\n"
             f"- Row status, fiber: {st(sf)}; mobile: {st(sm)}.\n"
             f"- Income: World Bank, latest year up to {stats['econ_year']}.\n")
    s = s[:s.index(a) + len(a)] + block + s[s.index(b):]
    open(p, "w", encoding="utf-8").write(s)
_readme()
