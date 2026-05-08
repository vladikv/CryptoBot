import os
import logging
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

DB_CONFIG = {
    "host":       os.getenv("DB_HOST", "localhost"),
    "port":       int(os.getenv("DB_PORT", 3306)),
    "user":       os.getenv("DB_USER", "root"),
    "password":   os.getenv("DB_PASSWORD", ""),
    "database":   os.getenv("DB_NAME", "cryptobot"),
    "charset":    "utf8mb4",
    "autocommit": True,
}


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def init_db():
    ddl = [
        """
        CREATE TABLE IF NOT EXISTS watchlist (
                                                 user_id  BIGINT      NOT NULL,
                                                 coin     VARCHAR(64) NOT NULL,
            added_at DATETIME    DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, coin)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,
        """
        CREATE TABLE IF NOT EXISTS alerts (
                                              id           INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                                              user_id      BIGINT        NOT NULL,
                                              coin         VARCHAR(64)   NOT NULL,
            target_price DECIMAL(20,8) NOT NULL,
            direction    ENUM('above','below') NOT NULL,
            created_at   DATETIME      DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_user (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,
        """
        CREATE TABLE IF NOT EXISTS portfolio (
                                                 id         INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                                                 user_id    BIGINT        NOT NULL,
                                                 coin       VARCHAR(64)   NOT NULL,
            amount     DECIMAL(20,8) NOT NULL,
            buy_price  DECIMAL(20,8) NOT NULL,
            added_at   DATETIME      DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_user (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,
        """
        CREATE TABLE IF NOT EXISTS user_settings (
                                                     user_id  BIGINT      PRIMARY KEY,
                                                     language VARCHAR(8)  DEFAULT 'uk'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,
    ]
    try:
        conn = get_connection()
        cur  = conn.cursor()
        for stmt in ddl:
            cur.execute(stmt)
        cur.close()
        conn.close()
        logger.info("DB initialized OK")
    except Error as e:
        logger.error(f"DB init error: {e}")
        raise


# ── Watchlist ─────────────────────────────────────────────────────────────────

def db_add_watchlist(user_id: int, coin: str) -> bool:
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute("INSERT IGNORE INTO watchlist (user_id, coin) VALUES (%s, %s)", (user_id, coin))
        affected = cur.rowcount
        cur.close(); conn.close()
        return affected > 0
    except Error as e:
        logger.error(f"db_add_watchlist: {e}")
        return False


def db_remove_watchlist(user_id: int, coin: str) -> bool:
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute("DELETE FROM watchlist WHERE user_id=%s AND coin=%s", (user_id, coin))
        affected = cur.rowcount
        cur.close(); conn.close()
        return affected > 0
    except Error as e:
        logger.error(f"db_remove_watchlist: {e}")
        return False


def db_get_watchlist(user_id: int) -> list[str]:
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute("SELECT coin FROM watchlist WHERE user_id=%s ORDER BY added_at", (user_id,))
        rows = [r[0] for r in cur.fetchall()]
        cur.close(); conn.close()
        return rows
    except Error as e:
        logger.error(f"db_get_watchlist: {e}")
        return []


# ── Alerts ────────────────────────────────────────────────────────────────────

def db_add_alert(user_id: int, coin: str, target: float, direction: str) -> int | None:
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute(
            "INSERT INTO alerts (user_id, coin, target_price, direction) VALUES (%s,%s,%s,%s)",
            (user_id, coin, target, direction)
        )
        new_id = cur.lastrowid
        cur.close(); conn.close()
        return new_id
    except Error as e:
        logger.error(f"db_add_alert: {e}")
        return None


def db_get_all_alerts() -> list[tuple]:
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute("SELECT id, user_id, coin, target_price, direction FROM alerts")
        rows = cur.fetchall()
        cur.close(); conn.close()
        return rows
    except Error as e:
        logger.error(f"db_get_all_alerts: {e}")
        return []


def db_get_user_alerts(user_id: int) -> list[tuple]:
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute(
            "SELECT id, coin, target_price, direction FROM alerts WHERE user_id=%s ORDER BY created_at",
            (user_id,)
        )
        rows = cur.fetchall()
        cur.close(); conn.close()
        return rows
    except Error as e:
        logger.error(f"db_get_user_alerts: {e}")
        return []


def db_delete_alert(alert_id: int) -> bool:
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute("DELETE FROM alerts WHERE id=%s", (alert_id,))
        affected = cur.rowcount
        cur.close(); conn.close()
        return affected > 0
    except Error as e:
        logger.error(f"db_delete_alert: {e}")
        return False


# ── Portfolio ─────────────────────────────────────────────────────────────────

def db_add_portfolio(user_id: int, coin: str, amount: float, buy_price: float) -> bool:
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute(
            "INSERT INTO portfolio (user_id, coin, amount, buy_price) VALUES (%s,%s,%s,%s)",
            (user_id, coin, amount, buy_price)
        )
        cur.close(); conn.close()
        return True
    except Error as e:
        logger.error(f"db_add_portfolio: {e}")
        return False


def db_get_portfolio(user_id: int) -> list[tuple]:
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute(
            "SELECT id, coin, amount, buy_price FROM portfolio WHERE user_id=%s ORDER BY added_at",
            (user_id,)
        )
        rows = cur.fetchall()
        cur.close(); conn.close()
        return rows
    except Error as e:
        logger.error(f"db_get_portfolio: {e}")
        return []


def db_remove_portfolio(entry_id: int, user_id: int) -> bool:
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute("DELETE FROM portfolio WHERE id=%s AND user_id=%s", (entry_id, user_id))
        affected = cur.rowcount
        cur.close(); conn.close()
        return affected > 0
    except Error as e:
        logger.error(f"db_remove_portfolio: {e}")
        return False


# ── User Language ─────────────────────────────────────────────────────────────

def db_get_language(user_id: int) -> str:
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute("SELECT language FROM user_settings WHERE user_id=%s", (user_id,))
        row = cur.fetchone()
        cur.close(); conn.close()
        return row[0] if row else "uk"
    except Error as e:
        logger.error(f"db_get_language: {e}")
        return "uk"


def db_set_language(user_id: int, lang: str):
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute(
            "INSERT INTO user_settings (user_id, language) VALUES (%s,%s) "
            "ON DUPLICATE KEY UPDATE language=%s",
            (user_id, lang, lang)
        )
        cur.close(); conn.close()
    except Error as e:
        logger.error(f"db_set_language: {e}")