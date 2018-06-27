# -*- coding: utf-8 -*-
import config
import telebot
from telebot import apihelper
from telebot import types
import shelve
from SQLighter import SQLighter
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
@bot.message_handler(commands=['start'])
def handle_start_help(message):
    state = get_state_for_user(message.chat.id)
    if not state:
        bot.send_message(message.chat.id, 'In the beginning you should describe your needs')
        set_user_state(message.chat.id,0)
        db_worker = SQLighter(config.database_name)
        q = db_worker.select_polls()
        if not q:
            bot.send_message(message.chat.id, 'Опросов нет!')
            print('нет опросов!')
            return None
        list_items = []
        for item in q:
            list_items.append(item[1])
        print('доступны опросы')
        
        print(list_items)
        markup = generate_keyboard(list_items)
        bot.send_message(message.chat.id, 'Выберите опрос:', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, 'не начинай заново!')
        
        

@bot.message_handler(commands=['stop'])
def handle_delete_help(message):
    state = get_state_for_user(message.chat.id)
    if state:
        finish_user_quest(message.chat.id)
        bot.send_message(message.chat.id, 'finished')
     

     

@bot.message_handler(content_types=["text"])
def repeat_all_messages(message): # Название функции не играет никакой роли, в принципе

    state = get_state_for_user(message.chat.id)
    db_worker = SQLighter(config.database_name)
        
    print(message.chat.id)
    print(state)
    if state == 0:
        p = db_worker.select_poll(message.text)
        if not p:
            bot.send_message(message.chat.id, 'не узнаю опроса')
            print('не узнаю опроса')
            return None
        print('выбран опрос №{}'.format(p[0]))
        q = db_worker.start_poll(p[0])
        
        set_user_state(message.chat.id,q[0])
        repeat_all_messages(message)#@todo чтоб в цикл не ушло оставить только ИД чата
    elif not state:
        bot.send_message(message.chat.id, 'Чтобы начать, выберите команду /start')
    else:
        #keyboard_hider = types.ReplyKeyboardRemove()
        q = db_worker.select_state(state)
        if not q:
            bot.send_message(message.chat.id, 'Хватит!')
            return None
        a = db_worker.check_answer(q[2],message.text)
        if a:
            print('выбран ответ ')
            n = db_worker.select_next_state(q[1],q[3]) #@todo переделать в следующий без нумирации
            if n:
                set_user_state(message.chat.id,n[0])
                repeat_all_messages(message)#@todo чтоб в цикл не ушло оставить только ИД чата
            else:
                bot.send_message(message.chat.id, 'опрос окончен')
                print('опрос окончен')
                finish_user_quest(message.chat.id)
            
        else:
            #bot.send_message(message.chat.id, 'не понимаю')
            print('не понимаю ответ')
            a = db_worker.select_options(q[2])
            quest = db_worker.select_single(q[2])
            #bot.send_message(message.chat.id, '{},{}'.format(state,q[1]))
            list_items = []
            for item in a:
                list_items.append(item[2])
            print(list_items)
            markup = generate_keyboard(list_items)
            bot.send_message(message.chat.id, '{},{}'.format(state,quest[1]), reply_markup=markup)
            
        
    

if __name__ == '__main__':
    bot.polling(none_stop=True)