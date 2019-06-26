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

from cogs.mongo.db import books, quests, owls, weather, sendoff

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


class Magic(commands.Cog):

    def __init__(self, client):
        self.client = client

    async def logging(self, msg):
        channel = self.client.get_channel(592270990894170112)
        date_time = datetime.now(tz=tz_target).strftime("%Y-%b-%d %HH")
        await channel.send(f"[{date_time}] " + msg)

    async def sendoff_owl(self, user, reaction, cycle):
        await reaction.message.channel.send("Sending off owl to the :trident: Headmaster's Tower")
        await asyncio.sleep(2)
        await reaction.message.channel.send(f"{user.mention}, you will receive an update when the clock moves an hour")
        await self.generate_owl_report(user, cycle)
        await self.logging(f"{user.name} has successfully sendoff their owl to the Headmaster's Office")

    # noinspection PyUnboundLocalVariable,PyUnusedLocal
    async def generate_owl_report(self, user, cycle):
        profile = sendoff.find({"user_id": str(user.id)}, {"_id": 0})
        weather1 = weather.find_one({"weather1": {"$type": "string"}}, {"weather1": 1})["weather1"]
        weather2 = weather.find_one({"weather2": {"$type": "string"}}, {"weather2": 1})["weather2"]

        if weather1 == "⛈":  # Thunderstorms
            await self.update_path(user, cycle, path_new="path19")
            report = "Your owl returned to you crawling on its feathers due to the ⛈Thunderstorms.\n" \
                     "Your owl will recover in 3 hours before you can send it off again."
            delay = 1 + 3
            scenario = 1

        elif weather1 == "🌨" and profile["type"] == "Snowy Owl":  # Snowy owl and Snowy weather
            report = "Your owl travelled hastily to the Headmaster's Office due to favorable 🌨 weather\n" \
                     "Estimated time of return: in 1 hour"
            delay = 1 + 1
            scenario = 2

        elif weather2 == "🌕" or weather2 == "🌑":  # Night
            report = "Owls are best at night and can return faster than normal travel time\n" \
                     "Estimated time of return: in 1 hour"
            delay = 1 + 1
            scenario = 2

        elif weather1 == "🌧":  # Rainy
            report = "Your owl struggled to reached the Headmaster's Office on time due to the 🌧rainy weather\n" \
                     "Estimated time of return: in 2 hours"
            delay = 1 + 2
            scenario = 2

        elif weather1 == "☁" or weather1 == "⛅":  # Cloudy & Partly sunny
            report = "Your owl has safely arrived at the Headmaster's Office\n" \
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
                           f"--> Scenario: {scenario}\n")

    # noinspection PyUnusedLocal,PyShadowingNames
    async def update_path(self, user, cycle, path_new):
        if path_new == "path2":
            quests.update_one({"user_id": str(user.id), "quest1.cycle": cycle},
                              {"$set": {"quest1.$.current_path": path_new, "quest1.$.timestamp": current_timestamp(),
                                        "quest1.$.actions": 0,
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
        await self.logging(f"Adding an {actions} action point/s for {user.name}")

    # noinspection PyUnusedLocal
    async def update_hint(self, user, cycle, hint):
        quests.update_one({"user_id": str(user.id), "quest1.cycle": cycle},
                          {"$set": {f"quest1.$.hints.{hint}": "unlocked", f"quest1.$.timestamp": current_timestamp()}})
        quests.update_one({"user_id": str(user.id), "quest1.cycle": cycle},
                          {"$inc": {f"quest1.$.hints_unlocked": 1}})
        await self.logging("Updating and adding hints locked")

    async def generate_data(self, guild, secret_channel, channel):

        channel_name = secret_channel.replace(" ", "-")
        webhook = await channel.create_webhook(name="webhooker")
        books.update_one({"server": str(guild.id)},
                         {"$set": {f"{channel_name}.id": str(channel.id), f"{channel_name}.webhook": webhook.url}})

        if channel_name == "eeylops-owl-emporium":
            books.update_one({"server": str(guild.id)},
                             {"$set": {f"{channel_name}.avatar": "https://i.imgur.com/8xR61b4.jpg",
                                       f"{channel_name}.username": "Manager Eeylops"}})

        elif channel_name == "gringotts-bank":
            books.update_one({"server": str(guild.id)},
                             {"$set": {f"{channel_name}.avatar": "https://i.imgur.com/IU882rV.jpg",
                                       f"{channel_name}.username": "Bank Manager Gringotts"}})

        elif channel_name == "ollivanders":
            books.update_one({"server": str(guild.id)},
                             {"$set": {f"{channel_name}.avatar": "https://i.imgur.com/sSgxEJO.jpg",
                                       f"{channel_name}.username": "Ollivanders"}})

        await self.logging(f"Generating secret channel: {channel_name} and its webhook")

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
            await self.logging(f"{user.name} successfully finished the quest")
            cycle, path, timestamp, user_hints, actions, purchase = get_data(user)
            quests.update_one({"user_id": str(user.id), "quest1.cycle": cycle},
                              {"$set": {"quest1.$.status": "completed"}})

        elif path == "path3":
            await self.update_path(user, cycle, path_new="path10")
            await message.add_reaction("❎")
            await self.logging(f"{user.name} tried to cast the Patronus summoning spell")

        elif path == "path10":
            await message.add_reaction("❔")
            await self.penalize(user, cycle, points=10)
            await self.logging(f"{user.name} tried to recast the Patronus summoning spell to no avail")

    @commands.command(aliases=["progress"])
    @commands.has_role("✨")
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

            embed = discord.Embed(description=description)
            embed.set_author(name=f"{ctx.message.author}'s Cycle #{cycle}", icon_url=ctx.message.author.avatar_url)
            await ctx.channel.send(embed=embed)
            await self.logging(f"{ctx.message.author.name} requested to show their progress")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):

        if str(payload.emoji) != "✉":
            return

        request = books.find_one({"server": f"{payload.guild_id}"},
                                 {"_id": 0, "welcome": 1, "sorting": 1, "letter": 1})

        if str(payload.emoji) == "✉" and payload.message_id == int(request['letter']):
            user = self.client.get_user(payload.user_id)

            if quests.find_one({"user_id": str(user.id)}, {"_id": 0}) is None:
                profile = {"user_id": str(payload.user_id), "quest1": []}
                quests.insert_one(profile)
                await self.logging(f"Successfully created quest profile for {user.name}")

            for i in (range(50)):
                cycle = i + 1
                if len(quests.find_one({"user_id": str(payload.user_id)}, {"_id": 0})["quest1"]) != cycle:
                    quests.update_one({"user_id": str(user.id)},
                                      {"$push": {"quest1": dict(status="ongoing", cycle=cycle, score=1000,
                                                                timestamp=current_timestamp(),
                                                                timestamp_start=current_timestamp(),
                                                                current_path="path1", actions=0,
                                                                purchase=False,
                                                                hints_unlocked=0,
                                                                hints=["locked", "locked", "locked", "locked",
                                                                       "locked"])}})
                    await self.logging(f"Successfully started cycle#{cycle} for {user.name}")
                    break

            user = self.client.get_user(int(payload.user_id))
            description = f"Dear {user.name},\n\nWe are pleased to accept you at House Patronus.\nDo browse " \
                f"the server's <#{request['welcome']}> channel for the basics and essentials of the guild then " \
                f"proceed to <#{request['sorting']}> to assign yourself some roles.\n\nWe await your return owl.\n\n" \
                f"Yours Truly,\nThe Headmaster "

            embed = discord.Embed(color=0xffff80, title=":love_letter: Acceptance Letter", description=description)
            await user.send(embed=embed)
            await self.logging(f"Successfully sent {user.name} their first clue through DM")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user == self.client.user:
            return

        elif reaction.message.author.bot:
            return

        elif str(reaction.emoji) == "🦉":
            role_owl = discord.utils.get(reaction.message.guild.roles, name="🦉").members
            request = books.find_one({"server": f"{reaction.message.guild.id}"},
                                     {"_id": 0, "tower": 1})

            if user not in role_owl:
                await self.logging(f"{user.name} tried to sendoff an owl but doesnt have the owl role")
                return

            elif request["tower"] not in str(reaction.message.content) or "✉" not in str(reaction.message.content):
                await self.logging(f"{user.name} has the owl role but the message is wrong (no channel/envelope emoji)")
                await reaction.message.add_reaction("❔")

            elif request["tower"] in str(reaction.message.content) and "✉" in str(reaction.message.content):
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
                    await reaction.message.channel.send(f"{user.mention}, Your owl is paralyzed due to your "
                                                        f"carelessness. Please wait until full recovery")
                    await asyncio.sleep(2)
                    await reaction.message.delete()
                    await self.logging(f"{user.name} tried to sendoff while owl is recovering")

    # noinspection PyUnboundLocalVariable
    @commands.command(aliases=["hint"])
    @commands.has_role("✨")
    async def hint_request(self, ctx):
        user = ctx.message.author

        # Not accepted the quest
        if not check_quest(user):
            await self.logging(f"{user.name} tried to use hint while the quest is not yet accepted")
            return

        # With quest acceptance
        elif check_quest(user):
            cycle, path, timestamp, user_hints, actions, purchase = get_data(user)
            t1 = datetime.strptime(timestamp, "%Y-%b-%d %HH")
            t2 = datetime.strptime(current_timestamp(), "%Y-%b-%d %HH")
            delta = (t2 - t1).days * 24 + (t2 - t1).seconds // 3600

            # Hint cooldown of 3 hours  # if delta <= 2:
            if delta >= 101:
                await ctx.channel.send(f"{user.mention}, you must wait for {3 - delta} hr before you can reveal a hint")
                await self.logging(f"{user.name} used hint while on cooldown")

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
                    if path == "path6" and ctx.channel.name != "eeylops-owl-emporium":
                        await user.send(f"These path hints can only be revealed in the secret channel")
                        await self.logging(f"{user.name} is under path6 and used hint in the wrong channel! DM'ed!")

                    # Path 8 as Gringotts transactions, hint starts at #4
                    elif path == "path8":
                        h = 3
                        while h <= 4:
                            if user_hints[h] == "locked":
                                hint_num = str(h + 1)
                                await self.update_hint(user, cycle, h)
                                await self.penalize(user, cycle, points=10)

                                embed = discord.Embed(color=user.colour, description=hints[path][hint_num])
                                embed.set_footer(icon_url=user.avatar_url, text=f"Path {path[4::]} | Hint# {hint_num}")
                                await user.send(embed=embed)
                                await self.logging(f"Sent a hint for {user.name} | {path}:{hint_num}")

                                break
                            h += 1

                        if h == 5:
                            raise IndexError

                    # Specific hint revelation
                    elif path == "path15" and ctx.channel.name == "gringotts-bank":
                        await self.penalize(user, cycle, points=5)
                        await ctx.channel.send(f"{user.mention}, don't we have what we wanted here already?")
                        await self.logging(f"S{user.name} transacted with gringotts with moneybag role already"
                                           f" | {path}")

                    else:
                        await self.update_hint(user, cycle, h)
                        await self.penalize(user, cycle, points=10)
                        await ctx.message.add_reaction("✅")

                        embed = discord.Embed(color=user.colour, description=hint)
                        embed.set_footer(icon_url=user.avatar_url, text=f"Path {path[4::]} | Hint# {hint_num}")
                        await user.send(embed=embed)
                        await self.logging(f"Sent a hint for {user.name} | {path}:{hint_num}")

                except IndexError:
                    await user.send(f"{user.mention}, you have used up all your hints for the path.")
                    await self.logging(f"{user.name} has used up all their hints | {path}")

                except KeyError:
                    await user.send(f"{user.mention}, you have used up all your hints for the path.")
                    await self.logging(f"{user.name} has used up all their hints | {path}")

    @commands.command(
        aliases=["knock", "knockknock", "knockknockknock", "knockknockknockknock", "knockknockknockknockknock"])
    @commands.cooldown(1, 3600, commands.BucketType.user)
    @commands.has_role("✨")
    async def knocking(self, ctx):
        knocks = str(int(len(ctx.message.content.replace("%", "")) / 5))
        await ctx.message.delete()
        if str(ctx.channel.name) == "eeylops-owl-emporium":

            user = ctx.author
            cycle, path, timestamp, user_hints, actions, purchase = get_data(user)

            channel = books.find_one({"server": str(ctx.guild.id)}, {"_id": 0, str(ctx.channel.name): 1})
            webhook_url = channel[str(ctx.channel.name)]["webhook"]
            avatar = channel[str(ctx.channel.name)]["avatar"]
            username = channel[str(ctx.channel.name)]["username"]

            # noinspection PyShadowingNames
            def get_info(x):
                if x == "1":
                    msg = "Welcome to the Emporium! We have all your feathered friend’s requirements here."
                    topic = "Be wary, we have limited stocks!"
                    return msg, topic
                elif x == "2":
                    msg = "Here at the Emporium, we sell Eeylops Premium Owl Treats. " \
                          "A treat shaped like a mice that is the best thing for a happy and healthy owl."
                    topic = "Stocks refresh every day! So better hurry before you run our of owls!"
                    return msg, topic
                elif x == "3":
                    msg = "We sell only the best of our trained owls to carry your letters. " \
                          "No address is needed as owls can find any witch or wizard whose name is on the letter"
                    topic = "Sending off your owl is very easy! Just add the owl to your item emoji and channel! " \
                            "Simple but complex as magic!"
                    return msg, topic
                elif x == "4":
                    msg = "We have Brown, Screech, Snowy, Tawny and Barred owls. " \
                          "Find your precious feathered friend from the low price of 11 Galleons."
                    topic = "I only open the store during certain hours and weather, " \
                            "if you can't find the store then no magic can!"
                    return msg, topic
                elif x == "5":
                    msg = "What are you waiting for? Command to purchase an owl!"
                    topic = "Store hours: 6 hours opened everyday but which hours?"
                    return msg, topic

            if path == "path6" or path == "path13" or path == "path2":
                if path == "path6":
                    await self.update_path(user, cycle, path_new="path13")

                msg, topic = get_info(knocks)
                await self.penalize(user, cycle, points=5)
                await ctx.channel.edit(topic=topic)
                webhook = DiscordWebhook(url=webhook_url, content=msg, avatar_url=avatar, username=username)
                webhook.execute()
                await self.logging(f"{user.name} knocks {knocks} times: changing the channel topic")

            else:
                knocks = "1"
                msg, topic = get_info(knocks)
                await self.penalize(user, cycle, points=5)
                await ctx.channel.edit(topic=topic)
                webhook = DiscordWebhook(url=webhook_url, content=msg, avatar_url=avatar, username=username)
                webhook.execute()
                await self.logging(f"{user.name} knocks {knocks} time -> default for their path")
        else:
            self.client.get_command("knocking").reset_cooldown(ctx)

    @commands.command(aliases=["purchase"])
    @commands.has_role("✨")
    async def buy_items(self, ctx, *args):

        if ctx.channel.name != "eeylops-owl-emporium":
            return

        elif ctx.channel.name == "eeylops-owl-emporium":

            try:
                query = args[0].title()
            except IndexError:
                self.client.get_command("buy_items").reset_cooldown(ctx)
                return

            user = ctx.author
            owl_buy = f"{query} Owl"
            cycle, path, timestamp, user_hints, actions, purchase = get_data(user)
            channel = books.find_one({"server": str(ctx.guild.id)}, {"_id": 0, str(ctx.channel.name): 1})
            webhook_url = channel[str(ctx.channel.name)]["webhook"]
            avatar = channel[str(ctx.channel.name)]["avatar"]
            username = channel[str(ctx.channel.name)]["username"]

            if purchase is False:
                msg = f"{ctx.author.mention}, I'm sorry dear. I only cater to guests once in a while. " \
                    f"Comeback again when the minute ticks zero"
                webhook = DiscordWebhook(url=webhook_url, content=msg, avatar_url=avatar, username=username)
                webhook.execute()
                await self.logging(f"{ctx.author.name} is trying purchase again but on hour cooldown")

            if owl_buy not in owls_list:
                msg = "My hearing must have been getting old. Which kind of owl is it again?"
                await self.penalize(user, cycle, points=10)
                webhook = DiscordWebhook(url=webhook_url, content=msg, avatar_url=avatar, username=username)
                webhook.execute()

                await self.logging(f"{user.name} tried to buy {owl_buy} but its not in the available list of owls")

            elif owl_buy in owls_list:
                purchaser = owls.find_one({"type": f"{owl_buy}"}, {"_id": 0, "purchaser": 1})["purchaser"]

                if purchaser != "None":

                    await self.penalize(user, cycle, points=5)
                    msg = f"My Dear, that owl has been bought earlier " \
                        f"by {self.client.get_user(int(purchaser)).name}. " \
                        f"Do come early tomorrow should you wish the same owl!"
                    webhook = DiscordWebhook(url=webhook_url, content=msg, avatar_url=avatar, username=username)
                    webhook.execute()
                    await quests.update_one({"user_id": str(user.id), "quest1.cycle": cycle},
                                            {"$set": {"quest1.$.purchase_owl": False}})
                    await self.logging(f"{user.name} tried to buy {owl_buy} but it has been purchased already")

                elif purchaser == "None":
                    role_galleons = discord.utils.get(ctx.guild.roles, name="💰")
                    if user not in role_galleons.members:
                        await self.update_path(user, cycle, path_new="path7")  # path_current="13"
                        await self.penalize(user, cycle, points=5)
                        msg = f"{user.mention}, my Dear, this does not come for free."
                        webhook = DiscordWebhook(url=webhook_url, content=msg, avatar_url=avatar, username=username)
                        webhook.execute()
                        await quests.update_one({"user_id": str(user.id), "quest1.cycle": cycle},
                                                {"$set": {"quest1.$.purchase_owl": False}})
                        await self.logging(f"{user.name} tried to buy {owl_buy} but they have no moneybag role")
                    else:
                        role_owl = discord.utils.get(ctx.guild.roles, name="🦉")
                        owls.update_one({"type": f"{owl_buy}"}, {"$set": {"purchaser": str(user.id)}})
                        sendoff.insert_one({"user_id": str(user.id), "type": owl_buy})
                        await ctx.message.add_reaction("🦉")
                        await self.update_path(user, cycle, path_new="path2")  # path_current="13"
                        await user.add_roles(role_owl)
                        await ctx.channel.send("You have acquired 🦉 role")
                        msg = "What a lovely choice of owl!"
                        webhook = DiscordWebhook(url=webhook_url, content=msg, avatar_url=avatar, username=username)
                        webhook.execute()

                        await self.logging(f"{user.name} bought {owl_buy}")

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

        elif message.content.lower() == "gringotts bank" and str(message.channel.category) == "⛲ Diagon Alley" \
                and str(message.channel) != "gringotts-bank":
            await self.create_gringotts(message.channel.category, message.guild,
                                        message.content.lower(), message, message.author)

        elif message.content.lower() == "ollivanders" and str(message.channel.category) == "⛲ Diagon Alley" \
                and str(message.channel) != "ollivanders":
            await self.create_ollivanders(message.channel.category, message.guild,
                                          message.content.lower(), message, message.author)

        elif "gringotts-bank" == str(message.channel) and message.content.startswith("%") is False:
            await self.transaction_gringotts(message.author, message.guild, message.content.lower(),
                                             message)

        elif spell_check(message.content):
            await self.expecto(message.guild, message.author, message.channel, message)

    async def create_emporium(self, category, guild, msg, message, user):
        channels = [channel.name for channel in category.text_channels]
        cycle, path, timestamp, user_hints, actions, purchase = get_data(user)
        await self.logging(f"{user.name} tried to open a secret channel `{msg} opened at 7AM-1PM`")

        if "eeylops-owl-emporium" not in channels:  # and 7 <= int(current_time2()) <= 13:  # 7AM-1PM
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

        elif "eeylops-owl-emporium" in channels:  # and 7 <= int(current_time2()) <= 13:  # 7AM-1PM
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
        await self.logging(f"{user.name} tried to open a secret channel `{msg} opened at 9AM-2PM`")

        if "gringotts-bank" not in channels:  # and 9 <= int(current_time2()) <= 14:  # 9AM-2PM
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True),
                guild.get_member(user.id): discord.PermissionOverwrite(read_messages=True, read_message_history=False)
            }
            gringotts = await guild.create_text_channel("gringotts-bank", category=category, overwrites=overwrites)
            await self.generate_data(guild, msg, gringotts)

            if path == "path7":
                await self.update_path(user, cycle, path_new="path8")

        elif "gringotts-bank" in channels:  # and 9 <= int(current_time2()) <= 14:  # 9AM-2PM:
            gringotts_id = books.find_one({"server": str(guild.id)},
                                          {"gringotts-bank": 1})["gringotts-bank"]["id"]
            gringotts_channel = self.client.get_channel(int(gringotts_id))
            await gringotts_channel.set_permissions(user, read_messages=True, send_messages=True,
                                                    read_message_history=False)

            if path == "path7":
                await self.update_path(user, cycle, path_new="path8")  # path_current=""
        else:
            await self.reaction_closed(message)

    async def create_ollivanders(self, category, guild, msg, message, user):
        channels = [channel.name for channel in category.text_channels]
        cycle, path, timestamp, user_hints, actions, purchase = get_data(user)
        await self.logging(f"{user.name} tried to open a secret channel `{msg} opened at 1PM-4PM`")

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
        gringotts = books.find_one({"server": str(guild.id)}, {"_id": 0, "gringotts-bank": 1})
        webhook_url = gringotts["gringotts-bank"]["webhook"]
        avatar = gringotts["gringotts-bank"]["avatar"]
        username = gringotts["gringotts-bank"]["username"]
        cycle, path, timestamp, user_hints, actions, purchase = get_data(user)

        if user not in role_galleons.members:

            with open("data/hints.json") as f:
                hints = json.load(f)

            if message.content.startswith == ";":
                await self.logging(f"{user.name} tried to used a command -> ignoring it")
                return

            elif actions <= 3 and "vault" in msg:
                await self.action_update(user, cycle, actions=3)
                await self.vault_access(cycle, user, webhook_url, avatar, username, role_galleons, message)

            elif actions > 3 or ";" in str(message.content) or path == "path18":
                return

            elif actions == 0:
                await self.action_update(user, cycle, actions=1)
                await self.update_hint(user, cycle, hint="0")

                msg = (hints["path8"]["1"]).format(user.mention)
                webhook = DiscordWebhook(url=webhook_url, content=msg, avatar_url=avatar, username=username)
                webhook.execute()
                await self.logging(f"Posted a hint for {user.name}: {msg}")

            elif actions == 1:
                await self.action_update(user, cycle, actions=1)
                await self.update_hint(user, cycle, hint="1")
                await message.add_reaction("❎")

                msg = (hints["path8"]["2"]).format(user.mention)
                webhook = DiscordWebhook(url=webhook_url, content=msg, avatar_url=avatar, username=username)
                webhook.execute()
                await self.logging(f"Posted a hint for {user.name}: {msg}")

            elif actions == 2:
                await self.action_update(user, cycle, actions=1)
                await self.update_hint(user, cycle, hint="2")

                msg = (hints["path8"]["3"]).format(user.mention)
                webhook = DiscordWebhook(url=webhook_url, content=msg, avatar_url=avatar, username=username)
                webhook.execute()
                await self.logging(f"Posted a hint for {user.name}: {msg}")

        else:
            if actions <= 3:
                await self.action_update(user, cycle, actions=3)
                msg = "{}, I know you. What are you doing here again. Didn't you get what you wanted already?".format(
                    user.mention)
                webhook = DiscordWebhook(url=webhook_url, content=msg, avatar_url=avatar, username=username)
                webhook.execute()
                await self.logging(f"{user.name} went back to Gringotts for nothing: {msg}")

    async def vault_access(self, cycle, user, webhook_url, avatar, username, role_galleons, message):
        await self.update_path(user, cycle, path_new="path18")  # path_current="8"

        msg = "Your identification, please? {}".format(user.mention)
        webhook = DiscordWebhook(url=webhook_url, content=msg, avatar_url=avatar, username=username)
        webhook.execute()
        await self.logging(f"{user.name} is trying to transact to Gringotts: -> awaits identification")

        identity = await self.obtain_identity(cycle, user, webhook_url, avatar, username, message)
        if identity != "Wrong":
            vault_number = await self.obtain_vault_number(cycle, user, webhook_url, avatar, username, message)
            if vault_number != "Wrong":
                vault_password = await self.obtain_vault_password(cycle, user, webhook_url, avatar, username, message)
                if vault_password != "Wrong":
                    await self.update_path(user, cycle, path_new="path15")

                    embed = DiscordEmbed(color=6118749,
                                         title=":closed_lock_with_key: Opening Vault# {}".format(user.id))
                    embed.set_image(url="https://i.imgur.com/RIS1TLh.gif")
                    webhook = DiscordWebhook(embed=embed, url=webhook_url, avatar_url=avatar, username=username)
                    webhook.add_embed(embed)
                    webhook.execute()
                    await self.logging(f"{user.name} successfully decoded gringotts")

                    await user.add_roles(role_galleons)
                    await self.logging(f"Added Moneybag role for {user.name}")

                    await asyncio.sleep(6)
                    msg = "You acquired :moneybag: role"
                    await message.channel.send(msg)

                    msg = "Now get out of my bank."
                    webhook = DiscordWebhook(url=webhook_url, content=msg, avatar_url=avatar, username=username)
                    webhook.execute()

    # noinspection PyUnboundLocalVariable
    async def obtain_identity(self, cycle, user, webhook_url, avatar, username, message):
        await self.logging(f"{user.name} is trying to transact to Gringotts: -> awaits identity")

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
                guess = await self.client.wait_for("message", timeout=180, check=check)
                await guess.delete()
                await self.update_path(user, cycle, path_new="path5")
                answer = "Correct"
                i = 4

            except asyncio.TimeoutError:
                msg = "{}. It seems that you have trouble showing me your identification. Get out of my Bank.".format(
                    user.mention)
                await self.action_update(user, cycle, actions=3)
                await self.penalize(user, cycle, points=10)
                webhook = DiscordWebhook(url=webhook_url, content=msg, avatar_url=avatar, username=username)
                webhook.execute()
                answer = "Wrong"
                i = 4

            except KeyError:
                if i == 0:
                    msg = "{}, that is not what we call identification here!".format(user.mention)
                    await self.penalize(user, cycle, points=5)
                elif i == 1:
                    msg = "{}, neither that one!".format(user.mention)
                    await self.penalize(user, cycle, points=5)
                elif i == 2:
                    msg = "{}, you don't have business here! Get out of my Bank".format(user.mention)
                    await self.action_update(user, cycle, actions=3)
                    await self.penalize(user, cycle, points=10)
                    answer = "Wrong"
                webhook = DiscordWebhook(url=webhook_url, content=msg, avatar_url=avatar, username=username)
                webhook.execute()
                i += 1
        await self.logging(f"{user.name} is trying to transact to Gringotts: -> awaits identity -> Ended")
        return answer

    # noinspection PyUnboundLocalVariable
    async def obtain_vault_number(self, cycle, user, webhook_url, avatar, username, message):
        await self.logging(f"{user.name} is trying to transact to Gringotts: -> awaits vault number")

        msg = "Very well then. And the vault number? {}".format(user.mention)
        webhook = DiscordWebhook(url=webhook_url, content=msg, avatar_url=avatar, username=username)
        webhook.execute()

        # noinspection PyShadowingNames
        def check(guess):
            if guess.channel != message.channel:
                return
            elif str(guess.content) == str(user.id) and guess.author == user and guess.channel == message.channel:
                return True
            elif guess.author == user and "%" not in str(guess.content):
                raise KeyError

        i = 0
        while i < 3:
            try:
                guess = await self.client.wait_for("message", timeout=180, check=check)
                await guess.delete()
                answer = "Correct"
                i = 4

            except asyncio.TimeoutError:
                msg = "{}. Are you stealing from someone? Get out of my Bank.".format(user.mention)
                await self.action_update(user, cycle, actions=3)
                await self.penalize(user, cycle, points=10)
                webhook = DiscordWebhook(url=webhook_url, content=msg, avatar_url=avatar, username=username)
                webhook.execute()
                answer = "Wrong"
                i = 4

            except KeyError:
                if i == 0:
                    msg = "{}, my records cannot be wrong, that is an invalid vault number!".format(user.mention)
                    await self.penalize(user, cycle, points=5)
                elif i == 1:
                    msg = "{}, that does not show either!".format(user.mention)
                    await self.penalize(user, cycle, points=5)
                elif i == 2:
                    msg = "{}, you don't have business here! Get out of my Bank".format(user.mention)
                    await self.action_update(user, cycle, actions=3)
                    await self.penalize(user, cycle, points=10)
                    webhook.execute()
                    answer = "Wrong"
                webhook = DiscordWebhook(url=webhook_url, content=msg, avatar_url=avatar, username=username)
                webhook.execute()
                i += 1
        await self.logging(f"{user.name} is trying to transact to Gringotts: -> awaits vault number -> Ended")
        return answer

    # noinspection PyUnboundLocalVariable
    async def obtain_vault_password(self, cycle, user, webhook_url, avatar, username, message):
        await self.logging(f"{user.name} is trying to transact to Gringotts: -> awaits password")

        await asyncio.sleep(1)
        msg = f"Come. We will apparate to your vault. {user.mention}"
        webhook = DiscordWebhook(url=webhook_url, content=msg, avatar_url=avatar, username=username)
        webhook.execute()

        await asyncio.sleep(3)
        msg = f"Ahhh. Here we are, and your password? {user.mention}"
        webhook = DiscordWebhook(url=webhook_url, content=msg, avatar_url=avatar, username=username)
        webhook.execute()

        # noinspection PyShadowingNames
        def check(guess):
            if guess.channel != message.channel:
                return
            elif str(guess.content) == (str(user.id))[::-1] and guess.author == user \
                    and guess.channel == message.channel:
                return True
            elif guess.author == user and "%" not in str(guess.content):
                raise KeyError

        i = 0
        while i < 4:
            try:
                guess = await self.client.wait_for("message", timeout=180, check=check)
                await guess.delete()
                answer = "Correct"
                i = 4

            except asyncio.TimeoutError:
                msg = f"{user.mention}. What do you mean you forgot? You wasted my time! Get out of my Bank!"
                await self.action_update(user, cycle, actions=3)
                await self.penalize(user, cycle, points=5)
                webhook = DiscordWebhook(url=webhook_url, content=msg, avatar_url=avatar, username=username)
                webhook.execute()
                answer = "Wrong"
                i = 4

            except KeyError:
                if i == 0:
                    msg = "Weird. It did not work"
                    await self.penalize(user, cycle, points=5)
                elif i == 1:
                    msg = "Huhh.. Are you sure that is the correct password?!"
                    await self.penalize(user, cycle, points=5)
                elif i == 2:
                    msg = "You waste my time. Get out of my Bank."
                    await self.action_update(user, cycle, actions=3)
                    await self.penalize(user, cycle, points=10)
                    answer = "Wrong"
                webhook = DiscordWebhook(url=webhook_url, content=msg, avatar_url=avatar, username=username)
                webhook.execute()
                i += 1
        await self.logging(f"{user.name} is trying to transact to Gringotts: -> awaits Ended")
        return answer


def setup(client):
    client.add_cog(Magic(client))
