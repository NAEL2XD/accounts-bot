import consts
import nextcord
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from bot import AccountBot

class Achievement:
	def __init__(
		self,
		description:str,
		roleID:int
	):
		self.description = description
		self.roleID = roleID

ROLES = {
	"Everyone Loves It":   Achievement("Make a awesome post in #COMMUNITY and get 10 ⬆️ (if no one downvotes, bot excluded.)", 1473009251399110687),
	"Bomber Enthusiastic": Achievement("Get bombed over 5 times, exploded into oblivion.",                                     1475909457270804653),
	"Well Donexplosion":   Achievement("Get lucky and make someone get bombed 5 times in 1 command, Abracadaboom!",            1505569438618091520),
	"You did it!":         Achievement("Find out that messaging can randomly get you an achievement, somehow.",                1534330974807130172),
	"Status Witch Hunt":   Achievement("Type the secret code in rBot's status to get this! It's complete random too!",         1558236812143755375)
}

async def unlock(self:"AccountBot", user:nextcord.Member, achievement:str, customString:str = ""):
	if (
		(g := self.get_guild(consts.GUILD_ID)) and
		achievement in ROLES and
		(rID := ROLES[achievement].roleID) and
		(role := g.get_role(rID))
	): 	
		await user.add_roles(role)
		await self.tryDM(
			f"{customString}\n\n-# You have just unlocked the `{achievement}` achievement, which is displayed in Account's Folder on your Profile. Totally ***RADICAL***, right?",
			user
		)