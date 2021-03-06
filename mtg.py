import requests
import json
import psycopg2
import telebot
import os
from bs4 import BeautifulSoup
class MtgFinder:
	session = {}
	rez = {}
	c_types=['c','t','o','m','cmc','mana','is','r','e','in','f',
	'color','type','oracle','edition','format','cmc','rarity']
	map={'color':'c1.color',
		'type':'c1.printed_type',
		'oracle':'o',
		'edition':'s.set_id',
		'format':'f',
		'cmc':'cmc',
		'rarity':'c1.rarity'}
	change=1
	set_list = []
	select = """select string_agg(nat_name,'||' order by nat_name) card_name,color,set_id,usd
from
(select string_agg(c1.printed_name,' // ' order by c1.name) nat_name,c1.color,c3.image,string_agg(c1.name,' // ' order by c1.name) en_name, s.set_id,cp.usd
			from mtg.card_export c1, mtg.card_export c3,mtg.card_price cp, mtg.set s
			where 1=1
			and c1.name = c3.name
			and c3.lang = 'en'
			and c1.set_id = c3.set_id
			and c3.id=cp.id
			and cast(c1.set_id as integer) = s.id
			and c1.set_id = (select max(c4.set_id)
			from mtg.card_export c4
			where c4.name = c1.name)
			{}
			group by c1.id,c1.color,c3.image, s.set_id,cp.usd
			order by c1.color,cp.usd) v
	group by en_name, color, set_id,usd
	order by color, card_name"""
	params={'q':''}
	mtg_records = {}
	temp_flag = {}
	type_flag = {}
	def __init__(self,bot):
		self.bot=bot
		try:
			conn=psycopg2.connect(user = os.environ.get('DB_USER'),
						  password = os.environ.get('DB_PASS'),
						  host = os.environ.get('DB_HOST'),
						  port = os.environ.get('DB_PORT'),
						  database=os.environ.get('DB_NAME'))
			cursor = conn.cursor()
			select_Query = """select set_name from mtg.set"""
			cursor.execute(select_Query)
			self.set_list = [set[0] for set in cursor.fetchall()]
			print(self.set_list)
		finally:
			if (conn):
				cursor.close()
				conn.close()
		
	def clear_param(self,chat_id):
		#self.params={'q':''}
		self.temp_flag[chat_id] = 0
		self.session[chat_id] = self.select
		self.bot.send_message(chat_id, 'Complete',reply_markup = self.prepare_cancel_keyboard())
	
	def add_param(self,chat_id,param):
		self.session[chat_id] = self.session[chat_id].format('and lower('+self.get_map(param)+') like {}')
		#self.select = self.select.format('and lower('+self.get_map(param)+') like {}')
		#self.params['q']=self.params['q']+self.get_map(param)+':'
	
	def add_params_value(self,chat_id,value):
		#if ' ' in value:
		#	value='"'+value+'"'
		self.session[chat_id] = self.session[chat_id].format("'%"+value.lower()+"%' {}")
		#self.select = self.select.format("'%"+value.lower()+"%' {}")
		#self.params['q']=self.params['q']+value+' '
	
	def get_map(self,type):
		return self.map[type.lower()]
	
	def prepare_keyboard(self):
		markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
		itembtn1 = telebot.types.KeyboardButton('Color')
		itembtn2 = telebot.types.KeyboardButton('Type')
		#itembtn3 = telebot.types.KeyboardButton('Oracle')
		itembtn4 = telebot.types.KeyboardButton('Edition')
		itembtn5 = telebot.types.KeyboardButton('Rarity')
		#itembtn6 = telebot.types.KeyboardButton('Cmc')
		itembtn6 = telebot.types.KeyboardButton('Finish')
		markup.row(itembtn1, itembtn2)
		markup.row(itembtn4,itembtn5)
		markup.row(itembtn6)
		return markup
	
	def prepare_color_keyboard(self):
		markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
		itembtn1 = telebot.types.KeyboardButton('R')
		itembtn2 = telebot.types.KeyboardButton('G')
		itembtn3 = telebot.types.KeyboardButton('U')
		itembtn4 = telebot.types.KeyboardButton('B')
		itembtn5 = telebot.types.KeyboardButton('W')
		itembtn6 = telebot.types.KeyboardButton('N')
		markup.row(itembtn1, itembtn2, itembtn3)
		markup.row(itembtn4, itembtn5, itembtn6)
		return markup
		
	def prepare_rarity_keyboard(self):
		markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
		itembtn1 = telebot.types.KeyboardButton('Common')
		itembtn2 = telebot.types.KeyboardButton('Uncommon')
		itembtn3 = telebot.types.KeyboardButton('Rare')
		itembtn4 = telebot.types.KeyboardButton('Mythic')
		markup.row(itembtn1, itembtn2)
		markup.row(itembtn3, itembtn4)
		return markup
	
	def prepare_cancel_keyboard(self):
		markup = telebot.types.ReplyKeyboardRemove(selective=False)
		return markup

