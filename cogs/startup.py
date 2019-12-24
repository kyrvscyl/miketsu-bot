"""
Startup Module
Miketsu, 2019
"""
import asyncio
import os
from datetime import datetime
from itertools import cycle
from math import ceil

import discord
import pytz
from discord.ext import tasks, commands

from cogs.mongo.database import get_collections

# Collections
changelogs = get_collections("changelogs")
config = get_collections("config")
guilds = get_collections("guilds")

# Lists
status = cycle(config.find_one({"list": 1}, {"_id": 0, "statuses": 1})["statuses"])
admin_roles = config.find_one({"list": 1}, {"_id": 0, "admin_roles": 1})["admin_roles"]

# Variables
id_guild = int(os.environ.get("SERVER"))
colour = config.find_one({"var": 1}, {"_id": 0, "embed_color": 1})["embed_color"]

id_headlines = guilds.find_one({"server": str(id_guild)}, {"_id": 0, "channels": 1})["channels"]["headlines"]
timezone = config.find_one({"var": 1}, {"_id": 0, "timezone": 1})["timezone"]


def check_if_has_any_admin_roles(ctx):
    for role in reversed(ctx.author.roles):
        if role.name in admin_roles:
            return True
    return False


class Startup(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.prefix = self.client.command_prefix

    def get_timestamp(self):
        return datetime.utcfromtimestamp(datetime.timestamp(datetime.now()))
    
    @commands.Cog.listener()
    async def on_ready(self):
        owner_id = await self.client.application_info()
        time_now = datetime.now(tz=pytz.timezone(timezone))

        print("Initializing...")
        print("-------")
        print("Logged in as {}".format(self.client.user))
        print("Hi! {}!".format(self.client.get_user(owner_id.owner.id)))
        print("Time now: {}".format(time_now.strftime("%d.%b %Y %H:%M:%S")))
        print("-------")
        try:
            self.change_status.start()
        except RuntimeError:
            pass
        print("-------")

    @tasks.loop(seconds=1200)
    async def change_status(self):
        try:
            await self.client.change_presence(activity=discord.Game(next(status)))
        except RuntimeError:
            pass

    @commands.command(aliases=["info", "i"])
    async def show_greeting_message(self, ctx):

        embed = discord.Embed(
            color=colour,
            description=f"To see my commands, type *`{self.prefix}help`*"
        )
        embed.set_author(name=f"Hello there! I'm {self.client.user.display_name}! ~")
        await ctx.channel.send(embed=embed)

    @commands.command(aliases=["h", "help"])
    async def show_help_message(self, ctx):
        embed = discord.Embed(
            title="help, h",
            color=colour,
            description=f"append the prefix symbol *`{self.prefix}`*"
        )
        embed.set_thumbnail(url=self.client.user.avatar_url)
        embed.set_footer(text="*Head commands, **#pvp-fair exclusive")
        embed.add_field(
            name="fake Onmyoji",
            value="*"
                  "daily, weekly, profile, set, buy, summon, explore, explores, chapter, realm, realms, rcollect, "
                  "evolve, friendship, ships, leaderboard, shikigami, shikigamis, shrine, sail, pray, stat, "
                  "frames, wish, wishlist, fulfill, parade, collections, shards, "
                  "raid, raidc, encounter, netherworld, bossinfo"
                  "*",
            inline=False
        )
        embed.add_field(
            name="Others",
            value="*"
                  "changelog, bounty, suggest, stickers, newsticker, wander, portrait, "
                  "stats, duel\\*\\*, memo\\*, manage\\*, events\\*"
                  "*",
            inline=False
        )
        await ctx.channel.send(embed=embed)

    @commands.command(aliases=["suggest", "report"])
    async def collect_suggestions(self, ctx, *, content):
        request = guilds.find_one({"server": str(id_guild)}, {"_id": 0, "channels.scroll-of-everything": 1})
        record_scroll_id = request["channels"]["scroll-of-everything"]
        record_scroll = self.client.get_channel(int(record_scroll_id))

        embed = discord.Embed(color=colour, title="📨 New Suggestion/Report", timestamp=self.get_timestamp())
        try:
            link = f"https://discordapp.com/channels/{ctx.message.guild.id}/{ctx.message.channel.id}/{ctx.message.id}"
            embed.description = f"Author: {ctx.author.mention}\n" \
                                f"Submitted through: {ctx.channel.mention}\n" \
                                f"Message Link: [Here]({link})"
        except AttributeError:
            embed.description = f"From: {ctx.author.mention}\n" \
                                f"Submitted through: Direct Message"

        embed.add_field(name="Content", value=f"{content}", inline=False)
        suggestion = await record_scroll.send(embed=embed)
        await suggestion.add_reaction("📌")
        await ctx.message.add_reaction("📩")

    @commands.command(aliases=["changelog", "changelogs"])
    @commands.guild_only()
    async def show_changelogs(self, ctx):

        changelog_lines = changelogs.find_one({"logs": 1}, {"_id": 0, "details": 1})["details"][:200]
        changelog_lines_formatted = []

        for line in reversed(changelog_lines):
            changelog_lines_formatted.append(f"• {line}\n")

        embed = discord.Embed(color=colour, title="Changelog", timestamp=self.get_timestamp())
        embed.description = " ".join(changelog_lines_formatted)

        await self.show_changelogs_paginate(ctx, changelog_lines_formatted)

    async def show_changelogs_paginate(self, ctx, formatted_list):

        page = 1
        max_lines = 20
        page_total = ceil(len(formatted_list) / max_lines)
        if page_total == 0:
            page_total = 1

        def create_new_embed_page(page_new):
            end = page * max_lines
            start = end - max_lines
            description = "".join(formatted_list[start:end])

            embed_new = discord.Embed(
                color=ctx.author.colour,
                title="Bot changelogs",
                description=description
            )
            embed_new.set_footer(text=f"Page: {page_new} of {page_total}")
            return embed_new

        msg = await ctx.channel.send(embed=create_new_embed_page(page))
        await msg.add_reaction("⬅")
        await msg.add_reaction("➡")

        def check(r, u):
            return u != self.client.user and r.message.id == msg.id

        while True:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=60, check=check)
            except asyncio.TimeoutError:
                await msg.clear_reactions()
                break
            else:
                if str(reaction.emoji) == "➡":
                    page += 1
                elif str(reaction.emoji) == "⬅":
                    page -= 1
                if page == 0:
                    page = page_total
                elif page > page_total:
                    page = 1
                await msg.edit(embed=create_new_embed_page(page))


def setup(client):
    client.add_cog(Startup(client))
