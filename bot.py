"""Telegram storefront and salon intake for Space of Beauty by Gromova."""
import html
import json
import logging
import os
import re
import sqlite3
import threading
import time
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import telebot
from telebot import types

TOKEN = os.getenv("TOKEN", "").strip()
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "").strip()
if not TOKEN or not ADMIN_CHAT_ID:
    raise RuntimeError("Set TOKEN and ADMIN_CHAT_ID in Render")
ADMIN_CHAT_ID = int(ADMIN_CHAT_ID)
ADMIN_LINK = "https://t.me/beautyspace_admin"
bot = telebot.TeleBot(TOKEN, parse_mode="HTML", threaded=False)
BOT_DISPLAY_NAME = "Space of Beauty by Gromova | Прайс • Запис • Вільні вікна"
BOT_DESCRIPTION = "Послуги • актуальний прайс • вільні вікна • запис • зв’язок з адміністратором"
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent
with (BASE_DIR / "eg_catalog.json").open(encoding="utf-8") as catalog_file:
    PRODUCT_DETAILS = json.load(catalog_file)
with (BASE_DIR / "salon_catalog.json").open(encoding="utf-8") as catalog_file:
    SALON_DETAILS = json.load(catalog_file)
PRODUCT_DETAILS.update(SALON_DETAILS)


# User analytics and mailing database.
# Primary storage is Neon Postgres via DATABASE_URL. SQLite is a local fallback only.
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
USE_POSTGRES = bool(DATABASE_URL)

if USE_POSTGRES:
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError:
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg[binary]>=3.2,<4"])
        import psycopg
        from psycopg.rows import dict_row

DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))
DATA_DIR.mkdir(parents=True, exist_ok=True)
USER_DB_PATH = Path(os.getenv("USER_DB_PATH", str(DATA_DIR / "users.sqlite3")))
DB_LOCK = threading.Lock()
pending_broadcasts = {}

ENTRY_NOTICE = (
    "<b>Бажаєте увійти до бота?</b>\n\n"
    "Натискаючи «Так, увійти», ви погоджуєтесь з обробкою технічних даних "
    "для роботи бота та внутрішньої статистики. Деталі: /privacy"
)

PRIVACY_TEXT = (
    "<b>Конфіденційність</b>\n\n"
    "Під час взаємодії з ботом Telegram передає технічні дані, зокрема chat_id, "
    "ім'я та username, якщо він є. Бот може зберігати дату першого й останнього "
    "звернення та інформацію про те, які розділи відкривалися, щоб підтримувати "
    "роботу сервісу, бачити загальну статистику та розуміти інтерес до послуг "
    "салону, навчання й професійних матеріалів.\n\n"
    "Телефон та інші контактні дані зберігаються лише тоді, коли ви самі надсилаєте "
    "їх у заявці або замовленні. Дані не публікуються у відкритому доступі.\n\n"
    "За вашою згодою бот надсилає рекламні повідомлення про послуги салону та косметику "
    "EG BY GROMOVA. Якщо згодом ви захочете відписатися від розсилки, надішліть боту "
    "команду /unsubscribe.\n\n"
    "З питань щодо даних можна звернутися до адміністратора: " + ADMIN_LINK
)

EVENT_LABELS = {
    "start": "Запустили бот",
    "salon": "Салон",
    "training": "Навчання GRAY FUSION",
    "gray_channel": "Канал про сивину",
    "windows": "Вільні вікна",
    "price": "Прайс",
    "booking": "Запис / консультація",
    "shop": "Магазин",
    "pro_care": "Для салонів краси",
    "cart": "Кошик",
    "contact": "Адміністратор",
}


