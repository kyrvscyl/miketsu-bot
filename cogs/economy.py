"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import asyncio
import os

import discord
from discord.ext import commands

from cogs.error import logging, get_f
from cogs.mongo.db import users, daily, shikigami, compensation, bounty
from cogs.startup import emoji_m, emoji_j, emoji_c, emoji_f, emoji_a
from cogs.summon import pool_r, pool_sp, pool_sr, pool_ssr

file = os.path.basename(__file__)[:-3:]

pool_all = []
pool_all.extend(pool_r)
pool_all.extend(pool_sp)
pool_all.extend(pool_sr)
pool_all.extend(pool_ssr)


def get_evo_link(evolution):
    key = {
        "True": "evo",
        "False": "pre_evo"
    }
    return key[evolution]


async def daily_give_rewards(user, ctx):

    daily.update_one({"key": "daily"}, {
        "$set": {
            f"{user.id}.rewards": "claimed",
            f"{user.id}.encounter_pass": 4,
            f"{user.id}.friendship_pass": 3
        }
    })
    users.update_one({"user_id": str(user.id)}, {
        "$inc": {
            "jades": 50,
            "coins": 25000,
            "realm_ticket": 3
        }
    })
    embed = discord.Embed(
        color=ctx.author.colour,
        title=":gift: Daily Rewards",
        description=f"A box containing 50{emoji_j}, 25,000{emoji_c}, 3🎟, 4🎫, 5{emoji_f}"
    )
    embed.set_footer(
        text=f"Claimed by {user.display_name}",
        icon_url=user.avatar_url
    )
    await ctx.channel.send(embed=embed)


async def weekly_give_rewards(user, ctx):

    daily.update_one({"key": "weekly"}, {
        "$set": {
            f"{user.id}.rewards": "claimed"
        }
    })
    users.update_one({"user_id": str(user.id)}, {
        "$inc": {
            "jades": 750,
            "coins": 150000,
            "amulets": 10
        }
    })

    embed = discord.Embed(
        color=ctx.author.colour,
        title=":gift: Weekly Rewards",
        description=f"A mythical box containing 750{emoji_j}, "
        f"150,000{emoji_c}, and 10{emoji_a}"
    )
    embed.set_footer(
        text=f"Claimed by {user.display_name}",
        icon_url=user.avatar_url
    )
    await ctx.channel.send(embed=embed)


async def profile_post(member, ctx):

    profile = users.find_one({
        "user_id": str(member.id)}, {
        "_id": 0, "SP": 1, "SSR": 1, "SR": 1, "R": 1, "amulets": 1,
        "amulets_spent": 1, "experience": 1, "level": 1, "level_exp_next": 1,
        "jades": 1, "coins": 1, "medals": 1, "realm_ticket": 1, "display": 1
    })

    try:
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

    except KeyError:
        logging(file, get_f(), "KeyError")
        return

    embed = discord.Embed(color=member.colour)

    if display != "None":
        evo = users.find_one({
            "user_id": str(member.id), "shikigami.name": display}, {
            "shikigami.$.name": 1
        })["shikigami"][0]["evolved"]

        thumbnail = shikigami.find_one({
            "shikigami.name": display}, {
            "shikigami.$.name": 1
        })["shikigami"][0]["thumbnail"][get_evo_link(evo)]

        embed.set_thumbnail(url=thumbnail)

    if display == "None":
        embed.set_thumbnail(url=member.avatar_url)
        embed.set_footer(
            text="use ;display to change thumbnail to your preferred shikigami"
        )

    embed.set_author(
        name=f"{member.display_name}\'s profile",
        icon_url=member.avatar_url
    )
    embed.add_field(
        name=":arrow_heading_up: Experience",
        value=f"Level: {level} ({exp}/{level_exp_next})"
    )
    embed.add_field(
        name="SP | SSR | SR | R",
        value=f"{profile['SP']} | {profile['SSR']} | {profile['SR']} | {profile['R']}"
    )
    embed.add_field(
        name=f"{emoji_a} Amulets",
        value=f"On Hand: {amulets} | Used: {amulets_spent}"
    )
    embed.add_field(
        name=f"🎟 | {emoji_m} | {emoji_j} | {emoji_c}",
        value=f"{realm_ticket} | {medals} | {jades:,d} | {coins:,d}",
    )
    await ctx.channel.send(embed=embed)


