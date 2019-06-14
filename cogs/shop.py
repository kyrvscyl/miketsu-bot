"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import discord, json, asyncio
from cogs.mongo.db import users
from discord.ext import commands
# from pymongo import MongoClient

# Mongo Startup
# memory = MongoClient("mongodb+srv://headmaster:headmaster@memory-scrolls-uhsu0.mongodb.net/test?retryWrites=true&w=majority")
# memory = MongoClient("mongodb://localhost:27017/")
# users = memory["miketsu"]["users"]

class Economy(commands.Cog):
	
	def __init__(self, client):
		self.client = client
	
	@commands.command()
	async def buy(self, ctx, *args):
		user = ctx.author
		try:
			if args[0] == "amulet":
				await ctx.message.add_reaction(":amulet:573071120685596682")
				
				def check(reaction, user):
					return user == ctx.author and str(reaction.emoji) == "<:amulet:573071120685596682>"
				try:
					reaction, user = await self.client.wait_for("reaction_add", timeout=10.0, check=check)
				except asyncio.TimeoutError:
					msg = "{}, timeout! You did not click {} on time. Please try again.".format(user.mention, "<:amulet:573071120685596682>")
					await ctx.channel.send(msg)
				else:
					await self.buy_amulet(user, ctx)
		except IndexError:
			embed = discord.Embed(color=0xffff80, title=":shopping_cart: Shopping District",
				description = "Purchase 11{} for 1000{}. `;buy amulet`".format("<:amulet:573071120685596682>", "<:jade:555630314282811412>"))
			embed.set_thumbnail(url=self.client.user.avatar_url)
			await ctx.channel.send(embed=embed)
		
	async def buy_amulet(self, user, ctx):
		if users.find_one({"user_id": str(user.id)}, {"_id": 0, "jades": 1})["jades"] >= 1000:
		
			users.update_one({"user_id": str(user.id)}, {"$inc": {"amulets": 11, "jades": -1000}})
			amulet = users.find_one({"user_id": str(user.id)}, {"_id": 0, "amulets": 1})["amulets"]
				
			msg = "{}, You have bought 11{}. You now have {}{}".format(user.mention, "<:amulet:573071120685596682>", amulet, "<:amulet:573071120685596682>")
			await ctx.channel.send(msg)
		else: 
			msg = "{}, You have insufficient {}".format(user.mention, "<:jade:555630314282811412>")
			await ctx.channel.send(msg)

		
		
def setup(client):
	client.add_cog(Economy(client))