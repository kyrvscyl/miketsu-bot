"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import asyncio
import json
import random

import discord
from discord.ext import commands

from cogs.mongo.db import users, daily, boss

# Global Variables
demon = ["Tsuchigumo", "Odokuro", "Shinkirou", "Oboroguruma", "Namazu"]
emoji_m = "<:medal:573071121545560064>"
emoji_j = "<:jade:555630314282811412>"
emoji_c = "<:coin:573071121495097344>"
emoji_f = "<:friendship:555630314056318979>"
emoji_a = "<:amulet:573071120685596682>"

# Lists startup
attack_list = open("lists/attack.lists")
attack_verb = attack_list.read().splitlines()
attack_list.close()


def get_emoji(item):
    emoji_dict = {
        "jades": emoji_j,
        "coins": emoji_c,
        "realm_ticket": "🎟",
        "amulets": emoji_a
    }
    return emoji_dict[item]


# noinspection PyShadowingNames,PyUnboundLocalVariable
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
            "rewards.medals": 100,
            "rewards.jades": 500,
            "rewards.experience": 250,
            "rewards.coins": 1000000
        }
    })


# noinspection PyShadowingNames,PyUnboundLocalVariable
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

    @commands.command(aliases=["enc"])
    @commands.cooldown(1, 180, commands.BucketType.user)
    @commands.guild_only()
    async def encounter(self, ctx):

        user = ctx.author
        profile = daily.find_one({
            "key": "daily"}, {
            "_id": 0, f"{user.id}.encounter_pass": 1
        })

        if profile[str(user.id)]["encounter_pass"] > 0:

            daily.update_one({
                "key": "daily"}, {
                "$inc": {
                    f"{user.id}.encounter_pass": -1
                }
            })

            await self.encounter_roll(user, ctx)

        else:
            await ctx.channel.send("You have used up all your 🎫")
            self.client.get_command("encounter").reset_cooldown(ctx)

    async def encounter_roll(self, user, ctx):

        async with ctx.channel.typing():

            await ctx.channel.send("🔍Searching the depths of Netherworld...")

            survivability = boss.find({"current_hp": {"$gt": 0}}, {"_id": 1}).count()
            discoverability = boss.find({"discoverer": {"$eq": 0}}, {"_id": 1}).count()
            roll1 = random.randint(0, 100)
            roll2 = random.randint(0, 100)

            await asyncio.sleep(3)

            if survivability > 0 or discoverability > 0 and roll1 <= 20:
                await self.boss_roll(user, ctx)

            elif survivability > 0 or discoverability > 0 and roll1 > 20 and roll2 > 40:
                await self.treasure_roll(user, ctx)

            elif survivability > 0 or discoverability > 0 and roll1 > 20 and roll2 <= 40:
                await self.quiz_roll(user, ctx)

            elif survivability == 0 and discoverability == 0 and roll1 > 20 and roll2 > 40:
                await self.treasure_roll(user, ctx)

            elif survivability == 0 and discoverability == 0 and roll1 > 20 and roll2 <= 40:
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
            color=user.colour,
            description=f"❔Who is this shikigami: {question}"
        )
        embed.set_author(name="Demon Quiz")
        embed.set_footer(
            text=f"Quiz for {user.display_name}. 10 sec | 3 guesses",
            icon_url=user.avatar_url
        )

        msg = await ctx.channel.send(embed=embed)

        def check(guess):
            guess_formatted = ("".join(guess.content)).title()

            if guess.author != user:
                return False

            elif guess_formatted == answer:
                return True

            elif guess_formatted != answer:
                raise KeyError

        guesses = 0
        while guesses != 3:

            try:
                await self.client.wait_for("message", timeout=10, check=check)

            except asyncio.TimeoutError:

                await ctx.channel.send(f"{user.mention}, time is up! You failed the quiz")
                await msg.delete()
                break

            except KeyError:

                if guesses == 0:
                    await ctx.channel.send(f"{user.mention}, wrong answer! 2 more tries left")
                    guesses += 1

                elif guesses == 1:
                    await ctx.channel.send(f"{user.mention}, wrong answer! 1 more try left")
                    guesses += 1

                elif guesses == 2:
                    await ctx.channel.send(f"{user.mention}, wrong answer. You failed the quiz")
                    await msg.delete()
                    break

            else:
                users.update_one({"user_id": str(user.id)}, {"$inc": {"amulets": 5}})
                await ctx.channel.send(f"{user.mention}, correct! You have earned 5{emoji_a}")
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
        embed.set_footer(
            text=f"Found by {user.display_name}",
            icon_url=user.avatar_url
        )

        msg = await ctx.channel.send(embed=embed)
        await msg.add_reaction("✅")

        # noinspection PyShadowingNames
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) == "✅"

        try:
            reaction, user = await self.client.wait_for("reaction_add", timeout=8.0, check=check)

        except asyncio.TimeoutError:

            await ctx.channel.send(f"{user.mention}, the treasure you found turned into ashes 🔥")
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

            await ctx.channel.send(f"{user.mention}, you have successfully exchanged!")

        else:
            await ctx.channel.send(f"{user.mention}, you do not have sufficient {cost_item}")

        self.client.get_command("encounter").reset_cooldown(ctx)

    async def boss_roll(self, user, ctx):

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
            await boss_create(user, boss_select)

        boss_profile = boss.find_one({
            "boss": boss_select}, {
            "_id": 0,
            "challengers": 1,
            "level": 1,
            "total_hp": 1,
            "current_hp": 1,
            "damage_cap": 1,
            "boss_url": 1
        })

        boss_lvl = boss_profile["level"]
        boss_totalhp = boss_profile["total_hp"]
        boss_currenthp = boss_profile["current_hp"]
        boss_damagecap = boss_profile["damage_cap"]
        boss_basedmg = boss_profile["total_hp"] * 0.02
        boss_url = boss_profile["boss_url"]

        boss_hp_remaining = round(((boss_currenthp / boss_totalhp) * 100), 2)

        description = \
            f"The Rare Boss `{boss_select}` has been triggered!\n" \
            f"Boss Level: `{boss_lvl}`\n" \
            f"Remaining Hp: `{boss_hp_remaining}%`\n\n" \
            f"Max players: 10\n" \
            f"Click the 🏁 to participate in the assembly! "

        embed = discord.Embed(
            color=user.colour,
            description=description
        )
        embed.set_thumbnail(url=boss_url)
        embed.set_footer(
            text=f"Discovered by {user.display_name}",
            icon_url=user.avatar_url
        )

        await asyncio.sleep(2)
        msg_boss = await ctx.channel.send(embed=embed)
        await msg_boss.add_reaction("🏁")

        timer = 180
        count_players = 0
        assembly_players = []

        # noinspection PyShadowingNames
        def check(reaction, user):
            return user != self.client.user and str(reaction.emoji) == "🏁" and reaction.message.id == msg_boss.id

        while count_players < 10:

            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=timer, check=check)

            except asyncio.TimeoutError:
                await ctx.channel.send("🎌 Assembly ends!")
                count_players += 15

            else:
                if not str(user.id) in assembly_players:

                    if boss.find_one({"boss": boss_select, "challengers.user_id": str(user.id)}, {"_id": 1}) is None:

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

                    assembly_players.append(str(user.id))
                    timer /= 1.20

                    msg = \
                        f"{user.mention} joins the assembly! 🏁 {count_players + 1}/10 players; " \
                        f"⏰{round(timer)} seconds before closing!"

                    await ctx.channel.send(msg)

                else:
                    await ctx.channel.send(f"{user.mention}, you already joined the assembly.")

                count_players += 1

        if len(assembly_players) == 0:

            await asyncio.sleep(3)
            await ctx.channel.send(f"❌ No players joined the assembly! Rare Boss {boss_select} fled.")
            self.client.get_command("encounter").reset_cooldown(ctx)

        else:

            await asyncio.sleep(3)
            await ctx.channel.send(f"🎮 Battle with {boss_select} starts!")

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

            msg = \
                f"{self.client.get_user(int(player)).mention} {random.choice(attack_verb)} {boss_select}, " \
                    f"dealing {round(player_dmg)} damage!"

            await ctx.channel.send(msg)
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

    # noinspection PyUnboundLocalVariable
    async def boss_check(self, assembly_players, boss_select, boss_url, boss_profile_new, ctx):

        boss_currenthp = boss.find_one({"boss": boss_select}, {"_id": 0, "current_hp": 1})["current_hp"]

        if boss_currenthp > 0:

            boss_jadesteal = round(boss_profile_new["rewards"]["jades"] * 0.05)
            boss_coinsteal = round(boss_profile_new["rewards"]["coins"] * 0.075)

            description1 = \
                f"💨 Rare Boss {boss_select} has fled with {round(boss_currenthp)} remaining Hp"

            description2 = \
                f"💸 Stealing {boss_jadesteal:,d}{emoji_j} & " \
                f"{boss_coinsteal}{emoji_c} each from its attackers!"

            embed = discord.Embed(
                color=0xffff80,
                description=description1 + "\n" + description2
            )
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

            await ctx.channel.send(f"🎯 Rare Boss {boss_select} has been defeated!")
            await self.boss_defeat(boss_select, rewards_zip, boss_url, boss_profile_new, ctx)

    async def boss_defeat(self, boss_select, rewards_zip, boss_url, boss_profile_new, ctx):

        discoverer = boss_profile_new["discoverer"]
        embed = discord.Embed(
            color=0xffff80,
            title="🎊 Boss Defeat Rewards!"
        )
        embed.set_thumbnail(url=boss_url)

        for reward in rewards_zip:

            try:
                name = self.client.get_user(int([reward][0][0])).display_name
                damage_contribution = round([reward][0][5] * 100, 2)
                coins_r = round([reward][0][1])
                jades_r = round([reward][0][2])
                medal_r = round([reward][0][3])
                exp_r = round([reward][0][4])

                embed.add_field(
                    name=f"{name}, {damage_contribution}%",
                    value=f"{coins_r:,d}{emoji_c}, {jades_r}{emoji_j}, {medal_r}{emoji_m}, {exp_r} ⤴"
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
            user = self.client.get_user(int(discoverer))
            msg = f"{user.mention} earned an extra 100{emoji_j}, 50,000{emoji_c}, " \
                f"15{emoji_m} and 100 ⤴ for initially discovering {boss_select}!"

            await ctx.channel.send(msg)

        except AttributeError:
            pass

        self.client.get_command("encounter").reset_cooldown(ctx)

    @commands.command(aliases=["binfo", "bossinfo"])
    async def boss_info(self, ctx, *args):

        query = args[0].capitalize()

        try:
            boss_profile = boss.find_one({
                "boss": query}, {
                "_id": 0,
                "level": 1,
                "total_hp": 1,
                "current_hp": 1,
                "rewards": 1,
                "discoverer": 1
            })

            try:
                user = self.client.get_user(int(boss_profile["discoverer"])).display_name

            except AttributeError:
                user = "None"

            level = boss_profile["level"]
            total_hp = boss_profile["total_hp"]
            current_hp = boss_profile["current_hp"]
            medals = boss_profile["rewards"]["medals"]
            experience = boss_profile["rewards"]["experience"]
            coins = boss_profile["rewards"]["coins"]
            jades = boss_profile["rewards"]["jades"]

            msg = f"Rare Boss {query} Stats:\n```Discoverer: {user.display_name}\n     Level: {level}\n" \
                f"  Total Hp: {total_hp}\nCurrent Hp: {current_hp}\n    Medals: {medals}\n" \
                f"     Jades: {jades}\n     Coins: {coins}\nExperience: {experience}```"

            await ctx.channel.send(msg)

        except IndexError:

            description = \
                "• Tsuchigumo\n" \
                "• Oboroguruma\n" \
                "• Odokuro\n:" \
                "• Shinkirou\n" \
                "• Namazu\n\n" \
                "Use `;binfo <boss_name>`"

            embed = discord.Embed(
                color=ctx.author.colour,
                title="Show Rare Boss Stats",
                description=description
            )

            try:
                embed.set_thumbnail(url=self.client.user.avatar_url)

            except AttributeError:
                pass

            await ctx.channel.send(embed=embed)

        except KeyError:
            await ctx.channel.send(f"Boss {query} is undiscovered")


def setup(client):
    client.add_cog(Encounter(client))
