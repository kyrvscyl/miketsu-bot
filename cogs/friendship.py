"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import asyncio

import discord
from discord.ext import commands

from cogs.mongo.db import users, daily, friendship

# Global Variables
emoji_m = "<:medal:573071121545560064>"
emoji_j = "<:jade:555630314282811412>"
emoji_c = "<:coin:573071121495097344>"
emoji_f = "<:friendship:555630314056318979>"
emoji_a = "<:amulet:573071120685596682>"


def get_bond(x, y):
    bond_list = sorted([x.id, y.id], reverse=True)

    return f"{bond_list[0]}x{bond_list[1]}"


# noinspection PyShadowingNames,PyUnusedLocal
async def friendship_levelup(ctx, code, giver, receiver):
    ship = friendship.find_one({
        "code": code}, {
        "_id": 0, "level": 1, "points": 1, "points_required": 1, "ship_name": 1
    })

    bond_current = ship["points"]
    bond_required = ship["points_required"]
    level = ship["level"]

    # Checks for max level
    if not level == 5:

        if bond_current >= bond_required:

            ship_name = ship["ship_name"]
            friendship.update_one({"code": code}, {"$inc": {"level": 1}})
            level_next = level + 1

            points_required = \
                round(-1.875 * (level_next ** 4) + 38.75 * (level_next ** 3) - 170.63 * (level_next ** 2)
                      + 313.75 * level_next - 175)

            friendship.update_one({"code": code}, {"$inc": {"points_required": points_required}})

            list_rank = []

            for ship in friendship.find({}, {"code": 1, "points": 1}):
                list_rank.append((ship["code"], ship["points"]))

            rank = (sorted(list_rank, key=lambda x: x[1], reverse=True)).index((code, bond_current)) + 1

            description = \
                f"Level: `{level}`\n" \
                f"Total points: `{bond_current}`{emoji_f}\n" \
                f"Server Rank: `{rank}`"

            embed = discord.Embed(
                color=giver.colour,
                description=description
            )
            embed.set_author(name="{}".format(ship_name), icon_url=giver.avatar_url)
            embed.set_thumbnail(url=receiver.avatar_url)
            await ctx.channel.send(embed=embed)


