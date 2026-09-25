"""Telegram storefront and salon intake for Space of Beauty by Gromova."""
import html
import json
import logging
import os
import re
import time
from collections import Counter
from pathlib import Path

import telebot
from telebot import types

TOKEN = os.getenv("TOKEN", "").strip()
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "").strip()
if not TOKEN or not ADMIN_CHAT_ID:
    raise RuntimeError("Set TOKEN and ADMIN_CHAT_ID in Render")
ADMIN_CHAT_ID = int(ADMIN_CHAT_ID)
ADMIN_LINK = "https://t.me/beautyspace_admin"
bot = telebot.TeleBot(TOKEN, parse_mode="HTML", threaded=False)
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent
with (BASE_DIR / "eg_catalog.json").open(encoding="utf-8") as catalog_file:
    PRODUCT_DETAILS = json.load(catalog_file)
with (BASE_DIR / "salon_catalog.json").open(encoding="utf-8") as catalog_file:
    SALON_DETAILS = json.load(catalog_file)
PRODUCT_DETAILS.update(SALON_DETAILS)

HOME = "🏠 Головне меню"
BACK = "⬅️ Назад"
SALON = "Салон"
SHOP = "Магазин косметики"
CART = "🧺 Кошик"
CONTACT = "Зв'язатися з адміністратором"
PRICE = "Прайс салону"
BOOK = "📝 Консультація / запис"
HOME_CARE = "Домашній догляд"
COLOR_BOX = "Color Box"
PRO_CARE = "Для салонів краси"
CLEAR = "Очистити кошик"
CHECKOUT = "✅ Оформити замовлення"
CANCEL = "Скасувати"
REMOVE = "Прибрати товар"

# Only a confirmed price is shown. The administrator confirms all other
# prices, volumes and stock before taking payment.
PRODUCTS = {
    "Шампунь EG №1 Очищення, 400 мл": 1000,
    "Шампунь EG №2 Баланс, 400 мл": 1000,
    "Зволожувальний бальзам EG, 250 мл": 1000,
    "Кондиціонер EG, 400 мл": 1000,
    "Відновлювальний спрей EG, 250 мл": 1000,
    "Термозахист EG, 100 мл": 900,
    "Маска EG Step 1 — ліпідна, 250 мл": 1200,
    "Маска EG Step 2 — амінокератинова, 250 мл": 1200,
    "Маска EG Step 3 — протеїнова, 250 мл": 1200,
    "Тонуюча маска by Gromova, 250 мл": 1000,
    "Олія EG для освітлення": 2100,
    "Color Box для прикореневої зони, 60 мл": 1800,
    "Color Box для довжини": 3500,
}
for name, details in SALON_DETAILS.items():
    PRODUCTS[name] = details.get("price", PRODUCTS.get(name))
CATEGORIES = {
    HOME_CARE: [name for name in PRODUCTS if not name.startswith("Color Box") and name not in SALON_DETAILS],
    COLOR_BOX: [name for name in PRODUCTS if name.startswith("Color Box")],
    PRO_CARE: list(SALON_DETAILS),
}
product_category = {name: category for category, names in CATEGORIES.items() for name in names}
SERVICES = {
    "GRAY FUSION — робота із сивиною":
        "Робота за природним малюнком сивини без фарбування натурального кореня. "
        "Складна техніка зазвичай займає 10–12 годин; вартість орієнтовно 15 000–20 000 грн. "
        "Остаточний план і вартість майстер визначає після консультації. "
        "Після роботи потрібен контроль кольору не рідше ніж раз на 4,5 місяця.",
    "Камуфляж сивини та тонування":
        "Первинний камуфляж із тонуванням: орієнтовно 5 000 грн, "
        "реконструкція окремо близько 2 000 грн. Повторна процедура: "
        "орієнтовно 2 500–3 000 грн плюс реконструкція близько 2 000 грн. "
        "Точна ціна залежить від довжини та стану волосся.",
    "Реконструкція волосся":
        "Салонний догляд підбирається після діагностики волосся. "
        "Орієнтир вартості разом із камуфляжем: від 2 000 грн; "
        "самостійну процедуру і ціну уточнює адміністратор.",
    "Вихід із темного кольору":
        "Після косметичного темного кольору зазвичай потрібні два етапи: "
        "смивка й реконструкція, потім освітлення та техніка. "
        "План, безпечний результат і вартість визначаються на консультації.",
    "Стрижка та інші послуги":
        "Напишіть адміністратору або залиште заявку: підберемо майстра "
        "і повідомимо актуальну вартість.",
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
                     reply_markup=keyboard([[SALON, SHOP], [CART], [CONTACT]]))

def salon(chat_id):
    section[chat_id] = "salon"
    bot.send_message(chat_id, "Салон на Оболоні, Київ, Прирічна 27Е. Що вас цікавить?",
                     reply_markup=keyboard([[PRICE], [BOOK], [CONTACT], [HOME]]))

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
    fields = ORDER_FIELDS if flow["kind"] == "order" else BOOK_FIELDS
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

@bot.message_handler(commands=["start", "help"])
def start(message):
    if message.chat.type != "private":
        return
    flows.pop(message.chat.id, None)
    menu(message.chat.id)

@bot.message_handler(commands=["id"])
def show_id(message):
    bot.send_message(message.chat.id, f"chat_id: <code>{message.chat.id}</code>")

@bot.message_handler(content_types=["text"])
def dispatch(message):
    if message.chat.type != "private":
        return
    chat_id = message.chat.id
    text = message.text.strip()
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
        elif current == "price":
            salon(chat_id)
        else:
            menu(chat_id)
        return
    if text == "Повторити надсилання" and chat_id in flows:
        flow = flows[chat_id]
        fields = ORDER_FIELDS if flow["kind"] == "order" else BOOK_FIELDS
        if flow["step"] == len(fields):
            complete(chat_id, message, flow)
        else:
            bot.send_message(chat_id, fields[flow["step"]][1])
        return
    if chat_id in flows:
        collect(chat_id, message, text)
        return
    if text == SALON:
        salon(chat_id)
    elif text == PRICE:
        prices(chat_id)
    elif text in SERVICES:
        bot.send_message(chat_id, html.escape(SERVICES[text]),
                         reply_markup=keyboard([[BOOK], [BACK, HOME]]))
    elif text == BOOK:
        begin_flow(chat_id, "booking")
    elif text == SHOP:
        shop(chat_id)
    elif text in CATEGORIES:
        catalog(chat_id, text)
    elif text in PRODUCTS:
        product(chat_id, text)
    elif text == "Додати в кошик" and selection.get(chat_id):
        carts.setdefault(chat_id, []).append(selection[chat_id])
        bot.send_message(chat_id, "Додано. " + cart_text(chat_id),
                         reply_markup=keyboard([[CART], [BACK, HOME]]))
    elif text == CART:
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
        contact(chat_id)
    else:
        bot.send_message(chat_id, "Оберіть кнопку в меню або напишіть адміністратору.",
                         reply_markup=keyboard([[HOME, CONTACT]]))

if __name__ == "__main__":
    while True:
        try:
            bot.remove_webhook()
            log.info("Bot polling started")
            bot.infinity_polling(timeout=30, long_polling_timeout=30, skip_pending=True)
        except Exception:
            log.exception("Polling failed; restarting in 5 seconds")
            time.sleep(5)
