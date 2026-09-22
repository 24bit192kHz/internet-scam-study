#!/usr/bin/env python3
"""Recover the wiped base dataset from the deployed v3 page (surge.sh embeds the
full 195-row master JSON), then rebuild countries/economics/bigmac CSVs."""
import csv, json, re, os, subprocess

DEST = "/tmp/opencode/internet-scam-chart/data"
STUDY = "/tmp/opencode/internet-scam-study/data"
os.makedirs(DEST, exist_ok=True)
os.makedirs(STUDY, exist_ok=True)

URL = "https://scam-index-195-8751.surge.sh"
html = subprocess.run(["curl", "-s", "-m", "30", URL], capture_output=True,
                      text=True).stdout
m = re.search(r"DATA = (\[.*?\]);", html, re.S)
assert m, "no embedded data found"
rows = json.loads(m.group(1))
assert len(rows) == 195, f"got {len(rows)} rows"

SUB = {}
def sub(region_map):
    for k, v in region_map.items():
        for iso in v.split():
            SUB[iso] = v and k  # noqa

submap = {
"Africa": {"Western Africa":"BEN BFA CPV CIV GMB GHA GIN GNB LBR MRT MLI NER NGA SEN SLE TGO",
"Middle Africa":"AGO CMR CAF TCD COG COD GNQ GAB STP",
"Eastern Africa":"BDI COM DJI ERI ETH KEN MDG MWI MUS MOZ RWA SOM SSD SYC TZA UGA ZMB ZWE",
"Northern Africa":"DZA EGY LBY MAR SDN TUN",
"Southern Africa":"BWA LSO NAM SWZ ZAF"},
"Asia": {"Eastern Asia":"CHN JPN KOR PRK MNG",
"Central Asia":"KAZ KGZ TJK TKM UZB",
"Southern Asia":"AFG BGD BTN IND IRN LKA MDV NPL PAK",
"Southeastern Asia":"BRN KHM IDN LAO MYS MMR PHL SGP THA TLS VNM",
"Western Asia":"ARM AZE BHR CYP GEO IRQ ISR JOR KWT LBN OMN PSE QAT SAU SYR TUR ARE YEM"},
"Europe": {"Eastern Europe":"BLR BGR CZE HUN MDA POL ROU RUS SVK UKR",
"Northern Europe":"DNK EST FIN ISL IRL LVA LTU NOR SWE GBR",
"Western Europe":"AUT BEL DEU FRA LIE LUX MCO NLD CHE",
"Southern Europe":"ALB AND BIH HRV GRC ITA MLT MNE PRT SMR SRB SVN ESP MKD VAT"},
"North America": {"Northern America":"CAN USA",
"Central America":"BLZ CRI GTM HND MEX NIC PAN SLV",
"Caribbean":"ATG BHS BRB CUB DMA DOM GRD HTI JAM KNA LCA VCT TTO"},
"South America": {"South America":"ARG BOL BRA CHL COL ECU GUY PRY PER SUR URY VEN"},
"Oceania": {"Australia/NZ":"AUS NZL","Melanesia":"FJI PNG SLB VUT",
"Micronesia":"FSM KIR MHL PLW NRU","Polynesia":"WSM TON TUV"},
}
for region, groups in submap.items():
    for sr, isos in groups.items():
        for iso in isos.split():
            SUB[iso] = sr

def w(path, cols, rows_):
    with open(path, "w", newline="", encoding="utf-8") as f:
        c = csv.writer(f); c.writerow(cols); c.writerows(rows_)

missing_sub = [r["iso3"] for r in rows if r["iso3"] not in SUB]
c_rows, e_rows, b_rows, m_rows = [], [], [], []
for r in rows:
    iso = r["iso3"]
    pop = r.get("pop")
    pop_m = round(pop / 1e6, 3) if pop and pop > 10000 else pop
    c_rows.append([iso, r["country"], r["region"], SUB.get(iso, ""), pop_m if pop_m else ""])
    e_rows.append([iso, r["country"], r.get("gdp") or "", r.get("gni") or "",
                   pop or "", 2024])
    if r.get("bigmac"):
        b_rows.append([iso, r["country"], r["bigmac"], "2026-07-01"])
    m_rows.append([iso, r["country"], r["region"], SUB.get(iso, ""),
                   r.get("fiber") or "", r.get("dsl") or "", r.get("mobile") or "",
                   r.get("voice_unlim") or "", r.get("voice_100min") or "",
                   r.get("speed_down") or "", r.get("speed_up") or "",
                   r.get("gni") or "", r.get("gdp") or "", r.get("gni_note") or "",
                   pop_m if pop_m else "", r.get("basket") or "",
                   r.get("scam_index") or "", r.get("scam_usd") or "",
                   r.get("bigmac_index") or "", r.get("n_avg") or ""])

cols_c = ["iso3", "country", "region", "subregion", "population_millions"]
cols_e = ["iso3", "country", "gdp_per_capita_usd", "gni_per_capita_usd",
          "population", "year"]
cols_b = ["iso_a3", "country", "usd_price", "date"]
cols_m = ["iso3", "country", "region", "subregion", "fiber", "dsl", "mobile",
          "voice_unlim", "voice_100min", "speed_down", "speed_up", "gni", "gdp",
          "gni_note", "population_millions", "basket", "scam_index", "scam_usd",
          "bigmac_index", "n_avg"]
for dest in (DEST, STUDY):
    w(os.path.join(dest, "countries_195.csv"), cols_c, c_rows)
    w(os.path.join(dest, "economics.csv"), cols_e, e_rows)
    w(os.path.join(dest, "bigmac.csv"), cols_b, b_rows)
w(os.path.join(DEST, "master_recovered.csv"), cols_m, m_rows)

print(f"recovered {len(rows)} rows from {URL}")
print("countries/econ written to:", DEST, "and", STUDY)
print("big mac rows:", len(b_rows), "| subregion missing:", missing_sub)
