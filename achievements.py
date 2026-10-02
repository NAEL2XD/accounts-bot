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
	"You did it!":         Achievement("Find out that messaging can randomly get you an achievement, somehow.",                1534330974807130172)
}

async def unlock(self:"AccountBot", user:nextcord.Member, achievement:str, customString:str = ""):
	g = self.get_guild(consts.GUILD_ID)
	if not g or g.get_member(user.id) is None: # silently ignore if they're not on server
		return

	if not customString:
		customString = f"Congratulations, You have gotten a new achievement: `{achievement}`\n\nYour role should be added in your profile, Hope you have fun!"

	if achievement in ROLES:
		rID = ROLES[achievement].roleID
		role = user.guild.get_role(rID)
		if not user.get_role(rID) and role:
			await user.add_roles(role)
			await self.tryDM(customString, user)