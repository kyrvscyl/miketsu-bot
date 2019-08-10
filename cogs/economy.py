"""
Economy Module
Miketsu, 2019
"""

import asyncio
import os
import random
from datetime import datetime
from math import ceil

import discord
import pytz
from PIL import Image
from discord.ext import commands

from cogs.frames import Frames
from cogs.mongo.database import get_collections
from cogs.startup import e_m, e_j, e_c, e_f, e_a, e_sp, e_ssr, e_sr, e_r, e_t, pluralize, primary_id, embed_color

# Collections
books = get_collections("bukkuman", "books")
bounty = get_collections("bukkuman", "bounty")
shikigamis = get_collections("miketsu", "shikigamis")
users = get_collections("miketsu", "users")
ships = get_collections("miketsu", "ships")
streak = get_collections("miketsu", "streak")
frames = get_collections("miketsu", "frames")
boss = get_collections("miketsu", "boss")

# Listings
spell_spams_id = []
pool_all = []
shrinable_shikigamis = []
rarities = ["SP", "SSR", "SR", "R"]
adverb = ["deliberately", "forcefully", "unknowingly", "accidentally", "dishonestly"]
verb = ["snatched", "stole", "took", "looted", "shoplifted", "embezzled"]
noun = ["custody", "care", "control", "ownership"]
comment = ["Sneaky!", "Gruesome!", "Madness!"]


for document in books.find({}, {"_id": 0, "channels.spell-spam": 1}):
    try:
        spell_spams_id.append(document["channels"]["spell-spam"])
    except KeyError:
        continue

for document in shikigamis.aggregate([
    {
        "$project": {
            "shikigami.name": 1
        }
    }, {
        "$unwind": {
            "path": "$shikigami"
        }
    }, {
        "$project": {
            "_id": 0
        }
    }
]):
    pool_all.append(document["shikigami"]["name"])

for document in shikigamis.aggregate([{
    "$unwind": {
        "path": "$shikigami"}}, {
    "$match": {
        "shikigami.shrine": True}}, {
    "$project": {
        "_id": 0, "shikigami.thumbnail": 0
    }
}]):
    shrinable_shikigamis.append(document["shikigami"]["name"])


def check_if_user_has_prayers(ctx):
    return users.find_one({"user_id": str(ctx.author.id)}, {"_id": 0, "prayers": 1})["prayers"] > 0


def get_frame_thumbnail(frame):
    request = frames.find_one({"name": frame}, {"_id": 0, "link": 1})
    return request["link"]


def get_time():
    tz_target = pytz.timezone("America/Atikokan")
    return datetime.now(tz=tz_target)


def get_timestamp():
    return datetime.utcfromtimestamp(datetime.timestamp(datetime.now()))


def get_evo_link(evolution):
    key = {"True": "evo", "False": "pre_evo"}
    return key[evolution]


def get_rarity(shiki):
    profile = shikigamis.find_one({"shikigami.name": shiki}, {"_id": 0, "rarity": 1})
    return profile["rarity"]


def get_requirement(r):
    key = {"R": 21, "SR": 11, "SSR": 2, "SP": 0}
    return key[r]


def get_talisman_acquire(x):
    dictionary = {"R": 50, "SR": 250, "SSR": 10000, "SP": 15000}
    return dictionary[x]


async def reset_boss():
    boss.update_many({}, {
        "$set": {
            "discoverer": 0,
            "level": 0,
            "damage_cap": 0,
            "total_hp": 0,
            "current_hp": 0,
            "challengers": [],
            "rewards": {}
        }
    })


async def acquisition_frame(user, frame_name, channel, jades):
    for entry in users.aggregate([
        {
            "$match": {
                "user_id": str(user.id)
            }
        }, {
            "$unwind": {
                "path": "$achievements"
            }
        }, {
            "$project": {
                "achievements": 1
            }
        }, {
            "$match": {
                "achievements.name": frame_name
            }
        }, {
            "$count": "count"
        }
    ]):
        if entry["count"] != 0:
            return

    users.update_one({
        "user_id": str(user.id)}, {
        "$push": {
            "achievements": {
                "name": frame_name,
                "date_acquired": get_time()
            }
        },
        "$inc": {
            "jades": jades
        }
    })
    embed = discord.Embed(
        color=user.colour,
        title="Frame Acquisition",
        description=f"{user.mention}, you acquired the {frame_name} frame and {jades:,d}{e_j}"
    )
    embed.set_thumbnail(url=get_frame_thumbnail(frame_name.title()))
    await channel.send(embed=embed)


async def claim_rewards_daily_give(user, ctx):
    users.update_one({"user_id": str(user.id)}, {
        "$inc": {
            "friendship_pass": 5,
            "jades": 50,
            "coins": 25000,
            "realm_ticket": 3,
            "encounter_ticket": 4
        },
        "$set": {
            "daily": True
        }
    })
    embed = discord.Embed(
        color=ctx.author.colour,
        title="🎁 Daily Rewards",
        description=f"A box containing 5 💗, 50{e_j}, 25k{e_c}, 3 🎟, 4 🎫"
    )
    embed.set_footer(text=f"Opened by {user.display_name}", icon_url=user.avatar_url)
    await ctx.channel.send(embed=embed)


async def weekly_give_rewards(user, ctx):
    users.update_one({"user_id": str(user.id)}, {
        "$inc": {
            "jades": 750,
            "coins": 150000,
            "amulets": 10
        },
        "$set": {
            "weekly": True
        }
    })

    embed = discord.Embed(
        color=ctx.author.colour,
        title="💝 Weekly Rewards",
        description=f"A mythical box containing 750{e_j}, 150k{e_c}, and 10{e_a}"
    )
    embed.set_footer(text=f"Opened by {user.display_name}", icon_url=user.avatar_url)
    await ctx.channel.send(embed=embed)


async def evolve_shikigami(ctx, rarity, evo, user, query, count):
    if rarity == "SP":
        embed = discord.Embed(
            colour=discord.Colour(embed_color),
            description=f"{user.mention}, SP shikigamis are pre-evolved"
        )
        await ctx.channel.send(embed=embed)

    elif evo == "True":
        embed = discord.Embed(
            colour=discord.Colour(embed_color),
            description=f"{user.mention}, your {query} is already evolved."
        )
        await ctx.channel.send(embed=embed)

    elif evo == "False":
        rarity_count = get_requirement(rarity)

        if count >= rarity_count:

            users.update_one({
                "user_id": str(user.id),
                "shikigami.name": query}, {
                "$inc": {
                    "shikigami.$.owned": -(rarity_count - 1),
                    f"{rarity}": -(rarity_count - 1)
                },
                "$set": {
                    "shikigami.$.evolved": "True",
                    "shikigami.$.shards": 5
                }
            })

            shikigami_profile = shikigamis.find_one({
                "shikigami.name": query.title()}, {
                "shikigami.$.name": 1
            })
            image_url = shikigami_profile["shikigami"][0]["thumbnail"]["evo"]

            embed = discord.Embed(
                colour=discord.Colour(embed_color),
                title="Evolution successful",
                description=f"{user.mention}, you have evolved your {query}!"
            )
            embed.set_thumbnail(url=image_url)
            await ctx.channel.send(embed=embed)

            if query == "Orochi":
                await acquisition_frame(user, "Sword Swallowing-Snake", ctx.channel, jades=2500)

        elif count == 0:
            embed = discord.Embed(
                colour=discord.Colour(embed_color),
                description=f"{user.mention}, you do not own that shikigami"
            )
            await ctx.channel.send(embed=embed)

        elif count <= (get_requirement(rarity) - 1):
            required = rarity_count - count
            noun_duplicate = pluralize('dupe', required)
            embed = discord.Embed(
                colour=discord.Colour(embed_color),
                title="Insufficient shikigamis",
                description=f"{user.mention}, you lack {required} more {query} {noun_duplicate} to evolve yours"
            )
            await ctx.channel.send(embed=embed)


