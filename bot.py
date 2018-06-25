# -*- coding: utf-8 -*-
import config
import telebot
from telebot import apihelper

def generate_keyboard(answers):
    """
    Создаем кастомную клавиатуру для выбора ответа
    :param answers: Правильный ответ
    :return: Объект кастомной клавиатуры
    """
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    
    for item in answers:
        markup.add(item)
    return markup

apihelper.proxy = {'https':config.socks5}

bot = telebot.TeleBot(config.token)
from telebot import types
@bot.message_handler(content_types=["text"])
def repeat_all_messages(message): # Название функции не играет никакой роли, в принципе
    markup = generate_keyboard(['1','2'])
    bot.send_message(message.chat.id, '?', reply_markup=markup)
    
#В диалоговом окне инженер вводит команду "Create purchase requisition"
@bot.message_handler(commands=['create'])
def handle_start_help(message):
    bot.send_message(message.chat.id, 'In the beginning you should describe your needs')  
if __name__ == '__main__':
    bot.polling(none_stop=True)