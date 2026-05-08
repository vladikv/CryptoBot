import os
import logging
import google.generativeai as genai
from dotenv import load_dotenv
from coingecko import get_crypto_data, resolve_coin_id

load_dotenv()
logger = logging.getLogger(__name__)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")


def ask_ai(question: str, lang: str = "uk") -> str:
    """Sends a question to Gemini with crypto context."""

    # Checks if a coin is mentioned in the question — if so, adds real data
    coin_data_context = ""
    words = question.upper().split()
    for word in words:
        coin_id = resolve_coin_id(word)
        data = get_crypto_data(coin_id)
        if data:
            change = data.get("price_change_percentage_24h") or 0
            coin_data_context = (
                f"\nПоточні дані по {data['name']}:\n"
                f"- Ціна: ${data['current_price']:,.2f}\n"
                f"- Зміна за 24г: {change:+.2f}%\n"
                f"- Маркет кап: ${data['market_cap']:,.0f}\n"
            )
            break

    lang_instruction = {
        "uk": "Відповідай українською мовою.",
        "en": "Reply in English.",
        "es": "Responde en español.",
    }.get(lang, "Відповідай українською мовою.")

    prompt = (
        f"Ти криптовалютний AI асистент у Telegram боті. "
        f"{lang_instruction} "
        f"Давай чіткі, корисні відповіді. Не давай фінансових порад — лише аналіз. "
        f"Максимум 300 слів.\n"
        f"{coin_data_context}\n"
        f"Питання: {question}"
    )

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        errors = {
            "uk": "❌ AI асистент тимчасово недоступний. Спробуй пізніше.",
            "en": "❌ AI assistant is temporarily unavailable. Try later.",
            "es": "❌ El asistente AI no está disponible. Inténtalo más tarde.",
        }
        return errors.get(lang, errors["uk"])
    except genai.Error as e:
        logger.error(f"Gemini error: {e}")
        errors = {
            "uk": "❌ AI асистент тимчасово недоступний. Спробуй пізніше.",
            "en": "❌ AI assistant is temporarily unavailable. Try later.",
            "es": "❌ El asistente AI no está disponible. Inténtalo más tarde.",
        }
        return errors.get(lang, errors["uk"])

def analyze_coin(coin_id: str, lang: str = "en") -> str:
    """
    Full analysis of a coin through Gemini with real data.
    """
    from coingecko import get_crypto_data, get_price_chart

    d = get_crypto_data(coin_id)
    if not d:
        return "❌ Coin not found."

    # Collecting data for the graph over 7 and 30 days
    chart_7  = get_price_chart(coin_id, 7)
    chart_30 = get_price_chart(coin_id, 30)

    prices_7  = [p[1] for p in chart_7["prices"]]  if chart_7  else []
    prices_30 = [p[1] for p in chart_30["prices"]] if chart_30 else []

    # Рахуємо RSI (14 періодів)
    rsi_value = _calc_rsi(prices_7) if len(prices_7) >= 14 else None

    # Рахуємо MA7 і MA30
    ma7  = sum(prices_7[-7:])  / 7  if len(prices_7)  >= 7  else None
    ma30 = sum(prices_30[-30:]) / 30 if len(prices_30) >= 30 else None

    change_7d  = ((prices_7[-1]  - prices_7[0])  / prices_7[0]  * 100) if len(prices_7)  >= 2 else None
    change_30d = ((prices_30[-1] - prices_30[0]) / prices_30[0] * 100) if len(prices_30) >= 2 else None

    change_24h = d.get("price_change_percentage_24h") or 0

    lang_instruction = {
        "uk": "Відповідай українською мовою.",
        "en": "Reply in English.",
        "es": "Responde en español.",
    }.get(lang, "Reply in English.")

    prompt = f"""You are a professional crypto analyst in a Telegram bot.
    {lang_instruction}
    Give a detailed but concise analysis. Do NOT give financial advice — analysis only.
    Use clear sections with emojis. Max 400 words.
    
    Coin: {d['name']} ({d['symbol'].upper()})
    
    MARKET DATA:
    - Current price: ${d['current_price']:,.4f}
    - 24h change: {change_24h:+.2f}%
    - 7d change: {f"{change_7d:+.2f}%" if change_7d else "N/A"}
    - 30d change: {f"{change_30d:+.2f}%" if change_30d else "N/A"}
    - Market cap: ${d.get('market_cap', 0):,.0f}
    - 24h volume: ${d.get('total_volume', 0):,.0f}
    - 24h high: ${d.get('high_24h', 0):,.4f}
    - 24h low: ${d.get('low_24h', 0):,.4f}
    - Rank: #{d.get('market_cap_rank', 'N/A')}
    - Circulating supply: {d.get('circulating_supply', 'N/A'):,.0f}
    
    TECHNICAL INDICATORS:
    - MA7: ${f"{ma7:,.4f}" if ma7 else "N/A"}
    - MA30: ${f"{ma30:,.4f}" if ma30 else "N/A"}
    - RSI(14): {f"{rsi_value:.1f}" if rsi_value else "N/A"}
    
    Provide analysis with these sections:
    1. 📊 Market Overview
    2. 📈 Technical Analysis (trend, MA, RSI interpretation)
    3. 💡 Key Levels (support/resistance based on 30d data)
    4. ⚠️ Risk Factors
    5. 🎯 Short-term Outlook (1-7 days)
    """

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Gemini analysis error: {e}")
        errors = {
            "uk": "❌ Analysis temporarily unavailable.",
            "en": "❌ Analysis temporarily unavailable.",
            "es": "❌ Análisis no disponible temporalmente.",
        }
        return errors.get(lang, errors["en"])


def _calc_rsi(prices: list, period: int = 14) -> float | None:
    """
    Calculates RSI (Relative Strength Index) over the last N prices.
    """
    if len(prices) < period + 1:
        return None
    gains, losses = [], []
    for i in range(1, period + 1):
        diff = prices[-period + i] - prices[-period + i - 1]
        if diff >= 0:
            gains.append(diff)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(diff))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))