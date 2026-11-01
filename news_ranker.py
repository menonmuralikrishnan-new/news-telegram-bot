CATEGORY_LIMITS = {
    "AI & Technology": 3,
    "India & Politics": 4,
    "World & Geopolitics": 4,
    "Business & Economy": 3,
    "Stock Market": 2,
    "Cricket": 3,
    "Football": 2,
    "Malayalam Cinema": 2
}


IMPORTANT_KEYWORDS = {
    "AI & Technology": [
        "openai", "google", "microsoft", "apple", "meta",
        "ai", "artificial intelligence", "chatgpt", "gemini",
        "chip", "nvidia", "semiconductor", "cybersecurity"
    ],

    "India & Politics": [
        "prime minister", "parliament", "government", "election",
        "supreme court", "minister", "bjp", "congress",
        "lok sabha", "rajya sabha", "india", "kerala"
    ],

    "World & Geopolitics": [
        "war", "conflict", "president", "trump", "putin",
        "modi", "russia", "china", "iran", "israel", "g7", "united states","europe"
    ],

    "Business & Economy": [
        "economy", "gdp", "inflation", "interest rate",
        "rbi", "reserve bank", "bank", "company",
        "business", "jobs", "trade", "tariff"
    ],

    "Stock Market": [
        "stock", "stocks", "share", "shares", "sensex",
        "nifty", "market", "nasdaq", "dow", "ipo",
        "investor", "earnings"
    ],

    "Cricket": [
        "india", "test", "odi", "t20", "ipl", "world cup",
        "wicket", "runs", "batsman", "bowler", "cricket"
    ],

    "Football": [
        "football", "soccer", "premier league", "champions league",
        "fifa", "goal", "transfer", "world cup",
        "laliga", "manchester united", "portugal", "real madrid"
    ],

    "Malayalam Cinema": [
        "malayalam", "mollywood", "mohanlal", "mammootty",
        "nivin",
        "film", "movie", "cinema"
    ]
}


def calculate_score(article):
    title = article["title"].lower()
    category = article["category"]

    score = 0

    # Stronger weight for words appearing in the headline
    for keyword in IMPORTANT_KEYWORDS.get(category, []):
        if keyword in title:
            score += 2

    # Stories from established sources get a small boost
    source = article["source"].lower()

    trusted_sources = [
        "bbc",
        "the hindu",
        "reuters",
        "economic times",
        "moneycontrol",
        "espn"
    ]

    for trusted in trusted_sources:
        if trusted in source:
            score += 1
            break

    return score


def rank_articles(articles):
    # Add importance score
    for article in articles:
        article["importance_score"] = calculate_score(article)

    # Sort each category separately
    ranked = {}

    for article in articles:
        category = article["category"]

        if category not in ranked:
            ranked[category] = []

        ranked[category].append(article)

    # Sort highest score first and apply category limit
    selected = []

    for category, category_articles in ranked.items():
        category_articles.sort(
            key=lambda x: x["importance_score"],
            reverse=True
        )

        limit = CATEGORY_LIMITS.get(category, 3)

        selected.extend(category_articles[:limit])

    return selected