async def shikigami_my_post(user, query, ctx):

    profile_my_shikigami = users.find_one({
        "user_id": str(user.id)}, {
        "_id": 0, "shikigami": {
            "$elemMatch": {
                "name": query
            }}
    })
    try:
        count = profile_my_shikigami["shikigami"][0]["owned"]
        grade = profile_my_shikigami["shikigami"][0]["grade"]
        evo = profile_my_shikigami["shikigami"][0]["evolved"]
        rarity = profile_my_shikigami["shikigami"][0]["rarity"]

        profile_shikigami = shikigami.find_one({
            "rarity": rarity}, {
            "_id": 0, "shikigami": {
                "$elemMatch": {
                    "name": query
                }}
        })
        normal = profile_shikigami["shikigami"][0]["skills"]["normal"]
        special = profile_shikigami["shikigami"][0]["skills"]["special"]

    except KeyError:
        await ctx.channel.send(f"{user.mention}, that shikigami does not exist nor you have it")
        return

    if evo == "True":
        thumbnail = profile_shikigami["shikigami"][0]["thumbnail"]["evo"]
        grade_star = ":star2:" * grade

    else:
        thumbnail = profile_shikigami["shikigami"][0]["thumbnail"]["pre_evo"]
        grade_star = ":star:" * grade

    embed = discord.Embed(
        color=user.colour,
        description=f"Grade: {grade_star}\n\nNormal: {normal}\nSpecial: {special}"
    )
    embed.set_thumbnail(url=thumbnail)
    embed.set_author(
        icon_url=user.avatar_url,
        name=f"{ctx.author.display_name}\"s {query}"
    )
    embed.set_footer(text=f"shikigami count: {count}")
    await ctx.channel.send(embed=embed)


async def evolve_shikigami(ctx, rarity, evo, user, query, count):

    def get_requirement(r):
        key = {
            "R": 21,
            "SR": 11,
            "SSR": 2,
            "SP": 0
        }
        return key[r]

    if rarity == "SP":
        await ctx.channel.send("{user.mention}, SPs are pre-evolved")

    elif evo == "True":
        await ctx.channel.send(f"{user.mention}, your {query} is already evolved.")

    elif evo == "False":

        rarity_count = get_requirement(rarity)
        if count >= rarity_count:

            users.update_one({
                "user_id": str(user.id), "shikigami.name": query}, {
                "$inc": {
                    "shikigami.$.owned": -(rarity_count - 1)
                }
            })
            users.update_one({
                "user_id": str(user.id),
                "shikigami.name": query}, {
                "$set": {
                    "shikigami.$.evolved": "True"
                }
            })

            await ctx.channel.send(f"{user.mention}, you have evolved your {query}!")

        elif count == 0:
            await ctx.channel.send(f"{user.mention}, you do not own that shikigami!")

        elif count <= (get_requirement(rarity) - 1):
            msg = f"{user.mention}, you lack {rarity_count - count} more {query} dupes to evolve yours"
            await ctx.channel.send(msg)


