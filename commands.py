from bot import *
import heapq
import random
import achievements

class Command:
	def __init__(
		self,
		description:str,
		asyncFunction,
		cooldown:float = 0,
		dontUpdateTimestamp:bool = False
	) -> None:
		self.description = description
		self.asyncFunction = asyncFunction
		self.cooldown = cooldown
		self.dontUpdateTimestamp = dontUpdateTimestamp

SELF:dict[str, Command] = {}

async def command_help(self:AccountBot, message:nextcord.Message):
	targetCommand = message.content[1:].split(" ", 2)
	if len(targetCommand) >= 2:
		cmd = targetCommand[1]
		if cmd in SELF:
			with open(f"data/help/{cmd}.txt", "r") as f:
				await message.reply(f"# Detailed Help about the command `.{cmd}`:\n\n{f.read()}")
		else:
			await message.reply(f"Command `{cmd}` was not found in the database.")
		return

	toSend = "## Help Commands:\n"
	for name, commandData in SELF.items():
		toSend += "`.{}`: *{}*{}\n".format(
			name,
			commandData.description,
			f" - ***This Command has a Cooldown of {commandData.cooldown} seconds***" if commandData.cooldown != 0 else ""
		)
	toSend += f"\n-# Tip: For a detailed explanation, type `.help (command)`."
	await message.reply(toSend)

async def command_bomb(self:AccountBot, message:nextcord.Message):
	# maybe it should be on its own command
	s = message.content.split(" ", 1)
	if len(s) > 1 and s[1] in ["lb", "leaderboard"]:
		self.getDataFromMember(message.author).cmdTimestamp = 0 # reset the timestamp

		sender = "## Bombed Rankings:\n"
		for rank, (userID, data) in enumerate(heapq.nlargest(10, self.USER_DATA.items(), key=lambda x: x[1].bombed)): # wtf
			user = self.get_user(userID)
			if user:
				sender += f"{rank + 1}. **`{user.name}`** with *`{data.bombed}`* bomb count.\n"
		await message.reply(sender)
		return

	targetUser = message.mentions[0] if message.mentions else message.author

	increment = 1
	while random.random() < 0.4:
		increment += 1

	targetID = self.getDataFromMember(targetUser)
	targetID.bombed += increment
	if targetID.bombed >= 5 and isinstance(targetUser, nextcord.Member):
		await achievements.unlock(self, targetUser, "Bomber Enthusiastic")

	sendMsg = f"get bombed you bozo :joy:"
	if increment > 1:
		sendMsg = f"WOW! Mega BOMBED! user didn't explode not 1 but ***{increment} TIMES!*** {":joy:" * increment}"
	await message.channel.send(f"{targetUser.mention} {sendMsg}, user got bombed {targetID.bombed} times")

async def command_achievements(self:AccountBot, message:nextcord.Message):
	if not (message.guild and message.author and isinstance(message.author, nextcord.Member)):
		return

	sender = "# ACHIEVEMENTS:\n"
	members = message.guild.member_count
	for name, data in achievements.SELF.items():
		role = message.guild.get_role(data.roleID)
		if not role:
			continue

		totalWithRole = len(role.members)
		if members:
			sender += "`{}`: {}{}\n-# **{}** of the users have this role.\n\n".format(
				name, data.description, " - ***You already have this role!***" if role in message.author.roles else "",
				f"{round((totalWithRole / members) * 100, 2)}% `{totalWithRole} / {members}`"
			)

	await message.reply(sender)

async def command_cmStats(self:AccountBot, message:nextcord.Message):
	targetID = self.getDataFromMember(message.author)
	if not targetID.communityReactions:
		await message.reply("You haven't gotten any stats on #COMMUNITY, try getting someone to vote you.")

	page = 1
	split = message.content.split(" ", 2)
	if len(split) > 1 and split[1].isdigit():
		page = int(split[1])

	if page < 1:
		await message.reply("Going out of bounds, aren't you?")

	m = await message.channel.send("Please wait, this may take a while...")

	sender = f"## Viewing Page {page} of {int(len(targetID.communityReactions) / 5) + 1}\n"
	offset = 0
	finallyProcessed = False
	for i, (messageID, communityID) in enumerate(heapq.nlargest((page + 1) * 5, targetID.communityReactions.items(), key=lambda x: x[0])):
		if i - offset < (page - 1) * 5:
			continue

		channel = self.get_channel(communityID)
		if not (channel and isinstance(channel, nextcord.TextChannel)):
			continue

		cm:nextcord.Message
		try:
			cm = await channel.fetch_message(messageID)
		except nextcord.NotFound:
			offset += 1
			continue
		finallyProcessed = True
		emojiDict = {str(emoji): emoji.count for emoji in cm.reactions if utils.isVotingEmoji(emoji)}
		total = emojiDict.get("⬆️", 0) - emojiDict.get("⬇️", 0)

		emoji = "⬆️"
		if total > 9:
			emoji = "⭐"
		elif total == 0:
			emoji = "❓"
		elif total < -9:
			emoji = "😂"
		elif total < 0:
			emoji = "⬇️"

		sender += f"{i+1}. `{emoji} {total}` - [This Post.]({cm.jump_url})\n"

	if not finallyProcessed:
		sender += "Yeah right, what were you trying to see in a page that does not exist exactly?"
	elif offset != 0:
		sender += f"-# {offset} of your message(s) were not found and was skipped."

	await m.delete()
	await message.reply(sender)

SELF = {
	"help": Command(
		description="Shows the current Help Command.",
		asyncFunction=command_help,
		dontUpdateTimestamp=True
	),
	"bomb": Command(
		description="Bomb someone else `(@ping them)` or just yourself!",
		asyncFunction=command_bomb,
		cooldown=60 # 1 minute
	),
	"achievements": Command(
		description="Shows stats of all the achievements with detail and such.",
		asyncFunction=command_achievements,
		dontUpdateTimestamp=True
	),
	"cmStats": Command(
		description="Fetches your current stats from #COMMUNITY posted artwork.",
		asyncFunction=command_cmStats,
		dontUpdateTimestamp=True
	)
}