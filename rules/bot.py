import os
import datetime
import nextcord
from sys import argv

class AccountBot(nextcord.Client):
	async def on_ready(self):
		print(f'Revamping rules')

		RULES = self.get_channel(1179013461133508689)
		if not isinstance(RULES, nextcord.TextChannel):
			exit(1)

		async for message in RULES.history():
			await message.delete()

		await RULES.send(f"# *Welcome to Account's Folder!*\nNo time to introduce, here is the rules, hope you follow them.\n\n`{"-" * 40}`")

		ruleCount = 1
		while True:
			rule = f"rule{ruleCount}"
			if os.path.exists(rule):
				with open(rule, "r") as f:
					await RULES.send(f"# {ruleCount}. {f.read()}\n# `{"=" * 22}`")
				ruleCount += 1
			else:
				break

		await RULES.send(
			"This *has* warnings threshold, this is the punishments you'll get if you accumulate too many warnings:\n\n"
			"***Warning 1***: Verbal Warning, just a \"Don't do it again\".\n"
			"***Warning 2***: 24-hour mute.\n"
			"***Warning 3***: 7-day ban.\n"
			"***Warning 4***: Perma-ban with appeal.\n"
			"***Warning 5***: Perma-ban without appeal.\n\n"
		)
		await RULES.send(f"# *Permanent Invite Link*\nhttps://discord.gg/dsRUP9MAxY\n\n-# Last Updated: {datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")} (`DD-MM-YYYY HH:MM:SS`) at UTC+1")
		await self.close()
		print("Done")

if __name__ == "__main__":
	AccountBot(intents=nextcord.Intents.all()).run(argv[1])
