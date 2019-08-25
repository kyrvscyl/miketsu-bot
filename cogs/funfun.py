"""
Funfun Module
Miketsu, 2019
"""
import asyncio
import random
import re
from itertools import cycle

import discord
from discord.ext import commands

from cogs.mongo.database import get_collections

# Collections
books = get_collections("bukkuman", "books")
stickers = get_collections("bukkuman", "stickers")
users = get_collections("miketsu", "users")

# Listings
actions = []
stickers_list = []


reaction_list_ = open("lists/reactions.lists")
reaction_list = reaction_list_.read().splitlines()
reaction_list_cycle = cycle(reaction_list)
reaction_list_.close()

success_lists_ = open("lists/success.lists")
success_lists = success_lists_.read().splitlines()
success_lists_cycle = cycle(success_lists)
success_lists_.close()

failed_lists_ = open("lists/failed.lists")
failed_lists = failed_lists_.read().splitlines()
failed_lists_cycle = cycle(failed_lists)
failed_lists_.close()


def generate_new_stickers():
    global stickers_list
    global actions

    for sticker in stickers.find({}, {"_id": 0}):
        stickers_list.append("`{}`, ".format(sticker["alias"]))
        actions.append(sticker["alias"])


generate_new_stickers()


async def mike_how_hot(guild, channel, msg):
    msg_formatted = msg.lower().split(" ")

    for word in msg_formatted:

        if re.match(r"^<@![0-9]+>$", word) or re.match(r"^<@[0-9]+>$", word):

            user_id = re.sub("[<>@!]", "", word)
            random.seed(int(user_id))
            member = guild.get_member(int(user_id))
            r = random.randint(1, 100)
            hot = r / 1.17

            emoji = "💔"
            if hot > 25:
                emoji = "❤"
            if hot > 50:
                emoji = "💖"
            if hot > 75:
                emoji = "💞"

            embed = discord.Embed(
                color=member.colour,
                title=f"**{member.display_name}** is **{hot:.2f}%** hot {emoji}"
            )
            await channel.send(embed=embed)
            break


class Funfun(commands.Cog):

    def __init__(self, client):
        self.client = client

    async def mike_shoot(self, user, guild, channel, args):
        msg_formatted = args.lower().split(" ")

        for word in msg_formatted:

            if re.match(r"^<@![0-9]+>$", word) or re.match(r"^<@[0-9]+>$", word):

                user_id = re.sub("[<>@!]", "", word)
                member = guild.get_member(int(user_id))

                if member.id != self.client.user.id:
                    roll = random.randint(1, 100)
                    response = next(success_lists_cycle).format(member.mention)
                    if roll >= 45:
                        response = next(failed_lists_cycle).format(user.mention)

                    embed = discord.Embed(color=member.colour, description=f"*{response}*")
                    await channel.send(embed=embed)
                    break

    @commands.command(aliases=["sticker", "stickers"])
    @commands.guild_only()
    async def sticker_help(self, ctx):

        quotient = int(len(stickers_list) / 2)
        page = 1
        page_total = 2

        def check(r, u):
            return u != self.client.user and r.message.id == msg.id

        def generate_stickers_embed(y):

            end = y * quotient
            start = end - quotient
            description = "".join(sorted(stickers_list[start:end]))[:-2:]

            embed = discord.Embed(
                color=0xffe6a7, title="stickers",
                description="posts a reaction image embed\n"
                            "just add \"mike\" in your message + the `<alias>`"
            )
            embed.add_field(name="Aliases", value="*" + description + "*")
            embed.set_footer(text=f"Page {y}")
            return embed

        msg = await ctx.channel.send(embed=generate_stickers_embed(page))
        await msg.add_reaction("⬅")
        await msg.add_reaction("➡")

        while True:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=30, check=check)
            except asyncio.TimeoutError:
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
                await msg.edit(embed=generate_stickers_embed(page))

    @commands.command(aliases=["newsticker", "ns"])
    @commands.guild_only()
    async def sticker_add_new(self, ctx, arg1, *, args):

        alias = arg1.lower()
        link = args

        if alias in actions:
            embed = discord.Embed(color=ctx.author.colour, title=f"Alias `{alias}` is already taken", )
            await ctx.channel.send(embed=embed)

        elif link[:20] == "https://i.imgur.com/" and link[-4:] == ".png":
            stickers.insert_one({"alias": alias, "link": link})
            embed = discord.Embed(color=ctx.author.colour, title=f"New sticker added with alias: `{alias}`")
            embed.set_image(url=link)
            await ctx.channel.send(embed=embed)
            generate_new_stickers()

        else:
            await ctx.message.add_reaction("❌")

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author == self.client.user:
            return

        elif message.author.bot:
            return

        elif isinstance(message.channel, discord.DMChannel):
            return

        elif "mike" in message.content.lower().split(" "):
            user = message.author
            list_message = message.content.lower().split()
            sticker_recognized = None

            for sticker_try in list_message:
                if sticker_try in actions:
                    sticker_recognized = sticker_try
                    break

            if sticker_recognized is None:

                try:
                    if len(message.content) == 4:
                        embed = discord.Embed(
                            colour=discord.Colour(0xffe6a7),
                            description=next(reaction_list_cycle)
                        )
                        msg = await message.channel.send(embed=embed)
                        await msg.delete(delay=15)
                        await message.delete(delay=15)

                    elif message.content.lower().split(" ", 2)[1] == "shoot":
                        await self.mike_shoot(message.author, message.guild, message.channel, message.content)

                    elif message.content.lower().split(" ", 1)[1][:7] == "how hot":
                        await mike_how_hot(message.guild, message.channel, message.content)

                except IndexError:
                    return

            else:
                x = users.update_one({"user_id": str(user.id), "level": {"$lt": 60}}, {"$inc": {"experience": 20}})
                sticker_url = stickers.find_one({"alias": sticker_recognized}, {"_id": 0, "link": 1})["link"]

                comment = " "
                if x.modified_count > 0:
                    comment = ", +20exp"

                embed = discord.Embed(color=user.colour)
                embed.set_footer(text=f"{user.display_name}{comment}", icon_url=user.avatar_url)
                embed.set_image(url=sticker_url)
                await message.channel.send(embed=embed)
                await message.delete()


def setup(client):
    client.add_cog(Funfun(client))
