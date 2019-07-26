"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import inspect
import os
from datetime import datetime

import discord
import pytz
from discord.ext import commands

from cogs.mongo.db import errors

file_name = os.path.basename(__file__)[:-3:]


def get_time():
    tz_target = pytz.timezone("America/Atikokan")
    return datetime.now(tz=tz_target)


def get_date_local():
    tz_target = pytz.timezone("Asia/Manila")
    return datetime.now(tz=tz_target).strftime("%Y-%m-%d")


def get_timestamp_local():
    tz_target = pytz.timezone("Asia/Manila")
    return datetime.now(tz=tz_target).strftime("%Y-%m-%d %H:%M:%S")


def get_f():
    return str(inspect.stack()[1][3])


def logging(file, function_name, error):
    error_report = {
        "time": get_timestamp_local(),
        "file": file,
        "function": function_name,
        "error": error
    }

    if errors.find_one({"date": get_date_local()}, {"_id": 0}) is None:
        errors.insert_one({"date": get_date_local(), "report": []})

    errors.update_one({
        "date": get_date_local()}, {
        "$push": {
            "report": error_report
        }
    })


class Error(commands.Cog):

    def __init__(self, client):
        self.client = client

    async def submit_error(self, ctx, error):
        channel = self.client.get_channel(584631677804871682)
        embed = discord.Embed(color=ctx.author.colour, title=f"{ctx.author} triggered an error")
        embed.add_field(
            name=f"Command: {ctx.command}",
            value=error
        )
        embed.set_footer(text="{}".format(get_time().strftime("%d.%b %Y %H:%M EST")))
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):

        if isinstance(error, commands.CheckFailure):
            logging(file_name, get_f(), f"commands.CheckFailure for {ctx.command} from {ctx.author.name}")

        elif isinstance(error, commands.NotOwner):
            logging(file_name, get_f(), "commands.NotOwner")

        elif isinstance(error, commands.CommandOnCooldown):
            await self.submit_error(ctx, error)

        elif isinstance(error, commands.MissingRequiredArgument):

            if str(ctx.command) == "collect_suggestion":
                embed = discord.Embed(
                    title="suggest",
                    colour=discord.Colour(0xffe6a7),
                    description="submit suggestions for the bot or server\n"
                                "available to use through direct message"
                )
                embed.add_field(name="Example", value="*`;suggest add new in-game stickers!`*", inline=False)
                await ctx.channel.send(embed=embed)

            elif str(ctx.command) == "shrine_shikigami":
                embed = discord.Embed(
                    title="shrine", colour=discord.Colour(0xffe6a7),
                    description="exchange your shikigamis for talismans to acquire exclusive shikigamis"
                )
                embed.add_field(
                    name="Arguments",
                    value="*sacrifice, exchange*",
                    inline=False
                )
                embed.add_field(
                    name="Example",
                    value="*`;shrine exchange`*",
                    inline=False
                )
                await ctx.channel.send(embed=embed)

            elif str(ctx.command) == "leaderboard_show":
                embed = discord.Embed(
                    title="leaderboard, lb", colour=discord.Colour(0xffe6a7),
                    description="shows various leaderboards"
                )
                embed.add_field(
                    name="Arguments",
                    value="*SSR, SR, level, medals, amulets, friendship, ships, SSRstreak*",
                    inline=False
                )
                embed.add_field(name="Example", value="*`;leaderboard friendship`*", inline=False)
                await ctx.channel.send(embed=embed)

            elif str(ctx.command) == "shikigami_list_show":
                embed = discord.Embed(
                    title="shikigamis, shikis", colour=discord.Colour(0xffe6a7),
                    description="shows your or tagged member's shikigami pulls by rarity"
                )
                embed.add_field(name="Arguments", value="*SP, SSR, SR, R*", inline=False)
                embed.add_field(name="Format", value="*`;shikis <rarity> <optional: @member>`*", inline=False)
                await ctx.channel.send(embed=embed)

            elif str(ctx.command) == "profile_change_display":
                embed = discord.Embed(
                    title="display", colour=discord.Colour(0xffe6a7),
                    description="changes your profile display thumbnail")
                embed.add_field(name="Example", value="*`;display inferno ibaraki`*", inline=False)
                await ctx.channel.send(embed=embed)

            elif str(ctx.command) == "summon_perform":
                embed = discord.Embed(
                    title="summon, s", colour=discord.Colour(0xffe6a7),
                    description="simulate summon and collect shikigamis"
                )
                embed.add_field(name="Format", value="*`;summon <1 or 10>`*", inline=False)
                await ctx.channel.send(embed=embed)

            elif str(ctx.command) == "bounty_query":
                embed = discord.Embed(
                    title="bounty, b",
                    colour=discord.Colour(0xffe6a7),
                    description="search shikigami bounty locations"
                )
                embed.add_field(name="Format", value="*`;bounty <shikigami or its first 2 letters>`*", inline=False)
                await ctx.channel.send(embed=embed)

            elif str(ctx.command) == "post_book_reference":
                await ctx.message.add_reaction("❌")

            elif str(ctx.command) == "castle_customize_frame":
                embed = discord.Embed(
                    title="frame add, frame edit", colour=discord.Colour(0xffe6a7),
                    description="customize your own photo frame\n"
                                "appears in the castle's floors via `;wander`\n"
                                "use `add` first before using `edit` argument\n"
                                "use square photos for best results"
                )
                embed.add_field(
                    name="Format",
                    value="*`;frame add <name> <floor#1-7> <img_link or default> <desc.>`*", inline=False)
                embed.add_field(
                    name="Example",
                    value="*`;frame add xann 6 default Headless`*",
                    inline=False
                )
                await ctx.channel.send(embed=embed)

            elif str(ctx.command) == "announcement_post_embed":
                embed = discord.Embed(
                    title="announce", colour=discord.Colour(0xffe6a7),
                    description="sends an embed message\n"
                                "prioritization: description > title > img_link\n"
                                "where title and img_link are optional"
                )
                embed.add_field(name="Format", value="*`;announce <#channel> <title|description|img_link>`*")
                embed.add_field(name="Example", value="*`;announce #headlines @role reminder to...`*", inline=False)
                await ctx.channel.send(embed=embed)

            elif str(ctx.command) == "announcement_post_message":
                embed = discord.Embed(
                    colour=discord.Colour(0xffe6a7),
                    title="say",
                    description="allows me to repeat a text message"
                )
                embed.add_field(name="Format", value="*`;say <#channel or channel_id> <any message>`*")
                await ctx.channel.send(embed=embed)

            elif str(ctx.command) == "show_cycle_quest1":
                embed = discord.Embed(
                    colour=discord.Colour(0xffe6a7),
                    title="cycle",
                    description="Patronus quest command participants only\nrequired to finish at least one quest cycle"
                )
                embed.add_field(name="Format", value="*`;cycle <cycle#1> <@member or leave blank if for yourself>`*")
                embed.add_field(name="Example", value="*`;cycle 1`*")
                await ctx.channel.send(embed=embed)

            else:
                await self.submit_error(ctx, error)

        elif isinstance(error, commands.NoPrivateMessage):
            await self.submit_error(ctx, error)

        elif isinstance(error, commands.CommandNotFound):
            logging(file_name, get_f(), f"commands.CommandNotFound: {ctx.command}")

        elif isinstance(error, commands.ExtensionError):
            logging(file_name, get_f(), f"commands.ExtensionError: {ctx.message.content}")

        elif isinstance(error, commands.BadArgument):
            await self.submit_error(ctx, error)

        elif isinstance(error, commands.UserInputError):

            if str(ctx.command) in [
                "raid_perform_attack",
                "raid_perform_calculation",
                "profile_show",
                "friendship_give"
            ]:
                embed = discord.Embed(
                    title="Invalid member", colour=discord.Colour(0xffe6a7),
                    description="That member doesn't exist in this guild"
                )
                await ctx.channel.send(embed=embed)

            else:
                await self.submit_error(ctx, error)

        elif isinstance(error, commands.CommandInvokeError):

            if str(ctx.command) == "announcement_post_message":
                await ctx.channel.send("Please provide a valid channel")

            else:
                await self.submit_error(ctx, error)

        else:
            await self.submit_error(ctx, error)


def setup(client):
    client.add_cog(Error(client))
