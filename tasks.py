import os
import json
import time
import aiohttp
import nextcord
import traceback
from functools import wraps
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
			except Exception:
				message = f"```\n{traceback.format_exc()}\n```"
				if i.response.is_done():
					await i.followup.send(message, ephemeral=True)
				else:
					await i.response.send_message(message, ephemeral=True)

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

	async def _startTask(self):
		reason = ""
		try:
			await self.target.send(f"Task ID `{self.id}` is started, this may take a while depending on how long it is.")

			old = time.time()
			success, url = await self.start()
			if success:
				await self.target.send(
					"# Task is successfully done!\n\n"
					f"Your Task ID `{self.id}` is finished without any errors, and has took `{round(time.time() - old, 4)}` seconds to finish.\n\n"
					f"The file is available in this URL: {url}\n"
					"-# Do note that this file CAN be deleted randomly in that server but its unlikely unless it is running out of space.\n"
					"-# Why not *Discord?* Due to its limited size, it would probably cause errors, so that's why this URL is used."
				)
				return
			reason = f"Task Failed due to this error: {url}"
		except Exception:
			reason = f"Exception Occurred!\n\n{traceback.format_exc()}"

		await self.target.send(
			"# Task has gotten errors!\n\n"
			f"Your Task ID `{self.id}` has received errors and has stopped.\n\n"
			f"```\n{reason}\n```\n\n"
			"Please fix on what you're doing!"
		)

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
				resp.raise_for_status()

				size = int(resp.headers.get("content-length", 0x80000000))
				if size > 0x7FFFFFFF:
					raise ValueError(f"Sorry! I can't handle large JSONs (your JSON size is {size} while i only accept 2GB!).")

				async for line in resp.content.iter_chunked(8192):
					string.extend(line)
		serialized = json.loads(string)
		del string

		if "song" not in serialized:
			raise ValueError("Not a Psych Engine Format.")
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
		return True, f"https://n2xd.dedyn.io/rBot/{self.id}.{self.extension}"