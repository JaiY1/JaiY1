import feedparser
import requests
from bs4 import BeautifulSoup
from database import save_article
from config import RSS_FEEDS, CATEGORY_KEYWORDS
from datetime import datetime
import time


def scrape_rss(category: str, urls: list[str]) -> list[dict]:
    articles = []
    for url in urls:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:  # max 10 per feed
                excerpt = ""
                if hasattr(entry, "summary"):
                    soup = BeautifulSoup(entry.summary, "html.parser")
                    excerpt = soup.get_text()[:500]

                published = None
                if hasattr(entry, "published"):
                    try:
                        published = entry.published
                    except Exception:
                        published = datetime.now().isoformat()

                # Try to extract thumbnail
                image_url = None
                if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
                    image_url = entry.media_thumbnail[0].get("url")
                elif hasattr(entry, "media_content") and entry.media_content:
                    image_url = entry.media_content[0].get("url")
                elif hasattr(entry, "enclosures") and entry.enclosures:
                    for enc in entry.enclosures:
                        if enc.get("type", "").startswith("image"):
                            image_url = enc.get("url")
                            break

                articles.append({
                    "url": entry.get("link", ""),
                    "title": entry.get("title", ""),
                    "source": feed.feed.get("title", url),
                    "category": category,
                    "excerpt": excerpt,
                    "summary": None,
                    "published_at": published,
                    "image_url": image_url,
                })
            time.sleep(0.3)  # be polite to servers
        except Exception as e:
            print(f"  Failed to scrape {url}: {e}")
    return articles


def scrape_all(interests: list[str]) -> list[dict]:
    """Scrape RSS feeds for a list of interest categories."""
    all_articles = []
    seen_urls = set()

    for interest in interests:
        interest_lower = interest.lower()
        # Find matching feed categories
        matched = [
            (cat, urls) for cat, urls in RSS_FEEDS.items()
            if interest_lower in cat or cat in interest_lower
        ]
        if not matched:
            # Default to world news if no match
            matched = [("world news", RSS_FEEDS["world news"])]

        for cat, urls in matched:
            print(f"  Scraping {cat}...")
            articles = scrape_rss(cat, urls)
            keywords = CATEGORY_KEYWORDS.get(cat, [])
            for a in articles:
                if not a["url"] or a["url"] in seen_urls:
                    continue
                # Apply keyword filter for team/topic-specific categories
                if keywords:
                    text = (a["title"] + " " + a.get("excerpt", "")).lower()
                    if not any(kw.lower() in text for kw in keywords):
                        continue
                seen_urls.add(a["url"])
                all_articles.append(a)

    return all_articles


def save_articles(articles: list[dict]) -> list[int]:
    """Save articles to DB, return list of new article IDs."""
    ids = []
    for article in articles:
        article_id = save_article(article)
        if article_id:
            ids.append(article_id)
    print(f"  Saved {len(ids)} new articles.")
    return ids
