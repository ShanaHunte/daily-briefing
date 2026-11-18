import feedparser
import os
import re
import time
import csv
import io
import json
import requests
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from google import genai
from google.genai import types

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
    "https://news.google.com" + "/rss/search?q=subsea+cable+OR+undersea+cable+when:14d&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com" + "/rss/search?q=Strait+of+Hormuz+OR+Red+Sea+shipping+insurance+when:14d&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com" + "/rss/search?q=Ukraine+power+grid+transformer+OR+Abu+Dhabi+talks+when:14d&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com" + "/rss/search?q=semiconductor+ASML+OR+gallium+OR+Nvidia+China+when:14d&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com" + "/rss/search?q=global+fertilizer+ammonia+supply+OR+seabed+mining+when:14d&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com" + "/rss/search?q=Congo+M23+tantalum+OR+Ethiopia+Eritrea+Red+Sea+when:14d&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com" + "/rss/search?q=food+shortage+OR+crop+failure+OR+grain+shortage+when:14d&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com" + "/rss/search?q=water+shortage+OR+water+rationing+OR+aquifer+depletion+when:14d&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com" + "/rss/search?q=emergency+preparedness+OR+survival+food+sales+OR+generator+demand+when:14d&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com" + "/rss/search?q=supply+chain+shortage+OR+grocery+shortage+OR+medicine+shortage+when:14d&hl=en-US&gl=US&ceid=US:en",
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
    "https://news.google.com" + "/rss/search?q=Duke+Energy+North+Carolina+rate+OR+LIEAP+energy+assistance+when:14d&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com" + "/rss/search?q=Wake+County+well+water+OR+groundwater+OR+PFAS+testing+when:14d&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com" + "/rss/search?q=Wake+County+trash+OR+convenience+center+OR+property+tax+relief+when:14d&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com" + "/rss/search?q=Raleigh+gas+prices+OR+North+Carolina+gas+tax+OR+I-540+toll+when:14d&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com" + "/rss/search?q=NC+Medicaid+OR+Healthy+Blue+North+Carolina+benefits+when:14d&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com" + "/rss/search?q=FAFSA+special+circumstances+professional+judgment+income+appeal+when:14d&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com" + "/rss/search?q=Wake+County+schools+WCPSS+fee+waiver+OR+Lifeline+phone+discount+when:14d&hl=en-US&gl=US&ceid=US:en",
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


# ==========================================
# LOCAL TAB: DATA SECTIONS (Raleigh / Wake / Durham)
# ==========================================
ET = ZoneInfo("America/New_York")
UA = {"User-Agent": "daily-briefing/1.0 (github.com/ShanaHunte/daily-briefing)"}


def now_et():
    return datetime.now(ET)


def stamp_et():
    return now_et().strftime("%a %b %d, %Y %I:%M %p ET").replace(" 0", " ")


# Local news: Google News RSS queries restricted to local outlets and government pages.
# No keyword filter here; everything returned is local by construction.
def _gn(q):
    return "https://news.google.com" + "/rss/search?q=" + q.replace(" ", "+") + "&hl=en-US&gl=US&ceid=US:en"

LOCAL_NEWS_FEEDS = [
    _gn("site:wral.com (Raleigh OR Wake OR Durham OR Cary OR Apex) when:2d"),
    _gn("site:abc11.com (Raleigh OR Wake OR Durham OR Cary OR Apex) when:2d"),
    _gn("site:cbs17.com (Raleigh OR Wake OR Durham OR Cary OR Apex) when:2d"),
    _gn("site:newsobserver.com (Raleigh OR Wake OR Durham OR Cary OR Apex) when:2d"),
    _gn("site:indyweek.com when:3d"),
    _gn("site:wunc.org when:2d"),
    _gn("site:raleighnc.gov when:7d"),
    _gn("site:wake.gov when:7d"),
    _gn("site:durhamnc.gov when:7d"),
    _gn("site:dconc.gov when:7d"),
    _gn("site:townofcary.org when:7d"),
    _gn("site:apexnc.org when:7d"),
    _gn("Wake County OR Durham County emergency OR closure OR outage OR road closure when:2d"),
    "https://wunc.org" + "/rss.xml",
]

