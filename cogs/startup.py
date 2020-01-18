"""
Startup Module
Miketsu, 2020
"""

import asyncio
from itertools import cycle

from discord.ext import commands, tasks

from cogs.ext.initialize import *


class Startup(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.prefix = self.client.command_prefix

        self.statuses = cycle(listings_1["statuses"])
    
    @commands.Cog.listener()
    async def on_ready(self):

        bot_info = await self.client.application_info()
        time_now = datetime.now(tz=pytz.timezone(timezone))

        print("Initializing...")
        print("-------")
        print(f"Logged in as {self.client.user}")
        print(f"Hi! {self.client.get_user(bot_info.owner.id)}!")
        print(f"Time now: {time_now.strftime('%d.%b %Y %H:%M:%S')}")
        print("-------")
        try:
            self.status_change.start()
        except RuntimeError:
            push_note("Exception occurred", "Experienced a hiccup while changing my status ~1")
        print("-------")

    @tasks.loop(seconds=1200)
    async def status_change(self):

        try:
            await self.client.change_presence(activity=discord.Game(next(self.statuses)))
        except RuntimeError:
            push_note("Exception occurred", "Experienced a hiccup while changing my status ~2")

    @commands.command(aliases=["info", "i"])
    async def help_info(self, ctx):

        embed = discord.Embed(
            color=colour,
            description=f"To see my commands, type *`{self.prefix}help`*"
        )
        embed.set_author(
            name=f"Hello there! I'm {self.client.user.display_name}! ~",
            icon_url=self.client.user.avatar_url
        )
        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["h", "help"])
    async def help_show(self, ctx):

        embed = discord.Embed(
            title="help, h", color=colour,
            description=f"append my command prefix symbol *`{self.prefix}`*"
        )
        embed.add_field(
            name="fake Onmyoji", inline=False,
            value=f"*{', '.join(sorted(commands_fake))}*",
        )
        embed.add_field(
            name="Others / Utility", inline=False,
            value=f"*{', '.join(sorted(commands_others))}*",
        )
        embed.set_thumbnail(url=self.client.user.avatar_url)
        embed.set_footer(text="*Head commands, **#pvp-fair")
        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["suggest", "report"])
    async def suggestions_collect(self, ctx, *, content):

        embed = discord.Embed(
            color=colour, timestamp=get_timestamp(),
            title="📨 New Suggestion/Report",
        )
        embed.add_field(
            name="Content", inline=False, value=f"{content}",
        )

        try:
            link = f"https://discordapp.com/channels/{ctx.message.guild.id}/{ctx.message.channel.id}/{ctx.message.id}"
            embed.description = f"Author: {ctx.author.mention}\n" \
                                f"Submitted through: {ctx.channel.mention}\n" \
                                f"Message Link: [Here]({link})"
        except AttributeError:
            embed.description = f"From: {ctx.author.mention}\n" \
                                f"Submitted through: Direct Message"

        scroll_channel = self.client.get_channel(int(id_scroll))
        msg = await process_msg_submit(scroll_channel, None, embed)
        await process_msg_reaction_add(msg, "📌")
        await process_msg_reaction_add(ctx.message, "📩")

    @commands.command(aliases=["changelogs", "changelog"])
    @commands.guild_only()
    async def changelog_show(self, ctx):

        changelog_lines = changelogs.find_one({"logs": 1}, {"_id": 0, "details": 1})["details"][:200]
        changelog_lines_formatted = []

        for line in reversed(changelog_lines):
            changelog_lines_formatted.append(f"• {line}\n")

        await self.changelog_show_paginate(ctx, changelog_lines_formatted)

    async def changelog_show_paginate(self, ctx, listings_formatted):

        page, max_lines = 1, 20
        page_total = ceil(len(listings_formatted) / max_lines)

        if page_total == 0:
            page_total = 1

        def embed_new_create(page_new):
            end = page * max_lines
            start = end - max_lines
            description = "".join(listings_formatted[start:end])

            embed_new = discord.Embed(color=colour, description=description)
            embed_new.set_author(name="Bot Changelogs", icon_url=self.client.user.avatar_url)
            embed_new.set_footer(text=f"Last 200 only; Page: {page_new} of {page_total}")
            return embed_new

        msg = await process_msg_submit(ctx.channel, None, embed_new_create(page))

        emojis_add = ["⬅", "➡"]
        for emoji in emojis_add:
            await process_msg_reaction_add(msg, emoji)

        def check(r, u):
            return u != self.client.user and r.message.id == msg.id and str(r.emoji) in emojis_add

        while True:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=60, check=check)
            except asyncio.TimeoutError:
                await process_msg_reaction_clear(msg)
                break
            else:
                if str(reaction.emoji) == emojis_add[1]:
                    page += 1
                elif str(reaction.emoji) == emojis_add[0]:
                    page -= 1
                if page == 0:
                    page = page_total
                elif page > page_total:
                    page = 1

                await process_msg_edit(msg, None, embed_new_create(page))
                await process_msg_reaction_remove(msg, str(reaction.emoji), user)

    @commands.command(aliases=["changelog_add"])
    @commands.is_owner()
    async def changelog_add_line(self, ctx, *, args=None):

        if args is not None:
            x = changelogs.update_one({"logs": 1}, {"$push": {"details": args}})

            if x.modified_count != 0:
                await process_msg_reaction_add(ctx.message, "✅")


def setup(client):
    client.add_cog(Startup(client))
