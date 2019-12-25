"""
Level Module
Miketsu, 2019
"""
from datetime import datetime

import discord
import pytz
from discord.ext import commands

from cogs.mongo.database import get_collections

# Collections
users = get_collections("users")
config = get_collections("config")
logs = get_collections("logs")


class Level(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.prefix = self.client.command_prefix

        self.emojis = config.find_one({"dict": 1}, {"_id": 0, "emojis": 1})["emojis"]

        self.e_x = self.emojis["x"]

        self.timezone = config.find_one({"var": 1}, {"_id": 0, "timezone": 1})["timezone"]

    def get_time(self):
        return datetime.now(tz=pytz.timezone(self.timezone))

    async def level_add_experience(self, user, exp):

        if users.find_one({"user_id": str(user.id)}, {"_id": 0, "level": 1})["level"] == 60:
            return
        else:
            users.update_one({"user_id": str(user.id)}, {"$inc": {"experience": exp}})

    async def level_add_level(self, user, ctx):

        profile = users.find_one({"user_id": str(user.id)}, {"_id": 0, "experience": 1, "level": 1})

        exp = profile["experience"]
        level = profile["level"]
        level_end = int(exp ** 0.3556302501)

        if level > level_end:
            users.update_one({"user_id": str(user.id)}, {"$set": {"level": level_end}})

        if level < level_end:

            level_next = 5 * (round(((level + 2) ** 2.811909279) / 5))
            jades, amulets, coins = 150, 10, 100000

            users.update_one({
                "user_id": str(user.id)}, {
                "$set": {
                    "level_exp_next": level_next,
                    "level": level_end
                },
                "$inc": {
                    "jades": jades, "amulets": amulets, "coins": coins
                }
            })

            await self.logs_add_line("jades", jades, user.id)
            await self.logs_add_line("amulets", amulets, user.id)
            await self.logs_add_line("coins", coins, user.id)

            if level_end == 60:

                jades, amulets, coins = 4000, 50, 1000000

                users.update_one({
                    "user_id": str(user.id)}, {
                    "$set": {
                        "level_exp_next": 100000,
                        "level": 60
                    },
                    "$inc": {
                        "jades": jades, "amulets": amulets, "coins": coins
                    }
                })

                await self.logs_add_line("jades", jades, user.id)
                await self.logs_add_line("amulets", amulets, user.id)
                await self.logs_add_line("coins", coins, user.id)

            try:
                await ctx.add_reaction(self.e_x)
            except discord.errors.HTTPException:
                pass

    async def level_create_user(self, user):

        if users.find_one({"user_id": str(user.id)}, {"_id": 0}) is None:
            profile = {
                "user_id": str(user.id),
                "experience": 0,
                "level": 1,
                "level_exp_next": 5,
                "amulets": 10,
                "amulets_spent": 0,
                "amulets_b": 0,
                "amulets_spent_b": 0,
                "SP": 0,
                "SSR": 0,
                "SR": 0,
                "R": 0,
                "N": 0,
                "SSN": 0,
                "sushi": 100,
                "jades": 0,
                "coins": 0,
                "medals": 0,
                "realm_ticket": 3,
                "encounter_ticket": 0,
                "parade_tickets": 0,
                "honor": 0,
                "talisman": 0,
                "guild_medal": 0,
                "display": None,
                "shikigami": [],
                "friendship": 0,
                "friendship_pass": 0,
                "prayers": 3,
                "daily": False,
                "weekly": False,
                "wish": True,
                "nether_pass": True,
                "raided_count": 0,
                "stickers": 0,
                "exploration": 1,
                "achievements_count": 0,
                "achievements": [],
                "cards": [],
                "bento": 0,
            }
            users.insert_one(profile)

    async def logs_add_line(self, currency, amount, user_id):
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
    async def on_message(self, message):

        if message.author == self.client.user:
            return

        elif message.author.bot is True:
            return

        await self.level_create_user(message.author)
        await self.level_add_experience(message.author, 5)
        await self.level_add_level(message.author, message)


def setup(client):
    client.add_cog(Level(client))
