"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import asyncio
import json
import random

import discord
from discord.ext import commands

from cogs.mongo.db import users, boss, books
from cogs.startup import emoji_m, emoji_j, emoji_c, emoji_a, emoji_f

demons = ["Tsuchigumo", "Odokuro", "Shinkirou", "Oboroguruma", "Namazu"]
boss_spawn = False
boss_comment = [
    "AHAHAHA!!! <:huehue:585442161093509120>",
    "UFUFUFUFU!! <:19:585443879541538826>",
    "KEKEKEKE!! <:huehue:585442161093509120>",
    "NYAHAHA!! <:19:585443879541538826>"
]

attack_list = open("lists/attack.lists")
attack_verb = attack_list.read().splitlines()
attack_list.close()


def get_emoji(item):
    emoji_dict = {
        "jades": emoji_j,
        "coins": emoji_c,
        "realm_ticket": "🎟",
        "amulets": emoji_a,
        "medals": emoji_m,
        "friendship": emoji_f,
        "encounter_ticket": "🎫"
    }
    return emoji_dict[item]


async def boss_create(user, boss_select):
    discoverer = users.find_one({"user_id": str(user.id)}, {"_id": 0, "level": 1})
    boss_lvl = discoverer["level"] + 60
    query = users.aggregate([{
        "$group": {
            "_id": "",
            "medals": {
                "$sum": "$medals"}}}, {
        "$project": {
            "_id": 0
        }
    }])

    total_medals = 10000
    for document in query:
        total_medals = document["medals"]

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

        if users.find_one({"user_id": player_id}, {"_id": 0, "jades": 1})["jades"] <= boss_jadesteal:
            users.update_one({"user_id": player_id}, {"$set": {"jades": 0}})

        else:
            users.update_one({"user_id": player_id}, {"$inc": {"jades": -boss_jadesteal}})

        if users.find_one({"user_id": player_id}, {"_id": 0, "coins": 1})["coins"] <= boss_coinsteal:
            users.update_one({"user_id": player_id}, {"$set": {"coins": 0}})

        else:
            users.update_one({"user_id": player_id}, {"$inc": {"coins": -boss_coinsteal}})


