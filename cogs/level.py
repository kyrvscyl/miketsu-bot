"""
Level Module
Miketsu, 2020
"""

from discord.ext import commands

from cogs.ext.initialize import *


class Level(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.prefix = self.client.command_prefix

    async def level_add_experience(self, user, experience):

        if users.find_one({"user_id": str(user.id)}, {"_id": 0, "level": 1})["level"] == 60:
            return
        else:
            users.update_one({"user_id": str(user.id)}, {"$inc": {"experience": experience}})

    async def level_add_level(self, user, message):

        query = users.find_one({"user_id": str(user.id)}, {"_id": 0, "experience": 1, "level": 1})

        experience, level = query["experience"], query["level"]
        level_end = int(experience ** 0.3556302501)

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

            await perform_add_log("jades", jades, user.id)
            await perform_add_log("amulets", amulets, user.id)
            await perform_add_log("coins", coins, user.id)

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

                await perform_add_log("jades", jades, user.id)
                await perform_add_log("amulets", amulets, user.id)
                await perform_add_log("coins", coins, user.id)

            await process_msg_reaction_add(message, e_x)

    async def level_create_user(self, user):

        if users.find_one({"user_id": str(user.id)}, {"_id": 0}) is None:
            users.insert_one({
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
                "souls": {},
                "scales": 0,
                "scales_rev": 0,
                "souls_unlocked": 1
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
