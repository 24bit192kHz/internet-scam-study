#!/usr/bin/env python3
"""Check each agent-returned row against that agent's own tool results:
a row is 'evidenced' when its local price (as published) appears in text the agent
actually received from WebFetch/WebSearch. Usage: evidence_check.py <workflow_dir> <out.json>"""
import json, re, sys, glob, os

wdir, out = sys.argv[1], sys.argv[2]
label = {}
for m in glob.glob(os.path.join(wdir, "agent-*.meta.json")):
    label[os.path.basename(m)[6:-10]] = json.load(open(m)).get("description")


def tool_text(path):
    """concatenate tool_result contents (what the agent saw), not its own messages"""
    buf = []
    for line in open(path, encoding="utf-8", errors="replace"):
        try:
            d = json.loads(line)
        except Exception:
            continue
        msg = d.get("message") or {}
        if msg.get("role") != "user":
            continue
        for c in msg.get("content") or []:
            if isinstance(c, dict) and c.get("type") == "tool_result":
                v = c.get("content")
                buf.append(json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v)
    return "\n".join(buf)


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
    txt = tool_text(os.path.join(wdir, f"agent-{aid}.jsonl"))
    norm = re.sub(r"\s+", " ", txt)
    rows = []
    for x in r.get("rows") or []:
        p = x.get("price_local")
        ev_price = p is not None and any(re.search(r"(?<![\d.,])" + re.escape(f) + r"(?![\d])", norm) for f in forms(p))
        q = re.sub(r"\s+", " ", x.get("quote") or "")[:60]
        ev_quote = bool(q) and q[:40] in norm
        rows.append(dict(x, evidence_price=ev_price, evidence_quote=ev_quote))
    res[label.get(aid, aid)] = rows
json.dump(res, open(out, "w"), ensure_ascii=False, indent=1)
for b, rows in res.items():
    priced = [x for x in rows if x.get("price_local") is not None]
    print(b, "rows", len(rows), "priced", len(priced), "price-evidenced", sum(x["evidence_price"] for x in priced),
          "quote-found", sum(x["evidence_quote"] for x in rows))
