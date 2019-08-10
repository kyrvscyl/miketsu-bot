"""
Clock Module
Miketsu, 2019
"""
from datetime import datetime

import discord
import pytz
from discord.ext import commands

from cogs.mongo.database import get_collections
from cogs.startup import primary_id, embed_color

# Collections
books = get_collections("bukkuman", "books")
reminders = get_collections("bukkuman", "reminders")


def get_time_est():
    tz_target = pytz.timezone("America/Atikokan")
    return datetime.now(tz=tz_target)


class Reminder(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(aliases=["test"])
    @commands.is_owner()
    async def manual_reminder(self, ctx):
        date_time = "Aug 07, 2019 11:00"
        await self.reminders_bidding_process(date_time)

    async def reminders_bidding_process(self, date_time):

        request = books.find_one({"server": str(primary_id)}, {"_id": 0})
        common_room_channel = self.client.get_channel(int(request["channels"]["headlines"]))
        reminders_date_list = reminders.find_one({"event": "bidding"}, {"_id": 1, "dates": 1})["dates"]
        slot_role = request["roles"]["big_spenders"]

        content = f"<@&{slot_role}>"
        embed = discord.Embed(
            color=embed_color,
            title="A new round of showdown bidding has started!",
            timestamp=datetime.utcfromtimestamp(datetime.timestamp(datetime.now()))
        )
        embed.set_footer(text=f"Round {reminders_date_list.index(date_time) + 1} of {len(reminders_date_list)}")

        msg = await common_room_channel.send(content=content, embed=embed)
        await msg.add_reaction("🔵")
        await msg.add_reaction("🔴")


def setup(client):
    client.add_cog(Reminder(client))
