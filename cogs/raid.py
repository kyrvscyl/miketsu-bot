"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import random

import discord
from discord.ext import commands

from cogs.mongo.db import users
from cogs.startup import emoji_m, emoji_j, emoji_c


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


def get_raid_count(victim):
    request = users.find_one({
        "user_id": str(victim.id)}, {
        "_id": 0, "raided_count": 1
    })
    return request["raided_count"]


async def raid_giverewards_victim_as_winner(victim, raider):
    users.update_one({"user_id": str(victim.id)}, {"$inc": {"coins": 50000, "jades": 100, "medals": 50}})
    users.update_one({"user_id": str(raider.id)}, {"$inc": {"realm_ticket": -1}})

    if users.find_one({"user_id": str(raider.id)}, {"_id": 0})["medals"] < 10:
        users.update_one({"user_id": str(raider.id)}, {"$set": {"medals": 0}})

    else:
        users.update_one({"user_id": str(raider.id)}, {"$inc": {"medals": -10}})


async def raid_giverewards_raider_as_winner(victim, raider):
    users.update_one({
        "user_id": str(raider.id)}, {
        "$inc": {
            "coins": 25000, "jades": 50, "medals": 25, "realm_ticket": -1
        }
    })

    if users.find_one({"user_id": str(victim.id)}, {"_id": 0})["medals"] < 10:
        users.update_one({"user_id": str(victim.id)}, {"$set": {"medals": 0}})

    else:
        users.update_one({"user_id": str(victim.id)}, {"$inc": {"medals": -10}})


async def raid_perform_calculation(victim, raider, ctx):
    try:
        profile_raider = users.find_one({
            "user_id": str(raider.id)}, {
            "_id": 0, "level": 1, "medals": 1, "SP": 1, "SSR": 1, "SR": 1, "R": 1
        })
        profile_victim = users.find_one({
            "user_id": str(victim.id)}, {
            "_id": 0, "level": 1, "medals": 1, "SP": 1, "SSR": 1, "SR": 1, "R": 1
        })

        chance1 = calculate(profile_raider["level"], profile_victim["level"], 0.15)
        chance2 = calculate(profile_raider["medals"], profile_victim["medals"], 0.15)
        chance3 = calculate(profile_raider["SP"], profile_victim["SP"], 0.09)
        chance4 = calculate(profile_raider["SSR"], profile_victim["SSR"], 0.07)
        chance5 = calculate(profile_raider["SR"], profile_victim["SR"], 0.03)
        chance6 = calculate(profile_raider["R"], profile_victim["R"], 0.01)
        total_chance = round((0.5 + chance1 + chance2 + chance3 + chance4 + chance5 + chance6) * 100)

        embed = discord.Embed(
            color=raider.colour,
            title=f"{raider.display_name} vs {victim.display_name} :: {total_chance}%"
        )
        await ctx.channel.send(embed=embed)

    except KeyError:
        embed = discord.Embed(
            title="Invalid member", colour=discord.Colour(0xffe6a7),
            description=f"{victim} doesnt have a realm yet in this server"
        )
        await ctx.channel.send(embed=embed)

    except TypeError:
        return


