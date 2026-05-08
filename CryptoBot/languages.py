TEXTS = {
    "uk": {
        "welcome": "👋 Привіт! Я *CryptoBot*.\n\nПоказую ціни, графіки, нагадую про цільові ціни.\nПиши символ монети або обери дію нижче:",
        "menu_ranks": "📊 Топ-10",
        "menu_watchlist": "⭐ Watchlist",
        "menu_alerts": "🔔 Мої алерти",
        "menu_help": "❓ Допомога",
        "menu_news": "📰 Новини",
        "menu_portfolio": "💼 Портфоліо",
        "menu_ai": "🤖 AI Асистент",
        "back": "◀️ Назад",
        "coin_not_found": "❌ Монету *{}* не знайдено.",
        "specify_coin": "Вкажи монету: {}",
        "chart_building": "⏳ Будую графік…",
        "chart_caption": "📈 *{}* — {}д",
        "no_data": "❌ Не вдалося отримати дані.",
        "alert_set": "🔔 Алерт встановлено!\n\n*{}*\nПоточна: {}\n{} Ціль: {}\n\nСповіщу, коли ціна {} цієї позначки.",
        "alert_triggered": "🔔 *Алерт спрацював!*\n\n*{}* досяг {}\nПоточна: {} {}",
        "alert_above": "перевищить",
        "alert_below": "впаде нижче",
        "no_alerts": "Немає активних алертів.\n\nВстанови: `/alert BTC 70000`",
        "my_alerts": "🔔 *Твої алерти:*\n",
        "delete_alert": "❌ Видалити",
        "alert_deleted": "✅ Алерт видалено.",
        "watchlist_empty": "⭐ Watchlist порожній.\nДодай: `/watchlist add BTC`",
        "watchlist_title": "⭐ *Твій Watchlist:*\n",
        "watchlist_added": "✅ *{}* додано до Watchlist!",
        "watchlist_exists": "ℹ️ *{}* вже є у Watchlist.",
        "watchlist_removed": "✅ *{}* видалено.",
        "watchlist_not_found": "ℹ️ *{}* немає у Watchlist.",
        "portfolio_empty": "💼 Портфоліо порожнє.\n\nДодай: `/portfolio add BTC 0.5 45000`",
        "portfolio_title": "💼 *Твоє портфоліо:*\n",
        "portfolio_added": "✅ *{}* додано до портфоліо!",
        "portfolio_removed": "✅ *{}* видалено з портфоліо.",
        "portfolio_total": "\n💰 *Загалом:* {}\n📈 *P&L:* {} ({}%)",
        "news_title": "📰 *Останні крипто новини:*\n",
        "news_loading": "⏳ Завантажую новини…",
        "news_not_found": "❌ Новини не знайдено.",
        "ai_loading": "🤖 Думаю…",
        "ai_intro": "Вкажи монету або задай питання: `/ai що думаєш про BTC?`",
        "compare_usage": "Використання: `/compare BTC ETH`",
        "compare_title": "📊 *Порівняння {} vs {}*\n",
        "language_changed": "✅ Мову змінено на Українську 🇺🇦",
        "analysis_loading": "🔍 Аналізую {}, зачекай...",
        "analysis_intro": "Вкажи монету: `/analysis BTC`",
        "choose_language": "🌍 Вибери мову / Choose language / Elige idioma:",
        "help_text": (
            "📋 *Команди:*\n\n"
            "/data `<монета>` — ціна і статистика\n"
            "/high\\_low `<монета>` — макс/мін за 24г\n"
            "/supply `<монета>` — запаси монети\n"
            "/chart `<монета> [днів]` — графік (1/7/30)\n"
            "/ranks — топ-10 за маркет капом\n"
            "/convert `<сума> <монета> <валюта>` — конвертер\n"
            "/alert `<монета> <ціна>` — сповіщення на ціну\n"
            "/alerts — мої активні алерти\n"
            "/watchlist — список обраних\n"
            "/portfolio — моє портфоліо\n"
            "/news `[монета]` — крипто новини\n"
            "/ai `<питання>` — AI асистент\n"
            "/compare `<монета1> <монета2>` — порівняння\n"
            "/language — змінити мову\n\n"
            "💡 Символи: BTC, ETH, SOL, DOGE…"
        ),
    },
    "en": {
        "welcome": "👋 Hi! I'm *CryptoBot*.\n\nI show prices, charts, and price alerts.\nType a coin symbol or choose an action below:",
        "menu_ranks": "📊 Top-10",
        "menu_watchlist": "⭐ Watchlist",
        "menu_alerts": "🔔 My Alerts",
        "menu_help": "❓ Help",
        "menu_news": "📰 News",
        "menu_portfolio": "💼 Portfolio",
        "menu_ai": "🤖 AI Assistant",
        "back": "◀️ Back",
        "coin_not_found": "❌ Coin *{}* not found.",
        "specify_coin": "Specify a coin: {}",
        "chart_building": "⏳ Building chart…",
        "chart_caption": "📈 *{}* — {}d",
        "no_data": "❌ Failed to get data.",
        "alert_set": "🔔 Alert set!\n\n*{}*\nCurrent: {}\n{} Target: {}\n\nI'll notify you when price {} this level.",
        "alert_triggered": "🔔 *Alert triggered!*\n\n*{}* reached {}\nCurrent: {} {}",
        "alert_above": "exceeds",
        "alert_below": "drops below",
        "no_alerts": "No active alerts.\n\nSet one: `/alert BTC 70000`",
        "my_alerts": "🔔 *Your alerts:*\n",
        "delete_alert": "❌ Delete",
        "alert_deleted": "✅ Alert deleted.",
        "watchlist_empty": "⭐ Watchlist is empty.\nAdd: `/watchlist add BTC`",
        "watchlist_title": "⭐ *Your Watchlist:*\n",
        "watchlist_added": "✅ *{}* added to Watchlist!",
        "watchlist_exists": "ℹ️ *{}* is already in Watchlist.",
        "watchlist_removed": "✅ *{}* removed.",
        "watchlist_not_found": "ℹ️ *{}* not in Watchlist.",
        "portfolio_empty": "💼 Portfolio is empty.\n\nAdd: `/portfolio add BTC 0.5 45000`",
        "portfolio_title": "💼 *Your portfolio:*\n",
        "portfolio_added": "✅ *{}* added to portfolio!",
        "portfolio_removed": "✅ *{}* removed from portfolio.",
        "portfolio_total": "\n💰 *Total:* {}\n📈 *P&L:* {} ({}%)",
        "news_title": "📰 *Latest crypto news:*\n",
        "news_loading": "⏳ Loading news…",
        "news_not_found": "❌ News not found.",
        "ai_loading": "🤖 Thinking…",
        "ai_intro": "Specify a coin or ask a question: `/ai what do you think about BTC?`",
        "compare_usage": "Usage: `/compare BTC ETH`",
        "compare_title": "📊 *Comparison {} vs {}*\n",
        "language_changed": "✅ Language changed to English 🇬🇧",
        "choose_language": "🌍 Вибери мову / Choose language / Elige idioma:",
        "analysis_loading": "🔍 Analyzing {}, please wait...",
        "analysis_intro": "Specify a coin: `/analysis BTC`",
        "help_text": (
            "📋 *Commands:*\n\n"
            "/data `<coin>` — price and stats\n"
            "/high\\_low `<coin>` — 24h max/min\n"
            "/supply `<coin>` — coin supply\n"
            "/chart `<coin> [days]` — chart (1/7/30)\n"
            "/ranks — top-10 by market cap\n"
            "/convert `<amount> <coin> <currency>` — converter\n"
            "/alert `<coin> <price>` — price alert\n"
            "/alerts — my active alerts\n"
            "/watchlist — watchlist\n"
            "/portfolio — my portfolio\n"
            "/news `[coin]` — crypto news\n"
            "/ai `<question>` — AI assistant\n"
            "/compare `<coin1> <coin2>` — comparison\n"
            "/language — change language\n\n"
            "💡 Symbols: BTC, ETH, SOL, DOGE…"
        ),
    },
    "es": {
        "welcome": "👋 ¡Hola! Soy *CryptoBot*.\n\nMuestro precios, gráficos y alertas de precios.\nEscribe un símbolo de moneda o elige una acción:",
        "menu_ranks": "📊 Top-10",
        "menu_watchlist": "⭐ Watchlist",
        "menu_alerts": "🔔 Mis Alertas",
        "menu_help": "❓ Ayuda",
        "menu_news": "📰 Noticias",
        "menu_portfolio": "💼 Portafolio",
        "menu_ai": "🤖 Asistente AI",
        "back": "◀️ Atrás",
        "coin_not_found": "❌ Moneda *{}* no encontrada.",
        "specify_coin": "Especifica una moneda: {}",
        "chart_building": "⏳ Construyendo gráfico…",
        "chart_caption": "📈 *{}* — {}d",
        "no_data": "❌ No se pudieron obtener datos.",
        "alert_set": "🔔 ¡Alerta establecida!\n\n*{}*\nActual: {}\n{} Objetivo: {}\n\nTe notificaré cuando el precio {} este nivel.",
        "alert_triggered": "🔔 *¡Alerta activada!*\n\n*{}* alcanzó {}\nActual: {} {}",
        "alert_above": "supere",
        "alert_below": "caiga por debajo de",
        "no_alerts": "No hay alertas activas.\n\nEstablece una: `/alert BTC 70000`",
        "my_alerts": "🔔 *Tus alertas:*\n",
        "delete_alert": "❌ Eliminar",
        "alert_deleted": "✅ Alerta eliminada.",
        "watchlist_empty": "⭐ Watchlist vacía.\nAñade: `/watchlist add BTC`",
        "watchlist_title": "⭐ *Tu Watchlist:*\n",
        "watchlist_added": "✅ *{}* añadido a Watchlist!",
        "watchlist_exists": "ℹ️ *{}* ya está en Watchlist.",
        "watchlist_removed": "✅ *{}* eliminado.",
        "watchlist_not_found": "ℹ️ *{}* no está en Watchlist.",
        "portfolio_empty": "💼 Portafolio vacío.\n\nAñade: `/portfolio add BTC 0.5 45000`",
        "portfolio_title": "💼 *Tu portafolio:*\n",
        "portfolio_added": "✅ *{}* añadido al portafolio!",
        "portfolio_removed": "✅ *{}* eliminado del portafolio.",
        "portfolio_total": "\n💰 *Total:* {}\n📈 *P&L:* {} ({}%)",
        "news_title": "📰 *Últimas noticias cripto:*\n",
        "news_loading": "⏳ Cargando noticias…",
        "news_not_found": "❌ Noticias no encontradas.",
        "ai_loading": "🤖 Pensando…",
        "ai_intro": "Especifica una moneda o haz una pregunta: `/ai qué piensas sobre BTC?`",
        "compare_usage": "Uso: `/compare BTC ETH`",
        "compare_title": "📊 *Comparación {} vs {}*\n",
        "language_changed": "✅ Idioma cambiado a Español 🇪🇸",
        "choose_language": "🌍 Вибери мову / Choose language / Elige idioma:",
        "analysis_loading": "🔍 Analizando {}, espera...",
        "analysis_intro": "Especifica una moneda: `/analysis BTC`",
        "help_text": (
            "📋 *Comandos:*\n\n"
            "/data `<moneda>` — precio y estadísticas\n"
            "/high\\_low `<moneda>` — máx/mín 24h\n"
            "/supply `<moneda>` — suministro\n"
            "/chart `<moneda> [días]` — gráfico (1/7/30)\n"
            "/ranks — top-10 por capitalización\n"
            "/convert `<cantidad> <moneda> <divisa>` — conversor\n"
            "/alert `<moneda> <precio>` — alerta de precio\n"
            "/alerts — mis alertas activas\n"
            "/watchlist — lista de seguimiento\n"
            "/portfolio — mi portafolio\n"
            "/news `[moneda]` — noticias cripto\n"
            "/ai `<pregunta>` — asistente AI\n"
            "/compare `<moneda1> <moneda2>` — comparación\n"
            "/language — cambiar idioma\n\n"
            "💡 Símbolos: BTC, ETH, SOL, DOGE…"
        ),
    },
}


def t(user_lang: str, key: str) -> str:
    """Returns text for the specified language."""
    return TEXTS.get(user_lang, TEXTS["uk"]).get(key, TEXTS["uk"].get(key, key))