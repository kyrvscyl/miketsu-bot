
"""
Discord Miketsu Bot.
kyrvscyl, 2021
"""

import discord
from discord.ext import commands
from discord_slash import SlashCommand

from cogs.ext.initialize import *

os.chdir(os.path.dirname(os.path.abspath(__file__)))

intents = discord.Intents.default()
intents.members = True

client = commands.Bot(command_prefix=command_prefix, case_insensitive=True, intents=intents)
client.remove_command("help")

slash = SlashCommand(client, sync_commands=True)

config.update_one({"var": 1}, {"$set": {"clock": False}})


def cogs_extension_startup():
    for filename in sorted(os.listdir("./cogs")):
        if filename.endswith(".py"):
            try:
                client.load_extension(f"cogs.{filename[:-3]}")
            except commands.ExtensionNotLoaded:
                print(f"Failed to load {filename}..")
            else:
                cogs_loaded.append(filename[:-3])
                print(f"Loading {filename}..")


@slash.slash(
    name="stats", guild_ids=[id_guild], description="Shows some bot statistics",
)
async def show_bot_statistics(ctx):

    def get_days_hours_minutes(td):
        return td.days, td.seconds // 3600, (td.seconds // 60) % 60

    bot_info = await client.application_info()
    days, hours, minutes = get_days_hours_minutes(datetime.now() - time_start)

    modules_loaded = ', '.join(sorted(cogs_loaded))
    if len(cogs_loaded) == 0:
        modules_loaded = None

    embed = discord.Embed(
        colour=colour,
        title=f"{client.user.name} Bot",
        description="A fan made Onmyoji-themed exclusive Discord bot",
        timestamp=get_timestamp()
    )
    embed.set_thumbnail(url=client.user.avatar_url)
    embed.add_field(
        name="Development",
        value=f"• Coding: <@!{bot_info.owner.id}>\n"
              f"• Support Group: <@!437941992748482562>\n"
              f"• Illustration by <@!628219450931544065>",
        inline=False
    )
    embed.add_field(
        name="Statistics",
        value=f"• Version: {version}\n"
              f"• Users: {len(client.users)}\n"
              f"• Running Time: {days}d, {hours}h, {minutes}m\n"
              f"• Ping: {round(client.latency, 5)} seconds",
        inline=False
    )
    embed.add_field(
        name=f"Modules [{len(cogs_loaded)}]",
        value=f"{modules_loaded}"
    )
    await process_msg_submit(ctx, None, embed)


@client.command(aliases=["load", "l"])
@commands.is_owner()
async def cogs_extension_load(ctx, extension):

    try:
        client.load_extension(f"cogs.{extension}")
    except commands.ExtensionNotFound:
        await process_msg_reaction_add(ctx.message, "❌")
    else:
        cogs_loaded.append(f"{extension}")
        print(f"Loading {extension}.py..")
        await process_msg_reaction_add(ctx.message, "✅")


@client.command(aliases=["unload", "ul"])
@commands.is_owner()
async def cogs_extension_unload(ctx, extension):
    try:
        client.unload_extension(f"cogs.{extension}")
    except commands.ExtensionNotLoaded:
        await process_msg_reaction_add(ctx.message, "❌")
    else:
        cogs_loaded.remove(f"{extension}")
        print(f"Unloading {extension}.py..")
        await process_msg_reaction_add(ctx.message, "✅")


@client.command(aliases=["reload", "rl"])
@commands.is_owner()
async def cogs_extension_reload(ctx, extension):

    try:
        client.reload_extension(f"cogs.{extension}")
    except commands.ExtensionNotLoaded:
        await process_msg_reaction_add(ctx.message, "❌")
    except commands.ExtensionNotFound:
        await process_msg_reaction_add(ctx.message, "❌")
    else:
        print(f"Reloading {extension}.py..")
        await process_msg_reaction_add(ctx.message, "✅")


@client.command(aliases=["shutdown"])
@commands.is_owner()
async def cogs_extension_shutdown(ctx):

    for file_name in os.listdir("./cogs"):
        if file_name.endswith(".py"):
            try:
                client.unload_extension(f"cogs.{file_name[:-3]}")
                cogs_loaded.remove(f"{file_name[:-3]}")
            except commands.ExtensionNotLoaded:
                continue
            else:
                print(f"Unloading {file_name}..")

    await process_msg_reaction_add(ctx.message, "✅")


@client.command(aliases=["initialize"])
@commands.is_owner()
async def cogs_extension_initialize(ctx):

    for file_name in os.listdir("./cogs"):
        if file_name.endswith(".py"):
            try:
                client.load_extension(f"cogs.{file_name[:-3]}")
                cogs_loaded.append(f"{file_name[:-3]}")
            except commands.ExtensionAlreadyLoaded:
                continue
            except commands.ExtensionFailed:
                continue
            else:
                print(f"Loading {file_name}..")

    await process_msg_reaction_add(ctx.message, "✅")


cogs_extension_startup()

print("-------")

try:
    client.run(token)
except RuntimeError:
    pass
