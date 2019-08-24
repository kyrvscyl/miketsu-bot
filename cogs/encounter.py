"""
Encounter Module
Miketsu, 2019
"""

import asyncio
import json
import random
from datetime import datetime, timedelta
from itertools import cycle

import discord
import pytz
from discord.ext import commands

from cogs.economy import reset_boss
from cogs.mongo.database import get_collections
from cogs.startup import e_m, e_j, e_c, e_a, e_f, embed_color, pluralize

# Collections
books = get_collections("bukkuman", "books")
users = get_collections("miketsu", "users")
boss = get_collections("miketsu", "boss")
shikigamis = get_collections("miketsu", "shikigamis")

# Listings
demons = []
quizzes = []
boss_comment = [
    "AHAHAHA!!! <:huehue:585442161093509120>",
    "UFUFUFUFU!! <:19:585443879541538826>",
    "KEKEKEKE!! <:huehue:585442161093509120>",
    "NYAHAHA!! <:19:585443879541538826>"
]
attack_list = open("lists/attack.lists")
attack_verb = attack_list.read().splitlines()
attack_list.close()


for quiz in shikigamis.find({"demon_quiz": {"$ne": None}}, {"_id": 0, "demon_quiz": 1, "name": 1}):
    quizzes.append(quiz)

for document in boss.find({}, {"_id": 0, "boss": 1}):
    demons.append(document["boss"])

boss_spawn = False
quizzes_shuffle = random.shuffle(quizzes)
quizzes_cycle = cycle(quizzes)


def get_timestamp():
    return datetime.utcfromtimestamp(datetime.timestamp(datetime.now()))


def get_time():
    tz_target = pytz.timezone("America/Atikokan")
    return datetime.now(tz=tz_target)


def status_set(x):
    global boss_spawn
    boss_spawn = x


def get_emoji(item):
    emoji_dict = {
        "jades": e_j, "coins": e_c, "realm_ticket": "🎟", "amulets": e_a, "medals": e_m,
        "friendship": e_f, "encounter_ticket": "🎫"
    }
    return emoji_dict[item]


def check_if_user_has_encounter_tickets(ctx):
    return users.find_one({"user_id": str(ctx.author.id)}, {"_id": 0, "encounter_ticket": 1})["encounter_ticket"] > 0


async def boss_create(user, boss_select):
    discoverer = users.find_one({"user_id": str(user.id)}, {"_id": 0, "level": 1})
    boss_lvl = discoverer["level"] + 60

    total_medals = 10000
    for x in users.aggregate([{
        "$group": {
            "_id": "",
            "medals": {
                "$sum": "$medals"}}}, {
        "$project": {
            "_id": 0
        }
    }]):
        total_medals = x["medals"]

    boss.update_one({
        "boss": boss_select}, {
        "$set": {
            "discoverer": str(user.id),
            "level": boss_lvl,
            "total_hp": round(total_medals * (1 + (boss_lvl / 100)), 0),
            "current_hp": round(total_medals * (1 + (boss_lvl / 100)), 0),
            "damage_cap": round(total_medals * (1 + (boss_lvl / 100)) * 0.2, 0),
            "rewards.medals": 200,
            "rewards.jades": 1000,
            "rewards.experience": 250,
            "rewards.coins": 1000000
        }
    })


async def boss_steal(assembly_players, boss_jadesteal, boss_coinsteal):
    for player_id in assembly_players:

        deduction_jades = users.update_one({
            "user_id": player_id, "jades": {"$gte": boss_jadesteal}}, {
            "$inc": {
                "jades": boss_jadesteal
            }
        })
        deduction_coins = users.update_one({
            "user_id": player_id, "coins": {"$gte": boss_coinsteal}}, {
            "$inc": {
                "coins": boss_coinsteal
            }
        })

        if deduction_jades.modified_count == 0:
            users.update_one({"user_id": player_id}, {"$set": {"jades": 0}})

        if deduction_coins.modified_count == 0:
            users.update_one({"user_id": player_id}, {"$set": {"coins": 0}})


