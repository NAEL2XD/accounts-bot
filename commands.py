import heapq
import random
import nextcord
import achievements as achievement
from bot import AccountBot

async def help(i:nextcord.Interaction, command:str):
	with open(f"data/help/{command}.txt", "r") as f:
		await i.response.send_message(f"# Detailed Help about the command `/{command}`:\n\n{f.read()}")

async def bomb(i:nextcord.Interaction, self:AccountBot, target:nextcord.Member, lb:bool):
	# maybe it should be on its own command
	if lb:
		sender = "## Bombed Rankings:\n"
		for rank, (userID, data) in enumerate(heapq.nlargest(10, self.USER_DATA.items(), key=lambda x: x[1].bombed)): # wtf
			user = self.get_user(userID)
			if user:
				sender += f"{rank + 1}. **`{user.name}`** with *`{data.bombed}`* bomb count.\n"
		await i.response.send_message(sender)
		return
	elif not target:
		await i.response.send_message("Cannot do task as user's field is null")
		return

	increment = 1
	while random.random() < 0.5:
		increment += 1

	targetID = self.getDataFromMember(target)
	targetID.bombed += increment

	sendMsg = "get bombed you bozo :joy:"
	if increment > 1:
		sendMsg = f"WOW! Mega BOMBED! user didn't explode not once but ***{increment} TIMES!*** {":joy:" * increment}"

	await i.response.send_message(f"{target.mention} {sendMsg}, user got bombed {targetID.bombed} times")
	if targetID.bombed >= 5 and isinstance(target, nextcord.Member):
		await achievement.unlock(self, target, "Bomber Enthusiastic")

async def achievements(i:nextcord.Interaction):
	if not (i.guild and i.user and isinstance(i.user, nextcord.Member)):
		return

	sender = "# ACHIEVEMENTS:\n"
	members = i.guild.member_count or 0
	for name, data in achievement.ROLES.items():
		role = i.guild.get_role(data.roleID)
		if role:
			totalWithRole = len(role.members)
			sender += "`{}`: {}{}\n-# **{}** of the users have this role.\n\n".format(
				name, data.description, " - ***You already have this role!***" if role in i.user.roles else "",
				f"{round((totalWithRole / members) * 100, 2)}% `{totalWithRole} / {members}`"
			)

	await i.response.send_message(sender)