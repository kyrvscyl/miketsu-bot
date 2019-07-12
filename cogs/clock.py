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
from cogs.magic import get_data, get_dictionary
from cogs.mongo.db import books, weather, sendoff, quests, owls, daily
from cogs.frame import frame_starlight, frame_blazing
from cogs.admin import Admin, reset_boss
from cogs.automation import Events

# Get the clock channels
clock_channels = []
for guild_clock in books.find({}, {"clock": 1, "_id": 0}):
    if guild_clock["clock"] != "":
        clock_channels.append(guild_clock["clock"])

# Timezone
tz_target = pytz.timezone("America/Atikokan")

# Global Variables
status = "None"
list_clock = ["",  # 0
              "",  # 1
              "",  # 2
              "🕐",  # 3
              "🕜",  # 4
              "🕑",  # 5
              "🕝",  # 6
              "🕒",  # 7
              "🕞",  # 8
              "🕓",  # 9
              "🕟",  # 10
              "🕔",  # 11
              "🕠",  # 12
              "🕕",  # 13
              "🕡",  # 14
              "🕖",  # 15
              "🕢",  # 16
              "🕗",  # 17
              "🕣",  # 18
              "🕘",  # 19
              "🕤",  # 20
              "🕙",  # 21
              "🕥",  # 22
              "🕚",  # 23
              "🕦",  # 24
              "🕛",  # 25
              "🕧"]  # 26


def get_time():
    time = datetime.now(tz=tz_target)
    return time


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


def get_emoji(hours, minutes):
    if int(minutes) >= 30:
        emoji_clock_index = (int(hours) * 2) + 2

    else:
        emoji_clock_index = (int(hours) * 2) + 1

    emoji_clock = list_clock[emoji_clock_index]
    return emoji_clock


# noinspection PyCallingNonCallable
async def penalty_hour():
    quests.update_many({"quest1.status": "ongoing"}, {"$inc": {"quest1.$.score": -2}})


async def actions_reset():
    quests.update_many({"quest1.status": "ongoing"}, {"$set": {"quest1.$.actions": 0}})


async def reset_library():

    for entry in daily.find({"key": "library"}, {"key": 0, "_id": 0}):
        for user_id in entry:
            daily.update_one({"key": "library"}, {"$set": {f"{user_id}": 0}})


