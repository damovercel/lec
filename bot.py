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
	bot.send_message(chat_id=chatId, text="Still under construction...")

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
			for e in page_tree.get_element_by_id("autor"):
				if e.tag == "a":
					b_author.append({"name": e.text, "url": e.attrib["href"]})
				# print(a.xpath('.//a'))
			b_genre = []
			for e in page_tree.get_element_by_id("genero"):
				if e.tag == "a":
					b_genre.append({"name": e.text, "url": e.attrib["href"]})
			b_sinopsis = page_tree.xpath('//*[@name="description"]')[0].attrib["content"]
			b_downloads = {}
			for d in page_tree.get_element_by_id("downloadContainer"):
				# print(d)
				b_downloads[d.xpath('.//input')[0].attrib["value"]] = d.attrib["href"]
			b_id = []
			for d in b_downloads.keys():
				l1 = b_downloads[d].find("&d=") + 3
				l2 = b_downloads[d].find("&ti", l1 + 1)
				print(b_downloads[d][l1 : l2])
				b_id.append(InlineKeyboardButton(text=d, callback_data=f"antupload {b_downloads[d][l1 : l2]}"))
			b_author_str = []
			b_genre_str = []
			for a in b_author:
				b_author_str.append(f"<a href=\"{URL_LECTULANDIA}{a['url']}\">{a['name']}</a>")
			for g in b_genre:
				b_genre_str.append(f"<a href=\"{URL_LECTULANDIA}{g['url']}\">{g['name']}</a>")
			# print(b_author, b_genre)
			rtext = ""
			rtext += f"<b>{b_title}</b>\n\n"
			rtext += f'<b>Autor</b>: {", ".join(b_author_str)}\n'
			rtext += f'<b>Genero</b>: {", ".join(b_genre_str)}\n'
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
		to_edit = bot.send_message(chat_id=chatId, text=rtext, parse_mode="html", disable_web_page_preview=True)
		if chatMessage.startswith(f"{URL_LECTULANDIA}/search/") \
		or chatMessage.startswith(f"{URL_LECTULANDIA}/autor/") \
		or chatMessage.startswith(f"{URL_LECTULANDIA}/serie/") \
		or chatMessage.startswith(f"{URL_LECTULANDIA}/genero/"):
			to_req = f"{chatMessage}"
		else:
			to_req = f"{URL_LECTULANDIA}/search/{chatMessageHtml}"
		req = scraper.get(url=to_req)
		page_tree = fromstring(html=req.content)
		if req.status_code == 200:
			found_list = {}
			for el in page_tree.get_element_by_id("main"):
				if el.tag == "div":
					if el.attrib["class"] == "content-wrap":
						div_name = el.xpath('.//section/h2')[0].text.strip(":")
						found_list[div_name] = []
						for li in el.xpath('.//section/div/ul')[0]:
							if div_name == "Series":
								ul_name = f"📚 {li.xpath('.//a')[0].text}"
							elif div_name == "Autores":
								ul_name = f"👩🏼‍💻 {li.xpath('.//a')[0].text}"
							else:
								ul_name = f"nd {li.xpath('.//a')[0].text}"
							ul_url = li.xpath('.//a')[0].attrib["href"]
							found_list[div_name].append({"name": ul_name, "url": ul_url})
					elif el.attrib["class"] == "page-nav":
						if not "Pages" in found_list.keys():
							found_list["Pages"] = []
						for bu in el:
							print(bu.text_content())
							if bu.attrib["class"] == "page-numbers current" or bu.attrib["class"] == "page-numbers dots":
								found_list["Pages"].append({"name": bu.text, "url": "non"})
							else:
								found_list["Pages"].append({"name": bu.text, "url": bu.attrib['href']})
						print(found_list["Pages"])
									#found_list["Pages"][el.text] = f"{URL_LECTULANDIA}{bu.attrib['href']}"

				if el.tag == "article":
					if el.attrib["class"] == "card":
						ar_lin_li = []
						ge_lin_li = []
						ar_name = ""
						ar_url = ""
						ar_lin = ""
						ge_lin = ""
						if not "Libros" in found_list.keys():
							found_list["Libros"] = []
						for e in el.xpath('.//div')[0]:
							# print(e.attrib)
							if e.tag == "h2":
								e_a = e.xpath('.//a')[0]
								ar_name = e_a.text.replace("\n", "").strip()
								ar_url = e_a.attrib["href"]
							elif e.attrib["class"] == "subdetail":
								# print("once")
								if not ar_lin_li:
									for a in e:
										ar_lin_li.append(f"<a href=\"{URL_LECTULANDIA}{a.attrib['href']}\">{a.text}</a>")
								elif not ge_lin_li:
									for a in e:
										ge_lin_li.append(f"<a href=\"{URL_LECTULANDIA}{a.attrib['href']}\">{a.text}</a>")
								if ar_lin_li:
									ar_lin = ", ".join(ar_lin_li)
								if ge_lin_li:
									ge_lin = ", ".join(ge_lin_li)
						# replace("\n", "").strip()
						ar_name = f"📖 {ar_name}"
						# print('"' + ar_name + '"')
						# ar_url = el.xpath('.//div/h2/a')[0].attrib["href"]
						found_list["Libros"].append({"name": ar_name, "url": ar_url, "ar_lin": ar_lin, "ge_lin": ge_lin})

			if not found_list:
				bot.edit_message_text(message_id=to_edit.message_id, chat_id=chatId, text=f"Ningun resultado para: <b>{chatMessage}</b>", parse_mode="html", disable_web_page_preview=True)
			else:
				# print(found_list["Libros"])
				bot.edit_message_text(message_id=to_edit.message_id, chat_id=chatId, text=f"Resultado para: <b>{chatMessage}</b>", parse_mode="html", disable_web_page_preview=True)
				for k in found_list.keys():
					rtext = ""
					rtext += f"<b>{k}</b>:"
					rtext += f"\n\n"
					for r in found_list[k]:
						r_now = ""
						if k == "Pages":
							if r["url"] == "non":
								r_now = f"{r['name']} "
							else:
								r_now = f"<a href=\"{URL_LECTULANDIA}{r['url']}\">{r['name']} </a>"
						elif k == "Libros":
							r_now = f"<a href=\"{URL_LECTULANDIA}{r['url']}\">{r['name']} </a>\n"
							if r["ar_lin"]:
								r_now += f"{r['ar_lin']}\n"
							if r["ge_lin"]:
								r_now += f"{r['ge_lin']}\n"
							r_now += "\n"
						else:
							r_now = f"<a href=\"{URL_LECTULANDIA}{r['url']}\">{r['name']}</a>\n\n"
						if len(rtext + r_now) >= 4096:
							bot.send_message(chat_id=chatId, text=rtext, parse_mode="html", disable_web_page_preview=True)
							rtext = ""
							rtext += f"<b>{k}</b>:"
							rtext += f"\n\n"

						rtext += r_now
					bot.send_message(chat_id=chatId, text=rtext, parse_mode="html", disable_web_page_preview=True)
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
				# rtext = ""
				# rtext += f"<b>Compartido</b>: {b_time}"
				bot.send_document(chat_id=chatId, document=open(file=f"./books/{b_name}", mode="rb"), parse_mode="html")
				unlink(f"./books/{b_name}")

			else:
				rtext = ""
				rtext += "<b>Error</b>: la conexion a antupload ha fallado"
				bot.send_message(chat_id=chatId, text=rtext, parse_mode="html")

	else:
		rtext = ""
		rtext += "<b>Error</b>: la conexion a lectulandia ha fallado"
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