async def raid_perform_attack(victim, raider, ctx):
    try:
        profile_raider = users.find_one({
            "user_id": str(raider.id)}, {
            "_id": 0, "level": 1, "medals": 1, "SP": 1, "SSR": 1, "SR": 1, "R": 1
        })
        profile_victim = users.find_one({
            "user_id": str(victim.id)}, {
            "_id": 0, "level": 1, "medals": 1, "SP": 1, "SSR": 1, "SR": 1, "R": 1
        })

        chance1 = calculate(profile_raider["level"], profile_victim["level"], 0.15)
        chance2 = calculate(profile_raider["medals"], profile_victim["medals"], 0.15)
        chance3 = calculate(profile_raider["SP"], profile_victim["SP"], 0.09)
        chance4 = calculate(profile_raider["SSR"], profile_victim["SSR"], 0.07)
        chance5 = calculate(profile_raider["SR"], profile_victim["SR"], 0.03)
        chance6 = calculate(profile_raider["R"], profile_victim["R"], 0.01)
        total_chance = round((0.5 + chance1 + chance2 + chance3 + chance4 + chance5 + chance6) * 100)
        roll = random.uniform(0, 100)

        if roll <= total_chance:
            embed = discord.Embed(
                title="Realm Raid", color=raider.colour,
                description=f"{raider.mention} raids {victim.display_name}'s realm!"
            )
            embed.add_field(
                name=f"Results, `{total_chance}%`",
                value=f"||"
                f"{raider.display_name} won!\n"
                f"25,000{emoji_c}, 50{emoji_j}, 25{emoji_m}"
                f"||"
            )
            await raid_giverewards_raider_as_winner(victim, raider)
            await ctx.channel.send(embed=embed)

        else:
            embed = discord.Embed(
                title="Realm Raid", color=raider.colour,
                description=f"{raider.mention} raids {victim.display_name}'s realm!"
            )
            embed.add_field(
                name=f"Results, `{total_chance}%`",
                value=f"||"
                f"{victim.display_name} won!\n"
                f"50,000{emoji_c}, 100{emoji_j}, 50{emoji_m}"
                f"||"
            )
            await raid_giverewards_raider_as_winner(victim, raider)
            await ctx.channel.send(embed=embed)

    except KeyError:
        embed = discord.Embed(
            title="Invalid member", colour=discord.Colour(0xffe6a7),
            description=f"{victim} doesnt have a realm yet in this server"
        )
        await ctx.channel.send(embed=embed)

    except TypeError:
        return


class Startup(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(aliases=["raid", "r"])
    @commands.guild_only()
    async def raid_perform_attack(self, ctx, *, victim: discord.Member = None):

        raider = ctx.author
        raider_tickets = users.find_one({"user_id": str(raider.id)}, {"_id": 0, "realm_ticket": 1})["realm_ticket"]

        if victim is None:
            embed = discord.Embed(
                title="raid, r", colour=discord.Colour(0xffe6a7),
                description="raids the tagged member, requires 1 ticket"
            )
            embed.add_field(name="Formats", value="*`;raid @member`*, *`;r <name#discriminator>`*")
            await ctx.channel.send(embed=embed)

        elif victim.bot or victim.id == ctx.author.id:
            return

        elif raider_tickets < 1:
            embed = discord.Embed(
                title=f"{raider.display_name}, you have insufficient tickets", colour=discord.Colour(0xffe6a7),
                description="Purchase at the shop or get your daily rewards"
            )
            await ctx.channel.send(embed=embed)
            return

        try:
            raid_count = get_raid_count(victim)

            if raid_count == 3:
                embed = discord.Embed(
                    title=f"{victim.display_name}'s realm is under protection", colour=discord.Colour(0xffe6a7),
                    description="Raids are capped at 3 times per day and per realm"
                )
                await ctx.channel.send(embed=embed)

            elif raid_count < 4:
                users.update_one({"user_id": str(victim.id)}, {"$inc": {"raided_count": 1}})
                await raid_perform_attack(victim, raider, ctx)

        except TypeError:
            embed = discord.Embed(
                title="Invalid member", colour=discord.Colour(0xffe6a7),
                description="That member doesn't exist in this guild"
            )
            await ctx.channel.send(embed=embed)


    @commands.command(aliases=["raidcalc", "raidc", "rc"])
    @commands.guild_only()
    async def raid_perform_calculation(self, ctx, *, victim: discord.Member = None):

        if victim is None:
            embed = discord.Embed(
                title="raidcalc, raidc, rc", colour=discord.Colour(0xffe6a7),
                description="calculates your odds of winning"
            )
            embed.add_field(
                name="Mechanics",
                value="```"
                      "Base Chance :: + 50 %\n"
                      "Δ Level     :: ± 15 %\n"
                      "Δ Medal     :: ± 15 %\n"
                      "Δ SP        :: ±  9 %\n"
                      "Δ SSR       :: ±  7 %\n"
                      "Δ SR        :: ±  3 %\n"
                      "Δ R         :: ±  1 %\n"
                      "```",
                inline=False
            )
            embed.add_field(name="Formats", value="*`;raidc @member`*, *`;rc <name#discriminator>`*", inline=False)
            await ctx.channel.send(embed=embed)

        elif victim == ctx.author or victim.bot is True:
            return

        elif victim != ctx.author:
            await raid_perform_calculation(victim, ctx.author, ctx)


def setup(client):
    client.add_cog(Startup(client))
