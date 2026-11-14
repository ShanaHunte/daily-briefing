import feedparser
import os
import time
import requests
from datetime import datetime, timedelta, timezone
from google import genai

# 1. Expanded Global News, National Media, Blogs & 14-Day Topic Feeds
FEEDS = [
    # Major Global & U.S. Outlets
    "http://bbci.co.uk" + "/news/world/rss.xml",
    "https://aljazeera.com" + "/xml/rss/all.xml",
    "https://nytimes.com" + "/services/xml/rss/nyt/World.xml",
    "https://npr.org" + "/1004/rss.xml",
    "https://theguardian.com" + "/world/rss",
    "https://cnbc.com" + "/id/100727362/device/rss/rss.html",

    # Defense, OSINT & Geopolitics Blogs
    "https://bellingcat.com" + "/feed/",
    "https://warontherocks.com" + "/feed/",
    "https://defensenews.com" + "/arc/outboundfeeds/rss/",
    "https://twz.com" + "/feed",

    # Maritime, Subsea Cables, Energy, Tech & Agriculture
    "https://gcaptain.com" + "/feed/",
    "https://splash247.com" + "/feed/",
    "https://submarinenetworks.com" + "/feed",
    "https://semianalysis.com" + "/feed",
    "https://utilitydive.com" + "/feeds/news/",
    "https://agweb.com" + "/rss/news",

    # High-Volume Global Topic Feeds (Infrastructure & Geopolitics)
    "https://google.com" + "/rss/search?q=subsea+cable+OR+undersea+cable+when:14d&hl=en-US&gl=US&ceid=US:en",
    "https://google.com" + "/rss/search?q=Strait+of+Hormuz+OR+Red+Sea+shipping+insurance+when:14d&hl=en-US&gl=US&ceid=US:en",
    "https://google.com" + "/rss/search?q=Ukraine+power+grid+transformer+OR+Abu+Dhabi+talks+when:14d&hl=en-US&gl=US&ceid=US:en",
    "https://google.com" + "/rss/search?q=semiconductor+ASML+OR+gallium+OR+Nvidia+China+when:14d&hl=en-US&gl=US&ceid=US:en",
    "https://google.com" + "/rss/search?q=global+fertilizer+ammonia+supply+OR+seabed+mining+when:14d&hl=en-US&gl=US&ceid=US:en",
    "https://google.com" + "/rss/search?q=Congo+M23+tantalum+OR+Ethiopia+Eritrea+Red+Sea+when:14d&hl=en-US&gl=US&ceid=US:en",

    # High-Volume Topic Feeds (Food Shortages, Water Crises & Preparedness Trends)
    "https://google.com" + "/rss/search?q=food+shortage+OR+crop+failure+OR+grain+shortage+when:14d&hl=en-US&gl=US&ceid=US:en",
    "https://google.com" + "/rss/search?q=water+shortage+OR+water+rationing+OR+aquifer+depletion+when:14d&hl=en-US&gl=US&ceid=US:en",
    "https://google.com" + "/rss/search?q=emergency+preparedness+OR+survival+food+sales+OR+generator+demand+when:14d&hl=en-US&gl=US&ceid=US:en",
    "https://google.com" + "/rss/search?q=supply+chain+shortage+OR+grocery+shortage+OR+medicine+shortage+when:14d&hl=en-US&gl=US&ceid=US:en",
]

# 2. Expanded Keywords (Infrastructure + Everyday Household Impacts)
KEYWORDS = [
    # Subsea & Digital
    "subsea cable", "undersea cable", "fiber optic", "landing station", "seabed mining",
    "gps jamming", "gps spoofing", "starlink", "leo satellite", "data center",
    # Maritime & Chokepoints
    "hormuz", "red sea", "bab el-mandeb", "suez", "war risk", "maritime insurance",
    "p&i club", "tanker", "blockade", "houthi", "swift",
    # Tech & Critical Minerals
    "semiconductor", "asml", "lithography", "gallium", "germanium", "spruce pine",
    "quartz", "rare earth", "nvidia", "h200", "tantalum", "tungsten", "tsmc",
    # Energy, Grids & Industrial Chemicals
    "transformer", "power grid", "substation", "electrical steel", "fertilizer",
    "ammonia", "potash", "phosphate", "nitric acid", "pharmaceutical", "medicine shortage",
    # Food, Water & Survival/Preparedness Trends
    "food shortage", "crop failure", "harvest", "drought", "water shortage",
    "water rationing", "aquifer", "reservoir", "boil water", "water contamination",
    "preparedness", "survival", "freeze dried", "stockpiling", "panic buying",
    "generator", "rationing", "food inflation", "supply chain",
    # Active Conflicts & Diplomacy
    "abu dhabi", "donbas", "iran", "israel", "ukraine", "russia", "taiwan",
    "m23", "congo", "ethiopia", "eritrea", "tariff", "sanctions", "trump", "xi jinping"
]

