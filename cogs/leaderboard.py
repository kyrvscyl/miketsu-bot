"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import asyncio

import discord
from discord.ext import commands

from cogs.mongo.db import users, friendship, streak

# Global Variables
emoji_m = "<:medal:573071121545560064>"
emoji_j = "<:jade:555630314282811412>"
emoji_c = "<:coin:573071121495097344>"
emoji_f = "<:friendship:555630314056318979>"
emoji_a = "<:amulet:573071120685596682>"


# noinspection PyUnusedLocal
def post(page, embed1, embed2, embed3):
    if page == 1:
        return embed1
    if page == 2:
        return embed2
    if page == 3:
        return embed3
    if page > 3:
        page = 1
        return embed1
    if page < 1:
        page = 3
        return embed3


# noinspection PyShadowingNames
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

        # At any argument, return the Level Leaderboard
        except IndexError:
            await self.leaderboard_post_level(ctx)

    async def leaderboard_post_ssr(self, ctx):
        ssr_board1 = []

        for user in users.find({}, {"_id": 0, "user_id": 1, "SSR": 1}):
            ssr_board1.append((self.client.get_user(int(user["user_id"])).name, user["SSR"]))

        ssr_board2 = sorted(ssr_board1, key=lambda x: x[1], reverse=True)

        description1 = ""
        description2 = ""
        description3 = ""

        for user in ssr_board2[0:10]:
            description1 += f":small_orange_diamond:{user[0]}, x{user[1]}\n"
        for user in ssr_board2[10:20]:
            description2 += f":small_orange_diamond:{user[0]}, x{user[1]}\n"
        for user in ssr_board2[20:30]:
            description3 += f":small_orange_diamond:{user[0]}, x{user[1]}\n"

        title = ":trophy: SSR LeaderBoard"

        embed1 = discord.Embed(color=ctx.author.colour, title=title, description=description1)
        embed1.set_footer(text="page 1")

        embed2 = discord.Embed(color=ctx.author.colour, title=title, description=description2)
        embed2.set_footer(text="page 2")

        embed3 = discord.Embed(color=ctx.author.colour, title=title, description=description3)
        embed3.set_footer(text="page 3")

        msg = await ctx.channel.send(embed=embed1)

        await msg.add_reaction("⬅")
        await msg.add_reaction("➡")

        def check(reaction, user):
            return user != self.client.user and reaction.message.id == msg.id

        # Embed pagination max 3 pages
        page = 1
        while True:
            try:
                timeout = 60
                reaction, user = await self.client.wait_for("reaction_add", timeout=timeout, check=check)
                if str(reaction.emoji) == "➡":
                    page += 1
                if str(reaction.emoji) == "⬅":
                    page -= 1
                await msg.edit(embed=post(page, embed1, embed2, embed3))

            except asyncio.TimeoutError:
                return False

    async def leaderboard_post_medals(self, ctx):
        medal_board1 = []

        for user in users.find({}, {"_id": 0, "user_id": 1, "medals": 1}):
            medal_board1.append((self.client.get_user(int(user["user_id"])).name, user["medals"]))

        medal_board2 = sorted(medal_board1, key=lambda x: x[1], reverse=True)

        description1 = ""
        description2 = ""
        description3 = ""

        for user in medal_board2[0:10]:
            description1 += f":small_orange_diamond:{user[0]}, x{user[1]}\n"
        for user in medal_board2[10:20]:
            description2 += f":small_orange_diamond:{user[0]}, x{user[1]}\n"
        for user in medal_board2[20:30]:
            description3 += f":small_orange_diamond:{user[0]}, x{user[1]}\n"

        title = "{} Medal LeaderBoard".format("<:medal:573071121545560064>")

        embed1 = discord.Embed(color=ctx.author.colour, title=title, description=description1)
        embed1.set_footer(text="page 1")

        embed2 = discord.Embed(color=ctx.author.colour, title=title, description=description2)
        embed2.set_footer(text="page 2")

        embed3 = discord.Embed(color=ctx.author.colour, title=title, description=description3)
        embed3.set_footer(text="page 3")

        msg = await ctx.channel.send(embed=embed1)

        await msg.add_reaction("⬅")
        await msg.add_reaction("➡")

        def check(reaction, user):
            return user != self.client.user and reaction.message.id == msg.id

        # Embed pagination max 3 pages
        page = 1
        while True:
            try:
                timeout = 60
                reaction, user = await self.client.wait_for("reaction_add", timeout=timeout, check=check)
                if str(reaction.emoji) == "➡":
                    page += 1
                if str(reaction.emoji) == "⬅":
                    page -= 1
                await msg.edit(embed=post(page, embed1, embed2, embed3))

            except asyncio.TimeoutError:
                return False

    async def leaderboard_post_level(self, ctx):
        level_board1 = []

        for user in users.find({}, {"_id": 0, "user_id": 1, "level": 1}):
            print(user["user_id"])
            level_board1.append((self.client.get_user(int(user["user_id"])).name, user["level"]))

        level_board2 = sorted(level_board1, key=lambda x: x[1], reverse=True)

        description1 = ""
        description2 = ""
        description3 = ""

        for user in level_board2[0:10]:
            description1 += f":small_orange_diamond:{user[0]}, x{user[1]}\n"
        for user in level_board2[10:20]:
            description2 += f":small_orange_diamond:{user[0]}, x{user[1]}\n"
        for user in level_board2[20:30]:
            description3 += f":small_orange_diamond:{user[0]}, x{user[1]}\n"

        title = ":arrow_heading_up: Level LeaderBoard"

        embed1 = discord.Embed(color=ctx.author.colour, title=title, description=description1)
        embed1.set_footer(text="page 1")

        embed2 = discord.Embed(color=ctx.author.colour, title=title, description=description2)
        embed2.set_footer(text="page 2")

        embed3 = discord.Embed(color=ctx.author.colour, title=title, description=description3)
        embed3.set_footer(text="page 3")

        msg = await ctx.channel.send(embed=embed1)

        await msg.add_reaction("⬅")
        await msg.add_reaction("➡")

        def check(reaction, user):
            return user != self.client.user and reaction.message.id == msg.id

        # Embed pagination max 3 pages
        page = 1
        while True:
            try:
                timeout = 60
                reaction, user = await self.client.wait_for("reaction_add", timeout=timeout, check=check)
                if str(reaction.emoji) == "➡":
                    page += 1
                if str(reaction.emoji) == "⬅":
                    page -= 1
                await msg.edit(embed=post(page, embed1, embed2, embed3))

            except asyncio.TimeoutError:
                return False

    async def leaderboard_post_amulet(self, ctx):
        amulet_board1 = []

        for user in users.find({}, {"_id": 0, "user_id": 1, "amulets_spent": 1}):
            amulet_board1.append((self.client.get_user(int(user["user_id"])).name, user["amulets_spent"]))

        amulet_board2 = sorted(amulet_board1, key=lambda x: x[1], reverse=True)

        description1 = ""
        description2 = ""
        description3 = ""

        for user in amulet_board2[0:10]:
            description1 += f":small_orange_diamond:{user[0]}, x{user[1]}\n"
        for user in amulet_board2[10:20]:
            description2 += f":small_orange_diamond:{user[0]}, x{user[1]}\n"
        for user in amulet_board2[20:30]:
            description3 += f":small_orange_diamond:{user[0]}, x{user[1]}\n"

        title = f"{emoji_a} Spender LeaderBoard"

        embed1 = discord.Embed(color=ctx.author.colour, title=title, description=description1)
        embed1.set_footer(text="page 1")

        embed2 = discord.Embed(color=ctx.author.colour, title=title, description=description2)
        embed2.set_footer(text="page 2")

        embed3 = discord.Embed(color=ctx.author.colour, title=title, description=description3)
        embed3.set_footer(text="page 3")

        msg = await ctx.channel.send(embed=embed1)

        await msg.add_reaction("⬅")
        await msg.add_reaction("➡")

        def check(reaction, user):
            return user != self.client.user and reaction.message.id == msg.id

        # Embed pagination max 3 pages
        page = 1
        while True:
            try:
                timeout = 60
                reaction, user = await self.client.wait_for("reaction_add", timeout=timeout, check=check)
                if str(reaction.emoji) == "➡":
                    page += 1
                if str(reaction.emoji) == "⬅":
                    page -= 1
                await msg.edit(embed=post(page, embed1, embed2, embed3))

            except asyncio.TimeoutError:
                return False

    async def leaderboard_friendship(self, ctx):
        fp_board1 = []

        for user in users.find({}, {"_id": 0, "user_id": 1, "friendship": 1}):
            fp_board1.append((self.client.get_user(int(user["user_id"])).name, user["friendship"]))

        fp_board12 = sorted(fp_board1, key=lambda x: x[1], reverse=True)

        description1 = ""
        description2 = ""
        description3 = ""

        for user in fp_board12[0:10]:
            description1 += f":small_orange_diamond:{user[0]}, x{user[1]}\n"
        for user in fp_board12[10:20]:
            description2 += f":small_orange_diamond:{user[0]}, x{user[1]}\n"
        for user in fp_board12[20:30]:
            description3 += f":small_orange_diamond:{user[0]}, x{user[1]}\n"

        title = f"{emoji_f} Friendship LeaderBoard"

        embed1 = discord.Embed(color=ctx.author.colour, title=title, description=description1)
        embed1.set_footer(text="page 1")

        embed2 = discord.Embed(color=ctx.author.colour, title=title, description=description2)
        embed2.set_footer(text="page 2")

        embed3 = discord.Embed(color=ctx.author.colour, title=title, description=description3)
        embed3.set_footer(text="page 3")

        msg = await ctx.channel.send(embed=embed1)

        await msg.add_reaction("⬅")
        await msg.add_reaction("➡")

        def check(reaction, user):
            return user != self.client.user and reaction.message.id == msg.id

        # Embed pagination max 3 pages
        page = 1
        while True:
            try:
                timeout = 60
                reaction, user = await self.client.wait_for("reaction_add", timeout=timeout, check=check)
                if str(reaction.emoji) == "➡":
                    page += 1
                if str(reaction.emoji) == "⬅":
                    page -= 1
                await msg.edit(embed=post(page, embed1, embed2, embed3))

            except asyncio.TimeoutError:
                return False

    async def leaderboard_post_ship(self, ctx):
        ship_board1 = []

        for ship in friendship.find({},
                                    {"_id": 0, "points": 1, "shipper1": 1, "shipper2": 1, "ship_name": 1, "level": 1}):
            ship_board1.append((ship["ship_name"], ship["shipper1"], ship["shipper2"], ship["level"], ship["points"]))

        ship_board2 = sorted(ship_board1, key=lambda x: x[4], reverse=True)

        description1 = ""
        description2 = ""
        description3 = ""

        for ship in ship_board2[0:10]:
            description1 += f":small_orange_diamond:{ship[0]}, x{ship[4]}{emoji_f}\n"
        for ship in ship_board2[10:20]:
            description2 += f":small_orange_diamond:{ship[0]}, x{ship[4]}{emoji_f}\n"
        for ship in ship_board2[20:30]:
            description3 += f":small_orange_diamond:{ship[0]}, x{ship[4]}{emoji_f}\n"

        title = ":ship: Ships LeaderBoard"

        embed1 = discord.Embed(color=ctx.author.colour, title=title, description=description1)
        embed1.set_footer(text="page 1")

        embed2 = discord.Embed(color=ctx.author.colour, title=title, description=description2)
        embed2.set_footer(text="page 2")

        embed3 = discord.Embed(color=ctx.author.colour, title=title, description=description3)
        embed3.set_footer(text="page 3")

        msg = await ctx.channel.send(embed=embed1)

        await msg.add_reaction("⬅")
        await msg.add_reaction("➡")

        def check(reaction, user):
            return user != self.client.user and reaction.message.id == msg.id

        # Embed pagination max 3 pages
        page = 1
        while True:
            try:
                timeout = 60
                reaction, user = await self.client.wait_for("reaction_add", timeout=timeout, check=check)
                if str(reaction.emoji) == "➡":
                    page += 1
                if str(reaction.emoji) == "⬅":
                    page -= 1
                await msg.edit(embed=post(page, embed1, embed2, embed3))

            except asyncio.TimeoutError:
                return False

    async def leaderboard_post_streak(self, ctx):
        streakboard1 = []

        for user in streak.find({}, {"_id": 0, "user_id": 1, "SSR_record": 1}):
            streakboard1.append((self.client.get_user(int(user["user_id"])).name, user["SSR_record"]))

        streakboard2 = sorted(streakboard1, key=lambda x: x[1], reverse=True)

        description1 = ""
        description2 = ""
        description3 = ""

        for user in streakboard2[0:10]:
            description1 += f":small_orange_diamond:{user[0]}, x{user[1]}{emoji_a}\n"
        for user in streakboard2[10:20]:
            description2 += f":small_orange_diamond:{user[0]}, x{user[1]}{emoji_a}\n"
        for user in streakboard2[20:30]:
            description3 += f":small_orange_diamond:{user[0]}, x{user[1]}{emoji_a}\n"

        title = "No SSR Streak LeaderBoard"

        embed1 = discord.Embed(color=ctx.author.colour, title=title, description=description1)
        embed1.set_footer(text="page 1")

        embed2 = discord.Embed(color=ctx.author.colour, title=title, description=description2)
        embed2.set_footer(text="page 2")

        embed3 = discord.Embed(color=ctx.author.colour, title=title, description=description3)
        embed3.set_footer(text="page 3")

        msg = await ctx.channel.send(embed=embed1)

        await msg.add_reaction("⬅")
        await msg.add_reaction("➡")

        def check(reaction, user):
            return user != self.client.user and reaction.message.id == msg.id

        # Embed pagination max 3 pages
        page = 1
        while True:
            try:
                timeout = 60
                reaction, user = await self.client.wait_for("reaction_add", timeout=timeout, check=check)
                if str(reaction.emoji) == "➡":
                    page += 1
                if str(reaction.emoji) == "⬅":
                    page -= 1
                await msg.edit(embed=post(page, embed1, embed2, embed3))

            except asyncio.TimeoutError:
                return False


def setup(client):
    client.add_cog(Leaderboard(client))
