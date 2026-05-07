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
)
from coingecko import (
    resolve_coin_id, get_crypto_data, get_top_cryptos, get_exchange_rates,
)
from charts import build_chart
from formatting import fmt_price, fmt_large, fmt_supply, fmt_change, change_emoji

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ══════════════════════════════ Keyboards ════════════════════════════════════

def kb_main():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Top-10",       callback_data="ranks"),
         InlineKeyboardButton("⭐ Watchlist",    callback_data="wl_show")],
        [InlineKeyboardButton("🔔 My Alerts",    callback_data="alerts_show"),
         InlineKeyboardButton("❓ Help",          callback_data="help")],
    ])


def kb_coin(coin_id: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📈 Chart 7d",     callback_data=f"chart|{coin_id}|7"),
         InlineKeyboardButton("📉 Max/Min",      callback_data=f"highlow|{coin_id}")],
        [InlineKeyboardButton("💰 Supply",       callback_data=f"supply|{coin_id}"),
         InlineKeyboardButton("🔔 Alert",        callback_data=f"alert_setup|{coin_id}")],
        [InlineKeyboardButton("⭐ To Watchlist", callback_data=f"wl_add|{coin_id}"),
         InlineKeyboardButton("◀️ Menu",         callback_data="back_main")],
    ])


def kb_chart(coin_id: str):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("1d",  callback_data=f"chart|{coin_id}|1"),
        InlineKeyboardButton("7d",  callback_data=f"chart|{coin_id}|7"),
        InlineKeyboardButton("30d", callback_data=f"chart|{coin_id}|30"),
    ]])


def kb_back():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("◀️ Back", callback_data="back_main")
    ]])


# ══════════════════════════════ Commands ═════════════════════════════════════

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hello! I'm *CryptoBot*.\n\n"
        "I show prices, charts, and notify you about target prices.\n"
        "Type a coin symbol or choose an action below:",
        parse_mode="Markdown",
        reply_markup=kb_main(),
    )


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        _help_text(), parse_mode="Markdown", reply_markup=kb_back()
    )


def _help_text() -> str:
    return (
        "📋 *Commands:*\n\n"
        "/data `<coin>` — price and statistics\n"
        "/high\\_low `<coin>` — 24h max/min\n"
        "/supply `<coin>` — coin supply\n"
        "/chart `<coin> [days]` — chart (1/7/30)\n"
        "/ranks — top-10 by market cap\n"
        "/convert `<amount> <coin> <currency>` — converter\n"
        "/alert `<coin> <price>` — price alert\n"
        "/alerts — my active alerts\n"
        "/watchlist — favorites list\n"
        "/watchlist add `<coin>`\n"
        "/watchlist remove `<coin>`\n\n"
        "💡 Symbols: BTC, ETH, SOL, DOGE…\n"
        "💡 Inline: `@your_bot bitcoin` in any chat"
    )


async def cmd_data(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Specify a coin: `/data BTC`", parse_mode="Markdown")
        return
    coin_id = resolve_coin_id(ctx.args[0])
    d = get_crypto_data(coin_id)
    if not d:
        await update.message.reply_text(
            f"❌ Coin *{ctx.args[0].upper()}* not found.", parse_mode="Markdown"
        )
        return
    await update.message.reply_text(
        _coin_text(d), parse_mode="Markdown", reply_markup=kb_coin(coin_id)
    )


def _coin_text(d: dict) -> str:
    change = d.get("price_change_percentage_24h")
    return (
        f"*{d['name']}* ({d['symbol'].upper()})\n\n"
        f"💵 Price: {fmt_price(d['current_price'])}\n"
        f"{change_emoji(change)} Change 24h: {fmt_change(change)}\n"
        f"📊 Market Cap: {fmt_large(d.get('market_cap'))}\n"
        f"🔄 Volume 24h: {fmt_large(d.get('total_volume'))}\n"
        f"🏆 Rank: #{d.get('market_cap_rank', 'N/A')}"
    )


async def cmd_high_low(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Specify a coin: `/high_low ETH`", parse_mode="Markdown")
        return
    coin_id = resolve_coin_id(ctx.args[0])
    d = get_crypto_data(coin_id)
    if not d:
        await update.message.reply_text(
            f"❌ *{ctx.args[0].upper()}* not found.", parse_mode="Markdown"
        )
        return
    await update.message.reply_text(
        f"*{d['name']}* — 24h max/min\n\n"
        f"🔺 Maximum: {fmt_price(d.get('high_24h'))}\n"
        f"🔻 Minimum: {fmt_price(d.get('low_24h'))}",
        parse_mode="Markdown",
    )


async def cmd_supply(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Specify a coin: `/supply SOL`", parse_mode="Markdown")
        return
    coin_id = resolve_coin_id(ctx.args[0])
    d = get_crypto_data(coin_id)
    if not d:
        await update.message.reply_text(
            f"❌ *{ctx.args[0].upper()}* not found.", parse_mode="Markdown"
        )
        return
    await update.message.reply_text(
        f"*{d['name']}* — supply\n\n"
        f"🔄 Circulating: {fmt_supply(d.get('circulating_supply'))}\n"
        f"📦 Total: {fmt_supply(d.get('total_supply'))}\n"
        f"🔒 Max supply: {fmt_supply(d.get('max_supply'))}",
        parse_mode="Markdown",
    )


async def cmd_ranks(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    coins = get_top_cryptos()
    if not coins:
        await update.message.reply_text("❌ Failed to retrieve data.")
        return
    await update.message.reply_text(_ranks_text(coins), parse_mode="Markdown")


def _ranks_text(coins: list) -> str:
    medals = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
    lines  = ["🏆 *Top-10 Cryptocurrencies*\n"]
    for i, c in enumerate(coins):
        change = c.get("price_change_percentage_24h")
        lines.append(
            f"{medals[i]} *{c['name']}* ({c['symbol'].upper()})\n"
            f"   {fmt_price(c['current_price'])}  ·  {fmt_change(change)}"
        )
    return "\n".join(lines)


async def cmd_chart(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text(
            "Specify a coin: `/chart BTC` or `/chart BTC 30`", parse_mode="Markdown"
        )
        return
    coin  = ctx.args[0]
    days  = int(ctx.args[1]) if len(ctx.args) > 1 else 7
    days  = max(1, min(days, 90))
    coin_id = resolve_coin_id(coin)

    msg = await update.message.reply_text("⏳ Building chart…")
    buf = build_chart(coin_id, days)
    await msg.delete()
    if not buf:
        await update.message.reply_text(
            f"❌ No data for *{coin.upper()}*.", parse_mode="Markdown"
        )
        return
    await update.message.reply_photo(
        photo=buf,
        caption=f"📈 *{coin_id.upper()}* — {days}d",
        parse_mode="Markdown",
        reply_markup=kb_chart(coin_id),
    )


async def cmd_convert(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if len(ctx.args) < 3:
        await update.message.reply_text(
            "Usage: `/convert 1 BTC UAH`", parse_mode="Markdown"
        )
        return
    try:
        amount  = float(ctx.args[0].replace(",", "."))
        from_sym = ctx.args[1]
        to_sym   = ctx.args[2].lower()
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid amount. Example: `/convert 0.5 ETH UAH`", parse_mode="Markdown"
        )
        return

    coin_id = resolve_coin_id(from_sym)
    d = get_crypto_data(coin_id)
    if not d:
        await update.message.reply_text(
            f"❌ Coin *{from_sym.upper()}* not found.", parse_mode="Markdown"
        )
        return

    price_usd = d["current_price"]

    if to_sym == "usd":
        result = amount * price_usd
        await update.message.reply_text(
            f"💱 {amount} *{from_sym.upper()}* = *${result:,.4f}*",
            parse_mode="Markdown",
        )
        return

    rates = get_exchange_rates()
    if not rates or to_sym not in rates or "usd" not in rates:
        await update.message.reply_text(
            f"❌ Currency *{to_sym.upper()}* not found.", parse_mode="Markdown"
        )
        return

    usd_rate    = rates["usd"]["value"]
    target_rate = rates[to_sym]["value"]
    result = amount * price_usd * (target_rate / usd_rate)

    await update.message.reply_text(
        f"💱 {amount} *{from_sym.upper()}* = *{result:,.2f} {to_sym.upper()}*",
        parse_mode="Markdown",
    )


async def cmd_alert(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if len(ctx.args) < 2:
        await update.message.reply_text(
            "Usage: `/alert BTC 70000`\n"
            "The bot will notify you when the price reaches the target.",
            parse_mode="Markdown",
        )
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
        await update.message.reply_text(
            f"❌ *{coin.upper()}* not found.", parse_mode="Markdown"
        )
        return

    current   = d["current_price"]
    direction = "above" if target > current else "below"
    db_add_alert(update.effective_user.id, coin_id, target, direction)

    arrow = "⬆️" if direction == "above" else "⬇️"
    await update.message.reply_text(
        f"🔔 Alert set!\n\n"
        f"*{d['name']}*\n"
        f"Current: {fmt_price(current)}\n"
        f"{arrow} Target: {fmt_price(target)}\n\n"
        f"I'll notify you when the price {'exceeds' if direction == 'above' else 'falls below'} this level.",
        parse_mode="Markdown",
    )


async def cmd_alerts(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    rows = db_get_user_alerts(update.effective_user.id)
    if not rows:
        await update.message.reply_text(
            "No active alerts.\n\nSet one: `/alert BTC 70000`",
            parse_mode="Markdown",
        )
        return
    lines   = ["🔔 *Your alerts:*\n"]
    buttons = []
    for alert_id, coin, target, direction in rows:
        arrow = "⬆️" if direction == "above" else "⬇️"
        lines.append(f"{arrow} *{coin.upper()}* → {fmt_price(float(target))}")
        buttons.append([InlineKeyboardButton(
            f"❌ {coin.upper()} {fmt_price(float(target))}",
            callback_data=f"del_alert|{alert_id}",
        )])
    await update.message.reply_text(
        "\n".join(lines), parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def cmd_watchlist(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args    = ctx.args

    if not args:
        await _show_watchlist(update.message, user_id)
        return

    action = args[0].lower()
    if action == "add" and len(args) > 1:
        coin_id = resolve_coin_id(args[1])
        d = get_crypto_data(coin_id)
        if not d:
            await update.message.reply_text(
                f"❌ *{args[1].upper()}* not found.", parse_mode="Markdown"
            )
            return
        added = db_add_watchlist(user_id, coin_id)
        msg = (f"✅ *{d['name']}* added to Watchlist!"
               if added else f"ℹ️ *{d['name']}* is already in Watchlist.")
        await update.message.reply_text(msg, parse_mode="Markdown")

    elif action == "remove" and len(args) > 1:
        coin_id = resolve_coin_id(args[1])
        removed = db_remove_watchlist(user_id, coin_id)
        msg = (f"✅ *{coin_id.upper()}* removed."
               if removed else f"ℹ️ *{coin_id.upper()}* is not in Watchlist.")
        await update.message.reply_text(msg, parse_mode="Markdown")
    else:
        await update.message.reply_text(
            "Usage:\n/watchlist\n/watchlist add BTC\n/watchlist remove BTC"
        )


async def _show_watchlist(message, user_id: int):
    coins = db_get_watchlist(user_id)
    if not coins:
        await message.reply_text(
            "⭐ Watchlist is empty.\nAdd: `/watchlist add BTC`",
            parse_mode="Markdown",
        )
        return
    lines   = ["⭐ *Your Watchlist:*\n"]
    buttons = []
    for coin in coins:
        d = get_crypto_data(coin)
        if d:
            change = d.get("price_change_percentage_24h")
            lines.append(
                f"{change_emoji(change)} *{d['name']}*: "
                f"{fmt_price(d['current_price'])}  {fmt_change(change)}"
            )
        buttons.append([InlineKeyboardButton(
            f"❌ {coin.upper()}", callback_data=f"wl_remove|{coin}"
        )])
    await message.reply_text(
        "\n".join(lines), parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


# ══════════════════════════ Callback Handler ══════════════════════════════════

async def on_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q    = update.callback_query
    await q.answer()
    data = q.data

    if data == "back_main":
        await q.edit_message_text("👋 Main Menu", reply_markup=kb_main())

    elif data == "help":
        await q.edit_message_text(
            _help_text(), parse_mode="Markdown", reply_markup=kb_back()
        )

    elif data == "ranks":
        coins = get_top_cryptos()
        if coins:
            await q.edit_message_text(
                _ranks_text(coins), parse_mode="Markdown", reply_markup=kb_back()
            )

    elif data == "wl_show":
        coins = db_get_watchlist(q.from_user.id)
        if not coins:
            await q.edit_message_text(
                "⭐ Watchlist is empty.\n/watchlist add BTC", reply_markup=kb_back()
            )
            return
        lines   = ["⭐ *Your Watchlist:*\n"]
        buttons = []
        for coin in coins:
            d = get_crypto_data(coin)
            if d:
                change = d.get("price_change_percentage_24h")
                lines.append(
                    f"{change_emoji(change)} *{d['name']}*: "
                    f"{fmt_price(d['current_price'])}  {fmt_change(change)}"
                )
            buttons.append([InlineKeyboardButton(
                f"❌ {coin.upper()}", callback_data=f"wl_remove|{coin}"
            )])
        buttons.append([InlineKeyboardButton("◀️ Back", callback_data="back_main")])
        await q.edit_message_text(
            "\n".join(lines), parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    elif data.startswith("wl_add|"):
        coin_id = data.split("|", 1)[1]
        db_add_watchlist(q.from_user.id, coin_id)
        await q.answer(f"✅ {coin_id.upper()} added to Watchlist!", show_alert=True)

    elif data.startswith("wl_remove|"):
        coin_id = data.split("|", 1)[1]
        db_remove_watchlist(q.from_user.id, coin_id)
        await q.edit_message_text(
            f"✅ *{coin_id.upper()}* removed from Watchlist.", parse_mode="Markdown"
        )

    elif data == "alerts_show":
        rows = db_get_user_alerts(q.from_user.id)
        if not rows:
            await q.edit_message_text(
                "No active alerts.\n`/alert BTC 70000`",
                parse_mode="Markdown", reply_markup=kb_back(),
            )
            return
        lines   = ["🔔 *Your alerts:*\n"]
        buttons = []
        for alert_id, coin, target, direction in rows:
            arrow = "⬆️" if direction == "above" else "⬇️"
            lines.append(f"{arrow} *{coin.upper()}* → {fmt_price(float(target))}")
            buttons.append([InlineKeyboardButton(
                f"❌ {coin.upper()} {fmt_price(float(target))}",
                callback_data=f"del_alert|{alert_id}",
            )])
        buttons.append([InlineKeyboardButton("◀️ Back", callback_data="back_main")])
        await q.edit_message_text(
            "\n".join(lines), parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    elif data.startswith("del_alert|"):
        alert_id = int(data.split("|", 1)[1])
        db_delete_alert(alert_id)
        await q.edit_message_text("✅ Alert deleted.", reply_markup=kb_back())

    elif data.startswith("alert_setup|"):
        coin_id = data.split("|", 1)[1]
        await q.message.reply_text(
            f"🔔 Set an alert for *{coin_id.upper()}*:\n"
            f"`/alert {coin_id} <price>`",
            parse_mode="Markdown",
        )

    elif data.startswith("chart|"):
        _, coin_id, days_str = data.split("|")
        days = int(days_str)
        await q.message.reply_text("⏳ Building chart…")
        buf = build_chart(coin_id, days)
        if buf:
            await q.message.reply_photo(
                photo=buf,
                caption=f"📈 *{coin_id.upper()}* — {days}d",
                parse_mode="Markdown",
                reply_markup=kb_chart(coin_id),
            )
        else:
            await q.message.reply_text("❌ Failed to build chart.")

    elif data.startswith("highlow|"):
        coin_id = data.split("|", 1)[1]
        d = get_crypto_data(coin_id)
        if d:
            await q.message.reply_text(
                f"*{d['name']}* — 24h max/min\n\n"
                f"🔺 Maximum: {fmt_price(d.get('high_24h'))}\n"
                f"🔻 Minimum: {fmt_price(d.get('low_24h'))}",
                parse_mode="Markdown",
            )

    elif data.startswith("supply|"):
        coin_id = data.split("|", 1)[1]
        d = get_crypto_data(coin_id)
        if d:
            await q.message.reply_text(
                f"*{d['name']}* — supply\n\n"
                f"🔄 Circulating: {fmt_supply(d.get('circulating_supply'))}\n"
                f"📦 Total: {fmt_supply(d.get('total_supply'))}\n"
                f"🔒 Max: {fmt_supply(d.get('max_supply'))}",
                parse_mode="Markdown",
            )


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
        f"{change_emoji(change)} {fmt_change(change)} over 24h\n"
        f"📊 Market Cap: {fmt_large(d.get('market_cap'))}"
    )
    await update.inline_query.answer([
        InlineQueryResultArticle(
            id=str(uuid4()),
            title=f"{d['name']} — {fmt_price(d['current_price'])}",
            description=f"{fmt_change(change)} over 24h · {fmt_large(d.get('market_cap'))}",
            input_message_content=InputTextMessageContent(
                text, parse_mode="Markdown"
            ),
        )
    ], cache_time=30)


# ══════════════════════════ Background job ═══════════════════════════════════

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
        arrow = "⬆️" if direction == "above" else "⬇️"
        try:
            await ctx.bot.send_message(
                chat_id=user_id,
                text=(
                    f"🔔 *Alert triggered!*\n\n"
                    f"*{d['name']}* reached {fmt_price(float(target))}\n"
                    f"Current: {fmt_price(current)} {arrow}"
                ),
                parse_mode="Markdown",
            )
        except TelegramError as e:
            logger.error(f"Alert send error uid={user_id}: {e}")
        db_delete_alert(alert_id)


# ══════════════════════════ Startup ══════════════════════════════════════════

def main():
    init_db()

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start",     cmd_start))
    app.add_handler(CommandHandler("help",      cmd_help))
    app.add_handler(CommandHandler("data",      cmd_data))
    app.add_handler(CommandHandler("high_low",  cmd_high_low))
    app.add_handler(CommandHandler("supply",    cmd_supply))
    app.add_handler(CommandHandler("ranks",     cmd_ranks))
    app.add_handler(CommandHandler("chart",     cmd_chart))
    app.add_handler(CommandHandler("convert",   cmd_convert))
    app.add_handler(CommandHandler("alert",     cmd_alert))
    app.add_handler(CommandHandler("alerts",    cmd_alerts))
    app.add_handler(CommandHandler("watchlist", cmd_watchlist))

    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(InlineQueryHandler(inline_query_handler))

    # Check alerts every 2 minutes
    app.job_queue.run_repeating(job_check_alerts, interval=120, first=15)

    logger.info("CryptoBot started ✅")
    asyncio.run(app.run_polling())


if __name__ == "__main__":
    main()