class Encounter(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(aliases=["encounter", "enc"])
    @commands.cooldown(1, 180, commands.BucketType.user)
    @commands.guild_only()
    async def encounter_search(self, ctx):

        user = ctx.author
        profile = users.find_one({"user_id": str(user.id)}, {"_id": 0, "encounter_ticket": 1})

        if profile["encounter_ticket"] > 0:
            users.update_one({"user_id": str(user.id)}, {"$inc": {"encounter_ticket": -1}})
            await self.encounter_roll(user, ctx)

        else:
            embed = discord.Embed(
                title="Insufficient encounter tickets", colour=discord.Colour(0xffe6a7),
                description="Purchase at the shop to obtain more tickets"
            )
            await ctx.channel.send(embed=embed)
            self.client.get_command("encounter").reset_cooldown(ctx)

    async def encounter_roll(self, user, ctx):

        embed = discord.Embed(title="🔍 Searching the depths of Netherworld...", color=user.colour)
        await ctx.channel.send(embed=embed)

        async with ctx.channel.typing():
            await asyncio.sleep(1)

        survivability = boss.find({"current_hp": {"$gt": 0}}, {"_id": 1}).count()
        discoverability = boss.find({"discoverer": {"$eq": 0}}, {"_id": 1}).count()

        if (survivability > 0 or discoverability > 0) and boss_spawn is False:
            roll = random.randint(0, 100)

            if roll <= 20:
                global boss_spawn
                boss_spawn = True
                await self.boss_roll(user, ctx)
            else:
                roll2 = random.randint(0, 100)
                await asyncio.sleep(1)

                if roll2 > 40:
                    await self.treasure_roll(user, ctx)
                else:
                    await self.quiz_roll(user, ctx)
        else:
            roll2 = random.randint(0, 100)
            await asyncio.sleep(1)

            if roll2 > 40:
                await self.treasure_roll(user, ctx)
            else:
                await self.quiz_roll(user, ctx)

    async def quiz_roll(self, user, ctx):

        with open("data/quiz.json") as f:
            quiz = json.load(f)

        answer = random.choice(list(quiz.keys()))
        questions = []

        for entry in quiz[answer]:
            if quiz[answer][entry] != 0:
                questions.append(quiz[answer][entry])

        question = random.choice(questions)
        embed = discord.Embed(
            title=f"Demon Quiz", color=user.colour,
            description=f"{user.mention}, you have 15 secs & 3 guesses\nearn 5 {emoji_a} if you got it correct"
        )
        embed.add_field(name="Who is this shikigami?", value=f"||{question}||")
        msg = await ctx.channel.send(embed=embed)

        def check(guess):
            guess_formatted = ("".join(guess.content)).title()
            if guess.author != user:
                return False
            elif guess_formatted == answer and guess.channel == ctx.channel:
                return True
            elif guess_formatted != answer and guess.channel == ctx.channel:
                raise KeyError

        guesses = 0
        while guesses < 3:
            try:
                await self.client.wait_for("message", timeout=15, check=check)

            except asyncio.TimeoutError:
                embed = discord.Embed(
                    title="Time is up!", color=user.colour,
                    description=f"{user.mention}, you have failed the quiz!"
                )
                await ctx.channel.send(embed=embed)
                await msg.delete()
                break

            except KeyError:
                if guesses == 0:
                    embed = discord.Embed(
                        title="Wrong answer!", color=user.colour,
                        description=f"{user.mention}, 2 more tries left!"
                    )
                    await ctx.channel.send(embed=embed)
                    guesses += 1

                elif guesses == 1:
                    embed = discord.Embed(
                        title="Wrong answer again!", color=user.colour,
                        description=f"{user.mention}, 1 more try left!"
                    )
                    await ctx.channel.send(embed=embed)
                    guesses += 1

                elif guesses == 2:
                    embed = discord.Embed(
                        title="Out of attempts!", color=user.colour,
                        description=f"{user.mention}, you have failed the quiz!"
                    )
                    await ctx.channel.send(embed=embed)
                    await msg.delete()
                    break

            else:
                users.update_one({"user_id": str(user.id)}, {"$inc": {"amulets": 5}})
                embed = discord.Embed(
                    title="Correct!", color=user.colour,
                    description=f"{user.mention}, you have earned 5 {emoji_a}"
                )
                await ctx.channel.send(embed=embed)
                await msg.delete()
                break

        self.client.get_command("encounter").reset_cooldown(ctx)

    async def treasure_roll(self, user, ctx):

        with open("data/rewards.json") as f:
            rewards = json.load(f)

        roll = random.randint(1, 6)
        offer_item = tuple(dict.keys(rewards[str(roll)]["offer"]))[0]
        offer_amount = tuple(dict.values(rewards[str(roll)]["offer"]))[0]
        cost_item = tuple(dict.keys(rewards[str(roll)]["cost"]))[0]
        cost_amount = tuple(dict.values(rewards[str(roll)]["cost"]))[0]

        embed = discord.Embed(
            color=user.colour,
            description=f"A treasure box containing {offer_amount:,d}{get_emoji(offer_item)}\n"
            f"It opens using {cost_amount:,d}{get_emoji(cost_item)}"
        )
        embed.set_footer(text=f"Found by {user.display_name}", icon_url=user.avatar_url)

        msg = await ctx.channel.send(embed=embed)
        await msg.add_reaction("✅")

        def check(r, u):
            return u == ctx.author and str(r.emoji) == "✅"

        try:
            reaction, user = await self.client.wait_for("reaction_add", timeout=6.0, check=check)
        except asyncio.TimeoutError:
            embed = discord.Embed(
                color=user.colour,
                description=f"{user.mention}, the treasure you found turned into ashes 🔥"
            )
            await ctx.channel.send(embed=embed)
            self.client.get_command("encounter").reset_cooldown(ctx)
        else:
            await self.treasure_claim(user, offer_item, offer_amount, cost_item, cost_amount, ctx)

    async def treasure_claim(self, user, offer_item, offer_amount, cost_item, cost_amount, ctx):

        if users.find_one({"user_id": str(user.id)}, {"_id": 0, cost_item: 1})[cost_item] >= cost_amount:

            users.update_one({
                "user_id": str(user.id)}, {
                "$inc": {
                    offer_item: offer_amount,
                    cost_item: -cost_amount}
            })
            embed = discord.Embed(
                color=user.colour,
                description=f"{user.mention}, you have successfully exchanged!"
            )
            await ctx.channel.send(embed=embed)
        else:
            embed = discord.Embed(
                color=user.colour,
                description=f"{user.mention}, you do not have sufficient {get_emoji(cost_item)}"
            )
            await ctx.channel.send(embed=embed)

        self.client.get_command("encounter").reset_cooldown(ctx)

    async def boss_roll(self, discoverer, ctx):

        boss_alive = []
        query = boss.find({
            "$or": [{
                "discoverer": {
                    "$eq": 0}}, {
                "current_hp": {
                    "$gt": 0}}]}, {
            "_id": 0, "boss": 1
        })

        for boss_name in query:
            boss_alive.append(boss_name["boss"])

        boss_select = random.choice(boss_alive)

        if boss.find_one({"boss": boss_select}, {"_id": 0, "discoverer": 1})["discoverer"] == 0:
            await boss_create(discoverer, boss_select)

        boss_profile = boss.find_one({
            "boss": boss_select}, {
            "_id": 0,
            "challengers": 1,
            "level": 1,
            "total_hp": 1,
            "current_hp": 1,
            "damage_cap": 1,
            "boss_url": 1,
            "rewards.coins": 1,
            "rewards.experience": 1,
            "rewards.jades": 1,
            "rewards.medals": 1,
        })

        boss_lvl = boss_profile["level"]
        boss_totalhp = boss_profile["total_hp"]
        boss_currenthp = boss_profile["current_hp"]
        boss_damagecap = boss_profile["damage_cap"]
        boss_basedmg = boss_profile["total_hp"] * 0.02
        boss_url = boss_profile["boss_url"]
        boss_coins = boss_profile["rewards"]["coins"]
        boss_exp = boss_profile["rewards"]["experience"]
        boss_jades = boss_profile["rewards"]["jades"]
        boss_medals = boss_profile["rewards"]["medals"]

        boss_hp_remaining = round(((boss_currenthp / boss_totalhp) * 100), 2)

        roles = books.find_one({"server": str(ctx.guild.id)}, {"_id": 0, "roles.boss_busters": 1})["roles"]

        embed = discord.Embed(
            title="Encounter Boss", color=discoverer.colour,
            description=f"<@&{roles['boss_busters']}>! The rare boss {boss_select} has been triggered!\n\n"
            f"⏰ 3 minutes assembly time!"
        )
        embed.add_field(
            name="Stats",
            value=f"```"
            f"Level   :  {boss_lvl}\n"
            f"HP      :  {boss_hp_remaining}%\n"
            f"Jades   :  {boss_jades:,d}\n"
            f"Coins   :  {boss_coins:,d}\n"
            f"Medals  :  {boss_medals:,d}\n"
            f"Exp     :  {boss_exp:,d}"
            f"```"
        )
        embed.add_field(name="Assembly Players", value="None", inline=False)
        embed.set_thumbnail(url=boss_url)
        embed.set_footer(
            text=f"Discovered by {discoverer.display_name}",
            icon_url=discoverer.avatar_url
        )

        await asyncio.sleep(2)
        msg_boss = await ctx.channel.send(embed=embed)
        await msg_boss.add_reaction("🏁")

        timer = 180
        count_players = 0
        assembly_players = []
        assembly_players_name = []

        def check(r, u):
            return u != self.client.user and str(r.emoji) == "🏁" and r.message.id == msg_boss.id

        def get_boss_profile_assembly(x):
            boss_rewards = boss.find_one({
                "boss": x}, {
                "_id": 0,
                "rewards.coins": 1,
                "rewards.experience": 1,
                "rewards.jades": 1,
                "rewards.medals": 1,
            })["rewards"]
            return boss_rewards["coins"], boss_rewards["experience"], boss_rewards["jades"], boss_rewards["medals"]

        while count_players < 10:

            try:
                await asyncio.sleep(1.2)
                reaction, user = await self.client.wait_for("reaction_add", timeout=timer, check=check)

            except asyncio.TimeoutError:
                embed = discord.Embed(title="🎌 Assembly ends!", colour=discord.Colour(0xffe6a7))
                await msg_boss.clear_reactions()
                await ctx.channel.send(embed=embed)
                break

            else:
                if str(user.id) in assembly_players:
                    embed = discord.Embed(
                        title="Encounter Boss", colour=discoverer.colour,
                        description=f"{user.mention}, you have already joined the assembly"
                    )
                    msg = await ctx.channel.send(embed=embed)
                    await msg.delete(delay=5)

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
                                "rewards.medals": 15,
                                "rewards.jades": 50,
                                "rewards.experience": 50,
                                "rewards.coins": 50000
                            }
                        })

                    timer /= 1.20
                    assembly_players.append(str(user.id))
                    assembly_players_name.append(user.display_name)
                    boss_coins_, boss_exp_, boss_jades_, boss_medals_ = get_boss_profile_assembly(boss_select)

                    embed = discord.Embed(
                        title="Encounter Boss", color=discoverer.colour,
                        description=f"<@&{roles['boss_busters']}>! The rare boss {boss_select} has been triggered!\n\n"
                        f"⏰ {round(timer)} secs left!"
                    )
                    embed.add_field(
                        name="Current Stats",
                        value=f"```"
                        f"Level   :  {boss_lvl}\n"
                        f"HP      :  {boss_hp_remaining}%\n"
                        f"Jades   :  {boss_jades_:,d}\n"
                        f"Coins   :  {boss_coins_:,d}\n"
                        f"Medals  :  {boss_medals_:,d}\n"
                        f"Exp     :  {boss_exp_:,d}"
                        f"```"
                    )
                    embed.add_field(
                        name="Assembly Players",
                        value="{}".format(", ".join(assembly_players_name)),
                        inline=False
                    )
                    embed.set_thumbnail(url=boss_url)
                    embed.set_footer(
                        text=f"Discovered by {discoverer.display_name}",
                        icon_url=discoverer.avatar_url
                    )
                    await msg_boss.edit(embed=embed)

                count_players += 1

        if len(assembly_players) == 0:
            await asyncio.sleep(3)
            embed = discord.Embed(
                title="Encounter Boss", colour=discord.Colour(0xffe6a7),
                description=f"No players have joined the assembly.\nThe rare boss {boss_select} has fled."
            )
            await ctx.channel.send(embed=embed)
            self.client.get_command("encounter").reset_cooldown(ctx)
            global boss_spawn
            boss_spawn = False

        else:
            await asyncio.sleep(3)
            embed = discord.Embed(title=f"Battle with {boss_select} starts!", colour=discord.Colour(0xffe6a7))
            await ctx.channel.send(embed=embed)

            async with ctx.channel.typing():
                await asyncio.sleep(3)
                await self.boss_assembly(boss_select, assembly_players, boss_damagecap, boss_basedmg, boss_url, ctx)

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
                f"{random.choice(attack_verb)} {boss_select}, dealing {round(player_dmg)} damage!*"
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
                f"💸 Stealing {boss_jadesteal:,d}{emoji_j} & {boss_coinsteal:,d}{emoji_c} each from its attackers!\n" \
                f"\n{random.choice(boss_comment)}~"

            embed = discord.Embed(colour=discord.Colour(0xffe6a7), description=description)
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
            self.client.get_command("encounter").reset_cooldown(ctx)
            global boss_spawn
            boss_spawn = False

        elif boss_currenthp == 0:

            query = boss.aggregate([{
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
            ])

            players_dmg = 0
            for damage in query:
                players_dmg = damage["total_damage"]

            challengers = []
            distribution = []
            query = boss.aggregate([{
                "$match": {
                    "boss": boss_select}}, {
                "$unwind": {
                    "path": "$challengers"}}, {
                "$project": {
                    "_id": 0, "challengers": 1
                }
            }])

            for data in query:
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
                title=f"The Rare Boss {boss_select} has been defeated!", colour=discord.Colour(0xffe6a7)
            )
            await ctx.channel.send(embed=embed)
            await self.boss_defeat(boss_select, rewards_zip, boss_url, boss_profile_new, ctx)

    async def boss_defeat(self, boss_select, rewards_zip, boss_url, boss_profile_new, ctx):

        embed = discord.Embed(colour=discord.Colour(0xffe6a7), title="🎊 Boss Defeat Rewards!")
        embed.set_thumbnail(url=boss_url)

        for reward in rewards_zip:
            try:
                name = ctx.guild.get_member(int([reward][0][0]))
                damage_contribution = round([reward][0][5] * 100, 2)
                coins_r = round([reward][0][1])
                jades_r = round([reward][0][2])
                medal_r = round([reward][0][3])
                exp_r = round([reward][0][4])

                embed.add_field(
                    name=f"{name}, {damage_contribution}%",
                    value=f"{coins_r:,d}{emoji_c}, {jades_r}{emoji_j}, {medal_r}{emoji_m}, {exp_r} ⤴",
                    inline=False
                )
                users.update_one({
                    "user_id": [reward][0][0]}, {
                    "$inc": {
                        "jades": round([reward][0][2]),
                        "coins": round([reward][0][1]),
                        "medals": round([reward][0][3]),
                        "experience": round([reward][0][4])}
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
                "experience": 100
            }
        })

        await asyncio.sleep(3)
        await ctx.channel.send(embed=embed)
        await asyncio.sleep(2)

        try:
            user = ctx.guild.get_member(int(discoverer))
            description = f"{user.mention} earned an extra 100{emoji_j}, 50,000{emoji_c}, " \
                f"15{emoji_m} and 100 ⤴ for initially discovering {boss_select}!"
            embed = discord.Embed(colour=discord.Colour(0xffe6a7), description=description)
            await ctx.channel.send(embed=embed)
        except AttributeError:
            pass

        self.client.get_command("encounter").reset_cooldown(ctx)
        global boss_spawn
        boss_spawn = False

    @commands.command(aliases=["binfo", "bossinfo"])
    @commands.guild_only()
    async def boss_info(self, ctx, *args):

        try:
            query = args[0].capitalize()
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
                title=f"Rare Boss {query} stats", colour=discord.Colour(0xffe6a7),
                description=description
            )
            embed.set_thumbnail(url=boss_url)
            await ctx.channel.send(embed=embed)

        except IndexError:

            embed = discord.Embed(
                title="bossinfo, binfo", colour=discord.Colour(0xffe6a7),
                description="shows discovered boss statistics")

            demons_formatted = ", ".join(demons)

            embed.add_field(name="Bosses", value="*{}*".format(demons_formatted))
            embed.add_field(name="Example", value="*`;binfo namazu`*", inline=False)
            await ctx.channel.send(embed=embed)

        except KeyError:
            return


def setup(client):
    client.add_cog(Encounter(client))