class Economy(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(aliases=["add"])
    @commands.is_owner()
    async def bounty_add_alias(self, ctx, *args):

        name = args[0].replace("_", " ").lower()
        alias = " ".join(args[1::]).replace("_", " ").lower()
        bounty.update_one({"aliases": name}, {"$push": {"aliases": alias}})
        await ctx.channel.send(f"Successfully added {alias} to {name}")


    @commands.command(aliases=["b"])
    @commands.guild_only()
    async def bounty(self, ctx, *, query):

        profile = bounty.find_one({"aliases": query.lower()}, {"_id": 0})

        if profile is not None:
            shikigami_profile = shikigami.find_one({
                "shikigami.name": query.title()}, {
                "shikigami.$.name": 1
            })

            if shikigami_profile is not None:
                image = shikigami_profile["shikigami"][0]["thumbnail"]["pre_evo"]
            else:
                image = ""

            name = profile["bounty"].title()
            description = ("• " + "\n• ".join(profile["location"]))
            aliases = profile["aliases"]
            text = ", ".join(aliases)

            embed = discord.Embed(
                color=ctx.author.colour,
                title=f"Bounty location for {name}:",
                description=description
            )
            embed.set_footer(icon_url=image, text=f"aliases: {text}")
            await ctx.channel.send(embed=embed)

        else:
            await ctx.channel.send("No results. If you believe this should have results, use command `;suggest`")


    @commands.command(aliases=["dailies", "day"])
    @commands.guild_only()
    async def daily(self, ctx):
        user = ctx.author
        profile = daily.find_one({"key": "daily"}, {"_id": 0, f"{user.id}": 1})

        if profile == {}:
            await daily_give_rewards(user, ctx)

        elif profile[str(user.id)]["rewards"] == "unclaimed":
            await daily_give_rewards(user, ctx)

        elif profile[str(user.id)]["rewards"] == "claimed":
            await ctx.channel.send("You have collected already today. Resets at 00:00 EST")


    @commands.command(aliases=["weeklies"])
    @commands.guild_only()
    async def weekly(self, ctx):

        user = ctx.author
        profile = daily.find_one({"key": "weekly"}, {"_id": 0, f"{user.id}": 1})

        if profile == {}:
            await weekly_give_rewards(user, ctx)

        elif profile[str(user.id)]["rewards"] == "unclaimed":
            await weekly_give_rewards(user, ctx)

        elif profile[str(user.id)]["rewards"] == "claimed":
            await ctx.channel.send("You have collected already this week. Resets at 00:00 EST Monday")


    @commands.command(aliases=["compensate"])
    @commands.guild_only()
    async def compensation(self, ctx):
        user = ctx.author
        profile = compensation.find_one({}, {"_id": 0, f"{user.id}": 1})

        if profile == {}:
            await ctx.channel.send(f"{ctx.author.mention}, you are not eligible for this compensation")

        elif profile != {}:
            if profile[str(user.id)] == "unclaimed":

                users.update_one({"user_id": str(user.id)}, {
                    "$inc": {
                        "jades": 3000
                    }
                })
                compensation.update_one({f"{user.id}": "unclaimed"}, {
                    "$set": {
                        f"{user.id}": "claimed"
                    }
                })

                msg = f"You have been compensated with 3000{emoji_j} due to recent data roll back."
                await ctx.channel.send(msg)

            elif profile[str(user.id)] == "claimed":
                await ctx.channel.send(f"{ctx.author.mention}, you can only claim this once!")


    @commands.command(aliases=["p"])
    @commands.guild_only()
    async def profile(self, ctx, *, member: discord.Member = None):

        if member is None:
            await profile_post(ctx.author, ctx)

        else:
            await profile_post(member, ctx)


    @commands.command(aliases=["display"])
    @commands.guild_only()
    async def change_display(self, ctx, *, select):

        user = ctx.author
        select_formatted = select.title()

        if select_formatted == "None":
            users.update_one({"user_id": str(user.id)}, {"$set": {"display": select_formatted}})
            await ctx.message.add_reaction("✅")

        elif select_formatted not in pool_all:
            await ctx.channel.send("Invalid shikigami name")

        elif select_formatted in pool_all:
            count = users.count_documents({"user_id": str(user.id), "shikigami.name": select_formatted})

            if count != 1:
                await ctx.channel.send("You do not own that shikigami")

            elif count == 1:
                users.update_one({"user_id": str(user.id)}, {"$set": {"display": select_formatted}})
                await ctx.message.add_reaction("✅")


    @commands.command(aliases=["list"])
    @commands.guild_only()
    async def shikigami_list(self, ctx, arg1, user: discord.User = None):
        rarity = str(arg1.upper())

        if user is None:
            await self.shikigami_list_post(ctx.author, rarity, ctx)

        else:
            await self.shikigami_list_post(user, rarity, ctx)


    async def shikigami_list_post(self, user, rarity, ctx):
        entries = users.aggregate([
            {
                '$match': {
                    'user_id': str(user.id)
                }
            }, {
                '$unwind': {
                    'path': '$shikigami'
                }
            }, {
                '$match': {
                    'shikigami.rarity': rarity
                }
            }, {
                '$project': {
                    '_id': 0,
                    'shikigami.name': 1,
                    'shikigami.owned': 1,
                    'shikigami.rarity': rarity
                }
            }
        ])

        user_shikigamis = []
        for entry in entries:
            user_shikigamis.append((entry["shikigami"]["name"], entry["shikigami"]["owned"]))

        user_shikigamis_sorted = sorted(user_shikigamis, key=lambda x: x[1], reverse=True)

        description = []
        for shiki in user_shikigamis_sorted:
            description.append(f":white_small_square:{shiki[0]}, x{shiki[1]}\n")

        user_shikigamis_page = 1
        icon_url = "https://i.imgur.com/CSMZAjb.png"

        embed = discord.Embed(
            color=user.colour,
            description="".join(description[0:10])
        )
        embed.set_author(
            icon_url=user.avatar_url,
            name=f"{user.display_name}'s Shikigamis"
        )
        embed.set_footer(
            text=f"Rarity: {rarity.upper()} - Page: {user_shikigamis_page}",
            icon_url=icon_url
        )

        msg = await ctx.channel.send(embed=embed)
        await msg.add_reaction("⬅")
        await msg.add_reaction("➡")

        def check(r, m):
            return m != self.client.user and r.message.id == msg.id

        while True:
            try:
                timeout = 30
                reaction, member = await self.client.wait_for("reaction_add", timeout=timeout, check=check)

                if str(reaction.emoji) == "➡":
                    user_shikigamis_page += 1
                if str(reaction.emoji) == "⬅":
                    user_shikigamis_page -= 1
                    if user_shikigamis_page == 0:
                        user_shikigamis_page = 1

                start = user_shikigamis_page * 10 - 10
                end = user_shikigamis_page * 10

                embed = discord.Embed(
                    color=user.colour,
                    description="".join(description[start:end])
                )
                embed.set_author(
                    icon_url=user.avatar_url,
                    name=f"{user.display_name}'s Shikigamis"
                )
                embed.set_footer(
                    text=f"Rarity: {rarity.upper()} - Page: {user_shikigamis_page}",
                    icon_url=icon_url
                )
                await msg.edit(embed=embed)
                break

            except asyncio.TimeoutError:
                break


    @commands.command(aliases=["my"])
    @commands.guild_only()
    async def shikigami_my(self, ctx, *args):
        query = (" ".join(args)).title()
        user = ctx.author

        profile_my_shikigami = users.find_one({
            "user_id": str(user.id)}, {
            "_id": 0, "shikigami": {
                "$elemMatch": {
                    "name": query
                }}
        })

        try:
            count = profile_my_shikigami["shikigami"][0]["owned"]
            grade = profile_my_shikigami["shikigami"][0]["grade"]
            evo = profile_my_shikigami["shikigami"][0]["evolved"]
            rarity = profile_my_shikigami["shikigami"][0]["rarity"]

            profile_shikigami = shikigami.find_one({
                "rarity": rarity}, {
                "_id": 0, "shikigami": {
                    "$elemMatch": {
                        "name": query
                    }}
            })

            normal = profile_shikigami["shikigami"][0]["skills"]["normal"]
            special = profile_shikigami["shikigami"][0]["skills"]["special"]

        except KeyError:
            await ctx.channel.send(f"{user.mention}, that shikigami does not exist nor you have it")
            return

        if evo == "True":
            thumbnail = profile_shikigami["shikigami"][0]["thumbnail"]["evo"]
            grade_star = ":star2:" * grade

        else:
            thumbnail = profile_shikigami["shikigami"][0]["thumbnail"]["pre_evo"]
            grade_star = ":star:" * grade

        embed = discord.Embed(
            color=user.colour,
            description=f"Grade: {grade_star}\n\nNormal: {normal}\nSpecial: {special}"
        )
        embed.set_thumbnail(url=thumbnail)
        embed.set_author(
            icon_url=user.avatar_url,
            name=f"{ctx.author.display_name}\"s {query}"
        )
        embed.set_footer(text=f"shikigami count: {count}")
        await ctx.channel.send(embed=embed)


    @commands.command(aliases=["addshiki"])
    @commands.is_owner()
    async def shikigami_add(self, ctx, *args):

        if len(args) < 4:
            return

        elif len(args) == 4:

            rarity = args[0].upper()
            query = (args[1].replace("_", " ")).title()

            profile = {
                "name": query,
                "skills": {
                    "normal": "",
                    "special": ""
                },
                "thumbnail": {
                    "pre_evo": args[2],
                    "evo": args[3]
                },
                "specialty": "None"
            }

            shikigami.update_one({
                "rarity": rarity}, {
                "$push": {"shikigami": profile}
            })
            await ctx.message.add_reaction("✅")

        else:
            await ctx.channel.send("Try again. Lacks input")


    @commands.command(aliases=["update"])
    @commands.is_owner()
    async def shikigami_update(self, ctx, *args):

        if len(args) == 0:
            return

        elif len(args) == 3:

            query = (args[0].replace("_", " ")).title()
            user = ctx.author

            profile_shikigami = shikigami.find_one({
                "shikigami.name": query}, {
                "_id": 0,
                "shikigami": {
                    "$elemMatch": {
                        "name": query
                    }}
            })

            try:
                if profile_shikigami["shikigami"][0]["profiler"] != "":
                    await ctx.channel.send("This shikigami has profile already. Try others.")

            except KeyError:
                try:
                    pre_evo = args[1]
                    evo = args[2]
                    profiler = ctx.author.display_name

                    shikigami.update_one({"shikigami.name": query}, {
                        "$set": {
                            "shikigami.$.thumbnail.pre_evo": pre_evo,
                            "shikigami.$.thumbnail.evo": evo,
                            "shikigami.$.profiler": str(profiler)
                        }
                    })
                    users.update_one({"user_id": str(user.id)}, {"$inc": {"jades": 100}})
                    await ctx.channel.send(f"{user.mention}, you have earned 100{emoji_j}")

                except KeyError:
                    await ctx.channel.send("Try again. Wrong format")

        else:
            await ctx.channel.send("Try again. Lacks input")


    @commands.command(aliases=["evo"])
    async def evolve(self, ctx, *args):

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

        if query == "":
            embed = discord.Embed(
                color=user.colour,
                title="💎 Shikigami Evolution",
                description="• SP - pre-evolved\n"
                            "• SSR - requires 1 dupe of the same kind\n"
                            "• SR - requires 10 dupes of the same kind\n"
                            "• R - requires 20 dupes of the same kind\n\n"
                            "Use `;evolve <shikigami>` to perform evolution"
            )
            embed.set_thumbnail(url=self.client.user.avatar_url)
            await ctx.channel.send(embed=embed)

        elif profile_my_shikigami == {}:
            await ctx.channel.send(f"{user.mention}, I did not find that shikigami nor you have it")

        elif profile_my_shikigami != {}:
            rarity = profile_my_shikigami["shikigami"][0]["rarity"]
            count = profile_my_shikigami["shikigami"][0]["owned"]
            evo = profile_my_shikigami["shikigami"][0]["evolved"]
            await evolve_shikigami(ctx, rarity, evo, user, query, count)


def setup(client):
    client.add_cog(Economy(client))
