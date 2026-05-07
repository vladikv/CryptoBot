import os
import logging
import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

BASE_URL = "https://api.coingecko.com/api/v3"
_KEY = os.getenv("COINGECKO_API_KEY", "")
HEADERS = {"x-cg-demo-api-key": _KEY} if _KEY else {}

# Символ → CoinGecko ID
SYMBOL_MAP: dict[str, str] = {
    "btc":  "bitcoin",           "eth":  "ethereum",
    "bnb":  "binancecoin",       "sol":  "solana",
    "xrp":  "ripple",            "ada":  "cardano",
    "doge": "dogecoin",          "dot":  "polkadot",
    "matic":"matic-network",     "ltc":  "litecoin",
    "avax": "avalanche-2",       "link": "chainlink",
    "uni":  "uniswap",           "atom": "cosmos",
    "trx":  "tron",              "usdt": "tether",
    "usdc": "usd-coin",          "shib": "shiba-inu",
    "near": "near",              "fil":  "filecoin",
    "apt":  "aptos",             "arb":  "arbitrum",
    "op":   "optimism",          "inj":  "injective-protocol",
    "sui":  "sui",               "ton":  "the-open-network",
}


def resolve_coin_id(name: str) -> str:
    return SYMBOL_MAP.get(name.lower().strip(), name.lower().strip())


def _get(path: str, params: dict = None):
    try:
        r = requests.get(
            f"{BASE_URL}{path}",
            params=params,
            headers=HEADERS,
            timeout=10
        )
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        logger.error(f"API error {path}: {e}")
        return None


def get_crypto_data(coin_id: str) -> dict | None:
    data = _get("/coins/markets", {
        "vs_currency": "usd",
        "ids": coin_id,
        "price_change_percentage": "24h",
    })
    return data[0] if data else None


def get_top_cryptos(n: int = 10) -> list | None:
    return _get("/coins/markets", {
        "vs_currency": "usd",
        "order":       "market_cap_desc",
        "per_page":    n,
        "page":        1,
    })


def get_price_chart(coin_id: str, days: int = 7) -> dict | None:
    return _get(f"/coins/{coin_id}/market_chart",
                {"vs_currency": "usd", "days": days})


def get_exchange_rates() -> dict | None:
    data = _get("/exchange_rates")
    return data.get("rates") if data else None