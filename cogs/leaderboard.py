"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import asyncio

import discord
from discord.ext import commands

from cogs.mongo.db import users, friendship, streak
from cogs.startup import emoji_f, emoji_a, emoji_m


class Leaderboard(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(aliases=["leaderboard", "lb"])
    async def leaderboard_show(self, ctx, *, args):

        if args.lower() in ["ssr"]:
            await self.leaderboard_post_ssr(ctx)

        elif args.lower() in ["sr"]:
            await self.leaderboard_post_sr(ctx)

        elif args.lower() in ["medal", "medals"]:
            await self.leaderboard_post_medals(ctx)

        elif args.lower() in ["amulet", "amulets"]:
            await self.leaderboard_post_amulet(ctx)

        elif args.lower() in ["friendship", "fp"]:
            await self.leaderboard_friendship(ctx)

        elif args.lower() in ["ship", "ships"]:
            await self.leaderboard_post_ship(ctx)

        elif args.lower() in ["streak", "ssrstreak"]:
            await self.leaderboard_post_streak(ctx)

        elif args.lower() in ["level"]:
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

        formatted_list = []
        for user in ssr_board2:
            formatted_list.append("{}".format(f"🔸{user[0]}, x{user[1]}\n"))

        title = "🏆 SSR LeaderBoard"
        await self.leaderboard_paginate(title, ctx, formatted_list)

    async def leaderboard_post_sr(self, ctx):

        sr_board1 = []
        query = users.find({}, {"_id": 0, "user_id": 1, "SR": 1})

        for user in query:
            try:
                member_name = self.client.get_user(int(user["user_id"])).display_name
                sr_board1.append((member_name, user["SR"]))
            except AttributeError:
                continue

        sr_board2 = sorted(sr_board1, key=lambda x: x[1], reverse=True)

        formatted_list = []
        for user in sr_board2:
            formatted_list.append("{}".format(f"🔸{user[0]}, x{user[1]}\n"))

        title = "🏆 SR LeaderBoard"
        await self.leaderboard_paginate(title, ctx, formatted_list)

    async def leaderboard_paginate(self, title, ctx, formatted_list):

        embed = discord.Embed(
            color=ctx.author.colour, title=title,
            description="".join(formatted_list[0:20])
        )
        embed.set_footer(text="Page: 1")
        msg = await ctx.channel.send(embed=embed)
        await msg.add_reaction("⬅")
        await msg.add_reaction("➡")

        def check(r, u):
            return u != self.client.user and r.message.id == msg.id

        def create_embed(page_new, query_list, color):
            end = page * 20
            start = end - 20
            description = "".join(query_list[start:end])
            embed_new = discord.Embed(
                color=color,
                title=title,
                description=f"{description}"
            )
            embed_new.set_footer(text=f"Page: {page_new}")
            return embed_new

        page = 1
        while True:
            try:
                timeout = 60
                reaction, user = await self.client.wait_for("reaction_add", timeout=timeout, check=check)
                if str(reaction.emoji) == "➡":
                    page += 1
                elif str(reaction.emoji) == "⬅":
                    page -= 1
                if page < 1:
                    page = 1
                await msg.edit(embed=create_embed(page, formatted_list, ctx.author.colour))
            except asyncio.TimeoutError:
                return False

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

        formatted_list = []
        for user in medal_board2:
            formatted_list.append("{}".format(f"🔸{user[0]}, x{user[1]}\n"))

        title = f"{emoji_m} Medal LeaderBoard"
        await self.leaderboard_paginate(title, ctx, formatted_list)

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
        formatted_list = []

        for user in level_board2:
            formatted_list.append("{}".format(f"🔸{user[0]}, x{user[1]}\n"))

        title = "⤴ Level LeaderBoard"
        await self.leaderboard_paginate(title, ctx, formatted_list)

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
        formatted_list = []

        for user in amulet_board2:
            formatted_list.append("{}".format(f"🔸{user[0]}, x{user[1]}\n"))

        title = f"{emoji_a} Spender LeaderBoard"
        await self.leaderboard_paginate(title, ctx, formatted_list)

    async def leaderboard_friendship(self, ctx):

        fp_board1 = []
        query = users.find({}, {"_id": 0, "user_id": 1, "friendship": 1})

        for user in query:
            try:
                member_name = self.client.get_user(int(user["user_id"])).display_name
                fp_board1.append((member_name, user["friendship"]))

            except AttributeError:
                continue

        fp_board2 = sorted(fp_board1, key=lambda x: x[1], reverse=True)
        formatted_list = []

        for user in fp_board2:
            formatted_list.append("{}".format(f"🔸{user[0]}, x{user[1]}\n"))

        title = f"{emoji_f} Friendship LeaderBoard"
        await self.leaderboard_paginate(title, ctx, formatted_list)

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
        formatted_list = []

        for ship in ship_board2:
            formatted_list.append("{}".format(f"🔸{ship[0]}, x{ship[4]}{emoji_f}\n"))

        title = "🚢 Ships LeaderBoard"
        await self.leaderboard_paginate(title, ctx, formatted_list)

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
        formatted_list = []

        for user in streakboard2:
            formatted_list.append("{}".format(f"🔸{user[0]}, x{user[1]}{emoji_a}\n"))

        title = "NO SSR Streak LeaderBoard"
        await self.leaderboard_paginate(title, ctx, formatted_list)


def setup(client):
    client.add_cog(Leaderboard(client))
