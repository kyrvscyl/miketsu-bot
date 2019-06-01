"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import discord, json
from datetime import datetime
from discord.ext import commands
import config.guild as guild

# Date and Time
timeStamp = datetime.now().strftime("%d.%b %Y %H:%M:%S")

class Error(commands.Cog):
	
	def __init__(self, client):
		self.client = client
	
	@commands.Cog.listener()
	async def on_command_error(self, ctx, error):
		
		# Probably not an admin
		if isinstance(error, commands.CheckFailure):
			return
		
		# Avoidance of spam
		elif isinstance(error, commands.CommandOnCooldown):
		
			if str(ctx.command) == "duel":
				msg = '{}, there is an ongoing duel, try again once it is finished.'.format(ctx.author.mention)
				await ctx.channel.send(msg)
				
			elif str(ctx.command) == "encounter":
				msg = '{}, there is an ongoing search, try again it is finished.'.format(ctx.author.mention)
				await ctx.channel.send(msg)
		
		# Lacks arguments
		elif isinstance(error, commands.MissingRequiredArgument):
			
			if str(ctx.command) == "summon":
				msg = "Use `;summon <1 or 10>`"
				await ctx.channel.send(msg)
			else: 
				print("{} : {}.".format(timeStamp, error))
		
		# No DM commands
		elif isinstance(error, commands.NoPrivateMessage):
			return
		
		# Silently ignore invalid commands
		elif isinstance(error, commands.CommandNotFound):
			return
		
		# Hot loading errors
		elif isinstance(error, commands.ExtensionError):
			print("{} : {}.".format(timeStamp, error))
		
		# Catching errors
		else :
			user = self.client.get_user(180717337475809281)
			msg = "{} : {}.".format(timeStamp, error)
			await user.send(msg)
			print(msg)
		
def setup(client):
	client.add_cog(Error(client))