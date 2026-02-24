import os
import telebot
from telebot import types

# =========================
# CONFIG
# =========================
TOKEN = os.environ.get("TOKEN")
if not TOKEN:
    raise RuntimeError("TOKEN env var is not set")

bot = telebot.TeleBot(TOKEN, parse_mode=None)

ADMIN_LINK = "https://t.me/beautyspace_admin"

# =========================
# BUTTONS (UA UI)
# =========================
BTN_HOME = "🏠 Головне меню"
BTN_BACK = "⬅️ Назад"

BTN_SALON = "Салон"
BTN_SHOP = "Магазин косметики"
BTN_ADMIN = "Зв'язатися з адміністратором"
BTN_PRICE = "Прайс салону"

BTN_REDKEN = "Redken"
BTN_EG = "EG by Gromova"

# Redken lines
RD_ACIDIC = "Acidic Bonding"
RD_ALLSOFT = "All Soft"
RD_MEGA_CURL = "All Soft Mega Curls"
RD_BLONDAGE = "Blondage"
RD_EXTREME = "Extreme"
RD_FRIZZ = "Frizz Dismiss"
RD_VOLUME = "Volume Injection"

# Product buttons
BTN_CHOOSE_VOLUME = "Вибрати обʼєм"
BTN_ADD_TO_CART = "Додати в кошик"
BTN_HOW_TO_USE = "Як правильно використовувати"
BTN_CART = "🧺 Кошик"

# Acidic volumes
BTN_VOL_300 = "300 мл — 950 грн"
BTN_VOL_500 = "500 мл — 1250 грн"

# Cart actions
BTN_CART_SHOW = "Показати кошик"
BTN_CART_CLEAR = "Очистити кошик"

# =========================
# SERVICES (can keep your texts)
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

# =========================
# PRODUCTS (template)
# =========================
PRODUCTS = {
    "acidic_shampoo": {
        "title": "Redken Acidic Bonding Shampoo",
        "photo": "https://raw.githubusercontent.com/gromovaglushakelena-hub/telegram-bot/main/images/redken/acidic-bonding-shampoo-300.jpg",
        "short": "Відновлюючий шампунь для пошкодженого волосся.",
        "how_to_use": (
            "Як використовувати:\n"
            "1) Намочіть волосся.\n"
            "2) Нанесіть шампунь на шкіру голови.\n"
            "3) Спіньте 1–2 хвилини.\n"
            "4) Змийте.\n"
            "5) Повторіть за потреби.\n\n"
            "Після — бальзам або маска."
        ),
        "volumes": {
            BTN_VOL_300: {"ml": 300, "price": 950},
            BTN_VOL_500: {"ml": 500, "price": 1250},
        }
    }
}

# =========================
# STATE (navigation stack + selected options + cart)
# =========================
user_nav = {}      # chat_id -> [screen1, screen2, ...]
user_selected = {} # chat_id -> dict (selected product, volume, etc.)
user_cart = {}     # chat_id -> list of items

# Screen names
SCR_MAIN = "main"
SCR_SALON = "salon"
SCR_PRICE = "price"
SCR_SHOP = "shop"
SCR_REDKEN = "redken"
SCR_PRODUCT_ACIDIC = "product_acidic"
SCR_VOL_ACIDIC = "vol_acidic"
SCR_CART = "cart"

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

def kb_price():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.row(SVC_CAMO, SVC_INTEGR)
    m.row(SVC_TONE, SVC_COLOR)
    m.row(SVC_HIGHL, SVC_AIRTOUCH)
    m.row(SVC_DARK_OUT, SVC_CUT)
    m.row(SVC_RECON)
    m.row(BTN_BACK, BTN_HOME)
    return m

def kb_shop():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.row(BTN_REDKEN, BTN_EG)
    m.row(BTN_BACK, BTN_HOME)
    return m

