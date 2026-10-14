import gc
import os
import json
import time
import random
import aiohttp
import nextcord
import traceback
from functools import wraps
from urllib.parse import quote
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
	from commands import BotCommands

def mode():
	def decorator(func):
		@wraps(func)
		async def wrapper(self:"BotCommands", i:nextcord.Interaction, *args, **kwargs):
			if not i.user:
				return

			try:
				await i.user.create_dm()
			except nextcord.Forbidden:
				return await i.response.send_message("You must have DMs enabled to use Tasks.", ephemeral=True)

			try:
				task = await func(self, i, *args, **kwargs)
				if isinstance(task, Task):
					self.bot.TASKS.append(task)
					await i.response.send_message(f"Task ID `{task.id}` has been added, you're on position {len(self.bot.TASKS)}.", ephemeral=True)
			except Exception as e:
				await i.response.send_message(f"{e}\n\n```\n{traceback.format_exc()}\n```", ephemeral=True)
		return wrapper
	return decorator

class Task:
	def __init__(self, bot:"BotCommands", i):
		target = i
		if not isinstance(target, (nextcord.User, nextcord.Member)):
			raise Exception("Who are you?")

		self.bot = bot
		self.target = target
		self.id = 1
		if os.path.exists("data/id.txt"):
			with open("data/id.txt", "r") as f:
				self.id = int(f.read()) + 1

		with open("data/id.txt", "w") as f:
			f.write(str(self.id))

	async def start(self) -> tuple[bool, str]:
		return True, ""

	async def handler(self):
		send = ""
		file = []
		try:
			old = time.time()
			success, output = await self.start()
			if not success:
				raise Exception(f"Task Failed due to this error: {output}")

			if len(output) > 1024:
				with open(".tmp", "w") as f:
					f.write(output)
				file.append(nextcord.File(".tmp", "big_file.txt"))
				output = "The output can be viewed by seeing big_file.txt"

			minutes, seconds = divmod(time.time() - old, 60)
			send = (
				"# Task is successfully done!\n\n"
				f"Your Task ID `{self.id}` is finished without any errors, and has took `{int(minutes)}:{seconds:06.3f}` seconds to finish.\n\n"
				f"The outputted message:\n\n```\n{output}\n```\n\n"
			)
		except Exception as e:
			with open(".tmp", "w") as f:
				f.write(traceback.format_exc())
				file.append(nextcord.File(".tmp", "error.txt"))

			send = (
				"# Task has gotten errors!\n\n"
				f"Your Task ID `{self.id}` has received errors and has stopped.\n\n"
				f"*{e}*\n-# The traceback is found on `error.txt`\n\n"
				"Please fix on whatever you're doing!"
			)

		await self.target.send(send, files=file)
		if os.path.exists(".tmp"):
			os.remove(".tmp")

class FNFConverter(Task):
	def __init__(self, bot:"BotCommands", i, chartFormat:str, pathToURL:str):
		super().__init__(bot, i)
		typeof, self.extension = os.path.splitext(chartFormat)
		self.url = pathToURL
		self.func:Callable[[float, int, float], str] = {
			"Add Yourself Singing": lambda time, direction, length: f"{{{round(time / 1000, 7)}}}: {{{direction}}}: {{{length}}}"
		}[typeof]

	async def start(self) -> tuple[bool, str]:
		string = bytearray()
		async with aiohttp.ClientSession() as session:
			async with session.get(self.url) as resp:
				try:
					resp.raise_for_status()
				except aiohttp.ClientResponseError as e:
					return False, f"{e}\n\n{await resp.text()}"

				size = int(resp.headers.get("content-length", 0x80000000))
				if size > 0x7FFFFFFF:
					return False, f"Sorry! I can't handle large JSONs (your JSON size is {size} while i only accept 2GB!)."

				async for line in resp.content.iter_chunked(8192):
					string.extend(line)
		serialized = json.loads(string)
		del string

		if "song" not in serialized:
			return False, "Not a Psych Engine Format."
		elif isinstance(serialized["song"], dict):
			serialized = serialized["song"]

		out:list[tuple[float, int, float]] = []
		for section in serialized["notes"]:
			hit = int(section["mustHitSection"]) * 4
			for notes in section["sectionNotes"]:
				out.append((notes[0], (notes[1] + hit) % 8, notes[2]))
		out.sort(key=lambda x: x[0])

		with open("convert.tmp", "w") as f:
			for time, direction, length in out:
				f.write(f"{self.func(time, direction, length)}\n")
		os.replace("convert.tmp", f"../Site/start/rBot/{self.id}.{self.extension}")
		del out

		gc.collect() # cleanup
		return True, f"https://n2xd.dedyn.io/rBot/{self.id}.{self.extension}"

class BadTranslate(Task):
	def __init__(self, bot:"BotCommands", i, content:str, cycle:int):
		super().__init__(bot, i)
		self.content = content
		self.cycle = cycle

	async def start(self) -> tuple[bool, str]:
		if len(self.content) < 2:
			return False, f"There is nothing to translate!"

		async with aiohttp.ClientSession(headers={
			"Accept": "application/json",
			"Accept-Encoding": "gzip, deflate, br, zstd",
			"Accept-Language": "en-US,en;q=0.9",
			"Priority": "u=0",
			"Referer": "https://translate.google.com/",
			"Sec-Fetch-Dest": "empty",
			"Sec-Fetch-Mode": "cors",
			"Sec-Fetch-Site": "same-origin",
			"Sec-Gpc": "1",
			"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:151.0) Gecko/20100101 Firefox/151.0",
			"X-Amzn-Trace-Id": "Root=1-6a1b4544-1194171b74103f097e63bc42"
		}) as base:
			langs = ["af","sq","am","ar","hy","az","eu","bn","bs","bg","ca","ceb","zh-CN","zh-TW","co","hr","cs","da","nl","en","eo","et","fi","fr","fy","gl","ka","de","el","gu","ht","ha","haw","iw","hi","hmn","hu","is","id","ga","ja","jw","kn","kk","km","ko","ku","lo","lv","lt","lb","mk","mg","ms","ml","mt","mi","mr","mn","ne","no","ny","ps","fa","pl","pt","pa","ro","ru","sm","gd","sr","st","sn","sd","si","sk","sl","so","es","sw","sv","tl","tg","ta","te","th","tr","uk","ur","uz","vi","cy","xh","yi","yo","zu"]

			oldLang = "en"
			for cycle in range(self.cycle):
				randomLang = oldLang
				while randomLang == oldLang:
					randomLang = random.choice(langs)

				if cycle == self.cycle - 1:
					randomLang = "en"

				async with base.get(f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={oldLang}&tl={randomLang}&dt=t&q={quote(self.content)}") as resp:
					resp.raise_for_status()
					self.content = "".join([x[0] for x in (await resp.json())[0]])
					oldLang = randomLang

		return True, f"Output for Bad Translation:\n\n{self.content}"