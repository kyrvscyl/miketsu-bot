"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import discord, json
from datetime import datetime
from discord.ext import commands

# Date and Time
time_stamp = datetime.now().strftime("%d.%b %Y %H:%M:%S")

class Error(commands.Cog):
	
	def __init__(self, client):
		self.client = client
	
	async def submit_error(self, ctx, error):
		user = ctx.author
		channel = self.client.get_channel(584631677804871682)
		
		embed=discord.Embed(color=0xffff80, title="{} triggered an error".format(user))
		embed.add_field(name="Command: {}".format(ctx.command), value=error)
		embed.set_footer(text="{}".format(time_stamp))
		print(error)
		await channel.send(embed=embed)
	
	@commands.Cog.listener()
	async def on_command_error(self, ctx, error):
		print(error)
		
		# Probably not an admin
		if isinstance(error, commands.CheckFailure):
			return
		
		# Broadcasting errors
		elif str(ctx.command) == "broadcast":
			if isinstance(error, commands.CommandInvokeError):
				msg = "Please provide a valid channel"	
				await ctx.channel.send(msg)
			
			elif isinstance(error, commands.ExpectedClosingQuoteError) or isinstance(error, commands.UnexpectedQuoteError):
				msg = "Double quotation marks must be prepended by a blackslash. (e.g. `\\\"Proper way\\\"`)"
				await ctx.channel.send(msg)
				
		# Spam control
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
			
			elif str(ctx.command) != "summon":
				await self.submit_error(ctx, error)
		
		# Commands under DM
		elif isinstance(error, commands.NoPrivateMessage):
			await self.submit_error(ctx, error)
		
		# Silently ignore invalid commands
		elif isinstance(error, commands.CommandNotFound):
			return
		
		# Hot loading errors
		elif isinstance(error, commands.ExtensionError):
			return

		# Catching other errors errors
		else:
			await self.submit_error(ctx, error)
			
				
def setup(client):
	client.add_cog(Error(client))