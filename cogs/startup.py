"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
from datetime import datetime
from itertools import cycle

import discord
from discord.ext import tasks, commands

from cogs.mongo.db import bounty, shikigami

status = cycle(["with the peasants", "with their feelings", "fake Onmyoji", "with Susabi", "in Patronusverse"])


# noinspection PyCallingNonCallable
class Startup(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command()
    async def ping(self, ctx):
        await ctx.send('Pong! {0}ms'.format(round(self.client.latency, 1)))

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
        
        msg = "Hello! I'm Miketsu. I am sharded by kyrvscyl. To see the list of my commands, type `;help` or `;help dm`"
        await ctx.channel.send(msg)

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
                                          "Others\n`;compensate`, `;suggest`, `;stickers`")
        try:

            if args[0].lower() == "dm":
                await ctx.author.send(embed=embed)

            else:
                await ctx.channel.send(embed=embed)

        except IndexError:
            await ctx.channel.send(embed=embed)

    @commands.command(aliases=["b"])
    async def bounty(self, ctx, *, query):

        profile = bounty.find_one({"aliases": query.lower()}, {"_id": 0})

        if profile is not None:
            shikigami_profile = shikigami.find_one({"shikigami.name": query.title()},
                                                   {"shikigami.$.name": 1})

            if shikigami_profile is not None:
                image = shikigami_profile["shikigami"][0]["thumbnail"]["pre_evo"]
            else:
                image = ""

            name = profile["bounty"].title()
            description = ("• " + "\n• ".join(profile["location"]))
            aliases = profile["aliases"]
            text = ", ".join(aliases)

            embed = discord.Embed(color=ctx.author.colour, title=f"Bounty location for {name}:",
                                  description=description)
            embed.set_footer(icon_url=image, text=f"aliases: {text}")
            await ctx.channel.send(embed=embed)

        else:
            await ctx.channel.send("No results. If you believe this should have results, use `;suggest` command")

    @commands.command(aliases=["baa"])
    @commands.is_owner()
    async def bounty_add_alias(self, ctx, *args):

        name = args[0].replace("_", " ").lower()
        alias = " ".join(args[1::]).replace("_", " ").lower()
        bounty.update_one({"aliases": name}, {"$push": {"aliases": alias}})
        await ctx.channel.send(f"Successfully added {alias} to {name}")

    @commands.command()
    async def suggest(self, ctx, *, suggestion):

        administrator = self.client.get_user(180717337475809281)
        await administrator.send(f"{ctx.author} suggested: {suggestion}")
        await ctx.channel.send(f"{ctx.author.mention}, thank you for that suggestion.")


def setup(client):
    client.add_cog(Startup(client))
