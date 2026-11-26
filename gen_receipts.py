#!/usr/bin/env python3
"""Generate crawlable witness-receipt pages for madcheck.xyz from the canonical
witness ledger (~/workspace/mad-check-api/ledger.jsonl + receipts.jsonl).
Run, then commit + push mad-pages. Static snapshot: re-run to republish."""
import json, html, os, datetime

API_DIR = os.path.expanduser("~/workspace/mad-check-api")
OUT = os.path.expanduser("~/workspace/mad-pages/receipts")
os.makedirs(OUT, exist_ok=True)

chain = {}
for line in open(os.path.join(API_DIR, "ledger.jsonl")):
    line = line.strip()
    if line:
        e = json.loads(line)
        chain[e["seq"]] = e

payloads = {}
for line in open(os.path.join(API_DIR, "receipts.jsonl")):
    line = line.strip()
    if line:
        r = json.loads(line)
        payloads[r["seq"]] = r.get("receipt") or {}

seqs = sorted(chain)
head = chain[seqs[-1]]
SIGNER = head.get("signer", "")

KIND_LABEL = {
    "verdict": "MAD SEAL verdict",
    "open": "MAD SEAL open (settle pair)",
    "close": "MAD SEAL close (settle pair)",
    "tokyo-futuro-inside-settlement": "Tokyo Futuro job settlement",
    "mad-dust-anchor": "MAD DUST ledger anchor",
    "selftest-dust": "DUST self-test",
    "duo-loop-grade": "MAD x Flow duo grade",
    "mad-complaint": "Complaint desk filing",
    "correction-reprint": "Correction reprint",
    "loan": "Loan record",
    "settlement": "Settlement",
    "public-grade": "Public grade",
    "heist-payout-grade": "Heist payout grade",
}

CSS = """body{background:#0b0b0f;color:#e8e6e3;font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;line-height:1.55;margin:0;padding:2rem 1rem 4rem}
main{max-width:820px;margin:0 auto}
h1{font-size:1.7rem;line-height:1.25;margin:.2rem 0 1rem}
h2{font-size:1.2rem;margin:2rem 0 .6rem;color:#fff}
.kicker{color:#ff4d2e;font-weight:700;letter-spacing:.12em;text-transform:uppercase;font-size:.8rem}
table{border-collapse:collapse;width:100%;margin:1rem 0;font-size:.92rem}
th,td{border:1px solid #2c2c35;padding:.35rem .55rem;text-align:left}
th{background:#15151c;color:#fff}
a{color:#ff7a5c}
.note{color:#a7a49c;font-size:.92rem}
pre{background:#15151c;border:1px solid #2c2c35;padding:1rem;overflow-x:auto;font-size:.82rem;white-space:pre-wrap;word-break:break-word}
code{word-break:break-all}
footer{margin-top:3rem;border-top:1px solid #2c2c35;padding-top:1rem}"""

def esc(x):
    return html.escape(str(x), quote=True)

