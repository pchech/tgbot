import telebot

def prepare_stop(message):
	markup_cancel = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
	cancel = telebot.types.KeyboardButton('stop')
	markup_cancel.row(cancel)		
	return markup_cancel

def validate_stop(message,bot):
	if message.text == 'stop':
		markup = telebot.types.ReplyKeyboardRemove(selective=False)
		bot.send_message(message.chat.id,'Процесс остановлен', reply_markup=markup)
		return True