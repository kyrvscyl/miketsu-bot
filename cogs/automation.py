"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import discord, json
from discord.ext import commands
import config.guild as guild

class Events(commands.Cog):
	
	def __init__(self, client):
		self.client = client
	
	# Whenever a member joins
	@commands.Cog.listener()
	async def on_member_join(self, member):
		
		default = self.client.get_channel(guild.guildDefault)
		msg = ":sparkles: Welcome to Patronus, {}. Kindly read your acceptance letter first.".format(member.mention)
		
		description = "Dear {},\n\nWe are pleased to accept you at House Patronus.\nDo browse the server's <#{}> channel for the basics and essentials of the guild then proceed to <#{}> to assign yourself some roles.\n\nWe await your return owl.\n\nYours Truly,\nThe Headmaster".format(member.name, guild.guildWelcome, guild.guildSorting)
		embed = discord.Embed(title=":love_letter: Acceptance Letter".format(member), description=description)
		
		await member.send(embed=embed)
		await default.send(msg)
	
def setup(client):
	client.add_cog(Events(client))