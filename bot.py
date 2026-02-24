import os
import telebot
from telebot import types

TOKEN = os.environ.get("TOKEN")
if not TOKEN:
    raise ValueError("TOKEN not found in environment variables")

bot = telebot.TeleBot(TOKEN)

# ===== Кнопки =====
BTN_SALON = "Салон"
BTN_SHOP = "Магазин косметики"
BTN_ADMIN = "Зв'язатися з адміністратором"
BTN_BACK = "⬅️ Назад"

BTN_REDKEN = "Redken"
BTN_EG = "EG by Gromova"
BTN_PRICE = "Прайс салону"

# ===== Лінійки Redken =====
RD_ACIDIC = "Acidic Bonding"
RD_ALLSOFT = "All Soft"
RD_MEGA_CURL = "All Soft Mega Curls"
RD_BLONDAGE = "Blondage"
RD_EXTREME = "Extreme"
RD_FRIZZ = "Frizz Dismiss"
RD_VOLUME = "Volume Injection"

# ===== Кнопки товара Acidic =====
BTN_CHOOSE_VOLUME = "Вибрати обʼєм"
BTN_VOL_300 = "300 мл — 950 грн"
BTN_VOL_500 = "500 мл — 1250 грн"
BTN_ADD_TO_CART = "Додати в кошик"
BTN_HOW_TO_USE = "Як правильно використовувати"
BTN_BACK_PRODUCT = "⬅ Назад до товару"  # кнопку оставляем как есть

ADMIN_LINK = "https://t.me/beautyspace_admin"

# ===== Послуги =====
SVC_CAMO = "Камуфляж сивини"
SVC_TONE = "Тонування"
SVC_COLOR = "Фарбування"
SVC_INTEGR = "Інтеграція сивини"
SVC_HIGHL = "Мелірування"
SVC_AIRTOUCH = "Airtouch"
SVC_DARK_OUT = "Вихід з темного кольору"
SVC_CUT = "Стрижка"
SVC_RECON = "Реконструкція 8D by Gromova"

# ===== Тексты услуг =====
SERVICE_TEXTS = {
    SVC_CAMO: (
        "Камуфляж сивини ✨\n\n"
        "Вартість: від 3000 грн\n"
        "Тривалість: до 1 години\n\n"
        "Що входить у процедуру:\n"
        "• консультація майстра\n"
        "• підбір відтінку\n"
        "• м’яке тонування сивини без зміни натурального кольору\n"
        "• стабілізація кольору\n"
        "• рекомендації по догляду\n\n"
        "⚠️ Камуфляж підходить не всім.\n"
        "Перед записом обов’язкова консультація.\n\n"
        "Реконструкція 8D by Gromova оплачується окремо."
    ),
    SVC_TONE: (
        "Тонування 🎨\n\n"
        "Вартість: від 3000 грн\n\n"
        "Що входить:\n"
        "• оновлення відтінку фарбником Redken\n"
        "• корекція нюансу кольору\n"
        "• стабілізація\n\n"
        "Реконструкція 8D by Gromova оплачується окремо."
    ),
    SVC_COLOR: (
        "Стійке фарбування 🖤\n\n"
        "Вартість: від 3500 грн\n\n"
        "Що входить:\n"
        "• консультація\n"
        "• фарбування кореня або кореня + довжини\n"
        "• стабілізація кольору\n\n"
        "Реконструкція 8D by Gromova оплачується окремо."
    ),
    SVC_INTEGR: (
        "Інтеграція сивини 🤍\n\n"
        "Вартість: від 12000 грн\n"
        "Тривалість: 6–10 годин\n\n"
        "Перед записом обов’язкова консультація.\n\n"
        "Реконструкція 8D by Gromova обов’язкова та оплачується додатково."
    ),
    SVC_HIGHL: (
        "Мелірування 🌟\n\n"
        "Вартість: від 12000 грн\n"
        "Тривалість: 4–6 годин\n\n"
        "Реконструкція 8D by Gromova обов’язкова та оплачується додатково."
    ),
    SVC_AIRTOUCH: (
        "Airtouch 💨\n\n"
        "Вартість: від 12000 грн\n"
        "Тривалість: 6–8 годин\n\n"
        "Реконструкція 8D by Gromova обов’язкова та оплачується додатково."
    ),
    SVC_DARK_OUT: (
        "Вихід з темного кольору 🚪\n\n"
        "Вартість: від 15000 грн\n\n"
        "⚠️ Перед записом обов’язкова консультація.\n"
        "Реконструкція 8D by Gromova обов’язкова та оплачується додатково."
    ),
    SVC_CUT: (
        "Стрижка ✂️\n\n"
        "Вартість: 1200 грн\n\n"
        "Що входить:\n"
        "• консультація\n"
        "• миття голови\n"
        "• укладка"
    ),
    SVC_RECON: (
        "Реконструкція 8D by Gromova 🧬\n\n"
        "Вартість: від 2500 грн\n"
        "Тривалість: до 2 годин\n\n"
        "8D by Gromova — авторська система глибокого відновлення волосся."
    ),
}

