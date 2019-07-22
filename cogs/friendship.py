"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import asyncio

import discord
from discord.ext import commands

from cogs.mongo.db import users, friendship
from cogs.startup import emoji_f


def get_bond(x, y):
    bond_list = sorted([x.id, y.id], reverse=True)
    return f"{bond_list[0]}x{bond_list[1]}"


class Friendship(commands.Cog):

    def __init__(self, client):
        self.client = client

    async def friendship_check_levelup(self, ctx, code, giver):
        ship = friendship.find_one({
            "code": code}, {
            "_id": 0, "level": 1, "points": 1, "points_required": 1, "ship_name": 1
        })
        bond_current = ship["points"]
        level = ship["level"]

        if level < 5:
            if bond_current >= ship["points_required"]:
                friendship.update_one({"code": code}, {"$inc": {"level": 1}})
                level_next = level + 1
                points_required = \
                    round(-1.875 * (level_next ** 4) + 38.75 * (level_next ** 3) - 170.63 * (level_next ** 2)
                          + 313.75 * level_next - 175)
                friendship.update_one({"code": code}, {"$inc": {"points_required": points_required}})
                await self.friendship_post_ship(code, giver, ctx)

    async def friendship_post_ship(self, code, query1, ctx):

        ship_profile = friendship.find_one({
            "code": code}, {
            "_id": 0, "shipper1": 1, "shipper2": 1, "points": 1, "level": 1, "ship_name": 1
        })

        list_rank = []
        for entry in friendship.find({}, {"code": 1, "points": 1}):
            list_rank.append((entry["code"], entry["points"]))

        rank = (sorted(list_rank, key=lambda x: x[1], reverse=True)).index((code, ship_profile["points"])) + 1

        if ship_profile['level'] > 1:
            rewards = str(ship_profile["level"] * 25) + " jades/day"
        else:
            rewards = "Must be Level 2 and above"

        description = \
            f"```" \
                f"• Level:        :: {ship_profile['level']}\n" \
                f"• Total Points: :: {ship_profile['points']}\n" \
                f"• Server Rank:  :: {rank}\n" \
                f"• Rewards       :: {rewards}" \
                f"```"

        embed = discord.Embed(
            color=query1.colour,
            description=description
        )
        embed.set_author(
            name=f"{ship_profile['ship_name']}",
            icon_url=self.client.get_user(int(ship_profile["shipper1"])).avatar_url
        )
        embed.set_thumbnail(url=self.client.get_user(int(ship_profile['shipper2'])).avatar_url)
        await ctx.channel.send(embed=embed)

    @commands.command(aliases=["ship"])
    @commands.guild_only()
    async def friendship_ship(self, ctx, query1: discord.Member = None, query2: discord.Member = None):

        try:
            if query1 is None and query2 is None:
                embed = discord.Embed(
                    title="ship", colour=discord.Colour(0xffe6a7),
                    description="shows a ship profile\nto change your ship's name use *`;fpchange`*"
                )
                embed.add_field(name="Formats", value="*• `;ship @member`*\n*• `;ship @member @member`*\n")
                await ctx.channel.send(embed=embed)

            elif query1 is not None and query2 is None:
                code = get_bond(ctx.author, query1)
                await self.friendship_post_ship(code, query1, ctx)

            elif query1 is not None and query2 is not None:
                code = get_bond(query1, query2)
                await self.friendship_post_ship(code, query1, ctx)

        except TypeError:
            embed = discord.Embed(
                colour=discord.Colour(0xffe6a7),
                title="Insufficient friendship points",
                description=f"{ctx.author.mention}, I'm sorry, but that ship has sunk before it was built."
            )
            await ctx.channel.send(embed=embed)

    @commands.command(aliases=["friendship", "fp"])
    @commands.guild_only()
    async def friendship_give(self, ctx, receiver: discord.Member = None):
        giver = ctx.author

        profile = users.find_one({"user_id": str(giver.id)}, {"_id": 0, "friendship_pass": 1})

        if receiver is None:
            embed = discord.Embed(
                title="friendship, fp", colour=discord.Colour(0xffe6a7),
                description="sends and receives friendship points & builds ship that earns daily reward\n"
                            "built ships are shown using *`;ship`*"
            )
            embed.add_field(
                name="Mechanics",
                value="```"
                      "• Send hearts      ::  + 5\n"
                      " * added ship exp  ::  + 5\n\n"
                      "• Confirm receipt < 2 min"
                      "\n * Receiver        ::  + 3"
                      "\n * added ship exp  ::  + 3```"
            )
            embed.add_field(name="Format", value="*`;friendship @member`*")
            await ctx.channel.send(embed=embed)

        elif receiver.bot is True or receiver == ctx.author:
            return

        elif profile["friendship_pass"] == 0:
            embed = discord.Embed(
                colour=discord.Colour(0xffe6a7),
                title="Insufficient friendship points",
                description=f"{giver.mention}, you have used up all your friendship points"
            )
            await ctx.channel.send(embed=embed)

        elif profile["friendship_pass"] > 0:
            code = get_bond(giver, receiver)
            users.update_one({
                "user_id": str(giver.id)}, {
                "$inc": {
                    "friendship_pass": -1
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
            await ctx.message.add_reaction(f"{emoji_f.replace('<', '').replace('>', '')}")

            def check(r, u):
                return u == receiver and str(r.emoji) == emoji_f

            try:
                await self.client.wait_for("reaction_add", timeout=120, check=check)
            except asyncio.TimeoutError:
                await self.friendship_check_levelup(ctx, code, giver)
                await ctx.message.clear_reactions()
            else:
                friendship.update_one({"code": code}, {"$inc": {"points": 3}})
                await self.friendship_check_levelup(ctx, code, giver)
                users.update_one({"user_id": str(receiver.id)}, {"$inc": {"friendship": 3}})
                await ctx.message.clear_reactions()
                await ctx.message.add_reaction("✅")

    @commands.command(aliases=["fpchange", "fpc"])
    @commands.guild_only()
    async def friendship_change_name(self, ctx, receiver: discord.Member = None, *, new_name):

        try:
            code = get_bond(ctx.author, receiver)
            friendship.update_one({"code": code}, {"$set": {"ship_name": new_name}})
            await self.friendship_post_ship(code, ctx.author, ctx)

        except AttributeError:
            embed = discord.Embed(
                title="fpchange, fpc", colour=discord.Colour(0xffe6a7),
                description="changes your ship name with the mentioned member"
            )
            embed.add_field(name="Formats", value="*• `;fpc @member <fancy name>`*")
            await ctx.channel.send(embe=embed)


def setup(client):
    client.add_cog(Friendship(client))