# National Weather Service alerts for Raleigh and Durham points (no key needed).
NWS_POINTS = {"Wake County (Raleigh)": (35.7796, -78.6382), "Durham County (Durham)": (35.9940, -78.8986)}


def fetch_local_news(days_back=2, cap=60):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
    items, seen, health = [], set(), []
    for url in LOCAL_NEWS_FEEDS:
        got = 0
        try:
            feed = feedparser.parse(url, request_headers=UA)
            for e in feed.entries[:25]:
                title = e.get("title", "").strip()
                key = re.sub(r"\W+", "", title.lower())[:80]
                if not title or key in seen:
                    continue
                pub = "Recent"
                if getattr(e, "published_parsed", None):
                    dt = datetime.fromtimestamp(time.mktime(e.published_parsed), tz=timezone.utc)
                    if dt < cutoff:
                        continue
                    pub = dt.astimezone(ET).strftime("%Y-%m-%d")
                seen.add(key)
                items.append(f"- [{pub}] {title} ({e.link})")
                got += 1
        except Exception as ex:
            health.append(f"feed error: {url[:70]} ({ex})")
        health.append(f"{got} items: {url[:90]}")
    print("LOCAL NEWS FEED HEALTH:\n  " + "\n  ".join(health))
    return "\n".join(items[:cap])


def fetch_nws_alerts():
    """Return markdown bullets of active NWS alerts, or a plain 'none' line. Raises on total failure."""
    lines, ok = [], 0
    for name, (lat, lon) in NWS_POINTS.items():
        r = requests.get("https://api.weather.gov/alerts/active", params={"point": f"{lat},{lon}"}, headers=UA, timeout=25)
        r.raise_for_status()
        ok += 1
        for f in r.json().get("features", []):
            p = f.get("properties", {})
            ends = p.get("ends") or p.get("expires") or ""
            try:
                ends = datetime.fromisoformat(ends).astimezone(ET).strftime("%a %b %d %I:%M %p ET").replace(" 0", " ")
            except Exception:
                pass
            lines.append(f"- **{p.get('event','Alert')}**, {name}: {p.get('headline','').strip()} (until {ends}). [National Weather Service](https://www.weather.gov/rah/)")
    if not ok:
        raise RuntimeError("no NWS response")
    return "\n".join(dict.fromkeys(lines)) if lines else "- No active National Weather Service alerts for Wake or Durham County right now."


def local_news_section():
    articles = fetch_local_news()
    alerts = ""
    try:
        alerts = fetch_nws_alerts()
    except Exception as ex:
        alerts = f"- Weather alerts could not be retrieved this run ({type(ex).__name__}). Check [weather.gov/rah](https://www.weather.gov/rah/) and [AlertWake](https://www.wake.gov/) directly."
    out = f"### Local alerts and emergency notices\n\nChecked {stamp_et()}.\n\n{alerts}\n\n"
    out += ("**Other emergency channels:** Wake County residents can sign up for AlertWake through [wake.gov](https://www.wake.gov/); "
            "Durham County has Alert Durham through [dconc.gov](https://www.dconc.gov/). Check the county site for current sign-up links.\n\n")
    if not articles:
        out += "### Local news highlights\n\nNo local headlines came back this run. The feed health is in the workflow log.\n"
        return out
    prompt = f"""
    You are a local news editor for Raleigh, Wake County (including Cary, Apex and unincorporated areas) and Durham County, NC.
    Today is {now_et().strftime('%A, %B %d, %Y')}. From ONLY the headlines below, write the most useful items for a household
    in this area. Prioritize: emergencies, closures, outages, road and transit changes, utility or tax changes, city and county
    announcements, public safety, schools, and anything with a deadline. Skip national stories, sports, and duplicates.
    Format: a bulleted list of 8 to 12 bullets, newest and most important first. Each bullet: **short label**, one plain sentence,
    the date, and a [Source name](url) link copied exactly from the headline list. Do not add facts that are not in the headlines.
    If fewer than 8 items qualify, list fewer. Write plainly, no filler, no headings.
    Headlines:
    {articles}
    """
    try:
        body = call_gemini(prompt)
    except Exception as ex:
        body = f"- Summary unavailable this run ({type(ex).__name__}). Raw headlines:\n\n{articles}"
    return out + f"### Local news highlights\n\n{body.strip()}\n"


