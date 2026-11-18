# Internet bill vs income · فاتورة الإنترنت مقابل الدخل

A 195-country, **operator-level** study of what home fiber and mobile data cost
relative to what people earn. Site (Arabic, with English under `/en/`):
**https://24bit192khz.github.io/internet-scam-study/**

| Page | Question |
|---|---|
| [Fiber](https://24bit192khz.github.io/internet-scam-study/fiber.html) | What does the home fiber plan nearest **200 Mbps** cost, averaged over each country's **3 biggest operators** (4 where a fourth major exists, e.g. Saudi = STC, Mobily, Zain, Salam)? |
| [Mobile](https://24bit192khz.github.io/internet-scam-study/mobile.html) | What does a prepaid bundle near **10 GB / 30 days** cost per GB? Is "unlimited" really unlimited (fair-use caps, throttling, 5G)? |
| [Saudi vs peers](https://24bit192khz.github.io/internet-scam-study/saudi.html) | Saudi Arabia against countries whose income per person is within 1.5× of it. |
| [Method & sources](https://24bit192khz.github.io/internet-scam-study/method.html) | Rules, audit status, data files, most-cited domains. |

## Headline numbers

<!-- stats:start -->
- **161** countries with a fiber price, **164** with a mobile price (503 fiber + 519 mobile operator rows, 958 source URLs).
- Median fiber plan: **$39.99/month**; median **$0.166 per Mbps**.
- Fiber within 2 % of monthly income in **59 of 161** countries.
- Median mobile price: **$1.10 per GB**; 60 % of countries sell some unlimited plan, 29 % one without a published throttle.
- Row status, fiber: unverified 305, corrected 94, verified 69, unsourced 19, not_offered 10, new 6; mobile: unverified 364, corrected 76, unsourced 42, verified 34, new 2, not_offered 1.
- Income: World Bank, latest year up to 2025.
<!-- stats:end -->

## Method

- **Fiber per country** = plain average of the plan nearest 200 Mbps at the 3 biggest
  fixed operators, regular monthly price (temporary intro promos are recorded but not
  used). DSL is excluded. Real down/up speeds are kept per plan.
- **Mobile per country** = average over the 3 biggest MNOs of what it costs to get at
  least 10 GB for a month on prepaid: the cheapest ~30-day bundle near 10 GB; a bundle
  of 10 GB or more counts at its full price, a smaller one is scaled up to 10 GB, and
  validity under 25 days is scaled to 30. Plus whether an unlimited plan exists
  (`yes` = no published throttle, `throttled`, `no`), its price, the published
  fair-use text and 5G.
- **Income**: World Bank GNI per capita (Atlas), latest year per country; GDP per
  capita as fallback, rough estimates only where no series exists (flagged `est`).
  Big Mac prices from The Economist (latest release). Monthly income = GNI / 12.
- **FX**: one snapshot (`data/fx.csv`) for every audited row. Currencies with no single
  meaningful rate (YER, SYP, KPW, SSP, SDG, CUP) are not converted.
- **Peers** ("vs peers" column, the stamp on the home page): countries with income
  within ×1.5 (widened to ×2 / ×3 until there are at least 8); the figure is the
  country's price divided by the peers' median.

### Audit (2026-11)

Every operator row was re-checked against the operator's published tariff page (or a
reputable comparison/regulator page) by parallel research agents. A new price is
accepted only if it appears in text that was actually fetched; status is then derived
by comparing with the earlier value:

| status | meaning |
|---|---|
| `verified` | re-confirmed, within 7 % of the earlier USD value |
| `corrected` | re-confirmed, different plan/price/speed |
| `new` | operator added in the audit |
| `unverified` | earlier value kept, could not be re-confirmed (still averaged; has a URL) |
| `unsourced` | earlier value with no URL or only Wikipedia: kept for reference, **not averaged** |
| `not_offered` | operator sells no such product |

## Data files

- `data/` canonical inputs: `fiber_ops.csv`, `mobile_ops.csv` (every operator row with
  local price, currency, status, source URL, notes), `economics.csv`, `bigmac.csv`,
  `fx.csv`, `countries_195.csv`, `names_ar.csv`
- `docs/data/` published outputs: `fiber_country.csv`, `mobile_country.csv`, the ops
  files, `sources.csv`, `stats.json`

## Reproduce

```bash
python3 tools/fetch_econ.py   # optional: refresh World Bank / Big Mac / FX
python3 build2.py             # data/ -> docs/data/
python3 render_site.py        # docs/data/ -> docs/*.html (ar) + docs/en/*.html
```
