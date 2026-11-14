import feedparser
import os
import re
import time
import requests
from datetime import datetime, timedelta, timezone
from google import genai

# ==========================================
# TAB 1: GLOBAL INFRASTRUCTURE & GEOPOLITICS
# ==========================================
GLOBAL_FEEDS = [
    "http://bbci.co.uk" + "/news/world/rss.xml",
    "https://aljazeera.com" + "/xml/rss/all.xml",
    "https://nytimes.com" + "/services/xml/rss/nyt/World.xml",
    "https://npr.org" + "/1004/rss.xml",
    "https://theguardian.com" + "/world/rss",
    "https://cnbc.com" + "/id/100727362/device/rss/rss.html",
    "https://bellingcat.com" + "/feed/",
    "https://warontherocks.com" + "/feed/",
    "https://defensenews.com" + "/arc/outboundfeeds/rss/",
    "https://twz.com" + "/feed",
    "https://gcaptain.com" + "/feed/",
    "https://splash247.com" + "/feed/",
    "https://submarinenetworks.com" + "/feed",
    "https://semianalysis.com" + "/feed",
    "https://utilitydive.com" + "/feeds/news/",
    "https://agweb.com" + "/rss/news",
    "https://google.com" + "/rss/search?q=subsea+cable+OR+undersea+cable+when:14d&hl=en-US&gl=US&ceid=US:en",
    "https://google.com" + "/rss/search?q=Strait+of+Hormuz+OR+Red+Sea+shipping+insurance+when:14d&hl=en-US&gl=US&ceid=US:en",
    "https://google.com" + "/rss/search?q=Ukraine+power+grid+transformer+OR+Abu+Dhabi+talks+when:14d&hl=en-US&gl=US&ceid=US:en",
    "https://google.com" + "/rss/search?q=semiconductor+ASML+OR+gallium+OR+Nvidia+China+when:14d&hl=en-US&gl=US&ceid=US:en",
    "https://google.com" + "/rss/search?q=global+fertilizer+ammonia+supply+OR+seabed+mining+when:14d&hl=en-US&gl=US&ceid=US:en",
    "https://google.com" + "/rss/search?q=Congo+M23+tantalum+OR+Ethiopia+Eritrea+Red+Sea+when:14d&hl=en-US&gl=US&ceid=US:en",
    "https://google.com" + "/rss/search?q=food+shortage+OR+crop+failure+OR+grain+shortage+when:14d&hl=en-US&gl=US&ceid=US:en",
    "https://google.com" + "/rss/search?q=water+shortage+OR+water+rationing+OR+aquifer+depletion+when:14d&hl=en-US&gl=US&ceid=US:en",
    "https://google.com" + "/rss/search?q=emergency+preparedness+OR+survival+food+sales+OR+generator+demand+when:14d&hl=en-US&gl=US&ceid=US:en",
    "https://google.com" + "/rss/search?q=supply+chain+shortage+OR+grocery+shortage+OR+medicine+shortage+when:14d&hl=en-US&gl=US&ceid=US:en",
]

GLOBAL_KEYWORDS = [
    "subsea cable", "undersea cable", "fiber optic", "landing station", "seabed mining",
    "gps jamming", "gps spoofing", "starlink", "leo satellite", "data center",
    "hormuz", "red sea", "bab el-mandeb", "suez", "war risk", "maritime insurance",
    "p&i club", "tanker", "blockade", "houthi", "swift",
    "semiconductor", "asml", "lithography", "gallium", "germanium", "spruce pine",
    "quartz", "rare earth", "nvidia", "h200", "tantalum", "tungsten", "tsmc",
    "transformer", "power grid", "substation", "electrical steel", "fertilizer",
    "ammonia", "potash", "phosphate", "nitric acid", "pharmaceutical", "medicine shortage",
    "food shortage", "crop failure", "harvest", "drought", "water shortage",
    "water rationing", "aquifer", "reservoir", "boil water", "water contamination",
    "preparedness", "survival", "freeze dried", "stockpiling", "panic buying",
    "generator", "rationing", "food inflation", "supply chain",
    "abu dhabi", "donbas", "iran", "israel", "ukraine", "russia", "taiwan",
    "m23", "congo", "ethiopia", "eritrea", "tariff", "sanctions", "trump", "xi jinping"
]

