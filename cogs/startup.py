"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
from datetime import datetime
from itertools import cycle

import discord
import pytz
from discord.ext import tasks, commands

emoji_m = "<:medal:573071121545560064>"
emoji_j = "<:jade:555630314282811412>"
emoji_c = "<:coin:573071121495097344>"
emoji_f = "<:friendship:555630314056318979>"
emoji_a = "<:amulet:603989470328651787>"
emoji_sp = "<:SP:602707718603538442>"
emoji_ssr = "<:SSR:602707410515132456>"
emoji_sr = "<:SR:602707410922242048>"
emoji_r = "<:R_:602707410582241280>"
emoji_n = "<:N_:602707410540560414>"
emoji_t = "<:talisman:573071120685596682>"


status = cycle([
    "with the peasants via ;info",
    "with their feelings via ;info",
    "fake Onmyoji via ;info",
    "with Susabi via ;info",
    "in Patronusverse via ;info"
])


def pluralize(singular, count):
    if count > 1:
        return singular + "s"
    else:
        return singular


class Startup(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("Initializing...")
        print("-------")
        print("Logged in as {0.user}".format(self.client))
        print("Hi! {}!".format(self.client.get_user(180717337475809281)))
        print("Time now: {}".format(datetime.now(tz=pytz.timezone("Asia/Manila")).strftime("%d.%b %Y %H:%M:%S")))
        print("-------")
        self.change_status.start()
        print("-------")

    @tasks.loop(seconds=1200)
    async def change_status(self):
        try:
            await self.client.change_presence(activity=discord.Game(next(status)))
        except RuntimeError:
            pass

    @commands.command(aliases=["info"])
    async def show_greeting_message(self, ctx):
        embed = discord.Embed(
            colour=discord.Colour(0xffe6a7),
            description="To see my commands, type *`;help`* or *`;help dm`*"
        )
        embed.set_author(name="Hello there! I'm Miketsu! ~")
        await ctx.channel.send(embed=embed)

    @commands.command(aliases=["h", "help"])
    async def show_help_message(self, ctx, *args):
        embed = discord.Embed(
            title="help",
            colour=discord.Colour(0xffe6a7),
            description="append the prefix semi-colon *`;`*"
        )
        embed.set_thumbnail(url=self.client.user.avatar_url)
        embed.set_footer(text="*Head commands")
        embed.add_field(
            name="Economy",
            value="*daily, weekly, profile, display, buy, summon, "
                  "evolve, friendship, leaderboard, shikigamis, shrine, sail, pray*",
            inline=False
        )
        embed.add_field(
            name="Gameplay",
            value="*raid, raidc, encounter, bossinfo*"
        )
        embed.add_field(
            name="Others",
            value="*bounty, suggest, stickers, newsticker, wander, frame, frames, stats, announce*\\*, *manage*\\*",
            inline=False
        )

        try:
            if args[0].lower() == "dm":
                try:
                    await ctx.author.send(embed=embed)
                except discord.errors.Forbidden:
                    return
            else:
                await ctx.channel.send(embed=embed)
        except IndexError:
            await ctx.channel.send(embed=embed)

    @commands.command(aliases=["suggest"])
    async def collect_suggestion(self, ctx, *, suggestion):
        administrator = self.client.get_user(180717337475809281)
        await administrator.send(f"{ctx.author} suggested: {suggestion}")
        await ctx.message.add_reaction("📩")


def setup(client):
    client.add_cog(Startup(client))
