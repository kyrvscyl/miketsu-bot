"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import asyncio
import os
import random
from datetime import datetime

import discord
import pytz
from discord.ext import commands

from cogs.admin import Admin
from cogs.castle import Castle
from cogs.error import logging, get_f
from cogs.frame import Frame
from cogs.library import Library
from cogs.magic import Magic, penalize, get_data, get_dictionary
from cogs.mongo.db import books, weather, sendoff, quests, owls, daily

# from cogs.owl import get_dictionary2


file = os.path.basename(__file__)[:-3:]


clock_channels = []
for guild_clock in books.find({}, {"channels.clock": 1, "_id": 0}):
    clock_channels.append(guild_clock["channels"]["clock"])


def get_time():
    tz_target = pytz.timezone("America/Atikokan")
    return datetime.now(tz=tz_target)


def generate_weather(hour):
    if 18 > hour >= 6:
        day = weather.find_one({"type": "day"}, {"_id": 0, "type": 0})
        weather1 = random.choice(list(day.values()))
        weather2 = ""
        weather.update_one({"weather1": {"$type": "string"}}, {"$set": {"weather1": weather1}})
        weather.update_one({"weather2": {"$type": "string"}}, {"$set": {"weather2": weather2}})

    else:
        night = weather.find_one({"type": "night"}, {"_id": 0, "type": 0})
        moon = weather.find_one({"type": "moon"}, {"_id": 0, "type": 0})
        weather1 = random.choice(list(night.values()))
        weather2 = random.choice(list(moon.values()))
        weather.update_one({"weather1": {"$type": "string"}}, {"$set": {"weather1": weather1}})
        weather.update_one({"weather2": {"$type": "string"}}, {"$set": {"weather2": weather2}})

    return weather1, weather2


def get_emoji(hours, minutes):
    list_clock = ["", "", "", "🕐", "🕜", "🕑", "🕝", "🕒", "🕞", "🕓", "🕟", "🕔", "🕠", "🕕",
                  "🕡", "🕖", "🕢", "🕗", "🕣", "🕘", "🕤", "🕙", "🕥", "🕚", "🕦", "🕛", "🕧"]

    if int(minutes) >= 30:
        emoji_clock_index = (int(hours) * 2) + 2
    else:
        emoji_clock_index = (int(hours) * 2) + 1

    emoji_clock = list_clock[emoji_clock_index]
    return emoji_clock


async def penalty_hour():
    quests.update_many({"quest1.status": "ongoing"}, {"$inc": {"quest1.$.score": -5}})


async def actions_reset():
    quests.update_many({"quest1.status": "ongoing"}, {"$set": {"quest1.$.actions": 0}})


async def reset_library():
    for entry in daily.find({"key": "library"}, {"key": 0, "_id": 0}):
        for user_id in entry:
            daily.update_one({"key": "library"}, {"$set": {f"{user_id}": 0}})


async def reset_purchase():
    quests.update_many({"quest1.purchase": False}, {"$set": {"quest1.$.purchase": True}})


async def owls_restock():
    owls.update_many({}, {"$set": {"purchaser": "None"}})


