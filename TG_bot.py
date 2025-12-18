import telebot
from telebot import types
bot = telebot.TeleBot('token')
@bot.message_handler(commands=['start'])
def start(message):

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Start")
    markup.add(btn1)
    bot.send_message(message.from_user.id, "......", reply_markup=markup)
