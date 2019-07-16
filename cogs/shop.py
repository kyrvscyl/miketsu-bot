"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import asyncio

import discord
from discord.ext import commands

from cogs.mongo.db import users
from cogs.startup import emoji_a, emoji_j


async def buy_amulet(user, ctx):

    if users.find_one({"user_id": str(user.id)}, {"_id": 0, "jades": 1})["jades"] >= 1000:
        users.update_one({"user_id": str(user.id)}, {"$inc": {"amulets": 11, "jades": -1000}})
        amulet = users.find_one({"user_id": str(user.id)}, {"_id": 0, "amulets": 1})["amulets"]
        await ctx.channel.send(f"{user.mention}, You have bought 11{emoji_a}. You now have {amulet}{emoji_a}")

    else:
        await ctx.channel.send(f"{user.mention}, You have insufficient {emoji_j}")


class Economy(commands.Cog):

    def __init__(self, client):
        self.client = client


    @commands.command()
    @commands.guild_only()
    async def buy(self, ctx, *args):
        user = ctx.author
        try:
            if args[0] == "amulet":
                await ctx.message.add_reaction(f"{emoji_a.replace('<', '').replace('>', '')}")

                def check(r, u):
                    return u == ctx.author and str(r.emoji) == emoji_a

                try:
                    reaction, user = await self.client.wait_for("reaction_add", timeout=10.0, check=check)
                except asyncio.TimeoutError:
                    msg = f"{user.mention}, timeout! You did not click {emoji_a} on time. Please try again."
                    await ctx.channel.send(msg)
                else:
                    await buy_amulet(user, ctx)

        except IndexError:
            embed = discord.Embed(
                color=0xffff80,
                title="🛒 Shopping District",
                description=f"Purchase 11{emoji_a} for 1000{emoji_j}. `;buy amulet`"
            )
            embed.set_thumbnail(url=self.client.user.avatar_url)
            await ctx.channel.send(embed=embed)


def setup(client):
    client.add_cog(Economy(client))
