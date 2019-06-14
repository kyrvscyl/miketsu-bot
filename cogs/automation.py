"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import discord, json
from cogs.mongo.db import books
from discord.ext import commands
# from pymongo import MongoClient

# Mongo Startup
# memory = MongoClient("mongodb+srv://headmaster:headmaster@memory-scrolls-uhsu0.mongodb.net/test?retryWrites=true&w=majority")
# memory = MongoClient("mongodb://localhost:27017/")
# books = memory["bukkuman"]["books"]

class Events(commands.Cog):
	
	def __init__(self, client):
		self.client = client
	
	def get_page(self, guild_id):
		request = books.find_one({"server": "{}".format(guild_id)}, {"_id": 0, "welcome": 1, "sorting": 1, "landing_zone": 1})
		welcome = request["welcome"]
		sorting = request["sorting"]
		landing_zone = request["landing_zone"]
		return welcome, sorting, landing_zone
	
	# Whenever a member joins
	@commands.Cog.listener()
	async def on_member_join(self, member):
		
		guild_id = member.guild.id
		welcome, sorting, landing_zone = self.get_page(guild_id)
		
		msg = ":sparkles:Welcome to Patronus, {}. Kindly read your acceptance letter first.".format(member.mention)
		description = "Dear {},\n\nWe are pleased to accept you at House Patronus.\nDo browse the server's <#{}> channel for the basics and essentials of the guild then proceed to <#{}> to assign yourself some roles.\n\nWe await your return owl.\n\nYours Truly,\nThe Headmaster".format(member.name, welcome, sorting)
		embed = discord.Embed(color=0xffff80, title=":love_letter: Acceptance Letter".format(member), description=description)
		
		await self.client.get_channel(int(landing_zone)).send(msg)
		await member.send(embed=embed)
		
def setup(client):
	client.add_cog(Events(client))