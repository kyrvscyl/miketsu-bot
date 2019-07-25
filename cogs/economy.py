"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import asyncio
import random

import discord
from discord.ext import commands

from cogs.mongo.db import users, shikigami, bounty, friendship, books, streak
from cogs.startup import \
    emoji_m, emoji_j, emoji_c, emoji_f, emoji_a, pluralize, emoji_sp, emoji_ssr, emoji_sr, emoji_r
from cogs.summon import pool_r, pool_sp, pool_sr, pool_ssr

pool_all = []
pool_all.extend(pool_r)
pool_all.extend(pool_sp)
pool_all.extend(pool_sr)
pool_all.extend(pool_ssr)

adverb = ["deliberately", "forcefully", "unknowingly", "accidentally", "dishonestly"]
verb = ["snatched", "stole", "took", "looted", "shoplifted", "embezzled"]
noun = ["custody", "care", "control", "ownership"]
comment = ["Sneaky!", "Gruesome!", "Madness!"]

spell_spam_ids = []
for document in books.find({}, {"_id": 0, "channels.spell-spam": 1}):
    try:
        spell_spam_ids.append(document["channels"]["spell-spam"])
    except KeyError:
        continue


def get_evo_link(evolution):
    key = {
        "True": "evo",
        "False": "pre_evo"
    }
    return key[evolution]


def get_requirement(r):
    key = {
        "R": 21,
        "SR": 11,
        "SSR": 2,
        "SP": 0
    }
    return key[r]


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
        description=f"A box containing 5 💗, 50{emoji_j}, 25k{emoji_c}, 3 🎟, 4 🎫"
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
        description=f"A mythical box containing 750{emoji_j}, 150k{emoji_c}, and 10{emoji_a}"
    )
    embed.set_footer(text=f"Opened by {user.display_name}", icon_url=user.avatar_url)
    await ctx.channel.send(embed=embed)


async def profile_post(member, ctx):

    profile = users.find_one({
        "user_id": str(member.id)}, {
        "_id": 0, "SP": 1, "SSR": 1, "SR": 1, "R": 1, "amulets": 1,
        "amulets_spent": 1, "experience": 1, "level": 1, "level_exp_next": 1,
        "jades": 1, "coins": 1, "medals": 1, "realm_ticket": 1, "display": 1, "friendship": 1,
        "encounter_ticket": 1, "friendship_pass": 1
    })

    ships_count = friendship.find({"code": {"$regex": f".*{ctx.author.id}.*"}}).count()
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
    else:
        embed.set_thumbnail(url=ctx.author.avatar_url)

    embed.set_author(
        name=f"{member.display_name}'s profile",
        icon_url=member.avatar_url
    )
    embed.add_field(
        name=":arrow_heading_up: Experience",
        value=f"Level: {level} ({exp}/{level_exp_next})"
    )
    embed.add_field(
        name=f"{emoji_sp} | {emoji_ssr} | {emoji_sr} | {emoji_r}",
        value=f"{profile['SP']} | {profile['SSR']} | {profile['SR']} | {profile['R']}"
    )
    embed.add_field(
        name=f"{emoji_a} Amulets",
        value=f"On Hand: {amulets} | Used: {amulets_spent}"
    )
    embed.add_field(
        name=f"💗 | 🎟 | 🎫 | 🚢",
        value=f"{friendship_pass} | {realm_ticket:,d} | {encounter_ticket:,d} | {ships_count}",
    )
    embed.add_field(
        name=f"{emoji_f} | {emoji_m} | {emoji_j} | {emoji_c}",
        value=f"{friendship_points:,d} | {medals:,d} | {jades:,d} | {coins:,d}",
    )
    await ctx.channel.send(embed=embed)


