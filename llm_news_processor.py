import requests
import json
import re
from collections import defaultdict

from news_fetcher import fetch_news
from news_filter import remove_duplicates
from news_ranker import rank_articles


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"

STORIES_PER_CATEGORY = 2
MAX_FINAL_STORIES = 16


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


# ---------------------------------------------------------
# CATEGORY-SPECIFIC KEYWORDS
# ---------------------------------------------------------

MALAYALAM_KEYWORDS = [
    "malayalam",
    "mollywood",
    "mohanlal",
    "mammootty",
    "dulquer",
    "dulquer salmaan",
    "fahadh",
    "fahadh faasil",
    "prithviraj",
    "prithviraj sukumaran",
    "tovino",
    "tovino thomas",
    "nivin pauly",
    "nazriya",
    "parvathy",
    "manju warrier",
    "soubin",
    "vineeth sreenivasan",
    "basil joseph",
    "asif ali",
    "shane nigam",
    "unni mukundan",
    "kunchacko boban",
    "basil joseph",
    "malayalam film",
    "malayalam movie",
    "malayalam cinema",
    "malayalam actor",
    "malayalam actress",
    "mollywood film",
    "mollywood movie"
]


STOCK_KEYWORDS = [
    "stock",
    "stocks",
    "share",
    "shares",
    "share price",
    "nifty",
    "sensex",
    "ipo",
    "equity",
    "investor",
    "investors",
    "52-week",
    "52 week",
    "market rally",
    "market crash",
    "market falls",
    "market rises",
    "listed company",
    "valuation",
    "brokerage"
]


# ---------------------------------------------------------
# MALAYALAM VALIDATION
# ---------------------------------------------------------

def is_malayalam_story(article):

    """
    Strictly verify that an entertainment article is actually
    related to Malayalam cinema.

    Being from an entertainment feed is NOT enough.
    """

    title = article["title"].lower()
    summary = article.get("summary", "").lower()

    text = title + " " + summary

    for keyword in MALAYALAM_KEYWORDS:

        if keyword in text:
            return True

    return False


# ---------------------------------------------------------
# STOCK VALIDATION
# ---------------------------------------------------------

def is_stock_story(article):

    title = article["title"].lower()
    summary = article.get("summary", "").lower()

    text = title + " " + summary

    for keyword in STOCK_KEYWORDS:

        if keyword in text:
            return True

    return False


# ---------------------------------------------------------
# LLM
# ---------------------------------------------------------

