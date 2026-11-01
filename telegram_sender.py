import json
import requests

from telegram_config import BOT_TOKEN, CHAT_ID


NEWS_FILE = "final_news.json"

TELEGRAM_URL = (
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
)


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


CATEGORY_EMOJIS = {
    "AI & Technology": "🤖",
    "India & Politics": "🇮🇳",
    "World & Geopolitics": "🌍",
    "Business & Economy": "💼",
    "Stock Market": "📈",
    "Cricket": "🏏",
    "Football": "⚽",
    "Malayalam Cinema": "🎬"
}


def load_news():

    with open(
        NEWS_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


def create_story(article, number):

    title = article.get(
        "title",
        "Untitled"
    )

    summary = article.get(
        "llm_summary",
        ""
    ).strip()

    link = article.get(
        "link",
        ""
    )

    text = []

    text.append(
        f"{number}. {title}"
    )

    if summary:

        text.append(
            f"📝 {summary}"
        )

    if link:

        text.append(
            f"🔗 {link}"
        )

    return "\n".join(text)

def create_messages(articles):

    """
    Create Telegram messages without cutting
    through individual stories.

    A new message starts only between stories.
    """

    messages = []

    current = []

    current_length = 0

    article_number = 1

    current_category = None

    def flush():

        nonlocal current
        nonlocal current_length

        if current:

            messages.append(
                "\n".join(current)
            )

        current = []
        current_length = 0

    for article in articles:

        category = article.get(
            "category",
            "News"
        )

        # Add category heading when category changes.
        if category != current_category:

            category_heading = (
                f"\n"
                f"{CATEGORY_EMOJIS.get(category, '📰')} "
                f"{category.upper()}\n"
                f"━━━━━━━━━━━━━━━━━━━━"
            )

            # If adding this would make the
            # message too large, start a new one.
            if (
                current_length
                + len(category_heading)
                + 100
                > 3500
            ):

                flush()

            current.append(
                category_heading
            )

            current_length += len(
                category_heading
            )

            current_category = category

        story = create_story(
            article,
            article_number
        )

        # IMPORTANT:
        # We test the COMPLETE story before
        # adding it.
        if (
            current_length
            + len(story)
            + 100
            > 3500
        ):

            flush()

            # Re-add category heading
            current.append(
                f"{CATEGORY_EMOJIS.get(category, '📰')} "
                f"{category.upper()}\n"
                f"━━━━━━━━━━━━━━━━━━━━"
            )

            current_length = len(
                current[0]
            )

            current_category = category

        current.append(
            story
        )

        current_length += (
            len(story) + 2
        )

        article_number += 1

    flush()

    return messages


def send_messages(messages):

    total = len(messages)

    for i, message in enumerate(
        messages,
        start=1
    ):

        response = requests.post(
            TELEGRAM_URL,
            json={
                "chat_id": CHAT_ID,
                "text": message,
                "disable_web_page_preview": True
            },
            timeout=30
        )

        print(
            f"Telegram message "
            f"{i}/{total}: "
            f"{response.status_code}"
        )

        if response.status_code != 200:

            print(
                response.text
            )

            return False

    return True


def main():

    articles = load_news()

    print(
        f"Loaded {len(articles)} "
        f"final stories."
    )

    messages = create_messages(
        articles
    )

    print(
        f"Created {len(messages)} "
        f"Telegram messages."
    )

    success = send_messages(
        messages
    )

    if success:

        print(
            "✅ Briefing sent successfully!"
        )

    else:

        print(
            "❌ Telegram sending failed."
        )


if __name__ == "__main__":
    main()
