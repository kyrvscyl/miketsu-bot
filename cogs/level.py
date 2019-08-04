"""
Level Module
Miketsu, 2019
"""

import discord
from discord.ext import commands

from cogs.mongo.db import get_collections

# Collections
users = get_collections("miketsu", "users")


async def add_experience(user, exp):
    if users.find_one({"user_id": str(user.id)}, {"_id": 0, "level": 1})["level"] == 60:
        return
    else:
        users.update_one({"user_id": str(user.id)}, {"$inc": {"experience": exp}})


async def level_up(user, ctx):
    profile = users.find_one({"user_id": str(user.id)}, {"_id": 0, "experience": 1, "level": 1})
    exp = profile["experience"]
    level = profile["level"]
    level_end = int(exp ** 0.3556302501)

    if level > level_end:
        users.update_one({"user_id": str(user.id)}, {"$set": {"level": level_end}})

    if level < level_end:
        level_next = 5 * (round(((level + 2) ** 2.811909279) / 5))
        users.update_one({
            "user_id": str(user.id)}, {
            "$set": {
                "level_exp_next": level_next,
                "level": level_end
            },
            "$inc": {
                "jades": 150, "amulets": 10, "coins": 100000
            }
        })
        if level_end == 60:
            users.update_one({
                "user_id": str(user.id)}, {
                "$set": {
                    "level_exp_next": 60,
                    "level": 60
                },
                "$inc": {
                    "jades": 4000, "amulets": 50, "coins": 1000000
                }
            })

        try:
            await ctx.add_reaction("⤴")
        except discord.errors.HTTPException:
            return


async def create_user(user):
    if users.find_one({"user_id": str(user.id)}, {"_id": 0}) is None:
        profile = {
            "user_id": str(user.id),
            "experience": 0,
            "level": 1,
            "level_exp_next": 5,
            "amulets": 10,
            "amulets_spent": 0,
            "SP": 0,
            "SSR": 0,
            "SR": 0,
            "R": 0,
            "jades": 0,
            "coins": 0,
            "medals": 0,
            "realm_ticket": 3,
            "honor": 0,
            "talisman": 0,
            "friendship": 0,
            "guild_medal": 0,
            "shikigami": [],
            "encounter_ticket": 0,
            "daily": False,
            "weekly": False,
            "raided_count": 0,
            "friendship_pass": 0,
            "display": "None",
            "prayers": 3
        }
        users.insert_one(profile)


class Level(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await create_user(member)

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author == self.client.user:
            return

        elif message.author.bot is True:
            return

        await create_user(message.author)
        await add_experience(message.author, 5)
        await level_up(message.author, message)


def setup(client):
    client.add_cog(Level(client))