class Clock(commands.Cog):

    def __init__(self, client):
        self.client = client

    async def logging(self, msg):
        channel = self.client.get_channel(592270990894170112)
        date_time = datetime.now(tz=tz_target).strftime("%Y-%b-%d %HH")
        await channel.send(f"[{date_time}] " + msg)

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
                await self.client.get_user(180717337475809281).send("The Clock has Stopped.")
                break

    @commands.command(aliases=["transform"])
    @commands.is_owner()
    async def transformation_trigger(self, ctx, *, args):
        await ctx.message.delete()

        if args.lower() == "start":
            await self.transformation_start()

        elif args.lower() == "end":
            await self.transformation_end()

    async def transformation_end(self):

        for entry in books.find({}, {"_id": 0, "server": 1}):

            try:
                server = self.client.get_guild(int(entry["server"]))
                reference_role = discord.utils.get(server.roles, name="Head")

                no_maj_role = discord.utils.get(server.roles, name="No-Maj")
                await asyncio.sleep(1)
                await no_maj_role.edit(position=reference_role.position - 1)

                patronus_role = discord.utils.get(server.roles, name="Patronus")
                await asyncio.sleep(1)
                await patronus_role.edit(position=reference_role.position - 1)

                auror_role = discord.utils.get(server.roles, name="Auror")
                await asyncio.sleep(1)
                await auror_role.edit(position=reference_role.position - 1)

                dementor_role = discord.utils.get(server.roles, name="Dementor")
                await asyncio.sleep(1)
                await dementor_role.edit(position=reference_role.position - 1)

                junior_role = discord.utils.get(server.roles, name="Junior Duel Champion")
                await asyncio.sleep(1)
                await junior_role.edit(position=reference_role.position - 1)

                senior_role = discord.utils.get(server.roles, name="Senior Duel Champion")
                await asyncio.sleep(1)
                await senior_role.edit(position=reference_role.position - 1)

            except AttributeError:
                return

    async def transformation_start(self):

        for entry in books.find({}, {"_id": 0, "server": 1}):

            try:
                server = self.client.get_guild(int(entry["server"]))
                reference_role = discord.utils.get(server.roles, name="🏆")

                no_maj_role = discord.utils.get(server.roles, name="No-Maj")
                await asyncio.sleep(1)
                await no_maj_role.edit(position=reference_role.position - 1)

                patronus_role = discord.utils.get(server.roles, name="Patronus")
                await asyncio.sleep(1)
                await patronus_role.edit(position=reference_role.position - 1)

                auror_role = discord.utils.get(server.roles, name="Auror")
                await asyncio.sleep(1)
                await auror_role.edit(position=reference_role.position - 1)

                dementor_role = discord.utils.get(server.roles, name="Dementor")
                await asyncio.sleep(1)
                await dementor_role.edit(position=reference_role.position - 1)

                junior_role = discord.utils.get(server.roles, name="Junior Duel Champion")
                await asyncio.sleep(1)
                await junior_role.edit(position=reference_role.position - 1)

                senior_role = discord.utils.get(server.roles, name="Senior Duel Champion")
                await asyncio.sleep(1)
                await senior_role.edit(position=reference_role.position - 1)

            except AttributeError:
                return

    async def owls_restock(self):
        owls.update_many({}, {"$set": {"purchaser": "None"}})
        await self.logging("Restocking emporium with all owls")

    # noinspection PyUnusedLocal
    @commands.command()
    @commands.is_owner()
    async def complete(self, ctx):
        await self.send_off_report()
        await asyncio.sleep(5)
        await self.send_off_complete()

    async def send_off_complete(self):
        for entry in sendoff.find({"timestamp_complete": get_time().strftime("%Y-%b-%d %HH")}, {"_id": 0}):
            user = self.client.get_user(int(entry["user_id"]))
            cycle, path, timestamp, user_hint, actions, purchase = get_data(user)

            if entry["scenario"] == 2:
                async with user.typing():
                    responses = get_dictionary("send_off")["complete"]

                    if path != "path0":
                        await Magic(self.client).update_path(user, cycle, path_new="path3")

                    await user.send(responses[0])
                    await asyncio.sleep(4)
                    await user.send(responses[1])
                    await asyncio.sleep(4)
                    msg = await user.send(responses[2].format(entry['type'].capitalize()))
                    await msg.add_reaction("✉")

            elif entry["scenario"] == 1:
                user = self.client.get_user(int(entry["user_id"]))
                msg = f"Your {entry['type']} has fully recovered"
                await Magic(self.client).update_path(user, cycle, path_new="path20")
                await user.send(msg)

            sendoff.delete_one({"user_id": entry["user_id"]})

    async def send_off_report(self):
        for entry in sendoff.find({"timestamp_update": {"$exists": True}}, {"_id": 0}):
            if entry["timestamp_update"] == get_time().strftime("%Y-%b-%d %HH"):
                user = self.client.get_user(int(entry["user_id"]))

                if entry["scenario"] == 1:
                    cycle, path, timestamp, user_hint, actions, purchase = get_data(user)
                    await Magic(self.client).penalize(user, cycle, points=20)

                description = entry["report"]
                embed = discord.Embed(
                    color=0xffffff,
                    title="Owl Report",
                    description=description
                )
                embed.set_footer(text=f"{entry['timestamp_update']}")
                await user.send(embed=embed)
                await asyncio.sleep(1)

    async def reset_purchase(self):
        quests.update_many({"quest1.purchase": False}, {"$set": {"quest1.$.purchase": True}})
        await self.logging("Resetting everyone's ability to purchase owls to True")

    async def clear_secrets(self):

        query = books.find({}, {
            "_id": 0, "eeylops-owl-emporium": 1, "ollivanders": 1, "gringotts-bank": 1
        })

        for entry in query:
            for secret in entry:
                for key in entry[secret]:

                    if key == "id":
                        channel = self.client.get_channel(int(entry[secret][key]))

                        if channel is not None:
                            try:
                                await channel.delete()

                            except discord.errors.Forbidden:
                                return

    async def clock_update(self):

        time = get_time().strftime("%H:%M EST | %a")
        hour_minute = datetime.now(tz=tz_target).strftime("%H:%M")
        minute = datetime.now(tz=tz_target).strftime("%M")
        hour_24 = int(datetime.now(tz=tz_target).strftime("%H"))
        hour_12 = datetime.now(tz=tz_target).strftime("%I")

        if status == "None":
            weather1 = weather.find_one({"weather1": {"$type": "string"}}, {"weather1": 1})["weather1"]
            weather2 = weather.find_one({"weather2": {"$type": "string"}}, {"weather2": 1})["weather2"]

            # Reset items during every after hour
            if minute == "00":
                weather1, weather2 = generate_weather(hour_24)

                await penalty_hour()
                await actions_reset()
                await self.reset_purchase()
                await self.clear_secrets()
                await self.send_off_report()
                await self.send_off_complete()
                await Events(self.client).reset_prefects()

            if hour_minute in ["02:00", "08:00", "14:00", "20:00"]:
                await self.owls_restock()

            if hour_minute == "00:00":
                server = self.client.get_guild(412057028887052288)
                spell_spam = self.client.get_channel(417507997846339585)

                await Admin(self.client).reset_daily(spell_spam)
                await reset_boss(spell_spam)
                await reset_library()
                await frame_starlight(server, spell_spam)
                await frame_blazing(server, spell_spam)

            if hour_minute == "19:00":
                await self.transformation_start()

            elif hour_minute == "06:00":
                await self.transformation_end()

            for clock_channel in clock_channels:
                clock = self.client.get_channel(int(clock_channel))

                if clock_channel == "584975951788638228":
                    name = f"{get_emoji(hour_12, minute)} {time} {weather1} {weather2}"

                else:
                    name = f"{get_emoji(hour_12, minute)} {time}"

                if clock is not None:
                    try:
                        await clock.edit(name=name)

                    except discord.errors.Forbidden:
                        return

    @commands.command(aliases=["so"])
    @commands.cooldown(1, 900, commands.BucketType.guild)
    async def shoutout(self, ctx, *args):

        if len(args) == 0:

            embed = discord.Embed(
                color=ctx.author.colour,
                description="Temporarily change the clock to a custom message.\n\n"
                            "Use `;shoutout <duration: 1-10 min> <message: 25 character limit`"
            )
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
