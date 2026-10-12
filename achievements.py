import consts
import nextcord
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from bot import AccountBot


ROLES = {
	1473009251399110687: "Make a awesome post in #COMMUNITY and get 10 ⬆️ (if no one downvotes, bot excluded.)",
	1475909457270804653: "Get bombed over 5 times, exploded into oblivion.",
	1505569438618091520: "Get lucky and make someone get bombed 5 times in 1 command, Abracadaboom!",
	1534330974807130172: "Find out that messaging can randomly get you an achievement, somehow.",
	1558236812143755375: "Type the secret code in rBot's status to get this! It's complete random too!"
}

async def unlock(self:"AccountBot", user:nextcord.Member, achievementID:int, customString:str = ""):
	if (
		user.guild.id == consts.GUILD_ID and
		achievementID in ROLES and
		(role := user.guild.get_role(achievementID)) and
		role not in user.roles # forgot
	): 	
		await user.add_roles(role)
		await self.tryDM(f"{customString}\n\n-# You have just unlocked the `{role.name}` achievement, which is displayed in Account's Folder on your Profile. Totally ***RADICAL***, right?", user)