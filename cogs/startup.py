"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
from datetime import datetime
from itertools import cycle

import discord
from discord.ext import tasks, commands

from cogs.mongo.db import bounty

status = cycle(["with the peasants", "with their feelings", "fake Onmyoji", "with Susabi", "in Patronusverse"])


# noinspection PyCallingNonCallable
class Startup(commands.Cog):

    def __init__(self, client):
        self.client = client

    # Bot logging in
    @commands.Cog.listener()
    async def on_ready(self):
        time_stamp = datetime.now().strftime("%d.%b %Y %H:%M:%S")
        print("Initializing...")
        print("-------")
        print("Logged in as {0.user}".format(self.client))
        print("Hi! {}!".format(self.client.get_user(180717337475809281)))
        print("Time now: {}".format(time_stamp))
        print("-------")
        print("Peasant Count: {}".format(len(self.client.users)))
        self.change_status.start()
        print("-------")

    @tasks.loop(seconds=1200)
    async def change_status(self):
        await self.client.change_presence(activity=discord.Game(next(status)))

    @commands.command()
    async def info(self, ctx):
        await ctx.channel.send(
            "Hello! I'm Miketsu. I am sharded by kyrvscyl. To see the list of my commands, type `;help` or `;help dm`")

    @commands.command(aliases=["h"])
    async def help(self, ctx, *args):
        embed = discord.Embed(color=0xffff80, title="My Commands",
                              description=":earth_asia: Economy\n`;daily`, `;weekly`, `;profile`, `;profile "
                                          "<@mention>`, `;buy`, `;summon`, `;evolve`, `;list <rarity>`, "
                                          "`;my <shikigami>`, `;shiki <shikigami>` `;friendship`\n\n"
                                          ":trophy: LeaderBoard (lb)\n`;lb level`, `;lb SSR`, `;lb medals`, "
                                          "`;lb amulets`, `;lb fp`, `;lb ships`, `;lb streak`\n\n"
                                          ":bow_and_arrow: Game play\n`;raidc`, `;raidc <@mention>`, "
                                          "`;raid <@mention>`, `;encounter`, `;binfo <boss>`\n\n"
                                          ":information_source: Information\n`;bounty <shikigami>`\n\n:heart: "
                                          "Others\n`;compensate`, `;suggest`, `;update`, `;stickers`")
        try:
            if args[0].lower() == "dm":
                await ctx.author.send(embed=embed)
            else:
                await ctx.channel.send(embed=embed)
        except IndexError:
            await ctx.channel.send(embed=embed)

    @commands.command(aliases=["b"])
    async def bounty(self, ctx, *args):
        query = " ".join(args)
        if not query == "":
            try:
                await ctx.channel.send(bounty.find_one({"shikigami": query}, {"_id": 0, "location": 1})["location"])
            except KeyError:
                await ctx.channel.send("I'm sorry. I did not catch that. Please re-query.")
            except TypeError:
                await ctx.channel.send("I'm sorry. That shikigami does not exist in the bounty list.")
        else:
            await ctx.channel.send("Hi! I can help you find bounty locations. Please type `;b <shikigami>`")

    @commands.command()
    async def suggest(self, ctx, *args):
        administrator = self.client.get_user(180717337475809281)
        try:
            if args[0] != "":
                await administrator.send(f"{ctx.author} suggested: {' '.join(args)}")
                await ctx.channel.send(f"{ctx.author.mention}, thank you for that suggestion.")
        except IndexError:
            await ctx.channel.send(f"Hi, {ctx.author.mention}!, I can collect suggestions. Please provide one.")


def setup(client):
    client.add_cog(Startup(client))
