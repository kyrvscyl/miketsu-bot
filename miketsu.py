"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import discord, json, os
from datetime import datetime
import config.guild as guild
from discord.ext import commands

# Directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Date and Time
timeStamp = datetime.now().strftime("%d.%b %Y %H:%M:%S")

# Instantiation
client = discord.Client()
client = commands.Bot(command_prefix = ";")
client.remove_command("help")

# Runs the cogs
for filename in os.listdir("./cogs"):
	if filename.endswith(".py"):
		client.load_extension(f"cogs.{filename[:-3]}")
		print("Loading {}..".format(filename))

@client.command(aliases=["l"])
@commands.is_owner()
async def load(ctx, extension):
	client.load_extension(f"cogs.{extension}")
	print("{} : Loading {}.py..".format(timeStamp, extension))
	msg = "Extension {}.py has been loaded".format(extension)
	await ctx.channel.send(msg)

@client.command(aliases=["ul"])
@commands.is_owner()
async def unload(ctx, extension):
	client.unload_extension(f"cogs.{extension}")
	print("{} : Unloading {}.py..".format(timeStamp, extension))
	msg = "Extension {}.py has been unloaded".format(extension)
	await ctx.channel.send(msg)

@client.command(aliases=["rl"])
@commands.is_owner()
async def reload(ctx, extension):
	client.unload_extension(f"cogs.{extension}")
	client.load_extension(f"cogs.{extension}")
	print("{} : Reloading {}.py..".format(timeStamp, extension))
	msg = "Extension {}.py has been reloaded".format(extension)
	await ctx.channel.send(msg)

print("-------")

client.run(guild.guildToken)
