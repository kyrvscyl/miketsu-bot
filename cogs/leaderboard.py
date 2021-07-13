"""
Leaderboard Module
"Miketsu, 2021
"""

from discord.ext import commands

from cogs.ext.initialize import *


class Leaderboard(commands.Cog):
    def __init__(self, client):

        self.client = client
        self.prefix = self.client.command_prefix

    async def leaderboard_show_help(self, ctx):

        embed = discord.Embed(
            title="leaderboard, lb", colour=colour,
            description="shows various leaderboards"
        )
        embed.add_field(
            name="Arguments",
            value=f"*SP, SSR, SR, SSN, level, medals, amulets, friendship, ships, streak, frames*",
            inline=False
        )
        embed.add_field(name="Example", value=f"*{self.prefix}leaderboard friendship*", inline=False)
        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["leaderboard", "lb"])
    @commands.guild_only()
    async def leaderboard_show(self, ctx, *, args=None):

        if args is None:
            await self.leaderboard_show_help(ctx)

        elif args.lower() in ["ssr"]:
            query = users.find({}, {"_id": 0, "user_id": 1, "SSR": 1})
            await self.leaderboard_show_record_users(ctx, query, f"{e_2} LeaderBoard", "SSR")

        elif args.lower() in ["sp"]:
            query = users.find({}, {"_id": 0, "user_id": 1, "SP": 1})
            await self.leaderboard_show_record_users(ctx, query, f"{e_1} LeaderBoard", "SP")

        elif args.lower() in ["sr"]:
            query = users.find({}, {"_id": 0, "user_id": 1, "SR": 1})
            await self.leaderboard_show_record_users(ctx, query, f"{e_3} LeaderBoard", "SR")

        elif args.lower() in ["ssn"]:
            query = users.find({}, {"_id": 0, "user_id": 1, "SSN": 1})
            await self.leaderboard_show_record_users(ctx, query, f"{e_6} LeaderBoard", "SSN")

        elif args.lower() in ["medal", "medals"]:
            query = users.find({}, {"_id": 0, "user_id": 1, "medals": 1})
            await self.leaderboard_show_record_users(ctx, query, f"{e_m} Medal LeaderBoard", "medals")

        elif args.lower() in ["amulet", "amulets"]:
            query = users.find({}, {"_id": 0, "user_id": 1, "amulets_spent": 1})
            await self.leaderboard_show_record_users(ctx, query, f"{e_a} Spender LeaderBoard", "amulets_spent")

        elif args.lower() in ["friendship", "fp"]:
            query = users.find({}, {"_id": 0, "user_id": 1, "friendship": 1})
            await self.leaderboard_show_record_users(ctx, query, f"{e_f} Friendship LeaderBoard", "friendship")

        elif args.lower() in ["level"]:
            query = users.find({}, {"_id": 0, "user_id": 1, "level": 1})
            await self.leaderboard_show_record_users(ctx, query, f"{e_x} Level LeaderBoard", "level")

        elif args.lower() in ["achievements", "frames"]:
            query = users.find({}, {"_id": 0, "user_id": 1, "achievements": 1})
            await self.leaderboard_show_record_users(ctx, query, "🖼 Frames LeaderBoard", "achievements")

        elif args.lower() in ["ship", "ships"]:
            query = ships.find({}, {"_id": 0, "points": 1, "ship_name": 1})
            await self.leaderboard_show_record_ships(ctx, query, "🚢 Ships LeaderBoard")

        elif args.lower() in ["streak", "ssrstreak"]:
            query = streaks.find({}, {"_id": 0, "user_id": 1, "SSR_current": 1})
            await self.leaderboard_show_record_users(
                ctx, query, f"No {e_2} Summon Streak LeaderBoard", "SSR_current"
            )

    async def leaderboard_show_record_users(self, ctx, query, title, key):

        listings, listings_formatted = [], []

        for user in query:
            try:
                member_name = self.client.get_user(int(user["user_id"])).display_name
            except AttributeError:
                continue
            else:
                if isinstance(user[key], list):
                    listings.append((member_name, len(user[key])))
                else:
                    listings.append((member_name, user[key]))

        for user in sorted(listings, key=lambda x: x[1], reverse=True):
            listings_formatted.append(f"🔸{user[0]}, x{user[1]:,d}\n")

        await self.leaderboard_show_paginate(title, ctx, listings_formatted)

    async def leaderboard_show_record_ships(self, ctx, query, title):

        listings, listings_formatted = [], []

        for ship in query:
            listings.append((ship["ship_name"], ship["points"]))

        for ship in sorted(listings, key=lambda x: x[1], reverse=True):
            listings_formatted.append(f"🔸{ship[0]}, x{ship[1]} {e_f} \n")

        await self.leaderboard_show_paginate(title, ctx, listings_formatted)

    async def leaderboard_show_paginate(self, title, ctx, listings_formatted):

        page, max_lines = 1, 15
        page_total = ceil(len(listings_formatted) / max_lines)
        if page_total == 0:
            page_total = 1

        def embed_new_create(page_new):
            end = page * max_lines
            start = end - max_lines
            description = "".join(listings_formatted[start:end])

            embed_new = discord.Embed(
                color=ctx.author.colour, title=title,
                description=f"{description}", timestamp=get_timestamp()
            )
            embed_new.set_footer(text=f"Page: {page_new} of {page_total}")
            return embed_new

        msg = await process_msg_submit(ctx.channel, None, embed_new_create(page))

        emojis_add = ["⬅", "➡"]
        for emoji in emojis_add:
            await process_msg_reaction_add(msg, emoji)

        def check(r, u):
            return u != self.client.user and r.message.id == msg.id and str(r.emoji) in emojis_add

        while True:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=60, check=check)
            except asyncio.TimeoutError:
                await process_msg_reaction_clear(msg)
                break
            else:
                if str(reaction.emoji) == emojis_add[1]:
                    page += 1
                elif str(reaction.emoji) == emojis_add[0]:
                    page -= 1
                if page == 0:
                    page = page_total
                elif page > page_total:
                    page = 1
                await process_msg_edit(msg, None, embed_new_create(page))
                await process_msg_reaction_remove(msg, str(reaction.emoji), user)


def setup(client):
    client.add_cog(Leaderboard(client))
