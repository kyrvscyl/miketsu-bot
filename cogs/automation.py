"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import discord, json, pytz
from datetime import datetime
from cogs.mongo.db import books, users
from discord.ext import commands

# Date and Time
tz_target = pytz.timezone("America/Atikokan")

class Events(commands.Cog):
	
	def __init__(self, client):
		self.client = client
	
	# Whenever a member joins
	@commands.Cog.listener()
	async def on_member_join(self, member):
		
		# Setup Variables
		time_stamp = datetime.now(tz=tz_target).strftime("%b %d, %Y %mEST")
		guild = member.guild
		request = books.find_one({"server": "{}".format(guild.id)}, {"_id": 0, "welcome": 1, "sorting": 1, "landing_zone": 1, "scroll-of-everything": 1, "default_role": 1})
		welcome = request["welcome"]
		sorting = request["sorting"]
		landing_zone = request["landing_zone"]
		record_scroll = request["scroll-of-everything"]
		default_role = request["default_role"]
		scrolls = member.guild.member_count
		guild_icon = member.guild.icon_url
		
		# Sets default role
		default_role2 = guild.get_role(int(default_role))
		await member.add_roles(default_role2)
		
		# Landing Zone 
		msg = ":sparkles:Welcome to Patronus, {}. Kindly read your acceptance letter first".format(member.mention)
		await self.client.get_channel(int(landing_zone)).send(msg)
		
		# Acceptance Letter
		description = "Dear {},\n\nWe are pleased to accept you at House Patronus.\nDo browse the server's <#{}> channel for the basics and essentials of the guild then proceed to <#{}> to assign yourself some roles.\n\nWe await your return owl.\n\nYours Truly,\nThe Headmaster".format(member.name, welcome, sorting)
		embed = discord.Embed(color=0xffff80, title=":love_letter: Acceptance Letter".format(member), description=description)
		await member.send(embed=embed)
		
		# Scroll of Everything
		embed = discord.Embed(color=0xffff80, title=":newspaper2: Memory Scroll Update", description=">> {} has joined the House!\n\nSending acceptance letter.. :love_letter:".format(member.mention))
		embed.set_thumbnail(url=member.avatar_url)
		embed.set_footer(text="Total Scrolls: {} | {}".format(scrolls, time_stamp), icon_url=guild_icon)
		
		await self.client.get_channel(int(record_scroll)).send(embed=embed)
	
	@commands.Cog.listener()
	async def on_member_remove(self, member):
		
		users.delete_one({"user_id": str(member.id)})
		
		time_stamp = datetime.now(tz=tz_target).strftime("%b %d, %Y %mEST")
		guild_id = member.guild.id
		request = books.find_one({"server": "{}".format(guild_id)}, {"_id": 0, "scroll-of-everything": 1})
		record_scroll = request["scroll-of-everything"]
		scrolls = member.guild.member_count
		guild_icon = member.guild.icon_url
		
		# Scroll of Everything
		embed = discord.Embed(color=0xac330f, title=":newspaper2: Memory Scroll Update", description=">> {} has left the House!\n\nObliviating their memory scroll..:sparkles:".format(member.mention))
		embed.set_thumbnail(url=member.avatar_url)
		embed.set_footer(text="Total Scrolls: {} | {}".format(scrolls, time_stamp), icon_url=guild_icon)

		await self.client.get_channel(int(record_scroll)).send(embed=embed)
	
def setup(client):
	client.add_cog(Events(client))