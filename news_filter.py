from rapidfuzz.fuzz import ratio
from datetime import datetime


# =========================================================
# NON-NEWS CONTENT
# =========================================================

NON_NEWS_KEYWORDS = [
    "quiz",
    "quizzes",
    "podcast",
    "football daily",
    "live stream",
    "watch live",
    "gallery",
    "photo gallery",
    "photos",
    "image gallery",
    "have your say",
    "your questions"
]

def is_non_news(article):
    title = article["title"].lower()

    for keyword in NON_NEWS_KEYWORDS:
        if keyword in title:
            return True

    return False


# =========================================================
# STRONG CATEGORY KEYWORDS
# =========================================================

CATEGORY_KEYWORDS = {

    "AI & Technology": [
        "artificial intelligence",
        "generative ai",
        "ai model",
        "ai models",
        "machine learning",
        "chatgpt",
        "openai",
        "gemini",
        "nvidia",
        "semiconductor",
        "cybersecurity",
        "smartphone",
        "iphone",
        "android",
        "samsung",
        "technology",
        "technology company",
        "tech company",
        "tech giant",
        "robotics",
        "robot",
        "software",
        "app",
        "internet",
        "social media"
    ],

    "India & Politics": [
        "prime minister",
        "pm modi",
        "lok sabha",
        "rajya sabha",
        "parliament",
        "election",
        "elections",
        "bjp",
        "congress party",
        "chief minister",
	"kerala chief minister",
        "union minister",
        "cabinet",
        "supreme court",
        "high court",
        "political party",
        "government policy",
        "india government",
        "indian government",
        "indian parliament",
        "assembly election",
        "state government"
    ],

    "World & Geopolitics": [
        "war",
        "ceasefire",
        "russia",
        "ukraine",
        "israel",
        "iran",
	"uk",
        "china",
        "donald trump",
        "trump administration",
        "vladimir putin",
        "white house",
        "us president",
        "united states",
        "sanctions",
        "missile",
        "diplomatic",
        "diplomacy",
        "foreign policy",
        "european union",
        "european parliament"
    ],

    "Business & Economy": [
        "economic growth",
        "economic slowdown",
        "gdp",
        "inflation",
        "interest rates",
        "interest rate",
        "reserve bank",
        "rbi",
        "economy",
        "trade",
        "tariff",
        "unemployment",
        "jobs",
        "corporate",
        "merger",
        "acquisition",
        "company earnings",
        "business",
        "businesses"
    ],

    "Stock Market": [
        "stock market",
        "stock markets",
        "share price",
        "share prices",
        "stock price",
        "stock prices",
        "sensex",
        "nifty",
        "nasdaq",
        "dow jones",
        "ipo",
        "market rally",
        "market crash",
        "market selloff",
        "investors",
        "investment",
        "equity market",
        "52-week high",
        "52-week low",
        "bull market",
        "bear market",
        "market valuation"
    ],

    "Cricket": [
        "cricket",
        "test match",
        "test series",
        "odi",
        "odi series",
        "t20",
        "t20i",
        "ipl",
        "world cup",
        "asia cup",
        "wicket",
        "wickets",
        "runs",
        "innings",
        "batter",
        "batsman",
        "bowler",
        "bowling",
        "batting",
        "scorecard",
        "cricket series",
        "cricket match",
        "india vs",
        "india women",
        "india men"
    ],

    "Football": [
        "football",
        "soccer",
        "premier league",
        "champions league",
        "europa league",
        "conference league",
        "fifa",
        "football match",
        "football fixture",
        "football fixtures",
        "football transfer",
        "football transfers",
        "football manager",
        "goalkeeper",
        "striker",
        "midfielder"
    ],

    "Malayalam Cinema": [
        "malayalam",
        "mollywood",
        "mohanlal",
        "mammootty",
        "prithviraj",
        "dulquer salmaan",
        "dulquer",
        "fahadh faasil",
        "fahadh",
        "tovino thomas",
        "tovino",
        "nivin pauly",
        "asif ali",
        "basil joseph",
        "malayalam film",
        "malayalam movie",
        "malayalam cinema"
    ]
}


# =========================================================
# SOURCE-BASED SIGNALS
# =========================================================

SOURCE_CATEGORY_HINTS = {

    "BBC Technology": "AI & Technology",
    "Indian Express Technology": "AI & Technology",

    "BBC India": "India & Politics",
    "Indian Express India": "India & Politics",
    "Indian Express Politics": "India & Politics",

    "BBC World": "World & Geopolitics",
    "Indian Express World": "World & Geopolitics",

    "BBC Business": "Business & Economy",
    "Indian Express Business": "Business & Economy",

    "Economic Times": "Stock Market",
    "Moneycontrol": "Stock Market",

    "BBC Cricket": "Cricket",
    "Indian Express Sports": "Cricket",

    "BBC Football": "Football",

    "Indian Express Entertainment": "Malayalam Cinema"
}


