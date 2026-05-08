import os
import logging
from uuid import uuid4
import asyncio

from dotenv import load_dotenv
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    InlineQueryResultArticle, InputTextMessageContent,
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    InlineQueryHandler, ContextTypes, CallbackContext,
)
from telegram.error import TelegramError

from database import (
    init_db,
    db_add_watchlist, db_remove_watchlist, db_get_watchlist,
    db_add_alert, db_get_all_alerts, db_get_user_alerts, db_delete_alert,
    db_add_portfolio, db_get_portfolio, db_remove_portfolio,
    db_get_language, db_set_language,
)
from coingecko import resolve_coin_id, get_crypto_data, get_top_cryptos, get_exchange_rates
from charts import build_chart
from formatting import fmt_price, fmt_large, fmt_supply, fmt_change, change_emoji
from languages import t
from news import get_news
from ai_assistant import ask_ai, analyze_coin

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ══════════════════════════════ Helpers ══════════════════════════════════════

def lang(user_id: int) -> str:
    return db_get_language(user_id)


# ══════════════════════════════ Keyboards ════════════════════════════════════

def kb_main(user_id: int):
    l = lang(user_id)
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(l, "menu_ranks"),     callback_data="ranks"),
         InlineKeyboardButton(t(l, "menu_watchlist"), callback_data="wl_show")],
        [InlineKeyboardButton(t(l, "menu_alerts"),    callback_data="alerts_show"),
         InlineKeyboardButton(t(l, "menu_news"),      callback_data="news_show")],
        [InlineKeyboardButton(t(l, "menu_portfolio"), callback_data="portfolio_show"),
         InlineKeyboardButton(t(l, "menu_ai"),        callback_data="ai_show")],
        [InlineKeyboardButton(t(l, "menu_help"),      callback_data="help")],
    ])


def kb_coin(coin_id: str, user_id: int):
    l = lang(user_id)
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📈 Chart 7d",      callback_data=f"chart|{coin_id}|7"),
         InlineKeyboardButton("📉 Max/Min",        callback_data=f"highlow|{coin_id}")],
        [InlineKeyboardButton("💰 Supply",         callback_data=f"supply|{coin_id}"),
         InlineKeyboardButton("🔔 Alert",          callback_data=f"alert_setup|{coin_id}")],
        [InlineKeyboardButton("⭐ Add to Watchlist", callback_data=f"wl_add|{coin_id}"),
         InlineKeyboardButton("📰 News",           callback_data=f"news_coin|{coin_id}")],
        [InlineKeyboardButton("🔍 Analysis",  callback_data=f"analysis|{coin_id}"),
         InlineKeyboardButton("📰 News",      callback_data=f"news_coin|{coin_id}")],
        [InlineKeyboardButton(t(l, "back"),         callback_data="back_main")],
    ])


def kb_chart(coin_id: str):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("1d",  callback_data=f"chart|{coin_id}|1"),
        InlineKeyboardButton("7d",  callback_data=f"chart|{coin_id}|7"),
        InlineKeyboardButton("30d", callback_data=f"chart|{coin_id}|30"),
    ]])


def kb_back(user_id: int):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(t(lang(user_id), "back"), callback_data="back_main")
    ]])


def kb_language():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇺🇦 Українська", callback_data="lang|uk"),
         InlineKeyboardButton("🇬🇧 English",    callback_data="lang|en"),
         InlineKeyboardButton("🇪🇸 Español",    callback_data="lang|es")],
    ])


# ══════════════════════════════ Commands ══════════════════════════════════════

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    l   = lang(uid)
    await update.message.reply_text(
        t(l, "welcome"), parse_mode="Markdown", reply_markup=kb_main(uid)
    )


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await update.message.reply_text(
        t(lang(uid), "help_text"), parse_mode="Markdown", reply_markup=kb_back(uid)
    )


