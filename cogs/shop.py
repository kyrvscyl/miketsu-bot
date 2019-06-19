"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import asyncio
import discord
from discord.ext import commands
from cogs.mongo.db import users

# Global Variables
emoji_m = "<:medal:573071121545560064>"
emoji_j = "<:jade:555630314282811412>"
emoji_c = "<:coin:573071121495097344>"
emoji_f = "<:friendship:555630314056318979>"
emoji_a = "<:amulet:573071120685596682>"


# noinspection PyShadowingNames,PyMethodMayBeStatic
class Economy(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command()
    async def buy(self, ctx, *args):
        user = ctx.author
        try:
            if args[0] == "amulet":
                await ctx.message.add_reaction(":amulet:573071120685596682")

                def check(reaction, user):
                    return user == ctx.author and str(reaction.emoji) == emoji_a

                try:
                    reaction, user = await self.client.wait_for("reaction_add", timeout=10.0, check=check)
                except asyncio.TimeoutError:
                    msg = f"{user.mention}, timeout! You did not click {emoji_a} on time. Please try again."
                    await ctx.channel.send(msg)
                else:
                    await self.buy_amulet(user, ctx)

        except IndexError:
            embed = discord.Embed(color=0xffff80, title=":shopping_cart: Shopping District",
                                  description=f"Purchase 11{emoji_a} for 1000{emoji_j}. `;buy amulet`")
            embed.set_thumbnail(url=self.client.user.avatar_url)
            await ctx.channel.send(embed=embed)

    async def buy_amulet(self, user, ctx):
        if users.find_one({"user_id": str(user.id)}, {"_id": 0, "jades": 1})["jades"] >= 1000:
            users.update_one({"user_id": str(user.id)}, {"$inc": {"amulets": 11, "jades": -1000}})
            amulet = users.find_one({"user_id": str(user.id)}, {"_id": 0, "amulets": 1})["amulets"]
            await ctx.channel.send(f"{user.mention}, You have bought 11{emoji_a}. You now have {amulet}{emoji_a}")
        else:
            await ctx.channel.send(f"{user.mention}, You have insufficient {emoji_j}")


def setup(client):
    client.add_cog(Economy(client))
