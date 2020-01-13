"""
Friendship Module
Miketsu, 2020
"""

import asyncio
from datetime import timedelta
from itertools import cycle

from discord.ext import commands

from cogs.ext.initialize import *


class Friendship(commands.Cog):

    def __init__(self, client):

        self.client = client
        self.prefix = self.client.command_prefix

        self.summon_captions = cycle(listings_1["summon_captions"])

    @commands.command(aliases=["sail"])
    @commands.guild_only()
    async def friendship_check_sail(self, ctx, *, member: discord.Member = None):

        if member is None:
            await self.friendship_check_sail_post(ctx.author, ctx.channel)

        else:
            await self.friendship_check_sail_post(member, ctx.channel)

    async def friendship_check_sail_post(self, user, channel):

        find_query = {"level": {"$gt": 1}, "code": {"$regex": f".*{user.id}.*"}}
        query = ships.find(find_query, {"_id": 0})
        ships_count = ships.count_documents(find_query)
        total_rewards = 0

        for ship in query:
            total_rewards += ship["level"] * 25

        embed = discord.Embed(
            color=user.colour, timestamp=get_timestamp(),
            description=f"Your total daily ship sail rewards: {total_rewards:,d}{e_j}",
        )
        embed.set_footer(
            text=f"{ships_count} {pluralize('ship', ships_count)}",
            icon_url=user.avatar_url
        )
        await process_msg_submit(channel, None, embed)

    @commands.command(aliases=["ships"])
    @commands.guild_only()
    async def friendship_ship_show_all(self, ctx, *, member: discord.Member = None):

        if member is None:
            await self.friendship_ship_show_generate(ctx.author, ctx)

        else:
            await self.friendship_ship_show_generate(member, ctx)

    async def friendship_ship_show_generate(self, member, ctx):

        listings_formatted = []
        for ship in ships.find({"code": {"$regex": f".*{member.id}.*"}}, {"_id": 0}):
            ship_entry = [ship["shipper1"], ship["shipper2"], ship["ship_name"], ship["level"], ship['cards']]
            listings_formatted.append(ship_entry)

        await self.friendship_ship_show_paginate(listings_formatted, member, ctx)

    async def friendship_ship_show_paginate(self, listings_formatted, member, ctx):

        page, max_lines = 1, 5
        page_total = ceil(len(listings_formatted) / max_lines)
        if page_total == 0:
            page_total = 1

        def embed_new_create(page_new):
            end = page_new * 5
            start = end - 5
            total_ships = len(listings_formatted)

            embed_new = discord.Embed(
                color=member.colour, timestamp=get_timestamp(),
                title=f"🚢 {member.display_name}'s ships [{total_ships} {pluralize('ship', total_ships)}]",
            )
            embed_new.set_footer(
                text=f"Page {page_new} of {page_total}",
                icon_url=member.avatar_url
            )

            while start < end:
                try:
                    caption = ""
                    timestamp = listings_formatted[start][4]["timestamp"]
                    collection = listings_formatted[start][4]["collected"]

                    if timestamp is not None and collection is False:

                        time_deployed = get_time_converted(timestamp)
                        time_deployed_delta = time_deployed + timedelta(days=1)
                        now = datetime.now(tz=pytz.timezone("UTC"))

                        if now < time_deployed_delta:
                            hours, minutes = hours_minutes(time_deployed_delta - now)
                            caption = f", `collect in {hours}h, {minutes}m`"
                        else:
                            caption = ", `claim now!`"

                    embed_new.add_field(
                        name=f"`Lvl.{listings_formatted[start][3]}` {listings_formatted[start][2]}{caption}",
                        value=f"<@{listings_formatted[start][0]}> & <@{listings_formatted[start][1]}>",
                        inline=False
                    )
                    start += 1
                except IndexError:
                    break
            return embed_new

        msg = await process_msg_submit(ctx.channel, None, embed_new_create(page))

        emojis_add = ["⬅", "➡"]
        for emoji in emojis_add:
            await process_msg_reaction_add(msg, emoji)

        def check_pagination(r, u):
            return u != self.client.user and r.message.id == msg.id and str(r.emoji) in emojis_add

        while True:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=180, check=check_pagination)
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

    @commands.command(aliases=["ship"])
    @commands.guild_only()
    async def friendship_ship(self, ctx, query1: discord.Member = None, *, query2: discord.Member = None):

        try:
            if query1 is None and query2 is None:
                embed = discord.Embed(
                    title="ship, ships", colour=colour,
                    description=f"shows a ship profile or your own list of ships\n"
                                f"to change your ship's name use *`{self.prefix}fpchange`*"
                )
                embed.add_field(
                    name="Formats", inline=False,
                    value=f"*• `{self.prefix}ship <@member>`*\n"
                          f"*• `{self.prefix}ship <@member> <@member>`*\n"
                          f"*• `{self.prefix}ships`*",
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif query1 is not None and query2 is None:
                code = get_bond(ctx.author.id, query1.id)
                await self.friendship_post_ship(code, query1, ctx)

            elif query1 is not None and query2 is not None:
                code = get_bond(query1.id, query2.id)
                await self.friendship_post_ship(code, query1, ctx)

        except TypeError:
            embed = discord.Embed(
                colour=colour,
                title="Invalid ship",
                description=f"that ship has sunk before it was even fully built"
            )
            await process_msg_submit(ctx.channel, None, embed)

    async def friendship_post_ship(self, code, query1, ctx):

        ship_profile = ships.find_one({"code": code}, {"_id": 0, })

        list_rank = []
        for entry in ships.find({}, {"code": 1, "points": 1}):
            list_rank.append((entry["code"], entry["points"]))

        rank = (sorted(list_rank, key=lambda x: x[1], reverse=True)).index((code, ship_profile["points"])) + 1

        if ship_profile['level'] > 1:
            rewards = str(ship_profile["level"] * 25) + " jades/reset"
        else:
            rewards = "Must be Level 2 & above"

        description = f"```" \
                      f"• Level:        :: {ship_profile['level']}/5\n" \
                      f"• Total Points: :: {ship_profile['points']}/{ship_profile['points_required']}\n" \
                      f"• Server Rank:  :: {rank}\n" \
                      f"• Rewards       :: {rewards}" \
                      f"```"

        embed = discord.Embed(color=query1.colour, description=description, timestamp=get_timestamp())
        embed.set_author(
            name=f"{ship_profile['ship_name']}",
            icon_url=self.client.get_user(int(ship_profile["shipper1"])).avatar_url
        )
        embed.set_thumbnail(url=self.client.get_user(int(ship_profile['shipper2'])).avatar_url)

        try:
            time_deployed = get_time_converted(ship_profile["cards"]["timestamp"])
        except TypeError:
            pass
        except AttributeError:
            pass
        else:
            time_deployed_delta = time_deployed + timedelta(days=1)
            now = datetime.now(tz=pytz.timezone("UTC"))

            if now < time_deployed_delta:
                hours, minutes = hours_minutes(time_deployed_delta - now)
                caption = f"Collect in {hours}h, {minutes}m"
            else:
                caption = "claim now!"

            embed.add_field(
                name=f"Equipped realm card",
                value=f"{ship_profile['cards']['name'].title()} | "
                      f"Grade {ship_profile['cards']['grade']} | "
                      f"{caption}"
            )

        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["friendship", "fp"])
    @commands.guild_only()
    @commands.cooldown(1, 0.5, commands.BucketType.user)
    async def friendship_give(self, ctx, *, receiver: discord.Member = None):

        giver = ctx.author
        profile = users.find_one({"user_id": str(giver.id)}, {"_id": 0, "friendship_pass": 1})

        if receiver is None:
            embed = discord.Embed(
                title="friendship, fp", colour=colour,
                description=f"sends and receives friendship & builds ship that earns daily reward\n"
                            f"built ships are shown using *`{self.prefix}ship`*"
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
            embed.add_field(name="Format", value=f"*`{self.prefix}friendship <@member>`*", inline=False)
            await process_msg_submit(ctx.channel, None, embed)

        elif receiver.bot is True or receiver == ctx.author:
            return

        elif receiver.name == giver.name:
            await process_msg_reaction_add(ctx.message, "❌")

        elif check_if_user_has_any_alt_roles(receiver):
            await process_msg_reaction_add(ctx.message, "❌")

        elif profile["friendship_pass"] < 1:
            embed = discord.Embed(
                colour=colour,
                title="Insufficient friendship passes",
                description=f"fulfill wishes or claim your dailies to obtain more"
            )
            await process_msg_submit(ctx.channel, None, embed)

        elif profile["friendship_pass"] > 0:
            code = get_bond(giver.id, receiver.id)
            users.update_one({
                "user_id": str(giver.id)}, {
                "$inc": {
                    "friendship_pass": -1
                }
            })
            await perform_add_log("friendship_pass", -1, giver)

            if ships.find_one({"code": code}, {"_id": 0}) is None:
                profile = {
                    "code": code,
                    "shipper1": str(ctx.author.id),
                    "shipper2": str(receiver.id),
                    "ship_name": f"{giver.name} and {receiver.name}'s ship",
                    "level": 1,
                    "points": 0,
                    "points_required": 50,
                    "cards": {
                        "equipped": False,
                        "name": None,
                        "grade": None,
                        "timestamp": None,
                        "collected": None
                    }
                }
                ships.insert_one(profile)

            ships.update_one({"code": code}, {"$inc": {"points": 5}})
            await self.friendship_give_check_levelup(ctx, code, giver)
            users.update_one({"user_id": str(giver.id)}, {"$inc": {"friendship": 5}})
            await perform_add_log("friendship", 5, giver)
            await ctx.message.add_reaction(f"{e_f.replace('<', '').replace('>', '')}")

            def check(r, u):
                return u.id == receiver.id and str(r.emoji) == e_f and r.message.id == ctx.message.id

            try:
                await self.client.wait_for("reaction_add", timeout=120, check=check)
            except asyncio.TimeoutError:
                await self.friendship_give_check_levelup(ctx, code, giver)
                await ctx.message.clear_reactions()
            else:
                ships.update_one({"code": code, "level": {"$lt": 5}}, {"$inc": {"points": 3}})
                await self.friendship_give_check_levelup(ctx, code, giver)
                users.update_one({"user_id": str(receiver.id)}, {"$inc": {"friendship": 3}})
                await perform_add_log("friendship", 3, receiver)
                await ctx.message.clear_reactions()
                await process_msg_reaction_add(ctx.message, "✅")

    async def friendship_give_check_levelup(self, ctx, code, giver):
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

    @commands.command(aliases=["fpchange", "fpc"])
    @commands.guild_only()
    async def friendship_change_name(self, ctx, receiver: discord.Member = None, *, new_name=None):

        embed = discord.Embed(
            title="fpchange, fpc", colour=colour,
            description="changes your ship name with the mentioned member"
        )
        embed.add_field(name="Format", value=f"*• `{self.prefix}fpc <@member> <ship name>`*")

        if new_name is None:
            await process_msg_submit(ctx.channel, None, embed)

        try:
            code = get_bond(ctx.author.id, receiver.id)
            ships.update_one({"code": code}, {"$set": {"ship_name": new_name}})
            await self.friendship_post_ship(code, ctx.author, ctx)

        except AttributeError:
            await process_msg_submit(ctx.channel, None, embed)


def setup(client):
    client.add_cog(Friendship(client))
