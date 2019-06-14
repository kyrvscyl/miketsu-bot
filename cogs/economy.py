"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import discord, json, asyncio
from cogs.mongo.db import users, daily, shikigami, compensation
from discord.ext import commands

class Economy(commands.Cog):
	
	def __init__(self, client):
		self.client = client

	@commands.command(aliases=["dailies"])
	async def daily(self, ctx):			
		user = ctx.author
		
		if daily.find_one({"key": "daily"}, {"_id": 0, "{}".format(user.id): 1}) == {}:
			await self.daily_give_rewards(user, ctx)
		
		elif daily.find_one({"key": "daily"}, {"{}".format(user.id): 1})[str(user.id)]["rewards"] == "unclaimed":
			await self.daily_give_rewards(user, ctx)

		else: 
			msg = "You have collected already today. Resets at 00:00 EST"
			await ctx.channel.send(msg)

	async def daily_give_rewards(self, user, ctx):
		
		daily.update_one({"key": "daily"}, {"$set": {"{}.rewards".format(user.id): "claimed", "{}.encounter_pass".format(user.id): 4, 		"{}.friendship_pass".format(user.id): 3}})
		
		embed = discord.Embed(color = 0xffff80, title = ":gift: Daily Rewards", 
			description = "A box containing 50<:jade:555630314282811412>, 25,000<:coin:573071121495097344>, 3:tickets:, 4:ticket:, 5<:friendship:555630314056318979>")
		embed.set_footer(text = "Claimed by {}".format(user.name), icon_url=user.avatar_url)
		
		users.update_one({"user_id": str(user.id)}, {"$inc": {"jades": 50, "coins": 25000}})
		
		if users.find_one({"user_id": str(user.id)}, {"_id": 0, "realm_ticket": 1})["realm_ticket"] < 27:
			users.update_one({"user_id": str(user.id)}, {"$inc": {"realm_ticket": 3}})
		else:
			users.update_one({"user_id": str(user.id)}, {"$set": {"realm_ticket": 30}})
		
		await ctx.channel.send(embed=embed)
		
	@commands.command(aliases=["weeklies"])
	async def weekly(self, ctx):
		user = ctx.author
		
		if daily.find_one({"key": "weekly"}, {"_id": 0, "{}".format(user.id): 1}) == {}:
			await self.weekly_give_rewards(user, ctx)
		
		elif daily.find_one({"key": "weekly"}, {"{}".format(user.id): 1})[str(user.id)]["rewards"] == "unclaimed":
			await self.weekly_give_rewards(user, ctx)
		else: 
			msg = "You have collected already this week. Resets at 00:00 EST Monday"
			await ctx.channel.send(msg)
	
	async def weekly_give_rewards(self, user, ctx):

		daily.update_one({"key": "weekly"}, {"$set": {"{}.rewards".format(user.id): "claimed"}})
		
		embed = discord.Embed(color = 0xffff80, title = ":gift: Weekly Rewards", 
			description = "A mythical box containing 750<:jade:555630314282811412>, 150,000<:coin:573071121495097344>, and 10<:amulet:573071120685596682>")
		embed.set_footer(text = "Claimed by {}".format(user.name), icon_url = user.avatar_url)
		
		users.update_one({"user_id": str(user.id)}, {"$inc": {"jades": 750, "coins": 150000, "amulets": 10}})
		await ctx.channel.send(embed=embed)

	@commands.command(aliases=["compensate"])
	async def compensation(self, ctx):
		requestor = ctx.author
		requestor_profile = compensation.find_one({}, {"_id": 0, "{}".format(requestor.id): 1})
		
		if requestor_profile == {} :
			msg = "{}, you are not eligible for this compensation".format(ctx.author.mention)
			await ctx.channel.send(msg)
		
		elif requestor_profile != {}:
			if requestor_profile[str(requestor.id)] == "unclaimed" :
				users.update_one({"user_id": str(requestor.id)}, {"$inc": {"jades": 3000}})
				compensation.update_one({"{}".format(requestor.id): "unclaimed"}, {"$set": {"{}".format(requestor.id): "claimed"}})
		
				msg = "You have been compensated with 3000<:jade:555630314282811412> due to recent data roll back."
				await ctx.channel.send(msg)	
				
			elif requestor_profile[str(requestor.id)] == "claimed" :
				msg = "{}, you can only claim this once!".format(ctx.author.mention)
				await ctx.channel.send(msg)
	
	@commands.command(aliases=["p"])
	async def profile(self, ctx, user: discord.User=None):
		
		if user == None:
			await self.profile_post(ctx.author, ctx)
		
		else:
			await self.profile_post(user, ctx)
				
	async def profile_post(self, user, ctx):
		profile = users.find_one({"user_id": str(user.id)}, {"_id": 0, 
			"SP": 1,
			"SSR": 1,
			"SR": 1,
			"R": 1,
			"amulets": 1,
			"amulets_spent": 1,
			"experience": 1,
			"level": 1,
			"level_exp_next": 1,
			"jades": 1,
			"coins": 1,
			"medals": 1,
			"realm_ticket": 1	
			})
		
		SP = profile["SP"]
		SSR = profile["SSR"]
		SR = profile["SR"]
		R = profile["R"]
		amulets = profile["amulets"]
		amulets_spent = profile["amulets_spent"]
		experience = profile["experience"]
		level = profile["level"]
		level_exp_next = profile["level_exp_next"]
		jades = profile["jades"]
		coins = profile["coins"]
		medals = profile["medals"]
		realm_ticket = profile["realm_ticket"]
		
		embed = discord.Embed(color=0xffff80)
		embed.set_thumbnail(url=user.avatar_url)
		embed.set_author(name="{}\'s profile".format(user.name))
		embed.add_field(inline = True, name = ":arrow_heading_up: Experience", 
			value = "Level: {} ({}/{})".format(level, experience, level_exp_next))
		embed.add_field(inline = True, name="SP | SSR | SR | R", 
			value="{} | {} | {} | {}".format(SP, SSR, SR, R))
		embed.add_field(inline = True, name = "{}Amulets".format("<:amulet:573071120685596682>"),
			value = "On Hand: {} | Used: {}".format(amulets, amulets_spent))
		embed.add_field(inline = True, name = ":tickets: | {} | {} | {}".format("<:medal:573071121545560064>", "<:jade:555630314282811412>", "<:coin:573071121495097344>"), 
			value = "{} | {} | {:,d} | {:,d}".format(realm_ticket, medals, jades, coins))
		
		await ctx.channel.send(embed=embed)
		
	@commands.command(aliases=["list"])
	async def shikigami_list(self, ctx, arg1, user: discord.User=None):
		rarity = str(arg1.upper())
		
		if user == None:
			await self.shikigami_list_post(ctx.author, rarity, ctx)
		else:
			await self.shikigami_list_post(user, rarity, ctx)

	async def shikigami_list_post(self, user, rarity, ctx):
		entries = users.aggregate([
			{
				'$match': {
					'user_id': str(user.id)
				}
			}, {
				'$unwind': {
					'path': '$shikigami'
				}
			}, {
				'$match': {
					'shikigami.rarity': rarity
				}
			}, {
				'$project': {
					'_id': 0, 
					'shikigami.name': 1, 
					'shikigami.owned': 1, 
					'shikigami.rarity': rarity
				}
			}
		])

		user_shiki = []
		for entry in entries:
			user_shiki.append((entry["shikigami"]["name"], entry["shikigami"]["owned"]))
					
		user_shiki_sorted = sorted(user_shiki, key=lambda x: x[1], reverse=True)
		shiki_pool_formatted = []
		
		i = 0
		while i < len(user_shiki_sorted):
			shiki_pool_formatted.append(user_shiki_sorted[i][0]+" | "+str(user_shiki_sorted[i][1]))
			i += 1
		
		description = []
		for shikigami in user_shiki_sorted:
			description.append(":white_small_square:{}, x{}\n".format(shikigami[0], shikigami[1]))
		
		user_shiki_pages = (len(user_shiki) + 9)//10 * 10
		user_shiki_page = 1
		
		icon_url = "https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/facebook/200/bookmark_1f516.png"
		
		embed = discord.Embed(color=0xffff80, description="".join(description[0:10]))
		embed.set_author(icon_url=user.avatar_url, name = "{}'s Shikigamis".format(user.name))
		embed.set_footer(text = "Rarity: {} - Page: {}".format(rarity.upper(), user_shiki_page), icon_url=icon_url)
		msg = await ctx.channel.send(embed=embed)
		
		await msg.add_reaction("⬅")
		await msg.add_reaction("➡")
		
		def check(reaction, member):
			return member != self.client.user and reaction.message.id == msg.id
		
		while True:
			try:
				timeout = 10
				reaction, member = await self.client.wait_for("reaction_add", timeout=timeout, check=check)
				
				if str(reaction.emoji) == "➡":
					user_shiki_page += 1

				if str(reaction.emoji) == "⬅":
					user_shiki_page -= 1
					if user_shiki_page == 0:
						user_shiki_page = 1				
					
				start = (user_shiki_page)*10-10
				end = (user_shiki_page)*10
				
				embed = discord.Embed(color=0xffff80, description="".join(description[start:end]))
				embed.set_author(icon_url=user.avatar_url, name = "{}'s Shikigamis".format(user.name))
				embed.set_footer(text = "Rarity: {} - Page: {}".format(rarity.upper(), user_shiki_page), icon_url=icon_url)

				await msg.edit(embed=embed)
				timeout = timeout - 1
			except asyncio.TimeoutError:
				return
		
	@commands.command(aliases=["my"])
	async def shikigami_my(self, ctx, *args):
		query = (" ".join(args)).title()
		await self.shikigami_my_post(ctx.author, query, ctx)

	async def shikigami_my_post(self, user, query, ctx):
		
		try : 
			profile_my_shikigami = users.find_one({"user_id": str(user.id)}, {"_id": 0, "shikigami": {"$elemMatch": {"name": query}}})
			count = profile_my_shikigami["shikigami"][0]["owned"]
			grade = profile_my_shikigami["shikigami"][0]["grade"]
			evo = profile_my_shikigami["shikigami"][0]["evolved"]
			rarity = profile_my_shikigami["shikigami"][0]["rarity"]
			
			
			profile_shikigami = shikigami.find_one({"rarity": rarity}, {"_id": 0, "shikigami": {"$elemMatch": {"name": query}}})
			normal = profile_shikigami["shikigami"][0]["skills"]["normal"]
			special = profile_shikigami["shikigami"][0]["skills"]["special"]
			specialty = profile_shikigami["shikigami"][0]["specialty"]
			
			
			if evo == "True":
				thumbnail = profile_shikigami["shikigami"][0]["thumbnail"]["evo"]
				grade_star = ":star2:"*grade
			else:
				thumbnail = profile_shikigami["shikigami"][0]["thumbnail"]["pre_evo"]
				grade_star = ":star:"*grade

			embed=discord.Embed(color=0xffff80, 
				description = "Grade: {}\n\nNormal: {}\nSpecial: {}\n\nSpecialty: {}".format(grade_star, normal, special, specialty))
			embed.set_thumbnail(url=thumbnail)
			embed.set_author(icon_url=user.avatar_url, name = "{}\"s {}".format(ctx.author.name, query))
			embed.set_footer(text = "shikigami count: {}".format(count))
			await ctx.channel.send(embed=embed)
	
		except KeyError:
			msg = "{}, that shikigami does not exist or your do not have it".format(user.mention)
			await ctx.channel.send(msg)
		
	@commands.command(aliases=["shiki", "shikigami"])
	async def shikigami_info(self, ctx, *args):
		query = (" ".join(args)).title()
		collect = []
		
		profile_shikigami = shikigami.find_one({"shikigami.name": query}, {"_id": 0, "shikigami": {"$elemMatch": {"name": query}}})
		normal = profile_shikigami["shikigami"][0]["skills"]["normal"]
		special = profile_shikigami["shikigami"][0]["skills"]["special"]
		specialty = profile_shikigami["shikigami"][0]["specialty"]
		pre_evo =  profile_shikigami["shikigami"][0]["thumbnail"]["pre_evo"]
		evo = profile_shikigami["shikigami"][0]["thumbnail"]["evo"]
		
		embed = discord.Embed(color=0xffff80, description="**Skills:**\nNormal: {}\nSpecial: {}\n\nSpecialty: {}".format(normal, special, specialty))
		embed.set_thumbnail(url = evo)
		embed.set_author(name = "{}".format(query), icon_url = pre_evo)
		await ctx.channel.send(embed=embed)
	
	@commands.command(aliases=["update"])
	async def shikigami_update(self, ctx, *args):
		if len(args) == 0 :
			
			embed = discord.Embed(color=0xffff80, description="Refer to sample correct command format:\n\n`;update <rarity> <shikigami> <normalskill> <specialskill> <pre-evo image link> <evo image link>`\n\nFor every <> replace spaces with underscore:\ne.g. inferno ibaraki -> inferno_ibaraki\n\nGrants 100{} per shikigami update per user".format("<:jade:555630314282811412>"))
			embed.set_thumbnail(url=self.client.user.avatar_url)
			await ctx.channel.send(embed=embed)
		
		elif len(args) == 6:
			
			rarity = args[0].upper()
			query = (args[1].replace("_", " ")).title()
			user = ctx.author
			
			profile_shikigami = shikigami.find_one({"shikigami.name": query}, {"_id": 0, "shikigami": {"$elemMatch": {"name": query}}})
			
			try:
				if profile_shikigami["shikigami"][0]["profiler"] != "":
					msg = "This shikigami has profile already. Try others."
					await ctx.channel.send(msg)

			except KeyError:
				try: 
					normal = (args[2].title().replace("_", " ")).title()
					special = (args[3].title().replace("_", " ")).title()
					pre_evo = args[4]
					evo = args[5]
					profiler = ctx.author.name
					
					x = shikigami.update_one({"shikigami.name": query}, {"$set": {
						"shikigami.$.skills.normal": normal, 
						"shikigami.$.skills.special": special,
						"shikigami.$.thumbnail.pre_evo": pre_evo,
						"shikigami.$.thumbnail.evo": evo,
						"shikigami.$.profiler": str(profiler)
						}})
					
					print(x.modified_count)
					
					users.update_one({"user_id": str(user.id)}, {"$inc": {"jades": 100}})
					
					msg ="{}, you have earned 100{}.".format(ctx.author.mention, "<:jade:555630314282811412>")
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
		profile_my_shikigami = users.find_one({"user_id": str(user.id)}, {"_id": 0, "shikigami": {"$elemMatch": {"name": query}}})
		
		if query == "":
			embed = discord.Embed(color=0xffff80, title=":gem: Shikigami Evolution",
				description = ":small_orange_diamond:SP - pre-evolved\n:small_orange_diamond:SSR - requires 1 dupe of the same kind\n:small_orange_diamond:SR - requires 10 dupes of the same kind\n:small_orange_diamond:R - requires 20 dupes of the same kind\n\nUse `;evolve <shikigami>` to perform evolution")
			embed.set_thumbnail(url=self.client.user.avatar_url)
			await ctx.channel.send(embed=embed)
		
		elif profile_my_shikigami == {}:
			msg = "{}, I did not find that shikigami nor you have it.".format(user.mention)
			await ctx.channel.send(msg)
			
		elif profile_my_shikigami != {}:
			rarity = profile_my_shikigami["shikigami"][0]["rarity"]
			count = profile_my_shikigami["shikigami"][0]["owned"]
			grade = profile_my_shikigami["shikigami"][0]["grade"]
			evo = profile_my_shikigami["shikigami"][0]["evolved"]
			
			if rarity == "R" :
				if evo == "True":
					msg = "{}, your {} is already evolved.".format(user.mention, query)
					await ctx.channel.send(msg)
					
				elif evo == "False":
					if count >= 21:
						users.update_one({"user_id": str(user.id), "shikigami.name": query}, {"$inc": {"shikigami.$.owned": -20}})
						users.update_one({"user_id": str(user.id), "shikigami.name": query}, {"$set": {"shikigami.$.evolved": "True"}})
						msg = "{}, you have evolved your {}!".format(user.mention, query)
						await ctx.channel.send(msg)
					
					elif count == 0:
						msg = "{}, you do not own that shikigami!".format(user.mention)
						await ctx.channel.send(msg)
						
					elif count <= 20:
						msg = "{}, you lack {} more {} dupes to evolve yours.".format(user.mention, 21-count, query)
						await ctx.channel.send(msg)
						
			elif rarity == "SR" :
				if evo == "True":
					msg = "{}, your {} is already evolved.".format(user.mention, query)
					await ctx.channel.send(msg)

				elif evo == "False":
					if count >= 11:
						users.update_one({"user_id": str(user.id), "shikigami.name": query}, {"$inc": {"shikigami.$.owned": -10}})
						users.update_one({"user_id": str(user.id), "shikigami.name": query}, {"$set": {"shikigami.$.evolved": "True"}})
						
						msg = "{}, you have evolved your {}!".format(user.mention, query)
						await ctx.channel.send(msg)

					elif count == 0:
						msg = "{}, you do not own that shikigami!".format(user.mention)
						await ctx.channel.send(msg)
						
					elif count <= 10:
						msg = "{}, you lack {} more {} dupes to evolve yours.".format(user.mention, 11-count, query)
						await ctx.channel.send(msg)
						
			elif rarity == "SSR" :
				if evo == "True":
					msg = "{}, your {} is already evolved.".format(user.mention, query)
					await ctx.channel.send(msg)
					
				elif evo == "False":
					if count >= 2:
						users.update_one({"user_id": str(user.id), "shikigami.name": query}, {"$inc": {"shikigami.$.owned": -1}})
						users.update_one({"user_id": str(user.id), "shikigami.name": query}, {"$set": {"shikigami.$.evolved": "True"}})
						
						msg = "{}, you have evolved your {}!".format(user.mention, query)
						await ctx.channel.send(msg)
						 
					elif count == 0:
						msg = "{}, you do not own that shikigami!".format(user.mention)
						await ctx.channel.send(msg)
						
					elif count == 1:
						msg = "{}, you lack {} more {} dupe to evolve yours.".format(user.mention, 2-count, query)
						await ctx.channel.send(msg)				
					
			elif rarity == "SP" :
				msg = "{}, SPs are pre-evolved.".format(user.mention)
				await ctx.channel.send(msg)
					
def setup(client):
	client.add_cog(Economy(client))