import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")

# RSS feeds organized by category
# For team-specific categories, also define KEYWORDS to filter articles
RSS_FEEDS = {
    "world news": [
        "http://feeds.bbci.co.uk/news/rss.xml",
        "https://feeds.reuters.com/reuters/topNews",
        "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        "https://www.theguardian.com/world/rss",
        "https://feeds.npr.org/1004/rss.xml",
    ],
    "nba": [
        "https://www.espn.com/espn/rss/nba/news",
        "https://bleacherreport.com/nba/feed",
        "https://www.cbssports.com/rss/headlines/nba/",
        "https://sports.yahoo.com/nba/rss.xml",
        "https://hoopshype.com/feed/",
    ],
    "timberwolves": [
        "https://www.espn.com/espn/rss/nba/news",
        "https://bleacherreport.com/nba/feed",
        "https://www.cbssports.com/rss/headlines/nba/",
        "https://sports.yahoo.com/nba/rss.xml",
        "https://hoopshype.com/feed/",
        "https://www.startribune.com/sports/timberwolves/rss",
    ],
    "arsenal": [
        "https://feeds.bbci.co.uk/sport/football/rss.xml",
        "https://www.theguardian.com/football/arsenal/rss",
        "https://www.espn.com/espn/rss/soccer/news",
        "https://www.skysports.com/rss/12040",
        "https://www.football.london/arsenal-fc/rss.xml",
        "https://arseblog.com/feed/",
    ],
    "soccer": [
        "https://feeds.bbci.co.uk/sport/football/rss.xml",
        "https://www.theguardian.com/football/rss",
        "https://www.espn.com/espn/rss/soccer/news",
        "https://www.skysports.com/rss/12040",
    ],
    "ai": [
        "https://techcrunch.com/category/artificial-intelligence/feed/",
        "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
        "https://www.wired.com/feed/tag/artificial-intelligence/rss",
        "https://venturebeat.com/category/ai/feed/",
        "https://www.technologyreview.com/feed/",
        "https://artificialintelligence-news.com/feed/",
    ],
    "tech": [
        "https://techcrunch.com/feed/",
        "https://www.theverge.com/rss/index.xml",
        "https://www.wired.com/feed/rss",
        "https://venturebeat.com/feed/",
        "https://arstechnica.com/feed/",
    ],
    "iran": [
        "https://www.aljazeera.com/xml/rss/all.xml",
        "https://feeds.bbci.co.uk/news/world/middle_east/rss.xml",
        "https://feeds.reuters.com/reuters/worldNews",
        "https://rss.nytimes.com/services/xml/rss/nyt/MiddleEast.xml",
        "https://www.theguardian.com/world/middleeast/rss",
        "https://feeds.npr.org/1004/rss.xml",
        "https://www.ft.com/world/mideast?format=rss",
    ],
    "middle east": [
        "https://www.aljazeera.com/xml/rss/all.xml",
        "https://feeds.bbci.co.uk/news/world/middle_east/rss.xml",
        "https://feeds.reuters.com/reuters/worldNews",
        "https://rss.nytimes.com/services/xml/rss/nyt/MiddleEast.xml",
        "https://www.theguardian.com/world/middleeast/rss",
    ],
    "finance": [
        "https://feeds.marketwatch.com/marketwatch/topstories/",
        "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "https://feeds.bloomberg.com/markets/news.rss",
        "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
        "https://www.theguardian.com/money/rss",
    ],
    "politics": [
        "https://feeds.npr.org/1001/rss.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml",
        "https://www.theguardian.com/politics/rss",
        "https://feeds.bbci.co.uk/news/politics/rss.xml",
    ],
}

# Keywords to filter articles for team/topic-specific categories
# Only articles containing at least one keyword will be kept
CATEGORY_KEYWORDS = {
    "timberwolves": ["timberwolves", "minnesota", "wolves", "ant", "anthony edwards", "rudy gobert", "jaden mcdaniels"],
    "arsenal": ["arsenal", "gunners", "arteta", "emirates", "saka", "odegaard", "havertz", "martinelli"],
    "iran": ["iran", "iranian", "tehran", "khamenei", "bushehr", "irgc", "persian"],
    "middle east": ["iran", "israel", "gaza", "hamas", "hezbollah", "middle east", "syria", "lebanon", "iraq"],
}
