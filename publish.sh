#!/usr/bin/env bash
# Publish the study to GitHub Pages: commit, push, enable Pages, verify.
set -euo pipefail
REPO="internet-scam-study"
OWNER="24bit192kHz"
cd "$(dirname "$0")"

echo "== rebuild =="
python3 recover.py >/dev/null
python3 build2.py | tail -3
python3 render_pages.py | tail -2

echo "== git =="
git add -A
git -c user.name="24bit192kHz" -c user.email="118996408+24bit192kHz@users.noreply.github.com" \
    commit -q -m "Operator-level fiber + mobile study: 195 countries, all sources" || true

if ! gh repo view "$OWNER/$REPO" >/dev/null 2>&1; then
  gh repo create "$REPO" --public --source=. --remote=origin --push \
    --description "195-country operator-level study: fiber (avg of 3 ISPs @ ~200Mbps) & mobile 4G/5G (GB/$, unlimited, FUP) vs GDP, GNI per capita, Big Mac. All sources included."
else
  git push -q origin HEAD 2>/dev/null || true
fi

echo "== enable Pages (branch main, /docs) =="
gh api -X POST "repos/$OWNER/$REPO/pages" \
  -f "source[branch]=main" -f "source[path]=/docs" 2>/dev/null \
  || gh api -X PUT "repos/$OWNER/$REPO/pages" \
       -f "source[branch]=main" -f "source[path]=/docs" 2>/dev/null \
  || echo "(pages already configured)"

echo "== URL =="
gh api "repos/$OWNER/$REPO/pages" --jq '.html_url' 2>/dev/null \
  || echo "https://$OWNER.github.io/$REPO/"
