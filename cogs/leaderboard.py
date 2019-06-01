"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import discord, json, asyncio
from discord.ext import commands
import config.guild as guild

class Leaderboard(commands.Cog):
	
	def __init__(self, client):
		self.client=client
	
	def post(self, page, embed1, embed2, embed3):
		if page == 1:
			return embed1
		if page == 2:
			return embed2
		if page == 3:
			return embed3
		if page > 3:
			page=1
			return embed1
		if page < 1:
			page=3
			return embed3

	@commands.command(aliases=["lb"])
	async def leaderboard(self, ctx, *args):
		with open("../data/users.json","r") as f:
			users=json.load(f)
		
		try: 	
			if args[0].upper() == "SSR":
				await self.leaderboard_post_ssr(users, ctx)
			elif args[0] == "medal" or args[0] == "medals":
				await self.leaderboard_post_medals(users, ctx)
			elif args[0] == "amulet" or args[0] == "amulets":
				await self.leaderboard_post_amulet(users, ctx)
			elif args[0] == "friendship" or args[0] == "fp":
				await self.leaderboardFriendship(users, ctx)
			elif args[0] == "ship" or args[0] == "ships":
				await self.leaderboardShip(ctx)
			
			else:
				await self.leaderboard_post_level(users, ctx)
				
		# At any argument, return the Level Leaderboard
		except IndexError as error:
			await self.leaderboard_post_level(users, ctx)

	async def leaderboard_post_ssr(self, users, ctx):
		ssrBoard1=[]

		for user in users:
			ssrBoard1.append((self.client.get_user(int(user)).name, users[user]["SSR"]))

		ssrBoard2=sorted(ssrBoard1, key=lambda x: x[1], reverse=True)

		description1=""
		description2=""
		description3=""

		for user in ssrBoard2[0:10]:
			description1 += ":small_orange_diamond:{}, x{}\n".format(user[0], user[1])
		for user in ssrBoard2[10:20]:
			description2 += ":small_orange_diamond:{}, x{}\n".format(user[0], user[1])
		for user in ssrBoard2[20:30]:
			description3 += ":small_orange_diamond:{}, x{}\n".format(user[0], user[1])
		
		title =":trophy: SSR LeaderBoard"
		
		embed1=discord.Embed(color=0xffff80, title=title, description=description1)
		embed1.set_footer(text="page 1")
		
		embed2=discord.Embed(color=0xffff80, title=title, description=description2)
		embed2.set_footer(text="page 2")
		
		embed3=discord.Embed(color=0xffff80, title=title, description=description3)
		embed3.set_footer(text="page 3")
		
		msg=await ctx.channel.send(embed=embed1)
		
		await msg.add_reaction("⬅")
		await msg.add_reaction("➡")
		
		def check(reaction, user):
			return user != self.client.user and reaction.message.id == msg.id
		
		# Embed pagination max 3 pages
		page=1
		while True:
			try:
				timeSec=10
				reaction, user=await self.client.wait_for("reaction_add", timeout=timeSec, check=check)
				if str(reaction.emoji) == "➡":
					page += 1
				if str(reaction.emoji) == "⬅":
					page -= 1
				await msg.edit(embed=self.post(page, embed1, embed2, embed3))
				timeSec=timeSec - 1
			except asyncio.TimeoutError:
				return False
				
	async def leaderboard_post_medals(self, users, ctx):
		medalsBoard1=[]

		for user in users:
			medalsBoard1.append((self.client.get_user(int(user)).name, users[user]["medals"]))

		medalsBoard2=sorted(medalsBoard1, key=lambda x: x[1], reverse=True)

		description1=""
		description2=""
		description3=""

		for user in medalsBoard2[0:10]:
			description1 += ":small_orange_diamond:{}, x{}\n".format(user[0], user[1])
		for user in medalsBoard2[10:20]:
			description2 += ":small_orange_diamond:{}, x{}\n".format(user[0], user[1])
		for user in medalsBoard2[20:30]:
			description3 += ":small_orange_diamond:{}, x{}\n".format(user[0], user[1])
		
		title="{} Medal LeaderBoard".format(guild.eMedal)
		
		embed1=discord.Embed(color=0xffff80, title=title, description=description1)
		embed1.set_footer(text="page 1")
		
		embed2=discord.Embed(color=0xffff80, title=title, description=description2)
		embed2.set_footer(text="page 2")
		
		embed3=discord.Embed(color=0xffff80, title=title, description=description3)
		embed3.set_footer(text="page 3")
		
		msg=await ctx.channel.send(embed=embed1)
		
		await msg.add_reaction("⬅")
		await msg.add_reaction("➡")
		
		def check(reaction, user):
			return user != self.client.user and reaction.message.id == msg.id
		
		# Embed pagination max 3 pages
		page=1
		while True:
			try:
				timeout=10
				reaction, user=await self.client.wait_for("reaction_add", timeout=timeout, check=check)
				if str(reaction.emoji) == "➡":
					page += 1
				if str(reaction.emoji) == "⬅":
					page -= 1
				await msg.edit(embed=self.post(page, embed1, embed2, embed3))
				timeout=timeout - 1
			except asyncio.TimeoutError:
				return False
	
	async def leaderboard_post_level(self, users, ctx):
		levelBoard1=[]

		for user in users:
			levelBoard1.append((self.client.get_user(int(user)).name, users[user]["level"]))

		levelBoard2=sorted(levelBoard1, key=lambda x: x[1], reverse=True)

		description1=""
		description2=""
		description3=""

		for user in levelBoard2[0:10]:
			description1 += ":small_orange_diamond:{}, x{}\n".format(user[0], user[1])
		for user in levelBoard2[10:20]:
			description2 += ":small_orange_diamond:{}, x{}\n".format(user[0], user[1])
		for user in levelBoard2[20:30]:
			description3 += ":small_orange_diamond:{}, x{}\n".format(user[0], user[1])
		
		title=":arrow_heading_up: Level LeaderBoard"
		
		embed1=discord.Embed(color=0xffff80, title=title, description=description1)
		embed1.set_footer(text="page 1")
		
		embed2=discord.Embed(color=0xffff80, title=title, description=description2)
		embed2.set_footer(text="page 2")
		
		embed3=discord.Embed(color=0xffff80, title=title, description=description3)
		embed3.set_footer(text="page 3")
		
		msg=await ctx.channel.send(embed=embed1)
		
		await msg.add_reaction("⬅")
		await msg.add_reaction("➡")
		
		def check(reaction, user):
			return user != self.client.user and reaction.message.id == msg.id
		
		# Embed pagination max 3 pages
		page=1
		while True:
			try:
				timeout=10
				reaction, user=await self.client.wait_for("reaction_add", timeout=timeout, check=check)
				if str(reaction.emoji) == "➡":
					page += 1
				if str(reaction.emoji) == "⬅":
					page -= 1
				await msg.edit(embed=self.post(page, embed1, embed2, embed3))
				timeout=timeout - 1
			except asyncio.TimeoutError:
				return False
	async def leaderboard_post_amulet(self, users, ctx):
		amuletBoard1=[]

		for user in users:
			amuletBoard1.append((self.client.get_user(int(user)).name, users[user]["amulets_spent"]))

		amuletBoard2=sorted(amuletBoard1, key=lambda x: x[1], reverse=True)

		description1=""
		description2=""
		description3=""

		for user in amuletBoard2[0:10]:
			description1 += ":small_orange_diamond:{}, x{}\n".format(user[0], user[1])
		for user in amuletBoard2[10:20]:
			description2 += ":small_orange_diamond:{}, x{}\n".format(user[0], user[1])
		for user in amuletBoard2[20:30]:
			description3 += ":small_orange_diamond:{}, x{}\n".format(user[0], user[1])
		
		title="{} Spender LeaderBoard".format(guild.eAmulet)
		
		embed1=discord.Embed(color=0xffff80, title=title, description=description1)
		embed1.set_footer(text="page 1")
		
		embed2=discord.Embed(color=0xffff80, title=title, description=description2)
		embed2.set_footer(text="page 2")
		
		embed3=discord.Embed(color=0xffff80, title=title, description=description3)
		embed3.set_footer(text="page 3")
		
		msg=await ctx.channel.send(embed=embed1)
		
		await msg.add_reaction("⬅")
		await msg.add_reaction("➡")
		
		def check(reaction, user):
			return user != self.client.user and reaction.message.id == msg.id
		
		# Embed pagination max 3 pages
		page=1
		while True:
			try:
				timeout=10
				reaction, user=await self.client.wait_for("reaction_add", timeout=timeout, check=check)
				if str(reaction.emoji) == "➡":
					page += 1
				if str(reaction.emoji) == "⬅":
					page -= 1
				await msg.edit(embed=self.post(page, embed1, embed2, embed3))
				timeout=timeout - 1
			except asyncio.TimeoutError:
				return False
	
	async def leaderboardFriendship(self, users, ctx):
		fpBoard1=[]

		for user in users:
			fpBoard1.append((self.client.get_user(int(user)).name, users[user]["friendship"]))

		fpBoard2=sorted(fpBoard1, key=lambda x: x[1], reverse=True)

		description1=""
		description2=""
		description3=""

		for user in fpBoard2[0:10]:
			description1 += ":small_orange_diamond:{}, x{}\n".format(user[0], user[1])
		for user in fpBoard2[10:20]:
			description2 += ":small_orange_diamond:{}, x{}\n".format(user[0], user[1])
		for user in fpBoard2[20:30]:
			description3 += ":small_orange_diamond:{}, x{}\n".format(user[0], user[1])
		
		title="{} Friendship LeaderBoard".format(guild.eFship)
		
		embed1=discord.Embed(color=0xffff80, title=title, description=description1)
		embed1.set_footer(text="page 1")
		
		embed2=discord.Embed(color=0xffff80, title=title, description=description2)
		embed2.set_footer(text="page 2")
		
		embed3=discord.Embed(color=0xffff80, title=title, description=description3)
		embed3.set_footer(text="page 3")
		
		msg=await ctx.channel.send(embed=embed1)
		
		await msg.add_reaction("⬅")
		await msg.add_reaction("➡")
		
		def check(reaction, user):
			return user != self.client.user and reaction.message.id == msg.id
		
		# Embed pagination max 3 pages
		page=1
		while True:
			try:
				timeout=10
				reaction, user=await self.client.wait_for("reaction_add", timeout=timeout, check=check)
				if str(reaction.emoji) == "➡":
					page += 1
				if str(reaction.emoji) == "⬅":
					page -= 1
				await msg.edit(embed=self.post(page, embed1, embed2, embed3))
				timeout=timeout - 1
			except asyncio.TimeoutError:
				return False
	
	async def leaderboardShip(self, ctx):
		with open("../data/friendship.json", "r") as f:
			friendship=json.load(f)
		
		shipsBoard1=[]

		for ship in friendship:
			shipsBoard1.append((friendship[ship]["ship_name"], friendship[ship]["shipper1"], friendship[ship]["shipper2"], friendship[ship]["level"], friendship[ship]["points"]))

		shipsBoard2=sorted(shipsBoard1, key=lambda x: x[4], reverse=True)

		description1=""
		description2=""
		description3=""

		for ship in shipsBoard2[0:10]:
			description1 += ":small_orange_diamond:{}, x{}{}\n".format(ship[0], ship[4], guild.eFship)
		for ship in shipsBoard2[10:20]:
			description2 += ":small_orange_diamond:{}, x{}{}\n".format(ship[0], ship[4], guild.eFship)
		for ship in shipsBoard2[20:30]:
			description3 += ":small_orange_diamond:{}, x{}{}\n".format(ship[0], ship[4], guild.eFship)
		
		title=":ship: Ships LeaderBoard"
		
		embed1=discord.Embed(color=0xffff80, title=title, description=description1)
		embed1.set_footer(text="page 1")
		
		embed2=discord.Embed(color=0xffff80, title=title, description=description2)
		embed2.set_footer(text="page 2")
		
		embed3=discord.Embed(color=0xffff80, title=title, description=description3)
		embed3.set_footer(text="page 3")
		
		msg=await ctx.channel.send(embed=embed1)
		
		await msg.add_reaction("⬅")
		await msg.add_reaction("➡")
		
		def check(reaction, user):
			return user != self.client.user and reaction.message.id == msg.id
		
		# Embed pagination max 3 pages
		page=1
		while True:
			try:
				timeout=10
				reaction, user=await self.client.wait_for("reaction_add", timeout=timeout, check=check)
				if str(reaction.emoji) == "➡":
					page += 1
				if str(reaction.emoji) == "⬅":
					page -= 1
				await msg.edit(embed=self.post(page, embed1, embed2, embed3))
				timeout=timeout - 1
			except asyncio.TimeoutError:
				return False
	
def setup(client):
	client.add_cog(Leaderboard(client))