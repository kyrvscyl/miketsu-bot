"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""

import os

import discord
from discord.ext import commands

from cogs.mongo.db import shikigamis

os.chdir(os.path.dirname(os.path.abspath(__file__)))
shikigami = os.path.basename(__file__)[:-3:]
token = shikigamis.find_one({shikigami: {"$type": "string"}}, {"_id": 0, shikigami: 1})[shikigami]

client = discord.Client()

# noinspection PyRedeclaration
client = commands.Bot(command_prefix=";")
client.remove_command("help")


for filename in os.listdir("./cogs"):
    if filename.endswith(".py"):
        client.load_extension(f"cogs.{filename[:-3]}")
        print(f"Loading {filename}..")


@client.command(aliases=["l"])
@commands.is_owner()
async def load(ctx, extension):
    client.load_extension(f"cogs.{extension}")
    print(f"Loading {extension}.py..")
    msg = await ctx.channel.send(f"Extension {extension}.py has been loaded")
    await msg.delete(delay=5)
    await ctx.message.delete(delay=5)


@client.command(aliases=["ul"])
@commands.is_owner()
async def unload(ctx, extension):
    client.unload_extension(f"cogs.{extension}")
    print(f"Unloading {extension}.py..")
    msg = await ctx.channel.send(f"Extension {extension}.py has been unloaded")
    await msg.delete(delay=5)
    await ctx.message.delete(delay=5)


@client.command(aliases=["rl"])
@commands.is_owner()
async def reload(ctx, extension):
    client.unload_extension(f"cogs.{extension}")
    client.load_extension(f"cogs.{extension}")
    print(f"Reloading {extension}.py..")
    msg = await ctx.channel.send(f"Extension {extension}.py has been reloaded")
    await msg.delete(delay=5)
    await ctx.message.delete(delay=5)


@client.command()
@commands.is_owner()
async def shutdown(ctx):
    for file_name in os.listdir("./cogs"):
        if file_name.endswith(".py") and file_name != "error.py":
            client.unload_extension(f"cogs.{file_name[:-3]}")
            print(f"Unloading {file_name}..")
    await ctx.channel.send("Bye-bye!")


@client.command()
@commands.is_owner()
async def initialize(ctx):
    for file_name in os.listdir("./cogs"):
        if file_name.endswith(".py"):
            client.load_extension(f"cogs.{file_name[:-3]}")
            print(f"Loading {file_name}..")
    await ctx.channel.send("Loading arrows..")


print("-------")

client.run(token)
