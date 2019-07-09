"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
from datetime import datetime

import discord
import pytz
from discord.ext import commands

from cogs.mongo.db import library

# Timezone
tz_target = pytz.timezone("America/Atikokan")


def get_info(args):

    book = library.find_one({"section": int(args)}, {"_id": 0})
    content = book["content"]
    title = book["title"]
    description = book["description"]
    footer = book["footer"]
    author = book["footer"]
    content = book["content"]


    return content, title, description, text, image, field, thumbnail


class Library(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    @commands.is_owner()
    async def post_book(self, ctx, *args):
        
        content, title, description, title, text, image, field, thumbnail = get_info(args)
        embed = discord.Embed(color=0xaef706)


        await ctx.channel.send(content=content, embed=embed)


def setup(client):
    client.add_cog(Library(client))
