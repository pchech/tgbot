import telebot
import os
from utils import validate_stop,prepare_stop
import Algorithmia

class Colorizer:
	def __init__(self,bot,api_key,collection_name):
		self.bot=bot
		self.client = Algorithmia.client(api_key)
        self.collection_name = collection_name

	def ask_for_image(self,message):
		markup_cancel = prepare_stop(message)
		msg=self.bot.send_message(message.chat.id,'Отправьте изображение',reply_markup = markup_cancel)
		self.bot.register_next_step_handler(msg, self.colorize)

	def colorize(self,message):
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
				self.bot.register_next_step_handler(msg, colorize)
			else:
				downloaded_file = self.bot.download_file(file.file_path)
				img=self.action(downloaded_file)
				self.bot.send_photo(message.chat.id, img, reply_markup=markup)
	def action(self,data):
        #mass = filepath.split("/")
        self.client.file("data://.my/"+self.collection_name+"/testimg.png").put(data)
        input = {
            "image": "data://.my/"+self.collection_name+"/testimg.png"
        }
        algo = self.client.algo('deeplearning/ColorfulImageColorization/1.1.13')
        out = algo.pipe(input).result
        t800Bytes = self.client.file(out['output']).getBytes()
        return t800Bytes