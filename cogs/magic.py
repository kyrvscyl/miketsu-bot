"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import asyncio
import json
import random
from datetime import datetime
from datetime import timedelta

import discord
import pytz
from discord.ext import commands
from discord_webhook import DiscordWebhook, DiscordEmbed

from cogs.mongo.db import books, quests, owls, weather, sendoff, thieves, patronus

# Date and Time
tz_target = pytz.timezone("America/Atikokan")

# Global Variables
owls_list = []
for owl in owls.find({}, {"_id": 0, "type": 1}):
    owls_list.append(owl["type"])

patronus_ = open("lists/patronuses.lists")
patronuses = patronus_.read().splitlines()
patronus_.close()

woods_ = open("lists/woods.lists")
woods = woods_.read().splitlines()
woods_.close()

flexibility_types_ = open("lists/flexibility_types.lists")
flexibility_types = flexibility_types_.read().splitlines()
flexibility_types_.close()

traits = ["pure emotions", "adventurous", "special", "strong-willed", "nature-loving"]
lengths = ["short", "long", "average"]
flexibilities = ["high", "low", "medium"]
cores = ["unicorn hair", "dragon heartstring", "phoenix feather"]
wand_lengths = ["8", "9", "10", "11", "12", "13", "14"]


def current_timestamp():
    return datetime.now(tz=tz_target).strftime("%Y-%b-%d %HH")


def current_time2():
    return datetime.now(tz=tz_target).strftime("%H")


# noinspection PyUnboundLocalVariable,PyShadowingNames
def get_data(user):
    data = quests.aggregate([{
        "$match": {"user_id": str(user.id)}}, {
        "$project": {
            "_id": 0, "quest1": {
                "$slice": ["$quest1", -1]}
        }}
    ])

    for profile in data:
        cycle = profile["quest1"][0]["cycle"]
        current_path = profile["quest1"][0]["current_path"]
        timestamp = profile["quest1"][0]["timestamp"]
        hints = profile["quest1"][0]["hints"]
        actions = profile["quest1"][0]["actions"]
        purchase = profile["quest1"][0]["purchase"]
        break

    return cycle, current_path, timestamp, hints, actions, purchase


# noinspection PyShadowingNames,PyUnboundLocalVariable
def get_profile_finished(user):
    data = quests.aggregate([{
        "$match": {
            "user_id": str(user.id)}}, {
        "$project": {
            "_id": 0,
            "quest1": {
                "$slice": ["$quest1", -1]
            }}
    }])

    for profile in data:
        patronus_summon = profile["quest1"][0]["patronus"]["patronus"]
        score = profile["quest1"][0]["score"]
        timestamp_start = profile["quest1"][0]["timestamp_start"]
        hints_unlocked = profile["quest1"][0]["hints_unlocked"]
        owl_final = profile["quest1"][0]["owl"]
        wand = profile["quest1"][0]["wand"]
        paths = profile["quest1"][0]["paths_unlocked"]

        break

    return score, timestamp_start, patronus_summon, hints_unlocked, owl_final, wand, paths


# noinspection PyUnboundLocalVariable
def get_profile_history(user, cycle):
    data = quests.aggregate([
        {
            '$match': {
                'user_id': str(user.id)
            }
        }, {
            '$unwind': {
                'path': '$quest1'
            }
        }, {
            '$match': {
                'quest1.cycle': int(cycle)
            }
        }
    ])

    for result in data:
        profile = result
        break

    return profile


# noinspection PyUnboundLocalVariable
def get_profile_progress(user):
    data = quests.aggregate([{
        "$match": {
            "user_id": str(user.id)}}, {
        "$project": {
            "_id": 0,
            "quest1": {"$slice": ["$quest1", -1]}
        }
    }])

    for profile in data:
        cycle = profile["quest1"][0]["cycle"]
        current_path = profile["quest1"][0]["current_path"]
        score = profile["quest1"][0]["score"]
        timestamp_start = profile["quest1"][0]["timestamp_start"]
        hints_unlocked = profile["quest1"][0]["hints_unlocked"]
        break

    return score, timestamp_start, current_path, cycle, hints_unlocked


def check_quest(user):
    return quests.find_one({"user_id": str(user.id)}, {"_id": 0, "user_id": 1}) != {}


def spell_check(msg):
    translate = msg.lower().translate({ord(i): None for i in "! "})
    spell = "expectopatronum"
    return all(c in spell for c in translate) and all(c in translate for c in spell)


def get_owl_type(x):
    trait = {
        "nature-loving": "barred",
        "adventurous": "brown",
        "special": "screech",
        "strong-willed": "snowy",
        "pure emotions": "tawny"
    }
    return trait[x]


def get_length_category(x):
    length = {
        "8": "short",
        "9": "short",
        "10": "average",
        "11": "average",
        "12": "long",
        "13": "long",
        "14": "long"
    }
    return length[x]


def get_flexibility_category(wand_flexibility):
    flexibility = {
        "pliant": "high",
        "supple": "high",
        "Surprisingly swishy": "high",
        "whippy": "high",
        "bendy": "high",
        "swishy": "high",
        "very flexible": "high",
        "brittle": "low",
        "hard": "low",
        "rigid": "low",
        "solid": "low",
        "unbending": "low",
        "unyielding": "low",
        "stiff": "low",
        "quite bendy": "medium",
        "quite flexible": "medium",
        "slightly springy": "medium",
        "reasonably supple": "medium",
        "slightly yielding": "medium",
        "fairly bendy": "medium"
    }
    return flexibility[wand_flexibility]


# noinspection PyShadowingNames
async def secret_banner(webhook_url, avatar, username, url):
    webhook = DiscordWebhook(url=webhook_url, avatar_url=avatar, username=username)
    embed = DiscordEmbed(color=0xffffff)
    embed.set_image(url=url)
    webhook.add_embed(embed)
    webhook.execute()


def get_dictionary(channel_name):
    with open("data/responses.json") as f:
        responses = json.load(f)
    return responses[channel_name]


# noinspection PyUnreachableCode,PyUnboundLocalVariable
async def generate_data(guild, secret_channel, channel):
    channel_name = secret_channel.replace(" ", "-")
    webhook = await channel.create_webhook(name="webhooker")

    if channel_name == "eeylops-owl-emporium":
        avatar_url = "https://i.imgur.com/8xR61b4.jpg"
        username = "Manager Eeylops"
        url = "https://i.imgur.com/wXSibYR.jpg"

    elif channel_name == "gringotts-bank":
        avatar_url = "https://i.imgur.com/IU882rV.jpg"
        username = "Bank Manager Gringotts"
        url = "https://i.imgur.com/whPMNPb.jpg"

    elif channel_name == "ollivanders":
        avatar_url = "https://i.imgur.com/DEuO4la.jpg"
        username = "Ollivanders"
        url = "https://i.imgur.com/5ibOfcp.jpg"

    books.update_one({
        "server": str(guild.id)}, {
        "$set": {
            f"{channel_name}.id": str(channel.id),
            f"{channel_name}.webhook": webhook.url,
            f"{channel_name}.avatar": avatar_url,
            f"{channel_name}.username": username
        }
    })
    await secret_banner(webhook.url, avatar_url, username, url)


async def reaction_closed(message):
    await message.add_reaction("🇨")
    await message.add_reaction("🇱")
    await message.add_reaction("🇴")
    await message.add_reaction("🇸")
    await message.add_reaction("🇪")
    await message.add_reaction("🇩")
    await asyncio.sleep(4)
    await message.delete()