def fetch_articles(days_back=14):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
    matched = []
    seen_titles = set()
    for url in FEEDS:
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
                if any(kw in text for kw in KEYWORDS):
                    seen_titles.add(title)
                    matched.append(f"- [{pub_date}] {title} ({entry.link})")
        except Exception:
            continue
    return "\n".join(matched[:180])

def generate_briefing(raw_articles, is_backfill=False):
    if not raw_articles:
        return "No major infrastructure, conflict, or household supply updates matched your keywords in this window."
    
    timeframe_label = "the past 14 days (2-week catch-up digest)" if is_backfill else "the last 24–48 hours"
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    prompt = f"""
    You are a senior geopolitical, critical infrastructure, and consumer resilience analyst. 
    Review these global and national news headlines from {timeframe_label} and synthesize the most 
    important developments into a comprehensive, well-organized intelligence briefing using these 6 sections:

    1. Subsea Cables, Space Timing & Digital Chokepoints
    2. Maritime War-Risk Insurance, Shipping & Red Sea / Hormuz
    3. Semiconductors, Critical Minerals & U.S.–China Tech Conflict
    4. Electrical Grid Transformers, Fertilizer & Industrial Supply Chains
    5. Active Wars, Peace Negotiations & U.S. Policy Shifts
    6. Quiet Household Impacts: Food Shortages, Water Crises & Preparedness/Survival Trends

    Group related headlines together, highlight early warning signs that everyday consumers might miss, 
    and include the date and clickable markdown links [Source](url) for every development cited.

    Headlines:
    {raw_articles}
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text

def save_and_notify(briefing_text, label):
    os.makedirs("archive", exist_ok=True)
    
    # Save permanent archive file
    archive_path = f"archive/{label}.md"
    with open(archive_path, "w", encoding="utf-8") as f:
        f.write(f"# Infrastructure & Resilience Briefing — {label}\n\n{briefing_text}\n")
    
    # Build archive list for homepage
    past_files = sorted(os.listdir("archive"), reverse=True)
    archive_links = "\n".join([f"- [{fn.replace('.md', '')}](archive/{fn})" for fn in past_files])
    
    # Update live homepage (index.md)
    with open("index.md", "w", encoding="utf-8") as f:
        f.write(f"# Global Infrastructure, Conflict & Resilience Briefing ({label})\n\n{briefing_text}\n\n---\n## Past Briefings Archive\n{archive_links}\n")

    # Send push alert to iPhone
    topic = os.environ.get("NTFY_TOPIC", "").strip().strip("/")
    if topic:
        ntfy_url = "https://ntfy.sh" + "/" + topic
        requests.post(
            ntfy_url,
            data=f"Your {label} Infrastructure & Resilience Briefing is ready.".encode("utf-8"),
            headers={
                "Title": "Daily Infrastructure & Resilience Briefing",
                "Click": "https://github.io"
            }
        )

if __name__ == "__main__":
    existing = [f for f in os.listdir("archive") if "Full-14Day" in f] if os.path.exists("archive") else []
    if not existing:
        articles = fetch_articles(days_back=14)
        briefing = generate_briefing(articles, is_backfill=True)
        save_and_notify(briefing, f"{datetime.now().strftime('%Y-%m-%d')}-Full-14Day-Digest")
    else:
        articles = fetch_articles(days_back=2)
        briefing = generate_briefing(articles, is_backfill=False)
        save_and_notify(briefing, datetime.now().strftime("%Y-%m-%d"))
