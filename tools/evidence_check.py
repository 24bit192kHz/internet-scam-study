#!/usr/bin/env python3
"""Check each agent-returned row against that agent's own tool results:
a row is 'evidenced' when its local price (as published) appears in text the agent
actually received from WebFetch/WebSearch. Usage: evidence_check.py <workflow_dir> <out.json>"""
import json, re, sys, glob, os

wdir, out = sys.argv[1], sys.argv[2]
label = {}
for m in glob.glob(os.path.join(wdir, "agent-*.meta.json")):
    label[os.path.basename(m)[6:-10]] = json.load(open(m)).get("description")


def base_domain(u):
    from urllib.parse import urlparse
    h = (urlparse(u if "//" in u else "http://" + u).hostname or "").lower()
    parts = [x for x in h.split(".") if x not in ("www",)]
    # keep the registrable part: last 2 labels, or 3 for ccSLDs like com.sa / co.ke
    if len(parts) >= 3 and (parts[-2] in ("com", "co", "net", "org", "gov", "ac", "or", "ne") or len(parts[-2]) <= 3 and len(parts[-1]) == 2):
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def tool_text(path):
    """WebFetch results only (what the agent saw from the web), grouped by base domain.
    The batch file it Read (which holds the old prices) and search snippets do not count."""
    uses, by_dom = {}, {}
    rows = []
    for line in open(path, encoding="utf-8", errors="replace"):
        try:
            rows.append(json.loads(line))
        except Exception:
            pass
    for d in rows:
        msg = d.get("message") or {}
        if msg.get("role") == "assistant":
            for c in msg.get("content") or []:
                if isinstance(c, dict) and c.get("type") == "tool_use":
                    uses[c.get("id")] = (c.get("name"), c.get("input") or {})
    for d in rows:
        msg = d.get("message") or {}
        if msg.get("role") != "user":
            continue
        for c in msg.get("content") or []:
            if isinstance(c, dict) and c.get("type") == "tool_result":
                name, inp = uses.get(c.get("tool_use_id"), (None, {}))
                if name == "WebFetch":
                    url = inp.get("url", "")
                elif name == "Bash" and "render_text.mjs" in (inp.get("command") or ""):
                    # headless render: the URL is the first http argument of the command
                    m = re.search(r"render_text\.mjs\s+[\"']?(https?://[^\s\"']+)", inp.get("command") or "")
                    if not m:
                        continue
                    url = m.group(1)
                else:
                    continue
                v = c.get("content")
                txt = json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
                dom = base_domain(url)
                by_dom[dom] = by_dom.get(dom, "") + "\n" + re.sub(r"\s+", " ", txt)
    return by_dom


def forms(p):
    p = float(p)
    s = {f"{p:g}", f"{p:.2f}", f"{p:,.0f}", f"{p:,.2f}", f"{p:.0f}" if p == int(p) else f"{p:g}"}
    if p == int(p):
        s |= {f"{int(p):,}".replace(",", "."), f"{int(p):,}".replace(",", " ")}
    else:
        s.add(f"{p:.2f}".replace(".", ","))
    return {x for x in s if x}


journal = [json.loads(l) for l in open(os.path.join(wdir, "journal.jsonl"))]
agent_of = {d["key"]: d["agentId"] for d in journal if d.get("type") == "started"}
res = {}
for d in journal:
    if d.get("type") != "result":
        continue
    aid = agent_of.get(d.get("key"))
    r = d.get("result") or {}
    if not aid or not isinstance(r, dict):
        continue
    by_dom = tool_text(os.path.join(wdir, f"agent-{aid}.jsonl"))
    rows = []
    for x in r.get("rows") or []:
        p = x.get("price_local")
        norm = by_dom.get(base_domain(x.get("source_url") or ""), "")
        ev_price = bool(norm) and p is not None and any(
            re.search(r"(?<![\d.,])" + re.escape(f) + r"(?![\d])", norm) for f in forms(p))
        q = re.sub(r"\s+", " ", x.get("quote") or "")[:60]
        ev_quote = bool(q) and bool(norm) and q[:40] in norm
        rows.append(dict(x, evidence_price=ev_price, evidence_quote=ev_quote))
    res[label.get(aid, aid)] = rows
json.dump(res, open(out, "w"), ensure_ascii=False, indent=1)
for b, rows in res.items():
    priced = [x for x in rows if x.get("price_local") is not None]
    print(b, "rows", len(rows), "priced", len(priced), "price-evidenced", sum(x["evidence_price"] for x in priced),
          "quote-found", sum(x["evidence_quote"] for x in rows))
