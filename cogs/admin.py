"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import discord, json, re
from cogs.mongo.db import daily, boss
from discord.ext import commands
from datetime import datetime
# from pymongo import MongoClient
		
class Admin(commands.Cog):
	
	def __init__(self, client):
		self.client = client
	
	@commands.command()
	@commands.is_owner()
	async def reset(self, ctx, *args):

		# Reset daily
		if args[0] == "daily":
			
			for entry in daily.find({"key": "daily"}, {"key": 0, "_id": 0}):
				for user_id in entry:
					daily.update_one({"key": "daily"}, {"$set": {"{}.rewards".format(user_id): "unclaimed"}})
			
			for user_id in daily.find_one({"key" : "raid"}, {"_id": 0, "key": 0}):
				daily.update_one({"key" : "raid"}, {"$set": {"{}.raid_count".format(user_id): 0}})
				
			msg = ":confetti_ball: Daily rewards have been reset."
			await ctx.channel.send(msg)
			
		# Resets weekly
		elif args[0] == "weekly":
				
			for entry in daily.find({"key": "weekly"}, {"key": 0, "_id": 0}):
				for user in entry:
					daily.update({"key": "weekly"}, {"$set": {"{}.rewards".format(user): "unclaimed"}})
				
			msg = ":confetti_ball: Weekly rewards have been reset."
			await ctx.channel.send(msg)
			
		# Resets the boss	
		elif args[0] == "boss":
			
			boss.update_many({}, {"$set": {"discoverer": 0, "level": 0, "damage_cap": 0, "total_hp": 0, "current_hp": 0, "rewards": 0, "challengers": [], "rewards": {}}})

			msg = "Assembly Boss encounter has been reset."
			await ctx.channel.send(msg)
		
		else:
			msg = "Please provide a valid argument: daily, weekly, or boss"
			await ctx.channel.send(msg)
	
	@commands.command(aliases=["c", "clear", "purge", "cl"])
	async def purge_messages(self, ctx, amount=2):
		if ctx.channel.permissions_for(ctx.author).administrator == True:
			await ctx.channel.purge(limit=amount+1)
	
	@commands.command(aliases=["bc"])
	async def broadcast(self, ctx, *args):
		channel = self.client.get_channel(int(re.sub("[<>#]", "", args[0])))
		
		# Checks if admin
		if ctx.channel.permissions_for(ctx.author).administrator == True:
			msg = "{}".format(" ".join(args[1:]))
			await channel.send(msg)
	
def setup(client):
	client.add_cog(Admin(client))