# ==========================================
# TAB 2: RALEIGH & NC HOUSEHOLD BRIEFING
# ==========================================
LOCAL_FEEDS = [
    "https://wunc.org" + "/rss.xml",
    "https://google.com" + "/rss/search?q=Duke+Energy+North+Carolina+rate+OR+LIEAP+energy+assistance+when:14d&hl=en-US&gl=US&ceid=US:en",
    "https://google.com" + "/rss/search?q=Wake+County+well+water+OR+groundwater+OR+PFAS+testing+when:14d&hl=en-US&gl=US&ceid=US:en",
    "https://google.com" + "/rss/search?q=Wake+County+trash+OR+convenience+center+OR+property+tax+relief+when:14d&hl=en-US&gl=US&ceid=US:en",
    "https://google.com" + "/rss/search?q=Raleigh+gas+prices+OR+North+Carolina+gas+tax+OR+I-540+toll+when:14d&hl=en-US&gl=US&ceid=US:en",
    "https://google.com" + "/rss/search?q=NC+Medicaid+OR+Healthy+Blue+North+Carolina+benefits+when:14d&hl=en-US&gl=US&ceid=US:en",
    "https://google.com" + "/rss/search?q=FAFSA+special+circumstances+professional+judgment+income+appeal+when:14d&hl=en-US&gl=US&ceid=US:en",
    "https://google.com" + "/rss/search?q=Wake+County+schools+WCPSS+fee+waiver+OR+Lifeline+phone+discount+when:14d&hl=en-US&gl=US&ceid=US:en",
]

LOCAL_KEYWORDS = [
    "duke energy", "rate hike", "utilities commission", "lieap", "energy assistance",
    "crisis intervention", "electric bill", "lifeline", "phone bill",
    "wake county", "raleigh", "well water", "groundwater", "aquifer", "pfas",
    "trash", "landfill", "convenience center", "property tax", "tax relief",
    "gas prices", "gas tax", "fuel", "i-540", "ncdot", "triangle expressway",
    "medicaid", "healthy blue", "nc dhhs", "benefits", "redetermination",
    "fafsa", "financial aid", "professional judgment", "special circumstances",
    "pell grant", "tuition", "wcpss", "wake county schools", "food assistance", "snap"
]

def fetch_articles(feeds, keywords, days_back=14):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
    matched = []
    seen_titles = set()
    for url in feeds:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:60]:
                title = entry.get("title", "").strip()
                if not title or title in seen_titles:
                    continue
                pub_date = "Recent"
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    dt = datetime.fromtimestamp(time.mktime(entry.published_parsed), tz=timezone.utc)
                    if dt < cutoff:
                        continue
                    pub_date = dt.strftime("%Y-%m-%d")
                text = f"{title} {entry.get('summary', '')}".lower()
                if any(kw in text for kw in keywords):
                    seen_titles.add(title)
                    matched.append(f"- [{pub_date}] {title} ({entry.link})")
        except Exception:
            continue
    return "\n".join(matched[:140])

def call_gemini(prompt):
    api_key = os.environ["GEMINI_API_KEY"].strip()
    attempts = [
        ("v1beta", "gemini-3.0-flash"),
        ("v1beta", "gemini-3-flash-preview"),
        ("v1alpha", "gemini-3.0-flash"),
        ("v1alpha", "gemini-3-flash-preview"),
        ("v1beta", "gemini-2.5-flash-lite"),
        ("v1beta", "gemini-2.0-flash"),
        ("v1beta", "gemini-2.5-pro"),
        ("v1", "gemini-2.5-flash-lite"),
        ("v1", "gemini-2.0-flash"),
    ]
    last_err = None
    for api_ver, model_name in attempts:
        try:
            client = genai.Client(api_key=api_key, http_options={"api_version": api_ver})
            response = client.models.generate_content(model=model_name, contents=prompt)
            if response and response.text:
                return response.text
        except Exception as e:
            last_err = e
            continue
    raise RuntimeError(f"All Gemini model attempts failed. Last error: {last_err}")

