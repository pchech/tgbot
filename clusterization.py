import telebot
import io
import numpy as np
from utils import prepare_stop, validate_stop
from skimage.io import imread	
from skimage import img_as_float
from sklearn.cluster import KMeans
import scipy.misc

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
				img=self.change_color(image_file,parameters)
				self.bot.send_photo(message.chat.id, img, reply_markup=markup)
	
	def	change_color(self,img,n_color):
		image=imread(img)
		image=img_as_float(image)
		X	=	image.reshape(image.shape[0]	*	image.shape[1],	3)
		clt=KMeans(random_state=241,init='k-means++',n_clusters=n_color)
		clt.fit(X)
		res=clt.predict(X)
		centre=clt.cluster_centers_
		new_X=[]
		for	i	in	range(X.shape[0]):
			new_X.append(centre[res[i]])
		new_image	=	np.array(new_X).reshape(image.shape[0],	image.shape[1],	3)
		n_img	=	scipy.misc.toimage(new_image)
		imgByteArr	=	io.BytesIO()
		n_img.save(imgByteArr,format	=	'JPEG')
		imgByteArr	=	imgByteArr.getvalue()
		return	imgByteArr