async def evolve_shikigami(ctx, rarity, evo, user, query, count):

    if rarity == "SP":
        embed = discord.Embed(
            colour=discord.Colour(0xffe6a7),
            description=f"{user.mention}, SP shikigamis are pre-evolved"
        )
        await ctx.channel.send(embed=embed)

    elif evo == "True":
        embed = discord.Embed(
            colour=discord.Colour(0xffe6a7),
            description=f"{user.mention}, your {query} is already evolved."
        )
        await ctx.channel.send(embed=embed)

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

            shikigami_profile = shikigami.find_one({
                "shikigami.name": query.title()}, {
                "shikigami.$.name": 1
            })
            image_url = shikigami_profile["shikigami"][0]["thumbnail"]["evo"]

            embed = discord.Embed(
                colour=discord.Colour(0xffe6a7),
                title="Evolution successful",
                description=f"{user.mention}, you have evolved your {query}!"
            )
            embed.set_thumbnail(url=image_url)
            await ctx.channel.send(embed=embed)

        elif count == 0:
            embed = discord.Embed(
                colour=discord.Colour(0xffe6a7),
                description=f"{user.mention}, you do not own that shikigami"
            )
            await ctx.channel.send(embed=embed)

        elif count <= (get_requirement(rarity) - 1):
            required = rarity_count - count
            noun_duplicate = pluralize('dupe', required)
            embed = discord.Embed(
                colour=discord.Colour(0xffe6a7),
                title="Insufficient shikigamis",
                description=f"{user.mention}, you lack {required} more {query} {noun_duplicate} to evolve yours"
            )
            await ctx.channel.send(embed=embed)