def generate_global_briefing(raw_articles, is_backfill=False):
    if not raw_articles:
        return "No major infrastructure, conflict, or household supply updates matched in this window."
    timeframe = "the past 14 days" if is_backfill else "the last 24–48 hours"
    prompt = f"""
    You are a senior geopolitical, critical infrastructure, and consumer resilience analyst.
    Review these global and national news headlines from {timeframe} and synthesize the most
    important developments into a structured briefing using these 6 sections:

    1. Subsea Cables, Space Timing & Digital Chokepoints
    2. Maritime War-Risk Insurance, Shipping & Red Sea / Hormuz
    3. Semiconductors, Critical Minerals & U.S.–China Tech Conflict
    4. Electrical Grid Transformers, Fertilizer & Industrial Supply Chains
    5. Active Wars, Peace Negotiations & U.S. Policy Shifts
    6. Quiet Household Impacts: Food Shortages, Water Crises & Preparedness/Survival Trends

    Include dates and clickable markdown links [Source](url) for every item cited.
    Headlines:
    {raw_articles}
    """
    return call_gemini(prompt)

def generate_local_briefing(raw_articles, is_backfill=False):
    if not raw_articles:
        return "No major Raleigh, Wake County, or NC household cost-of-living updates matched in this window."
    timeframe = "the past 14 days" if is_backfill else "the last 24–48 hours"
    prompt = f"""
    You are a North Carolina public policy, utilities, and household cost-of-living analyst.
    Review these Raleigh, Wake County, and North Carolina headlines from {timeframe} and organize
    actionable updates into these 5 sections:

    1. NC Electric Rates, Duke Energy & Utility/Phone Bill Relief (LIEAP, CIP, Lifeline)
    2. Unincorporated Wake County: Well Water, Groundwater/PFAS, Trash & Property Taxes
    3. Raleigh Fuel Prices, NC Gas Tax & Triangle Commuting Costs
    4. NC Medicaid (Healthy Blue) & State Healthcare Benefit Updates
    5. College Financial Aid (FAFSA Income-Loss Appeals) & Wake County Youth Programs

    Highlight practical steps, deadlines, or savings opportunities, and include dates and clickable
    markdown links [Source](url) for every item cited.
    Headlines:
    {raw_articles}
    """
    return call_gemini(prompt)

