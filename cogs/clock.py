"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import asyncio
from datetime import datetime

import discord
import pytz
from discord.ext import tasks, commands

from cogs.mongo.db import books

# Get the clock channels
clock_channels = []
for guild_clock in books.find({}, {"clock": 1, "_id": 0}):
    if guild_clock["clock"] != "":
        clock_channels.append(guild_clock["clock"])

# Timezone
tz_target = pytz.timezone("America/Atikokan")

# Global Variables
status = "None"
list_clock = ["", "", "", "🕐", "🕜", "🕑", "🕒", "🕞", "🕓", "🕓", "🕔", "🕠", "🕕", "🕕", "🕖", "🕢", "🕗", "🕣",
              "🕘", "🕤", "🕙", "🕥", "🕚", "🕦", "🕛", "🕧"]


def get_time():
    time = datetime.now(tz=tz_target)
    return time


# noinspection PyCallingNonCallable,PyShadowingNames
class Clock(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        self.clock_update.start()

    @tasks.loop(seconds=30)
    async def clock_update(self):

        if status == "None":
            hour = datetime.now(tz=tz_target).strftime("%I")
            minute = datetime.now(tz=tz_target).strftime("%M")

            for clock_channel in clock_channels:
                clock = self.client.get_channel(int(clock_channel))

                def get_emoji(hour, minute):
                    if int(minute) >= 30:
                        emoji_clock_index = int(hour) * 2 + 1
                    else:
                        emoji_clock_index = int(hour) * 2
                    emoji_clock = list_clock[int(emoji_clock_index)]
                    return emoji_clock

                await clock.edit(name=f"{get_emoji(hour, minute)} {get_time().strftime('%H:%M EST | %a')}")

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
