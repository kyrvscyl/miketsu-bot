"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import discord, json
from cogs.mongo.db import bounty
from discord.ext import tasks, commands
from datetime import datetime
from itertools import cycle

status = cycle(["with the peasants", "with their feelings", "fake Onmyoji", "with Susabi"])

# Date and Time
time_stamp = datetime.now().strftime("%d.%b %Y %H:%M:%S")
time_stamp2 = datetime.now().strftime("%m.%d.%Y.%H%M")

class Startup(commands.Cog):
	
	def __init__(self, client):
		self.client = client
	
	# Bot logging in
	@commands.Cog.listener()
	async def on_ready(self):
		print("Initializing...")
		print("-------")
		print("Logged in as {0.user}".format(self.client))
		# Say Hi to me!a
		print("Hi! {}!".format(self.client.get_user(180717337475809281)))
		print("Time now: {}".format(time_stamp))
		print("-------")
		print("Peasant Count: {}".format(len(self.client.users)))
		self.changeStatus.start()
		# self.changeCastle.start()
		print("-------")
	
	@tasks.loop(seconds=1200)
	async def changeStatus(self):
		await self.client.change_presence(activity=discord.Game(next(status)))
	
	@commands.command()
	async def info(self, ctx):
		await ctx.channel.send("Hello! I'm Miketsu. I am sharded by kyrvscyl. To see the list of my commands, type `;help` or `;help dm`")
	
	@commands.command(aliases=["h"])
	async def help(self, ctx, *args):
		embed = discord.Embed(color = 0xffff80, title = "My Commands",
			description = ":earth_asia: Economy\n`;daily`, `;weekly`, `;profile`, `;profile <@mention>`, `;buy`, `;summon`, `;evolve`, `;list <rarity>`, `;my <shikigami>`, `;shiki <shikigami>` `;friendship`\n\n:trophy: LeaderBoard (lb)\n`;lb level`, `;lb SSR`, `;lb medals`, `;lb amulets`, `;lb fp`, `;lb ships`\n\n:bow_and_arrow: Gameplay\n`;raidc`, `;raidc <@mention>`, `;raid <@mention>`, `;encounter`, `;binfo <boss>`\n\n:information_source: Information\n`;bounty <shikigami>`\n\n:heart: Others\n`;compensate`, `;suggest`, `;update`, `;stickers`")
		try:
			if args[0].lower() == "dm":
				await ctx.author.send(embed=embed)
			else:
				await ctx.channel.send(embed=embed)
		except IndexError as error:
			await ctx.channel.send(embed=embed)
	
	@commands.command(aliases=["b"])
	async def bounty(self, ctx, *args):
		query = " ".join(args)
		if not query == "":
			try: 
				msg = bounty.find_one({"shikigami": query}, {"_id": 0, "location": 1})["location"]
				await ctx.channel.send(msg)
			except KeyError as error:
				msg = "I'm sorry. I did not catch that. Please requery."
				await ctx.channel.send(msg)
			except TypeError as error:
				msg = "I'm sorry. That shikigami does not exist in the bounty list."
				await ctx.channel.send(msg)	
		else:
			msg = "Hi! I can help you find bounty locations. Please type `;b <shikigami>`"
			await ctx.channel.send(msg)
	
	@commands.command()
	async def suggest(self, ctx, *args):
		administrator = self.client.get_user(180717337475809281)
		try: 
			if args[0] != "":
				msg1 = "{} suggested: {}".format(ctx.author, " ".join(args))
				msg2 = "{}, thank you for that suggestion.".format(ctx.author.mention)
				await administrator.send(msg1)
				await ctx.channel.send(msg2)
		except IndexError as Error:
			msg = "Hi, {}!, I can collect suggestions. Please provide one.".format(ctx.author.mention)
			await ctx.channel.send(msg)
	
def setup(client):
	client.add_cog(Startup(client))