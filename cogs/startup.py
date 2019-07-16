"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import os
from datetime import datetime
from itertools import cycle

import discord
import pytz
from discord.ext import tasks, commands

from cogs.error import logging, get_f

file = os.path.basename(__file__)[:-3:]
emoji_m = "<:medal:573071121545560064>"
emoji_j = "<:jade:555630314282811412>"
emoji_c = "<:coin:573071121495097344>"
emoji_f = "<:friendship:555630314056318979>"
emoji_a = "<:amulet:573071120685596682>"


status = cycle([
    "with the peasants",
    "with their feelings",
    "fake Onmyoji",
    "with Susabi",
    "in Patronusverse"
])


def pluralize(singular, count):
    if count > 1:
        return singular + "s"
    else:
        return singular


class Startup(commands.Cog):

    def __init__(self, client):
        self.client = client


    @commands.command()
    @commands.guild_only()
    async def ping(self, ctx):
        await ctx.send('Pong! {0}ms'.format(round(self.client.latency, 1)))


    @commands.Cog.listener()
    async def on_ready(self):
        print("Initializing...")
        print("-------")
        print("Logged in as {0.user}".format(self.client))
        print("Hi! {}!".format(self.client.get_user(180717337475809281)))
        print("Time now: {}".format(datetime.now(tz=pytz.timezone("Asia/Manila")).strftime("%d.%b %Y %H:%M:%S")))
        print("-------")
        print("Peasant Count: {}".format(len(self.client.users)))
        self.change_status.start()
        print("-------")


    @tasks.loop(seconds=1200)
    async def change_status(self):
        await self.client.change_presence(activity=discord.Game(next(status)))


    @commands.command()
    @commands.guild_only()
    async def info(self, ctx):

        msg = "Hello! I'm Miketsu. To see the list of my commands, type `;help` or `;help dm`"
        await ctx.channel.send(msg)


    @commands.command(aliases=["h"])
    async def help(self, ctx, *args):

        description = \
            "🌏 Economy\n`;daily`, `;weekly`, `;profile`, `;profile <@mention>`, `;buy`, `;summon`, " \
            "`;evolve`, `;list <rarity>`, `;my <shikigami>`, `;shiki <shikigami>` `;friendship`\n\n" \
            "🏆 LeaderBoard (lb)\n`;lb level`, `;lb SSR`, `;lb medals`, `;lb amulets`, `;lb fp`, " \
            "`;lb ships`, `;lb streak`\n\n" \
            "🏹 Game play\n`;raidc`, `;raidc <@mention>`, `;raid <@mention>`, " \
            "`;encounter`, `;binfo <boss>`\n\n" \
            "ℹ Information\n`;bounty <shikigami>`\n\n" \
            "❤ Others\n`;compensate`, `;suggest`, `;stickers`"
        embed = discord.Embed(color=0xffff80, title="My Commands", description=description)

        try:
            if args[0].lower() == "dm":
                try:
                    await ctx.author.send(embed=embed)
                except discord.errors.Forbidden:
                    logging(file, get_f(), "discord.errors.Forbidden")
                    await ctx.channel.send(f"I can't direct message you, {ctx.author.mention}")
            else:
                await ctx.channel.send(embed=embed)
        except IndexError:
            await ctx.channel.send(embed=embed)


    @commands.command()
    @commands.guild_only()
    async def suggest(self, ctx, *, suggestion):
        administrator = self.client.get_user(180717337475809281)
        await administrator.send(f"{ctx.author} suggested: {suggestion}")
        await ctx.channel.send(f"{ctx.author.mention}, thank you for that suggestion.")


def setup(client):
    client.add_cog(Startup(client))