# ---- Housing: Zillow Home Value Index (monthly, public CSV) ----
ZHVI_BASE = "https://files.zillowstatic.com/research/public_csvs/zhvi/"
ZHVI_ZIP = ZHVI_BASE + "Zip_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv"
ZHVI_COUNTY = ZHVI_BASE + "County_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv"
ZHVI_CITY = ZHVI_BASE + "City_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv"

ZIP_GROUPS = [
    ("Raleigh", ["27601", "27603", "27604", "27605", "27606", "27607", "27608", "27609", "27610", "27612", "27613", "27614", "27615", "27616", "27617"]),
    ("Durham", ["27701", "27703", "27704", "27705", "27707", "27712", "27713"]),
    ("Cary", ["27511", "27513", "27518", "27519"]),
    ("Apex", ["27502", "27523", "27539"]),
    ("Wake County, mostly outside city limits (proxy zips)", ["27562", "27592"]),
]


ALL_ZIPS = set(z for _, zs in ZIP_GROUPS for z in zs)


def _stream_rows(url, keep):
    with requests.get(url, stream=True, headers=UA, timeout=120) as r:
        r.raise_for_status()
        lines = (ln.decode("utf-8", "ignore") for ln in r.iter_lines())
        reader = csv.DictReader(lines)
        cols = reader.fieldnames
        rows = [row for row in reader if keep(row)]
    return cols, rows


def _latest_and_yearago(row, cols):
    dates = [c for c in cols if re.match(r"\d{4}-\d{2}-\d{2}$", c)]
    last = None
    for c in reversed(dates):
        if row.get(c):
            last = c
            break
    if not last:
        return None
    idx = dates.index(last)
    ya = row.get(dates[idx - 12]) if idx >= 12 else None
    cur = float(row[last])
    chg = (cur / float(ya) - 1) * 100 if ya else None
    return last, cur, chg


def housing_rows_from_csv(zip_cols, zip_rows, cty_cols, cty_rows):
    out = []
    zmap = {r["RegionName"]: r for r in zip_rows}
    for group, zips in ZIP_GROUPS:
        for z in zips:
            r = zmap.get(z)
            res = _latest_and_yearago(r, zip_cols) if r else None
            if res:
                out.append((group, z, res))
    cty = []
    for r in cty_rows:
        if r.get("RegionName") in ("Wake County", "Durham County") and r.get("StateName") == "NC":
            res = _latest_and_yearago(r, cty_cols)
            if res:
                cty.append((r["RegionName"], res))
    return out, cty


def fmt_money(v):
    return "${:,.0f}".format(v)


def render_housing(zip_out, cty_out):
    month = None
    lines = ["| Area | Typical home value | vs. 1 year ago |", "| --- | ---: | ---: |"]
    for name, (d, cur, chg) in cty_out:
        month = month or d
        lines.append(f"| **{name} (all)** | {fmt_money(cur)} | {chg:+.1f}% |" if chg is not None else f"| **{name} (all)** | {fmt_money(cur)} | n/a |")
    for group, z, (d, cur, chg) in zip_out:
        month = month or d
        c = f"{chg:+.1f}%" if chg is not None else "n/a"
        lines.append(f"| {group}, {z} | {fmt_money(cur)} | {c} |")
    return month, "\n".join(lines)


