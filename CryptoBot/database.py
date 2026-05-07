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
    """Створює таблиці якщо не існують."""
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
    ]
    try:
        conn = get_connection()
        cur = conn.cursor()
        for stmt in ddl:
            cur.execute(stmt)
        cur.close()
        conn.close()
        logger.info("DB initialized OK")
    except Error as e:
        logger.error(f"DB init error: {e}")
        raise


# ── Watchlist ────────────────────────────────────────────────────────────────

def db_add_watchlist(user_id: int, coin: str) -> bool:
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT IGNORE INTO watchlist (user_id, coin) VALUES (%s, %s)",
            (user_id, coin)
        )
        affected = cur.rowcount
        cur.close(); conn.close()
        return affected > 0
    except Error as e:
        logger.error(f"db_add_watchlist: {e}")
        return False


def db_remove_watchlist(user_id: int, coin: str) -> bool:
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM watchlist WHERE user_id=%s AND coin=%s",
            (user_id, coin)
        )
        affected = cur.rowcount
        cur.close(); conn.close()
        return affected > 0
    except Error as e:
        logger.error(f"db_remove_watchlist: {e}")
        return False


def db_get_watchlist(user_id: int) -> list[str]:
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT coin FROM watchlist WHERE user_id=%s ORDER BY added_at",
            (user_id,)
        )
        rows = [r[0] for r in cur.fetchall()]
        cur.close(); conn.close()
        return rows
    except Error as e:
        logger.error(f"db_get_watchlist: {e}")
        return []


# ── Alerts ───────────────────────────────────────────────────────────────────

def db_add_alert(user_id: int, coin: str, target: float, direction: str) -> int | None:
    try:
        conn = get_connection()
        cur = conn.cursor()
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
        cur = conn.cursor()
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
        cur = conn.cursor()
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
        cur = conn.cursor()
        cur.execute("DELETE FROM alerts WHERE id=%s", (alert_id,))
        affected = cur.rowcount
        cur.close(); conn.close()
        return affected > 0
    except Error as e:
        logger.error(f"db_delete_alert: {e}")
        return False