def kb_redken():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.row(RD_ACIDIC, RD_ALLSOFT)
    m.row(RD_MEGA_CURL, RD_BLONDAGE)
    m.row(RD_EXTREME, RD_FRIZZ)
    m.row(RD_VOLUME)
    m.row(BTN_BACK, BTN_HOME)
    return m

def kb_product():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.row(BTN_CHOOSE_VOLUME)
    m.row(BTN_ADD_TO_CART, BTN_HOW_TO_USE)
    m.row(BTN_BACK, BTN_HOME)
    return m

def kb_volumes():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.row(BTN_VOL_300, BTN_VOL_500)
    m.row(BTN_BACK, BTN_HOME)
    return m

def kb_cart():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.row(BTN_CART_SHOW, BTN_CART_CLEAR)
    m.row(BTN_BACK, BTN_HOME)
    return m

# =========================
# NAV HELPERS
# =========================
def nav_init(chat_id: int):
    if chat_id not in user_nav:
        user_nav[chat_id] = []
    if chat_id not in user_selected:
        user_selected[chat_id] = {}
    if chat_id not in user_cart:
        user_cart[chat_id] = []

def nav_go(chat_id: int, screen: str):
    nav_init(chat_id)
    user_nav[chat_id].append(screen)

def nav_back(chat_id: int):
    nav_init(chat_id)
    if len(user_nav[chat_id]) > 1:
        user_nav[chat_id].pop()  # remove current
    else:
        user_nav[chat_id] = [SCR_MAIN]

def nav_current(chat_id: int) -> str:
    nav_init(chat_id)
    if not user_nav[chat_id]:
        user_nav[chat_id] = [SCR_MAIN]
    return user_nav[chat_id][-1]

def show_screen(chat_id: int, screen: str):
    # Central place: what to show for each screen
    if screen == SCR_MAIN:
        bot.send_message(chat_id, "Вітаємо 💛\nОберіть розділ нижче:", reply_markup=kb_main())

    elif screen == SCR_SALON:
        bot.send_message(chat_id, "Розділ: Салон ✂️\nОберіть, що потрібно:", reply_markup=kb_salon())

    elif screen == SCR_PRICE:
        bot.send_message(chat_id, "Прайс салону 💰\nОберіть послугу:", reply_markup=kb_price())

    elif screen == SCR_SHOP:
        bot.send_message(chat_id, "Магазин косметики 🛍️\nОберіть бренд:", reply_markup=kb_shop())

    elif screen == SCR_REDKEN:
        bot.send_message(chat_id, "Redken 🧴\nОберіть лінійку:", reply_markup=kb_redken())

    elif screen == SCR_PRODUCT_ACIDIC:
        p = PRODUCTS["acidic_shampoo"]
        caption = f'{p["title"]} 300 мл\n\n{p["short"]}'
        bot.send_photo(chat_id, p["photo"], caption=caption, reply_markup=kb_product())

    elif screen == SCR_VOL_ACIDIC:
        bot.send_message(chat_id, "Оберіть обʼєм:", reply_markup=kb_volumes())

    elif screen == SCR_CART:
        bot.send_message(chat_id, "Кошик 🧺\nОберіть дію:", reply_markup=kb_cart())

    else:
        # fallback
        bot.send_message(chat_id, "Оберіть кнопку в меню нижче ✅", reply_markup=kb_main())

# =========================
# COMMANDS
# =========================
@bot.message_handler(commands=["start"])
def cmd_start(message):
    chat_id = message.chat.id
    nav_init(chat_id)
    user_nav[chat_id] = [SCR_MAIN]
    user_selected[chat_id] = {}
    show_screen(chat_id, SCR_MAIN)

# =========================
# GLOBAL NAV BUTTONS
# =========================
@bot.message_handler(func=lambda m: m.text == BTN_HOME)
def handle_home(message):
    chat_id = message.chat.id
    nav_init(chat_id)
    user_nav[chat_id] = [SCR_MAIN]
    show_screen(chat_id, SCR_MAIN)

