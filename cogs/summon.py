"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import discord, json, random
from cogs.mongo.db import users, streak, shikigami
from discord.ext import commands
# from pymongo import MongoClient

# Mongo Startup
# memory = MongoClient("mongodb+srv://headmaster:headmaster@memory-scrolls-uhsu0.mongodb.net/test?retryWrites=true&w=majority")
# memory = MongoClient("mongodb://localhost:27017/")
# users = memory["miketsu"]["users"]
# streak = memory["miketsu"]["streak"]
# shikigami = memory["miketsu"]["shikigami"]

# Generate summon pool
pool_sp = []
for shiki in shikigami.find({"rarity": "SP"}, {"_id": 0, "shikigami.name": 1}):
	for entry in shiki["shikigami"]:
		pool_sp.append(entry["name"])

pool_ssr = []
for shiki in shikigami.find({"rarity": "SSR"}, {"_id": 0, "shikigami.name": 1}):
	for entry in shiki["shikigami"]:
		pool_ssr.append(entry["name"])

pool_sr = []
for shiki in shikigami.find({"rarity": "SR"}, {"_id": 0, "shikigami.name": 1}):
	for entry in shiki["shikigami"]:
		pool_sr.append(entry["name"])

pool_r = []
for shiki in shikigami.find({"rarity": "R"}, {"_id": 0, "shikigami.name": 1}):
	for entry in shiki["shikigami"]:
		pool_r.append(entry["name"])

# Lists startup
caption = open("lists/summon.lists")
summon_caption = caption.read().splitlines()
caption.close()

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
			amulet_pull = int(arg)	
			amulet_have = users.find_one({"user_id": str(user.id)}, {"_id": 0, "amulets": 1})["amulets"]
			
			if amulet_have > 0:
				if amulet_pull > amulet_have:
					msg = "{}, you only have {}<:amulet:573071120685596682> to summon.".format(user.mention, amulet_have)
					await ctx.channel.send(msg)
					
				elif amulet_pull == 10 and amulet_have >= 10:
					await self.summon_perform(ctx, user, users, amulet_pull)
					
				elif amulet_pull == 1 and amulet_have >= 1:
					await self.summon_perform(ctx, user, users, amulet_pull)
					
				else:
					msg = "{}, summon can only be by ones or by tens.".format(user.mention)
					await ctx.channel.send(msg)
			else:
				msg = "{}, you have no <:amulet:573071120685596682> to summon.".format(user.mention)
				await ctx.channel.send(msg)
		except ValueError:
			msg = "Type `;summon <1 or 10>` to perform summon.".format(user.mention)
			await ctx.channel.send(msg)
		
	async def summon_perform(self, ctx, user, users, amulet_pull):
		summon_pull = []
		
		for count in range(amulet_pull):
			roll = random.uniform(0,100)
			if roll < 1.2:
				p = random.uniform(0,1.2)
				if p >= 126/109:
					summon_pull.append(("SP", "||{}||".format(random.choice(pool_sp))))
				else:
					summon_pull.append(("SSR", "||{}||".format(random.choice(pool_ssr))))
			elif roll <= 18.8:
				summon_pull.append(("SR", random.choice(pool_sr)))
			else:
				summon_pull.append(("R", random.choice(pool_r)))

		sum_sp = sum(entry.count("SP") for entry in summon_pull)
		sum_ssr = sum(entry.count("SSR") for entry in summon_pull)
		sum_sr = sum(entry.count("SR") for entry in summon_pull)
		sum_r = sum(entry.count("R") for entry in summon_pull)

		f_sp = str(sum_sp) + " " + self.pluralize("SP", sum_sp)
		f_ssr = str(sum_ssr) + " " + self.pluralize("SSR", sum_ssr)
		f_sr = str(sum_sr) + " " + self.pluralize("SR", sum_sr)
		f_r = str(sum_r) + " " + self.pluralize("R", sum_r)

		description = ""
		for entry in summon_pull:
			description += ":small_orange_diamond:{}\n".format(entry[1])
		
		embed = discord.Embed(color=0xffff4a, title=":confetti_ball: Results", description=description)
		
		if amulet_pull == 10:
			embed.set_footer(text = "{}; {}; {}; {}".format(f_sp, f_ssr, f_sr, f_r))
		
		# Thumbnails 
		elif amulet_pull == 1:
			rarity = summon_pull[0][0] 
			shiki = summon_pull[0][1].replace("||", "")
			thumbnail = shikigami.find_one({"rarity": rarity}, {"_id": 0, "shikigami": {"$elemMatch": {"name": shiki}}})["shikigami"][0]["thumbnail"]["pre_evo"]
			embed.set_thumbnail(url=thumbnail)

		msg = "{}".format(random.choice(summon_caption)).format(user.mention)
		await ctx.channel.send(msg, embed=embed)
		await self.summon_update(user, users, sum_sp, sum_ssr, sum_sr, sum_r, amulet_pull, summon_pull)
		await self.summon_streak(user, summon_pull)
			
	async def summon_update(self, user, users, sum_sp, sum_ssr, sum_sr, sum_r, amulet_pull, summon_pull):
		
		users.update_one({"user_id": str(user.id)}, {"$inc": {"SP": sum_sp, "SSR": sum_ssr, "SR": sum_sr, "R": sum_r, "amulets_spent": amulet_pull, "amulets": -amulet_pull}})

		for summon in summon_pull:
			# Creates a shikigami profile
			if users.find_one({"user_id": str(user.id), "shikigami.name": summon[1].replace("||", "")}, {"_id": 0, "shikigami.$": 1}) == None:
				users.update_one({"user_id": str(user.id)}, {"$push": {
					"shikigami": {"name": summon[1].replace("||", ""), "rarity": summon[0], "grade": 1, "owned": 0, "evolved": "False"}
					}})

			users.update_one({"user_id": str(user.id),  "shikigami.name": summon[1].replace("||", "")}, {
			"$inc": {
			"shikigami.$.owned": 1
			}})
			
	async def summon_streak(self, user, summon_pull):
		
		if streak.find_one({"user_id": str(user.id)}, {"_id": 0}) == None:
			profile = {"user_id": str(user.id), "SSR_current": 0, "SSR_record": 0}
			streak.insert_one(profile)
		
		for summon in summon_pull:
			SSR_current = streak.find_one({"user_id": str(user.id)}, {"_id": 0})["SSR_current"]
			SSR_record = streak.find_one({"user_id": str(user.id)}, {"_id": 0})["SSR_record"]
			
			if summon[0] == "SP" or summon[0] == "SR" or summon[0] == "R":
				if SSR_current == SSR_record:
					streak.update_one({"user_id": str(user.id)}, {"$inc": {"SSR_current": 1, "SSR_record": 1}})
				else:
					streak.update_one({"user_id": str(user.id)}, {"$inc": {"SSR_current": 1}})
				
			if summon[0] == "SSR":
				streak.update_one({"user_id": str(user.id)}, {"$set": {"SSR_current": 0}})
		
def setup(client):
	client.add_cog(Summon(client))