def ask_llm(article):

    title = article["title"]
    source = article["source"]
    original_category = article["category"]
    summary = article.get("summary", "")[:1200]

    prompt = f"""
You are an expert editor preparing a PERSONAL MORNING NEWS BRIEFING.

Analyze ONE article.

Your job is to:

1. Identify the correct category.
2. Decide whether it is meaningful news.
3. Give it an importance score.
4. Give it a morning briefing score.
5. Write a concise, FACTUAL summary.
6. Identify the main event/topic.


CATEGORIES:

AI & Technology:
AI, artificial intelligence, technology, smartphones, gadgets,
software, cybersecurity and major technology developments.

India & Politics:
Indian politics, elections, government, parliament, courts,
political parties and major Indian domestic developments.

World & Geopolitics:
International politics, wars, conflicts, diplomacy and
international relations.

Business & Economy:
Inflation, GDP, interest rates, RBI, jobs, trade, companies,
business policy and economic developments.

Stock Market:
Stocks, shares, Nifty, Sensex, IPOs, equity markets,
stock prices and major market developments.

Cricket:
Cricket matches, players, teams and tournaments.

Football:
Football/soccer matches, players, clubs, leagues and tournaments.

Malayalam Cinema:
ONLY Malayalam-language cinema, Mollywood films, Malayalam actors,
directors, filmmakers and Malayalam box-office developments.


VERY IMPORTANT MALAYALAM RULE:

Do NOT classify an article as Malayalam Cinema merely because it
comes from an entertainment section.

If the article is about Bollywood, Hindi cinema, Telugu cinema,
Tamil cinema or another film industry, it is NOT Malayalam Cinema.

For example:

"Mirzapur Movie box office..." = NOT Malayalam Cinema.

"Nivin Pauly film crosses ₹300 crore" = Malayalam Cinema.

"Mohanlal's upcoming film..." = Malayalam Cinema.

"Mammootty film..." = Malayalam Cinema.

"Mollywood box office..." = Malayalam Cinema.


IMPORTANCE:

5 = Major event that many people should know about.

4 = Important development with significant impact or broad interest.

3 = Meaningful development worth knowing.

2 = Minor or niche update.

1 = Routine, trivial, promotional or low-value news.


MORNING BRIEFING SCORE:

9-10 = Essential headline.
7-8 = Very strong story.
5-6 = Useful story.
3-4 = Optional/niche.
1-2 = Low-value.
0 = Should not be included.


DO NOT GIVE EVERYTHING THE SAME SCORE.

Think about how valuable this story is to someone who has only
five minutes to understand what happened today.


SUMMARY RULES:

The summary MUST contain actual information from the article.

Bad summary:
"Significant development with broad public interest."

Good summary:
"Retail inflation rose to 4.82% in August, with higher food prices
adding pressure on households. The rise could influence the RBI's
approach to interest rates at its October meeting."

Do NOT invent facts.

Do NOT mention information that is not present in the article.

Keep the summary to 1-2 sentences.

Do not use phrases such as:
"this story is important"
"this is significant"
"this deserves attention"

Instead, explain WHAT HAPPENED and WHY IT MATTERS.


TOPIC KEY:

Create a short identifier for the central event.

Examples:

"India wins Women's Asia Cup"
"HDFC Bank 52-week low"
"Rajasthan local elections"
"Nivin Pauly film box office"

Two articles covering the same event should receive the same
topic_key even if their headlines are different.


ARTICLE:

Title: {title}
Source: {source}
Original category: {original_category}
Article summary: {summary}


Return ONLY valid JSON:

{{
    "category": "one category from the list",
    "importance": 1,
    "briefing_score": 0,
    "relevant": true,
    "topic_key": "short event identifier",
    "summary": "1-2 factual sentences explaining what happened and why it matters"
}}
"""

    try:

        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            },
            timeout=120
        )

        response.raise_for_status()

        result = response.json()

        parsed = json.loads(
            result["response"].strip()
        )

        # -----------------------------
        # Validate category
        # -----------------------------

        if parsed.get("category") not in CATEGORIES:

            parsed["category"] = original_category

        # -----------------------------
        # Validate importance
        # -----------------------------

        try:
            parsed["importance"] = int(
                parsed.get("importance", 3)
            )
        except:

            parsed["importance"] = 3

        parsed["importance"] = max(
            1,
            min(5, parsed["importance"])
        )

        # -----------------------------
        # Validate briefing score
        # -----------------------------

        try:
            parsed["briefing_score"] = int(
                parsed.get("briefing_score", 5)
            )
        except:

            parsed["briefing_score"] = 5

        parsed["briefing_score"] = max(
            0,
            min(10, parsed["briefing_score"])
        )

        # -----------------------------
        # Validate relevance
        # -----------------------------

        parsed["relevant"] = bool(
            parsed.get("relevant", True)
        )

        # -----------------------------
        # Summary fallback
        # -----------------------------

        if not parsed.get("summary"):

            parsed["summary"] = (
                article.get("summary", "")
            )

        # -----------------------------
        # Topic fallback
        # -----------------------------

        if not parsed.get("topic_key"):

            parsed["topic_key"] = title[:80]

        return parsed

    except Exception as e:

        print(f"LLM error for: {title}")
        print(e)

        return {
            "category": original_category,
            "importance": 3,
            "briefing_score": 5,
            "relevant": True,
            "topic_key": title[:80],
            "summary": article.get(
                "summary",
                "No summary available."
            )
        }


# ---------------------------------------------------------
# CATEGORY SAFETY
# ---------------------------------------------------------

def apply_category_fallback(article, result):

    title = article["title"].lower()
    source = article["source"]

    # -----------------------------------------------------
    # Malayalam Cinema
    # -----------------------------------------------------

    if source == "Indian Express Entertainment":

        if is_malayalam_story(article):

            result["category"] = "Malayalam Cinema"

        else:

            # VERY IMPORTANT:
            # Do not allow generic entertainment stories
            # into Malayalam Cinema.

            if result["category"] == "Malayalam Cinema":

                result["category"] = "Business & Economy"

                result["relevant"] = False

    # -----------------------------------------------------
    # Stock Market
    # -----------------------------------------------------

    if source == "Economic Times":

        if is_stock_story(article):

            result["category"] = "Stock Market"

    return result


# ---------------------------------------------------------
# PROCESS ARTICLES
# ---------------------------------------------------------

def process_articles(articles):

    processed = []

    print("\nClassifying articles with Llama...\n")

    for index, article in enumerate(
        articles,
        start=1
    ):

        print(
            f"[{index}/{len(articles)}] "
            f"{article['title'][:90]}"
        )

        result = ask_llm(article)

        result = apply_category_fallback(
            article,
            result
        )

        article_copy = article.copy()

        article_copy["llm_category"] = result["category"]

        article_copy["importance"] = result["importance"]

        article_copy["briefing_score"] = result[
            "briefing_score"
        ]

        article_copy["relevant"] = result["relevant"]

        article_copy["topic_key"] = result[
            "topic_key"
        ]

        article_copy["briefing_summary"] = result[
            "summary"
        ]

        processed.append(article_copy)

    return processed


# ---------------------------------------------------------
# SCORE
# ---------------------------------------------------------

def get_story_score(article):

    return (
        article["briefing_score"] * 10
        + article["importance"] * 2
    )


# ---------------------------------------------------------
# DUPLICATE EVENT DETECTION
# ---------------------------------------------------------

