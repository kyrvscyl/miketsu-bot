"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import discord, json, os
from datetime import datetime
from discord.ext import commands
from pymongo import MongoClient
	
# Directory/ Bot Name
os.chdir(os.path.dirname(os.path.abspath(__file__)))
shikigami = os.path.basename(__file__)[:-3:]

# Mongo Startup
memory = MongoClient("mongodb+srv://headmaster:headmaster@memory-scrolls-uhsu0.mongodb.net/test?retryWrites=true&w=majority")
shikigamis = memory["bukkuman"]["shikigamis"]
token = shikigamis.find_one({"{}".format(shikigami): {"$type": "string"}}, {"_id": 0, shikigami: 1})[shikigami]
memory.close()

# Date and Time
time_stamp = datetime.now().strftime("%d.%b %Y %H:%M:%S")

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
	print("{} : Loading {}.py..".format(time_stamp, extension))
	
	msg = "Extension {}.py has been loaded".format(extension)
	await ctx.channel.send(msg)

@client.command(aliases=["ul"])
@commands.is_owner()
async def unload(ctx, extension):
	client.unload_extension(f"cogs.{extension}")
	print("{} : Unloading {}.py..".format(time_stamp, extension))
	
	msg = "Extension {}.py has been unloaded".format(extension)
	await ctx.channel.send(msg)

@client.command(aliases=["rl"])
@commands.is_owner()
async def reload(ctx, extension):
	client.unload_extension(f"cogs.{extension}")
	client.load_extension(f"cogs.{extension}")
	print("{} : Reloading {}.py..".format(time_stamp, extension))
	
	msg = "Extension {}.py has been reloaded".format(extension)
	await ctx.channel.send(msg)

@client.command()
@commands.is_owner()
async def shutdown(ctx):
	for filename in os.listdir("../cogs"):
		if filename.endswith(".py") and filename != "error.py":
			client.unload_extension(f"cogs.{filename[:-3]}")
			print("Unloading {}..".format(filename))

	msg = "Bye-bye!"
	await ctx.channel.send(msg)

@client.command()
@commands.is_owner()
async def initialize(ctx):
	for filename in os.listdir("../cogs"):
		if filename.endswith(".py"):
			client.load_extension(f"cogs.{filename[:-3]}")
			print("Loading {}..".format(filename))

	msg = "Loading arrows.."
	await ctx.channel.send(msg)

print("-------")

client.run(token)