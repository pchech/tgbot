import telebot
import cherrypy
from flask import Flask, request
import requests
import json
import os

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
@bot.message_handler(commands=['change'])
def change_mod(message):
    global change
    if change == 0:
        change = 1
        bot.send_message(message.chat.id, 'Включен MTG режим')
    else:
        change = 0
        bot.send_message(message.chat.id, 'Включен обычный режим')

def is_normal(message):
    global change
    return change == 0
def is_mtg(message):
    global change
    return change == 1

@bot.message_handler(func=is_normal, content_types=["text"])
def repeat_all_messages(message): # Название функции не играет никакой роли, в принципе
    bot.send_message(message.chat.id, message.text[::-1])

@bot.message_handler(func=is_mtg, content_types=["text"])
def card_search(message):
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