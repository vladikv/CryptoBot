import logging
import feedparser
import requests

logger = logging.getLogger(__name__)

RSS_FEEDS = [
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://cointelegraph.com/rss",
    "https://decrypt.co/feed",
]


def get_news(filter_coin: str = None, limit: int = 8) -> list[dict]:
    """Retrieves news from RSS feeds, optionally filters by coin."""
    articles = []

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:10]:
                title = entry.get("title", "").strip()
                link  = entry.get("link", "").strip()
                if not title or not link:
                    continue
                if filter_coin:
                    if filter_coin.lower() not in title.lower():
                        continue
                articles.append({"title": title, "link": link})
        except Exception as e:
            logger.error(f"RSS error {feed_url}: {e}")

    # Removes duplicates by title
    seen   = set()
    unique = []
    for a in articles:
        if a["title"] not in seen:
            seen.add(a["title"])
            unique.append(a)

    return unique[:limit]