import feedparser
import os
import time
import requests
from datetime import datetime, timedelta, timezone
from google import genai

# 1. Global News, National Media & Niche Infrastructure Blogs
FEEDS = [
    "https://reuters.com",
    "http://bbci.co.uk",
    "https://aljazeera.com",
    "https://nytimes.com",
    "https://gcaptain.com",                  # Maritime & war-risk insurance
    "https://submarinenetworks.com",      # Subsea fiber-optic cables
    "https://semianalysis.com",           # Semiconductor supply chains
    "https://bellingcat.com",            # Conflict & OSINT analysis
]

# 2. Keywords from your Master Brief
KEYWORDS = [
    "subsea cable", "undersea cable", "hormuz", "red sea", "war risk", 
    "maritime insurance", "transformer", "power grid", "asml", "gallium", 
    "germanium", "spruce pine", "fertilizer", "ammonia", "gps jamming", 
    "starlink", "abu dhabi", "nvidia", "seabed mining", "m23", "tantalum"
]

def fetch_articles(days_back=14):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
    matched = []
    for url in FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:50]:
                pub_date = "Recent"
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    dt = datetime.fromtimestamp(time.mktime(entry.published_parsed), tz=timezone.utc)
                    if dt < cutoff:
                        continue
                    pub_date = dt.strftime("%Y-%m-%d")
                text = f"{entry.get('title', '')} {entry.get('summary', '')}".lower()
                if any(kw in text for kw in KEYWORDS):
                    matched.append(f"- [{pub_date}] {entry.title} ({entry.link}): {entry.get('summary', '')[:250]}...")
        except Exception:
            continue
    return "\n".join(matched)

def generate_briefing(raw_articles, is_backfill=False):
    if not raw_articles:
        return "No major infrastructure or conflict updates matched your keywords in this window."
    
    timeframe_label = "the past 14 days (2-week catch-up digest)" if is_backfill else "the last 24 hours"
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    prompt = f"""
    You are a geopolitical and critical infrastructure analyst. Review these news items from {timeframe_label}
    and organize all relevant developments into a clear, structured briefing matching these categories:
    1. Subsea Cables & Digital Chokepoints
    2. Maritime Insurance, Shipping & Red Sea/Hormuz
    3. Semiconductors, Critical Minerals & Tech
    4. Energy Grids, Transformers & Fertilizer/Food Supply
    5. Active Negotiations & U.S. Policy Shifts

    Include the publication date and clickable source links for every item. Raw articles:
    {raw_articles}
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text

def save_and_notify(briefing_text, label):
    today = datetime.now().strftime("%Y-%m-%d")
    os.makedirs("archive", exist_ok=True)
    
    # Save permanent archive file
    archive_path = f"archive/{label}.md"
    with open(archive_path, "w", encoding="utf-8") as f:
        f.write(f"# Infrastructure & Conflict Briefing — {label}\n\n{briefing_text}\n")
    
    # Build archive list for homepage
    past_files = sorted(os.listdir("archive"), reverse=True)
    archive_links = "\n".join([f"- [{fn.replace('.md', '')}](archive/{fn})" for fn in past_files])
    
    # Update live homepage (index.md)
    with open("index.md", "w", encoding="utf-8") as f:
        f.write(f"# Latest Infrastructure & Conflict Briefing ({label})\n\n{briefing_text}\n\n---\n## Past Briefings Archive\n{archive_links}\n")

    # Send push alert to iPhone
    topic = os.environ.get("NTFY_TOPIC")
    if topic:
        requests.post(
            f"https://ntfy.sh{topic}",
            data=f"Your {label} Infrastructure & Conflict Briefing is ready.".encode("utf-8"),
            headers={
                "Title": "Daily Infrastructure Briefing",
                "Click": "https://github.io"
            }
        )

if __name__ == "__main__":
    # Automatically run a 14-day catch-up if fewer than 2 archive files exist; otherwise run daily 2-day window
    existing = os.listdir("archive") if os.path.exists("archive") else []
    if len(existing) < 2:
        articles = fetch_articles(days_back=14)
        briefing = generate_briefing(articles, is_backfill=True)
        save_and_notify(briefing, f"{datetime.now().strftime('%Y-%m-%d')}-14Day-Digest")
    else:
        articles = fetch_articles(days_back=2)
        briefing = generate_briefing(articles, is_backfill=False)
        save_and_notify(briefing, datetime.now().strftime("%Y-%m-%d"))
