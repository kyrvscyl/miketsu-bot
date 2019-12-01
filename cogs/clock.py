"""
Clock Module
Miketsu, 2019
"""

import asyncio
import os
import random
import sys
from datetime import datetime, timedelta
from itertools import cycle

import discord
import pytz
from discord.ext import commands

from cogs.economy import Economy
from cogs.gameplay import boss_daily_reset_check
from cogs.frames import Frames
from cogs.mongo.database import get_collections
from cogs.quest import Expecto, owls_restock

# Collections
config = get_collections("config")
events = get_collections("events")
guilds = get_collections("guilds")
quests = get_collections("quests")
reminders = get_collections("reminders")
streaks = get_collections("streaks")
weathers = get_collections("weathers")

# Lists
admin_roles = config.find_one({"list": 1}, {"_id": 0, "admin_roles": 1})["admin_roles"]
captions = cycle(events.find_one({"event": "showdown bidding"}, {"_id": 1, "comments": 1})["comments"])
clock_emojis = config.find_one({"list": 1}, {"_id": 0, "clock_emojis": 1})["clock_emojis"]

# Variables
guild_id = int(os.environ.get("SERVER"))
clock_channel = guilds.find_one({"server": str(guild_id)}, {"channels.clock": 1, "_id": 0})["channels"]["clock"]
embed_color = config.find_one({"var": 1}, {"_id": 0, "embed_color": 1})["embed_color"]
headlines_id = guilds.find_one({"server": str(guild_id)}, {"_id": 0, "channels": 1})["channels"]["headlines"]
silver_sickles_id = guilds.find_one({"server": str(guild_id)}, {"_id": 0, "roles": 1})["roles"]["silver_sickles"]
timezone = config.find_one({"var": 1}, {"_id": 0, "timezone": 1})["timezone"]


def check_if_has_any_admin_roles(ctx):
    for role in reversed(ctx.author.roles):
        if role.name in admin_roles:
            return True
    return False


def get_time():
    return datetime.now(tz=pytz.timezone(timezone))


def get_timestamp():
    return datetime.utcfromtimestamp(datetime.timestamp(datetime.now()))


def get_emoji(hours, minutes):
    if int(minutes) >= 30:
        emoji_clock_index = (int(hours) * 2) + 2
    else:
        emoji_clock_index = (int(hours) * 2) + 1

    emoji_clock = clock_emojis[emoji_clock_index]
    return emoji_clock


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


