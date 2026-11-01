@echo off

cd /d C:\news-bot

call venv\Scripts\activate.bat

python news_fetcher.py

if errorlevel 1 exit /b 1

python news_selector.py

if errorlevel 1 exit /b 1

python telegram_sender.py

exit /b 0
