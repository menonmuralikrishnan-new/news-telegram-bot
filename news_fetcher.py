import json
import feedparser
import requests

from datetime import datetime, timedelta, timezone
from dateutil import parser as date_parser
from bs4 import BeautifulSoup

from news_filter import remove_duplicates
from news_ranker import rank_articles


SOURCES_FILE = "sources.json"

# Fetch the last 72 hours.
HOURS = 72

# Ollama model
OLLAMA_MODEL = "llama3.2:3b"
OLLAMA_URL = "http://localhost:11434/api/generate"


def clean_text(text):
    """Remove HTML and clean whitespace."""

    if not text:
        return ""

    soup = BeautifulSoup(text, "html.parser")

    return " ".join(
        soup.get_text(" ", strip=True).split()
    )


def parse_date(value):
    """Convert RSS date into UTC datetime."""

    if not value:
        return None

    try:
        dt = date_parser.parse(value)

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt.astimezone(timezone.utc)

    except Exception:
        return None


# ============================================================
# OLLAMA
# ============================================================

def summarize_with_ollama(title, article_summary):
    """
    Generate a short factual summary.

    If RSS article information is available, summarize it.
    If not, create a cautious headline-based brief.
    """

    if article_summary.strip():

        prompt = f"""
You are a concise news summarizer.

Create a short factual summary of the news item below.

Rules:
- Use ONLY the information provided.
- Do not invent facts.
- Do not add opinions.
- Keep it to 1-2 sentences.
- Around 30-50 words.
- Mention important people, organizations, events,
  results or numbers when provided.
- Return ONLY the summary.

HEADLINE:
{title}

RSS ARTICLE INFORMATION:
{article_summary}
"""

    else:

        prompt = f"""
You are a concise news briefing assistant.

The RSS feed provides only the headline, not the full article.

Create a SHORT headline-based briefing from the headline.

Rules:
- Do NOT pretend you read the full article.
- Do NOT invent details.
- Do NOT add facts that are not contained in the headline.
- Explain what the headline is reporting.
- Keep it to ONE sentence.
- Around 20-30 words.
- Return ONLY the briefing.

HEADLINE:
{title}
"""

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2
        }
    }

    try:

        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=120
        )

        response.raise_for_status()

        result = response.json()

        summary = result.get(
            "response",
            ""
        ).strip()

        if summary:
            return summary

    except requests.exceptions.ConnectionError:

        print()
        print("ERROR: Ollama is not running.")
        print("Start it with: ollama serve")
        print()

    except Exception as e:

        print(
            f"Ollama error: {e}"
        )

    return "Summary unavailable."



# ============================================================
# RSS FETCHING
# ============================================================

def fetch_feed(source_name, url, category):
    """Fetch one RSS feed."""

    print(f"    Fetching: {source_name}")

    try:

        feed = feedparser.parse(url)

    except Exception as e:

        print(f"    ERROR: {e}")
        return []

    if not feed.entries:

        print("    No entries found.")
        return []

    cutoff = (
        datetime.now(timezone.utc)
        - timedelta(hours=HOURS)
    )

    articles = []

    for entry in feed.entries:

        # ----------------------------------------------------
        # DATE
        # ----------------------------------------------------

        published = None

        for field in [
            "published",
            "updated",
            "created"
        ]:

            if field in entry:

                published = parse_date(
                    entry.get(field)
                )

                if published:
                    break

        if published and published < cutoff:
            continue

        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        title = clean_text(
            entry.get("title", "")
        )

        if not title:
            continue

        # ----------------------------------------------------
        # LINK
        # ----------------------------------------------------

        link = entry.get("link", "")

        if not link:
            continue

        # ----------------------------------------------------
        # RSS SUMMARY
        # ----------------------------------------------------

        summary = clean_text(
            entry.get("summary", "")
            or entry.get("description", "")
        )

        # ----------------------------------------------------
        # IGNORE VIDEO ARTICLES
        # ----------------------------------------------------

        if "/videos/" in link.lower():
            continue

        # ----------------------------------------------------
        # ARTICLE
        # ----------------------------------------------------

        article = {

            "title": title,

            "link": link,

            "source": "The Indian Express",

            "feed": source_name,

            # IMPORTANT:
            # Python determines the category.
            # Llama does NOT change it.
            "category": category,

            "summary": summary,

            "published": (
                published.isoformat()
                if published
                else ""
            ),

            # Ollama summary will be added later.
            "llm_summary": ""
        }

        articles.append(article)

    print(
        f"    Found: {len(articles)}"
    )

    return articles


