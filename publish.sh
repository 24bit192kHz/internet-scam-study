#!/usr/bin/env bash
# Rebuild the site from data/ and publish to GitHub Pages (branch master, /docs).
# Optional: --refresh-econ re-pulls World Bank / Big Mac / FX first (tools/fetch_econ.py).
set -euo pipefail
cd "$(dirname "$0")"
[[ "${1:-}" == "--refresh-econ" ]] && python3 tools/fetch_econ.py
python3 build2.py | tail -3
python3 render_site.py
git add -A data docs build2.py render_site.py tools README.md publish.sh
if git diff --cached --quiet; then echo "nothing to commit"; else
  git commit -q -m "${MSG:-Rebuild site from data}"; fi
git push origin HEAD:master
gh api "repos/24bit192kHz/internet-scam-study/pages" --jq '.html_url'