class Economy(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(alises=["issue"])
    @commands.is_owner()
    async def issue_frame_rewards(self, ctx):

        await self.frame_automate()
        await ctx.message.delete()

    async def frame_automate(self):

        await self.frame_starlight()
        await asyncio.sleep(1)
        await self.frame_blazing()

    async def frame_starlight(self):

        for channel in spell_spam_ids:
            try:
                spell_spam_channel = self.client.get_channel(int(channel))
                guild = spell_spam_channel.guild
            except AttributeError:
                continue

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

            if starlight_current == starlight_new:
                users.update_one({"user_id": str(starlight_current.id)}, {"$inc": {"jades": 2000}})
                msg = f"{starlight_current.mention} has earned 2,000{emoji_j} " \
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

    async def frame_blazing(self):

        for channel in spell_spam_ids:
            try:
                spell_spam_channel = self.client.get_channel(int(channel))
                guild = spell_spam_channel.guild
            except AttributeError:
                continue

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

            if blazing_current == blazing_new:
                users.update_one({"user_id": str(blazing_current.id)}, {"$inc": {"amulets": 10}})
                msg = f"{blazing_current.mention} has earned 10{emoji_a} for wielding the Blazing Sun frame for a day!"
                await spell_spam_channel.send(msg)

            else:
                await blazing_new.add_roles(blazing_role)
                await asyncio.sleep(3)
                await blazing_current.remove_roles(blazing_role)
                await asyncio.sleep(3)

                description = f"{blazing_new.mention} {random.choice(adverb)} {random.choice(verb)} " \
                    f"the Rare Blazing Sun Frame from {blazing_current.mention}\"s {random.choice(noun)}!! " \
                    f"{random.choice(comment)}\n\n: 🍀 Distinct SSRs under possession: {ssr_list_new[0][1]} shikigamis"

                embed = discord.Embed(
                    color=0xffff80,
                    title="📨 Hall of Framers Update",
                    description=description
                )
                embed.set_thumbnail(url="https://vignette.wikia.nocookie.net/onmyoji/images/7/72/Frame62.png")
                await spell_spam_channel.send(embed=embed)

    @commands.command(aliases=["add"])
    @commands.is_owner()
    async def bounty_add_alias(self, ctx, *args):

        name = args[0].replace("_", " ").lower()
        alias = " ".join(args[1::]).replace("_", " ").lower()
        bounty.update_one({"aliases": name}, {"$push": {"aliases": alias}})
        embed = discord.Embed(
            colour=discord.Colour(0xffe6a7),
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
            shikigami_profile = shikigami.find_one({
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
                title="No exact results", colour=discord.Colour(0xffe6a7),
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
                title="You have collected already today", colour=discord.Colour(0xffe6a7),
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
                title="You have collected already this week", colour=discord.Colour(0xffe6a7),
                description="Resets every Monday at 00:00 EST"
            )
            await ctx.channel.send(embed=embed)

    @commands.command(aliases=["profile", "p"])
    @commands.guild_only()
    async def profile_show(self, ctx, *, member: discord.Member = None):

        if member is None:
            await profile_post(ctx.author, ctx)
        else:
            await profile_post(member, ctx)

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
                colour=discord.Colour(0xffe6a7),
                title="Invalid shikigami name"
            )
            await ctx.channel.send(embed=embed)

        elif select_formatted in pool_all:
            count = users.count_documents({"user_id": str(user.id), "shikigami.name": select_formatted})

            if count != 1:
                embed = discord.Embed(
                    colour=discord.Colour(0xffe6a7),
                    description=f"{user.mention}, you do not own that shikigami"
                )
                await ctx.channel.send(embed=embed)

            elif count == 1:
                users.update_one({"user_id": str(user.id)}, {"$set": {"display": select_formatted}})
                await ctx.message.add_reaction("✅")

    @commands.command(aliases=["shikigamis", "shikis"])
    @commands.guild_only()
    async def shikigami_list_show(self, ctx, arg1, user: discord.User = None):
        rarity = str(arg1.upper())

        if user is None:
            await self.shikigami_list_post(ctx.author, rarity, ctx)

        else:
            await self.shikigami_list_post(user, rarity, ctx)

    async def shikigami_list_post(self, user, rarity, ctx):
        entries = users.aggregate([{
            "$match": {
                "user_id": str(user.id)}}, {
            "$unwind": {
                "path": "$shikigami"}}, {
            "$match": {
                "shikigami.rarity": rarity}}, {
            "$project": {
                "_id": 0,
                "shikigami.name": 1,
                "shikigami.owned": 1,
                "shikigami.rarity": rarity
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

        icon_url = "https://i.imgur.com/CSMZAjb.png"
        user_shikigamis_page = 1
        embed = discord.Embed(color=user.colour, description="".join(description[0:10]))
        embed.set_author(icon_url=user.avatar_url, name=f"{user.display_name}'s shikigamis")
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
                embed = discord.Embed(color=user.colour, description="".join(description[start:end]))
                embed.set_author(icon_url=user.avatar_url, name=f"{user.display_name}'s Shikigamis")
                embed.set_footer(
                    text=f"Rarity: {rarity.upper()} - Page: {user_shikigamis_page}",
                    icon_url=icon_url
                )
                await msg.edit(embed=embed)
                break
            except asyncio.TimeoutError:
                break

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
                "thumbnail": {
                    "pre_evo": args[2],
                    "evo": args[3]
                }
            }

            shikigami.update_one({
                "rarity": rarity}, {
                "$push": {"shikigami": profile}
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
                    await ctx.message.add_reaction("❌")

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
                title="evolve, evo", colour=discord.Colour(0xffe6a7),
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
                title="Invalid shikigami", colour=discord.Colour(0xffe6a7),
                description=f"{user.mention}, I did not find that shikigami nor you have it"
            )
            await ctx.channel.send(embed=embed)

        elif profile_my_shikigami != {}:
            rarity = profile_my_shikigami["shikigami"][0]["rarity"]
            count = profile_my_shikigami["shikigami"][0]["owned"]
            evo = profile_my_shikigami["shikigami"][0]["evolved"]
            await evolve_shikigami(ctx, rarity, evo, user, query, count)


def setup(client):
    client.add_cog(Economy(client))
