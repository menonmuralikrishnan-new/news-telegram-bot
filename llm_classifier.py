import requests
import json


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"


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


def classify_article(article):

    prompt = f"""
You are an expert daily news editor.

Classify the following news article.

TITLE:
{article["title"]}

SOURCE:
{article["source"]}

ORIGINAL CATEGORY:
{article["category"]}

ARTICLE SUMMARY:
{article.get("summary", "")}

Choose exactly ONE category from:

{json.dumps(CATEGORIES)}

Important rules:

1. Classify based on what the article is ACTUALLY about.
2. The original category is only a hint. It may be wrong.
3. Do not classify based on one ambiguous word.
4. "shares" does NOT automatically mean Stock Market.
5. A Samsung phone/technology story belongs to AI & Technology.
6. Cricket stories belong to Cricket.
7. Football stories belong to Football.
8. A foreign election belongs to World & Geopolitics.
9. Indian elections and Indian government/politics belong to India & Politics.
10. Stock Market requires actual financial-market content.
11. Malayalam movies, actors and Mollywood belong to Malayalam Cinema.
12. If the article is trivial, promotional, a quiz, podcast, lifestyle piece, or otherwise not useful for a daily news briefing, mark it as irrelevant.

Also give an importance score from 1 to 10.

10 = extremely important national/international development
8-9 = major development
6-7 = important news
4-5 = moderately useful
1-3 = minor/trivial

Return ONLY valid JSON in exactly this format:

{{
    "category": "one category from the list",
    "importance": 1,
    "relevant": true,
    "reason": "one short sentence"
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

        answer = result["response"]

        return json.loads(answer)


    except Exception as e:

        print(f"LLM error: {e}")

        return {
            "category": article["category"],
            "importance": 0,
            "relevant": True,
            "reason": "LLM classification failed"
        }


if __name__ == "__main__":

    print("=" * 70)
    print("OLLAMA NEWS CLASSIFIER TEST")
    print("=" * 70)

    test_articles = [

        {
            "title": "Samsung launches Galaxy S26 FE for the premium segment buyers in India",
            "source": "The Hindu",
            "category": "India & Politics",
            "summary": ""
        },

        {
            "title": "Swedish left-wing bloc narrowly ahead with election too close to call",
            "source": "BBC World",
            "category": "India & Politics",
            "summary": ""
        },

        {
            "title": "Trump downplays warnings of AI risks, citing rivalry with China",
            "source": "BBC Technology",
            "category": "World & Geopolitics",
            "summary": ""
        },

        {
            "title": "India vs Afghanistan, 1st T20I: IND beat AFG by 7-wickets and take 1-0 lead in New Delhi",
            "source": "Indian Express Sports",
            "category": "Cricket",
            "summary": ""
        },

        {
            "title": "Sussanne Khan says mom Zarine's death brought her closer to Hrithik Roshan's mom",
            "source": "Indian Express Entertainment",
            "category": "Stock Market",
            "summary": ""
        }
    ]


    for i, article in enumerate(test_articles, 1):

        print(f"\nTEST {i}")
        print("-" * 70)

        print(f"Title: {article['title']}")
        print(f"Original category: {article['category']}")

        result = classify_article(article)

        print(f"LLM category: {result.get('category')}")
        print(f"Importance: {result.get('importance')}/10")
        print(f"Relevant: {result.get('relevant')}")
        print(f"Reason: {result.get('reason')}")


    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)