# ============================================================
# FETCH ALL SOURCES
# ============================================================

def fetch_all_sources():

    with open(
        SOURCES_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        config = json.load(f)

    all_articles = []

    for category, sources in config["sources"].items():

        print()
        print("=" * 60)
        print(category)
        print("=" * 60)

        for source_name, url in sources.items():

            articles = fetch_feed(
                source_name,
                url,
                category
            )

            all_articles.extend(
                articles
            )

    return all_articles


# ============================================================
# PRINT NEWS + AI SUMMARIES
# ============================================================

def print_news(articles):

    categories = [

        "AI & Technology",

        "India & Politics",

        "World & Geopolitics",

        "Business & Economy",

        "Stock Market",

        "Cricket",

        "Football",

        "Malayalam Cinema"
    ]

    print()
    print("=" * 75)
    print("                    NEWS + AI SUMMARIES")
    print("=" * 75)

    for category in categories:

        category_articles = [

            article
            for article in articles
            if article["category"] == category
        ]

        print()
        print()
        print("┌" + "─" * 73 + "┐")
        print(
            f"│ {category:<71} │"
        )
        print(
            "└" + "─" * 73 + "┘"
        )

        if not category_articles:

            print("  NO ARTICLES FOUND")
            continue

        # Newest first
        category_articles.sort(
            key=lambda x: x.get(
                "published",
                ""
            ),
            reverse=True
        )

        for i, article in enumerate(
            category_articles,
            start=1
        ):

            print()
            print(
                f"  [{i}] {article['title']}"
            )

            print(
                f"      Feed: {article['feed']}"
            )

            if article.get("published"):

                print(
                    f"      Published: "
                    f"{article['published']}"
                )

            print()
            print(
                "      🤖 AI Summary:"
            )

            print(
                f"      {article['llm_summary']}"
            )

            print()
            print(
                f"      Link: {article['link']}"
            )

            print(
                "      " + "-" * 65
            )

    print()
    print("=" * 75)
    print("                       END OF NEWS")
    print("=" * 75)


# ============================================================
# CATEGORY COUNTS
# ============================================================

def print_category_counts(articles):

    categories = [

        "AI & Technology",

        "India & Politics",

        "World & Geopolitics",

        "Business & Economy",

        "Stock Market",

        "Cricket",

        "Football",

        "Malayalam Cinema"
    ]

    print()
    print("=" * 60)
    print("CATEGORY COUNTS")
    print("=" * 60)

    for category in categories:

        count = sum(

            1
            for article in articles
            if article["category"] == category

        )

        print(
            f"{category}: {count}"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 50)
    print("       PERSONAL NEWS BOT")
    print("       THE INDIAN EXPRESS")
    print("       + LLAMA 3.2")
    print("=" * 50)
    print()

    # --------------------------------------------------------
    # FETCH
    # --------------------------------------------------------

    articles = fetch_all_sources()

    print()
    print(
        f"Total fetched: {len(articles)}"
    )

    # --------------------------------------------------------
    # REMOVE DUPLICATES
    # --------------------------------------------------------

    articles = remove_duplicates(
        articles
    )

    print(
        f"After duplicate removal: "
        f"{len(articles)}"
    )

    # --------------------------------------------------------
    # INITIAL RANKING
    # --------------------------------------------------------

    articles = rank_articles(
        articles
    )

    print(
        f"After initial ranking: "
        f"{len(articles)}"
    )

    # --------------------------------------------------------
    # CATEGORY COUNTS
    # --------------------------------------------------------

    print_category_counts(
        articles
    )

    # --------------------------------------------------------
    # GENERATE AI SUMMARIES
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("GENERATING LLAMA SUMMARIES")
    print("=" * 60)

    for i, article in enumerate(
        articles,
        start=1
    ):

        print()
        print(
            f"[{i}/{len(articles)}] "
            f"{article['title']}"
        )

        article["llm_summary"] = (
            summarize_with_ollama(
                article["title"],
                article["summary"]
            )
        )

        print(
            f"    → {article['llm_summary']}"
        )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    with open(
        "news_articles.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            articles,
            f,
            indent=4,
            ensure_ascii=False
        )

    # --------------------------------------------------------
    # SHOW EVERYTHING
    # --------------------------------------------------------

    print_news(
        articles
    )

    print()
    print(
        "Saved to news_articles.json"
    )


if __name__ == "__main__":
    main()