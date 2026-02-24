import os
import logging
import telebot
from telebot import types

# =========================
# CONFIG
# =========================
TOKEN = (os.environ.get("TOKEN") or "").strip()
ADMIN_CHAT_ID = (os.environ.get("ADMIN_CHAT_ID") or "").strip()  # пример: -5268865051

if not TOKEN:
    raise RuntimeError("TOKEN env var is not set")

if not ADMIN_CHAT_ID:
    raise RuntimeError("ADMIN_CHAT_ID env var is not set (example: -5268865051)")

ADMIN_CHAT_ID = int(ADMIN_CHAT_ID)

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

# =========================
# HELPERS
# =========================
def is_private(message: types.Message) -> bool:
    return message.chat.type == "private"

def safe_send_to_admin(text: str) -> bool:
    try:
        bot.send_message(ADMIN_CHAT_ID, text, reply_markup=types.ReplyKeyboardRemove(), disable_web_page_preview=True)
        return True
    except Exception as e:
        log.exception("Failed to send to admin chat: %s", e)
        return False

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

def kb_price(services):
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for row in services:
        m.row(*row)
    m.row(BTN_BACK, BTN_HOME)
    return m

def kb_shop():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.row(BTN_REDKEN, BTN_EG)
    m.row(BTN_BACK, BTN_HOME)
    return m

def kb_lines(lines):
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for row in lines:
        m.row(*row)
    m.row(BTN_BACK, BTN_HOME)
    return m

def kb_product():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.row(BTN_CHOOSE_VOLUME)
    m.row(BTN_ADD_TO_CART, BTN_HOW_TO_USE)
    m.row(BTN_BACK, BTN_HOME)
    return m

def kb_volumes(volume_buttons):
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for row in volume_buttons:
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
# CATALOG (товары + цены + описания)
# =========================
# Твоя задача потом: вставить "photo" и поменять price.
# Фото пока можешь оставлять пустым "".

