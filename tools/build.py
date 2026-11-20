#!/usr/bin/env python3
"""Builds the Fairbill website into public/ from src/ and data/.

You normally don't run this yourself: GitHub runs it automatically every time
you change a file in the repository (see .github/workflows/deploy.yml).
To run it on your computer: python tools/build.py
"""
import csv, json, html, re, shutil, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC, DATA, OUT = ROOT / "src", ROOT / "data", ROOT / "public"

cfg = json.loads((DATA / "config.json").read_text(encoding="utf-8"))
SITE = cfg["site_url"].rstrip("/")
CHECKED = cfg["prices_checked"]
TODAY = datetime.date.today().isoformat()
YEAR = re.search(r"\d{4}", CHECKED).group(0) if re.search(r"\d{4}", CHECKED) else str(datetime.date.today().year)

def num(x):
    x = float(x)
    return int(x) if x == int(x) else round(x, 2)

plans = []
with open(DATA / "precios.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        plans.append([r["provider"].strip(), int(r["speed_mbps"]), r["plan_name"].strip(),
                      num(r["advertised_usd"]), num(r["after_promo_usd"] or 0)])
provs = {}
with open(DATA / "proveedores.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        provs[r["provider"].strip()] = {"rise": float(r["rise_after_promo"]), "type": r["type"], "note": r["note"]}

order = list(dict.fromkeys(p[0] for p in plans))
for p in order:
    provs.setdefault(p, {"rise": 1.3, "type": "Internet", "note": ""})

esc = html.escape
slug = lambda s: re.sub(r"[^a-z0-9]+", "-", s.lower().replace("&", "")).strip("-")
speed = lambda sp: f"{sp/1000:g} Gig" if sp >= 1000 else f"{sp} Mbps"
usd = lambda v: f"${round(v):,}"
def pname(p):
    return p[2] if re.search(r"Mbps|Gig", p[2]) else f"{p[2]} ({speed(p[1])})"
def after(p):
    return p[4] or round(p[3] * provs[p[0]]["rise"])

# ---------- shared pieces ----------
NAV = """<nav><div class="wrap">
  <a class="logo" href="{r}index.html"><svg width="28" height="28" viewBox="0 0 28 28" aria-hidden="true"><rect x="3" y="2" width="22" height="24" rx="4" fill="currentColor"/><path d="M8 9h12M8 14h8" stroke="var(--bg)" stroke-width="2.4" stroke-linecap="round"/><circle cx="19" cy="20" r="4" fill="#ff2e7e"/></svg>Fairbill</a>
  <div class="links"><a href="{r}index.html#compare">Compare</a><a href="{r}index.html#browse">Browse ZIPs</a><a href="{r}index.html#prices">Advertised prices</a><a href="{r}guides/lower-your-internet-bill.html">Lower your bill</a></div>
  <a class="btn pink" href="{r}index.html#compare">Check my bill</a>
</div></nav>"""
FOOT = """<footer class="band"><div class="wrap">
  <div><b class="logo" style="font-size:20px">Fairbill</b><p style="margin-top:6px">Know what your neighbors pay.</p></div>
  <div>{links}</div>
  <div><a href="{r}index.html#compare">Compare a bill</a><br><a href="{r}guides/lower-your-internet-bill.html">How to lower your bill</a><br><a href="{r}privacy.html">Privacy policy</a></div>
  <div>Contact: {mail}<br>© {y} Fairbill</div>
</div></footer>"""
def foot(r):
    links = "<br>".join(f'<a href="{r}providers/{slug(p)}.html">{esc(p)} prices</a>' for p in order)
    return FOOT.format(r=r, links=links, mail=esc(cfg["contact_email"]), y=YEAR)
def head(title, desc, path, r, ld, og_type="article"):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{SITE}/{path}">
<meta property="og:type" content="{og_type}">
<meta property="og:url" content="{SITE}/{path}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="{SITE}/og.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{r}favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{r}style.css">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
</head>
"""
ORG = {"@type": "Organization", "@id": f"{SITE}/#org", "name": "Fairbill", "url": f"{SITE}/",
       "logo": f"{SITE}/favicon.svg", "email": cfg["contact_email"]}
def faq_ld(qas):
    return {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q,
            "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in qas]}
def faq_html(qas):
    return "".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in qas)

# ---------- start fresh ----------
if OUT.exists():
    shutil.rmtree(OUT)
(OUT / "providers").mkdir(parents=True)
(OUT / "guides").mkdir()
for f in ["style.css", "favicon.svg", "og.png"]:
    shutil.copy(SRC / f, OUT / f)

# ---------- home page ----------
idx = (SRC / "index.html").read_text(encoding="utf-8")
config_js = json.dumps({"SUPABASE_URL": cfg["supabase_url"], "SUPABASE_ANON_KEY": cfg["supabase_anon_key"],
                        "CONTACT_EMAIL": cfg["contact_email"]})
plans_js = json.dumps(plans, ensure_ascii=False)
rise_js = json.dumps({p: provs[p]["rise"] for p in order})
ad_rows = "".join(f'<tr><td><a href="providers/{slug(p[0])}.html">{esc(p[0])}</a></td><td>{esc(pname(p))}</td>'
                  f'<td class="n">{usd(p[3])}</td><td class="n">{usd(after(p)) if after(p) > p[3] + 1 else "Same"}</td></tr>' for p in plans)
cards = "".join(f'<a href="providers/{slug(p)}.html"><b>{esc(p)}</b><span>From {usd(min(x[3] for x in plans if x[0]==p))}/mo advertised · {esc(provs[p]["type"])}</span></a>' for p in order)
faqs = re.findall(r"<details><summary>(.*?)</summary><p>(.*?)</p></details>", idx, re.S)
faqs = [(html.unescape(q), html.unescape(re.sub(r"<.*?>", "", a))) for q, a in faqs]
ld_home = {"@context": "https://schema.org", "@graph": [
    {"@type": "WebSite", "@id": f"{SITE}/#site", "name": "Fairbill", "url": f"{SITE}/", "publisher": {"@id": f"{SITE}/#org"}},
    ORG,
    {"@type": "WebApplication", "name": "Fairbill internet bill comparison", "url": f"{SITE}/",
     "applicationCategory": "FinanceApplication", "operatingSystem": "Any",
     "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
     "description": "Compare what you pay for home internet with what neighbors in your ZIP code pay for the same provider and plan."},
    {"@type": "Dataset", "name": f"Advertised home internet prices by provider ({CHECKED})",
     "description": "New-customer, internet-only monthly prices with autopay for major US internet providers, with estimated regular prices after promotions end.",
     "url": f"{SITE}/#prices", "creator": {"@id": f"{SITE}/#org"}, "dateModified": TODAY,
     "spatialCoverage": "United States", "variableMeasured": ["Advertised monthly price (USD)", "Estimated price after promotion (USD)"],
     "isAccessibleForFree": True},
    {**faq_ld(faqs), "@id": f"{SITE}/#faq"}]}
rep = {"{{SITE}}": SITE, "{{CONFIG}}": config_js, "{{PLANS_JS}}": plans_js, "{{CHECKED_JS}}": json.dumps(CHECKED),
       "{{CHECKED}}": esc(CHECKED), "{{AD_ROWS}}": ad_rows, "{{PROVIDER_CARDS}}": cards,
       "{{JSONLD}}": json.dumps(ld_home, ensure_ascii=False)}
for k, v in rep.items():
    idx = idx.replace(k, v)
idx = re.sub(r"const RISE=\{.*?\};", "const RISE=" + rise_js + ";", idx, flags=re.S)
assert "{{" not in idx, re.findall(r"\{\{\w+\}\}", idx)
(OUT / "index.html").write_text(idx, encoding="utf-8")

priv = (SRC / "privacy.html").read_text(encoding="utf-8").replace("{{SITE}}", SITE).replace("{{CONTACT}}", esc(cfg["contact_email"]))
(OUT / "privacy.html").write_text(priv, encoding="utf-8")

# ---------- provider pages ----------
pages = ["", "privacy.html"]
for prov in order:
    ps = [p for p in plans if p[0] == prov]
    lo = min(p[3] for p in ps)
    hi_gap = max(after(p) - p[3] for p in ps)
    rises = hi_gap > 3
    title = f"{prov} internet prices in {YEAR}: advertised vs. what you'll pay"
    desc = (f"{prov} advertises home internet from {usd(lo)}/month. See every plan's advertised price, "
            f"the estimated price after the promo ends, and how to lower your {prov} bill.")
    rows = "".join(f'<tr><td>{esc(pname(p))}</td><td class="n">{usd(p[3])}</td>'
                   f'<td class="n">{usd(after(p)) if after(p) > p[3] + 1 else "Same"}</td>'
                   f'<td class="n"><a href="../index.html?provider={esc(prov)}&amp;speed={p[1]}#compare">Compare</a></td></tr>' for p in ps)
    cheapest = min(ps, key=lambda p: p[3])
    if rises:
        rise_txt = (f"Expect your bill to rise once the introductory price ends. By our estimate, {prov} plans can cost "
                    f"up to about {usd(hi_gap)} more per month at the regular rate. The exact increase depends on your plan and address.")
    else:
        rise_txt = (f"{prov} prices tend to stay close to the advertised rate, so large jumps after the first year are less common "
                    f"than with cable providers. Taxes, fees and equipment can still add to your bill.")
    qas = [
        (f"How much does {prov} internet cost per month?",
         f"As of {CHECKED}, {prov} advertises plans from {usd(lo)} a month ({pname(cheapest)}) for new customers, internet only, with autopay. Prices vary by address."),
        (f"Does {prov} raise prices after the first year?", rise_txt),
        (f"How can I lower my {prov} bill?",
         f"Compare your price with what neighbors pay for the same plan on Fairbill, then call {prov}, mention the advertised new-customer price and ask for the retention department if the first agent can't help."),
    ]
    ld = {"@context": "https://schema.org", "@graph": [ORG,
          {"@type": "Article", "headline": title, "description": desc, "dateModified": TODAY,
           "author": {"@id": f"{SITE}/#org"}, "publisher": {"@id": f"{SITE}/#org"},
           "mainEntityOfPage": f"{SITE}/providers/{slug(prov)}.html"},
          {"@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": "Fairbill", "item": f"{SITE}/"},
              {"@type": "ListItem", "position": 2, "name": f"{prov} prices", "item": f"{SITE}/providers/{slug(prov)}.html"}]},
          faq_ld(qas)]}
    others = " · ".join(f'<a href="{slug(o)}.html">{esc(o)}</a>' for o in order if o != prov)
    page = head(title, desc, f"providers/{slug(prov)}.html", "../", ld) + f"""<body>
{NAV.format(r="../")}
<main class="band"><div class="wrap prose">
  <p class="crumbs"><a href="../index.html">Fairbill</a> › {esc(prov)} prices</p>
  <h1>{esc(prov)} internet prices: advertised vs. what you'll really pay</h1>
  <p class="lede">{esc(prov)} advertises home internet from <b>{usd(lo)} a month</b>. Here is every plan's advertised price, our estimate of the regular price once promotions end, and how to pay less.</p>
  <p class="updated">Prices checked {esc(CHECKED)}. New-customer, internet-only prices with autopay; they vary by address.</p>
  <div class="scroll"><table><thead><tr><th>Plan</th><th class="n">Advertised</th><th class="n">After promo (est.)</th><th class="n">Your bill</th></tr></thead><tbody>{rows}</tbody></table></div>
  <h2>What to know about {esc(prov)} pricing</h2>
  <p>{esc(provs[prov]["note"])}</p>
  <p>{esc(rise_txt)}</p>
  <h2>See what your neighbors pay for {esc(prov)}</h2>
  <p>Advertised prices only tell half the story. On Fairbill, people share what they actually pay for {esc(prov)}, anonymously, by ZIP code and plan. Add your bill to see where you stand.</p>
  <p><a class="btn pink" href="../index.html?provider={esc(prov)}#compare">Compare my {esc(prov)} bill</a></p>
  <h2>How to lower your {esc(prov)} bill</h2>
  <ol>
    <li>Find your exact monthly price for internet only on your latest bill.</li>
    <li>Compare it with the advertised price above and with what neighbors pay on Fairbill.</li>
    <li>Call {esc(prov)} and say: "Your website lists this plan at {usd(cheapest[3])} for new customers. I'd like a better price, or I'll look at other providers."</li>
    <li>If the first agent can't help, ask for the retention (cancellations) department.</li>
  </ol>
  <p>Full step-by-step script: <a href="../guides/lower-your-internet-bill.html">How to lower your internet bill</a>.</p>
  <h2>Questions</h2>
  {faq_html(qas)}
  <h2>Other providers</h2>
  <p>{others}</p>
</div></main>
{foot("../")}
</body>
</html>
"""
    (OUT / "providers" / f"{slug(prov)}.html").write_text(page, encoding="utf-8")
    pages.append(f"providers/{slug(prov)}.html")

# ---------- guide page ----------
gtitle = f"How to lower your internet bill in {YEAR}: a 10-minute call script"
gdesc = "A step-by-step script to lower your home internet bill: what to check first, what to say, when to ask for the retention department and when to switch."
gqas = [
    ("What is the retention department?", "It's the team that handles customers who want to cancel. They usually have more discounts available than the first agent you reach."),
    ("When is the best time to call?", "A few weeks before your promotional price ends, or right after a price increase shows up on your bill."),
    ("Will asking for a lower price affect my service?", "No. Asking about prices and discounts doesn't change your service unless you agree to a new plan."),
]
cheap = sorted(plans, key=lambda p: p[3])[:5]
cheap_rows = "".join(f'<li><a href="../providers/{slug(p[0])}.html">{esc(p[0])}</a> {esc(pname(p))}: {usd(p[3])}/mo advertised</li>' for p in cheap)
gld = {"@context": "https://schema.org", "@graph": [ORG,
       {"@type": "Article", "headline": gtitle, "description": gdesc, "dateModified": TODAY,
        "author": {"@id": f"{SITE}/#org"}, "publisher": {"@id": f"{SITE}/#org"},
        "mainEntityOfPage": f"{SITE}/guides/lower-your-internet-bill.html"}, faq_ld(gqas)]}
guide = head(gtitle, gdesc, "guides/lower-your-internet-bill.html", "../", gld) + f"""<body>
{NAV.format(r="../")}
<main class="band"><div class="wrap prose">
  <p class="crumbs"><a href="../index.html">Fairbill</a> › Guides</p>
  <h1>How to lower your internet bill: a 10-minute call script</h1>
  <p class="lede">Internet companies raise prices on loyal customers once promotions end. Most will lower your bill if you ask the right way, with the right numbers.</p>
  <p class="updated">Updated {esc(CHECKED)}.</p>
  <h2>Before you call: get three numbers</h2>
  <ol>
    <li><b>What you pay now</b> for internet only, from your latest bill.</li>
    <li><b>What your provider advertises</b> to new customers for the same speed. See <a href="../index.html#prices">advertised prices by provider</a>.</li>
    <li><b>What your neighbors pay</b> for the same plan in your ZIP code. <a href="../index.html#compare">Check it on Fairbill</a>.</li>
  </ol>
  <h2>The script</h2>
  <pre>Hi, I'm calling about my internet bill. I'm paying [your price] a month for [your plan].

Your website advertises this plan for [advertised price] to new customers, and people in my ZIP code typically pay [neighbors' price].

I'd like to stay, but I need my bill closer to that. What can you do for me today?

If they say no: "Then please transfer me to the retention department. I'm ready to cancel."</pre>
  <p>On Fairbill, the <a href="../index.html#script">script fills in your real numbers</a> automatically.</p>
  <h2>If they won't lower it</h2>
  <ul>
    <li>Ask for the retention (cancellations) department. They usually have more room to offer discounts.</li>
    <li>Ask about a slower plan. Many homes don't need more than 300 to 500 Mbps.</li>
    <li>Return rented equipment if you can use your own router, and remove add-ons you don't use.</li>
    <li>Check other providers at your address. Some of the lowest advertised prices right now:</li>
  </ul>
  <ul>{cheap_rows}</ul>
  <h2>Questions</h2>
  {faq_html(gqas)}
</div></main>
{foot("../")}
</body>
</html>
"""
(OUT / "guides" / "lower-your-internet-bill.html").write_text(guide, encoding="utf-8")
pages.append("guides/lower-your-internet-bill.html")

# ---------- crawl files ----------
(OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")
urls = "".join(f"  <url><loc>{SITE}/{p}</loc><lastmod>{TODAY}</lastmod></url>\n" for p in pages)
(OUT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n', encoding="utf-8")
R404 = SITE + "/"
(OUT / "404.html").write_text(head("Page not found · Fairbill", "This page doesn't exist.", "404.html", R404, {"@context": "https://schema.org", **ORG}).replace(f'<link rel="canonical" href="{SITE}/404.html">\n', '<meta name="robots" content="noindex">\n') +
    f'<body>{NAV.format(r=R404)}<main class="band"><div class="wrap prose"><h1>Page not found</h1><p><a class="btn pink" href="{R404}">Go to Fairbill</a></p></div></main></body></html>', encoding="utf-8")
for f in DATA.glob("google*.html"):   # Google Search Console verification files
    shutil.copy(f, OUT / f.name)
if (DATA / "ads.txt").exists():
    shutil.copy(DATA / "ads.txt", OUT / "ads.txt")
if (DATA / "CNAME").exists():
    shutil.copy(DATA / "CNAME", OUT / "CNAME")

# ---------- database prices (paste into Supabase when prices change) ----------
sq = lambda t: "'" + t.replace("'", "''") + "'"
vals = ",\n  ".join(f"({sq(p[0])}, {p[1]}, {sq(p[2])}, {p[3]})" for p in plans)
(ROOT / "supabase" / "plans.sql").write_text(
    "-- Generated by tools/build.py from data/precios.csv. Paste into Supabase > SQL Editor > Run.\n"
    "insert into public.plans (provider, speed, name, advertised) values\n  " + vals +
    "\non conflict (provider, speed) do update set name = excluded.name, advertised = excluded.advertised, checked = current_date;\n",
    encoding="utf-8")
print(f"Built {len(pages)} pages into {OUT}")
