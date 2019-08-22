"""
Ship Module
Miketsu, 2019
"""

import asyncio
from datetime import datetime
from math import ceil

import discord
from discord.ext import commands

from cogs.mongo.database import get_collections
from cogs.startup import e_f, e_j, pluralize, embed_color

# Collections
users = get_collections("miketsu", "users")
ships = get_collections("miketsu", "ships")


def get_bond(x, y):
    bond_list = sorted([x.id, y.id], reverse=True)
    return f"{bond_list[0]}x{bond_list[1]}"


def get_timestamp():
    return datetime.utcfromtimestamp(datetime.timestamp(datetime.now()))


class Friendship(commands.Cog):

    def __init__(self, client):
        self.client = client

    async def friendship_check_levelup(self, ctx, code, giver):
        ship = ships.find_one({
            "code": code}, {
            "_id": 0, "level": 1, "points": 1, "points_required": 1, "ship_name": 1
        })
        bond_current = ship["points"]
        level = ship["level"]

        if level < 5:
            if bond_current >= ship["points_required"]:
                ships.update_one({"code": code}, {"$inc": {"level": 1}})
                level_next = level + 1
                points_required = \
                    round(-1.875 * (level_next ** 4) + 38.75 * (level_next ** 3) - 170.63 * (level_next ** 2)
                          + 313.75 * level_next - 175)
                ships.update_one({"code": code}, {"$inc": {"points_required": points_required}})

                if level_next == 5:
                    ships.update_one({"code": code}, {"$set": {"points": 575, "points_required": 575}})

                await self.friendship_post_ship(code, giver, ctx)

    async def friendship_post_ship(self, code, query1, ctx):

        ship_profile = ships.find_one({
            "code": code}, {
            "_id": 0, "shipper1": 1, "shipper2": 1, "points": 1, "level": 1, "ship_name": 1, "points_required": 1
        })

        list_rank = []
        for entry in ships.find({}, {"code": 1, "points": 1}):
            list_rank.append((entry["code"], entry["points"]))

        rank = (sorted(list_rank, key=lambda x: x[1], reverse=True)).index((code, ship_profile["points"])) + 1

        if ship_profile['level'] > 1:
            rewards = str(ship_profile["level"] * 25) + " jades/day"
        else:
            rewards = "Must be Level 2 & above"

        description = f"```" \
                      f"• Level:        :: {ship_profile['level']}/5\n" \
                      f"• Total Points: :: {ship_profile['points']}/{ship_profile['points_required']}\n" \
                      f"• Server Rank:  :: {rank}\n" \
                      f"• Rewards       :: {rewards}" \
                      f"```"

        embed = discord.Embed(color=query1.colour, description=description)
        embed.set_author(
            name=f"{ship_profile['ship_name']}",
            icon_url=self.client.get_user(int(ship_profile["shipper1"])).avatar_url
        )
        embed.set_thumbnail(url=self.client.get_user(int(ship_profile['shipper2'])).avatar_url)
        await ctx.channel.send(embed=embed)

    @commands.command(aliases=["sail"])
    @commands.guild_only()
    async def friendship_check_sail(self, ctx):

        request = ships.find({"level": {"$gt": 1}, "code": {"$regex": f".*{ctx.author.id}.*"}})
        ships_count = request.count()
        total_rewards = 0

        for ship in request:
            total_rewards += ship["level"] * 25

        noun = pluralize("ship", ships_count)
        embed = discord.Embed(
            color=ctx.author.colour,
            description=f"Total daily ship sail rewards: {total_rewards:,d}{e_j}"
        )
        embed.set_footer(
            text=f"{ships_count} {noun}",
            icon_url=ctx.author.avatar_url
        )
        await ctx.channel.send(embed=embed)

    @commands.command(aliases=["ships"])
    @commands.guild_only()
    async def friendship_ship_show_all(self, ctx, *, member: discord.Member = None):

        if member is None:
            await self.friendship_ship_show_generate(ctx.author, ctx)

        else:
            await self.friendship_ship_show_generate(member, ctx)

    async def friendship_ship_show_generate(self, member, ctx):

        ships_listings = []
        for ship in ships.find({"code": {"$regex": f".*{member.id}.*"}}):
            ship_entry = [ship["shipper1"], ship["shipper2"], ship["ship_name"], ship["level"]]
            ships_listings.append(ship_entry)

        await self.friendship_ship_show_paginate(ships_listings, member, ctx)

    async def friendship_ship_show_paginate(self, formatted_list, member, ctx):

        page = 1
        max_lines = 5
        page_total = ceil(len(formatted_list) / max_lines)
        if page_total == 0:
            page_total = 1

        def create_new_embed_page(page_new):
            end = page_new * 5
            start = end - 5
            total_ships = len(formatted_list)

            embed = discord.Embed(
                color=member.colour,
                title=f"🚢 {member.display_name}'s ships [{total_ships} {pluralize('ship', total_ships)}]",
                timestamp=get_timestamp()
            )
            embed.set_footer(text=f"Page {page_new} of {page_total}")

            while start < end:
                try:
                    embed.add_field(
                        name=f"{formatted_list[start][2]}, level {formatted_list[start][3]}",
                        value=f"<@{formatted_list[start][0]}> & <@{formatted_list[start][1]}>",
                        inline=False
                    )
                    start += 1
                except IndexError:
                    break
            return embed

        def check_pagination(r, u):
            return u != self.client.user and r.message.id == msg.id

        msg = await ctx.channel.send(embed=create_new_embed_page(page))
        await msg.add_reaction("⬅")
        await msg.add_reaction("➡")

        while True:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=180, check=check_pagination)
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

    @commands.command(aliases=["ship"])
    @commands.guild_only()
    async def friendship_ship(self, ctx, query1: discord.Member = None, query2: discord.Member = None):

        try:
            if query1 is None and query2 is None:
                embed = discord.Embed(
                    title="ship, ships", colour=discord.Colour(embed_color),
                    description="shows a ship profile or your own ships\nto change your ship's name use *`;fpchange`*"
                )
                embed.add_field(
                    name="Formats",
                    value="*• `;ship <@member>`*\n"
                          "*• `;ship <@member> <@member>`*\n"
                          "*• `;ships`*"
                )
                await ctx.channel.send(embed=embed)

            elif query1 is not None and query2 is None:
                code = get_bond(ctx.author, query1)
                await self.friendship_post_ship(code, query1, ctx)

            elif query1 is not None and query2 is not None:
                code = get_bond(query1, query2)
                await self.friendship_post_ship(code, query1, ctx)

        except TypeError:
            embed = discord.Embed(
                colour=discord.Colour(embed_color),
                title="Invalid ship",
                description=f"{ctx.author.mention}, I'm sorry, but that ship has sunk before it was built."
            )
            await ctx.channel.send(embed=embed)

    @commands.command(aliases=["friendship", "fp"])
    @commands.guild_only()
    async def friendship_give(self, ctx, *, receiver: discord.Member = None):

        giver = ctx.author
        profile = users.find_one({"user_id": str(giver.id)}, {"_id": 0, "friendship_pass": 1})

        if receiver is None:
            embed = discord.Embed(
                title="friendship, fp", colour=discord.Colour(embed_color),
                description="sends and receives friendship & builds ship that earns daily reward\n"
                            "built ships are shown using *`;ship`*"
            )
            embed.add_field(
                name="Mechanics",
                value="```"
                      "• Send hearts      ::  + 5\n"
                      " * added ship exp  ::  + 5\n\n"
                      "• Confirm receipt < 2 min"
                      "\n * Receiver        ::  + 3"
                      "\n * added ship exp  ::  + 3```",
                inline=False
            )
            embed.add_field(name="Format", value="*`;friendship <@member>`*", inline=False)
            await ctx.channel.send(embed=embed)

        elif receiver.bot is True or receiver == ctx.author:
            return

        elif profile["friendship_pass"] < 1:
            embed = discord.Embed(
                colour=discord.Colour(embed_color),
                title="Insufficient friendship passes",
                description=f"{giver.mention}, you have used up all your friendship passes"
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

            if ships.find_one({"code": code}, {"_id": 0}) is None:
                profile = {
                    "code": code,
                    "shipper1": str(ctx.author.id),
                    "shipper2": str(receiver.id),
                    "ship_name": f"{giver.name} and {receiver.name}'s ship",
                    "level": 1,
                    "points": 0,
                    "points_required": 50
                }
                ships.insert_one(profile)

            ships.update_one({"code": code}, {"$inc": {"points": 5}})
            users.update_one({"user_id": str(giver.id)}, {"$inc": {"friendship": 5}})
            await ctx.message.add_reaction(f"{e_f.replace('<', '').replace('>', '')}")

            def check(r, u):
                return u.id == receiver.id and str(r.emoji) == e_f and r.message.id == ctx.message.id

            try:
                await self.client.wait_for("reaction_add", timeout=120, check=check)
            except asyncio.TimeoutError:
                await self.friendship_check_levelup(ctx, code, giver)
                await ctx.message.clear_reactions()
            else:
                ships.update_one({"code": code, "level": {"$lt": 5}}, {"$inc": {"points": 3}})
                await self.friendship_check_levelup(ctx, code, giver)
                users.update_one({"user_id": str(receiver.id)}, {"$inc": {"friendship": 3}})
                await ctx.message.clear_reactions()
                await ctx.message.add_reaction("✅")

    @commands.command(aliases=["fpchange", "fpc"])
    @commands.guild_only()
    async def friendship_change_name(self, ctx, receiver: discord.Member = None, *, new_name=None):

        embed = discord.Embed(
            title="fpchange, fpc", colour=discord.Colour(embed_color),
            description="changes your ship name with the mentioned member"
        )
        embed.add_field(name="Format", value="*• `;fpc <@member> <ship name>`*")

        if new_name is None:
            await ctx.channel.send(embed=embed)

        try:
            code = get_bond(ctx.author, receiver)
            ships.update_one({"code": code}, {"$set": {"ship_name": new_name}})
            await self.friendship_post_ship(code, ctx.author, ctx)

        except AttributeError:
            await ctx.channel.send(embed=embed)


def setup(client):
    client.add_cog(Friendship(client))
