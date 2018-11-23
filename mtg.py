import requests
import json
import telebot
c_types=['c','t','o','m','cmc','mana','is','r','e','in','f']
change=0
def validate_type(type):
    if type in c_types:
        return True
    else:
        return False
		
def is_normal(message):
    global change
    return change == 0
	
def is_mtg(message):
    global change
    return change == 1
	
def card_search(message,bot):
    if '=' in message.text:
        list_arg=message.text.split(' ')
        params={'q':''}
        rez=''
        for arg in list_arg:
            one_arg=arg.split('=')
            if validate_type(one_arg[0]) is False:
                bot.send_message(message.chat.id,'Неправильный аргумент')
                return
            params['q']=params['q']+':'.join(one_arg)+' '
        url='https://api.scryfall.com/cards/search'
        rsp=requests.get(url=url,params=params)
        rsp=json.loads(rsp.text)
        try:
            card_list=rsp['data']
            for card in card_list:
                rez+=card['name']+'\n'
            bot.send_message(message.chat.id,rez)
        except KeyError:
            bot.send_message(message.chat.id,'Неправильный запрос')
    else:
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