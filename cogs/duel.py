"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import discord, json, asyncio, random
from discord.ext import commands
from config.guild import guildArena

specialty = {'Earth': 1, 'Storm': 2, 'Tech': 3, 'Order': 4, 'Chaos': 5, 'Fire': 6, 'Frost': 7, 'Life': 8, 'Death': 9}

class Duel(commands.Cog):
	
	def __init__(self, client):
		self.client = client
	
	@commands.command(aliases=["d"])
	@commands.cooldown(1, 120, commands.BucketType.guild)
	@commands.guild_only()
	async def duel(self, ctx, user: discord.User=None):
		await ctx.message.add_reaction("✅")
		
		duelist1 = ctx.author
		duelist2 = user
		
		# Checks if no user
		if user == None:
			msg = "{}, please mention a user to duel".format(ctx.author.mention)
			await ctx.channel.send(msg)
			self.client.get_command("duel").reset_cooldown(ctx)
			
		else:
			# Checks if user duels themselves
			if duelist1 == duelist2:
				msg = "{}, you cannot duel yourself.".format(ctx.author.mention)
				await ctx.channel.send(msg)
				self.client.get_command("duel").reset_cooldown(ctx)
			
			# Checks if user duels the bot
			if duelist2 == self.client.user:
				msg = "{}, I\"m just the narrator.. whyy.. would you do that?".format(ctx.author.mention)
				await ctx.channel.send(msg)
				self.client.get_command("duel").reset_cooldown(ctx)
			
			else: 	
				# Wait for confirmation
				def check(reaction, duelist2):
					return duelist2.id == user.id and str(reaction.emoji) == "✅"
				try:
					reaction, duelist2 = await self.client.wait_for("reaction_add", timeout=10.0, check=check)
				
				except asyncio.TimeoutError:
					msg = "{}, Your challenge was not accepted.".format(duelist1.mention)
					await ctx.channel.send(msg)
					self.client.get_command("duel").reset_cooldown(ctx)
				
				else:
					msg = "{} has accepted the challenge!".format(duelist2.mention)
					await ctx.channel.send(msg)
					await self.duel_create(duelist1, duelist2, ctx)
					await asyncio.sleep(2)
					
					round = 0
					pool1 = []
					pool2 = []
					duelist_channel_id1 = 0
					duelist_channel_id2 = 0
					
					await self.duel_start(duelist1, duelist2, round, pool1, pool2, duelist_channel_id1, duelist_channel_id2, ctx)
					
	async def duel_create(self, duelist1, duelist2, ctx):
		with open("../data/duel.json", "r") as f:
			duel = json.load(f)

		duel[str(ctx.message.id)] = {}
		duel[str(ctx.message.id)]["duelists"] = {}
		duel[str(ctx.message.id)]["duelists"][str(duelist1.id)] = {"Hp" : 15, "shikigami" : {}}
		duel[str(ctx.message.id)]["duelists"][str(duelist2.id)] = {"Hp" : 15, "shikigami" : {}}
		duel[str(ctx.message.id)]["duelists"][str(duelist1.id)]["shikigami"] = {"1": {}, "2": {}, "3": {}, "4": {}, "5": {}}
		duel[str(ctx.message.id)]["duelists"][str(duelist2.id)]["shikigami"] = {"1": {}, "2": {}, "3": {}, "4": {}, "5": {}}
		
		with open("../data/duel.json", "w") as f:
			json.dump(duel, f, indent="\t")
		
		# Stats harvesting
		with open("../data/duel_stats.json", "r") as f:
			duel_stats = json.load(f)
		
		if not str(duelist1.id) in duel_stats:
			duel_stats[str(duelist1.id)] = {}
			duel_stats[str(duelist1.id)]["win"] = 0
			duel_stats[str(duelist1.id)]["lose"] = 0
			duel_stats[str(duelist1.id)]["total"] = 0
			duel_stats[str(duelist1.id)]["pulls"] = {}
			duel_stats[str(duelist1.id)]["pulls"][""] = {"win":0, "lose":0, "total":0}
		
		if not str(duelist2.id) in duel_stats:
			duel_stats[str(duelist2.id)] = {}
			duel_stats[str(duelist2.id)]["win"] = 0
			duel_stats[str(duelist2.id)]["lose"] = 0
			duel_stats[str(duelist2.id)]["total"] = 0
			duel_stats[str(duelist2.id)]["pulls"] = {}
			duel_stats[str(duelist2.id)]["pulls"][""] = {"win":0, "lose":0, "total":0}
		
		with open("../data/duel_stats.json", "w") as f:
			json.dump(duel_stats, f, indent="\t")
		
	async def duel_start(self, duelist1, duelist2, round, pool1, pool2, duelist_channel_id1, duelist_channel_id2, ctx):
		
		round += 1
		arena_channel = self.client.get_channel(guildArena)
		
		if round == 1:
			
			msg = "Drafting phase starts in 10 sec. Duelists, check your :mailbox_with_mail:DM."
			await ctx.channel.send(msg)
			
			msg = "Drafting Phase. You are battling against {}. Let me get the vital information."
		
			await duelist1.send(msg.format(duelist2.name))
			duelist_channel_id1 = duelist1.dm_channel.id
			
			await duelist2.send(msg.format(duelist1.name))
			duelist_channel_id2 = duelist2.dm_channel.id
			
			async with duelist1.dm_channel.typing():
			
				with open("../data/duel_stats.json", "r") as f:
					duel_stats = json.load(f)
					
				stats1 =  []
				stats2 = []
				
				def winrateCalc(x, y):
					try: 
						return round((x / y)*100,2)
					except ZeroDivisionError:
						return 0
							
				win1 = duel_stats[str(duelist1.id)]["win"]
				total1 = duel_stats[str(duelist1.id)]["total"]
				win2 = duel_stats[str(duelist2.id)]["win"]
				total2 = duel_stats[str(duelist2.id)]["total"]
				
				for user in duel_stats:
					for shikigami in duel_stats[user]["pulls"]:
						if user == str(duelist1.id) :
							count1 = duel_stats[user]["pulls"][shikigami]["total"]
							a = duel_stats[user]["pulls"][shikigami]["win"]
							b = duel_stats[user]["pulls"][shikigami]["total"]
							winrate1_1 = winrateCalc(a,b)
							entry1 = (shikigami, count1, winrate1_1)
							stats1.append(entry1)
						if user == str(duelist2.id) :
							count2 = duel_stats[user]["pulls"][shikigami]["total"]
							a = duel_stats[user]["pulls"][shikigami]["win"]
							b = duel_stats[user]["pulls"][shikigami]["total"]
							winrate2_2 = winrateCalc(a,b)
							entry2 = (shikigami, count2, winrate2_2)
							stats2.append(entry2)
				
				most_pick1 = sorted(stats1, key=lambda x: x[1], reverse=True)
				most_win1 = sorted(stats1, key=lambda x: x[2], reverse=True)
				most_lose1 = sorted(stats1, key=lambda x: x[2], reverse=False)

				most_pick2 = sorted(stats2, key=lambda x: x[1], reverse=True)
				most_win2 = sorted(stats2, key=lambda x: x[2], reverse=True)
				most_lose2 = sorted(stats2, key=lambda x: x[2], reverse=False)
				
				embed1=discord.Embed(color=0xac330f, title = "{}\"s Stats".format(duelist2.name), 
					description = "Total games: {}\nTotal Wins: {}\nWin Rate: {}%\n\nMost picked: {}\nMost Wins using: {}\nMost Losses using: {}".format(total2, win2, winrateCalc(win2,total2), most_pick2[0][0], most_win2[0][0], most_lose2[0][0]))
				embed1.set_thumbnail(url=duelist2.avatar_url)
						
				embed2=discord.Embed(color=0xac330f, title = "{}\"s Stats".format(duelist1.name), 
						description = "Total games: {}\nTotal Wins: {}\nWin Rate: {}%\n\nMost picked: {}\nMost Win using: {}\nMost Losses using: {}".format(total1, win1, winrateCalc(win1,total1), most_pick1[0][0], most_win1[0][0], most_lose1[0][0]))
				embed2.set_thumbnail(url=duelist1.avatar_url)
					
				await asyncio.sleep(3)
				await duelist1.send(embed=embed1)
				await duelist2.send(embed=embed2)
				
			with open("../data/users.json", "r") as f:
				users = json.load(f)
			
			# Building a list out of the duelists shikigami pool
			async with duelist1.dm_channel.typing():
				
				for rarity in users[str(duelist1.id)]["shikigami"]:
					for shikigami in users[str(duelist1.id)]["shikigami"][rarity]:
						if users[str(duelist1.id)]["shikigami"][rarity][shikigami]["owned"] != 0:
							pool1.append(shikigami)
			
				embed1=discord.Embed(color = 0xffff80, title = "{}\"s Shikigamis".format(duelist1.name), 
					description = "{}".format(", ".join(pool1)))
				
			# Sends the shikigami pool to the duelists
			async with duelist2.dm_channel.typing():
			
				for rarity in users[str(duelist2.id)]["shikigami"]:
					for shikigami in users[str(duelist2.id)]["shikigami"][rarity]:
						if users[str(duelist2.id)]["shikigami"][rarity][shikigami]["owned"] != 0:
							pool2.append(shikigami)
				
				embed2 = discord.Embed(color = 0xffff80, title="{}\"s Shikigamis".format(duelist2.name), 
					description = "{}".format(", ".join(pool2)))
				
			await asyncio.sleep(5)
			await duelist1.send(embed=embed1)
			await duelist2.send(embed=embed2)

			await self.duel_pick(duelist1, duelist2, round, pool1, pool2, duelist_channel_id1, duelist_channel_id2, ctx)
		
		if 5 > round > 1:
			msg = ":video_game: Round {} drafting. Duelists, check your :mailbox_with_mail:DM.".format(round)
			await arena_channel.send(msg)
			
			await self.duel_pick(duelist1, duelist2, round, pool1, pool2, duelist_channel_id1, duelist_channel_id2, ctx)
			
		if round == 5:
			msg = ":video_game: Last round drafting. Duelists, check your :mailbox_with_mail:DM."
			await arena_channel.send(msg)
			await self.duel_pick(duelist1, duelist2, round, pool1, pool2, duelist_channel_id1, duelist_channel_id2, ctx)
		
		if round == 6:
			await self.duel_end(duelist1, duelist2, round, pool1, pool2, duelist_channel_id1, duelist_channel_id2, ctx)

	async def duel_end(self, duelist1, duelist2, round, pool1, pool2, duelist_channel_id1, duelist_channel_id2, ctx):
		
		arena_channel = self.client.get_channel(guildArena)
		
		with open("../data/duel.json", "r") as f:
			duel = json.load(f)
			
		with open("../data/duel_stats.json", "r") as f:
			duel_stats = json.load(f)
			
		duelist1_hp_final = duel[str(ctx.message.id)]["duelists"][str(duelist1.id)]["Hp"]
		duelist2_hp_final = duel[str(ctx.message.id)]["duelists"][str(duelist2.id)]["Hp"]
		
		duel_stats[str(duelist1.id)]["total"] = +1
		duel_stats[str(duelist2.id)]["total"] = +1
		
		if duelist1_hp_final > duelist2_hp_final :
			duel_stats[str(duelist1.id)]["win"] = +1
			duel_stats[str(duelist2.id)]["lose"] = +1
			msg = "The Duel has ended. ||{} ({} Hp) has won over {} ({} Hp)!||".format(duelist1.mention, duelist1_hp_final, duelist2.mention, duelist2_hp_final)
			await arena_channel.send(msg)
			
		elif duelist1_hp_final < duelist2_hp_final :
			duel_stats[str(duelist1.id)]["lose"] = +1
			duel_stats[str(duelist2.id)]["win"] = +1
			msg = "The Duel has ended. ||{} ({} Hp) has won over {} ({} Hp)!||".format(duelist2.mention, duelist2_hp_final, duelist1.mention, duelist1_hp_final)
			await arena_channel.send(msg)
		
		else :
			msg = "The battle is tie!"
			await arena_channel.send(msg)
			
		with open("../data/duel_stats.json", "w") as f:
			json.dump(duel_stats, f, indent="\t")
		
		self.client.get_command("duel").reset_cooldown(ctx)
		
	async def duel_pick(self, duelist1, duelist2, round, pool1, pool2, duelist_channel_id1, duelist_channel_id2, ctx):
		await asyncio.sleep(5)
		msg1 = "Round {}. You have 20 seconds. Please select your shikigami.".format(round)
		msg2 = "Round {}. Your opponent is picking.".format(round)

		await duelist1.send(msg1)
		await duelist2.send(msg2)
		
		duelist1_select = []
		duelist2_select = []
		
		def check1(select1):
			shikigami1 = (select1.content).title()
			
			if select1.author != duelist1 :
				return False
			
			elif shikigami1 in pool1:
				duelist1_select.append(shikigami1)
				return select1.channel.id == duelist_channel_id1
				
			elif shikigami1 not in pool1:
				raise KeyError
		
		i = 0
		while i < 1 :
		
			try : 
				msg = await self.client.wait_for("message", check=check1, timeout=20)
				await duelist1.send("Round {}. You have selected {}".format(round, msg.content.title()))
				i += 1
			
			except asyncio.TimeoutError:
				shikigami1 = pool1[random.randint(1,len(pool1))-1]
				msg = "Round {}. Time\"s Up! Your shikigami has been randomly selected: {}".format(round, shikigami1)
				duelist1_select.append(shikigami1)
				await duelist1.send(msg)
				i += 1
			except KeyError:
				msg = "You do not have that shikigami nor does it exist. Please try again"
				await duelist1.send(msg)
				
		await duelist2.send(msg1)
		await duelist1.send(msg2)
		
		def check2(select2):
			shikigami2 = (select2.content).title()
			
			if select2.author != duelist2 :
				return False
			
			if shikigami2 in pool2:
				duelist2_select.append(shikigami2)
				return select2.channel.id == duelist_channel_id2 and select2.author== duelist2
				
			elif shikigami2 not in pool2:
				raise KeyError				
		
		i = 0
		while i < 1 :

			try :
				msg = await self.client.wait_for("message", check=check2, timeout=20)	
				await duelist2.send("Round {}. You have selected {}".format(round, msg.content.title()))
				i += 1
					
			except asyncio.TimeoutError:
				shikigami2 = pool2[random.randint(1,len(pool2))-1]
				msg = "Round {}. Time's Up! Your shiki has been randomly selected: {}".format(round, shikigami2)
				duelist2_select.append(shikigami2)
				await duelist2.send(msg)
				i += 1
			except KeyError:
				msg = "You do not have that shikigami nor does it exist. Please try again"
				await duelist2.send(msg)
				i = 0
		
		msg = "Round {}. Battle starts in 10 seconds. Please spectate at <#{}>".format(round, guildArena)
		await duelist1.send(msg)
		await duelist2.send(msg)
		
		await self.duel_shiki_set(duelist1, duelist2, duelist1_select, duelist2_select, round, pool1, pool2, duelist_channel_id1, duelist_channel_id2, ctx)

	async def duel_shiki_set(self, duelist1, duelist2, duelist1_select, duelist2_select, round, pool1, pool2, duelist_channel_id1, duelist_channel_id2, ctx):
		with open("../data/users.json", "r") as f:
			users = json.load(f)
		
		duelist1_select1 = []
		duelist2_select1 = []
		
		for rarity in users[str(duelist1.id)]["shikigami"]:
			for shikigami in users[str(duelist1.id)]["shikigami"][rarity]:
				if shikigami == duelist1_select[0]:
					duelist1_select1.append(shikigami)
					duelist1_select1.append(users[str(duelist1.id)]["shikigami"][rarity][shikigami]["grade"])
					duelist1_select1.append(users[str(duelist1.id)]["shikigami"][rarity][shikigami]["evolved"])
					duelist1_select1.append(rarity)
		
		for rarity in users[str(duelist2.id)]["shikigami"]:
			for shikigami in users[str(duelist2.id)]["shikigami"][rarity]:
				if shikigami == duelist2_select[0]:
					duelist2_select1.append(shikigami)
					duelist2_select1.append(users[str(duelist2.id)]["shikigami"][rarity][shikigami]["grade"])
					duelist2_select1.append(users[str(duelist2.id)]["shikigami"][rarity][shikigami]["evolved"])
					duelist2_select1.append(rarity)
		
		with open("../data/duel.json", "r") as f:
			duel = json.load(f)	
			
			duelist1_currenthp = duel[str(ctx.message.id)]["duelists"][str(duelist1.id)]["Hp"]
			duelist2_currenthp = duel[str(ctx.message.id)]["duelists"][str(duelist2.id)]["Hp"]

			duel[str(ctx.message.id)]["duelists"][str(duelist1.id)]["shikigami"][str(round)][duelist1_select1[0]] = 0
			duel[str(ctx.message.id)]["duelists"][str(duelist1.id)]["shikigami"][str(round)]["grade"] = duelist1_select1[1]
			duel[str(ctx.message.id)]["duelists"][str(duelist1.id)]["shikigami"][str(round)]["evolved"] = duelist1_select1[2]
			
			duel[str(ctx.message.id)]["duelists"][str(duelist2.id)]["shikigami"][str(round)][duelist2_select1[0]] = 0
			duel[str(ctx.message.id)]["duelists"][str(duelist2.id)]["shikigami"][str(round)]["grade"] = duelist2_select1[1]
			duel[str(ctx.message.id)]["duelists"][str(duelist2.id)]["shikigami"][str(round)]["evolved"] = duelist2_select1[2]
		
		with open("../data/duel.json", "w") as f:
			json.dump(duel, f, indent="\t")
		
		await self.duel_process(duelist1, duelist2, duelist1_select1, duelist2_select1, round, duelist1_currenthp, duelist2_currenthp, pool1, pool2, duelist_channel_id1, duelist_channel_id2, ctx)

	async def duel_process(self, duelist1, duelist2, duelist1_select1, duelist2_select1, round, duelist1_currenthp, duelist2_currenthp, pool1, pool2, duelist_channel_id1, duelist_channel_id2, ctx):
		
		await asyncio.sleep(2)
		msg = ":video_game: Round {} begins: {} ({} Hp) :crossed_swords: {} ({} Hp)".format(round, duelist1.name, duelist1_currenthp, duelist2.name, duelist2_currenthp)
		arena_channel = self.client.get_channel(guildArena)
		await arena_channel.send(msg)
		
		def get_specialty(query, shikigami):
			for rarity in shikigami:
				for shiki in shikigami[rarity]:
					if query == shiki:
						return shikigami[rarity][shiki]['specialty']

		def get_specialty_code(query):
			for kind in specialty:
				if query == kind:
					return specialty[kind]		
		
		
		async with ctx.channel.typing(): 
		
			with open("../data/shikigami.json") as f:
				shikigami= json.load(f)
			
			shiki1_specialty = get_specialty(duelist1_select1[0], shikigami)
			shiki2_specialty = get_specialty(duelist2_select1[0], shikigami)
			print(shiki1_specialty)
			print(shiki2_specialty)
			
			shiki1_normal = shikigami[duelist1_select1[3]][duelist1_select1[0]]["skills"]["normal"]
			shiki1_special = shikigami[duelist1_select1[3]][duelist1_select1[0]]["skills"]["special"]
			
			shiki1_specialty_code = get_specialty_code(shiki1_specialty)
			shiki2_specialty_code = get_specialty_code(shiki2_specialty)
			
			shiki2_normal = shikigami[duelist2_select1[3]][duelist2_select1[0]]["skills"]["normal"]
			shiki2_special = shikigami[duelist2_select1[3]][duelist2_select1[0]]["skills"]["special"]
			
			if duelist1_select1[3] == "True":
				shiki1_thumbnail =  shikigami[duelist1_select1[3]][duelist1_select1[0]]["thumbnail"]["evo"]
				bonus_damage1 = 1
			else:
				shiki1_thumbnail =  shikigami[duelist1_select1[3]][duelist1_select1[0]]["thumbnail"]["pre_evo"]
				bonus_damage1 = 0
				
			if duelist2_select1[3] == "True":
				shiki2_thumbnail =  shikigami[duelist2_select1[3]][duelist2_select1[0]]["thumbnail"]["evo"]
				bonus_damage2 = 1
			else:
				shiki2_thumbnail =  shikigami[duelist2_select1[3]][duelist2_select1[0]]["thumbnail"]["pre_evo"]
				bonus_damage2 = 0
			
			with open("../data/duel.json") as f:
				duel = json.load(f)
			
			diff = shiki1_specialty_code - shiki2_specialty_code
			print(diff)
			
			def get_rarity_add_chance(z):
				if z == "SP":
					return 70
				if z == "SSR" :
					return 55
				if z == "SR" :
					return 35
				if z == "R" :
					return 20
					
			with open("../data/duel_stats.json") as f:
				duel_stats = json.load(f)
				
			if not duelist1_select1[0] in duel_stats[str(duelist1.id)]["pulls"]:
				duel_stats[str(duelist1.id)]["pulls"][duelist1_select1[0]] = {}
				duel_stats[str(duelist1.id)]["pulls"][duelist1_select1[0]]["win"] = 0
				duel_stats[str(duelist1.id)]["pulls"][duelist1_select1[0]]["lose"] = 0
				duel_stats[str(duelist1.id)]["pulls"][duelist1_select1[0]]["total"] = 0
				duel_stats[str(duelist1.id)]["pulls"][duelist1_select1[0]]["total"] = 0
			
			if not duelist2_select1[0] in duel_stats[str(duelist2.id)]["pulls"]:
				duel_stats[str(duelist2.id)]["pulls"][duelist2_select1[0]] = {}
				duel_stats[str(duelist2.id)]["pulls"][duelist2_select1[0]]["win"] = 0
				duel_stats[str(duelist2.id)]["pulls"][duelist2_select1[0]]["lose"] = 0
				duel_stats[str(duelist2.id)]["pulls"][duelist2_select1[0]]["total"] = 0
				duel_stats[str(duelist2.id)]["pulls"][duelist2_select1[0]]["total"] = 0		
			
			with open("../data/duel_stats.json", "w") as f:
				json.dump(duel_stats, f, indent="\t")
				
			chance1 = get_rarity_add_chance(duelist1_select1[3])
			chance2 = get_rarity_add_chance(duelist2_select1[3])
			
			if diff == -1 or diff == 8: # x wins, y loses
				total_damage1 = (3 + bonus_damage1)
				duel[str(ctx.message.id)]["duelists"][str(duelist2.id)]["Hp"] -= total_damage1
				duel[str(ctx.message.id)]["duelists"][str(duelist2.id)]["shikigami"][duelist2_select1[0]] = total_damage1
				duel[str(ctx.message.id)]["duelists"][str(duelist1.id)]["shikigami"][duelist1_select1[0]] = total_damage1
							
				duel_stats[str(duelist1.id)]["pulls"][duelist1_select1[0]]["win"] += 1
				duel_stats[str(duelist2.id)]["pulls"][duelist2_select1[0]]["lose"] += 1
				duel_stats[str(duelist1.id)]["pulls"][duelist1_select1[0]]["total"] += 1
				duel_stats[str(duelist2.id)]["pulls"][duelist2_select1[0]]["total"] += 1
				
				title1 = "{} ; {}".format(duelist1_select1[0], ":star:"*duelist1_select1[1])
				description1 = "Specialty: {}\n\n*{} uses {} to {}!*".format(shiki1_specialty, duelist1_select1[0], shiki1_special, duelist2_select1[0])
				text1 = "Pulled by {}".format(duelist1.name)
				icon_url1 = duelist1.avatar_url
				thumbnail1 = shiki1_thumbnail
				
				title2 = "{} ; {}".format(duelist2_select1[0], ":star:"*duelist2_select1[1])
				description2 = "Specialty: {}\n\n*{} was killed by {}\"s attack!*".format(shiki2_specialty, duelist2_select1[0], duelist1_select1[0])
				text2 = "Pulled by {}".format(duelist2.name)	
				icon_url2 = duelist2.avatar_url
				thumbnail2 = shiki2_thumbnail
					
			if diff == -2 or diff == 7: # x does nothing, y single attacks # x has chance to backfire
				total_damage2 = (1 +bonus_damage2)
				duel[str(ctx.message.id)]["duelists"][str(duelist1.id)]["Hp"] -= total_damage2
				duel[str(ctx.message.id)]["duelists"][str(duelist2.id)]["shikigami"][duelist2_select1[0]] = total_damage2
				
				duel_stats[str(duelist2.id)]["pulls"][duelist2_select1[0]]["total"] += 1
				duel_stats[str(duelist1.id)]["pulls"][duelist1_select1[0]]["total"] += 1
				
				title1 = "{} ; {}".format(duelist2_select1[0], ":star:"*duelist2_select1[1])
				description1 = "Specialty: {}\n\n*{} uses {} to {}!*".format(shiki2_specialty, duelist2_select1[0], shiki2_special, duelist1_select1[0])
				text1 = "Pulled by {}".format(duelist2.name)
				icon_url1 = duelist2.avatar_url
				thumbnail1 = shiki2_thumbnail
				
				if random.randint(1,100) <= chance1 :
					title2 = "{} ; {}".format(duelist1_select1[0], ":star:"*duelist1_select1[1])
					description2 = "Specialty: {}\n\n*{} backfires and uses {} to {}!*".format(shiki1_specialty, duelist1_select1[0], shiki1_special, duelist2_select1[0])
					text2 = "Pulled by {}".format(duelist1.name)	
					icon_url2 = duelist1.avatar_url
					thumbnail2 = shiki1_thumbnail
					duel[str(ctx.message.id)]["duelists"][str(duelist2.id)]["Hp"] -= 1
				
				else: 
					duel_stats[str(duelist2.id)]["pulls"][duelist2_select1[0]]["win"] += 1
					duel_stats[str(duelist1.id)]["pulls"][duelist1_select1[0]]["lose"] += 1
				
					title2 = "{} ; {}".format(duelist1_select1[0], ":star:"*duelist1_select1[1])
					description2 = "Specialty: {}\n\n*{} was dazed by {}\"s {}!*".format(shiki1_specialty, duelist1_select1[0], duelist2_select1[0], shiki2_special)
					text2 = "Pulled by {}".format(duelist1.name)	
					icon_url2 = duelist1.avatar_url
					thumbnail2 = shiki1_thumbnail
					
			if diff == -3 or diff == 6: # x attacks y, y attacks x
				total_damage1 = (2 + bonus_damage1)
				total_damage2 = (2 + bonus_damage2)
				
				duel[str(ctx.message.id)]["duelists"][str(duelist1.id)]["Hp"] -= total_damage1
				duel[str(ctx.message.id)]["duelists"][str(duelist2.id)]["Hp"] -= total_damage2
				duel[str(ctx.message.id)]["duelists"][str(duelist1.id)]["shikigami"][duelist1_select1[0]] = total_damage1
				duel[str(ctx.message.id)]["duelists"][str(duelist2.id)]["shikigami"][duelist2_select1[0]] = total_damage2
				
				duel_stats[str(duelist2.id)]["pulls"][duelist2_select1[0]]["total"] += 1
				duel_stats[str(duelist1.id)]["pulls"][duelist1_select1[0]]["total"] += 1
				
				title1 = "{} ; {}".format(duelist1_select1[0], ":star:"*duelist1_select1[1])
				description1 = "Specialty: {}\n\n*{} uses {} to {}!*".format(shiki1_specialty, duelist1_select1[0], shiki1_special, duelist2_select1[0])
				text1 = "Pulled by {}".format(duelist1.name)
				icon_url1 = duelist1.avatar_url
				thumbnail1 = shiki1_thumbnail
				
				title2 = "{} ; {}".format(duelist2_select1[0], ":star:"*duelist2_select1[1])
				description2 = "Specialty: {}\n\n*{} backfires and uses {} to {}!*".format(shiki2_specialty, duelist2_select1[0], shiki2_special, duelist1_select1[0])
				text2 = "Pulled by {}".format(duelist2.name)	
				icon_url2 = duelist2.avatar_url
				thumbnail2 = shiki2_thumbnail
				
			if diff == -4 or diff == 5: # x single attacks, y does nothing # y has chance to backfire
				total_damage1 = (1 + bonus_damage1)
				duel[str(ctx.message.id)]["duelists"][str(duelist2.id)]["Hp"] -= total_damage1
				duel[str(ctx.message.id)]["duelists"][str(duelist1.id)]["shikigami"][duelist1_select1[0]] = total_damage1
				
				duel_stats[str(duelist2.id)]["pulls"][duelist2_select1[0]]["total"] += 1
				duel_stats[str(duelist1.id)]["pulls"][duelist1_select1[0]]["total"] += 1
				
				title1 = "{} ; {}".format(duelist1_select1[0], ":star:"*duelist1_select1[1])
				description1 = "Specialty: {}\n\n*{} uses {} to {}!*".format(shiki1_specialty, duelist1_select1[0], shiki1_special, duelist2_select1[0])
				text1 = "Pulled by {}".format(duelist1.name)
				icon_url1 = duelist1.avatar_url
				thumbnail1 = shiki1_thumbnail

				if random.randint(1,100) <= chance2 :
					title2 = "{} ; {}".format(duelist2_select1[0], ":star:"*duelist2_select1[1])
					description2 = "Specialty: {}\n\n*{} backfires and uses {} to {}!*".format(shiki2_specialty, duelist2_select1[0], shiki2_special, duelist1_select1[0])
					text2 = "Pulled by {}".format(duelist2.name)	
					icon_url2 = duelist2.avatar_url
					thumbnail2 = shiki2_thumbnail
					duel[str(ctx.message.id)]["duelists"][str(duelist1.id)]["Hp"] -= 1
				
				else: 
					duel_stats[str(duelist2.id)]["pulls"][duelist2_select1[0]]["lose"] += 1
					duel_stats[str(duelist1.id)]["pulls"][duelist1_select1[0]]["win"] += 1
				
					title2 = "{} ; {}".format(duelist2_select1[0], ":star:"*duelist2_select1[1])
					description2 = "Specialty: {}\n\n*{} was dazed by {}\"s {}!*".format(shiki2_specialty, duelist2_select1[0], duelist1_select1[0], shiki1_special)
					text2 = "Pulled by {}".format(duelist2.name)	
					icon_url2 = duelist2.avatar_url
					thumbnail2 = shiki2_thumbnail	
							
			if diff == -5 or diff == 4: # x does nothing, y single attacks # x has chance to backfire
				total_damage2 = (1 + bonus_damage2)
				duel[str(ctx.message.id)]["duelists"][str(duelist1.id)]["Hp"] -= total_damage2
				duel[str(ctx.message.id)]["duelists"][str(duelist2.id)]["shikigami"][duelist2_select1[0]] = total_damage2
				
				duel_stats[str(duelist2.id)]["pulls"][duelist2_select1[0]]["total"] += 1
				duel_stats[str(duelist1.id)]["pulls"][duelist1_select1[0]]["total"] += 1
				
				title1 = "{} ; {}".format(duelist2_select1[0], ":star:"*duelist2_select1[1])
				description1 = "Specialty: {}\n\n*{} uses {} to {}!*".format(shiki2_specialty, duelist2_select1[0], shiki2_special, duelist1_select1[0])
				text1 = "Pulled by {}".format(duelist2.name)
				icon_url1 = duelist2.avatar_url
				thumbnail1 = shiki2_thumbnail
				
				if random.randint(1,100) <= chance1 :
					title2 = "{} ; {}".format(duelist1_select1[0], ":star:"*duelist1_select1[1])
					description2 = "Specialty: {}\n\n*{} backfires and uses {} to {}!*".format(shiki1_specialty, duelist1_select1[0], shiki1_special, duelist2_select1[0])
					text2 = "Pulled by {}".format(duelist1.name)	
					icon_url2 = duelist1.avatar_url
					thumbnail2 = shiki1_thumbnail
					duel[str(ctx.message.id)]["duelists"][str(duelist2.id)]["Hp"] -= 1
					
				else: 
				
					duel_stats[str(duelist2.id)]["pulls"][duelist2_select1[0]]["win"] += 1
					duel_stats[str(duelist1.id)]["pulls"][duelist1_select1[0]]["lose"] += 1
					
					title2 = "{} ; {}".format(duelist1_select1[0], ":star:"*duelist1_select1[1])
					description2 = "Specialty: {}\n\n*{} was dazed by {}\"s {}!*".format(shiki1_specialty, duelist1_select1[0], duelist2_select1[0], shiki2_special)
					text2 = "Pulled by {}".format(duelist1.name)	
					icon_url2 = duelist1.avatar_url
					thumbnail2 = shiki1_thumbnail
				
			if diff == -6 or diff == 3: # x attacks y, y attacks x
				total_damage1 = (2 + bonus_damage1)
				total_damage2 = (2 + bonus_damage2)
				
				duel[str(ctx.message.id)]["duelists"][str(duelist1.id)]["Hp"] -= total_damage1
				duel[str(ctx.message.id)]["duelists"][str(duelist2.id)]["Hp"] -= total_damage2
				duel[str(ctx.message.id)]["duelists"][str(duelist1.id)]["shikigami"][duelist1_select1[0]] = total_damage1
				duel[str(ctx.message.id)]["duelists"][str(duelist2.id)]["shikigami"][duelist2_select1[0]] = total_damage2
				
				duel_stats[str(duelist2.id)]["pulls"][duelist2_select1[0]]["total"] += 1
				duel_stats[str(duelist1.id)]["pulls"][duelist1_select1[0]]["total"] += 1
				
				title1 = "{} ; {}".format(duelist2_select1[0], ":star:"*duelist2_select1[1])
				description1 = "Specialty: {}\n\n*{} uses {} to {}!*".format(shiki2_specialty, duelist2_select1[0], shiki2_special, duelist1_select1[0])
				text1 = "Pulled by {}".format(duelist2.name)
				icon_url1 = duelist2.avatar_url
				thumbnail1 = shiki2_thumbnail
				
				title2 = "{} ; {}".format(duelist1_select1[0], ":star:"*duelist1_select1[1])
				description2 = "Specialty: {}\n\n*{} lives and uses {} to {}!*".format(shiki1_specialty, duelist1_select1[0], shiki1_special, duelist2_select1[0])
				text2 = "Pulled by {}".format(duelist1.name)	
				icon_url2 = duelist1.avatar_url
				thumbnail2 = shiki1_thumbnail
				
			if diff == -7 or diff == 2: # x single attacks, y does nothing # y has chance to backfire
				total_damage1 = (1 + bonus_damage1)
				duel[str(ctx.message.id)]["duelists"][str(duelist2.id)]["Hp"] -= total_damage1
				duel[str(ctx.message.id)]["duelists"][str(duelist1.id)]["shikigami"][duelist1_select1[0]] = total_damage1
				
				duel_stats[str(duelist2.id)]["pulls"][duelist2_select1[0]]["total"] += 1
				duel_stats[str(duelist1.id)]["pulls"][duelist1_select1[0]]["total"] += 1
				
				title1 = "{} ; {}".format(duelist1_select1[0], ":star:"*duelist1_select1[1])
				description1 = "Specialty: {}\n\n*{} uses {} to {}!*".format(shiki1_specialty, duelist1_select1[0], shiki1_special, duelist2_select1[0])
				text1 = "Pulled by {}".format(duelist1.name)
				icon_url1 = duelist1.avatar_url
				thumbnail1 = shiki1_thumbnail
				
				if random.randint(1,100) <= chance2 :
					title2 = "{} ; {}".format(duelist2_select1[0], ":star:"*duelist2_select1[1])
					description2 = "Specialty: {}\n\n*{} backfires and uses {} to {}!*".format(shiki2_specialty, duelist2_select1[0], shiki2_special, duelist1_select1[0])
					text2 = "Pulled by {}".format(duelist2.name)	
					icon_url2 = duelist2.avatar_url
					thumbnail2 = shiki2_thumbnail
					duel[str(ctx.message.id)]["duelists"][str(duelist1.id)]["Hp"] -= 1
				
				else: 
					duel_stats[str(duelist1.id)]["pulls"][duelist1_select1[0]]["win"] += 1
					duel_stats[str(duelist2.id)]["pulls"][duelist2_select1[0]]["lose"] += 1
					
					title2 = "{} ; {}".format(duelist2_select1[0], ":star:"*duelist2_select1[1])
					description2 = "Specialty: {}\n\n*{} was dazed by {}\"s {}!*".format(shiki2_specialty, duelist2_select1[0], duelist1_select1[0], shiki1_special)
					text2 = "Pulled by {}".format(duelist2.name)	
					icon_url2 = duelist2.avatar_url
					thumbnail2 = shiki2_thumbnail
					
			if diff == -8 or diff == 1: # x loses, y wins
				
				total_damage2 = (3 + bonus_damage2)
				duel[str(ctx.message.id)]["duelists"][str(duelist1.id)]["Hp"] -= total_damage2
				duel[str(ctx.message.id)]["duelists"][str(duelist2.id)]["shikigami"][duelist2_select1[0]] = total_damage2
				
				duel_stats[str(duelist2.id)]["pulls"][duelist2_select1[0]]["win"] += 1
				duel_stats[str(duelist1.id)]["pulls"][duelist1_select1[0]]["lose"] += 1
				duel_stats[str(duelist2.id)]["pulls"][duelist2_select1[0]]["total"] += 1
				duel_stats[str(duelist1.id)]["pulls"][duelist1_select1[0]]["total"] += 1
				
				title1 = "{} ; {}".format(duelist2_select1[0], ":star:"*duelist2_select1[1])
				description1 = "Specialty: {}\n*{} uses {} to {}!*".format(shiki2_specialty, duelist2_select1[0], shiki2_special, duelist1_select1[0])
				text1 = "Pulled by {}".format(duelist2.name)
				icon_url1 = duelist2.avatar_url
				thumbnail1 = shiki2_thumbnail
				
				title2 = "{} ; {}".format(duelist1_select1[0], ":star:"*duelist1_select1[1])
				description2 = "Specialty: {}\n*{} was killed by {}\"s {}!*".format(shiki1_specialty, duelist1_select1[0], duelist2_select1[0], shiki2_specialty)
				text2 = "Pulled by {}".format(duelist1.name)
				icon_url2 = duelist1.avatar_url
				thumbnail2 = shiki1_thumbnail

			if diff == 0: # fight 
				total_damage1 = (1 + bonus_damage2)
				total_damage2 = (1 + bonus_damage2)
				
				duel[str(ctx.message.id)]["duelists"][str(duelist1.id)]["Hp"] -= total_damage2
				duel[str(ctx.message.id)]["duelists"][str(duelist2.id)]["Hp"] -= total_damage1
				duel[str(ctx.message.id)]["duelists"][str(duelist1.id)]["shikigami"][duelist1_select1[0]] = total_damage1
				duel[str(ctx.message.id)]["duelists"][str(duelist2.id)]["shikigami"][duelist2_select1[0]] = total_damage2
				
				duel_stats[str(duelist2.id)]["pulls"][duelist2_select1[0]]["total"] += 1
				duel_stats[str(duelist1.id)]["pulls"][duelist1_select1[0]]["total"] += 1
				
				title1 = "{} ; {}".format(duelist2_select1[0], ":star:"*duelist2_select1[1])
				description1 = "Specialty: {}\n*{} uses {} to {}!*".format(shiki2_specialty, duelist2_select1[0], shiki2_normal, duelist1_select1[0])
				text1 = "Pulled by {}".format(duelist2.name)
				icon_url1 = duelist2.avatar_url
				thumbnail1 = shiki2_thumbnail
				
				title2 = "{} ; {}".format(duelist1_select1[0], ":star:"*duelist1_select1[1])
				description2 = "Specialty: {}\n*{} uses {} to {}!*".format(shiki2_specialty, duelist1_select1[0], shiki1_normal, duelist2_select1[0])
				text2 = "Pulled by {}".format(duelist1.name)
				icon_url2 = duelist1.avatar_url
				thumbnail2 = shiki1_thumbnail
			
			with open("../data/duel.json", "w") as f:
				json.dump(duel, f, indent="\t")
			
			with open("../data/duel_stats.json", "w") as f:
				json.dump(duel_stats, f, indent="\t")
			
			await asyncio.sleep(8)
		
		# duelist1_response
		embed1 = discord.Embed(color=0xffff80, title=title1, description=description1)
		embed1.set_thumbnail(url=thumbnail1)
		embed1.set_footer(text=text1, icon_url=icon_url1)
		
		# duelist2_response
		embed2 = discord.Embed(color=0xac330f, title=title2, description=description2)
		embed2.set_thumbnail(url = thumbnail2)
		embed2.set_footer(text = text2,icon_url = icon_url2)
			
		await arena_channel.send(embed=embed1)
		
		async with ctx.channel.typing(): 
			await asyncio.sleep(4)
			await arena_channel.send(embed=embed2)
			
		async with ctx.channel.typing(): 	
			await asyncio.sleep(3)
		
		await self.duel_start(duelist1, duelist2, round, pool1, pool2, duelist_channel_id1, duelist_channel_id2, ctx)


def setup(client):
	client.add_cog(Duel(client))