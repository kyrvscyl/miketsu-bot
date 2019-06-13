"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import discord, json, random
from cogs.mongo.db import users, daily
from discord.ext import commands
from pymongo import MongoClient

# Mongo Startup
# memory = MongoClient("mongodb+srv://headmaster:headmaster@memory-scrolls-uhsu0.mongodb.net/test?retryWrites=true&w=majority")
# memory = MongoClient("mongodb://localhost:27017/")
# users = memory["miketsu"]["users"]
# daily = memory["miketsu"]["daily"]

class Startup(commands.Cog):
	
	def __init__(self, client):
		self.client = client
	
	def calculate(self, x, y, z):
		try:
			if x - y > 0 :
				return ((x - y) / x) * z
			elif x - y < 0 :
				return -((y - x) / y) * z
			else: 
				return 0
		except ZeroDivisionError:
			return 0
	
	@commands.command(aliases=["r"])
	@commands.guild_only()
	async def raid(self, ctx, victim: discord.User=None):
		raider = ctx.author
		
		# No mentioned user
		if victim == None:
			msg = "{}, please mention a user to raid. Consumes 1:tickets:".format(ctx.author.mention)
			await ctx.channel.send(msg)
		
		# No Victim is a bot
		elif victim.bot == True:
			msg = "{}, you cannot do that!".format(ctx.author.mention)
			await ctx.channel.send(msg)
		
		# Victim is self
		elif victim.id == ctx.author.id:
			msg = "{}, you cannot raid your own realm.".format(ctx.author.mention)
			await ctx.channel.send(msg)
				
		# Checking realm tickets
		elif users.find_one({"user_id": str(raider.id)}, {"_id": 0, "realm_ticket": 1})["realm_ticket"] == 0:
			msg = "{}, You have insufficient :tickets:".format(ctx.author.mention)
			await ctx.channel.send(msg)
			
		# Create initial record
		elif daily.find_one({"key": "raid"}, {"_id": 0, "{}.raid_count".format(victim.id): 1}) == {}:
			daily.update_one({"key": "raid"}, {"$set": {"{}.raid_count".format(victim.id): 1}})	
			await self.raid_attack(users, victim, raider, ctx)	
			
		# Employ protection
		elif daily.find_one({"key": "raid"}, {"_id": 0, "{}.raid_count".format(victim.id): 1})[str(victim.id)]["raid_count"] == 3:
			msg = "{}, this user's realm is under protection.".format(ctx.author.mention)
			await ctx.channel.send(msg)	
		
		# Raids the victim
		elif daily.find_one({"key": "raid"}, {"_id": 0, "{}.raid_count".format(victim.id): 1})[str(victim.id)]["raid_count"] < 4:
			daily.update_one({"key": "raid"}, {"$inc": {"{}.raid_count".format(victim.id): 1}})
			await self.raid_attack(users, victim, raider, ctx)		
				
	async def raid_attack(self, users, victim, raider, ctx):	
		try: 
			# Getting profiles
			profile_raider = users.find_one({'user_id': str(raider.id)},{'_id': 0, 'level': 1, 'medals': 1, 'SP': 1, 'SSR': 1, 'SR': 1, 'R': 1})
			profile_victim = users.find_one({'user_id': str(victim.id)},{'_id': 0, 'level': 1, 'medals': 1, 'SP': 1, 'SSR': 1, 'SR': 1, 'R': 1})
			
			r_lvl = profile_raider["level"]
			r_medal = profile_raider["medals"]
			r_sp = profile_raider["SP"]
			r_ssr = profile_raider["SSR"]
			r_sr = profile_raider["SR"]
			r_r = profile_raider["R"]
			
			v_lvl = profile_victim["level"]
			v_medal = profile_victim["medals"]
			v_sp = profile_victim["SP"]
			v_ssr = profile_victim["SSR"]
			v_sr = profile_victim["SR"]
			v_r = profile_victim["R"]
			
			chance0 = 0.5
			chance1 = self.calculate(r_lvl, v_lvl, 0.15)
			chance2 = self.calculate(r_medal, v_medal, 0.15)
			chance3 = self.calculate(r_sp, v_sp, 0.09)
			chance4 = self.calculate(r_ssr, v_ssr, 0.07)
			chance5 = self.calculate(r_sr, v_sr, 0.03)
			chance6 = self.calculate(r_r, v_r, 0.01)
			total_chance = round((chance0 + chance1 + chance2 + chance3 + chance4 + chance5 + chance6)*100,2)
			roll = random.uniform(0,100)
			
			if roll <= total_chance:
				embed = discord.Embed(color=0xffff80, title=":clipboard: Raid Report", 
					description = ":bow_and_arrow: Raider: `{}`\n:dart:  Victim: `{}`\n\n:game_die: `{}%` success\n:trophy: `{}` prevails!\n\n:gift: Rewards:\n25,000{}, 30{}, 10{}".format(raider.name, victim.name, total_chance, raider.name, "<:coin:573071121495097344>", "<:jade:555630314282811412>", "<:medal:573071121545560064>"))
				embed.set_thumbnail(url=raider.avatar_url)

				await self.raid_giverewards_raider_as_winner(users, victim, raider)
				await ctx.channel.send(embed=embed)
			else:
				embed = discord.Embed(color=0xac330f, title=":clipboard: Raid Report", 
					description = ":bow_and_arrow: Raider: `{}`\n:dart:  Victim: `{}`\n\n:game_die: `{}%` success\n:trophy: `{}` prevails!\n\n:gift: Comeback Rewards:\n50,000{}, 100{}, 20{}".format(raider.name, victim.name, total_chance, victim.name,"<:coin:573071121495097344>", "<:jade:555630314282811412>", "<:medal:573071121545560064>"))
				embed.set_thumbnail(url=victim.avatar_url)
				
				await self.raid_giverewards_victim_as_winner(users, victim, raider)
				await ctx.channel.send(embed=embed)
				
		# Invalid mentioned user	
		except KeyError as error:
			msg = "{}, I did not find that user. Please try again.".format(raider.mention)
			await ctx.channel.send(msg)
		except TypeError as error:
			return

	async def raid_giverewards_victim_as_winner(self, users, victim, raider):
		
		# Victim 
		users.update_one({"user_id": str(victim.id)}, {"$inc": {"coins": 50000, "jades": 100, "medals": 20}})
		
		# Raider 
		users.update_one({"user_id": str(raider.id)}, {"$inc": {"realm_ticket": -1}})
		
		# No negative medals
		if users.find_one({"user_id": str(raider.id)}, {"_id": 0})["medals"] < 10:
			users.update_one({"user_id": str(raider.id)}, {"$set": {"medals": 0}})
		else:
			users.update_one({"user_id": str(raider.id)}, {"$inc": {"medals": -10}})
			
	async def raid_giverewards_raider_as_winner(self, users, victim, raider):
		
		# Raider
		users.update_one({"user_id": str(raider.id)}, {"$inc": {"coins": 25000, "jades": 30, "medals": 10, "realm_ticket": -1}})
		
		# No negative medals
		if users.find_one({"user_id": str(victim.id)}, {"_id": 0})["medals"] < 10:
			users.update_one({"user_id": str(victim.id)}, {"$set": {"medals": 0}})
		else:
			users.update_one({"user_id": str(victim.id)}, {"$inc": {"medals": -10}})
				
	@commands.command(aliases=["rc", "raidc"])
	async def raid_calculate(self, ctx, user:discord.User=None):
		
		# No mentioned user
		if user == None:
			embed = discord.Embed(color=0xffff80, title=":game_die: Raid Calculation", 
			description = "This calculates the percent chance of successfully raiding the mentioned user. Success chance is a function of level, medals, & shikigami pool of the victim & raider.\n\n:white_small_square: Base chance: 50%\n:white_small_square: Level: ± 15%\n:white_small_square: Medals: ± 15%\n:white_small_square: SP: ± 9%\n:white_small_square: SSR: ± 7%\n:white_small_square: SR: ±3%\n:white_small_square: R: ±1%")
			embed.set_thumbnail(url=self.client.user.avatar_url)
			
			await ctx.channel.send(embed=embed)
			
		# Responds on self raid
		elif user == ctx.author or user.bot == True:
			msg = "{}, why would you do that?".format(ctx.author.mention)
			await ctx.channel.send(msg)
		
		# Calculates the chance
		elif user != ctx.author:
			await self.raid_calculation(user, ctx.author, ctx)

	async def raid_calculation(self, victim, raider, ctx):
	
		try:
			# Getting profiles
			profile_raider = users.find_one({'user_id': str(raider.id)},{'_id': 0, 'level': 1, 'medals': 1, 'SP': 1, 'SSR': 1, 'SR': 1, 'R': 1})
			profile_victim = users.find_one({'user_id': str(victim.id)},{'_id': 0, 'level': 1, 'medals': 1, 'SP': 1, 'SSR': 1, 'SR': 1, 'R': 1})
			
			r_lvl = profile_raider["level"]
			r_medal = profile_raider["medals"]
			r_sp = profile_raider["SP"]
			r_ssr = profile_raider["SSR"]
			r_sr = profile_raider["SR"]
			r_r = profile_raider["R"]
			
			v_lvl = profile_victim["level"]
			v_medal = profile_victim["medals"]
			v_sp = profile_victim["SP"]
			v_ssr = profile_victim["SSR"]
			v_sr = profile_victim["SR"]
			v_r = profile_victim["R"]
			
			chance0 = 0.5
			chance1 = self.calculate(r_lvl, v_lvl, 0.15)
			chance2 = self.calculate(r_medal, v_medal, 0.15)
			chance3 = self.calculate(r_sp, v_sp, 0.09)
			chance4 = self.calculate(r_ssr, v_ssr, 0.07)
			chance5 = self.calculate(r_sr, v_sr, 0.03)
			chance6 = self.calculate(r_r, v_r, 0.01)
			total_chance = round((chance0 + chance1 + chance2 + chance3 + chance4 + chance5 + chance6)*100,2)
			
			embed = discord.Embed(color=0xffff80, title=":gear: Raid Calculation", 
				description = ":bow_and_arrow: Raider: `{}`\n:dart:  Victim: `{}`\n\n:game_die: `{}%` success".format(raider.name, victim.name, total_chance))
			embed.set_thumbnail(url=raider.avatar_url)
			
			await ctx.channel.send(embed=embed)
			
		# Invalid mentioned user	
		except KeyError as error:
			msg = "{}, I did not find that user. Please try again.".format(raider.mention)
			await ctx.channel.send(msg)
		except TypeError as error:
			return
	
def setup(client):
	client.add_cog(Startup(client))