def same_event(article1, article2):

    # First use the LLM-generated topic key.
    topic1 = article1.get(
        "topic_key",
        ""
    ).lower().strip()

    topic2 = article2.get(
        "topic_key",
        ""
    ).lower().strip()

    if topic1 and topic2:

        if topic1 == topic2:
            return True

    # ---------------------------------------------
    # Fallback title overlap
    # ---------------------------------------------

    stopwords = {
        "the", "and", "for", "with", "from",
        "after", "before", "over", "into",
        "this", "that", "has", "have", "been",
        "will", "are", "was", "were", "its",
        "their", "they", "india", "women",
        "final", "news", "live", "highlights"
    }

    words1 = {
        word.strip(".,:;!?-'\"()")
        for word in article1["title"].lower().split()
        if len(word.strip(".,:;!?-'\"()")) >= 4
        and word.strip(".,:;!?-'\"()") not in stopwords
    }

    words2 = {
        word.strip(".,:;!?-'\"()")
        for word in article2["title"].lower().split()
        if len(word.strip(".,:;!?-'\"()")) >= 4
        and word.strip(".,:;!?-'\"()") not in stopwords
    }

    if not words1 or not words2:
        return False

    shared = words1 & words2

    if len(shared) >= 4:
        return True

    overlap = len(shared) / min(
        len(words1),
        len(words2)
    )

    return overlap >= 0.65


# ---------------------------------------------------------
# FINAL SELECTION
# ---------------------------------------------------------

def select_final_articles(articles):

    """
    EXACTLY TWO STORIES PER CATEGORY.

    Each category is processed independently.

    If the first two candidates are duplicates,
    we move to the next candidate.
    """

    grouped = {
        category: []
        for category in CATEGORIES
    }

    # -----------------------------------------------------
    # STEP 1: Category filtering
    # -----------------------------------------------------

    for article in articles:

        if not article["relevant"]:
            continue

        category = article["llm_category"]

        if category not in grouped:
            continue

        # Extra Malayalam safety.
        if category == "Malayalam Cinema":

            if not is_malayalam_story(article):
                continue

        grouped[category].append(article)

    # -----------------------------------------------------
    # STEP 2: Sort each category
    # -----------------------------------------------------

    for category in grouped:

        grouped[category].sort(
            key=get_story_score,
            reverse=True
        )

    # -----------------------------------------------------
    # STEP 3: Select 2 unique stories/category
    # -----------------------------------------------------

    final_articles = []

    for category in CATEGORIES:

        selected_for_category = []

        for article in grouped[category]:

            if len(selected_for_category) >= 2:
                break

            duplicate = False

            # Compare against stories already selected
            # in this category.
            for existing in selected_for_category:

                if same_event(article, existing):

                    duplicate = True
                    break

            if duplicate:
                continue

            selected_for_category.append(article)

        final_articles.extend(
            selected_for_category
        )

    # -----------------------------------------------------
    # STEP 4: Sort final stories by briefing score
    # -----------------------------------------------------

    final_articles.sort(
        key=get_story_score,
        reverse=True
    )

    return final_articles


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():

    print("=" * 70)
    print("NEWS BOT - PERSONAL MORNING BRIEFING")
    print("=" * 70)

    print("\nFetching news...")

    articles = fetch_news()

    print(
        f"Fetched: {len(articles)} articles"
    )

    print(
        "\nRemoving duplicates and filtering..."
    )

    articles = remove_duplicates(
        articles
    )

    print(
        f"After filtering: {len(articles)} articles"
    )

    print("\nRanking articles...")

    candidates = rank_articles(
        articles
    )

    print(
        f"Ranked candidates: {len(candidates)}"
    )

    # -----------------------------------------------------
    # IMPORTANT:
    #
    # Do NOT globally slice candidates.
    #
    # We need all category candidates so that Malayalam,
    # Stock Market, etc. cannot disappear.
    # -----------------------------------------------------

    processed = process_articles(
        candidates
    )

    final_articles = select_final_articles(
        processed
    )

    # -----------------------------------------------------
    # CATEGORY BREAKDOWN
    # -----------------------------------------------------

    print("\n")
    print("=" * 70)
    print("FINAL CATEGORY BREAKDOWN")
    print("=" * 70)

    counts = {
        category: 0
        for category in CATEGORIES
    }

    for article in final_articles:

        counts[
            article["llm_category"]
        ] += 1

    for category in CATEGORIES:

        print(
            f"{category}: "
            f"{counts[category]}"
        )

    # -----------------------------------------------------
    # FINAL STORIES
    # -----------------------------------------------------

    print("\n")
    print("=" * 70)
    print(
        f"FINAL STORIES: "
        f"{len(final_articles)}"
    )
    print("=" * 70)

    for index, article in enumerate(
        final_articles,
        start=1
    ):

        print(
            f"\n{index}. "
            f"{article['title']}"
        )

        print(
            f"   Category: "
            f"{article['llm_category']}"
        )

        print(
            f"   Importance: "
            f"{article['importance']}/5"
        )

        print(
            f"   Briefing Score: "
            f"{article['briefing_score']}/10"
        )

        print(
            f"   Source: "
            f"{article['source']}"
        )

        print(
            f"   Summary: "
            f"{article['briefing_summary']}"
        )

        print(
            f"   Topic: "
            f"{article['topic_key']}"
        )

        print(
            f"   Link: "
            f"{article['link']}"
        )


if __name__ == "__main__":
    main()