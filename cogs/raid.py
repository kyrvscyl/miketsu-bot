"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import discord, json, random
import config.guild as guild
from discord.ext import commands

class Startup(commands.Cog):
	
	def __init__(self, client):
		self.client = client
	
	def chanceCalc(self, x, y, z):
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
	async def raid(self, ctx, user: discord.User=None):
		# No mentioned user
		if user == None:
			msg = "{}, please mention a user to raid. Consumes 1:tickets:".format(ctx.author.mention)
			await ctx.channel.send(msg)
		else:
		
		# Raiding oneself
			if user.id == ctx.author.id:
				msg = "{}, you cannot raid your own realm.".format(ctx.author.mention)
				await ctx.channel.send(msg)
				
			# Valid user
			else:
				with open("../data/users.json","r") as f:
					users = json.load(f)	
					
				# Checking realm tickets
				if users[str(ctx.author.id)]["realm_ticket"] > 0:
					with open("../data/daily.json", "r") as f:
						daily = json.load(f)
						
					# Checking and adding protection 1
					if not str(user.id) in daily["raid"]:
						daily["raid"][str(user.id)] = {}
						daily["raid"][str(user.id)]["raid_count"] = 0
						
						with open("../data/daily.json", "w") as f:
							json.dump(daily, f, indent="\t")	
							
						await self.raid_attack(users, user, ctx.author, ctx)	
						
					# Checking and adding protection 2
					elif daily["raid"][str(user.id)]["raid_count"] != 3:
						await self.raid_attack(users, user, ctx.author, ctx)		
						
					# Protected user
					else:
						msg = "{}, this user\"s realm is under protection.".format(ctx.author.mention)
						await ctx.channel.send(msg)
						
				# No realm tickets
				else:
					msg = "{}, You have insufficient :tickets:".format(ctx.author.mention)
					await ctx.channel.send(msg)
			
	async def raid_attack(self, users, victim, raider, ctx):	
		try: 
			raiderLevel = users[str(raider.id)]["level"]
			raiderMedal = users[str(raider.id)]["medals"]
			raiderSP = users[str(raider.id)]["SP"]
			raiderSSR = users[str(raider.id)]["SSR"]
			raiderSR = users[str(raider.id)]["SR"]
			raiderR = users[str(raider.id)]["R"]
			victimLevel = users[str(victim.id)]["level"]
			victimMedal = users[str(victim.id)]["medals"]
			victimSP = users[str(victim.id)]["SP"]
			victimSSR = users[str(victim.id)]["SSR"]
			victimSR = users[str(victim.id)]["SR"]
			victimR = users[str(victim.id)]["R"]
			
			chance0 = 0.5
			chance1 = self.chanceCalc(raiderLevel, victimLevel, 0.15)
			chance2 = self.chanceCalc(raiderMedal, victimMedal, 0.15)
			chance3 = self.chanceCalc(raiderSP, victimSP, 0.09)
			chance4 = self.chanceCalc(raiderSSR, victimSSR, 0.07)
			chance5 = self.chanceCalc(raiderSR, victimSR, 0.03)
			chance6 = self.chanceCalc(raiderR, victimR, 0.01)
			
			total_chance = round((chance0 + chance1 + chance2 + chance3 + chance4 + chance5 + chance6)*100,2)
			
			roll = random.uniform(0,100)
			
			if roll <= total_chance:

				embed = discord.Embed(color = 0xffff80, title = ":clipboard: Raid Report", 
					description = ":bow_and_arrow: Raider: `{}`\n:dart:  Victim: `{}`\n\n:game_die: `{}%` success\n:trophy: `{}` prevails!\n\n:gift: Rewards:\n10,000{}, 30{}, 10{}".format(raider.name, victim.name, total_chance, raider.name, guild.eCoin, guild.eJade, guild.eMedal))
				embed.set_thumbnail(url = raider.avatar_url)

				await self.raid_giverewards_raider_as_winner(users, victim, raider)
				await ctx.channel.send(embed=embed)
			else:
				embed = discord.Embed(color = 0xac330f, title = ":clipboard: Raid Report", 
					description = ":bow_and_arrow: Raider: `{}`\n:dart:  Victim: `{}`\n\n:game_die: `{}%` success\n:trophy: `{}` prevails!\n\n:gift: Comeback Rewards:\n50,000{}, 100{}, 20{}".format(raider.name, victim.name, total_chance, victim.name, guild.eCoin, guild.eJade, guild.eMedal))
				embed.set_thumbnail(url = victim.avatar_url)
				
				await self.raid_giverewards_victim_as_winner(users, victim, raider)
				await ctx.channel.send(embed=embed)
				
		except KeyError as error:
			await ctx.channel.send("{}, I did not find that user. Please try again.".format(ctx.author.mention))

	async def raid_giverewards_victim_as_winner(self, users, victim, raider):
		users[str(victim.id)]["medals"] += 20
		users[str(raider.id)]["coins"] += 50000
		users[str(victim.id)]["jades"] += 100
		users[str(raider.id)]["realm_ticket"] -= 1
		
		if users[str(raider.id)]["medals"] < 10:
			users[str(raider.id)]["medals"] = 0
		else:
			users[str(raider.id)]["medals"] -= 10
			
		with open("../data/users.json", "w") as f:
			json.dump(users, f, indent="\t")
			
	async def raid_giverewards_raider_as_winner(self, users, victim, raider):
		users[str(raider.id)]["medals"] += 10
		users[str(raider.id)]["coins"] += 10000
		users[str(raider.id)]["jades"] += 30
		users[str(raider.id)]["realm_ticket"] -= 1
		
		# No negative medals
		if users[str(victim.id)]["medals"] < 5:
			users[str(victim.id)]["medals"] = 0
		else:
			users[str(victim.id)]["medals"] -= 5
		
		with open("../data/users.json", "w") as f:
			json.dump(users, f, indent="\t")
		
		with open("../data/daily.json", "r") as f:
			daily = json.load(f)	
		
		daily['raid'][str(victim.id)]["raid_count"] += 1
		
		with open("../data/daily.json", "w") as f:
			json.dump(daily, f, indent="\t")
		
	@commands.command(aliases=["rc", "raidc"])
	async def raid_calculate(self, ctx, user:discord.User=None):
		# No mentioned user
		if user == None:
			embed = discord.Embed(color=0xffff80, title=":game_die: Raid Calculation", 
			description = "This calculates the percent chance of successfully raiding the mentioned user. Success chance is a function of level, medals, & shikigami pool of the victim & raider.\n\n:white_small_square: Base chance: 50%\n:white_small_square: Level: ± 15%\n:white_small_square: Medals: ± 15%\n:white_small_square: SP: ± 9%\n:white_small_square: SSR: ± 7%\n:white_small_square: SR: ±3%\n:white_small_square: R: ±1%")
			embed.set_thumbnail(url=self.client.user.avatar_url)
			await ctx.channel.send(embed=embed)
		# Responds on self raid
		elif user == ctx.author:
			msg = "{}, why would you do that?".format(ctx.author.mention)
			await ctx.channel.send(msg)
		# Perform user check
		else:
			await self.raid_calculation(user, ctx.author, ctx)

	async def raid_calculation(self, victim, raider, ctx):
		with open("../data/users.json","r") as f:
			users = json.load(f)
			# Calculates the chance
			try: 
				raiderLevel = users[str(raider.id)]["level"]
				raiderMedal = users[str(raider.id)]["medals"]
				raiderSP = users[str(raider.id)]["SP"]
				raiderSSR = users[str(raider.id)]["SSR"]
				raiderSR = users[str(raider.id)]["SR"]
				raiderR = users[str(raider.id)]["R"]
				
				victimLevel = users[str(victim.id)]["level"]
				victimMedal = users[str(victim.id)]["medals"]
				victimSP = users[str(victim.id)]["SP"]
				victimSSR = users[str(victim.id)]["SSR"]
				victimSR = users[str(victim.id)]["SR"]
				victimR = users[str(victim.id)]["R"]

				chance0 = 0.5
				chance1 = self.chanceCalc(raiderLevel, victimLevel, 0.15)
				chance2 = self.chanceCalc(raiderMedal, victimMedal, 0.15)
				chance3 = self.chanceCalc(raiderSP, victimSP, 0.09)
				chance4 = self.chanceCalc(raiderSSR, victimSSR, 0.07)
				chance5 = self.chanceCalc(raiderSR, victimSR, 0.03)
				chance6 = self.chanceCalc(raiderR, victimR, 0.01)
				total_chance = round((chance0 + chance1 + chance2 + chance3 + chance4 + chance5 + chance6)*100, 2)
				
				embed = discord.Embed(color = 0xffff80, title = ":gear: Raid Calculation", 
					description = ":bow_and_arrow: Raider: `{}`\n:dart:  Victim: `{}`\n\n:game_die: `{}%` success".format(raider.name, victim.name, total_chance))
				embed.set_thumbnail(url = raider.avatar_url)
				await ctx.channel.send(embed=embed)
				
			# Invalid mentioned user	
			except KeyError as error:
				msg = "{}, I did not find that user. Please try again.".format(raider.mention)
				await ctx.channel.send(msg)

def setup(client):
	client.add_cog(Startup(client))