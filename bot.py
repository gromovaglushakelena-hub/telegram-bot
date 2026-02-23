import telebot
import os
from telebot import types

TOKEN = os.environ.get("TOKEN")
bot = telebot.TeleBot(TOKEN)

# ===== Кнопки =====
BTN_SALON = "Салон"
BTN_SHOP = "Магазин косметики"
BTN_ADMIN = "Зв'язатися з адміністратором"
BTN_BACK = "⬅️ Назад"
BTN_PRICE = "Прайс салону"

SVC_CAMO = "Камуфляж сивини"
SVC_TONE = "Тонування"
SVC_COLOR = "Фарбування"
SVC_INTEGR = "Інтеграція сивини"
SVC_HIGHL = "Мелірування"
SVC_AIRTOUCH = "Airtouch"
SVC_DARK_OUT = "Вихід з темного кольору"
SVC_CUT = "Стрижка"
SVC_RECON = "Реконструкція 8D by Gromova"

ADMIN_LINK = "https://t.me/beautyspace_admin"

# ===== Тексты услуг =====
SERVICE_TEXTS = {
    SVC_CAMO: "Камуфляж сивини ✨\n\nВартість: від ____ грн\nТочна ціна залежить від довжини, густоти та % сивини.",
    SVC_TONE: "Тонування 🎨\n\nВартість: від ____ грн",
    SVC_COLOR: "Фарбування 🖤\n\nВартість: від ____ грн",
    SVC_INTEGR: "Інтеграція сивини 🤍\n\nВартість: від ____ грн",
    SVC_HIGHL: "Мелірування 🌟\n\nВартість: від ____ грн",
    SVC_AIRTOUCH: "Airtouch 💨\n\nВартість: від ____ грн",
    SVC_DARK_OUT: "Вихід з темного кольору 🚪\n\nВартість: від ____ грн",
    SVC_CUT: "Стрижка ✂️\n\nВартість: від ____ грн",
    SVC_RECON: "Реконструкція 8D by Gromova 🧬\n\nВартість: від ____ грн",
}

# ===== Клавиатуры =====
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
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

# ===== Start =====
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id,
                     "Вітаємо 💛\nОберіть розділ нижче:",
                     reply_markup=main_menu())

# ===== Главное меню =====
@bot.message_handler(func=lambda m: m.text == BTN_SALON)
def open_salon(message):
    bot.send_message(message.chat.id,
                     "Розділ: Салон ✂️\nОберіть, що потрібно:",
                     reply_markup=salon_menu())

@bot.message_handler(func=lambda m: m.text == BTN_PRICE)
def open_price(message):
    bot.send_message(message.chat.id,
                     "Прайс салону 💰\nОберіть послугу:",
                     reply_markup=price_menu())

@bot.message_handler(func=lambda m: m.text in SERVICE_TEXTS)
def show_service(message):
    bot.send_message(message.chat.id,
                     SERVICE_TEXTS[message.text],
                     reply_markup=price_menu())

@bot.message_handler(func=lambda m: m.text == BTN_ADMIN)
def contact_admin(message):
    bot.send_message(message.chat.id,
                     "Напишіть адміністратору 👇\n" + ADMIN_LINK,
                     reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == BTN_BACK)
def go_back(message):
    bot.send_message(message.chat.id,
                     "Головне меню ✅",
                     reply_markup=main_menu())

bot.infinity_polling()