CATALOG = {
    "Redken": {
        "lines": {
            "Acidic Bonding": {
    "items": {
        "acidic_shampoo": {
            "title": "Redken Acidic Bonding Shampoo",
            "photo": "URL_ФОТО_ШАМПУНЬ_ABC",
            "short": "Відновлюючий шампунь для пошкодженого та освітленого волосся. Зменшує ламкість, ущільнює структуру.",
            "how_to_use": "Нанесіть на вологе волосся, спіньте, змийте. Використовуйте разом із кондиціонером.",
            "volumes": {
                "300 мл — 950 грн": {"ml": 300, "price": 950},
                "500 мл — 1250 грн": {"ml": 500, "price": 1250}
            }
        },
        "acidic_conditioner": {
            "title": "Redken Acidic Bonding Conditioner",
            "photo": "URL_ФОТО_БАЛЬЗАМ_ABC",
            "short": "Кондиціонер для зміцнення довжини. Розгладжує та додає блиску.",
            "how_to_use": "Нанесіть після шампуню на довжину, витримайте 1–3 хв, змийте.",
            "volumes": {
                "300 мл — 950 грн": {"ml": 300, "price": 950},
                "500 мл — 1250 грн": {"ml": 500, "price": 1250}
            }
        },
        "acidic_mask": {
            "title": "Redken Acidic Bonding Mask",
            "photo": "URL_ФОТО_МАСКА_ABC",
            "short": "Інтенсивна маска для глибокого відновлення волосся.",
            "how_to_use": "Нанесіть після шампуню на 5–10 хвилин. 1–2 рази на тиждень.",
            "volumes": {
                "250 мл — 1300 грн": {"ml": 250, "price": 1300}
            }
        },
        "acidic_leavein": {
            "title": "Redken Acidic Bonding Leave-In",
            "photo": "URL_ФОТО_КРЕМ_ABC",
            "short": "Незмивний крем-захист. Зменшує пухнастість та ламкість.",
            "how_to_use": "Нанесіть на вологу довжину, не змивайте.",
            "volumes": {
                "150 мл — 1000 грн": {"ml": 150, "price": 1000}
            }
        }
    }
},

"All Soft": {
    "items": {
        "allsoft_shampoo": {
            "title": "Redken All Soft Shampoo",
            "photo": "URL_ФОТО_ALLSOFT_SH",
            "short": "Живильний шампунь для сухого волосся.",
            "how_to_use": "Нанесіть на вологе волосся, спіньте, змийте.",
            "volumes": {
                "300 мл — 850 грн": {"ml": 300, "price": 850}
            }
        },
        "allsoft_conditioner": {
            "title": "Redken All Soft Conditioner",
            "photo": "URL_ФОТО_ALLSOFT_COND",
            "short": "Кондиціонер для м’якості та гладкості.",
            "how_to_use": "Нанесіть на довжину після шампуню, змийте.",
            "volumes": {
                "300 мл — 850 грн": {"ml": 300, "price": 850}
            }
        },
        "allsoft_cream": {
            "title": "Redken All Soft Leave-In Cream",
            "photo": "URL_ФОТО_ALLSOFT_CREAM",
            "short": "Незмивний крем для м’якості та захисту.",
            "how_to_use": "Нанесіть на вологу довжину, не змивайте.",
            "volumes": {
                "150 мл — 950 грн": {"ml": 150, "price": 950}
            }
        },
        "allsoft_oil": {
            "title": "Redken All Soft Oil",
            "photo": "URL_ФОТО_ALLSOFT_OIL",
            "short": "Флюїд-олійка для блиску та гладкості.",
            "how_to_use": "Нанесіть 1–2 краплі на суху або вологу довжину.",
            "volumes": {
                "111 мл — 1000 грн": {"ml": 111, "price": 1000}
            }
        }
    }
},

"Acidic Color Gloss": {
    "items": {
        "color_shampoo": {
            "title": "Redken Acidic Color Gloss Shampoo",
            "photo": "URL_ФОТО_COLOR_SH",
            "short": "Шампунь для збереження яскравості кольору.",
            "how_to_use": "Нанесіть на вологе волосся, змийте.",
            "volumes": {
                "300 мл — 950 грн": {"ml": 300, "price": 950}
            }
        },
        "color_conditioner": {
            "title": "Redken Acidic Color Gloss Conditioner",
            "photo": "URL_ФОТО_COLOR_COND",
            "short": "Кондиціонер для блиску та захисту кольору.",
            "how_to_use": "Нанесіть на довжину після шампуню.",
            "volumes": {
                "300 мл — 950 грн": {"ml": 300, "price": 950}
            }
        },
        "color_fluid": {
            "title": "Redken Acidic Color Gloss Fluid",
            "photo": "URL_ФОТО_COLOR_FLUID",
            "short": "Незмивний флюїд для сяйва кольору.",
            "how_to_use": "Нанесіть на довжину, не змивайте.",
            "volumes": {
                "100 мл — 1000 грн": {"ml": 100, "price": 1000}
            }
        },
        "color_treatment": {
            "title": "Redken Acidic Color Gloss Treatment",
            "photo": "URL_ФОТО_COLOR_TREAT",
            "short": "Інтенсивний догляд для продовження стійкості кольору.",
            "how_to_use": "Нанесіть після шампуню на 5 хв.",
            "volumes": {
                "237 мл — 1400 грн": {"ml": 237, "price": 1400}
            }
        }
    }
}
"Extreme": {
    "items": {
        "extreme_shampoo": {
            "title": "Redken Extreme Shampoo",
            "photo": "URL_EXTREME_SHAMPOO",
            "short": "Зміцнюючий шампунь для ослабленого та ламкого волосся.",
            "how_to_use": "Нанесіть на вологе волосся, спіньте, змийте.",
            "volumes": {
                "300 мл — 950 грн": {"ml": 300, "price": 950}
            }
        },
        "extreme_conditioner": {
            "title": "Redken Extreme Conditioner",
            "photo": "URL_EXTREME_CONDITIONER",
            "short": "Кондиціонер для відновлення структури волосся.",
            "how_to_use": "Нанесіть після шампуню на довжину, змийте.",
            "volumes": {
                "300 мл — 950 грн": {"ml": 300, "price": 950}
            }
        }
    }
},

"Extreme Length": {
    "items": {
        "extreme_length_shampoo": {
            "title": "Redken Extreme Length Shampoo",
            "photo": "URL_EXTREME_LENGTH_SH",
            "short": "Шампунь з біотином для зміцнення довжини.",
            "how_to_use": "Нанесіть на вологе волосся, змийте.",
            "volumes": {
                "300 мл — 950 грн": {"ml": 300, "price": 950}
            }
        },
        "extreme_length_conditioner": {
            "title": "Redken Extreme Length Conditioner",
            "photo": "URL_EXTREME_LENGTH_COND",
            "short": "Кондиціонер для росту та зменшення ламкості.",
            "how_to_use": "Нанесіть на довжину після шампуню.",
            "volumes": {
                "300 мл — 950 грн": {"ml": 300, "price": 950}
            }
        }
    }
},

"Volume Injection": {
    "items": {
        "volume_shampoo": {
            "title": "Redken Volume Injection Shampoo",
            "photo": "URL_VOLUME_SH",
            "short": "Шампунь для надання об’єму тонкому волоссю.",
            "how_to_use": "Нанесіть на вологе волосся, змийте.",
            "volumes": {
                "300 мл — 950 грн": {"ml": 300, "price": 950}
            }
        },
        "volume_conditioner": {
            "title": "Redken Volume Injection Conditioner",
            "photo": "URL_VOLUME_COND",
            "short": "Легкий кондиціонер для об’єму без обтяження.",
            "how_to_use": "Нанесіть після шампуню на довжину.",
            "volumes": {
                "300 мл — 950 грн": {"ml": 300, "price": 950}
            }
        }
    }
},

"Frizz Dismiss": {
    "items": {
        "frizz_shampoo": {
            "title": "Redken Frizz Dismiss Shampoo",
            "photo": "URL_FRIZZ_SH",
            "short": "Шампунь проти пухнастості та вологості.",
            "how_to_use": "Нанесіть на вологе волосся, змийте.",
            "volumes": {
                "300 мл — 950 грн": {"ml": 300, "price": 950}
            }
        },
        "frizz_conditioner": {
            "title": "Redken Frizz Dismiss Conditioner",
            "photo": "URL_FRIZZ_COND",
            "short": "Кондиціонер для гладкості та контролю пухнастості.",
            "how_to_use": "Нанесіть після шампуню на довжину.",
            "volumes": {
                "300 мл — 950 грн": {"ml": 300, "price": 950}
            }
        }
    }
},

"Grow Full": {
    "items": {
        "growfull_shampoo": {
            "title": "Redken Grow Full Shampoo",
            "photo": "URL_GROWFULL_SH",
            "short": "Шампунь для стимуляції густоти волосся.",
            "how_to_use": "Нанесіть на шкіру голови, змийте.",
            "volumes": {
                "300 мл — 950 грн": {"ml": 300, "price": 950}
            }
        },
        "growfull_conditioner": {
            "title": "Redken Grow Full Conditioner",
            "photo": "URL_GROWFULL_COND",
            "short": "Кондиціонер для зміцнення та об’єму.",
            "how_to_use": "Нанесіть на довжину після шампуню.",
            "volumes": {
                "300 мл — 950 грн": {"ml": 300, "price": 950}
            }
        }
    }
},
            
            "EG by Gromova": {
        "lines": {
            "Система догляду": {"items": {}},
        }
    }
}

REDKEN_LINES_ROWS = [
    ("Acidic Bonding", "All Soft"),
    ("All Soft Mega Curls", "Blondage"),
    ("Extreme", "Frizz Dismiss"),
    ("Volume Injection",),
]

# =========================
# STATE
# =========================
user_nav = {}        # chat_id -> stack
user_selected = {}   # chat_id -> {"brand","line","item_key","volume_btn"}
user_cart = {}       # chat_id -> list of items

user_checkout = {}       # chat_id -> dict
user_checkout_step = {}  # chat_id -> int

SCR_MAIN = "main"
SCR_SALON = "salon"
SCR_PRICE = "price"
SCR_SHOP = "shop"
SCR_BRAND_REDKEN = "brand_redken"
SCR_BRAND_EG = "brand_eg"
SCR_LINE = "line"
SCR_ITEM = "item"
SCR_VOLUMES = "volumes"
SCR_CART = "cart"

CHECKOUT_FIELDS = [
    ("first_name", "Вкажіть ваше ім’я 👇"),
    ("last_name", "Вкажіть ваше прізвище 👇"),
    ("phone", "Вкажіть номер телефону 📞\nПриклад: +380XXXXXXXXX"),
    ("city", "Вкажіть місто 🏙️"),
    ("np_type", "Доставка Новою Поштою:\nНапишіть: Відділення або Поштомат 📦"),
    ("np_number", "Вкажіть номер відділення або поштомату 👇"),
]

def nav_init(chat_id: int):
    user_nav.setdefault(chat_id, [SCR_MAIN])
    user_selected.setdefault(chat_id, {})
    user_cart.setdefault(chat_id, [])

def nav_go(chat_id: int, screen: str):
    nav_init(chat_id)
    user_nav[chat_id].append(screen)

def nav_back(chat_id: int):
    nav_init(chat_id)
    if len(user_nav[chat_id]) > 1:
        user_nav[chat_id].pop()

def nav_current(chat_id: int) -> str:
    nav_init(chat_id)
    return user_nav[chat_id][-1]

# =========================
# RENDER SCREEN
# =========================
def show_main(chat_id: int):
    bot.send_message(chat_id, "Вітаємо 💛\nОберіть розділ нижче:", reply_markup=kb_main())

def show_salon(chat_id: int):
    bot.send_message(chat_id, "Розділ: Салон ✂️\nОберіть, що потрібно:", reply_markup=kb_salon())

def show_price(chat_id: int):
    bot.send_message(chat_id, "Прайс салону 💰\nОберіть послугу:", reply_markup=kb_price(PRICE_ROWS))

def show_shop(chat_id: int):
    bot.send_message(chat_id, "Магазин косметики 🛍️\nОберіть бренд:", reply_markup=kb_shop())

def show_redken_lines(chat_id: int):
    bot.send_message(chat_id, "Redken 🧴\nОберіть лінійку:", reply_markup=kb_lines(REDKEN_LINES_ROWS))

def show_cart(chat_id: int):
    bot.send_message(chat_id, "Кошик 🧺\nОберіть дію:", reply_markup=kb_cart())

def show_item(chat_id: int):
    sel = user_selected.get(chat_id, {})
    brand = sel.get("brand")
    line = sel.get("line")
    item_key = sel.get("item_key")

    item = CATALOG[brand]["lines"][line]["items"][item_key]
    caption = f"<b>{item['title']}</b>\n\n{item['short']}\n\nНатисніть «Вибрати обʼєм»."

    photo = item.get("photo", "").strip()
    if photo:
        bot.send_photo(chat_id, photo, caption=caption, reply_markup=kb_product())
    else:
        bot.send_message(chat_id, caption, reply_markup=kb_product())

def show_volumes(chat_id: int):
    sel = user_selected.get(chat_id, {})
    brand = sel.get("brand")
    line = sel.get("line")
    item_key = sel.get("item_key")

    item = CATALOG[brand]["lines"][line]["items"][item_key]
    volume_buttons = list(item["volumes"].keys())

    rows = []
    # делаем кнопки по 2 в ряд
    for i in range(0, len(volume_buttons), 2):
        rows.append(tuple(volume_buttons[i:i+2]))

    bot.send_message(chat_id, "Оберіть обʼєм:", reply_markup=kb_volumes(rows))

# =========================
# COMMANDS
# =========================
@bot.message_handler(commands=["start"])
def cmd_start(message):
    if not is_private(message):
        return
    chat_id = message.chat.id
    nav_init(chat_id)
    user_nav[chat_id] = [SCR_MAIN]
    user_selected[chat_id] = {}
    show_main(chat_id)

@bot.message_handler(commands=["id"])
def cmd_id(message):
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else None
    bot.send_message(chat_id, f"chat_id: {chat_id}\nuser_id: {user_id}", reply_markup=types.ReplyKeyboardRemove())

# =========================
# GLOBAL NAV (личка)
# =========================
@bot.message_handler(func=lambda m: is_private(m) and m.text == BTN_HOME)
def handle_home(message):
    chat_id = message.chat.id
    nav_init(chat_id)
    user_nav[chat_id] = [SCR_MAIN]
    show_main(chat_id)

@bot.message_handler(func=lambda m: is_private(m) and m.text == BTN_BACK)
def handle_back(message):
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
    if cur == SCR_CART:
        show_cart(chat_id)
        return

    # запасной выход
    show_main(chat_id)

# =========================
# MAIN MENU (личка)
# =========================
@bot.message_handler(func=lambda m: is_private(m) and m.text == BTN_SALON)
def open_salon(message):
    chat_id = message.chat.id
    nav_go(chat_id, SCR_SALON)
    show_salon(chat_id)

@bot.message_handler(func=lambda m: is_private(m) and m.text == BTN_SHOP)
def open_shop(message):
    chat_id = message.chat.id
    nav_go(chat_id, SCR_SHOP)
    show_shop(chat_id)

@bot.message_handler(func=lambda m: is_private(m) and m.text == BTN_ADMIN)
def contact_admin(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, f"Напишіть адміністратору 👇\n{ADMIN_LINK}", reply_markup=kb_main())

@bot.message_handler(func=lambda m: is_private(m) and m.text == BTN_CART)
def open_cart(message):
    chat_id = message.chat.id
    nav_go(chat_id, SCR_CART)
    show_cart(chat_id)

# =========================
# SALON (личка)
# =========================
@bot.message_handler(func=lambda m: is_private(m) and m.text == BTN_PRICE)
def open_price(message):
    chat_id = message.chat.id
    nav_go(chat_id, SCR_PRICE)
    show_price(chat_id)

@bot.message_handler(func=lambda m: is_private(m) and m.text in SERVICE_TEXTS)
def show_service(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, SERVICE_TEXTS[message.text], reply_markup=kb_price(PRICE_ROWS))

# =========================
# SHOP (личка)
# =========================
@bot.message_handler(func=lambda m: is_private(m) and m.text == BTN_REDKEN)
def open_redken(message):
    chat_id = message.chat.id
    user_selected[chat_id] = {"brand": "Redken"}
    nav_go(chat_id, SCR_BRAND_REDKEN)
    show_redken_lines(chat_id)

@bot.message_handler(func=lambda m: is_private(m) and m.text == BTN_EG)
def open_eg(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "EG by Gromova (товари додамо наступним блоком) 💛", reply_markup=kb_shop())

# =========================
# REDKEN LINES (личка)
# =========================
@bot.message_handler(func=lambda m: is_private(m) and m.text in CATALOG["Redken"]["lines"].keys())
def redken_line(message):
    chat_id = message.chat.id
    line = message.text

    # когда товаров нет — говорим и возвращаемся в линии
    items = CATALOG["Redken"]["lines"][line]["items"]
    if not items:
        bot.send_message(chat_id, "Цю лінійку додамо наступною ✅", reply_markup=kb_lines(REDKEN_LINES_ROWS))
        return

    # сейчас в Acidic Bonding открываем первый товар (шампунь)
    # позже добавлю меню товаров внутри линии
    first_key = list(items.keys())[0]
    user_selected[chat_id] = {"brand": "Redken", "line": line, "item_key": first_key}
    nav_go(chat_id, SCR_ITEM)
    show_item(chat_id)

# =========================
# PRODUCT ACTIONS (личка)
# =========================
@bot.message_handler(func=lambda m: is_private(m) and m.text == BTN_CHOOSE_VOLUME)
def choose_volume(message):
    chat_id = message.chat.id
    sel = user_selected.get(chat_id, {})
    ready = sel.get("brand") and sel.get("line") and sel.get("item_key")
    if not ready:
        show_shop(chat_id)
        return
    nav_go(chat_id, SCR_VOLUMES)
    show_volumes(chat_id)



@bot.message_handler(func=lambda m: is_private(m) and m.text == BTN_HOW_TO_USE)
def how_to_use(message):
    chat_id = message.chat.id
    sel = user_selected.get(chat_id, {})
    brand = sel.get("brand")
    line = sel.get("line")
    item_key = sel.get("item_key")

    ok = brand and line and item_key
    if not ok:
        show_shop(chat_id)
        return

    item = CATALOG[brand]["lines"][line]["items"][item_key]
    bot.send_message(chat_id, item["how_to_use"], reply_markup=kb_product())

@bot.message_handler(func=lambda m: is_private(m) and m.text == BTN_ADD_TO_CART)
def add_to_cart(message):
    chat_id = message.chat.id
    sel = user_selected.get(chat_id, {})
    brand = sel.get("brand")
    line = sel.get("line")
    item_key = sel.get("item_key")
    volume_btn = sel.get("volume_btn")

    ok = brand and line and item_key
    if not ok:
        show_shop(chat_id)
        return

    if not volume_btn:
        bot.send_message(chat_id, "Спочатку натисніть «Вибрати обʼєм» ✅", reply_markup=kb_product())
        return

    item = CATALOG[brand]["lines"][line]["items"][item_key]
    v = item["volumes"][volume_btn]

    user_cart[chat_id].append({
        "title": item["title"],
        "ml": v["ml"],
        "price": v["price"]
    })

    bot.send_message(
        chat_id,
        f"Додано в кошик ✅\n{item['title']} — {v['ml']} мл — {v['price']} грн\n\nВідкрийте кошик кнопкою «{BTN_CART}».",
        reply_markup=kb_product()
    )

# =========================
# CART (личка)
# =========================
@bot.message_handler(func=lambda m: is_private(m) and m.text == BTN_CART_SHOW)
def cart_show(message):
    chat_id = message.chat.id
    items = user_cart.get(chat_id, [])

    if not items:
        bot.send_message(chat_id, "Кошик порожній 🫶", reply_markup=kb_cart())
        return

    total = sum(i["price"] for i in items)
    lines = []
    for idx, i in enumerate(items, 1):
        lines.append(f"{idx}) {i['title']} — {i['ml']} мл — {i['price']} грн")

    text = "Ваш кошик 🧺\n\n" + "\n".join(lines) + f"\n\nРазом: {total} грн"
    bot.send_message(chat_id, text, reply_markup=kb_cart())

@bot.message_handler(func=lambda m: is_private(m) and m.text == BTN_CART_CLEAR)
def cart_clear(message):
    chat_id = message.chat.id
    user_cart[chat_id] = []
    bot.send_message(chat_id, "Кошик очищено ✅", reply_markup=kb_cart())

# =========================
# CHECKOUT (личка)
# =========================
def ask_next_field(chat_id: int):
    step = user_checkout_step.get(chat_id, 0)

    if step >= len(CHECKOUT_FIELDS):
        send_order_to_admin(chat_id)
        return

    key, question = CHECKOUT_FIELDS[step]
    bot.send_message(chat_id, question)

@bot.message_handler(func=lambda m: is_private(m) and m.text == BTN_CHECKOUT)
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

@bot.message_handler(func=lambda m: is_private(m) and m.chat.id in user_checkout_step)
def collect_checkout(message):
    chat_id = message.chat.id
    step = user_checkout_step.get(chat_id)
    key, _ = CHECKOUT_FIELDS[step]
    value = (message.text or "").strip()

    if key == "phone":
        cleaned = value.replace(" ", "").replace("-", "")
        good = cleaned.startswith("+") and len(cleaned) >= 10
        if not good:
            bot.send_message(chat_id, "Номер введено некоректно ❌\nПриклад: +380XXXXXXXXX")
            return
        value = cleaned

    user_checkout[chat_id][key] = value
    user_checkout_step[chat_id] = step + 1
    ask_next_field(chat_id)

def send_order_to_admin(chat_id: int):
    items = user_cart.get(chat_id, [])
    data = user_checkout.get(chat_id, {})

    total = sum(i["price"] for i in items)

    lines = []
    for idx, i in enumerate(items, 1):
        lines.append(f"{idx}) {i['title']} — {i['ml']} мл — {i['price']} грн")
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

# =========================
# FALLBACK (ПОСЛЕДНИМ)
# В группах молчим, чтобы меню не “дублировалось” в чате заказов
# =========================
@bot.message_handler(func=lambda m: True)
def fallback(message):
    if not is_private(message):
        return
    bot.send_message(message.chat.id, "Я вас зрозуміла ✅\nОберіть кнопку в меню нижче.", reply_markup=kb_main())

# =========================
# RUN
# =========================
bot.remove_webhook()
bot.infinity_polling(skip_pending=True)