# noinspection PyUnusedLocal,PyShadowingNames
class Friendship(commands.Cog):

    def __init__(self, client):
        self.client = client

    # noinspection PyTypeChecker
    @commands.command(aliases=["ship"])
    async def friendship_ship(self, ctx, query1: discord.Member = None, query2: discord.Member = None):

        try:
            # No mentioned User
            if query1 is None and query2 is None:
                await ctx.channel.send("Please mention a user or users to view ships.")

            # Only 1 mentioned user
            elif query1 is not None and query2 is None:

                code = get_bond(ctx.author, query1)
                ship = friendship.find_one({
                    "code": code}, {
                    "_id": 0, "shipper1": 1, "shipper2": 1, "points": 1, "level": 1, "ship_name": 1
                })

                list_rank = []
                for ship in friendship.find({}, {"code": 1, "points": 1}):
                    list_rank.append((ship["code"], ship["points"]))

                rank = (sorted(list_rank, key=lambda x: x[1], reverse=True)).index((code, ship["points"])) + 1

                description = \
                    f"Level: `{ship['level']}`\n" \
                    f"Total points: `{ship['points']}`{emoji_f}\n" \
                    f"Server Rank: `{rank}`"

                embed = discord.Embed(
                    color=query1.colour,
                    description=description
                )

                embed.set_author(
                    name=f"{ship['ship_name']}",
                    icon_url=self.client.get_user(int(ship["shipper1"])).avatar_url
                )
                embed.set_thumbnail(url=self.client.get_user(int(ship['shipper2'])).avatar_url)

                await ctx.channel.send(embed=embed)

            # 2 mentioned users
            elif query1 is not None and query2 is not None:

                code = get_bond(query1, query2)
                ship = friendship.find_one({
                    "code": code}, {
                    "_id": 0, "shipper1": 1, "shipper2": 1, "points": 1, "level": 1, "ship_name": 1
                })

                list_rank = []
                for ship in friendship.find({}, {"code": 1, "points": 1}):
                    list_rank.append((ship["code"], ship["points"]))

                rank = (sorted(list_rank, key=lambda x: x[1], reverse=True)).index((code, ship["points"])) + 1

                description = \
                    f"Level: `{ship['level']}`\n" \
                    f"Total points: `{ship['points']}`{emoji_f}\n" \
                    f"Server Rank: `{rank}`"

                embed = discord.Embed(
                    color=query2.colour,
                    description=description
                )
                embed.set_author(
                    name=f"{ship['ship_name']}",
                    icon_url=self.client.get_user(int(ship["shipper1"])).avatar_url
                )
                embed.set_thumbnail(url=self.client.get_user(int(ship['shipper2'])).avatar_url)
                await ctx.channel.send(embed=embed)

        except TypeError:
            await ctx.channel.send(f"{ctx.author.mention}, I'm sorry, but that ship has sunk before it was built.")

    # noinspection PyTypeChecker
    @commands.command(aliases=["fp"])
    async def friendship(self, ctx, receiver: discord.Member = None):
        giver = ctx.author

        # Checks if no user mentioned
        if receiver is None:

            embed = discord.Embed(
                color=giver.colour,
                title="{} Friendship System".format("<:friendship:555630314056318979>"),
                description="Send & receive friendship points: `;fp @mention`\n"
                            "Show ship's information: `;ship @mention`\n"
                            "Change ship's name: `;fpc @mention <name>`"
            )
            embed.set_thumbnail(url=self.client.user.avatar_url)

            await ctx.channel.send(embed=embed)

        elif receiver.bot is True or receiver == ctx.author:
            return

        elif daily.find_one({"key": "daily"}, {"_id": 0, f"{giver.id}": 1})[str(giver.id)]["friendship_pass"] == 0:

            await ctx.channel.send("You have used up all your friendship points today.")

        elif daily.find_one({"key": "daily"}, {"_id": 0, f"{giver.id}": 1})[str(giver.id)]["friendship_pass"] > 0:

            code = get_bond(giver, receiver)
            daily.update_one({
                "key": "daily"}, {
                "$inc": {
                    "{}.friendship_pass".format(giver.id): -1
                }
            })

            if friendship.find_one({"code": code}, {"_id": 0}) is None:
                profile = {
                    "code": code,
                    "shipper1": str(ctx.author.id),
                    "shipper2": str(receiver.id),
                    "ship_name": f"{giver.name} and {receiver.name}'s ship",
                    "level": 1,
                    "points": 0,
                    "points_required": 50
                }
                friendship.insert_one(profile)

            friendship.update_one({"code": code}, {"$inc": {"points": 5}})
            users.update_one({"user_id": str(giver.id)}, {"$inc": {"friendship": 5}})
            await ctx.message.add_reaction(":friendship:555630314056318979")

            def check(reaction, user):
                return user == receiver and str(reaction.emoji) == emoji_f

            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=120, check=check)

            except asyncio.TimeoutError:
                await friendship_levelup(ctx, code, giver, receiver)
                await ctx.message.clear_reactions()

            else:
                friendship.update_one({"code": code}, {"$inc": {"points": 3}})
                await friendship_levelup(ctx, code, giver, receiver)

                users.update_one({"user_id": str(receiver.id)}, {"$inc": {"friendship": 3}})
                await ctx.message.clear_reactions()
                await ctx.message.add_reaction("✅")

    # noinspection PyTypeChecker
    @commands.command(aliases=["fpchange", "fpc"])
    async def friendship_changename(self, ctx, receiver: discord.Member = None, *args):

        try:
            code = get_bond(ctx.author, receiver)
            new_name = " ".join(args)
            ship = friendship.find_one({
                "code": code}, {
                "_id": 0, "shipper1": 1, "shipper2": 1, "points": 1, "level": 1, "ship_name": 1
            })

            shipper1 = ship["shipper1"]
            shipper2 = ship["shipper2"]
            ship_name = ship["ship_name"]
            bond_current = ship["points"]
            level = ship["level"]

            friendship.update_one({"code": code}, {"$set": {"ship_name": new_name}})

            list_rank = []
            for ship in friendship.find({}, {"code": 1, "points": 1}):
                list_rank.append((ship["code"], ship["points"]))

            rank = (sorted(list_rank, key=lambda x: x[1], reverse=True)).index((code, bond_current)) + 1

            description = \
                f"Level: `{level}`\n" \
                f"Total points: `{bond_current}`{emoji_f}\n" \
                f"Server Rank: `{rank}`"

            embed = discord.Embed(
                color=ctx.author.colour,
                description=description
            )
            embed.set_author(
                name=f"{new_name}",
                icon_url=self.client.get_user(int(shipper1)).avatar_url
            )
            embed.set_thumbnail(url=self.client.get_user(int(shipper2)).avatar_url)

            await ctx.channel.send(embed=embed)

        except AttributeError:
            await ctx.channel.send("Use `;fpc @mention <name>` to change your ship's name")


def setup(client):
    client.add_cog(Friendship(client))
