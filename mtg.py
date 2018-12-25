import requests
import json
import telebot
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
def clear_param():
	global params
	params={'q':''}
	markup = telebot.types.ReplyKeyboardRemove(selective=False)
	bot.send_message(message.chat.id, 'Complete',reply_markup = markup)
	
def add_param(param):
	global params
	params['q']=params['q']+get_map(param)+':'
	
def add_params_value(value):
	global params
	params['q']=params['q']+value+' '
	
def get_map(type):
	return map['type']


#Смена режима работы бота
def change_to_mtg(message,bot):
	global change
	if change != 1:
		change = 1
		bot.send_message(message.chat.id, 'Включен MTG режим')

def change_to_advance(message,bot):
	msg=bot.send_message(message.chat.id, 'Включен MTG Advance режим')
	markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard = True,resize_keyboard=True)
	itembtn1 = telebot.types.KeyboardButton('Сolor')
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
		clear_param()
	else:
		if validate_type(message.text) is False:
			markup = telebot.types.ReplyKeyboardRemove(selective=False)
			msg=bot.send_message(message.chat.id, 'Неправильный фильтр',reply_markup = markup)
			bot.register_next_step_handler(msg, advance_search,{'bot' : bot})
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
	url='https://api.scryfall.com/cards/search'
	rsp=requests.get(url=url,params=params)
	rsp=json.loads(rsp.text)
	try:
		card_list=rsp['data']
		for card in card_list:
			rez+=card['name']+'\n'
		bot.send_message(message.chat.id,rez)
	except KeyError:
		bot.send_message(message.chat.id,'Неправильный запрос')
	
def card_search(message,bot):
        url='https://api.scryfall.com/cards/named'
        params={'fuzzy':message.text}
        try:
            rsp=requests.get(url=url,params=params)
            rsp=json.loads(rsp.text)
            img_url=rsp['image_uris']['normal']
            img_rsp=requests.get(url=img_url)
            img=img_rsp.content
            bot.send_photo(message.chat.id,img)
        except KeyError:
            url='https://api.scryfall.com/cards/autocomplete'
            params = {'q': message.text}
            rsp = requests.get(url=url, params=params)
            rsp=json.loads(rsp.text)
            data=rsp['data']
            if data==[]:
                rez='Совпадений не найдено'
            else:
                rez='\n'.join(data)
            bot.send_message(message.chat.id,rez)