@bot.message_handler(func=lambda m: m.text == BTN_BACK)
def handle_back(message):
    chat_id = message.chat.id
    nav_back(chat_id)
    show_screen(chat_id, nav_current(chat_id))

# =========================
# MAIN MENU
# =========================
@bot.message_handler(func=lambda m: m.text == BTN_SALON)
def open_salon(message):
    chat_id = message.chat.id
    nav_go(chat_id, SCR_SALON)
    show_screen(chat_id, SCR_SALON)

@bot.message_handler(func=lambda m: m.text == BTN_SHOP)
def open_shop(message):
    chat_id = message.chat.id
    nav_go(chat_id, SCR_SHOP)
    show_screen(chat_id, SCR_SHOP)

@bot.message_handler(func=lambda m: m.text == BTN_ADMIN)
def contact_admin(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, f"Напишіть адміністратору 👇\n{ADMIN_LINK}", reply_markup=kb_main())

@bot.message_handler(func=lambda m: m.text == BTN_CART)
def open_cart(message):
    chat_id = message.chat.id
    nav_go(chat_id, SCR_CART)
    show_screen(chat_id, SCR_CART)

# =========================
# SALON
# =========================
@bot.message_handler(func=lambda m: m.text == BTN_PRICE)
def open_price(message):
    chat_id = message.chat.id
    nav_go(chat_id, SCR_PRICE)
    show_screen(chat_id, SCR_PRICE)

@bot.message_handler(func=lambda m: m.text in SERVICE_TEXTS)
def show_service(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, SERVICE_TEXTS[message.text], reply_markup=kb_price())

# =========================
# SHOP
# =========================
@bot.message_handler(func=lambda m: m.text == BTN_REDKEN)
def open_redken(message):
    chat_id = message.chat.id
    nav_go(chat_id, SCR_REDKEN)
    show_screen(chat_id, SCR_REDKEN)

@bot.message_handler(func=lambda m: m.text == BTN_EG)
def open_eg(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "EG by Gromova (додамо товари пізніше) 💛", reply_markup=kb_shop())

# =========================
# REDKEN LINES
# =========================
@bot.message_handler(func=lambda m: m.text == RD_ACIDIC)
def show_acidic_product(message):
    chat_id = message.chat.id
    # remember selected product
    nav_init(chat_id)
    user_selected[chat_id]["product_key"] = "acidic_shampoo"
    user_selected[chat_id].pop("volume_btn", None)  # reset volume
    nav_go(chat_id, SCR_PRODUCT_ACIDIC)
    show_screen(chat_id, SCR_PRODUCT_ACIDIC)

