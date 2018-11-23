import telebot
import io
from utils import prepare_stop, validate_stop
from modules import change_color

class Cluster:
	def __init__(self,bot):
		self.bot=bot
		
	def ask_for_image_clust(self,message):
		markup_cancel = prepare_stop(message)
		msg=self.bot.send_message(message.chat.id,'Выберите число цветов (не более 10)',reply_markup = markup_cancel)
		self.bot.register_next_step_handler(msg, self.ask_for_color)

	def ask_for_color(self,message):
		if validate_stop(message,self.bot):
			return
		try:
			global parameters
			parameters=int(message.text)
			if parameters > 10:
				msg=self.bot.send_message(message.chat.id,'Не больше 10 цветов')
				self.bot.register_next_step_handler(msg, self.ask_for_color)
				return
			msg=self.bot.send_message(message.chat.id,'Отправьте изображение')
			self.bot.register_next_step_handler(msg, self.clusterization)
		except ValueError:
			msg=self.bot.send_message(message.chat.id,'Параметр должен быть числовым')
			self.bot.register_next_step_handler(msg, self.ask_for_color)
			return

		
	def clusterization(self,message):
		if validate_stop(message,self.bot):
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
				self.bot.register_next_step_handler(msg, self.clusterization)
			else:
				downloaded_file = self.bot.download_file(file.file_path)
				image_file = io.BytesIO(downloaded_file)
				img=change_color(image_file,parameters)
				self.bot.send_photo(message.chat.id, img, reply_markup=markup)