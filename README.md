# 📈 CryptoBot

> A Telegram bot for real-time cryptocurrency tracking, portfolio management, and AI-powered analysis.

---

## ✨ Features

| Feature | Description |
|---|---|
| 📊 **Live Prices** | Real-time prices, 24h change, market cap, volume |
| 📈 **Charts** | Price charts for 1d / 7d / 30d with min/max labels |
| 🔔 **Price Alerts** | Get notified when a coin hits your target price |
| ⭐ **Watchlist** | Save your favorite coins and track them instantly |
| 💼 **Portfolio** | Track your holdings with P&L calculations |
| 💱 **Converter** | Convert any crypto to USD, UAH, EUR and more |
| 📰 **News** | Latest crypto news from CoinDesk, CoinTelegraph, Decrypt |
| 🤖 **AI Analysis** | Full technical analysis powered by Google Gemini |
| 🔍 **Compare** | Side-by-side comparison of two coins |
| 🌍 **Multi-language** | English, Ukrainian, Spanish |
| 💬 **Inline mode** | Use `@bot bitcoin` in any chat |

---

## 🤖 Commands

/start        — Main menu
/data         — Coin price and stats
/chart        — Price chart (1/7/30 days)
/ranks        — Top-10 by market cap
/alert        — Set price alert
/alerts       — My active alerts
/watchlist    — Manage watchlist
/portfolio    — Portfolio with P&L
/convert      — Currency converter
/news         — Latest crypto news
/analysis     — AI technical analysis
/compare      — Compare two coins
/high_low     — 24h max/min
/supply       — Coin supply info
/language     — Change language
/help         — Help

---

## 🛠 Tech Stack

- **Python 3.12**
- **python-telegram-bot 21.5**
- **MariaDB** — stores watchlist, alerts, portfolio, user settings
- **CoinGecko API** — real-time market data
- **Google Gemini** — AI analysis
- **matplotlib** — price charts
- **feedparser** — RSS news feeds

---

CryptoBot/
├── bot.py            # Main file — all handlers & commands
├── database.py       # MariaDB operations
├── coingecko.py      # CoinGecko API
├── charts.py         # Price chart builder
├── formatting.py     # Number formatting
├── languages.py      # EN / UA / ES translations
├── news.py           # RSS news fetcher
├── ai_assistant.py   # Gemini AI integration
├── requirements.txt
├── create_db.sql
├── .env.example
└── .gitignore
---

## ⚠️ Disclaimer
This bot is for informational purposes only. Not financial advice.