#Смена режима работы бота
	def change_to_mtg(self,message):
		if self.change != 1:
			self.change = 1
			self.bot.send_message(message.chat.id, 'Включен MTG режим')
			self.type_flag[message.chat.id] = False

	def change_to_advance(self,message):
		self.session[message.chat.id] = self.select
		self.temp_flag[message.chat.id] = 0
		msg=self.bot.send_message(message.chat.id, 'Включен MTG Advance режим')
		msg=self.bot.send_message(message.chat.id, 'Выберите фильтр',reply_markup = self.prepare_keyboard())
		self.bot.register_next_step_handler(msg, self.advance_search)
		
#	def change_to_normal(self,message):
		
		#if self.change != 0:
		#	self.change = 0
		#	self.bot.send_message(message.chat.id, 'Включен обычный режим')
		
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
			if self.temp_flag[message.chat.id]!=0:
				self.session[message.chat.id] = self.session[message.chat.id].format('')
				self.card_search_advance(message)
				self.clear_param(message.chat.id)
			else:
				msg=self.bot.send_message(message.chat.id, 'Запрос без фильтров временно запрещен',reply_markup = self.prepare_keyboard())
				self.bot.register_next_step_handler(msg, self.advance_search)
		else:
			if self.validate_type(message.text) is False:
				msg=self.bot.send_message(message.chat.id, 'Неправильный фильтр', reply_markup = self.prepare_keyboard())
				self.bot.register_next_step_handler(msg, self.advance_search)
			else:
				self.temp_flag[message.chat.id]=1
				self.add_param(message.chat.id,message.text)
				if message.text.lower() == 'color':
					msg=self.bot.send_message(message.chat.id, 'Введите значение', reply_markup = self.prepare_color_keyboard())
				elif message.text.lower() == 'rarity':
					msg=self.bot.send_message(message.chat.id, 'Введите значение', reply_markup = self.prepare_rarity_keyboard())
				else:
					msg=self.bot.send_message(message.chat.id, 'Введите значение', reply_markup = self.prepare_cancel_keyboard())
				self.bot.register_next_step_handler(msg, self.cardd_search)

	def cardd_search(self,message):
		self.add_params_value(message.chat.id,message.text)
		msg=self.bot.send_message(message.chat.id, 'Продолжим?', reply_markup = self.prepare_keyboard())
		self.bot.register_next_step_handler(msg, self.advance_search)

	def card_search_advance(self,message):
		self.type_flag[message.chat.id] = True
		try:
			conn=psycopg2.connect(user = os.environ.get('DB_USER'),
						  password = os.environ.get('DB_PASS'),
						  host = os.environ.get('DB_HOST'),
						  port = os.environ.get('DB_PORT'),
						  database=os.environ.get('DB_NAME'))
			cursor = conn.cursor()
			cursor.execute(self.session[message.chat.id])
			self.mtg_records[message.chat.id] = cursor.fetchall()
			if cursor.rowcount == 0:
				self.bot.send_message(message.chat.id,'Не найдено')
			else:
				self.print_card_list(message)
		finally:
			if (conn):
				cursor.close()
				conn.close()
				
	#	self.params['include_multilingual']=True
	#	url='https://api.scryfall.com/cards/search'
	#	rsp=requests.get(url=url,params=self.params)
		#self.bot.send_message(message.chat.id,rsp.url)
	#	rsp=json.loads(rsp.text)
	#	rez=''
	#	try:
	#		card_list=rsp['data']
	#		for card in card_list:
	#			try:
	#				rez+=card['name']+'\t'+card['usd']+'\n'
	#			except KeyError:
	#				pass
	#		self.bot.send_message(message.chat.id,rez)
	#	except KeyError:
	#		self.bot.send_message(message.chat.id,'Неправильный запрос')
	
	def card_search(self,message):
		self.type_flag[message.chat.id] = False
		try:
			conn=psycopg2.connect(user = os.environ.get('DB_USER'),
						  password = os.environ.get('DB_PASS'),
						  host = os.environ.get('DB_HOST'),
						  port = os.environ.get('DB_PORT'),
						  database=os.environ.get('DB_NAME'))
			cursor = conn.cursor()
			select_Query = """select distinct string_agg(c1.printed_name,' // '),c1.color,(select image
 from mtg.card_export c4
 where c4.name = c3.name
 and c4.set_id = c3.set_id 
 and c4.lang = 'en'
 limit 1) image_en, string_agg(c1.name,' // '), s.set_id,cp.usd
			from mtg.card_export c1, mtg.set s, mtg.card_export c3,mtg.card_price cp
			where c1.id in
			(select c2.id
			from mtg.card_export c2
			where replace(lower(c2.printed_name),',','') like lower(%(like)s) escape '='
			)
			and c1.name = c3.name
			and c3.lang = 'en'
			and c1.set_id = c3.set_id
			and c3.id=cp.id
			and s.id = cast(c1.set_id as integer)
			and s.set_num = (select max(s1.set_num)
							from mtg.card_export ce, mtg.set s1
							where cast(ce.set_id as integer)=s1.id
							and ce.name = c1.name
							)
			group by c1.id,c1.color, s.set_id,image_en,cp.usd
			order by c1.color,cp.usd desc"""
			cursor.execute(select_Query, dict(like= '%'+message.text.replace(',','')+'%'))
			self.mtg_records[message.chat.id] = cursor.fetchall()
			if cursor.rowcount == 0:
				self.bot.send_message(message.chat.id,'Не найдено')
			elif cursor.rowcount < 3:
				for row in self.mtg_records[message.chat.id]:
					self.bot.send_photo(message.chat.id,bytes(row[2]))
					#self.bot.send_message(message.chat.id, 'TCG Price:' + str(row[5]))
					loading = self.bot.send_message(message.chat.id, 'Price is loading ... ')
					self.bot.edit_message_text(chat_id=loading.chat.id, message_id=loading.message_id, text=self.scg_search(row[3]))
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
	def scg_search(self,card_name):
		url = "http://www.starcitygames.com/results?name={}&numpage=100".format(card_name)
		rsp = requests.get(url)
		bs = BeautifulSoup(rsp.content,'html.parser')
		rs = bs.findAll(attrs={'class':['deckdbbody_row','deckdbbody2_row']})
		if len(rs) != 0:
			result = 'Edition | Price \n'
			for row in rs:
				try:
					edition = row.findNext(class_='search_results_2').a.string
					if edition not in self.set_list:
						continue
					price = row.findNext(class_='search_results_9').string
					result += edition + ' | ' + price + '\n'
				except AttributeError:
					pass
		else:
			result = 'Not Found'
		return result

	def print_card_list(self,message):
		keyboard = telebot.types.InlineKeyboardMarkup()
		callback_button = telebot.types.InlineKeyboardButton(text="Показать следующую страницу", callback_data="next")
		keyboard.add(callback_button)
		self.rez[message.chat.id]=' '
		for i in range (len(self.mtg_records[message.chat.id])):
			if self.type_flag[message.chat.id] is False:
				if self.mtg_records[message.chat.id][0][0] != self.mtg_records[message.chat.id][0][3]:
					self.rez[message.chat.id] += self.mtg_records[message.chat.id][0][0] + '[' + self.mtg_records[message.chat.id][0][3] + ']' + '\n' + self.mtg_records[message.chat.id][0][1] + ' | ' + self.mtg_records[message.chat.id][0][4] + ' | ' + str(self.mtg_records[message.chat.id][0][5])+ '\n----------\n' 
				else:
					self.rez[message.chat.id] += self.mtg_records[message.chat.id][0][0] + ' | ' + self.mtg_records[message.chat.id][0][1] + '\n' + self.mtg_records[message.chat.id][0][4] + ' | ' + str(self.mtg_records[message.chat.id][0][5])+ '\n----------\n'
			else:
				self.rez[message.chat.id] += self.mtg_records[message.chat.id][0][0] + '\n' + self.mtg_records[message.chat.id][0][1] + ' | ' + self.mtg_records[message.chat.id][0][2] + ' | ' + str(self.mtg_records[message.chat.id][0][3])+ '\n----------\n'
			self.mtg_records[message.chat.id].pop(0)
			if i == 10:
				break
		if len(self.mtg_records[message.chat.id]) == 0:
			self.type_flag[message.chat.id] = False
			self.bot.send_message(message.chat.id, self.rez[message.chat.id])
		else:
			self.bot.send_message(message.chat.id, self.rez[message.chat.id], reply_markup = keyboard)
	
	
	def callback_inline(self,call):
		keyboard = telebot.types.InlineKeyboardMarkup()
		callback_button = telebot.types.InlineKeyboardButton(text="Показать следующую страницу", callback_data="next")
		keyboard.add(callback_button)
		if call.message:
			if call.data == "next":
				self.rez[call.message.chat.id]=''
				for i in range (len(self.mtg_records[call.message.chat.id])):
					if self.type_flag[call.message.chat.id] is False:
						if self.mtg_records[call.message.chat.id][0][0] != self.mtg_records[call.message.chat.id][0][3]:
							self.rez[call.message.chat.id] += self.mtg_records[call.message.chat.id][0][0] + '[' + self.mtg_records[call.message.chat.id][0][3] + ']' + '\n' + self.mtg_records[call.message.chat.id][0][1] + ' | ' + self.mtg_records[call.message.chat.id][0][4] + ' | ' + str(self.mtg_records[call.message.chat.id][0][5])+ '\n----------\n' 
						else:
							self.rez[call.message.chat.id] += self.mtg_records[call.message.chat.id][0][0] + ' | ' + self.mtg_records[call.message.chat.id][0][1] + '\n' + self.mtg_records[call.message.chat.id][0][4] + ' | ' + str(self.mtg_records[call.message.chat.id][0][5])+ '\n----------\n'
					else:
						self.rez[call.message.chat.id] += self.mtg_records[call.message.chat.id][0][0] + '\n' + self.mtg_records[call.message.chat.id][0][1] + ' | ' + self.mtg_records[call.message.chat.id][0][2] + ' | ' + str(self.mtg_records[call.message.chat.id][0][3])+ '\n----------\n'
					self.mtg_records[call.message.chat.id].pop(0)
					if i == 10:
						break
				if len(self.mtg_records[call.message.chat.id]) == 0:
					self.type_flag[call.message.chat.id] = False
					self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=self.rez[call.message.chat.id])
				else:
					self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=self.rez[call.message.chat.id], reply_markup = keyboard)