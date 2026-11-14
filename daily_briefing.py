import feedparser
import os
import requests
from datetime import datetime
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

def fetch_relevant_articles():
    matched = []
    for url in FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:15]:
                text = f"{entry.get('title', '')} {entry.get('summary', '')}".lower()
                if any(kw in text for kw in KEYWORDS):
                    matched.append(f"- {entry.title} ({entry.link}): {entry.get('summary', '')[:250]}...")
        except Exception:
            continue
    return "\n".join(matched)

def generate_briefing(raw_articles):
    if not raw_articles:
        return "No major infrastructure or conflict updates matched your keywords in the last 24 hours."
    
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    prompt = f"""
    You are a geopolitical and critical infrastructure analyst. Review these news items 
    and organize any relevant developments into a concise daily briefing matching these categories:
    1. Subsea Cables & Digital Chokepoints
    2. Maritime Insurance, Shipping & Red Sea/Hormuz
    3. Semiconductors, Critical Minerals & Tech
    4. Energy Grids, Transformers & Fertilizer/Food Supply
    5. Active Negotiations & U.S. Policy Shifts

    Include clickable source links for every item. Raw articles:
    {raw_articles}
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text

def save_and_notify(briefing_text):
    today = datetime.now().strftime("%Y-%m-%d")
    os.makedirs("archive", exist_ok=True)
    
    # Save permanent daily archive file
    archive_path = f"archive/{today}.md"
    with open(archive_path, "w", encoding="utf-8") as f:
        f.write(f"# Infrastructure & Conflict Briefing — {today}\n\n{briefing_text}\n")
    
    # Build archive list for homepage
    past_files = sorted(os.listdir("archive"), reverse=True)
    archive_links = "\n".join([f"- [{fn.replace('.md', '')}](archive/{fn})" for fn in past_files])
    
    # Update live homepage (index.md)
    with open("index.md", "w", encoding="utf-8") as f:
        f.write(f"# Latest Infrastructure & Conflict Briefing ({today})\n\n{briefing_text}\n\n---\n## Past Briefings Archive\n{archive_links}\n")

    # Send push alert to iPhone
    topic = os.environ.get("NTFY_TOPIC")
    if topic:
        requests.post(
            f"https://ntfy.sh{topic}",
            data=f"Your {today} Infrastructure & Conflict Briefing is ready.".encode("utf-8"),
            headers={
                "Title": "Daily Infrastructure Briefing",
                "Click": "https://shanahunte.github.io/daily-briefing/"
            }
        )

if __name__ == "__main__":
    articles = fetch_relevant_articles()
    briefing = generate_briefing(articles)
    save_and_notify(briefing)
