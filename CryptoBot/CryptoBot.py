from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests
import json

api_key = 'https://api.coingecko.com/api/v3/ping?x_cg_demo_api_key=CG-NXRaB55eZMZJBpsPtcRXCbsE'

def get_crypto_data(crypto):
    try:
        response = requests.get(f'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={crypto}&api_key={api_key}')
        response.raise_for_status()
        data = response.json()[0]
        return data
    except requests.exceptions.HTTPError as errh:
        print("Http Error:", errh)
    except requests.exceptions.ConnectionError as errc:
        print("Error Connecting:", errc)
    except requests.exceptions.Timeout as errt:
        print("Timeout Error:", errt)
    except requests.exceptions.RequestException as err:
        print("Something went wrong", err)


def get_top_cryptos():
    try:
        response = requests.get(f'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=10&page=1&sparkline=false&api_key={api_key}')
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.HTTPError as errh:
        print("Http Error:", errh)
    except requests.exceptions.ConnectionError as errc:
        print("Error Connecting:", errc)
    except requests.exceptions.Timeout as errt:
        print("Timeout Error:", errt)
    except requests.exceptions.RequestException as err:
        print("Something went wrong", err)


def get_dex_pools(query, network, include, page=1):
    headers = {"x-cg-pro-api-key": api_key}
    try:
        response = requests.get(f'https://pro-api.coingecko.com/api/v3/onchain/search/pools?query={query}&network={network}&include={include}&page={page}', headers=headers)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.HTTPError as errh:
        print("Http Error:", errh)
    except requests.exceptions.ConnectionError as errc:
        print("Error Connecting:", errc)
    except requests.exceptions.Timeout as errt:
        print("Timeout Error:", errt)
    except requests.exceptions.RequestException as err:
        print("Something went wrong", err)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    welcome_message = 'Hello! I am your Crypto Bot. I can provide real-time data for any cryptocurrency. Use /help to see my commands.'
    await update.message.reply_text(welcome_message)


async def data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    crypto = update.message.text.split()[1]
    data = get_crypto_data(crypto)
    if data:
        await update.message.reply_text(f'The current price of {crypto} is ${data["current_price"]}. The price change in the last 24 hours is {data["price_change_percentage_24h"]}%.\nThe market cap is ${data["market_cap"]}.\nThe total volume in the last 24 hours is ${data["total_volume"]}.')
    else:
        await update.message.reply_text(f'Sorry, I could not fetch the data for {crypto}. Please check the cryptocurrency name and try again.')


async def high_low(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    crypto = update.message.text.split()[1]
    data = get_crypto_data(crypto)
    if data:
        await update.message.reply_text(f'The highest price in the last 24 hours for {crypto} is ${data["high_24h"]}, and the lowest price is ${data["low_24h"]}.')
    else:
        await update.message.reply_text(f'Sorry, I could not fetch the data for {crypto}. Please check the cryptocurrency name and try again.')


async def supply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    crypto = update.message.text.split()[1]
    data = get_crypto_data(crypto)
    if data:
        await update.message.reply_text(f'The circulating supply of {crypto} is {data["circulating_supply"]}, and the total supply is {data["total_supply"]}.')
    else:
        await update.message.reply_text(f'Sorry, I could not fetch the data for {crypto}. Please check the cryptocurrency name and try again.')


async def ranks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = get_top_cryptos()
    if data:
        message = "Here are the top 10 cryptocurrencies:\n"
        for i, crypto in enumerate(data, start=1):
            message += f'{i}. *{crypto["name"]}* ({crypto["symbol"].upper()}):\n- Current price is ${crypto["current_price"]}\n- Market cap is ${crypto["market_cap"]}\n- Total volume in the last 24 hours is ${crypto["total_volume"]}\n\n'
        await update.message.reply_text(message, parse_mode='Markdown')
    else:
        await update.message.reply_text('Sorry, I could not fetch the data for the top 10 cryptocurrencies. Please try again later.')


async def search_pools(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    params = update.message.text.split()[1:]
    query = params[0] if len(params) > 0 else 'weth'
    network = params[1] if len(params) > 1 else 'eth'
    include = params[2] if len(params) > 2 else 'dex'
    page = int(params[3]) if len(params) > 3 else 1
    data = get_dex_pools(query, network, include, page)
    if data and "data" in data:
        message = f"Here are the DEX pool data for the query {query} on the network {network}:\n"
        for i, pool in enumerate(data["data"], start=1):
            message += f'\n{i}. Pool ID: *{pool["id"]}*\n- Pool Name: {pool["attributes"]["name"]}\n- Base Token Price (USD): ${pool["attributes"]["base_token_price_usd"]}\n- Quote Token Price (USD): ${pool["attributes"]["quote_token_price_usd"]}\n- Base Token Price (Quote Token): {pool["attributes"]["base_token_price_quote_token"]}\n- Quote Token Price (Base Token): {pool["attributes"]["quote_token_price_base_token"]}\n- Total Liquidity: ${pool["attributes"]["reserve_in_usd"]}\n- Price Change Percentage in the last 5 minutes: {pool["attributes"]["price_change_percentage"]["m5"]}%\n- Price Change Percentage in the last 1 hour: {pool["attributes"]["price_change_percentage"]["h1"]}%\n- Price Change Percentage in the last 6 hours: {pool["attributes"]["price_change_percentage"]["h6"]}%\n- Price Change Percentage in the last 24 hours: {pool["attributes"]["price_change_percentage"]["h24"]}%\n'
        for i in range(0, len(message), 4096):
            await update.message.reply_text(message[i:i+4096], parse_mode='Markdown')
    else:
        await update.message.reply_text(f'Sorry, I could not fetch the data for the query {query} on the network {network}. Please check the query and network and try again.')

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_message = ('/data - command to get the data of a cryptocurrency\n'
                    '/high_low - command to get the highest and lowest prices of a cryptocurrency in the last 24 hours\n'
                    '/supply - command to get the circulating supply and total supply of a cryptocurrency\n'
                    '/ranks - command to get the top 10 cryptocurrencies\n'
                    '/search_pools - command to get the on-chain DEX pool data')
    await update.message.reply_text(help_message)

app = ApplicationBuilder().token('7175743730:AAGjaMErAEbNr5QZlA-KC8u9iHsZi5_hHhw').build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("data", data))
app.add_handler(CommandHandler("high_low", high_low))
app.add_handler(CommandHandler("supply", supply))
app.add_handler(CommandHandler("ranks", ranks))
app.add_handler(CommandHandler("search_pools", search_pools))
app.add_handler(CommandHandler("help", help))

app.run_polling()