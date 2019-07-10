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


# noinspection PyShadowingBuiltins
class Emotes(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(aliases=["sticker"])
    async def stickers(self, ctx):
        embed = discord.Embed(color=0xffff80, title="Available stickers!", description=description)
        embed.set_footer(text="just add 'mike' plus the sticker name in your message!")
        await ctx.channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):

        # Ignore myself
        if message.author == self.client.user:
            return

        # Ignore other bots
        elif message.author.bot:
            return

        elif "mike" in message.content.lower():
            user = message.author
            list = message.content.lower().split()
            action_recognized = None

            # find the action
            for action_try in list:
                if action_try in actions:
                    action_recognized = action_try
                    break

            if action_recognized is None:
                return

            else:
                users.update_one({"user_id": str(user.id)}, {"$inc": {"experience": 15}})
                color = message.author.colour
                selection = [v for v in emotes[action_recognized].values()]
                thumbnail = random.choice(selection)
                embed = discord.Embed(color=color)
                embed.set_footer(
                    text=f"{message.author.display_name}, +20exp",
                    icon_url=message.author.avatar_url
                )
                embed.set_image(url=thumbnail)
                await message.channel.send(embed=embed)
                await message.delete()

        elif "@{}".format(self.client.user.id) in message.content:
            await message.delete()
            msg = "<:0_0:596721853448454203><:1_0:596721853305978882>" \
                  "<:2_0:596721853528014880><:3_0:596721853259841564><:4_0:596721853779804219>\n" \
                  "<:0_1:596721853775740948><:1_1:596721853205315596>" \
                  "<:2_1:596721853465231362><:3_1:596721853716889641><:4_1:596721853691592705>\n" \
                  "<:0_2:596721853569957918><:1_2:596721853624483840>" \
                  "<:2_2:596721853561569280><:3_2:596721853620420627><:4_2:596721853612163152>"
            await message.channel.send(msg)


def setup(client):
    client.add_cog(Emotes(client))
