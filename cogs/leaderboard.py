"""
Leaderboard Module
Miketsu, 2020
"""


import asyncio
from math import ceil

from discord.ext import commands

from cogs.ext.initialize import *


class Leaderboard(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.prefix = self.client.command_prefix

    @commands.command(aliases=["leaderboard", "lb"])
    @commands.guild_only()
    async def leaderboard_show(self, ctx, *, args):

        if args.lower() in ["ssr"]:
            query = users.find({}, {"_id": 0, "user_id": 1, "SSR": 1})
            await self.leaderboard_post_record_users(ctx, query, f"{e_2} LeaderBoard", "SSR")

        elif args.lower() in ["sp"]:
            query = users.find({}, {"_id": 0, "user_id": 1, "SP": 1})
            await self.leaderboard_post_record_users(ctx, query, f"{e_1} LeaderBoard", "SP")

        elif args.lower() in ["sr"]:
            query = users.find({}, {"_id": 0, "user_id": 1, "SR": 1})
            await self.leaderboard_post_record_users(ctx, query, f"{e_3} LeaderBoard", "SR")

        elif args.lower() in ["ssn"]:
            query = users.find({}, {"_id": 0, "user_id": 1, "SSN": 1})
            await self.leaderboard_post_record_users(ctx, query, f"{e_6} LeaderBoard", "SSN")

        elif args.lower() in ["medal", "medals"]:
            query = users.find({}, {"_id": 0, "user_id": 1, "medals": 1})
            await self.leaderboard_post_record_users(ctx, query, f"{e_m} Medal LeaderBoard", "medals")

        elif args.lower() in ["amulet", "amulets"]:
            query = users.find({}, {"_id": 0, "user_id": 1, "amulets_spent": 1})
            await self.leaderboard_post_record_users(ctx, query, f"{e_a} Spender LeaderBoard", "amulets_spent")

        elif args.lower() in ["friendship", "fp"]:
            query = users.find({}, {"_id": 0, "user_id": 1, "friendship": 1})
            await self.leaderboard_post_record_users(ctx, query, f"{e_f} Friendship LeaderBoard", "friendship")

        elif args.lower() in ["streak", "ssrstreak"]:
            query = streaks.find({}, {"_id": 0, "user_id": 1, "SSR_current": 1})
            await self.leaderboard_post_record_users(
                ctx, query, f"No {e_2} Summon Streak LeaderBoard", "SSR_current"
            )

        elif args.lower() in ["level"]:
            query = users.find({}, {"_id": 0, "user_id": 1, "level": 1})
            await self.leaderboard_post_record_users(ctx, query, f"{e_x} Level LeaderBoard", "level")

        elif args.lower() in ["achievements", "frames"]:
            query = users.find({}, {"_id": 0, "user_id": 1, "achievements": 1})
            await self.leaderboard_post_record_users(ctx, query, "🖼 Frames LeaderBoard", "achievements")

        elif args.lower() in ["ship", "ships"]:
            query = ships.find({}, {"_id": 0, "points": 1, "ship_name": 1})
            await self.leaderboard_post_record_ships(ctx, query, "🚢 Ships LeaderBoard")

    async def leaderboard_post_record_users(self, ctx, query, title, key):

        raw_list = []
        formatted_list = []

        for user in query:
            try:
                member_name = self.client.get_user(int(user["user_id"])).display_name
                if isinstance(user[key], list):
                    raw_list.append((member_name, len(user[key])))
                else:
                    raw_list.append((member_name, user[key]))
            except AttributeError:
                continue

        for user in sorted(raw_list, key=lambda x: x[1], reverse=True):
            formatted_list.append(f"🔸{user[0]}, x{user[1]:,d}\n")

        await self.leaderboard_paginate(title, ctx, formatted_list)

    async def leaderboard_post_record_ships(self, ctx, query, title):

        raw_list = []
        formatted_list = []

        for ship in query:
            raw_list.append((ship["ship_name"], ship["points"]))

        for ship in sorted(raw_list, key=lambda x: x[1], reverse=True):
            formatted_list.append(f"🔸{ship[0]}, x{ship[1]} {e_f} \n")

        await self.leaderboard_paginate(title, ctx, formatted_list)

    async def leaderboard_paginate(self, title, ctx, formatted_list):

        page = 1
        max_lines = 15
        page_total = ceil(len(formatted_list) / max_lines)
        if page_total == 0:
            page_total = 1

        def embed_new_create(page_new):
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

        msg = await process_msg_submit(ctx.channel, None, embed_new_create(page))
        emoji_arrows = ["⬅", "➡"]
        for emoji in emoji_arrows:
            await process_msg_reaction_add(msg, emoji)

        def check(r, u):
            return u != self.client.user and r.message.id == msg.id

        while True:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=60, check=check)
            except asyncio.TimeoutError:
                await process_msg_reaction_clear(msg)
                break
            else:
                if str(reaction.emoji) == emoji_arrows[1]:
                    page += 1
                elif str(reaction.emoji) == emoji_arrows[0]:
                    page -= 1
                if page == 0:
                    page = page_total
                elif page > page_total:
                    page = 1
                await process_msg_edit(msg, None, embed_new_create(page))


def setup(client):
    client.add_cog(Leaderboard(client))

