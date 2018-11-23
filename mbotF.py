import telebot
import cherrypy
from flask import Flask, request
import requests
import json
import os
import io
from modules import Colorizer, change_color
from mtg import card_search,is_normal, is_mtg, change_mod
from filters import Filt
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
colorizer=Colorizer(os.environ.get('ALGO_KEY'),'MyCollection')
welcome_message="""Бот обладает следующими возможностями:
/filter - Применить один из 5 фильтров (черно-белое фото, сепия, негатив, наложение шума, изменение яркости)
/colorize - Окраска черно-белых изображений"""

filt=Filt(bot)
@bot.message_handler(commands=['change'])
def change_mod_process(message):
    change_mod(message,bot)



	
@bot.message_handler(commands=['filter'])
def apply_filter(message):
	filt.choose_filter(message)

@bot.message_handler(commands=['colorize'])
def ask_for_image(message):
	markup_cancel = prepare_stop(message)
	msg=bot.send_message(message.chat.id,'Отправьте изображение',reply_markup = markup_cancel)
	bot.register_next_step_handler(msg, colorize)

def colorize(message):
	if validate_stop(message):
		return
	if message.photo is None:
		msg=bot.send_message(message.chat.id,'Не изображение')
		bot.register_next_step_handler(msg, colorize)
		return
	else:
		markup = telebot.types.ReplyKeyboardRemove(selective=False)
		photo = message.photo[-1].file_id
		file = bot.get_file(photo)
		if file.file_size > 10485760:
			msg=bot.send_message(message.chat.id,'Файл не должен быть больше 10 МБ')
			bot.register_next_step_handler(msg, colorize)
		else:
			downloaded_file = bot.download_file(file.file_path)
			img=colorizer.action(downloaded_file)
			bot.send_photo(message.chat.id, img, reply_markup=markup)
			
@bot.message_handler(commands=['change_color'])
def ask_for_image_clust(message):
	markup_cancel = prepare_stop(message)
	msg=bot.send_message(message.chat.id,'Выберите число цветов (не более 10)',reply_markup = markup_cancel)
	bot.register_next_step_handler(msg, ask_for_color)

def ask_for_color(message):
	if validate_stop(message):
		return
	try:
		global parameters
		parameters=int(message.text)
		if parameters > 10:
			msg=bot.send_message(message.chat.id,'Не больше 10 цветов')
			bot.register_next_step_handler(msg, ask_for_color)
			return
		msg=bot.send_message(message.chat.id,'Отправьте изображение')
		bot.register_next_step_handler(msg, clusterization)
	except ValueError:
		msg=bot.send_message(message.chat.id,'Параметр должен быть числовым')
		bot.register_next_step_handler(msg, ask_for_color)
		return

	
def clusterization(message):
	if validate_stop(message):
		return
	if message.photo is None:
		msg=bot.send_message(message.chat.id,'Не изображение')
		bot.register_next_step_handler(msg, colorize)
		return
	else:
		markup = telebot.types.ReplyKeyboardRemove(selective=False)
		photo = message.photo[-1].file_id
		file = bot.get_file(photo)
		if file.file_size > 10485760:
			msg=bot.send_message(message.chat.id,'Файл не должен быть больше 10 МБ')
			bot.register_next_step_handler(msg, clusterization)
		else:
			downloaded_file = bot.download_file(file.file_path)
			image_file = io.BytesIO(downloaded_file)
			img=change_color(image_file,parameters)
			bot.send_photo(message.chat.id, img, reply_markup=markup)
	
		
@bot.message_handler(func=is_normal, content_types=["text"])
def show_welcome(message):
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
    bot.set_webhook(url='https://cryptic-citadel-53949.herokuapp.com/' + token)
    return "!", 200


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))