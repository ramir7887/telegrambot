
#import initbot
import requests
from telebot import types
import telebot
import json
import socket
import redis
import re
import yaml
from postgres import Postgres
############################################
############################################
#1)Добавить функцию с общей информацией о станке
#2)Разделить тело бота и функции на два файла
#3)Добавить авторизацию (хотя бы файлик или словарь)
#4)Функция оповещения о ошибках (сказать что бы создали ошибку)посмотреть как парсить ее
#5)Красивое отображение сообщений 
#6)Думать уже о базе данных ошибок
############################################
############################################


TOKEN =  "#########################################" #токен бота
#MAIN_URL = f'https://api.telegram.org/bot{TOKEN}'
r = redis.StrictRedis(host='localhost', port=6379, db=0)

def getInfo(machine):
	register = {'Станок 1':['Milling Machine', 'Фрезерный','Лаборатория 3-6'],'Станок 2':['СА-535','Токарный','Лаборатория 11'],'Станок 3':['Стенд АксиОМА','Стенд','Аудитория 349'],'Станок 4':['Стенд АксиОМА','Стенд','Аудитория 3-6'],'Станок 5':['Мини станок','Стенд','Аудитория 355'],'Станок 6':['CAN станок','Фрезерный','Аудитория 355']}
	nameData = ['Название: ', 'Тип: ','Расположение: ']
	getData = register[machine]
	strInfo = ''
	for i,j in zip(nameData,getData):
		strInfo += i+'<i>'+j+'</i>\n'
	strInfo = '<b>'+machine+'</b>\n'+strInfo
	return strInfo #возвращает строку ответа с названием, типом и расположением оборудования

def getAnswer(param, machine):
	####### берет yaml, преобразует в словарь и возвращает словарь
	listParam = {'Моточасы':['mototimes','mototime'],'Канал 1':['chan1_entries', 'chan1'],'ПЛК':['plc_entries','plc']}
	var1 = listParam[param][0]
	var2 = listParam[param][1]
	response = requests.get('https://eio.ksu.ru.com/locales/ru.yml')
	convert = bytes(response.content)
	convert = convert.decode('utf-8')
	convert = yaml.load(convert)
	convert = convert['ru'][var1]  # готовый словарь с названиями
	############работа с редис
	mach = machine
	mach = int(mach[-1])
	if mach >=4:
		mach += 1
	red = str(r.get(str(mach)))
	red = red.replace('=>',':')
	dict1=eval(red)
	dict1 = eval(dict1)#словарь со значениями
	strAnsver = ''
	#соединение значений с названиями
	for key in convert:
		newkey = var1+'.'+key
		try:
			newstr = convert[key]+': <b>'+dict1[var2][newkey]+'</b>\n'
		except:
			continue
		strAnsver += newstr
	strAnsver = '<b>'+flgMachine+':</b> '+param+'\n' + strAnsver
	return strAnsver  #возвращает строку ответа


def AUTORIZ():
	markupAUTORIZ = types.ReplyKeyboardMarkup(resize_keyboard= True)
	AutoBtn = types.KeyboardButton('Aвторизация')
	markupAUTORIZ.add(AutoBtn)
	return markupAUTORIZ
	 
def MAINMENU():
	mainMenu = types.ReplyKeyboardMarkup(row_width= 1, resize_keyboard= True)
	itembtn1 = types.KeyboardButton('Cписок оборудования')
	itembtn2 = types.KeyboardButton('Последние крит.данные')
	itembtn3 = types.KeyboardButton('Выход из уч.записи')
	mainMenu.add(itembtn1, itembtn2, itembtn3)
	return mainMenu

def MARKUPone(machine_count):  #клавиатура со списком станков, нежно передать кол-во станков (int)
	markup1 = types.ReplyKeyboardMarkup(resize_keyboard= True, row_width= 2)
	listbtn = []
	for i in range(machine_count):
		listbtn.append(types.KeyboardButton('Станок {0}'.format(str(i+1))))
	listbtn.append(types.KeyboardButton('Главное меню'))
	for i in range(len(listbtn)):
		markup1.add(listbtn[i])
	#markup1.row_width = 2
	return markup1

