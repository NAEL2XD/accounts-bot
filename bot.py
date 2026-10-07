from __future__ import annotations

import os
import sys
import json
import time
import consts
import random
import aiohttp
import nextcord
import traceback
import achievements
from tasks import Task
from commands import BotCommands
from typing import Union, Optional
from nextcord.ext import tasks, commands

Member = Union[nextcord.User, nextcord.Member]

class UserData:
	def __init__(self, data:dict = {}):
		self.roleSave:list[int] = []
		self.bombed:int = 0
		self.cmdTimestamp:float = 0

		for key, value in self.__dict__.items():
			if key in data and isinstance(data[key], type(value)):
				self.__dict__[key] = data[key]

class AccountBot(commands.Bot):
	LOGS_CHANNEL:Optional[nextcord.TextChannel] = None
	USER_DATA:dict[int, UserData] = {}
	TASKS:list[Task] = []
	CUR_COMMIT = ""

	@tasks.loop(seconds=1)
	async def taskLoop(self):
		if self.TASKS:
			await self.TASKS.pop()._startTask()

	# BOT UTILITIES
	def getDataFromMember(self, member:Member) -> UserData:
		if member.id not in self.USER_DATA:
			self.USER_DATA[member.id] = UserData()
		return self.USER_DATA[member.id]

	@tasks.loop(minutes=10)
	async def autoSave(self):
		dataPath = "data/users.json"
		tmpPath = f"{dataPath}.tmp"
		with open(tmpPath, "w") as f:
			json.dump({num: value.__dict__ for num, value in self.USER_DATA.items()}, f, separators=(',', ':'))
		os.replace(tmpPath, dataPath)

	@tasks.loop(minutes=2)
	async def tagline(self):
		await self.change_presence(
			activity=nextcord.Game(
				random.choice([
					"*not* Made by TheTrueAccount_2",
					"may i pls get gbs of chart pls pls pls plspslsplspls",
					"420",
					"VDaB news: Community is still a dumpster fire",
					"i exist, totally i do.",
					"shame that nobody knows i exist",
					"Go go gadget documents.",
					"I will come in and ruin- i mean make your day!",
					f"I have a total of {len(self.TASKS)} tasks to do, be right back!",
					"don't use bandu, instead use me!" # lancey joke
				])
			)
		)

	@tasks.loop(minutes=30)
	async def autoUpdate(self):
		commit = ""
		async with aiohttp.ClientSession() as session:
			async with session.get("https://api.github.com/repos/NAEL2XD/accounts-bot/commits") as r:
				try:
					r.raise_for_status()
				except aiohttp.ClientResponseError:
					return
				commit = str((await r.json())[0]["sha"]).strip().lower()

		if commit in [self.CUR_COMMIT, ""]:
			return

		self.autoSave.cancel()
		await self.autoSave()

		with open("data/commit.txt", "w") as f:
			f.write(commit)

		with open("restart.sh", "w") as f:
			f.write(consts.RESTART_SCRIPT)

		os.chmod("restart.sh", 0o755)
		os.execvp("/bin/bash", ["bash", "restart.sh"])

	async def tryDM(self, message:str, member:Member):
		try:
			await member.send(message)
		except:
			pass

	async def voteHandler(self, message:nextcord.Message):
		if isinstance(message.channel, nextcord.TextChannel) and message.channel.category and \
			isinstance(message.channel.category, nextcord.CategoryChannel) and message.channel.category.id not in consts.COMMUNITY_IDS:
			return

		media:nextcord.Attachment|None = None
		if message.attachments:
			media = message.attachments[0]
		elif message.snapshots and message.snapshots[0].attachments:
			media = message.snapshots[0].attachments[0]

		if (media and media.content_type or "").split("/", 1)[0].lower() in ["image", "video", "audio"] and isinstance(message.author, nextcord.Member):
			emojiDict = {str(emoji): emoji.count for emoji in message.reactions if str(emoji) in ['⬆️', '⬇️'] and emoji.me}
			for emoji in ["⬆️", "⬇️"]: # KeyError goes bye.
				if emoji not in emojiDict:
					await message.add_reaction(emoji)
					emojiDict[emoji] = 1

			if emojiDict["⬆️"] >= 10 and emojiDict["⬇️"] <= 1:
				await achievements.unlock(
					self, message.author, "Everyone Loves It", 
					"# Congratulations!!\n\n"
					f"Your [post]({message.jump_url}) there was a massive success!\n\n"
					"Because your post didn't even get a single downvote, and has more than 10 upvotes, that means you now have gotten the `Everyone Loves It!!` role!\n\n"
					"Check your profile, it should be there now, and have fun with your new role!"
				)

	#
	# CURRENT CONFIG
	#
	def __init__(self, *, intents:nextcord.Intents):
		super().__init__(intents=intents)
		if os.path.exists("data/users.json"):
			with open("data/users.json", "r") as f:
				self.USER_DATA = {int(key): UserData(value) for key, value in dict(json.load(f)).items()}

		if os.path.exists("data/commit.txt"):
			with open("data/commit.txt", "r") as f:
				self.CUR_COMMIT = f.read()
		os.makedirs("data/ids", exist_ok=True)

		self.tagline.start()
		self.autoSave.start()
		self.taskLoop.start()
		if os.getenv("D_TESTING") != "1":
			self.autoUpdate.start()

	async def on_ready(self):
		print(f"Logged on as {self.user}!")

		if (
			(guild := self.get_guild(consts.GUILD_ID)) and
			(logs := guild.get_channel(1179012815479115786)) and
			isinstance(logs, nextcord.TextChannel)
		):
			self.LOGS_CHANNEL = logs

		await self.tagline()

	async def on_member_join(self, member:nextcord.Member):
		age = time.time() - member.created_at.timestamp()
		if age < consts.MINIMUM_AGE:
			days = round(age / 86400, 1)
			await member.kick(reason=f"Not old enough to join this server ({days} days old)")
			await self.tryDM(
				f"Hey {member.name}, thanks for joining Account's Folder\n\n"
				"You're seeing this DM because your account is **NOT** old enough to join Account's Folder\n\n"
				f"Your account's creation is `{member.created_at.strftime("%d-%m-%Y %H:%M:%S")}` (`{days} days`), "
				"when Account's Folder requires all users to be more than 14 days old.\n\n"
				f"Wait about `{round((consts.MINIMUM_AGE - age) / 86400, 1)} days` to be able to access this server again!\n\n"
				f"-# You can join back in this server if you're old enough: https://discord.gg/dsRUP9MAxY",
				member
			)
			return

		for roleID in self.getDataFromMember(member).roleSave:
			try:
				role = member.guild.get_role(roleID)
				if role:
					await member.add_roles(role)
			except:
				pass

	async def on_member_remove(self, member:nextcord.Member):
		self.getDataFromMember(member).roleSave = [role.id for role in member.roles]

	async def on_raw_reaction_add(self, m:nextcord.RawReactionActionEvent):
		cID = self.get_channel(m.channel_id)
		if not cID or not isinstance(cID, nextcord.TextChannel) or cID.category_id not in consts.COMMUNITY_IDS:
			return

		msg = await cID.fetch_message(m.message_id)
		if msg: # CCC
			await self.voteHandler(msg)

	async def on_message(self, message:nextcord.Message):
		isSelf = message.author == self.user
		if isSelf or not isinstance(message.channel, nextcord.TextChannel):
			if isinstance(message.channel, nextcord.DMChannel) and self.LOGS_CHANNEL and not isSelf: # not in account's folder but in a DM, so we send that to a channel
				await (await message.forward(self.LOGS_CHANNEL)).reply(f"From {message.author.mention}")
			return

		# Community Channel Checks
		await self.voteHandler(message)

		# i was bored ok?
		if random.random() >= 0.999 and isinstance(message.author, nextcord.Member):
			await achievements.unlock(self, message.author, "You did it!", "your did it, you gain achievement")

	#
	# Error Handling
	#
	async def handleErr(self, exception:str, send:str):
		with open("data/exception.txt", "w", encoding="utf-8") as f:
			f.write(exception)

		user = self.get_user(786639413282209802)
		if user:
			await user.send(send, file=nextcord.File("data/exception.txt", "exception.txt"))

		os.remove("data/exception.txt")

	async def on_error(self, error):
		await self.handleErr(traceback.format_exc(), f"# New Exception Occurred! - Reason: `{error}`")

	async def on_application_command_error(self, interaction:nextcord.Interaction, exception:nextcord.ApplicationError):
		await self.handleErr(
			"\n".join(traceback.format_exception(type(exception), exception, exception.__traceback__)),
			"# New Exception Occurred!\n"
			f"- Reason: `{exception}`\n"
			f"- Interaction: `{interaction.application_command}`"
		)

if __name__ == "__main__":
	self = AccountBot(intents=nextcord.Intents.all())
	self.add_cog(BotCommands(self))
	self.run(sys.argv[1])