async def frame_starlight(guild, spell_spam_channel):
    starlight_role = discord.utils.get(guild.roles, name="Starlight Sky")

    streak_list = []
    for user in streak.find({}, {"_id": 0, "user_id": 1, "SSR_current": 1}):
        streak_list.append((user["user_id"], user["SSR_current"]))

    streak_list_new = sorted(streak_list, key=lambda x: x[1], reverse=True)
    starlight_new = guild.get_member(int(streak_list_new[0][0]))
    starlight_current = starlight_role.members[0]

    if len(starlight_role.members) == 0:
        await starlight_new.add_roles(starlight_role)
        await asyncio.sleep(3)

        description = \
            f"{starlight_new.mention}\"s undying luck of not summoning an SSR has " \
            f"earned themselves the Rare Starlight Sky Frame!\n\n" \
            f"🍀 No SSR streak as of posting: {streak_list_new[0][1]} summons!"

        embed = discord.Embed(
            color=0xac330f,
            title="📨 Hall of Framers Update",
            description=description
        )
        embed.set_thumbnail(url="https://vignette.wikia.nocookie.net/onmyoji/images/1/17/Frame7.png")
        await spell_spam_channel.send(embed=embed)
        await acquisition_frame(starlight_new, "Starlight Sky", spell_spam_channel, jades=2500)

    if starlight_current == starlight_new:
        users.update_one({"user_id": str(starlight_current.id)}, {"$inc": {"jades": 2000}})
        msg = f"{starlight_current.mention} has earned 2,000{e_j} " \
              f"for wielding the Starlight Sky frame for a day!"
        await spell_spam_channel.send(msg)

    else:
        await starlight_new.add_roles(starlight_role)
        await asyncio.sleep(3)
        await starlight_current.remove_roles(starlight_role)
        await asyncio.sleep(3)

        description = \
            f"{starlight_new.mention} {random.choice(adverb)} {random.choice(verb)} " \
            f"the Rare Starlight Sky Frame from {starlight_current.mention}\"s " \
            f"{random.choice(noun)}!! {random.choice(comment)}\n\n" \
            f"🍀 No SSR streak record as of posting: {streak_list_new[0][1]} summons!"

        embed = discord.Embed(
            color=0xac330f,
            title="📨 Hall of Framers Update",
            description=description
        )
        embed.set_thumbnail(url="https://vignette.wikia.nocookie.net/onmyoji/images/1/17/Frame7.png")
        await spell_spam_channel.send(embed=embed)
        await acquisition_frame(starlight_new, "Starlight Sky", spell_spam_channel, jades=2500)


async def frame_blazing(guild, spell_spam_channel):
    blazing_role = discord.utils.get(guild.roles, name="Blazing Sun")

    ssr_list = []
    for user in users.find({}, {"_id": 0, "user_id": 1, "SSR": 1}):
        ssr_list.append((user["user_id"], user["SSR"]))

    ssr_list_new = sorted(ssr_list, key=lambda x: x[1], reverse=True)
    blazing_new = guild.get_member(int(ssr_list_new[0][0]))
    blazing_current = blazing_role.members[0]

    if len(blazing_role.members) == 0:
        await blazing_new.add_roles(blazing_role)
        await asyncio.sleep(3)

        description = \
            f"{blazing_new.mention}\"s fortune luck earned themselves the Rare Blazing Sun Frame!\n\n" \
            f"🍀 Distinct SSRs under possession: {ssr_list_new[0][1]} shikigamis"

        embed = discord.Embed(
            color=0xac330f,
            title="📨 Hall of Framers Update",
            description=description
        )
        embed.set_thumbnail(url="https://vignette.wikia.nocookie.net/onmyoji/images/7/72/Frame62.png")
        await spell_spam_channel.send(embed=embed)
        await acquisition_frame(blazing_new, "Blazing Sun", spell_spam_channel, jades=2500)

    if blazing_current == blazing_new:
        users.update_one({"user_id": str(blazing_current.id)}, {"$inc": {"amulets": 10}})
        msg = f"{blazing_current.mention} has earned 10{e_a} for wielding the Blazing Sun frame for a day!"
        await spell_spam_channel.send(msg)

    else:
        await blazing_new.add_roles(blazing_role)
        await asyncio.sleep(3)
        await blazing_current.remove_roles(blazing_role)
        await asyncio.sleep(3)

        description = f"{blazing_new.mention} {random.choice(adverb)} {random.choice(verb)} " \
                      f"the Rare Blazing Sun Frame from {blazing_current.mention}\"s {random.choice(noun)}!! " \
                      f"{random.choice(comment)}\n\n" \
                      f"🍀 Distinct SSRs under possession: {ssr_list_new[0][1]} shikigamis"

        embed = discord.Embed(
            color=0xffff80,
            title="📨 Hall of Framers Update",
            description=description
        )
        embed.set_thumbnail(url="https://vignette.wikia.nocookie.net/onmyoji/images/7/72/Frame62.png")
        await spell_spam_channel.send(embed=embed)
        await acquisition_frame(blazing_new, "Blazing Sun", spell_spam_channel, jades=2500)