def MARKUPtwo():							#что сюда передавать
	markup2 = types.ReplyKeyboardMarkup(resize_keyboard= True)
	itembtn1 = types.KeyboardButton('Моточасы')
	itembtn2 = types.KeyboardButton('Канал 1')
	itembtn3 = types.KeyboardButton('ПЛК')
	itembtn4 = types.KeyboardButton('Назад')
	itembtn5 = types.KeyboardButton('Главное меню')
	markup2.add(itembtn1, itembtn2, itembtn3, itembtn4, itembtn5)
	return markup2 
#####################
#глобальные переменные для хранения состояний
flgAUTO = False
flgMachine = None
flgParam = None
######################
#создание бота
bot = telebot.TeleBot(TOKEN)
def get_updates_json(request):  
    response = requests.get(request + 'getUpdates')
    return response.json()
#получение информации о боте
user = bot.get_me()
print(user)

#обработчики команд
@bot.message_handler(commands = ['start'])
def send_welcome(message):
	bot.reply_to(message, 'Бот предоставляет доступ к информации о работе технологического оборудования. Проходит альфа-тестирование.\nДоступно станков: 4\nПользоваться только клавиатурой и командами')
	print('\n'+ str(message.chat.id)+ str(message.chat.first_name))
	print("\n" + message.text)
	bot.send_message(message.chat.id, "Для авторизации отправьте ЛОГИН:ПАРОЛЬ и нажмите 'Авторизация'", reply_markup= AUTORIZ())

#команда help(пока пустая)
@bot.message_handler(commands = ['help'])
def help_func(message):
	pass

#обработчик текстовых сообщений
#реагирует на команды текстовые
@bot.message_handler(content_types = ['text'])
def id_st(message):
	if 'Aвторизация' in message.text:
		global flgAUTO 
		flgAUTO= True
		bot.send_message(message.chat.id, 'Авторизация пройдена',reply_markup= MAINMENU() )
	elif 'Cписок оборудования' in message.text:
		if flgAUTO == True:
			bot.send_message(message.chat.id,'<b>Список оборудования</b>', reply_markup= MARKUPone(6), parse_mode= 'HTML')
		else:
			bot.send_message(message.chat.id, "Некорректные данные! Попробуйте еще раз!", reply_markup= AUTORIZ())
	elif 'Последние крит.данные' in message.text:
		bot.reply_to(message,'Раздел находится в разработке.')
	elif 'Выход из уч.записи' in message.text:
		bot.send_message(message.chat.id, "Для авторизации отправьте ЛОГИН:ПАРОЛЬ и нажмите", reply_markup= AUTORIZ())

	elif 'Станок' in message.text:
		#должна отправлять еще общую информацию о станке, ее нужно брать из POSTGRESQL базы
		#пока что просто отправляет со списков информацию
		global flgMachine
		flgMachine = message.text
		bot.send_message(message.chat.id, getInfo(message.text),parse_mode= 'HTML',reply_markup= MARKUPtwo())
	elif 'Общ.информация' in message.text:
		name = 'Стенд Аксиома'
		typ = 'Стенд'
		place = 'Ауд. 349'
		#здесь информация из POSGRESQL будет потом, пока что просто текст с общей информацией
		bot.send_message(message.chat.id,"Назывние: {0}\nТип: {1}\nМестоположение: {2}".format(name,typ,place))
	elif 'Моточасы' in message.text:
		bot.send_message(message.chat.id, getAnswer(message.text,flgMachine), parse_mode= 'HTML')
	elif 'Канал 1' in message.text:
		bot.send_message(message.chat.id, getAnswer(message.text,flgMachine), parse_mode= 'HTML')
	elif 'ПЛК' in message.text:
		bot.send_message(message.chat.id, getAnswer(message.text,flgMachine), parse_mode= 'HTML')
	elif 'Главное меню' in message.text:
		bot.send_message(message.chat.id, message.text, reply_markup=MAINMENU())
	elif 'Назад' in message.text:
		bot.send_message(message.chat.id, message.text, reply_markup= MARKUPone(6))
	else:
		if ':' in message.text:
			print(message.text)
		else:
			print('некомандное сообщение')
			bot.reply_to(message, 'Такой команды я точно не ожидал')

#пуллинг
bot.polling(none_stop=True)  
#while True:
    #try:
	    #bot.polling(none_stop=True)
	#except Exception as e:
	    #time.sleep(10)
#if __name__ == '__main__':  
  # bot.polling()
