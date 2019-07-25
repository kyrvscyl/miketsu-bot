"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import asyncio
import json
import random
from datetime import datetime, timedelta

import discord
import pytz
from discord.ext import commands
from discord_webhook import DiscordWebhook, DiscordEmbed

from cogs.mongo.db import owls, weather, sendoff, patronus
from cogs.mongo.db import quests, books, thieves

diagon_alleys = []
for guild_channel in books.find({}, {"_id": 0, "categories.diagon-alley": 1}):
    diagon_alleys.append(guild_channel["categories"]["diagon-alley"])


def get_time():
    tz_target = pytz.timezone("America/Atikokan")
    return datetime.now(tz=tz_target)


def check_quest(user):
    return quests.find_one({"user_id": str(user.id)}, {"_id": 0, "user_id": 1}) != {}


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

    else:
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


async def secret_banner(webhook_url, avatar, username, url):
    webhook = DiscordWebhook(url=webhook_url, avatar_url=avatar, username=username)
    embed = DiscordEmbed(color=0xffffff)
    embed.set_image(url=url)
    webhook.add_embed(embed)
    webhook.execute()


async def reaction_closed(message):
    await message.add_reaction("🇨")
    await message.add_reaction("🇱")
    await message.add_reaction("🇴")
    await message.add_reaction("🇸")
    await message.add_reaction("🇪")
    await message.add_reaction("🇩")
    await asyncio.sleep(4)
    await message.delete()


async def secret_response(guild_id, channel_name, description):
    secret = books.find_one({"server": str(guild_id)}, {"_id": 0, str(channel_name): 1})
    webhook_url = secret[str(channel_name)]["webhook"]
    avatar = secret[str(channel_name)]["avatar"]
    username = secret[str(channel_name)]["username"]
    webhook = DiscordWebhook(url=webhook_url, avatar_url=avatar, username=username)
    embed = DiscordEmbed(color=0xffffff, description="*\"" + description + "\"*")
    webhook.add_embed(embed)
    webhook.execute()


owls_list = []
for owl in owls.find({}, {"_id": 0, "type": 1}):
    owls_list.append(owl["type"])

diagon_alleys = []
for guild_channel in books.find({}, {"_id": 0, "categories.diagon-alley": 1}):
    diagon_alleys.append(guild_channel["categories"]["diagon-alley"])

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


def get_time():
    tz_target = pytz.timezone("America/Atikokan")
    return datetime.now(tz=tz_target)


def get_data_quest1(user_id):
    data = quests.aggregate([{
        "$match": {"user_id": str(user_id)}}, {
        "$project": {
            "_id": 0, "quest1": {
                "$slice": ["$quest1", -1]}
        }}
    ])

    cycle, current_path, timestamp, hints, actions, purchase = "", "", "", "", "", ""

    for profile in data:
        cycle = profile["quest1"][0]["cycle"]
        current_path = profile["quest1"][0]["current_path"]
        timestamp = profile["quest1"][0]["timestamp"]
        hints = profile["quest1"][0]["hints"]
        actions = profile["quest1"][0]["actions"]
        purchase = profile["quest1"][0]["purchase"]
        break
    return cycle, current_path, timestamp, hints, actions, purchase


def get_profile_finished_quest1(user):
    data = quests.aggregate([{
        "$match": {
            "user_id": str(user.id)}}, {
        "$project": {
            "_id": 0,
            "quest1": {
                "$slice": ["$quest1", -1]
            }}
    }])

    score, timestamp_start, patronus_summon, hints_unlocked, owl_final, wand, paths = "", "", "", "", "", "", ""

    for profile in data:
        patronus_summon = profile["quest1"][0]["patronus"]
        score = profile["quest1"][0]["score"]
        timestamp_start = profile["quest1"][0]["timestamp_start"]
        hints_unlocked = profile["quest1"][0]["hints_unlocked"]
        owl_final = profile["quest1"][0]["owl"]
        wand = profile["quest1"][0]["wand"]
        paths = profile["quest1"][0]["hints"]
        break

    return score, timestamp_start, patronus_summon, hints_unlocked, owl_final, wand, paths


def get_profile_history_quest1(user, cycle):
    data = quests.aggregate([{
        '$match': {
            'user_id': str(user.id)}}, {
        '$unwind': {
            'path': '$quest1'}}, {
        '$match': {
            'quest1.cycle': cycle
        }
    }
    ])
    for result in data:
        return result


def get_profile_progress_quest1(user):
    data = quests.aggregate([{
        "$match": {
            "user_id": str(user.id)}}, {
        "$project": {
            "_id": 0,
            "quest1": {"$slice": ["$quest1", -1]}
        }
    }])

    score, timestamp_start, current_path, cycle, hints_unlocked, paths = "", "", "", "", "", ""

    for profile in data:
        cycle = profile["quest1"][0]["cycle"]
        current_path = profile["quest1"][0]["current_path"]
        score = profile["quest1"][0]["score"]
        timestamp_start = profile["quest1"][0]["timestamp_start"]
        hints_unlocked = profile["quest1"][0]["hints_unlocked"]
        paths = profile["quest1"][0]["hints"]
        break

    return score, timestamp_start, current_path, cycle, hints_unlocked, paths


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


async def owls_restock():
    owls.update_many({}, {"$set": {"purchaser": "None"}})


def get_responses_quest1(key):
    with open("data/responses1.json") as f:
        responses = json.load(f)
    return responses[key]


async def penalize_quest1(user, cycle, points):
    quests.update_one({"user_id": str(user.id), "quest1.cycle": cycle}, {"$inc": {"quest1.$.score": -points}})


async def action_update_quest1(user, cycle, actions):
    quests.update_one({"user_id": str(user.id), "quest1.cycle": cycle}, {"$inc": {"quest1.$.actions": actions}})


async def update_hint_quest1(user, path, cycle, hint):
    quests.update_one({
        "user_id": str(user.id), "quest1.cycle": cycle}, {
        "$set": {
            f"quest1.$.hints.{path}.{hint}": "unlocked",
            f"quest1.$.timestamp": get_time().strftime("%Y-%b-%d %HH")
        },
        "$inc": {
            f"quest1.$.hints_unlocked": 1
        }
    })


