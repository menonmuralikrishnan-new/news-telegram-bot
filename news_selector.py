import json
import requests
from datetime import datetime

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"

INPUT_FILE = "news_articles.json"
OUTPUT_FILE = "final_news.json"

CATEGORIES = [
    "AI & Technology",
    "India & Politics",
    "World & Geopolitics",
    "Business & Economy",
    "Stock Market",
    "Cricket",
    "Football",
    "Malayalam Cinema"
]


def score_article(article):

    title = article.get("title", "")
    summary = article.get("llm_summary", "")
    category = article.get("category", "")

    prompt = f"""
You are selecting stories for a high-quality morning news briefing.

Evaluate this news story.

CATEGORY:
{category}

HEADLINE:
{title}

SUMMARY:
{summary}

Give an importance score from 1 to 5.

5 = major national/international development,
    major political event, major market event,
    major technology development, major sports event,
    or major Malayalam cinema development.

4 = clearly important and useful for a morning briefing.

3 = moderately useful.

2 = minor story.

1 = trivial, promotional, celebrity gossip,
    routine update, or low-value story.

Return ONLY a single number:
1
2
3
4
or
5
"""

    try:

        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0
                }
            },
            timeout=120
        )

        response.raise_for_status()

        text = response.json().get(
            "response",
            ""
        ).strip()

        for value in ["5", "4", "3", "2", "1"]:

            if value in text:
                return int(value)

    except Exception as e:

        print(
            f"Scoring error: {e}"
        )

    return 3


def select_articles(articles):

    print()
    print("=" * 60)
    print("SCORING NEWS WITH LLAMA")
    print("=" * 60)

    # ---------------------------------------------------------
    # Score every article
    # ---------------------------------------------------------

    for i, article in enumerate(
        articles,
        start=1
    ):

        print(
            f"[{i}/{len(articles)}] "
            f"{article['title']}"
        )

        article["importance"] = score_article(
            article
        )

        print(
            f"    Importance: "
            f"{article['importance']}/5"
        )

    # ---------------------------------------------------------
    # Group by category
    # ---------------------------------------------------------

    by_category = {}

    for category in CATEGORIES:

        by_category[category] = []

    for article in articles:

        category = article.get(
            "category"
        )

        if category in by_category:

            by_category[category].append(
                article
            )

    # ---------------------------------------------------------
    # Sort each category
    # ---------------------------------------------------------

    for category in CATEGORIES:

        by_category[category].sort(
            key=lambda x: (
                x.get("importance", 0),
                x.get("published", "")
            ),
            reverse=True
        )

    # ---------------------------------------------------------
    # FIRST: guarantee one per category
    # ---------------------------------------------------------

    selected = []

    for category in CATEGORIES:

        stories = by_category[category]

        if stories:

            selected.append(
                stories[0]
            )

    # ---------------------------------------------------------
    # TARGET: 14-16 stories
    #
    # We start at 14.
    # If there are enough good stories,
    # we go up to 16.
    # ---------------------------------------------------------

    remaining = []

    selected_ids = {
        id(article)
        for article in selected
    }

    for category in CATEGORIES:

        for article in by_category[category]:

            if id(article) not in selected_ids:

                remaining.append(article)

    remaining.sort(
        key=lambda x: (
            x.get("importance", 0),
            x.get("published", "")
        ),
        reverse=True
    )

    # Prefer stories scoring >= 3.
    good_remaining = [
        article
        for article in remaining
        if article.get("importance", 0) >= 3
    ]

    # Add enough to reach 14.
    for article in good_remaining:

        if len(selected) >= 14:
            break

        selected.append(article)

    # Add up to 16 if there are still
    # genuinely useful stories.
    for article in good_remaining:

        if len(selected) >= 16:
            break

        if article not in selected:

            selected.append(article)

    # ---------------------------------------------------------
    # FINAL SORT
    # ---------------------------------------------------------

    category_order = {
        category: i
        for i, category in enumerate(
            CATEGORIES
        )
    }

    selected.sort(
        key=lambda x: (
            category_order.get(
                x.get("category"),
                999
            ),
            -x.get("importance", 0)
        )
    )

    return selected


def main():

    print()
    print("=" * 60)
    print("NEWS SELECTOR")
    print("=" * 60)

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        articles = json.load(f)

    print(
        f"Loaded {len(articles)} candidates."
    )

    final_articles = select_articles(
        articles
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            final_articles,
            f,
            indent=4,
            ensure_ascii=False
        )

    print()
    print("=" * 60)
    print("FINAL SELECTION")
    print("=" * 60)

    for i, article in enumerate(
        final_articles,
        start=1
    ):

        print(
            f"{i}. "
            f"[{article['category']}] "
            f"{article['title']} "
            f"({article['importance']}/5)"
        )

    print()
    print(
        f"Final stories: "
        f"{len(final_articles)}"
    )

    print(
        f"Saved to: "
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()