# =========================================================
# CATEGORY CLASSIFICATION
# =========================================================

def classify_article(article):

    title = article["title"].lower()
    source = article["source"]

    scores = {
        category: 0
        for category in CATEGORY_KEYWORDS
    }


    # -----------------------------------------------------
    # HEADLINE SIGNAL
    # -----------------------------------------------------

    for category, keywords in CATEGORY_KEYWORDS.items():

        for keyword in keywords:

            if keyword in title:

                # Strong phrases get more weight
                if len(keyword.split()) >= 2:
                    scores[category] += 3
                else:
                    scores[category] += 1


    # -----------------------------------------------------
    # SOURCE SIGNAL
    # -----------------------------------------------------

    source_hint = SOURCE_CATEGORY_HINTS.get(source)

    if source_hint:
        scores[source_hint] += 2


    # -----------------------------------------------------
    # SPORTS OVERRIDE
    # -----------------------------------------------------

    if scores["Cricket"] > 0:
        return "Cricket"

    if scores["Football"] > 0:
        return "Football"


    # -----------------------------------------------------
    # MALAYALAM CINEMA OVERRIDE
    # -----------------------------------------------------

    if scores["Malayalam Cinema"] > 0:
        return "Malayalam Cinema"


    # -----------------------------------------------------
    # TECHNOLOGY OVERRIDE
    # -----------------------------------------------------

    if scores["AI & Technology"] >= 3:
        return "AI & Technology"


    # -----------------------------------------------------
    # STOCK MARKET
    # -----------------------------------------------------

    if scores["Stock Market"] >= 3:
        return "Stock Market"


    # -----------------------------------------------------
    # INDIA VS WORLD POLITICS
    # -----------------------------------------------------

    india_score = scores["India & Politics"]
    world_score = scores["World & Geopolitics"]


    # Only classify as Indian politics if there is
    # an actual Indian political signal.
    if india_score > 0 and india_score >= world_score:
        return "India & Politics"


    # Foreign/world political story
    if world_score > 0:
        return "World & Geopolitics"


    # -----------------------------------------------------
    # BUSINESS
    # -----------------------------------------------------

    if scores["Business & Economy"] > 0:
        return "Business & Economy"


    # -----------------------------------------------------
    # FALLBACK
    # -----------------------------------------------------

    return source_hint if source_hint else article["category"]


# =========================================================
# NORMALIZE TITLE
# =========================================================

def normalize_title(title):

    title = title.lower()

    punctuation = ".,!?;:'\"()[]{}-–—"

    for char in punctuation:
        title = title.replace(char, " ")

    return " ".join(title.split())


# =========================================================
# PUBLICATION TIME
# =========================================================

def get_time(article):

    try:
        return datetime.fromisoformat(article["published"])
    except Exception:
        return datetime.min


# =========================================================
# DUPLICATE DETECTION
# =========================================================

def same_story(title1, title2):

    title1 = normalize_title(title1)
    title2 = normalize_title(title2)


    # Very similar headlines
    if ratio(title1, title2) >= 88:
        return True


    words1 = set(title1.split())
    words2 = set(title2.split())


    common_words = {
        "the", "a", "an", "and", "or", "to", "of",
        "in", "on", "for", "with", "as", "is", "by",
        "after", "before", "from", "at", "over",
        "says", "said"
    }


    words1 -= common_words
    words2 -= common_words


    if not words1 or not words2:
        return False


    shared = words1.intersection(words2)

    smaller = min(len(words1), len(words2))


    # Different articles about the same event can have
    # similar words, so require substantial overlap.
    if (
        len(shared) >= 4
        and len(shared) / smaller >= 0.75
    ):
        return True


    return False


# =========================================================
# REMOVE DUPLICATES + CLASSIFY
# =========================================================

def remove_duplicates(articles):

    cleaned = []


    # -----------------------------------------------------
    # Remove non-news
    # -----------------------------------------------------

    for article in articles:

        if is_non_news(article):
            continue

        cleaned.append(article)


    # -----------------------------------------------------
    # Classify
    # -----------------------------------------------------

    for article in cleaned:

        original_category = article["category"]

        article["original_category"] = original_category

        article["category"] = classify_article(article)


    # -----------------------------------------------------
    # Newest articles first
    # -----------------------------------------------------

    cleaned.sort(
        key=get_time,
        reverse=True
    )


    # -----------------------------------------------------
    # Remove duplicates across ALL categories
    # -----------------------------------------------------

    unique_articles = []


    for article in cleaned:

        duplicate = False


        for existing in unique_articles:

            if same_story(
                article["title"],
                existing["title"]
            ):
                duplicate = True
                break


        if not duplicate:

            unique_articles.append(article)


    return unique_articles