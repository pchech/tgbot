import telebot
import io
from utils import validate_stop,prepare_stop
from PIL import Image, ImageDraw
import random

class Filter():
	def __init__(self,bot):
		self.bot=bot
	

	def choose_filter(self,message):
		markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard = True,resize_keyboard=True)
		itembtn1 = telebot.types.KeyboardButton('Черно-белое')
		itembtn2 = telebot.types.KeyboardButton('Сепия')
		itembtn3 = telebot.types.KeyboardButton('Негатив')
		itembtn4 = telebot.types.KeyboardButton('Изменить яркость')
		itembtn5 = telebot.types.KeyboardButton('Добавить шум')
		itembtn6 = telebot.types.KeyboardButton('Остановить')
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
		if fil == 'Сепия':
			msg=self.bot.send_message(message.chat.id,'Укажите глубину', reply_markup=markup_cancel)
			self.bot.register_next_step_handler(msg, self.add_parameters)
		elif fil in ('Изменить яркость','Добавить шум'):
			msg=self.bot.send_message(message.chat.id,'Укажите параметр', reply_markup=markup_cancel)
			self.bot.register_next_step_handler(msg, self.add_parameters)
		elif fil in ('Черно-белое','Негатив'):
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
			if fil == 'Добавить шум':
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
				if fil in ('Изменить яркость','Добавить шум','Сепия'):	
					img=self.filter_choice(image_file,parameters)
				else:
					img=self.filter_choice(image_file,None)
				imgByteArr = io.BytesIO()
				img.save(imgByteArr,format = 'PNG')
				imgByteArr = imgByteArr.getvalue()
				self.bot.send_photo(message.chat.id, imgByteArr,reply_markup = markup)

	def filter_choice(self,image_file,parameters):
		if fil == 'Черно-белое':
			img=self.black_white_filter(image_file)
		elif fil == 'Сепия':
			img=self.sepia(image_file,parameters)
		elif fil == 'Негатив':
			img=self.negative(image_file)
		elif fil == 'Изменить яркость':
			img=self.brightnessChange(image_file,parameters)
		elif fil == 'Добавить шум':
			img=self.add_noise(image_file,parameters)
		return img
		
	######ФИЛЬТРЫ
	def	black_white_filter(self,dir):
								image	=	Image.open(dir)	#Открываем	изображениеH.
								draw	=	ImageDraw.Draw(image)	#Создаем	инструмент	для	рисования.
								width	=	image.size[0]	#Определяем	ширину.
								height	=	image.size[1]	#Определяем	высоту.
								pix	=	image.load()	#Выгружаем	значения	пикселей.
								factor	=	1
								for	i	in	range(width):
												for	j	in	range(height):
																a	=	pix[i,	j][0]
																b	=	pix[i,	j][1]
																c	=	pix[i,	j][2]
																S	=	a	+	b	+	c
																if	(S	>	(((255	+	factor)	//	2)	*	3)):
																				a,	b,	c	=	255,	255,	255
																else:
																				a,	b,	c	=	0,	0,	0
																draw.point((i,	j),	(a,	b,	c))
								return	image
				def	sepia(self,dir,parameters):
								image	=	Image.open(dir)		#	Открываем	изображениеH.
								draw	=	ImageDraw.Draw(image)	#Создаем	инструмент	для	рисования.
								width	=	image.size[0]	#Определяем	ширину.
								height	=	image.size[1]	#Определяем	высоту.
								pix	=	image.load()	#Выгружаем	значения	пикселей.
								depth	=	parameters
								for	i	in	range(width):
												for	j	in	range(height):
																a	=	pix[i,	j][0]
																b	=	pix[i,	j][1]
																c	=	pix[i,	j][2]
																S	=	(a	+	b	+	c)	//	3
																a	=	S	+	depth	*	2
																b	=	S	+	depth
																c	=	S
																if	(a	>	255):
																				a	=	255
																if	(b	>	255):
																				b	=	255
																if	(c	>	255):
																				c	=	255
																draw.point((i,	j),	(a,	b,	c))
								return	image

				def	negative(self,dir):
								image	=	Image.open(dir)		#	Открываем	изображениеH.
								draw	=	ImageDraw.Draw(image)	#Создаем	инструмент	для	рисования.
								width	=	image.size[0]	#Определяем	ширину.
								height	=	image.size[1]	#Определяем	высоту.
								pix	=	image.load()	#Выгружаем	значения	пикселей.
								for	i	in	range(width):
												for	j	in	range(height):
																a	=	pix[i,	j][0]
																b	=	pix[i,	j][1]
																c	=	pix[i,	j][2]
																draw.point((i,	j),	(255	-	a,	255	-	b,	255	-	c))
								return	image

				def	brightnessChange(self,dir,parameters):
								image	=	Image.open(dir)		#	Открываем	изображениеH.
								draw	=	ImageDraw.Draw(image)	#Создаем	инструмент	для	рисования.
								width	=	image.size[0]	#Определяем	ширину.
								height	=	image.size[1]	#Определяем	высоту.
								pix	=	image.load()	#Выгружаем	значения	пикселей.
								factor	=	parameters
								for	i	in	range(width):
												for	j	in	range(height):
																a	=	pix[i,	j][0]	+	factor
																b	=	pix[i,	j][1]	+	factor
																c	=	pix[i,	j][2]	+	factor
																if	(a	<	0):
																				a	=	0
																if	(b	<	0):
																				b	=	0
																if	(c	<	0):
																				c	=	0
																if	(a	>	255):
																				a	=	255
																if	(b	>	255):
																				b	=	255
																if	(c	>	255):
																				c	=	255
																draw.point((i,	j),	(a,	b,	c))
								return	image

				def	add_noise(self,dir,parameters):
								image	=	Image.open(dir)		#	Открываем	изображениеH.
								draw	=	ImageDraw.Draw(image)	#Создаем	инструмент	для	рисования.
								width	=	image.size[0]	#Определяем	ширину.
								height	=	image.size[1]	#Определяем	высоту.
								pix	=	image.load()	#Выгружаем	значения	пикселей.
								factor	=	parameters
								for	i	in	range(width):
												for	j	in	range(height):
																rand	=	random.randint(-factor,	factor)
																a	=	pix[i,	j][0]	+	rand
																b	=	pix[i,	j][1]	+	rand
																c	=	pix[i,	j][2]	+	rand
																if	(a	<	0):
																				a	=	0
																if	(b	<	0):
																				b	=	0
																if	(c	<	0):
																				c	=	0
																if	(a	>	255):
																				a	=	255
																if	(b	>	255):
																				b	=	255
																if	(c	>	255):
																				c	=	255
																draw.point((i,	j),	(a,	b,	c))
								return	image