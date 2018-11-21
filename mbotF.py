import telebot
import cherrypy
from flask import Flask, request
import requests
import json
import os
import io
from modules import Filter
token = os.environ.get('TOKEN')
server = Flask(__name__)
WEBHOOK_HOST = 'cryptic-citadel-53949.herokuapp.com'
WEBHOOK_PORT = 8443#8443  # 443, 80, 88 или 8443 (порт должен быть открыт!)
WEBHOOK_LISTEN = '0.0.0.0'  # На некоторых серверах придется указывать такой же IP, что и выше

WEBHOOK_SSL_CERT = './webhook_cert.pem'  # Путь к сертификату
WEBHOOK_SSL_PRIV = './webhook_pkey.pem'  # Путь к приватному ключу

WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % (token)

bot = telebot.TeleBot(token)
change=0
filter = Filter()
@bot.message_handler(commands=['change'])
def change_mod(message):
    global change
    if change == 0:
        change = 1
        bot.send_message(message.chat.id, 'Включен MTG режим')
    else:
        change = 0
        bot.send_message(message.chat.id, 'Включен обычный режим')
c_types=['c','t','o','m','cmc','mana','is','r','e','in','f']
def validate_type(type):
    if type in c_types:
        return True
    else:
        return False
def is_normal(message):
    global change
    return change == 0
def is_mtg(message):
    global change
    return change == 1

	
@bot.message_handler(commands=['filter'])
def choose_filter(message):
	markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard = True)
	itembtn1 = telebot.types.KeyboardButton('bw')
	itembtn2 = telebot.types.KeyboardButton('sepia')
	markup.add(itembtn1, itembtn2)
	msg=bot.send_message(message.chat.id,'Выберите фильтр', reply_markup = markup)
	bot.register_next_step_handler(msg, welcome)
	
def welcome(message):
	markup = types.ReplyKeyboardRemove(selective=False)
	msg=bot.send_message(message.chat.id,'Отправьте изображение',reply_markup = markup)
	bot.register_next_step_handler(msg, make_filter)
	

def make_filter(message):
	photo = message.photo[-1].file_id
	file = bot.get_file(photo)
	downloaded_file = bot.download_file(file.file_path)
	image_file = io.BytesIO(downloaded_file)
	if message.text == 'bw':
		img=filter.black_white_filter(image_file)
	else:
		img=filter.sepia(image_file)
	imgByteArr = io.BytesIO()
	img.save(imgByteArr,format = 'PNG')
	imgByteArr = imgByteArr.getvalue()
	bot.send_photo(message.chat.id, imgByteArr)
	
@bot.message_handler(func=is_normal, content_types=["text"])
def repeat_all_messages(message): # Название функции не играет никакой роли, в принципе
    bot.send_message(message.chat.id, message.text[::-1])

@bot.message_handler(func=is_mtg, content_types=["text"])
def card_search(message):
    if '=' in message.text:
        list_arg=message.text.split(' ')
        params={'q':''}
        rez=''
        for arg in list_arg:
            one_arg=arg.split('=')
            if validate_type(one_arg[0]) is False:
                bot.send_message(message.chat.id,'Неправильный аргумент')
                return
            params['q']=params['q']+':'.join(one_arg)+' '
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
    else:
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
	
@server.route('/' + token, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200


@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://cryptic-citadel-53949.herokuapp.com/' + token)
    return "!", 200


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))