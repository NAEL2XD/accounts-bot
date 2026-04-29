import os
import sys
import json
import time
import utils
import consts
import asyncio
import aiohttp
import nextcord
import traceback
from typing import Union
from functools import wraps
from nextcord.ext import tasks, commands as slashcmds

if __name__ == "__main__":
	import commands
	import achievements as achievement

Member = Union[nextcord.User, nextcord.Member]

class UserData:
	def __init__(self, data:dict = {}):
		self.roleSave:list[int] = []
		self.bombed:int = 0
		self.cmdTimestamp:float = 0

		for key in self.__dict__.keys():
			if key in data and isinstance(data[key], type(self.__dict__[key])):
				self.__dict__[key] = data[key]

class AccountBot(slashcmds.Bot):
	USER_DATA:dict[int, UserData] = {}
	LOGS_CHANNEL:nextcord.TextChannel|None = None
	SAVE_OUTDATED = False
	LAST_ONLINE = 0.0
	CUR_COMMIT = ""

	# BOT UTILITIES
	def getDataFromMember(self, member:Member) -> UserData:
		self.SAVE_OUTDATED = True
		if member.id not in self.USER_DATA:
			self.USER_DATA[member.id] = UserData()
		return self.USER_DATA[member.id]

	@tasks.loop(minutes=10)
	async def autoSave(self):
		if self.SAVE_OUTDATED:
			dataPath = "data/users.json"
			tmpPath = f"{dataPath}.tmp"
			with open(tmpPath, "w") as f:
				json.dump({num: value.__dict__ for num, value in self.USER_DATA.items()}, f, separators=(',', ':'))
			os.replace(tmpPath, dataPath)
			self.SAVE_OUTDATED = False

	@tasks.loop(minutes=1)
	async def autoSet(self):
		await self.change_presence(
			activity=nextcord.Game(f"UPTIME: {utils.formatToTimeAgo(time.time() - self.LAST_ONLINE)}"),
			status=nextcord.Status.do_not_disturb
		)

	@tasks.loop(minutes=30)
	async def autoUpdate(self):
		commit = ""
		async with aiohttp.ClientSession() as session:
			async with session.get(consts.REPO_COMMIT_API) as r:
				try:
					r.raise_for_status()
				except aiohttp.ClientResponseError:
					return
				commit = str((await r.json())[0]["sha"]).strip().lower()

		if commit in [self.CUR_COMMIT, ""]:
			return

		self.SAVE_OUTDATED = True
		self.autoSave.cancel()
		await self.autoSave()

		with open("data/commit.txt", "w") as f:
			f.write(commit)

		# yes its stupid but it works
		with open("restart.sh", "w") as f:
			f.write("\n".join([
				'#!/bin/bash',
				'if [ -d ".tmp" ]; then',
				'	cd .tmp',
				'	git pull origin main',
				'	cd ..',
				'else',
				'	git clone https://github.com/NAEL2XD/accounts-bot.git .tmp',
				'fi',
				'cp -rf ./.tmp/. .',
				'echo wait for start...',
				f'~/env/bin/python bot.py "{sys.argv[1]}"'
			]))

		os.chmod("restart.sh", 0o755)
		os.execvp("/bin/bash", ["bash", "restart.sh"])

	async def tryDM(self, message:str, member:Member):
		try:
			await member.send(message)
		except:
			pass

	#
	# CURRENT CONFIG
	#
	def __init__(self, *, intents: nextcord.Intents) -> None:
		super().__init__(intents=intents, default_guild_ids=None)
		if os.path.exists("data/users.json"):
			with open("data/users.json", "r") as f:
				self.USER_DATA = {int(key): UserData(value) for key, value in dict(json.load(f)).items()}

		utils.touch("commit.txt")
		with open("data/commit.txt", "r") as f:
			self.CUR_COMMIT = f.read()

	async def on_ready(self):
		print(f"Logged on as {self.user}!")
		self.LAST_ONLINE = time.time()

		try:
			self.autoSave.start()
			self.autoSet.start()
			if os.getenv("D_TESTING") != "1":
				self.autoUpdate.start()
		except RuntimeError:
			pass

		guild = self.get_guild(consts.GUILD_ID)
		if guild:
			logs = guild.get_channel(consts.LOGS_ID)
			if logs and isinstance(logs, nextcord.TextChannel):
				self.LOGS_CHANNEL = logs

	async def on_member_join(self, member:nextcord.Member):
		age = time.time() - member.created_at.timestamp()
		if age < consts.FOURTEEN_DAYS:
			days = round(age / 86400, 1)
			await member.kick(reason=f"Not old enough to join this server ({days} days old)")
			await self.tryDM(
				f"Hey {member.name}, thanks for joining Account's Folder\n\n"
				"You're seeing this DM because your account is **NOT** old enough to join Account's Folder\n\n"
				f"Your account's creation is `{member.created_at.strftime("%d-%m-%Y %H:%M:%S")}` (`{days} days`), "
				"while Account's Folder requires all users to be more than 14 days old.\n\n"
				f"Wait about `{round((consts.FOURTEEN_DAYS - age) / 86400, 1)} days` to be able to access this server again!\n\n"
				"-# p.s. If that time is up, you can rejoin this server (https://discord.gg/dsRUP9MAxY)\n"
				"-# Oh and DON'T FLOOD OUR LOGS!!!",
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
		if not cID or not isinstance(cID, nextcord.TextChannel) or not cID.category_id != consts.COMMUNITY_ID:
			return # This shouldn't happen

		mID = await cID.fetch_message(m.message_id)
		if not mID or not isinstance(mID.channel, nextcord.TextChannel): # CCC
			return

		emojiDict = {str(emoji): emoji.count for emoji in mID.reactions if str(emoji) in ['⬆️', '⬇️'] and emoji.me}
		for emoji in ["⬆️", "⬇️"]: # KeyError goes bye.
			if emoji not in emojiDict:
				await mID.add_reaction(emoji)
				emojiDict[emoji] = 1

		if emojiDict["⬆️"] >= 10 and emojiDict["⬇️"] <= 1 and isinstance(mID.author, nextcord.Member):
			await achievement.unlock(
				self, mID.author, "Everyone Loves It", 
				"# Congratulations!!\n\n"
				f"Your [post]({mID.jump_url}) there was a massive success!\n\n"
				"Because your post didn't even get a single downvote, and has more than 10 upvotes, that means you now have gotten the `Everyone Loves It!!` role!\n\n"
				"Check your profile, it should be there now, and have fun with your new role!"
			)

	async def on_message(self, message:nextcord.Message):
		isSelf = message.author == self.user
		if isSelf or not isinstance(message.channel, nextcord.TextChannel):
			if isinstance(message.channel, nextcord.DMChannel) and self.LOGS_CHANNEL and not isSelf: # not in account's folder but in a DM, so we send that to a channel
				await (await message.forward(self.LOGS_CHANNEL)).reply(f"From {message.author.mention}")
			return
		userData = self.getDataFromMember(message.author)

		# Honeypot
		if message.channel.id == consts.HONEYPOT_ID and isinstance(message.author, nextcord.Member):
			userData.roleSave = [role.id for role in message.author.roles]
			await message.author.kick(reason="User intentionally got hacked, or actually just got hacked!! Should have changed your Password.")
			await self.tryDM(
				"## You've been HACKED!!\n\n"
				"Either you got this by getting yourself (intentionally) hacked or just too curious to go to a channel that's for a honeypot.\n\n"
				"If you *did* get hacked? CHANGE your password, ADD 2 Factor Authentification, "
				"UNAUTHORIZE anything suspicious in your account (`User Settings > Devices & Authorised Apps`)\n\n"
				"If you took all actions (or just became too curious), then you can join back this server @ https://discord.gg/dsRUP9MAxY\n\n"
				"-# Oh and no, you're not banned.",
				message.author
			)
			await message.delete()
			return

		# Community Channel Checks
		if (message.attachments or message.snapshots) and \
			message.channel.category and isinstance(message.channel.category, nextcord.CategoryChannel) and message.channel.category.id == consts.COMMUNITY_ID:
			media:nextcord.Attachment
			if message.attachments:
				media = message.attachments[0]
			elif message.snapshots and message.snapshots[0].attachments:
				media = message.snapshots[0].attachments[0]

			if (media and media.content_type or "").split("/", 1)[0].lower() in ["image", "video", "audio"]:
				await asyncio.sleep(0.25)
				for emoji in ['⬆️', '⬇️']:
					await message.add_reaction(emoji)
			return

	async def on_error(self, error):
		with open("data/exception.txt", "w", encoding="utf-8") as f:
			f.write(traceback.format_exc().replace("  ", "\t"))

		user = self.get_user(consts.DEVELOPER_ID)
		if user:
			await user.send(f"New Exception Occurred!\nReason: `{error}`", file=nextcord.File("data/exception.txt", "exception.txt"))
		os.remove("data/exception.txt")

if __name__ == "__main__":
	self = AccountBot(intents=nextcord.Intents.all())

	# BOILERPLATE BULLSHIT but it works but also it fucking sucks
	def cooldown(seconds: float):
		def decorator(func):
			@wraps(func)
			async def wrapper(i:nextcord.Interaction, *args, **kwargs):
				if not i.user:
					return

				user = self.getDataFromMember(i.user)
				timeLeft = user.cmdTimestamp - time.time() + seconds
				if timeLeft < 0:
					if seconds != 0:
						user.cmdTimestamp = time.time()
					return await func(i=i, *args, **kwargs)
				return await i.response.send_message(f"You are using this command way too quickly! Please wait about `{round(timeLeft, 2)} seconds` to run this command again.")
			return wrapper
		return decorator

	# TODO: somehow make this in commands.py and also make it register too
	@self.slash_command(description="Shows the current Help Command.")
	async def help(
		i:nextcord.Interaction,
		command:str = nextcord.SlashOption(description="The command to use from the choices.", choices=["bomb", "achievements", "help"])
	): await commands.help(i, command)

	@self.slash_command(description="Bomb someone else `(@ping them)` or just yourself!")
	@cooldown(30)
	async def bomb(
		i:nextcord.Interaction,
		user:nextcord.Member = nextcord.SlashOption(description="User to target and bomb.", required=False),
		lb:bool = nextcord.SlashOption(description="Optional field if you wanna see the leaderboard (user must be null)", required=False)
	): await commands.bomb(i, self, user, lb)

	@self.slash_command(description="Shows stats of all the achievements with detail and such.")
	async def achievements(i:nextcord.Interaction):
		await commands.achievements(i)

	self.run(sys.argv[1])