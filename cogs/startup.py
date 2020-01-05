"""
Startup Module
Miketsu, 2020
"""
import asyncio
import os
from datetime import datetime
from itertools import cycle
from math import ceil

import pytz
from discord.ext import tasks, commands
from pushbullet import Pushbullet

from cogs.ext.database import get_collections
from cogs.ext.processes import *

# Pushbullet
pb = Pushbullet(api_key=str(os.environ.get("PUSHBULLET")))

# Collections
changelogs = get_collections("changelogs")
config = get_collections("config")
guilds = get_collections("guilds")

# Instantiations
id_guild = int(os.environ.get("SERVER"))


class Startup(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.prefix = self.client.command_prefix

        self.colour = config.find_one({"var": 1}, {"_id": 0, "embed_color": 1})["embed_color"]
        self.timezone = config.find_one({"var": 1}, {"_id": 0, "timezone": 1})["timezone"]

        self.statuses = cycle(config.find_one({"list": 1}, {"_id": 0, "statuses": 1})["statuses"])
        
        self.commands_fake = [
            "daily", "weekly", "profile", "set", "buy", "summon", "explore", "explores", "chapter", "card", "realms",
            "rcollect", "evolve", "friendship", "ships", "leaderboard", "shikigami", "shikigamis", "shrine", "sail",
            "pray", "stat", "frames", "wish", "wishlist", "fulfill", "parade", "collections", "shards", "cards",
            "raid", "raidc", "encounter", "netherworld", "bossinfo", "ship", "fpchange", "bento", "raidable",
            "souls [beta]"
        ]

        self.commands_others = [
            "changelogs", "bounty", "suggest", "stickers", "newsticker", "wander", "portrait",
            "stats", "duel\\*\\*", "memo\\*", "manage\\*", "events\\*", "info", "report"
        ]

    def get_timestamp(self):
        return datetime.utcfromtimestamp(datetime.timestamp(datetime.now()))
    
    @commands.Cog.listener()
    async def on_ready(self):

        bot_info = await self.client.application_info()
        time_now = datetime.now(tz=pytz.timezone(self.timezone))

        print("Initializing...")
        print("-------")
        print("Logged in as {}".format(self.client.user))
        print("Hi! {}!".format(self.client.get_user(bot_info.owner.id)))
        print("Time now: {}".format(time_now.strftime("%d.%b %Y %H:%M:%S")))
        print("-------")
        try:
            self.change_status.start()
        except RuntimeError:
            pb.push_note("Miketsu Bot", "Experience a hiccup while changing my status ~1")
        print("-------")

    @tasks.loop(seconds=1200)
    async def change_status(self):

        try:
            await self.client.change_presence(activity=discord.Game(next(self.statuses)))
        except RuntimeError:
            pb.push_note("Miketsu Bot", "Experience a hiccup on changing my status ~2")

    @commands.command(aliases=["info", "i"])
    async def show_message_greetings(self, ctx):

        embed = discord.Embed(
            color=self.colour,
            description=f"To see my commands, type *`{self.prefix}help`*"
        )
        embed.set_author(
            name=f"Hello there! I'm {self.client.user.display_name}! ~",
            icon_url=self.client.user.avatar_url
        )
        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["h", "help"])
    async def show_message_help(self, ctx):

        embed = discord.Embed(
            title="help, h",
            color=self.colour,
            description=f"append my command prefix symbol *`{self.prefix}`*"
        )
        embed.add_field(
            name="fake Onmyoji",
            value=f"*{', '.join(sorted(self.commands_fake))}*",
            inline=False
        )
        embed.add_field(
            name="Others / Utility",
            value=f"*{', '.join(sorted(self.commands_others))}*",
            inline=False
        )
        embed.set_thumbnail(url=self.client.user.avatar_url)
        embed.set_footer(text="*Head commands, **#pvp-fair exclusive")
        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["suggest", "report"])
    async def collect_suggestions(self, ctx, *, content):

        query = guilds.find_one({"server": str(id_guild)}, {"_id": 0, "channels": 1})
        id_scroll = query["channels"]["scroll-of-everything"]
        scroll_channel = self.client.get_channel(int(id_scroll))

        embed = discord.Embed(
            color=self.colour,
            title="📨 New Suggestion/Report",
            timestamp=self.get_timestamp()
        )
        embed.add_field(name="Content", value=f"{content}", inline=False)

        try:
            link = f"https://discordapp.com/channels/{ctx.message.guild.id}/{ctx.message.channel.id}/{ctx.message.id}"
            embed.description = f"Author: {ctx.author.mention}\n" \
                                f"Submitted through: {ctx.channel.mention}\n" \
                                f"Message Link: [Here]({link})"
        except AttributeError:
            embed.description = f"From: {ctx.author.mention}\n" \
                                f"Submitted through: Direct Message"

        msg = await process_msg_submit(scroll_channel, None, embed)
        await process_msg_reaction_add(msg, "📌")
        await process_msg_reaction_add(ctx.message, "📩")

    @commands.command(aliases=["changelog", "changelogs"])
    @commands.guild_only()
    async def show_changelogs(self, ctx):

        changelog_lines = changelogs.find_one({"logs": 1}, {"_id": 0, "details": 1})["details"][:200]
        changelog_lines_formatted = []

        for line in reversed(changelog_lines):
            changelog_lines_formatted.append(f"• {line}\n")

        await self.show_changelogs_paginate(ctx, changelog_lines_formatted)

    async def show_changelogs_paginate(self, ctx, formatted_list):

        page, max_lines = 1, 20
        page_total = ceil(len(formatted_list) / max_lines)

        if page_total == 0:
            page_total = 1

        def embed_new_create(page_new):
            end = page * max_lines
            start = end - max_lines
            description = "".join(formatted_list[start:end])

            embed_new = discord.Embed(color=self.colour, title="Bot changelogs", description=description)
            embed_new.set_footer(text=f"Page: {page_new} of {page_total}")
            return embed_new

        msg = await process_msg_submit(ctx.channel, None, embed_new_create(page))
        await process_msg_reaction_add(msg, "⬅")
        await process_msg_reaction_add(msg, "➡")

        def check(r, u):
            return u != self.client.user and r.message.id == msg.id

        while True:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=60, check=check)
            except asyncio.TimeoutError:
                await process_msg_reaction_clear(msg)
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

                await process_msg_edit(msg, None, embed_new_create(page))
                await process_msg_reaction_remove(msg, str(reaction.emoji), user)

    @commands.command(aliases=["changelog_add"])
    @commands.is_owner()
    async def add_changelogs(self, ctx, *, args):

        comment = args
        changelogs.update_one({
            "logs": 1,
        }, {
            "$push": {
                "details": comment
            }
        })
        await process_msg_reaction_add(ctx.message, "✅")


def setup(client):
    client.add_cog(Startup(client))
