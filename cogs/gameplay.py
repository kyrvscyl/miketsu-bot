"""
Encounter Module
Miketsu, 2019
"""

import asyncio
import os
import random
from datetime import datetime, timedelta
from itertools import cycle

import discord
import pytz
from discord.ext import commands

from cogs.economy import reset_boss
from cogs.mongo.database import get_collections

# Collections
bosses = get_collections("bosses")
config = get_collections("config")
guilds = get_collections("guilds")
logs = get_collections("logs")
shikigamis = get_collections("shikigamis")
users = get_collections("users")

# Dictionary
attack_verb = cycle(config.find_one({"dict": 1}, {"_id": 0, "attack_verb": 1})["attack_verb"])
emojis = config.find_one({"dict": 1}, {"_id": 0, "emojis": 1})["emojis"]
get_emojis = config.find_one({"dict": 1}, {"_id": 0, "get_emojis": 1})["get_emojis"]

# Lists
demons = []
quizzes = []
boss_comment = config.find_one({"list": 1}, {"_id": 0, "boss_comment": 1})["boss_comment"]
assemble_captions = cycle(config.find_one({"list": 1}, {"_id": 0, "assemble_captions": 1})["assemble_captions"])

# Variables
guild_id = int(os.environ.get("SERVER"))
admin_roles = config.find_one({"list": 1}, {"_id": 0, "admin_roles": 1})["admin_roles"]
embed_color = config.find_one({"var": 1}, {"_id": 0, "embed_color": 1})["embed_color"]
timezone = config.find_one({"var": 1}, {"_id": 0, "timezone": 1})["timezone"]

e_m = emojis["m"]
e_j = emojis["j"]
e_c = emojis["c"]
e_f = emojis["f"]
e_a = emojis["a"]
e_t = emojis["t"]


for quiz in shikigamis.find({"demon_quiz": {"$ne": None}}, {"_id": 0, "demon_quiz": 1, "name": 1}):
    quizzes.append(quiz)

for document in bosses.find({}, {"_id": 0, "boss": 1}):
    demons.append(document["boss"])


boss_spawn = False
quizzes_shuffle = random.shuffle(quizzes)
quizzes_cycle = cycle(quizzes)


async def boss_daily_reset_check():
    survivability = bosses.find({"current_hp": {"$gt": 0}}, {"_id": 1}).count()
    discoverability = bosses.find({"discoverer": {"$eq": 0}}, {"_id": 1}).count()

    if survivability == 0 and discoverability == 0:
        await reset_boss()


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


def check_if_user_has_any_admin_roles(ctx):
    for role in reversed(ctx.author.roles):
        if role.name in admin_roles:
            return True
    return False


def check_if_user_has_encounter_tickets(ctx):
    return users.find_one({"user_id": str(ctx.author.id)}, {"_id": 0, "encounter_ticket": 1})["encounter_ticket"] > 0


def check_if_user_has_raid_tickets(ctx):
    return users.find_one({"user_id": str(ctx.author.id)}, {"_id": 0, "realm_ticket": 1})["realm_ticket"] > 0


def emojify(item):
    emoji_dict = {
        "jades": e_j, "coins": e_c, "realm_ticket": "🎟", "amulets": e_a,
        "medals": e_m, "friendship": e_f, "encounter_ticket": "🎫", "talisman": e_t,
        "prayers": "🙏", "friendship_pass": "💗", "parade_tickets": "🎏"
    }
    return emoji_dict[item]


def get_emoji(item):
    return get_emojis[item]


def get_raid_count(victim):
    return users.find_one({"user_id": str(victim.id)}, {"_id": 0, "raided_count": 1})["raided_count"]


def get_time():
    return datetime.now(tz=pytz.timezone(timezone))


def get_timestamp():
    return datetime.utcfromtimestamp(datetime.timestamp(datetime.now()))


def pluralize(singular, count):
    if count > 1:
        if singular[-1:] == "s":
            return singular + "es"
        return singular + "s"
    else:
        return singular


def status_set(x):
    global boss_spawn
    boss_spawn = x


