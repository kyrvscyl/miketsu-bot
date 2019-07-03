"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import random

import discord
from discord.ext import commands

from cogs.mongo.db import users, daily

# Global Variables
emoji_m = "<:medal:573071121545560064>"
emoji_j = "<:jade:555630314282811412>"
emoji_c = "<:coin:573071121495097344>"
emoji_f = "<:friendship:555630314056318979>"
emoji_a = "<:amulet:573071120685596682>"


def calculate(x, y, z):
    try:
        if x - y > 0:
            return ((x - y) / x) * z
        elif x - y < 0:
            return -((y - x) / y) * z
        else:
            return 0
    except ZeroDivisionError:
        return 0


async def raid_giverewards_victim_as_winner(victim, raider):

    users.update_one({"user_id": str(victim.id)}, {"$inc": {"coins": 50000, "jades": 100, "medals": 50}})
    users.update_one({"user_id": str(raider.id)}, {"$inc": {"realm_ticket": -1}})

    if users.find_one({"user_id": str(raider.id)}, {"_id": 0})["medals"] < 10:
        users.update_one({"user_id": str(raider.id)}, {"$set": {"medals": 0}})

    else:
        users.update_one({"user_id": str(raider.id)}, {"$inc": {"medals": -10}})


async def raid_giverewards_raider_as_winner(victim, raider):

    users.update_one({"user_id": str(raider.id)},
                     {"$inc": {"coins": 25000, "jades": 50, "medals": 25, "realm_ticket": -1}})

    if users.find_one({"user_id": str(victim.id)}, {"_id": 0})["medals"] < 10:
        users.update_one({"user_id": str(victim.id)}, {"$set": {"medals": 0}})

    else:
        users.update_one({"user_id": str(victim.id)}, {"$inc": {"medals": -10}})


async def raid_calculation(victim, raider, ctx):

    try:

        profile_raider = users.find_one({"user_id": str(raider.id)},
                                        {"_id": 0, "level": 1, "medals": 1, "SP": 1, "SSR": 1, "SR": 1, "R": 1})
        profile_victim = users.find_one({"user_id": str(victim.id)},
                                        {"_id": 0, "level": 1, "medals": 1, "SP": 1, "SSR": 1, "SR": 1, "R": 1})

        chance1 = calculate(profile_raider["level"], profile_victim["level"], 0.15)
        chance2 = calculate(profile_raider["medals"], profile_victim["medals"], 0.15)
        chance3 = calculate(profile_raider["SP"], profile_victim["SP"], 0.09)
        chance4 = calculate(profile_raider["SSR"], profile_victim["SSR"], 0.07)
        chance5 = calculate(profile_raider["SR"], profile_victim["SR"], 0.03)
        chance6 = calculate(profile_raider["R"], profile_victim["R"], 0.01)
        total_chance = round((0.5 + chance1 + chance2 + chance3 + chance4 + chance5 + chance6) * 100, 2)

        embed = discord.Embed(color=raider.colour)
        embed.set_author(icon_url=raider.avatar_url, name=f"vs {victim.display_name} :: {total_chance}%")
        await ctx.channel.send(embed=embed)

    except KeyError:
        return

    except TypeError:
        return


async def raid_attack(victim, raider, ctx):

    try:

        profile_raider = users.find_one({'user_id': str(raider.id)},
                                        {'_id': 0, 'level': 1, 'medals': 1, 'SP': 1, 'SSR': 1, 'SR': 1, 'R': 1})
        profile_victim = users.find_one({'user_id': str(victim.id)},
                                        {'_id': 0, 'level': 1, 'medals': 1, 'SP': 1, 'SSR': 1, 'SR': 1, 'R': 1})

        chance1 = calculate(profile_raider["level"], profile_victim["level"], 0.15)
        chance2 = calculate(profile_raider["medals"], profile_victim["medals"], 0.15)
        chance3 = calculate(profile_raider["SP"], profile_victim["SP"], 0.09)
        chance4 = calculate(profile_raider["SSR"], profile_victim["SSR"], 0.07)
        chance5 = calculate(profile_raider["SR"], profile_victim["SR"], 0.03)
        chance6 = calculate(profile_raider["R"], profile_victim["R"], 0.01)
        total_chance = round((0.5 + chance1 + chance2 + chance3 + chance4 + chance5 + chance6) * 100, 2)
        roll = random.uniform(0, 100)

        if roll <= total_chance:
            embed = discord.Embed(color=raider.colour)
            embed.set_author(icon_url=raider.avatar_url, name=f"vs {victim.display_name} :: {total_chance}%")
            embed.add_field(name=f"*Result: {raider.display_name} wins!*",
                            value=f"25,000{emoji_c}, 50{emoji_j}, 25{emoji_m}")

            await raid_giverewards_raider_as_winner(victim, raider)
            await ctx.channel.send(embed=embed)

        else:
            embed = discord.Embed(color=raider.colour)
            embed.set_author(icon_url=raider.avatar_url, name=f"vs {victim.display_name} :: {total_chance}%")
            embed.add_field(name=f"*Result: {victim.display_name} wins!*",
                            value=f"50,000{emoji_c}, 100{emoji_j}, 50{emoji_m}")

            await raid_giverewards_victim_as_winner(victim, raider)
            await ctx.channel.send(embed=embed)

    except KeyError:
        return

    except TypeError:
        return


# noinspection PyTypeChecker
class Startup(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(aliases=["r"])
    @commands.guild_only()
    async def raid(self, ctx, *, victim: discord.Member = None):
        raider = ctx.author

        if victim is None:
            await ctx.channel.send(f"{raider.mention}, mention a user to raid")

        elif victim.bot or victim.id == ctx.author.id:
            return

        elif users.find_one({"user_id": str(raider.id)}, {"_id": 0, "realm_ticket": 1})["realm_ticket"] == 0:
            await ctx.channel.send(f"{raider.mention}, you have insufficient :tickets:")

        elif daily.find_one({"key": "raid"}, {"_id": 0, f"{victim.id}.raid_count": 1}) == {}:
            daily.update_one({"key": "raid"}, {"$set": {f"{victim.id}.raid_count": 1}})
            await raid_attack(victim, raider, ctx)

        elif daily.find_one({"key": "raid"},
                            {"_id": 0, f"{victim.id}.raid_count": 1})[str(victim.id)]["raid_count"] == 3:
            await ctx.channel.send(f"{raider.mention}, this user's realm is under protection.")

        elif daily.find_one({"key": "raid"},
                            {"_id": 0, f"{victim.id}.raid_count": 1})[str(victim.id)]["raid_count"] < 4:
            daily.update_one({"key": "raid"}, {"$inc": {f"{victim.id}.raid_count": 1}})
            await raid_attack(victim, raider, ctx)

    @commands.command(aliases=["rc", "raidc"])
    async def raid_calculate(self, ctx, *, victim: discord.Member = None):

        if victim is None:
            embed = discord.Embed(color=ctx.author.colour,
                                  title="Success Chance",
                                  description="• Base chance: 50%\n"
                                              "• Level: ± 15%\n"
                                              "• Medals: ± 15%\n"
                                              "• SP: ± 9%\n"
                                              "• SSR: ± 7%\n"
                                              "• SR: ± 3%\n"
                                              "• R: ± 1%")
            await ctx.channel.send(embed=embed)

        elif victim == ctx.author or victim.bot is True:
            return

        elif victim != ctx.author:
            await raid_calculation(victim, ctx.author, ctx)


def setup(client):
    client.add_cog(Startup(client))
