import os
import sys
import json
import time
import utils
import shutil
import asyncio
import nextcord
from typing import Union
from nextcord.ext import tasks

if __name__ == "__main__":
	# circular import fix
	import commands
	import achievements

Member = Union[nextcord.User, nextcord.Member]

class UserData:
	def __init__(self, data:dict = {}):
		self.roleSave:list[int] = []
		self.bombed:int = 0
		self.cmdTimestamp:float = 0

		for key in self.__dict__.keys():
			if key in data and isinstance(data[key], type(self.__dict__[key])):
				self.__dict__[key] = data[key]

class AccountBot(nextcord.Client):
	USER_DATA:dict[int, UserData] = {}
	LOGS_CHANNEL:nextcord.TextChannel|None = None
	GIT_COMMIT_PENDING = False
	SAVE_OUTDATED = False
	LAST_ONLINE = 0.0
	CUR_COMMIT = ""

	# BOT UTILITIES
	def getDataFromMember(self, member:Member) -> UserData:
		if member.id not in self.USER_DATA:
			self.USER_DATA[member.id] = UserData()
		self.SAVE_OUTDATED = True
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

	# nice it works well
	# yea it ruins uptime but who the hell cares about it
	@tasks.loop(minutes=30)
	async def autoUpdate(self):
		commit = utils.getCommit()
		if any(commit == x for x in [self.CUR_COMMIT, ""]):
			return

		self.GIT_COMMIT_PENDING = True
		if os.path.exists(".tmp"):
			os.chdir(".tmp")
			os.system("git pull origin main")
			os.chdir("..")
		else:
			os.system("git clone https://github.com/NAEL2XD/accounts-bot.git .tmp")

		shutil.copytree(".tmp", os.getcwd(), dirs_exist_ok=True)
		with open("data/commit.txt", "w") as f:
			f.write(commit)

		self.SAVE_OUTDATED = True
		self.autoSave.cancel()
		await self.autoSave()

		if not os.path.exists("restart.sh"):
			with open("restart.sh", "w") as f:
				f.write(f'#!/bin/bash\nsleep 2\n~/env/bin/python bot.py "{sys.argv[1]}"')

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
		super().__init__(intents=intents)
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


		channel = self.get_guild(1036051546284249139)
		if not channel:
			return

		logs = channel.get_channel(1179015275065131069)
		if logs and isinstance(logs, nextcord.TextChannel):
			self.LOGS_CHANNEL = logs

	async def on_member_join(self, member:nextcord.Member):
		fourteenDays = 60 * 60 * 24 * 14
		ageInSeconds = time.time() - member.created_at.timestamp()
		if ageInSeconds < fourteenDays: # 2 weeks
			formattedDays = round(ageInSeconds / 86400, 1)
			await self.tryDM(
				f"Hey {member.name}, thanks for joining Account's Folder\n\n"
				"You're seeing this DM because your account is not old enough to join Account's Folder\n\n"
				f"Your account's creation is `{member.created_at.strftime("%d-%m-%Y %H:%M:%S")}` (`{formattedDays} days`), "
				"while Account's Folder requires all users to be more than 14 days old.\n\n"
				f"Wait about `{round((fourteenDays - ageInSeconds) / 86400, 1)} days` to be able to access this server again!\n\n"
				"-# p.s. If that time is up, you can rejoin this server (https://discord.gg/dsRUP9MAxY)\n"
				"-# Oh and DON'T FLOOD OUR LOGS!!!",
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

	async def on_raw_reaction_add(self, m:nextcord.RawReactionActionEvent):
		cID = self.get_channel(m.channel_id)
		if not cID or not isinstance(cID, nextcord.TextChannel) or not cID.category_id or cID.category_id != 1208732034340487208:
			return # This shouldn't happen, it always exist and has all the metadata stuff

		mID = await cID.fetch_message(m.message_id)
		if not mID or not isinstance(mID.channel, nextcord.TextChannel): # CCC
			return

		emojiDict = {str(emoji): emoji.count for emoji in mID.reactions if utils.isVotingEmoji(emoji) and emoji.me}
		for emoji in ["⬆️", "⬇️"]: # fix a bug where if bot doesn't have a reaction it just throws keyerror
			if emoji not in emojiDict:
				await mID.add_reaction(emoji)
				emojiDict[emoji] = 1

		if emojiDict["⬆️"] >= 10 and emojiDict["⬇️"] == 1:
			if isinstance(mID.author, nextcord.Member):
				await achievements.unlock(
					self, mID.author, "Everyone Loves It", 
					"# Congratulations!!\n\n"
					f"Your [post]({mID.jump_url}) there was a massive success!\n\n"
					"Because your post didn't even get a single downvote, and has more than 10 upvotes, that means you now have gotten the `Everyone Loves It!!` role!\n\n"
					"Check your profile, it should be there now, and have fun with your new role!"
				)

	async def on_message(self, message:nextcord.Message):
		if message.author == self.user or not isinstance(message.channel, nextcord.TextChannel) or self.GIT_COMMIT_PENDING:
			if isinstance(message.channel, nextcord.DMChannel) and self.LOGS_CHANNEL: # not in account's folder but in a DM, so we send that to a channel
				await self.LOGS_CHANNEL.send(f"From: {message.author.mention}:")
				await message.forward(self.LOGS_CHANNEL)
			return

		userData = self.getDataFromMember(message.author)

		# Honeypot
		if message.channel.id == 1411421102558810223 and isinstance(message.author, nextcord.Member):
			userData.roleSave = [role.id for role in message.author.roles]
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
			message.channel.category and isinstance(message.channel.category, nextcord.CategoryChannel) and message.channel.category.id == 1208732034340487208:
			firstAttachment:nextcord.Attachment
			if message.attachments:
				firstAttachment = message.attachments[0]
			elif message.snapshots and message.snapshots and message.snapshots[0].attachments:
				firstAttachment = message.snapshots[0].attachments[0]

			if firstAttachment and firstAttachment.content_type:
				nameContent = firstAttachment.content_type.split("/", 1)[0].lower()
				if nameContent in ["image", "video", "audio"]:
					await asyncio.sleep(0.25) # maybe wait a bit, for some reason it just doesn't give out the ⬆️ reaction and thinks the bot doesn't like that artwork
					for emoji in ['⬆️', '⬇️']:
						await message.add_reaction(emoji)
			return

		# Bot Commands (not using discord's / commands)
		if message.content and message.content[0] == ".":
			cmd = message.content[1:].split(" ", 1)[0]
			if cmd in commands.CMDS:
				command = commands.CMDS[cmd]
				timeLeft = userData.cmdTimestamp - time.time() + command.cooldown
				if timeLeft < 0:
					if command.cooldown != 0:
						userData.cmdTimestamp = time.time()
					await command.asyncFunction(self=self, message=message)
					return
				await message.reply(f"You are using this command way too quickly! Please wait about `{round(timeLeft, 2)} seconds` to run this command again.")

if __name__ == "__main__":
	AccountBot(intents=nextcord.Intents.all()).run(sys.argv[1])
