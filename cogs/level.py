"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
from discord.ext import commands

from cogs.mongo.db import users


async def add_experience(user, exp):
    # Maximum level check
    if users.find_one({"user_id": str(user.id)}, {"_id": 0, "level": 1})["level"] == 60:
        return
    else:
        users.update_one({"user_id": str(user.id)}, {"$inc": {"experience": exp}})


async def level_up(user, ctx):
    exp = users.find_one({"user_id": str(user.id)}, {"_id": 0, "experience": 1})["experience"]
    level = users.find_one({"user_id": str(user.id)}, {"_id": 0, "level": 1})["level"]
    level_end = int(exp ** 0.3)

    # Add one level
    if level < level_end:
        level_next = 5 * (round(((level + 2) ** 3.3333333333) / 5))
        users.update_one({"user_id": str(user.id)}, {"$set": {"level_exp_next": level_next}})
        users.update_one({"user_id": str(user.id)},
                         {"$inc": {"jades": 150, "amulets": 10, "coins": 100000, "level": level_end}})

        # Add emoji during levelup
        await ctx.add_reaction("⤴")


async def create_user(user):
    if users.find_one({"user_id": str(user.id)}, {"_id": 0}) is None:
        profile = {"user_id": str(user.id), "experience": 0, "level": 1, "level_exp_next": 5, "amulets": 10,
                   "amulets_spent": 0, "SP": 0, "SSR": 0, "SR": 0, "R": 0, "jades": 0, "coins": 0, "medals": 0,
                   "realm_ticket": 0, "honor": 0, "talisman": 0, "friendship": 0, "guild_medal": 0, "shikigami": []}

        # Creates a profile
        users.insert_one(profile)


class Level(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await create_user(member)

    @commands.Cog.listener()
    async def on_message(self, ctx):
        # Ignore myself
        if ctx.author == self.client.user:
            return

        # Ignore other bots
        elif ctx.author.bot is True:
            return

        # Perform add experience
        await create_user(ctx.author)
        await add_experience(ctx.author, 5)
        await level_up(ctx.author, ctx)


def setup(client):
    client.add_cog(Level(client))
