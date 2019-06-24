"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import asyncio
import random
from datetime import datetime

import discord
import pytz
from discord.ext import commands

from cogs.magic import Magic
from cogs.magic import get_data
from cogs.mongo.db import books, weather, sendoff, quests, owls
from cogs.admin import Admin


# Get the clock channels
clock_channels = []
for guild_clock in books.find({}, {"clock": 1, "_id": 0}):
    if guild_clock["clock"] != "":
        clock_channels.append(guild_clock["clock"])

# Timezone
tz_target = pytz.timezone("America/Atikokan")

# Global Variables
status = "None"
list_clock = ["", "", "🕐", "🕜", "🕑", "🕒", "🕞", "🕓", "🕓", "🕔", "🕠", "🕕", "🕕", "🕖", "🕢", "🕗", "🕣",
              "🕘", "🕤", "🕙", "🕥", "🕚", "🕦", "🕛", "🕧"]


def get_time():
    time = datetime.now(tz=tz_target)
    return time


# noinspection PyCallingNonCallable
class Clock(commands.Cog):

    def __init__(self, client):
        self.client = client

    async def logging(self, msg):
        channel = self.client.get_channel(592270990894170112)
        date_time = datetime.now(tz=tz_target).strftime("%Y-%b-%d %HH")
        await channel.send(f"[{date_time}] " + msg)

    @commands.Cog.listener()
    async def on_ready(self):

        while True:
            if get_time().strftime("%S") == "00":
                await self.clock_update()
                await asyncio.sleep(1)
            else:
                await asyncio.sleep(1)

    # noinspection PyShadowingNames
    async def penalty_hour(self):
        quests.update_many({"quest1.status": "ongoing"}, {"$inc": {"quest1.$.score": -2}})
        await self.logging("Penalizing everyone with 2 points for every hour passed")

    async def owls_restock(self):
        owls.update_many({"purchaser": {"$ne": "None"}}, {"$set": {"purchaser": "None"}})
        await self.logging("Restocking emporium with all owls")

    async def actions_reset(self):
        quests.update_many({"quest1.status": "ongoing"}, {"$set": {"quest1.$.actions": 0}})
        await self.logging("Resetting all user actions to 0")

    async def send_off_complete(self):

        for entry in sendoff.find({"timestamp_complete": {"$exists": True}}, {"_id": 0}):
            if entry["timestamp_complete"] == get_time().strftime("%Y-%b-%d %HH"):

                user = self.client.get_user(int(entry["user_id"]))
                cycle, path, timestamp, user_hint, actions = get_data(user)

                if entry["scenario"] == 2:
                    description = f"Dear {user.name},\n\nIt is wondrous to have such another promising magic " \
                        f"practitioner, you see in the castle everyone there is special, but what makes them " \
                        f"more special is their Patronus charm.\n\nYour term awaits soon. Good luck!\n\n" \
                        f"Yours Truly,\nThe Headmaster "

                    embed = discord.Embed(color=0xffff80, description=description)
                    msg = f"Your {entry['type']} has returned with a letter from the Headmaster"
                    await Magic(self).update_path(user, cycle, path_new="path3")
                    await user.send(msg, embed=embed)
                    await self.logging(f"Sent {user}: Confirmation letter receipt from the Headmaster")

                elif entry["scenario"] == 1:
                    user = self.client.get_user(int(entry["user_id"]))
                    msg = f"Your {entry['type']} has fully recovered"

                    await Magic(self).update_path(user, cycle, path_new="path20")
                    await user.send(embed=msg)

    async def send_off_report(self):

        for entry in sendoff.find({"timestamp_update": {"$exists": True}}, {"_id": 0}):
            if entry["timestamp_update"] == get_time().strftime("%Y-%b-%d %HH"):
                user = self.client.get_user(int(entry["user_id"]))

                if entry["scenario"] == 1:
                    cycle, path, timestamp, user_hint, actions = get_data(user)
                    await Magic(self).penalize(user, cycle, points=20)

                await user.send(entry["report"])

    async def clear_secrets(self):
        for entry in books.find({}, {"_id": 0, "eeylops-owl-emporium": 1, "ollivanders": 1, "gringotts-bank": 1}):
            for secret in entry:
                for key in entry[secret]:
                    if key == "id":
                        channel = self.client.get_channel(int(entry[secret][key]))
                        if channel is not None:
                            await channel.delete()

    async def clock_update(self):
        time = get_time().strftime("%H:%M EST | %a")
        hour_minute = datetime.now(tz=tz_target).strftime("%H:%M")
        minute = datetime.now(tz=tz_target).strftime("%M")
        hour_24 = int(datetime.now(tz=tz_target).strftime("%H"))
        hour_12 = datetime.now(tz=tz_target).strftime("%I")

        if status == "None":
            weather1 = weather.find_one({"weather1": {"$type": "string"}}, {"weather1": 1})["weather1"]
            weather2 = weather.find_one({"weather2": {"$type": "string"}}, {"weather2": 1})["weather2"]

            # noinspection PyShadowingNames
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

            if minute == "00":
                weather1, weather2 = generate_weather(hour_24)
                await self.penalty_hour()
                await self.actions_reset()
                await self.clear_secrets()
                await self.send_off_report()
                await self.send_off_complete()

            if hour_minute == "00:00":
                spell_spam = self.client.get_channel(417507997846339585)
                await self.owls_restock()
                await Admin(self).reset_daily(spell_spam)
                await Admin(self).reset_boss(spell_spam)

            for clock_channel in clock_channels:
                clock = self.client.get_channel(int(clock_channel))

                def get_emoji(hours, minutes):
                    if int(minutes) >= 30:
                        emoji_clock_index = int(hours) * 2 + 1
                    else:
                        emoji_clock_index = int(hours) * 2
                    emoji_clock = list_clock[int(emoji_clock_index)]
                    return emoji_clock

                if clock_channel == "584975951788638228":
                    name = f"{get_emoji(hour_12, minute)} {time} {weather1} {weather2}"
                else:
                    name = f"{get_emoji(hour_12, minute)} {time}"
                await clock.edit(name=name)

    @commands.command(aliases=["so"])
    @commands.cooldown(1, 900, commands.BucketType.guild)
    async def shoutout(self, ctx, *args):

        if len(args) == 0:
            embed = discord.Embed(color=0xffff80,
                                  description="Temporarily change the clock to a custom message.\n\nUse `;shoutout "
                                              "<duration: 1-10 min> <message: 25 character limit`")
            embed.set_thumbnail(url=self.client.user.avatar_url)
            await ctx.channel.send(embed=embed)
            self.client.get_command("shoutout").reset_cooldown(ctx)

        elif len(args) < 2:
            await ctx.channel.send("Lacks arguments. Check proper format first `;shoutout`")
            self.client.get_command("shoutout").reset_cooldown(ctx)

        elif abs(int(args[0])) > 10:
            await ctx.channel.send(f"Reduce your minutes by {abs(int(args[0])) - 10}")
            self.client.get_command("shoutout").reset_cooldown(ctx)

        elif len(" ".join(args[1::])) > 25:
            await ctx.channel.send(f"Reduce your message length by {len(' '.join(args[1::])) - 24}")
            self.client.get_command("shoutout").reset_cooldown(ctx)

        elif abs(int(args[0])) <= 10 and len(" ".join(args[1::])) <= 25:
            msg = " ".join(args[1::])
            clock_channel = books.find_one({"server": str(ctx.guild.id)}, {"clock": 1, "_id": 0})["clock"]
            clock = self.client.get_channel(int(clock_channel))

            def status_set(x):
                global status
                status = x

            status_set(msg)
            await clock.edit(name=msg)
            await ctx.channel.send(f"**Shoutout:** {msg} | **Countdown:** {abs(int(args[0]))} min")
            await asyncio.sleep(abs(int(args[0])) * 60 - 1)
            status_set("None")
            self.client.get_command("shoutout").reset_cooldown(ctx)


def setup(client):
    client.add_cog(Clock(client))
