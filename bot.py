import os
import json
import time
import asyncio
import nextcord
from sys import argv
from typing import Union
from nextcord.ext import tasks

if __name__ == "__main__":
	# circular import fix
	import commands
	import achievements
	import utils

Member = Union[nextcord.User, nextcord.Member]

class UserData:
	def __init__(self, data:dict = {}) -> None:
		self.roleSave:list[int] = []
		self.bombed:int = 0
		self.cmdTimestamp:float = 0

		for key in self.__dict__.keys():
			if key in data and isinstance(data[key], type(self.__dict__[key])):
				self.__dict__[key] = data[key]

class AccountBot(nextcord.Client):
	USER_DATA:dict[int, UserData] = {}
	LOGS_CHANNEL:nextcord.TextChannel|None = None
	LAST_ONLINE:float = 0

	# BOT UTILITIES
	def getDataFromMember(self, member:Member) -> UserData:
		if member.id in self.USER_DATA:
			return self.USER_DATA[member.id]
		self.USER_DATA[member.id] = UserData()
		return self.USER_DATA[member.id]

	outdatedSave:bool = False
	@tasks.loop(minutes=10)
	async def autoSave(self):
		if self.outdatedSave:
			dataPath:str = "data/users.json"
			tmpPath:str = f"{dataPath}.tmp"
			with open(tmpPath, "w") as f:
				json.dump({num: value.__dict__ for num, value in self.USER_DATA.items()}, f, separators=(',', ':'))
			os.replace(tmpPath, dataPath)
			self.outdatedSave = False

	@tasks.loop(minutes=1)
	async def autoSet(self):
		await self.change_presence(
			activity=nextcord.Game(f"UPTIME: {utils.formatToTimeAgo(time.time() - self.LAST_ONLINE)}"),
			status=nextcord.Status.idle
		)
		return

	async def tryDM(self, message:str, member:Member):
		try:
			await member.send(message)
		except:
			pass

	#
	# CURRENT CONFIG
	#
	def __init__(self, *, intents: nextcord.Intents) -> None:
		super().__init__(intents=intents)
		if os.path.exists("data/users.json"):
			with open("data/users.json", "r") as f:
				self.USER_DATA = {int(key): UserData(value) for key, value in dict(json.load(f)).items()}

	async def on_ready(self):
		print(f'Logged on as {self.user}!')
		self.LAST_ONLINE = time.time()

		try:
			self.autoSave.start()
			self.autoSet.start()
		except RuntimeError:
			pass

		if not self.LOGS_CHANNEL:
			logChannel = self.get_channel(1179015275065131069)
			if not logChannel:
				return
			elif isinstance(logChannel, nextcord.TextChannel):
				self.LOGS_CHANNEL = logChannel

	async def on_member_join(self, member:nextcord.Member):
		fourteenDays = 60 * 60 * 24 * 14
		ageInSeconds = time.time() - member.created_at.timestamp()
		if ageInSeconds < fourteenDays: # 2 weeks
			formattedDays = round(ageInSeconds / 86400, 1)
			timeString = member.created_at.strftime("%d-%m-%Y %H:%M:%S")
			await self.tryDM(
				f"Hey {member.name}, thanks for joining Account's Folder\n\n"
				"You're seeing this DM because Your Account is not old enough to Join Account's Folder\n\n"
				f"Your Account's creation is `{timeString}` (`{formattedDays} days`), while Account's Folder requires all Users to be More than 14 days old.\n\n"
				f"Wait about `{round((fourteenDays - ageInSeconds) / 86400, 1)} days` to be able to access this server again!\n\n"
				"-# p.s. If that time is up, you can rejoin this server (https://discord.gg/dsRUP9MAxY)",
				member
			)
			await member.kick(reason=f"Not old enough to join this server ({formattedDays} days old)")
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
		self.outdatedSave = True

	async def on_raw_reaction_add(self, m:nextcord.RawReactionActionEvent):
		# it works but my god the code for this is so hideous.
		def isVotingEmoji(e) -> bool:
			return any(str(e) == emoji for emoji in ['⬆️', '⬇️'])

		if not isVotingEmoji(m.emoji): # check if the emoji is what we want for CCC
			return

		cID = self.get_channel(m.channel_id)
		if not cID or not isinstance(cID, nextcord.TextChannel) or not cID.category_id or cID.category_id != 1208732034340487208:
			return # This shouldn't happen, it always exist and has all the metadata stuff

		mID = await cID.get_partial_message(m.message_id).fetch()
		if not mID or not isinstance(mID.channel, nextcord.TextChannel): # CCC
			return

		emojiDict = {str(emoji): emoji.count for emoji in mID.reactions if isVotingEmoji(emoji)}
		for emoji in ["⬆️", "⬇️"]: # fix a bug where if bot doesn't have a reaction it just throws keyerror
			if emoji not in emojiDict:
				await mID.add_reaction(emoji)
				emojiDict[emoji] = 1

		if emojiDict["⬆️"] >= 10 and emojiDict["⬇️"] == 1:
			author = mID.author
			if not isinstance(author, nextcord.Member):
				return

			await achievements.unlock(
				self, author, "Everyone Loves It", 
				"# Congratulations!!\n\n"
				f"Your [post]({mID.jump_url}) there was a massive success!\n\n"
				"Because your post didn't even get a single downvote, and has more than 10 upvotes, that means you now have gotten the `Everyone Loves It!!` role!\n\n"
				"Check your profile, it should be there now, and have fun with your new role!"
			)

	async def on_message(self, message:nextcord.Message):
		if message.author == self.user or not isinstance(message.channel, nextcord.TextChannel):
			return
		elif not message.guild and self.LOGS_CHANNEL: # not in account's folder but in a DM, so we send that to a channel
			files = [await file.to_file() for file in message.attachments]
			await self.LOGS_CHANNEL.send(f"{message.author.mention}: {message.content}", files=files)
			return

		userData = self.getDataFromMember(message.author)

		# Honeypot
		if message.channel.id == 1411421102558810223 and isinstance(message.author, nextcord.Member):
			userData.roleSave = [role.id for role in message.author.roles]
			self.outdatedSave = True
			await message.author.kick(reason="User intentionally got hacked, or actually just got hacked!! Should have changed your Password.")
			await self.tryDM(
				"## You've been HACKED!!\n\n"
				"Either you got this by getting yourself (intentionally) hacked or just too curious to go to a channel that's for a honeypot.\n\n"
				"If you *did* get hacked, CHANGE your password, ADD 2fa, UNAUTHORIZE anything suspicious in your account (`User Settings > Devices | Authorised Apps`)\n\n"
				"If you took all actions (or just became too curious), then you can join back this server: https://discord.gg/dsRUP9MAxY\n\n"
				"-# Oh and no, you're not banned.",
				message.author
			)
			await message.delete()
			return

		# Community Channel Checks
		if (message.attachments or message.snapshots) and \
			isinstance(message.channel.category, nextcord.CategoryChannel) and message.channel.category.id == 1208732034340487208:
			firstAttachment:nextcord.Attachment
			if message.attachments:
				firstAttachment = message.attachments[0]
			elif message.snapshots and message.snapshots[0].attachments: # forwarded message (which is called a snapshot, i guess)
				firstAttachment = message.snapshots[0].attachments[0]

			if firstAttachment and firstAttachment.content_type:
				nameContent = firstAttachment.content_type.split("/", 1)[0].lower()
				if any(nameContent == x for x in ["image", "video", "audio"]):
					await asyncio.sleep(1) # maybe wait a bit, for some reason it just doesn't give out the ⬆️ reaction and thinks the bot doesn't like that artwork
					for emoji in ['⬆️', '⬇️']:
						await message.add_reaction(emoji)
			return

		# Bot Commands (not using discord's / commands)
		if message.content and message.content[0] == ".":
			cmd = message.content[1:].split(" ", 1)[0]
			if cmd in commands.SELF:
				command = commands.SELF[cmd]
				timeLeft = userData.cmdTimestamp - time.time() + command.cooldown
				if timeLeft < 0:
					userData.cmdTimestamp = time.time()
					await command.asyncFunction(self=self, message=message)
					self.outdatedSave = True
				else:
					await message.reply(f"You are using this command way too quickly! Wait about `{round(timeLeft, 2)} seconds` to run this command again.")

if __name__ == "__main__":
	AccountBot(intents=nextcord.Intents.all()).run(argv[1])
