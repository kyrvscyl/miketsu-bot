"""
Clock Module
Miketsu, 2019
"""

import asyncio
import random
from datetime import datetime

import discord
import pytz
from discord.ext import commands

from cogs.castle import Castle
from cogs.economy import Economy, reset_boss
from cogs.frames import Frames
from cogs.library import Library
from cogs.mongo.db import get_collections
from cogs.quest import Expecto, owls_restock
from cogs.reminder import Reminder
from cogs.startup import embed_color

# Collections
books = get_collections("bukkuman", "books")
weather = get_collections("bukkuman", "weather")
reminders = get_collections("bukkuman", "reminders")
quests = get_collections("miketsu", "quests")

# Listings
clock_channels = []
list_clock = [
    "", "", "", "🕐", "🕜", "🕑", "🕝", "🕒", "🕞", "🕓", "🕟", "🕔", "🕠", "🕕",
    "🕡", "🕖", "🕢", "🕗", "🕣", "🕘", "🕤", "🕙", "🕥", "🕚", "🕦", "🕛", "🕧"
]

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


async def reset_purchase():
    quests.update_many({"quest1.purchase": False}, {"$set": {"quest1.$.purchase": True}})


class Clock(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        await self.clock_start()

    @commands.command(aliases=["tick"])
    @commands.is_owner()
    async def clock_start_manually(self, ctx):

        await self.clock_start()
        embed = discord.Embed(
            colour=discord.Colour(embed_color),
            description="Successfully started the clock manually"
        )
        await ctx.channel.send(embed=embed)

    async def clock_start(self):
        while True:
            # noinspection PyBroadException
            try:
                if get_time().strftime("%S") == "00":
                    await self.clock_update()
                    await asyncio.sleep(1)
                else:
                    await asyncio.sleep(1)
            except:
                continue

    @commands.command(aliases=["fastforward"])
    @commands.is_owner()
    async def hourly_task(self, ctx):
        await actions_reset()
        await reset_purchase()
        await Expecto(self.client).send_off_report_quest1()
        await Expecto(self.client).send_off_complete_quest1()
        await ctx.author.send("Actions reset, purchase reset, send-off reports performed")

    async def clear_secrets(self):
        query = books.find({}, {
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

    async def clock_update(self):

        time = get_time().strftime("%H:%M EST | %a")
        hour_minute = get_time().strftime("%H:%M")
        date_time = get_time().strftime("%b %d, %Y %H:%M")
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
            await Expecto(self.client).send_off_report_quest1()
            await Expecto(self.client).send_off_complete_quest1()
            await self.clear_secrets()
            await Frames(self.client).achievements_process_hourly()

        if date_time in reminders.find_one({"key": "bidding"}, {"_id": 0, "dates": 1})["dates"]:
            await Reminder(self.client).reminders_bidding_process(date_time)

        if hour_minute in ["02:00", "08:00", "14:00", "20:00"]:
            await owls_restock()

        if hour_minute in ["02:00", "08:00", "14:00", "20:00"]:
            await owls_restock()

        if hour_minute == "00:00":
            await Economy(self.client).frame_automate()
            await Economy(self.client).reset_rewards_daily()
            await reset_boss()
            await Frames(self.client).achievements_process_daily()
            await Library(self.client).post_new_table_of_content()

        if hour_minute == "19:00":
            await Castle(self.client).transformation_start()

        elif hour_minute == "06:00":
            await Castle(self.client).transformation_start()

        for clock_channel in clock_channels:
            try:
                clock = self.client.get_channel(int(clock_channel))
                await clock.edit(name=f"{get_emoji(hour_12, minute)} {time} {weather1} {weather2}")
            except AttributeError:
                continue
            except discord.errors.InvalidArgument:
                continue
            except discord.errors.Forbidden:
                continue
            except discord.errors.HTTPException:
                continue


def setup(client):
    client.add_cog(Clock(client))
