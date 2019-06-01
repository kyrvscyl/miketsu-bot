"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import discord, json, random, asyncio
from discord.ext import commands
import config.guild as guild
from config.lists import bossesList, attackVerb
from config.guild import eAmulet


demon = ["Tsuchigumo", "Odokuro", "Shinkirou", "Oboroguruma", "Namazu"]

class Encounter(commands.Cog):
	
	def __init__(self, client):
		self.client = client
	
	def getEmoji(self, item):
		if item == "jades":
			return guild.eJade
		if item == "coins":
			return guild.eCoin
		if item == "medals":
			return guild.eMedal
		if item == "realm_ticket":
			return "🎟"		
		if item == "amulets":
			return guild.eAmulet

	@commands.command(aliases=["enc"])
	@commands.cooldown(1, 180, commands.BucketType.guild)
	@commands.guild_only()
	async def encounter(self, ctx):
		user = ctx.author
		
		# Check user tickets first
		with open("../data/daily.json", "r") as f:
			daily = json.load(f)
		
		if str(user.id) in daily["daily"]:
			if daily["daily"][str(user.id)]["encounter_pass"] > 0:
				daily["daily"][str(user.id)]["encounter_pass"] -= 1
				
				with open("../data/daily.json", "w") as f:
					json.dump(daily, f, indent="\t")
					
				await self.encounter_roll(user, ctx)
			
			else:
				msg = "You have used up all your :ticket: today."
				await ctx.channel.send(msg)
				self.client.get_command("encounter").reset_cooldown(ctx)
				
		else: 
			msg = "Please claim your daily rewards to obtain 4:ticket:"
			await ctx.channel.send(msg)
			self.client.get_command("encounter").reset_cooldown(ctx)

	async def encounter_roll(self, user, ctx):	
		with open("../data/boss.json", "r") as f:
			boss = json.load(f)	
		
		async with ctx.channel.typing():
			msg = "🔍Searching the depths of Netherworld..."
			await ctx.channel.send(msg)
		
			survivability = 0
			k = 0
			while k < len(demon):
				survivability += boss[demon[k]]["current_hp"]
				k += 1
			discoverability = 0
			i = 0
			while i < len(demon):
				try: 
					discoverability += int(boss[demon[i]]["discoverer"])
				except ValueError as error:
					discoverability = 1
					i += 10
				i += 1
			if survivability > 0 or discoverability == 1:
				roll = random.randint(0,100)
				
				if roll <= 20:	
					await asyncio.sleep(3)
					await self.boss_roll(user, ctx)
				else:
					roll2 = random.randint(0,100)
					await asyncio.sleep(3)
					if roll2 > 40:
						await self.treasure_roll(user, ctx)
					else: 
						await self.quiz_roll(user, ctx)
			else:
				roll2 = random.randint(0,100)
				await asyncio.sleep(3)
				if roll2 > 40:
					await self.treasure_roll(user, ctx)
				else: 
					await self.quiz_roll(user, ctx)

	async def quiz_roll(self, guesser, ctx):
		
		guesser = ctx.author
		
		with open("../data/quiz.json", "r") as f:
			quiz = json.load(f)
			
		shikiAll = list(quiz.keys())
		answer = random.choice(shikiAll)
		questions = []
		
		for entry in quiz[answer]:
			if quiz[answer][entry] != 0:
				questions.append(quiz[answer][entry])
		
		question = random.choice(questions)
				
		embed = discord.Embed(color=0xffff80, description=":grey_question:Who is this shikigami: {}".format(question))
		embed.set_author(name="Demon Quiz")
		embed.set_footer(text="Quiz for {}. 10 sec | 2 guesses".format(ctx.message.author.name), icon_url=ctx.message.author.avatar_url)
		
		msgQuestion = await ctx.channel.send(embed=embed)
			
		def check(guess):
			guessFormatted = ("".join(guess.content)).title()
			if guess.author != guesser:
				return False
			elif guessFormatted == answer:
				return True
			elif guessFormatted != answer:
				raise KeyError
		
		guesses = 0
		while guesses <= 2:
			
			try: 
				guessAnswer = await self.client.wait_for("message", timeout=10, check=check)
				msg = "{}, correct! You have earned 5{}".format(ctx.message.author.mention, eAmulet)
				await ctx.channel.send(msg)
				guesses = 5
				
				with open("../data/users.json", "r") as f:
					users = json.load(f)
					
				users[str(guesser.id)]["amulets"] += 5

				with open("../data/users.json", "w") as f:
					json.dump(users, f, indent="\t")
				
				await msgQuestion.delete()
				self.client.get_command("encounter").reset_cooldown(ctx)
				
			except asyncio.TimeoutError:
				msg = "{}, time is up! You failed the quiz".format(ctx.message.author.mention)
				await ctx.channel.send(msg)
				guesses = 3
				
				await msgQuestion.delete()
				self.client.get_command("encounter").reset_cooldown(ctx)
				
			except KeyError:
				guesses += 1
				if guesses == 2:
					msg = "{}, wrong answer. You failed the quiz".format(ctx.message.author.mention)
					await ctx.channel.send(msg)
					await msgQuestion.delete()
					self.client.get_command("encounter").reset_cooldown(ctx)
				
				elif guesses == 1:
					msg = "{}, wrong answer! 1 more try left.".format(ctx.message.author.mention)
					await ctx.channel.send(msg)
					
	async def treasure_roll(self, user, ctx):
		with open("../data/rewards.json", "r") as f:
			rewards = json.load(f)
		
		roll = random.randint(1,6)
		
		offer_item = tuple(dict.keys(rewards[str(roll)]["offer"]))[0]
		offer_amount = tuple(dict.values(rewards[str(roll)]["offer"]))[0]
		cost_item = tuple(dict.keys(rewards[str(roll)]["cost"]))[0]
		cost_amount = tuple(dict.values(rewards[str(roll)]["cost"]))[0]
		
		embed = discord.Embed(color = 0xffff80, description = "A treasure box containing {:,d}{}\nIt opens using {:,d}{}".format(offer_amount, self.getEmoji(offer_item), cost_amount, self.getEmoji(cost_item)))
		embed.set_footer(text = "Found by {}".format(user.name), icon_url=user.avatar_url)

		msg = await ctx.channel.send(embed=embed)
		await msg.add_reaction("✅")
		
		def check(reaction, user):
			return user == ctx.author and str(reaction.emoji) == "✅"
		
		try:
			reaction, user = await self.client.wait_for("reaction_add", timeout=8.0, check=check)
			
		except asyncio.TimeoutError:
			msg = "{}, the treasure you found turned into ashes :fire:".format(user.mention)
			await ctx.channel.send(msg)
			self.client.get_command("encounter").reset_cooldown(ctx)
		else:
			await self.treasure_claim(user, offer_item, offer_amount, cost_item, cost_amount, ctx)

	async def treasure_claim(self, user, offer_item, offer_amount, cost_item, cost_amount, ctx):
		with open("../data/users.json", "r") as f:
			users = json.load(f)
		if users[str(user.id)][cost_item] > cost_amount:
			users[str(user.id)][offer_item] += offer_amount
			users[str(user.id)][cost_item] -= cost_amount
			msg = "{}, you have successfully exchanged!".format(user.mention)
			await ctx.channel.send(msg)
			with open("../data/users.json", "w") as f:
				json.dump(users, f, indent="\t")
			self.client.get_command("encounter").reset_cooldown(ctx)
		else:
			msg = "{}, you do not have sufficient {}.".format(user.mention, cost_item)
			await ctx.channel.send(msg)
			self.client.get_command("encounter").reset_cooldown(ctx)
		
	async def boss_roll(self, user, ctx):
		with open("../data/boss.json", "r") as f:
			boss = json.load(f)
	
		bossesListAlive = []
		
		for rareBoss in bossesList:
			if boss[rareBoss]["discoverer"] == "None" or boss[rareBoss]["current_hp"] > 0:
				bossesListAlive.append(rareBoss)
			
		bossDiscovered = random.choice(bossesListAlive)
		
		if boss[bossDiscovered]["discoverer"] == "None":
			await self.boss_create(user, bossDiscovered)

		with open("../data/boss.json", "r") as f:
			boss = json.load(f)
			
		bossLvl = boss[bossDiscovered]["level"]
		bossTotalHP = boss[bossDiscovered]["total_hp"]
		bossCurentHP = boss[bossDiscovered]["current_hp"]
		bossDamageCAP = boss[bossDiscovered]["damage_cap"]
		bossBaseDMG = boss[bossDiscovered]["total_hp"]*0.02
		bossURL = boss[bossDiscovered]["boss_url"]
			
		embed = discord.Embed(color = 0xffff80, 
			description = "The Rare Boss `{}` has been triggered!\nBoss Level: `{}`\nRemaining Hp: `{}%`\n\nMax players: 10\nClick the 🏁 to participate in the assembly!".format(bossDiscovered, bossLvl, round(((bossCurentHP/bossTotalHP)*100),2)))
		embed.set_thumbnail(url = bossURL)
		embed.set_footer(text = "Discovered by {}".format(user.name), icon_url=user.avatar_url)

		await asyncio.sleep(3)
		msg = await ctx.channel.send(embed=embed)
		await msg.add_reaction("🏁")
		
		timerSec = 180
		countPlayers = 0
		assemblyPlayers = []
		
		def assemblyCheck(reaction, user):
			return  user != self.client.user and str(reaction.emoji) == "🏁"
		
		while countPlayers < 11:
			try:
				reaction, user = await self.client.wait_for("reaction_add", timeout=timerSec, check=assemblyCheck)
			
			except asyncio.TimeoutError:
				await ctx.channel.send(":crossed_flags: Assembly ends!")
				countPlayers += 15
			
			else:
				if not str(user.id) in assemblyPlayers: 
					with open("../data/boss.json", "r") as f:
						boss = json.load(f)
					
					if not str(user.id) in boss[bossDiscovered]["challengers"]:
						boss[bossDiscovered]["challengers"][str(user.id)] = 0
						boss[bossDiscovered]["rewards"]["medals"] += 15
						boss[bossDiscovered]["rewards"]["jades"] += 50
						boss[bossDiscovered]["rewards"]["experience"] += 50
						boss[bossDiscovered]["rewards"]["coins"] += 50000			
					
					with open("../data/boss.json", "w") as f:
						json.dump(boss, f, indent="\t")
					assemblyPlayers.append(str(user.id))
					timerSec = timerSec / 1.20
					
					msg = "{} joins the assembly! :checkered_flag: {}/10 players; :alarm_clock:{} seconds before closing!".format(user.mention, (countPlayers+1), round(timerSec))
					await ctx.channel.send(msg)
				else: 
					msg = "{}, you already joined the assembly.".format(user.mention)
					await ctx.channel.send(msg)
				countPlayers += 1
		
		if len(assemblyPlayers) == 0:
			msg = ":x: No players joined the assembly! Rare Boss {} fled.".format(bossDiscovered)
			await asyncio.sleep(3)
			await ctx.channel.send(msg)
			self.client.get_command("encounter").reset_cooldown(ctx)
		else:
			msg = ":video_game: Battle with {} starts!".format(bossDiscovered)
			await asyncio.sleep(3)
			await ctx.channel.send(msg)
			async with ctx.channel.typing():
				await asyncio.sleep(3)
				await self.boss_assembly(boss, bossDiscovered, user, assemblyPlayers, bossDamageCAP, bossBaseDMG, bossURL, ctx)

	async def boss_create(self, user, bossDiscovered):
		with open("../data/users.json", "r") as f:
			users = json.load(f)
		
		bossLvl = users[str(user.id)]["level"] + 60
		guildMedalTotal = 0
		
		for member in users.keys():
			guildMedalTotal += users[member]["medals"]
		
		with open("../data/boss.json", "r") as f:
			boss = json.load(f)
			
		boss[bossDiscovered]["discoverer"] = str(user.id)
		boss[bossDiscovered]["level"] = bossLvl
		boss[bossDiscovered]["total_hp"] = round(guildMedalTotal*(1+(bossLvl/100)),0)
		boss[bossDiscovered]["current_hp"] = round(guildMedalTotal*(1+(bossLvl/100)),0)
		boss[bossDiscovered]["damage_cap"] = round(guildMedalTotal*(1+(bossLvl/100))*0.2,0)
		boss[bossDiscovered]["rewards"] = {}
		boss[bossDiscovered]["rewards"]["medals"] = 100
		boss[bossDiscovered]["rewards"]["experience"] = 250
		boss[bossDiscovered]["rewards"]["coins"] = 1000000
		boss[bossDiscovered]["rewards"]["jades"] = 500
		
		with open("../data/boss.json", "w") as f:
			json.dump(boss, f, indent="\t")

	async def boss_assembly(self, boss, bossDiscovered, user, assemblyPlayers, bossDamageCAP, bossBaseDMG, bossURL, ctx):
		with open("../data/users.json", "r") as f:
			users = json.load(f)
		
		damagePlayers = []

		for player in assemblyPlayers:
			playerDMG = bossBaseDMG + ((users[player]["medals"])*(1+((users[player]["level"])/100)))
			if playerDMG > bossDamageCAP:
				playerDMG = bossDamageCAP
			damagePlayers.append(playerDMG)
			boss[bossDiscovered]["challengers"][player] += round(playerDMG,0)
			boss[bossDiscovered]["current_hp"] -= round(playerDMG,0)
			
			msg = "{} {} {}, dealing {} damage!".format(self.client.get_user(int(player)).mention, random.choice(attackVerb), bossDiscovered, round(playerDMG))
			await ctx.channel.send(msg)
			await asyncio.sleep(3)
		
		
		# Boss HP no less than 0
		if boss[bossDiscovered]["current_hp"] <= 0:
			boss[bossDiscovered]["current_hp"] = 0

		with open("../data/boss.json", "w") as f:
			json.dump(boss, f, indent="\t")
				
		await self.boss_check(assemblyPlayers, bossDiscovered, bossURL, ctx)
		
	async def boss_check(self, assemblyPlayers, bossDiscovered, bossURL, ctx):
		with open("../data/boss.json", "r") as f:
			boss = json.load(f)
		
		if boss[bossDiscovered]["current_hp"] > 0:
			bossCurentHP = boss[bossDiscovered]["current_hp"]
			bossJadeSteal = round(boss[bossDiscovered]["rewards"]["jades"]*0.05)
			bossCoinSteal = round(boss[bossDiscovered]["rewards"]["coins"]*0.075)
			
			description1 = ":dash: Rare Boss {} has fled with {} remaining Hp".format(bossDiscovered, round(bossCurentHP))
			description2 = ":money_with_wings: Stealing {:,d}{} and {}{}each from its attackers!".format(bossJadeSteal ,guild.eJade, bossCoinSteal, guild.eCoin)
			
			embed = discord.Embed(color=0xffff80, description=description1+"\n"+description2)
			embed.set_thumbnail(url=bossURL)
			
			await self.boss_steal(assemblyPlayers, bossJadeSteal, bossCoinSteal)
			await asyncio.sleep(3)
			
			with open("../data/boss.json", "r") as f:
				boss = json.load(f)
			
			boss[bossDiscovered]["rewards"]["jades"] += bossJadeSteal
			boss[bossDiscovered]["rewards"]["coins"] += bossCoinSteal
			
			with open("../data/boss.json", "w") as f:
				json.dump(boss, f, indent="\t")
			
			await ctx.channel.send(embed=embed)
			
			self.client.get_command("encounter").reset_cooldown(ctx)
		
		else: 
			challengersDMG = sum(list(boss[bossDiscovered]["challengers"].values()))
			challengers = []
			distibution = []
				
			for x in boss[bossDiscovered]["challengers"]:
				challengers.append(x)
				distibution.append(round(((boss[bossDiscovered]["challengers"][x])/challengersDMG),2))
			
			bossCoins = (boss[bossDiscovered]["rewards"]["coins"])
			bossJades = (boss[bossDiscovered]["rewards"]["jades"])
			bossMedals = (boss[bossDiscovered]["rewards"]["medals"])
			bossEXP = (boss[bossDiscovered]["rewards"]["experience"])
			
			bossCoinsUsers = [i * bossCoins for i in distibution]
			bossJadesUsers = [i * bossJades for i in distibution]
			bossMedalsUsers = [i * bossMedals for i in distibution]
			bossEXPUsers = [i * bossEXP for i in distibution]
			
			rewardsZip = list(zip(challengers, bossCoinsUsers, bossJadesUsers, bossMedalsUsers, bossEXPUsers, distibution))
			
			msg = ":bow_and_arrow: Rare Boss {} has been defeated!".format(bossDiscovered)
			await ctx.channel.send(msg)
			
			await self.boss_defeat(bossDiscovered, boss, rewardsZip, bossURL, ctx)
			
	async def boss_defeat(self, bossDiscovered, boss, rewardsZip, bossURL, ctx):

		with open("../data/boss.json", "r") as f:
			boss = json.load(f)
			
		discoverer = boss[bossDiscovered]["discoverer"]
		
		with open("../data/users.json", "r") as f:
			users = json.load(f)
		
		
		embed = discord.Embed(color=0xffff80, title=":confetti_ball: Boss Defeat Rewards!")
		embed.set_thumbnail(url=bossURL)
		
		for reward in rewardsZip:
			users[[reward][0][0]]["coins"] += round([reward][0][1])
			users[[reward][0][0]]["jades"] += round([reward][0][2])
			users[[reward][0][0]]["medals"] += round([reward][0][3])
			users[[reward][0][0]]["experience"] += round([reward][0][4])
			embed.add_field(name = "{}, {}%".format(self.client.get_user(int([reward][0][0])).name, round([reward][0][5]*100,2)), inline = True,
				value = '{:,d}{}, {}{}, {}{}, {}:arrow_heading_up:'.format(round([reward][0][1]), guild.eCoin, round([reward][0][2]), guild.eJade, round([reward][0][3]), guild.eMedal, round([reward][0][4])))
		
		users[discoverer]["jades"] += 100
		users[discoverer]["coins"] += 50000
		users[discoverer]["medals"] += 15
		users[discoverer]["experience"] += 100
			
		await asyncio.sleep(3)
		await ctx.channel.send(embed=embed)
		await asyncio.sleep(2)
		
		embed = discord.Embed(color=0xffff80, title=":confetti_ball: Boss Defeat Rewards!")
		embed.set_thumbnail(url=bossURL)
		
		msg = "{} earned an extra 100{}, 50,000{}, 15{} and 100:arrow_heading_up: for initially discovering {}!".format(self.client.get_user(int(discoverer)).mention, guild.eJade, guild.eCoin, guild.eMedal, bossDiscovered)
		
		await ctx.channel.send(msg)
		self.client.get_command("encounter").reset_cooldown(ctx)
		
		with open("../data/users.json", "w") as f:
			json.dump(users, f, indent="\t")

	async def boss_steal(self, assemblyPlayers, bossJadeSteal, bossCoinSteal):
		with open("../data/users.json", "r") as f:
			users = json.load(f)
		
		for player in assemblyPlayers:
			if users[player]["jades"] <= bossJadeSteal:
				users[player]["jades"] = 0
			else:
				users[player]["jades"] -= bossJadeSteal
				
			if users[player]["coins"] <= bossCoinSteal:
				users[player]["coins"] = 0
			else:
				users[player]["coins"] -= bossCoinSteal
				
		with open("../data/users.json", "w") as f:
			json.dump(users, f, indent="\t")

	@commands.command(aliases=['binfo', 'bossinfo'])
	async def boss_info(self, ctx, *args):

		msg = 'Type `;binfo boss_name`\n\n:small_orange_diamond:Tsuchigumo\n:small_orange_diamond:Oboroguruma\n:small_orange_diamond:Odokuro\n:small_orange_diamond:Shinkirou\n:small_orange_diamond:Namazu'
		with open('../data/boss.json', 'r') as f:
			boss = json.load(f)	
		try:
			query = args[0].capitalize()
			discoverer = boss[query]['discoverer']
			user = self.client.get_user(int(discoverer))
			level = boss[query]['level']
			total_hp = boss[query]['total_hp']
			current_hp = boss[query]['current_hp']
			medals = boss[query]['rewards']['medals']
			experience = boss[query]['rewards']['experience']
			coins = boss[query]['rewards']['coins']
			jades = boss[query]['rewards']['jades']
			
			msg = 'Rare Boss {} Stats:\n```Discoverer: {}\n     Level: {}\n  Total Hp: {}\nCurrent Hp: {}\n    Medals: {}\n     Jades: {}\n     Coins: {}\nExperience: {}```'.format(query, user.name, level, total_hp, current_hp, medals, jades, coins, experience)
			await ctx.channel.send(msg)
		except IndexError as error: 
			await ctx.channel.send(msg)
		except KeyError as error:
			msg = 'Please retry your query.'
			await ctx.channel.send(msg)

def setup(client):
	client.add_cog(Encounter(client))