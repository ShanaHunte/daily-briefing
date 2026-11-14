import feedparser
import os
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

def save_and_notify(global_text, local_text, label):
    os.makedirs("archive", exist_ok=True)
    os.makedirs("archive-local", exist_ok=True)

    # Save permanent archive files for both tabs
    with open(f"archive/{label}.md", "w", encoding="utf-8") as f:
        f.write(f"# Global Infrastructure & Conflict Briefing — {label}\n\n{global_text}\n")

    with open(f"archive-local/{label}.md", "w", encoding="utf-8") as f:
        f.write(f"# Raleigh & NC Household Briefing — {label}\n\n{local_text}\n")

    # Build archive link lists
    global_files = sorted(os.listdir("archive"), reverse=True)
    global_links = "\n".join([f"- [{fn.replace('.md', '')}](archive/{fn})" for fn in global_files])

    local_files = sorted(os.listdir("archive-local"), reverse=True)
    local_links = "\n".join([f"- [{fn.replace('.md', '')}](archive-local/{fn})" for fn in local_files])

    # Styled visual tab bar at the top of both pages
    nav_bar = (
        '<div style="display:flex; gap:10px; margin-bottom:20px; border-bottom:2px solid #e1e4e8; padding-bottom:10px;">'
        '<a href="./" style="padding:8px 16px; background:#0969da; color:white; text-decoration:none; border-radius:6px; font-weight:bold;">🌐 Global Infrastructure & Conflict</a>'
        '<a href="local.html" style="padding:8px 16px; background:#f6f8fa; color:#24292f; border:1px solid #d0d7de; text-decoration:none; border-radius:6px; font-weight:bold;">🏠 Raleigh & NC Household</a>'
        '</div>\n\n'
    )

    # Tab 1 Page: index.md
    with open("index.md", "w", encoding="utf-8") as f:
        f.write(
            f"{nav_bar}# Global Infrastructure, Conflict & Resilience Briefing ({label})\n\n"
            f"{global_text}\n\n---\n## Past Global Briefings Archive\n{global_links}\n"
        )

    # Tab 2 Page: local.md
    with open("local.md", "w", encoding="utf-8") as f:
        f.write(
            f"{nav_bar}# Raleigh & NC Household Cost-of-Living Briefing ({label})\n\n"
            f"{local_text}\n\n---\n## Past Local Briefings Archive\n{local_links}\n"
        )

    # Send single push alert to iPhone
    topic = os.environ.get("NTFY_TOPIC", "").strip().strip("/")
    if topic:
        ntfy_url = "https://ntfy.sh" + "/" + topic
        page_url = "https://github.io" + "/daily-briefing/"
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

