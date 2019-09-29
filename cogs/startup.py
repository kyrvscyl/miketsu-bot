"""
Startup Module
Miketsu, 2019
"""

import os
from datetime import datetime
from itertools import cycle

import discord
import pytz
from discord.ext import tasks, commands

from cogs.mongo.database import get_collections

# Collections
guilds = get_collections("guilds")

# Global Variables
e_m = "<:medal:573071121545560064>"
e_j = "<:jade:555630314282811412>"
e_c = "<:coin:573071121495097344>"
e_f = "<:friendship:555630314056318979>"
e_a = "<:amulet:603989470328651787>"
e_sp = "<:SP:602707718603538442>"
e_ssr = "<:SSR:602707410515132456>"
e_sr = "<:SR:602707410922242048>"
e_r = "<:R_:602707410582241280>"
e_n = "<:N_:602707410540560414>"
e_t = "<:talisman:573071120685596682>"

embed_color = 0xffa8e1
guild_id = int(os.environ.get("PATRONUS"))
hosting_id = int(guilds.find_one({
    "server": str(guild_id)}, {
    "_id": 0, "channels.bot-sparring": 1
})["channels"]["bot-sparring"])

# Listings
status = cycle([
    "with the peasants via ;info",
    "with their feelings via ;info",
    "fake Onmyoji via ;info",
    "with Susabi via ;info",
    "in Patronusverse via ;info"
])


def pluralize(singular, count):
    if count > 1:
        if singular[-1:] == "s":
            return singular + "es"
        return singular + "s"
    else:
        return singular


class Startup(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        owner_id = await self.client.application_info()

        print("Initializing...")
        print("-------")
        print("Logged in as {0.user}".format(self.client))
        print("Hi! {}!".format(self.client.get_user(owner_id.owner.id)))
        print("Time now: {}".format(datetime.now(tz=pytz.timezone("America/Atikokan")).strftime("%d.%b %Y %H:%M:%S")))
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
            color=embed_color,
            description="To see my commands, type *`;help`* or *`;help dm`*"
        )
        embed.set_author(name=f"Hello there! I'm {self.client.user.display_name}! ~")
        await ctx.channel.send(embed=embed)

    @commands.command(aliases=["h", "help"])
    async def show_help_message(self, ctx, *args):
        embed = discord.Embed(
            title="help",
            color=embed_color,
            description="append the prefix semi-colon *`;`*"
        )
        embed.set_thumbnail(url=self.client.user.avatar_url)
        embed.set_footer(text="*Head commands")
        embed.add_field(
            name="Economy",
            value="*daily, weekly, profile, display, buy, summon, "
                  "evolve, friendship, leaderboard, shikigamis, shrine, sail, pray, stat, "
                  "frames, wish, wishlist, fulfill, parade, uncollected, collections*",
            inline=False
        )
        embed.add_field(
            name="Gameplay",
            value="*raid, raidc, encounter, bossinfo*"
        )
        embed.add_field(
            name="Others",
            value="*bounty, suggest, stickers, newsticker, wander, portrait, "
                  "statistics, announce*\\*, *manage*\\*",
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

    @commands.command(aliases=["suggest", "report"])
    async def collect_suggestion(self, ctx, *, suggestion):
        request = guilds.find_one({"server": str(guild_id)}, {"_id": 0, "channels.headmasters-office": 1})

        headmaster_office_id = request["channels"]["headmasters-office"]
        headmaster_office_channel = self.client.get_channel(int(headmaster_office_id))

        link = f"https://discordapp.com/channels/{ctx.message.guild.id}/{ctx.message.channel.id}/{ctx.message.id}"
        embed = discord.Embed(color=embed_color, title="New Report/Suggestion")
        embed.description = f"{ctx.author.mention} suggested: {suggestion} at <#{ctx.channel.id}>\n" \
                            f"Message link: [here]({link})"
        await headmaster_office_channel.send(embed=embed)
        await ctx.message.add_reaction("📩")


def setup(client):
    client.add_cog(Startup(client))
