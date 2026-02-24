import os
import re
import logging
from typing import Dict, Any, List, Optional, Tuple

import telebot
from telebot import types


# =========================
# CONFIG
# =========================
TOKEN = (os.environ.get("TOKEN") or "").strip()
ADMIN_CHAT_ID_RAW = (os.environ.get("ADMIN_CHAT_ID") or "").strip()  # пример: -5268865051

if not TOKEN:
    raise RuntimeError("TOKEN env var is not set")

if not ADMIN_CHAT_ID_RAW:
    raise RuntimeError("ADMIN_CHAT_ID env var is not set (example: -5268865051)")

ADMIN_CHAT_ID = int(ADMIN_CHAT_ID_RAW)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("eg-bot")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
ADMIN_LINK = "https://t.me/beautyspace_admin"


# =========================
# UI BUTTONS (UA)
# =========================
BTN_HOME = "🏠 Головне меню"
BTN_BACK = "⬅️ Назад"

BTN_SALON = "Салон"
BTN_SHOP = "Магазин косметики"
BTN_ADMIN = "Зв'язатися з адміністратором"
BTN_PRICE = "Прайс салону"

BTN_REDKEN = "Redken"
BTN_EG = "EG by Gromova"

BTN_CART = "🧺 Кошик"
BTN_CART_SHOW = "Показати кошик"
BTN_CART_CLEAR = "Очистити кошик"
BTN_CHECKOUT = "✅ Оформити замовлення"

BTN_CHOOSE_VOLUME = "Вибрати обʼєм"
BTN_ADD_TO_CART = "Додати в кошик"
BTN_HOW_TO_USE = "Як правильно використовувати"

BTN_ITEMS = "🧴 Товари лінійки"


# =========================
# HELPERS
# =========================
def is_private(message: types.Message) -> bool:
    return message.chat.type == "private"


def safe_send_to_admin(text: str) -> bool:
    try:
        bot.send_message(
            ADMIN_CHAT_ID,
            text,
            reply_markup=types.ReplyKeyboardRemove(),
            disable_web_page_preview=True
        )
        return True
    except Exception as e:
        log.exception("Failed to send to admin chat: %s", e)
        return False


def safe_send_photo(chat_id: int, photo_path: str, caption: str, reply_markup: types.ReplyKeyboardMarkup) -> None:
    """
    photo_path: относительный путь типа images/xxx.jpg
    """
    abs_path = os.path.join(BASE_DIR, photo_path)
    try:
        with open(abs_path, "rb") as f:
            bot.send_photo(chat_id, f, caption=caption, reply_markup=reply_markup)
    except Exception as e:
        log.exception("Failed to send photo %s: %s", abs_path, e)
        bot.send_message(chat_id, caption, reply_markup=reply_markup)


def chunk_two(items: List[str]) -> List[Tuple[str, ...]]:
    rows: List[Tuple[str, ...]] = []
    for i in range(0, len(items), 2):
        rows.append(tuple(items[i:i + 2]))
    return rows


# =========================
# KEYBOARDS
# =========================
def kb_main():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.row(BTN_SALON, BTN_SHOP)
    m.row(BTN_CART)
    m.row(BTN_ADMIN)
    return m


def kb_salon():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.row(BTN_PRICE)
    m.row(BTN_ADMIN)
    m.row(BTN_HOME)
    return m


def kb_price(services_rows):
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for row in services_rows:
        m.row(*row)
    m.row(BTN_BACK, BTN_HOME)
    return m


def kb_shop():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.row(BTN_REDKEN, BTN_EG)
    m.row(BTN_BACK, BTN_HOME)
    return m


def kb_lines(lines_rows):
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for row in lines_rows:
        m.row(*row)
    m.row(BTN_BACK, BTN_HOME)
    return m


def kb_items(items_rows):
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for row in items_rows:
        m.row(*row)
    m.row(BTN_BACK, BTN_HOME)
    return m


def kb_product():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.row(BTN_ITEMS)
    m.row(BTN_CHOOSE_VOLUME)
    m.row(BTN_ADD_TO_CART, BTN_HOW_TO_USE)
    m.row(BTN_BACK, BTN_HOME)
    return m


