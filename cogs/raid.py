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
    # Victim
    users.update_one({"user_id": str(victim.id)}, {"$inc": {"coins": 50000, "jades": 100, "medals": 20}})

    # Raider
    users.update_one({"user_id": str(raider.id)}, {"$inc": {"realm_ticket": -1}})

    # No negative medals
    if users.find_one({"user_id": str(raider.id)}, {"_id": 0})["medals"] < 10:
        users.update_one({"user_id": str(raider.id)}, {"$set": {"medals": 0}})
    else:
        users.update_one({"user_id": str(raider.id)}, {"$inc": {"medals": -10}})


async def raid_giverewards_raider_as_winner(victim, raider):
    # Raider
    users.update_one({"user_id": str(raider.id)},
                     {"$inc": {"coins": 25000, "jades": 30, "medals": 10, "realm_ticket": -1}})

    # No negative medals
    if users.find_one({"user_id": str(victim.id)}, {"_id": 0})["medals"] < 10:
        users.update_one({"user_id": str(victim.id)}, {"$set": {"medals": 0}})
    else:
        users.update_one({"user_id": str(victim.id)}, {"$inc": {"medals": -10}})


async def raid_calculation(victim, raider, ctx):
    try:
        # Getting profiles
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

        embed = discord.Embed(color=raider.colour, title=":gear: Raid Calculation",
                              description=f":bow_and_arrow: Raider: `{raider.name}`\n"
                              f":dart:  Victim: `{victim.name}`\n\n"
                              f":game_die: `{total_chance}%` success")
        embed.set_thumbnail(url=raider.avatar_url)
        await ctx.channel.send(embed=embed)

    # Invalid mentioned user
    except KeyError:
        await ctx.channel.send(f"{raider.mention}, I did not find that user. Please try again.")
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
            embed = discord.Embed(color=raider.colour, title=":clipboard: Raid Report",
                                  description=f":bow_and_arrow: Raider: `{raider.name}`\n"
                                  f":dart: Victim: `{victim.name}`\n\n:game_die: `{total_chance}%` success\n"
                                  f":trophy: `{raider.name}` prevails!\n\n"
                                  f":gift: Rewards:\n25,000{emoji_c}, 30{emoji_j}, 10{emoji_m}")
            embed.set_thumbnail(url=raider.avatar_url)

            await raid_giverewards_raider_as_winner(victim, raider)
            await ctx.channel.send(embed=embed)
        else:
            embed = discord.Embed(color=victim.colour, title=":clipboard: Raid Report",
                                  description=f":bow_and_arrow: Raider: `{raider.name}`\n"
                                  f":dart:  Victim: `{victim.name}`\n\n:game_die: `{total_chance}%` success\n"
                                  f":trophy: `{victim.name}` prevails!\n\n"
                                  f":gift: Comeback Rewards:\n50,000{emoji_c}, 100{emoji_j}, 20{emoji_m}")
            embed.set_thumbnail(url=victim.avatar_url)

            await raid_giverewards_victim_as_winner(victim, raider)
            await ctx.channel.send(embed=embed)

    # Invalid mentioned user
    except KeyError:
        await ctx.channel.send(f"{raider.mention}, I did not find that user. Please try again.")
    except TypeError:
        return


class Startup(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(aliases=["r"])
    @commands.guild_only()
    async def raid(self, ctx, victim: discord.User = None):
        raider = ctx.author

        # No mentioned user
        if victim is None:
            await ctx.channel.send(f"{ctx.author.mention}, please mention a user to raid. Consumes 1:tickets:")

        # No Victim is a bot
        elif victim.bot:
            await ctx.channel.send(f"{ctx.author.mention}, you cannot do that!")

        # Victim is self
        elif victim.id == ctx.author.id:
            await ctx.channel.send(f"{ctx.author.mention}, you cannot raid your own realm.")

        # Checking realm tickets
        elif users.find_one({"user_id": str(raider.id)}, {"_id": 0, "realm_ticket": 1})["realm_ticket"] == 0:
            await ctx.channel.send(f"{ctx.author.mention}, You have insufficient :tickets:")

        # Create initial record
        elif daily.find_one({"key": "raid"}, {"_id": 0, f"{victim.id}.raid_count": 1}) == {}:
            daily.update_one({"key": "raid"}, {"$set": {f"{victim.id}.raid_count": 1}})
            await raid_attack(victim, raider, ctx)

        # Employ protection
        elif daily.find_one({"key": "raid"},
                            {"_id": 0, f"{victim.id}.raid_count": 1})[str(victim.id)]["raid_count"] == 3:
            await ctx.channel.send(f"{ctx.author.mention}, this user's realm is under protection.")

        # Raids the victim
        elif daily.find_one({"key": "raid"},
                            {"_id": 0, f"{victim.id}.raid_count": 1})[str(victim.id)]["raid_count"] < 4:
            daily.update_one({"key": "raid"}, {"$inc": {f"{victim.id}.raid_count": 1}})
            await raid_attack(victim, raider, ctx)

    @commands.command(aliases=["rc", "raidc"])
    async def raid_calculate(self, ctx, user: discord.User = None):

        # No mentioned user
        if user is None:
            embed = discord.Embed(color=0xffff80, title=":game_die: Raid Calculation",
                                  description="This calculates the percent chance of successfully raiding the "
                                              "mentioned user. Success chance is a function of level, medals, "
                                              "& shikigami pool of the victim & raider.\n\n:white_small_square: Base "
                                              "chance: 50%\n:white_small_square: Level: ± 15%\n:white_small_square: "
                                              "Medals: ± 15%\n:white_small_square: SP: ± 9%\n:white_small_square: SSR: "
                                              "± 7%\n:white_small_square: SR: ±3%\n:white_small_square: R: ±1%")
            embed.set_thumbnail(url=self.client.user.avatar_url)
            await ctx.channel.send(embed=embed)

        # Responds on self raid
        elif user == ctx.author or user.bot is True:
            await ctx.channel.send(f"{ctx.author.mention}, why would you do that?")

        # Calculates the chance
        elif user != ctx.author:
            await raid_calculation(user, ctx.author, ctx)


def setup(client):
    client.add_cog(Startup(client))
