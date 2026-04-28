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
	) -> None:
		self.description = description
		self.asyncFunction = asyncFunction
		self.cooldown = cooldown

CMDS:dict[str, Command] = {}

async def command_help(self:AccountBot, message:nextcord.Message):
	targetCommand = message.content[1:].split(" ", 2)
	if len(targetCommand) >= 2:
		cmd = targetCommand[1]
		if cmd in CMDS:
			with open(f"data/help/{cmd}.txt", "r") as f:
				await message.reply(f"# Detailed Help about the command `.{cmd}`:\n\n{f.read()}")
		else:
			await message.reply(f"Command `{cmd}` was not found in the database.")
		return

	toSend = "## Help Commands:\n"
	for name, commandData in CMDS.items():
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

	increment = 1
	while random.random() < 0.5:
		increment += 1

	targetUser = message.mentions[0] if message.mentions else message.author
	targetID = self.getDataFromMember(targetUser)
	targetID.bombed += increment

	sendMsg = "get bombed you bozo :joy:"
	if increment > 1:
		sendMsg = f"WOW! Mega BOMBED! user didn't explode not once but ***{increment} TIMES!*** {":joy:" * increment}"
	await message.channel.send(f"{targetUser.mention} {sendMsg}, user got bombed {targetID.bombed} times")

	if targetID.bombed >= 5 and isinstance(targetUser, nextcord.Member):
		await achievements.unlock(self, targetUser, "Bomber Enthusiastic")

async def command_achievements(self:AccountBot, message:nextcord.Message):
	if not (message.guild and message.author and isinstance(message.author, nextcord.Member)):
		return

	sender = "# ACHIEVEMENTS:\n"
	members = message.guild.member_count or 0
	for name, data in achievements.ROLES.items():
		role = message.guild.get_role(data.roleID)
		if role:
			totalWithRole = len(role.members)
			sender += "`{}`: {}{}\n-# **{}** of the users have this role.\n\n".format(
				name, data.description, " - ***You already have this role!***" if role in message.author.roles else "",
				f"{round((totalWithRole / members) * 100, 2)}% `{totalWithRole} / {members}`"
			)

	await message.reply(sender)

CMDS = {
	"help": Command(
		description="Shows the current Help Command.",
		asyncFunction=command_help
	),
	"bomb": Command(
		description="Bomb someone else `(@ping them)` or just yourself!",
		asyncFunction=command_bomb,
		cooldown=45
	),
	"achievements": Command(
		description="Shows stats of all the achievements with detail and such.",
		asyncFunction=command_achievements
	)
}
