#!/usr/bin/env python3
"""Merge audited agent evidence (evidence_check.py output files) into data/*_ops.csv.

Rules
- An agent row is ACCEPTED only if it has a local price, an http source that is not
  Wikipedia, and that price appears in text the agent actually fetched (evidence_price).
- Accepted rows are converted to USD with data/fx.csv (one snapshot). Currencies whose
  single rate is not meaningful (split/redenominated/informal) are not converted.
- status is derived here, not taken from the agent:
    verified   accepted and USD within 7 % of the old row with the same speed tier / bundle
    corrected  accepted and different
    new        accepted row for an operator the study did not have
    unverified old values kept, not re-confirmed (still in the average if they had a URL)
    unsourced  old value with no URL or only Wikipedia: kept for reference, NOT averaged
    not_offered operator confirmed to sell no such product (no price)
Usage: merge_audit.py <evidence.json> [<evidence.json> ...]
"""
import csv, json, os, re, sys, unicodedata

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
CHECKED = "2026-11-18"
FX_SKIP = {"YER", "SYP", "KPW", "SSP", "SDG", "CUP"}
TOL = 0.07

fx = {r["currency"]: float(r["per_usd"]) for r in csv.DictReader(open(os.path.join(DATA, "fx.csv")))}


def load(p):
    return list(csv.DictReader(open(p, newline="", encoding="utf-8")))


def num(v):
    try:
        return float(str(v).replace(",", "")) if v not in (None, "") else None
    except ValueError:
        return None


def key(s):
    s = unicodedata.normalize("NFKD", s or "").lower()
    s = re.sub(r"\(.*?\)", " ", s)
    s = re.sub(r"[^a-z0-9& ]+", " ", s)
    stop = {"telecom", "telecommunications", "the", "group", "mobile", "communications", "ltd", "sa", "plc", "company"}
    w = [x for x in s.split() if x not in stop]
    return w[0] if w else s.strip()


def weak(u):
    u = (u or "").strip().lower()
    return (not u.startswith("http")) or "wikipedia.org" in u


def clean_text(s):
    # fix glued words from the first pass ("a2026", "to200 Mbps", "no5G"), leave domains (a1.net) alone
    s = re.sub(r"\b(a|an|to|and|no|with|of|in|from|the|for|or|at|on|than|over|under|about|only|advertise|advertises)(\d)(?![\d]*\.[a-z])",
               r"\1 \2", s or "")
    return s


def usd(price, cur):
    if price is None or not cur:
        return None
    cur = cur.upper()
    if cur == "USD":
        return price
    if cur in FX_SKIP or cur not in fx:
        return None
    return price / fx[cur]


ev = {}
for p in sys.argv[1:]:
    for batch, rows in json.load(open(p)).items():
        for r in rows:
            ev.setdefault((batch.split("_")[0], r["iso3"]), []).append(r)

FCOLS = ["iso3", "country", "operator", "plan_name", "technology", "speed_down_mbps", "speed_up_mbps",
         "price_local", "promo_price_local", "currency", "price_usd_month", "status", "checked",
         "source_url", "notes"]
MCOLS = ["iso3", "country", "operator", "network", "bundle_gb", "validity_days", "price_local", "currency",
         "bundle_price_usd", "ten_gb_price_usd", "unlimited", "unlimited_offer_usd", "unlimited_price_local",
         "fup_policy", "5g", "status", "checked", "source_url", "notes"]