async def cmd_language(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await update.message.reply_text(
        t(lang(uid), "choose_language"), reply_markup=kb_language()
    )


async def cmd_data(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    l   = lang(uid)
    if not ctx.args:
        await update.message.reply_text(t(l, "specify_coin").format("/data BTC"), parse_mode="Markdown")
        return
    coin_id = resolve_coin_id(ctx.args[0])
    d = get_crypto_data(coin_id)
    if not d:
        await update.message.reply_text(t(l, "coin_not_found").format(ctx.args[0].upper()), parse_mode="Markdown")
        return
    await update.message.reply_text(_coin_text(d), parse_mode="Markdown", reply_markup=kb_coin(coin_id, uid))


def _coin_text(d: dict) -> str:
    change = d.get("price_change_percentage_24h")
    name = d['name'].replace('*', '').replace('_', '')
    return (
        f"*{name}* ({d['symbol'].upper()})\n\n"
        f"💵 Price: {fmt_price(d['current_price'])}\n"
        f"{change_emoji(change)} 24h Change: {fmt_change(change)}\n"
        f"📊 Market Cap: {fmt_large(d.get('market_cap'))}\n"
        f"🔄 24h Volume: {fmt_large(d.get('total_volume'))}\n"
        f"🏆 Rank: #{d.get('market_cap_rank', 'N/A')}"
    )


async def cmd_high_low(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    l   = lang(uid)
    if not ctx.args:
        await update.message.reply_text(t(l, "specify_coin").format("/high_low ETH"), parse_mode="Markdown")
        return
    coin_id = resolve_coin_id(ctx.args[0])
    d = get_crypto_data(coin_id)
    if not d:
        await update.message.reply_text(t(l, "coin_not_found").format(ctx.args[0].upper()), parse_mode="Markdown")
        return
    await update.message.reply_text(
        f"*{d['name']}* — 24h Max/Min\n\n"
        f"🔺 Maximum: {fmt_price(d.get('high_24h'))}\n"
        f"🔻 Minimum: {fmt_price(d.get('low_24h'))}",
        parse_mode="Markdown",
    )


async def cmd_supply(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    l   = lang(uid)
    if not ctx.args:
        await update.message.reply_text(t(l, "specify_coin").format("/supply SOL"), parse_mode="Markdown")
        return
    coin_id = resolve_coin_id(ctx.args[0])
    d = get_crypto_data(coin_id)
    if not d:
        await update.message.reply_text(t(l, "coin_not_found").format(ctx.args[0].upper()), parse_mode="Markdown")
        return
    await update.message.reply_text(
        f"*{d['name']}* — Supply\n\n"
        f"🔄 Circulating: {fmt_supply(d.get('circulating_supply'))}\n"
        f"📦 Total: {fmt_supply(d.get('total_supply'))}\n"
        f"🔒 Max Supply: {fmt_supply(d.get('max_supply'))}",
        parse_mode="Markdown",
    )


async def cmd_ranks(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid   = update.effective_user.id
    coins = get_top_cryptos()
    if not coins:
        await update.message.reply_text(t(lang(uid), "no_data"))
        return
    await update.message.reply_text(_ranks_text(coins), parse_mode="Markdown")


def _ranks_text(coins: list) -> str:
    medals = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
    lines  = ["🏆 Top-10 Cryptocurrencies\n"]
    for i, c in enumerate(coins):
        change = c.get("price_change_percentage_24h")
        name = c['name'].replace('*', '').replace('_', '')
        lines.append(
            f"{medals[i]} {name} ({c['symbol'].upper()})\n"
            f"   {fmt_price(c['current_price'])}  ·  {fmt_change(change)}"
        )
    return "\n".join(lines)

async def cmd_chart(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    l   = lang(uid)
    if not ctx.args:
        await update.message.reply_text(t(l, "specify_coin").format("/chart BTC or /chart BTC 30"), parse_mode="Markdown")
        return
    coin    = ctx.args[0]
    days    = int(ctx.args[1]) if len(ctx.args) > 1 else 7
    days    = max(1, min(days, 90))
    coin_id = resolve_coin_id(coin)

    msg = await update.message.reply_text(t(l, "chart_building"))
    buf = build_chart(coin_id, days)
    await msg.delete()
    if not buf:
        await update.message.reply_text(t(l, "coin_not_found").format(coin.upper()), parse_mode="Markdown")
        return
    await update.message.reply_photo(
        photo=buf,
        caption=t(l, "chart_caption").format(coin_id.upper(), days),
        parse_mode="Markdown",
        reply_markup=kb_chart(coin_id),
    )


async def cmd_convert(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    l   = lang(uid)
    if len(ctx.args) < 3:
        await update.message.reply_text("Usage: `/convert 1 BTC UAH`", parse_mode="Markdown")
        return
    try:
        amount   = float(ctx.args[0].replace(",", "."))
        from_sym = ctx.args[1]
        to_sym   = ctx.args[2].lower()
    except ValueError:
        await update.message.reply_text("❌ Invalid amount.", parse_mode="Markdown")
        return

    coin_id = resolve_coin_id(from_sym)
    d = get_crypto_data(coin_id)
    if not d:
        await update.message.reply_text(t(l, "coin_not_found").format(from_sym.upper()), parse_mode="Markdown")
        return

    price_usd = d["current_price"]
    if to_sym == "usd":
        await update.message.reply_text(
            f"💱 {amount} *{from_sym.upper()}* = *${amount * price_usd:,.4f}*",
            parse_mode="Markdown",
        )
        return

    rates = get_exchange_rates()
    if not rates or to_sym not in rates or "usd" not in rates:
        await update.message.reply_text(f"❌ Currency *{to_sym.upper()}* not found.", parse_mode="Markdown")
        return

    result = amount * price_usd * (rates[to_sym]["value"] / rates["usd"]["value"])
    await update.message.reply_text(
        f"💱 {amount} *{from_sym.upper()}* = *{result:,.2f} {to_sym.upper()}*",
        parse_mode="Markdown",
    )


async def cmd_alert(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    l   = lang(uid)
    if len(ctx.args) < 2:
        await update.message.reply_text("Usage: `/alert BTC 70000`", parse_mode="Markdown")
        return
    try:
        coin   = ctx.args[0]
        target = float(ctx.args[1].replace(",", "."))
    except ValueError:
        await update.message.reply_text("❌ Price must be a number.")
        return

    coin_id   = resolve_coin_id(coin)
    d         = get_crypto_data(coin_id)
    if not d:
        await update.message.reply_text(t(l, "coin_not_found").format(coin.upper()), parse_mode="Markdown")
        return

    current   = d["current_price"]
    direction = "above" if target > current else "below"
    db_add_alert(uid, coin_id, target, direction)

    arrow = "⬆️" if direction == "above" else "⬇️"
    await update.message.reply_text(
        t(l, "alert_set").format(
            d['name'], fmt_price(current), arrow, fmt_price(target),
            t(l, "alert_above") if direction == "above" else t(l, "alert_below")
        ),
        parse_mode="Markdown",
    )


async def cmd_alerts(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    l    = lang(uid)
    rows = db_get_user_alerts(uid)
    if not rows:
        await update.message.reply_text(t(l, "no_alerts"), parse_mode="Markdown")
        return
    lines   = [t(l, "my_alerts")]
    buttons = []
    for alert_id, coin, target, direction in rows:
        arrow = "⬆️" if direction == "above" else "⬇️"
        lines.append(f"{arrow} *{coin.upper()}* → {fmt_price(float(target))}")
        buttons.append([InlineKeyboardButton(
            f"{t(l, 'delete_alert')} {coin.upper()} {fmt_price(float(target))}",
            callback_data=f"del_alert|{alert_id}",
        )])
    await update.message.reply_text(
        "\n".join(lines), parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def cmd_watchlist(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    l    = lang(uid)
    args = ctx.args

    if not args:
        await _show_watchlist(update.message, uid)
        return

    action = args[0].lower()
    if action == "add" and len(args) > 1:
        coin_id = resolve_coin_id(args[1])
        d = get_crypto_data(coin_id)
        if not d:
            await update.message.reply_text(t(l, "coin_not_found").format(args[1].upper()), parse_mode="Markdown")
            return
        added = db_add_watchlist(uid, coin_id)
        msg = t(l, "watchlist_added" if added else "watchlist_exists").format(d['name'])
        await update.message.reply_text(msg, parse_mode="Markdown")
    elif action == "remove" and len(args) > 1:
        coin_id = resolve_coin_id(args[1])
        removed = db_remove_watchlist(uid, coin_id)
        msg = t(l, "watchlist_removed" if removed else "watchlist_not_found").format(coin_id.upper())
        await update.message.reply_text(msg, parse_mode="Markdown")
    else:
        await update.message.reply_text(
            "Usage:\n/watchlist\n/watchlist add BTC\n/watchlist remove BTC"
        )


async def _show_watchlist(message, user_id: int):
    l     = lang(user_id)
    coins = db_get_watchlist(user_id)
    if not coins:
        await message.reply_text(t(l, "watchlist_empty"), parse_mode="Markdown")
        return
    lines   = [t(l, "watchlist_title")]
    buttons = []
    for coin in coins:
        d = get_crypto_data(coin)
        if d:
            change = d.get("price_change_percentage_24h")
            lines.append(f"{change_emoji(change)} *{d['name']}*: {fmt_price(d['current_price'])}  {fmt_change(change)}")
        buttons.append([InlineKeyboardButton(f"❌ {coin.upper()}", callback_data=f"wl_remove|{coin}")])
    await message.reply_text(
        "\n".join(lines), parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def cmd_portfolio(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    l    = lang(uid)
    args = ctx.args

    if not args:
        await _show_portfolio(update.message, uid)
        return

    action = args[0].lower()

    if action == "add" and len(args) >= 4:
        try:
            coin      = args[1]
            amount    = float(args[2].replace(",", "."))
            buy_price = float(args[3].replace(",", "."))
        except ValueError:
            await update.message.reply_text("❌ Invalid format. Example: `/portfolio add BTC 0.5 45000`", parse_mode="Markdown")
            return
        coin_id = resolve_coin_id(coin)
        d = get_crypto_data(coin_id)
        if not d:
            await update.message.reply_text(t(l, "coin_not_found").format(coin.upper()), parse_mode="Markdown")
            return
        db_add_portfolio(uid, coin_id, amount, buy_price)
        await update.message.reply_text(t(l, "portfolio_added").format(d['name']), parse_mode="Markdown")

    elif action == "remove" and len(args) >= 2:
        try:
            entry_id = int(args[1])
        except ValueError:
            await update.message.reply_text("❌ Specify entry ID. See /portfolio")
            return
        removed = db_remove_portfolio(entry_id, uid)
        msg = t(l, "portfolio_removed").format(args[1]) if removed else "❌ Entry not found."
        await update.message.reply_text(msg, parse_mode="Markdown")
    else:
        await update.message.reply_text(
            "Usage:\n"
            "/portfolio — show\n"
            "/portfolio add BTC 0.5 45000\n"
            "/portfolio remove <ID>"
        )


async def _show_portfolio(message, user_id: int):
    l    = lang(user_id)
    rows = db_get_portfolio(user_id)
    if not rows:
        await message.reply_text(t(l, "portfolio_empty"), parse_mode="Markdown")
        return

    lines       = [t(l, "portfolio_title")]
    total_value = 0.0
    total_cost  = 0.0

    for entry_id, coin, amount, buy_price in rows:
        d = get_crypto_data(coin)
        if not d:
            continue
        current     = d["current_price"]
        value       = float(amount) * current
        cost        = float(amount) * float(buy_price)
        pnl         = value - cost
        pnl_pct     = (pnl / cost * 100) if cost > 0 else 0
        total_value += value
        total_cost  += cost
        emoji        = "🟢" if pnl >= 0 else "🔴"

        lines.append(
            f"\n{emoji} *{d['name']}* (ID:{entry_id})\n"
            f"   Amount: {float(amount):,.4f}\n"
            f"   Bought at: {fmt_price(float(buy_price))}\n"
            f"   Current: {fmt_price(current)}\n"
            f"   Value: {fmt_price(value)}\n"
            f"   P&L: {'+' if pnl >= 0 else ''}{fmt_price(pnl)} ({pnl_pct:+.2f}%)"
        )

    total_pnl     = total_value - total_cost
    total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0
    lines.append(t(l, "portfolio_total").format(
        fmt_price(total_value),
        f"{'+' if total_pnl >= 0 else ''}{fmt_price(total_pnl)}",
        f"{total_pnl_pct:+.2f}"
    ))

    await message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_news(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid         = update.effective_user.id
    l           = lang(uid)
    filter_coin = ctx.args[0].upper() if ctx.args else None

    msg = await update.message.reply_text(t(l, "news_loading"))
    articles = get_news(filter_coin)
    await msg.delete()

    if not articles:
        await update.message.reply_text(t(l, "news_not_found"), parse_mode="Markdown")
        return

    title = t(l, "news_title") if not filter_coin else f"📰 *News about {filter_coin}:*\n"
    lines = [title]
    for i, a in enumerate(articles, 1):
        lines.append(f"{i}. [{a['title']}]({a['link']})")

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown",
        disable_web_page_preview=True,
    )


async def cmd_ai(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    l   = lang(uid)

    if not ctx.args:
        await update.message.reply_text(t(l, "ai_intro"), parse_mode="Markdown")
        return

    question = " ".join(ctx.args)
    msg      = await update.message.reply_text(t(l, "ai_loading"))
    answer   = ask_ai(question, l)
    await msg.delete()
    await update.message.reply_text(answer)

async def cmd_analysis(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    l   = lang(uid)

    if not ctx.args:
        await update.message.reply_text(t(l, "analysis_intro"), parse_mode="Markdown")
        return

    coin    = ctx.args[0]
    coin_id = resolve_coin_id(coin)
    d       = get_crypto_data(coin_id)
    if not d:
        await update.message.reply_text(t(l, "coin_not_found").format(coin.upper()), parse_mode="Markdown")
        return

    msg    = await update.message.reply_text(t(l, "analysis_loading").format(d['name']))
    result = analyze_coin(coin_id, l)
    await msg.delete()
    await update.message.reply_text(result)

async def cmd_compare(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    l   = lang(uid)

    if len(ctx.args) < 2:
        await update.message.reply_text(t(l, "compare_usage"), parse_mode="Markdown")
        return

    coin1_id = resolve_coin_id(ctx.args[0])
    coin2_id = resolve_coin_id(ctx.args[1])
    d1 = get_crypto_data(coin1_id)
    d2 = get_crypto_data(coin2_id)

    if not d1:
        await update.message.reply_text(t(l, "coin_not_found").format(ctx.args[0].upper()), parse_mode="Markdown")
        return
    if not d2:
        await update.message.reply_text(t(l, "coin_not_found").format(ctx.args[1].upper()), parse_mode="Markdown")
        return

    def row(label, v1, v2):
        return f"*{label}*\n  {d1['symbol'].upper()}: {v1}\n  {d2['symbol'].upper()}: {v2}\n"

    c1 = d1.get("price_change_percentage_24h")
    c2 = d2.get("price_change_percentage_24h")

    text = (
            t(l, "compare_title").format(d1['name'], d2['name']) +
            "\n" +
            row("💵 Price", fmt_price(d1['current_price']), fmt_price(d2['current_price'])) +
            row(f"{change_emoji(c1)}{change_emoji(c2)} 24h Change", fmt_change(c1), fmt_change(c2)) +
            row("📊 Market Cap", fmt_large(d1.get('market_cap')), fmt_large(d2.get('market_cap'))) +
            row("🔄 24h Volume", fmt_large(d1.get('total_volume')), fmt_large(d2.get('total_volume'))) +
            row("🏆 Rank", f"#{d1.get('market_cap_rank','N/A')}", f"#{d2.get('market_cap_rank','N/A')}")
    )
    await update.message.reply_text(text, parse_mode="Markdown")


# ══════════════════════════ Callback Handler ══════════════════════════════════

async def on_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q    = update.callback_query
    await q.answer()
    data = q.data
    uid  = q.from_user.id
    l    = lang(uid)

    if data == "back_main":
        await q.edit_message_text(t(l, "welcome"), parse_mode="Markdown", reply_markup=kb_main(uid))

    elif data == "help":
        await q.edit_message_text(t(l, "help_text"), parse_mode="Markdown", reply_markup=kb_back(uid))

    elif data == "ranks":
        coins = get_top_cryptos()
        if coins:
            await q.edit_message_text(_ranks_text(coins), reply_markup=kb_back(uid))

    elif data == "news_show":
        msg      = await q.message.reply_text(t(l, "news_loading"))
        articles = get_news()
        await msg.delete()
        if not articles:
            await q.message.reply_text(t(l, "news_not_found"))
            return
        lines = [t(l, "news_title")]
        for i, a in enumerate(articles, 1):
            lines.append(f"{i}. [{a['title']}]({a['link']})")
        await q.message.reply_text("\n".join(lines), parse_mode="Markdown", disable_web_page_preview=True)

    elif data.startswith("news_coin|"):
        coin_id  = data.split("|", 1)[1]
        articles = get_news(coin_id.upper())
        if not articles:
            await q.message.reply_text(t(l, "news_not_found"))
            return
        lines = [f"📰 *News about {coin_id.upper()}:*\n"]
        for i, a in enumerate(articles, 1):
            lines.append(f"{i}. [{a['title']}]({a['link']})")
        await q.message.reply_text("\n".join(lines), parse_mode="Markdown", disable_web_page_preview=True)

    elif data == "ai_show":
        await q.message.reply_text(t(l, "ai_intro"), parse_mode="Markdown")

    elif data == "portfolio_show":
        await _show_portfolio(q.message, uid)

    elif data == "wl_show":
        await _show_watchlist(q.message, uid)

    elif data.startswith("wl_add|"):
        coin_id = data.split("|", 1)[1]
        db_add_watchlist(uid, coin_id)
        await q.answer(f"✅ {coin_id.upper()} added to Watchlist!", show_alert=True)

    elif data.startswith("wl_remove|"):
        coin_id = data.split("|", 1)[1]
        db_remove_watchlist(uid, coin_id)
        await q.edit_message_text(f"✅ *{coin_id.upper()}* removed from Watchlist.", parse_mode="Markdown")

    elif data == "alerts_show":
        rows = db_get_user_alerts(uid)
        if not rows:
            await q.edit_message_text(t(l, "no_alerts"), parse_mode="Markdown", reply_markup=kb_back(uid))
            return
        lines   = [t(l, "my_alerts")]
        buttons = []
        for alert_id, coin, target, direction in rows:
            arrow = "⬆️" if direction == "above" else "⬇️"
            lines.append(f"{arrow} *{coin.upper()}* → {fmt_price(float(target))}")
            buttons.append([InlineKeyboardButton(
                f"{t(l, 'delete_alert')} {coin.upper()} {fmt_price(float(target))}",
                callback_data=f"del_alert|{alert_id}",
            )])
        buttons.append([InlineKeyboardButton(t(l, "back"), callback_data="back_main")])
        await q.edit_message_text("\n".join(lines), parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith("del_alert|"):
        db_delete_alert(int(data.split("|", 1)[1]))
        await q.edit_message_text(t(l, "alert_deleted"), reply_markup=kb_back(uid))

    elif data.startswith("alert_setup|"):
        coin_id = data.split("|", 1)[1]
        await q.message.reply_text(
            f"🔔 `/alert {coin_id} <price>`", parse_mode="Markdown"
        )

    elif data.startswith("chart|"):
        _, coin_id, days_str = data.split("|")
        days = int(days_str)
        await q.message.reply_text(t(l, "chart_building"))
        buf = build_chart(coin_id, days)
        if buf:
            await q.message.reply_photo(
                photo=buf,
                caption=t(l, "chart_caption").format(coin_id.upper(), days),
                parse_mode="Markdown",
                reply_markup=kb_chart(coin_id),
            )
        else:
            await q.message.reply_text(t(l, "no_data"))

    elif data.startswith("highlow|"):
        coin_id = data.split("|", 1)[1]
        d = get_crypto_data(coin_id)
        if d:
            await q.message.reply_text(
                f"*{d['name']}* — 24h Max/Min\n\n"
                f"🔺 Maximum: {fmt_price(d.get('high_24h'))}\n"
                f"🔻 Minimum: {fmt_price(d.get('low_24h'))}",
                parse_mode="Markdown",
            )

    elif data.startswith("supply|"):
        coin_id = data.split("|", 1)[1]
        d = get_crypto_data(coin_id)
        if d:
            await q.message.reply_text(
                f"*{d['name']}* — Supply\n\n"
                f"🔄 Circulating: {fmt_supply(d.get('circulating_supply'))}\n"
                f"📦 Total: {fmt_supply(d.get('total_supply'))}\n"
                f"🔒 Max: {fmt_supply(d.get('max_supply'))}",
                parse_mode="Markdown",
            )

    elif data.startswith("lang|"):
        new_lang = data.split("|", 1)[1]
        db_set_language(uid, new_lang)
        await q.edit_message_text(t(new_lang, "language_changed"), parse_mode="Markdown")

    elif data.startswith("analysis|"):
        coin_id = data.split("|", 1)[1]
    d = get_crypto_data(coin_id)
    if not d:
        return
    l   = lang(uid)
    msg = await q.message.reply_text(t(l, "analysis_loading").format(d['name']))
    result = analyze_coin(coin_id, l)
    await msg.delete()
    await q.message.reply_text(result)

# ══════════════════════════ Inline mode ══════════════════════════════════════

async def inline_query_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query_text = update.inline_query.query.strip()
    if not query_text:
        return
    coin_id = resolve_coin_id(query_text)
    d = get_crypto_data(coin_id)
    if not d:
        return
    change = d.get("price_change_percentage_24h")
    text = (
        f"*{d['name']}* ({d['symbol'].upper()})\n\n"
        f"💵 {fmt_price(d['current_price'])}\n"
        f"{change_emoji(change)} {fmt_change(change)} 24h\n"
        f"📊 Market Cap: {fmt_large(d.get('market_cap'))}"
    )
    await update.inline_query.answer([
        InlineQueryResultArticle(
            id=str(uuid4()),
            title=f"{d['name']} — {fmt_price(d['current_price'])}",
            description=f"{fmt_change(change)} 24h · {fmt_large(d.get('market_cap'))}",
            input_message_content=InputTextMessageContent(text, parse_mode="Markdown"),
        )
    ], cache_time=30)


# ══════════════════════════ Background job ════════════════════════════════════

async def job_check_alerts(ctx: CallbackContext):
    alerts = db_get_all_alerts()
    for alert_id, user_id, coin, target, direction in alerts:
        d = get_crypto_data(coin)
        if not d:
            continue
        current   = d["current_price"]
        triggered = (
                (direction == "above" and current >= float(target)) or
                (direction == "below" and current <= float(target))
        )
        if not triggered:
            continue
        l     = lang(user_id)
        arrow = "⬆️" if direction == "above" else "⬇️"
        try:
            await ctx.bot.send_message(
                chat_id=user_id,
                text=t(l, "alert_triggered").format(
                    d['name'], fmt_price(float(target)), fmt_price(current), arrow
                ),
                parse_mode="Markdown",
            )
        except TelegramError as e:
            logger.error(f"Alert send error uid={user_id}: {e}")
        db_delete_alert(alert_id)


# ══════════════════════════ Run ═══════════════════════════════════════════════

def main():
    init_db()
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start",     cmd_start))
    app.add_handler(CommandHandler("help",      cmd_help))
    app.add_handler(CommandHandler("language",  cmd_language))
    app.add_handler(CommandHandler("data",      cmd_data))
    app.add_handler(CommandHandler("high_low",  cmd_high_low))
    app.add_handler(CommandHandler("supply",    cmd_supply))
    app.add_handler(CommandHandler("ranks",     cmd_ranks))
    app.add_handler(CommandHandler("chart",     cmd_chart))
    app.add_handler(CommandHandler("convert",   cmd_convert))
    app.add_handler(CommandHandler("alert",     cmd_alert))
    app.add_handler(CommandHandler("alerts",    cmd_alerts))
    app.add_handler(CommandHandler("watchlist", cmd_watchlist))
    app.add_handler(CommandHandler("portfolio", cmd_portfolio))
    app.add_handler(CommandHandler("news",      cmd_news))
    app.add_handler(CommandHandler("ai",        cmd_ai))
    app.add_handler(CommandHandler("compare",   cmd_compare))
    app.add_handler(CommandHandler("analysis", cmd_analysis))

    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(InlineQueryHandler(inline_query_handler))

    app.job_queue.run_repeating(job_check_alerts, interval=120, first=15)

    logger.info("CryptoBot started ✅")
    asyncio.run(app.run_polling())


if __name__ == "__main__":
    main()