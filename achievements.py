import consts
import nextcord

class Achievement:
	def __init__(self, description:str, ishard:bool) -> None:
		self.description:str = description
		self.hard:bool = ishard

ROLES = {
	1473009251399110687: Achievement("Make a awesome post in #COMMUNITY and get 10 ⬆️ (if no one downvotes, bot excluded.)", False),
	1475909457270804653: Achievement("Get bombed over 5 times, exploded into oblivion.", False),
	1505569438618091520: Achievement("Get lucky and make someone get bombed 5 times in 1 command, Abracadaboom!", False),
	1534330974807130172: Achievement("Find out that messaging can randomly get you an achievement, somehow.", False),
	1558236812143755375: Achievement("Type the secret code in rBot's status to get this! It's complete random too!", False),
	1570122920380997713: Achievement("Be world famous with 25 ⬆️ on one post. Champion Star!", True)
}

async def unlock(user:nextcord.Member, achievementID:int, customString:str = ""):
	if (
		user.guild.id == consts.GUILD_ID and
		achievementID in ROLES and
		(role := user.guild.get_role(achievementID)) and
		role not in user.roles # forgot
	): 	
		from io import BytesIO
		files:list[nextcord.File] = []
		if ROLES[achievementID].hard:
			from PIL import Image, ImageDraw, ImageFont
			b = BytesIO()
			a = Image.open("asset/achievement.png")
			d = ImageDraw.Draw(a)
			t = ImageFont.truetype("asset/m.ttf", 80)
			_, _, w, _ = d.textbbox((0, 0), role.name, t)
			d.text(((1280 - w) / 2, 310), role.name, "black", t)
			a.save(b, format="PNG")
			files.append(nextcord.File(b.getvalue(), "you good.png", spoiler=True))

		try:
			await user.add_roles(role)
			await user.send(f"{customString}\n\n-# You have just unlocked the `{role.name}` achievement, which is displayed in Account's Folder on your Profile. Totally ***RADICAL***, right?", files=files)
		except:
			pass