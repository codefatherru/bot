# -*- coding: utf-8 -*-
import sqlite3

class SQLighter:

    def __init__(self, database):
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()
    def select_user(self, rownum):
        """ Получаем одну строку с номером rownum """
        with self.connection:
            return self.cursor.execute('SELECT * FROM user WHERE id = ?', (rownum,)).fetchone()
    def update_user(self, chat_id,role_id,id,is_bot,first_name,last_name = None,username = None,language_code = None):
        with self.connection:
            return self.cursor.execute('INSERT OR REPLACE INTO user(chat_id,role_id,id,is_bot,first_name,last_name,username,language_code) VALUES(?,?,?,?,?,?,?,?)', (chat_id,role_id,id,is_bot,first_name,last_name ,username,language_code))    
    def select_all(self):
        """ Получаем все строки """
        with self.connection:
            return self.cursor.execute('SELECT * FROM question').fetchall()

    def select_single(self, rownum):
        """ Получаем одну строку с номером rownum """
        with self.connection:
            return self.cursor.execute('SELECT * FROM question WHERE id = ?', (rownum,)).fetchone()    

    def select_state(self, rownum):
        """ Получаем одну строку с номером rownum """
        with self.connection:
            return self.cursor.execute('SELECT * FROM p2q WHERE id = ?', (rownum,)).fetchone()
    def select_next_state(self, poll,rownum):
        """ Получаем одну строку с номером rownum """
        with self.connection:
            return self.cursor.execute('select * from p2q where poll_id=? and sequence >? order by sequence limit 1', (poll,rownum)).fetchone()

    def select_options(self, rownum):
        """ Получаем одну строку с номером rownum """
        with self.connection:
            return self.cursor.execute('SELECT * FROM option WHERE question_id = ?', (rownum,)).fetchall()
    def check_answer(self, question, title):
        """ Получаем одну строку с номером rownum """
        #print(('select * from option where question_id = ? and title = ?', (question, title)))
        with self.connection:
            return self.cursor.execute('select * from option where question_id = ? and title = ?', (question, title)).fetchone()
    def select_poll(self, rownum):
        """ Получаем одну строку с номером rownum """
        with self.connection:
            return self.cursor.execute('SELECT * FROM poll WHERE title = ?', (rownum,)).fetchone()
    def start_poll(self, rownum):
        """ Получаем одну строку с номером rownum """
        with self.connection:
            return self.cursor.execute('select * from p2q where poll_id=? order by sequence limit 1', (rownum,)).fetchone()
    def select_polls(self):
        """ Получаем одну строку с номером rownum """
        with self.connection:
            return self.cursor.execute('SELECT * FROM poll ').fetchall()

    def count_rows(self):
        """ Считаем количество строк """
        with self.connection:
            result = self.cursor.execute('SELECT * FROM question').fetchall()
            return len(result)

    def close(self):
        """ Закрываем текущее соединение с БД """
        self.connection.close()