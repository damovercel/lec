#!/bin/python3

from telegram import InputMediaPhoto
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from os import environ, mkdir
from lxml.html import fromstring
from json import load
from urllib.parse import quote
from cloudscraper import create_scraper
# from urllib.parse import quote

###        								###
###        								###
###        								###
#print("arregral la linea 32, esta feisima")
###        								###
###    									###
###    									###

BOT_TOKEN = environ.get("BOT_TOKEN")
DEBUG_ID = environ.get("DEBUG_ID")

CONFIG = load(open("./config.json"))
WEB_HEADERS = CONFIG["WEB_HEADERS"]
WEB_BROWSER = CONFIG["WEB_BROWSER"]
URL_LECTULANDIA = CONFIG["URL_LECTULANDIA"]

scraper = create_scraper(browser=WEB_BROWSER)

URL_LECTULANDIA = scraper.get(url=URL_LECTULANDIA).url

def printt(*values):
	rep = ""
	if len(values) == 1:
		rep += values[0]
	else:
		for c in values:
			rep += f"{c}\n"
	bot.send_message(chat_id=DEBUG_ID, text=rep)


def command_start(update, context):
	chatId = update["message"]["chat"]["id"]
	bot.send_message(chat_id=chatId, text=".")

def b_search(update, context):
	chatId = update["message"]["chat"]["id"]
	chatMessage = update["message"]["text"]
	chatMessageHtml = quote(chatMessage)
	rtext = ""
	rtext += f"Buscando resultados para: <b>{chatMessage}</b>"
	to_edit = bot.send_message(chat_id=chatId, text=rtext, parse_mode="html")



if __name__ == '__main__':
	updater = Updater(BOT_TOKEN)
	dispatcher = updater.dispatcher
	bot = updater.bot

	dispatcher.add_handler(CommandHandler(command="start", callback=command_start))
	dispatcher.add_handler(MessageHandler(filters=Filters.text, callback=b_search))

	bot.send_message(chat_id=DEBUG_ID, text="Polling!!!")
	print("Polling!!!")
	updater.start_polling(drop_pending_updates=True)