def housing_section():
    try:
        zc, zr = _stream_rows(ZHVI_ZIP, lambda r: r.get("RegionName") in ALL_ZIPS)
        cc, cr = _stream_rows(ZHVI_COUNTY, lambda r: r.get("StateName") == "NC" and r.get("RegionName") in ("Wake County", "Durham County"))
        zip_out, cty_out = housing_rows_from_csv(zc, zr, cc, cr)
        if not zip_out and not cty_out:
            raise RuntimeError("no matching rows")
        month, table = render_housing(zip_out, cty_out)
        note = ("Zillow Home Value Index, typical value of single-family homes and condos in the middle price tier. "
                f"Zillow publishes this monthly, so these numbers change once a month; latest data point is {month}. "
                "Unincorporated Wake and Durham County have no zip codes of their own, so the county rows cover everything in the county "
                "and the 27562 and 27592 rows are a rough proxy for rural Wake. A blank zip means Zillow has no figure for it.")
        return f"### Housing market: typical home values\n\nChecked {stamp_et()}.\n\n{table}\n\n{note} Source: [Zillow Research data](https://www.zillow.com/research/data/).\n"
    except Exception as ex:
        print("HOUSING FAILED:", repr(ex))
        return grounded_section(
            "Housing market: typical home values",
            "Find the latest typical home value / median sale price and 1-year change for Raleigh, Durham, Cary, Apex, "
            "Wake County and Durham County NC, from Zillow, Redfin, Realtor.com or the Triangle MLS / NC Realtors market reports. "
            "Give each figure with the source month. Zip-level values for Raleigh and Durham zip codes if available. "
            "If a figure is not found, say 'not found'. Do not estimate.",
            prefix_note="The Zillow data file could not be read this run, so this section is a search summary instead.")


# ---- Groceries: BLS average prices (monthly, national) ----
BLS_SERIES = {
    "APU0000708111": "Eggs, grade A large, per dozen",
    "APU0000709112": "Milk, whole, per gallon",
    "APU0000702111": "Bread, white pan, per pound",
    "APU0000711211": "Bananas, per pound",
    "APU0000712311": "Tomatoes, field grown, per pound",
}


def bls_prices():
    payload = {"seriesid": list(BLS_SERIES), "startyear": str(now_et().year - 1), "endyear": str(now_et().year)}
    key = os.environ.get("BLS_API_KEY", "").strip()
    url = "https://api.bls.gov/publicAPI/v2/timeseries/data/" if key else "https://api.bls.gov/publicAPI/v1/timeseries/data/"
    if key:
        payload["registrationkey"] = key
    r = requests.post(url, json=payload, headers=UA, timeout=40)
    r.raise_for_status()
    rows = []
    for s in r.json()["Results"]["series"]:
        pts = [p for p in s["data"] if p["period"].startswith("M") and p["value"] not in ("-", "")]
        if not pts:
            continue
        cur = pts[0]
        yago = next((p for p in pts if p["year"] == str(int(cur["year"]) - 1) and p["period"] == cur["period"]), None)
        chg = f"{(float(cur['value'])/float(yago['value'])-1)*100:+.1f}%" if yago else "n/a"
        rows.append(f"| {BLS_SERIES[s['seriesID']]} | ${float(cur['value']):.2f} | {cur['periodName']} {cur['year']} | {chg} |")
    if not rows:
        raise RuntimeError("no BLS rows")
    return "| Item | U.S. city average | Month | vs. 1 year ago |\n| --- | ---: | --- | ---: |\n" + "\n".join(rows)


def grocery_section():
    try:
        table = bls_prices()
        head = (f"Checked {stamp_et()}.\n\n**Average prices (national, monthly).** The Bureau of Labor Statistics does not publish "
                f"Raleigh or Durham prices for these items, so this is the U.S. city average, updated once a month.\n\n{table}\n\n"
                "Source: [BLS average price data](https://www.bls.gov/regions/mid-atlantic/data/averageretailfoodandenergyprices_usandmidwest_table.htm).\n\n")
    except Exception as ex:
        print("BLS FAILED:", repr(ex))
        head = "Average price data from BLS could not be read this run.\n\n"
    deals = grounded_section(
        "x",
        "Find this week's best grocery prices in Raleigh, Cary, Apex and Durham NC for: eggs (dozen), milk (gallon), bread (loaf), "
        "bottled water (24 pack or case), and fresh produce staples (bananas, apples, potatoes, onions, greens). Use current weekly ads, "
        "store sale pages and coupon pages for Aldi, Lidl, Food Lion, Harris Teeter, Walmart, Publix, Kroger-type chains, Costco/Sam's if listed, "
        "and Compare Foods or Carlie C's if they publish ads. For each item name the single best store this week, the sale price, the sale "
        "dates, and give a link to that store's ad or coupon page copied from your search results. Say 'no current ad found' for any item "
        "you cannot confirm. Do not guess prices. Keep it to a short list of 5 to 7 bullets.",
        headed=False)
    return f"### Groceries: average prices and this week's best staples\n\n{head}**Best place to buy this week**\n\n{deals}\n"


