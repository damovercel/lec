#!/bin/python3

from telegram import InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from os import environ, mkdir, unlink
from lxml.html import fromstring
from json import load
from urllib.parse import quote
from cloudscraper import create_scraper
# from urllib.parse import quote
###        								###
###        								###
###        								###
print("arregral en la busqueda la recoleccion de generos, autores, y series")
###        								###
###    									###
###    									###

BOT_TOKEN = environ.get("BOT_TOKEN")
DEBUG_ID = environ.get("DEBUG_ID")

CONFIG = load(open("./config.json"))
WEB_HEADERS = CONFIG["WEB_HEADERS"]
WEB_BROWSER = CONFIG["WEB_BROWSER"]
URL_LECTULANDIA = CONFIG["URL_LECTULANDIA"]
URL_ANTUPLOAD = CONFIG["URL_ANTUPLOAD"]

try:
	mkdir("./books/")
except:
	pass

scraper = create_scraper(browser=WEB_BROWSER)

# URL_LECTULANDIA = scraper.get(url=URL_LECTULANDIA).url

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
	bot.send_message(chat_id=chatId, text="o")

def b_search(update, context):
	chatId = update["message"]["chat"]["id"]
	chatMessage = update["message"]["text"]
	chatMessageHtml = quote(chatMessage)
	if chatMessage.startswith(f"{URL_LECTULANDIA}/book/"):
		rtext = ""
		rtext += f"Buscando informacion de: <b>{chatMessage}</b>"
		to_edit = bot.send_photo(chat_id=chatId, photo=open("./lectulandia.png", "rb"), caption=rtext, parse_mode="html")
		req = scraper.get(url=chatMessage)
		page_tree = fromstring(html=req.content)
		if req.status_code == 200:
			b_title = page_tree.xpath('//*[@id="title"]/h1')[0].text
			b_cover = page_tree.xpath('//*[@id="cover"]/img')[0].attrib["src"]
			b_author = []
			for a in page_tree.xpath('//*[@id="autor"]'):
				print(a.xpath('.//a'))
				b_author.append(a.xpath('.//a')[0].text)
			b_genre = []
			for a in page_tree.xpath('//*[@id="genero"]'):
				b_genre.append(a.xpath('.//a')[0].text)
			# b_sinopsis = page_tree.xpath('//*[@id="sinopsis"]')[0].text_content()
			b_sinopsis = page_tree.xpath('//*[@name="description"]')[0].attrib["content"]
			b_downloads = {}
			for d in page_tree.xpath('//*[@id="downloadContainer"]')[0]:
				print(d)
				b_downloads[d.xpath('.//input')[0].attrib["value"]] = d.attrib["href"]
			b_id = []
			for d in b_downloads.keys():
				l1 = b_downloads[d].find("&d=") + 3
				l2 = b_downloads[d].find("&ti", l1 + 1)
				print(b_downloads[d][l1 : l2])
				b_id.append(InlineKeyboardButton(text=d, callback_data=f"antupload {b_downloads[d][l1 : l2]}"))
			rtext = ""
			rtext += f"<b>{b_title}</b>\n\n"
			rtext += f'<b>Autor</b>: {", ".join(b_author)}\n'
			rtext += f'<b>Genero</b>: {", ".join(b_genre)}\n'
			rtext += f"<b>Sinopsis</b>: {b_sinopsis}"
			print(b_id)

			bot.edit_message_media(chat_id=chatId, message_id=to_edit.message_id, reply_markup=InlineKeyboardMarkup([b_id]), media=InputMediaPhoto(media=b_cover, caption=rtext, parse_mode="html"))

		else:
			rtext = ""
			rtext += "<b>Error</b>: la conexion a lectulandia ha fallado"
			bot.edit_message_caption(message_id=to_edit.message_id, chat_id=chatId, caption=rtext, parse_mode="html")	

	else:
		rtext = ""
		rtext += f"Buscando resultados para: <b>{chatMessage}</b>"
		to_edit = bot.send_message(chat_id=chatId, text=rtext, parse_mode="html")
		req = scraper.get(url=f"{URL_LECTULANDIA}/search/{chatMessageHtml}")
		page_tree = fromstring(html=req.content)
		if req.status_code == 200:
			found_list = {}
			for el in page_tree.xpath('//*[@id="main"]')[0]:
				if el.tag == "div":
					if el.attrib["class"] == "content-wrap":
						# print(div.xpath('.//section/h2')[0].text)
						div_name = el.xpath('.//section/h2')[0].text.strip(":")
						found_list[div_name] = []
						for li in el.xpath('.//section/div/ul')[0]:
							# print(li)
							ul_name = li.xpath('.//a')[0].text
							ul_url = li.xpath('.//a')[0].attrib["href"]
							found_list[div_name].append({"name": ul_name, "url": ul_url})
				if el.tag == "article":
					if el.attrib["class"] == "card":
						if not "Libros" in found_list.keys():
							found_list["Libros"] = []
						ar_name = el.xpath('.//div/h2/a')[0].text
						ar_url = el.xpath('.//div/h2/a')[0].attrib["href"]
						found_list["Libros"].append({"name": ar_name, "url": ar_url})

			if not found_list:
				bot.edit_message_text(message_id=to_edit.message_id, chat_id=chatId, text=f"Ningun resultado para: <b>{chatMessage}</b>", parse_mode="html")
			else:
				bot.edit_message_text(message_id=to_edit.message_id, chat_id=chatId, text=f"Resultados para: <b>{chatMessage}</b>", parse_mode="html")
				for k in found_list.keys():
					rtext = ""
					rtext += f"<b>{k}</b>:"
					rtext += f"\n\n"
					for r in found_list[k]:
						rtext += f'{r["name"]}\n<code>{URL_LECTULANDIA}{r["url"]}</code>\n\n'
					bot.send_message(chat_id=chatId, text=rtext, parse_mode="html")
		else:
			rtext = ""
			rtext += "<b>Error</b>: la conexion a lectulandia ha fallado"
			bot.edit_message_text(message_id=to_edit.message_id, chat_id=chatId, text=rtext, parse_mode="html")
