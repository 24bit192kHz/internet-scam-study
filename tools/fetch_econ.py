#!/usr/bin/env python3
"""Refresh data/economics.csv (World Bank API), data/bigmac.csv (The Economist
big-mac-data repo) and data/fx.csv (open.er-api.com, one snapshot for every row).

Per country we take the latest World Bank year that has a value (2025 where
published). GNI basis is recorded in gni_note:
  wb            World Bank GNI per capita, Atlas method (NY.GNP.PCAP.CD)
  gdp-fallback  no WB GNI: World Bank GDP per capita used instead
  est           no WB data at all: documented rough estimate (see EST below)
"""
import csv, json, os, sys, urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
UA = {"User-Agent": "internet-scam-study/1.0"}

# rough GNI-per-capita estimates for states with no World Bank series
# (UN/IMF-order-of-magnitude figures; flagged "est" everywhere they appear)
EST = {"YEM": 600, "SSD": 400, "ERI": 650, "VAT": 50000, "PRK": 1800, "CUB": 9605}


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read()


def wb(indicator):
    url = (f"https://api.worldbank.org/v2/country/all/indicator/{indicator}"
           "?format=json&per_page=20000&date=2018:2026")
    out = {}
    for r in json.loads(get(url))[1]:
        if r["value"] is None:
            continue
        out.setdefault(r["countryiso3code"], {})[int(r["date"])] = r["value"]
    return out


def latest(series, iso):
    s = series.get(iso) or {}
    if not s:
        return None, None
    y = max(s)
    return s[y], y


def main():
    countries = list(csv.DictReader(open(os.path.join(DATA, "countries_195.csv"))))
    gni, gdp, pop = wb("NY.GNP.PCAP.CD"), wb("NY.GDP.PCAP.CD"), wb("SP.POP.TOTL")
    rows = []
    for c in countries:
        iso = c["iso3"]
        g, gy = latest(gni, iso)
        d, dy = latest(gdp, iso)
        p, _ = latest(pop, iso)
        if g is not None:
            note, gval, year = "wb", g, gy
        elif d is not None:
            note, gval, year = "gdp-fallback", d, dy
        elif iso in EST:
            note, gval, year = "est", EST[iso], ""
        else:
            note, gval, year = "missing", "", ""
        rows.append(dict(iso3=iso, country=c["country"],
                         gdp_per_capita_usd=round(d) if d else "", gdp_year=dy or "",
                         gni_per_capita_usd=round(gval) if gval != "" else "",
                         gni_year=year, gni_note=note,
                         population=round(p / 1e6, 3) if p else ""))
    cols = list(rows[0])
    with open(os.path.join(DATA, "economics.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)

    bm = list(csv.DictReader(get("https://raw.githubusercontent.com/TheEconomist/"
                                 "big-mac-data/master/output-data/big-mac-full-index.csv"
                                 ).decode().splitlines()))
    last = max(r["date"] for r in bm)
    with open(os.path.join(DATA, "bigmac.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["iso_a3", "country", "usd_price", "date"])
        for r in bm:
            if r["date"] == last:
                w.writerow([r["iso_a3"], r["name"], round(float(r["dollar_price"]), 2), last])

    fx = json.loads(get("https://open.er-api.com/v6/latest/USD"))
    with open(os.path.join(DATA, "fx.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["currency", "per_usd", "as_of"])
        for k, v in sorted(fx["rates"].items()):
            w.writerow([k, v, fx["time_last_update_utc"]])
    from collections import Counter
    print("econ notes:", Counter(r["gni_note"] for r in rows),
          "years:", Counter(r["gni_year"] for r in rows))
    print("big mac date:", last, "| fx:", fx["time_last_update_utc"], len(fx["rates"]))


if __name__ == "__main__":
    sys.exit(main())