# ---- Gemini with Google Search grounding ----
MODEL_ATTEMPTS = [
    ("v1beta", "gemini-3.0-flash"), ("v1beta", "gemini-3-flash-preview"), ("v1beta", "gemini-2.5-flash"),
    ("v1beta", "gemini-2.5-flash-lite"), ("v1beta", "gemini-2.0-flash"), ("v1beta", "gemini-2.5-pro"),
]


def call_gemini_grounded(prompt):
    api_key = os.environ["GEMINI_API_KEY"].strip()
    last = None
    for api_ver, model_name in MODEL_ATTEMPTS:
        try:
            client = genai.Client(api_key=api_key, http_options={"api_version": api_ver})
            cfg = types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearch())], temperature=0.2)
            resp = client.models.generate_content(model=model_name, contents=prompt, config=cfg)
            if not (resp and resp.text):
                continue
            sources = []
            try:
                for ch in resp.candidates[0].grounding_metadata.grounding_chunks or []:
                    if ch.web and ch.web.uri:
                        sources.append((ch.web.title or "source", ch.web.uri))
            except Exception:
                pass
            return resp.text, sources
        except Exception as e:
            last = e
            continue
    raise RuntimeError(f"All grounded Gemini attempts failed. Last error: {last}")


def grounded_section(title, task, prefix_note="", headed=True):
    today = now_et().strftime("%A, %B %d, %Y")
    prompt = f"""
    You are researching for a daily household briefing for Raleigh, Wake County (including Cary, Apex, and unincorporated areas)
    and Durham County, North Carolina. Today is {today}. Use Google Search to find CURRENT information.
    Rules: every fact needs a date or 'as of' time and a [Source name](url) markdown link. Use only URLs that came from your
    search results. If you cannot find something, say 'not found today' for that item. Never estimate or invent numbers, dates,
    names or links. Be concise and plain; no filler; no headings; bullets or short paragraphs only.

    Task: {task}
    """
    try:
        text, sources = call_gemini_grounded(prompt)
    except Exception as ex:
        print("GROUNDED FAILED:", title, repr(ex))
        body = f"This section could not be retrieved this run ({type(ex).__name__}). It will retry on the next daily run."
        return (f"### {title}\n\n{body}\n" if headed else body)
    text = re.sub(r"(?m)^#{1,6}\s+(.*)$", r"**\1**", text.strip())
    if not re.search(r"https?://", text):
        text += "\n\n(No source links came back with this answer, so treat it as unconfirmed.)"
    seen, src_lines = set(), []
    for t, u in sources:
        if u not in seen:
            seen.add(u)
            src_lines.append(f"[{t}]({u})")
    srcs = ("\n\n<small>Pages the search used: " + " · ".join(src_lines[:8]) + "</small>") if src_lines else ""
    note = (prefix_note + "\n\n") if prefix_note else ""
    body = f"Checked {stamp_et()}.\n\n{note}{text}{srcs}"
    return (f"### {title}\n\n{body}\n" if headed else text + srcs)


def gas_section():
    return grounded_section(
        "Gas prices: Raleigh, Durham, Cary and Apex",
        "Find (1) the current AAA average price for regular gas in North Carolina and the Raleigh and Durham metro if AAA lists them, "
        "with AAA's update date; and (2) the THREE least expensive stations for regular gas across Raleigh, Durham, Cary and Apex "
        "right now, from GasBuddy or similar. For each of the three give: station name, street address, price per gallon, and the "
        "time that price was reported or updated. Crowd-sourced station prices go stale within hours, so state each one's report time "
        "and say if it is older than 24 hours. If station-level prices are not available, say so and give the area averages only.")


