"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import json
import os
import random

import discord
from discord.ext import commands

from cogs.error import logging, get_f
from cogs.mongo.db import users

file = os.path.basename(__file__)[:-3:]

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


    @commands.command(aliases=["sticker"])
    @commands.guild_only()
    async def stickers(self, ctx):

        embed = discord.Embed(color=0xffff80, title="Available stickers!", description=description)
        embed.set_footer(text="just add 'mike' plus the sticker name in your message!")
        await ctx.channel.send(embed=embed)


    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author == self.client.user:
            return

        elif message.author.bot:
            return

        elif len(message.content.split(" ")) > 2:
            return

        elif "mike" in message.content.lower():
            user = message.author
            list_emotes = message.content.lower().split()
            action_recognized = None

            for action_try in list_emotes:
                if action_try in actions:
                    action_recognized = action_try
                    break

            if action_recognized is None:
                return

            else:
                users.update_one({"user_id": str(user.id)}, {"$inc": {"experience": 20}})
                selection = [v for v in emotes[action_recognized].values()]
                thumbnail = random.choice(selection)
                embed = discord.Embed(color=message.author.colour)
                embed.set_footer(
                    text=f"{message.author.display_name}, +20exp",
                    icon_url=message.author.avatar_url
                )
                embed.set_image(url=thumbnail)
                try:
                    await message.channel.send(embed=embed)
                except discord.errors.Forbidden:
                    logging(file, get_f, "discord.errors.Forbidden")
                    return
                except discord.errors.HTTPException:
                    logging(file, get_f, "discord.errors.Forbidden")
                    return
                try:
                    await message.delete()
                except discord.errors.Forbidden:
                    logging(file, get_f, "discord.errors.Forbidden")
                except discord.errors.HTTPException:
                    logging(file, get_f, "discord.errors.Forbidden")


        elif "@{}".format(self.client.user.id) in message.content:
            try:
                await message.delete()
            except discord.errors.Forbidden:
                logging(file, get_f, "discord.errors.Forbidden")
            except discord.errors.HTTPException:
                logging(file, get_f, "discord.errors.Forbidden")

            msg = "<:0_0:596721853448454203><:1_0:596721853305978882>" \
                  "<:2_0:596721853528014880><:3_0:596721853259841564><:4_0:596721853779804219>\n" \
                  "<:0_1:596721853775740948><:1_1:596721853205315596>" \
                  "<:2_1:596721853465231362><:3_1:596721853716889641><:4_1:596721853691592705>\n" \
                  "<:0_2:596721853569957918><:1_2:596721853624483840>" \
                  "<:2_2:596721853561569280><:3_2:596721853620420627><:4_2:596721853612163152>"

            try:
                await message.channel.send(msg)
            except discord.errors.Forbidden:
                logging(file, get_f, "discord.errors.Forbidden")
            except discord.errors.HTTPException:
                logging(file, get_f, "discord.errors.Forbidden")


def setup(client):
    client.add_cog(Emotes(client))