def sqlite_connect():
    conn = sqlite3.connect(str(USER_DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def pg_connect():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def init_user_db():
    with DB_LOCK:
        if USE_POSTGRES:
            with pg_connect() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        chat_id BIGINT PRIMARY KEY,
                        username TEXT,
                        first_name TEXT,
                        last_name TEXT,
                        first_seen TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        last_seen TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        is_client BOOLEAN NOT NULL DEFAULT FALSE,
                        is_master BOOLEAN NOT NULL DEFAULT FALSE,
                        opted_out BOOLEAN NOT NULL DEFAULT FALSE,
                        blocked BOOLEAN NOT NULL DEFAULT FALSE,
                        interactions INTEGER NOT NULL DEFAULT 0,
                        consent_at TIMESTAMPTZ
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS events (
                        id BIGSERIAL PRIMARY KEY,
                        chat_id BIGINT NOT NULL REFERENCES users(chat_id) ON DELETE CASCADE,
                        event TEXT NOT NULL,
                        ts TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_events_chat ON events(chat_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_users_last_seen ON users(last_seen)")
                conn.execute("DELETE FROM events WHERE chat_id = %s", (ADMIN_CHAT_ID,))
                conn.execute("DELETE FROM users WHERE chat_id = %s", (ADMIN_CHAT_ID,))
        else:
            with sqlite_connect() as conn:
                conn.executescript("""
                    CREATE TABLE IF NOT EXISTS users (
                        chat_id INTEGER PRIMARY KEY,
                        username TEXT,
                        first_name TEXT,
                        last_name TEXT,
                        first_seen TEXT NOT NULL,
                        last_seen TEXT NOT NULL,
                        is_client INTEGER NOT NULL DEFAULT 0,
                        is_master INTEGER NOT NULL DEFAULT 0,
                        opted_out INTEGER NOT NULL DEFAULT 0,
                        blocked INTEGER NOT NULL DEFAULT 0,
                        interactions INTEGER NOT NULL DEFAULT 0,
                        consent_at TEXT
                    );
                    CREATE TABLE IF NOT EXISTS events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        chat_id INTEGER NOT NULL,
                        event TEXT NOT NULL,
                        ts TEXT NOT NULL
                    );
                    CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts);
                    CREATE INDEX IF NOT EXISTS idx_events_chat ON events(chat_id);
                """)
                columns = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
                if "consent_at" not in columns:
                    conn.execute("ALTER TABLE users ADD COLUMN consent_at TEXT")
                conn.execute("DELETE FROM events WHERE chat_id = ?", (ADMIN_CHAT_ID,))
                conn.execute("DELETE FROM users WHERE chat_id = ?", (ADMIN_CHAT_ID,))


def now_dt():
    return datetime.now(ZoneInfo("Europe/Kyiv"))


def now_iso():
    return now_dt().isoformat(timespec="seconds")


def register_user(chat_id, user=None, event=None, client=False, master=False):
    if int(chat_id) == ADMIN_CHAT_ID:
        return
    username = getattr(user, "username", None) if user else None
    first_name = getattr(user, "first_name", None) if user else None
    last_name = getattr(user, "last_name", None) if user else None
    ts = now_dt()
    with DB_LOCK:
        if USE_POSTGRES:
            with pg_connect() as conn:
                conn.execute(
                    """
                    INSERT INTO users (
                        chat_id, username, first_name, last_name, first_seen, last_seen,
                        is_client, is_master, blocked, interactions
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, FALSE, 1)
                    ON CONFLICT(chat_id) DO UPDATE SET
                        username = COALESCE(EXCLUDED.username, users.username),
                        first_name = COALESCE(EXCLUDED.first_name, users.first_name),
                        last_name = COALESCE(EXCLUDED.last_name, users.last_name),
                        last_seen = EXCLUDED.last_seen,
                        is_client = users.is_client OR EXCLUDED.is_client,
                        is_master = users.is_master OR EXCLUDED.is_master,
                        blocked = FALSE,
                        interactions = users.interactions + 1
                    """,
                    (
                        int(chat_id), username, first_name, last_name, ts, ts,
                        bool(client), bool(master),
                    ),
                )
                if event:
                    conn.execute(
                        "INSERT INTO events (chat_id, event, ts) VALUES (%s, %s, %s)",
                        (int(chat_id), event, ts),
                    )
        else:
            iso = ts.isoformat(timespec="seconds")
            with sqlite_connect() as conn:
                conn.execute(
                    """
                    INSERT INTO users (
                        chat_id, username, first_name, last_name, first_seen, last_seen,
                        is_client, is_master, blocked, interactions
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 1)
                    ON CONFLICT(chat_id) DO UPDATE SET
                        username = COALESCE(excluded.username, users.username),
                        first_name = COALESCE(excluded.first_name, users.first_name),
                        last_name = COALESCE(excluded.last_name, users.last_name),
                        last_seen = excluded.last_seen,
                        is_client = MAX(users.is_client, excluded.is_client),
                        is_master = MAX(users.is_master, excluded.is_master),
                        blocked = 0,
                        interactions = users.interactions + 1
                    """,
                    (
                        int(chat_id), username, first_name, last_name, iso, iso,
                        int(bool(client)), int(bool(master)),
                    ),
                )
                if event:
                    conn.execute(
                        "INSERT INTO events (chat_id, event, ts) VALUES (?, ?, ?)",
                        (int(chat_id), event, iso),
                    )


def track_message(message, event=None, client=False, master=False):
    if not message or message.chat.type != "private":
        return
    register_user(message.chat.id, message.from_user, event, client, master)


def track_callback(call, event=None, client=False, master=False):
    if not call or not call.message or call.message.chat.type != "private":
        return
    register_user(call.message.chat.id, call.from_user, event, client, master)


def set_consent(chat_id):
    if int(chat_id) == ADMIN_CHAT_ID:
        return
    ts = now_dt()
    with DB_LOCK:
        if USE_POSTGRES:
            with pg_connect() as conn:
                conn.execute(
                    "UPDATE users SET consent_at = COALESCE(consent_at, %s), last_seen = %s WHERE chat_id = %s",
                    (ts, ts, int(chat_id)),
                )
        else:
            iso = ts.isoformat(timespec="seconds")
            with sqlite_connect() as conn:
                conn.execute(
                    "UPDATE users SET consent_at = COALESCE(consent_at, ?), last_seen = ? WHERE chat_id = ?",
                    (iso, iso, int(chat_id)),
                )


def has_consent(chat_id):
    if int(chat_id) == ADMIN_CHAT_ID:
        return True
    with DB_LOCK:
        if USE_POSTGRES:
            with pg_connect() as conn:
                row = conn.execute(
                    "SELECT consent_at FROM users WHERE chat_id = %s",
                    (int(chat_id),),
                ).fetchone()
        else:
            with sqlite_connect() as conn:
                row = conn.execute(
                    "SELECT consent_at FROM users WHERE chat_id = ?",
                    (int(chat_id),),
                ).fetchone()
    return bool(row and row["consent_at"])


def send_entry_prompt(chat_id):
    actions = types.InlineKeyboardMarkup()
    actions.add(types.InlineKeyboardButton("Так, увійти", callback_data="enter:yes"))
    bot.send_message(chat_id, ENTRY_NOTICE, reply_markup=actions)


def set_role(chat_id, role):
    if role not in ("client", "master"):
        return
    ts = now_dt()
    with DB_LOCK:
        if USE_POSTGRES:
            with pg_connect() as conn:
                if role == "client":
                    conn.execute(
                        "UPDATE users SET is_client = TRUE, last_seen = %s WHERE chat_id = %s",
                        (ts, int(chat_id)),
                    )
                else:
                    conn.execute(
                        "UPDATE users SET is_master = TRUE, last_seen = %s WHERE chat_id = %s",
                        (ts, int(chat_id)),
                    )
        else:
            iso = ts.isoformat(timespec="seconds")
            with sqlite_connect() as conn:
                if role == "client":
                    conn.execute(
                        "UPDATE users SET is_client = 1, last_seen = ? WHERE chat_id = ?",
                        (iso, int(chat_id)),
                    )
                else:
                    conn.execute(
                        "UPDATE users SET is_master = 1, last_seen = ? WHERE chat_id = ?",
                        (iso, int(chat_id)),
                    )


def user_has_segment(chat_id):
    with DB_LOCK:
        if USE_POSTGRES:
            with pg_connect() as conn:
                row = conn.execute(
                    "SELECT is_client, is_master FROM users WHERE chat_id = %s",
                    (int(chat_id),),
                ).fetchone()
        else:
            with sqlite_connect() as conn:
                row = conn.execute(
                    "SELECT is_client, is_master FROM users WHERE chat_id = ?",
                    (int(chat_id),),
                ).fetchone()
    return bool(row and (row["is_client"] or row["is_master"]))


def set_opt_out(chat_id, opted_out):
    ts = now_dt()
    with DB_LOCK:
        if USE_POSTGRES:
            with pg_connect() as conn:
                conn.execute(
                    "UPDATE users SET opted_out = %s, last_seen = %s WHERE chat_id = %s",
                    (bool(opted_out), ts, int(chat_id)),
                )
        else:
            iso = ts.isoformat(timespec="seconds")
            with sqlite_connect() as conn:
                conn.execute(
                    "UPDATE users SET opted_out = ?, last_seen = ? WHERE chat_id = ?",
                    (int(bool(opted_out)), iso, int(chat_id)),
                )


def mark_blocked(chat_id):
    with DB_LOCK:
        if USE_POSTGRES:
            with pg_connect() as conn:
                conn.execute("UPDATE users SET blocked = TRUE WHERE chat_id = %s", (int(chat_id),))
        else:
            with sqlite_connect() as conn:
                conn.execute("UPDATE users SET blocked = 1 WHERE chat_id = ?", (int(chat_id),))


def recipient_rows(segment):
    filters_pg = ["opted_out = FALSE", "blocked = FALSE", "consent_at IS NOT NULL"]
    filters_sq = ["opted_out = 0", "blocked = 0", "consent_at IS NOT NULL"]
    if segment == "clients":
        filters_pg.append("is_client = TRUE")
        filters_sq.append("is_client = 1")
    elif segment == "masters":
        filters_pg.append("is_master = TRUE")
        filters_sq.append("is_master = 1")
    elif segment == "both":
        filters_pg.extend(["is_client = TRUE", "is_master = TRUE"])
        filters_sq.extend(["is_client = 1", "is_master = 1"])
    elif segment != "all":
        return []
    with DB_LOCK:
        if USE_POSTGRES:
            with pg_connect() as conn:
                return conn.execute(
                    "SELECT chat_id FROM users WHERE " + " AND ".join(filters_pg) + " ORDER BY chat_id"
                ).fetchall()
        with sqlite_connect() as conn:
            return conn.execute(
                "SELECT chat_id FROM users WHERE " + " AND ".join(filters_sq) + " ORDER BY chat_id"
            ).fetchall()


def stats_text():
    now = now_dt()
    week = now - timedelta(days=7)
    month = now - timedelta(days=30)
    today = now.date()
    with DB_LOCK:
        if USE_POSTGRES:
            with pg_connect() as conn:
                row = conn.execute(
                    """
                    SELECT
                        COUNT(*) AS total,
                        COUNT(*) FILTER (WHERE is_client) AS clients,
                        COUNT(*) FILTER (WHERE is_master) AS masters,
                        COUNT(*) FILTER (WHERE is_client AND is_master) AS both_roles,
                        COUNT(*) FILTER (WHERE NOT is_client AND NOT is_master) AS unknown_role,
                        COUNT(*) FILTER (WHERE opted_out) AS opted_out,
                        COUNT(*) FILTER (WHERE blocked) AS blocked,
                        COUNT(*) FILTER (WHERE last_seen >= %s) AS active_7,
                        COUNT(*) FILTER (WHERE last_seen >= %s) AS active_30,
                        COUNT(*) FILTER (WHERE first_seen::date = %s) AS new_today,
                        COUNT(*) FILTER (WHERE first_seen >= %s) AS new_7
                    FROM users
                    WHERE consent_at IS NOT NULL
                    """,
                    (week, month, today, week),
                ).fetchone()
                top = conn.execute(
                    """
                    SELECT event, COUNT(*) AS qty
                    FROM events
                    WHERE ts >= %s
                    GROUP BY event
                    ORDER BY qty DESC
                    LIMIT 8
                    """,
                    (month,),
                ).fetchall()
        else:
            week_s = week.isoformat(timespec="seconds")
            month_s = month.isoformat(timespec="seconds")
            with sqlite_connect() as conn:
                row = conn.execute(
                    """
                    SELECT
                        COUNT(*) AS total,
                        SUM(CASE WHEN is_client = 1 THEN 1 ELSE 0 END) AS clients,
                        SUM(CASE WHEN is_master = 1 THEN 1 ELSE 0 END) AS masters,
                        SUM(CASE WHEN is_client = 1 AND is_master = 1 THEN 1 ELSE 0 END) AS both_roles,
                        SUM(CASE WHEN is_client = 0 AND is_master = 0 THEN 1 ELSE 0 END) AS unknown_role,
                        SUM(CASE WHEN opted_out = 1 THEN 1 ELSE 0 END) AS opted_out,
                        SUM(CASE WHEN blocked = 1 THEN 1 ELSE 0 END) AS blocked,
                        SUM(CASE WHEN last_seen >= ? THEN 1 ELSE 0 END) AS active_7,
                        SUM(CASE WHEN last_seen >= ? THEN 1 ELSE 0 END) AS active_30,
                        SUM(CASE WHEN substr(first_seen, 1, 10) = ? THEN 1 ELSE 0 END) AS new_today,
                        SUM(CASE WHEN first_seen >= ? THEN 1 ELSE 0 END) AS new_7
                    FROM users
                    WHERE consent_at IS NOT NULL
                    """,
                    (week_s, month_s, today.isoformat(), week_s),
                ).fetchone()
                top = conn.execute(
                    """
                    SELECT event, COUNT(*) AS qty
                    FROM events
                    WHERE ts >= ?
                    GROUP BY event
                    ORDER BY qty DESC
                    LIMIT 8
                    """,
                    (month_s,),
                ).fetchall()
    lines = [
        "<b>Статистика Telegram-бота</b>",
        "",
        f"Усього користувачів: <b>{row['total'] or 0}</b>",
        f"Клієнти / інтерес до салону: <b>{row['clients'] or 0}</b>",
        f"Майстри / інтерес до навчання: <b>{row['masters'] or 0}</b>",
        f"І клієнти, і майстри: <b>{row['both_roles'] or 0}</b>",
        f"Ще не визначені: <b>{row['unknown_role'] or 0}</b>",
        "",
        f"Нові сьогодні: <b>{row['new_today'] or 0}</b>",
        f"Нові за 7 днів: <b>{row['new_7'] or 0}</b>",
        f"Активні за 7 днів: <b>{row['active_7'] or 0}</b>",
        f"Активні за 30 днів: <b>{row['active_30'] or 0}</b>",
        f"Відмовилися від розсилок: <b>{row['opted_out'] or 0}</b>",
        f"Заблокували бот: <b>{row['blocked'] or 0}</b>",
    ]
    if top:
        lines.extend(["", "<b>Що відкривали за 30 днів:</b>"])
        for item in top:
            label = EVENT_LABELS.get(item["event"], item["event"])
            lines.append(f"• {html.escape(label)} — {item['qty']}")
    return "\n".join(lines)


def broadcast_worker(admin_chat_id, segment, body, photo_file_id=None):
    rows = recipient_rows(segment)
    sent = failed = blocked = 0
    message = html.escape(body) + "\n\nЩоб не отримувати розсилки від бота: /unsubscribe"
    for row in rows:
        chat_id = int(row["chat_id"])
        try:
            if photo_file_id:
                # Telegram photo captions are limited to 1024 characters.
                # Send the original photo and complete text as consecutive messages.
                bot.send_photo(chat_id, photo_file_id)
            bot.send_message(chat_id, message, disable_web_page_preview=True)
            sent += 1
        except Exception as exc:
            failed += 1
            code = getattr(exc, "error_code", None)
            lowered = str(exc).lower()
            if code == 403 or "blocked" in lowered or "forbidden" in lowered:
                mark_blocked(chat_id)
                blocked += 1
        time.sleep(0.05)
    bot.send_message(
        admin_chat_id,
        "<b>Розсилка завершена</b>\n"
        f"Надіслано: {sent}\n"
        f"Не доставлено: {failed}\n"
        f"Заблокували бот: {blocked}",
    )


init_user_db()

HOME = "🏠 Головне меню"
BACK = "⬅️ Назад"
SALON = "Салон"
SHOP = "Магазин косметики"
CART = "🧺 Кошик"
CONTACT = "Зв'язатися з адміністратором"
PRICE = "Прайс салону"
TEAM = "👥 Наша команда"
SALON_INTRO = "🏡 Знайомство з салоном"
MAP_MENU = "📍 Як нас знайти"
WINDOWS = "Найближчі вільні вікна"
HAIRCUT = "Стрижка"
BOOK = "📝 Консультація / запис"
HOME_CARE = "Домашній догляд"
COLOR_BOX = "Color Box"
TRAINING = "🎓 Навчання для майстрів"
GRAY_CHANNEL = "GRAY FUSION | Все про сивину"
GRAY_CHANNEL_URL = "https://t.me/gromova_sedina_kiev"
PRO_CARE = "Для салонів краси"
CLEAR = "Очистити кошик"
CHECKOUT = "✅ Оформити замовлення"
CANCEL = "Скасувати"
REMOVE = "Прибрати товар"

# Only a confirmed price is shown. The administrator confirms all other
# prices, volumes and stock before taking payment.
PRODUCTS = {
    "Шампунь EG №1 Очищення, 400 мл": 1200,
    "Шампунь EG №2 Баланс, 400 мл": 1200,
    "Зволожувальний бальзам EG, 250 мл": 1200,
    "Кондиціонер EG, 400 мл": 1200,
    "Відновлювальний спрей EG, 250 мл": 1200,
    "Термозахист EG, 100 мл": 1200,
    "Маска EG Step 1 — ліпідна, 250 мл": 1200,
    "Маска EG Step 2 — амінокератинова, 250 мл": 1200,
    "Маска EG Step 3 — протеїнова, 250 мл": 1200,
    "Тонуюча маска by Gromova, 250 мл": 1000,
    "Color Box для прикореневої зони, 60 мл": 1800,
    "Color Box для довжини": 3500,
}
for name, details in SALON_DETAILS.items():
    PRODUCTS[name] = details.get("price", PRODUCTS.get(name))
HOME_PRODUCTS = [
    "Маска EG Step 1 — ліпідна, 250 мл",
    "Маска EG Step 2 — амінокератинова, 250 мл",
    "Маска EG Step 3 — протеїнова, 250 мл",
    "Зволожувальний бальзам EG, 250 мл",
    "Відновлювальний спрей EG, 250 мл",
    "Шампунь EG №1 Очищення, 400 мл",
    "Шампунь EG №2 Баланс, 400 мл",
    "Кондиціонер EG, 400 мл",
    "Термозахист EG, 100 мл",
]
CATEGORIES = {
    HOME_CARE: HOME_PRODUCTS,
    COLOR_BOX: [name for name in PRODUCTS if name.startswith("Color Box")],
    PRO_CARE: list(SALON_DETAILS),
}

product_category = {name: category for category, names in CATEGORIES.items() for name in names}
SERVICES = {
    "GRAY FUSION — робота із сивиною":
        "GRAY FUSION — фарбування за природним малюнком сивини\n\nМи повторюємо розташування вашої сивини по довжині, поєднуючи світлі та темні пасма. Кількість світлого підбираємо відповідно до кількості сивини, а натуральний корінь не фарбуємо. Завдяки цьому колір плавно відростає без різкої межі, і вам не потрібно зафарбовувати корені кожні 3–4 тижні.\n\nРобота займає приблизно 6–10 годин.\n\nОрієнтовна вартість:\n• 1 довжина — 11 000–12 000 грн\n• 2 довжина — 13 000–14 000 грн\n• 3 довжина — 15 000–16 000 грн\n• 4 довжина — 16 000–17 000 грн\n\nЯкщо волосся раніше фарбували в темний колір, попередньо потрібна змивка. Її виконуємо в окремий день, тому на таку роботу потрібно виділити два дні. Вартість змивки розраховується додатково.\n\nПеред записом обов’язкова консультація з адміністратором, щоб уточнити вартість і спланувати візити з урахуванням вашої довжини, густоти та попередніх фарбувань.\n\nПісля GRAY FUSION потрібно приходити на контроль кольору та догляд раз на 3–4 місяці, максимум через 4,5 місяця. На цих візитах ми оцінюємо стан волосся й за потреби освіжаємо відтінок.",
    "Камуфляж сивини":
        "Камуфляж сивини\n\nПоверхневе тонування сивини у прикореневій зоні. Залежно від бажаного результату можна надати сивині теплішого відтінку без затемнення або злегка «припилити» її на 1–2 тони.\n\nКамуфляж виконується лише на прикореневій зоні до 3 см.\n\nЯкщо у вас повністю натуральне волосся, перед процедурою потрібна консультація з майстром, щоб визначити, чи підходить вам камуфляж і який результат можна отримати.\n\nВартість — 3000 грн за прикореневу зону до 3 см.",
    "Тонування волосся":
        "Тонування волосся\n\nВиконуємо тонування кислим барвником Redken.\n\nВартість — 3000–4000 грн.\nТривалість — 2,5–3 години.\n\nЯкщо додатково потрібна нейтралізація небажаного відтінку або вирівнювання кольору, доплата становить 500–1000 грн.\n\nПеред записом потрібна консультація з адміністратором або майстром, щоб уточнити необхідні етапи роботи та остаточну вартість.",
    "Реконструкція 8D by Gromova":
        "Реконструкція 8D by Gromova\n\nПоетапний салонний догляд для сухого, пористого, освітленого та пошкодженого волосся. Допомагає зменшити жорсткість і сплутування, повернути м’якість, еластичність, гладкість та блиск.\n\nЩо означає «наповнити волосся»?\nПісля освітлення або частих фарбувань волосся може відчуватися сухим, шорстким і «порожнім». Під час процедури ми послідовно працюємо з ліпідним доглядом, амінокислотами, протеїнами та зволоженням. Волосся стає більш щільним і пружним на дотик, краще ковзає та легше розчісується.\n\nП’ять етапів догляду:\n1. Ліпіди й цераміди — пом’якшують пористі ділянки, згладжують поверхню та зменшують тертя.\n2. Амінокислотний спрей — зволожує й готує волосся до наступного протеїнового етапу.\n3. Кератин і протеїни — додають відчуття щільності та пружності, покращують стан пошкодженої поверхні.\n4. Інтенсивне зволоження — допомагає утримувати вологу, підтримує гнучкість і зменшує пухнастість.\n5. Фінальне розгладжування — надає блиск, полегшує розчісування та завершує догляд.\n\nМайстер оцінює стан волосся перед процедурою. Результат і його тривалість залежать від початкового пошкодження та домашнього догляду.\n\nТривалість:\n• Окрема реконструкція — до 2 годин.\n• Разом із тонуванням — приблизно 2–2,5 години, іноді до 3 годин.\n\nВартість окремої реконструкції:\n• 1 довжина — 3000 грн\n• 2 довжина — 3500 грн\n• 3 довжина — 4000 грн\n• 4 довжина — 4500 грн\n• 5 довжина — 5000 грн\n\nТонування оплачується додатково. Вашу категорію довжини та загальну вартість комплексу уточнить адміністратор перед записом.",
    "Вихід із темного / чорного":
        "Вихід із темного / чорного\n\nДля волосся, раніше пофарбованого в темний або чорний колір. Працюємо з накопиченим штучним пігментом, щоб перейти до світлішого відтінку або виконати обрану техніку фарбування.\n\nРоботу розділяємо на два дні.\n\nПерший день — приблизно 4–5 годин.\nВиконуємо змивку косметичного пігменту, реконструкцію та попередню підготовку волосся до наступного етапу.\n\nДругий день — приблизно 6–10 годин.\nВиконуємо саме фарбування за узгодженим із майстром планом: необхідне освітлення, обрану техніку та тонування.\n\nНаскільки світлим може бути результат, залежить від стану волосся, попередніх фарбувань і накопиченого пігменту. Бажаний відтінок та можливості волосся обговорюємо з майстром до початку роботи.\n\nОрієнтовна вартість за два дні роботи:\n• 1 довжина — 15 000–16 000 грн\n• 2 довжина — 17 000–18 000 грн\n• 3 довжина — 21 000–22 000 грн\n• 4 довжина — 23 000–24 000 грн\n• 5 довжина — 25 000–26 000 грн\n\nПеред записом потрібна консультація. Остаточну вартість і план роботи майстер визначає після огляду волосся в салоні. Адміністратор допоможе записатися на консультацію та узгодити два дні для процедури.",
    "Розгладжування MODIFIX Dr. Sorbie":
        "Розгладжування MODIFIX Dr. Sorbie\n\nПроцедура для пористого, пухнастого та неслухняного волосся. Допомагає зменшити прояви надмірної пористості, зробити волосся більш гладким, слухняним і зручним в укладанні.\n\nЕфект м’якший, ніж після кератинового випрямлення: волосся зберігає об’єм, його можна накручувати. Вираженого ефекту повністю прямого волосся немає.\n\nПідходить для блонду, натурального, фарбованого й темного волосся. Особливо актуальна для пористого волосся після інтенсивних освітлень або виходу з чорного кольору. Перед процедурою майстер оцінює стан волосся та підбирає догляд.\n\nТривалість процедури — близько 3 годин.\nЕфект зберігається до 3 місяців залежно від стану волосся та домашнього догляду.\n\nВартість:\n• 1 довжина — 5000 грн\n• 2 довжина — 5500 грн\n• 3 довжина — 6000 грн\n• 4 довжина — 6500 грн\n• 5 довжина — 7000 грн\n\nВашу категорію довжини та вартість уточнимо перед записом.",
    HAIRCUT:
        "Стрижка жіноча — 1200 грн.\n"
        "Стрижка чоловіча — 1200 грн.\n"
        "Стрижка чубчика — 500 грн.\n\n"
        "Стрижка в Олени Громової — 1500 грн.\n"
        "Олена працює лише в комплексі з реконструкцією волосся. "
        "Реконструкція оплачується додатково й не входить у 1500 грн. "
        "Вартість реконструкції та загальну суму комплексу уточнить адміністратор перед записом.",
    "Інші послуги":
        "Інші послуги\n\nНаші майстри мають понад 10 років досвіду та володіють усіма техніками фарбування, зокрема:\n• AirTouch\n• Balayage\n• Шатуш\n• Мелірування\n• Однотонне фарбування\n\nЩоб підібрати техніку саме для вас, потрібна консультація. Розкажіть, який результат хочете отримати, — ми проконсультуємо щодо вашого випадку та зорієнтуємо у вартості.\n\nЗалиште заявку через кнопку «📝 Консультація / запис» або напишіть адміністратору: https://t.me/beautyspace_admin",
}
# Per-process state; an interrupted Render restart resets unfinished dialogs.
carts = {}
flows = {}
selection = {}
section = {}
ORDER_FIELDS = [
    ("first_name", "Ваше ім'я?"),
    ("last_name", "Ваше прізвище для Нової пошти?"),
    ("phone", "Номер телефону у форматі +380XXXXXXXXX?"),
    ("city", "Місто доставки?"),
    ("delivery", "Відділення чи поштомат Нової пошти?"),
    ("number", "Номер відділення або поштомату?"),
]
TEAM_BOOK_FIELDS = [
    ("service", "На яку послугу хочете записатися?"),
    ("when", "На яку дату або час вам було б зручно?"),
    ("name", "Як до вас звертатися?"),
    ("phone", "Залиште номер телефону у форматі +380XXXXXXXXX."),
]
BOOK_FIELDS = [
    ("name", "Як до вас звертатися?"),
    ("phone", "Залиште номер телефону у форматі +380XXXXXXXXX."),
    ("service", "Яка послуга вас цікавить? Можна коротко описати волосся і бажаний результат."),
    ("when", "Коли вам зручно прийти? Напишіть бажані дні або час."),
]

def keyboard(rows):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for row in rows:
        kb.row(*row)
    return kb

def menu(chat_id):
    section[chat_id] = "main"
    bot.send_message(chat_id, "Вітаємо у Space of Beauty by Gromova. Оберіть розділ:",
                     reply_markup=keyboard([[SALON, SHOP], [TRAINING], [GRAY_CHANNEL], [CART], [MAP_MENU], [CONTACT]]))


SALON_MAP_URL = (
    "https://www.google.com/maps/dir/?api=1"
    "&destination=%D0%9F%D1%80%D0%B8%D1%80%D1%96%D1%87%D0%BD%D0%B0+27%D0%95%2C+"
    "%D0%9A%D0%B8%D1%97%D0%B2%2C+%D0%A3%D0%BA%D1%80%D0%B0%D1%97%D0%BD%D0%B0"
)
SALON_INTRO_TEXT = (
    "<b>Знайомство зі Space of Beauty by Gromova 🤍</b>\n\n"
    "Ми знаходимося в Києві, на Оболоні, за адресою: вул. Прирічна, 27Е, "
    "просто біля набережної.\n\n"
    "У нас затишний, просторий салон із красивим краєвидом із вікон. "
    "Поки ми займаємося вашим волоссям, ви можете милуватися набережною "
    "та спостерігати за корабликами, що пропливають повз.\n\n"
    "Ми знаємо, що деякі процедури тривають 6–10 годин, тому подбали про "
    "те, щоб вам було комфортно протягом усього візиту.\n\n"
    "🚗 <b>Власна парковка</b>\n"
    "Приїжджайте на автомобілі. Біля салону є власна парковка для наших клієнтів.\n\n"
    "👘 <b>Турбота про ваш одяг</b>\n"
    "Кожному клієнту ми пропонуємо переодягнутися у спеціальний халат. "
    "Ваш одяг залишиться чистим, не забрудниться фарбою та не помнеться під час процедури.\n\n"
    "☕ <b>Чай, кава та смачна їжа</b>\n"
    "Ми завжди запропонуємо вам чай або каву. Якщо ви прийшли на тривале фарбування, "
    "можете замовити доставку їжі прямо до салону або попросити адміністратора "
    "допомогти із замовленням. Не соромтеся їсти під час перебування у нас!\n\n"
    "💻 <b>Працюйте, поки ми займаємося вашим волоссям</b>\n"
    "У салоні є Wi-Fi. Можете взяти ноутбук, працювати, відповідати на повідомлення "
    "та займатися своїми справами під час фарбування.\n\n"
    "⚡ <b>Ми готові до відключень світла та води</b>\n"
    "У салоні встановлений генератор, а також є запас води об'ємом 1000 літрів. "
    "Тому навіть під час відключень електроенергії ми можемо продовжувати роботу "
    "та виконувати заплановані процедури.\n\n"
    "У Space of Beauty by Gromova можна відпочивати, працювати, пити каву, "
    "обідати та просто насолоджуватися часом, поки ми займаємося вашим волоссям.\n\n"
    "Будемо раді бачити вас у нашому салоні! 🤍"
)


def show_salon_intro(chat_id):
    section[chat_id] = "salon_intro"
    image_path = BASE_DIR / "images/salon/salon-intro.jpg"
    if image_path.is_file():
        with image_path.open("rb") as photo:
            bot.send_photo(chat_id, photo, caption="Space of Beauty by Gromova 🤍")
    else:
        log.warning("Salon intro image not found: %s", image_path)
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📍 Як нас знайти", url=SALON_MAP_URL),
        types.InlineKeyboardButton("📝 Записатися", callback_data="salon_intro:book"),
    )
    markup.add(types.InlineKeyboardButton("🏠 Головне меню", callback_data="salon_intro:home"))
    bot.send_message(chat_id, SALON_INTRO_TEXT, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "enter:yes")
def enter_bot(call):
    if not call.message or call.message.chat.type != "private":
        bot.answer_callback_query(call.id)
        return
    register_user(call.message.chat.id, call.from_user, event="start")
    set_consent(call.message.chat.id)
    bot.answer_callback_query(call.id, "Готово")
    menu(call.message.chat.id)


@bot.callback_query_handler(func=lambda call: bool(call.data and call.data.startswith("role:")))
def role_callback(call):
    if not call.message or call.message.chat.type != "private":
        bot.answer_callback_query(call.id)
        return
    role = call.data.partition(":")[2]
    if role not in ("client", "master"):
        bot.answer_callback_query(call.id)
        return
    track_callback(call, event="salon" if role == "client" else "training",
                   client=role == "client", master=role == "master")
    set_role(call.message.chat.id, role)
    bot.answer_callback_query(call.id, "Збережено")
    label = "клієнт салону" if role == "client" else "майстер / колорист"
    bot.send_message(call.message.chat.id, "Дякуємо. Позначили вас як " + label + ".")


@bot.callback_query_handler(func=lambda call: call.data == "salon_intro:home")
def salon_intro_home(call):
    if not call.message or call.message.chat.type != "private":
        bot.answer_callback_query(call.id)
        return
    bot.answer_callback_query(call.id)
    flows.pop(call.message.chat.id, None)
    menu(call.message.chat.id)


@bot.callback_query_handler(func=lambda call: call.data == "salon_intro:book")
def salon_intro_booking(call):
    if not call.message or call.message.chat.type != "private":
        bot.answer_callback_query(call.id)
        return
    track_callback(call, event="booking", client=True)
    bot.answer_callback_query(call.id)
    begin_flow(call.message.chat.id, "booking")


def salon(chat_id):
    section[chat_id] = "salon"
    bot.send_message(chat_id, "Салон на Оболоні, Київ, Прирічна 27Е. Що вас цікавить?",
                     reply_markup=keyboard([[SALON_INTRO], [PRICE], [WINDOWS], [BOOK], [TEAM], [CONTACT], [HOME]]))

# Manually confirmed availability; never infer extra openings from an empty day.
WINDOWS_UPDATED = "22.11.2026"
WINDOW_SERVICES = {
    "GRAY FUSION": {
        "2026-11-23": ["12:30"],
        "2026-11-27": ["12:30"],
        "2026-12-01": ["10:00"]
    },
    "камуфляж / тонування": {
        "2026-11-23": ["12:30"],
        "2026-11-24": ["10:00", "16:30"],
        "2026-11-29": ["15:30"]
    },
    "жіноча стрижка": {
        "2026-11-24": ["10:00"],
        "2026-11-25": ["15:30"],
        "2026-12-02": ["10:00"]
    },
    "чоловіча стрижка": {
        "2026-11-24": ["10:00"],
        "2026-11-25": ["15:30"],
        "2026-12-02": ["10:00"]
    },
    "реконструкція 8D": {
        "2026-11-23": ["12:30"],
        "2026-11-24": ["10:00"],
        "2026-11-25": ["15:30"]
    }
}
DARK_WINDOW_PAIRS = [
    ["2026-11-26", "10:00", "2026-11-27", "12:30"],
    ["2026-11-30", "10:00", "2026-12-01", "12:30"],
    ["2026-12-08", "10:00", "2026-12-09", "12:30"]
]

def window_date_label(day):
    months = ("січня", "лютого", "березня", "квітня", "травня", "червня",
              "липня", "серпня", "вересня", "жовтня", "листопада", "грудня")
    return f"{day.day} {months[day.month - 1]}"


def available_windows(today=None):
    today = today or datetime.now(ZoneInfo("Europe/Kyiv")).date()
    first = today
    last = today + timedelta(days=14)
    slots = {}

    def eligible(day):
        return first <= day <= last

    def add(day, hour, service):
        choices = slots.setdefault((day, hour), [])
        if service not in choices:
            choices.append(service)

    for service, days in WINDOW_SERVICES.items():
        for day_text, hours in days.items():
            day = date.fromisoformat(day_text)
            if eligible(day):
                for hour in hours:
                    add(day, hour, service)
    for start_text, start_hour, end_text, end_hour in DARK_WINDOW_PAIRS:
        start, end = date.fromisoformat(start_text), date.fromisoformat(end_text)
        if eligible(start) and eligible(end):
            add(start, start_hour, "вихід із темного / чорного (2 дні: "
                + "1-й день — змивка: " + window_date_label(start) + " о " + start_hour
                + "\n2-й день — фарбування: " + window_date_label(end) + " о " + end_hour + ")")
    return sorted(slots.items())


WINDOW_FILTERS = [
    ("GRAY FUSION", "GRAY FUSION"),
    ("Вихід із темного / чорного", "dark"),
    ("Камуфляж сивини", "камуфляж / тонування"),
    ("Тонування волосся", "камуфляж / тонування"),
    ("Реконструкція 8D by Gromova", "реконструкція 8D"),
    ("Жіноча стрижка", "жіноча стрижка"),
    ("Чоловіча стрижка", "чоловіча стрижка"),
    ("Розгладжування MODIFIX Dr. Sorbie", None),
    ("Інші послуги", None),
]


def windows_view(service_index=None):
    markup = types.InlineKeyboardMarkup()
    if service_index is None:
        for index, (name, _) in enumerate(WINDOW_FILTERS):
            markup.add(types.InlineKeyboardButton(name, callback_data=f"windows:{index}"))
        text = ("<b>Найближчі вільні вікна</b>\n\nОберіть послугу, щоб переглянути дати.\n"
                "Запис через адміністратора: час може бути зайнятий протягом дня, "
                "тому адміністратор перевірить актуальність і підтвердить запис.\n\n"
                "Оновлено: " + WINDOWS_UPDATED)
    else:
        name, key = WINDOW_FILTERS[service_index]
        text = "<b>" + html.escape(name) + "</b>\n"
        slots = available_windows()
        matching = [(day, hour, choices) for (day, hour), choices in slots
                    if (key == "dark" and any(c.startswith("вихід із темного") for c in choices))
                    or (key is not None and key in choices)]
        weekdays = ("Понеділок", "Вівторок", "Середа", "Четвер", "П’ятниця", "Субота", "Неділя")
        if key == "dark" and matching:
            text += "\nПотрібні обидва дні обраної пари:\n"
            for day, hour, choices in matching:
                pair = next(c for c in choices if c.startswith("вихід із темного"))
                details = pair.split("(2 дні: ", 1)[1].rstrip(")")
                text += "\n📅 <b>" + html.escape(details) + "</b>\n"
        else:
            current = None
            for day, hour, choices in matching:
                if day != current:
                    text += "\n📅 <b>" + weekdays[day.weekday()] + ", " + window_date_label(day) + "</b>\n"
                    current = day
                text += "🕒 <b>" + hour + "</b>\n"
        if matching:
            text += "\nДля запису надішліть адміністратору обрану дату, час і назву послуги. "
            text += "Актуальність вікна та запис підтверджує адміністратор."
        else:
            text += ("\nНайближчі дати для цієї послуги уточніть в адміністратора. "
                     "Напишіть, коли вам зручно прийти.")
        markup.add(types.InlineKeyboardButton("⬅️ Інша послуга", callback_data="windows:list"))
    markup.add(types.InlineKeyboardButton("Запис через адміністратора", url=ADMIN_LINK))
    return text, markup


def show_windows(chat_id):
    section[chat_id] = "windows"
    bot.send_message(chat_id, "Оберіть послугу нижче.",
                     reply_markup=keyboard([[CONTACT], [BACK, HOME]]))
    text, markup = windows_view()
    bot.send_message(chat_id, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: bool(call.data and call.data.startswith("windows:")))
def windows_callback(call):
    if not call.message or call.message.chat.type != "private":
        bot.answer_callback_query(call.id)
        return
    track_callback(call, event="windows", client=True)
    value = call.data.partition(":")[2]
    if value != "list" and (not value.isdigit() or not 0 <= int(value) < len(WINDOW_FILTERS)):
        bot.answer_callback_query(call.id, "Відкрийте розділ вільних вікон ще раз.")
        return
    bot.answer_callback_query(call.id)
    chat_id = call.message.chat.id
    flows.pop(chat_id, None)
    section[chat_id] = "windows"
    text, markup = windows_view(None if value == "list" else int(value))
    try:
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup)
    except telebot.apihelper.ApiTelegramException as exc:
        if "message is not modified" not in str(exc).lower():
            raise



# Photos supplied and approved by the salon owner. Keep originals unaltered except size.
# Order: director, administrators, masters.
TEAM_MEMBERS = [
    ("Олена Громова", "Керівник", "images/team/01_olena_gromova.jpg"),
    ("Вікторія П'ятницька", "Адміністратор", "images/team/02_viktoriia_piatnytska.jpg"),
    ("Марина Мартиненко", "Адміністратор", "images/team/03_maryna_martynenko.jpg"),
    ("Крістіна Сталоверова", "Майстер", "images/team/04_krystina_staloverova.jpg"),
    ("Крістіна Кожевнікова", "Майстер", "images/team/05_krystina_kozhevnikova.jpg"),
    ("Альона Мясникова", "Майстер", "images/team/06_alona_miasnykova.jpg"),
    ("Альона Міхайлішина", "Майстер", "images/team/07_alona_mikhailishyna.jpg"),
    ("Оля Молочко", "Майстер", "images/team/08_olia_molochko.jpg"),
    ("Оля Алексєєва", "Майстер", "images/team/09_olia_alekseeva.jpg"),
    ("Марина Тріщук", "Майстер", "images/team/10_maryna_trishchuk.jpg"),
]


def show_team(chat_id):
    """Show the existing labelled photos in the owner's requested order."""
    flows.pop(chat_id, None)
    section[chat_id] = "team"
    bot.send_message(chat_id, "Наша команда Space of Beauty by Gromova:",
                     reply_markup=keyboard([[BACK, HOME]]))
    last_group = None
    for index, (name, role, path) in enumerate(TEAM_MEMBERS):
        group = "Керівник" if index == 0 else ("Адміністратори" if index < 3 else "Майстри")
        if group != last_group:
            bot.send_message(chat_id, f"<b>{group}</b>")
            last_group = group
        actions = types.InlineKeyboardMarkup()
        if role == "Майстер":
            actions.add(types.InlineKeyboardButton(
                "Записатися до майстра", callback_data=f"team:book:{index}"))
        else:
            actions.add(types.InlineKeyboardButton(
                "Зв'язатися з адміністратором", url=ADMIN_LINK))
        with (BASE_DIR / path).open("rb") as photo:
            bot.send_photo(chat_id, photo,
                           caption=f"<b>{html.escape(name)}</b> · {role}",
                           reply_markup=actions)



@bot.callback_query_handler(func=lambda call: bool(call.data and call.data.startswith("team:book:")))
def book_team_member(call):
    if not call.message or call.message.chat.type != "private":
        bot.answer_callback_query(call.id)
        return
    try:
        index = int(call.data.rsplit(":", 1)[1])
        name, role, _ = TEAM_MEMBERS[index]
        if role != "Майстер":
            raise ValueError("Not a master")
    except (ValueError, IndexError):
        bot.answer_callback_query(call.id, "Відкрийте розділ «Наша команда» ще раз.")
        return
    bot.answer_callback_query(call.id)
    chat_id = call.message.chat.id
    flows[chat_id] = {"kind": "booking", "step": 0, "data": {}, "master": name}
    section[chat_id] = "team_booking"
    bot.send_message(chat_id, f"Ви обрали майстра <b>{html.escape(name)}</b>.\n\nНа яку послугу хочете записатися?", reply_markup=keyboard([[CANCEL, HOME]]))


def prices(chat_id):
    section[chat_id] = "price"
    bot.send_message(chat_id, "Оберіть послугу. Ціни орієнтовні, точну вартість уточнюємо після консультації.",
                     reply_markup=keyboard([[name] for name in SERVICES] + [[BOOK], [BACK, HOME]]))

def shop(chat_id):
    section[chat_id] = "shop"
    bot.send_message(chat_id, "Оберіть розділ магазину:",
                     reply_markup=keyboard([[HOME_CARE], [COLOR_BOX], [PRO_CARE], [CART], [BACK, HOME]]))

def catalog(chat_id, category=HOME_CARE):
    section[chat_id] = "catalog"
    introduction = f"{category}. Оберіть товар."
    if category == PRO_CARE:
        introduction += " Професійна система EG by Gromova. Ціну й об’єм засобів без зазначеної вартості уточнить адміністратор до оплати."
    bot.send_message(chat_id, introduction,
        reply_markup=keyboard([[name] for name in CATEGORIES[category]] + [[CART], [BACK, HOME]]))

def product(chat_id, name):
    selection[chat_id] = name
    section[chat_id] = "product"
    price = PRODUCTS[name]
    cost = f"{price} грн" if price is not None else "ціну та наявність уточнить адміністратор"
    details = PRODUCT_DETAILS.get(name)
    markup = keyboard([["Додати в кошик"], [BACK, CART, HOME]])
    if details:
        volume = f"\nОб’єм: {details['volume_ml']} мл" if details.get("volume_ml") else ""
        caption = f"<b>{html.escape(details['title'])}</b>\n{html.escape(name)}{volume}\n{cost}"
        try:
            with (BASE_DIR / details["photo"]).open("rb") as photo:
                bot.send_photo(chat_id, photo, caption=caption, reply_markup=markup)
        except Exception:
            log.exception("Product photo could not be sent: %s", details["photo"])
            bot.send_message(chat_id, caption, reply_markup=markup)
        for chunk in description_chunks(details["description"]):
            bot.send_message(chat_id, html.escape(chunk), reply_markup=markup)
        return
    description = ("Для прикореневої зони й довжини є окремі набори. "
                   "Color Box підтримує результат між візитами, не замінює контроль у салоні."
                   if name.startswith("Color Box") else
                   "Спосіб застосування й відповідність вашому волоссю уточнить адміністратор.")
    bot.send_message(chat_id, f"<b>{html.escape(name)}</b>\n{cost}.\n{description}",
                     reply_markup=keyboard([["Додати в кошик"], [BACK, CART, HOME]]))

def description_chunks(text):
    """Split full descriptions at paragraphs; keep each Telegram message safe."""
    while text:
        end = min(len(text), 3000)
        # Telegram measures text in UTF-16 units; preserve whole code points.
        while len(text[:end].encode("utf-16-le")) // 2 > 3500:
            end -= 1
        if end < len(text):
            boundary = text.rfind("\n\n", 0, end)
            if boundary <= 0:
                boundary = text.rfind(" ", 0, end)
            if boundary > 0:
                end = boundary
        yield text[:end]
        text = text[end:].lstrip()

def cart_text(chat_id):
    counts = Counter(carts.get(chat_id, []))
    if not counts:
        return "Кошик порожній."
    lines = []
    known = 0
    unknown = False
    for name, count in counts.items():
        price = PRODUCTS.get(name)
        if price is None:
            unknown = True
            info = "ціну уточнить адміністратор"
        else:
            known += price * count
            info = f"{price * count} грн"
        lines.append(f"• {html.escape(name)} × {count} — {info}")
    summary = (f"Відомі позиції: {known} грн. Підсумок підтвердить адміністратор."
               if unknown else f"Разом: {known} грн.")
    return "Ваш кошик:\n" + "\n".join(lines) + "\n\n" + summary

def cart(chat_id):
    section[chat_id] = "cart"
    bot.send_message(chat_id, cart_text(chat_id),
                     reply_markup=keyboard([[CHECKOUT], [REMOVE, CLEAR], [BACK, HOME]]))

def contact(chat_id):
    bot.send_message(chat_id, "Адміністратор: " + ADMIN_LINK + "\n"
                     "Для консультації або запису можна залишити заявку в боті.",
                     reply_markup=keyboard([[BOOK], [HOME]]))

def begin_flow(chat_id, kind):
    if kind == "order" and not carts.get(chat_id):
        cart(chat_id)
        return
    flows[chat_id] = {"kind": kind, "step": 0, "data": {}}
    fields = ORDER_FIELDS if kind == "order" else BOOK_FIELDS
    intro = ("Замовлення через Нову пошту. Оплата 100% на ФОП після підтвердження "
             "наявності, остаточної суми й реквізитів адміністратором. "
             "Не надсилайте дані банківської картки в бот."
             if kind == "order" else "Залиште заявку, адміністратор зв'яжеться з вами.")
    bot.send_message(chat_id, intro + "\n\n" + fields[0][1],
                     reply_markup=keyboard([[CANCEL, HOME]]))

def valid_phone(text):
    number = re.sub(r"[\s()\-]", "", text)
    return number if re.fullmatch(r"\+380\d{9}", number) else None

def send_admin(text):
    try:
        bot.send_message(ADMIN_CHAT_ID, text, disable_web_page_preview=True)
        return True
    except Exception:
        log.exception("Cannot send request to admin")
        return False

def complete(chat_id, message, flow):
    data = flow["data"]
    username = message.from_user.username if message.from_user else None
    identity = f"@{html.escape(username)}" if username else f"chat_id: <code>{chat_id}</code>"
    if flow["kind"] == "booking":
        text = ("<b>Нова заявка на консультацію / запис</b>\n"
                f"Клієнт: {html.escape(data['name'])}\nТелефон: {html.escape(data['phone'])}\n"
                f"Послуга: {html.escape(data['service'])}\nКоли: {html.escape(data['when'])}\n"
                f"Telegram: {identity}")
        if flow.get("master"):
            text += f"\nОбраний майстер: {html.escape(flow['master'])}"
    else:
        text = ("<b>Нове замовлення EG by Gromova</b>\n"
                f"{cart_text(chat_id)}\n\n"
                f"Отримувач: {html.escape(data['first_name'])} {html.escape(data['last_name'])}\n"
                f"Телефон: {html.escape(data['phone'])}\nМісто: {html.escape(data['city'])}\n"
                f"Нова пошта: {html.escape(data['delivery'])} № {html.escape(data['number'])}\n"
                "Оплата: 100% на ФОП після підтвердження адміністратором.\n"
                f"Telegram: {identity}")
    if send_admin(text):
        if flow["kind"] == "order":
            carts[chat_id] = []
            response = ("Замовлення передано адміністратору. Вам підтвердять наявність, "
                        "остаточну суму та надішлють реквізити ФОП для 100% оплати.")
        else:
            response = "Заявку передано адміністратору. Вам напишуть для узгодження запису."
        flows.pop(chat_id, None)
        bot.send_message(chat_id, response, reply_markup=keyboard([[HOME, CONTACT]]))
    else:
        # Keep the cart and form for a retry rather than losing the request.
        bot.send_message(chat_id, "Не вдалося передати заявку. Спробуйте ще раз "
                         "або напишіть адміністратору: " + ADMIN_LINK,
                         reply_markup=keyboard([["Повторити надсилання", CANCEL], [HOME]]))

def collect(chat_id, message, text):
    flow = flows[chat_id]
    fields = ORDER_FIELDS if flow["kind"] == "order" else (TEAM_BOOK_FIELDS if flow.get("master") else BOOK_FIELDS)
    if flow["step"] >= len(fields):
        bot.send_message(chat_id, "Натисніть «Повторити надсилання» або «Скасувати».")
        return
    key, _ = fields[flow["step"]]
    if len(text) > 300 or not text.strip():
        bot.send_message(chat_id, "Напишіть коротку відповідь (до 300 символів).")
        return
    if key == "phone":
        phone = valid_phone(text)
        if not phone:
            bot.send_message(chat_id, "Перевірте номер: +380XXXXXXXXX")
            return
        text = phone
    if key == "delivery" and text.strip().casefold() not in (
            "відділення", "поштомат", "отделение", "почтомат"):
        bot.send_message(chat_id, "Напишіть «Відділення» або «Поштомат».")
        return
    if key == "number" and not re.fullmatch(r"\d{1,5}", text.strip()):
        bot.send_message(chat_id, "Вкажіть номер відділення або поштомату цифрами.")
        return
    flow["data"][key] = text.strip()
    flow["step"] += 1
    if flow["step"] == len(fields):
        complete(chat_id, message, flow)
    else:
        bot.send_message(chat_id, fields[flow["step"]][1])

TRAINING_TEXT = '<b>АВТОРСЬКА СИСТЕМА GRAY FUSION BY GROMOVA</b>\nДводенний практичний курс підвищення кваліфікації для колористів.\n\nGRAY FUSION — система роботи з клієнтами із сивиною. Вона дозволяє візуально поєднати природну сивину з пофарбованим волоссям, уникнути різкої межі відростання та вибудувати подальший супровід клієнта.\n\n<b>ДЕНЬ 1 — ТЕОРІЯ</b>\n\n<b>1. Що таке GRAY FUSION</b>\nПринцип злиття сивини, природне відростання, відмінності від мелірування, AirTouch і балаяжу. Кому підходить система, обмеження та визначення кінцевої мети.\n\n<b>2. Діагностика клієнта із сивиною</b>\nВідсоток, тип і розташування сивини, осередкова сивина, натуральна й косметична база, історія фарбувань, якість, щільність і пористість волосся. Оцінка реалістичного результату.\n\n<b>3. Побудова малюнка GRAY FUSION</b>\nЧитання природного малюнка сивини та відтворення його у фарбуванні. Фронтальна зона, проділ, скроні, осередкова сивина. Набір, щільність і розташування пасом без смуг і плям.\n\n<b>4. Перехід зі складних вихідних баз</b>\nБагаторічне фарбування коренів, темна косметична база, старий AirTouch або мелірування, надлишок блонду, плями, смуги, затемнення та різні рівні глибини тону. Поетапний перехід зі збереженням якості волосся.\n\n<b>5. Освітлення</b>\nВибір продукту й окисника, робота з натуральною та косметичною базою, поділ голови, послідовність і контроль освітлення, зупинка реакції. Робота з тонким, щільним, пористим і раніше освітленим волоссям. Типові помилки та пошкодження.\n\n<b>6. Нейтралізація та вирівнювання кольору</b>\nКоли і як нейтралізувати небажаний фон освітлення, вирівнювати неоднорідне полотно й працювати з різними зонами на одній голові.\n\n<b>7. Тонування</b>\nРобочі формули та логіка їх складання. Як поєднати сивину із загальною масою волосся, не перекриваючи її щільним кольором.\n\n<b>8. Камуфляж сивини</b>\nВідмінність від щільного фарбування, показання та обмеження. Камуфляж у системі GRAY FUSION і на наступних візитах.\n\n<b>9. Якість волосся та відновлення</b>\nЗміни волосся під час освітлення, оцінка його ресурсу, збереження якості під час складних переходів. Авторська система відновлення by Gromova.\n\n<b>10. Супровід клієнта після GRAY FUSION</b>\nПлан подальших візитів: камуфляж, тонування, корекції та домашній догляд. Як підтримувати результат без щомісячного зафарбовування коренів.\n\n<b>11. Консультація та робота з клієнтом</b>\nРеалістичні очікування, пояснення стратегії та довгострокова співпраця із салоном.\n\n<b>ДЕНЬ 2 — ПРАКТИКА</b>\n\nПовне практичне відпрацювання: діагностика → стратегія → схема → набір пасом → робота по зонах → освітлення → нейтралізація → вирівнювання → тонування → камуфляж за необхідності → реконструкція → фінальний результат.\n\nМи навчаємо не просто повторювати схему, а самостійно приймати рішення для конкретного клієнта.\n\n<b>КОМУ ПІДХОДИТЬ НАВЧАННЯ?</b>\n\nДосвідченим практикуючим колористам, які знають основи колористики та колірне коло, впевнено виконують мелірування, мають досвід AirTouch, балаяжу й контурингу, розуміють освітлення, нейтралізацію та тонування.\n\n<b>Це не базовий курс.</b> Ми не навчаємо колористики з нуля.\n\nПісля навчання ви зможете не просто виконувати GRAY FUSION, а розуміти, що робити з конкретним клієнтом сьогодні та як вести його далі.\n\nЩоб дізнатися вартість, найближчі дати та записатися, натисніть кнопку нижче.'

def show_training(chat_id):
    section[chat_id] = "training"
    # Telegram messages have a 4096-character limit; split on paragraph boundaries.
    paragraphs = TRAINING_TEXT.split("\n\n")
    chunks, current = [], ""
    for paragraph in paragraphs:
        candidate = current + ("\n\n" if current else "") + paragraph
        if len(candidate) > 3500:
            if current:
                chunks.append(current)
            current = paragraph
        else:
            current = candidate
    if current:
        chunks.append(current)
    for chunk in chunks[:-1]:
        bot.send_message(chat_id, chunk)
    actions = types.InlineKeyboardMarkup()
    actions.add(types.InlineKeyboardButton("Дізнатися вартість та записатися", url=ADMIN_LINK))
    bot.send_message(chat_id, chunks[-1], reply_markup=actions)
    bot.send_message(chat_id, "Повернутися до меню:", reply_markup=keyboard([[BACK, HOME]]))

@bot.message_handler(commands=["start", "help"])
def start(message):
    if message.chat.type != "private":
        return
    flows.pop(message.chat.id, None)
    if has_consent(message.chat.id):
        menu(message.chat.id)
    else:
        send_entry_prompt(message.chat.id)

@bot.message_handler(commands=["privacy"])
def privacy_info(message):
    if message.chat.type != "private":
        return
    bot.send_message(message.chat.id, PRIVACY_TEXT, disable_web_page_preview=True)


@bot.message_handler(commands=["id"])
def show_id(message):
    if message.chat.type != "private":
        return
    track_message(message)
    bot.send_message(message.chat.id, f"chat_id: <code>{message.chat.id}</code>")


@bot.message_handler(commands=["stats"])
def admin_stats(message):
    if message.chat.type != "private" or message.chat.id != ADMIN_CHAT_ID:
        return
    track_message(message)
    bot.send_message(message.chat.id, stats_text())


@bot.message_handler(commands=["broadcast"])
def admin_broadcast(message):
    if message.chat.type != "private" or message.chat.id != ADMIN_CHAT_ID:
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3 or parts[1].lower() not in ("all", "clients", "masters", "both"):
        bot.send_message(
            message.chat.id,
            "Формат:\n"
            "<code>/broadcast clients Текст</code> — клієнтам\n"
            "<code>/broadcast masters Текст</code> — майстрам\n"
            "<code>/broadcast both Текст</code> — тим, хто в обох групах\n"
            "<code>/broadcast all Текст</code> — усім",
        )
        return
    segment = parts[1].lower()
    body = parts[2].strip()
    if not body or len(body) > 3500:
        bot.send_message(message.chat.id, "Текст розсилки має бути від 1 до 3500 символів.")
        return
    count = len(recipient_rows(segment))
    pending_broadcasts[message.chat.id] = {"segment": segment, "body": body}
    labels = {
        "all": "усім",
        "clients": "клієнтам",
        "masters": "майстрам",
        "both": "клієнтам + майстрам",
    }
    bot.send_message(
        message.chat.id,
        "<b>Попередній перегляд розсилки</b>\n"
        f"Кому: {labels[segment]}\n"
        f"Отримувачів зараз: <b>{count}</b>\n\n"
        + html.escape(body)
        + "\n\nДля запуску: /confirm_broadcast\nСкасувати: /cancel_broadcast",
    )


@bot.message_handler(content_types=["photo"])
def admin_photo_broadcast(message):
    if message.chat.type != "private" or message.chat.id != ADMIN_CHAT_ID:
        return
    caption = (message.caption or "").strip()
    parts = caption.split(maxsplit=2)
    if len(parts) < 3 or parts[0] != "/broadcast_photo" or parts[1].lower() not in ("all", "clients", "masters", "both"):
        return
    segment, body = parts[1].lower(), parts[2].strip()
    if not body or len(body) > 3500:
        bot.send_message(message.chat.id, "Текст має бути від 1 до 3500 символів.")
        return
    photo_file_id = message.photo[-1].file_id
    pending_broadcasts[message.chat.id] = {
        "segment": segment, "body": body, "photo_file_id": photo_file_id
    }
    count = len(recipient_rows(segment))
    bot.send_photo(message.chat.id, photo_file_id)
    bot.send_message(
        message.chat.id,
        "<b>Попередній перегляд розсилки з фото</b>\n"
        f"Отримувачів: <b>{count}</b>\n\n"
        + html.escape(body)
        + "\n\nЗапустити: /confirm_broadcast\nСкасувати: /cancel_broadcast",
    )


@bot.message_handler(commands=["broadcast_photo"])
def admin_photo_broadcast_reply(message):
    if message.chat.type != "private" or message.chat.id != ADMIN_CHAT_ID:
        return
    parts = message.text.split(maxsplit=2)
    reply = message.reply_to_message
    if (len(parts) < 3 or parts[1].lower() not in ("all", "clients", "masters", "both")
            or not reply or not reply.photo):
        bot.send_message(message.chat.id, "Відповідайте на фото командою /broadcast_photo all Текст")
        return
    segment, body = parts[1].lower(), parts[2].strip()
    if not body or len(body) > 3500:
        bot.send_message(message.chat.id, "Текст має бути від 1 до 3500 символів.")
        return
    photo_file_id = reply.photo[-1].file_id
    pending_broadcasts[message.chat.id] = {
        "segment": segment, "body": body, "photo_file_id": photo_file_id
    }
    count = len(recipient_rows(segment))
    bot.send_photo(message.chat.id, photo_file_id)
    bot.send_message(message.chat.id,
        "<b>Попередній перегляд розсилки з фото</b>\n"
        f"Отримувачів: <b>{count}</b>\n\n" + html.escape(body)
        + "\n\nЗапустити: /confirm_broadcast\nСкасувати: /cancel_broadcast")


@bot.message_handler(commands=["confirm_broadcast"])
def confirm_broadcast(message):
    if message.chat.type != "private" or message.chat.id != ADMIN_CHAT_ID:
        return
    pending = pending_broadcasts.pop(message.chat.id, None)
    if not pending:
        bot.send_message(message.chat.id, "Немає підготовленої розсилки.")
        return
    count = len(recipient_rows(pending["segment"]))
    bot.send_message(message.chat.id, f"Запускаю розсилку для {count} отримувачів.")
    threading.Thread(
        target=broadcast_worker,
        args=(message.chat.id, pending["segment"], pending["body"], pending.get("photo_file_id")),
        daemon=True,
    ).start()


@bot.message_handler(commands=["cancel_broadcast"])
def cancel_broadcast(message):
    if message.chat.type != "private" or message.chat.id != ADMIN_CHAT_ID:
        return
    pending_broadcasts.pop(message.chat.id, None)
    bot.send_message(message.chat.id, "Розсилку скасовано.")


@bot.message_handler(commands=["unsubscribe"])
def unsubscribe(message):
    if message.chat.type != "private":
        return
    track_message(message)
    set_opt_out(message.chat.id, True)
    bot.send_message(message.chat.id, "Готово. Розсилки від бота більше не надходитимуть.")


@bot.message_handler(commands=["subscribe"])
def subscribe(message):
    if message.chat.type != "private":
        return
    track_message(message)
    set_opt_out(message.chat.id, False)
    bot.send_message(message.chat.id, "Розсилки знову увімкнено.")


@bot.message_handler(content_types=["text"])
def dispatch(message):
    if message.chat.type != "private":
        return
    chat_id = message.chat.id
    text = message.text.strip()
    if chat_id != ADMIN_CHAT_ID and not has_consent(chat_id):
        send_entry_prompt(chat_id)
        return
    track_message(message)
    if text in (HOME, CANCEL):
        flows.pop(chat_id, None)
        menu(chat_id)
        return
    if text == BACK:
        flows.pop(chat_id, None)
        current = section.get(chat_id)
        if current == "product":
            catalog(chat_id, product_category.get(selection.get(chat_id), HOME_CARE))
        elif current == "catalog":
            shop(chat_id)
        elif current in ("price", "haircut", "windows", "team", "salon_intro", "training"):
            salon(chat_id)
        else:
            menu(chat_id)
        return
    if text == "Повторити надсилання" and chat_id in flows:
        flow = flows[chat_id]
        fields = ORDER_FIELDS if flow["kind"] == "order" else (TEAM_BOOK_FIELDS if flow.get("master") else BOOK_FIELDS)
        if flow["step"] == len(fields):
            complete(chat_id, message, flow)
        else:
            bot.send_message(chat_id, fields[flow["step"]][1])
        return
    if chat_id in flows:
        collect(chat_id, message, text)
        return
    if text == SALON:
        register_user(chat_id, message.from_user, event="salon", client=True)
        salon(chat_id)
    elif text == TRAINING:
        register_user(chat_id, message.from_user, event="training", master=True)
        show_training(chat_id)
    elif text == GRAY_CHANNEL:
        register_user(chat_id, message.from_user, event="gray_channel", client=True)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Перейти до каналу про сивину", url=GRAY_CHANNEL_URL))
        bot.send_message(chat_id, "Маєте запитання про сивину або техніку GRAY FUSION? У нашому каналі розповідаємо про сивину, догляд та показуємо приклади робіт.", reply_markup=markup)
    elif text == SALON_INTRO:
        show_salon_intro(chat_id)
    elif text == MAP_MENU:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📍 Відкрити маршрут у Google Maps", url=SALON_MAP_URL))
        bot.send_message(chat_id, "Чекаємо на вас: Київ, Оболонь, вул. Прирічна, 27Е. Натисніть кнопку, щоб прокласти маршрут.", reply_markup=markup)
    elif text == TEAM:
        show_team(chat_id)
    elif text == WINDOWS:
        register_user(chat_id, message.from_user, event="windows", client=True)
        show_windows(chat_id)
    elif text == PRICE:
        register_user(chat_id, message.from_user, event="price", client=True)
        prices(chat_id)
    elif text in SERVICES:
        if text == "Реконструкція 8D by Gromova":
            section[chat_id] = "price"
            try:
                with (BASE_DIR / "images/salon/reconstruction-8d.jpg").open("rb") as photo:
                    bot.send_photo(chat_id, photo, caption="Реконструкція 8D by Gromova",
                                   reply_markup=keyboard([[BOOK], [BACK, HOME]]))
            except Exception:
                log.exception("Could not send reconstruction photo")
        if text == HAIRCUT:
            section[chat_id] = "haircut"
        bot.send_message(chat_id, html.escape(SERVICES[text]),
                         reply_markup=keyboard([[BOOK], [BACK, HOME]]))
        if text == "GRAY FUSION — робота із сивиною":
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("Більше про сивину в нашому каналі", url=GRAY_CHANNEL_URL))
            bot.send_message(chat_id, "Відповіді на запитання про сивину та приклади робіт:", reply_markup=markup)
    elif text == BOOK:
        register_user(chat_id, message.from_user, event="booking", client=True)
        begin_flow(chat_id, "booking")
    elif text == SHOP:
        register_user(chat_id, message.from_user, event="shop", client=True)
        shop(chat_id)
    elif text in CATEGORIES:
        if text == PRO_CARE:
            register_user(chat_id, message.from_user, event="pro_care", master=True)
        else:
            register_user(chat_id, message.from_user, event="shop", client=True)
        catalog(chat_id, text)
    elif text in PRODUCTS:
        product(chat_id, text)
    elif text == "Додати в кошик" and selection.get(chat_id):
        carts.setdefault(chat_id, []).append(selection[chat_id])
        bot.send_message(chat_id, "Додано. " + cart_text(chat_id),
                         reply_markup=keyboard([[CART], [BACK, HOME]]))
    elif text == CART:
        register_user(chat_id, message.from_user, event="cart", client=True)
        cart(chat_id)
    elif text == REMOVE:
        items = carts.get(chat_id, [])
        if items:
            items.pop()
            bot.send_message(chat_id, "Останню позицію прибрано.")
        cart(chat_id)
    elif text == CLEAR:
        carts[chat_id] = []
        cart(chat_id)
    elif text == CHECKOUT:
        begin_flow(chat_id, "order")
    elif text == CONTACT:
        register_user(chat_id, message.from_user, event="contact", client=True)
        contact(chat_id)
    else:
        bot.send_message(chat_id, "Оберіть кнопку в меню або напишіть адміністратору.",
                         reply_markup=keyboard([[HOME, CONTACT]]))

def configure_bot_profile():
    """Update the public Telegram profile for the salon bot."""
    try:
        bot.set_my_name(BOT_DISPLAY_NAME)
        bot.set_my_name(BOT_DISPLAY_NAME, language_code="uk")
        bot.set_my_description(BOT_DESCRIPTION)
        bot.set_my_description(BOT_DESCRIPTION, language_code="uk")
        bot.set_my_short_description(BOT_DESCRIPTION)
        bot.set_my_short_description(BOT_DESCRIPTION, language_code="uk")
        log.info("Bot profile metadata updated")
    except Exception:
        log.exception("Could not update bot profile metadata")

if __name__ == "__main__":
    configure_bot_profile()
    while True:
        try:
            bot.remove_webhook()
            log.info("Bot polling started")
            bot.infinity_polling(timeout=30, long_polling_timeout=30, skip_pending=True)
        except Exception:
            log.exception("Polling failed; restarting in 5 seconds")
            time.sleep(5)
