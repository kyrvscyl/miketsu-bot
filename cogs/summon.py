"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import discord, json, random
from discord.ext import commands
import config.guild as guild
import config.lists as lists

class Summon(commands.Cog):
	
	def __init__(self, client):
		self.client = client
	
	def pluralize(self, singular, count):
		if count > 1:
			return singular+"s"
		else:
			return singular
	
	@commands.command(aliases=["s"])
	@commands.guild_only()
	async def summon(self, ctx, arg):
		user = ctx.author
		try :
			pullAmulet = int(arg)
			with open("../data/users.json", "r") as f:
				users = json.load(f)
			
			onhandAmulet = users[str(user.id)]["amulets"]
			
			if onhandAmulet > 0:
			
				if pullAmulet == 10 and onhandAmulet >= 0:
					await self.summonPerform(ctx, user, pullAmulet)
					return
					
				if pullAmulet == 1 and onhandAmulet >= 1:
					await self.summonPerform(ctx, user, pullAmulet)
					return
				
				if pullAmulet > onhandAmulet:
					msg = "{}, you only have {}{} to summon.".format(user.mention, onhandAmulet, guild.eAmulet)
					await ctx.channel.send(msg)
					return	
				else:
					msg = "{}, summon can only be by ones or by tens.".format(user.mention)
					await ctx.channel.send(msg)
					return
			else:
				msg = "{}, you have no {} to summon.".format(user.mention, guild.eAmulet)
				await ctx.channel.send(msg)
		except:
			msg = "Type `;summon <1 or 10>` to perform summon.".format(user.mention)
			await ctx.channel.send(msg)

	async def summonPerform(self, ctx, user, pullAmulet):
		
		summonPulls = []
		for count in range(pullAmulet):
			roll = random.uniform(0,100)
			if roll < 1.2:
				p = random.uniform(0,1.2)
				if p >= 126/109:
					summonPulls.append(("SP", "||{}||".format(random.choice(lists.poolSP))))
				else:
					summonPulls.append(("SSR", "||{}||".format(random.choice(lists.poolSSR))))
			elif roll <= 18.8:
				summonPulls.append(("SR", random.choice(lists.poolSR)))
			else:
				summonPulls.append(("R", random.choice(lists.poolR)))

		summonSP = sum(entry.count("SP") for entry in summonPulls)
		summonSSR = sum(entry.count("SSR") for entry in summonPulls)
		summonSR = sum(entry.count("SR") for entry in summonPulls)
		summonR = sum(entry.count("R") for entry in summonPulls)

		footerSP = str(summonSP) + " " + self.pluralize("SP", summonSP)
		footerSSR = str(summonSSR) + " " + self.pluralize("SSR", summonSSR)
		footerSR = str(summonSR) + " " + self.pluralize("SR", summonSR)
		footerR = str(summonR) + " " + self.pluralize("R", summonR)

		description = ""
		for entry in summonPulls:
			description += ":small_orange_diamond:{}\n".format(entry[1])
		
		embed = discord.Embed(color = 0xffff4a, title = ":confetti_ball: Results", description = description)
		
		if pullAmulet == 10:
			embed.set_footer(text = "{}; {}; {}; {}".format(footerSP, footerSSR, footerSR, footerR))
		elif pullAmulet == 1:
			with open("../data/shikigami.json", "r") as f:
				shikigami = json.load(f)
			summonPic = shikigami[summonPulls[0][0]][summonPulls[0][1].replace("||", "")]["thumbnail"]["pre_evo"]
			embed.set_thumbnail(url=summonPic)

		msg = "{}".format(random.choice(lists.summonList)).format(ctx.author.mention)
		await ctx.channel.send(msg, embed=embed)
		
		with open("../data/users.json", "r") as f:
			users = json.load(f)
			
			await self.summonUpdate(users, ctx.author, summonSP, summonSSR, summonSR, summonR, pullAmulet, summonPulls)
			await self.summonStreak(user, summonPulls)
			
	async def summonUpdate(self, users, user, summonSP, summonSSR, summonSR, summonR, pullAmulet, summonPulls):
		
		users[str(user.id)]["SP"] += summonSP
		users[str(user.id)]["SSR"] += summonSSR
		users[str(user.id)]["SR"] += summonSR
		users[str(user.id)]["R"] += summonR
		users[str(user.id)]["amulets_spent"] += pullAmulet
		users[str(user.id)]["amulets"] -= pullAmulet
		
		for summon in summonPulls:
			users[str(user.id)]["shikigami"][summon[0]][summon[1].replace("||", "")]["owned"] += 1
		
		with open("../data/users.json", "w") as f:
			json.dump(users, f, indent="\t")
		
	async def summonStreak(self, user, summonPulls):
		with open("../data/streak.json", "r") as f:
			streak = json.load(f)
		
		if not str(user.id) in streak:
			streak[str(user.id)] = {}
			streak[str(user.id)]["SSR_current"] = 0
			streak[str(user.id)]["SSR_record"] = 0
		
		
		for summon in summonPulls:
			if summon[0] == "SP" or summon[0] == "SR" or summon[0] == "R":
				if streak[str(user.id)]["SSR_current"] == (streak[str(user.id)]["SSR_record"]):
					streak[str(user.id)]["SSR_current"] += 1
					streak[str(user.id)]["SSR_record"] += 1
					
				if streak[str(user.id)]["SSR_current"] != (streak[str(user.id)]["SSR_record"]):
					streak[str(user.id)]["SSR_current"] += 1
				
			if summon[0] == "SSR":
				streak[str(user.id)]["SSR_current"] = 1
		
		with open("../data/streak.json", "w") as f:
			json.dump(streak, f, indent="\t")

def setup(client):
	client.add_cog(Summon(client))