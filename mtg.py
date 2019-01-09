import requests
import json
import psycopg2
import telebot
import os
class MtgFinder:
	c_types=['c','t','o','m','cmc','mana','is','r','e','in','f',
	'color','type','oracle','edition','format','cmc']
	map={'color':'c',
		'type':'t',
		'oracle':'o',
		'edition':'e',
		'format':'f',
		'cmc':'cmc'}
	change=0
	params={'q':''}
	mtg_records=[]
	
	def __init__(self,bot):
		self.bot=bot
	def clear_param(self,chat_id):
		self.params={'q':''}
		markup = telebot.types.ReplyKeyboardRemove(selective=False)
		self.bot.send_message(chat_id, 'Complete',reply_markup = markup)
	
	def add_param(self,param):
		self.params['q']=self.params['q']+self.get_map(param)+':'
	
	def add_params_value(self,value):
		if ' ' in value:
			value='"'+value+'"'
		self.params['q']=self.params['q']+value+' '
	
	def get_map(self,type):
		return self.map[type.lower()]


#Смена режима работы бота
	def change_to_mtg(self,message):
		if self.change != 1:
			self.change = 1
			self.bot.send_message(message.chat.id, 'Включен MTG режим')

	def change_to_advance(self,message):
		msg=self.bot.send_message(message.chat.id, 'Включен MTG Advance режим')
		markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
		itembtn1 = telebot.types.KeyboardButton('Color')
		itembtn2 = telebot.types.KeyboardButton('Type')
		itembtn3 = telebot.types.KeyboardButton('Oracle')
		itembtn4 = telebot.types.KeyboardButton('Edition')
		itembtn5 = telebot.types.KeyboardButton('Format')
		itembtn6 = telebot.types.KeyboardButton('Cmc')
		itembtn6 = telebot.types.KeyboardButton('Finish')
		markup.row(itembtn1, itembtn2,itembtn3)
		markup.row(itembtn4, itembtn5)
		markup.row(itembtn6)
		msg=self.bot.send_message(message.chat.id, 'Выберите фильтр',reply_markup = markup)
		self.bot.register_next_step_handler(msg, self.advance_search)
		
	def change_to_normal(self,message):
		if self.change != 0:
			self.change = 0
			self.bot.send_message(message.chat.id, 'Включен обычный режим')
		
#Проверка на валидность типа
	def validate_type(self,type):
		if type.lower() in self.c_types:
			return True
		else:
			return False
		
#Бот в обычном режиме?	
	def is_normal(self,message):
		return self.change == 0
	
#Бот в MTG режиме?
	def is_mtg(self,message):
		return self.change == 1
	
	def is_mtg_advanced(self,message):
		return self.change == 2
	