STYLE = """<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Inter:wght@400;500;600&display=swap');
:root{--bg:#FAF6F0;--card:#FFFFFF;--ink:#1E2A38;--muted:#5E6B78;--line:#E8E0D5;--shadow:rgba(30,42,56,.07)}
@media (prefers-color-scheme:dark){:root{--bg:#12171D;--card:#1B222B;--ink:#E8EDF2;--muted:#9AA7B4;--line:#2A333D;--shadow:rgba(0,0,0,.35)}}
body{background:var(--bg)!important;color:var(--ink)!important;font-family:Inter,system-ui,-apple-system,'Segoe UI',sans-serif!important}
.briefing{--accent:#2F5D8C;--soft:#E4ECF4;max-width:760px;margin:0 auto;padding:8px 4px 40px;color:var(--ink);font-size:16px;line-height:1.6}
.briefing.local{--accent:#C2603A;--soft:#F8E8DF}
@media (prefers-color-scheme:dark){.briefing{--accent:#7FB0E0;--soft:#1F2D3B}.briefing.local{--accent:#E58F6B;--soft:#3A2A22}}
.briefing h1,.briefing h2,.briefing h3{border:0!important;padding:0!important;color:var(--ink)!important}
.briefing .tabs{display:flex;gap:8px;flex-wrap:wrap;margin:6px 0 4px}
.briefing .tab{padding:10px 18px;border-radius:999px;border:1px solid var(--line);background:var(--card);color:var(--ink)!important;text-decoration:none!important;font-weight:600;font-size:.95rem}
.briefing .tab.g:hover{border-color:#2F5D8C}
.briefing .tab.l:hover{border-color:#C2603A}
.briefing .tab.on{background:var(--accent);border-color:var(--accent);color:#fff!important}
.briefing .hero{margin:26px 0 8px}
.briefing .kicker{font-size:.75rem;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);font-weight:600}
.briefing .hero h1{font-family:Fraunces,Georgia,serif!important;font-size:clamp(1.9rem,6vw,2.7rem);line-height:1.1;margin:6px 0 8px!important;letter-spacing:-.01em}
.briefing .date{color:var(--muted);font-size:.95rem;margin:0}
.briefing .lede{color:var(--muted);margin:14px 0 6px}
.briefing .card{background:var(--card);border:1px solid var(--line);border-top:4px solid var(--accent);border-radius:14px;padding:4px 22px 16px;margin:18px 0;box-shadow:0 1px 2px var(--shadow),0 8px 22px var(--shadow)}
.briefing .card h3{font-family:Fraunces,Georgia,serif!important;font-size:1.22rem;line-height:1.25;margin:18px 0 6px!important}
.briefing .card ul{padding-left:1.1rem;margin:0}
.briefing .card li{margin:14px 0}
.briefing .card li strong{color:var(--accent)}
.briefing a{color:var(--accent);overflow-wrap:anywhere}
.briefing details.archive{margin-top:30px;padding:14px 18px;border:1px solid var(--line);border-radius:14px;background:var(--card)}
.briefing details.archive summary{cursor:pointer;font-weight:600}
.briefing details.archive ul{margin:10px 0 0;padding-left:1.1rem}
@media (max-width:600px){.briefing .tab{flex:1 1 100%;text-align:center}.briefing .card{padding:2px 16px 14px}}
</style>"""


def pretty_date(label):
    try:
        return datetime.strptime(label[:10], "%Y-%m-%d").strftime("%A, %B %d, %Y").replace(" 0", " ")
    except ValueError:
        return label


def cardify(text):
    """Wrap each numbered section of the AI briefing in its own card."""
    text = text.strip()
    # Turn bold numbered lines like "**1. Title**" into real headings
    text = re.sub(r'(?m)^\*\*(\d+\.\s.+?)\*\*\s*$', r'### \1', text)
    parts = re.split(r'(?m)^#{2,4}\s+', text)
    out = []
    intro = parts[0].strip()
    if intro:
        out.append(f'<div class="lede" markdown="1">\n\n{intro}\n\n</div>')
    for p in parts[1:]:
        out.append(f'<section class="card" markdown="1">\n\n### {p.strip()}\n\n</section>')
    return "\n\n".join(out)


def tab_bar(active):
    g_on = " on" if active == "global" else ""
    l_on = " on" if active == "local" else ""
    return (
        '<nav class="tabs">'
        f'<a class="tab g{g_on}" href="./">🌐 Global Infrastructure &amp; Conflict</a>'
        f'<a class="tab l{l_on}" href="local.html">🏠 Raleigh &amp; NC Household</a>'
        '</nav>'
    )


def build_page(kind, title, window, label, body, links, archive_title):
    return (
        f'{STYLE}\n\n'
        f'<div class="briefing {kind}" markdown="1">\n\n'
        f'{tab_bar(kind)}\n\n'
        f'<header class="hero"><div class="kicker">Daily Briefing</div>'
        f'<h1>{title}</h1>'
        f'<p class="date">{pretty_date(label)} · {window}</p></header>\n\n'
        f'{cardify(body)}\n\n'
        f'<details class="archive" markdown="1">\n<summary>{archive_title}</summary>\n\n{links}\n\n</details>\n\n'
        f'</div>\n'
    )


