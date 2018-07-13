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

@bot.message_handler(commands=['help'])
def handle_delete_help(message):
    bot.send_message(message.chat.id, '/start - начать заново \n /stop - закончть опрос \n /buyer - сменить роль на "Закупщик"  \n /internal - сменить роль на "Внутренний клиент"')
        
@bot.message_handler(commands=['start'])
def handle_start_help(message):
    state = get_state_for_user(message.chat.id)
    user = message.from_user
    print(user)
    if not state:
        bot.send_message(message.chat.id, 'In the beginning you should describe your needs')
        set_user_state(message.chat.id,0)
        db_worker = SQLighter(config.database_name)
        user = message.from_user
        u = db_worker.select_user(user.id)
        if not u:
            handle_me(message) #если не было такого юзера  - заведем 
            u = db_worker.select_user(user.id)
        q = db_worker.select_polls(u[1])
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
     

@bot.message_handler(commands=['buyer', 'internal'])
def handle_me(message):
    user = message.from_user
    print(user)
    print(message.text)
    role = 2 if message.text == '/buyer' else 1
    db_worker = SQLighter(config.database_name)
    db_worker.update_user(message.chat.id, role, user.id,user.is_bot,user.first_name,user.last_name,user.username,user.language_code)
    bot.send_message(message.chat.id, 'welcome {} as a {}'.format(user.first_name,('buyer' if role == 2 else 'internal' )))
    
     

     

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
        bot.send_message(message.chat.id, 'To start please use command /start')
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
                #@todo надо использовать ссылки https://core.telegram.org/bots/api#inlinekeyboardmarkup
                #@todo тут дикий ксотыль вместо пооиска по бд
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
                '13-15':'Please use <strong>procurement outsourcing</strong> or <strong>joint purchases</strong> or <strong>volume consolidation</strong> as procurement strategy. Would you like to learn more about procurement outsourcing, joint purchases, volume consolidation? See more information on links below:<a href="https://mwpartners.bitrix24.ru/~Acz6s" target="_blank" class="external">Procurement outsourcing</a><a href="https://mwpartners.bitrix24.ru/~7Ze9t" target="_blank" class="external">Joint purchases</a><a href="https://mwpartners.bitrix24.ru/~x18gJ" target="_blank" class="external">Volume consolidation</a>',
                '13-16':'Please use <strong>request for information (RFI) or request for proposal (RFP)</strong> as procurement strategy. Also <strong>procurement outsourcing</strong> is applicable because of low volume. Would you like to learn more about request of information (RFI) request of proposal (RFP)? See more information on links below:<a href="https://mwpartners.bitrix24.ru/~kbeyW" target="_blank" class="external">RFI and RFP </a> Download free template on links below: <a href="https://mwpartners.bitrix24.ru/~DBnU4" target="_blank" class="external">RFI-template</a> <a href="https://mwpartners.bitrix24.ru/~fqaIu" target="_blank" class="external">RFP-template</a>',
                '13-17':'Please use <strong>global sourcing</strong> as procurement strategy. Also <strong>procurement outsourcing</strong> is applicable because of low volume. Would you like to learn more about global sourcing? See more information on links below:<a href="https://mwpartners.bitrix24.ru/~Acz6s" target="_blank" class="external">Procurement outsourcing</a> <a href="https://mwpartners.bitrix24.ru/~D7BXF" target="_blank" class="external">Global sourcing</a>',
                '14-15':'Please use <strong>value analysis and value engineering or standardization or risk-management as procurement strategy. </strong>Would you like to learn more about value analysis and value engineering, standardisation, risk-management? See more information on links below: <a href="https://mwpartners.bitrix24.ru/~KRJ1R" target="_blank" class="external">Value analysis and value   engineering </a> <a href="https://mwpartners.bitrix24.ru/~YcW8F" target="_blank" class="external">Standardization</a> <a href="https://mwpartners.bitrix24.ru/~MUxUq" target="_blank" class="external">Risk-management</a>',
                '14-16':'Please use <strong>strategic alliances, collaborative cost reduction, value based sourcing as a strategy</strong>. Would you like to learn more about <strong>strategic alliances, collaborative cost reduction, value based sourcing?</strong> See more information on links below<a href="https://mwpartners.bitrix24.ru/~6O1Ko" target="_blank" class="external">Strategic alliances</a> <a href="https://mwpartners.bitrix24.ru/~qq7H2" target="_blank" class="external">Collaborative   cost reduction 			</a> <a href="https://mwpartners.bitrix24.ru/~BRCT1" target="_blank" class="external">Value-based sourcing </a>',
                '14-17':'Please use<strong> reverse auction (tender) together with regression analysis and target pricing</strong> here as a strategy. Would you like to learn more about<strong> reverse auction (tender), regression analysis and target pricing </strong>? See more information on links below: 		<a href="https://mwpartners.bitrix24.ru/~jXJud" target="_blank" class="external">Reverse auctions</a> 		<a href="https://mwpartners.bitrix24.ru/~SdN9O" target="_blank" class="external">Target pricing</a>',
                }
                
                rez3 = {
                '13-15':'You should use <strong>"Lose-Lose"</strong> negotiation strategy. This strategy involves the evading from participation in negotiations when you have a weak position. Would you like to learn more about effective negotiations? See more information on <a href="https://mwpartners.bitrix24.ru/~5sy0F" target="_blank" class="external">link below</a>',
                '13-16':'You should use <strong>"Win-Lose"</strong> negotiation strategy. The opponent is considered as a rival. The strategy is used when the most important outcome is result. Negotiator is focusing on rivalry, often ready to use all available tools to get the desired agreement, including the methods of manipulation. Would you like to learn more about effective negotiations? See more information on <a href="https://mwpartners.bitrix24.ru/~5sy0F" target="_blank" class="external">link below</a>',
                '13-17':'You should use <strong>"Win-Lose"</strong> negotiation strategy. The opponent is considered as a rival. The strategy is used when the most important outcome is result. Negotiator is focusing on rivalry, often ready to use all available tools to get the desired agreement, including the methods of manipulation. Would you like to learn more about effective negotiations? See more information on <a href="https://mwpartners.bitrix24.ru/~5sy0F" target="_blank" class="external">link below</a>',
                '14-15':'You should use <strong>"Lose-Win"</strong> negotiation strategy. The implementation of adaptation strategies is appropriate, when the most important outcome for you are relations with you partner and result is not the most important. Would you like to learn more about effective negotiations? See more information on <a href="https://mwpartners.bitrix24.ru/~5sy0F" target="_blank" class="external">link below</a>',
                '14-16':'You should use <strong>"Win-Win"</strong> negotiation strategy. Cooperation strategy is moved for the mutual win in the negotiation process by expanding the pie based on the understanding of the parties\' interests. Would you like to learn more about effective negotiations? See more information on <a href="https://mwpartners.bitrix24.ru/~5sy0F" target="_blank" class="external">link below</a>',
                '14-17':'You should use <strong>"Win-Lose"</strong> negotiation strategy. The opponent is considered as a rival. The strategy is used when the most important outcome is result. Negotiator is focusing on rivalry, often ready to use all available tools to get the desired agreement, including the methods of manipulation. Would you like to learn more about effective negotiations? See more information on <a href="https://mwpartners.bitrix24.ru/~5sy0F">link below</a>',
                }
                if q[1] == 1:
                    print(rez1[h])
                    bot.send_message(message.chat.id, rez1[h])
                    
                elif q[1] == 2:
                    print(rez2[h])
                    bot.send_message(message.chat.id, rez2[h], parse_mode='HTML')
                elif q[1] == 3:
                    print(rez3[h])
                    bot.send_message(message.chat.id, rez3[h], parse_mode='HTML')
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
            bot.send_message(message.chat.id, '{}'.format(quest[1]), reply_markup=markup)
            
        
    

if __name__ == '__main__':
    bot.polling(none_stop=True)