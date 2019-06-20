"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""

import os

import discord
from discord.ext import commands

from cogs.mongo.db import shikigamis

# Directory/ Bot Name
os.chdir(os.path.dirname(os.path.abspath(__file__)))
shikigami = os.path.basename(__file__)[:-3:]

# Token
token = shikigamis.find_one({shikigami: {"$type": "string"}}, {"_id": 0, shikigami: 1})[shikigami]

# Instantiation
client = discord.Client()
# noinspection PyRedeclaration
client = commands.Bot(command_prefix=";")
client.remove_command("help")

# Runs the cogs
for filename in os.listdir("./cogs"):
    if filename.endswith(".py"):
        client.load_extension(f"cogs.{filename[:-3]}")
        print(f"Loading {filename}..")


@client.command(aliases=["l"])
@commands.is_owner()
async def load(ctx, extension):
    client.load_extension(f"cogs.{extension}")
    print(f"Loading {extension}.py..")
    await ctx.channel.send(f"Extension {extension}.py has been loaded")


@client.command(aliases=["ul"])
@commands.is_owner()
async def unload(ctx, extension):
    client.unload_extension(f"cogs.{extension}")
    print(f"Unloading {extension}.py..")
    await ctx.channel.send("Extension {extension}.py has been unloaded")


@client.command(aliases=["rl"])
@commands.is_owner()
async def reload(ctx, extension):
    client.unload_extension(f"cogs.{extension}")
    client.load_extension(f"cogs.{extension}")
    print("Reloading {extension}.py..")
    await ctx.channel.send(f"Extension {extension}.py has been reloaded")


# noinspection PyShadowingNames
@client.command()
@commands.is_owner()
async def shutdown(ctx):
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and filename != "error.py":
            client.unload_extension(f"cogs.{filename[:-3]}")
            print(f"Unloading {filename}..")
    await ctx.channel.send("Bye-bye!")


# noinspection PyShadowingNames
@client.command()
@commands.is_owner()
async def initialize(ctx):
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            client.load_extension(f"cogs.{filename[:-3]}")
            print(f"Loading {filename}..")
    await ctx.channel.send("Loading arrows..")


print("-------")

client.run(token)
