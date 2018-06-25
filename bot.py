# -*- coding: utf-8 -*-
import config
import telebot
from telebot import apihelper
from telebot import types
import shelve
from config import shelve_name, database_name

def set_user_state(chat_id, state):
    """
    Записываем юзера в игроки и запоминаем, что он должен ответить.
    :param chat_id: id юзера
    :param estimated_answer: правильный ответ (из БД)
    """
    with shelve.open(shelve_name) as storage:
        storage[str(chat_id)] = state
def finish_user_quest(chat_id):
    """
    Заканчиваем игру текущего пользователя и удаляем правильный ответ из хранилища
    :param chat_id: id юзера
    """
    with shelve.open(shelve_name) as storage:
        del storage[str(chat_id)]
def get_state_for_user(chat_id):
    """
    Получаем правильный ответ для текущего юзера.
    В случае, если человек просто ввёл какие-то символы, не начав игру, возвращаем None
    :param chat_id: id юзера
    :return: (str) Правильный ответ / None
    """
    with shelve.open(shelve_name) as storage:
        try:
            state = storage[str(chat_id)]
            return state
        # Если человек не играет, ничего не возвращаем
        except KeyError:
            return None
            
            
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

#В диалоговом окне инженер вводит команду "Create purchase requisition"
@bot.message_handler(commands=['create'])
def handle_start_help(message):
    bot.send_message(message.chat.id, 'In the beginning you should describe your needs')
    set_user_state(message.chat.id,1)    


@bot.message_handler(content_types=["text"])
def repeat_all_messages(message): # Название функции не играет никакой роли, в принципе

    state = get_state_for_user(message.chat.id)
    if not state:
        bot.send_message(message.chat.id, 'Чтобы начать, выберите команду /create')
    else:
        #keyboard_hider = types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, '{},{}'.format(state,message.text))
        markup = generate_keyboard(['1','2'])
        bot.send_message(message.chat.id, '?', reply_markup=markup)
        set_user_state(message.chat.id,state+1)
    

if __name__ == '__main__':
    bot.polling(none_stop=True)