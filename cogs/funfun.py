"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import random
import re

import discord
from discord.ext import commands

reaction_list_ = open("lists/reactions.lists")
reaction_list = reaction_list_.read().splitlines()
reaction_list_.close()

success_lists_ = open("lists/success.lists")
success_lists = success_lists_.read().splitlines()
success_lists_.close()

failed_lists_ = open("lists/failed.lists")
failed_lists = failed_lists_.read().splitlines()
failed_lists_.close()


async def mike_shoot(user, guild, channel, args):

    msg_formatted = args.lower().split(" ")

    for word in msg_formatted:

        if re.match(r"^<@![0-9]+>$", word) or re.match(r"^<@[0-9]+>$", word):

            user_id = re.sub("[<>@!]", "", word)
            member = guild.get_member(int(user_id))

            roll = random.randint(1, 100)
            response = random.choice(success_lists).format(member.mention)
            if roll >= 45:
                response = random.choice(failed_lists).format(user.mention)

            embed = discord.Embed(
                color=member.colour,
                description="\"*"+response+"*\""
            )
            await channel.send(embed=embed)
            break


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
                title=f"**{member.display_name}** is **{hot:.2f}%** hot {emoji} today"
            )
            await channel.send(embed=embed)
            break


class Funfun(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message):

        if self.client.user == message.author:
            return

        elif message.author.bot:
            return

        elif message.content.lower()[:4] == "mike":

            if len(message.content) == 4:
                embed = discord.Embed(
                    colour=discord.Colour(0xffe6a7),
                    description="\"*"+random.choice(reaction_list)+"*\""
                )
                msg = await message.channel.send(embed=embed)
                await msg.delete(delay=15)
                await message.delete(delay=15)

            elif message.content.lower().split(" ", 2)[1] == "shoot":
                await mike_shoot(message.author, message.guild, message.channel, message.content)

            elif message.content.lower().split(" ", 1)[1][:7] == "how hot":
                await mike_how_hot(message.guild, message.channel, message.content)


def setup(client):
    client.add_cog(Funfun(client))