# ===== Фото/опис товару Acidic =====
ACIDIC_PHOTO_URL = "https://raw.githubusercontent.com/gromovaglushakelena-hub/telegram-bot/main/images/redken/acidic-bonding-shampoo-300.jpg"
ACIDIC_CAPTION = "Redken Acidic Bonding Shampoo 300 мл\n\nВідновлюючий шампунь для пошкодженого волосся."


# ===== Клавиатуры =====
def main_menu():
    markup = types.

ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(BTN_SALON, BTN_SHOP)
    markup.row(BTN_ADMIN)
    return markup


def salon_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(BTN_PRICE)
    markup.row(BTN_ADMIN)
    markup.row(BTN_BACK)
    return markup


def price_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(SVC_CAMO, SVC_INTEGR)
    markup.row(SVC_TONE, SVC_COLOR)
    markup.row(SVC_HIGHL, SVC_AIRTOUCH)
    markup.row(SVC_DARK_OUT, SVC_CUT)
    markup.row(SVC_RECON)
    markup.row(BTN_BACK)
    return markup


def shop_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(BTN_REDKEN, BTN_EG)
    markup.row(BTN_BACK)
    return markup


def redken_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(RD_ACIDIC, RD_ALLSOFT)
    markup.row(RD_MEGA_CURL, RD_BLONDAGE)
    markup.row(RD_EXTREME, RD_FRIZZ)
    markup.row(RD_VOLUME)
    markup.row(BTN_BACK)
    return markup


def acidic_volume_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(BTN_VOL_300, BTN_VOL_500)
    markup.row(BTN_BACK_PRODUCT)
    return markup


def product_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(BTN_CHOOSE_VOLUME)
    markup.row(BTN_ADD_TO_CART, BTN_HOW_TO_USE)
    markup.row(BTN_BACK_PRODUCT)
    return markup


# ===== Start =====
@bot.message_handler(commands=["start"])
def start_message(message):
    bot.send_message(
        message.chat.id,
        "Вітаємо 💛\nОберіть розділ нижче:",
        reply_markup=main_menu(),
    )


# ===== Главное меню =====
@bot.message_handler(func=lambda m: m.text == BTN_SALON)
def open_salon(message):
    bot.send_message(
        message.chat.id,
        "Розділ: Салон ✂️\nОберіть, що потрібно:",
        reply_markup=salon_menu(),
    )


@bot.message_handler(func=lambda m: m.text == BTN_SHOP)
def open_shop(message):
    bot.send_message(
        message.chat.id,
        "Магазин косметики 🛍️\nОберіть бренд:",
        reply_markup=shop_menu(),
    )