def kb_volumes(volume_rows):
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for row in volume_rows:
        m.row(*row)
    m.row(BTN_BACK, BTN_HOME)
    return m


def kb_cart():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.row(BTN_CART_SHOW, BTN_CART_CLEAR)
    m.row(BTN_CHECKOUT)
    m.row(BTN_BACK, BTN_HOME)
    return m


# =========================
# SALON SERVICES (твои тексты)
# =========================
SVC_CAMO = "Камуфляж сивини"
SVC_TONE = "Тонування"
SVC_COLOR = "Фарбування"
SVC_INTEGR = "Інтеграція сивини"
SVC_HIGHL = "Мелірування"
SVC_AIRTOUCH = "Airtouch"
SVC_DARK_OUT = "Вихід з темного кольору"
SVC_CUT = "Стрижка"
SVC_RECON = "Реконструкція 8D by Gromova"

SERVICE_TEXTS = {
    SVC_CAMO: "Камуфляж сивини ✨\n\nВартість: від 3000 грн\nТривалість: до 1 години\n\n"
              "Що входить у процедуру:\n• консультація майстра\n• підбір відтінку\n"
              "• м’яке тонування сивини без зміни натурального кольору\n• стабілізація кольору\n"
              "• рекомендації по догляду\n\n⚠️ Камуфляж підходить не всім.\n"
              "Перед записом обов’язкова консультація.\n\n"
              "Реконструкція 8D by Gromova оплачується окремо.",

    SVC_TONE: "Тонування 🎨\n\nВартість: від 3000 грн\n\nЩо входить:\n"
              "• оновлення відтінку фарбником Redken\n• корекція нюансу кольору\n• стабілізація\n\n"
              "Реконструкція 8D by Gromova оплачується окремо.",

    SVC_COLOR: "Стійке фарбування 🖤\n\nВартість: від 3500 грн\n\n"
               "Що входить:\n• консультація\n• фарбування кореня або кореня + довжини\n• стабілізація кольору\n\n"
               "Реконструкція 8D by Gromova оплачується окремо.",

    SVC_INTEGR: "Інтеграція сивини 🤍\n\nВартість: від 12000 грн\nТривалість: 6–10 годин\n\n"
                "Перед записом обов’язкова консультація.\n\n"
                "Реконструкція 8D by Gromova обов’язкова та оплачується додатково.",

    SVC_HIGHL: "Мелірування 🌟\n\nВартість: від 12000 грн\nТривалість: 4–6 годин\n\n"
               "Реконструкція 8D by Gromova обов’язкова та оплачується додатково.",

    SVC_AIRTOUCH: "Airtouch 💨\n\nВартість: від 12000 грн\nТривалість: 6–8 годин\n\n"
                  "Реконструкція 8D by Gromova обов’язкова та оплачується додатково.",

    SVC_DARK_OUT: "Вихід з темного кольору 🚪\n\nВартість: від 15000 грн\n\n"
                  "⚠️ Перед записом обов’язкова консультація.\n"
                  "Реконструкція 8D by Gromova обов’язкова та оплачується додатково.",

    SVC_CUT: "Стрижка ✂️\n\nВартість: 1200 грн\n\n"
             "Що входить:\n• консультація\n• миття голови\n• укладка",

    SVC_RECON: "Реконструкція 8D by Gromova 🧬\n\nВартість: від 2500 грн\nТривалість: до 2 годин\n\n"
               "8D by Gromova — авторська система глибокого відновлення волосся."
}

PRICE_ROWS = [
    (SVC_CAMO, SVC_INTEGR),
    (SVC_TONE, SVC_COLOR),
    (SVC_HIGHL, SVC_AIRTOUCH),
    (SVC_DARK_OUT, SVC_CUT),
    (SVC_RECON,),
]


# =========================
# CATALOG
# =========================
# ВАЖНО:
# 1) Вставь сюда свой огромный CATALOG целиком.
# 2) CATALOG должен быть валидным словарём и полностью закрываться.
# 3) photo хранится как "images/xxx.jpg"
#
# Ниже каркас. Замени на свой.
CATALOG: Dict[str, Any] = {
    "Redken": {
        "lines": {
            # сюда вставляется твой реальный контент
        }
    },
    "EG by Gromova": {
        "lines": {}
    }
}

