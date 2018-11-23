import telebot
import io
from modules import Filter
from utils import validate_stop,prepare_stop
filter = Filter()
class Filt():
	def __init__(self,bot):
		self.bot=bot
	

	def choose_filter(self,message):
		markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard = True)
		itembtn1 = telebot.types.KeyboardButton('bw')
		itembtn2 = telebot.types.KeyboardButton('sepia')
		itembtn3 = telebot.types.KeyboardButton('negative')
		itembtn4 = telebot.types.KeyboardButton('brightness')
		itembtn5 = telebot.types.KeyboardButton('noise')
		itembtn6 = telebot.types.KeyboardButton('stop')
		markup.row(itembtn1, itembtn2,itembtn3)
		markup.row(itembtn4, itembtn5)
		markup.row(itembtn6)
		msg=self.bot.send_message(message.chat.id,'Выберите фильтр', reply_markup = markup)	
		self.bot.register_next_step_handler(msg, self.welcome)
		
	def welcome(self,message):
		if validate_stop(message,self.bot):
			return
		global fil
		fil=message.text
		markup_cancel = prepare_stop(message)
		if fil == 'sepia':
			msg=self.bot.send_message(message.chat.id,'Укажите глубину', reply_markup=markup_cancel)
			self.bot.register_next_step_handler(msg, self.add_parameters)
		elif fil in ('brightness','noise'):
			msg=self.bot.send_message(message.chat.id,'Укажите параметр', reply_markup=markup_cancel)
			self.bot.register_next_step_handler(msg, self.add_parameters)
		elif fil in ('bw','negative'):
			msg=self.bot.send_message(message.chat.id,'Отправьте изображение', reply_markup=markup_cancel)
			self.bot.register_next_step_handler(msg, self.make_filter)
		else:
			msg=self.bot.send_message(message.chat.id,'Неверный фильтр')
			self.bot.register_next_step_handler(msg, self.welcome)
			return

	def add_parameters(self,message):
		if validate_stop(message,self.bot):
			return
		global parameters
		try:
			parameters=int(message.text)
			if fil == 'noise':
				parameters=abs(parameters)
			msg=self.bot.send_message(message.chat.id,'Отправьте изображение')
			self.bot.register_next_step_handler(msg, self.make_filter)
		except ValueError:
			msg=self.bot.send_message(message.chat.id,'Параметр должен быть числовым')
			self.bot.register_next_step_handler(msg, self.add_parameters)
			return

	def make_filter(self,message):
		if validate_stop(message,self.bot):
			return
		markup = telebot.types.ReplyKeyboardRemove(selective=False)
		if message.photo is None:
			msg=self.bot.send_message(message.chat.id,'Не изображение')
			self.bot.register_next_step_handler(msg, self.make_filter)
			return
		else:
			photo = message.photo[-1].file_id
			file = self.bot.get_file(photo)
			if file.file_size > 10485760:
				msg=self.bot.send_message(message.chat.id,'Файл не должен быть больше 10 МБ')
				self.bot.register_next_step_handler(msg, self.make_filter)
			else:
				downloaded_file = self.bot.download_file(file.file_path)
				image_file = io.BytesIO(downloaded_file)
				if fil in ('brightness','noise','sepia'):	
					img=self.filter_choice(image_file,parameters)
				else:
					img=self.filter_choice(image_file,None)
				imgByteArr = io.BytesIO()
				img.save(imgByteArr,format = 'PNG')
				imgByteArr = imgByteArr.getvalue()
				self.bot.send_photo(message.chat.id, imgByteArr,reply_markup = markup)

	def filter_choice(self,image_file,parameters):
		if fil == 'bw':
			img=filter.black_white_filter(image_file)
		elif fil == 'sepia':
			img=filter.sepia(image_file,parameters)
		elif fil == 'negative':
			img=filter.negative(image_file)
		elif fil == 'brightness':
			img=filter.brightnessChange(image_file,parameters)
		elif fil == 'noise':
			img=filter.add_noise(image_file,parameters)
		return img