@bot.message_handler(func=lambda m: m.text == BTN_PRICE)
def open_price(message):
    bot.send_message(
        message.chat.id,
        "Прайс салону 💰\nОберіть послугу:",
        reply_markup=price_menu(),
    )


@bot.message_handler(func=lambda m: m.text in SERVICE_TEXTS)
def show_service(message):
    bot.send_message(
        message.chat.id,
        SERVICE_TEXTS[message.text],
        reply_markup=price_menu(),
    )


@bot.message_handler(func=lambda m: m.text == BTN_ADMIN)
def contact_admin(message):
    bot.send_message(
        message.chat.id,
        "Напишіть адміністратору 👇\n" + ADMIN_LINK,
        reply_markup=main_menu(),
    )


@bot.message_handler(func=lambda m: m.text == BTN_BACK)
def go_back(message):
    bot.send_message(
        message.chat.id,
        "Головне меню ✅",
        reply_markup=main_menu(),
    )


# ===== Redken =====
@bot.message_handler(func=lambda m: m.text == BTN_REDKEN)
def open_redken(message):
    bot.send_message(
        message.chat.id,
        "Redken 🧴\nОберіть лінійку:",
        reply_markup=redken_menu(),
    )


@bot.message_handler(func=lambda m: m.text == RD_ACIDIC)
def show_acidic(message):
    bot.send_photo(
        message.chat.id,
        ACIDIC_PHOTO_URL,
        caption=ACIDIC_CAPTION,
        reply_markup=product_menu(),
    )


@bot.message_handler(func=lambda m: m.text == BTN_CHOOSE_VOLUME)
def choose_volume(message):
    bot.send_message(
        message.chat.id,
        "Оберіть обʼєм:",
        reply_markup=acidic_volume_menu(),
    )


@bot.message_handler(func=lambda m: m.text == BTN_VOL_300)
def select_300(message):
    bot.send_message(
        message.chat.id,
        "Ви обрали 300 мл — 950 грн\n\nНатисніть «Додати в кошик».",
        reply_markup=product_menu(),
    )


@bot.message_handler(func=lambda m: m.text == BTN_VOL_500)
def select_500(message):
    bot.send_message(
        message.chat.id,
        "Ви обрали 500 мл — 1250 грн\n\nНатисніть «Додати в кошик».",

        reply_markup=product_menu(),
    )


# ✅ Назад до товару — делаем не строгое сравнение, чтобы работало и с ⬅ и с ⬅️
@bot.message_handler(func=lambda m: m.text and "Назад до товару" in m.text)
def back_to_product(message):
    bot.send_photo(
        message.chat.id,
        ACIDIC_PHOTO_URL,
        caption=ACIDIC_CAPTION,
        reply_markup=product_menu(),
    )


# ===== Заглушки, чтобы кнопки не были "мертвыми" =====
@bot.message_handler(func=lambda m: m.text == BTN_ADD_TO_CART)
def add_to_cart(message):
    bot.send_message(
        message.chat.id,
        "Кошик ще в розробці 🛒\nЯ додам це в наступному кроці.",
        reply_markup=product_menu(),
    )


@bot.message_handler(func=lambda m: m.text == BTN_HOW_TO_USE)
def how_to_use(message):
    bot.send_message(
        message.chat.id,
        "Як використовувати:\n"
        "1) Намочіть волосся.\n"
        "2) Нанесіть шампунь на шкіру голови.\n"
        "3) Спіньте 1–2 хвилини.\n"
        "4) Змийте.\n"
        "5) Повторіть за потреби.\n\n"
        "Після — бальзам або маска.",
        reply_markup=product_menu(),
    )


# ===== Фолбек на неизвестные сообщения (чтобы бот не молчал) =====
@bot.message_handler(func=lambda m: True)
def unknown(message):
    bot.send_message(
        message.chat.id,
        "Я вас зрозуміла ✅\nОберіть кнопку в меню нижче.",
        reply_markup=main_menu(),
    )


# ===== Запуск =====
bot.infinity_polling()
