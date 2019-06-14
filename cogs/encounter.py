"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import discord, json, random, asyncio
from cogs.mongo.db import users, daily, boss
from discord.ext import commands

demon = ["Tsuchigumo", "Odokuro", "Shinkirou", "Oboroguruma", "Namazu"]

# Lists startup
attack_list = open("lists/attack.lists")
attack_verb = attack_list.read().splitlines()
attack_list.close()

class Encounter(commands.Cog):
	
	def __init__(self, client):
		self.client = client
	
	def getEmoji(self, item):
		if item == "jades":
			return "<:jade:555630314282811412>"
		if item == "coins":
			return "<:coin:573071121495097344>"
		if item == "medals":
			return "<:medal:573071121545560064>"
		if item == "realm_ticket":
			return "🎟"		
		if item == "amulets":
			return "<:amulet:573071120685596682>"

	@commands.command(aliases=["enc"])
	@commands.cooldown(1, 180, commands.BucketType.guild)
	@commands.guild_only()
	async def encounter(self, ctx):
		user = ctx.author
		
		# Check user tickets first
		if daily.find_one({"key": "daily"}, {"_id": 0, "{}.encounter_pass".format(user.id): 1})[str(user.id)]["encounter_pass"] > 0:
			daily.update_one({"key": "daily"}, {"$inc": {"{}.encounter_pass".format(user.id): -1}})
			await self.encounter_roll(user, ctx)
		
		else:
			msg = "You have used up all your :ticket:"
			await ctx.channel.send(msg)
			self.client.get_command("encounter").reset_cooldown(ctx)

	async def encounter_roll(self, user, ctx):	
		async with ctx.channel.typing():
			msg = "🔍Searching the depths of Netherworld..."
			await ctx.channel.send(msg)
			
			survivability = boss.find({"current_hp": {"$gt": 0}}, {"_id": 1}).count()
			discoverability = boss.find({"discoverer": {"$eq": 0}}, {"_id": 1}).count()
			
			if survivability > 0 or discoverability > 0:
				roll = random.randint(0,100)
				
				if roll <= 20:	
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
		
		with open("data/quiz.json", "r") as f:
			quiz = json.load(f)
		
		guesser = ctx.author
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
		
		msg_question = await ctx.channel.send(embed=embed)
			
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
				msg = "{}, correct! You have earned 5{}".format(ctx.message.author.mention, "<:amulet:573071120685596682>")
				await ctx.channel.send(msg)
				guesses = 5
				
				users.update_one({"user_id": str(guesser.id)}, {"$inc": {"amulets": 5}})
	
				await msg_question.delete()
				self.client.get_command("encounter").reset_cooldown(ctx)
				return
				
			except asyncio.TimeoutError:
				msg = "{}, time is up! You failed the quiz".format(ctx.message.author.mention)
				await ctx.channel.send(msg)
				guesses = 3
				
				await msg_question.delete()
				self.client.get_command("encounter").reset_cooldown(ctx)
				
			except KeyError:
				guesses += 1
				if guesses == 2:
					msg = "{}, wrong answer. You failed the quiz".format(ctx.message.author.mention)
					await ctx.channel.send(msg)
					await msg_question.delete()
					self.client.get_command("encounter").reset_cooldown(ctx)
				
				elif guesses == 1:
					msg = "{}, wrong answer! 1 more try left.".format(ctx.message.author.mention)
					await ctx.channel.send(msg)
					
	async def treasure_roll(self, user, ctx):
		with open("data/rewards.json", "r") as f:
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
		
		if users.find_one({"user_id": str(user.id)}, {"_id": 0, cost_item: 1})[cost_item] >= cost_amount:
		
			users.update_one({"user_id": str(user.id)}, {"$inc": {offer_item: offer_amount, cost_item: -cost_amount}})
		
			msg = "{}, you have successfully exchanged!".format(user.mention)
			await ctx.channel.send(msg)
			
			self.client.get_command("encounter").reset_cooldown(ctx)
		else:
			msg = "{}, you do not have sufficient {}.".format(user.mention, cost_item)
			await ctx.channel.send(msg)
			self.client.get_command("encounter").reset_cooldown(ctx)
		
	async def boss_roll(self, user, ctx):
		
		boss_alive = []
		
		for boss_name in boss.find({"$or": [{"discoverer": {"$eq": 0}}, {"current_hp": {"$gt": 0}}]}, {"_id": 0, "boss": 1}):
			boss_alive.append(boss_name["boss"])
			
		boss_select = random.choice(boss_alive)		
		if boss.find_one({"boss": boss_select}, {"_id": 0, "discoverer": 1})["discoverer"] == 0:
			await self.boss_create(user, boss_select)
		
		boss_profile = boss.find_one({"boss": boss_select}, {"_id": 0, "challengers": 1, "level": 1, "total_hp": 1, "current_hp": 1, "damage_cap": 1, "boss_url": 1})
		
		boss_lvl = boss_profile["level"]
		boss_totalhp = boss_profile["total_hp"]
		boss_currenthp = boss_profile["current_hp"]
		boss_damagecap = boss_profile["damage_cap"]
		boss_basedmg = boss_profile["total_hp"]*0.02
		boss_url = boss_profile["boss_url"]
		boss_challengers = boss_profile["challengers"]
			
		embed = discord.Embed(color = 0xffff80, 
			description = "The Rare Boss `{}` has been triggered!\nBoss Level: `{}`\nRemaining Hp: `{}%`\n\nMax players: 10\nClick the 🏁 to participate in the assembly!".format(boss_select, boss_lvl, round(((boss_currenthp/boss_totalhp)*100),2)))
		embed.set_thumbnail(url = boss_url)
		embed.set_footer(text = "Discovered by {}".format(user.name), icon_url=user.avatar_url)

		await asyncio.sleep(2)
		msg = await ctx.channel.send(embed=embed)
		await msg.add_reaction("🏁")
		
		timer = 5
		count_players = 0
		assembly_players = []
		
		def check(reaction, user):
			return  user != self.client.user and str(reaction.emoji) == "🏁"
		
		while count_players < 11:
			try:
				reaction, user = await self.client.wait_for("reaction_add", timeout=timer, check=check)
			
			except asyncio.TimeoutError:
				await ctx.channel.send(":crossed_flags: Assembly ends!")
				count_players += 15
			
			else:
				if not str(user.id) in assembly_players: 
					
					if boss.find_one({"boss": boss_select, "challengers.user_id": str(user.id)}, {"_id": 1}) == None:
						
						boss.update_one({"boss": boss_select}, {"$push": {"challengers": {"user_id": str(user.id), "damage": 0}}})
						boss.update_one({"boss": boss_select}, {"$inc": {"rewards.medals": 15, "rewards.jades": 50, "rewards.experience": 50, "rewards.coins": 50000}})
					
					assembly_players.append(str(user.id))
					timer = timer / 1.20
					
					msg = "{} joins the assembly! :checkered_flag: {}/10 players; :alarm_clock:{} seconds before closing!".format(user.mention, (count_players+1), round(timer))
					await ctx.channel.send(msg)
				else: 
					msg = "{}, you already joined the assembly.".format(user.mention)
					await ctx.channel.send(msg)
				count_players += 1
		
		if len(assembly_players) == 0:
			msg = ":x: No players joined the assembly! Rare Boss {} fled.".format(boss_select)
			await asyncio.sleep(3)
			await ctx.channel.send(msg)
			self.client.get_command("encounter").reset_cooldown(ctx)
		else:
			msg = ":video_game: Battle with {} starts!".format(boss_select)
			await asyncio.sleep(3)
			await ctx.channel.send(msg)
			async with ctx.channel.typing():
				await asyncio.sleep(3)
				await self.boss_assembly(boss, boss_select, user, assembly_players, boss_damagecap, boss_basedmg, boss_url, ctx)

	async def boss_create(self, user, boss_select):
		
		discoverer_level = users.find_one({"user_id": str(user.id)}, {"_id": 0, "level": 1})["level"]
		boss_lvl = discoverer_level + 60
		
		for y in users.aggregate([{ "$group": {"_id" : "", "medals": { "$sum": "$medals"}}}, { "$project": {"_id": 0}}]):
			total_medals = y["medals"]
		
		boss.update_one({"boss": boss_select}, {
			"$set": {
			"discoverer": str(user.id), 
			"level": boss_lvl, 
			"total_hp": round(total_medals*(1+(boss_lvl/100)),0), 
			"current_hp": round(total_medals*(1+(boss_lvl/100)),0),
			"damage_cap": round(total_medals*(1+(boss_lvl/100))*0.2,0),
			"rewards.medals": 100, 
			"rewards.jades": 500, 
			"rewards.experience": 250, 
			"rewards.coins": 1000000
			}})

	async def boss_assembly(self, boss, boss_select, user, assembly_players, boss_damagecap, boss_basedmg, boss_url, ctx):
		
		# Damage calculation 
		damage_players = []
		for player in assembly_players:
			
			player_medals = users.find_one({"user_id": player}, {"_id": 0, "medals": 1})["medals"]
			player_level = users.find_one({"user_id": player}, {"_id": 0, "level": 1})["level"]
			player_dmg = boss_basedmg + ((player_medals)*(1+((player_level)/100)))
			
			if player_dmg > boss_damagecap:
				player_dmg = boss_damagecap
			
			damage_players.append(player_dmg)
			
			boss.update_one({"boss": boss_select, "challengers.user_id": player}, {
			"$inc": {
			"challengers.$.damage": round(player_dmg, 0),
			"current_hp": -round(player_dmg, 0)
			}})

			msg = "{} {} {}, dealing {} damage!".format(self.client.get_user(int(player)).mention, random.choice(attack_verb), boss_select, round(player_dmg))
			await ctx.channel.send(msg)
			await asyncio.sleep(3)
		
		# Boss HP no less than 0
		boss_profile_new = boss.find_one({"boss": boss_select}, {"_id": 0, "current_hp": 1, "rewards": 1, "discoverer": 1})
		
		if boss_profile_new["current_hp"] <= 0:
			boss.update_one({"boss": boss_select}, {"$set": {"current_hp":0}})

		await self.boss_check(assembly_players, boss_select, boss_url, boss_profile_new, ctx)
		
	async def boss_check(self, assembly_players, boss_select, boss_url, boss_profile_new, ctx):
		
		boss_currenthp = boss.find_one({"boss": boss_select}, {"_id": 0, "current_hp": 1})["current_hp"]
		if boss_currenthp > 0:
			
			boss_jadesteal = round(boss_profile_new["rewards"]["jades"]*0.05)
			boss_coinsteal = round(boss_profile_new["rewards"]["coins"]*0.075)
			
			description1 = ":dash: Rare Boss {} has fled with {} remaining Hp".format(boss_select, round(boss_currenthp))
			description2 = ":money_with_wings: Stealing {:,d}{} & {}{} each from its attackers!".format(boss_jadesteal, "<:jade:555630314282811412>", boss_coinsteal, "<:coin:573071121495097344>")
			
			embed = discord.Embed(color=0xffff80, description=description1+"\n"+description2)
			embed.set_thumbnail(url=boss_url)
			
			await self.boss_steal(assembly_players, boss_jadesteal, boss_coinsteal)
			await asyncio.sleep(3)
			
			boss.update_one({"boss": boss_select}, {
			"$inc": {
			"rewards.jades": boss_jadesteal,
			"rewards.coins": boss_coinsteal
			}})
			
			await ctx.channel.send(embed=embed)
			self.client.get_command("encounter").reset_cooldown(ctx)
		
		else: 
			
			for damage in boss.aggregate([{"$match": {"boss": boss_select}}, {"$unwind": {"path": "$challengers"}}, {"$group": {"_id": "", "total_damage": {"$sum": "$challengers.damage"}}}, {"$project": {"_id": 0}}]):
				players_dmg = damage["total_damage"]
			
			challengers = []
			distribution = []
			
			for data in boss.aggregate([{"$match": {"boss": boss_select}}, {"$unwind": {"path": "$challengers"}},{"$project": {"_id": 0, "challengers": 1}}]):
				challengers.append(data["challengers"]["user_id"])
				distribution.append(round(((data["challengers"]["damage"])/players_dmg),2))
			
			boss_coins = boss_profile_new["rewards"]["coins"]
			boss_jades = boss_profile_new["rewards"]["jades"]
			boss_medals = boss_profile_new["rewards"]["medals"]
			boss_exp = boss_profile_new["rewards"]["experience"]
			
			boss_coins_user = [i * boss_coins for i in distribution]
			boss_jades_users = [i * boss_jades for i in distribution]
			boss_medals_users = [i * boss_medals for i in distribution]
			boss_exp_users = [i * boss_exp for i in distribution]
			
			rewards_zip = list(zip(challengers, boss_coins_user, boss_jades_users, boss_medals_users, boss_exp_users, distribution))
			msg = ":bow_and_arrow: Rare Boss {} has been defeated!".format(boss_select)
			await ctx.channel.send(msg)
			
			await self.boss_defeat(boss_select, boss, rewards_zip, boss_url, boss_profile_new, ctx)
			
			
	async def boss_defeat(self, boss_select, boss, rewards_zip, boss_url, boss_profile_new, ctx):
		
		discoverer = boss_profile_new["discoverer"]
		embed = discord.Embed(color=0xffff80, title=":confetti_ball: Boss Defeat Rewards!")
		embed.set_thumbnail(url=boss_url)
		
		for reward in rewards_zip:
			users.update_one({"user_id": [reward][0][0]}, {"$inc": {"jades": round([reward][0][2]), "coins": round([reward][0][1]), "medals": round([reward][0][3]), "experience": round([reward][0][4])}})
			embed.add_field(name = "{}, {}%".format(self.client.get_user(int([reward][0][0])).name, round([reward][0][5]*100,2)), inline = True,
				value = "{:,d}{}, {}{}, {}{}, {} :arrow_heading_up:".format(round([reward][0][1]), "<:coin:573071121495097344>", round([reward][0][2]), "<:jade:555630314282811412>", round([reward][0][3]), "<:medal:573071121545560064>", round([reward][0][4])))
		
		users.update_one({"user_id": discoverer}, {"$inc": {"jades": 100, "coins": 50000, "medals": 15, "experience": 100}})
		
		await asyncio.sleep(3)
		await ctx.channel.send(embed=embed)
		await asyncio.sleep(2)
		
		embed = discord.Embed(color=0xffff80, title=":confetti_ball: Boss Defeat Rewards!")
		embed.set_thumbnail(url=boss_url)
		msg = "{} earned an extra 100{}, 50,000{}, 15{} and 100 :arrow_heading_up: for initially discovering {}!".format(self.client.get_user(int(discoverer)).mention, "<:jade:555630314282811412>", "<:coin:573071121495097344>", "<:medal:573071121545560064>", boss_select)
		
		await ctx.channel.send(msg)
		self.client.get_command("encounter").reset_cooldown(ctx)

	async def boss_steal(self, assembly_players, boss_jadesteal, boss_coinsteal):
		
		for player_id in assembly_players:
			
			if users.find_one({"user_id": player_id}, {"_id": 0, "jades": 1})["jades"] <= boss_jadesteal:
				users.update_one({"user_id": player_id}, {"$set": {"jades": 0}})
			else:
				users.update_one({"user_id": player_id}, {"$inc": {"jades": -boss_jadesteal}})
			
			if users.find_one({"user_id": player_id}, {"_id": 0, "coins": 1})["coins"] <= boss_coinsteal:
				users.update_one({"user_id": player_id}, {"$set": {"coins": 0}})
			else:
				users.update_one({"user_id": player_id}, {"$inc": {"coins": -boss_coinsteal}})

	@commands.command(aliases=["binfo", "bossinfo"])
	async def boss_info(self, ctx, *args):
		try:
			query = args[0].capitalize()
			boss_profile = boss.find_one({"boss": query}, {"_id": 0, "level": 1, "total_hp": 1, "current_hp": 1, "rewards": 1, "discoverer": 1})
			discoverer = boss_profile["discoverer"]
			user = self.client.get_user(int(discoverer))
			level = boss_profile["level"]
			total_hp = boss_profile["total_hp"]
			current_hp = boss_profile["current_hp"]
			medals = boss_profile["rewards"]["medals"]
			experience = boss_profile["rewards"]["experience"]
			coins = boss_profile["rewards"]["coins"]
			jades = boss_profile["rewards"]["jades"]
			
			msg = "Rare Boss {} Stats:\n```Discoverer: {}\n     Level: {}\n  Total Hp: {}\nCurrent Hp: {}\n    Medals: {}\n     Jades: {}\n     Coins: {}\nExperience: {}```".format(query, user.name, level, total_hp, current_hp, medals, jades, coins, experience)
			await ctx.channel.send(msg)
		
		except IndexError as error: 
			description = ":small_orange_diamond:Tsuchigumo\n:small_orange_diamond:Oboroguruma\n:small_orange_diamond:Odokuro\n:small_orange_diamond:Shinkirou\n:small_orange_diamond:Namazu\n\nUse `;binfo <boss_name>`"
			
			embed = discord.Embed(color=0xffff80, title="Show Rare Boss Stats", description=description)
			embed.set_thumbnail(url=self.client.user.avatar_url)
			await ctx.channel.send(embed=embed)
		
		except KeyError as error:
			msg = "Boss {} is undiscovered".format(query)
			await ctx.channel.send(msg)

def setup(client):
	client.add_cog(Encounter(client))