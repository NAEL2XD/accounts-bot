import os
import time
import heapq
import random
import nextcord
import achievements as achievement
from bot import AccountBot
from functools import wraps
from nextcord.ext import commands

def cooldown(seconds:float):
	def decorator(func):
		@wraps(func)
		async def wrapper(self:'BotCommands', i:nextcord.Interaction, *args, **kwargs):
			if not i.user:
				return

			user = self.bot.getDataFromMember(i.user)
			left = user.cmdTimestamp - time.time() + seconds
			if left < 0:
				if seconds != 0:
					user.cmdTimestamp = time.time()
				return await func(self=self, i=i, *args, **kwargs)

			return await i.response.send_message(
				f"You are using this command way too quickly! Please wait about `{round(left, 2)} seconds` to run this command again, or wait until my message gets deleted automatically.",
				delete_after=left
			)
		return wrapper
	return decorator

class BotCommands(commands.Cog):
	def __init__(self, bot:AccountBot):
		self.bot = bot

	@nextcord.slash_command(description="Shows the current Help Command.")
	async def help(
		self,
		i:nextcord.Interaction,
		command:str = nextcord.SlashOption(
			description="The command to use from the choices.", 
			choices=["help", "bomb", "achievements"]
		)
	):
		with open(f"data/help/{command}.txt", "r") as f:
			await i.response.send_message(f"# Detailed Help about the command `/{command}`:\n\n{f.read()}")

	@nextcord.slash_command(description="Bomb someone else or just yourself!")
	@cooldown(30)
	async def bomb(
		self,
		i:nextcord.Interaction,
		member:nextcord.Member = nextcord.SlashOption(
			description="User to target and bomb, null to bomb yourself.", 
			required=False
		),
		leaderboard:bool = nextcord.SlashOption(
			description="Optional field if you wanna see the leaderboard", 
			required=False
		)
	):
		if i.user and leaderboard:
			self.bot.getDataFromMember(i.user).cmdTimestamp = 0

			sender = "## Bombed Rankings:\n"
			for rank, (user_id, data) in enumerate(heapq.nlargest(10, self.bot.USER_DATA.items(), key=lambda x: x[1].bombed)):
				user = self.bot.get_user(user_id)
				if user:
					sender += f"{rank + 1}. **`{user.name}`** with *`{data.bombed}`* bomb count.\n"

			await i.response.send_message(sender)
			return

		increment = 1
		while random.random() < 0.5:
			increment += 1

		sender = "get bombed you bozo :joy:"
		if increment > 1:
			sender = f"WOW! Mega BOMBED! user didn't explode not once but ***{increment} TIMES!*** {':joy:' * increment}"

		user = member or i.user
		target = self.bot.getDataFromMember(user)
		target.bombed += increment

		await i.response.send_message(f"{user.mention} {sender}, user got bombed {target.bombed} times")
		if target.bombed >= 5:
			await achievement.unlock(self.bot, user, "Bomber Enthusiastic")

	@nextcord.slash_command(description="Shows stats of all the achievements with details and such.")
	async def achievements(self, i:nextcord.Interaction):
		if not (i.guild and isinstance(i.user, nextcord.Member)):
			return

		sender = "# ACHIEVEMENTS:\n"
		members = i.guild.member_count or 1
		for name, data in achievement.ROLES.items():
			role = i.guild.get_role(data.roleID)
			if role:
				totalWithRole = len(role.members)
				sender += "`{}`: {}{}\n-# **{}** of the users have this role.\n\n".format(
					name, data.description, " - ***You already have this role!***" if role in i.user.roles else "",
					f"{round((totalWithRole / members) * 100, 2)}% `{totalWithRole} / {members}`"
				)

		await i.response.send_message(sender)

	@nextcord.slash_command(description="Shows information about this custom bot.")
	async def about(self, i:nextcord.Interaction):
		commit = "?"
		if os.path.exists("data/commit.txt"):
			with open("data/commit.txt", "r") as f:
				commit = f.read()[:8]

		await i.response.send_message(embed=nextcord.Embed(
			color=0x674CE4,
			title=f"*`Account's rBot`* (Commit {commit})",
			description=
				"Account's rBot is a custom bot programmed for this server only. It provides utilities, moderation, and much more.\n"
				"[*Source Code*](https://github.com/NAEL2XD/accounts-bot) • [*Made by Nael2xd*](<https://discord.com/users/786639413282209802>)",
		))