async def boss_daily_reset_check():
    survivability = boss.find({"current_hp": {"$gt": 0}}, {"_id": 1}).count()
    discoverability = boss.find({"discoverer": {"$eq": 0}}, {"_id": 1}).count()

    if survivability == 0 and discoverability == 0:
        await reset_boss()


class Encounter(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(aliases=["quiz"])
    @commands.is_owner()
    async def encounter_add_quiz(self, ctx, arg1, *, emoji):

        name = arg1.replace("_", " ").lower()
        print("{} : {}".format(name, emoji))
        x = shikigamis.update_one({"name": name}, {"$set": {"demon_quiz": emoji}})
        if x.modified_count != 0:
            await ctx.message.add_reaction("✅")

    @commands.command(aliases=["q"])
    @commands.is_owner()
    async def encounter_add_quiz(self, ctx):

        msg = await ctx.channel.send(content="🔍 Searching the depths of Netherworld...")
        await self.encounter_roll_treasure(ctx.author, ctx, msg)

    @commands.command(aliases=["encounter", "enc"])
    @commands.check(check_if_user_has_encounter_tickets)
    @commands.cooldown(1, 180, commands.BucketType.user)
    @commands.guild_only()
    async def encounter_search(self, ctx):

        users.update_one({"user_id": str(ctx.author.id)}, {"$inc": {"encounter_ticket": -1}})
        await self.encounter_roll(ctx.author, ctx)
        self.client.get_command("encounter_search").reset_cooldown(ctx)

    async def encounter_roll(self, user, ctx):

        async with ctx.channel.typing():
            search_msg = await ctx.channel.send(content="🔍 Searching the depths of Netherworld...")
            await asyncio.sleep(1)

        survivability = boss.count({"current_hp": {"$gt": 0}})
        discoverability = boss.count({"discoverer": {"$eq": 0}})

        if (survivability > 0 or discoverability > 0) and boss_spawn is False:
            roll_1 = random.randint(0, 100)

            if roll_1 <= 27:
                status_set(True)
                await self.boss_roll(user, ctx, search_msg)
            else:
                roll_2 = random.randint(0, 100)
                await asyncio.sleep(1)

                if roll_2 > 30:
                    await self.encounter_roll_treasure(user, ctx, search_msg)
                else:
                    await self.encounter_roll_quiz(user, ctx, search_msg)
        else:
            roll_2 = random.randint(0, 100)
            await asyncio.sleep(1)

            if roll_2 > 30:
                await self.encounter_roll_treasure(user, ctx, search_msg)
            else:
                await self.encounter_roll_quiz(user, ctx, search_msg)

    async def encounter_roll_quiz(self, user, ctx, search_msg):

        quiz_select = next(quizzes_cycle)
        answer = quiz_select['name']
        question = quiz_select['demon_quiz']
        timeout = 10
        guesses = 3

        embed = discord.Embed(title=f"Demon Quiz", color=user.colour)
        embed.description = f"Time Limit: {timeout} sec"
        embed.add_field(name="Who is this shikigami?", value=f"||{question}||")
        embed.set_footer(text=f"{guesses} {pluralize('guess', guesses)}", icon_url=user.avatar_url)
        await search_msg.edit(embed=embed)

        def check(guess):
            if guess.content.lower() == answer and guess.channel == ctx.channel and guess.author.id == user.id:
                return True
            elif guess.content.lower() != answer and guess.channel == ctx.channel and guess.author.id == user.id:
                raise KeyError

        while guesses != 0:
            try:
                await self.client.wait_for("message", timeout=timeout, check=check)

            except asyncio.TimeoutError:
                embed = discord.Embed(
                    title="Demon Quiz", color=user.colour,
                    description=f"You have failed the quiz",
                    timestamp=get_timestamp()
                )
                embed.add_field(name="Correct Answer", value=f"||{answer.title()}||")
                embed.set_footer(text="Time is up!", icon_url=user.avatar_url)
                await search_msg.edit(embed=embed)
                break

            except KeyError:

                if guesses == 3:
                    guesses -= 1
                    embed.set_footer(text=f"{guesses} {pluralize('guess', guesses)}", icon_url=user.avatar_url)
                    await search_msg.edit(embed=embed)


                elif guesses == 2:
                    guesses -= 1
                    embed.set_footer(text=f"{guesses} {pluralize('guess', guesses)}", icon_url=user.avatar_url)
                    await search_msg.edit(embed=embed)

                elif guesses == 1:
                    guesses -= 1
                    embed.set_footer(text=f"{guesses} {pluralize('guess', guesses)}", icon_url=user.avatar_url)
                    embed.remove_field(0)
                    embed.add_field(name="Correct Answer", value=f"||{answer.title()}||")
                    await search_msg.edit(embed=embed)
                    break
            else:
                users.update_one({"user_id": str(user.id)}, {"$inc": {"amulets": 5}})
                embed = discord.Embed(
                    title="Demon Quiz", color=user.colour,
                    description=f"You have earned 5{e_a}",
                    timestamp=get_timestamp()
                )
                embed.set_footer(text="Correct!", icon_url=user.avatar_url)
                await search_msg.edit(embed=embed)
                break

    async def encounter_roll_treasure(self, user, ctx, search_msg):

        with open("data/rewards.json") as f:
            rewards = json.load(f)

        roll = random.randint(1, 12)
        offer_item = tuple(dict.keys(rewards[str(roll)]["offer"]))[0]
        offer_amount = tuple(dict.values(rewards[str(roll)]["offer"]))[0]
        cost_item = tuple(dict.keys(rewards[str(roll)]["cost"]))[0]
        cost_amount = tuple(dict.values(rewards[str(roll)]["cost"]))[0]

        embed = discord.Embed(
            color=user.colour,
            title="Encounter treasure",
            description=f"A treasure chest containing {offer_amount:,d}{get_emoji(offer_item)}\n"
                        f"It opens using {cost_amount:,d}{get_emoji(cost_item)}",
            timestamp=get_timestamp()
        )
        embed.set_footer(text=f"Found by {user.display_name}", icon_url=user.avatar_url)
        await search_msg.edit(embed=embed)
        await search_msg.add_reaction("✅")

        def check(r, u):
            return u == ctx.author and str(r.emoji) == "✅" and search_msg.id == r.message.id

        try:
            await self.client.wait_for("reaction_add", timeout=6.0, check=check)

        except asyncio.TimeoutError:
            embed = discord.Embed(
                color=user.colour,
                title="Encounter Treasure",
                description=f"The chest you found turned into ashes 🔥",
                timestamp=get_timestamp()
            )
            embed.set_footer(text=f"Found by {user.display_name}", icon_url=user.avatar_url)
            await search_msg.edit(embed=embed)

        else:
            cost_item_current = users.find_one({"user_id": str(user.id)}, {"_id": 0, cost_item: 1})[cost_item]
            if cost_item_current >= cost_amount:
                users.update_one({
                    "user_id": str(user.id)}, {
                    "$inc": {
                        offer_item: offer_amount,
                        cost_item: -cost_amount}
                })
                embed = discord.Embed(
                    color=user.colour,
                    title="Encounter treasure",
                    description=f"You have successfully exchanged {cost_amount}{get_emoji(cost_item)} for "
                                f"{offer_amount}{get_emoji(offer_item)}",
                    timestamp=get_timestamp()
                )
                embed.set_footer(text=f"Found by {user.display_name}", icon_url=user.avatar_url)
                await search_msg.edit(embed=embed)
            else:
                embed = discord.Embed(
                    color=user.colour,
                    title="Encounter treasure",
                    description=f"Exchanged failed. You only have {cost_item_current}{get_emoji(cost_item)}",
                    timestamp=get_timestamp()
                )
                embed.set_footer(text=f"Found by {user.display_name}", icon_url=user.avatar_url)
                await search_msg.edit(embed=embed)

    async def boss_roll(self, discoverer, ctx, search_msg):

        boss_alive = []
        for boss_name in boss.find({
            "$or": [{
                "discoverer": {
                    "$eq": 0}}, {
                "current_hp": {
                    "$gt": 0}}]}, {
            "_id": 0, "boss": 1
        }):
            boss_alive.append(boss_name["boss"])

        boss_select = random.choice(boss_alive)

        if boss.find_one({"boss": boss_select}, {"_id": 0, "discoverer": 1})["discoverer"] == 0:
            await boss_create(discoverer, boss_select)

        def get_boss_profile(name):
            boss_profile_ = boss.find_one({
                "boss": name}, {
                "_id": 0, "challengers": 1, "level": 1, "total_hp": 1, "current_hp": 1, "damage_cap": 1, "boss_url": 1,
                "rewards.coins": 1, "rewards.experience": 1, "rewards.jades": 1, "rewards.medals": 1,
            })

            boss_totalhp = boss_profile_["total_hp"]
            boss_currenthp = boss_profile_["current_hp"]
            boss_lvl = boss_profile_["level"]
            boss_url = boss_profile_["boss_url"]
            boss_coins = boss_profile_["rewards"]["coins"]
            boss_exp = boss_profile_["rewards"]["experience"]
            boss_jades = boss_profile_["rewards"]["jades"]
            boss_medals = boss_profile_["rewards"]["medals"]
            boss_hp_remaining = round(((boss_currenthp / boss_totalhp) * 100), 2)
            return boss_lvl, boss_hp_remaining, boss_jades, boss_coins, boss_medals, boss_exp, boss_url

        timeout = 180
        count_players = 0
        assembly_players = []
        assembly_players_name = []

        def generate_embed_boss(time_remaining, listings):

            formatted_listings = ", ".join(listings)
            if len(formatted_listings) == 0:
                formatted_listings = None

            a, b, c, d, e, f, g = get_boss_profile(boss_select)

            embed_new = discord.Embed(
                title="Encounter Boss", color=discoverer.colour,
                description=f"The rare boss {boss_select} has been triggered!\n\n"
                            f"⏰ {round(time_remaining)} secs left!",
                timestamp=get_timestamp()
            )
            embed_new.add_field(
                name="Stats",
                value=f"```"
                      f"Level   :  {a}\n"
                      f"HP      :  {b}%\n"
                      f"Jades   :  {c:,d}\n"
                      f"Coins   :  {d:,d}\n"
                      f"Medals  :  {e:,d}\n"
                      f"Exp     :  {f:,d}"
                      f"```"
            )
            embed_new.add_field(name="Assembly Players", value=formatted_listings, inline=False)
            embed_new.set_thumbnail(url=g)
            embed_new.set_footer(
                text=f"Discovered by {discoverer.display_name}",
                icon_url=discoverer.avatar_url
            )
            return embed_new

        await asyncio.sleep(2)
        time_discovered = get_time()
        await search_msg.edit(embed=generate_embed_boss(timeout, assembly_players_name))
        await search_msg.add_reaction("🏁")

        def check(r, u):
            return u != self.client.user and str(r.emoji) == "🏁" and r.message.id == search_msg.id

        while count_players < 20:
            try:
                await asyncio.sleep(1)
                timeout = ((time_discovered + timedelta(seconds=180)) - get_time()).total_seconds()
                reaction, user = await self.client.wait_for("reaction_add", timeout=timeout, check=check)

            except asyncio.TimeoutError:
                embed = discord.Embed(title="🎌 Assembly ends!", colour=discord.Colour(embed_color))
                await search_msg.clear_reactions()
                await ctx.channel.send(embed=embed)
                break

            else:
                if str(user.id) in assembly_players:
                    pass

                elif str(user.id) not in assembly_players:
                    query = boss.find_one({"boss": boss_select, "challengers.user_id": str(user.id)}, {"_id": 1})

                    if query is None:
                        boss.update_one({
                            "boss": boss_select}, {
                            "$push": {
                                "challengers": {
                                    "user_id": str(user.id),
                                    "damage": 0
                                }
                            },
                            "$inc": {
                                "rewards.medals": 100,
                                "rewards.jades": 200,
                                "rewards.experience": 150,
                                "rewards.coins": 250000
                            }
                        })

                    assembly_players.append(str(user.id))
                    assembly_players_name.append(user.display_name)
                    timeout_new = ((time_discovered + timedelta(seconds=180)) - get_time()).total_seconds()
                    await search_msg.edit(embed=generate_embed_boss(timeout_new, assembly_players_name))

                count_players += 1

        if len(assembly_players) == 0:
            await asyncio.sleep(3)
            embed = discord.Embed(
                title="Encounter Boss", colour=discord.Colour(embed_color),
                description=f"No players have joined the assembly.\nThe rare boss {boss_select} has fled."
            )
            await ctx.channel.send(embed=embed)
            status_set(False)

        else:
            await asyncio.sleep(3)
            embed = discord.Embed(title=f"Battle with {boss_select} starts!", colour=discord.Colour(embed_color))
            await ctx.channel.send(embed=embed)

            boss_profile = boss.find_one({
                "boss": boss_select}, {
                "_id": 0, "total_hp": 1,  "damage_cap": 1, "boss_url": 1
            })
            boss_damagecap = boss_profile["damage_cap"]
            boss_url_ = boss_profile["boss_url"]
            boss_basedmg = boss_profile["total_hp"] * 0.01

            async with ctx.channel.typing():
                await asyncio.sleep(3)
                await self.boss_assembly(boss_select, assembly_players, boss_damagecap, boss_basedmg, boss_url_, ctx)

    async def boss_assembly(self, boss_select, assembly_players, boss_damagecap, boss_basedmg, boss_url, ctx):

        damage_players = []
        for player in assembly_players:
            player_medals = users.find_one({"user_id": player}, {"_id": 0, "medals": 1})["medals"]
            player_level = users.find_one({"user_id": player}, {"_id": 0, "level": 1})["level"]
            player_dmg = boss_basedmg + (player_medals * (1 + (player_level / 100)))

            if player_dmg > boss_damagecap:
                player_dmg = boss_damagecap

            damage_players.append(player_dmg)
            boss.update_one({
                "boss": boss_select,
                "challengers.user_id": player}, {
                "$inc": {
                    "challengers.$.damage": round(player_dmg, 0),
                    "current_hp": -round(player_dmg, 0)
                }
            })
            player_ = ctx.guild.get_member(int(player))
            embed = discord.Embed(
                color=player_.colour,
                description=f"*{player_.mention} "
                            f"{random.choice(attack_verb)} {boss_select}, dealing {round(player_dmg):,d} damage!*"
            )
            await ctx.channel.send(embed=embed)
            await asyncio.sleep(3)

        boss_profile_new = boss.find_one({
            "boss": boss_select}, {
            "_id": 0,
            "current_hp": 1,
            "rewards": 1,
            "discoverer": 1
        })

        if boss_profile_new["current_hp"] <= 0:
            boss.update_one({"boss": boss_select}, {"$set": {"current_hp": 0}})

        await self.boss_check(assembly_players, boss_select, boss_url, boss_profile_new, ctx)

    async def boss_check(self, assembly_players, boss_select, boss_url, boss_profile_new, ctx):

        boss_currenthp = boss.find_one({"boss": boss_select}, {"_id": 0, "current_hp": 1})["current_hp"]

        if boss_currenthp > 0:

            boss_jadesteal = round(boss_profile_new["rewards"]["jades"] * 0.08)
            boss_coinsteal = round(boss_profile_new["rewards"]["coins"] * 0.07)

            description = f"💨 Rare Boss {boss_select} has fled with {round(boss_currenthp):,d} remaining HP\n" \
                          f"💸 Stealing {boss_jadesteal:,d}{e_j} & {boss_coinsteal:,d}{e_c} " \
                          f"each from its attackers!\n\n{random.choice(boss_comment)}~"

            embed = discord.Embed(colour=discord.Colour(embed_color), description=description)
            embed.set_thumbnail(url=boss_url)

            await boss_steal(assembly_players, boss_jadesteal, boss_coinsteal)
            await asyncio.sleep(3)

            boss.update_one({
                "boss": boss_select}, {
                "$inc": {
                    "rewards.jades": boss_jadesteal,
                    "rewards.coins": boss_coinsteal
                }
            })

            await ctx.channel.send(embed=embed)
            self.client.get_command("encounter_search").reset_cooldown(ctx)
            status_set(False)

        elif boss_currenthp == 0:

            players_dmg = 0
            for damage in boss.aggregate([{
                "$match": {
                    "boss": boss_select}}, {
                "$unwind": {
                    "path": "$challengers"}}, {
                "$group": {
                    "_id": "",
                    "total_damage": {
                        "$sum": "$challengers.damage"}}}, {
                "$project": {
                    "_id": 0
                }}
            ]):
                players_dmg = damage["total_damage"]

            challengers = []
            distribution = []

            for data in boss.aggregate([{
                "$match": {
                    "boss": boss_select}}, {
                "$unwind": {
                    "path": "$challengers"}}, {
                "$project": {
                    "_id": 0, "challengers": 1
                }
            }]):
                challengers.append(data["challengers"]["user_id"])
                distribution.append(round(((data["challengers"]["damage"]) / players_dmg), 2))

            boss_coins = boss_profile_new["rewards"]["coins"]
            boss_jades = boss_profile_new["rewards"]["jades"]
            boss_medals = boss_profile_new["rewards"]["medals"]
            boss_exp = boss_profile_new["rewards"]["experience"]

            boss_coins_user = [i * boss_coins for i in distribution]
            boss_jades_users = [i * boss_jades for i in distribution]
            boss_medals_users = [i * boss_medals for i in distribution]
            boss_exp_users = [i * boss_exp for i in distribution]

            rewards_zip = list(
                zip(challengers, boss_coins_user, boss_jades_users, boss_medals_users, boss_exp_users, distribution))

            embed = discord.Embed(
                title=f"The Rare Boss {boss_select} has been defeated!", colour=discord.Colour(embed_color)
            )
            await ctx.channel.send(embed=embed)
            await self.boss_defeat(boss_select, rewards_zip, boss_url, boss_profile_new, ctx)

    async def boss_defeat(self, boss_select, rewards_zip, boss_url, boss_profile_new, ctx):

        embed = discord.Embed(colour=discord.Colour(embed_color), title="🎊 Boss Defeat Rewards!")
        embed.set_thumbnail(url=boss_url)

        for reward in rewards_zip:
            try:
                name = ctx.guild.get_member(int([reward][0][0]))
                damage_contribution = round([reward][0][5] * 100, 2)
                player_level = users.find_one({"user_id": [reward][0][0]}, {"_id": 0, "level": 1})["level"]
                coins_r = round([reward][0][1] * (1 + player_level / 100))
                jades_r = round([reward][0][2] * (1 + player_level / 100))
                medal_r = round([reward][0][3] * (1 + player_level / 100))
                exp_r = round([reward][0][4] * (1 + player_level / 100))

                embed.add_field(
                    name=f"{name}, {damage_contribution}%",
                    value=f"{coins_r:,d}{e_c}, {jades_r}{e_j}, {medal_r}{e_m}, {exp_r} ⤴",
                    inline=False
                )
                users.update_one({
                    "user_id": [reward][0][0]}, {
                    "$inc": {
                        "jades": round([reward][0][2]),
                        "coins": round([reward][0][1]),
                        "medals": round([reward][0][3])
                    }
                })
                users.update_one({
                    "user_id": [reward][0][0], "level": {"$lt": 60}}, {
                    "$inc": {
                        "experience": round([reward][0][4])
                    }
                })

            except AttributeError:
                continue

        discoverer = boss_profile_new["discoverer"]
        users.update_one({
            "user_id": discoverer}, {
            "$inc": {
                "jades": 100,
                "coins": 50000,
                "medals": 15,
            }
        })
        users.update_one({
            "user_id": discoverer, "level": {"$lt": 60}}, {
            "$inc": {
                "experience": 100
            }
        })

        await asyncio.sleep(3)
        await ctx.channel.send(embed=embed)
        await asyncio.sleep(2)

        try:
            user = ctx.guild.get_member(int(discoverer))
            description = f"{user.mention} earned an extra 100{e_j}, 50,000{e_c}, " \
                          f"15{e_m} and 100 ⤴ for initially discovering {boss_select}!"
            embed = discord.Embed(colour=discord.Colour(embed_color), description=description)
            await ctx.channel.send(embed=embed)
        except AttributeError:
            pass

        self.client.get_command("encounter_search").reset_cooldown(ctx)
        users.update_many({"level": {"$gt": 60}}, {"$set": {"experience": 100000, "level_exp_next": 100000}})
        status_set(False)

    @commands.command(aliases=["binfo", "bossinfo"])
    @commands.guild_only()
    async def boss_info(self, ctx, *, args=None):

        try:
            query = args.title()
            if query not in demons:
                raise AttributeError

            boss_profile = boss.find_one({
                "boss": query}, {
                "_id": 0,
                "level": 1,
                "total_hp": 1,
                "current_hp": 1,
                "rewards": 1,
                "discoverer": 1,
                "boss_url": 1
            })

            try:
                discoverer = ctx.guild.get_member(int(boss_profile["discoverer"])).display_name
            except AttributeError:
                discoverer = "None"

            level = boss_profile["level"]
            total_hp = boss_profile["total_hp"]
            current_hp = boss_profile["current_hp"]
            medals = boss_profile["rewards"]["medals"]
            experience = boss_profile["rewards"]["experience"]
            coins = boss_profile["rewards"]["coins"]
            jades = boss_profile["rewards"]["jades"]
            boss_url = boss_profile["boss_url"]

            description = f"```" \
                          f"Discoverer  :: {discoverer}\n" \
                          f"     Level  :: {level}\n" \
                          f"  Total Hp  :: {total_hp}\n" \
                          f"Current Hp  :: {current_hp}\n" \
                          f"    Medals  :: {medals}\n" \
                          f"     Jades  :: {jades}\n" \
                          f"     Coins  :: {coins}\n" \
                          f"Experience  :: {experience}```"

            embed = discord.Embed(
                title=f"Rare Boss {query} stats", colour=discord.Colour(embed_color),
                description=description
            )
            embed.set_thumbnail(url=boss_url)
            await ctx.channel.send(embed=embed)

        except AttributeError:
            embed = discord.Embed(
                title="bossinfo, binfo", colour=discord.Colour(embed_color),
                description="shows discovered boss statistics"
            )
            demons_formatted = ", ".join(demons)
            embed.add_field(name="Bosses", value="*{}*".format(demons_formatted))
            embed.add_field(name="Example", value="*`;binfo namazu`*", inline=False)
            await ctx.channel.send(embed=embed)


def setup(client):
    client.add_cog(Encounter(client))
