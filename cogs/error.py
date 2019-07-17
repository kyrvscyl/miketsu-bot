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

        elif isinstance(error, commands.BadArgument):

            if str(ctx.command) in ["raid", "raid_calculate"]:
                return

            else:
                await self.submit_error(ctx, error)

        elif isinstance(error, commands.CommandInvokeError):

            if str(ctx.command) == "broadcast":
                await ctx.channel.send("Please provide a valid channel")

            else:
                await self.submit_error(ctx, error)

        elif isinstance(error, commands.CommandOnCooldown):

            if str(ctx.command) == "encounter":
                await ctx.channel.send(f"{ctx.author.mention}, there is an ongoing search, try again once it finishes")

            elif str(ctx.command) == "shoutout":
                await ctx.channel.send(f"{ctx.author.mention}, there is a shoutout already, try again later")

            else:
                await self.submit_error(ctx, error)

        elif isinstance(error, commands.MissingRequiredArgument):

            if str(ctx.command) == "suggest":
                await ctx.channel.send(f"Hi, {ctx.author.mention}, I can collect suggestions. Kindly provide one.")

            elif str(ctx.command) == "summon":
                await ctx.channel.send("Use `;summon <1 or 10>`")

            elif str(ctx.command) == "bounty":
                await ctx.channel.send("Hi! I can search for bounty locations. Use `;bounty <shikigami>`")

            elif str(ctx.command) == "post_book_reference":
                await ctx.message.add_reaction("❌")

            elif str(ctx.command) == "announcement_post":
                await ctx.channel.send(
                    "Use `;announce <#channel> <title|description|image_link>` where title & image_link are optional"
                )

            else:
                await self.submit_error(ctx, error)

        elif isinstance(error, commands.NoPrivateMessage):
            await self.submit_error(ctx, error)

        elif isinstance(error, commands.CommandNotFound):
            logging(file_name, get_f(), f"commands.CommandNotFound: {ctx.command}")

        elif isinstance(error, commands.ExtensionError):
            logging(file_name, get_f(), f"commands.ExtensionError: {ctx.message.content}")

        else:
            await self.submit_error(ctx, error)


def setup(client):
    client.add_cog(Error(client))
