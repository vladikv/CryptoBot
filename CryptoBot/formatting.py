def fmt_price(n) -> str:
    """$0.000123  або  $1,234.56"""
    if n is None:
        return "N/A"
    try:
        if n == 0:
            return "$0.00"
        if n < 0.001:
            return f"${n:.8f}"
        if n < 1:
            return f"${n:.4f}"
        return f"${n:,.2f}"
    except Exception:
        return str(n)


def fmt_large(n) -> str:
    """1234567890  →  $1.23B"""
    if n is None:
        return "N/A"
    try:
        if n >= 1_000_000_000_000:
            return f"${n / 1_000_000_000_000:.2f}T"
        if n >= 1_000_000_000:
            return f"${n / 1_000_000_000:.2f}B"
        if n >= 1_000_000:
            return f"${n / 1_000_000:.2f}M"
        return f"${n:,.0f}"
    except Exception:
        return str(n)


def fmt_supply(n) -> str:
    if n is None:
        return "N/A"
    try:
        return f"{n:,.0f}"
    except Exception:
        return str(n)


def fmt_change(pct) -> str:
    if pct is None:
        return "N/A"
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct:.2f}%"


def change_emoji(pct) -> str:
    if pct is None:
        return "⚪"
    return "🟢" if pct >= 0 else "🔴"