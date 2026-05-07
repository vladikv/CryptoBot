import logging
from datetime import datetime
from io import BytesIO

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from coingecko import get_price_chart, resolve_coin_id

logger = logging.getLogger(__name__)


def build_chart(coin: str, days: int = 7) -> BytesIO | None:
    coin_id = resolve_coin_id(coin)
    data = get_price_chart(coin_id, days)
    if not data or "prices" not in data:
        return None

    prices = data["prices"]
    if len(prices) < 2:
        return None

    timestamps = [datetime.fromtimestamp(p[0] / 1000) for p in prices]
    values     = [p[1] for p in prices]

    pct_change = (values[-1] - values[0]) / values[0] * 100
    color = "#00d4aa" if pct_change >= 0 else "#ff4757"
    sign  = "+" if pct_change >= 0 else ""

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#16213e")

    ax.plot(timestamps, values, color=color, linewidth=2)
    ax.fill_between(timestamps, values, alpha=0.15, color=color)

    locator = mdates.DayLocator() if days <= 30 else mdates.WeekdayLocator()
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    fig.autofmt_xdate()

    ax.tick_params(colors="#aaaaaa", labelsize=9)
    for spine in ax.spines.values():
        spine.set_edgecolor("#333355")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f"${x:,.0f}" if x >= 1 else f"${x:.4f}")
    )
    ax.set_ylabel("USD", color="#aaaaaa", fontsize=10)
    ax.set_title(
        f"{coin_id.upper()}  ·  {days}д  |  {sign}{pct_change:.2f}%",
        color="white", fontsize=14, pad=12,
    )


    min_i = values.index(min(values))
    max_i = values.index(max(values))
    for i, label in [(min_i, f"${min(values):,.2f}"), (max_i, f"${max(values):,.2f}")]:
        ax.annotate(
            label,
            xy=(timestamps[i], values[i]),
            xytext=(0, 10 if i == max_i else -16),
            textcoords="offset points",
            ha="center", fontsize=8, color="#dddddd",
            arrowprops=dict(arrowstyle="-", color="#555577", lw=0.8)
        )

    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=130, facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf