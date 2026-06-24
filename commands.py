import os
import time
import heapq
import consts
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
				user.cmdTimestamp = time.time()
				return await func(self, i, *args, **kwargs)

			return await i.response.send_message(
				f"You are using this command way too quickly! Please wait about `{round(left, 2)} seconds` to run this command again, or wait until my message gets deleted automatically.",
				delete_after=left
			)
		return wrapper
	return decorator

class BotCommands(commands.Cog):
	def __init__(self, bot:AccountBot):
		self.bot = bot

	@nextcord.slash_command(description="Shows the current Help Command.", integration_types=[0, 1], contexts=[0, 1, 2])
	async def help(
		self,
		i:nextcord.Interaction,
		command:str = nextcord.SlashOption(
			description="The command to use from the choices.", 
			choices=os.listdir("data/help")
		)
	):
		with open(f"data/help/{command}", "r") as f:
			await i.response.send_message(f"# Detailed Help about the command `/{command}`:\n\n{f.read()}")

	@nextcord.slash_command(description="Bomb someone else or just yourself!", integration_types=[0, 1], contexts=[0, 1, 2])
	@cooldown(10)
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
		if leaderboard:
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

		funnies = {
			1: "WOW! Mega BOMBED! user did explode not once but ***{} TIMES!***",
			5: "TACTICAL NUKE!!! user exploded a GRAND TOTAL OF __***{} TIMES!***__"
		}

		sender = "get bombed you bozo"
		for condition, message in funnies.items():
			if increment >= condition:
				sender = message.format(increment)
			else:
				break

		user = member or i.user
		target = self.bot.getDataFromMember(user)
		target.bombed += increment

		await i.response.send_message(f"{user.mention} {sender} {':joy:' * increment}, user got bombed {target.bombed} times")
		if target.bombed >= 5:
			await achievement.unlock(self.bot, user, "Bomber Enthusiastic")
		if increment >= 5 and isinstance(i.user, nextcord.Member):
			await achievement.unlock(self.bot, i.user, "Well Donexplosion")

	@nextcord.slash_command(description="Shows stats of all the achievements with details and such.", guild_ids=[consts.GUILD_ID])
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

	@nextcord.slash_command(description="Shows information about this custom bot.", integration_types=[0, 1], contexts=[0, 1, 2])
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

	@nextcord.message_command("Warn AI Usage", guild_ids=[consts.GUILD_ID])
	async def warnAI(self, i:nextcord.Interaction, message:nextcord.Message):
		user = i.user
		if not (isinstance(user, nextcord.Member) and self.bot.LOGS_CHANNEL):
			return

		await self.bot.LOGS_CHANNEL.send(
			"## ⚠️ Potential Usage of AI Reported!\n"
			f"**Reporter**: {user.mention}\n"
			f"**Message Link**: {message.jump_url}\n"
			f"-# <@&{consts.MOD_ROLE}> <@&{consts.ADMIN_ROLE}>"
		)

		await message.reply(embed=nextcord.Embed(
			color=0xFF0040,
			title="Potential AI Use Found",
			description="An individual has reported this message for the usage of AI.\n"
						"This server has NO tolerance of any AI Generated Content (Rule 8) and has been alerted to staff.\n\n"
						"-# ***Repeated usage of AI will result in harsher punishments.***"
		))
	
		await i.response.send_message("Potential Reporting has been Logged.", ephemeral=True)

	@nextcord.message_command("Pin Message", guild_ids=[consts.GUILD_ID])
	async def pinMessage(self, i:nextcord.Interaction, message:nextcord.Message):
		try:
			assert i.channel and isinstance(i.user, nextcord.Member), "Not a valid channel or member"
			assert isinstance(i.channel, nextcord.Thread) and isinstance(i.channel.parent, nextcord.ForumChannel), "This command must be used inside a forum post"
			assert i.channel.category_id == consts.COMMUNITY_ID, "This command must be used in the #COMMUNITY channel"
			assert i.channel.owner_id == i.user.id, "You do not own this forum post"
		except AssertionError as asrt:
			return await i.response.send_message(f"{asrt}!", ephemeral=True)

		await (message.unpin if message.pinned else message.pin)()
		await i.response.send_message("Done.", ephemeral=True)

	@nextcord.message_command(guild_ids=[1126244249076244571])
	async def shutdown(self, i:nextcord.Interaction):
		self.bot.autoSave.cancel()
		await self.bot.autoSave()
		await i.response.send_message("Shutting down...")
		exit(0)