# Список линий для кнопок. Поменяй под свои линии, которые реально есть в CATALOG["Redken"]["lines"].
REDKEN_LINES_ROWS = [
    ("Acidic Bonding", "Acidic Color Gloss"),
    ("Extreme", "Extreme Length"),
    ("Frizz Dismiss", "Blondage"),
    ("Volume Injection", "Styling"),
]


# =========================
# STATE (per user)
# =========================
SCR_MAIN = "main"
SCR_SALON = "salon"
SCR_PRICE = "price"
SCR_SHOP = "shop"
SCR_BRAND_REDKEN = "brand_redken"
SCR_BRAND_EG = "brand_eg"
SCR_LINE = "line"
SCR_ITEMS = "items"
SCR_ITEM = "item"
SCR_VOLUMES = "volumes"
SCR_CART = "cart"
SCR_CHECKOUT = "checkout"

user_nav: Dict[int, List[str]] = {}          # chat_id -> stack of screens
user_selected: Dict[int, Dict[str, Any]] = {} # chat_id -> brand/line/item_key/volume_btn
user_cart: Dict[int, List[Dict[str, Any]]] = {}  # chat_id -> list of items

user_checkout: Dict[int, Dict[str, str]] = {}
user_checkout_step: Dict[int, int] = {}

CHECKOUT_FIELDS = [
    ("first_name", "Вкажіть ваше ім’я 👇"),
    ("last_name", "Вкажіть ваше прізвище 👇"),
    ("phone", "Вкажіть номер телефону 📞\nПриклад: +380XXXXXXXXX"),
    ("city", "Вкажіть місто 🏙️"),
    ("np_type", "Доставка Новою Поштою:\nНапишіть: Відділення або Поштомат 📦"),
    ("np_number", "Вкажіть номер відділення або поштомату 👇"),
]


def nav_init(chat_id: int) -> None:
    user_nav.setdefault(chat_id, [SCR_MAIN])
    user_selected.setdefault(chat_id, {})
    user_cart.setdefault(chat_id, [])


def nav_go(chat_id: int, screen: str) -> None:
    nav_init(chat_id)
    user_nav[chat_id].append(screen)


def nav_back(chat_id: int) -> None:
    nav_init(chat_id)
    if len(user_nav[chat_id]) > 1:
        user_nav[chat_id].pop()


def nav_current(chat_id: int) -> str:
    nav_init(chat_id)
    return user_nav[chat_id][-1]


# =========================
# DATA ACCESS
# =========================
def get_lines(brand: str) -> Dict[str, Any]:
    return (CATALOG.get(brand) or {}).get("lines") or {}


def get_items(brand: str, line: str) -> Dict[str, Any]:
    return (((CATALOG.get(brand) or {}).get("lines") or {}).get(line) or {}).get("items") or {}


def get_item(brand: str, line: str, item_key: str) -> Dict[str, Any]:
    return get_items(brand, line).get(item_key) or {}


def current_item_context(chat_id: int) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    sel = user_selected.get(chat_id, {})
    return sel.get("brand"), sel.get("line"), sel.get("item_key")


def current_volume_buttons(chat_id: int) -> List[str]:
    brand, line, item_key = current_item_context(chat_id)
    if not (brand and line and item_key):
        return []
    item = get_item(brand, line, item_key)
    volumes = item.get("volumes") or {}
    return list(volumes.keys())


# =========================
# RENDER
# =========================
def show_main(chat_id: int) -> None:
    bot.send_message(chat_id, "Вітаємо 💛\nОберіть розділ нижче:", reply_markup=kb_main())


def show_salon(chat_id: int) -> None:
    bot.send_message(chat_id, "Розділ: Салон ✂️\nОберіть, що потрібно:", reply_markup=kb_salon())


def show_price(chat_id: int) -> None:
    bot.send_message(chat_id, "Прайс салону 💰\nОберіть послугу:", reply_markup=kb_price(PRICE_ROWS))


def show_shop(chat_id: int) -> None:
    bot.send_message(chat_id, "Магазин косметики 🛍️\nОберіть бренд:", reply_markup=kb_shop())