class Clock(commands.Cog):

    def __init__(self, client):
        self.client = client


    # noinspection PyBroadException
    @commands.Cog.listener()
    async def on_ready(self):
        while True:
            try:
                if get_time().strftime("%S") == "00":
                    await self.clock_update()
                    await asyncio.sleep(1)
                else:
                    await asyncio.sleep(1)
            except:
                continue


    @commands.command(aliases=["transform"])
    @commands.is_owner()
    async def transformation_trigger(self, ctx, *, args):

        if args.lower() == "start":
            await self.transformation_start()
            await ctx.message.delete()

        elif args.lower() == "end":
            await self.transformation_end()
            await ctx.message.delete()


    async def transformation_end(self):

        for entry in books.find({}, {"_id": 0, "server": 1}):
            try:
                server = self.client.get_guild(int(entry["server"]))
                reference_role = discord.utils.get(server.roles, name="Head")
                roles = ["No-Maj", "Patronus", "Auror", "Dementor", "Junior Duel Champion", "Senior Duel Champion"]

                for role in roles:
                    try:
                        current_role = discord.utils.get(server.roles, name=role)
                        await current_role.edit(position=reference_role.position - 1)
                        await asyncio.sleep(1)
                    except AttributeError:
                        logging(file, get_f(), "AttributeError")
                        continue
                    except discord.errors.Forbidden:
                        logging(file, get_f(), "discord.errors.Forbidden")
                        continue
                    except discord.errors.HTTPException:
                        logging(file, get_f(), "discord.errors.HTTPException")
                        continue
                    except discord.errors.InvalidArgument:
                        logging(file, get_f(), "discord.errors.InvalidArgument")
                        continue

            except AttributeError:
                logging(file, get_f(), "AttributeError")
                continue


    async def transformation_start(self):

        for entry in books.find({}, {"_id": 0, "server": 1}):

            try:
                server = self.client.get_guild(int(entry["server"]))
                reference_role = discord.utils.get(server.roles, name="🏆")
                roles = ["No-Maj", "Patronus", "Auror", "Dementor", "Junior Duel Champion", "Senior Duel Champion"]

                for role in roles:
                    try:
                        current_role = discord.utils.get(server.roles, name=role)
                        await current_role.edit(position=reference_role.position - 1)
                        await asyncio.sleep(1)
                    except AttributeError:
                        logging(file, get_f(), "AttributeError")
                        continue
                    except discord.errors.Forbidden:
                        logging(file, get_f(), "discord.errors.Forbidden")
                        continue
                    except discord.errors.HTTPException:
                        logging(file, get_f(), "discord.errors.HTTPException")
                        continue
                    except discord.errors.InvalidArgument:
                        logging(file, get_f(), "discord.errors.InvalidArgument")
                        continue

            except AttributeError:
                logging(file, get_f(), "AttributeError")
                continue


    @commands.command(aliases=["fastforward"])
    @commands.is_owner()
    async def hourly_task(self, ctx):
        await actions_reset()
        await reset_purchase()
        await self.send_off_report()
        await self.send_off_complete()
        await ctx.author.send("Actions reset, purchase reset, send off reports performed")


    async def send_off_complete(self):

        for entry in sendoff.find({"timestamp_complete": get_time().strftime("%Y-%b-%d %HH")}, {"_id": 0}):
            try:
                user = self.client.get_user(int(entry["user_id"]))
                cycle, path, timestamp, user_hint, actions, purchase = get_data(user.id)
            except AttributeError:
                logging(file, get_f(), "AttributeError")
                continue

            if entry["scenario"] == 2:
                async with user.typing():
                    responses = get_dictionary("send_off")["complete"]

                    if path != "path0":
                        await Magic(self.client).update_path(user, cycle, path_new="path3")

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
                        logging(file, get_f(), "discord.errors.Forbidden")
                        continue
                    except discord.errors.HTTPException:
                        logging(file, get_f(), "discord.errors.HTTPException")
                        continue

            elif entry["scenario"] == 1:
                await Magic(self.client).update_path(user, cycle, path_new="path20")

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
                    logging(file, get_f(), "discord.errors.Forbidden")
                    continue
                except discord.errors.HTTPException:
                    logging(file, get_f(), "discord.errors.HTTPException")
                    continue


    async def send_off_report(self):

        # add quest number in query
        for entry in sendoff.find({"timestamp_update": get_time().strftime("%Y-%b-%d %HH")}, {"_id": 0}):
            user = self.client.get_user(int(entry["user_id"]))

            if entry["scenario"] == 1:
                try:
                    cycle, path, timestamp, user_hint, actions, purchase = get_data(user.id)
                    await penalize(user, cycle, points=20)
                except AttributeError:
                    logging(file, get_f(), "AttributeError")
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
                logging(file, get_f(), "discord.errors.Forbidden")
                continue
            except discord.errors.HTTPException:
                logging(file, get_f(), "discord.errors.HTTPException")
                continue

    """
    async def send_off_flourish(self):

        query = sendoff.find({
            "quest": 2,
            "status": "incomplete",
            "timestamp_complete": get_time().strftime("%Y-%b-%d %HH")}, {
            "_id": 0
        })

        for entry in query:
            try:
                user = self.client.get_user(int(entry["user_id"]))
            except AttributeError:
                continue

            async with user.typing():
                responses = get_dictionary2("send_off")["complete"]

                try:
                    await user.send(responses[0])
                    await asyncio.sleep(4)
                    await user.send(responses[1])
                    await asyncio.sleep(4)
                    msg = await user.send(responses[2].format(entry['type'].capitalize()))
                    await msg.add_reaction("✉")

                    sendoff.update_one({
                        "user_id": entry["user_id"],
                        "cycle": query["cycle"]}, {
                        "$set": {
                            "status": "done"
                        }
                    })
                    # Change of path add

                except discord.errors.Forbidden:
                    logging(file, get_f(), "discord.errors.Forbidden")
                    continue
                except discord.errors.HTTPException:
                    logging(file, get_f(), "discord.errors.HTTPException")
                    continue
        
    """

    async def clear_secrets(self):
        query = books.find({}, {
            "_id": 0,
            "eeylops-owl-emporium": 1,
            "ollivanders": 1,
            "gringotts-bank": 1
        })

        for entry in query:
            for secret in entry:
                for key in entry[secret]:
                    if key == "id":
                        try:
                            channel = self.client.get_channel(int(entry[secret][key]))
                            await channel.delete()
                        except AttributeError:
                            continue
                        except discord.errors.Forbidden:
                            continue
                        except discord.errors.NotFound:
                            logging(file, get_f(), "discord.errors.NotFound")
                            continue
                        except discord.errors.HTTPException:
                            logging(file, get_f(), "discord.errors.HTTPException")
                            continue


    async def clock_update(self):

        time = get_time().strftime("%H:%M EST | %a")
        hour_minute = get_time().strftime("%H:%M")
        minute = get_time().strftime("%M")
        hour_24 = get_time().strftime("%H")
        hour_12 = get_time().strftime("%I")
        weather1 = weather.find_one({"weather1": {"$type": "string"}}, {"weather1": 1})["weather1"]
        weather2 = weather.find_one({"weather2": {"$type": "string"}}, {"weather2": 1})["weather2"]

        if minute == "00":
            weather1, weather2 = generate_weather(int(hour_24))
            await penalty_hour()
            await actions_reset()
            await reset_purchase()
            await self.send_off_report()
            await self.send_off_complete()
            await self.clear_secrets()
            await Castle(self.client).reset_prefects()


        if hour_minute in ["02:00", "08:00", "14:00", "20:00"]:
            await owls_restock()

        if hour_minute == "00:00":
            await Admin(self.client).reset_daily()
            await Frame(self.client).frame_automate()
            await reset_library()
            await Library(self.client).post_new_table_of_content()

        if hour_minute == "19:00":
            await self.transformation_start()

        elif hour_minute == "06:00":
            await self.transformation_end()

        for clock_channel in clock_channels:
            try:
                clock = self.client.get_channel(int(clock_channel))
                await clock.edit(name=f"{get_emoji(hour_12, minute)} {time} {weather1} {weather2}")
            except AttributeError:
                continue
            except discord.errors.InvalidArgument:
                logging(file, get_f(), "discord.errors.InvalidArgument")
                continue
            except discord.errors.Forbidden:
                logging(file, get_f(), "discord.errors.Forbidden")
                continue
            except discord.errors.HTTPException:
                logging(file, get_f(), "discord.errors.HTTPException")
                continue


def setup(client):
    client.add_cog(Clock(client))