async def logs_add_line(currency, amount, user_id):

    if logs.find_one({"user_id": str(user_id)}, {"_id": 0}) is None:
        profile = {"user_id": str(user_id), "logs": []}
        logs.insert_one(profile)

    logs.update_one({
        "user_id": str(user_id)
    }, {
        "$push": {
            f"logs": {
                "$each": [{
                    "currency": currency,
                    "amount": amount,
                    "date": get_time(),
                }],
                "$position": 0
            }
        }
    })


class Gameplay(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.prefix = self.client.command_prefix

    @commands.command(aliases=["raid", "r"])
    @commands.check(check_if_user_has_raid_tickets)
    @commands.guild_only()
    async def raid_perform(self, ctx, *, victim: discord.Member = None):

        if victim is None:
            raise discord.ext.commands.MissingRequiredArgument

        elif victim.bot or victim.id == ctx.author.id:
            return

        else:
            try:
                raid_count = get_raid_count(victim)

                if raid_count >= 3:
                    embed = discord.Embed(
                        colour=discord.Colour(embed_color),
                        description="raids are capped at 3 times per day and per realm"
                    )
                    embed.set_author(
                        name="Realm is under protection",
                        icon_url=victim.avatar_url
                    )
                    await ctx.channel.send(embed=embed)

                elif raid_count < 4:

                    raider = ctx.author
                    raider_medals = users.find_one({"user_id": str(raider.id)}, {"_id": 0, "level": 1})["level"]
                    victim_medals = users.find_one({"user_id": str(victim.id)}, {"_id": 0, "level": 1})["level"]
                    level_diff = raider_medals - victim_medals
                    range_diff = 30

                    if abs(level_diff) <= range_diff:
                        users.update_one({"user_id": str(victim.id)}, {"$inc": {"raided_count": 1}})
                        users.update_one({"user_id": str(raider.id)}, {"$inc": {"realm_ticket": -1}})
                        await logs_add_line("realm_ticket", -1, raider.id)
                        await self.raid_perform_attack(victim, raider, ctx)

                    else:
                        embed = discord.Embed(
                            title=f"Invalid chosen realm", colour=discord.Colour(embed_color),
                            description=f"You can only raid realms with ±{range_diff:,d} of your level",
                        )
                        await ctx.channel.send(embed=embed)

            except TypeError:
                raise discord.ext.commands.BadArgument

    async def raid_perform_attack(self, victim, raider, ctx):
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
                coins, jades, medals, exp = 25000, 50, 25, 40
                embed = discord.Embed(
                    title="Realm raid", color=raider.colour,
                    description=f"{raider.mention} raids {victim.display_name}'s realm!",
                    timestamp=get_timestamp()
                )
                embed.add_field(
                    name=f"Results, `{total_chance}%`",
                    value=f"{raider.display_name} won!\n"
                          f"{coins:,d}{e_c}, {jades:,d}{e_j}, {medals:,d}{e_m}"
                )
                embed.set_footer(text=raider.display_name, icon_url=raider.avatar_url)
                await self.raid_perform_attack_giverewards_as_winner_raider(raider, coins, jades, medals, exp)
                await ctx.channel.send(embed=embed)

            else:
                coins, jades, medals, exp = 50000, 100, 50, 20
                embed = discord.Embed(
                    title="Realm raid", color=raider.colour,
                    description=f"{raider.mention} raids {victim.display_name}'s realm!",
                    timestamp=get_timestamp()
                )
                embed.add_field(
                    name=f"Results, `{total_chance}%`",
                    value=f"{victim.display_name} won!\n"
                          f"{coins:,d}{e_c}, {jades:,d}{e_j}, {medals:,d}{e_m}"
                )
                embed.set_footer(text=raider.display_name, icon_url=raider.avatar_url)
                await self.raid_perform_attack_giverewards_as_winner_victim(victim, raider, coins, jades, medals, exp)
                await ctx.channel.send(embed=embed)

        except KeyError:
            raise discord.ext.commands.BadArgument

        except TypeError:
            return

    async def raid_perform_attack_giverewards_as_winner_victim(self, victim, raider, coins, jades, medals, exp):
        users.update_one({"user_id": str(raider.id), "level": {"$lt": 60}}, {"$inc": {"experience": exp}})
        users.update_one({"user_id": str(victim.id)}, {"$inc": {"coins": coins, "jades": jades, "medals": medals}})

        await logs_add_line("coins", coins, victim.id)
        await logs_add_line("jades", jades, victim.id)
        await logs_add_line("medals", medals, victim.id)

    async def raid_perform_attack_giverewards_as_winner_raider(self, raider, coins, jades, medals, exp):
        users.update_one({"user_id": str(raider.id), "level": {"$lt": 60}}, {"$inc": {"experience": exp}})
        users.update_one({"user_id": str(raider.id)}, {"$inc": {"coins": coins, "jades": jades, "medals": medals}})

        await logs_add_line("coins", coins, raider.id)
        await logs_add_line("jades", jades, raider.id)
        await logs_add_line("medals", medals, raider.id)

    @commands.command(aliases=["raidcalc", "raidc", "rc"])
    @commands.guild_only()
    async def raid_perform_calculation(self, ctx, *, victim: discord.Member = None):

        if victim is None:
            raise discord.ext.commands.MissingRequiredArgument

        elif victim == ctx.author or victim.bot is True:
            return

        elif victim != ctx.author:
            await self.raid_perform_calculation_submit(victim, ctx.author, ctx)

    async def raid_perform_calculation_submit(self, victim, raider, ctx):
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
            raise discord.ext.commands.BadArgument

        except TypeError:
            return

    @commands.command(aliases=["qz"])
    @commands.check(check_if_user_has_any_admin_roles)
    async def encounter_add_quiz(self, ctx, arg1, *, emoji):

        name = arg1.replace("_", " ").lower()
        x = shikigamis.update_one({"name": name}, {"$set": {"demon_quiz": emoji}})
        if x.modified_count != 0:
            await ctx.message.add_reaction("✅")

    @commands.command(aliases=["encounter", "enc"])
    @commands.check(check_if_user_has_encounter_tickets)
    @commands.cooldown(1, 180, commands.BucketType.user)
    @commands.guild_only()
    async def encounter_search(self, ctx):

        users.update_one({"user_id": str(ctx.author.id)}, {"$inc": {"encounter_ticket": -1}})
        await logs_add_line("encounter_ticket", -1, ctx.author.id)
        await self.encounter_roll(ctx.author, ctx)
        self.client.get_command("encounter_search").reset_cooldown(ctx)

    async def encounter_roll(self, user, ctx):

        async with ctx.channel.typing():
            search_msg = await ctx.channel.send(content="🔍 Searching the depths of Netherworld...")
            await asyncio.sleep(1)

        survivability = bosses.count({"current_hp": {"$gt": 0}})
        discoverability = bosses.count({"discoverer": {"$eq": 0}})

        if (survivability > 0 or discoverability > 0) and boss_spawn is False:
            roll_1 = random.randint(0, 100)

            if roll_1 <= 27:
                status_set(True)
                await self.encounter_roll_boss(user, ctx, search_msg)
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
        embed.add_field(name="Who is this shikigami?", value=f"{question}")
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
                embed.add_field(name="Correct Answer", value=f"{answer.title()}")
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
                    embed.add_field(name="Correct Answer", value=f"{answer.title()}")
                    await search_msg.edit(embed=embed)
                    break
            else:
                users.update_one({"user_id": str(user.id)}, {"$inc": {"amulets": 5}})
                await logs_add_line("amulets", 5, ctx.author.id)
                embed = discord.Embed(
                    title="Demon Quiz", color=user.colour,
                    description=f"You have earned 5{e_a}",
                    timestamp=get_timestamp()
                )
                embed.set_footer(text="Correct!", icon_url=user.avatar_url)
                await search_msg.edit(embed=embed)
                break

    async def encounter_roll_treasure(self, user, ctx, search_msg):

        rewards = config.find_one({"dict": 1}, {"_id": 0, "rewards": 1})["rewards"]

        roll = random.randint(1, len(rewards))
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
            await search_msg.clear_reactions()

        else:
            cost_item_current = users.find_one({"user_id": str(user.id)}, {"_id": 0, cost_item: 1})[cost_item]
            if cost_item_current >= cost_amount:
                users.update_one({
                    "user_id": str(user.id)}, {
                    "$inc": {
                        offer_item: offer_amount,
                        cost_item: -cost_amount}
                })

                await logs_add_line(offer_item, offer_amount, user.id)
                await logs_add_line(cost_item, -cost_amount, user.id)

                cost_item_have = users.find_one({"user_id": str(user.id)}, {"_id": 0, cost_item: 1})[cost_item]
                offer_item_have = users.find_one({"user_id": str(user.id)}, {"_id": 0, offer_item: 1})[offer_item]

                embed = discord.Embed(
                    color=user.colour,
                    title="Encounter treasure",
                    description=f"You acquired {offer_amount:,d}{get_emoji(offer_item)} in exchange for "
                                f"{cost_amount:,d}{get_emoji(cost_item)}",
                    timestamp=get_timestamp()
                )
                embed.add_field(
                    name="Inventory",
                    value=f"`{offer_item_have:,d}` {emojify(offer_item)} | `{cost_item_have:,d}` {emojify(cost_item)}"
                )
                embed.set_footer(text=f"Found by {user.display_name}", icon_url=user.avatar_url)
                await search_msg.edit(embed=embed)
                await search_msg.clear_reactions()
            else:
                embed = discord.Embed(
                    color=user.colour,
                    title="Encounter treasure",
                    description=f"exchange failed, you only have {cost_item_current:,d}{get_emoji(cost_item)}",
                    timestamp=get_timestamp()
                )
                embed.set_footer(text=f"Found by {user.display_name}", icon_url=user.avatar_url)
                await search_msg.edit(embed=embed)
                await search_msg.clear_reactions()

    async def encounter_roll_boss(self, discoverer, ctx, search_msg):

        boss_alive = []
        for boss_name in bosses.find({
            "$or": [{
                "discoverer": {
                    "$eq": 0}}, {
                "current_hp": {
                    "$gt": 0}}]}, {
            "_id": 0, "boss": 1
        }):
            boss_alive.append(boss_name["boss"])

        boss_select = random.choice(boss_alive)

        if bosses.find_one({"boss": boss_select}, {"_id": 0, "discoverer": 1})["discoverer"] == 0:
            await self.encounter_roll_boss_create(discoverer, boss_select)

        def get_boss_profile(name):
            boss_profile_ = bosses.find_one({
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
        boss_busters_id = guilds.find_one({"server": str(guild_id)}, {"_id": 0, "roles": 1})["roles"]["boss_busters"]

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
            embed_new.add_field(
                name=f"Assembly Players [{len(assembly_players)}]",
                value=formatted_listings,
                inline=False
            )
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

        link = f"https://discordapp.com/channels/{search_msg.guild.id}/{search_msg.channel.id}/{search_msg.id}"
        embed = discord.Embed(
            title=f"🏁 Assemble here!",
            url=link
        )
        await ctx.channel.send(content=f"<@&{boss_busters_id}>! {next(assemble_captions)}", embed=embed)

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
                    query = bosses.find_one({"boss": boss_select, "challengers.user_id": str(user.id)}, {"_id": 1})

                    if query is None:
                        bosses.update_one({
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

            boss_profile = bosses.find_one({
                "boss": boss_select}, {
                "_id": 0, "total_hp": 1,  "damage_cap": 1, "boss_url": 1
            })
            boss_dmgcap = boss_profile["damage_cap"]
            boss_url_ = boss_profile["boss_url"]
            boss_dmg = boss_profile["total_hp"] * 0.01

            async with ctx.channel.typing():
                await asyncio.sleep(3)
                await self.encounter_roll_boss_assembly(
                    boss_select, assembly_players, boss_dmgcap, boss_dmg, boss_url_, ctx
                )

    async def encounter_roll_boss_assembly(self, boss_select, assembly_players, boss_dmgcap, boss_dmg, boss_url, ctx):

        damage_players = []
        for player in assembly_players:
            player_medals = users.find_one({"user_id": player}, {"_id": 0, "medals": 1})["medals"]
            player_level = users.find_one({"user_id": player}, {"_id": 0, "level": 1})["level"]
            player_dmg = boss_dmg + (player_medals * (1 + (player_level / 100)))

            if player_dmg > boss_dmgcap:
                player_dmg = boss_dmgcap

            damage_players.append(player_dmg)
            bosses.update_one({
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
                            f"{next(attack_verb)} {boss_select}, dealing {round(player_dmg):,d} damage!*"
            )
            await ctx.channel.send(embed=embed)
            await asyncio.sleep(1)

        boss_profile_new = bosses.find_one({
            "boss": boss_select}, {
            "_id": 0,
            "current_hp": 1,
            "rewards": 1,
            "discoverer": 1
        })

        if boss_profile_new["current_hp"] <= 0:
            bosses.update_one({"boss": boss_select}, {"$set": {"current_hp": 0}})

        await self.encounter_roll_boss_check(assembly_players, boss_select, boss_url, boss_profile_new, ctx)

    async def encounter_roll_boss_check(self, assembly_players, boss_select, boss_url, boss_profile_new, ctx):

        boss_currenthp = bosses.find_one({"boss": boss_select}, {"_id": 0, "current_hp": 1})["current_hp"]

        if boss_currenthp > 0:

            boss_jadesteal = round(boss_profile_new["rewards"]["jades"] * 0.02)
            boss_coinsteal = round(boss_profile_new["rewards"]["coins"] * 0.03)

            description = f"💨 Rare Boss {boss_select} has fled with {round(boss_currenthp):,d} remaining HP\n" \
                          f"💸 Stealing {boss_jadesteal:,d} {e_j} & {boss_coinsteal:,d} {e_c} " \
                          f"each from its attackers!\n\n{random.choice(boss_comment)}~"

            embed = discord.Embed(
                colour=discord.Colour(embed_color), description=description, timestamp=get_timestamp()
            )
            embed.set_thumbnail(url=boss_url)

            await self.encounter_roll_boss_steal(assembly_players, boss_jadesteal, boss_coinsteal)
            await asyncio.sleep(3)

            bosses.update_one({
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
            for damage in bosses.aggregate([{
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

            for data in bosses.aggregate([{
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
            await self.encounter_roll_boss_defeat(boss_select, rewards_zip, boss_url, boss_profile_new, ctx)

    async def encounter_roll_boss_defeat(self, boss_select, rewards_zip, boss_url, boss_profile_new, ctx):

        embed = discord.Embed(
            colour=discord.Colour(embed_color),
            title="🎊 Boss defeat rewards!",
            timestamp=get_timestamp()
        )
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
                    value=f"{coins_r:,d}{e_c}, {jades_r:,d}{e_j}, {medal_r:,d}{e_m}, {exp_r:,d} ⤴",
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
                await logs_add_line("jades", round([reward][0][2]), [reward][0][0])
                await logs_add_line("coins", round([reward][0][1]), [reward][0][0])
                await logs_add_line("medals", round([reward][0][3]), [reward][0][0])

                users.update_one({
                    "user_id": [reward][0][0], "level": {"$lt": 60}}, {
                    "$inc": {
                        "experience": round([reward][0][4])
                    }
                })

            except AttributeError:
                continue

        try:
            jades, coins, medals, exp = 250, 150000, 150, 100
            discoverer = boss_profile_new["discoverer"]
            users.update_one({
                "user_id": discoverer}, {
                "$inc": {
                    "jades": jades,
                    "coins": coins,
                    "medals": medals,
                }
            })
            await logs_add_line("jades", jades, discoverer)
            await logs_add_line("coins", coins, discoverer)
            await logs_add_line("medals", medals, discoverer)

            users.update_one({
                "user_id": discoverer, "level": {"$lt": 60}}, {
                "$inc": {
                    "experience": exp
                }
            })

            await asyncio.sleep(3)
            await ctx.channel.send(embed=embed)
            await asyncio.sleep(2)
            user = ctx.guild.get_member(int(discoverer))
            description = f"{user.mention} earned an extra {jades:,d}{e_j}, {coins:,d}{e_c}, " \
                          f"{medals:,d}{e_m} and {exp:,d} ⤴ for initially discovering {boss_select}!"
            embed = discord.Embed(
                colour=discord.Colour(embed_color),
                description=description, timestamp=get_timestamp()
            )
            await ctx.channel.send(embed=embed)
        except AttributeError:
            pass

        self.client.get_command("encounter_search").reset_cooldown(ctx)
        users.update_many({"level": {"$gt": 60}}, {"$set": {"experience": 100000, "level_exp_next": 100000}})
        status_set(False)

    async def encounter_roll_boss_create(self, user, boss_select):
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

        bosses.update_one({
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

    async def encounter_roll_boss_steal(self, assembly_players, boss_jadesteal, boss_coinsteal):
        for player_id in assembly_players:

            deduction_jades = users.update_one({
                "user_id": player_id, "jades": {"$gte": boss_jadesteal}}, {
                "$inc": {
                    "jades": - boss_jadesteal
                }
            })
            if deduction_jades.modified_count > 0:
                await logs_add_line("jades", -boss_jadesteal, player_id)


            deduction_coins = users.update_one({
                "user_id": player_id, "coins": {"$gte": boss_coinsteal}}, {
                "$inc": {
                    "coins": - boss_coinsteal
                }
            })
            if deduction_jades.modified_count > 0:
                await logs_add_line("coins", -boss_coinsteal, player_id)

            if deduction_jades.modified_count == 0:
                users.update_one({"user_id": player_id}, {"$set": {"jades": 0}})
                current_jades = users.find_one({"user_id": player_id}, {"_id": 0, "jades": 1})["jades"]
                await logs_add_line("jades", -current_jades, player_id)
            else:
                await logs_add_line("jades", -boss_jadesteal, player_id)

            if deduction_coins.modified_count == 0:
                users.update_one({"user_id": player_id}, {"$set": {"coins": 0}})
                current_coins = users.find_one({"user_id": player_id}, {"_id": 0, "coins": 1})["coins"]
                await logs_add_line("coins", -current_coins, player_id)
            else:
                await logs_add_line("coins", -boss_coinsteal, player_id)

    @commands.command(aliases=["binfo", "bossinfo"])
    @commands.guild_only()
    async def encounter_boss_stats(self, ctx, *, args=None):

        try:
            query = args.title()
            if query.lower() == "all":

                query = bosses.find({"current_hp": {"$gt": 0}}, {"_id": 0, "boss": 1, "total_hp": 1, "current_hp": 1})
                bosses_formatted = []

                for boss in query:
                    percent = (boss["current_hp"] / boss["total_hp"]) * 100
                    bosses_formatted.append(
                        f"• {round(percent,2)}%    {boss['boss']}"
                    )

                bosses_formatted_lines = "\n".join(bosses_formatted)

                embed = discord.Embed(
                    title=f"Boss survivability", colour=discord.Colour(embed_color),
                    description=f"```"
                                f"  HP        Boss\n"
                                f"{bosses_formatted_lines}\n"
                                f"```",
                    timestamp=get_timestamp()
                )
                await ctx.channel.send(embed=embed)

            elif query not in demons:
                raise AttributeError

            else:
                boss_profile = bosses.find_one({
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
                    description=description,
                    timestamp=get_timestamp()
                )
                embed.set_thumbnail(url=boss_url)
                await ctx.channel.send(embed=embed)

        except AttributeError:
            embed = discord.Embed(
                title="bossinfo, binfo", colour=discord.Colour(embed_color),
                description="shows discovered boss statistics"
            )
            demons_formatted = ", ".join(demons)
            embed.add_field(name="Bosses", value=f"*{demons_formatted}*")
            embed.add_field(
                name="Example",
                value=f"*`{self.prefix}binfo namazu`*\n"
                      f"*`{self.prefix}binfo all`*",
                inline=False
            )
            await ctx.channel.send(embed=embed)


def setup(client):
    client.add_cog(Gameplay(client))