class Economy(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(aliases=["wish"])
    @commands.guild_only()
    async def wish_perform(self, ctx, *, shikigami=None):

        user = ctx.author
        profile = users.find_one({"user_id": str(user.id)}, {"_id": 0, "wish": 1})

        if shikigami is None:
            embed = discord.Embed(
                color=embed_color,
                title="wish, w",
                description=f"wish for a shikigami shard to manually summon it"
            )
            embed.add_field(name="Example", value="*`;wish inferno ibaraki`*")
            await ctx.channel.send(embed=embed)

        elif profile["wish"] is False:
            embed = discord.Embed(
                color=user.colour,
                description=f"{user.mention}, your wish has been fulfilled already today",
            )
            await ctx.channel.send(embed=embed)

        elif profile["wish"] is not True:
            embed = discord.Embed(
                color=user.colour,
                description=f"{user.mention}, you have wished already today",
            )
            await ctx.channel.send(embed=embed)

        elif profile["wish"] is True and shikigami.title() not in pool_all:
            embed = discord.Embed(
                color=user.colour,
                description=f"{user.mention}, you provided an invalid shikigami name"
            )
            await ctx.channel.send(embed=embed)

        elif profile["wish"] is True and shikigami.title() in pool_all:

            users.update_one({"user_id": str(user.id)}, {"$set": {"wish": shikigami.title()}})
            query = users.find_one({
                "user_id": str(user.id),
                "shikigami.name": shikigami.title()}, {
                "_id": 0, "shikigami.$": 1
            })

            if query is None:
                users.update_one({
                    "user_id": str(user.id)}, {
                    "$push": {
                        "shikigami": {
                            "name": shikigami.title(),
                            "rarity": get_rarity(shikigami.title()),
                            "grade": 1,
                            "owned": 0,
                            "evolved": "False",
                            "shards": 0
                        }
                    }
                })

            embed = discord.Embed(
                color=user.colour,
                title=f"Successfully registered your wish",
                description=f"{user.mention}, you wished for {shikigami.title()} shard",
                timestamp=get_timestamp()
            )
            embed.set_footer(text=f"use ;wishlist for daily shard wishes")
            await ctx.message.add_reaction("✅")
            await ctx.channel.send(embed=embed)

    @commands.command(aliases=["wishlist", "wl"])
    @commands.guild_only()
    async def wish_show_list(self, ctx):

        wishes = users.find({"wish": {"$ne": True}}, {"_id": 0, "wish": 1, "user_id": 1})

        shard_wishes = []
        for wish in wishes:
            user = self.client.get_user(int(wish["user_id"]))
            wish = wish['wish']
            if wish is False:
                wish = "Fulfilled"
            shard_wishes.append(f"▫{user} | *{wish}*\n")

        await self.wish_show_list_paginate(ctx, shard_wishes)

    async def wish_show_list_paginate(self, ctx, shard_wishes):

        page = 1
        max_lines = 10
        page_total = ceil(len(shard_wishes) / max_lines)
        ordinal = lambda n: "%d%s" % (n, "tsnrhtdd"[(n / 10 % 10 != 1) * (n % 10 < 4) * n % 10::4])

        def create_new_embed_page(page_new):
            end = page_new * max_lines
            start = end - max_lines
            description_new = "".join(shard_wishes[start:end])

            embed_new = discord.Embed(
                color=embed_color,
                title=f"🗒 Wish List [{ordinal(get_time().timetuple().tm_yday)} day]",
                description=f"{description_new}",
                timestamp=get_timestamp()
            )
            embed_new.set_footer(text=f"Page: {page_new} of {page_total}")
            embed_new.set_thumbnail(url=ctx.guild.icon_url)
            return embed_new

        def check(r, u):
            return u != self.client.user and r.message.id == msg.id

        msg = await ctx.channel.send(embed=create_new_embed_page(page))
        await msg.add_reaction("⬅")
        await msg.add_reaction("➡")

        while True:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=60, check=check)
            except asyncio.TimeoutError:
                break
            else:
                if str(reaction.emoji) == "➡":
                    page += 1
                elif str(reaction.emoji) == "⬅":
                    page -= 1
                if page == 0:
                    page = page_total
                elif page > page_total:
                    page = 1
                await msg.edit(embed=create_new_embed_page(page))

    @commands.command(aliases=["fulfill", "ff"])
    @commands.guild_only()
    async def wish_grant(self, ctx, *, member: discord.Member = None):

        user = ctx.author

        if member is None:
            embed = discord.Embed(
                color=ctx.author.colour,
                title=f"fulfill, ff",
                description=f"fulfill a wish from a member in *`;wishlist`*\nno confirmation prompt for fulfilling",
            )
            embed.add_field(name="Format", value="*`;ff <@member>`*")
            await ctx.channel.send(embed=embed)
            return

        try:
            shikigami_wished_for = users.find_one({"user_id": str(member.id)}, {"_id": 0, "wish": 1})["wish"]

        except KeyError:
            embed = discord.Embed(
                title="Invalid member", colour=discord.Colour(embed_color),
                description="That member doesn't exist nor has a profile in this guild"
            )
            await ctx.channel.send(embed=embed)
            return

        if shikigami_wished_for is True:
            embed = discord.Embed(
                color=user.colour,
                title=f"Invalid member",
                description=f"{user.mention}, that user has not placed their daily wish yet",
            )
            await ctx.channel.send(embed=embed)

        elif shikigami_wished_for is False:
            embed = discord.Embed(
                color=user.colour,
                title=f"Wish fulfillment failed",
                description=f"{user.mention}, that user has their wish fulfilled already"
            )
            await ctx.channel.send(embed=embed)

        else:
            profile = users.find_one({
                "user_id": str(user.id), "shikigami.name": shikigami_wished_for}, {
                "_id": 0, "shikigami.$.name": 1
            })

            if profile is None:
                embed = discord.Embed(
                    color=user.colour,
                    title=f"Insufficient shards",
                    description=f"{user.mention}, you do not have any shards of that shikigami",
                )
                await ctx.channel.send(embed=embed)

            elif profile["shikigami"][0]["shards"] == 0:
                embed = discord.Embed(
                    color=user.colour,
                    title=f"Insufficient shards",
                    description=f"{user.mention}, you do not have any shards of that shikigami",
                )
                await ctx.channel.send(embed=embed)

            elif profile["shikigami"][0]["shards"] > 0:
                users.update_one({"user_id": str(user.id), "shikigami.name": shikigami_wished_for}, {
                    "$inc": {
                        "shikigami.$.shards": -1,
                        "friendship_pass": 3,
                        "friendship": 10
                    }
                })

                users.update_one({"user_id": str(member.id), "shikigami.name": shikigami_wished_for}, {
                    "$inc": {
                        "shikigami.$.shards": 1
                    },
                    "$set": {
                        "wish": False
                    }
                })

                embed = discord.Embed(
                    color=user.colour,
                    title=f"Wish fulfilled",
                    description=f"{user.mention}, you donated 1 {shikigami_wished_for} shard to {member.mention}.\n"
                                f"Acquired 10{e_f} and 3 💗",
                    timestamp=get_timestamp()
                )
                await ctx.channel.send(embed=embed)

    @commands.command()
    @commands.is_owner()
    async def reset(self, ctx, *, args):

        if args == "daily":
            await self.reset_rewards_daily()
            await ctx.message.add_reaction("✅")

        elif args == "weekly":
            await self.reset_rewards_weekly()
            await Frames(self.client).achievements_process_weekly()
            await ctx.message.add_reaction("✅")

        elif args == "boss":
            await reset_boss()
            await ctx.message.add_reaction("✅")

        elif args not in ["daily", "weekly", "boss"]:
            embed = discord.Embed(
                colour=discord.Colour(embed_color),
                title="Invalid argument",
                description="Provide a valid argument: `daily`, `weekly`, or `boss`"
            )
            await ctx.channel.send(embed=embed)

    async def reset_rewards_daily(self):

        users.update_many({}, {"$set": {"daily": False, "raided_count": 0, "prayers": 3, "wish": True}})
        query = {"level": {"$gt": 1}}
        project = {"ship_name": 1, "shipper1": 1, "shipper2": 1, "level": 1}

        for ship in ships.find(query, project):
            rewards = ship["level"] * 25
            users.update_one({"user_id": ship["shipper1"]}, {"$inc": {"jades": rewards}})
            users.update_one({"user_id": ship["shipper2"]}, {"$inc": {"jades": rewards}})

        embed1 = discord.Embed(
            title="🎁 Daily rewards have been reset", colour=discord.Colour(embed_color),
            description="Claim yours using `;daily`"
        )
        embed2 = discord.Embed(
            title="🛳 Daily ship sail rewards have been issued", colour=discord.Colour(0xf8f4b1),
            description="Check your income using `;sail`"
        )

        for channel in spell_spams_id:
            current_channel = self.client.get_channel(int(channel))
            try:
                await current_channel.send(embed=embed1)
                await current_channel.send(embed=embed2)
            except AttributeError:
                continue
            except discord.errors.Forbidden:
                continue

    async def reset_rewards_weekly(self):

        users.update_many({}, {"$set": {"weekly": False}})

        embed = discord.Embed(
            title="💝 Weekly rewards have been reset", colour=discord.Colour(embed_color),
            description="Claim yours using `;weekly`"
        )
        for channel in spell_spams_id:
            current_channel = self.client.get_channel(int(channel))
            await current_channel.send(embed=embed)

    @commands.command(aliases=["stat"])
    @commands.guild_only()
    async def stat_shikigami(self, ctx, *, name):

        if name.lower() == "all":
            rarity_evolved = [0]
            count_all = []

            for rarity in rarities:

                for result in users.aggregate([
                    {
                        "$match": {
                            "shikigami.evolved": "True"
                        }
                    }, {
                        "$unwind": {
                            "path": "$shikigami"
                        }
                    }, {
                        "$project": {
                            "shikigami": 1
                        }
                    }, {
                        "$match": {
                            "shikigami.evolved": "True",
                            "shikigami.rarity": rarity
                        }
                    }, {
                        "$count": "count"
                    }
                ]):
                    rarity_evolved.append(result["count"])

            for rarity in rarities:

                for result in users.aggregate([
                    {
                        "$project": {
                            "_id": 0,
                            "user_id": 1,
                            "shikigami": 1
                        }
                    }, {
                        "$unwind": {
                            "path": "$shikigami"
                        }
                    }, {
                        "$match": {
                            "shikigami.rarity": rarity
                        }
                    }, {
                        "$group": {
                            "_id": "",
                            "evolved": {
                                "$sum": "$shikigami.owned"
                            }
                        }
                    }
                ]):
                    count_all.append(result["evolved"])

            count_1 = count_all[0] + rarity_evolved[0]
            count_2 = count_all[1] + rarity_evolved[1] * 1
            count_3 = count_all[2] + rarity_evolved[2] * 10
            count_4 = count_all[3] + rarity_evolved[3] * 20
            count_total = count_1 + count_2 + count_3 + count_4

            distribution_1 = round(count_1 / count_total * 100, 3)
            distribution_2 = round(count_2 / count_total * 100, 3)
            distribution_3 = round(count_3 / count_total * 100, 3)
            distribution_4 = round(count_4 / count_total * 100, 3)

            embed = discord.Embed(
                title="Rarity | Distribution | Count", color=ctx.author.colour,
                description=f"```"
                            f"Rarity\n"
                            f"SP    ::    {distribution_1}%  ::   {count_1:,d}\n"
                            f"SSR   ::    {distribution_2}%  ::   {count_2:,d}\n"
                            f"SR    ::   {distribution_3}%  ::   {count_3:,d}\n"
                            f"R     ::   {distribution_4}%  ::   {count_4:,d}"
                            f"```",
                timestamp=get_timestamp()
            )

            embed.set_author(name="Summon Pull Statistics")
            embed.add_field(name="Total Amulets Spent", value=f"{count_total:,d}")
            await ctx.channel.send(embed=embed)

        elif name.title() not in pool_all:
            embed = discord.Embed(
                title="Invalid shikigami name",
                colour=discord.Colour(embed_color),
                description="Try again"
            )
            await ctx.channel.send(embed=embed)

        elif name.title() in pool_all:

            listings = []
            for entry in users.aggregate([
                {
                    "$match": {
                        "shikigami.name": name.title()
                    }
                }, {
                    "$project": {
                        "_id": 0,
                        "user_id": 1,
                        "shikigami.name": 1
                    }
                }, {
                    "$unwind": {
                        "path": "$shikigami"
                    }
                }, {
                    "$match": {
                        "shikigami.name": name.title()
                    }
                }
            ]):
                try:
                    listings.append(self.client.get_user(int(entry["user_id"])).display_name)
                except AttributeError:
                    continue

            thumbnail_url = ""
            for entry in shikigamis.find({}, {"_id": 0, "shikigami": {"$elemMatch": {"name": name.title()}}}):
                try:
                    thumbnail_url = entry["shikigami"][0]["thumbnail"]["pre_evo"]
                except KeyError:
                    continue

            count_pre_evo = 0
            count_evolved = 0

            for result_pre_evo in users.aggregate([
                {
                    "$match": {
                        "shikigami.name": name.title()
                    }
                }, {
                    "$project": {
                        "_id": 0,
                        "user_id": 1,
                        "shikigami": 1
                    }
                }, {
                    "$unwind": {
                        "path": "$shikigami"
                    }
                }, {
                    "$match": {
                        "shikigami.name": name.title(),
                        "shikigami.evolved": "False"
                    }
                }, {
                    "$count": "pre_evo"
                }
            ]):
                count_pre_evo = result_pre_evo["pre_evo"]

            for result_evolved in users.aggregate([
                {
                    "$match": {
                        "shikigami.name": name.title()
                    }
                }, {
                    "$project": {
                        "_id": 0,
                        "user_id": 1,
                        "shikigami": 1
                    }
                }, {
                    "$unwind": {
                        "path": "$shikigami"
                    }
                }, {
                    "$match": {
                        "shikigami.name": name.title(),
                        "shikigami.evolved": "True"
                    }
                }, {
                    "$count": "evolved"
                }
            ]):
                count_evolved = result_evolved["evolved"]

            embed = discord.Embed(
                title=f"Stats for {name.title()}", colour=ctx.author.colour,
                description=f"```"
                            f"Pre-evolve    ::   {count_pre_evo}\n"
                            f"Evolved       ::   {count_evolved}"
                            f"```",
                timestamp=get_timestamp()
            )

            listings_formatted = ", ".join(listings)

            if len(listings) == 0:
                listings_formatted = "None"

            embed.set_thumbnail(url=thumbnail_url)
            embed.add_field(
                name=f"Owned by {len(listings)} {pluralize('member', len(listings))}",
                value=f"{listings_formatted}"
            )
            await ctx.channel.send(embed=embed)

    @commands.command(aliases=["pray"])
    @commands.guild_only()
    @commands.check(check_if_user_has_prayers)
    async def pray_use(self, ctx):

        embed = discord.Embed(
            title="Pray to the Goddess of Hope and Prosperity!",
            color=ctx.author.colour,
            description="45% chance to obtain rich rewards"
        )
        msg = await ctx.channel.send(embed=embed)
        rewards_emoji = [e_j, e_f, e_a, e_c, e_t, e_m]

        rewards_selection = []
        for x in range(0, 3):
            emoji = random.choice(rewards_emoji)
            await msg.add_reaction(emoji.replace("<", "").replace(">", ""))
            rewards_emoji.remove(emoji)
            rewards_selection.append(emoji)

        def check(r, u):
            return str(r.emoji) in rewards_selection and u == ctx.author

        def get_rewards(y):
            dictionary1 = {e_j: 250, e_f: 50, e_a: 3, e_c: 450000, e_t: 1500, e_m: 150}
            dictionary2 = {
                e_j: "jades",
                e_f: "friendship",
                e_a: "amulets",
                e_c: "coins",
                e_t: "talisman",
                e_m: "medals"
            }
            return dictionary1[y], dictionary2[y]

        try:
            roll = random.randint(1, 100)
            reaction, user = await self.client.wait_for("reaction_add", timeout=150, check=check)
        except asyncio.TimeoutError:
            return

        else:
            users.update_one({"user_id": str(ctx.author.id)}, {"$inc": {"prayers": -1}})

            if roll >= 55:
                embed = discord.Embed(
                    title=f"Results", color=ctx.author.colour,
                    description=f"||Sometimes, you have to pray harder to be heard||"
                )
                await ctx.channel.send(embed=embed)

            else:
                amount, rewards = get_rewards(str(reaction.emoji))
                embed = discord.Embed(
                    title=f"Results", color=ctx.author.colour,
                    description=f"||Your prayer has been heard, you obtained {amount}{str(reaction.emoji)}||"
                )
                users.update_one({"user_id": str(ctx.author.id)}, {"$inc": {rewards: amount}})
                await ctx.channel.send(embed=embed)
                return

    @commands.command(aliases=["issue"])
    @commands.is_owner()
    async def issue_frame_rewards(self, ctx):

        await self.frame_automate()
        await ctx.message.delete()

    async def frame_automate(self):

        request = books.find_one({"server": str(primary_id)}, {"_id": 0, "channels": 1})
        spell_spam_id = request["channels"]["spell-spam"]
        spell_spam_channel = self.client.get_channel(int(spell_spam_id))
        guild = spell_spam_channel.guild

        await frame_starlight(guild, spell_spam_channel)
        await asyncio.sleep(1)
        await frame_blazing(guild, spell_spam_channel)

    @commands.command(aliases=["add"])
    @commands.is_owner()
    async def bounty_add_alias(self, ctx, *args):

        name = args[0].replace("_", " ").lower()
        alias = " ".join(args[1::]).replace("_", " ").lower()
        bounty.update_one({"aliases": name}, {"$push": {"aliases": alias}})
        embed = discord.Embed(
            colour=discord.Colour(embed_color),
            title=f"Successfully added {alias} to {name}"
        )
        await ctx.channel.send(embed=embed)

    @commands.command(aliases=["b", "bounty"])
    @commands.guild_only()
    async def bounty_query(self, ctx, *, query):

        if len(query) < 2:
            return

        bounty_search1 = bounty.find_one({"aliases": query.lower()}, {"_id": 0})
        bounty_search2 = bounty.find({"aliases": {"$regex": f"^{query[:2]}"}}, {"_id": 0})

        if bounty_search1 is not None:
            shikigami_profile = shikigamis.find_one({
                "shikigami.name": query.title()}, {
                "shikigami.$.name": 1
            })

            if shikigami_profile is not None:
                image = shikigami_profile["shikigami"][0]["thumbnail"]["pre_evo"]
            else:
                image = ""

            name = bounty_search1["bounty"].title()
            description = ("• " + "\n• ".join(bounty_search1["location"]))
            aliases = bounty_search1["aliases"]
            text = ", ".join(aliases)

            embed = discord.Embed(
                color=ctx.author.colour,
                title=f"Bounty location for {name}:",
                description=description
            )
            embed.set_footer(icon_url=image, text=f"aliases: {text}")
            await ctx.channel.send(embed=embed)

        elif bounty_search2 is not None:
            bounty_list = []
            for result in bounty_search2:
                bounty_list.append(result["bounty"])

            embed = discord.Embed(
                title="No exact results", colour=discord.Colour(embed_color),
                description="But here are the list of shikigamis that match the first two letters"
            )
            embed.add_field(name="Possible queries", value="*{}*".format(", ".join(bounty_list)))
            await ctx.channel.send(embed=embed)

    @commands.command(aliases=["daily"])
    @commands.guild_only()
    async def claim_rewards_daily(self, ctx):
        user = ctx.author
        profile = users.find_one({"user_id": str(user.id)}, {"_id": 0, "daily": 1})

        if profile["daily"] is False:
            await claim_rewards_daily_give(user, ctx)

        elif profile["daily"] is True:
            embed = discord.Embed(
                title="You have collected already today", colour=discord.Colour(embed_color),
                description="Resets everyday at 00:00 EST")
            await ctx.channel.send(embed=embed)

    @commands.command(aliases=["weekly"])
    @commands.guild_only()
    async def claim_rewards_weekly(self, ctx):

        user = ctx.author
        profile = users.find_one({"user_id": str(user.id)}, {"_id": 0, "weekly": 1})

        if profile["weekly"] is False:
            await weekly_give_rewards(user, ctx)

        elif profile["weekly"] is True:
            embed = discord.Embed(
                title="You have collected already this week", colour=discord.Colour(embed_color),
                description="Resets every Monday at 00:00 EST"
            )
            await ctx.channel.send(embed=embed)

    @commands.command(aliases=["profile", "p"])
    @commands.guild_only()
    async def profile_show(self, ctx, *, member: discord.Member = None):

        if member is None:
            await self.profile_post(ctx.author, ctx)

        else:
            await self.profile_post(member, ctx)

    async def profile_generate_frame_image(self, member, achievements):

        achievements_names = []
        for entry in achievements:
            try:
                achievements_names.append(f"{entry['name']}.png")
            except KeyError:
                continue

        list_images = []
        for filename in sorted(os.listdir("./data/achievements")):
            if filename.endswith(".png") and filename in achievements_names:
                list_images.append(f"data/achievements/{filename}")

        images = list(map(Image.open, list_images))

        def get_image_variables(x):
            total_frames = len(x)
            w = 1000
            h = ceil(total_frames / 5) * 200
            return w, h

        width, height = get_image_variables(list_images)
        new_im = Image.new("RGBA", (width, height))

        def get_coordinates(c):
            x = (c * 200 - (ceil(c / 5) - 1) * 1000) - 200
            y = (ceil(c / 5) * 200) - 200
            return x, y

        for index, item in enumerate(images):
            new_im.paste(images[index], (get_coordinates(index + 1)))

        address = f"temp/{member.id}.png"
        new_im.save(address)
        new_photo = discord.File(address, filename=f"{member.id}.png")
        hosting_channel = self.client.get_channel(556032841897607178)
        msg = await hosting_channel.send(file=new_photo)
        attachment_link = msg.attachments[0].url
        return attachment_link

    async def profile_post(self, member, ctx):

        profile = users.find_one({
            "user_id": str(member.id)}, {
            "_id": 0, "SP": 1, "SSR": 1, "SR": 1, "R": 1, "amulets": 1,
            "amulets_spent": 1, "experience": 1, "level": 1, "level_exp_next": 1,
            "jades": 1, "coins": 1, "medals": 1, "realm_ticket": 1, "display": 1, "friendship": 1,
            "encounter_ticket": 1, "friendship_pass": 1, "talisman": 1, "prayers": 1, "achievements": 1, "frame": 1,
            "achievements_count": 1
        })

        ships_count = ships.find({"code": {"$regex": f".*{ctx.author.id}.*"}}).count()
        amulets = profile["amulets"]
        amulets_spent = profile["amulets_spent"]
        exp = profile["experience"]
        level = profile["level"]
        level_exp_next = profile["level_exp_next"]
        jades = profile["jades"]
        coins = profile["coins"]
        medals = profile["medals"]
        realm_ticket = profile["realm_ticket"]
        display = profile["display"]
        friendship_points = profile["friendship"]
        encounter_ticket = profile["encounter_ticket"]
        friendship_pass = profile["friendship_pass"]
        talismans = profile["talisman"]
        prayers = profile["prayers"]
        frame = profile["frame"]
        achievements_count = profile["achievements_count"]
        achievements = profile["achievements"]

        if len(achievements) > achievements_count:
            frame = await self.profile_generate_frame_image(member, achievements)
            users.update_one({"user_id": str(member.id)}, {
                "$set": {
                    "frame": frame, "achievements_count": len(achievements)
                }
            })

        embed = discord.Embed(color=member.colour)

        if display != "None":
            evo = users.find_one({
                "user_id": str(member.id), "shikigami.name": display}, {
                "shikigami.$.name": 1
            })["shikigami"][0]["evolved"]

            thumbnail = shikigamis.find_one({
                "shikigami.name": display}, {
                "shikigami.$.name": 1
            })["shikigami"][0]["thumbnail"][get_evo_link(evo)]

            embed.set_thumbnail(url=thumbnail)

        else:
            embed.set_thumbnail(url=member.avatar_url)

        embed.set_author(
            name=f"{member.display_name}'s profile",
            icon_url=member.avatar_url
        )
        embed.add_field(
            name=":arrow_heading_up: Experience",
            value=f"Level: {level} ({exp:,d}/{level_exp_next:,d})"
        )
        embed.add_field(
            name=f"{e_sp} | {e_ssr} | {e_sr} | {e_r}",
            value=f"{profile['SP']} | {profile['SSR']} | {profile['SR']} | {profile['R']:,d}"
        )
        embed.add_field(
            name=f"{e_a} Amulets",
            value=f"On Hand: {amulets} | Used: {amulets_spent:,d}"
        )
        embed.add_field(
            name=f"💗 | 🎟 | 🎫 | 🚢 | 🙏",
            value=f"{friendship_pass} | {realm_ticket:,d} | {encounter_ticket:,d} | {ships_count} | {prayers}"
        )
        embed.add_field(
            name=f"{e_f} | {e_t} | {e_m} | {e_j} | {e_c}",
            value=f"{friendship_points:,d} | {talismans:,d} | {medals:,d} | {jades:,d} | {coins:,d}"
        )
        msg = await ctx.channel.send(embed=embed)
        await msg.add_reaction("🖼")

        def check(r, u):
            return str(r.emoji) == "🖼" and r.message.id == msg.id and u.bot is False

        try:
            await self.client.wait_for("reaction_add", timeout=30, check=check)
        except asyncio.TimeoutError:
            return
        else:
            embed = discord.Embed(color=member.colour, timestamp=get_timestamp())
            embed.set_author(
                name=f"{member.display_name}'s achievements",
                icon_url=member.avatar_url
            )
            embed.set_image(url=frame)
            embed.set_footer(text="Hall of Frames")
            await msg.edit(embed=embed)

    @commands.command(aliases=["display"])
    @commands.guild_only()
    async def profile_change_display(self, ctx, *, select):

        user = ctx.author
        select_formatted = select.title()

        if select_formatted == "None":
            users.update_one({"user_id": str(user.id)}, {"$set": {"display": select_formatted}})
            await ctx.message.add_reaction("✅")

        elif select_formatted not in pool_all:
            embed = discord.Embed(
                colour=discord.Colour(embed_color),
                title="Invalid shikigami name"
            )
            await ctx.channel.send(embed=embed)

        elif select_formatted in pool_all:
            count = users.count_documents({"user_id": str(user.id), "shikigami.name": select_formatted})

            if count != 1:
                embed = discord.Embed(
                    colour=discord.Colour(embed_color),
                    description=f"{user.mention}, you do not own that shikigami"
                )
                await ctx.channel.send(embed=embed)

            elif count == 1:
                users.update_one({"user_id": str(user.id)}, {"$set": {"display": select_formatted}})
                await ctx.message.add_reaction("✅")

    @commands.command(aliases=["shikigamis", "shikis", "shiki"])
    @commands.guild_only()
    async def shikigami_list_show_collected(self, ctx, arg1, member: discord.Member = None):

        rarity = str(arg1.upper())

        if rarity not in rarities:
            return

        elif member is None:
            await self.shikigami_list_post_collected(ctx.author, rarity, ctx)

        else:
            await self.shikigami_list_post_collected(member, rarity, ctx)

    async def shikigami_list_post_collected(self, member, rarity, ctx):

        user_shikigamis = []
        for entry in users.aggregate([{
            "$match": {
                "user_id": str(member.id)
            }}, {
            "$unwind": {
                "path": "$shikigami"
            }}, {
            "$match": {
                "shikigami.rarity": rarity
            }}, {
            "$project": {
                "_id": 0,
                "shikigami.name": 1,
                "shikigami.owned": 1,
                "shikigami.shards": 1
            }
        }]):
            user_shikigamis.append((
                entry["shikigami"]["name"],
                entry["shikigami"]["owned"],
                entry["shikigami"]["shards"]
            ))

        user_shikigamis_sorted = sorted(user_shikigamis, key=lambda x: x[1], reverse=True)

        formatted_list = []
        for shiki in user_shikigamis_sorted:
            formatted_list.append(f"▫{shiki[0]}, x{shiki[1]}, x{shiki[2]} shards\n")

        await self.shikigami_list_paginate(member, formatted_list, rarity, ctx, "Shikigamis")

    @commands.command(aliases=["uncollected", "unc"])
    @commands.guild_only()
    async def shikigami_list_show_uncollected(self, ctx, arg1, member: discord.Member = None):

        rarity = str(arg1.upper())

        if rarity not in rarities:
            return

        elif member is None:
            await self.shikigami_list_post_uncollected(ctx.author, rarity, ctx)

        else:
            await self.shikigami_list_post_uncollected(member, rarity, ctx)

    async def shikigami_list_post_uncollected(self, member, rarity, ctx):

        user_shikigamis = []
        for entry in users.aggregate([{
            "$match": {
                "user_id": str(member.id)}}, {
            "$unwind": {
                "path": "$shikigami"}}, {
            "$match": {
                "shikigami.rarity": rarity}}, {
            "$project": {
                "_id": 0,
                "shikigami.name": 1,
                "shikigami.owned": 1,
                "shikigami.shards": 1
            }
        }]):
            user_shikigamis.append((
                entry["shikigami"]["name"]
            ))

        pool_rarity_select = []
        for entry in shikigamis.aggregate([{
            "$match": {
                "rarity": rarity}}, {
            "$unwind": {
                    "path": "$shikigami"}}, {
            "$project": {
                    "_id": 0,
                    "shikigami.name": 1
                }
            }
        ]):
            pool_rarity_select.append(entry["shikigami"]["name"])

        uncollected_list = list(set(pool_rarity_select) - set(user_shikigamis))

        formatted_list = []
        for shiki in uncollected_list:
            formatted_list.append(f"▫{shiki}\n")

        await self.shikigami_list_paginate(member, formatted_list, rarity, ctx, "Uncollected shikigamis")

    async def shikigami_list_paginate(self, member, formatted_list, rarity, ctx, author_name):

        page = 1
        max_lines = 10
        page_total = int(len(formatted_list) / max_lines)

        def create_new_embed_page(page_new):
            end = page_new * max_lines
            start = end - max_lines
            embed_new = discord.Embed(color=member.colour, timestamp=get_timestamp())
            embed_new.description = "".join(formatted_list[start:end])
            embed_new.set_author(icon_url=member.avatar_url, name=author_name)
            embed_new.set_footer(
                text=f"Rarity: {rarity.upper()} - Page: {page_new} of {page_total}",
                icon_url="https://i.imgur.com/CSMZAjb.png"
            )
            return embed_new

        msg = await ctx.channel.send(embed=create_new_embed_page(1))
        await msg.add_reaction("⬅")
        await msg.add_reaction("➡")

        def check(r, m):
            return m != self.client.user and r.message.id == msg.id

        while True:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=60, check=check)
            except asyncio.TimeoutError:
                break
            else:
                if str(reaction.emoji) == "➡":
                    page += 1
                elif str(reaction.emoji) == "⬅":
                    page -= 1
                if page == 0:
                    page = page_total
                elif page > page_total:
                    page = 1
                await msg.edit(embed=create_new_embed_page(page))

    @commands.command(aliases=["addshiki"])
    @commands.is_owner()
    async def shikigami_add(self, ctx, *args):

        if len(args) < 5:
            return

        elif len(args) == 5:

            rarity = args[0].upper()
            query = (args[1].replace("_", " ")).title()
            shrine = False

            if args[4] == "shrine":
                shrine = True

            shikigamis.update_one({
                "rarity": rarity}, {
                "$push": {
                    "shikigami": {
                        "name": query,
                        "thumbnail": {
                            "pre_evo": args[2],
                            "evo": args[3]
                        },
                        "shrine": shrine
                    }
                }
            })
            await ctx.message.add_reaction("✅")
        else:
            await ctx.message.add_reaction("❌")

    @commands.command(aliases=["update"])
    @commands.is_owner()
    async def shikigami_update(self, ctx, *args):

        if len(args) == 0:
            return

        elif len(args) == 3:
            query = (args[0].replace("_", " ")).title()
            profile_shikigami = shikigamis.find_one({
                "shikigami.name": query}, {
                "_id": 0,
                "shikigami": {
                    "$elemMatch": {
                        "name": query
                    }}
            })

            try:
                if profile_shikigami["shikigami"][0]["profiler"] != "":
                    await ctx.message.add_reaction("❌")

            except KeyError:
                try:
                    pre_evo = args[1]
                    evo = args[2]
                    profiler = ctx.author.display_name

                    shikigamis.update_one({"shikigami.name": query}, {
                        "$set": {
                            "shikigami.$.thumbnail.pre_evo": pre_evo,
                            "shikigami.$.thumbnail.evo": evo,
                            "shikigami.$.profiler": str(profiler)
                        }
                    })
                except KeyError:
                    await ctx.message.add_reaction("❌")
        else:
            await ctx.message.add_reaction("❌")

    @commands.command(aliases=["evolve", "evo"])
    async def evolve_perform(self, ctx, *args):

        user = ctx.author
        query = (" ".join(args)).title()
        profile_my_shikigami = users.find_one({
            "user_id": str(user.id)}, {
            "_id": 0,
            "shikigami": {
                "$elemMatch": {
                    "name": query
                }}
        })

        if len(query) < 2:
            embed = discord.Embed(
                title="evolve, evo", colour=discord.Colour(embed_color),
                description="perform evolution of owned shikigami")
            embed.add_field(
                name="Mechanics",
                inline=False,
                value="```"
                      "• SP  :: pre-evolved\n"
                      "• SSR :: requires 1 dupe\n"
                      "• SR  :: requires 10 dupes\n"
                      "• R   :: requires 20 dupes"
                      "```"
            )
            embed.add_field(name="Format", value="*`;evolve <shikigami>`*")
            await ctx.channel.send(embed=embed)

        elif profile_my_shikigami == {}:
            embed = discord.Embed(
                title="Invalid shikigami", colour=discord.Colour(embed_color),
                description=f"{user.mention}, I did not find that shikigami nor you have it"
            )
            await ctx.channel.send(embed=embed)

        elif profile_my_shikigami != {}:
            rarity = profile_my_shikigami["shikigami"][0]["rarity"]
            count = profile_my_shikigami["shikigami"][0]["owned"]
            evo = profile_my_shikigami["shikigami"][0]["evolved"]
            await evolve_shikigami(ctx, rarity, evo, user, query, count)

    @commands.command(aliases=["shrine"])
    @commands.guild_only()
    async def shrine_shikigami(self, ctx, arg1="", *, args=""):

        user = ctx.author
        name = args.lower().title()

        def get_talisman_required(x):
            dictionary = {
                "SSR": 1500000,
                "SR": 500000,
                "R": 50000
            }
            return dictionary[x]

        if arg1.lower() not in ["sacrifice", "exchange", "s", "exc"]:
            raise commands.MissingRequiredArgument(ctx.author)

        elif arg1.lower() in ["sacrifice", "s"] and len(args) == 0:
            embed = discord.Embed(
                title="shrine sacrifice, shrine s", colour=discord.Colour(embed_color),
                description="sacrifice your shikigamis to the shrine in exchange for talismans"
            )
            embed.add_field(
                name="Rarity :: Talisman",
                value="```"
                      "SP     ::  15,000\n"
                      "SSR    ::  10,000\n"
                      "SR     ::     250\n"
                      "R      ::      50\n"
                      "```",
                inline=False
            )
            embed.add_field(
                name="Format",
                value="*`;shrine s <shikigami>`*"
            )
            await ctx.channel.send(embed=embed)

        elif arg1.lower() in ["exchange", "exc"] and len(args) == 0:
            embed = discord.Embed(
                title="shrine exchange, shrine exc", colour=discord.Colour(embed_color),
                description="exchange your talismans for exclusive shikigamis"
            )
            embed.add_field(
                name="Shikigami :: Talisman",
                value="```"
                      "Juzu          ::     50,000\n"
                      "Usagi         ::     50,000\n"
                      "Tenjo Kudari  ::     50,000\n"
                      "Mannendake    ::    500,000\n"
                      "Jinmenju      ::    500,000\n"
                      "Kainin        ::    500,000\n"
                      "Ryomen        ::  1,500,000"
                      "```",
                inline=False
            )
            embed.add_field(
                name="Formats",
                value="*`;shrine exc <shikigami>`*"
            )
            await ctx.channel.send(embed=embed)

        elif arg1.lower() in ["sacrifice", "s"] and name not in pool_all:
            embed = discord.Embed(
                title="Invalid shikigami name", colour=discord.Colour(embed_color),
                description="use *`;shikis`* to get the list of your shikigamis"
            )
            await ctx.channel.send(embed=embed)

        elif arg1.lower() in ["exchange", "exc"] and name not in shrinable_shikigamis:
            embed = discord.Embed(
                title="Invalid shikigami name", colour=discord.Colour(embed_color),
                description="use *`;shrine`* to check the list of valid shikigamis"
            )
            await ctx.channel.send(embed=embed)

        elif arg1.lower() in ["sacrifice", "s"] and name in pool_all:

            request = users.find_one({
                "user_id": str(user.id), "shikigami.name": name}, {
                "_id": 0, "shikigami.$.name": 1
            })
            count_shikigami = request["shikigami"][0]["owned"]
            rarity = request["shikigami"][0]["rarity"]
            talismans = get_talisman_acquire(rarity)

            def check(m):
                try:
                    int(m.content)
                    return m.author == ctx.author and m.channel == ctx.channel
                except TypeError:
                    return
                except ValueError:
                    return

            try:
                embed = discord.Embed(
                    colour=user.colour,
                    title=f"Specify amount of {name} to sacrifice",
                    description=f"{user.mention}, you currently have {count_shikigami:,d} of that shikigami"
                )
                await ctx.channel.send(embed=embed)
                answer = await self.client.wait_for("message", timeout=15, check=check)

            except asyncio.TimeoutError:
                embed = discord.Embed(
                    title="Invalid amount", colour=user.colour,
                    description=f"{user.mention}, that is not a valid number"
                )
                await ctx.channel.send(embed=embed)

            else:
                request_shrine = int(answer.content)
                if count_shikigami >= request_shrine:
                    final_talismans = talismans * request_shrine
                    users.update_one({
                        "user_id": str(user.id),
                        "shikigami.name": name}, {
                        "$inc": {
                            "shikigami.$.owned": - request_shrine,
                            "talisman": final_talismans,
                            f"{rarity}": - request_shrine
                        }
                    })
                    embed = discord.Embed(
                        title="Confirmation sacrifice", colour=user.colour,
                        description=f"{user.mention}, you sacrificed your {name} for {final_talismans:,d}{e_t}"
                    )
                    await ctx.channel.send(embed=embed)

                else:
                    embed = discord.Embed(
                        title="Insufficient shikigamis", colour=user.colour,
                        description=f"{user.mention}, you do not have that amount of shikigamis"
                    )
                    await ctx.channel.send(embed=embed)

        elif arg1.lower() in ["exchange", "exc"] and name in shrinable_shikigamis:

            rarity = shikigamis.find_one({"shikigami.name": name}, {"_id": 0, "rarity": 1})["rarity"]
            talisman = users.find_one({"user_id": str(user.id)}, {"_id": 0, "talisman": 1})["talisman"]
            required_talisman = get_talisman_required(rarity)

            if talisman >= required_talisman:
                embed = discord.Embed(
                    title="Exchange confirmation", colour=discord.Colour(embed_color),
                    description=f"{user.mention}, confirm exchange of {required_talisman:,d}{e_t} for a {name}"
                )
                confirm_ = await ctx.channel.send(embed=embed)
                await confirm_.add_reaction("✅")

                def check(r, u):
                    return u == ctx.author and str(r.emoji) == "✅"

                try:
                    await self.client.wait_for("reaction_add", timeout=10.0, check=check)
                except asyncio.TimeoutError:
                    embed = discord.Embed(
                        title="Timeout!", colour=discord.Colour(embed_color),
                        description=f"{ctx.author.mention}, you did not confirm the {e_t} exchange"
                    )
                    await ctx.channel.send(embed=embed)
                else:
                    query = users.find_one({
                        "user_id": str(user.id),
                        "shikigami.name": name}, {
                        "_id": 0, "shikigami.$": 1
                    })

                    if query is None:
                        users.update_one({
                            "user_id": str(user.id)}, {
                            "$push": {
                                "shikigami": {
                                    "name": name,
                                    "rarity": rarity,
                                    "grade": 1,
                                    "owned": 0,
                                    "evolved": "False",
                                    "shards": 0
                                }
                            }
                        })

                    users.update_one({
                        "user_id": str(user.id),
                        "shikigami.name": name}, {
                        "$inc": {
                            "shikigami.$.owned": 1,
                            "talisman": - required_talisman,
                            f"{rarity}": 1
                        }
                    })
                    embed = discord.Embed(
                        title="Exchange success!", colour=discord.Colour(embed_color),
                        description=f"{ctx.author.mention}, acquired {name} for {required_talisman:,d}{e_t}"
                    )
                    await ctx.channel.send(embed=embed)

            elif talisman < required_talisman:
                embed = discord.Embed(
                    title="Insufficient talisman", colour=discord.Colour(embed_color),
                    description=f"{user.mention}, shrine shikigamis to obtain more. "
                                f"Lacks {required_talisman - talisman:,d}{e_t}"
                )
                await ctx.channel.send(embed=embed)


def setup(client):
    client.add_cog(Economy(client))