class Quest(commands.Cog):

    def __init__(self, client):
        self.client = client

    async def logging(self, msg):
        channel = self.client.get_channel(592270990894170112)
        await channel.send(f"[{get_time().strftime('%Y-%b-%d %HH')}] " + msg)

    @commands.command(aliases=["hint"])
    @commands.has_role("🐬")
    async def hint_request(self, ctx):

        user = ctx.message.author
        cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(user.id)
        t1 = datetime.strptime(timestamp, "%Y-%b-%d %HH")
        t2 = datetime.strptime(get_time().strftime("%Y-%b-%d %HH"), "%Y-%b-%d %HH")
        delta = (t2 - t1).days * 24 + (t2 - t1).seconds // 3600

        if delta < 1:
            await ctx.channel.send(f"{user.mention}, you must wait for 1 hr before you can unlock one")

        elif delta >= 1:
            with open("data/hints.json") as f:
                hints = json.load(f)

            try:
                hint = ""
                hint_num = 0
                h = 0
                while h <= 5:

                    if user_hints[path][h] == "locked":
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
                    text=f"Quest# 1 | Path# {path[4::]} | Hint# {hint_num}"
                )
                await update_hint_quest1(user, path, cycle, h)
                await penalize_quest1(user, cycle, points=10)
                await ctx.message.add_reaction("✅")
                await user.send(embed=embed)

            except IndexError:
                await user.send(f"You have used up all your hints for this path. "
                                f"Your hint for this hour is not consumed yet.")

            except KeyError:
                await user.send(f"You have used up all your hints for this path. "
                                f"Your hint for this hour is not consumed yet.")

    @commands.Cog.listener()
    async def on_message(self, m):

        if m.author == self.client.user:
            return

        elif isinstance(m.channel, discord.DMChannel):
            return

        elif m.author.bot:
            return
        
        elif not check_quest(m.author):
            return
        
        msg = m.content.lower()
        user = m.author
        role_dolphin = discord.utils.get(m.guild.roles, name="🐬")

        if user not in role_dolphin.members:
            return
        
        elif str(m.channel.category.id) in diagon_alleys:
        
            if msg == "eeylops owl emporium" and str(m.channel) != "eeylops-owl-emporium":
                await Expecto(self.client).create_emporium(m.channel.category, m.guild, msg, m, user)
    
            elif msg in ["gringotts bank", "gringotts wizarding bank"] and str(m.channel) != "gringotts-bank":
                await self.create_gringotts(m.channel.category, m.guild, m, user)
    
            elif msg == "ollivanders" and str(m.channel) != "ollivanders":
                await Expecto(self.client).create_ollivanders(m.channel.category, m.guild, msg, m, user)
    
            elif "gringotts-bank" == str(m.channel) and m.content.startswith(";") is False:
                await self.transaction_gringotts(user, m.guild, m)
            
        elif spell_check(m.content) and user in role_dolphin.members:
            await Expecto(self.client).expecto_patronum(m.guild, user, m.channel, m)
    
    async def create_gringotts(self, category, guild, message, user):

        role_galleons = discord.utils.get(message.guild.roles, name="💰")
        channels = [channel.name for channel in category.text_channels]
        cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(user.id)
        list_thieves = thieves.find_one({}, {"_id": 0, "names": 1})["names"]

        list_thieves_name = []
        for thief in list_thieves:
            try:
                list_thieves_name.append(guild.get_member(int(thief)).display_name)
            except AttributeError:
                continue

        formatted_thieves = "\n".join(list_thieves_name)
        topic = f"List of Potential Thieves:\n{formatted_thieves}"

        if "gringotts-bank" not in channels and int(get_time().strftime("%H")) in [9, 10, 11, 12, 21, 22, 23, 0]:

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True),
                guild.get_member(user.id): discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    read_message_history=True
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
                if path not in ["path8", "path18", "path12", "path13", "path0"]:
                    await Expecto(self.client).update_path_quest1(user, cycle, path_new="path8")
                await asyncio.sleep(3)
                await message.delete()
            else:
                await asyncio.sleep(3)
                await message.delete()
                await penalize_quest1(user, cycle, points=30)

        elif "gringotts-bank" in channels and int(get_time().strftime("%H")) in [9, 10, 11, 12, 21, 22, 23, 0]:

            gringotts_id = books.find_one({"server": str(guild.id)}, {"gringotts-bank": 1})["gringotts-bank"]["id"]
            gringotts_channel = self.client.get_channel(int(gringotts_id))

            await gringotts_channel.set_permissions(
                user,
                read_messages=True,
                send_messages=True,
                read_message_history=True
            )
            await message.add_reaction("✨")
            await gringotts_channel.edit(topic=topic)

            if user not in role_galleons.members:
                if path not in ["path8", "path18", "path12", "path13", "path0"]:
                    await Expecto(self.client).update_path_quest1(user, cycle, path_new="path8")
                await asyncio.sleep(3)
                await message.delete()
            else:
                await asyncio.sleep(3)
                await message.delete()
                await penalize_quest1(user, cycle, points=30)
        else:
            await reaction_closed(message)

    async def transaction_gringotts(self, user, guild, message):

        role_galleons = discord.utils.get(message.guild.roles, name="💰")
        cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(user.id)

        if user in role_galleons.members:

            if actions >= 3:
                return

            else:
                responses = get_responses_quest1("gringotts_bank")
                msg = responses["has_moneybag"].format(user.mention)
                await secret_response(guild.id, message.channel.name, msg)
                await action_update_quest1(user, cycle, actions=3)
                await penalize_quest1(user, cycle, points=20)

        elif user not in role_galleons.members:

            if actions >= 3:
                return

            elif actions < 3 and message.content.lower() in ["vault", "money", "galleon", "galleons"]:
                responses = get_responses_quest1("gringotts_bank")
                await action_update_quest1(user, cycle, actions=10)
                await self.vault_access(user, guild, role_galleons, message, responses)

            elif actions < 3:
                responses = get_responses_quest1("gringotts_bank")
                msg = responses["transaction"][actions].format(user.mention)
                await secret_response(guild.id, message.channel.name, msg)
                await action_update_quest1(user, cycle, actions=1)
                await penalize_quest1(user, cycle, points=10)

    async def vault_access(self, user, guild, role_galleons, message, responses):

        identity = await self.obtain_identity(user, guild, message, responses)

        if identity == "Correct":
            vault_number = await self.obtain_vault_number(user, guild, message, responses)

            if vault_number == "Correct":
                vault_password = await self.obtain_vault_password(user, guild, message, responses)

                if vault_password == "Correct":
                    msg1 = f"{user.mention} has acquired 💰 role"
                    msg2 = responses["success"].format(user.mention)
                    vault = f"{str(user.id).replace('1', '@').replace('5', '%').replace('7', '&').replace('3', '#')}"

                    secret = books.find_one({"server": str(guild.id)}, {"_id": 0, str(message.channel.name): 1})
                    webhook_url = secret[str(message.channel.name)]["webhook"]
                    avatar = secret[str(message.channel.name)]["avatar"]
                    username = secret[str(message.channel.name)]["username"]

                    cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(user.id)

                    embed = DiscordEmbed(
                        color=0xffffff,
                        title=f"🔐 Opening Vault# {vault}"
                    )
                    embed.set_image(url="https://i.imgur.com/RIS1TLh.gif")

                    webhook = DiscordWebhook(url=webhook_url, avatar_url=avatar, username=username)
                    webhook.add_embed(embed)
                    webhook.execute()

                    if path != "path0":
                        await Expecto(self.client).update_path_quest1(user, cycle, path_new="path15")

                    await user.add_roles(role_galleons)
                    await asyncio.sleep(6)
                    await message.channel.send(msg1)
                    await secret_response(guild.id, message.channel.name, msg2)

                    thieves.update_one({}, {"$pull": {"names": str(user.id)}})

    async def obtain_identity(self, user, guild, message, responses):

        answer, topic = "Wrong", ""
        msg = responses["get_identity"]["1"].format(user.mention)
        await secret_response(guild.id, message.channel.name, msg)
        cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(user.id)

        if path != "path0":
            await Expecto(self.client).update_path_quest1(user, cycle, path_new="path21")

        def check(g):
            key = (str(user.avatar_url).rsplit('/', 2)[1:])[1][:32:]
            if g.channel != message.channel:
                return
            elif str(g.content) == key and g.author == user and g.channel == message.channel:
                return True
            elif g.author == user and ";" not in str(g.content):
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

                await Expecto(self.client).update_path_quest1(user, cycle, path_new="path18")
                await action_update_quest1(user, cycle, actions=3)
                await penalize_quest1(user, cycle, points=10)
                await secret_response(guild.id, message.channel.name, msg)
                await message.channel.edit(topic=topic)
                break

            except KeyError:

                if i == 0:
                    msg = responses["get_identity"]["invalid1"][0].format(user.mention)
                    topic = responses["get_identity"]["invalid1"][1]
                    await penalize_quest1(user, cycle, points=10)

                elif i == 1:
                    msg = responses["get_identity"]["invalid2"][0].format(user.mention)
                    topic = responses["get_identity"]["invalid2"][1]
                    await penalize_quest1(user, cycle, points=10)

                elif i == 2:
                    msg = responses["get_identity"]["invalid3"][0].format(user.mention)
                    topic = responses["get_identity"]["invalid3"][1]

                    if thieves.find_one({"names": str(user.id)}, {"_id": 0}) is None:
                        thieves.update_one({}, {"$push": {"names": str(user.id)}})

                    await Expecto(self.client).update_path_quest1(user, cycle, path_new="path18")
                    await action_update_quest1(user, cycle, actions=3)
                    await penalize_quest1(user, cycle, points=10)

                await message.channel.edit(topic=topic)
                await secret_response(guild.id, message.channel.name, msg)
                i += 1

            else:
                answer = "Correct"
                await guess.add_reaction("✅")
                await asyncio.sleep(3)
                await guess.delete()
                break

        return answer

    async def obtain_vault_number(self, user, guild, message, responses):

        answer, topic = "Wrong", ""
        msg = responses["get_vault"]["1"].format(user.mention)
        await secret_response(guild.id, message.channel.name, msg)
        cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(user.id)

        if path != "path0":
            await Expecto(self.client).update_path_quest1(user, cycle, path_new="path22")

        if path == "path18":
            await Expecto(self.client).update_path_quest1(user, cycle, path_new="path5")

        def check(g):
            if g.channel != message.channel:
                return
            elif str(g.content) == str(user.id) and g.author == user and g.channel == message.channel:
                return True
            elif g.author == user and ";" not in str(g.content):
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

                await Expecto(self.client).update_path_quest1(user, cycle, path_new="path12")
                await action_update_quest1(user, cycle, actions=3)
                await penalize_quest1(user, cycle, points=10)
                await secret_response(guild.id, message.channel.name, msg)
                await message.channel.edit(topic=topic)
                break

            except KeyError:

                if i == 0:
                    msg = responses["get_vault"]["invalid1"][0].format(user.mention)
                    topic = responses["get_vault"]["invalid1"][1]
                    await penalize_quest1(user, cycle, points=10)

                elif i == 1:
                    msg = responses["get_vault"]["invalid2"][0].format(user.mention)
                    topic = responses["get_vault"]["invalid2"][1]
                    await penalize_quest1(user, cycle, points=10)

                elif i == 2:
                    answer = "Wrong"
                    msg = responses["get_vault"]["invalid3"][0].format(user.mention)
                    topic = responses["get_vault"]["invalid3"][1]

                    if thieves.find_one({"names": str(user.id)}, {"_id": 0}) is None:
                        thieves.update_one({}, {"$push": {"names": str(user.id)}})

                    await Expecto(self.client).update_path_quest1(user, cycle, path_new="path12")
                    await action_update_quest1(user, cycle, actions=3)
                    await penalize_quest1(user, cycle, points=10)

                await message.channel.edit(topic=topic)
                await secret_response(guild.id, message.channel.name, msg)
                i += 1

            else:
                answer = "Correct"
                await guess.add_reaction("✅")
                await asyncio.sleep(3)
                await guess.delete()
                break

        return answer

    async def obtain_vault_password(self, user, guild, message, responses):

        answer, topic, msg = "Wrong", "", ""
        msg1 = responses["get_password"]["1"].format(user.mention)
        msg2 = responses["get_password"]["2"].format(user.mention)
        await asyncio.sleep(1)
        await secret_response(guild.id, message.channel.name, msg1)
        await asyncio.sleep(3)
        await secret_response(guild.id, message.channel.name, msg2)
        cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(user.id)

        if path != "path0":
            await Expecto(self.client).update_path_quest1(user, cycle, path_new="path23")

        def check(g):
            if g.channel != message.channel:
                return
            elif str(g.content) == (str(user.id))[::-1] and g.author == user \
                    and g.channel == message.channel:
                return True
            elif g.author == user and ";" not in str(g.content):
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

                await Expecto(self.client).update_path_quest1(user, cycle, path_new="path13")
                await action_update_quest1(user, cycle, actions=3)
                await penalize_quest1(user, cycle, points=10)
                await secret_response(guild.id, message.channel.name, msg)
                await message.channel.edit(topic=topic)
                break

            except KeyError:

                if i == 0:
                    msg = responses["get_password"]["invalid1"][0].format(user.mention)
                    topic = responses["get_password"]["invalid1"][1]
                    await penalize_quest1(user, cycle, points=10)

                elif i == 1:
                    msg = responses["get_password"]["invalid2"][0].format(user.mention)
                    topic = responses["get_password"]["invalid2"][1]
                    await penalize_quest1(user, cycle, points=10)

                elif i == 2:
                    answer = "Wrong"
                    msg = responses["get_password"]["invalid3"][0].format(user.mention)
                    topic = responses["get_password"]["invalid3"][1]

                    if thieves.find_one({"names": str(user.id)}, {"_id": 0}) is None:
                        thieves.update_one({}, {"$push": {"names": str(user.id)}})

                    await Expecto(self.client).update_path_quest1(user, cycle, path_new="path13")
                    await action_update_quest1(user, cycle, actions=3)
                    await penalize_quest1(user, cycle, points=10)

                await message.channel.edit(topic=topic)
                await secret_response(guild.id, message.channel.name, msg)
                i += 1

            else:
                answer = "Correct"
                await guess.add_reaction("✅")
                await asyncio.sleep(3)
                await guess.delete()
                break

        return answer


