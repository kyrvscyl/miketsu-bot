"""
Stickers Module
Miketsu, 2019
"""

import asyncio

import discord
from discord.ext import commands

from cogs.mongo.database import get_collections

# Collections
books = get_collections("bukkuman", "books")
stickers = get_collections("bukkuman", "stickers")
users = get_collections("miketsu", "users")


# Listings
stickers_list = []
actions = []


def generate_new_stickers():
    global stickers_list
    global actions

    for sticker in stickers.find({}, {"_id": 0}):
        stickers_list.append("`{}`, ".format(sticker["alias"]))
        actions.append(sticker["alias"])


generate_new_stickers()


class Emotes(commands.Cog):

    def __init__(self, client):
        self.client = client

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
            embed = discord.Embed(color=ctx.author.colour, title=f"Alias `{alias}` is already taken",)
            await ctx.channel.send(embed=embed)

        elif link[:20] == "https://i.imgur.com/" and link[-4:] == ".png":
            stickers.insert_one({"alias": alias, "link": link})
            embed = discord.Embed(color=ctx.author.colour,title=f"New sticker added with alias: `{alias}`")
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

        elif len(message.content.split(" ")) > 2:
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
                return

            else:
                users.update_one({"user_id": str(user.id), "experience": {"$lt": 100000}}, {"$inc": {"experience": 20}})
                sticker_url = stickers.find_one({"alias": sticker_recognized}, {"_id": 0, "link": 1})["link"]
                embed = discord.Embed(color=user.colour)
                embed.set_footer(text=f"{user.display_name}, +20exp", icon_url=user.avatar_url)
                embed.set_image(url=sticker_url)
                await message.channel.send(embed=embed)
                await message.delete()


def setup(client):
    client.add_cog(Emotes(client))
