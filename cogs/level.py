"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import discord, json
from cogs.mongo.db import users
from discord.ext import commands
# from pymongo import MongoClient

# Mongo Startup
# memory = MongoClient("mongodb+srv://headmaster:headmaster@memory-scrolls-uhsu0.mongodb.net/test?retryWrites=true&w=majority")
# memory = MongoClient("mongodb://localhost:27017/")
# users = memory["miketsu"]["users"]

class Level(commands.Cog):
	
	def __init__(self, client):
		self.client = client
	
	@commands.Cog.listener()
	async def on_member_join(self, member):
		await self.create_user(member)
	
	@commands.Cog.listener()
	async def on_message(self, ctx):
		# Ignore myself
		if ctx.author == self.client.user:
			return
		
		# Ignore other bots
		elif ctx.author.bot == True:
			return
		
		# Perform add experience
		await self.create_user(ctx.author)
		await self.add_experience(ctx.author, 5)
		await self.level_up(ctx.author, ctx)
	
	async def add_experience(self, user, exp):
		# Maximum level check
		if users.find_one({"user_id": str(user.id)}, {"_id": 0, "level": 1})["level"] == 60:
			return
		else:
			users.update_one({"user_id": str(user.id)}, {"$inc": {"experience": exp}})

	async def level_up(self, user, ctx):
		
		exp = users.find_one({"user_id": str(user.id)}, {"_id": 0, "experience": 1})["experience"]
		level = users.find_one({"user_id": str(user.id)}, {"_id": 0, "level": 1})["level"]
		level_end = int(exp **(0.3))
		
		# Add one level
		if level < level_end:
			
			level_next = 5*(round(((level+2)**3.3333333333)/5))
			users.update_one({"user_id": str(user.id)}, {"$set": {"level_exp_next": level_next}})
			users.update_one({"user_id": str(user.id)}, {"$inc": {"jades": 150, "amulets": 10, "coins": 100000, "level": level_end}})

			# Add emoji during levelup
			await ctx.add_reaction("⤴")

	async def create_user(self, user):
		if users.find_one({"user_id": str(user.id)}, {"_id": 0}) == None:
			profile = {}
			profile["user_id"] = str(user.id)
			profile["experience"] = 0
			profile["level"] = 1
			profile["level_exp_next"] = 5
			profile["amulets"] = 10
			profile["amulets_spent"] = 0
			profile["SP"] = 0
			profile["SSR"] = 0
			profile["SR"] = 0
			profile["R"] = 0
			profile["jades"] = 0
			profile["coins"] = 0
			profile["medals"] = 0
			profile["realm_ticket"] = 0
			profile["honor"] = 0
			profile["talisman"] = 0
			profile["friendship"] = 0
			profile["guild_medal"] = 0
			profile["shikigami"] = []
			
			# Creates a profile
			users.insert_one(profile)
		
def setup(client):
	client.add_cog(Level(client))