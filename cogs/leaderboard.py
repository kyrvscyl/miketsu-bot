"""
Leaderboard Module
Miketsu, 2019
"""

import asyncio
from datetime import datetime
from math import ceil

import discord
from discord.ext import commands

from cogs.mongo.database import get_collections
from cogs.startup import e_f, e_a, e_m, e_ssr, e_sr

# Collections
users = get_collections("miketsu", "users")
ships = get_collections("miketsu", "ships")
streak = get_collections("miketsu", "streak")


def get_timestamp():
    return datetime.utcfromtimestamp(datetime.timestamp(datetime.now()))


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
            await self.leaderboard_post_friendship(ctx)

        elif args.lower() in ["ship", "ships"]:
            await self.leaderboard_post_ships(ctx)

        elif args.lower() in ["streak", "ssrstreak"]:
            await self.leaderboard_post_streak(ctx)

        elif args.lower() in ["level"]:
            await self.leaderboard_post_level(ctx)

        elif args.lower() in ["achievements", "frames"]:
            await self.leaderboard_post_achievements(ctx)

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

        title = f"{e_ssr} LeaderBoard"
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

        title = f"{e_sr} LeaderBoard"
        await self.leaderboard_paginate(title, ctx, formatted_list)

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
            formatted_list.append("{}".format(f"🔸{user[0]}, x{user[1]:,d}\n"))

        title = f"{e_m} Medal LeaderBoard"
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

        title = f"{e_a} Spender LeaderBoard"
        await self.leaderboard_paginate(title, ctx, formatted_list)

    async def leaderboard_post_friendship(self, ctx):

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

        title = f"{e_f} Friendship LeaderBoard"
        await self.leaderboard_paginate(title, ctx, formatted_list)

    async def leaderboard_post_ships(self, ctx):

        ship_board1 = []
        query = ships.find({}, {
            "_id": 0, "points": 1, "shipper1": 1, "shipper2": 1, "ship_name": 1, "level": 1
        })

        for ship in query:
            ship_board1.append((ship["ship_name"], ship["shipper1"], ship["shipper2"], ship["level"], ship["points"]))

        ship_board2 = sorted(ship_board1, key=lambda x: x[4], reverse=True)
        formatted_list = []

        for ship in ship_board2:
            formatted_list.append("{}".format(f"🔸{ship[0]}, x{ship[4]}{e_f}\n"))

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
            formatted_list.append("{}".format(f"🔸{user[0]}, x{user[1]}{e_a}\n"))

        title = f"No {e_ssr} Summon Streak LeaderBoard"
        await self.leaderboard_paginate(title, ctx, formatted_list)

    async def leaderboard_post_achievements(self, ctx):

        frame_board1 = []
        query = users.find({}, {"_id": 0, "user_id": 1, "achievements": 1})

        for user in query:
            try:
                member_name = self.client.get_user(int(user["user_id"])).display_name
                frame_board1.append((member_name, len(user["achievements"])))
            except AttributeError:
                continue

        frame_board2 = sorted(frame_board1, key=lambda x: x[1], reverse=True)
        formatted_list = []

        for user in frame_board2:
            formatted_list.append("{}".format(f"🔸{user[0]}, x{user[1]}\n"))

        title = "<:blazingsun:606711888541384714> Frames LeaderBoard"
        await self.leaderboard_paginate(title, ctx, formatted_list)

    async def leaderboard_paginate(self, title, ctx, formatted_list):

        page = 1
        max_lines = 15
        page_total = ceil(len(formatted_list) / max_lines)

        def create_new_embed_page(page_new):
            end = page * max_lines
            start = end - max_lines
            description = "".join(formatted_list[start:end])

            embed_new = discord.Embed(
                color=ctx.author.colour,
                title=title,
                description=f"{description}",
                timestamp=get_timestamp()
            )
            embed_new.set_footer(text=f"Page: {page_new} of {page_total}")
            return embed_new

        msg = await ctx.channel.send(embed=create_new_embed_page(page))
        await msg.add_reaction("⬅")
        await msg.add_reaction("➡")

        def check(r, u):
            return u != self.client.user and r.message.id == msg.id

        while True:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=60, check=check)
            except asyncio.TimeoutError:
                break
            else:
                if str(reaction.emoji) == "➡":
                    page += 1
                elif str(reaction.emoji) == "⬅":
                    page -= 1
                if page == 0:
                    page = page_total
                elif page > page_total:
                    page = 1
                await msg.edit(embed=create_new_embed_page(page))


def setup(client):
    client.add_cog(Leaderboard(client))