class Expecto(commands.Cog):

    def __init__(self, client):
        self.client = client

    async def send_off_complete_quest1(self):
        for entry in sendoff.find({"timestamp_complete": get_time().strftime("%Y-%b-%d %HH")}, {"_id": 0}):
            try:
                user = self.client.get_user(int(entry["user_id"]))
                cycle, path, timestamp, user_hint, actions, purchase = get_data_quest1(user.id)
            except AttributeError:
                continue

            if entry["scenario"] == 2:
                async with user.typing():
                    responses = get_responses_quest1("send_off")["complete"]

                    if path != "path0":
                        await self.update_path_quest1(user, cycle, path_new="path3")

                    try:
                        await user.send(responses[0])
                        await asyncio.sleep(4)
                        await user.send(responses[1])
                        await asyncio.sleep(4)
                        msg = await user.send(responses[2].format(entry['type'].capitalize()))
                        await msg.add_reaction("✉")

                        sendoff.update_one({
                            "user_id": str(user.id), "cycle": cycle}, {
                            "$set": {"status": "done"}
                        })

                    except discord.errors.Forbidden:
                        continue
                    except discord.errors.HTTPException:
                        continue

            elif entry["scenario"] == 1:
                await self.update_path_quest1(user, cycle, path_new="path20")

                try:
                    await user.send(f"Your {entry['type']} has fully recovered")
                    sendoff.update_one({
                        "user_id": str(user.id), "cycle": cycle}, {
                        "$unset": {
                            "delay": "",
                            "report": "",
                            "scenario": "",
                            "timestamp": "",
                            "timestamp_complete": "",
                            "timestamp_update": "",
                            "weather1": "",
                            "weather2": ""
                        }
                    })

                except discord.errors.Forbidden:
                    continue
                except discord.errors.HTTPException:
                    continue

    async def send_off_report_quest1(self):
        query = sendoff.find({
            "quest": 1,
            "timestamp_update": get_time().strftime("%Y-%b-%d %HH")}, {
            "_id": 0
        })

        for entry in query:
            user = self.client.get_user(int(entry["user_id"]))

            if entry["scenario"] == 1:
                try:
                    cycle, path, timestamp, user_hint, actions, purchase = get_data_quest1(user.id)
                    await penalize_quest1(user, cycle, points=20)
                except AttributeError:
                    continue

            description = entry["report"]
            embed = discord.Embed(
                color=0xffffff,
                title="Owl Report",
                description=description
            )
            embed.set_footer(text=f"{entry['timestamp_update']}")

            try:
                await user.send(embed=embed)
                await asyncio.sleep(1)
            except discord.errors.Forbidden:
                continue
            except discord.errors.HTTPException:
                continue

    async def expecto_patronum(self, guild, user, channel, message):

        role_star = discord.utils.get(guild.roles, name="🌟")
        cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(user.id)

        if path in ["path3", "path0", "path25"] and user not in role_star.members:
            await message.add_reaction("❎")
            await self.update_path_quest1(user, cycle, path_new="path10")
            await penalize_quest1(user, cycle, points=5)

        elif path == "path10":
            await message.add_reaction("❔")
            await penalize_quest1(user, cycle, points=15)

        elif user in role_star.members:
            async with channel.typing():
                role_dolphin = discord.utils.get(guild.roles, name="🐬")
                role_galleon = discord.utils.get(guild.roles, name="💰")
                role_owl = discord.utils.get(guild.roles, name="🦉")
                cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(user.id)
                uppers = len([char for char in message.content if char.isupper()])
                lowers = len([char for char in message.content if char.islower()])
                symbol = len([char for char in message.content if char == "!"])
                strength = round((uppers * 1.35) + lowers + (symbol * 1.5), 2)
                strength = round(random.uniform(strength - 5, strength + 5), 2)

                if strength > 100:
                    strength = round(random.uniform(98, 99.99), 2)

                added_points = round(50 * (strength / 100))

                score, timestamp_start, patronus_summon, hints_unlocked, owl_final, wand, paths \
                    = get_profile_finished_quest1(user)

                t1 = datetime.strptime(timestamp_start, "%Y-%b-%d %HH")
                t2 = datetime.strptime(get_time().strftime("%Y-%b-%d %HH"), "%Y-%b-%d %HH")
                delta = (t2 - t1).days * 24 + (t2 - t1).seconds // 3600

                paths_unlocked = ""
                for y in list(paths.keys()):
                    paths_unlocked += "{}, ".format(y.replace("path", ""))

                description = \
                    f"• Cycle Score: {score + added_points} points, (+{added_points} bonus points)\n" \
                        f"• Hints unlocked: {hints_unlocked}\n" \
                        f"• No. of Paths unlocked: {len(paths)}\n" \
                        f"• Paths unlocked: [{paths_unlocked[:-2]}]\n" \
                        f"• Owl: {owl_final.title()} [{patronus_summon['trait'].title()}]"

                quests.update_one({
                    "user_id": str(user.id), "quest1.cycle": cycle}, {
                    "$inc": {
                        "quest1.$.score": added_points
                    },
                    "$set": {
                        "quest1.$.strength": strength,
                        "quest1.$.timestamp": get_time().strftime("%Y-%b-%d %HH"),
                        "quest1.$.status": "completed"
                    }
                })

                embed = discord.Embed(
                    color=0x50e3c2,
                    title=f"Patronus: {patronus_summon['patronus'].title()} | Strength: {strength}%",
                    description=description
                )
                embed.set_image(url=patronus_summon["link"])
                embed.set_footer(text=f"Hours spent: {delta} hours")
                embed.set_author(
                    name=f"{user.display_name} | Cycle #{cycle} results!",
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

    async def sendoff_owl_quest1(self, user, cycle):
        responses = get_responses_quest1("send_off")
        await user.send(responses["success1"])
        await asyncio.sleep(2)
        await user.send(responses["success2"])
        await self.generate_owl_report_quest1(user, cycle, responses)

    async def generate_owl_report_quest1(self, user, cycle, responses):

        profile = sendoff.find_one({"user_id": str(user.id), "cycle": cycle}, {"_id": 0})
        weather1 = weather.find_one({"weather1": {"$type": "string"}}, {"weather1": 1})["weather1"]
        weather2 = weather.find_one({"weather2": {"$type": "string"}}, {"weather2": 1})["weather2"]

        def get_specific_report(key):
            return responses["reports"][key]["delay"], \
                   responses["reports"][key]["scenario"], \
                   responses["reports"][key]["content"]

        if weather1 == "⛈":
            delay, scenario, content = get_specific_report("thunderstorms")
            await self.update_path_quest1(user, cycle, path_new="path19")

        elif weather1 == "🌨" and profile["type"] == "snowy":
            delay, scenario, content = get_specific_report("snowy_snowy_owl")

        elif weather2 == "🌕" or weather2 == "🌑":
            delay, scenario, content = get_specific_report("night_time")

        elif weather1 == "🌧" or weather1 == "🌨":
            delay, scenario, content = get_specific_report("rainy_snowy")

        else:
            delay, scenario, content = get_specific_report("cloudy_sunny")

        timestamp_update = (get_time() + timedelta(days=1 / 24)).strftime("%Y-%b-%d %HH")
        timestamp_complete = (get_time() + timedelta(days=delay / 24)).strftime("%Y-%b-%d %HH")

        sendoff.update_one({
            "user_id": str(user.id),
            "cycle": cycle}, {
            "$set": {
                "report": content,
                "weather1": weather1,
                "weather2": weather2,
                "timestamp": get_time().strftime("%Y-%b-%d %HH"),
                "timestamp_update": timestamp_update,
                "timestamp_complete": timestamp_complete,
                "delay": delay,
                "scenario": scenario,
                "quest": 1
            }
        })

    async def update_path_quest1(self, user, cycle, path_new):

        quests.update_one({
            "user_id": str(user.id), "quest1.cycle": cycle}, {
            "$set": {
                "quest1.$.current_path": path_new
            }
        })

        path_profile = quests.find_one({
            "user_id": str(user.id), "quest1.cycle": cycle}, {
            "_id": 0, "quest1.$.hints": 1
        })

        if path_new not in path_profile["quest1"][0]["hints"]:
            quests.update_one({
                "user_id": str(user.id), "quest1.cycle": cycle}, {
                "$set": {
                    f"quest1.$.hints.{path_new}": ["locked", "locked", "locked", "locked", "locked"]
                }
            }
            )
        await Quest(self.client).logging(f"Shifted {user} path to {path_new}")

    @commands.command(aliases=["patronus"])
    @commands.has_role("Test")
    @commands.guild_only()
    async def show_patronus(self, ctx, *, _patronus):

        profiles = patronus.find({"patronus": _patronus.lower()})
        patronus_descriptions = []

        name, link = "", ""
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

        def check(r, u):
            return u != self.client.user and r.message.id == msg.id

        def create_embed(p):

            try:
                embed = discord.Embed(
                    color=0x50e3c2,
                    title=f"{name.title()} | Combination # {p + 1}",
                    description=patronus_descriptions[p]
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

    @commands.command(aliases=["cycle"])
    @commands.guild_only()
    async def show_cycle_quest1(self, ctx, cycle_query, *, user: discord.Member = None):

        requestor = ctx.message.author
        requestor_profile = quests.find_one({"user_id": str(requestor)}, {"_id": 0}) is None

        if requestor_profile is None:
            await ctx.channel.send("You have to finish your own first cycle first.")

        elif requestor_profile is not None:
            query = quests.aggregate([{"$match": {"user_id": str(requestor.id)}}, {
                "$project": {
                    "_id": 0,
                    "status": {
                        "$slice": ["$quest1.status", 1]
                    }
                }
            }])

            profile = {}
            for result in query:
                profile = result
                break

            if profile["status"][0] == "ongoing":
                await ctx.channel.send("You have to finish your own first cycle first.")

            elif profile["status"][0] == "completed":

                try:
                    cycle_query = int(cycle_query)

                    if user is None:
                        user = ctx.message.author

                    profile = get_profile_history_quest1(user, cycle_query)
                    patronus_summon = profile["quest1"]["patronus"]["patronus"]
                    score = profile["quest1"]["score"]
                    timestamp_start = profile["quest1"]["timestamp_start"]
                    timestamp_end = profile["quest1"]["timestamp"]
                    hints_unlocked = profile["quest1"]["hints_unlocked"]
                    owl_final = profile["quest1"]["owl"]
                    wand = profile["quest1"]["wand"]
                    paths = profile["quest1"]["hints"]
                    strength = profile["quest1"]["strength"]
                    patronus_profile = profile["quest1"]["patronus"]

                    t1 = datetime.strptime(timestamp_start, "%Y-%b-%d %HH")
                    t2 = datetime.strptime(timestamp_end, "%Y-%b-%d %HH")
                    delta = (t2 - t1).days * 24 + (t2 - t1).seconds // 3600

                    paths_unlocked = ""
                    for y in list(paths.keys()):
                        paths_unlocked += "{}, ".format(y.replace("path", ""))

                    description = \
                        f"• Cycle Score: {score} points\n" \
                            f"• Hints unlocked: {hints_unlocked}\n" \
                            f"• No. of paths unlocked: {len(paths)}\n" \
                            f"• Paths unlocked: [{paths_unlocked[:-2]}]\n" \
                            f"• Owl: {owl_final.title()} [{patronus_profile['trait'].title()}]"

                    embed = discord.Embed(
                        color=0x50e3c2,
                        title=f"Your Patronus: {patronus_summon.title()} | Strength: {strength}%",
                        description=description
                    )
                    embed.set_image(url=patronus_profile["link"])
                    embed.set_footer(text=f"Hours spent: {delta} hours")
                    embed.set_author(
                        name=f"{user.display_name} | Cycle #{cycle_query} results",
                        icon_url=user.avatar_url
                    )
                    embed.add_field(
                        name="Wand Properties",
                        value=f"{wand['length']} inches, {wand['flexibility']}, {wand['core'].replace(' ', '-')}-cored,"
                        f" {wand['wood']} wand"
                    )
                    await ctx.channel.send(embed=embed)

                except ValueError:
                    await ctx.channel.send("Use `;cycle <cycle#> <@mention>.")
                except TypeError:
                    await ctx.channel.send("Use `;cycle <cycle#> <@mention>.")

    @commands.command(aliases=["progress"])
    @commands.has_role("🐬")
    async def show_progress_quest1(self, ctx):

        user = ctx.message.author
        requestor_profile = quests.find_one({"user_id": str(user.id)}, {"_id": 0})

        if requestor_profile is None:
            await ctx.channel.send("You have to signup first to the quest.")

        elif requestor_profile is not None:

            score, timestamp_start, current_path, cycle, hints_unlocked, paths \
                = get_profile_progress_quest1(ctx.message.author)
            t1 = datetime.strptime(timestamp_start, "%Y-%b-%d %HH")
            t2 = datetime.strptime(get_time().strftime("%Y-%b-%d %HH"), "%Y-%b-%d %HH")
            hours_passed = (t2 - t1).days * 24 + (t2 - t1).seconds // 3600

            paths_unlocked = ""
            for y in list(paths.keys()):
                paths_unlocked += "{}, ".format(y.replace("path", ""))

            description = \
                f"• Current Score: {score}\n" \
                    f"• Hours passed: {hours_passed}\n" \
                    f"• Penalties: {1000 - score}\n" \
                    f"• Current path: {current_path.replace('path', 'Path ').capitalize()}\n" \
                    f"• No. of paths unlocked: {len(paths)}\n" \
                    f"• Paths unlocked: {paths_unlocked[:-2]}\n" \
                    f"• Hints unlocked: {hints_unlocked}"

            embed = discord.Embed(
                color=ctx.message.author.colour,
                description=description
            )
            embed.set_author(
                name=f"{ctx.message.author}'s Cycle #{cycle}",
                icon_url=ctx.message.author.avatar_url
            )
            await ctx.message.author.send(embed=embed)
            await ctx.message.add_reaction("✅")

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
            "_id": 0, "messages.quests": 1
        })

        if str(payload.emoji) == "🐬" and payload.message_id == int(request["messages"]["quests"]):
            member = server.get_member(user.id)

            if quests.find_one({"user_id": str(user.id)}, {"_id": 0}) is None:
                profile = {"user_id": str(payload.user_id), "server": str(payload.guild_id), "quest1": []}
                quests.insert_one(profile)

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
                                timestamp=get_time().strftime("%Y-%b-%d %HH"),
                                timestamp_start=get_time().strftime("%Y-%b-%d %HH"),
                                current_path="path0",
                                paths_unlocked=0,
                                actions=0,
                                purchase=True,
                                hints_unlocked=0,
                                hints={"path0": ["locked", "locked", "locked", "locked", "locked"]}
                            )
                        }
                    })
                    await Quest(self.client).logging(f"Started quest1: cycle#{cycle} for {user}")
                    break

            await member.add_roles(role_dolphin)
            responses = get_responses_quest1("start_quest")

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

        msg = reaction.message.content

        if user == self.client.user:
            return

        elif user.bot:
            return

        elif str(reaction.emoji) == "✉" and user != self.client.user \
                and "envelope" in msg and reaction.message.author == self.client.user:

            cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(user.id)
            server = quests.find_one({"user_id": str(user.id)}, {"_id": 0, "server": 1})
            request = books.find_one({
                "server": server["server"]}, {
                "_id": 0, "channels.welcome": 1, "channels.sorting-hat": 1
            })

            description = get_responses_quest1("start_quest")["letter"].format(
                user.name, request["channels"]["welcome"], request["channels"]["sorting-hat"]
            )
            embed = discord.Embed(
                color=0xffff80,
                title="Acceptance Letter",
                description=description
            )
            embed.set_thumbnail(url=self.client.get_guild(int(server["server"])).icon_url)
            await user.send(embed=embed)
            await self.update_path_quest1(user, cycle, path_new="path1")
            await penalize_quest1(user, cycle, points=20)

        elif str(reaction.emoji) == "✉" and "returned with" in msg and reaction.message.author == self.client.user:

            server = quests.find_one({"user_id": str(user.id)}, {"_id": 0, "server": 1})
            cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(user.id)
            description = get_responses_quest1("send_off")["letter"].format(user.name)
            embed = discord.Embed(color=0xffff80, description=description)
            embed.set_thumbnail(url=self.client.get_guild(int(server["server"])).icon_url)

            if path != "path0":
                await Expecto(self.client).update_path_quest1(user, cycle, path_new="path25")
                await penalize_quest1(user, cycle, points=25)

            await user.send(embed=embed)

        elif str(reaction.emoji) == "🦉":

            role_owl = discord.utils.get(reaction.message.guild.roles, name="🦉")
            request = books.find_one({
                "server": f"{reaction.message.guild.id}"}, {
                "_id": 0, "channels.absence-applications": 1
            })
            valid_channel_id = request["channels"]["absence-applications"]
            cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(user.id)

            if user not in role_owl.members:
                await penalize_quest1(user, cycle, points=30)

            elif (valid_channel_id not in msg or "180717337475809281" not in msg) and "✉" not in msg:

                await reaction.message.add_reaction("❔")
                await penalize_quest1(user, cycle, points=10)

            elif (valid_channel_id in msg or "180717337475809281" in msg) and "✉" in msg:

                cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(user.id)

                if path in ["path0", "path2", "path20"]:
                    if path != "path0":
                        await self.update_path_quest1(user, cycle, path_new="path4")

                    await self.sendoff_owl_quest1(user, cycle)
                    await reaction.message.add_reaction("✅")
                    await asyncio.sleep(2)
                    await reaction.message.delete()

                elif path == "path19":
                    msg = get_responses_quest1("send_off")["penalize"]
                    await penalize_quest1(user, cycle, points=20)
                    await user.send(msg)
                    await asyncio.sleep(2)
                    await reaction.message.delete()

    @commands.command(aliases=["knock", "inquire"])
    @commands.has_role("🐬")
    async def transact_emporium(self, ctx):

        if str(ctx.channel.name) != "eeylops-owl-emporium":
            return

        elif str(ctx.channel.name) == "eeylops-owl-emporium":
            user = ctx.author
            cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(user.id)

            if actions > 3:
                if ctx.message.content in [";knock", ";inquire"]:
                    await ctx.message.delete()

            elif ctx.message.content == ";knock":
                if path == "path6":
                    await self.update_path_quest1(user, cycle, path_new="path9")
                elif path == "path15":
                    await self.update_path_quest1(user, cycle, path_new="path16")

                responses = get_responses_quest1("eeylops_owl")
                msg = responses["knock"][0]
                topic = responses["knock"][1]
                await ctx.channel.edit(topic=topic)
                await ctx.message.delete()
                await secret_response(ctx.guild.id, ctx.channel.name, msg)
                await penalize_quest1(user, cycle, points=15)

            elif ctx.message.content == ";inquire":
                if path == "path9":
                    await self.update_path_quest1(user, cycle, path_new="path14")
                elif path == "path15":
                    await self.update_path_quest1(user, cycle, path_new="path16")

                responses = get_responses_quest1("eeylops_owl")["inquire"]
                msg, topic = responses[actions]
                await ctx.channel.edit(topic=topic)
                await ctx.message.delete()
                await action_update_quest1(user, cycle, actions=1)
                await penalize_quest1(user, cycle, points=15)
                await secret_response(ctx.guild.id, ctx.channel.name, msg)

    @commands.command(aliases=["purchase"])
    @commands.has_role("🐬")
    async def buy_items(self, ctx, *args):

        if ctx.channel.name != "eeylops-owl-emporium":
            return

        elif ctx.channel.name == "eeylops-owl-emporium":

            if args is None:
                return

            try:
                owl_buy = args[0].lower()
            except IndexError:
                return

            user = ctx.author
            cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(user.id)
            responses = get_responses_quest1("eeylops_owl")

            if purchase is False:
                msg = responses["purchasing"]["max_actions"]
                await penalize_quest1(user, cycle, points=20)
                await user.send(msg)
                await ctx.message.delete()

            elif owl_buy not in owls_list:
                msg = responses["purchasing"]["invalid_owl"]
                await penalize_quest1(user, cycle, points=20)
                await secret_response(ctx.guild.id, ctx.channel.name, msg)
                await ctx.message.delete()

            elif owl_buy in owls_list:
                purchaser_id = owls.find_one({"type": f"{owl_buy}"}, {"_id": 0, "purchaser": 1})["purchaser"]
                role_owl = discord.utils.get(ctx.guild.roles, name="🦉")
                role_galleons = discord.utils.get(ctx.guild.roles, name="💰")

                if user in role_owl.members:
                    msg = responses["purchasing"]["buying_again"][0].format(user.mention)
                    topic = responses["purchasing"]["buying_again"][1]
                    await penalize_quest1(user, cycle, points=75)
                    await secret_response(ctx.guild.id, ctx.channel.name, msg)
                    await ctx.channel.edit(topic=topic)
                    await ctx.message.delete()

                elif user not in role_galleons.members:
                    msg = responses["purchasing"]["no_moneybag"][0].format(user.mention)
                    topic = responses["purchasing"]["no_moneybag"][1]
                    await self.update_path_quest1(user, cycle, path_new="path7")
                    await penalize_quest1(user, cycle, points=10)
                    await secret_response(ctx.guild.id, ctx.channel.name, msg)
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
                    msg = responses["purchasing"]["out_of_stock"][0].format(user.mention, purchaser.display_name)
                    topic = responses["purchasing"]["out_of_stock"][1]
                    await self.update_path_quest1(user, cycle, path_new="path24")
                    await penalize_quest1(user, cycle, points=20)
                    await secret_response(ctx.guild.id, ctx.channel.name, msg)
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
                        msg = responses["purchasing"]["success_purchase"][0].format(user.mention)
                        topic = responses["purchasing"]["success_purchase"][1]

                        embed = discord.Embed(
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
                            await self.update_path_quest1(user, cycle, path_new="path2")

                        await ctx.message.add_reaction("🦉")
                        await user.add_roles(role_owl)
                        await asyncio.sleep(1)
                        await ctx.channel.send(f"{user.mention} has acquired 🦉 role")
                        await asyncio.sleep(2)
                        await secret_response(ctx.guild.id, ctx.channel.name, msg)
                        await asyncio.sleep(3)
                        await ctx.channel.send(embed=embed)
                        await asyncio.sleep(2)
                        await ctx.message.delete()

    async def create_emporium(self, category, guild, msg, message, user):

        role_owl = discord.utils.get(guild.roles, name="🦉")
        role_galleons = discord.utils.get(guild.roles, name="💰")
        channels = [channel.name for channel in category.text_channels]
        cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(user.id)

        if "eeylops-owl-emporium" not in channels \
                and int(get_time().strftime("%H")) in [8, 9, 10, 11, 12, 13, 20, 21, 22, 23, 0, 1]:

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True),
                guild.get_member(user.id): discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    read_message_history=True
                )
            }

            emporium = await guild.create_text_channel("eeylops-owl-emporium", category=category, overwrites=overwrites)
            await generate_data(guild, msg, emporium)
            await message.add_reaction("✨")

            if user not in role_owl.members and user not in role_galleons.members:
                if path not in ["path9"]:
                    await self.update_path_quest1(user, cycle, path_new="path6")

            await asyncio.sleep(3)
            await message.delete()

        elif "eeylops-owl-emporium" in channels \
                and int(get_time().strftime("%H")) in [8, 9, 10, 11, 12, 13, 20, 21, 22, 23, 0, 1]:

            emporium_id = books.find_one({
                "server": str(guild.id)}, {
                "eeylops-owl-emporium": 1
            })

            emporium_channel = self.client.get_channel(int(emporium_id["eeylops-owl-emporium"]["id"]))

            await emporium_channel.set_permissions(
                user, read_messages=True,
                send_messages=True,
                read_message_history=True
            )
            await message.add_reaction("✨")

            if user not in role_owl.members and user not in role_galleons.members:
                await self.update_path_quest1(user, cycle, path_new="path6")

            await asyncio.sleep(3)
            await message.delete()

        else:
            await reaction_closed(message)

    async def create_ollivanders(self, category, guild, msg, message, user):

        channels = [channel.name for channel in category.text_channels]
        cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(user.id)

        if "ollivanders" not in channels and int(get_time().strftime("%H")) in [13, 14, 15, 16, 17, 1, 2, 3, 4, 5]:

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True),
                guild.get_member(user.id): discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    read_message_history=True
                )
            }

            ollivanders = await guild.create_text_channel("ollivanders", category=category, overwrites=overwrites)
            await generate_data(guild, msg, ollivanders)
            await message.add_reaction("✨")
            await asyncio.sleep(3)
            await message.delete()

            if path in ["path10", "path3", "path25"]:
                await self.update_path_quest1(user, cycle, path_new="path11")

            await self.transaction_ollivanders(guild, user, ollivanders)

        elif "ollivanders" in channels and int(get_time().strftime("%H")) in [13, 14, 15, 16, 17, 1, 2, 3, 4, 5]:

            ollivanders_id = books.find_one({"server": str(guild.id)}, {"ollivanders": 1})["ollivanders"]["id"]
            ollivanders_channel = self.client.get_channel(int(ollivanders_id))

            await ollivanders_channel.set_permissions(
                user,
                read_messages=True,
                send_messages=True,
                read_message_history=True
            )
            await message.add_reaction("✨")
            await asyncio.sleep(1)
            await asyncio.sleep(3)
            await message.delete()

            if path in ["path10", "path3", "path25"]:
                await self.update_path_quest1(user, cycle, path_new="path11")

            await self.transaction_ollivanders(guild, user, ollivanders_channel)

        else:
            await reaction_closed(message)

    async def transaction_ollivanders(self, guild, user, channel):

        cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(user.id)

        if actions >= 3:
            return

        elif actions < 3:
            role_star = discord.utils.get(guild.roles, name="🌟")
            responses = get_responses_quest1("ollivanders")
            msg1 = responses["intro"].format(user.mention)
            await secret_response(guild.id, channel.name, msg1)
            await asyncio.sleep(3)

            def check(guess):
                if guess.author != user:
                    return
                elif guess.content.lower() in ["yes", "yeah", "yea", "maybe", "probably", "perhaps"]:
                    return guess.author == user and channel == guess.channel
                else:
                    raise KeyError

            try:
                await self.client.wait_for("message", timeout=30, check=check)

            except asyncio.TimeoutError:
                msg = responses["timeout_intro"].format(user.mention)
                await penalize_quest1(user, cycle, points=10)
                await action_update_quest1(user, cycle, actions=3)
                await secret_response(guild.id, channel.name, msg)

            except KeyError:
                msg = responses["invalid"]
                await penalize_quest1(user, cycle, points=10)
                await action_update_quest1(user, cycle, actions=3)
                await secret_response(guild.id, channel.name, msg)

            else:
                if user not in role_star.members and path in ["path11", "path3", "path10", "path0", "path25", "path17"]:
                    msg1 = responses["valid"][0].format(user.mention)
                    msg2 = responses["valid"][1].format(user.mention)
                    topic = responses["valid"][2]
                    await action_update_quest1(user, cycle, actions=3)
                    await secret_response(guild.id, channel.name, msg1)
                    await asyncio.sleep(6)
                    await secret_response(guild.id, channel.name, msg2)
                    await channel.edit(topic=topic)
                    await asyncio.sleep(5)
                    await self.wand_personalise(user, guild, channel, cycle, role_star, responses)

                else:
                    msg = responses["valid_no_owl"][0].format(user.mention)
                    topic = responses["valid_no_owl"][1]
                    await penalize_quest1(user, cycle, points=25)
                    await action_update_quest1(user, cycle, actions=3)
                    await secret_response(guild.id, channel.name, msg)
                    await channel.edit(topic=topic)

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

        owl_type = ""
        for profile in data:
            owl_type = profile["quest1"][0]["owl"]
            break

        trait = owls.find_one({"type": owl_type}, {"_id": 0, "trait": 1})["trait"]
        msg1 = responses["owl_analysis"][trait][0]
        topic = responses["owl_analysis"][trait][1]

        await secret_response(guild.id, channel.name, msg1)
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
                        msg = responses["no_patronus"].format(user.mention)
                        await secret_response(guild.id, channel.name, msg)

                    elif __patronus is not None:
                        description = f"Wood: `{wand_wood.title()}`\n" \
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

                        def check(_answer):
                            return user.id == _answer.author.id \
                                   and _answer.content.lower() in ["y", "n"] \
                                   and msg_confirm.channel.id == _answer.channel.id

                        while True:
                            try:
                                answer = await self.client.wait_for("message", timeout=120, check=check)

                            except asyncio.TimeoutError:
                                msg = responses["timeout_response"].format(user.mention)
                                await penalize_quest1(user, cycle, points=20)
                                await secret_response(guild.id, channel.name, msg)
                                break

                            else:
                                if answer.content.lower() == "y":
                                    msg1 = f"{user.mention} has acquired 🌟 role"
                                    msg2 = responses["success_purchase"].format(user.mention)
                                    quests.update_one({
                                        "user_id": str(user.id),
                                        "quest1.cycle": cycle}, {
                                        "$set": {
                                            "quest1.$.wand": wand_creation,
                                            "quest1.$.patronus": __patronus
                                        }
                                    })

                                    await user.add_roles(role_star)
                                    await channel.send(msg1)
                                    await secret_response(guild.id, channel.name, msg2)
                                    break

                                elif answer.content.lower() == "n":
                                    msg = responses["timeout_response"].format(user.mention)
                                    cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(user.id)

                                    if path == "path0":
                                        await self.update_path_quest1(user, cycle, path_new="path17")

                                    await penalize_quest1(user, cycle, points=20)
                                    await secret_response(guild.id, channel.name, msg)
                                    break

    async def get_wand_core(self, user, guild, channel, responses):

        wand_core = ""
        formatted_cores = "`, `".join(cores)
        msg = responses["core_selection"]["1"].format(user.mention, formatted_cores)
        await asyncio.sleep(1)
        await secret_response(guild.id, channel.name, msg)
        cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(user.id)

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
                msg = responses["core_selection"]["timeout"].format(user.mention)
                wand_core = "Wrong"

                if path == "path0":
                    await self.update_path_quest1(user, cycle, path_new="path17")

                await action_update_quest1(user, cycle, actions=3)
                await penalize_quest1(user, cycle, points=10)
                await secret_response(guild.id, channel.name, msg)
                break

            except KeyError:

                if path == "path0":
                    await self.update_path_quest1(user, cycle, path_new="path17")

                if i == 0:
                    msg = responses["core_selection"]["invalid1"][0].format(user.mention)
                    topic = responses["core_selection"]["invalid1"][1]
                    await channel.edit(topic=topic)
                    await penalize_quest1(user, cycle, points=5)

                elif i == 1:
                    wand_core = "Wrong"
                    msg = responses["core_selection"]["invalid2"][0].format(user.mention)
                    topic = responses["core_selection"]["invalid2"][1]
                    await action_update_quest1(user, cycle, actions=3)
                    await penalize_quest1(user, cycle, points=10)
                    await channel.edit(topic=topic)

                await secret_response(guild.id, channel.name, msg)
                i += 1

            else:
                wand_core = answer.content
                msg = responses["core_selection"]["chose"][0].format(
                    wand_core.capitalize(),
                    responses["core_description"][f'{wand_core.lower()}']
                )
                topic = responses["core_selection"]["chose"][1]
                await channel.edit(topic=topic)
                await secret_response(guild.id, channel.name, msg)
                break

        return wand_core.lower()

    async def get_wand_wood(self, user, guild, channel, wood_selection, responses):

        wand_wood = ""
        formatted_woods = "`, `".join(wood_selection)
        msg = responses["wood_selection"]["1"].format(user.mention, formatted_woods)
        await asyncio.sleep(1)
        await secret_response(guild.id, channel.name, msg)
        cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(user.id)

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
                msg = responses["wood_selection"]["timeout"].format(user.mention)

                if path == "path0":
                    await self.update_path_quest1(user, cycle, path_new="path17")

                await penalize_quest1(user, cycle, points=15)
                await action_update_quest1(user, cycle, actions=3)
                await secret_response(guild.id, channel.name, msg)
                break

            except KeyError:

                if path == "path0":
                    await self.update_path_quest1(user, cycle, path_new="path17")

                if i == 0:
                    msg = responses["wood_selection"]["invalid1"][0].format(user.mention)
                    topic = responses["wood_selection"]["invalid1"][1]
                    await channel.edit(topic=topic)
                    await penalize_quest1(user, cycle, points=10)

                elif i == 1:
                    wand_wood = "Wrong"
                    msg = responses["wood_selection"]["invalid2"][0].format(user.mention)
                    topic = responses["wood_selection"]["invalid2"][1]
                    await action_update_quest1(user, cycle, actions=3)
                    await penalize_quest1(user, cycle, points=10)
                    await channel.edit(topic=topic)

                await secret_response(guild.id, channel.name, msg)
                i += 1

            else:
                wand_wood = answer.content
                msg = responses["wood_selection"]["chose"][0].format(
                    wand_wood.capitalize(),
                    responses["wood_description"][f'{wand_wood.lower()}']
                )
                topic = responses["wood_selection"]["chose"][1]
                await channel.edit(topic=topic)
                await secret_response(guild.id, channel.name, msg)
                break

        return wand_wood.lower()

    async def get_wand_length(self, user, guild, channel, responses):

        wand_length = ""
        msg = responses["length_selection"]["1"].format(user.mention)
        await asyncio.sleep(1)
        await secret_response(guild.id, channel.name, msg)
        cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(user.id)

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
                msg = responses["length_selection"]["timeout"].format(user.mention)

                if path == "path0":
                    await self.update_path_quest1(user, cycle, path_new="path17")

                await penalize_quest1(user, cycle, points=15)
                await action_update_quest1(user, cycle, actions=3)
                await secret_response(guild.id, channel.name, msg)
                break

            except KeyError:

                if path == "path0":
                    await self.update_path_quest1(user, cycle, path_new="path17")

                if i == 0:
                    msg = responses["length_selection"]["invalid1"][0].format(user.mention)
                    topic = responses["length_selection"]["invalid1"][1]
                    await channel.edit(topic=topic)
                    await penalize_quest1(user, cycle, points=10)

                elif i == 1:
                    wand_length = "Wrong"
                    msg = responses["length_selection"]["invalid2"][0].format(user.mention)
                    topic = responses["length_selection"]["invalid2"][1]
                    await action_update_quest1(user, cycle, actions=3)
                    await penalize_quest1(user, cycle, points=15)
                    await channel.edit(topic=topic)

                await secret_response(guild.id, channel.name, msg)
                i += 1

            else:
                wand_length = answer.content
                msg = responses["length_selection"]["chose"][0].format(wand_length)
                topic = responses["length_selection"]["chose"][1]
                await channel.edit(topic=topic)
                await secret_response(guild.id, channel.name, msg)
                break

        return wand_length

    async def get_wand_flexibility(self, user, guild, channel, responses):

        wand_flexibility = ""
        formatted_flexibility = "`, `".join(flexibility_types)
        msg = responses["flexibility_selection"]["1"].format(user.mention, formatted_flexibility)
        await asyncio.sleep(2)
        await secret_response(guild.id, channel.name, msg)
        cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(user.id)

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
                msg = responses["flexibility_selection"]["timeout"].format(user.mention)

                if path == "path0":
                    await self.update_path_quest1(user, cycle, path_new="path17")

                await penalize_quest1(user, cycle, points=15)
                await action_update_quest1(user, cycle, actions=3)
                await secret_response(guild.id, channel.name, msg)
                break

            except KeyError:

                if path == "path0":
                    await self.update_path_quest1(user, cycle, path_new="path17")

                if i == 0:
                    msg = responses["flexibility_selection"]["invalid1"][0].format(user.mention)
                    topic = responses["flexibility_selection"]["invalid1"][1]
                    await channel.edit(topic=topic)
                    await penalize_quest1(user, cycle, points=10)

                elif i == 1:
                    wand_flexibility = "Wrong"
                    msg = responses["flexibility_selection"]["invalid2"][0].format(user.mention)
                    topic = responses["flexibility_selection"]["invalid2"][1]
                    await action_update_quest1(user, cycle, actions=3)
                    await penalize_quest1(user, cycle, points=15)
                    await channel.edit(topic=topic)

                await secret_response(guild.id, channel.name, msg)
                i += 1

            else:
                wand_flexibility = answer.content
                msg = responses["flexibility_selection"]["chose"][0].format(wand_flexibility.title())
                topic = responses["flexibility_selection"]["chose"][1]
                await channel.edit(topic=topic)
                await secret_response(guild.id, channel.name, msg)
                break

        return wand_flexibility.lower()
    
      
def setup(client):
    client.add_cog(Quest(client))
    client.add_cog(Expecto(client))