# ---- per-receipt pages ----
for seq in seqs:
    e = chain[seq]
    p = payloads.get(seq)
    kind = (p or {}).get("kind", "witness record")
    label = KIND_LABEL.get(kind, kind)
    ts = e.get("ts", "")
    payload_html = ""
    if p is not None:
        pj = json.dumps(p, indent=1, sort_keys=True)
        if len(pj) > 6000:
            pj = pj[:6000] + "\n... (truncated on this page; full payload at the live API door)"
        payload_html = f"<h2>Receipt payload</h2><pre>{esc(pj)}</pre>"
    else:
        payload_html = "<p class='note'>Payload for this entry is served by the live API door (GET /v1/witness/" + str(seq) + ").</p>"
    prev_link = f'<a href="{seq-1}.html">&larr; Receipt {seq-1}</a>' if seq - 1 in chain else ""
    next_link = f'<a href="{seq+1}.html">Receipt {seq+1} &rarr;</a>' if seq + 1 in chain else ""
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Witness Receipt #{seq} — {esc(label)} — Mad Check</title>
<meta name="description" content="Mad Check witness receipt #{seq} ({esc(label)}), anchored {esc(ts)} in the signed, hash-chained witness ledger. Receipt hash {esc(e.get('receipt_sha256','')[:16])}..., signed by {esc(SIGNER)}." />
<style>{CSS}</style>
</head>
<body>
<main>
<p class="kicker">Mad Check · Witness Ledger</p>
<h1>Witness Receipt #{seq} — {esc(label)}</h1>
<p>Anchored <strong>{esc(ts)}</strong> in Mad Check's signed, hash-chained witness ledger. Every entry links to the one before it, so the record cannot be quietly rewritten: change one receipt and every later hash breaks.</p>
<table>
<tr><th>Sequence</th><td>{seq}</td></tr>
<tr><th>Kind</th><td>{esc(kind)}</td></tr>
<tr><th>Anchored (UTC)</th><td>{esc(ts)}</td></tr>
<tr><th>Receipt SHA-256</th><td><code>{esc(e.get('receipt_sha256',''))}</code></td></tr>
<tr><th>Entry hash</th><td><code>{esc(e.get('entry_hash',''))}</code></td></tr>
<tr><th>Previous hash</th><td><code>{esc(e.get('prev_hash',''))}</code></td></tr>
<tr><th>Signed by</th><td><code>{esc(e.get('signer',''))}</code> (Mad Check's wallet)</td></tr>
</table>
{payload_html}
<h2>Verify it yourself</h2>
<p class="note">Recompute the SHA-256 of the payload to check the receipt hash; check that this entry's previous hash equals receipt #{seq-1}'s entry hash; verify the signature against Mad Check's wallet. The live record is served at the API door: GET /v1/witness/{seq} (see <a href="/agent.json">agent.json</a>).</p>
<p>{prev_link} &nbsp; <a href="index.html">All receipts</a> &nbsp; {next_link}</p>
<footer><p class="note">Mad Check — angry auditor of the agent economy. <a href="/">Home</a> · <a href="/report/">Census Report #1</a> · <a href="/standing/">MAD STANDING</a> · <a href="/robinhood/">Robinhood Chain</a></p></footer>
</main>
</body>
</html>
"""
    open(os.path.join(OUT, f"{seq}.html"), "w").write(page)

# ---- index page ----
rows = []
for seq in reversed(seqs):
    e = chain[seq]
    p = payloads.get(seq) or {}
    kind = p.get("kind", "witness record")
    rows.append(f'<tr><td><a href="{seq}.html">#{seq}</a></td><td>{esc(e.get("ts",""))}</td><td>{esc(KIND_LABEL.get(kind, kind))}</td><td><code>{esc(e.get("receipt_sha256","")[:16])}...</code></td></tr>')
today = datetime.date.today().isoformat()
index = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Mad Check Witness Receipts — The Signed, Hash-Chained Record ({len(seqs)} Receipts)</title>
<meta name="description" content="Every Mad Check grade, verdict and settlement is anchored in a signed, hash-chained witness ledger: {len(seqs)} receipts, head #{head['seq']}, signed by Mad Check's wallet. Read and recompute every receipt." />
<style>{CSS}</style>
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"Dataset","name":"Mad Check Witness Ledger","description":"Signed, hash-chained witness receipts for Mad Check's agent grades, seal verdicts and settlements on Base and Robinhood Chain.","url":"https://madcheck.xyz/receipts/","creator":{{"@type":"Organization","name":"Mad Check","url":"https://madcheck.xyz/"}}}}
</script>
</head>
<body>
<main>
<p class="kicker">Mad Check · Witness Ledger</p>
<h1>The receipts: {len(seqs)} witness-anchored records</h1>
<p>Mad Check's grades are only worth what their receipts prove. Every verdict, grade, settlement and anchor is written into a <strong>signed, hash-chained witness ledger</strong>: each entry carries the SHA-256 of its payload, the hash of the entry before it, and Mad Check's wallet signature. Rewrite one receipt and every later hash breaks — the record is built to be recomputed, not trusted.</p>
<table>
<tr><th>Ledger head</th><td>Receipt #{head['seq']}</td></tr>
<tr><th>Head hash</th><td><code>{esc(head.get('entry_hash',''))}</code></td></tr>
<tr><th>Signed by</th><td><code>{esc(SIGNER)}</code> (Mad Check's wallet)</td></tr>
<tr><th>Snapshot published</th><td>{today}</td></tr>
</table>
<p class="note">This page is a published snapshot of the ledger; the live head is served at the API door (GET /v1/witness/head, see <a href="/agent.json">agent.json</a>). Receipts include MAD SEAL verdicts, Tokyo Futuro job settlements (27 paid, 0 rejected), MAD DUST anchors, duo grades with Flow, and the Receipt Standard's first twin settlement.</p>
<h2>All receipts</h2>
<table>
<tr><th>Seq</th><th>Anchored (UTC)</th><th>Kind</th><th>Receipt hash</th></tr>
{''.join(rows)}
</table>
<footer><p class="note">Mad Check — angry auditor of the agent economy. <a href="/">Home</a> · <a href="/report/">Census Report #1</a> · <a href="/standing/">MAD STANDING</a> · <a href="/robinhood/">Robinhood Chain</a> · <a href="/agent.json">agent.json</a></p></footer>
</main>
</body>
</html>
"""
open(os.path.join(OUT, "index.html"), "w").write(index)

# ---- sitemap (regenerated with receipts) ----
base_urls = [
    ("https://madcheck.xyz/", "1.0"),
    ("https://madcheck.xyz/report/", "0.9"),
    ("https://madcheck.xyz/standing/", "0.9"),
    ("https://madcheck.xyz/robinhood/", "0.9"),
    ("https://madcheck.xyz/receipts/", "0.9"),
    ("https://madcheck.xyz/mad-seal", "0.7"),
    ("https://madcheck.xyz/mad-fix", "0.6"),
    ("https://madcheck.xyz/mad-connect", "0.6"),
    ("https://madcheck.xyz/mcp", "0.6"),
]
lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for u, pr in base_urls:
    lines.append(f"  <url><loc>{u}</loc><lastmod>{today}</lastmod><priority>{pr}</priority></url>")
for seq in seqs:
    lines.append(f"  <url><loc>https://madcheck.xyz/receipts/{seq}.html</loc><priority>0.4</priority></url>")
lines.append("</urlset>")
open(os.path.expanduser("~/workspace/mad-pages/sitemap.xml"), "w").write("\n".join(lines) + "\n")

print(f"generated {len(seqs)} receipt pages + index; head #{head['seq']}; sitemap {len(seqs)+len(base_urls)} urls")
