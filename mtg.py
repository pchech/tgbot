import requests
import json
import psycopg2
import telebot
import os
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
token = os.environ.get('TOKEN')
bot = telebot.TeleBot(token)
def clear_param(chat_id,bot):
	global params
	params={'q':''}
	markup = telebot.types.ReplyKeyboardRemove(selective=False)
	bot.send_message(chat_id, 'Complete',reply_markup = markup)
	
def add_param(param):
	global params
	params['q']=params['q']+get_map(param)+':'
	
def add_params_value(value):
	global params
	if ' ' in value:
		value='"'+value+'"'
	params['q']=params['q']+value+' '
	
def get_map(type):
	return map[type.lower()]


#Смена режима работы бота
def change_to_mtg(message,bot):
	global change
	if change != 1:
		change = 1
		bot.send_message(message.chat.id, 'Включен MTG режим')

def change_to_advance(message,bot):
	msg=bot.send_message(message.chat.id, 'Включен MTG Advance режим')
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
	msg=bot.send_message(message.chat.id, 'Выберите фильтр',reply_markup = markup)
	bot.register_next_step_handler(msg, advance_search,{'bot' : bot})
		
def change_to_normal(message, bot):
	global change
	if change != 0:
		change = 0
		bot.send_message(message.chat.id, 'Включен обычный режим')
		
#Проверка на валидность типа
def validate_type(type):
    if type.lower() in c_types:
        return True
    else:
        return False
		
#Бот в обычном режиме?	
def is_normal(message):
    global change
    return change == 0
	
#Бот в MTG режиме?
def is_mtg(message):
    global change
    return change == 1
	
def is_mtg_advanced(message):
	global change
	return change == 2
	
#Поиск карты по названию


def advance_search(message,bot):
	bot=bot['bot']
	if message.text.lower() == 'finish':
		card_search_advance(message,bot)
		clear_param(message.chat.id, bot)
	else:
		if validate_type(message.text) is False:
			msg=bot.send_message(message.chat.id, 'Неправильный фильтр')
			bot.register_next_step_handler(msg, advance_search,{'bot' : bot})
		else:
			add_param(message.text)
			msg=bot.send_message(message.chat.id, 'Введите значение')
			bot.register_next_step_handler(msg, cardd_search, {'bot' : bot})

def cardd_search(message,bot):
	bot=bot['bot']
	add_params_value(message.text)
	msg=bot.send_message(message.chat.id, 'Продолжим?')
	bot.register_next_step_handler(msg, advance_search,{'bot' : bot})

def card_search_advance(message,bot):
	global params
	params['include_multilingual']=True
	url='https://api.scryfall.com/cards/search'
	rsp=requests.get(url=url,params=params)
	bot.send_message(message.chat.id,rsp.url)
	rsp=json.loads(rsp.text)
	rez=''
	try:
		card_list=rsp['data']
		for card in card_list:
			try:
				rez+=card['name']+'\t'+card['usd']+'\n'
			except KeyError:
				pass
		bot.send_message(message.chat.id,rez)
	except KeyError:
		bot.send_message(message.chat.id,'Неправильный запрос')
	
def card_search(message,bot):
	try:
		conn=psycopg2.connect(user = "ptefqjhdtyrgya",
                      password = "d06f1f573d5919c73c80143e18ea9883e1760412d455a00b901b67f5ac40fcd8",
                      host = "ec2-54-247-161-208.eu-west-1.compute.amazonaws.com",
                      port = "5432",
                      database="de7cvsaumikoei")
		cursor = conn.cursor()
		select_Query = "select printed_name,color,image from mtg.card_export where lower(printed_name) like lower(%(like)s) escape '=' order by color"
		cursor.execute(select_Query, dict(like= '%'+message.text+'%'))
		global mtg_records
		mtg_records = cursor.fetchall()
		if cursor.rowcount == 0:
			bot.send_message(message.chat.id,'Не найдено')
		elif cursor.rowcount < 3:
			for row in mtg_records:
				bot.send_photo(message.chat.id,bytes(row[2]))
		else:
			print_card_list(bot,message)
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
def print_card_list(bot,message):
	global mtg_records
	keyboard = telebot.types.InlineKeyboardMarkup()
	callback_button = telebot.types.InlineKeyboardButton(text="Показать следующую страницу", callback_data="next")
	keyboard.add(callback_button)
	rez=''
	for i in range (len(mtg_records)):
		rez += mtg_records[0][0] + ' | ' + mtg_records[0][1] + '\n'
		mtg_records.pop(0)
		if i == 19:
			break
	bot.send_message(message.chat.id, rez, reply_markup = keyboard)
	
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
	bot.send_message(call.message.chat.id, 'Callback')
	if call.message:
		if call.data == "next":
			global mtg_records
			rez=''
			for i in range (len(mtg_records)):
				rez += mtg_records[0][0] + ' | ' + mtg_records[0][1] + '\n'
				mtg_records.pop(0)
				if i == 19:
					break
			bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=rez)