def build_archive_page(kind, title, label, body):
    back = "../" if kind == "global" else "../local.html"
    return (
        f'{STYLE}\n\n'
        f'<div class="briefing {kind}" markdown="1">\n\n'
        f'<nav class="tabs"><a class="tab on" href="{back}">← Back to today\'s briefing</a></nav>\n\n'
        f'<header class="hero"><div class="kicker">Archive</div>'
        f'<h1>{title}</h1><p class="date">{pretty_date(label)}</p></header>\n\n'
        f'{cardify(body)}\n\n'
        f'</div>\n'
    )


def save_and_notify(global_text, local_text, label):
    os.makedirs("archive", exist_ok=True)
    os.makedirs("archive-local", exist_ok=True)

    # Save permanent archive files for both tabs
    with open(f"archive/{label}.md", "w", encoding="utf-8") as f:
        f.write(build_archive_page("global", "Global Infrastructure &amp; Conflict", label, global_text))

    with open(f"archive-local/{label}.md", "w", encoding="utf-8") as f:
        f.write(build_archive_page("local", "Raleigh &amp; NC Household", label, local_text))

    # Archive link lists (GitHub Pages publishes .md files as .html)
    global_files = sorted(os.listdir("archive"), reverse=True)
    global_links = "\n".join([f"- [{fn[:-3]}](archive/{fn[:-3]}.html)" for fn in global_files if fn.endswith(".md")])

    local_files = sorted(os.listdir("archive-local"), reverse=True)
    local_links = "\n".join([f"- [{fn[:-3]}](archive-local/{fn[:-3]}.html)" for fn in local_files if fn.endswith(".md")])

    # Tab 1 Page: index.md
    with open("index.md", "w", encoding="utf-8") as f:
        f.write(build_page(
            "global", "Global Infrastructure, Conflict &amp; Resilience", "Last 48 hours", label,
            global_text, global_links, "Past global briefings"))

    # Tab 2 Page: local.md
    with open("local.md", "w", encoding="utf-8") as f:
        f.write("---\nlayout: default\n---\n\n")
        f.write(build_page(
            "local", "Raleigh &amp; NC Household Costs",
            "Last 14 days" if "14Day" in label else "Last 48 hours", label,
            local_text, local_links, "Past local briefings"))


    # Send single push alert to iPhone
    topic = os.environ.get("NTFY_TOPIC", "").strip().strip("/")
    if topic:
        ntfy_url = "https://ntfy.sh" + "/" + topic
        page_url = "https://" + "shanahunte" + ".github.io" + "/daily-briefing/"
        requests.post(
            ntfy_url,
            data=f"Your {label} Global & Raleigh/NC Briefings are ready.".encode("utf-8"),
            headers={
                "Title": "Daily Briefings Updated",
                "Click": page_url
            }
        )

if __name__ == "__main__":
    local_existing = os.listdir("archive-local") if os.path.exists("archive-local") else []
    if not local_existing:
        g_articles = fetch_articles(GLOBAL_FEEDS, GLOBAL_KEYWORDS, days_back=2)
        l_articles = fetch_articles(LOCAL_FEEDS, LOCAL_KEYWORDS, days_back=14)
        g_brief = generate_global_briefing(g_articles, is_backfill=False)
        l_brief = generate_local_briefing(l_articles, is_backfill=True)
        save_and_notify(g_brief, l_brief, f"{datetime.now().strftime('%Y-%m-%d')}-Local-14Day-Init")
    else:
        g_articles = fetch_articles(GLOBAL_FEEDS, GLOBAL_KEYWORDS, days_back=2)
        l_articles = fetch_articles(LOCAL_FEEDS, LOCAL_KEYWORDS, days_back=2)
        g_brief = generate_global_briefing(g_articles, is_backfill=False)
        l_brief = generate_local_briefing(l_articles, is_backfill=False)
        save_and_notify(g_brief, l_brief, datetime.now().strftime("%Y-%m-%d"))

