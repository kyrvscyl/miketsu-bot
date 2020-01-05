"""
Clock Module
Miketsu, 2020
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
from pushbullet import Pushbullet

from cogs.economy import Economy
from cogs.ext.database import get_collections
from cogs.frames import Frames
from cogs.gameplay import Gameplay
from cogs.quest import Expecto, owls_restock

# Pushbullet
pb = Pushbullet(api_key=str(os.environ.get("PUSHBULLET")))

# Collections
config = get_collections("config")
events = get_collections("events")
guilds = get_collections("guilds")
logs = get_collections("logs")
quests = get_collections("quests")
reminders = get_collections("reminders")
ships = get_collections("ships")
streaks = get_collections("streaks")
users = get_collections("users")
weathers = get_collections("weathers")

# Instantiations
id_guild = int(os.environ.get("SERVER"))


def check_if_user_has_any_admin_roles(ctx):
    for role in reversed(ctx.author.roles):
        if role.name in config.find_one({"list": 1}, {"_id": 0})["admin_roles"]:
            return True
    return False


class Clock(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.prefix = self.client.command_prefix

        self.colour = config.find_one({"var": 1}, {"_id": 0, "embed_color": 1})["embed_color"]
        self.timezone = config.find_one({"var": 1}, {"_id": 0, "timezone": 1})["timezone"]

        self.channels = guilds.find_one({"server": str(id_guild)}, {"_id": 0, "channels": 1})
        self.roles = guilds.find_one({"server": str(id_guild)}, {"_id": 0, "roles": 1})
        self.listings = config.find_one({"list": 1}, {"_id": 0})

        self.id_boss_busters = self.roles["roles"]["boss_busters"]
        self.id_silver_sickles = self.roles["roles"]["silver_sickles"]

        self.id_clock = self.channels["channels"]["clock"]
        self.id_headlines = self.channels["channels"]["headlines"]
        self.id_spell_spam = self.channels["channels"]["spell-spam"]

        self.admin_roles = self.listings["admin_roles"]
        self.clock_emojis = self.listings["clock_emojis"]

        self.captions = cycle(events.find_one({"event": "showdown bidding"}, {"_id": 1, "comments": 1})["comments"])

    def get_time(self):
        return datetime.now(tz=pytz.timezone(self.timezone))

    def get_timestamp(self):
        return datetime.utcfromtimestamp(datetime.timestamp(datetime.now()))

    def get_emoji(self, hours, minutes):
        if int(minutes) >= 30:
            emoji_clock_index = (int(hours) * 2) + 2
        else:
            emoji_clock_index = (int(hours) * 2) + 1

        emoji_clock = self.clock_emojis[emoji_clock_index]
        return emoji_clock

    def generate_weather(self, hour):
        print(f"Generating new weather")

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

    def pluralize(self, singular, count):
        if count > 1:
            if singular[-1:] == "s":
                return singular + "es"
            return singular + "s"
        else:
            return singular

    async def perform_announce_netherworld(self):

        print("Opening the netherworld gates")
        users.update_many({}, {"$set": {"nether_pass": True}})
        spell_spam_channel = self.client.get_channel(int(self.id_spell_spam))
        content = f"<@&{self.id_boss_busters}>"

        embed = discord.Embed(
            color=self.colour,
            title="Netherworld gates update",
            description=f"The gates of Netherworld have been re-opened\n"
                        f"use `{self.prefix}enc` to explore them by chance",
            timestamp=self.get_timestamp()
        )
        await spell_spam_channel.send(content=content, embed=embed)

    async def perform_announce_reminders(self):

        print("Processing event reminders")
        for reminder in events.find({"status": True}, {"_id": 0}):
            if reminder["next"].strftime("%Y-%m-%d %H:%M") == self.get_time().strftime("%Y-%m-%d %H:%M"):

                events.update_one({
                    "code": reminder["code"],
                    "status": True
                }, {
                    "$set": {
                        "last": reminder["next"],
                        "next": reminder["next"] + timedelta(days=reminder["delta"])
                    }
                })

                headlines_channel = self.client.get_channel(int(self.id_headlines))

                content = f"<@&{reminder['role_id']}>"
                embed = discord.Embed(
                    title="⏰ Reminder",
                    description="{}".format(reminder['description'].replace('\\n', '\n')),
                    timestamp=self.get_timestamp(),
                    color=16733562
                )
                await headlines_channel.send(content=content, embed=embed)

                new_reminder = events.find_one({"code": reminder["code"], "status": True}, {"_id": 0})

                if new_reminder["next"] > reminder["end"]:
                    events.update_one({"code": reminder["code"], "status": True}, {"$set": {"status": False}})

    async def perform_announce_reminders_bidding(self, date_time):

        print(f"Processing bidding reminders")
        request = guilds.find_one({"server": str(id_guild)}, {"_id": 0})
        headlines_channel = self.client.get_channel(int(request["channels"]["headlines"]))
        reminders_date_list = events.find_one({"event": "showdown bidding"}, {"_id": 1, "dates": 1})["dates"]
        gold_galleons_id = request["roles"]["golden_galleons"]

        content = f"<@&{gold_galleons_id}>"
        embed = discord.Embed(
            color=self.colour,
            title="A new round of showdown bidding has started!",
            timestamp=datetime.utcfromtimestamp(datetime.timestamp(datetime.now()))
        )
        embed.description = next(self.captions)
        try:
            embed.set_footer(text=f"Round {reminders_date_list.index(date_time) + 1} of {len(reminders_date_list)}")
            msg = await headlines_channel.send(content=content, embed=embed)
            await msg.add_reaction("🔵")
            await msg.add_reaction("🔴")

        except ValueError:
            pass

    async def perform_delete_secret_channels(self):
        query = guilds.find({}, {"_id": 0, "eeylops-owl-emporium": 1, "ollivanders": 1, "gringotts-bank": 1})
        print("Deleting exposed secret channels")

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

    async def perform_penalize_streak(self):
        print("Penalizing all summon streaks")

        for streak in streaks.find({}, {"_id": 0}):
            current_streak = streak["SSR_current"]
            new_streak = int(current_streak * (3/4))

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

    async def perform_penalize_score(self):
        quests.update_many({"quest1.status": "ongoing"}, {"$inc": {"quest1.$.score": -5}})
        print(f"Penalizing all ongoing quest1 users")

    async def perform_reset_actions(self):
        quests.update_many({"quest1.status": "ongoing"}, {"$set": {"quest1.$.actions": 0}})
        print(f"Resetting all quest1 actions to 0")

    async def perform_reset_purchase(self):
        quests.update_many({"quest1.purchase": False}, {"$set": {"quest1.$.purchase": True}})
        print(f"Resetting all quest1 purchases to True")

    async def perform_add_log(self, currency, amount, user_id):

        if logs.find_one({"user_id": str(user_id)}, {"_id": 0}) is None:
            profile = {"user_id": str(user_id), "logs": []}
            logs.insert_one(profile)

        logs.update_one({
            "user_id": str(user_id)
        }, {
            "$push": {
                "logs": {
                    "$each": [{
                        "currency": currency,
                        "amount": amount,
                        "date": self.get_time(),
                    }],
                    "$position": 0,
                    "$slice": 200
                }
            }
        })

    @commands.Cog.listener()
    async def on_ready(self):
        await self.clock_start()

    @commands.command(aliases=["tick"])
    @commands.guild_only()
    async def clock_start_manual(self, ctx):
        config.update_one({"var": 1}, {"$set": {"clock": False}})
        await ctx.message.add_reaction("✅")
        await self.clock_start()

    async def clock_start(self):

        if config.find_one({"var": 1}, {"_id": 0, "clock": 1})["clock"] is False:
            config.update_one({"var": 1}, {"$set": {"clock": True}})
            print("Initializing a clock instance")
            pb.push_note("Miketsu Bot", "Initializing a clock instance")

            while True:
                try:
                    if self.get_time().strftime("%S") == "00":
                        await self.clock_update()
                        await asyncio.sleep(1)
                    else:
                        await asyncio.sleep(1)

                except KeyboardInterrupt:
                    pb.push_note("Miketsu Bot", "Stopping a concurrent function")
                    break
                except:
                    pb.push_note("Miketsu Bot", "Ignoring exception on clock processing")
                    continue

    async def clock_update(self):

        try:
            time = self.get_time().strftime("%H:%M EST | %a")
            hour_minute = self.get_time().strftime("%H:%M")
            minute_hand = self.get_time().strftime("%M")
            hour_24 = self.get_time().strftime("%H")
            hour_12 = self.get_time().strftime("%I")
            day_week = self.get_time().strftime("%a")
            bidding_format = self.get_time().strftime("%b %d, %Y %H:%M")
            weather1 = weathers.find_one({"weather1": {"$type": "string"}}, {"weather1": 1})["weather1"]
            weather2 = weathers.find_one({"weather2": {"$type": "string"}}, {"weather2": 1})["weather2"]

            if minute_hand == "00":
                weather1, weather2 = self.generate_weather(int(hour_24))

            try:
                clock = self.client.get_channel(int(self.id_clock))
                clock_name = f"{self.get_emoji(hour_12, minute_hand)} {time} {weather1} {weather2}"
                print(f"{clock.name} -> {clock_name}")

                if clock.name == clock_name:
                    print("Killing the function")
                    raise KeyboardInterrupt

                await clock.edit(name=clock_name)

            except asyncio.CancelledError:
                raise KeyboardInterrupt
            except AttributeError:
                pass
            except discord.errors.InvalidArgument:
                pass
            except discord.errors.Forbidden:
                pass
            except discord.errors.HTTPException:
                pass

            if minute_hand == "00":
                await self.perform_penalize_score()
                await self.perform_reset_actions()
                await self.perform_reset_purchase()
                await Expecto(self.client).send_off_report_quest1()
                await Expecto(self.client).send_off_complete_quest1()
                await self.perform_delete_secret_channels()
                await self.perform_announce_reminders_bidding(bidding_format)
                await self.perform_announce_reminders()

            if hour_minute in ["02:00", "08:00", "14:00", "20:00"]:
                await owls_restock()

            if hour_minute in ["06:00", "18:00"]:
                await self.perform_announce_netherworld()

            if hour_minute == "00:00":
                await Gameplay(self.client).boss_daily_reset_check()
                await Economy(self.client).perform_reset_rewards_daily()

                if day_week.lower() == "mon":
                    await Economy(self.client).perform_reset_rewards_weekly()

                await Economy(self.client).frame_automate()
                await self.perform_penalize_streak()
                await Frames(self.client).achievements_process_daily()

            if minute_hand == "00":
                await Frames(self.client).achievements_process_hourly()

        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            pb.push_note("Miketsu Bot", f"{exc_type}, Line {exc_tb.tb_lineno}")
            print("clock.py error: ", f"{exc_type}, Line {exc_tb.tb_lineno}")

    @commands.command(aliases=["events", "event", "e"])
    @commands.check(check_if_user_has_any_admin_roles)
    async def events_manipulate(self, ctx, *args):

        if len(args) == 0:
            embed = discord.Embed(
                title="events, e",
                description="manipulate event settings for reminders, etc.",
                color=self.colour
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
                color=self.colour
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
                color=self.colour
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
            await self.events_manipulate_activate(ctx, args[2].lower(), args[1].lower())

        elif len(args) == 2 and args[0].lower() in ["deactivate", "d"] and args[1].lower() in ["cc", "ft"]:

            action = events.update_one({"code": args[1].lower(), "status": True}, {"$set": {"status": False}})

            if action.modified_count == 0:
                embed = discord.Embed(
                    title="Invalid action",
                    description="this event is already deactivated",
                    color=self.colour
                )
                await ctx.channel.send(embed=embed)

            else:
                await ctx.message.add_reaction("✅")

        else:
            await ctx.message.add_reaction("❌")

    async def events_manipulate_activate(self, ctx, event, timing):

        if timing.lower() == "now":
            offset = (self.get_time().weekday() - 2) % 7
            get_patch_start_day = (self.get_time() - timedelta(days=offset)).strftime("%Y-%m-%d")
        else:
            offset = (self.get_time().weekday() - 2) % 7
            get_patch_start_day = (self.get_time() + timedelta(days=offset)).strftime("%Y-%m-%d")

        date_absolute = datetime.strptime(get_patch_start_day, "%Y-%m-%d")
        request = events.find_one({"code": event}, {"_id": 0})

        date_next = date_absolute + timedelta(days=request['delta']) - timedelta(hours=request['delta_hr'])
        date_start = date_absolute

        if timing.lower() == "now":
            date_start = datetime.strptime(self.get_time().strftime("%Y-%m-%d"), "%Y-%m-%d")
            date_next = date_start + timedelta(days=request['delta']) - timedelta(hours=request['delta_hr'])

            if date_start < datetime.strptime(self.get_time().strftime("%Y-%m-%d %H:%M"), "%Y-%m-%d %H:%M"):
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
            color=self.colour,
            timestamp=self.get_timestamp()
        )
        embed.add_field(
            name="Action",
            value=f"Pings <@&{role_id}> role; {request['delta_hr']} hours before the reset at <#{self.id_headlines}>"
        )
        await ctx.channel.send(embed=embed)

    @commands.command(aliases=["test2"])
    @commands.is_owner()
    async def manual_process_achievements_hourly(self, ctx):
        await ctx.message.add_reaction("✅")
        await Frames(self.client).achievements_process_hourly()

    @commands.command(aliases=["test4"])
    @commands.is_owner()
    async def manual_process_achievements_daily(self, ctx):
        await ctx.message.add_reaction("✅")
        await Frames(self.client).achievements_process_daily()

    @commands.command(aliases=["test3"])
    @commands.is_owner()
    async def manual_process_frames_daily(self, ctx):
        await ctx.message.add_reaction("✅")
        await Economy(self.client).frame_automate()
        await self.perform_penalize_streak()


def setup(client):
    client.add_cog(Clock(client))