#Поиск карты по названию


	def advance_search(self,message):
		if message.text.lower() == 'finish':
			self.card_search_advance(message)
			self.clear_param(message.chat.id)
		else:
			if self.validate_type(message.text) is False:
				msg=self.bot.send_message(message.chat.id, 'Неправильный фильтр')
				self.bot.register_next_step_handler(msg, self.advance_search)
			else:
				self.add_param(message.text)
				msg=self.bot.send_message(message.chat.id, 'Введите значение')
				self.bot.register_next_step_handler(msg, self.cardd_search)

	def cardd_search(self,message):
		self.add_params_value(message.text)
		msg=self.bot.send_message(message.chat.id, 'Продолжим?')
		self.bot.register_next_step_handler(msg, self.advance_search)

	def card_search_advance(self,message):
		self.params['include_multilingual']=True
		url='https://api.scryfall.com/cards/search'
		rsp=requests.get(url=url,params=self.params)
		#self.bot.send_message(message.chat.id,rsp.url)
		rsp=json.loads(rsp.text)
		rez=''
		try:
			card_list=rsp['data']
			for card in card_list:
				try:
					rez+=card['name']+'\t'+card['usd']+'\n'
				except KeyError:
					pass
			self.bot.send_message(message.chat.id,rez)
		except KeyError:
			self.bot.send_message(message.chat.id,'Неправильный запрос')
	
	def card_search(self,message):
		try:
			conn=psycopg2.connect(user = "ptefqjhdtyrgya",
						  password = "d06f1f573d5919c73c80143e18ea9883e1760412d455a00b901b67f5ac40fcd8",
						  host = "ec2-54-247-161-208.eu-west-1.compute.amazonaws.com",
						  port = "5432",
						  database="de7cvsaumikoei")
			cursor = conn.cursor()
			select_Query = """select string_agg(c1.printed_name,'\\'),c1.color,c3.image,string_agg(c1.name,'\\')
			from mtg.card_export c1, mtg.card_export c3
			where c1.id in
			(select c2.id
			from mtg.card_export c2
			where (lower(c2.printed_name) like lower(%(like)s) escape '='
			or
			lower(c2.name) like lower(%(like)s) escape '=')
			)
			and c1.name = c3.name
			and c3.lang = 'en'
			group by c1.id,c1.color,c3.image
			order by c1.color"""
			cursor.execute(select_Query, dict(like= '%'+message.text+'%'))
			self.mtg_records = cursor.fetchall()
			if cursor.rowcount == 0:
				self.bot.send_message(message.chat.id,'Не найдено')
			elif cursor.rowcount < 3:
				for row in self.mtg_records:
					self.bot.send_photo(message.chat.id,bytes(row[2]))
			else:
				self.print_card_list(message)
		finally:
			if (conn):
				cursor.close()
				conn.close()
#        url='https://api.scryfall.com/cards/named'
#        params={'fuzzy':message.text}
#        try:
#            rsp=requests.get(url=url,params=params)
#            rsp=json.loads(rsp.text)
#            img_url=rsp['image_uris']['normal']
#            img_rsp=requests.get(url=img_url)
#            img=img_rsp.content
#            bot.send_photo(message.chat.id,img)
#            try:
#                bot.send_message(message.chat.id,rsp['usd'])
#            except KeyError:
#                pass
#        except KeyError:
#            url='https://api.scryfall.com/cards/autocomplete'
#            params = {'q': message.text}
#            rsp = requests.get(url=url, params=params)
#            rsp=json.loads(rsp.text)
#            data=rsp['data']
#            if data==[]:
#                rez='Совпадений не найдено'
#            else:
#                rez='\n'.join(data)
#            bot.send_message(message.chat.id,rez)
	def print_card_list(self,message):
		keyboard = telebot.types.InlineKeyboardMarkup()
		callback_button = telebot.types.InlineKeyboardButton(text="Показать следующую страницу", callback_data="next")
		keyboard.add(callback_button)
		rez=''
		flag = False
		for i in range (len(self.mtg_records)):
			if self.mtg_records[0][0] != self.mtg_records[0][3]:
				rez += self.mtg_records[0][0] + '[' + self.mtg_records[0][3] + ']' + ' | ' + self.mtg_records[0][1] + '\n'
			else:
				rez += self.mtg_records[0][0] + ' | ' + self.mtg_records[0][1] + '\n'
			self.mtg_records.pop(0)
			if i == 19:
				flag = True
				break
		if flag is False:
			self.bot.send_message(message.chat.id, rez)
		else:
			self.bot.send_message(message.chat.id, rez, reply_markup = keyboard)
	
	
	def callback_inline(self,call):
		keyboard = telebot.types.InlineKeyboardMarkup()
		callback_button = telebot.types.InlineKeyboardButton(text="Показать следующую страницу", callback_data="next")
		keyboard.add(callback_button)
		if call.message:
			if call.data == "next":
				rez=''
				for i in range (len(self.mtg_records)):
					rez += self.mtg_records[0][0] + ' | ' + self.mtg_records[0][1] + '\n'
					self.mtg_records.pop(0)
					if i == 19:
						break
				if len(self.mtg_records) == 0:
					self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=rez)
				else:
					self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=rez, reply_markup = keyboard)