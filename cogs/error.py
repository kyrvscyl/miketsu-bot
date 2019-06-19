"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import discord
import pytz
from datetime import datetime
from discord.ext import commands

# Timezone
tz_target = pytz.timezone("America/Atikokan")


class Error(commands.Cog):

    def __init__(self, client):
        self.client = client

    async def submit_error(self, ctx, error):
        time_stamp = datetime.now().strftime("%d.%b %Y %H:%M:%S")
        channel = self.client.get_channel(584631677804871682)

        embed = discord.Embed(color=ctx.author.colour, title=f"{ctx.author} triggered an error")
        embed.add_field(name="Command: {}".format(ctx.command), value=error)
        embed.set_footer(text="{}".format(time_stamp))
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
                await ctx.channel.send("Please provide a valid channel")

            elif isinstance(error, commands.ExpectedClosingQuoteError) \
                    or isinstance(error, commands.UnexpectedQuoteError):
                msg = "Double quotation marks must be prepended by a backslash. (e.g. `\\\"Proper way\\\"`)"
                await ctx.channel.send(msg)

        # Spam control
        elif isinstance(error, commands.CommandOnCooldown):

            if str(ctx.command) == "encounter":
                await ctx.channel.send(f"{ctx.author.mention}, there is an ongoing search, try again once it finishes")

            elif str(ctx.command) == "shoutout":
                await ctx.channel.send(f"{ctx.author.mention}, there is a shoutout already, try again later")

        # Lacks arguments
        elif isinstance(error, commands.MissingRequiredArgument):
            if str(ctx.command) == "summon":
                await ctx.channel.send("Use `;summon <1 or 10>`")

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
