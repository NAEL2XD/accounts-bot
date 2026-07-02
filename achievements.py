import consts
from bot import nextcord, AccountBot

class Achievement:
	def __init__(
		self,
		description:str,
		roleID:int
	):
		self.description = description
		self.roleID = roleID

ROLES = {
	"Everyone Loves It": Achievement(
		"Get 10 ⬆️ without someone ⬇️ing your post in #COMMUNITY",
		consts.ELI_ROLE
	),
	"Bomber Enthusiastic": Achievement(
		"Get bombed over 5 times, exploded into oblivion.",
		consts.BE_ROLE
	),
	"Well Donexplosion": Achievement(
		"Get lucky and make someone get bombed 5 times in 1 command, Abracadaboom!",
		consts.WDP_ROLE
	)
}

async def unlock(self:AccountBot, user:nextcord.Member, achievement:str, customString:str = ""):
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