# -*- coding: utf-8 -*-
import config
import telebot
from telebot import apihelper
from telebot import types
import shelve
from SQLighter import SQLighter
from config import shelve_name, database_name
import time
from urllib.request import urlopen
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import matplotlib.dates as mdates

def getSoup(url):
    """скачивает  указанный url и возвращает объект парсера, в который он загружен"""

    try:
            
        html = urlopen(url)
    except HTTPError as e:
        print(e)
        return None
    try:
        bsObj = BeautifulSoup(html, "html.parser")
        
    except AttributeError as e:
        return None
    return bsObj
            
            
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
    bot.send_message(message.chat.id, '/elets - давление в Елце \n /msk - давление в Москве ')
        
@bot.message_handler(commands=['elets','msk'])
def handle_start_help(message):
    #state = get_state_for_user(message.chat.id)
    user = message.from_user
    print(user)
    print('обработчик старта получил сообщение')
    print(message.text)
    now = datetime.datetime.now()
    if message.text == '/elets':
        url = 'https://www.gismeteo.ru/weather-yelets-4436/2-weeks/'
        title ='Прогноз давления на 2 недели от '+str(now.date())
    elif message.text == '/msk':
        url = 'https://www.gismeteo.ru/weather-moscow-4368/2-weeks/'
        title ='Прогноз давления на 2 недели от '+str(now.date())
    p = getSoup(url)
    pr = p.find('div',{'data-widget-id':"pressure"})
    date_c = list()
    min_c = list()
    max_c = list()
    if pr:
        #print(pr)
        
        days = pr.findAll('div', {'class':"w_date"})
        for day in days:
            date = day.find('span').get_text(strip=True)
            if date.count(' '):
                date = date.split(' ')[0]
            #print(date)
            nday = now.replace(day=int(date))
            #print(now.date())
            date_c.append(nday.date())
    vl = pr.find('div',{'class':'values'})
    if vl:
        #print(vl)
        vals = vl.findAll('div', {'class':'value'})
        for val in vals:
            max = val.find('div',{'class':'maxt'}).find('span').get_text(strip=True)
            min = val.find('div',{'class':'mint'}).find('span').get_text(strip=True)
            #print((min,max))
            min_c.append(int(min))
            max_c.append(int(max))
    data =  {'min': min_c, 'max': max_c, 'date':date_c}
    print(data)
    df = pd.DataFrame.from_dict(data)
    # convert UNIX epoch to datetime
    df.date = pd.to_datetime(df.date)
    # plot ...
    #df.plot(x='date', y='max')
    plt.plot( 'date', 'max', data=df, marker='o', markerfacecolor='blue', color='skyblue', linewidth=2,  label="max")
    plt.plot( 'date', 'min', data=df, marker='o', markerfacecolor='blue', color='skyblue', linewidth=2,  label="min")
    
    plt.xticks(rotation=70)
    
    plt.legend()



    #plt.show()
    file = str(now.date())+'_'+str(message.chat.id) +'.png'
    plt.savefig(file, format='png', dpi=100)
    plt.clf()
    img = open(file, 'rb')
    bot.send_photo(message.chat.id, img, title)
        
    
    
        


     

@bot.message_handler(content_types=["text"])
def repeat_all_messages(message): # Название функции не играет никакой роли, в принципе

    
    markup = generate_keyboard(['/msk','/elets'])
    bot.send_message(message.chat.id, 'для какого города нужен прогноз давления?', reply_markup=markup)
    
        
    

if __name__ == '__main__':
    while True:

        try:

            bot.polling(none_stop=True)

        # ConnectionError and ReadTimeout because of possible timout of the requests library

        # TypeError for moviepy errors

        # maybe there are others, therefore Exception

        except Exception as e:

            print(e)

            time.sleep(15)
 
