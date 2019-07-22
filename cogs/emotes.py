"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import json
import random

import discord
from discord.ext import commands

from cogs.mongo.db import users

with open("data/emotes.json") as f:
    stickers = json.load(f)

actions = list(stickers.keys())
emotes = stickers

list_stickers = []
for sticker in actions:
    list_stickers.append("`{}`, ".format(sticker))

description = "".join(list_stickers)[:-2:]


class Emotes(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(aliases=["sticker", "stickers"])
    @commands.guild_only()
    async def sticker_help(self, ctx):
        embed = discord.Embed(
            color=0xffe6a7, title="stickers",
            description="posts a reaction image embed\n"
                        "just add \"mike\" in your message + the `<alias>`"
        )
        embed.add_field(name="Aliases", value="*" + description + "*")
        await ctx.channel.send(embed=embed)

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
                users.update_one({"user_id": str(user.id)}, {"$inc": {"experience": 20}})
                selection = [v for v in emotes[sticker_recognized].values()]
                sticker_url = random.choice(selection)
                embed = discord.Embed(color=user.colour)
                embed.set_footer(text=f"{user.display_name}, +20exp", icon_url=user.avatar_url)
                embed.set_image(url=sticker_url)
                await message.channel.send(embed=embed)
                await message.delete()


def setup(client):
    client.add_cog(Emotes(client))
