﻿# -*- coding: utf-8 -*-
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
            
            
def set_user_history(chat_id, poll_id, state):
    """
    Записываем юзера в игроки и запоминаем, что он должен ответить.
    :param chat_id: id юзера
    :param estimated_answer: правильный ответ (из БД)
    """
    with shelve.open(shelve_name) as storage:
        storage[str(chat_id) +'-'+ str(poll_id)] = state
def finish_user_history(chat_id, poll_id):
    """
    Заканчиваем игру текущего пользователя и удаляем правильный ответ из хранилища
    :param chat_id: id юзера
    """
    with shelve.open(shelve_name) as storage:
        del storage[str(chat_id) +'-'+ str(poll_id)]
def get_history_for_user(chat_id, poll_id):
    """
    Получаем правильный ответ для текущего юзера.
    В случае, если человек просто ввёл какие-то символы, не начав игру, возвращаем None
    :param chat_id: id юзера
    :return: (str) Правильный ответ / None
    """
    with shelve.open(shelve_name) as storage:
        try:
            state = storage[str(chat_id) +'-'+ str(poll_id)]
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
            print('выбран ответ ') #пользователь указал ответ на вопрос и мы его опознали 
            h  = get_history_for_user(message.chat.id, q[1])
            h = (h+'-'+str(a[0])) if h else str(a[0])
            set_user_history(message.chat.id, q[1],h)
            print(h)
            n = db_worker.select_next_state(q[1],q[3]) #@todo переделать в следующий без нумирации
            if n:
                set_user_state(message.chat.id,n[0])
                repeat_all_messages(message)#@todo чтоб в цикл не ушло оставить только ИД чата
            else:
                
                print('опрос окончен')
                finish_user_quest(message.chat.id)
                finish_user_history(message.chat.id, q[1])
                print(h)
                rez1 = {
                '1-3-11':'Please request free samples or technical specification in supplier. Would like to learn more about technical specification or free sample? See more information on the link below',
                '1-3-12':'Please use the technical specification to describe your needs. Would like to learn more about technical specification? See more information on the link below. Download the free template of technical specification here',
                '1-4-11':'Please request free samples or technical specification in supplier. Would like to learn more about technical specification or free sample? See more information on the link below',
                '1-4-12':'Please use the technical specification to describe your needs. Would like to learn more about technical specification? See more information on the link below. Download the free template of technical specification here',
                '1-5-11':'Please use the e-catalogs of supplers to describe your needs. Would like to learn more about e-catalogs? See more information on the link below.',
                '1-5-12':'Please use the e-catalogs of supplers to describe your needs. Would like to learn more about e-catalogs? See more information on the link below.',
                '1-6-11':'Please use the the functional specification to describe your needs. Would like to learn more about functional specification? See more information on the link below. Download the free template of functional specification here',
                '1-6-12':'Please use the the functional specification to describe your needs. Would like to learn more about functional specification? See more information on the link below. Download the free template of functional specification here',
                '1-7-11':'Please use e-catalogs of suppliers or request free samples in supplier when possible. Would like to learn more about  free samples or e-catalogs? See more information on the link below',
                '1-7-12':'Please use the e-catalogs of supplers to describe your needs. Would like to learn more about e-catalogs? See more information on the link below.',
                '1-8-11':'Please use e-catalogs of suppliers or request free samples in supplier when possible. Would like to learn more about  free samples or e-catalogs? See more information on the link below',
                '1-8-12':'Please use the e-catalogs of supplers to describe your needs. Would like to learn more about e-catalogs? See more information on the link below.',
                '1-9-11':'Please use e-catalogs of suppliers or request free samples in supplier when possible. Would like to learn more about  free samples or e-catalogs? See more information on the link below',
                '1-9-12':'Please use the e-catalogs of supplers to describe your needs. Would like to learn more about e-catalogs? See more information on the link below.',
                '1-10-11':'Please use the the functional specification to describe your needs. Would like to learn more about functional specification? See more information on the link below. Download the free template of functional specification here',
                '1-10-12':'Please use the the functional specification to describe your needs. Would like to learn more about functional specification? See more information on the link below. Download the free template of functional specification here',
                '2-3-11':'Please request free samples or technical specification in supplier. Would like to learn more about technical specification or free sample? See more information on the link below',
                '2-3-12':'Please use the technical specification to describe your needs. Would like to learn more about technical specification? See more information on the link below. Download the free template of technical specification here',
                '2-4-11':'Please request free samples or technical specification in supplier. Would like to learn more about technical specification or free sample? See more information on the link below',
                '2-4-12':'Please use the technical specification to describe your needs. Would like to learn more about technical specification? See more information on the link below. Download the free template of technical specification here',
                '2-5-11':'Please use the e-catalogs of supplers to describe your needs. Would like to learn more about e-catalogs? See more information on the link below.',
                '2-5-12':'Please use the e-catalogs of supplers to describe your needs. Would like to learn more about e-catalogs? See more information on the link below.',
                '2-6-11':'Please use the the drawinngs to describe your needs. Would like to learn more about functional specification? See more information on the link below. Download the free template of functional specification here',
                '2-6-12':'Please use the the drawings to describe your needs. Would like to learn more about functional specification? See more information on the link below. Download the free template of functional specification here',
                '2-7-11':'Please use e-catalogs of suppliers or request free samples in supplier when possible. Would like to learn more about  free samples or e-catalogs? See more information on the link below',
                '2-7-12':'Please use the e-catalogs of supplers to describe your needs. Would like to learn more about e-catalogs? See more information on the link below.',
                '2-8-11':'Please use e-catalogs of suppliers or request free samples in supplier when possible. Would like to learn more about  free samples or e-catalogs? See more information on the link below',
                '2-8-12':'Please use the e-catalogs of supplers to describe your needs. Would like to learn more about e-catalogs? See more information on the link below.',
                '2-9-11':'Please use e-catalogs of suppliers or request free samples in supplier when possible. Would like to learn more about  free samples or e-catalogs? See more information on the link below',
                '2-9-12':'Please use the e-catalogs of supplers to describe your needs. Would like to learn more about e-catalogs? See more information on the link below.',
                '2-10-11':'Please use the the functional specification to describe your needs. Would like to learn more about functional specification? See more information on the link below. Download the free template of functional specification here',
                '2-10-12':'Please use the the functional specification to describe your needs. Would like to learn more about functional specification? See more information on the link below. Download the free template of functional specification here',
                }
                rez2 = {
                '13-15':'Please use procurement outsourcing or joint purchases or volume consolidation as procurement strategy. Would you like to learn more about procurement outsourcing, joint purchases, volume consolidation? See more information on link below',
                '13-16':'Please use request for information (RFI), request for quotation (RFQ), request for proposal (RFP) as procurement strategy. Also procurement outsourcing is applicable because of low volume. Would you like to learn more about request of information (RFI), request of quotation (RFQ), request of proposal (RFP)? See more information on link below. Download free template of RFQ, RFP, RFI here',
                '13-17':'Please use request for bids (RFB) as procurement strategy.  Also procurement outsourcing is applicable because of low volume. Would you like to learn more about request for bids (RFB)? See more information on link below. Download free template of RFB here',
                '14-15':'Please use value analysis and value engineering or standardisation or risk-management as procurement strategy. Would you like to learn more about value analysis and value engineering, standardisation, risk-management? See more information on link below',
                '14-16':'Please use strategic alliances, joint spend management, savings sharing as a strategy. Would you like to learn more about strategic alliances, joint spend management, savings sharing? See more information on link below',
                '14-17':'Please use global sourcing or reverse auction (tender) together with regression analysis and target pricing here as a strategy. Would you like to learn more about global sourcing, reverse auction (tender), regression analysis and target pricing ? See more information on link below',
                }
                
                rez3 = {
                '13-15':'"You should use ""Lose-Lose"" negotiation strategy.  This strategy involves the evading from participation in negotiations when you have a weak position. Would you like to learn more about ""Lose-Lose"" negotiation strategy? See more information on link below"',
                '13-16':'"You should use ""Win-Lose"" negotiation strategy.  The opponent is considered as a rival. The strategy is used when the most important outcome is result. Negotiator is focusing on rivalry, often ready to use all available tools to get the desired agreement, including the methods of manipulation. Would you like to learn more about ""Win-Lose"" negotiation strategy? See more information on link below"',
                '13-17':'"You should use ""Win-Lose"" negotiation strategy.  The opponent is considered as a rival. The strategy is used when the most important outcome is result. Negotiator is focusing on rivalry, often ready to use all available tools to get the desired agreement, including the methods of manipulation. Would you like to learn more about ""Win-Lose"" negotiation strategy? See more information on link below"',
                '14-15':'"You should use ""Lose-Win"" negotiation strategy.  The implementation of adaptation strategies is appropriate, when the most important outcome for you are relations with you partner and result is not the most important. Would you like to learn more about ""Lose-Win"" negotiation strategy? See more information on link below"',
                '14-16':'"You should use ""Win-Win"" negotiation strategy.  Cooperation strategy is moved for the mutual win in the negotiation process by expanding the pie based on the understanding of the parties\' interests. Would you like to learn more about ""Win-Win"" negotiation strategy? See more information on link below"',
                '14-17':'"You should use ""Win-Lose"" negotiation strategy.  The opponent is considered as a rival. The strategy is used when the most important outcome is result. Negotiator is focusing on rivalry, often ready to use all available tools to get the desired agreement, including the methods of manipulation. Would you like to learn more about ""Win-Lose"" negotiation strategy? See more information on link below"',
                }
                if q[1] == 1:
                    print(rez1[h])
                    bot.send_message(message.chat.id, rez1[h])
                    
                elif q[1] == 2:
                    print(rez2[h])
                    bot.send_message(message.chat.id, rez2[h])
                elif q[1] == 3:
                    print(rez3[h])
                    bot.send_message(message.chat.id, rez3[h])
                bot.send_message(message.chat.id, 'опрос окончен')
            
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