class Magic(commands.Cog):

    def __init__(self, client):
        self.client = client

    async def logging(self, msg):
        channel = self.client.get_channel(592270990894170112)
        date_time = datetime.now(tz=tz_target).strftime("%Y-%b-%d %HH")
        await channel.send(f"[{date_time}] " + msg)

    # noinspection PyUnboundLocalVariable
    @commands.command(aliases=["patronus"])
    @commands.has_role("Test")
    async def show_patronus(self, ctx, *, _patronus):
        profiles = patronus.find({"patronus": _patronus.lower()})
        patronus_descriptions = []

        for profile in profiles:
            name = profile["patronus"]
            wood = profile["wood"]
            flexibility = profile["flexibility"]
            length = profile["length"]
            core = profile["core"]
            trait = profile["trait"]
            link = profile["link"]

            description = \
                f"Owl Requirements: \n" \
                    f"• Type: {get_owl_type(trait)} owl\n" \
                    f"•Trait: {trait.title()}\n\n" \
                    f"Wand Requirements:\n" \
                    f"• Flexibility: {flexibility.title()}\n" \
                    f"• Length: {length.title()}\n" \
                    f"• Core: {core.title()}\n" \
                    f"• Wood: {wood.title()}\n"

            patronus_descriptions.append(description)

        embed1 = discord.Embed(
            color=0x50e3c2,
            title=f"{name.title()} | Combination # 1",
            description=patronus_descriptions[0]
        )
        embed1.set_image(url=link)

        msg = await ctx.channel.send(embed=embed1)
        await msg.add_reaction("⬅")
        await msg.add_reaction("➡")

        # noinspection PyShadowingNames
        def check(reaction, user):
            return user != self.client.user and reaction.message.id == msg.id

        # noinspection PyShadowingNames
        def create_embed(page):

            try:
                embed = discord.Embed(
                    color=0x50e3c2,
                    title=f"{name.title()} | Combination # {page + 1}",
                    description=patronus_descriptions[page]
                )
                embed.set_image(url=link)

            except IndexError:
                embed = embed1

            return embed

        page = 0
        while True:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=60, check=check)
            except asyncio.TimeoutError:
                return False
            else:
                if str(reaction.emoji) == "➡":
                    page += 1
                elif str(reaction.emoji) == "⬅":
                    page -= 1
                await msg.edit(embed=create_embed(page))

    async def sendoff_owl(self, user, cycle):
        responses = get_dictionary("send_off")
        await user.send(responses["success1"])
        await asyncio.sleep(2)
        await user.send(responses["success2"])
        await self.generate_owl_report(user, cycle, responses)

    # noinspection PyUnboundLocalVariable,PyUnusedLocal
    async def generate_owl_report(self, user, cycle, responses):

        profile = sendoff.find_one({"user_id": str(user.id), "cycle": cycle}, {"_id": 0})
        weather1 = weather.find_one({"weather1": {"$type": "string"}}, {"weather1": 1})["weather1"]
        weather2 = weather.find_one({"weather2": {"$type": "string"}}, {"weather2": 1})["weather2"]

        def get_specific_report(key):
            return responses["reports"][key]["delay"], \
                   responses["reports"][key]["scenario"], \
                   responses["reports"][key]["content"]

        if weather1 == "⛈":
            delay, scenario, content = get_specific_report("thunderstorms")
            await self.update_path(user, cycle, path_new="path19")

        elif weather1 == "🌨" and profile["type"] == "snowy":
            delay, scenario, content = get_specific_report("snowy_snowy_owl")

        elif weather2 == "🌕" or weather2 == "🌑":
            delay, scenario, content = get_specific_report("night_time")

        elif weather1 == "🌧" or weather1 == "🌨":
            delay, scenario, content = get_specific_report("rainy_snowy")

        elif weather1 == "☁" or weather1 == "⛅" or weather1 == "☀":
            delay, scenario, content = get_specific_report("cloudy_sunny")

        timestamp_update = (datetime.now(tz=tz_target) + timedelta(days=1 / 24)).strftime("%Y-%b-%d %HH")
        timestamp_complete = (datetime.now(tz=tz_target) + timedelta(days=delay / 24)).strftime("%Y-%b-%d %HH")

        sendoff.update_one({
            "user_id": str(user.id)}, {
            "$set": {
                "report": content,
                "weather1": weather1,
                "weather2": weather2,
                "timestamp": current_timestamp(),
                "timestamp_update": timestamp_update,
                "timestamp_complete": timestamp_complete,
                "delay": delay,
                "scenario": scenario
            }
        })

    # noinspection PyUnusedLocal,PyShadowingNames
    async def update_path(self, user, cycle, path_new):
        quests.update_one({
            "user_id": str(user.id), "quest1.cycle": cycle}, {
            "$set": {
                "quest1.$.current_path": path_new,
                "quest1.$.timestamp": current_timestamp(),
                "quest1.$.hints": ["locked", "locked", "locked", "locked", "locked"]
            },
            "$inc": {
                "quest1.$.paths_unlocked": 1
            }
        })
        await self.logging(f"Shifting {user.name}'s current path to {path_new}")

    async def penalize(self, user, cycle, points):
        quests.update_one({"user_id": str(user.id), "quest1.cycle": cycle}, {"$inc": {"quest1.$.score": -points}})
        await self.logging(f"Penalizing {user.name} for {points} points")

    async def action_update(self, user, cycle, actions):
        quests.update_one({"user_id": str(user.id), "quest1.cycle": cycle}, {"$inc": {"quest1.$.actions": actions}})
        await self.logging(f"Adding {actions} action point/s for {user}")

    async def update_hint(self, user, cycle, hint):
        await self.logging("Updating and adding hints locked")
        quests.update_one({
            "user_id": str(user.id), "quest1.cycle": cycle}, {
            "$set": {
                f"quest1.$.hints.{hint}": "unlocked",
                f"quest1.$.timestamp": current_timestamp()
            },
            "$inc": {
                f"quest1.$.hints_unlocked": 1
            }
        })

    async def expecto(self, guild, user, channel, message):
        role_star = discord.utils.get(guild.roles, name="🌟")
        cycle, path, timestamp, user_hints, actions, purchase = get_data(user)

        if path == "path3":
            await message.add_reaction("❎")
            await self.update_path(user, cycle, path_new="path10")
            await self.penalize(user, cycle, points=5)

        elif path == "path10":
            await message.add_reaction("❔")
            await self.penalize(user, cycle, points=15)

        elif user in role_star.members:
            async with channel.typing():
                role_dolphin = discord.utils.get(guild.roles, name="🐬")
                role_galleon = discord.utils.get(guild.roles, name="💰")
                role_owl = discord.utils.get(guild.roles, name="🦉")
                cycle, path, timestamp, user_hints, actions, purchase = get_data(user)
                uppers = len([char for char in message.content if char.isupper()])
                lowers = len([char for char in message.content if char.islower()])
                symbol = len([char for char in message.content if char == "!"])
                strength = round((uppers * 1.35) + lowers + (symbol * 1.5), 2)
                strength = round(random.uniform(strength - 5, strength + 5), 2)

                if strength > 100:
                    strength = round(random.uniform(98, 99.99), 2)

                added_points = round(75 * (strength / 100))

                score, timestamp_start, patronus_summon, hints_unlocked, owl_final, wand, paths \
                    = get_profile_finished(user)

                t1 = datetime.strptime(timestamp_start, "%Y-%b-%d %HH")
                t2 = datetime.strptime(current_timestamp(), "%Y-%b-%d %HH")
                delta = (t2 - t1).days * 24 + (t2 - t1).seconds // 3600

                patronus_profile = patronus.find_one({
                    "patronus": patronus_summon.lower()}, {
                    "_id": 0,
                    "trait": 1,
                    "link": 1
                })

                description = \
                    f"• Cycle Score: {score + added_points} points, (+{added_points} bonus points)\n" \
                        f"• Hints unlocked: {hints_unlocked}\n" \
                        f"• Paths unlocked: {paths}\n" \
                        f"• Owl: {owl_final.title()} [{patronus_profile['trait'].title()}]"

                quests.update_one({
                    "user_id": str(user.id), "quest1.cycle": cycle}, {
                    "$inc": {
                        "quest1.$.cycle": added_points
                    },
                    "$set": {
                        "quest1.$.strength": strength
                    }
                })

                embed = discord.Embed(
                    color=0x50e3c2,
                    title=f"Your Patronus: {patronus_summon.title()} | Strength: {strength}%",
                    description=description
                )
                embed.set_image(url=patronus_profile["link"])
                embed.set_footer(text=f"Hours spent: {delta} hours")
                embed.set_author(
                    name=f"{user.name} | Cycle #{cycle} results!",
                    icon_url=user.avatar_url
                )
                embed.add_field(
                    name="Wand Properties",
                    value=f"{wand['length']} inches, {wand['flexibility']}, {wand['core'].replace(' ', '-')}-cored, "
                    f"{wand['wood']} wand"
                )
                content = f"{user.mention}, 🎊 **Congratulations!** You have finished the quest!"
                await user.remove_roles(role_dolphin, role_galleon, role_owl, role_star)
                await channel.send(content=content, embed=embed)

    # noinspection PyTypeChecker,PyUnboundLocalVariable
    @commands.command(aliases=["cycle"])
    async def show_cycle(self, ctx, user: discord.Member = None, *, args):

        requestor = ctx.message.author
        requestor_profile = quests.find_one({"user_id": str(requestor)}, {"_id": 0}) is None

        if requestor_profile is None:
            await ctx.channel.send("You have to finish your own first cycle first.")

        elif requestor_profile is not None:

            query = quests.aggregate([{
                '$match': {
                    'user_id': str(requestor.id)}}, {
                '$project': {
                    '_id': 0,
                    'cycle': {
                        '$slice': ['$quest1.cycle', -1]
                    }
                }}
            ])

            for result in query:
                profile = result
                break

            if profile["cycle"][0] <= 1:
                await ctx.channel.send("You have to finish your own first cycle first.")

            elif profile["cycle"][0] >= 2:

                try:
                    cycle_query = int(args)
                    profile = get_profile_history(user, cycle_query)
                except ValueError:
                    return

                patronus_summon = profile["quest1"][0]["patronus"]["patronus"]
                score = profile["quest1"][0]["score"]
                timestamp_start = profile["quest1"][0]["timestamp_start"]
                hints_unlocked = profile["quest1"][0]["hints_unlocked"]
                owl_final = profile["quest1"][0]["owl"]
                wand = profile["quest1"][0]["wand"]
                paths = profile["quest1"][0]["paths_unlocked"]
                strength = profile["quest1"][0]["strength"]

                t1 = datetime.strptime(timestamp_start, "%Y-%b-%d %HH")
                t2 = datetime.strptime(current_timestamp(), "%Y-%b-%d %HH")
                delta = (t2 - t1).days * 24 + (t2 - t1).seconds // 3600

                patronus_profile = patronus.find_one({
                    "patronus": patronus_summon.lower()}, {
                    "_id": 0,
                    "trait": 1,
                    "link": 1
                })

                description = \
                    f"• Cycle Score: {score} points\n" \
                        f"• Hints unlocked: {hints_unlocked}\n" \
                        f"• Paths unlocked: {paths}\n" \
                        f"• Owl: {owl_final.title()} [{patronus_profile['trait'].title()}]"

                embed = discord.Embed(
                    color=0x50e3c2,
                    title=f"Your Patronus: {patronus_summon.title()} | Strength: {strength}%",
                    description=description
                )
                embed.set_image(url=patronus_profile["link"])
                embed.set_footer(text=f"Hours spent: {delta} hours")
                embed.set_author(
                    name=f"{user.name} | Cycle #{cycle_query} results",
                    icon_url=user.avatar_url
                )
                embed.add_field(
                    name="Wand Properties",
                    value=f"{wand['length']} inches, {wand['flexibility']}, {wand['core'].replace(' ', '-')}-cored, "
                    f"{wand['wood']} wand"
                )
                await ctx.channel.send(embed=embed)

    @commands.command(aliases=["progress"])
    @commands.has_role("🐬")
    async def show_progress(self, ctx):

        if not check_quest(ctx.message.author):
            return

        elif check_quest(ctx.message.author):
            score, timestamp_start, current_path, cycle, hints_unlocked = get_profile_progress(ctx.message.author)
            t1 = datetime.strptime(timestamp_start, "%Y-%b-%d %HH")
            t2 = datetime.strptime(current_timestamp(), "%Y-%b-%d %HH")
            hours_passed = (t2 - t1).days * 24 + (t2 - t1).seconds // 3600

            description = \
                f"• Current Score: {score}\n" \
                    f"• Hours passed: {hours_passed}\n" \
                    f"• Penalties: {1000 - score}\n" \
                    f"• Current Path: {current_path.capitalize()}\n" \
                    f"• Hints Unlocked: {hints_unlocked}"

            embed = discord.Embed(
                color=ctx.message.author.colour,
                description=description
            )
            embed.set_author(
                name=f"{ctx.message.author}'s Cycle #{cycle}",
                icon_url=ctx.message.author.avatar_url
            )
            await ctx.message.author.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):

        if str(payload.emoji) != "🐬":
            return

        elif self.client.get_user(payload.user_id).bot is True:
            return

        server = self.client.get_guild(payload.guild_id)
        role_dolphin = discord.utils.get(server.roles, name="🐬")
        user = self.client.get_user(payload.user_id)

        if user in role_dolphin.members:
            return

        request = books.find_one({
            "server": f"{payload.guild_id}"}, {
            "_id": 0, "welcome": 1, "sorting": 1, "letter": 1
        })

        if str(payload.emoji) == "🐬" and payload.message_id == int(request['letter']):
            member = server.get_member(user.id)

            if quests.find_one({"user_id": str(user.id)}, {"_id": 0}) is None:
                profile = {"user_id": str(payload.user_id), "server": str(payload.guild_id), "quest1": []}
                quests.insert_one(profile)
                await self.logging(f"Successfully created quest profile for {user}")

            # Cycle creation
            for i in (range(300)):
                cycle = i + 1

                if len(quests.find_one({"user_id": str(payload.user_id)}, {"_id": 0})["quest1"]) < cycle:
                    quests.update_one({
                        "user_id": str(user.id)}, {
                        "$push": {
                            "quest1": dict(
                                status="ongoing",
                                cycle=cycle,
                                score=1000,
                                timestamp=current_timestamp(),
                                timestamp_start=current_timestamp(),
                                current_path="path0",
                                paths_unlocked=0,
                                actions=0,
                                purchase=True,
                                hints_unlocked=0,
                                hints=["locked", "locked", "locked", "locked", "locked"]
                            )
                        }
                    })
                    await self.logging(f"Successfully started `cycle#{cycle}` for {user}")
                    break

            await member.add_roles(role_dolphin)
            responses = get_dictionary("start_quest")

            async with user.typing():
                await asyncio.sleep(3)
                await user.send(responses["1"])
                await asyncio.sleep(5)
                await user.send(responses["2"])
                await asyncio.sleep(6)
                await user.send(responses["3"])
                await asyncio.sleep(5)
                await user.send(responses["4"])
                await asyncio.sleep(5)
                msg = await user.send(responses["5"])
                await asyncio.sleep(2)
                await msg.add_reaction("✉")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):

        if user == self.client.user:
            return

        elif user.bot:
            return

        elif str(reaction.emoji) == "✉" and user != self.client.user \
                and "envelope" in reaction.message.content and reaction.message.author == self.client.user:

            cycle, path, timestamp, user_hints, actions, purchase = get_data(user)
            server = quests.find_one({"user_id": str(user.id)}, {"_id": 0, "server": 1})
            request = books.find_one({
                "server": server["server"]}, {
                "_id": 0, "welcome": 1, "sorting": 1, "letter": 1
            })

            description = get_dictionary("start_quest")["letter"].format(
                user.name, request["welcome"], request["sorting"]
            )
            embed = discord.Embed(
                color=0xffff80,
                title="Acceptance Letter",
                description=description
            )
            embed.set_thumbnail(url=self.client.get_guild(int(server["server"])).icon_url)
            await user.send(embed=embed)
            await self.update_path(user, cycle, path_new="path1")
            await self.penalize(user, cycle, points=20)

        elif str(reaction.emoji) == "✉" and "returned with" in reaction.message.content \
                and reaction.message.author == self.client.user:

            server = quests.find_one({"user_id": str(user.id)}, {"_id": 0, "server": 1})
            cycle, path, timestamp, user_hints, actions, purchase = get_data(user)
            description = get_dictionary("send_off")["letter"].format(user.name)
            embed = discord.Embed(color=0xffff80, description=description)
            embed.set_thumbnail(url=self.client.get_guild(int(server["server"])).icon_url)
            await self.penalize(user, cycle, points=25)
            await user.send(embed=embed)

        elif str(reaction.emoji) == "🦉":
            role_owl = discord.utils.get(reaction.message.guild.roles, name="🦉")
            request = books.find_one({"server": f"{reaction.message.guild.id}"}, {"_id": 0, "tower": 1})
            cycle, path, timestamp, user_hints, actions, purchase = get_data(user)

            if user not in role_owl.members:
                await self.penalize(user, cycle, points=30)
                await self.logging(f"{user} tried to sendoff an owl but doesnt have the owl role")

            elif (request["tower"] not in str(reaction.message.content) or
                  "<@!180717337475809281>" not in str(reaction.message.content)) and \
                    "✉" not in str(reaction.message.content):

                await reaction.message.add_reaction("❔")
                await self.penalize(user, cycle, points=10)

            elif (request["tower"] in str(reaction.message.content) or
                  "<@!180717337475809281>" in str(reaction.message.content)) and "✉" in str(reaction.message.content):

                cycle, path, timestamp, user_hints, actions, purchase = get_data(user)

                if path in ["path0", "path2", "path20"]:
                    if path != "path0":
                        await self.update_path(user, cycle, path_new="path4")

                    await self.sendoff_owl(user, cycle)
                    await reaction.message.add_reaction("✅")
                    await asyncio.sleep(2)
                    await reaction.message.delete()

                elif path == "path19":
                    msg = get_dictionary("send_off")["penalize"]
                    await self.penalize(user, cycle, points=20)
                    await user.send(msg)
                    await asyncio.sleep(2)
                    await reaction.message.delete()

    # noinspection PyUnboundLocalVariable
    @commands.command(aliases=["hint"])
    @commands.has_role("🐬")
    async def hint_request(self, ctx):

        user = ctx.message.author
        cycle, path, timestamp, user_hints, actions, purchase = get_data(user)
        t1 = datetime.strptime(timestamp, "%Y-%b-%d %HH")
        t2 = datetime.strptime(current_timestamp(), "%Y-%b-%d %HH")
        delta = (t2 - t1).days * 24 + (t2 - t1).seconds // 3600

        # Hint cooldown of 3 hours  # if delta <= 2:
        if delta >= 101:

            await ctx.channel.send(f"{user.mention}, you must wait for {3 - delta} hr before you can reveal a hint")
            await self.logging(f"{user} used hint while on cooldown")

        # More than 3 hours passed  # elif delta >= 3:
        elif delta <= 100:
            with open("data/hints.json") as f:
                hints = json.load(f)

            try:
                h = 0
                while h <= 5:  # Iterating through locked hints

                    if user_hints[h] == "locked":
                        hint_num = str(h + 1)
                        hint = hints[path][hint_num]
                        break
                    h += 1

                embed = discord.Embed(
                    color=user.colour,
                    description="*\"" + hint + "\"*"
                )
                embed.set_footer(
                    icon_url=user.avatar_url,
                    text=f"Path {path[4::]} | Hint# {hint_num}"
                )

                await self.update_hint(user, cycle, h)
                await self.penalize(user, cycle, points=10)
                await ctx.message.add_reaction("✅")
                await user.send(embed=embed)
                await self.logging(f"Sent a hint for {user} | {path}:{hint_num}")

            except IndexError:
                await user.send(f"You have used up all your hints for the path.")
                await self.logging(f"{user} has used up all their hints | {path}")

            except KeyError:
                await user.send(f"You have used up all your hints for the path.")
                await self.logging(f"{user} has used up all their hints | {path}")

    # noinspection PyMethodMayBeStatic
    async def secret_response(self, guild_id, channel_name, description):
        secret = books.find_one({"server": str(guild_id)}, {"_id": 0, str(channel_name): 1})
        webhook_url = secret[str(channel_name)]["webhook"]
        avatar = secret[str(channel_name)]["avatar"]
        username = secret[str(channel_name)]["username"]
        webhook = DiscordWebhook(url=webhook_url, avatar_url=avatar, username=username)
        embed = DiscordEmbed(color=0xffffff, description="*\"" + description + "\"*")
        webhook.add_embed(embed)
        webhook.execute()

    # noinspection PyUnboundLocalVariable
    @commands.command(aliases=["knock", "inquire"])
    @commands.has_role("🐬")
    async def knocking(self, ctx):

        if str(ctx.channel.name) != "eeylops-owl-emporium":
            return

        elif str(ctx.channel.name) == "eeylops-owl-emporium":
            user = ctx.author
            cycle, path, timestamp, user_hints, actions, purchase = get_data(user)

            # noinspection PyShadowingNames
            if actions == 3:
                if ctx.message.content in [";knock", ";inquire"]:
                    await ctx.message.delete()

            elif ctx.message.content == ";knock":
                if path == "path6":
                    await self.update_path(user, cycle, path_new="path9")
                elif path == "path15":
                    await self.update_path(user, cycle, path_new="path16")

                responses = get_dictionary("eeylops_owl")
                msg = responses["knock"][0]
                topic = responses["knock"][1]
                await ctx.channel.edit(topic=topic)
                await ctx.message.delete()
                await self.secret_response(ctx.guild.id, ctx.channel.name, msg)
                await self.penalize(user, cycle, points=15)

            elif ctx.message.content == ";inquire":
                if path == "path9":
                    await self.update_path(user, cycle, path_new="path14")
                elif path == "path15":
                    await self.update_path(user, cycle, path_new="path16")

                responses = get_dictionary("eeylops_owl")["inquire"]
                msg, topic = responses[actions]
                await ctx.channel.edit(topic=topic)
                await ctx.message.delete()
                await self.action_update(user, cycle, actions=1)
                await self.penalize(user, cycle, points=15)
                await self.secret_response(ctx.guild.id, ctx.channel.name, msg)

    # noinspection PyShadowingNames
    @commands.command(aliases=["purchase"])
    @commands.has_role("🐬")
    async def buy_items(self, ctx, *args):

        if ctx.channel.name != "eeylops-owl-emporium":
            return

        elif ctx.channel.name == "eeylops-owl-emporium":
            try:
                owl_buy = args[0].lower()
            except IndexError:
                return

            user = ctx.author
            cycle, path, timestamp, user_hints, actions, purchase = get_data(user)
            responses = get_dictionary("eeylops_owl")

            if purchase is False:
                msg = responses["purchasing"]["max_actions"]
                await self.penalize(user, cycle, points=5)
                await user.send(msg)
                await ctx.message.delete()

            elif owl_buy not in owls_list:
                msg = responses["purchasing"]["invalid_owl"]
                await self.penalize(user, cycle, points=20)
                await self.secret_response(ctx.guild.id, ctx.channel.name, msg)
                await ctx.message.delete()

            elif owl_buy in owls_list:
                purchaser_id = owls.find_one({"type": f"{owl_buy}"}, {"_id": 0, "purchaser": 1})["purchaser"]
                role_owl = discord.utils.get(ctx.guild.roles, name="🦉")
                role_galleons = discord.utils.get(ctx.guild.roles, name="💰")

                if user in role_owl.members:
                    msg = responses["purchasing"]["buying_again"][0].format(user.display_name)
                    topic = responses["purchasing"]["buying_again"][1]
                    await self.penalize(user, cycle, points=75)
                    await self.secret_response(ctx.guild.id, ctx.channel.name, msg)
                    await ctx.channel.edit(topic=topic)
                    await ctx.message.delete()

                elif user not in role_galleons.members:
                    msg = responses["purchasing"]["no_moneybag"][0].format(user.display_name)
                    topic = responses["purchasing"]["no_moneybag"][1]
                    await self.update_path(user, cycle, path_new="path7")
                    await self.penalize(user, cycle, points=5)
                    await self.secret_response(ctx.guild.id, ctx.channel.name, msg)
                    await ctx.channel.edit(topic=topic)
                    await ctx.message.delete()

                    quests.update_one({
                        "user_id": str(user.id), "quest1.cycle": cycle}, {
                        "$set": {
                            "quest1.$.purchase": False
                        }
                    })

                elif purchaser_id != "None":
                    purchaser = ctx.guild.get_member(int(purchaser_id))
                    msg = responses["purchasing"]["out_of_stock"][0].format(user.display_name, purchaser.display_name)
                    topic = responses["purchasing"]["out_of_stock"][1]
                    await self.update_path(user, cycle, path_new="path24")
                    await self.penalize(user, cycle, points=10)
                    await self.secret_response(ctx.guild.id, ctx.channel.name, msg)
                    await ctx.channel.edit(topic=topic)
                    await ctx.message.delete()

                    quests.update_one({
                        "user_id": str(user.id), "quest1.cycle": cycle}, {
                        "$set": {
                            "quest1.$.purchase": False
                        }
                    })

                elif purchaser_id == "None":
                    async with ctx.channel.typing():
                        role_owl = discord.utils.get(ctx.guild.roles, name="🦉")
                        owl_profile = owls.find_one({"type": owl_buy}, {"_id": 0})
                        description = owl_profile["description"]
                        msg = responses["purchasing"]["success_purchase"][0].format(user.display_name)
                        topic = responses["purchasing"]["success_purchase"][1]

                        embed = discord.Embed(
                            title=f"🦉 {owl_profile['type'].title()} | {owl_profile['trait'].capitalize()}",
                            description="*" + description + "*",
                            color=user.colour
                        )
                        embed.set_thumbnail(url=owl_profile["thumbnail"])

                        owls.update_one({"type": owl_buy}, {"$set": {"purchaser": str(user.id)}})
                        sendoff.insert_one({"user_id": str(user.id), "type": owl_buy, "cycle": cycle})
                        quests.update_one({
                            "user_id": str(user.id),
                            "quest1.cycle": cycle}, {
                            "$set": {
                                "quest1.$.purchase": False,
                                "quest1.$.owl": owl_buy
                            }
                        })
                        await ctx.channel.edit(topic=topic)

                        if path != "path0":
                            await self.update_path(user, cycle, path_new="path2")

                        await user.add_roles(role_owl)
                        await ctx.channel.send(f"{user.mention} has acquired 🦉 role")
                        await ctx.message.add_reaction("🦉")
                        await asyncio.sleep(2)
                        await self.secret_response(ctx.guild.id, ctx.channel.name, msg)
                        await asyncio.sleep(3)
                        await ctx.channel.send(embed=embed)
                        await asyncio.sleep(2)
                        await ctx.message.delete()

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author == self.client.user:
            return

        elif message.author.bot:
            return

        elif isinstance(message.channel, discord.DMChannel):
            return

        elif not check_quest(message.author):
            return

        elif message.content.lower() == "eeylops owl emporium" and str(
                message.channel.category) == "⛲ Diagon Alley" and str(message.channel) != "eeylops-owl-emporium":

            role_dolphin = discord.utils.get(message.guild.roles, name="🐬")

            if message.author in role_dolphin.members:
                await self.create_emporium(message.channel.category, message.guild,
                                           message.content.lower(), message, message.author)

        elif message.content.lower() in ["gringotts bank", "gringotts wizarding bank"] \
                and str(message.channel.category) == "⛲ Diagon Alley" and str(message.channel) != "gringotts-bank":

            role_dolphin = discord.utils.get(message.guild.roles, name="🐬")

            if message.author in role_dolphin.members:
                await self.create_gringotts(message.channel.category, message.guild,
                                            message.content.lower(), message, message.author)

        elif message.content.lower() == "ollivanders" and str(message.channel.category) == "⛲ Diagon Alley" \
                and str(message.channel) != "ollivanders":

            role_dolphin = discord.utils.get(message.guild.roles, name="🐬")

            if message.author in role_dolphin.members:
                await self.create_ollivanders(message.channel.category, message.guild,
                                              message.content.lower(), message, message.author)

        elif "gringotts-bank" == str(message.channel) and message.content.startswith(";") is False:
            await self.transaction_gringotts(message.author, message.guild, message)

        elif spell_check(message.content):
            await self.expecto(message.guild, message.author, message.channel, message)

    async def create_emporium(self, category, guild, msg, message, user):

        role_owl = discord.utils.get(guild.roles, name="🦉")
        role_galleons = discord.utils.get(guild.roles, name="💰")
        channels = [channel.name for channel in category.text_channels]
        cycle, path, timestamp, user_hints, actions, purchase = get_data(user)

        await self.logging(f"{user} tried to open a secret channel `{msg} opened at 07:00 - 14:00`")

        if "eeylops-owl-emporium" not in channels:  # and 7 <= int(current_time2()) <= 14:  # 07:00 - 14:00

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True),
                guild.get_member(user.id): discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    read_message_history=False
                )
            }

            emporium = await guild.create_text_channel("eeylops-owl-emporium", category=category, overwrites=overwrites)
            await generate_data(guild, msg, emporium)
            await message.add_reaction("✨")

            if user not in role_owl.members and user not in role_galleons.members:
                await self.update_path(user, cycle, path_new="path6")

            await asyncio.sleep(3)
            await message.delete()

        elif "eeylops-owl-emporium" in channels:  # and 7 <= int(current_time2()) <= 14:  # 07:00 - 14:00

            emporium_id = books.find_one({
                "server": str(guild.id)}, {
                "eeylops-owl-emporium": 1
            })

            emporium_channel = self.client.get_channel(int(emporium_id["eeylops-owl-emporium"]["id"]))

            await emporium_channel.set_permissions(
                user, read_messages=True,
                send_messages=True,
                read_message_history=False
            )
            await message.add_reaction("✨")

            if user not in role_owl.members and user not in role_galleons.members:
                await self.update_path(user, cycle, path_new="path6")

            await asyncio.sleep(3)
            await message.delete()

        else:
            await reaction_closed(message)

    async def create_gringotts(self, category, guild, msg, message, user):
        role_galleons = discord.utils.get(message.guild.roles, name="💰")
        channels = [channel.name for channel in category.text_channels]
        cycle, path, timestamp, user_hints, actions, purchase = get_data(user)
        list_thieves = thieves.find_one({}, {"_id": 0, "names": 1})["names"]

        list_thieves_name = []
        for thief in list_thieves:
            try:
                list_thieves_name.append(guild.get_member(int(thief)).display_name)
            except AttributeError:
                continue

        formatted_thieves = "\n".join(list_thieves_name)
        topic = f"List of Potential Thieves:\n{formatted_thieves}"
        await self.logging(f"{user} tried to open a secret channel `{msg} opened at 08:00 - 15:00`")

        # Topic creation
        if "gringotts-bank" not in channels:  # and 8 <= int(current_time2()) <= 15:  # 08:00 - 15:00

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True),
                guild.get_member(user.id): discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    read_message_history=False
                )
            }

            gringotts = await guild.create_text_channel(
                "gringotts-bank",
                category=category,
                overwrites=overwrites,
                topic=topic
            )
            await generate_data(guild, "gringotts-bank", gringotts)
            await message.add_reaction("✨")

            if user not in role_galleons.members:
                if path not in ["path8", "path18", "path12", "path13"]:
                    await self.update_path(user, cycle, path_new="path8")
                await asyncio.sleep(3)
                await message.delete()
            else:
                await asyncio.sleep(3)
                await message.delete()
                await self.penalize(user, cycle, points=30)

        elif "gringotts-bank" in channels:  # and 8 <= int(current_time2()) <= 15:  # 08:00 - 15:00

            gringotts_id = books.find_one({"server": str(guild.id)}, {"gringotts-bank": 1})["gringotts-bank"]["id"]
            gringotts_channel = self.client.get_channel(int(gringotts_id))

            await gringotts_channel.set_permissions(
                user,
                read_messages=True,
                send_messages=True,
                read_message_history=False
            )
            await message.add_reaction("✨")
            await gringotts_channel.edit(topic=topic)

            if user not in role_galleons.members:
                if path not in ["path8", "path18", "path12", "path13"]:
                    await self.update_path(user, cycle, path_new="path8")
                await asyncio.sleep(3)
                await message.delete()
            else:
                await asyncio.sleep(3)
                await message.delete()
                await self.penalize(user, cycle, points=30)
        else:
            await reaction_closed(message)

    async def create_ollivanders(self, category, guild, msg, message, user):
        channels = [channel.name for channel in category.text_channels]
        cycle, path, timestamp, user_hints, actions, purchase = get_data(user)
        await self.logging(f"{user} tried to open a secret channel `{msg} opened at 1PM-4PM`")

        if "ollivanders" not in channels:  # and 13 <= int(current_time2()) <= 16:  # 1PM-4PM:

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True),
                guild.get_member(user.id): discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    read_message_history=False
                )
            }

            ollivanders = await guild.create_text_channel("ollivanders", category=category, overwrites=overwrites)
            await generate_data(guild, msg, ollivanders)
            await message.add_reaction("✨")
            await asyncio.sleep(3)
            await message.delete()

            if path in ["path10", "path3"]:
                await self.update_path(user, cycle, path_new="path11")

            await self.transaction_ollivanders(guild, user, ollivanders)

        elif "ollivanders" in channels:  # and 13 <= int(current_time2()) <= 16:  # 1PM-4PM:

            ollivanders_id = books.find_one({"server": str(guild.id)}, {"ollivanders": 1})["ollivanders"]["id"]
            ollivanders_channel = self.client.get_channel(int(ollivanders_id))

            await ollivanders_channel.set_permissions(
                user,
                read_messages=True,
                send_messages=True,
                read_message_history=False
            )
            await message.add_reaction("✨")
            await asyncio.sleep(1)
            await asyncio.sleep(3)
            await message.delete()

            if path in ["path10", "path3"]:
                await self.update_path(user, cycle, path_new="path11")

            await self.transaction_ollivanders(guild, user, ollivanders_channel)

        else:
            await reaction_closed(message)

    async def transaction_ollivanders(self, guild, user, channel):
        cycle, path, timestamp, user_hints, actions, purchase = get_data(user)

        if actions >= 3:
            return

        elif actions < 3:

            role_star = discord.utils.get(guild.roles, name="🌟")
            responses = get_dictionary("ollivanders")
            msg1 = responses["intro1"].format(user.mention)
            msg2 = responses["intro2"].format(user.mention)
            await self.secret_response(guild.id, channel.name, msg1)
            await asyncio.sleep(3)
            await self.secret_response(guild.id, channel.name, msg2)

            def check(guess):
                if guess.author != user:
                    return
                elif guess.content.lower() in ["yes", "yeah", "yea", "maybe"]:
                    return guess.author == user and channel == guess.channel
                else:
                    raise KeyError

            try:
                await self.client.wait_for("message", timeout=30, check=check)

            except asyncio.TimeoutError:
                msg = responses["timeout_intro"].format(user.mention)
                await self.action_update(user, cycle, actions=3)
                await self.secret_response(guild.id, channel.name, msg)

            except KeyError:
                msg = responses["invalid"]
                await self.penalize(user, cycle, points=5)
                await self.action_update(user, cycle, actions=3)
                await self.secret_response(guild.id, channel.name, msg)

            else:
                if user not in role_star.members and path in ["path11", "path3", "path10", "path0"]:
                    msg1 = responses["valid"][0].format(user.mention)
                    msg2 = responses["valid"][1].format(user.mention)
                    topic = responses["valid"][2]
                    await self.action_update(user, cycle, actions=3)
                    await self.secret_response(guild.id, channel.name, msg1)
                    await asyncio.sleep(3)
                    await self.secret_response(guild.id, channel.name, msg2)
                    await channel.edit(topic=topic)
                    await asyncio.sleep(3)
                    await self.wand_personalise(user, guild, channel, cycle, role_star, responses)

                else:
                    msg = responses["valid_no_owl"][0].format(user.mention)
                    topic = responses["valid_no_owl"][1]
                    await self.penalize(user, cycle, points=25)
                    await self.action_update(user, cycle, actions=3)
                    await self.secret_response(guild.id, channel.name, msg)
                    await channel.edit(topic=topic)

    # noinspection PyUnboundLocalVariable,PyMethodMayBeStatic,PyShadowingNames
    async def wand_personalise(self, user, guild, channel, cycle, role_star, responses):

        data = quests.aggregate([{
            "$match": {"user_id": str(user.id)}}, {
            "$project": {
                "_id": 0,
                "quest1": {
                    "$slice": ["$quest1", -1]
                }
            }
        }])

        for profile in data:
            owl = profile["quest1"][0]["owl"]
            break

        trait = owls.find_one({"type": owl}, {"_id": 0, "trait": 1})["trait"]
        msg1 = responses["owl_analysis"][trait][0]
        topic = responses["owl_analysis"][trait][1]

        await self.secret_response(guild.id, channel.name, msg1)
        await channel.edit(topic=topic)
        await asyncio.sleep(9)

        wand_length = await self.get_wand_length(user, guild, channel, responses)

        if wand_length != "Wrong":
            wand_flexibility = await self.get_wand_flexibility(user, guild, channel, responses)

            if wand_flexibility != "Wrong":
                wand_length_category = get_length_category(wand_length)
                wand_flexibility_category = get_flexibility_category(wand_flexibility)

                wood_selection = []
                query = patronus.find({
                    "flexibility": wand_flexibility_category,
                    "length": wand_length_category,
                    "trait": trait.lower()}, {
                    "_id": 0, "wood": 1
                })

                for wand in query:
                    if wand["wood"] not in wood_selection:
                        wood_selection.append(wand["wood"])

                wand_wood = await self.get_wand_wood(user, guild, channel, wood_selection, responses)

                if wand_wood != "Wrong":
                    wand_core = await self.get_wand_core(user, guild, channel, responses)
                    wand_creation = {
                        "flexibility_category": wand_flexibility_category,
                        "flexibility": wand_flexibility,
                        "length_category": wand_length_category,
                        "length": wand_length,
                        "core": wand_core,
                        "trait": trait,
                        "wood": wand_wood
                    }
                    __patronus = patronus.find_one({
                        "flexibility": wand_flexibility_category,
                        "length": wand_length_category,
                        "trait": trait,
                        "core": wand_core,
                        "wood": wand_wood}, {
                        "_id": 0
                    })

                    if __patronus is None:
                        msg = responses["no_patronus"].format(user.display_name)
                        await self.secret_response(guild.id, channel.name, msg)

                    elif __patronus is not None:
                        description = \
                            f"Wood: `{wand_wood.title()}`\n" \
                            f"Length: `{wand_length} in`\n" \
                            f"Flexibility: `{wand_flexibility.title()}`\n" \
                            f"Core: `{wand_core.title()}`"

                        embed = discord.Embed(color=user.colour, description=description)
                        embed.set_author(
                            name="Wand Properties",
                            icon_url=user.avatar_url
                        )
                        embed.set_footer(text="Confirm purchase? Y/N")

                        msg_confirm = await channel.send(embed=embed)

                        # noinspection PyShadowingNames
                        def check(_answer):
                            return user.id == _answer.author.id \
                                   and _answer.content.lower() in ["y", "n"] \
                                   and msg_confirm.channel.id == _answer.channel.id

                        while True:
                            try:
                                answer = await self.client.wait_for("message", timeout=120, check=check)

                            except asyncio.TimeoutError:
                                msg = responses["timeout_response"].format(user.mention)
                                await self.penalize(user, cycle, points=20)
                                await self.secret_response(guild.id, channel.name, msg)
                                break

                            else:
                                if answer.content.lower() == "y":
                                    msg = f"{user.mention} has acquired 🌟 role"
                                    quests.update_one({
                                        "user_id": str(user.id),
                                        "quest1.cycle": cycle}, {
                                        "$set": {
                                            "quest1.$.wand": wand_creation,
                                            "quest1.$.patronus": __patronus
                                        }
                                    })

                                    await user.add_roles(role_star)
                                    await channel.send(msg)
                                    break

                                elif answer.content.lower() == "n":
                                    msg = responses["timeout_response"].format(user.mention)
                                    cycle, path, timestamp, user_hints, actions, purchase = get_data(user)

                                    if path == "path0":
                                        await self.update_path(user, cycle, path_new="path17")

                                    await self.penalize(user, cycle, points=20)
                                    await self.secret_response(guild.id, channel.name, msg)
                                    break

    # noinspection PyUnboundLocalVariable
    async def get_wand_core(self, user, guild, channel, responses):

        formatted_cores = "`, `".join(cores)
        msg = responses["core_selection"]["1"].format(user.mention, formatted_cores)
        await asyncio.sleep(1)
        await self.secret_response(guild.id, channel.name, msg)
        cycle, path, timestamp, user_hints, actions, purchase = get_data(user)

        def check(guess):
            if guess.channel != channel or guess.author != user:
                return False
            elif guess.content.lower() in cores and guess.author == user and channel == guess.channel:
                return True
            elif guess.content.lower() not in cores and guess.author == user and channel == guess.channel:
                raise KeyError

        i = 0
        while i < 2:
            try:
                answer = await self.client.wait_for("message", timeout=60, check=check)

            except asyncio.TimeoutError:
                msg = responses["core_selection"]["timeout"]
                wand_core = "Wrong"

                if path == "path0":
                    await self.update_path(user, cycle, path_new="path17")

                await self.action_update(user, cycle, actions=3)
                await self.penalize(user, cycle, points=10)
                await self.secret_response(guild.id, channel.name, msg)
                break

            except KeyError:

                if path == "path0":
                    await self.update_path(user, cycle, path_new="path17")

                if i == 0:
                    msg = responses["core_selection"]["invalid1"][0].format(answer.content.title())
                    topic = responses["core_selection"]["invalid1"][1]
                    await channel.edit(topic=topic)
                    await self.penalize(user, cycle, points=5)

                elif i == 1:
                    wand_core = "Wrong"
                    msg = responses["core_selection"]["invalid2"][0].format(answer.content.title())
                    topic = responses["core_selection"]["invalid2"][1]
                    await self.action_update(user, cycle, actions=3)
                    await self.penalize(user, cycle, points=10)
                    await channel.edit(topic=topic)

                await self.secret_response(guild.id, channel.name, msg)
                i += 1

            else:
                wand_core = answer.content
                msg = responses["core_selection"]["chose"][0].format(
                    wand_core.capitalize(),
                    responses["core_description"][f'{wand_core.lower()}']
                )
                topic = responses["core_selection"]["chose"][1]
                await channel.edit(topic=topic)
                await self.secret_response(guild.id, channel.name, msg)
                break

        await self.logging(f"{user} is trying to personalise wand: -> awaits core -> Ended")
        return wand_core.lower()

    # noinspection PyUnboundLocalVariable
    async def get_wand_wood(self, user, guild, channel, wood_selection, responses):

        formatted_woods = "`, `".join(wood_selection)
        msg = responses["wood_selection"]["1"].format(user.mention, formatted_woods)
        await asyncio.sleep(1)
        await self.secret_response(guild.id, channel.name, msg)
        cycle, path, timestamp, user_hints, actions, purchase = get_data(user)

        def check(guess):
            if guess.channel != channel or guess.author != user:
                return False
            elif guess.content.lower() in wood_selection and guess.author == user and channel == guess.channel:
                return True
            elif guess.content.lower() not in wood_selection and guess.author == user and channel == guess.channel:
                raise KeyError

        i = 0
        while i < 2:
            try:
                answer = await self.client.wait_for("message", timeout=60, check=check)

            except asyncio.TimeoutError:
                wand_wood = "Wrong"
                msg = responses["wood_selection"]["timeout"]

                if path == "path0":
                    await self.update_path(user, cycle, path_new="path17")

                await self.penalize(user, cycle, points=15)
                await self.action_update(user, cycle, actions=3)
                await self.secret_response(guild.id, channel.name, msg)
                break

            except KeyError:

                if path == "path0":
                    await self.update_path(user, cycle, path_new="path17")

                if i == 0:
                    msg = responses["wood_selection"]["invalid1"][0].format(answer.content.title())
                    topic = responses["wood_selection"]["invalid1"][1]
                    await channel.edit(topic=topic)
                    await self.penalize(user, cycle, points=5)

                elif i == 1:
                    wand_wood = "Wrong"
                    msg = responses["wood_selection"]["invalid2"][0].format(answer.content.title())
                    topic = responses["wood_selection"]["invalid2"][1]
                    await self.action_update(user, cycle, actions=3)
                    await self.penalize(user, cycle, points=10)
                    await channel.edit(topic=topic)

                await self.secret_response(guild.id, channel.name, msg)
                i += 1

            else:
                wand_wood = answer.content
                msg = responses["wood_selection"]["chose"][0].format(
                    wand_wood.capitalize(),
                    responses["wood_description"][f'{wand_wood.lower()}']
                )
                topic = responses["wood_selection"]["chose"][1]
                await channel.edit(topic=topic)
                await self.secret_response(guild.id, channel.name, msg)
                break

        await self.logging(f"{user} is trying to personalise wand: -> awaits wood -> Ended")
        return wand_wood.lower()

    # noinspection PyUnboundLocalVariable
    async def get_wand_length(self, user, guild, channel, responses):
        msg = responses["length_selection"]["1"].format(user.mention)
        await asyncio.sleep(1)
        await self.secret_response(guild.id, channel.name, msg)
        cycle, path, timestamp, user_hints, actions, purchase = get_data(user)

        def check(guess):
            if guess.channel != channel or guess.author != user:
                return False
            elif guess.content in wand_lengths and guess.author == user and channel == guess.channel:
                return True
            elif guess.content not in wand_lengths and guess.author == user and channel == guess.channel:
                raise KeyError

        i = 0
        while i < 2:

            try:
                answer = await self.client.wait_for("message", timeout=120, check=check)

            except asyncio.TimeoutError:
                wand_length = "Wrong"
                msg = responses["length_selection"]["timeout"]

                if path == "path0":
                    await self.update_path(user, cycle, path_new="path17")

                await self.penalize(user, cycle, points=15)
                await self.action_update(user, cycle, actions=3)
                await self.secret_response(guild.id, channel.name, msg)
                break

            except KeyError:

                if path == "path0":
                    await self.update_path(user, cycle, path_new="path17")

                if i == 0:
                    msg = responses["length_selection"]["invalid1"][0].format(answer.content.title())
                    topic = responses["length_selection"]["invalid1"][1]
                    await channel.edit(topic=topic)
                    await self.penalize(user, cycle, points=5)

                elif i == 1:
                    wand_length = "Wrong"
                    msg = responses["length_selection"]["invalid2"][0].format(answer.content.title())
                    topic = responses["length_selection"]["invalid2"][1]
                    await self.action_update(user, cycle, actions=3)
                    await self.penalize(user, cycle, points=10)
                    await channel.edit(topic=topic)

                await self.secret_response(guild.id, channel.name, msg)
                i += 1

            else:
                wand_length = answer.content
                msg = responses["length_selection"]["chose"][0].format(wand_length)
                topic = responses["length_selection"]["chose"][1]
                await channel.edit(topic=topic)
                await self.secret_response(guild.id, channel.name, msg)
                break

        await self.logging(f"{user} is trying to personalise wand: -> awaits length -> Ended")
        return wand_length

    # noinspection PyUnboundLocalVariable
    async def get_wand_flexibility(self, user, guild, channel, responses):

        formatted_flexibility = "`, `".join(flexibility_types)
        msg = responses["flexibility_selection"]["1"].format(user.mention, formatted_flexibility)
        await asyncio.sleep(2)
        await self.secret_response(guild.id, channel.name, msg)
        cycle, path, timestamp, user_hints, actions, purchase = get_data(user)

        def check(guess):
            if guess.channel != channel or guess.author != user:
                return False
            elif guess.content.lower() in flexibility_types and guess.author == user and channel == guess.channel:
                return True
            elif guess.content.lower() not in flexibility_types and guess.author == user and channel == guess.channel:
                raise KeyError

        i = 0
        while i < 2:
            try:
                answer = await self.client.wait_for("message", timeout=60, check=check)

            except asyncio.TimeoutError:
                wand_flexibility = "Wrong"
                msg = responses["flexibility_selection"]["timeout"]

                if path == "path0":
                    await self.update_path(user, cycle, path_new="path17")

                await self.penalize(user, cycle, points=15)
                await self.action_update(user, cycle, actions=3)
                await self.secret_response(guild.id, channel.name, msg)
                break

            except KeyError:

                if path == "path0":
                    await self.update_path(user, cycle, path_new="path17")

                if i == 0:
                    msg = responses["flexibility_selection"]["invalid1"][0].format(answer.content.title())
                    topic = responses["flexibility_selection"]["invalid1"][1]
                    await channel.edit(topic=topic)
                    await self.penalize(user, cycle, points=5)

                elif i == 1:
                    wand_flexibility = "Wrong"
                    msg = responses["flexibility_selection"]["invalid2"][0].format(answer.content.title())
                    topic = responses["flexibility_selection"]["invalid2"][1]
                    await self.action_update(user, cycle, actions=3)
                    await self.penalize(user, cycle, points=10)
                    await channel.edit(topic=topic)

                await self.secret_response(guild.id, channel.name, msg)
                i += 1

            else:
                wand_flexibility = answer.content
                msg = responses["flexibility_selection"]["chose"][0].format(wand_flexibility.title())
                topic = responses["flexibility_selection"]["chose"][1]
                await channel.edit(topic=topic)
                await self.secret_response(guild.id, channel.name, msg)
                break

        await self.logging(f"{user} is trying to personalise wand: -> awaits flexibility -> Ended")
        return wand_flexibility.lower()

    async def transaction_gringotts(self, user, guild, message):

        role_galleons = discord.utils.get(message.guild.roles, name="💰")
        cycle, path, timestamp, user_hints, actions, purchase = get_data(user)
        responses = get_dictionary("gringotts_bank")

        if user in role_galleons.members:
            msg = responses["has_moneybag"].format(user.display_name)
            await self.secret_response(guild.id, message.channel.name, msg)
            await self.action_update(user, cycle, actions=3)
            await self.penalize(user, cycle, points=20)

        elif user not in role_galleons.members:

            if actions >= 3:
                return

            elif actions < 3 and "vault" in message.content:
                await self.action_update(user, cycle, actions=5)
                await self.vault_access(user, guild, role_galleons, message, responses)

            elif actions < 3:
                msg = responses["transaction"][actions].format(user.mention)
                await self.secret_response(guild.id, message.channel.name, msg)
                await self.action_update(user, cycle, actions=1)
                await self.penalize(user, cycle, points=10)

    async def vault_access(self, user, guild, role_galleons, message, responses):

        identity = await self.obtain_identity(user, guild, message, responses)

        if identity != "Wrong":
            vault_number = await self.obtain_vault_number(user, guild, message, responses)

            if vault_number != "Wrong":
                vault_password = await self.obtain_vault_password(user, guild, message, responses)

                if vault_password != "Wrong":
                    msg1 = f"{user.mention} has acquired 💰 role"
                    msg2 = responses["success"].format(user.mention)
                    vault = f"{str(user.id).replace('1', '@').replace('5', '%').replace('7', '&').replace('3', '#')}"

                    secret = books.find_one({"server": str(guild.id)}, {"_id": 0, str(message.channel.name): 1})
                    webhook_url = secret[str(message.channel.name)]["webhook"]
                    avatar = secret[str(message.channel.name)]["avatar"]
                    username = secret[str(message.channel.name)]["username"]

                    cycle, path, timestamp, user_hints, actions, purchase = get_data(user)

                    embed = DiscordEmbed(
                        color=0xffffff,
                        title=f"🔐 Opening Vault# {vault}"
                    )
                    embed.set_image(url="https://i.imgur.com/RIS1TLh.gif")

                    webhook = DiscordWebhook(url=webhook_url, avatar_url=avatar, username=username)
                    webhook.add_embed(embed)
                    webhook.execute()

                    if path != "path0":
                        await self.update_path(user, cycle, path_new="path15")

                    await user.add_roles(role_galleons)
                    await asyncio.sleep(6)
                    await message.channel.send(msg1)
                    await self.secret_response(guild.id, message.channel.name, msg2)

                    thieves.update_one({}, {"$pull": {"names": str(user.id)}})

    # noinspection PyUnboundLocalVariable
    async def obtain_identity(self, user, guild, message, responses):

        msg = responses["get_identity"]["1"].format(user.mention)
        await self.secret_response(guild.id, message.channel.name, msg)
        cycle, path, timestamp, user_hints, actions, purchase = get_data(user)

        if path != "path0":
            await self.update_path(user, cycle, path_new="path21")

        # noinspection PyShadowingNames
        def check(guess):
            key = (str(user.avatar_url).rsplit('/', 2)[1:])[1][:32:]
            if guess.channel != message.channel:
                return
            elif str(guess.content) == key and guess.author == user and guess.channel == message.channel:
                return True
            elif guess.author == user and ";" not in str(guess.content):
                raise KeyError

        i = 0
        while i < 3:
            try:
                guess = await self.client.wait_for("message", timeout=120, check=check)

            except asyncio.TimeoutError:
                answer = "Wrong"
                msg = responses["get_identity"]["timeout"][0].format(user.mention)
                topic = responses["get_identity"]["timeout"][1]

                if thieves.find_one({"names": str(user.id)}, {"_id": 0}) is None:
                    thieves.update_one({}, {"$push": {"names": str(user.id)}})

                await self.update_path(user, cycle, path_new="path18")
                await self.action_update(user, cycle, actions=3)
                await self.penalize(user, cycle, points=10)
                await self.secret_response(guild.id, message.channel.name, msg)
                await message.channel.edit(topic=topic)
                break

            except KeyError:

                if i == 0:
                    msg = responses["get_identity"]["invalid1"][0].format(user.mention)
                    topic = responses["get_identity"]["invalid1"][1]
                    await self.penalize(user, cycle, points=5)

                elif i == 1:
                    msg = responses["get_identity"]["invalid2"][0].format(user.mention)
                    topic = responses["get_identity"]["invalid2"][1]
                    await self.penalize(user, cycle, points=5)

                elif i == 2:
                    msg = responses["get_identity"]["invalid3"][0].format(user.mention)
                    topic = responses["get_identity"]["invalid3"][1]

                    if thieves.find_one({"names": str(user.id)}, {"_id": 0}) is None:
                        thieves.update_one({}, {"$push": {"names": str(user.id)}})

                    await self.update_path(user, cycle, path_new="path18")
                    await self.action_update(user, cycle, actions=3)
                    await self.penalize(user, cycle, points=10)

                await message.channel.edit(topic=topic)
                await self.secret_response(guild.id, message.channel.name, msg)
                i += 1

            else:
                answer = "Correct"
                await guess.add_reaction("✅")
                await asyncio.sleep(3)
                await guess.delete()
                break

        await self.logging(f"{user} is trying to transact to Gringotts: -> awaits identity -> Ended")
        return answer

    # noinspection PyUnboundLocalVariable
    async def obtain_vault_number(self, user, guild, message, responses):

        msg = responses["get_vault"]["1"].format(user.mention)
        await self.secret_response(guild.id, message.channel.name, msg)
        cycle, path, timestamp, user_hints, actions, purchase = get_data(user)

        if path != "path0":
            await self.update_path(user, cycle, path_new="path22")

        if path == "path18":
            await self.update_path(user, cycle, path_new="path5")

        # noinspection PyShadowingNames
        def check(guess):
            if guess.channel != message.channel:
                return
            elif str(guess.content) == str(user.id) and guess.author == user and guess.channel == message.channel:
                return True
            elif guess.author == user and ";" not in str(guess.content):
                raise KeyError

        i = 0
        while i < 3:
            try:
                guess = await self.client.wait_for("message", timeout=120, check=check)

            except asyncio.TimeoutError:
                answer = "Wrong"
                msg = responses["get_vault"]["timeout"][0].format(user.mention)
                topic = responses["get_vault"]["timeout"][1]

                if thieves.find_one({"names": str(user.id)}, {"_id": 0}) is None:
                    thieves.update_one({}, {"$push": {"names": str(user.id)}})

                await self.update_path(user, cycle, path_new="path12")
                await self.action_update(user, cycle, actions=3)
                await self.penalize(user, cycle, points=10)
                await self.secret_response(guild.id, message.channel.name, msg)
                await message.channel.edit(topic=topic)
                break

            except KeyError:

                if i == 0:
                    msg = responses["get_vault"]["invalid1"][0].format(user.mention)
                    topic = responses["get_vault"]["invalid1"][1]
                    await self.penalize(user, cycle, points=5)

                elif i == 1:
                    msg = responses["get_vault"]["invalid2"][0].format(user.mention)
                    topic = responses["get_vault"]["invalid2"][1]
                    await self.penalize(user, cycle, points=5)

                elif i == 2:
                    answer = "Wrong"
                    msg = responses["get_vault"]["invalid3"][0].format(user.mention)
                    topic = responses["get_vault"]["invalid3"][1]

                    if thieves.find_one({"names": str(user.id)}, {"_id": 0}) is None:
                        thieves.update_one({}, {"$push": {"names": str(user.id)}})

                    await self.update_path(user, cycle, path_new="path12")
                    await self.action_update(user, cycle, actions=3)
                    await self.penalize(user, cycle, points=10)

                await message.channel.edit(topic=topic)
                await self.secret_response(guild.id, message.channel.name, msg)
                i += 1

            else:
                answer = "Correct"
                await guess.add_reaction("✅")
                await asyncio.sleep(3)
                await guess.delete()
                break

        await self.logging(f"{user} is trying to transact to Gringotts: -> awaits vault number -> Ended")
        return answer

    # noinspection PyUnboundLocalVariable
    async def obtain_vault_password(self, user, guild, message, responses):

        msg1 = responses["get_password"]["1"].format(user.mention)
        msg2 = responses["get_password"]["2"].format(user.mention)
        await asyncio.sleep(1)
        await self.secret_response(guild.id, message.channel.name, msg1)
        await asyncio.sleep(3)
        await self.secret_response(guild.id, message.channel.name, msg2)
        cycle, path, timestamp, user_hints, actions, purchase = get_data(user)

        if path != "path0":
            await self.update_path(user, cycle, path_new="path23")

        # noinspection PyShadowingNames
        def check(guess):
            if guess.channel != message.channel:
                return
            elif str(guess.content) == (str(user.id))[::-1] and guess.author == user \
                    and guess.channel == message.channel:
                return True
            elif guess.author == user and ";" not in str(guess.content):
                raise KeyError

        i = 0
        while i < 3:
            try:
                guess = await self.client.wait_for("message", timeout=120, check=check)

            except asyncio.TimeoutError:
                answer = "Wrong"
                msg = responses["get_password"]["timeout"][0].format(user.mention)
                topic = responses["get_password"]["timeout"][1]

                if thieves.find_one({"names": str(user.id)}, {"_id": 0}) is None:
                    thieves.update_one({}, {"$push": {"names": str(user.id)}})

                await self.update_path(user, cycle, path_new="path13")
                await self.action_update(user, cycle, actions=3)
                await self.penalize(user, cycle, points=5)
                await self.secret_response(guild.id, message.channel.name, msg)
                await message.channel.edit(topic=topic)
                break

            except KeyError:

                if i == 0:
                    msg = responses["get_password"]["invalid1"][0].format(user.mention)
                    topic = responses["get_password"]["invalid1"][1]
                    await self.penalize(user, cycle, points=5)

                elif i == 1:
                    msg = responses["get_password"]["invalid2"][0].format(user.mention)
                    topic = responses["get_password"]["invalid2"][1]
                    await self.penalize(user, cycle, points=5)

                elif i == 2:
                    answer = "Wrong"
                    msg = responses["get_password"]["invalid3"][0].format(user.mention)
                    topic = responses["get_password"]["invalid3"][1]

                    if thieves.find_one({"names": str(user.id)}, {"_id": 0}) is None:
                        thieves.update_one({}, {"$push": {"names": str(user.id)}})

                    await self.update_path(user, cycle, path_new="path13")
                    await self.action_update(user, cycle, actions=3)
                    await self.penalize(user, cycle, points=10)

                await message.channel.edit(topic=topic)
                await self.secret_response(guild.id, message.channel.name, msg)
                i += 1

            else:
                answer = "Correct"
                await guess.add_reaction("✅")
                await asyncio.sleep(3)
                await guess.delete()
                break

        await self.logging(f"{user} is trying to transact to Gringotts: -> awaits Ended")
        return answer


def setup(client):
    client.add_cog(Magic(client))
