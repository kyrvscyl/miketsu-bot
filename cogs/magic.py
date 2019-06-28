"""
Discord Susabi Bot.
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

from cogs.mongo.db import books, quests, owls, weather, sendoff, thieves

# Date and Time
tz_target = pytz.timezone("America/Atikokan")

# Global Variables
owls_list = []
for owl in owls.find({}, {"_id": 0, "type": 1}):
    owls_list.append(owl["type"])


def current_timestamp():
    timestamp = datetime.now(tz=tz_target).strftime("%Y-%b-%d %HH")
    return timestamp


def current_time2():
    time_current2 = datetime.now(tz=tz_target).strftime("%H")
    return time_current2


# noinspection PyUnboundLocalVariable,PyShadowingNames
def get_data(user):
    data = quests.aggregate([{"$match": {"user_id": str(user.id)}},
                             {"$project": {"_id": 0, "quest1": {"$slice": ["$quest1", -1]}}}])
    for profile in data:
        cycle = profile["quest1"][0]["cycle"]
        current_path = profile["quest1"][0]["current_path"]
        timestamp = profile["quest1"][0]["timestamp"]
        hints = profile["quest1"][0]["hints"]
        actions = profile["quest1"][0]["actions"]
        purchase = profile["quest1"][0]["purchase"]
        break
    return cycle, current_path, timestamp, hints, actions, purchase


def check_quest(user):
    profile = quests.find_one({"user_id": str(user.id)}, {"_id": 0, "user_id": 1})
    return profile != {}


def spell_check(msg):
    translate = msg.lower().translate({ord(i): None for i in "! "})
    spell = "expectopatronum"
    return all(c in spell for c in translate) and all(c in translate for c in spell)


async def secret_banner(webhook_url, avatar, username, url):
    webhook = DiscordWebhook(url=webhook_url, avatar_url=avatar, username=username)
    embed = DiscordEmbed(color=0xffffff)
    embed.set_image(url=url)
    webhook.add_embed(embed)
    webhook.execute()


class Magic(commands.Cog):

    def __init__(self, client):
        self.client = client

    async def logging(self, msg):
        channel = self.client.get_channel(592270990894170112)
        date_time = datetime.now(tz=tz_target).strftime("%Y-%b-%d %HH")
        await channel.send(f"[{date_time}] " + msg)

    async def sendoff_owl(self, user, reaction, cycle):
        await user.send("*Sending off owl to the :trident: Headmaster's Tower*")
        await asyncio.sleep(2)
        await reaction.message.channel.send(f"*{user}, you will receive an update when the clock moves an hour*")
        await self.generate_owl_report(user, cycle)
        await self.logging(f"{user} has successfully dispatched their owl to the Headmaster's Office")

    # noinspection PyUnboundLocalVariable,PyUnusedLocal
    async def generate_owl_report(self, user, cycle):
        profile = sendoff.find_one({"user_id": str(user.id), "cycle": cycle}, {"_id": 0})
        weather1 = weather.find_one({"weather1": {"$type": "string"}}, {"weather1": 1})["weather1"]
        weather2 = weather.find_one({"weather2": {"$type": "string"}}, {"weather2": 1})["weather2"]

        if weather1 == "⛈":  # Thunderstorms
            await self.update_path(user, cycle, path_new="path19")
            report = "Your owl returned to you crawling on its feathers due to the thunderstorms.\n\n" \
                     "Your owl will recover in 3 hours before you can send it off again."
            delay = 1 + 3
            scenario = 1

        elif weather1 == "🌨" and profile["type"] == "Snowy Owl":  # Snowy owl and Snowy weather
            report = "Your owl travelled hastily to the Headmaster's Office due to favorable weather for the owl.\n\n" \
                     "Estimated time of return: in 1 hour"
            delay = 1 + 1
            scenario = 2

        elif weather2 == "🌕" or weather2 == "🌑":  # Night
            report = "Owls are best at night and can return faster than normal travel time.\n\n" \
                     "Estimated time of return: in 1 hour"
            delay = 1 + 1
            scenario = 2

        elif weather1 == "🌧" or weather1 == "🌨":  # Rainy or snowy
            report = "Your owl struggled to reached the Headmaster's Office on time due to unfavoured weather.\n\n" \
                     "Estimated time of return: in 2 hours"
            delay = 1 + 2
            scenario = 2

        elif weather1 == "☁" or weather1 == "⛅":  # Cloudy & Partly sunny
            report = "Your owl has safely arrived at the Headmaster's Office.\n\n" \
                     "Estimated time of return: in 1 hour"
            delay = 1 + 1
            scenario = 2

        timestamp_update = (datetime.now(tz=tz_target) + timedelta(days=1 / 24)).strftime("%Y-%b-%d %HH")
        timestamp_complete = (datetime.now(tz=tz_target) + timedelta(days=delay / 24)).strftime("%Y-%b-%d %HH")
        sendoff.update_one({"user_id": str(user.id)}, {"$set": {"report": report,
                                                                "weather1": weather1,
                                                                "weather2": weather2,
                                                                "timestamp": current_timestamp(),
                                                                "timestamp_update": timestamp_update,
                                                                "timestamp_complete": timestamp_complete,
                                                                "delay": delay,
                                                                "scenario": scenario}})

        await self.logging(f"Generated owl report for {user.name}\n"
                           f"--> Report: {report}\n"
                           f"--> Weather1: {weather1}\n"
                           f"--> Weather2: {weather2}\n"
                           f"--> Time of sendoff: {current_timestamp()}\n"
                           f"--> Time of sending of update: {timestamp_update}\n"
                           f"--> Time of sending of completion: {timestamp_complete}\n"
                           f"--> Hours delay of owl: {delay}\n"
                           f"--> Scenario: {scenario}\n"
                           f"--> Cycle#: {cycle}")

    # noinspection PyUnusedLocal,PyShadowingNames
    async def update_path(self, user, cycle, path_new):
        if path_new == "path18" or path_new == "path5":
            quests.update_one({"user_id": str(user.id), "quest1.cycle": cycle},
                              {"$set": {"quest1.$.current_path": path_new, "quest1.$.timestamp": current_timestamp(),
                                        "quest1.$.hints": ["locked", "locked", "locked", "locked", "locked"]}})
        else:
            quests.update_one({"user_id": str(user.id), "quest1.cycle": cycle},
                              {"$set": {"quest1.$.current_path": path_new, "quest1.$.timestamp": current_timestamp(),
                                        "quest1.$.actions": 0,
                                        "quest1.$.hints": ["locked", "locked", "locked", "locked", "locked"]}})
        await self.logging(f"Shifting {user.name}'s current path to {path_new}")

    # noinspection PyUnusedLocal
    async def penalize(self, user, cycle, points):
        quests.update_one({"user_id": str(user.id), "quest1.cycle": cycle},
                          {"$inc": {"quest1.$.score": -points}})
        await self.logging(f"Penalizing {user.name} for {points} points")

    # noinspection PyUnusedLocal
    async def action_update(self, user, cycle, actions):
        quests.update_one({"user_id": str(user.id), "quest1.cycle": cycle},
                          {"$inc": {"quest1.$.actions": actions}})
        await self.logging(f"Adding {actions} action point/s for {user}")

    # noinspection PyUnusedLocal
    async def update_hint(self, user, cycle, hint):
        quests.update_one({"user_id": str(user.id), "quest1.cycle": cycle},
                          {"$set": {f"quest1.$.hints.{hint}": "unlocked", f"quest1.$.timestamp": current_timestamp()}})
        quests.update_one({"user_id": str(user.id), "quest1.cycle": cycle},
                          {"$inc": {f"quest1.$.hints_unlocked": 1}})
        await self.logging("Updating and adding hints locked")

    # noinspection PyUnboundLocalVariable
    async def generate_data(self, guild, secret_channel, channel):

        channel_name = secret_channel.replace(" ", "-")
        webhook = await channel.create_webhook(name="webhooker")
        books.update_one({"server": str(guild.id)},
                         {"$set": {f"{channel_name}.id": str(channel.id), f"{channel_name}.webhook": webhook.url}})

        if channel_name == "eeylops-owl-emporium":
            avatar_url = "https://i.imgur.com/8xR61b4.jpg"
            username = "Manager Eeylops"
            url = "https://i.imgur.com/wXSibYR.jpg"
            books.update_one({"server": str(guild.id)},
                             {"$set": {f"{channel_name}.avatar": avatar_url,
                                       f"{channel_name}.username": username}})

        elif channel_name == "gringotts-bank":
            avatar_url = "https://i.imgur.com/IU882rV.jpg"
            username = "Bank Manager Gringotts"
            url = "https://i.imgur.com/whPMNPb.jpg"
            books.update_one({"server": str(guild.id)},
                             {"$set": {f"{channel_name}.avatar": avatar_url,
                                       f"{channel_name}.username": username}})

        elif channel_name == "ollivanders":
            avatar_url = "https://i.imgur.com/DEuO4la.jpg"
            username = "Ollivanders"
            books.update_one({"server": str(guild.id)},
                             {"$set": {f"{channel_name}.avatar": avatar_url,
                                       f"{channel_name}.username": username}})

        await self.logging(f"Generating secret channel: {channel_name} and its webhook")
        await secret_banner(webhook.url, avatar_url, username, url)

    async def reaction_closed(self, message):
        await self.logging("Secret channel is 'CLOSED': Added reactions and deleting message")
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

        if user in role_star.members:
            uppers = len([char for char in message.content if char.isupper()])
            lowers = len([char for char in message.content if char.islower()])
            symbol = len([char for char in message.content if char == "!"])

            strength = round((uppers * 1.35) + lowers + (symbol * 1.5), 2)
            range_min = strength - 5
            range_max = strength + 5
            strength = round(random.uniform(range_min, range_max), 2)

            if strength > 100:
                strength = round(random.uniform(98, 99.99), 2)

            await channel.send(f"Your Patronus strength: {strength}%")
            await self.logging(f"{user} successfully finished the quest")
            cycle, path, timestamp, user_hints, actions, purchase = get_data(user)
            quests.update_one({"user_id": str(user.id), "quest1.cycle": cycle},
                              {"$set": {"quest1.$.status": "completed"}})

            await self.logging(f"{user} successfully finished the quest")

        elif path == "path3":
            await self.update_path(user, cycle, path_new="path10")
            await self.penalize(user, cycle, points=5)
            await message.add_reaction("❎")
            await self.logging(f"{user} tried to cast the Patronus charm summoning spell")

        elif path == "path10":
            await message.add_reaction("❔")
            await self.penalize(user, cycle, points=10)
            await self.logging(f"{user} tried to recast the Patronus summoning spell to no avail")

    @commands.command(aliases=["progress"])
    @commands.has_role("🐬")
    async def show_progress(self, ctx):
        if not check_quest(ctx.message.author):
            return

        elif check_quest(ctx.message.author):

            # noinspection PyShadowingNames,PyUnboundLocalVariable
            def get_profile(user):
                data = quests.aggregate([{"$match": {"user_id": str(user.id)}},
                                         {"$project": {"_id": 0, "quest1": {"$slice": ["$quest1", -1]}}}])
                for profile in data:
                    cycle = profile["quest1"][0]["cycle"]
                    current_path = profile["quest1"][0]["current_path"]
                    score = profile["quest1"][0]["score"]
                    timestamp_start = profile["quest1"][0]["timestamp_start"]
                    hints_unlocked = profile["quest1"][0]["hints_unlocked"]
                    break
                return score, timestamp_start, current_path, cycle, hints_unlocked

            score, timestamp_start, current_path, cycle, hints_unlocked = get_profile(ctx.message.author)

            t1 = datetime.strptime(timestamp_start, "%Y-%b-%d %HH")
            t2 = datetime.strptime(current_timestamp(), "%Y-%b-%d %HH")
            hours_passed = (t2 - t1).days * 24 + (t2 - t1).seconds // 3600

            description = f"▫Current Score: {score}\n" \
                f"▫Hours passed: {hours_passed}\n" \
                f"▫Penalties: {1000 - score}\n\n" \
                f"▫Current Path: {current_path.capitalize()}\n" \
                f"▫Hints Unlocked: {hints_unlocked}"

            embed = discord.Embed(color=ctx.message.author.colour, description=description)
            embed.set_author(name=f"{ctx.message.author}'s Cycle #{cycle}",
                             icon_url=ctx.message.author.avatar_url)
            await ctx.channel.send(embed=embed)
            await self.logging(f"{ctx.message.author.name} requested to show their progress")

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

        request = books.find_one({"server": f"{payload.guild_id}"},
                                 {"_id": 0, "welcome": 1, "sorting": 1, "letter": 1})

        if str(payload.emoji) == "🐬" and payload.message_id == int(request['letter']):
            member = server.get_member(user.id)

            if quests.find_one({"user_id": str(user.id)}, {"_id": 0}) is None:
                profile = {"user_id": str(payload.user_id), "server": str(payload.guild_id), "quest1": []}
                quests.insert_one(profile)
                await self.logging(f"Successfully created quest profile for {user.name}")

            # Cycle creation
            for i in (range(200)):
                cycle = i + 1
                if len(quests.find_one({"user_id": str(payload.user_id)}, {"_id": 0})["quest1"]) != cycle:
                    quests.update_one({"user_id": str(user.id)},
                                      {"$push": {"quest1": dict(status="ongoing", cycle=cycle, score=1000,
                                                                timestamp=current_timestamp(),
                                                                timestamp_start=current_timestamp(),
                                                                current_path="path1", actions=0,
                                                                purchase=True,
                                                                hints_unlocked=0,
                                                                hints=["locked", "locked", "locked", "locked",
                                                                       "locked"])}})
                    await self.logging(f"Successfully started cycle#{cycle} for {user.name}")
                    break

            # Process actions
            await self.logging(f"Successfully sent {user.name} their first clues through DM")
            await member.add_roles(role_dolphin)
            await self.logging(f"Successfully added dolphin role to {user.name}")

            # Sending of messages
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

        if user == self.client.user:
            return

        elif user.bot:
            return

        elif str(reaction.emoji) == "✉" and user != self.client.user \
                and "envelope" in reaction.message.content and reaction.message.author == self.client.user:
            server = quests.find_one({"user_id": str(user.id)}, {"_id": 0, "server": 1})
            request = books.find_one({"server": server["server"]},
                                     {"_id": 0, "welcome": 1, "sorting": 1, "letter": 1})

            description = f"*Dear {user.name},\n\nWe are pleased to accept you at House Patronus.\nDo browse " \
                f"the server's <#{request['welcome']}> channel for the basics and essentials of the guild then " \
                f"proceed to <#{request['sorting']}> to assign yourself some roles.\n\nWe await your return owl.\n\n" \
                f"Yours Truly,\nThe Headmaster*"

            embed = discord.Embed(color=0xffff80, title="Acceptance Letter", description=description)
            embed.set_thumbnail(url=self.client.get_guild(int(server["server"])).icon_url)
            await user.send(embed=embed)
            await self.logging(f"{user} opened the letter of Headmaster invitation letter.")

        elif str(reaction.emoji) == "✉" and user != self.client.user \
                and "returned with" in reaction.message.content and reaction.message.author == self.client.user:
            server = quests.find_one({"user_id": str(user.id)}, {"_id": 0, "server": 1})
            cycle, path, timestamp, user_hints, actions, purchase = get_data(user)
            await self.update_path(user, cycle, path_new="path3")

            description = f"Dear {user.name},\n\nIt is wondrous to have such another promising magic " \
                f"practitioner. At the castle, everyone there is special, but what makes them " \
                f"more special is their Patronus charm.\n\nYour term awaits soon. Good luck!\n\n" \
                f"Yours Sincerely,\nThe Headmaster "

            embed = discord.Embed(color=0xffff80, description=description)
            embed.set_thumbnail(url=self.client.get_guild(int(server["server"])).icon_url)
            await user.send(embed=embed)
            await self.logging(f"{user} opened the letter of Headmaster response.")

        elif str(reaction.emoji) == "🦉":
            role_owl = discord.utils.get(reaction.message.guild.roles, name="🦉").members
            request = books.find_one({"server": f"{reaction.message.guild.id}"},
                                     {"_id": 0, "tower": 1})

            if user not in role_owl:
                await self.logging(f"{user} tried to sendoff an owl but doesnt have the owl role")

            elif (request["tower"] not in str(reaction.message.content) or
                  "kyrvscyl#9389" not in str(reaction.message.content)) and "✉" not in str(reaction.message.content):
                await self.logging(f"{user} has the owl role but the message is wrong (no channel/envelope emoji)")
                await reaction.message.add_reaction("❔")

            elif (request["tower"] not in str(reaction.message.content) or
                  "kyrvscyl#9389" not in str(reaction.message.content)) and "✉" in str(reaction.message.content):
                cycle, path, timestamp, user_hints, actions, purchase = get_data(user)

                # Path having the owl roles and haven't sent off yet
                if path == "path2" or path == "path20":
                    await self.update_path(user, cycle, path_new="path4")  # Transfers to waiting path
                    await reaction.message.add_reaction("✅")
                    await asyncio.sleep(2)
                    await self.sendoff_owl(user, reaction, cycle)
                    await reaction.message.delete()

                # Punishment path
                elif path == "path19":
                    await self.penalize(user, cycle, points=20)
                    msg = "*\"Your owl was paralyzed due to the storms. It needs time to heal itself.\"*"
                    await user.send(msg)
                    await asyncio.sleep(2)
                    await reaction.message.delete()
                    await self.logging(f"{user} tried to sendoff while owl is recovering")

    # noinspection PyUnboundLocalVariable
    @commands.command(aliases=["hint"])
    @commands.has_role("🐬")
    async def hint_request(self, ctx):
        user = ctx.message.author

        # Not accepted the quest
        if not check_quest(user):
            await self.logging(f"{user} tried to use hint while the quest is not yet accepted")

        # With quest acceptance
        elif check_quest(user):
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
                        await self.penalize(user, cycle, points=5)
                        await ctx.channel.send(f"{user.mention}, don't we have what we wanted here already?")
                        await self.logging(f"S{user.name} transacted with gringotts with moneybag role already"
                                           f" | {path}")

                    else:
                        await self.update_hint(user, cycle, h)
                        await self.penalize(user, cycle, points=10)
                        await ctx.message.add_reaction("✅")

                        embed = discord.Embed(color=user.colour, description="*\"" + hint + "\"*")
                        embed.set_footer(icon_url=user.avatar_url, text=f"Path {path[4::]} | Hint# {hint_num}")
                        await user.send(embed=embed)
                        await self.logging(f"Sent a hint for {user.name} | {path}:{hint_num}")

                except IndexError:
                    await user.send(f"{user.mention}, you have used up all your hints for the path.")
                    await self.logging(f"{user} has used up all their hints | {path}")

                except KeyError:
                    await user.send(f"{user.mention}, you have used up all your hints for the path.")
                    await self.logging(f"{user} has used up all their hints | {path}")

    # noinspection PyMethodMayBeStatic
    async def secret_response(self, guild_id, channel_name, description):
        secret_channel = books.find_one({"server": str(guild_id)}, {"_id": 0, str(channel_name): 1})
        webhook_url = secret_channel[str(channel_name)]["webhook"]
        avatar = secret_channel[str(channel_name)]["avatar"]
        username = secret_channel[str(channel_name)]["username"]
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
            await ctx.message.delete()

            command = ctx.message.content.replace(";", "")
            user = ctx.author
            cycle, path, timestamp, user_hints, actions, purchase = get_data(user)

            # noinspection PyShadowingNames
            if command == "knock":
                msg = "Welcome to the Emporium!\n\nWe have all your feathered friend's requirements here!\n" \
                      "Please tell me, what can I be of service to you?"
                topic = "Due to the increasing demand of owls, the emporium can only supply that much"

            elif actions == 3:
                return

            elif command == "inquire":
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
                await self.action_update(user, cycle, actions=1)

            if path == "path6":
                await self.update_path(user, cycle, path_new="path9")

            await self.penalize(user, cycle, points=10)
            await ctx.channel.edit(topic=topic)
            await self.secret_response(ctx.guild.id, ctx.channel.name, msg)
            await self.logging(f"{user} interacted using command {command} with action# {actions}")

    @commands.command(aliases=["purchase"])
    @commands.has_role("🐬")
    async def buy_items(self, ctx, *args):

        if ctx.channel.name != "eeylops-owl-emporium":
            return

        elif ctx.channel.name == "eeylops-owl-emporium":

            try:
                query = args[0].title()
                owl_buy = f"{query} Owl"
            except IndexError:
                return

            user = ctx.author
            cycle, path, timestamp, user_hints, actions, purchase = get_data(user)

            if purchase is False:
                msg = "Relentlessly, you queued in line. " \
                      "Only to to realize that it would be best to just return on the next hour instead"
                await self.penalize(user, cycle, points=5)
                await self.secret_response(ctx.guild.id, ctx.channel.name, msg)
                await self.logging(f"{ctx.author.name} is trying purchase again but on hour cooldown")

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
                    await self.penalize(user, cycle, points=5)
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
                        await ctx.message.add_reaction("🦉")
                        async with ctx.channel.typing():
                            role_owl = discord.utils.get(ctx.guild.roles, name="🦉")
                            owl_description = owls.find_one({"type": f"{owl_buy}"}, {"_id": 0})
                            description = owl_description["description"]
                            msg = "What a lovely choice of owl!"
                            embed = discord.Embed(title=f":owl: {owl_description['type']} | {owl_description['trait']}",
                                                  description="*" + description + "*", color=user.colour)
                            embed.set_thumbnail(url=owl_description["thumbnail"])

                            owls.update_one({"type": f"{owl_buy}"}, {"$set": {"purchaser": str(user.id)}})
                            sendoff.insert_one({"user_id": str(user.id), "type": owl_buy, "cycle": cycle})

                            await self.secret_response(ctx.guild.id, ctx.channel.name, msg)
                            await asyncio.sleep(3)
                            await ctx.channel.send(embed=embed)
                            await asyncio.sleep(2)
                            await self.update_path(user, cycle, path_new="path2")
                            await user.add_roles(role_owl)
                            await ctx.channel.send(f"{user.mention} has acquired 🦉 role")
                            await self.logging(f"{user} bought {owl_buy}")

        await ctx.message.delete()

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author == self.client.user:
            return

        elif message.author.bot:
            return

        elif not check_quest(message.author):
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

        elif "gringotts-bank" == str(message.channel) and message.content.startswith(";") is False:
            await self.transaction_gringotts(message.author, message.guild, message.content.lower(),
                                             message)

        elif spell_check(message.content):
            await self.expecto(message.guild, message.author, message.channel, message)

    async def create_emporium(self, category, guild, msg, message, user):
        channels = [channel.name for channel in category.text_channels]
        cycle, path, timestamp, user_hints, actions, purchase = get_data(user)
        await self.logging(f"{user} tried to open a secret channel `{msg} opened at 07:00 - 14:00`")

        if "eeylops-owl-emporium" not in channels:  # and 7 <= int(current_time2()) <= 14:  # 07:00 - 14:00
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True),
                guild.get_member(user.id): discord.PermissionOverwrite(read_messages=True, read_message_history=False)
            }
            emporium = await guild.create_text_channel("eeylops-owl-emporium", category=category, overwrites=overwrites)
            await self.generate_data(guild, msg, emporium)

            if path == "path1":
                await self.update_path(user, cycle, path_new="path6")  # path_current="1"
            elif path == "path15":
                return

        elif "eeylops-owl-emporium" in channels:  # and 7 <= int(current_time2()) <= 14:  # 07:00 - 14:00
            emporium_id = books.find_one({"server": str(guild.id)},
                                         {"eeylops-owl-emporium": 1})["eeylops-owl-emporium"]["id"]
            emporium_channel = self.client.get_channel(int(emporium_id))
            await emporium_channel.set_permissions(user, read_messages=True, send_messages=False,
                                                   read_message_history=False)

            if path == "path1":
                await self.update_path(user, cycle, path_new="path6")  # path_current="1"
            elif path == "path15":
                return
        else:
            await self.reaction_closed(message)

    async def create_gringotts(self, category, guild, msg, message, user):
        channels = [channel.name for channel in category.text_channels]
        cycle, path, timestamp, user_hints, actions, purchase = get_data(user)
        await self.logging(f"{user} tried to open a secret channel `{msg} opened at 08:00 - 15:00`")

        # Topic creation
        list_thieves = thieves.find_one({}, {"_id": 0, "names": 1})["names"]
        formatted_thieves = "\n".join(list_thieves)
        topic = f"List of Potential Thieves:\n{formatted_thieves}"

        if "gringotts-bank" not in channels:  # and 8 <= int(current_time2()) <= 15:  # 08:00 - 15:00
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True),
                guild.get_member(user.id): discord.PermissionOverwrite(read_messages=True, read_message_history=False)
            }

            gringotts = await guild.create_text_channel("gringotts-bank", category=category, overwrites=overwrites,
                                                        topic=topic)
            await self.generate_data(guild, "gringotts-bank", gringotts)

            if path == "path7":
                await self.update_path(user, cycle, path_new="path8")

        elif "gringotts-bank" in channels:  # and 8 <= int(current_time2()) <= 15:  # 08:00 - 15:00
            gringotts_id = books.find_one({"server": str(guild.id)},
                                          {"gringotts-bank": 1})["gringotts-bank"]["id"]
            gringotts_channel = self.client.get_channel(int(gringotts_id))
            await gringotts_channel.set_permissions(user, read_messages=True, send_messages=True,
                                                    read_message_history=False)
            await gringotts_channel.edit(topic=topic)

            if path == "path7":
                await self.update_path(user, cycle, path_new="path8")

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
                guild.get_member(user.id): discord.PermissionOverwrite(read_messages=True, read_message_history=False)
            }
            ollivanders = await guild.create_text_channel("ollivanders", category=category, overwrites=overwrites)
            await self.generate_data(guild, msg, ollivanders)

            if path == "path10":
                await self.update_path(user, cycle, path_new="path6")  # path_current="10"
                await self.wand_personalise(guild, user, ollivanders, path, cycle)

        elif "ollivanders" in channels:  # and 13 <= int(current_time2()) <= 16:  # 1PM-4PM:
            ollivanders_id = books.find_one({"server": str(guild.id)},
                                            {"ollivanders": 1})["ollivanders"]["id"]
            ollivanders_channel = self.client.get_channel(int(ollivanders_id))
            await ollivanders_channel.set_permissions(user, read_messages=True, send_messages=True,
                                                      read_message_history=False)

            if path == "path10":
                await self.update_path(user, cycle, path_new="path6")
                await self.wand_personalise(guild, user, ollivanders_channel, path, cycle)
        else:
            await self.reaction_closed(message)

    async def wand_personalise(self, guild, user, channel, path, cycle):

        ollivanders = books.find_one({"server": str(guild.id)}, {"_id": 0, "ollivanders": 1})
        print(ollivanders)
        webhook_url = ollivanders["ollivanders"]["webhook"]
        avatar = ollivanders["ollivanders"]["avatar"]
        username = ollivanders["ollivanders"]["username"]

        msg = f"{user.mention}, what can I help you for?"
        webhook = DiscordWebhook(url=webhook_url, content=msg, avatar_url=avatar, username=username)
        webhook.execute()

        def check(guess):
            if guess.author != user:
                return
            elif "wand" in guess.content or "wands" in guess.content:
                return guess.author == user
            else:
                raise KeyError

        try:
            await self.client.wait_for("message", timeout=30, check=check)

            if path == "path10":
                await self.update_path(user, cycle, path_new="path12")  # path_current="10"

                msg = f"{user.mention}, I see you want some wands. Here are the list of my wands."
                topic = "Your wand selection affects your progress and ending results."
                await channel.edit(topic=topic)

                webhook = DiscordWebhook(url=webhook_url, content=msg, avatar_url=avatar, username=username)
                webhook.execute()
                await asyncio.sleep(3)

                msg = "List of Wands:"
                webhook = DiscordWebhook(url=webhook_url, content=msg, avatar_url=avatar, username=username)
                webhook.execute()

            else:
                topic = "Your wand selection affects your progress and ending results."
                await channel.edit(topic=topic)
                webhook = DiscordWebhook(url=webhook_url, content=msg, avatar_url=avatar, username=username)
                webhook.execute()

        except KeyError:
            msg = "Oh! You do not want wands? Very well, please free to browse my shop then."
            webhook = DiscordWebhook(url=webhook_url, content=msg, avatar_url=avatar, username=username)
            webhook.execute()

    async def transaction_gringotts(self, user, guild, msg, message):
        role_galleons = discord.utils.get(message.guild.roles, name="💰")
        cycle, path, timestamp, user_hints, actions, purchase = get_data(user)

        if user in role_galleons.members:
            await self.action_update(user, cycle, actions=3)
            msg = f"{user}, what are you doing here again.\n\nI thought you got what you wanted here already."
            await self.secret_response(guild.id, message.channel.name, msg)
            await self.penalize(user, cycle, points=10)
            await self.logging(f"{user} went back to Gringotts for nothing: {msg}")

        elif user not in role_galleons.members:

            if message.content.startswith == ";" or actions >= 3:
                await self.logging(f"{user} tried to used a command with >= 3 actions -> ignoring")

            elif actions < 3 and "vault" in msg:
                await self.action_update(user, cycle, actions=5)
                await self.update_path(user, cycle, path_new="path18")
                await self.vault_access(cycle, user, guild, role_galleons, message)

            elif actions < 3:
                responses = [
                    "Greetings, {}. What do you want?",

                    "{}, I am assuming you do not know, we secure the wizarding families' treasuries here.\n\n"
                    "Now, what do you want from us?",

                    "{}, I don't think you are well aware of what is happening here.\n\n"
                    "I have other clients to assist, come back again once you know, because I do not like my time "
                    "being wasted. "
                ]

                hint = actions + 1
                await self.action_update(user, cycle, actions=1)
                await self.update_hint(user, cycle, hint)
                await self.penalize(user, cycle, points=10)

                msg = responses[actions].format(user)
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
                    await self.update_path(user, cycle, path_new="path15")

                    secret_channel = books.find_one({"server": str(guild.id)}, {"_id": 0, str(message.channel.name): 1})
                    webhook_url = secret_channel[str(message.channel.name)]["webhook"]
                    avatar = secret_channel[str(message.channel.name)]["avatar"]
                    username = secret_channel[str(message.channel.name)]["username"]
                    webhook = DiscordWebhook(url=webhook_url, avatar_url=avatar, username=username)

                    vault = f"{str(user.id).replace('1', '@').replace('5', '%').replace('7', '&').replace('3', '#')}"
                    embed = DiscordEmbed(color=0xffffff,
                                         title=f":closed_lock_with_key: Opening Vault# {vault}")
                    embed.set_image(url="https://i.imgur.com/RIS1TLh.gif")
                    webhook.add_embed(embed)
                    webhook.execute()
                    await self.logging(f"{user} successfully decoded gringotts")

                    await user.add_roles(role_galleons)
                    await self.logging(f"Added Moneybag role for {user.name}")

                    await asyncio.sleep(6)
                    msg = f"{user.mention} has acquired :moneybag: role"
                    await message.channel.send(msg)

                    msg = "Very well then. You can get out of my bank now."
                    await self.secret_response(guild.id, message.channel.name, msg)

    # noinspection PyUnboundLocalVariable
    async def obtain_identity(self, user, guild, message):
        await self.logging(f"{user} is trying to transact to Gringotts: -> awaits identity")
        cycle, path, timestamp, user_hints, actions, purchase = get_data(user)

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
                await guess.add_reaction("✅")
                await asyncio.sleep(3)
                await guess.delete()

                if path == "path18":
                    await self.update_path(user, cycle, path_new="path5")

                answer = "Correct"
                i = 4

            except asyncio.TimeoutError:
                if thieves.find_one({"names": user.name}, {"_id": 0}) is None:
                    thieves.update_one({}, {"$push": {"names": user.name}})

                msg = f"{user}, it seems that you have trouble showing me your identification.\n\n" \
                    f"I'm gonna have to ask you to get out of my bank. You are wasting my time."
                await self.action_update(user, cycle, actions=3)
                await self.penalize(user, cycle, points=10)
                await self.secret_response(guild.id, message.channel.name, msg)
                topic = "The goblins can await for two minutes for every question they ask"
                await message.channel.edit(topic=topic)
                answer = "Wrong"
                i = 4

            except KeyError:
                if i == 0:
                    msg = f"{user}, that is not what we call identification here!"
                    await self.penalize(user, cycle, points=5)
                    topic = "One customer vault access request ticket can be used every hour"
                    await message.channel.edit(topic=topic)

                elif i == 1:
                    msg = f"{user}, neither that one!\n\nWhat are you even suggesting to me? The identification I am " \
                        f"looking for is a 32 alpha-numeric character!"
                    await self.penalize(user, cycle, points=5)
                    topic = "Identification cards equate to the wizards'/witches'/spirits' avatar"
                    await message.channel.edit(topic=topic)

                elif i == 2:
                    if thieves.find_one({"names": user.name}, {"_id": 0}) is None:
                        thieves.update_one({}, {"$push": {"names": user.name}})

                    msg = f"{user}, I don't think you have any business here!\n\n" \
                        f"I'm gonna have to ask you to get out of my bank. You are plainly wasting my time."
                    await self.action_update(user, cycle, actions=3)
                    await self.penalize(user, cycle, points=10)
                    topic = "Banking Hours: 08:00 - 15:00"
                    await message.channel.edit(topic=topic)
                    answer = "Wrong"

                await self.secret_response(guild.id, message.channel.name, msg)
                i += 1

        await self.logging(f"{user} is trying to transact to Gringotts: -> awaits identity -> Ended")
        return answer

    # noinspection PyUnboundLocalVariable
    async def obtain_vault_number(self, cycle, user, guild, message):
        await self.logging(f"{user} is trying to transact to Gringotts: -> awaits vault number")

        msg = f"Very well then, {user}. And the vault number?"
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
                await guess.add_reaction("✅")
                await asyncio.sleep(3)
                await guess.delete()
                topic = "Banking Hours: 08:00 - 15:00"
                await message.channel.edit(topic=topic)
                answer = "Correct"
                i = 4

            except asyncio.TimeoutError:
                if thieves.find_one({"names": user.name}, {"_id": 0}) is None:
                    thieves.update_one({}, {"$push": {"names": user.name}})

                msg = f"{user}. Are you stealing from someone?\n\nGet the hell out of my bank now!"
                await self.action_update(user, cycle, actions=3)
                await self.penalize(user, cycle, points=10)
                await self.secret_response(guild.id, message.channel.name, msg)

                answer = "Wrong"
                i = 4

            except KeyError:
                if i == 0:
                    msg = f"{user}, my records cannot be wrong, that is an invalid vault number."
                    await self.penalize(user, cycle, points=5)

                elif i == 1:
                    msg = f"{user}, that does not show either!"
                    await self.penalize(user, cycle, points=5)
                    topic = "Gringotts, the wizard bank! Ain't no safer place. Not one. Except perhaps Patronus Castle."
                    await message.channel.edit(topic=topic)

                elif i == 2:
                    if thieves.find_one({"names": user.name}, {"_id": 0}) is None:
                        thieves.update_one({}, {"$push": {"names": user.name}})

                    msg = f"{user}, I don't think you have any business here!\n\n" \
                        f"I'm gonna have to ask you to get out of my bank. You are just wasting my time."
                    await self.action_update(user, cycle, actions=3)
                    await self.penalize(user, cycle, points=10)
                    topic = "Most commonly used passwords:\n1. ALOHOMORA\n2. vault number reversal\n3. Password1234"
                    await message.channel.edit(topic=topic)
                    answer = "Wrong"

                await self.secret_response(guild.id, message.channel.name, msg)
                i += 1

        await self.logging(f"{user} is trying to transact to Gringotts: -> awaits vault number -> Ended")
        return answer

    # noinspection PyUnboundLocalVariable
    async def obtain_vault_password(self, cycle, user, guild, message):
        await self.logging(f"{user} is trying to transact to Gringotts: -> awaits password")

        await asyncio.sleep(1)
        msg = f"Come. We will apparate to your vault. {user}."
        await self.secret_response(guild.id, message.channel.name, msg)

        await asyncio.sleep(3)
        msg = f"Ahhh. Here we are, and your password, {user}?"
        await self.secret_response(guild.id, message.channel.name, msg)

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
                await guess.add_reaction("✅")
                await asyncio.sleep(3)
                await guess.delete()
                answer = "Correct"
                i = 4

            except asyncio.TimeoutError:
                if thieves.find_one({"names": user.name}, {"_id": 0}) is None:
                    thieves.update_one({}, {"$push": {"names": user.name}})

                msg = f"{user}. What do you mean that you forgot? You wasted my time! Get out of my bank!"
                await self.action_update(user, cycle, actions=3)
                await self.penalize(user, cycle, points=5)
                await self.secret_response(guild.id, message.channel.name, msg)
                answer = "Wrong"
                i = 4

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
                    await self.action_update(user, cycle, actions=3)
                    await self.penalize(user, cycle, points=10)
                    answer = "Wrong"

                await self.secret_response(guild.id, message.channel.name, msg)
                i += 1

        await self.logging(f"{user} is trying to transact to Gringotts: -> awaits Ended")
        return answer


def setup(client):
    client.add_cog(Magic(client))
