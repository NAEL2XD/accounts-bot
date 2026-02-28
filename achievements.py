from bot import *

class Achievements:
	def __init__(
		self,
		description:str,
		roleID:int
	) -> None:
		self.description = description
		self.roleID = roleID

SELF = {
	"Everyone Loves It": Achievements(
		description="Get 10 ⬆️ without someone ⬇️ing your post in #COMMUNITY",
		roleID=1473009251399110687
	),
	"Bomber Enthusiastic": Achievements(
		description="Get bombed over 50 times, exploded into oblivion.",
		roleID=1475909457270804653
	)
}

async def unlock(self:AccountBot, user:nextcord.Member, achievement:str, customString:str = ""):
	if not customString:
		customString = f"Congratulations, You have gotten a new achievement: `{achievement}`\n\nYour role should be added in your profile, Hope you have fun!"

	if achievement in SELF:
		rID = SELF[achievement].roleID
		role = user.guild.get_role(rID)
		if not user.get_role(rID) and role:
			await user.add_roles(role)
			await self.tryDM(customString, user)