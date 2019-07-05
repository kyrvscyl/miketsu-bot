"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import asyncio

import discord
from discord.ext import commands

from cogs.mongo.db import users, daily, shikigami, compensation
from cogs.summon import pool_r, pool_sp, pool_sr, pool_ssr

# Global Variables
emoji_m = "<:medal:573071121545560064>"
emoji_j = "<:jade:555630314282811412>"
emoji_c = "<:coin:573071121495097344>"
emoji_f = "<:friendship:555630314056318979>"
emoji_a = "<:amulet:573071120685596682>"

pool_all = []
pool_all.extend(pool_r)
pool_all.extend(pool_sp)
pool_all.extend(pool_sr)
pool_all.extend(pool_ssr)


# noinspection PyMethodMayBeStatic,PyShadowingNames
class Economy(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(aliases=["dailies"])
    async def daily(self, ctx):
        user = ctx.author
        profile = daily.find_one({"key": "daily"}, {"_id": 0, f"{user.id}": 1})

        if profile == {}:
            await self.daily_give_rewards(user, ctx)

        elif profile[str(user.id)]["rewards"] == "unclaimed":
            await self.daily_give_rewards(user, ctx)

        elif profile[str(user.id)]["rewards"] == "claimed":
            await ctx.channel.send("You have collected already today. Resets at 00:00 EST")

    async def daily_give_rewards(self, user, ctx):

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
            description=f"A box containing 50{emoji_j}, 25,000{emoji_c}, 3:tickets:, 4:ticket:, 5{emoji_f}"
        )
        embed.set_footer(
            text=f"Claimed by {user.name}",
            icon_url=user.avatar_url
        )

        await ctx.channel.send(embed=embed)

    @commands.command(aliases=["weeklies"])
    async def weekly(self, ctx):
        user = ctx.author
        profile = daily.find_one({"key": "weekly"}, {"_id": 0, f"{user.id}": 1})

        if profile == {}:
            await self.weekly_give_rewards(user, ctx)

        elif profile[str(user.id)]["rewards"] == "unclaimed":
            await self.weekly_give_rewards(user, ctx)

        elif profile[str(user.id)]["rewards"] == "claimed":
            await ctx.channel.send("You have collected already this week. Resets at 00:00 EST Monday")

    async def weekly_give_rewards(self, user, ctx):
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
            text=f"Claimed by {user.name}",
            icon_url=user.avatar_url
        )

        await ctx.channel.send(embed=embed)

    @commands.command(aliases=["compensate"])
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

    # noinspection PyTypeChecker
    @commands.command(aliases=["p"])
    async def profile(self, ctx, *, user: discord.Member = None):

        if user is None:
            await self.profile_post(ctx.author, ctx)

        else:
            await self.profile_post(user, ctx)

    @commands.command(aliases=["display"])
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

    async def profile_post(self, user, ctx):

        try:
            profile = users.find_one({
                "user_id": str(user.id)}, {
                "_id": 0, "SP": 1, "SSR": 1, "SR": 1, "R": 1, "amulets": 1,
                "amulets_spent": 1, "experience": 1, "level": 1, "level_exp_next": 1,
                "jades": 1, "coins": 1, "medals": 1, "realm_ticket": 1, "display": 1
            })

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

            embed = discord.Embed(color=user.colour)

            if display != "None":
                evo = users.find_one({
                    "user_id": str(user.id), "shikigami.name": display}, {
                    "shikigami.$.name": 1
                })["shikigami"][0]["evolved"]

                def get_evo_link(evo):
                    key = {
                        "True": "evo",
                        "False": "pre_evo"
                    }
                    return key[evo]

                thumbnail = shikigami.find_one({
                    "shikigami.name": display}, {
                    "shikigami.$.name": 1
                })["shikigami"][0]["thumbnail"][get_evo_link(evo)]

                embed.set_thumbnail(url=thumbnail)

            if display == "None":
                embed.set_thumbnail(url=user.avatar_url)
                embed.set_footer(
                    text="use ;display to change thumbnail to your preferred shikigami"
                )

            embed.set_author(
                name=f"{user.name}\'s profile",
                icon_url=user.avatar_url
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
                name=f":tickets: | {emoji_m} | {emoji_j} | {emoji_c}",
                value=f"{realm_ticket} | {medals} | {jades:,d} | {coins:,d}",
            )

            await ctx.channel.send(embed=embed)

        except KeyError:
            return

    @commands.command(aliases=["list"])
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
        for shikigami in user_shikigamis_sorted:
            description.append(f":white_small_square:{shikigami[0]}, x{shikigami[1]}\n")

        user_shikigamis_page = 1
        icon_url = "https://i.imgur.com/CSMZAjb.png"

        embed = discord.Embed(
            color=user.colour,
            description="".join(description[0:10])
        )
        embed.set_author(
            icon_url=user.avatar_url,
            name=f"{user.name}'s Shikigamis"
        )
        embed.set_footer(
            text=f"Rarity: {rarity.upper()} - Page: {user_shikigamis_page}",
            icon_url=icon_url
        )

        msg = await ctx.channel.send(embed=embed)
        await msg.add_reaction("⬅")
        await msg.add_reaction("➡")

        def check(reaction, member):
            return member != self.client.user and reaction.message.id == msg.id

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
                    name=f"{user.name}'s Shikigamis"
                )
                embed.set_footer(
                    text=f"Rarity: {rarity.upper()} - Page: {user_shikigamis_page}",
                    icon_url=icon_url
                )
                await msg.edit(embed=embed)

            except asyncio.TimeoutError:
                return

    @commands.command(aliases=["my"])
    async def shikigami_my(self, ctx, *args):
        query = (" ".join(args)).title()

        await self.shikigami_my_post(ctx.author, query, ctx)

    # noinspection PyUnboundLocalVariable
    async def shikigami_my_post(self, user, query, ctx):

        try:
            profile_my_shikigami = users.find_one({
                "user_id": str(user.id)}, {
                "_id": 0, "shikigami": {
                    "$elemMatch": {
                        "name": query
                    }}
            })

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
                name=f"{ctx.author.name}\"s {query}"
            )
            embed.set_footer(text=f"shikigami count: {count}")

            await ctx.channel.send(embed=embed)

        except KeyError:
            await ctx.channel.send(f"{user.mention}, that shikigami does not exist nor you have it")

    @commands.command(aliases=["shiki", "shikigami"])
    async def shikigami_info(self, ctx, *args):
        query = (" ".join(args)).title()

        profile_shikigami = shikigami.find_one({
            "shikigami.name": query}, {
            "_id": 0,
            "shikigami": {
                "$elemMatch": {
                    "name": query
                }}
        })

        normal = profile_shikigami["shikigami"][0]["skills"]["normal"]
        special = profile_shikigami["shikigami"][0]["skills"]["special"]
        specialty = profile_shikigami["shikigami"][0]["specialty"]
        pre_evo = profile_shikigami["shikigami"][0]["thumbnail"]["pre_evo"]
        evo = profile_shikigami["shikigami"][0]["thumbnail"]["evo"]

        embed = discord.Embed(
            color=ctx.author.colour,
            description=f"**Skills:**\nNormal: {normal}\nSpecial: {special}\n\nSpecialty: {specialty}"
        )
        embed.set_thumbnail(url=evo)
        embed.set_author(
            name=f"{query}",
            icon_url=pre_evo
        )

        await ctx.channel.send(embed=embed)

    @commands.command(aliases=["update"])
    async def shikigami_update(self, ctx, *args):

        if len(args) == 0:

            embed = discord.Embed(
                color=ctx.author.colour,
                description="Refer to sample correct command format:\n\n"
                            "`;update <rarity> <shikigami> <normal_skill> <special_skill> "
                            "<pre-evo image link> <evo image link>`\n\nFor every <> replace spaces "
                            "with underscore:\ne.g. inferno ibaraki -> inferno_ibaraki\n\n"
                            "Grants 100{emoji_j} per shikigami update per user"
            )
            embed.set_thumbnail(url=self.client.user.avatar_url)

            await ctx.channel.send(embed=embed)

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
                    profiler = ctx.author.name

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
                title=":gem: Shikigami Evolution",
                description=":small_orange_diamond:SP - pre-evolved\n:small_orange_diamond:SSR - "
                            "requires 1 dupe of the same kind\n:small_orange_diamond:SR - requires "
                            "10 dupes of the same kind\n:small_orange_diamond:R - requires 20 dupes "
                            "of the same kind\n\nUse `;evolve <shikigami>` to perform evolution"
            )
            embed.set_thumbnail(url=self.client.user.avatar_url)

            await ctx.channel.send(embed=embed)

        elif profile_my_shikigami == {}:
            await ctx.channel.send(f"{user.mention}, I did not find that shikigami nor you have it")

        elif profile_my_shikigami != {}:

            rarity = profile_my_shikigami["shikigami"][0]["rarity"]
            count = profile_my_shikigami["shikigami"][0]["owned"]
            evo = profile_my_shikigami["shikigami"][0]["evolved"]

            await self.evolve_shikigami(ctx, rarity, evo, user, query, count)

    async def evolve_shikigami(self, ctx, rarity, evo, user, query, count):

        def get_requirement(rarity):
            key = {
                "R": 21,
                "SR": 11,
                "SSR": 2,
                "SP": 0
            }
            return key[rarity]

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


def setup(client):
    client.add_cog(Economy(client))
