import telebot
import os

TOKEN = os.environ.get("TOKEN")

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "Привет 🌿 Это бот Space of Beauty by Gromova")

bot.infinity_polling()