def show_redken_lines(chat_id: int) -> None:
    # Подстраховка: показываем только линии, которые реально есть в CATALOG
    real_lines = set(get_lines("Redken").keys())
    rows: List[Tuple[str, ...]] = []
    for row in REDKEN_LINES_ROWS:
        filtered = tuple([x for x in row if x in real_lines])
        if filtered:
            rows.append(filtered)
    if not rows:
        bot.send_message(chat_id, "Redken 🧴\nЛінійки зараз не додані.", reply_markup=kb_shop())
        return
    bot.send_message(chat_id, "Redken 🧴\nОберіть лінійку:", reply_markup=kb_lines(rows))


def show_cart(chat_id: int) -> None:
    bot.send_message(chat_id, "Кошик 🧺\nОберіть дію:", reply_markup=kb_cart())


def show_items_in_line(chat_id: int) -> None:
    sel = user_selected.get(chat_id, {})
    brand = sel.get("brand")
    line = sel.get("line")
    if not (brand and line):
        show_shop(chat_id)
        return

    items = get_items(brand, line)
    if not items:
        bot.send_message(chat_id, "У цій лінійці товари ще не додані ✅", reply_markup=kb_lines(REDKEN_LINES_ROWS))
        return

    # Кнопками показываем названия товаров (title). Внутри — маппинг title -> item_key
    title_to_key: Dict[str, str] = {}
    titles: List[str] = []
    for k, it in items.items():
        t = (it.get("title") or "").strip()
        if not t:
            continue
        titles.append(t)
        title_to_key[t] = k

    # сохраняем маппинг в состояние
    user_selected[chat_id]["title_to_key"] = title_to_key

    titles_sorted = sorted(titles)
    rows = chunk_two(titles_sorted)
    bot.send_message(chat_id, f"{brand} 🧴\nЛінійка: <b>{line}</b>\nОберіть товар:", reply_markup=kb_items(rows))


def show_item(chat_id: int) -> None:
    brand, line, item_key = current_item_context(chat_id)
    if not (brand and line and item_key):
        show_shop(chat_id)
        return

    item = get_item(brand, line, item_key)
    title = item.get("title") or ""
    short = item.get("short") or ""
    caption = f"<b>{title}</b>\n\n{short}\n\nНатисніть «Вибрати обʼєм»."

    photo = (item.get("photo") or "").strip()
    if photo:
        safe_send_photo(chat_id, photo, caption, kb_product())
        return

    bot.send_message(chat_id, caption, reply_markup=kb_product())


def show_volumes(chat_id: int) -> None:
    buttons = current_volume_buttons(chat_id)
    if not buttons:
        bot.send_message(chat_id, "Обʼєми зараз не додані ✅", reply_markup=kb_product())
        return

    rows = chunk_two(buttons)
    bot.send_message(chat_id, "Оберіть обʼєм:", reply_markup=kb_volumes(rows))


# =========================
# COMMANDS
# =========================
@bot.message_handler(commands=["start"])
def cmd_start(message: types.Message):
    if not is_private(message):
        return
    chat_id = message.chat.id
    nav_init(chat_id)
    user_nav[chat_id] = [SCR_MAIN]
    user_selected[chat_id] = {}
    show_main(chat_id)


