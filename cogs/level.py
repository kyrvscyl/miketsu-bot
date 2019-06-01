"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import discord, json
from discord.ext import commands
import config.lists as shiki

class Level(commands.Cog):
	
	def __init__(self, client):
		self.client = client
	
	@commands.Cog.listener()
	async def on_message(self, ctx):
		# Ignore myself
		if ctx.author == self.client.user:
			return
		# Ignore other bots
		elif ctx.author.bot == True:
			return
		# Perform add experience
		with open("../data/users.json", "r") as f:
			users = json.load(f)
			await self.create_user(users, ctx.author)
			await self.add_experience(users, ctx.author, 5)
			await self.level_up(users, ctx.author, ctx)
		with open("../data/users.json", "w") as f:
			json.dump(users, f, indent="\t")
	
	async def add_experience(self, users, user, exp):
		# Maximum level check
		if users[str(user.id)]["level"] == 60:
			return
		else:
			users[str(user.id)]["experience"] += exp

	async def level_up(self, users, user, ctx):
		exp = users[str(user.id)]["experience"]
		levelStart = users[str(user.id)]["level"]
		levelEnd = int(exp **(0.3))
		
		# Add one level
		if levelStart < levelEnd:
			users[str(user.id)]["level_exp_next"] = 5*(round(((users[str(user.id)]["level"]+2)**3.3333333333)/5))
			users[str(user.id)]["jades"] += 150
			users[str(user.id)]["amulets"] += 10
			users[str(user.id)]["coins"] += 100000
			users[str(user.id)]["level"] = levelEnd
			
			# Add emoji during levelup
			await ctx.add_reaction("⤴")

	async def create_user(self, users, user):
		if not str(user.id) in users:
			users[str(user.id)] = {}
			users[str(user.id)]["experience"] = 0
			users[str(user.id)]["level"] = 1
			users[str(user.id)]["level_exp_next"] = 5
			users[str(user.id)]["amulets"] = 10
			users[str(user.id)]["amulets_spent"] = 0
			users[str(user.id)]["SP"] = 0
			users[str(user.id)]["SSR"] = 0
			users[str(user.id)]["SR"] = 0
			users[str(user.id)]["R"] = 0
			users[str(user.id)]["jades"] = 0
			users[str(user.id)]["coins"] = 0
			users[str(user.id)]["medals"] = 0
			users[str(user.id)]["realm_ticket"] = 0
			users[str(user.id)]["honor"] = 0
			users[str(user.id)]["talisman"] = 0
			users[str(user.id)]["friendship"] = 0
			users[str(user.id)]["guild_medal"] = 0
			users[str(user.id)]["shikigami"] = {"SP" : {},"SSR" : {},"SR" : {},"R" : {}}
			
			# Iterates for every shikigami
			for member in users:
				for rarity in users[member]["shikigami"]:
					if rarity == "SP":
						for shikigami in shiki.poolSP:
							users[str(user.id)]["shikigami"][rarity][shikigami] = {}
					if rarity == "SSR":
						for shikigami in shiki.poolSSR:
							users[str(user.id)]["shikigami"][rarity][shikigami] = {}
					if rarity == "SR":
						for shikigami in shiki.poolSR:
							users[str(user.id)]["shikigami"][rarity][shikigami] = {}
					if rarity == "R":
						for shikigami in shiki.poolR:
							users[str(user.id)]["shikigami"][rarity][shikigami] = {}
							
			# Iterates for every shikigami
			for member in users:
				for rarity in users[member]["shikigami"]:
					for shikigami in users[member]["shikigami"][rarity]:
						users[str(user.id)]["shikigami"][rarity][shikigami]["owned"] = 0
						users[str(user.id)]["shikigami"][rarity][shikigami]["grade"] = 1
						# SP as pre-evolved
						if rarity == "SP":
							users[str(user.id)]["shikigami"][rarity][shikigami]["evolved"] = "True"
						else:
							users[str(user.id)]["shikigami"][rarity][shikigami]["evolved"] = "False"

def setup(client):
	client.add_cog(Level(client))