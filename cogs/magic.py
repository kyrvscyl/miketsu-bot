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

        break

    return score, timestamp_start, patronus_summon, hints_unlocked, owl_final, wand

    # noinspection PyShadowingNames,PyUnboundLocalVariable


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


# noinspection PyUnreachableCode
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

            description = f"Owl Requirements: \n" \
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
        timeout = 60

        while True:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=timeout, check=check)

                if str(reaction.emoji) == "➡":
                    page += 1

                elif str(reaction.emoji) == "⬅":
                    page -= 1

                await msg.edit(embed=create_embed(page))

            except asyncio.TimeoutError:
                return False

    async def sendoff_owl(self, user, cycle):

        await user.send("*Sending off owl to the :trident: Headmaster's Tower*")
        await asyncio.sleep(2)
        await user.send("*You will receive an update when the clock moves an hour*")
        await self.generate_owl_report(user, cycle)
        await self.logging(f"{user} has successfully dispatched their owl to the Headmaster's Office")

    # noinspection PyUnboundLocalVariable,PyUnusedLocal
    async def generate_owl_report(self, user, cycle):

        profile = sendoff.find_one({"user_id": str(user.id), "cycle": cycle}, {"_id": 0})
        weather1 = weather.find_one({"weather1": {"$type": "string"}}, {"weather1": 1})["weather1"]
        weather2 = weather.find_one({"weather2": {"$type": "string"}}, {"weather2": 1})["weather2"]

        if weather1 == "⛈":  # Thunderstorms

            # delay, scenario, report, = 4, 1
            delay, scenario, report, = 2, 1, "Your owl returned to you crawling on its feathers due to the " \
                                             "thunderstorms.\n\nYour owl will recover in 3 hours before you can " \
                                             "send it off again."

            await self.update_path(user, cycle, path_new="path19")

        elif weather1 == "🌨" and profile["type"] == "snowy":  # Snowy owl and Snowy weather

            delay, scenario, report = 2, 2, "Your owl travelled hastily to the Headmaster's Office due to favorable " \
                                            "weather for the owl.\n\nEstimated time of return: in 1 hour"

        elif weather2 == "🌕" or weather2 == "🌑":  # Night

            delay, scenario, report = 2, 2, "Owls are best at night and can return faster than normal travel " \
                                            "time.\n\nEstimated time of return: in 1 hour "

        elif weather1 == "🌧" or weather1 == "🌨":  # Rainy or snowy

            # delay, scenario, report, = 3, 1
            delay, scenario, report = 2, 2, "Your owl struggled to reached the Headmaster's Office on time due to " \
                                            "unfavoured weather.\n\nEstimated time of return: in 2 hours"

        elif weather1 == "☁" or weather1 == "⛅" or weather1 == "☀":  # Cloudy & Partly sunny, or sunny

            delay, scenario, report = 2, 2, "Your owl has safely arrived at the Headmaster's Office.\n\n" \
                                            "Estimated time of return: in 1 hour"

        timestamp_update = (datetime.now(tz=tz_target) + timedelta(days=1 / 24)).strftime("%Y-%b-%d %HH")
        timestamp_complete = (datetime.now(tz=tz_target) + timedelta(days=delay / 24)).strftime("%Y-%b-%d %HH")

        sendoff.update_one({
            "user_id": str(user.id)}, {
            "$set": {
                "report": report,
                "weather1": weather1,
                "weather2": weather2,
                "timestamp": current_timestamp(),
                "timestamp_update": timestamp_update,
                "timestamp_complete": timestamp_complete,
                "delay": delay,
                "scenario": scenario
            }
        })

        await self.logging(
            f"\n-->Generated owl report for {user.name}\n"
            f"--> Report: {report}\n"
            f"--> Weather1: {weather1}\n"
            f"--> Weather2: {weather2}\n"
            f"--> Time of sendoff: {current_timestamp()}\n"
            f"--> Time of sending of update: {timestamp_update}\n"
            f"--> Time of sending of completion: {timestamp_complete}\n"
            f"--> Hours delay of owl: {delay}\n"
            f"--> Scenario: {scenario}\n"
            f"--> Cycle#: {cycle}"
        )

    # noinspection PyUnusedLocal,PyShadowingNames
    async def update_path(self, user, cycle, path_new):

        quests.update_one({
            "user_id": str(user.id), "quest1.cycle": cycle}, {
            "$set": {
                "quest1.$.current_path": path_new,
                "quest1.$.timestamp": current_timestamp(),
                "quest1.$.actions": 0,
                "quest1.$.hints": ["locked", "locked", "locked", "locked", "locked"]
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

    # noinspection PyUnboundLocalVariable
    async def generate_data(self, guild, secret_channel, channel):

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

        await self.logging(f"Generating secret channel: {channel_name} and its webhook")
        await secret_banner(webhook.url, avatar_url, username, url)

    async def reaction_closed(self, message):

        await self.logging("Secret channel is 'CLOSED': Adding reactions and deleting message")
        await message.add_reaction("🇨")
        await message.add_reaction("🇱")
        await message.add_reaction("🇴")
        await message.add_reaction("🇸")
        await message.add_reaction("🇪")
        await message.add_reaction("🇩")
        await asyncio.sleep(4)
        await message.delete()

    async def expecto(self, guild, user, channel, message):

        role_star = discord.utils.get(guild.roles, name="🌟")
        cycle, path, timestamp, user_hints, actions, purchase = get_data(user)

        if path == "path3":

            await message.add_reaction("❎")
            await self.update_path(user, cycle, path_new="path10")
            await self.penalize(user, cycle, points=5)
            await self.logging(f"{user} tried to cast the Patronus charm summoning spell")

        elif path == "path10":

            await message.add_reaction("❔")
            await self.penalize(user, cycle, points=10)
            await self.logging(f"{user} tried to recast the Patronus summoning spell to no avail")

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

                score, timestamp_start, patronus_summon, hints_unlocked, owl_final, wand = get_profile_finished(user)

                t1 = datetime.strptime(timestamp_start, "%Y-%b-%d %HH")
                t2 = datetime.strptime(current_timestamp(), "%Y-%b-%d %HH")
                delta = (t2 - t1).days * 24 + (t2 - t1).seconds // 3600

                patronus_profile = patronus.find_one({
                    "patronus": patronus_summon.lower()}, {
                    "_id": 0,
                    "trait": 1,
                    "link": 1
                })

                description = f"• Cycle Score: {score} points\n" \
                    f"• Hints unlocked: {hints_unlocked}\n" \
                    f"• Owl: {owl_final.title()} [{patronus_profile['trait'].title()}]"

                embed = discord.Embed(
                    color=0x50e3c2,
                    title=f"Your Patronus Strength: {strength}% | {patronus_summon.title()}",
                    description=description
                )
                embed.set_image(url=patronus_profile["link"])
                embed.set_footer(text=f"Hours spent: {delta} hours")
                embed.set_author(
                    name=f"{user.name} | Cycle #{cycle} Results!",
                    icon_url=user.avatar_url
                )
                embed.add_field(
                    name="Wand Properties",
                    value=f"{wand['length']} inches, {wand['flexibility']}, {wand['core'].replace(' ', '-')}-cored, "
                    f"{wand['wood']} wand"
                )

                content = f"{user.mention}, :confetti_ball: **Congratulations!** You have finished the quest!"

                quests.update_one({
                    "user_id": str(user.id),
                    "quest1.cycle": cycle}, {
                    "$set": {
                        "quest1.$.status": "completed"
                    }
                })

                await user.remove_roles(role_dolphin, role_galleon, role_owl, role_star)
                await channel.send(content=content, embed=embed)
                await self.logging(f"{user} successfully finished the quest")

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

            description = f"▫Current Score: {score}\n" \
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
            await self.logging(f"{ctx.message.author} requested to show their progress")

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

                if len(quests.find_one({"user_id": str(payload.user_id)}, {"_id": 0})["quest1"]) != cycle:
                    quests.update_one({
                        "user_id": str(user.id)}, {
                        "$push": {
                            "quest1": dict(
                                status="ongoing",
                                cycle=cycle, score=1000,
                                timestamp=current_timestamp(),
                                timestamp_start=current_timestamp(),
                                current_path="path1", actions=0,
                                purchase=True,
                                hints_unlocked=0,
                                hints=["locked", "locked", "locked", "locked", "locked"]
                            )
                        }
                    })

                    await self.logging(f"Successfully started `cycle#{cycle}` for {user}")
                    break

            await member.add_roles(role_dolphin)
            await self.logging(f"Successfully sent {user} their first clues through DM")
            await self.logging(f"Successfully added dolphin role to {user}")

            msg1 = "~~✨ You have been obliviated.~~"
            msg2 = "*\"You almost lost your consciousness and balance...\"*"
            msg3 = "*\"... and as you opened your eyes, it brought sheer wonder of what exactly happened just a few " \
                   "moments ago..\"* "
            msg4 = "*\"You quickly scanned the surrounding and saw nothing but the one at your hand...\"*"
            msg5 = "*\"It's an envelope with a very familiar wax seal\"*"

            async with user.typing():
                await asyncio.sleep(3)
                await user.send(msg1)
                await asyncio.sleep(5)
                await user.send(msg2)
                await asyncio.sleep(6)
                await user.send(msg3)
                await asyncio.sleep(5)
                await user.send(msg4)
                await asyncio.sleep(5)
                msg = await user.send(msg5)
                await asyncio.sleep(2)
                await msg.add_reaction("✉")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        role_dolphin = discord.utils.get(reaction.message.guild.roles, name="🐬")

        if user == self.client.user:
            return

        elif user.bot:
            return

        elif user not in role_dolphin.members:
            return

        elif str(reaction.emoji) == "✉" and user != self.client.user \
                and "envelope" in reaction.message.content and reaction.message.author == self.client.user:

            cycle, path, timestamp, user_hints, actions, purchase = get_data(user)

            server = quests.find_one({"user_id": str(user.id)}, {"_id": 0, "server": 1})
            request = books.find_one({
                "server": server["server"]}, {
                "_id": 0, "welcome": 1, "sorting": 1, "letter": 1
            })

            description = f"*Dear {user.name},\n\nWe are pleased to accept you at House Patronus.\nDo browse " \
                f"the server's <#{request['welcome']}> channel for the basics and essentials of the guild then " \
                f"proceed to <#{request['sorting']}> to assign yourself some roles.\n\nWe await your return owl.\n\n" \
                f"Yours Truly,\nThe Headmaster*"

            embed = discord.Embed(
                color=0xffff80,
                title="Acceptance Letter",
                description=description
            )
            embed.set_thumbnail(url=self.client.get_guild(int(server["server"])).icon_url)

            await user.send(embed=embed)
            await self.penalize(user, cycle, points=20)
            await self.logging(f"{user} opened the letter of Headmaster invitation letter.")

        elif str(reaction.emoji) == "✉" and "returned with" in reaction.message.content \
                and reaction.message.author == self.client.user:

            server = quests.find_one({"user_id": str(user.id)}, {"_id": 0, "server": 1})
            cycle, path, timestamp, user_hints, actions, purchase = get_data(user)

            description = f"*Dear {user.name},\n\nIt is wondrous to have such another promising magic " \
                f"practitioner. At the castle, everyone there is special, but what makes them " \
                f"more special is their Patronus charm.\n\nYour term awaits soon. Good luck!\n\n" \
                f"Yours Sincerely,\nThe Headmaster*"

            embed = discord.Embed(color=0xffff80, description=description)
            embed.set_thumbnail(url=self.client.get_guild(int(server["server"])).icon_url)

            await self.update_path(user, cycle, path_new="path3")
            await user.send(embed=embed)
            await self.logging(f"{user} opened the letter of Headmaster response.")

        elif str(reaction.emoji) == "🦉":

            role_owl = discord.utils.get(reaction.message.guild.roles, name="🦉")
            request = books.find_one({"server": f"{reaction.message.guild.id}"}, {"_id": 0, "tower": 1})
            cycle, path, timestamp, user_hints, actions, purchase = get_data(user)

            if user not in role_owl.members:
                await self.penalize(user, cycle, points=30)
                await self.logging(f"{user} tried to sendoff an owl but doesnt have the owl role")

            elif (request["tower"] not in str(reaction.message.content) or
                  "180717337475809281" not in str(reaction.message.content)) and \
                    "✉" not in str(reaction.message.content):

                await reaction.message.add_reaction("❔")
                await self.penalize(user, cycle, points=10)
                await self.logging(f"{user} has the owl role but the message is wrong")

            elif (request["tower"] in str(reaction.message.content) or
                  "kyrvscyl#9389" in str(reaction.message.content)) and "✉" in str(reaction.message.content):

                cycle, path, timestamp, user_hints, actions, purchase = get_data(user)

                # Path having the owl roles and haven't sent off yet
                if path == "path2" or path == "path20":

                    await self.update_path(user, cycle, path_new="path4")  # Transfers to waiting path
                    await self.sendoff_owl(user, cycle)
                    await reaction.message.add_reaction("✅")
                    await asyncio.sleep(2)
                    await reaction.message.delete()
                    await self.logging(f"{user} successfully decoded the clue for sending a letter")

                # Punishment path
                elif path == "path19":
                    msg = "*\"Your owl was paralyzed due to the storms. It needs time to heal itself.\"*"

                    await self.penalize(user, cycle, points=20)
                    await user.send(msg)
                    await asyncio.sleep(2)
                    await reaction.message.delete()
                    await self.logging(f"{user} tried to sendoff while owl is recovering")

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

                # Specific hint revelation
                if path == "path15" and ctx.channel.name == "gringotts-bank":

                    await self.penalize(user, cycle, points=20)
                    await ctx.channel.send(f"{user.mention}, don't we have what we wanted here already?")
                    await self.logging(f"{user} transacted with gringotts with moneybag role already | {path}")

                else:

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
                return

            elif ctx.message.content == ";knock":

                msg = "Welcome to the Emporium!\n\nWe have all your feathered friend's requirements here!\n" \
                      "Please tell me, what can I be of service to you?"
                topic = "Due to the increasing demand of owls, the emporium can only supply that much"

                if path == "path6":
                    await self.update_path(user, cycle, path_new="path9")

                await ctx.channel.edit(topic=topic)
                await ctx.message.delete()
                await self.secret_response(ctx.guild.id, ctx.channel.name, msg)
                await self.penalize(user, cycle, points=15)
                await self.logging(f"{user} interacted using command {ctx.message.content} with action# {actions}")

            elif ctx.message.content == ";inquire":

                responses = [
                    (
                        "Here at the Emporium, we sell **Eeylops Premium Owl Treats!**\n\nA treat shaped like a mice "
                        "which is the best thing for a happy and healthy owl.",
                        "Stocks refresh every 12:00"),
                    (
                        "We sell only the best of our trained owls to carry your letters.\n\nNo address is needed "
                        "as owls can find any witch or wizard whose name is on the letter.",
                        "You & Your Owl Book:\nA snippet from Chapter 3, Page#44:\n\n... To send off your owl, "
                        "add your owl to your message with your :item: plus the @recipient or #address ..."),
                    (
                        "We have the following kinds of owls for all your wizarding needs! Find your precious "
                        "feathered friend from the low price of 11 galleons! Which owl you desire to "
                        "purchase?\n\nBrown, Screech, Snowy, Tawny, and Barred owls",
                        "Store Hours: 07:00 - 14:00\nMomentarily closed during thunderstorms and rain")
                ]

                msg, topic = responses[actions]

                await ctx.channel.edit(topic=topic)
                await ctx.message.delete()
                await self.action_update(user, cycle, actions=1)
                await self.penalize(user, cycle, points=15)
                await self.secret_response(ctx.guild.id, ctx.channel.name, msg)
                await self.logging(f"{user} interacted using command {ctx.message.content} with action# {actions}")

    # noinspection PyShadowingNames
    @commands.command(aliases=["purchase"])
    @commands.has_role("🐬")
    async def buy_items(self, ctx, *args):

        if ctx.channel.name != "eeylops-owl-emporium":
            return

        elif ctx.channel.name == "eeylops-owl-emporium":
            await ctx.message.delete()

            try:
                owl_buy = args[0].lower()

            except IndexError:
                return

            user = ctx.author
            cycle, path, timestamp, user_hints, actions, purchase = get_data(user)

            if purchase is False:

                msg = "*Relentlessly, you queued in line. " \
                      "Only to to realize that it would be best to just return on the next hour instead*"

                await self.penalize(user, cycle, points=5)
                await user.send(msg)
                await self.logging(f"{user} is trying purchase again but on hour cooldown")

            elif owl_buy not in owls_list:

                msg = "My hearing must have been getting old.\n\nWhich kind of owl is it again?"

                await self.penalize(user, cycle, points=10)
                await self.secret_response(ctx.guild.id, ctx.channel.name, msg)
                await self.logging(f"{user} tried to buy {owl_buy} but its not in the available list of owls")

            elif owl_buy in owls_list:

                purchaser_id = owls.find_one({"type": f"{owl_buy}"}, {"_id": 0, "purchaser": 1})["purchaser"]
                role_owl = discord.utils.get(ctx.guild.roles, name="🦉")

                if user in role_owl.members:

                    msg = f"My dear {user}, it would be best to sell this owl to those who do not own any yet as" \
                        f" my stocks are very limited."

                    await self.penalize(user, cycle, points=25)
                    await self.secret_response(ctx.guild.id, ctx.channel.name, msg)
                    await self.logging(f"{user} tried to buy {owl_buy} again")

                elif purchaser_id != "None":

                    purchaser = self.client.get_user(int(purchaser_id))
                    msg = f"My dear, that owl has been bought earlier by {purchaser}.\n\n" \
                        f"Should you wish to buy the same kind of owl again, do visit us just when our stocks " \
                        f"arrived. So you don't run out of. "

                    await self.penalize(user, cycle, points=10)
                    await self.secret_response(ctx.guild.id, ctx.channel.name, msg)
                    await quests.update_one({"user_id": str(user.id), "quest1.cycle": cycle},
                                            {"$set": {"quest1.$.purchase": False}})
                    await self.logging(f"{user} tried to buy {owl_buy} but it has been purchased already")

                elif purchaser_id == "None":

                    role_galleons = discord.utils.get(ctx.guild.roles, name="💰")

                    if user not in role_galleons.members:

                        msg = f"I'm sorry my dear {user}, this does not come for free.\n\n" \
                            f"I put into good efforts in training my owls to the best they can. " \
                            f"You're gonna have to pay me, should you yearn to get any owl from my emporium."

                        await self.update_path(user, cycle, path_new="path7")
                        await self.penalize(user, cycle, points=5)
                        await self.secret_response(ctx.guild.id, ctx.channel.name, msg)
                        quests.update_one({"user_id": str(user.id), "quest1.cycle": cycle},
                                          {"$set": {"quest1.$.purchase": False}})
                        await self.logging(f"{user} tried to buy {owl_buy} but they have no moneybag role")

                    else:

                        async with ctx.channel.typing():

                            role_owl = discord.utils.get(ctx.guild.roles, name="🦉")
                            owl_desc = owls.find_one({"type": owl_buy}, {"_id": 0})
                            description = owl_desc["description"]
                            msg = "What a lovely choice of owl!"

                            embed = discord.Embed(
                                title=f":owl: {owl_desc['type'].title()} | {owl_desc['trait'].capitalize()}",
                                description="*" + description + "*",
                                color=user.colour
                            )
                            embed.set_thumbnail(url=owl_desc["thumbnail"])

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

                            await self.update_path(user, cycle, path_new="path2")
                            await user.add_roles(role_owl)
                            await ctx.channel.send(f"{user.mention} has acquired 🦉 role")
                            await self.logging(f"{user} bought {owl_buy}")

                            await ctx.message.add_reaction("🦉")
                            await asyncio.sleep(2)

                            await self.secret_response(ctx.guild.id, ctx.channel.name, msg)
                            await asyncio.sleep(3)

                            await ctx.channel.send(embed=embed)
                            await asyncio.sleep(2)

    @commands.Cog.listener()
    async def on_message(self, message):
        role_dolphin = discord.utils.get(message.guild.roles, name="🐬")

        if message.author == self.client.user:
            return

        elif message.author.bot:
            return

        elif not check_quest(message.author) or message.author not in role_dolphin.members:
            return

        elif message.content.lower() == "eeylops owl emporium" and str(
                message.channel.category) == "⛲ Diagon Alley" and str(message.channel) != "eeylops-owl-emporium":

            await self.create_emporium(message.channel.category, message.guild,
                                       message.content.lower(), message, message.author)

        elif message.content.lower() in ["gringotts bank", "gringotts wizarding bank"] \
                and str(message.channel.category) == "⛲ Diagon Alley" and str(message.channel) != "gringotts-bank":

            await self.create_gringotts(message.channel.category, message.guild,
                                        message.content.lower(), message, message.author)

        elif message.content.lower() == "ollivanders" and str(message.channel.category) == "⛲ Diagon Alley" \
                and str(message.channel) != "ollivanders":

            await self.create_ollivanders(message.channel.category, message.guild,
                                          message.content.lower(), message, message.author)

        elif "gringotts-bank" == str(message.channel) and message.content.startswith != ";":
            await self.transaction_gringotts(message.author, message.guild, message.content.lower(), message)

        elif spell_check(message.content):
            await self.expecto(message.guild, message.author, message.channel, message)

    async def create_emporium(self, category, guild, msg, message, user):

        role_owl = discord.utils.get(guild.roles, name="🦉")
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
                    read_message_history=False)
            }

            emporium = await guild.create_text_channel("eeylops-owl-emporium", category=category, overwrites=overwrites)
            await self.generate_data(guild, msg, emporium)
            await message.add_reaction("✨")

            if user not in role_owl.members:
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

            if user not in role_owl.members:
                await self.update_path(user, cycle, path_new="path6")

            await asyncio.sleep(3)
            await message.delete()

        else:
            await self.reaction_closed(message)

    async def create_gringotts(self, category, guild, msg, message, user):

        role_galleons = discord.utils.get(message.guild.roles, name="💰")
        channels = [channel.name for channel in category.text_channels]
        cycle, path, timestamp, user_hints, actions, purchase = get_data(user)
        list_thieves = thieves.find_one({}, {"_id": 0, "names": 1})["names"]
        formatted_thieves = "\n".join(list_thieves)
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
                    read_message_history=False)
            }

            gringotts = await guild.create_text_channel(
                "gringotts-bank",
                category=category,
                overwrites=overwrites,
                topic=topic
            )
            await self.generate_data(guild, "gringotts-bank", gringotts)
            await message.add_reaction("✨")

            if user not in role_galleons.members:
                await self.update_path(user, cycle, path_new="path8")
                await asyncio.sleep(3)
                await message.delete()

            else:
                await asyncio.sleep(3)
                await message.delete()

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
                await self.update_path(user, cycle, path_new="path8")
                await asyncio.sleep(3)
                await message.delete()

            else:
                await asyncio.sleep(3)
                await message.delete()

        else:
            await self.reaction_closed(message)

    async def create_ollivanders(self, category, guild, msg, message, user):

        channels = [channel.name for channel in category.text_channels]
        cycle, path, timestamp, user_hints, actions, purchase = get_data(user)

        await self.logging(f"{user} tried to open a secret channel `{msg} opened at 1PM-4PM`")

        if "ollivanders" not in channels:  # and 13 <= int(current_time2()) <= 16:  # 1PM-4PM:

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True),
                guild.get_member(user.id): discord.PermissionOverwrite(read_messages=True, send_messages=True,
                                                                       read_message_history=False)
            }

            ollivanders = await guild.create_text_channel("ollivanders", category=category, overwrites=overwrites)
            await self.generate_data(guild, msg, ollivanders)
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
            await self.reaction_closed(message)

    async def transaction_ollivanders(self, guild, user, channel):

        msg = f"{user}, what can I help you for?"
        role_star = discord.utils.get(guild.roles, name="🌟")
        cycle, path, timestamp, user_hints, actions, purchase = get_data(user)

        await self.secret_response(guild.id, channel.name, msg)

        def check(guess):

            if guess.author != user:
                return

            elif "wand" in guess.content.lower() or "wands" in guess.content.lower():
                return guess.author == user and channel == guess.channel

            else:
                raise KeyError

        try:
            await self.client.wait_for("message", timeout=30, check=check)
            answer = "Correct"

        except KeyError:
            answer = "Wrong"
            msg = "Oh! You do not want my wands? Feel free to browse my shop then."
            await self.secret_response(guild.id, channel.name, msg)

        # Processing
        if answer == "Wrong":
            await self.penalize(user, cycle, points=5)

        elif user not in role_star.members and path in ["path11", "path3", "path10"]:

            msg = f"{user}, I see you want wands. Allow me to guide you through your wand selection, shall we?"
            topic = "Every choice affects your ending results."

            await self.secret_response(guild.id, channel.name, msg)
            await channel.edit(topic=topic)
            await asyncio.sleep(3)
            await self.wand_personalise(user, guild, channel, cycle, role_star)

        else:
            await self.penalize(user, cycle, points=25)
            topic = "Ollivanders! Home of the best crafted wands!"
            await channel.edit(topic=topic)

    # noinspection PyUnboundLocalVariable,PyMethodMayBeStatic,PyShadowingNames
    async def wand_personalise(self, user, guild, channel, cycle, role_star):

        data = quests.aggregate([{"$match": {"user_id": str(user.id)}},
                                 {"$project": {"_id": 0, "quest1": {"$slice": ["$quest1", -1]}}}])

        for profile in data:
            owl = profile["quest1"][0]["owl"]
            break

        trait = owls.find_one({"type": owl}, {"_id": 0, "trait": 1})["trait"]

        responses = {
            "pure emotions": ("I see you... I see that you have a temperamental and sensitive character.. "
                              "And perhaps also, a person who is attracted to those with inner conflicts..\n\n"
                              "Very unyielding yet faithful to those who are honest with themselves.",

                              "Core rarity: Unicorn Hair < Dragon Heartstring < Phoenix Feather\nChoose wisely."),

            "strong-willed": ("My child, do you ever believe in self-sacrificing. You are a strong-willed person. "
                              "Capable of being the bravest of them all and with outstanding passion and strong "
                              "sense of self, belief, and above all, justice.",

                              "Certain Woods are rare in nature and inherently possess rare Patronus'"),

            "adventurous": ("One stepped in this house, I knew how creative and brilliant youngster you are. "
                            "Hmm.. Very ambitious as well. Destined for a final quest.. Wise and rich in "
                            "experiences. A great partner with uninterrupted excitement and fun.",

                            "Casting the spells require diction, it must be concentrated and pure."),

            "nature-loving": ("Do you perhaps have high interest in nature? You are well fitted to be someone with "
                              "exceptional skills in magical beasts and herbalogy. Great talent requires great "
                              "wand",

                              "Owl selection plays an important role in Patronus summoning"),

            "special": ("A very special person. With traits of care and love for others. I know just the perfect "
                        "wands for you, wands with healing, defensive, and legilimency properties. Utterly loved "
                        "by nature, indeed.",

                        "There are a total of 142 collectible Patronus'")
        }

        msg1 = responses[trait][0]
        topic = responses[trait][1]

        await self.secret_response(guild.id, channel.name, msg1)
        await channel.edit(topic=topic)
        await asyncio.sleep(9)

        wand_length = await self.get_wand_length(user, guild, channel, cycle)

        if wand_length != "Wrong":
            wand_flexibility = await self.get_wand_flexibility(user, guild, channel, cycle)

            if wand_flexibility != "Wrong":
                wand_length_category = get_length_category(wand_length)
                wand_flexibility_category = get_flexibility_category(wand_flexibility)

                wood_selection = []
                for wand in patronus.find({"flexibility": wand_flexibility_category, "length": wand_length_category,
                                           "trait": trait.lower()}, {"_id": 0, "wood": 1}):

                    if wand["wood"] not in wood_selection:
                        wood_selection.append(wand["wood"])

                wand_wood = await self.get_wand_wood(user, guild, channel, cycle, wood_selection)

                if wand_wood != "Wrong":
                    wand_core = await self.get_wand_core(user, guild, channel, cycle)

                    wand_creation = {"flexibility_category": wand_flexibility_category,
                                     "flexibility": wand_flexibility,
                                     "length_category": wand_length_category,
                                     "length": wand_length,
                                     "core": wand_core,
                                     "trait": trait,
                                     "wood": wand_wood}

                    __patronus = patronus.find_one({"flexibility": wand_flexibility_category,
                                                    "length": wand_length_category, "trait": trait,
                                                    "core": wand_core, "wood": wand_wood}, {"_id": 0})

                    if __patronus is None:

                        msg = f"It seems that you're out of luck, {user}. I do not have that kind of wand. " \
                            f"Perhaps, you're looking for a rare combination of wand properties. " \
                            f"But no such wand is crafted yet by me. I suggest you try to wield a common core, " \
                            f"I'm sure there are lots of available for your choice."

                        await self.secret_response(guild.id, channel.name, msg)

                    elif __patronus is not None:

                        description = f"Wood: `{wand_wood.title()}`\n" \
                            f"Length: `{wand_length} in`\n" \
                            f"Flexibility: `{wand_flexibility.title()}`\n" \
                            f"Core: `{wand_core.title()}`"

                        embed = discord.Embed(color=user.colour, description=description)
                        embed.set_author(name="Wand Properties", icon_url=user.avatar_url)
                        embed.set_footer(text="Confirm purchase?")

                        msg = await channel.send(embed=embed)
                        await msg.add_reaction("✅")
                        await msg.add_reaction("❌")

                        # noinspection PyShadowingNames
                        def check(reaction, purchaser):
                            return msg.id == reaction.message.id and user.id == purchaser.id \
                                   and str(reaction.emoji) in ["✅", "❌"]

                        i = 0
                        while i < 1:

                            try:
                                reaction, purchaser = await self.client.wait_for("reaction_add", timeout=60,
                                                                                 check=check)
                                if str(reaction.emoji) == "✅":

                                    msg = f"{user.mention} has acquired :star2: role"
                                    quests.update_one({"user_id": str(user.id), "quest1.cycle": cycle},
                                                      {"$set": {"quest1.$.wand": wand_creation,
                                                                "quest1.$.patronus": __patronus}})

                                    await user.add_roles(role_star)
                                    await channel.send(msg)
                                    break

                                elif str(reaction.emoji) == "❌":
                                    msg = f"{user.mention}, come back soon once you've decided"
                                    await self.penalize(user, cycle, points=20)
                                    await channel.send(msg)
                                    break

                            except asyncio.TimeoutError:
                                i = 5

    # noinspection PyUnboundLocalVariable
    async def get_wand_core(self, user, guild, channel, cycle):

        formatted_cores = "`, `".join(cores)
        msg = f"{user}, lastly, the wand cores.\n\nSelect from the choices: `{formatted_cores}`"

        await asyncio.sleep(1)
        await self.secret_response(guild.id, channel.name, msg)

        def check(guess):
            if guess.author != user:
                return

            elif guess.content.lower() in cores and guess.author == user:
                return channel == guess.channel

            else:
                raise KeyError

        i = 0
        while i < 2:

            try:
                answer = await self.client.wait_for("message", timeout=60, check=check)
                wand_core = answer.content
                msg = f"{user}, {wand_core.capitalize()}. Another Interesting choice."  # change
                topic = "Wand flexibility is categorized into 3 major divisions"  # change

                await channel.edit(topic=topic)
                await self.secret_response(guild.id, channel.name, msg)
                break

            except asyncio.TimeoutError:

                msg = f"{user}, you can return again once you have decided well."
                wand_core = "Wrong"

                await self.action_update(user, cycle, actions=3)
                await self.penalize(user, cycle, points=10)
                await self.secret_response(guild.id, channel.name, msg)
                break

            except KeyError:

                if i == 0:
                    msg = "I don't think I craft that kind of length, do you mind telling me again?"
                    await self.penalize(user, cycle, points=5)

                elif i == 1:

                    msg = f"{user}, I don't think I craft that kind of length, do come again, should you wish to " \
                        f"pursue your path."
                    topic = "TEST"
                    wand_core = "Wrong"

                    await self.action_update(user, cycle, actions=3)
                    await self.penalize(user, cycle, points=10)
                    await channel.edit(topic=topic)

                await self.secret_response(guild.id, channel.name, msg)
                i += 1

        await self.logging(f"{user} is trying to personalise wand: -> awaits core -> Ended")
        return wand_core.lower()

    # noinspection PyUnboundLocalVariable
    async def get_wand_wood(self, user, guild, channel, cycle, wood_selection):

        formatted_woods = "`, `".join(wood_selection)
        msg = f"{user}, I just happen to have the appropriate woods for your wand characteristics.\n\n" \
            f"Select from the choices: `{formatted_woods}`"

        await asyncio.sleep(1)
        await self.secret_response(guild.id, channel.name, msg)

        def check(guess):
            if guess.author != user:
                return
            elif guess.content.lower() in wood_selection and guess.author == user:
                return channel == guess.channel
            else:
                raise KeyError

        i = 0
        while i < 2:

            try:
                answer = await self.client.wait_for("message", timeout=60, check=check)
                wand_wood = answer.content
                msg = f"{user}, {wand_wood.capitalize()}. Another Interesting choice."
                topic = "Wand flexibility is categorized into 3 major parts."  # change

                await channel.edit(topic=topic)
                await self.secret_response(guild.id, channel.name, msg)
                break

            except asyncio.TimeoutError:

                wand_wood = "Wrong"
                msg = f"{user}, you can return again once you have decided well."
                topic = "TEST"  # Change

                await channel.edit(topic=topic)
                await self.penalize(user, cycle, points=15)
                await self.action_update(user, cycle, actions=3)
                await self.secret_response(guild.id, channel.name, msg)
                break

            except KeyError:

                wand_wood = "Wrong"
                msg = f"{user}, I seems that I have no kind of that wand design ready for now."
                topic = "TEST"  # Change

                await channel.edit(topic=topic)
                await self.penalize(user, cycle, points=15)
                await self.action_update(user, cycle, actions=3)
                await self.secret_response(guild.id, channel.name, msg)
                break

        await self.logging(f"{user} is trying to personalise wand: -> awaits wood -> Ended")
        return wand_wood.lower()

    # noinspection PyUnboundLocalVariable
    async def get_wand_length(self, user, guild, channel, cycle):

        msg = f"We have wand lengths, {user}.\nDo tell me, which length in inches best suits your personality?\n\n" \
            f"Enter your choice: 8, 9, 10, 11, 12, 13, or 14."

        await asyncio.sleep(1)
        await self.secret_response(guild.id, channel.name, msg)

        def check(guess):
            if guess.author != user:
                return
            elif guess.content in ["8", "9", "10", "11", "12", "13", "14"] and guess.author == user:
                return channel == guess.channel
            else:
                raise KeyError

        i = 0
        while i < 1:

            try:

                answer = await self.client.wait_for("message", timeout=120, check=check)

                wand_length = answer.content
                msg = f"{user}, {wand_length} inches. Interesting choice."
                topic = "Wand length is categorized into 3 major parts."  # change

                await channel.edit(topic=topic)
                await self.secret_response(guild.id, channel.name, msg)
                break

            except asyncio.TimeoutError:

                wand_length = "Wrong"
                msg = f"{user}, you can return again once you have decided well."
                topic = "Wand length is categorized into 3 major parts."

                await channel.edit(topic=topic)
                await self.penalize(user, cycle, points=15)
                await self.action_update(user, cycle, actions=3)
                await self.secret_response(guild.id, channel.name, msg)
                break

            except KeyError:

                wand_length = "Wrong"
                msg = f"I don't think I craft that kind of length, do come back once you figure out your best " \
                    f"choice of wand length, {user}"
                topic = "Wand length is categorized into 3 major parts."

                await channel.edit(topic=topic)
                await self.penalize(user, cycle, points=15)
                await self.action_update(user, cycle, actions=3)
                await self.secret_response(guild.id, channel.name, msg)
                i += 1

        await self.logging(f"{user} is trying to personalise wand: -> awaits length -> Ended")
        return wand_length

    # noinspection PyUnboundLocalVariable
    async def get_wand_flexibility(self, user, guild, channel, cycle):

        await self.logging(f"{user} is trying to select flexibility -> awaits flexibility")

        formatted_flexibility = "`, `".join(flexibility_types)
        msg1 = f"Now {user}, wands can come too in various flexibility, it entails the ability of the person to " \
            f"adapt to various circumstances. Tell me, how much can you adapt?\n\n" \
            f"Choose from the following: `{formatted_flexibility}`"

        await asyncio.sleep(2)
        await self.secret_response(guild.id, channel.name, msg1)

        def check(guess):
            if guess.author != user:
                return
            elif guess.content.lower() in flexibility_types and guess.author == user:
                return channel == guess.channel
            else:
                raise KeyError

        i = 0
        while i < 2:

            try:
                answer = await self.client.wait_for("message", timeout=60, check=check)
                wand_flexibility = answer.content
                msg = f"{user}, {wand_flexibility.capitalize()}. Another Interesting choice."
                topic = "Wand flexibility is categorized into 3 major parts."  # change

                await channel.edit(topic=topic)
                await self.secret_response(guild.id, channel.name, msg)
                break

            except asyncio.TimeoutError:

                wand_flexibility = "Wrong"
                msg = f"{user}, you can return again once you have decided well."
                topic = "Wand flexibility is categorized into 3 major parts."  # change

                await channel.edit(topic=topic)
                await self.penalize(user, cycle, points=15)
                await self.action_update(user, cycle, actions=3)
                await self.secret_response(guild.id, channel.name, msg)
                break

            except KeyError:

                if i == 0:
                    wand_flexibility = "Wrong"
                    msg = f"{user}, I've never heard of that kind of flexibility.."
                    topic = "Wand flexibility is categorized into 3 major parts."  # change

                    await channel.edit(topic=topic)
                    await self.penalize(user, cycle, points=15)
                    await self.action_update(user, cycle, actions=3)
                    await self.secret_response(guild.id, channel.name, msg)

                else:
                    wand_flexibility = "Wrong"
                    msg = f"{user}, That too. Do come back once you are able to distinguish."
                    topic = "Wand flexibility is categorized into 3 major parts."  # change

                    await channel.edit(topic=topic)
                    await self.penalize(user, cycle, points=25)
                    await self.action_update(user, cycle, actions=3)
                    await self.secret_response(guild.id, channel.name, msg)

                i += 1

        await self.logging(f"{user} is trying to personalise wand: -> awaits flexibility -> Ended")
        return wand_flexibility.lower()

    async def transaction_gringotts(self, user, guild, msg, message):

        role_galleons = discord.utils.get(message.guild.roles, name="💰")
        cycle, path, timestamp, user_hints, actions, purchase = get_data(user)

        if user in role_galleons.members:

            msg = f"{user}, what are you doing here again.\n\nI thought you got what you wanted here already."

            await self.action_update(user, cycle, actions=3)
            await self.secret_response(guild.id, message.channel.name, msg)
            await self.penalize(user, cycle, points=20)
            await self.logging(f"{user} went back to Gringotts for nothing: {msg}")

        elif user not in role_galleons.members:

            if actions >= 3:
                return

            elif actions < 3 and "vault" in msg:
                await self.action_update(user, cycle, actions=5)
                await self.vault_access(cycle, user, guild, role_galleons, message)

            elif actions < 3:

                responses = [
                    "Greetings, {}. What do you want?",

                    "{}, I am assuming you do not know, we secure the wizarding families' treasuries here.\n\n"
                    "Now, what do you want from us?",

                    "{}, I don't think you are well aware of what is happening here.\n\n"
                    "I have other clients to assist, come back once you know, because I do not like my time "
                    "being wasted. "
                ]

                hint = actions + 1
                msg = responses[actions].format(user)

                await self.action_update(user, cycle, actions=1)
                await self.update_hint(user, cycle, hint)
                await self.penalize(user, cycle, points=10)
                await self.secret_response(guild.id, message.channel.name, msg)
                await self.logging(f"Posted a hint for {user}")

    async def vault_access(self, cycle, user, guild, role_galleons, message):

        msg = f"Your identification, please? {user}"

        await self.secret_response(guild.id, message.channel.name, msg)
        await self.logging(f"{user} is trying to transact to Gringotts: -> awaits identification")
        identity = await self.obtain_identity(user, guild, message)

        if identity != "Wrong":
            vault_number = await self.obtain_vault_number(cycle, user, guild, message)

            if vault_number != "Wrong":
                vault_password = await self.obtain_vault_password(cycle, user, guild, message)

                if vault_password != "Wrong":
                    msg1 = f"{user.mention} has acquired :moneybag: role"
                    msg2 = "Very well then. You can get out of my bank now."
                    vault = f"{str(user.id).replace('1', '@').replace('5', '%').replace('7', '&').replace('3', '#')}"

                    secret = books.find_one({"server": str(guild.id)}, {"_id": 0, str(message.channel.name): 1})
                    webhook_url = secret[str(message.channel.name)]["webhook"]
                    avatar = secret[str(message.channel.name)]["avatar"]
                    username = secret[str(message.channel.name)]["username"]

                    embed = DiscordEmbed(color=0xffffff, title=f":closed_lock_with_key: Opening Vault# {vault}")
                    embed.set_image(url="https://i.imgur.com/RIS1TLh.gif")

                    webhook = DiscordWebhook(url=webhook_url, avatar_url=avatar, username=username)
                    webhook.add_embed(embed)
                    webhook.execute()

                    await self.update_path(user, cycle, path_new="path15")
                    await self.logging(f"{user} successfully decoded vault password")
                    await user.add_roles(role_galleons)
                    await self.logging(f"Added Moneybag role for {user}")
                    await asyncio.sleep(6)
                    await message.channel.send(msg1)
                    await self.secret_response(guild.id, message.channel.name, msg2)

                    thieves.update_one({}, {"$pull": {"names": str(user.name)}})

    # noinspection PyUnboundLocalVariable
    async def obtain_identity(self, user, guild, message):

        cycle, path, timestamp, user_hints, actions, purchase = get_data(user)

        await self.logging(f"{user} is trying to transact to Gringotts: -> awaits identity")

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
                answer = "Correct"
                await guess.add_reaction("✅")
                await asyncio.sleep(3)
                await guess.delete()

                if path == "path18":
                    await self.update_path(user, cycle, path_new="path5")

                break

            except asyncio.TimeoutError:

                if thieves.find_one({"names": user.name}, {"_id": 0}) is None:
                    thieves.update_one({}, {"$push": {"names": user.name}})

                msg = f"{user}, it seems that you have trouble showing me your identification.\n\n" \
                    f"I'm gonna have to ask you to get out of my bank. You are wasting my time."
                topic = "The goblins can await for two minutes for every question they ask"
                answer = "Wrong"

                await self.update_path(user, cycle, path_new="path18")
                await self.action_update(user, cycle, actions=3)
                await self.penalize(user, cycle, points=10)
                await self.secret_response(guild.id, message.channel.name, msg)
                await message.channel.edit(topic=topic)
                break

            except KeyError:

                if i == 0:
                    msg = f"{user}, that is not what we call identification here!"
                    topic = "One customer vault access request ticket can be used every hour"

                    await self.penalize(user, cycle, points=5)
                    await message.channel.edit(topic=topic)

                elif i == 1:

                    msg = f"{user}, neither that one!\n\nWhat are you even suggesting to me? The identification I am " \
                        f"looking for is a 32 alpha-numeric character!"
                    topic = "Identification cards equate to the wizards'/witches'/spirits' avatar"

                    await self.penalize(user, cycle, points=5)
                    await message.channel.edit(topic=topic)

                elif i == 2:

                    if thieves.find_one({"names": user.name}, {"_id": 0}) is None:
                        thieves.update_one({}, {"$push": {"names": user.name}})

                    msg = f"{user}, I don't think you have any business here!\n\n" \
                        f"I'm gonna have to ask you to get out of my bank. You are plainly wasting my time."
                    topic = "Banking Hours: 08:00 - 15:00"
                    answer = "Wrong"

                    await self.update_path(user, cycle, path_new="path18")
                    await self.action_update(user, cycle, actions=3)
                    await self.penalize(user, cycle, points=10)
                    await message.channel.edit(topic=topic)

                await self.secret_response(guild.id, message.channel.name, msg)
                i += 1

        await self.logging(f"{user} is trying to transact to Gringotts: -> awaits identity -> Ended")
        return answer

    # noinspection PyUnboundLocalVariable
    async def obtain_vault_number(self, cycle, user, guild, message):

        msg = f"Very well then, {user}. And the vault number?"

        await self.logging(f"{user} is trying to transact to Gringotts: -> awaits vault number")
        await self.secret_response(guild.id, message.channel.name, msg)

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
                topic = "Banking Hours: 08:00 - 15:00"
                answer = "Correct"

                await guess.add_reaction("✅")
                await asyncio.sleep(3)
                await guess.delete()
                await message.channel.edit(topic=topic)
                break

            except asyncio.TimeoutError:

                if thieves.find_one({"names": user.name}, {"_id": 0}) is None:
                    thieves.update_one({}, {"$push": {"names": user.name}})

                msg = f"{user}. Are you stealing from someone?\n\nGet the hell out of my bank now!"
                answer = "Wrong"

                await self.action_update(user, cycle, actions=3)
                await self.penalize(user, cycle, points=10)
                await self.secret_response(guild.id, message.channel.name, msg)
                break

            except KeyError:
                if i == 0:
                    msg = f"{user}, my records cannot be wrong, that is an invalid vault number."

                    await self.penalize(user, cycle, points=5)

                elif i == 1:
                    msg = f"{user}, that does not show either!"
                    topic = "Gringotts, the wizard bank! Ain't no safer place. Not one. Except perhaps Patronus Castle."

                    await self.penalize(user, cycle, points=5)
                    await message.channel.edit(topic=topic)

                elif i == 2:
                    if thieves.find_one({"names": user.name}, {"_id": 0}) is None:
                        thieves.update_one({}, {"$push": {"names": user.name}})

                    msg = f"{user}, I don't think you have any business here!\n\n" \
                        f"I'm gonna have to ask you to get out of my bank. You are just wasting my time."
                    topic = "Most commonly used passwords:\n1. ALOHOMORA\n2. vault number reversal\n3. Password1234"
                    answer = "Wrong"

                    await self.action_update(user, cycle, actions=3)
                    await self.penalize(user, cycle, points=10)
                    await message.channel.edit(topic=topic)

                await self.secret_response(guild.id, message.channel.name, msg)
                i += 1

        await self.logging(f"{user} is trying to transact to Gringotts: -> awaits vault number -> Ended")
        return answer

    # noinspection PyUnboundLocalVariable
    async def obtain_vault_password(self, cycle, user, guild, message):

        msg1 = f"Come. We will apparate to your vault. {user}."
        msg2 = f"Ahhh. Here we are, and your password, {user}?"

        await self.logging(f"{user} is trying to transact to Gringotts: -> awaits password")
        await asyncio.sleep(1)
        await self.secret_response(guild.id, message.channel.name, msg1)
        await asyncio.sleep(3)
        await self.secret_response(guild.id, message.channel.name, msg2)

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
                answer = "Correct"

                await guess.add_reaction("✅")
                await asyncio.sleep(3)
                await guess.delete()
                break

            except asyncio.TimeoutError:

                if thieves.find_one({"names": user.name}, {"_id": 0}) is None:
                    thieves.update_one({}, {"$push": {"names": user.name}})

                msg = f"{user}. What do you mean that you forgot? You wasted my time! Get out of my bank!"
                answer = "Wrong"

                await self.action_update(user, cycle, actions=3)
                await self.penalize(user, cycle, points=5)
                await self.secret_response(guild.id, message.channel.name, msg)
                break

            except KeyError:
                if i == 0:
                    msg = "Well that's weird. It did not work"
                    await self.penalize(user, cycle, points=5)

                elif i == 1:
                    msg = "Huhh.. Are you sure that is your correct password?!"
                    await self.penalize(user, cycle, points=5)

                elif i == 2:
                    if thieves.find_one({"names": user.name}, {"_id": 0}) is None:
                        thieves.update_one({}, {"$push": {"names": user.name}})

                    msg = f"{user}, I don't think you have any business here!\n\n" \
                        f"I'm gonna have to ask you to get out of my bank. You are wasting my time."
                    answer = "Wrong"

                    await self.action_update(user, cycle, actions=3)
                    await self.penalize(user, cycle, points=10)

                await self.secret_response(guild.id, message.channel.name, msg)
                i += 1

        await self.logging(f"{user} is trying to transact to Gringotts: -> awaits Ended")
        return answer


def setup(client):
    client.add_cog(Magic(client))