def dl_antupload(update, context):
	update.callback_query.answer()
	chatId = update["callback_query"]["message"]["chat"]["id"]
	callb_query = update["callback_query"]["data"]
	b_id = callb_query.split(" ")[1]
	print(callb_query)
	req = scraper.get(url=f"{URL_LECTULANDIA}/download.php?d={b_id}")
	if req.status_code == 200:
		page_tree = fromstring(html=req.content)
		script_text = ""
		for s in page_tree.xpath('//*/script'):
			if s.text is not None:
				if "linkCode" in s.text:
					script_text = s.text
		antu_id = ""
		if script_text:
			l1 = script_text.find("linkCode") + 8
			l2 = script_text.find(";", l1 + 1)
			antu_id = script_text[l1 : l2].replace("=", " ").strip().strip('"')
			if antu_id.endswith("/"):
				antu_id = antu_id[: -1]
			print(antu_id)
		if antu_id:
			req = scraper.get(url=f"{URL_ANTUPLOAD}/file/{antu_id}")
			#print(req.text)
			if req.status_code == 200:
				page_tree = fromstring(html=req.content)
				b_url = page_tree.get_element_by_id("downloadB").attrib["href"]
				
				b_name = ""
				b_time = ""
				for p in page_tree.get_element_by_id("fileDescription"):
					des = p.xpath('.//span')
					if des:
						text_cont = p.xpath('.//text()')
						if len(text_cont) > 1:
							if text_cont[0] == "Name: ":
								b_name = text_cont[1]
							elif text_cont[0] == "Uploaded: ":
								b_time = text_cont[1]
				b_file = open(file=f"./books/{b_name}", mode="wb")
				with scraper.get(url=f"{URL_ANTUPLOAD}{b_url}", stream=True) as req_b:
					if req_b.status_code == 200:
						for buff in req_b.iter_content(chunk_size=1024):
							if buff:
								b_file.write(buff)
						b_file.close()
				rtext = ""
				rtext += f"<b>Compartido</b>: {b_time}"
				bot.send_document(chat_id=chatId, document=open(file=f"./books/{b_name}", mode="rb"), caption=rtext, parse_mode="html")
				unlink(f"./books/{b_name}")

	else:
		rtext = ""
		rtext += "<b>Error</b>: la conexion a antupload ha fallado"
		bot.send_message(chat_id=chatId, text=rtext, parse_mode="html")



if __name__ == '__main__':
	updater = Updater(BOT_TOKEN)
	dispatcher = updater.dispatcher
	bot = updater.bot

	dispatcher.add_handler(CommandHandler(command="start", callback=command_start))
	dispatcher.add_handler(MessageHandler(filters=Filters.text, callback=b_search))
	dispatcher.add_handler(CallbackQueryHandler(pattern="antupload", callback=dl_antupload))

	bot.send_message(chat_id=DEBUG_ID, text="Polling!!!")
	print("Polling!!!")
	updater.start_polling(drop_pending_updates=True)
