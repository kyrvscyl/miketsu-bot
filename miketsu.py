"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import os
from datetime import datetime

import discord
from discord.ext import commands

from cogs.mongo.database import get_collections

os.chdir(os.path.dirname(os.path.abspath(__file__)))
token = os.environ.get("TOKEN")

# Collections
config = get_collections("config")

# Variables
prefix = ";"
time_start = datetime.now()
version = "1.7.beta"

# Instantiation
client = commands.Bot(command_prefix=prefix, case_insensitive=True)
client.remove_command("help")
cogs_loaded = []


for filename in sorted(os.listdir("./cogs")):
    if filename.endswith(".py"):
        client.load_extension(f"cogs.{filename[:-3]}")
        cogs_loaded.append(filename[:-3])
        print(f"Loading {filename}..")


def check_if_has_any_development_roles(ctx):
    for role in reversed(ctx.author.roles):
        if role.name in config.find_one({"list": 1}, {"_id": 0, "dev_roles": 1})["dev_roles"]:
            return True
    return False


@client.command(aliases=["stats", "statistics"])
async def show_bot_statistics(ctx):
    guilds_list = []
    for guild in client.guilds:
        guilds_list.append(guild.name)

    def days_hours_minutes(td):
        return td.days, td.seconds // 3600, (td.seconds // 60) % 60

    days, hours, minutes = days_hours_minutes(datetime.now() - time_start)
    timestamp = datetime.timestamp(datetime.now())

    embed = discord.Embed(
        title=f"{client.user.name} Bot", colour=discord.Colour(16770727),
        description="A fan made Onmyoji-themed exclusive Discord bot with a touch of wizarding magic ✨",
        timestamp=datetime.utcfromtimestamp(timestamp)
    )
    embed.set_thumbnail(url=client.user.avatar_url)
    embed.add_field(
        name="💻 Development",
        value=f"• Coding: <@!180717337475809281>\n"
              f"• Support Group: <@!437941992748482562>, <@!201402446705065984>",
        inline=False
    )
    embed.add_field(
        name="🛠 Statistics",
        value=f"• Version: {version}\n"
              f"• Servers Count: {len(guilds_list)}\n"
              f"• Servers: {' ,'.join(guilds_list)}\n"
              f"• Users: {len(client.users)}\n"
              f"• Running Time: {days}d, {hours}h, {minutes}m\n"
              f"• Ping: {round(client.latency, 5)} seconds",
        inline=False
    )
    embed.add_field(name="💾 Modules", value="{}".format(", ".join(sorted(cogs_loaded))))
    await ctx.channel.send(embed=embed)


@client.command(aliases=["load", "l"])
@commands.check(check_if_has_any_development_roles)
async def cogs_extension_load(ctx, extension):
    try:
        client.load_extension(f"cogs.{extension}")
        cogs_loaded.append(f"{extension}")
        print(f"Loading {extension}.py..")
    except commands.ExtensionNotLoaded:
        await ctx.message.add_reaction("❌")
    else:
        await ctx.message.add_reaction("✅")


@client.command(aliases=["unload", "ul"])
@commands.check(check_if_has_any_development_roles)
async def cogs_extension_unload(ctx, extension):
    try:
        client.unload_extension(f"cogs.{extension}")
        cogs_loaded.remove(f"{extension}")
        print(f"Unloading {extension}.py..")
    except commands.ExtensionNotLoaded:
        await ctx.message.add_reaction("❌")
    else:
        await ctx.message.add_reaction("✅")


@client.command(aliases=["reload", "rl"])
@commands.check(check_if_has_any_development_roles)
async def cogs_extension_reload(ctx, extension):
    try:
        client.reload_extension(f"cogs.{extension}")
        print(f"Reloading {extension}.py..")
    except commands.ExtensionNotLoaded:
        await ctx.message.add_reaction("❌")
    except commands.ExtensionNotFound:
        await ctx.message.add_reaction("❌")
    else:
        await ctx.message.add_reaction("✅")


@client.command(aliases=["shutdown"])
@commands.check(check_if_has_any_development_roles)
async def cogs_extension_shutdown(ctx):
    for file_name in os.listdir("./cogs"):
        try:
            if file_name.endswith(".py"):
                client.unload_extension(f"cogs.{file_name[:-3]}")
                cogs_loaded.remove(f"{file_name[:-3]}")
                print(f"Unloading {file_name}..")
        except commands.ExtensionNotLoaded:
            continue

    await ctx.message.add_reaction("✅")


@client.command(aliases=["initialize"])
@commands.check(check_if_has_any_development_roles)
async def cogs_extension_initialize(ctx):
    for file_name in os.listdir("./cogs"):
        try:
            if file_name.endswith(".py"):
                client.load_extension(f"cogs.{file_name[:-3]}")
                cogs_loaded.append(f"{file_name[:-3]}")
                print(f"Loading {file_name}..")
        except commands.ExtensionAlreadyLoaded:
            continue
        except commands.ExtensionFailed:
            continue

    await ctx.message.add_reaction("✅")


print("-------")

try:
    client.run(token)
except RuntimeError:
    pass
