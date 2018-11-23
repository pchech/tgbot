import telebot
from modules import Colorizer
import os
from utils import validate_stop,prepare_stop
colorizer=Colorizer(os.environ.get('ALGO_KEY'),'MyCollection')

class Coloriz:
	def __init__(self,bot):
		self.bot=bot

	def ask_for_image(self,message):
		markup_cancel = prepare_stop(message)
		msg=self.bot.send_message(message.chat.id,'Отправьте изображение',reply_markup = markup_cancel)
		self.bot.register_next_step_handler(msg, self.colorize)

	def colorize(self,message):
		if validate_stop(message,bot):
			return
		if message.photo is None:
			msg=self.bot.send_message(message.chat.id,'Не изображение')
			self.bot.register_next_step_handler(msg, self.colorize)
			return
		else:
			markup = telebot.types.ReplyKeyboardRemove(selective=False)
			photo = message.photo[-1].file_id
			file = self.bot.get_file(photo)
			if file.file_size > 10485760:
				msg=self.bot.send_message(message.chat.id,'Файл не должен быть больше 10 МБ')
				self.bot.register_next_step_handler(msg, colorize)
			else:
				downloaded_file = self.bot.download_file(file.file_path)
				img=colorizer.action(downloaded_file)
				self.bot.send_photo(message.chat.id, img, reply_markup=markup)