def merge(kind):
    old = load(os.path.join(DATA, f"{kind}_ops.csv"))
    names = {r["iso3"]: r["country"] for r in load(os.path.join(DATA, "countries_195.csv"))}
    out, stats = [], {}
    by_iso = {}
    for r in old:
        by_iso.setdefault(r["iso3"], []).append(r)
    isos = sorted(set(by_iso) | {i for (k, i) in ev if k == kind})
    for iso in isos:
        olds = by_iso.get(iso, [])
        news = ev.get((kind, iso), [])
        used = set()
        for o in olds:
            m = None
            for j, n in enumerate(news):
                if j not in used and key(n["operator"]) == key(o["operator"]):
                    m = j
                    break
            if m is None:
                for j, n in enumerate(news):
                    if j not in used and (key(o["operator"]) in key(n["operator"]) or key(n["operator"]) in (o["operator"] or "").lower()):
                        m = j
                        break
            n = news[m] if m is not None else None
            if m is not None:
                used.add(m)
            out.append(row(kind, o, n, names))
        for j, n in enumerate(news):
            if j in used:
                continue
            r = row(kind, None, n, names)
            if r:
                out.append(r)
    out = [r for r in out if r]
    for r in out:
        stats[r["status"]] = stats.get(r["status"], 0) + 1
    cols = FCOLS if kind == "fiber" else MCOLS
    with open(os.path.join(DATA, f"{kind}_ops.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in sorted(out, key=lambda r: (r["iso3"], r["operator"].lower())):
            w.writerow({c: ("" if r.get(c) is None else r.get(c)) for c in cols})
    return stats


def accepted(n):
    return (n is not None and n.get("price_local") is not None and n.get("evidence_price")
            and not weak(n.get("source_url")) and n.get("status") not in ("not_offered",))


def row(kind, o, n, names):
    if o is None and not accepted(n):
        return None  # never add an unevidenced operator
    base = dict(o) if o else dict(iso3=n["iso3"], country=names.get(n["iso3"], n["iso3"]), operator=n["operator"])
    base["notes"] = clean_text(base.get("notes", ""))
    if kind == "mobile":
        base["fup_policy"] = clean_text(base.get("fup_policy", ""))
        base.setdefault("bundle_gb", "")
    old_usd = num(base.get("price_usd_month" if kind == "fiber" else "ten_gb_price_usd"))
    if accepted(n):
        cur = (n.get("currency") or "").upper()
        p = float(n["price_local"])
        u = usd(p, cur)
        base.update(price_local=p, currency=cur, checked=CHECKED, source_url=n["source_url"].strip())
        extra = f"audit {CHECKED}: {cur} {p:g}"
        if n.get("promo_price_local") is not None:
            extra += f" regular (intro promo {cur} {float(n['promo_price_local']):g})"
        if n.get("vat_included") is not None:
            extra += "; VAT incl." if n["vat_included"] else "; excl. VAT"
        if u is None:
            extra += f"; no single meaningful {cur}/USD rate - USD left blank"
        if n.get("comment"):
            extra += "; " + n["comment"].strip()
        base["notes"] = extra + (" || first pass: " + base["notes"] if base.get("notes") else "")
        if kind == "fiber":
            base.update(plan_name=n.get("plan_name") or base.get("plan_name", ""),
                        technology=n.get("technology") or base.get("technology", ""),
                        promo_price_local=n.get("promo_price_local") if n.get("promo_price_local") is not None else "",
                        price_usd_month=round(u, 2) if u is not None else "")
            if n.get("speed_down_mbps"):
                base["speed_down_mbps"] = n["speed_down_mbps"]
            if n.get("speed_up_mbps"):
                base["speed_up_mbps"] = n["speed_up_mbps"]
            new_usd = u
        else:
            gb = num(n.get("data_gb"))
            base.update(bundle_gb=gb if gb else "", validity_days=n.get("validity_days") or "",
                        bundle_price_usd=round(u, 2) if u is not None else "")
            new_usd = (u / gb * 10) if (u is not None and gb) else None
            base["ten_gb_price_usd"] = round(new_usd, 2) if new_usd is not None else ""
            if n.get("unlimited") in ("yes", "throttled", "no"):
                base["unlimited"] = n["unlimited"]
            if n.get("fiveg") in ("yes", "no"):
                base["5g"] = n["fiveg"]
            if n.get("fup_policy"):
                base["fup_policy"] = n["fup_policy"]
            if n.get("unlimited_price_local") is not None:
                ul = usd(float(n["unlimited_price_local"]), cur)
                base["unlimited_price_local"] = n["unlimited_price_local"]
                base["unlimited_offer_usd"] = round(ul, 2) if ul is not None else ""
        if o is None:
            base["status"] = "new"
        elif old_usd and new_usd and abs(new_usd - old_usd) / old_usd <= TOL:
            base["status"] = "verified"
        else:
            base["status"] = "corrected"
        return base
    # not accepted: keep old values
    base.setdefault("checked", "")
    if n is not None and n.get("status") == "not_offered" and old_usd is None:
        base["status"] = "not_offered"
    elif old_usd is None:
        base["status"] = "unverified"
    elif weak(base.get("source_url")):
        base["status"] = "unsourced"
    else:
        base["status"] = "unverified"
    if n is not None and n.get("comment"):
        base["notes"] = f"audit {CHECKED}: not re-confirmed ({n.get('status')}: {n['comment'].strip()[:300]})" + \
                        (" || " + base["notes"] if base.get("notes") else "")
    return base


for k in ("fiber", "mobile"):
    print(k, merge(k))
