"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import asyncio

import discord
from discord.ext import commands

from cogs.mongo.db import users, friendship, streak
from cogs.startup import emoji_f, emoji_a, emoji_m


def post(page, embed1, embed2, embed3):
    if page == 1:
        return embed1
    elif page == 2:
        return embed2
    elif page == 3:
        return embed3
    elif page > 3:
        return embed1
    elif page < 1:
        return embed3


class Leaderboard(commands.Cog):

    def __init__(self, client):
        self.client = client


    @commands.command(aliases=["lb"])
    async def leaderboard(self, ctx, *args):

        try:
            if args[0].upper() == "SSR":
                await self.leaderboard_post_ssr(ctx)

            elif args[0] == "medal" or args[0] == "medals":
                await self.leaderboard_post_medals(ctx)

            elif args[0] == "amulet" or args[0] == "amulets":
                await self.leaderboard_post_amulet(ctx)

            elif args[0] == "friendship" or args[0] == "fp":
                await self.leaderboard_friendship(ctx)

            elif args[0] == "ship" or args[0] == "ships":
                await self.leaderboard_post_ship(ctx)

            elif args[0] == "streak":
                await self.leaderboard_post_streak(ctx)

            else:
                await self.leaderboard_post_level(ctx)

        except IndexError:
            await self.leaderboard_post_level(ctx)


    async def leaderboard_post_ssr(self, ctx):

        ssr_board1 = []
        query = users.find({}, {"_id": 0, "user_id": 1, "SSR": 1})

        for user in query:
            try:
                member_name = self.client.get_user(int(user["user_id"])).display_name
                ssr_board1.append((member_name, user["SSR"]))
            
            except AttributeError:
                continue
                
        ssr_board2 = sorted(ssr_board1, key=lambda x: x[1], reverse=True)

        description1 = ""
        description2 = ""
        description3 = ""

        for user in ssr_board2[0:10]:
            description1 += f"🔸{user[0]}, x{user[1]}\n"

        for user in ssr_board2[10:20]:
            description2 += f"🔸{user[0]}, x{user[1]}\n"

        for user in ssr_board2[20:30]:
            description3 += f"🔸{user[0]}, x{user[1]}\n"

        title = "🏆 SSR LeaderBoard"
        await self.paginate_embed(title, ctx, description1, description2, description3)


    async def leaderboard_post_medals(self, ctx):

        medal_board1 = []
        query = users.find({}, {"_id": 0, "user_id": 1, "medals": 1})

        for user in query:
            try:
                member_name = self.client.get_user(int(user["user_id"])).display_name
                medal_board1.append((member_name, user["medals"]))
            
            except AttributeError:
                continue

        medal_board2 = sorted(medal_board1, key=lambda x: x[1], reverse=True)

        description1 = ""
        description2 = ""
        description3 = ""

        for user in medal_board2[0:10]:
            description1 += f"🔸{user[0]}, x{user[1]}\n"

        for user in medal_board2[10:20]:
            description2 += f"🔸{user[0]}, x{user[1]}\n"

        for user in medal_board2[20:30]:
            description3 += f"🔸{user[0]}, x{user[1]}\n"

        title = f"{emoji_m} Medal LeaderBoard"
        await self.paginate_embed(title, ctx, description1, description2, description3)


    async def leaderboard_post_level(self, ctx):

        level_board1 = []
        query = users.find({}, {"_id": 0, "user_id": 1, "level": 1})

        for user in query:
            try:
                member_name = self.client.get_user(int(user["user_id"])).display_name
                level_board1.append((member_name, user["level"]))
            
            except AttributeError:
                continue

        level_board2 = sorted(level_board1, key=lambda x: x[1], reverse=True)

        description1 = ""
        description2 = ""
        description3 = ""

        for user in level_board2[0:10]:
            description1 += f"🔸{user[0]}, x{user[1]}\n"

        for user in level_board2[10:20]:
            description2 += f"🔸{user[0]}, x{user[1]}\n"

        for user in level_board2[20:30]:
            description3 += f"🔸{user[0]}, x{user[1]}\n"

        title = "⤴ Level LeaderBoard"
        await self.paginate_embed(title, ctx, description1, description2, description3)


    async def leaderboard_post_amulet(self, ctx):

        amulet_board1 = []
        query = users.find({}, {"_id": 0, "user_id": 1, "amulets_spent": 1})

        for user in query:
            try:
                member_name = self.client.get_user(int(user["user_id"])).display_name
                amulet_board1.append((member_name, user["amulets_spent"]))

            except AttributeError:
                continue

        amulet_board2 = sorted(amulet_board1, key=lambda x: x[1], reverse=True)

        description1 = ""
        description2 = ""
        description3 = ""

        for user in amulet_board2[0:10]:
            description1 += f"🔸{user[0]}, x{user[1]}\n"

        for user in amulet_board2[10:20]:
            description2 += f"🔸{user[0]}, x{user[1]}\n"

        for user in amulet_board2[20:30]:
            description3 += f"🔸{user[0]}, x{user[1]}\n"

        title = f"{emoji_a} Spender LeaderBoard"
        await self.paginate_embed(title, ctx, description1, description2, description3)


    async def leaderboard_friendship(self, ctx):

        fp_board1 = []
        query = users.find({}, {"_id": 0, "user_id": 1, "friendship": 1})

        for user in query:
            try:
                member_name = self.client.get_user(int(user["user_id"])).display_name
                fp_board1.append((member_name, user["friendship"]))

            except AttributeError:
                continue

        fp_board12 = sorted(fp_board1, key=lambda x: x[1], reverse=True)

        description1 = ""
        description2 = ""
        description3 = ""

        for user in fp_board12[0:10]:
            description1 += f"🔸{user[0]}, x{user[1]}\n"

        for user in fp_board12[10:20]:
            description2 += f"🔸{user[0]}, x{user[1]}\n"

        for user in fp_board12[20:30]:
            description3 += f"🔸{user[0]}, x{user[1]}\n"

        title = f"{emoji_f} Friendship LeaderBoard"
        await self.paginate_embed(title, ctx, description1, description2, description3)


    async def leaderboard_post_ship(self, ctx):

        ship_board1 = []
        query = friendship.find({}, {
            "_id": 0,
            "points": 1,
            "shipper1": 1,
            "shipper2": 1,
            "ship_name": 1,
            "level": 1
        })

        for ship in query:
            ship_board1.append((ship["ship_name"], ship["shipper1"], ship["shipper2"], ship["level"], ship["points"]))

        ship_board2 = sorted(ship_board1, key=lambda x: x[4], reverse=True)

        description1 = ""
        description2 = ""
        description3 = ""

        for ship in ship_board2[0:10]:
            description1 += f"🔸{ship[0]}, x{ship[4]}{emoji_f}\n"

        for ship in ship_board2[10:20]:
            description2 += f"🔸{ship[0]}, x{ship[4]}{emoji_f}\n"

        for ship in ship_board2[20:30]:
            description3 += f"🔸{ship[0]}, x{ship[4]}{emoji_f}\n"

        title = "🚢 Ships LeaderBoard"
        await self.paginate_embed(title, ctx, description1, description2, description3)


    async def leaderboard_post_streak(self, ctx):

        streakboard1 = []
        query = streak.find({}, {"_id": 0, "user_id": 1, "SSR_current": 1})

        for user in query:
            try:
                member_name = self.client.get_user(int(user["user_id"])).display_name
                streakboard1.append((member_name, user["SSR_current"]))
            
            except AttributeError:
                continue
            
        streakboard2 = sorted(streakboard1, key=lambda x: x[1], reverse=True)

        description1 = ""
        description2 = ""
        description3 = ""

        for user in streakboard2[0:10]:
            description1 += f"🔸{user[0]}, x{user[1]}{emoji_a}\n"

        for user in streakboard2[10:20]:
            description2 += f"🔸{user[0]}, x{user[1]}{emoji_a}\n"

        for user in streakboard2[20:30]:
            description3 += f"🔸{user[0]}, x{user[1]}{emoji_a}\n"

        title = "NO SSR Streak LeaderBoard"
        await self.paginate_embed(title, ctx, description1, description2, description3)


    async def paginate_embed(self, title, ctx, description1, description2, description3):

        embed1 = discord.Embed(color=ctx.author.colour, title=title, description=description1)
        embed1.set_footer(text="page 1")

        embed2 = discord.Embed(color=ctx.author.colour, title=title, description=description2)
        embed2.set_footer(text="page 2")

        embed3 = discord.Embed(color=ctx.author.colour, title=title, description=description3)
        embed3.set_footer(text="page 3")

        msg = await ctx.channel.send(embed=embed1)

        await msg.add_reaction("⬅")
        await msg.add_reaction("➡")

        def check(r, u):
            return u != self.client.user and r.message.id == msg.id

        page = 1
        while True:
            try:
                timeout = 60
                reaction, user = await self.client.wait_for("reaction_add", timeout=timeout, check=check)

                if str(reaction.emoji) == "➡":
                    page += 1
                elif str(reaction.emoji) == "⬅":
                    page -= 1
                await msg.edit(embed=post(page, embed1, embed2, embed3))

            except asyncio.TimeoutError:
                return False


def setup(client):
    client.add_cog(Leaderboard(client))