# placeholders for other lines (so user doesn't get stuck)
@bot.message_handler(func=lambda m: m.text in {RD_ALLSOFT, RD_MEGA_CURL, RD_BLONDAGE, RD_EXTREME, RD_FRIZZ, RD_VOLUME})
def other_redken_lines(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Цю лінійку додамо наступною ✅", reply_markup=kb_redken())

# =========================
# PRODUCT ACTIONS
# =========================
@bot.message_handler(func=lambda m: m.text == BTN_CHOOSE_VOLUME)
def choose_volume(message):
    chat_id = message.chat.id
    # only from product screen makes sense, but we allow anyway
    nav_go(chat_id, SCR_VOL_ACIDIC)
    show_screen(chat_id, SCR_VOL_ACIDIC)

@bot.message_handler(func=lambda m: m.text in {BTN_VOL_300, BTN_VOL_500})
def select_volume(message):
    chat_id = message.chat.id
    nav_init(chat_id)
    product_key = user_selected[chat_id].get("product_key")
    if not product_key:
        # no product chosen -> return to main
        user_nav[chat_id] = [SCR_MAIN]
        show_screen(chat_id, SCR_MAIN)
        return

    p = PRODUCTS[product_key]
    if message.text not in p["volumes"]:
        bot.send_message(chat_id, "Оберіть обʼєм з кнопок нижче ✅", reply_markup=kb_volumes())
        return

    user_selected[chat_id]["volume_btn"] = message.text
    info = p["volumes"][message.text]
    bot.send_message(
        chat_id,
        f"Ви обрали {info['ml']} мл — {info['price']} грн\n\nТепер натисніть «Додати в кошик».",
        reply_markup=kb_product()
    )
    # after choosing volume we go back to product screen logically
    # (so "Назад" from product returns to Redken)
    # remove the volume screen from stack if it is current
    if nav_current(chat_id) == SCR_VOL_ACIDIC:
        nav_back(chat_id)

@bot.message_handler(func=lambda m: m.text == BTN_HOW_TO_USE)
def how_to_use(message):
    chat_id = message.chat.id
    nav_init(chat_id)
    product_key = user_selected[chat_id].get("product_key")
    if not product_key:
        bot.send_message(chat_id, "Спочатку оберіть товар ✅", reply_markup=kb_main())
        return
    p = PRODUCTS[product_key]
    bot.send_message(chat_id, p["how_to_use"], reply_markup=kb_product())

@bot.message_handler(func=lambda m: m.text == BTN_ADD_TO_CART)
def add_to_cart(message):
    chat_id = message.chat.id
    nav_init(chat_id)

    product_key = user_selected[chat_id].get("product_key")
    volume_btn = user_selected[chat_id].get("volume_btn")

    if not product_key:
        bot.send_message(chat_id, "Спочатку оберіть товар ✅", reply_markup=kb_main())
        return

    if not volume_btn:
        bot.send_message(chat_id, "Спочатку натисніть «Вибрати обʼєм» ✅", reply_markup=kb_product())
        return

    p = PRODUCTS[product_key]
    info = p["volumes"][volume_btn]
    item = {
        "title": p["title"],
        "ml": info["ml"],
        "price": info["price"]
    }
    user_cart[chat_id].append(item)

    bot.send_message(
        chat_id,
        f"Додано в кошик ✅\n{item['title']} — {item['ml']} мл — {item['price']} грн\n\n"
        f"Можна додати ще або відкрити кошик: «{BTN_CART}».",
        reply_markup=kb_product()
    )

# =========================
# CART
# =========================
@bot.message_handler(func=lambda m: m.text == BTN_CART_SHOW)
def cart_show(message):
    chat_id = message.chat.id
    nav_init(chat_id)

    items = user_cart[chat_id]
    if not items:
        bot.send_message(chat_id, "Кошик порожній 🫶", reply_markup=kb_cart())
        return

    total = sum(i["price"] for i in items)
    lines = []
    for idx, i in enumerate(items, 1):
        lines.append(f"{idx}) {i['title']} — {i['ml']} мл — {i['price']} грн")

    text = "Ваш кошик 🧺\n\n" + "\n".join(lines) + f"\n\nРазом: {total} грн"
    bot.send_message(chat_id, text, reply_markup=kb_cart())

@bot.message_handler(func=lambda m: m.text == BTN_CART_CLEAR)
def cart_clear(message):
    chat_id = message.chat.id
    nav_init(chat_id)
    user_cart[chat_id] = []
    bot.send_message(chat_id, "Кошик очищено ✅", reply_markup=kb_cart())

# =========================
# CHECKOUT → SEND TO GROUP
# =========================

# 👉 ВСТАВЬ СЮДА ID ГРУППЫ (начинается с -100...)
ADMIN_CHAT_ID = -1000000000000  # ← ПОКА ВРЕМЕННО, потом заменишь


# Храним данные заказа клиента
user_checkout = {}
user_checkout_step = {}


CHECKOUT_FIELDS = [
    ("first_name", "Вкажіть ваше ім’я 👇"),
    ("last_name", "Вкажіть ваше прізвище 👇"),
    ("phone", "Вкажіть номер телефону 📞\nПриклад: +380XXXXXXXXX"),
    ("city", "Вкажіть місто 🏙️"),
    ("np_type", "Доставка Новою Поштою:\nНапишіть: Відділення або Поштомат 📦"),
    ("np_number", "Вкажіть номер відділення або поштомату 👇"),
]


def kb_cart():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(BTN_CART_SHOW, BTN_CART_CLEAR)
    kb.row("✅ Оформити замовлення")
    kb.row(BTN_BACK, BTN_HOME)
    return kb


@bot.message_handler(func=lambda m: m.text == "✅ Оформити замовлення")
def start_checkout(message):
    chat_id = message.chat.id

    items = user_cart.get(chat_id, [])
    if not items:
        bot.send_message(chat_id, "Кошик порожній 🧺", reply_markup=kb_cart())
        return

    user_checkout[chat_id] = {}
    user_checkout_step[chat_id] = 0

    bot.send_message(chat_id, "Оформлюємо замовлення 📝\nВідповідайте по черзі.", reply_markup=types.ReplyKeyboardRemove())
    ask_next_field(chat_id)


def ask_next_field(chat_id):
    step = user_checkout_step[chat_id]

    if step >= len(CHECKOUT_FIELDS):
        send_order_to_group(chat_id)
        return

    key, question = CHECKOUT_FIELDS[step]
    bot.send_message(chat_id, question)


@bot.message_handler(func=lambda m: m.chat.id in user_checkout_step)
def collect_checkout_data(message):
    chat_id = message.chat.id

    step = user_checkout_step.get(chat_id)
    if step is None:
        return

    key, _ = CHECKOUT_FIELDS[step]
    value = (message.text or "").strip()

    # Проверка телефона
    if key == "phone":
        cleaned = value.replace(" ", "").replace("-", "")
        if not (cleaned.startswith("+") and len(cleaned) >= 10):
            bot.send_message(chat_id, "Номер введено некоректно ❌\nПриклад: +380XXXXXXXXX")
            return

    user_checkout[chat_id][key] = value
    user_checkout_step[chat_id] += 1

    ask_next_field(chat_id)


def send_order_to_group(chat_id):
    items = user_cart.get(chat_id, [])
    data = user_checkout.get(chat_id, {})

    total = sum(i["price"] for i in items)

    lines = []
    for idx, i in enumerate(items, 1):
        lines.append(f"{idx}) {i['title']} — {i['ml']} мл — {i['price']} грн")

    items_text = "\n".join(lines)

    text = (
        "🔥 НОВЕ ЗАМОВЛЕННЯ\n\n"
        f"👤 {data['first_name']} {data['last_name']}\n"
        f"📞 {data['phone']}\n"
        f"🏙️ {data['city']}\n"
        f"📦 НП: {data['np_type']} №{data['np_number']}\n\n"
        f"🧴 Товари:\n{items_text}\n\n"
        f"💰 Разом: {total} грн\n\n"
        f"🆔 Telegram клієнта: {chat_id}"
    )

    try:
        bot.send_message(ADMIN_CHAT_ID, text)
        bot.send_message(chat_id, "Дякуємо ❤️ Замовлення відправлено адміністратору.", reply_markup=kb_main())
    except:
        bot.send_message(chat_id, "Помилка відправки адміністратору ❌")

    # Очистка
    user_cart[chat_id] = []
    user_checkout.pop(chat_id, None)
    user_checkout_step.pop(chat_id, None)

# =========================
# FALLBACK (unknown text)
# IMPORTANT: must be LAST handler
# =========================
@bot.message_handler(func=lambda m: True)
def unknown(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Я вас зрозуміла ✅\nОберіть кнопку в меню нижче.", reply_markup=kb_main())

# =========================
# RUN
# =========================
# Important for Render + polling:
# - remove webhook just in case
# - skip_pending=True helps avoid old queued updates
bot.remove_webhook()
bot.infinity_polling(skip_pending=True)
