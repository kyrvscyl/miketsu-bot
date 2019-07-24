"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import asyncio
import json
from datetime import datetime

import discord
import pytz
from discord.ext import commands
from discord_webhook import DiscordWebhook, DiscordEmbed

import cogs.expecto as expecto
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
        cycle, path, timestamp, user_hints, actions, purchase = expecto.get_data_quest1(user.id)
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
                await expecto.update_hint_quest1(user, path, cycle, h)
                await expecto.penalize_quest1(user, cycle, points=10)
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
        role_tea = discord.utils.get(m.guild.roles, name="🍵")

        if user not in role_dolphin.members or user not in role_tea.members:
            return
        
        elif str(m.channel.category.id) in diagon_alleys:
        
            if msg == "eeylops owl emporium" and str(m.channel) != "eeylops-owl-emporium":
                await expecto.Expecto(self.client).create_emporium(m.channel.category, m.guild, msg, m, user)
    
            elif msg in ["gringotts bank", "gringotts wizarding bank"] and str(m.channel) != "gringotts-bank":
                await self.create_gringotts(m.channel.category, m.guild, m, user)
    
            elif msg == "ollivanders" and str(m.channel) != "ollivanders":
                await expecto.Expecto(self.client).create_ollivanders(m.channel.category, m.guild, msg, m, user)
    
            elif "gringotts-bank" == str(m.channel) and m.content.startswith(";") is False:
                await self.transaction_gringotts(user, m.guild, m)
            
        elif expecto.spell_check(m.content) and user in role_dolphin.members:
            await expecto.Expecto(self.client).expecto_patronum(m.guild, user, m.channel, m)
    
    async def create_gringotts(self, category, guild, message, user):

        role_galleons = discord.utils.get(message.guild.roles, name="💰")
        channels = [channel.name for channel in category.text_channels]
        cycle, path, timestamp, user_hints, actions, purchase = expecto.get_data_quest1(user.id)
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
                if path not in ["path8", "path18", "path12", "path13", "path0"]:
                    await expecto.Expecto(self.client).update_path_quest1(user, cycle, path_new="path8")
                await asyncio.sleep(3)
                await message.delete()
            else:
                await asyncio.sleep(3)
                await message.delete()
                await expecto.penalize_quest1(user, cycle, points=30)

        elif "gringotts-bank" in channels and int(get_time().strftime("%H")) in [9, 10, 11, 12, 21, 22, 23, 0]:

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
                if path not in ["path8", "path18", "path12", "path13", "path0"]:
                    await expecto.Expecto(self.client).update_path_quest1(user, cycle, path_new="path8")
                await asyncio.sleep(3)
                await message.delete()
            else:
                await asyncio.sleep(3)
                await message.delete()
                await expecto.penalize_quest1(user, cycle, points=30)
        else:
            await reaction_closed(message)

    async def transaction_gringotts(self, user, guild, message):

        role_galleons = discord.utils.get(message.guild.roles, name="💰")
        cycle, path, timestamp, user_hints, actions, purchase = expecto.get_data_quest1(user.id)

        if user in role_galleons.members:

            if actions >= 3:
                return

            else:
                responses = expecto.get_responses_quest1("gringotts_bank")
                msg = responses["has_moneybag"].format(user.mention)
                await secret_response(guild.id, message.channel.name, msg)
                await expecto.action_update_quest1(user, cycle, actions=3)
                await expecto.penalize_quest1(user, cycle, points=20)

        elif user not in role_galleons.members:

            if actions >= 3:
                return

            elif actions < 3 and message.content.lower() in ["vault", "money", "galleon", "galleons"]:
                responses = expecto.get_responses_quest1("gringotts_bank")
                await expecto.action_update_quest1(user, cycle, actions=10)
                await self.vault_access(user, guild, role_galleons, message, responses)

            elif actions < 3:
                responses = expecto.get_responses_quest1("gringotts_bank")
                msg = responses["transaction"][actions].format(user.mention)
                await secret_response(guild.id, message.channel.name, msg)
                await expecto.action_update_quest1(user, cycle, actions=1)
                await expecto.penalize_quest1(user, cycle, points=10)

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

                    cycle, path, timestamp, user_hints, actions, purchase = expecto.get_data_quest1(user.id)

                    embed = DiscordEmbed(
                        color=0xffffff,
                        title=f"🔐 Opening Vault# {vault}"
                    )
                    embed.set_image(url="https://i.imgur.com/RIS1TLh.gif")

                    webhook = DiscordWebhook(url=webhook_url, avatar_url=avatar, username=username)
                    webhook.add_embed(embed)
                    webhook.execute()

                    if path != "path0":
                        await expecto.Expecto(self.client).update_path_quest1(user, cycle, path_new="path15")

                    await user.add_roles(role_galleons)
                    await asyncio.sleep(6)
                    await message.channel.send(msg1)
                    await secret_response(guild.id, message.channel.name, msg2)

                    thieves.update_one({}, {"$pull": {"names": str(user.id)}})

    async def obtain_identity(self, user, guild, message, responses):

        answer, topic = "Wrong", ""
        msg = responses["get_identity"]["1"].format(user.mention)
        await secret_response(guild.id, message.channel.name, msg)
        cycle, path, timestamp, user_hints, actions, purchase = expecto.get_data_quest1(user.id)

        if path != "path0":
            await expecto.Expecto(self.client).update_path_quest1(user, cycle, path_new="path21")

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

                await expecto.Expecto(self.client).update_path_quest1(user, cycle, path_new="path18")
                await expecto.action_update_quest1(user, cycle, actions=3)
                await expecto.penalize_quest1(user, cycle, points=10)
                await secret_response(guild.id, message.channel.name, msg)
                await message.channel.edit(topic=topic)
                break

            except KeyError:

                if i == 0:
                    msg = responses["get_identity"]["invalid1"][0].format(user.mention)
                    topic = responses["get_identity"]["invalid1"][1]
                    await expecto.penalize_quest1(user, cycle, points=10)

                elif i == 1:
                    msg = responses["get_identity"]["invalid2"][0].format(user.mention)
                    topic = responses["get_identity"]["invalid2"][1]
                    await expecto.penalize_quest1(user, cycle, points=10)

                elif i == 2:
                    msg = responses["get_identity"]["invalid3"][0].format(user.mention)
                    topic = responses["get_identity"]["invalid3"][1]

                    if thieves.find_one({"names": str(user.id)}, {"_id": 0}) is None:
                        thieves.update_one({}, {"$push": {"names": str(user.id)}})

                    await expecto.Expecto(self.client).update_path_quest1(user, cycle, path_new="path18")
                    await expecto.action_update_quest1(user, cycle, actions=3)
                    await expecto.penalize_quest1(user, cycle, points=10)

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
        cycle, path, timestamp, user_hints, actions, purchase = expecto.get_data_quest1(user.id)

        if path != "path0":
            await expecto.Expecto(self.client).update_path_quest1(user, cycle, path_new="path22")

        if path == "path18":
            await expecto.Expecto(self.client).update_path_quest1(user, cycle, path_new="path5")

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

                await expecto.Expecto(self.client).update_path_quest1(user, cycle, path_new="path12")
                await expecto.action_update_quest1(user, cycle, actions=3)
                await expecto.penalize_quest1(user, cycle, points=10)
                await secret_response(guild.id, message.channel.name, msg)
                await message.channel.edit(topic=topic)
                break

            except KeyError:

                if i == 0:
                    msg = responses["get_vault"]["invalid1"][0].format(user.mention)
                    topic = responses["get_vault"]["invalid1"][1]
                    await expecto.penalize_quest1(user, cycle, points=10)

                elif i == 1:
                    msg = responses["get_vault"]["invalid2"][0].format(user.mention)
                    topic = responses["get_vault"]["invalid2"][1]
                    await expecto.penalize_quest1(user, cycle, points=10)

                elif i == 2:
                    answer = "Wrong"
                    msg = responses["get_vault"]["invalid3"][0].format(user.mention)
                    topic = responses["get_vault"]["invalid3"][1]

                    if thieves.find_one({"names": str(user.id)}, {"_id": 0}) is None:
                        thieves.update_one({}, {"$push": {"names": str(user.id)}})

                    await expecto.Expecto(self.client).update_path_quest1(user, cycle, path_new="path12")
                    await expecto.action_update_quest1(user, cycle, actions=3)
                    await expecto.penalize_quest1(user, cycle, points=10)

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
        cycle, path, timestamp, user_hints, actions, purchase = expecto.get_data_quest1(user.id)

        if path != "path0":
            await expecto.Expecto(self.client).update_path_quest1(user, cycle, path_new="path23")

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

                await expecto.Expecto(self.client).update_path_quest1(user, cycle, path_new="path13")
                await expecto.action_update_quest1(user, cycle, actions=3)
                await expecto.penalize_quest1(user, cycle, points=10)
                await secret_response(guild.id, message.channel.name, msg)
                await message.channel.edit(topic=topic)
                break

            except KeyError:

                if i == 0:
                    msg = responses["get_password"]["invalid1"][0].format(user.mention)
                    topic = responses["get_password"]["invalid1"][1]
                    await expecto.penalize_quest1(user, cycle, points=10)

                elif i == 1:
                    msg = responses["get_password"]["invalid2"][0].format(user.mention)
                    topic = responses["get_password"]["invalid2"][1]
                    await expecto.penalize_quest1(user, cycle, points=10)

                elif i == 2:
                    answer = "Wrong"
                    msg = responses["get_password"]["invalid3"][0].format(user.mention)
                    topic = responses["get_password"]["invalid3"][1]

                    if thieves.find_one({"names": str(user.id)}, {"_id": 0}) is None:
                        thieves.update_one({}, {"$push": {"names": str(user.id)}})

                    await expecto.Expecto(self.client).update_path_quest1(user, cycle, path_new="path13")
                    await expecto.action_update_quest1(user, cycle, actions=3)
                    await expecto.penalize_quest1(user, cycle, points=10)

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
    
        
def setup(client):
    client.add_cog(Quest(client))
