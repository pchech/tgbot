import telebot
from flask import Flask, request
import os
from mtg import card_search,is_normal, is_mtg, change_to_normal,change_to_advance,change_to_mtg
from utils import validate_stop
from filters import Filter
from colorization import Colorizer
from clusterization import Cluster
token = os.environ.get('TOKEN')
server = Flask(__name__)
#WEBHOOK_HOST = 'cryptic-citadel-53949.herokuapp.com'
WEBHOOK_HOST = 'testmtgbot.herokuapp.com'
WEBHOOK_PORT = 8443#8443  # 443, 80, 88 или 8443 (порт должен быть открыт!)
WEBHOOK_LISTEN = '0.0.0.0'  # На некоторых серверах придется указывать такой же IP, что и выше

WEBHOOK_SSL_CERT = './webhook_cert.pem'  # Путь к сертификату
WEBHOOK_SSL_PRIV = './webhook_pkey.pem'  # Путь к приватному ключу

WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % (token)

bot = telebot.TeleBot(token)

welcome_message="""Бот обладает следующими возможностями:
/filter - Применить один из 5 фильтров (черно-белое фото, сепия, негатив, наложение шума, изменение яркости)
/colorize - Окраска черно-белых изображений
/change_color - Уменьшение количества цветов
/start – Показать список доступных команд"""

filt=Filter(bot)
coloriz=Colorizer(bot,os.environ.get('ALGO_KEY'),'MyCollection')
cluster=Cluster(bot)
@bot.message_handler(commands=['normalmode'])
def change_mod_process(message):
    change_to_normal(message,bot)
	
@bot.message_handler(commands=['mtgmode'])
def change_mod_process(message):
    change_to_mtg(message,bot)
	
@bot.message_handler(commands=['mtgadvancemode'])
def change_mod_process(message):
    change_to_advance(message,bot)

@bot.message_handler(commands=['filter'])
def apply_filter(message):
	filt.choose_filter(message)

@bot.message_handler(commands=['colorize'])
def colorize_photo(message):
	coloriz.ask_for_image(message)
			
@bot.message_handler(commands=['change_color'])
def ask_for_image_clust(message):
	cluster.ask_for_image_clust(message)
	
		
@bot.message_handler(func=is_normal, content_types=["text"])
def show_welcome(message):
	if validate_stop(message,bot):
		return
	bot.send_message(message.chat.id, welcome_message)
	
@bot.message_handler(commands=['start'])
def ask_for_image_clust(message):
	if validate_stop(message,bot):
		return
	bot.send_message(message.chat.id, welcome_message)

@bot.message_handler(func=is_mtg, content_types=["text"])
def mtg_search(message):
    card_search(message,bot)
	
@server.route('/' + token, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200


@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_HOST+WEBHOOK_URL_PATH)
    return "!", 200


if __name__ == "__main__":
    server.run(host=WEBHOOK_LISTEN, port=int(os.environ.get('PORT', 5000)))