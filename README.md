# News Telegram Bot

A Python news-processing pipeline that fetches articles from configured sources, removes duplicates, ranks and selects stories, and can deliver a curated update to Telegram.

## Features

- Fetches news from the RSS/API sources in `sources.json`.
- Filters duplicate stories and ranks articles for relevance.
- Supports LLM-assisted news processing and classification.
- Sends selected stories to a configured Telegram chat.

## Setup

```bash
python -m venv venv
venv\\Scripts\\activate
pip install -r requirements.txt
copy telegram_config.example.py telegram_config.py
```

Set `BOT_TOKEN` and `CHAT_ID` in your local `telegram_config.py`. This file is deliberately excluded from version control.

## Usage

Run the news workflow with:

```bash
python llm_news_processor.py
```

Use `telegram_test.py` or `test_telegram_token.py` only after configuring Telegram credentials.

## Repository hygiene

Generated article output, the virtual environment, cache files, and Telegram credentials are ignored so that only the source code and reusable configuration are published.
