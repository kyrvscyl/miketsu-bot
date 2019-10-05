"""
Clock Module
Miketsu, 2019
"""

import asyncio
import os
import random
import sys
from datetime import datetime

import discord
import pytz
from discord.ext import commands

from cogs.economy import Economy, reset_boss
from cogs.frames import Frames
from cogs.mongo.database import get_collections
from cogs.quest import Expecto, owls_restock

# Collections
guilds = get_collections("guilds")
weathers = get_collections("weathers")
reminders = get_collections("reminders")
quests = get_collections("quests")
config = get_collections("config")

# Lists
clock_emojis = config.find_one({"list": 1}, {"_id": 0, "clock_emojis": 1})["clock_emojis"]

# Variables
guild_id = int(os.environ.get("SERVER"))
timezone = config.find_one({"var": 1}, {"_id": 0, "timezone": 1})["timezone"]
embed_color = config.find_one({"var": 1}, {"_id": 0, "embed_color": 1})["embed_color"]
clock_channel = guilds.find_one({"server": str(guild_id)}, {"channels.clock": 1, "_id": 0})["channels"]["clock"]


def get_time():
    return datetime.now(tz=pytz.timezone(timezone))


def generate_weather(hour):
    if 18 > hour >= 6:
        day = weathers.find_one({"type": "day"}, {"_id": 0, "type": 0})
        weather1 = random.choice(list(day.values()))
        weather2 = ""
        weathers.update_one({"weather1": {"$type": "string"}}, {"$set": {"weather1": weather1}})
        weathers.update_one({"weather2": {"$type": "string"}}, {"$set": {"weather2": weather2}})

    else:
        night = weathers.find_one({"type": "night"}, {"_id": 0, "type": 0})
        moon = weathers.find_one({"type": "moon"}, {"_id": 0, "type": 0})
        weather1 = random.choice(list(night.values()))
        weather2 = random.choice(list(moon.values()))
        weathers.update_one({"weather1": {"$type": "string"}}, {"$set": {"weather1": weather1}})
        weathers.update_one({"weather2": {"$type": "string"}}, {"$set": {"weather2": weather2}})

    return weather1, weather2


def get_emoji(hours, minutes):
    if int(minutes) >= 30:
        emoji_clock_index = (int(hours) * 2) + 2
    else:
        emoji_clock_index = (int(hours) * 2) + 1

    emoji_clock = clock_emojis[emoji_clock_index]
    return emoji_clock


async def penalty_hour():
    quests.update_many({"quest1.status": "ongoing"}, {"$inc": {"quest1.$.score": -5}})


async def actions_reset():
    quests.update_many({"quest1.status": "ongoing"}, {"$set": {"quest1.$.actions": 0}})


async def reset_purchase():
    quests.update_many({"quest1.purchase": False}, {"$set": {"quest1.$.purchase": True}})


class Clock(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        await self.clock_start()

    async def clock_start(self):
        while True:
            try:
                if get_time().strftime("%S") == "00":
                    await self.clock_update()
                    await asyncio.sleep(1)
                else:
                    await asyncio.sleep(1)
            except:
                continue

    async def clock_update(self):

        try:
            time = get_time().strftime("%H:%M EST | %a")
            hour_minute = get_time().strftime("%H:%M")
            minute = get_time().strftime("%M")
            hour_24 = get_time().strftime("%H")
            hour_12 = get_time().strftime("%I")
            day_week = get_time().strftime("%a")
            weather1 = weathers.find_one({"weather1": {"$type": "string"}}, {"weather1": 1})["weather1"]
            weather2 = weathers.find_one({"weather2": {"$type": "string"}}, {"weather2": 1})["weather2"]

            if minute == "00":
                weather1, weather2 = generate_weather(int(hour_24))

            try:
                clock = self.client.get_channel(int(clock_channel))
                await clock.edit(name=f"{get_emoji(hour_12, minute)} {time} {weather1} {weather2}")
            except RuntimeError:
                pass
            except AttributeError:
                pass
            except discord.errors.InvalidArgument:
                pass
            except discord.errors.Forbidden:
                pass
            except discord.errors.HTTPException:
                pass

            if minute == "00":
                await penalty_hour()
                await actions_reset()
                await reset_purchase()
                await Expecto(self.client).send_off_report_quest1()
                await Expecto(self.client).send_off_complete_quest1()
                await self.perform_delete_secret_channels()
                await Frames(self.client).achievements_process_hourly()

            if hour_minute in ["02:00", "08:00", "14:00", "20:00"]:
                await owls_restock()

            if hour_minute == "00:00":
                await reset_boss()
                await Economy(self.client).reset_rewards_daily()

                if day_week.lower() == "mon":
                    await Economy(self.client).reset_rewards_weekly()

                await Economy(self.client).frame_automate()
                await Frames(self.client).achievements_process_daily()

        except:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            print("clock.py error: ", f"{exc_type}, Line {exc_tb.tb_lineno}")

    async def perform_delete_secret_channels(self):
        query = guilds.find({}, {
            "_id": 0, "eeylops-owl-emporium": 1, "ollivanders": 1, "gringotts-bank": 1
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
                            continue
                        except discord.errors.HTTPException:
                            continue


def setup(client):
    client.add_cog(Clock(client))
