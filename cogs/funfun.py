"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import random
import re

import discord
from discord.ext import commands


class Funfun(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message):

        if "mike" in message.content.lower():

            if "how hot" in message.content.lower():
                msg_formatted = message.content.lower().split(" ")

                for word in msg_formatted:
                    if re.match(r"^<@![0-9]+>$", word) or re.match(r"^<@[0-9]+>$", word):

                        user_id = re.sub("[<>@!]", "", word)
                        random.seed(int(user_id))
                        member = message.guild.get_member(int(user_id))
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
                            color=message.author.colour,
                            title=f"**{member.display_name}** is **{hot:.2f}%** hot {emoji}"
                        )
                        await message.channel.send(embed=embed)
                        break


def setup(client):
    client.add_cog(Funfun(client))