@bot.message_handler(commands=["id"])
def cmd_id(message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else None
    bot.send_message(chat_id, f"chat_id: {chat_id}\nuser_id: {user_id}", reply_markup=types.ReplyKeyboardRemove())


# =========================
# GLOBAL NAV
# =========================
@bot.message_handler(func=lambda m: is_private(m) and m.text == BTN_HOME)
def handle_home(message: types.Message):
    chat_id = message.chat.id
    nav_init(chat_id)
    user_nav[chat_id] = [SCR_MAIN]
    user_selected[chat_id] = {}
    show_main(chat_id)


@bot.message_handler(func=lambda m: is_private(m) and m.text == BTN_BACK)
def handle_back(message: types.Message):
    chat_id = message.chat.id
    nav_back(chat_id)
    cur = nav_current(chat_id)

    if cur == SCR_MAIN:
        show_main(chat_id)
        return
    if cur == SCR_SALON:
        show_salon(chat_id)
        return
    if cur == SCR_PRICE:
        show_price(chat_id)
        return
    if cur == SCR_SHOP:
        show_shop(chat_id)
        return
    if cur == SCR_BRAND_REDKEN:
        show_redken_lines(chat_id)
        return
    if cur == SCR_LINE:
        show_redken_lines(chat_id)
        return
    if cur == SCR_ITEMS:
        show_items_in_line(chat_id)
        return
    if cur == SCR_ITEM:
        show_items_in_line(chat_id)
        return
    if cur == SCR_VOLUMES:
        show_item(chat_id)
        return
    if cur == SCR_CART:
        show_cart(chat_id)
        return

    show_main(chat_id)


# =========================
# MAIN MENU
# =========================
@bot.message_handler(func=lambda m: is_private(m) and m.text == BTN_SALON)
def open_salon(message: types.Message):
    chat_id = message.chat.id
    nav_go(chat_id, SCR_SALON)
    show_salon(chat_id)


@bot.message_handler(func=lambda m: is_private(m) and m.text == BTN_SHOP)
def open_shop(message: types.Message):
    chat_id = message.chat.id
    nav_go(chat_id, SCR_SHOP)
    show_shop(chat_id)


@bot.message_handler(func=lambda m: is_private(m) and m.text == BTN_ADMIN)
def contact_admin(message: types.Message):
    chat_id = message.chat.id
    bot.send_message(chat_id, f"Напишіть адміністратору 👇\n{ADMIN_LINK}", reply_markup=kb_main())


@bot.message_handler(func=lambda m: is_private(m) and m.text == BTN_CART)
def open_cart(message: types.Message):
    chat_id = message.chat.id
    nav_go(chat_id, SCR_CART)
    show_cart(chat_id)


# =========================
# SALON
# =========================
@bot.message_handler(func=lambda m: is_private(m) and m.text == BTN_PRICE)
def open_price(message: types.Message):
    chat_id = message.chat.id
    nav_go(chat_id, SCR_PRICE)
    show_price(chat_id)


@bot.message_handler(func=lambda m: is_private(m) and m.text in SERVICE_TEXTS)
def show_service(message: types.Message):
    chat_id = message.chat.id
    bot.send_message(chat_id, SERVICE_TEXTS[message.text], reply_markup=kb_price(PRICE_ROWS))


# =========================
# SHOP
# =========================
@bot.message_handler(func=lambda m: is_private(m) and m.text == BTN_REDKEN)
def open_redken(message: types.Message):
    chat_id = message.chat.id
    user_selected[chat_id] = {"brand": "Redken"}
    nav_go(chat_id, SCR_BRAND_REDKEN)
    show_redken_lines(chat_id)


@bot.message_handler(func=lambda m: is_private(m) and m.text == BTN_EG)
def open_eg(message: types.Message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "EG by Gromova (товари додамо наступним блоком) 💛", reply_markup=kb_shop())


# =========================
# REDKEN LINES
# =========================
@bot.message_handler(func=lambda m: is_private(m) and (m.text in get_lines("Redken").keys()))
def redken_line(message: types.Message):
    chat_id = message.chat.id
    line = message.text

    items = get_items("Redken", line)
    if not items:
        bot.send_message(chat_id, "Цю лінійку додамо наступною ✅", reply_markup=kb_lines(REDKEN_LINES_ROWS))
        return

    user_selected[chat_id] = {"brand": "Redken", "line": line}
    nav_go(chat_id, SCR_LINE)
    nav_go(chat_id, SCR_ITEMS)
    show_items_in_line(chat_id)


# =========================
# ITEMS IN LINE (by title)
# =========================
@bot.message_handler(func=lambda m: is_private(m) and m.text and (m.text in (user_selected.get(m.chat.id, {}).get("title_to_key") or {})))
def pick_item_from_line(message: types.Message):
    chat_id = message.chat.id
    title = message.text

    mapping = user_selected.get(chat_id, {}).get("title_to_key") or {}
    item_key = mapping.get(title)
    if not item_key:
        bot.send_message(chat_id, "Товар не знайдено ✅", reply_markup=kb_main())
        return

    user_selected[chat_id]["item_key"] = item_key
    user_selected[chat_id].pop("volume_btn", None)
    nav_go(chat_id, SCR_ITEM)
    show_item(chat_id)


# =========================
# PRODUCT ACTIONS
# =========================
@bot.message_handler(func=lambda m: is_private(m) and m.text == BTN_ITEMS)
def open_items_btn(message: types.Message):
    chat_id = message.chat.id
    nav_go(chat_id, SCR_ITEMS)
    show_items_in_line(chat_id)


@bot.message_handler(func=lambda m: is_private(m) and m.text == BTN_CHOOSE_VOLUME)
def choose_volume(message: types.Message):
    chat_id = message.chat.id
    brand, line, item_key = current_item_context(chat_id)
    if not (brand and line and item_key):
        show_shop(chat_id)
        return
    nav_go(chat_id, SCR_VOLUMES)
    show_volumes(chat_id)


@bot.message_handler(func=lambda m: is_private(m) and m.text and (m.text in current_volume_buttons(m.chat.id)))
def pick_volume(message: types.Message):
    chat_id = message.chat.id
    user_selected.setdefault(chat_id, {})
    user_selected[chat_id]["volume_btn"] = message.text

    bot.send_message(
        chat_id,
        f"Обʼєм обрано ✅\n{message.text}\nТепер натисніть «{BTN_ADD_TO_CART}».",
        reply_markup=kb_product()
    )


@bot.message_handler(func=lambda m: is_private(m) and m.text == BTN_HOW_TO_USE)
def how_to_use(message: types.Message):
    chat_id = message.chat.id
    brand, line, item_key = current_item_context(chat_id)
    if not (brand and line and item_key):
        show_shop(chat_id)
        return

    item = get_item(brand, line, item_key)
    text = (item.get("how_to_use") or "").strip()
    if not text:
        text = "Інструкцію додамо наступним блоком ✅"
    bot.send_message(chat_id, text, reply_markup=kb_product())


@bot.message_handler(func=lambda m: is_private(m) and m.text == BTN_ADD_TO_CART)
def add_to_cart(message: types.Message):
    chat_id = message.chat.id
    brand, line, item_key = current_item_context(chat_id)
    volume_btn = (user_selected.get(chat_id, {}) or {}).get("volume_btn")

    if not (brand and line and item_key):
        show_shop(chat_id)
        return

    if not volume_btn:
        bot.send_message(chat_id, "Спочатку натисніть «Вибрати обʼєм» ✅", reply_markup=kb_product())
        return

    item = get_item(brand, line, item_key)
    volumes = item.get("volumes") or {}
    v = volumes.get(volume_btn)

    if not v:
        bot.send_message(chat_id, "Обʼєм не знайдено ✅", reply_markup=kb_product())
        return

    user_cart.setdefault(chat_id, [])
    user_cart[chat_id].append({
        "title": item.get("title") or "",
        "ml": v.get("ml"),
        "price": int(v.get("price") or 0)
    })

    bot.send_message(
        chat_id,
        f"Додано в кошик ✅\n{item.get('title','')} — {v.get('ml')} мл — {v.get('price')} грн\n\nВідкрийте кошик кнопкою «{BTN_CART}».",
        reply_markup=kb_product()
    )


# =========================
# CART
# =========================
@bot.message_handler(func=lambda m: is_private(m) and m.text == BTN_CART_SHOW)
def cart_show(message: types.Message):
    chat_id = message.chat.id
    items = user_cart.get(chat_id, [])

    if not items:
        bot.send_message(chat_id, "Кошик порожній 🫶", reply_markup=kb_cart())
        return

    total = sum(int(i.get("price") or 0) for i in items)
    lines = []
    for idx, i in enumerate(items, 1):
        lines.append(f"{idx}) {i.get('title','')} — {i.get('ml')} мл — {i.get('price')} грн")

    text = "Ваш кошик 🧺\n\n" + "\n".join(lines) + f"\n\nРазом: {total} грн"
    bot.send_message(chat_id, text, reply_markup=kb_cart())


@bot.message_handler(func=lambda m: is_private(m) and m.text == BTN_CART_CLEAR)
def cart_clear(message: types.Message):
    chat_id = message.chat.id
    user_cart[chat_id] = []
    bot.send_message(chat_id, "Кошик очищено ✅", reply_markup=kb_cart())


# =========================
# CHECKOUT
# =========================
def ask_next_field(chat_id: int) -> None:
    step = user_checkout_step.get(chat_id, 0)

    if step >= len(CHECKOUT_FIELDS):
        send_order_to_admin(chat_id)
        return

    _, question = CHECKOUT_FIELDS[step]
    bot.send_message(chat_id, question)


@bot.message_handler(func=lambda m: is_private(m) and m.text == BTN_CHECKOUT)
def start_checkout(message: types.Message):
    chat_id = message.chat.id
    items = user_cart.get(chat_id, [])

    if not items:
        bot.send_message(chat_id, "Кошик порожній 🧺", reply_markup=kb_cart())
        return

    user_checkout[chat_id] = {}
    user_checkout_step[chat_id] = 0
    nav_go(chat_id, SCR_CHECKOUT)

    bot.send_message(
        chat_id,
        "Оформлюємо замовлення 📝\nВідповідайте по черзі.",
        reply_markup=types.ReplyKeyboardRemove()
    )
    ask_next_field(chat_id)


PHONE_RE = re.compile(r"^\+\d{10,15}$")


@bot.message_handler(func=lambda m: is_private(m) and (m.chat.id in user_checkout_step))
def collect_checkout(message: types.Message):
    chat_id = message.chat.id
    step = user_checkout_step.get(chat_id)

    if step is None:
        return
    if step >= len(CHECKOUT_FIELDS):
        return

    value = (message.text or "").strip()
    if not value:
        bot.send_message(chat_id, "Напишіть текстом 👇")
        return

    key, _ = CHECKOUT_FIELDS[step]

    if key == "phone":
        cleaned = value.replace(" ", "").replace("-", "")
        ok = bool(PHONE_RE.match(cleaned))
        if not ok:
            bot.send_message(chat_id, "Номер введено некоректно ❌\nПриклад: +380XXXXXXXXX")
            return
        value = cleaned

    user_checkout[chat_id][key] = value
    user_checkout_step[chat_id] = step + 1
    ask_next_field(chat_id)


def send_order_to_admin(chat_id: int) -> None:
    items = user_cart.get(chat_id, [])
    data = user_checkout.get(chat_id, {})

    total = sum(int(i.get("price") or 0) for i in items)
    lines = []
    for idx, i in enumerate(items, 1):
        lines.append(f"{idx}) {i.get('title','')} — {i.get('ml')} мл — {i.get('price')} грн")
    items_text = "\n".join(lines)

    text = (
        "🔥 <b>НОВЕ ЗАМОВЛЕННЯ</b>\n\n"
        f"👤 <b>Клієнт:</b> {data.get('first_name','')} {data.get('last_name','')}\n"
        f"📞 <b>Телефон:</b> {data.get('phone','')}\n"
        f"🏙️ <b>Місто:</b> {data.get('city','')}\n"
        f"📦 <b>НП:</b> {data.get('np_type','')} №{data.get('np_number','')}\n\n"
        f"🧴 <b>Товари:</b>\n{items_text}\n\n"
        f"💰 <b>Разом:</b> {total} грн\n"
        f"🆔 <b>Chat ID клієнта:</b> <code>{chat_id}</code>"
    )

    sent = safe_send_to_admin(text)

    if sent:
        bot.send_message(chat_id, "Дякуємо ❤️ Замовлення відправлено адміністратору.", reply_markup=kb_main())
    else:
        bot.send_message(chat_id, "Помилка відправки адміністратору ❌\nАдміністратор: " + ADMIN_LINK, reply_markup=kb_main())

    # очистка
    user_cart[chat_id] = []
    user_checkout.pop(chat_id, None)
    user_checkout_step.pop(chat_id, None)
    # навигацию возвращаем в начало
    user_nav[chat_id] = [SCR_MAIN]
    user_selected[chat_id] = {}


# =========================
# FALLBACK (последним)
# В группах молчим
# =========================
@bot.message_handler(func=lambda m: True)
def fallback(message: types.Message):
    if not is_private(message):
        return
    bot.send_message(message.chat.id, "Я вас зрозуміла ✅\nОберіть кнопку в меню нижче.", reply_markup=kb_main())


# =========================
# RUN
# =========================
def main():
    log.info("Starting bot...")
    try:
        bot.remove_webhook()
    except Exception as e:
        log.warning("remove_webhook warning: %s", e)

    bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=30)


if __name__ == "__main__":
    main()