async def frame_automate_penalize():

    for streak in streaks.find({}, {"_id": 0}):
        current_streak = streak["SSR_current"]
        new_streak = int(current_streak / 2)

        if new_streak > 1:
            streaks.update_one({
                "user_id": streak["user_id"]}, {
                "$set": {
                    "SSR_current": new_streak,
                    "SSR_record": new_streak
                }
            })

        else:
            streaks.update_one({
                "user_id": streak["user_id"]}, {
                "$set": {
                    "SSR_current": 0,
                    "SSR_record": 0
                }
            })


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
            bidding_format = get_time().strftime("%b %d, %Y %H:%M")
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
                await self.reminders_bidding_process(bidding_format)
                await self.events_activate_reminder_submit()
                await Frames(self.client).achievements_process_hourly()

            if hour_minute in ["02:00", "08:00", "14:00", "20:00"]:
                await owls_restock()

            if hour_minute == "00:00":
                await boss_daily_reset_check()
                await Economy(self.client).reset_rewards_daily()

                if day_week.lower() == "mon":
                    await Economy(self.client).reset_rewards_weekly()

                await Economy(self.client).frame_automate()
                await frame_automate_penalize()
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

    async def events_activate_reminder_submit(self):

        for reminder in events.find({"status": True}, {"_id": 0}):
            if reminder["next"].strftime("%Y-%m-%d") == get_time().strftime("%Y-%m-%d"):

                events.update_one({
                    "code": reminder["code"],
                    "status": True
                }, {
                    "$set": {
                        "last": reminder["next"],
                        "next": reminder["next"] + timedelta(days=reminder["delta"])
                    }
                })

                headlines_channel = self.client.get_channel(int(headlines_id))

                content = f"<@&{reminder['role_id']}>"
                embed = discord.Embed(
                    title="⏰ Reminder",
                    description="{}".format(reminder['description'].replace('\\n', '\n')),
                    timestamp=get_timestamp(),
                    color=16733562
                )
                await headlines_channel.send(content=content, embed=embed)

                new_reminder = events.find_one({"code": reminder["code"], "status": True}, {"_id": 0})

                if new_reminder["next"] > reminder["end"]:
                    events.update_one({"code": reminder["code"], "status": True}, {"$set": {"status": False}})

    @commands.command(aliases=["events", "event", "e"])
    @commands.check(check_if_has_any_admin_roles)
    async def events_manipulate(self, ctx, *args):

        if len(args) == 0:
            embed = discord.Embed(
                title="events, e",
                description="manipulate event settings for reminders, etc.",
                color=embed_color
            )
            embed.add_field(
                name="Arguments",
                value="activate, deactivate",
                inline=False
            )
            await ctx.channel.send(embed=embed)
        
        elif len(args) == 1 and args[0].lower() in ["activate", "a"]:
            embed = discord.Embed(
                title="events activate, e a",
                description="activate repetitive events",
                color=embed_color
            )
            embed.add_field(
                name="Timing",
                value="now, next",
                inline=False
            )
            embed.add_field(
                name="Event codes",
                value="coin chaos [cc], fortune temple [ft]",
                inline=False
            )
            embed.add_field(
                name="Example",
                value="*`;events act next cc`* - next Wed patch\n"
                      "*`;events act now cc`* - activates this week",
                inline=False
            )
            await ctx.channel.send(embed=embed)

        elif len(args) == 1 and args[0].lower() in ["deactivate", "d"]:
            embed = discord.Embed(
                title="events deactivate, e d",
                description="deactivate events",
                color=embed_color
            )
            embed.add_field(
                name="Event codes",
                value="coin chaos [cc], fortune temple [ft]",
                inline=False
            )
            embed.add_field(
                name="Example",
                value="*`;events d cc`*\n",
                inline=False
            )
            await ctx.channel.send(embed=embed)

        elif len(args) == 3 and args[0].lower() in ["activate", "a"] \
                and args[1].lower() in ["now", "next"] and args[2].lower() in ["cc", "ft"]:
            await self.events_manipulate_process_activation(ctx, args[2].lower(), args[1].lower())

        elif len(args) == 2 and args[0].lower() in ["deactivate", "d"] and args[1].lower() in ["cc", "ft"]:

            action = events.update_one({"code": args[1].lower(), "status": True}, {"$set": {"status": False}})

            if action.modified_count == 0:
                embed = discord.Embed(
                    title="Invalid action",
                    description="this event is already deactivated",
                    color=embed_color
                )
                await ctx.channel.send(embed=embed)

            else:
                await ctx.message.add_reaction("✅")

        else:
            await ctx.message.add_reaction("❌")

    async def events_manipulate_process_activation(self, ctx, event, timing):

        if timing.lower() == "now":
            offset = (get_time().weekday() - 2) % 7
            get_patch_start_day = (get_time() - timedelta(days=offset)).strftime("%Y-%m-%d")
        else:
            offset = (get_time().weekday() - 2) % 7
            get_patch_start_day = (get_time() + timedelta(days=offset)).strftime("%Y-%m-%d")

        date_absolute = datetime.strptime(get_patch_start_day, "%Y-%m-%d")
        request = events.find_one({"code": event}, {"_id": 0})

        date_next = date_absolute + timedelta(days=request['delta']) - timedelta(hours=request['delta_hr'])
        date_start = date_absolute

        if timing.lower() == "now":
            date_start = datetime.strptime(get_time().strftime("%Y-%m-%d"), "%Y-%m-%d")
            date_next = date_start + timedelta(days=request['delta']) - timedelta(hours=request['delta_hr'])

            if date_start < datetime.strptime(get_time().strftime("%Y-%m-%d %H:%M"), "%Y-%m-%d %H:%M"):
                date_start = date_start + timedelta(days=1)
                date_next = date_next + timedelta(days=1)

        date_end = date_absolute + timedelta(days=request['duration']) - timedelta(hours=request['delta_hr'])

        events.update_one({
            "code": event,
        }, {
            "$set": {
                "status": True,
                "last": None,
                "next": date_next,
                "start": date_start,
                "end": date_end
            }
        })
        await asyncio.sleep(2)
        request = events.find_one({"code": event}, {"_id": 0})
        role_id = request['role_id']

        embed = discord.Embed(
            title="Event activation",
            description=f"Title: {request['event'].title()}\n"
                        f"Duration: `{date_start.strftime('%Y-%m-%d | %a')}` until "
                        f"`{date_end.strftime('%Y-%m-%d | %a')}`",
            color=embed_color,
            timestamp=get_timestamp()
        )
        embed.add_field(
            name="Action",
            value=f"Pings <@&{role_id}> role; {request['delta_hr']} hours before the reset at <#{headlines_id}>"
        )
        await ctx.channel.send(embed=embed)

    @commands.command(aliases=["test"])
    @commands.is_owner()
    async def events_manipulate_manual_post(self, ctx):
        await Frames(self.client).achievements_process_hourly()

    async def reminders_bidding_process(self, date_time):

        request = guilds.find_one({"server": str(guild_id)}, {"_id": 0})
        headlines_channel = self.client.get_channel(int(request["channels"]["headlines"]))
        reminders_date_list = events.find_one({"event": "showdown bidding"}, {"_id": 1, "dates": 1})["dates"]
        gold_galleons_id = request["roles"]["golden_galleons"]

        content = f"<@&{gold_galleons_id}>"
        embed = discord.Embed(
            color=embed_color,
            title="A new round of showdown bidding has started!",
            timestamp=datetime.utcfromtimestamp(datetime.timestamp(datetime.now()))
        )
        embed.description = next(captions)
        try:
            embed.set_footer(text=f"Round {reminders_date_list.index(date_time) + 1} of {len(reminders_date_list)}")
            msg = await headlines_channel.send(content=content, embed=embed)
            await msg.add_reaction("🔵")
            await msg.add_reaction("🔴")

        except ValueError:
            pass


def setup(client):
    client.add_cog(Clock(client))
