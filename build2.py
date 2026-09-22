#!/usr/bin/env python3
"""Build the multi-chart static site (docs/) from operator-level fiber + mobile CSVs.
Fiber study: avg of ~3 operators' nearest-200Mbps plans per country (DSL dropped).
Mobile study: 10GB price, $/GB, unlimited flags, FUP policies per operator.
Country economics: World Bank GDP/GNI p.c. + Economist Big Mac."""
import csv, json, os, glob, statistics, re
from urllib.parse import urlparse

BASE = os.path.dirname(os.path.abspath(__file__))
# operator-level CSVs land in the shared research dir (agents write there);
# econ + country meta are copied there too
DATA = "/tmp/opencode/internet-scam-chart/data"
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

# GNI fallback chain (same documented basis as v3 study):
# 1) World Bank GNI p.c.  2) WB GDP p.c.  3) marked estimate for states with no WB data
GNI_EST = {"YEM": 600, "SSD": 400, "ERI": 650, "VAT": 50000, "PRK": 1800}

def gni_with_note(e, iso):
    gni = num(e.get("gni_per_capita_usd"))
    if gni is not None:
        return gni, "wb"
    gdp = num(e.get("gdp_per_capita_usd"))
    if gdp is not None:
        return gdp, "gdp-fallback"
    if iso in GNI_EST:
        return GNI_EST[iso], "est"
    return None, "missing"

# ---- load operator-level files ---------------------------------------
fiber_ops, mobile_ops = [], []
for f in sorted(glob.glob(os.path.join(DATA, "fiber_ops_*.csv"))):
    fiber_ops += [r for r in load(f) if r.get("iso3")]
for f in sorted(glob.glob(os.path.join(DATA, "mobile_ops_*.csv"))):
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

# ---- country-level fiber: AVERAGE OF THE 3 COMPANIES ------------------
fiber_by_iso = {}
for r in fiber_ops:
    fiber_by_iso.setdefault(r["iso3"], []).append(r)

fiber_country = []
for iso, ops in fiber_by_iso.items():
    prices = [num(o["price_usd_month"]) for o in ops if num(o.get("price_usd_month"))]
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
fiber_country.sort(key=lambda r: -(r["avg_price"] or 0))

# ---- country-level mobile --------------------------------------------
mobile_by_iso = {}
for r in mobile_ops:
    mobile_by_iso.setdefault(r["iso3"], []).append(r)

mobile_country = []
for iso, ops in mobile_by_iso.items():
    t10 = [num(o["ten_gb_price_usd"]) for o in ops if num(o.get("ten_gb_price_usd"))]
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
        pop=num(m.get("population_millions")), n_ops=len(ops),
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
mobile_country.sort(key=lambda r: -(r["per_gb"] or 0))

# ---- sources ----------------------------------------------------------
all_sources = []
for kind, rows in (("fiber", fiber_ops), ("mobile", mobile_ops)):
    for r in rows:
        u = (r.get("source_url") or "").strip()
        if u and u != "knowledge":
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

# operator-level dumps (raw, for the repo / full transparency)
with open(os.path.join(DOCS, "data", "fiber_ops.csv"), "w", newline="", encoding="utf-8") as f:
    cols = ["iso3", "country", "operator", "plan_name", "speed_down_mbps",
            "speed_up_mbps", "price_usd_month", "source_url", "notes"]
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader()
    for r in sorted(fiber_ops, key=lambda x: x["iso3"]): w.writerow(r)
with open(os.path.join(DOCS, "data", "mobile_ops.csv"), "w", newline="", encoding="utf-8") as f:
    cols = ["iso3", "country", "operator", "network", "ten_gb_price_usd",
            "unlimited_offer_usd", "unlimited", "fup_policy", "5g",
            "source_url", "notes"]
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader()
    for r in sorted(mobile_ops, key=lambda x: x["iso3"]): w.writerow(r)
with open(os.path.join(DOCS, "data", "sources.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["kind", "iso3", "operator", "url"])
    w.writeheader()
    for s in sorted(all_sources, key=lambda x: (x["kind"], x["iso3"])): w.writerow(s)

def med(vals):
    vals = [v for v in vals if v]
    return round(statistics.median(vals), 4) if vals else None

stats = dict(
    n_fiber_countries=len(fiber_country), n_mobile_countries=len(mobile_country),
    n_fiber_ops=len(fiber_ops), n_mobile_ops=len(mobile_ops),
    n_sources=len(all_sources),
    med_fiber=med_fiber,
    med_ppm=med([r["ppm"] for r in fiber_country]),
    med_per_gb=med([r["per_gb"] for r in mobile_country]),
    pct_unlim_any=round(100 * sum(1 for r in mobile_country
                                  if r["unlim_yes"] + r["unlim_throttled"] > 0)
                        / len(mobile_country)) if mobile_country else 0,
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
