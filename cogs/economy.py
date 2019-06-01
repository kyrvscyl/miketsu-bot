"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import discord, json, asyncio
from discord.ext import commands
from config.guild import eJade, eAmulet, eMedal, eCoin, eFship

class Economy(commands.Cog):
	
	def __init__(self, client):
		self.client = client

	@commands.command(aliases=["dailies"])
	async def daily(self, ctx):
		with open("../data/daily.json", "r") as f:
			users = json.load(f)
			
		await self.dailyConfirm(users, ctx.author, ctx)
		
		with open("../data/daily.json", "w") as f:
			json.dump(users, f, indent="\t")
			
	async def dailyConfirm(self, users, user, ctx):
		if not str(user.id) in users["daily"]:
			users["daily"][str(user.id)] = {}
			users["daily"][str(user.id)]["encounter_pass"] = 4
			users["daily"][str(user.id)]["friendship_pass"] = 3
			
			embed = discord.Embed(color = 0xffff80, title = ":gift: Daily Rewards", 
				description = "A box containing 50{}, 10,000{}, 3:tickets:, & 4:ticket:".format(eJade, eCoin, eFship))
			embed.set_footer(text = "Claimed by {}".format(user.name), icon_url=user.avatar_url)
				
			await self.dailyAdd(users, ctx.author)
			await ctx.channel.send(embed=embed)
		else: 
			msg = "You have collected already today. Resets at 00:00 EST"
			await ctx.channel.send(msg)

	async def dailyAdd(self, users, user):
		with open("../data/users.json", "r") as f:
			users = json.load(f)
			
			if str(user.id) in users:
				users[str(user.id)]["jades"] += 50
				users[str(user.id)]["coins"] += 10000
				
				if users[str(user.id)]["realm_ticket"] < 27:
					users[str(user.id)]["realm_ticket"] += 3
				else:
					users[str(user.id)]["realm_ticket"] = 30

				with open("../data/users.json", "w") as f:
					json.dump(users, f, indent="\t")
		

	@commands.command()
	async def weekly(self, ctx):
		with open("../data/daily.json", "r") as f:
			users = json.load(f)
			
		await self.weeklyConfirm(users, ctx.author, ctx)
		
		with open("../data/daily.json", "w") as f:
			json.dump(users, f, indent="\t")

	async def weeklyConfirm(self, users, user, ctx):
		if not str(user.id) in users["weekly"]:
			users["weekly"][str(user.id)] = {}
			
			embed = discord.Embed(color = 0xffff80, title = ":gift: Weekly Rewards", 
				description = "A mythical box containing 750{}, 100,000{}, and 1{}".format(eJade, eCoin, eAmulet))
			embed.set_footer(text = "Claimed by {}".format(user.name), icon_url = user.avatar_url)
				
			await self.weeklyAdd(users, ctx.author)
			await ctx.channel.send(embed=embed)
		else: 
			msg = "You have collected already this week. Resets at 00:00 EST Monday"
			await ctx.channel.send(msg)

	async def weeklyAdd(self, users, user):
		with open("../data/users.json", "r") as f:
			users = json.load(f)
			
			if str(user.id) in users:
				users[str(user.id)]["jades"] += 750
				users[str(user.id)]["coins"] += 100000
				users[str(user.id)]["amulets"] += 1
			else: return
			
		with open("../data/users.json", "w") as f:
			json.dump(users, f, indent="\t")
	
	@commands.command(aliases=["compensate"])
	async def compensation(self, ctx):
		requestor = ctx.author.id
		with open("../data/compensation.json", "r") as f:
			compensation = json.load(f)
		
		if str(requestor) not in compensation :
			msg = "{}, you are not eligible for this compensation".format(ctx.author.mention)
			await ctx.channel.send(msg)
		
		if str(requestor) in compensation:
		
			if compensation[str(requestor)] == "unclaimed" :
				with open("../data/users.json", "r") as f:
					users = json.load(f)
				
				users[str(requestor)]["jades"] += 3000
				
				with open("../data/users.json", "w") as f:
					json.dump(users, f, indent="\t")
					
				with open("../data/compensation.json", "r") as f:
					compensation = json.load(f)
				
				compensation[str(requestor)] = "claimed"
				
				with open("../data/compensation.json", "w") as f:
					json.dump(compensation, f, indent="\t")
					
				msg = "You have been compensated with 3000{} due to recent data roll back.".format(eJade)
				await ctx.channel.send(msg)	
				
			elif compensation[str(requestor)] == "claimed" :
				msg = "{}, you can only claim this once!".format(ctx.author.mention)
				await ctx.channel.send(msg)
	
	@commands.command(aliases=["p"])
	async def profile(self, ctx, user: discord.User=None):
		with open("../data/users.json","r") as f:
				users = json.load(f)	
		if user == None:
			await self.profilePost(users, ctx.author, ctx)
		else:
			await self.profilePost(users, user, ctx)
				
	async def profilePost(self, users, user, ctx):
		
		SP = users[str(user.id)]["SP"]
		SSR = users[str(user.id)]["SSR"]
		SR = users[str(user.id)]["SR"]
		R = users[str(user.id)]["R"]
		amulets = users[str(user.id)]["amulets"]
		amulets_spent = users[str(user.id)]["amulets_spent"]
		experience = users[str(user.id)]["experience"]
		level = users[str(user.id)]["level"]
		level_exp_next = users[str(user.id)]["level_exp_next"]
		jades = users[str(user.id)]["jades"]
		coins = users[str(user.id)]["coins"]
		medals = users[str(user.id)]["medals"]
		realm_ticket = users[str(user.id)]["realm_ticket"]
		
		embed = discord.Embed(color=0xffff80)
		embed.set_thumbnail(url=user.avatar_url)
		embed.set_author(name="{}\'s profile".format(user.name))
		embed.add_field(inline = True, name = ":arrow_heading_up: Experience", 
			value = "Level: {} ({}/{})".format(level, experience, level_exp_next))
		embed.add_field(inline = True, name="SP | SSR | SR | R", 
			value="{} | {} | {} | {}".format(SP, SSR, SR, R))
		embed.add_field(inline = True, name = "{}Amulets".format(eAmulet),
			value = "On Hand: {} | Used: {}".format(amulets, amulets_spent))
		embed.add_field(inline = True, name = ":tickets: | {} | {} | {}".format(eMedal, eJade, eCoin), 
			value = "{} | {} | {:,d} | {:,d}".format(realm_ticket, medals, jades, coins))
			
		await ctx.channel.send(embed=embed)
		
	@commands.command(aliases=["list"])
	async def shikigamiList(self, ctx, arg1, user: discord.User=None):
		rarity = str(arg1.upper())
		
		with open("../data/users.json", "r") as f:
			users = json.load(f)
		
		if user == None:
			await self.shikigamiListPost(users, ctx.author, rarity, ctx)
		else:
			await self.shikigamiListPost(users, user, rarity, ctx)

	async def shikigamiListPost(self, users, user, rarity, ctx):
		
		userShiki = []
		
		for shikigami in users[str(user.id)]["shikigami"][rarity]:
			userShikiCount = users[str(user.id)]["shikigami"][rarity][shikigami]["owned"]
			if users[str(user.id)]["shikigami"][rarity][shikigami]["owned"] != 0:
				userShiki.append((shikigami, userShikiCount))
					
		userShikiSorted = sorted(userShiki, key=lambda x: x[1], reverse=True)
		shiki_pool_formatted = []
		
		i = 0
		while i < len(userShikiSorted):
			shiki_pool_formatted.append(userShikiSorted[i][0]+" | "+str(userShikiSorted[i][1]))
			i += 1
		
		description = []
		for shikigami in userShikiSorted:
			description.append(":white_small_square:{}, x{}\n".format(shikigami[0], shikigami[1]))
		
		userShikiPages = (len(userShiki) + 9)//10 * 10
		userShikiPage = 1
		
		icon_url = "https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/facebook/200/bookmark_1f516.png"
		
		embed = discord.Embed(color=0xffff80, description="".join(description[0:10]))
		embed.set_author(icon_url=user.avatar_url, name = "{}'s Shikigamis".format(user.name))
		embed.set_footer(text = "Rarity: {} - Page: {}".format(rarity.upper(), userShikiPage), icon_url=icon_url)
		msg = await ctx.channel.send(embed=embed)
		
		await msg.add_reaction("⬅")
		await msg.add_reaction("➡")
		
		
		def check(reaction, user):
			return user != self.client.user and reaction.message.id == msg.id
		
		while True:
			try:
				timeSec = 10
				reaction, user = await self.client.wait_for("reaction_add", timeout=timeSec, check=check)
				
				if str(reaction.emoji) == "➡":
					userShikiPage += 1

				if str(reaction.emoji) == "⬅":
					userShikiPage -= 1
					if userShikiPage == 0:
						userShikiPage = 1				
					
				start = (userShikiPage)*10-10
				end = (userShikiPage)*10
				
				embed = discord.Embed(color=0xffff80, description="".join(description[start:end]))
				embed.set_author(icon_url=user.avatar_url, name = "{}'s Shikigamis".format(user.name))
				embed.set_footer(text = "Rarity: {} - Page: {}".format(rarity.upper(), userShikiPage), icon_url=icon_url)

				await msg.edit(embed=embed)
				timeSec = timeSec - 1
			except asyncio.TimeoutError:
				return False
		
	@commands.command(aliases=["my"])
	async def shikigamiMy(self, ctx, *args):
		query = (" ".join(args)).title()
		with open("../data/users.json", "r") as f:
			users = json.load(f)
		await self.shikigamiMyPost(users, ctx.author, query, ctx)

	async def shikigamiMyPost(self, users, user, query, ctx):
	
		for rarity in users[str(user.id)]["shikigami"]:
			for shikigami in users[str(user.id)]["shikigami"][rarity]:
				if query == shikigami:
					count = users[str(user.id)]["shikigami"][rarity][shikigami]["owned"]
					grade = users[str(user.id)]["shikigami"][rarity][shikigami]["grade"]
					evo = users[str(user.id)]["shikigami"][rarity][shikigami]["evolved"]
					
					if count == 0:
						msg = "{} does not have {}.".format(user.name, query)
						await ctx.channel.send(msg)
						return
					
					with open ("../data/shikigami.json") as f:
						shikigami= json.load(f)
					
					for rarity in shikigami:
						for shiki in shikigami[rarity]:
							if query == shiki:
								normal = shikigami[rarity][query]["skills"]["normal"]
								special = shikigami[rarity][query]["skills"]["special"]
								specialty = shikigami[rarity][query]["specialty"]
								if evo == "True":
									evo = shikigami[rarity][query]["thumbnail"]["evo"]
									grade_star = ":star2:"*grade
								else:
									evo = shikigami[rarity][query]["thumbnail"]["pre_evo"]
									grade_star = ":star:"*grade

					embed=discord.Embed(color=0xffff80, 
						description = "Grade: {}\n\nNormal: {}\nSpecial: {}\n\nSpecialty: {}".format(grade_star, normal, special, specialty))
					embed.set_thumbnail(url=evo)
					embed.set_author(icon_url=user.avatar_url, name = "{}\"s {}".format(ctx.author.name, query))
					embed.set_footer(text = "shikigami count: {}".format(count))
					await ctx.channel.send(embed=embed)
					return	
		
		msg = "{}, {} does not exist in my memory.".format(user.mention, query)
		await ctx.channel.send(msg)
		
	@commands.command(aliases=["shiki", "shikigami"])
	async def shikigamiInfo(self, ctx, *args):
		with open ("../data/shikigami.json") as f:
			shikigami= json.load(f)
		
		query = (" ".join(args)).title()
		collect = []
		
		for rarity in shikigami:
			for shiki in shikigami[rarity]:
				if query == shiki:
					normal = shikigami[rarity][query]["skills"]["normal"]
					special = shikigami[rarity][query]["skills"]["special"]
					pre_evo = shikigami[rarity][query]["thumbnail"]["pre_evo"]
					evo = shikigami[rarity][query]["thumbnail"]["evo"]
					specialty = shikigami[rarity][query]["specialty"]
		
		embed = discord.Embed(color=0xffff80, description="Skills:\nNormal: {}\nSpecial: {}\n\nSpecialty: {}".format(normal, special, specialty))
		embed.set_thumbnail(url = evo)
		embed.set_author(name = "{}".format(query), icon_url = pre_evo)
		await ctx.channel.send(embed=embed)
	
	@commands.command(aliases=["update"])
	async def updateShiki(self, ctx, *args):
		if len(args) == 0 :
			
			embed = discord.Embed(color=0xffff80, description="Refer to sample correct command format:\n\n`;update <rarity> <shikigami> <normalskill> <specialskill> <pre-evo image link> <evo image link>`\n\nFor every <> replace spaces with underscore:\ne.g. inferno ibaraki -> inferno_ibaraki\n\nGrants 100{} per shikigami update per user".format(eJade))
			embed.set_thumbnail(url=self.client.user.avatar_url)
			await ctx.channel.send(embed=embed)
			return
		
		elif len(args) == 6:
			with open ("shikigami.json") as f:
					shikigami= json.load(f)
			rarity = args[0].upper()
			query = (args[1].replace("_", " ")).title()
			user = ctx.author
				
			if "profiler" in shikigami[rarity][query]:
				msg = "This shikigami has profile already. Try others."
				await ctx.channel.send(msg)
				return
			else: 		
				try: 
					normal = (args[2].title().replace("_", " ")).title()
					special = (args[3].title().replace("_", " ")).title()
					pre_evo = args[4]
					evo = args[5]
					
					shikigami[rarity][query]["thumbnail"]["pre_evo"] = pre_evo
					shikigami[rarity][query]["thumbnail"]["evo"] = evo
					shikigami[rarity][query]["skills"]["normal"] = normal
					shikigami[rarity][query]["skills"]["special"] = special
					
					if not "profiler" in shikigami[rarity][query]:
						shikigami[rarity][query]["profiler"] = user.name
					
					with open("../data/shikigami.json", "w") as f:
						json.dump(shikigami, f, indent="\t")
					
					with open ("../data/users.json") as f:
						users= json.load(f)
					
					users[str(user.id)]["jades"] += 100
					
					with open("../data/users.json", "w") as f:
						json.dump(users, f, indent="\t")
					
					msg ="{}, you have earned 100{}.".format(ctx.author.mention, eJade)
					await ctx.channel.send(msg)
							
				except KeyError as error:
					msg = "Try again. Wrong format"
					await ctx.channel.send(msg)
		else: 
			msg = "Try again. Lacks input"
			await ctx.channel.send(msg)
		
	@commands.command(aliases=["evo"])
	async def evolve(self, ctx, *args):
		user = ctx.author
		query = (" ".join(args)).title()
		with open("../data/users.json", "r") as f:
			users = json.load(f)
		
		if query == "":
			embed = discord.Embed(color=0xffff80, title=":gem: Shikigami Evolution",
				description = ":small_orange_diamond:SP - pre-evolved\n:small_orange_diamond:SSR - requires 1 dupe of the same kind\n:small_orange_diamond:SR - requires 10 dupes of the same kind\n:small_orange_diamond:R - requires 20 dupes of the same kind\n\nUse `;evolve <shikigami>` to perform evolution")
			embed.set_thumbnail(url=self.client.user.avatar_url)
			await ctx.channel.send(embed=embed)
			return 
			
		for rarity in users[str(user.id)]["shikigami"]:
			for shikigami in users[str(user.id)]["shikigami"][rarity]:
				
				
				if query == shikigami and rarity == "R" :
					count = users[str(user.id)]["shikigami"][rarity][shikigami]["owned"]
					grade = users[str(user.id)]["shikigami"][rarity][shikigami]["grade"]
					evo = users[str(user.id)]["shikigami"][rarity][shikigami]["evolved"]
					if evo == "True":
						msg = "{}, your {} is already evolved.".format(user.mention, query)
						await ctx.channel.send(msg)
						return
					if evo == "False":
						if count >= 21:
							users[str(user.id)]["shikigami"][rarity][shikigami]["owned"] -= 20
							users[str(user.id)]["shikigami"][rarity][shikigami]["evolved"] = "True"
							with open("../data/users.json", "w") as f:
								json.dump(users, f, indent="\t")
							msg = "{}, you have evolved your {}!".format(user.mention, query)
							await ctx.channel.send(msg)
							return 
						if count == 0:
							msg = "{}, you do not own that shikigami!".format(user.mention)
							await ctx.channel.send(msg)
							return
						if count <= 20:
							msg = "{}, you lack {} {} dupes to evolve yours.".format(user.mention, 21-count, query)
							await ctx.channel.send(msg)
							return
					
				if query == shikigami and rarity == "SR" :
					count = users[str(user.id)]["shikigami"][rarity][shikigami]["owned"]
					grade = users[str(user.id)]["shikigami"][rarity][shikigami]["grade"]
					evo = users[str(user.id)]["shikigami"][rarity][shikigami]["evolved"]
					if evo == "True":
						msg = "{}, your {} is already evolved.".format(user.mention, query)
						await ctx.channel.send(msg)
						return
					if evo == "False":
						if count >= 11:
							users[str(user.id)]["shikigami"][rarity][shikigami]["owned"] -= 10
							users[str(user.id)]["shikigami"][rarity][shikigami]["evolved"] = "True"
							with open("../data/users.json", "w") as f:
								json.dump(users, f, indent="\t")
							msg = "{}, you have evolved your {}!".format(user.mention, query)
							await ctx.channel.send(msg)
							return 
						if count == 0:
							msg = "{}, you do not own that shikigami!".format(user.mention)
							await ctx.channel.send(msg)
							return
						if count <= 10:
							msg = "{}, you lack {} {} dupes to evolve yours.".format(user.mention, 11-count, query)
							await ctx.channel.send(msg)
							return
							
				if query == shikigami and rarity == "SSR" :
					count = users[str(user.id)]["shikigami"][rarity][shikigami]["owned"]
					grade = users[str(user.id)]["shikigami"][rarity][shikigami]["grade"]
					evo = users[str(user.id)]["shikigami"][rarity][shikigami]["evolved"]
					if evo == "True":
						msg = "{}, your {} is already evolved.".format(user.mention, query)
						await ctx.channel.send(msg)
						return
					if evo == "False":
						if count >= 2:
							users[str(user.id)]["shikigami"][rarity][shikigami]["owned"] -= 1
							users[str(user.id)]["shikigami"][rarity][shikigami]["evolved"] = "True"
							with open("../data/users.json", "w") as f:
								json.dump(users, f, indent="\t")
							msg = "{}, you have evolved your {}!".format(user.mention, query)
							await ctx.channel.send(msg)
							return 
						if count == 0:
							msg = "{}, you do not own that shikigami!".format(user.mention)
							await ctx.channel.send(msg)
							return
						if count == 1:
							msg = "{}, you lack {} {} dupe to evolve yours.".format(user.mention, 2-count, query)
							await ctx.channel.send(msg)
							return
						
				if query == shikigami and rarity == "SP" :
						msg = "{}, SPs are pre-evolved.".format(user.mention)
						await ctx.channel.send(msg)
						return
						
		msg = "{}, I did not find that shikigami. Please input exact name.".format(user.mention)
		await ctx.channel.send(msg)
	
def setup(client):
	client.add_cog(Economy(client))