def dates_section():
    return grounded_section(
        "Important dates: Wake and Durham County",
        "List dated, upcoming items for the next 45 days: (a) meetings of the Wake County Board of Commissioners (regular meetings are "
        "on the first and third Mondays with work sessions on the second Monday), Raleigh City Council, Durham County Commissioners, "
        "Durham City Council, Cary Town Council, Apex Town Council, and the school boards for Wake County and Durham Public Schools; "
        "(b) public hearings, community input sessions and public interest meetings on rezonings, budgets, transit, roads or housing; "
        "(c) elections and voting dates from the NC State Board of Elections and the Wake and Durham boards of elections, including "
        "registration deadlines, early voting and any special or municipal elections; (d) civic and government deadlines such as "
        "property tax deadlines, permit or comment deadlines, and county office closures or holiday schedule changes. "
        "Group by date, soonest first, with time, place and link for each. Mention the next 12 items at most.")


def arts_section():
    return grounded_section(
        "Arts council: grants, events and featured artists",
        "Report from the United Arts Council of Raleigh and Wake County, the Durham Arts Council, the Town of Cary and Apex arts "
        "programs, and the NC Arts Council: (1) open grants and calls for artists with deadline, amount if stated, and link; "
        "(2) upcoming arts events in the next two weeks; (3) one or two featured artists or exhibitions currently promoted by these "
        "organizations. Put the deadline first on each grant. Say 'not found today' for any part you cannot confirm.")


def health_section():
    return grounded_section(
        "Health and human services updates",
        "Find current updates from Wake County Health and Human Services, Durham County Department of Public Health and Social "
        "Services, and the NC Department of Health and Human Services that affect residents: Medicaid and NC Health Choice changes, "
        "SNAP/food assistance (including any funding or benefit disruptions), LIEAP and energy assistance windows, WIC, vaccine and "
        "flu/COVID clinics, public health alerts or advisories, food pantry or free clinic announcements, and behavioral health or "
        "crisis resources. Include effective dates and deadlines. Newest first, up to 8 bullets.")


def jobs_section():
    return grounded_section(
        "Jobs: top hiring industries and employers",
        "Describe the Raleigh-Durham-Cary job market: the top hiring industries right now and the top employers with a link to their "
        "careers page or a current openings count where shown. Use NC Commerce labor market data, BLS, NCWorks, and large employer "
        "career sites. Cover at least: health care (Duke Health, WakeMed, UNC Rex), universities (Duke, NC State, UNC), state and "
        "local government, technology and life sciences (including any recent large announced hires or layoffs), and retail or "
        "logistics. Give the latest unemployment rate for the Raleigh and Durham-Chapel Hill metros with the month. Flag any recent "
        "layoffs or WARN notices in Wake or Durham County.")


def build_local_sections():
    parts = []
    for fn in (local_news_section, housing_section, gas_section, dates_section, arts_section, grocery_section, health_section, jobs_section):
        try:
            parts.append(fn())
        except Exception as ex:
            print("SECTION FAILED:", fn.__name__, repr(ex))
            parts.append(f"### {fn.__name__.replace('_section','').title()}\n\nThis section failed this run ({type(ex).__name__}).\n")
    return "\n\n".join(parts)


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
            "Updated " + stamp_et() + " · news from the last 48 hours", label,
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
    g_articles = fetch_articles(GLOBAL_FEEDS, GLOBAL_KEYWORDS, days_back=2)
    g_brief = generate_global_briefing(g_articles, is_backfill=False)
    local_sections = build_local_sections()
    l_articles = fetch_articles(LOCAL_FEEDS, LOCAL_KEYWORDS, days_back=2)
    try:
        policy = generate_local_briefing(l_articles, is_backfill=False)
    except Exception as ex:
        policy = f"Unavailable this run ({type(ex).__name__})."
    if policy.strip().startswith("No major"):
        policy = "Nothing new matched the cost-of-living filters in the last 48 hours."
    l_brief = local_sections + "\n\n### Cost of living watch: utilities, benefits, financial aid\n\n" + policy
    save_and_notify(g_brief, l_brief, datetime.now(ET).strftime("%Y-%m-%d"))
