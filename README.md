# 📊 Internet Scam Study — fiber & mobile prices vs national income

A 195-country, **operator-level** study of how much internet actually costs relative
to what people earn — split into two focused studies:

| Study | Page | Question |
|---|---|---|
| 🌐 **Fiber** | [`/fiber`](docs/fiber.html) | What does the typical **~200 Mbps fiber** plan cost, averaged across each country's **3 major operators** (e.g. Saudi = mean of **STC, Mobily, Zain, Salam**)? How does that compare with GDP, GNI per capita and the Big Mac? |
| 📱 **Mobile 4G/5G** | [`/mobile`](docs/mobile.html) | How much **GB per dollar**? Is "unlimited" really unlimited — **fair-use policy (FUP)**, throttle thresholds, 5G availability? |

**DSL is excluded from this study entirely** (legacy tech, not comparable to fiber).
The earlier all-in basket study (fiber+DSL+voice, 3-source average) lives in the
`v3` branch/history of the original project.

## Methodology

- **195 countries** (all UN members + Palestine + Vatican), Sep-2026 FX.
- **Fiber price per country** = plain average of the nearest-to-200 Mbps consumer
  fiber tier from **3 real operators** (4 where they exist). Real down/up speeds
  recorded per plan; $/Mbps computed from the average.
- **Mobile per country** = average of 3 MNOs' prepaid ~10 GB / 30-day price.
  Per-operator columns: `unlimited` ∈ {yes, throttled, no}, `fup_policy`
  (published threshold text), `5g`, cheapest unlimited offer price.
- **Economics**: World Bank API (GDP & GNI per capita 2024 — GNI = average income
  per person), The Economist Big Mac Index (2026-07-01).
- **Every operator row carries a `source_url`** — see [`docs/data/sources.csv`](docs/data/sources.csv)
  (N source citations, domains listed below). Rows researched from knowledge without
  a live URL are marked `knowledge` and flagged in the audit notes.

## Data files

- `docs/data/fiber_country.csv` — country-level fiber averages + econ join
- `docs/data/mobile_country.csv` — country-level mobile averages, unlimited/FUP shares
- `docs/data/fiber_ops.csv` — **every operator plan** (fiber) with source URL
- `docs/data/mobile_ops.csv` — **every operator plan** (mobile) with FUP policy + source
- `docs/data/sources.csv` — all citations
- `docs/data/stats.json` — headline statistics

## Headline numbers

_Filled by build: see stats.json._

## Reproduce

```bash
python3 build2.py   # regenerates docs/ from data/*.csv
```

Data collection used parallel research agents (one per region), then
plausibility audits (range rules, n_ops consistency, duplicate checks).
