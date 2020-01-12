"""
Raid Module
Miketsu, 2020
"""

import asyncio

from discord.ext import commands

from cogs.ext.initialize import *


class Raid(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.prefix = self.client.command_prefix

    def calculate(self, x, y, z):
        try:
            if x - y > 0:
                return ((x - y) / x) * z
            elif x - y < 0:
                return -((y - x) / y) * z
            else:
                return 0
        except ZeroDivisionError:
            return 0

    def get_raid_chance(self, raider, victim):

        raider_stats = users.find_one({
            "user_id": str(raider.id)}, {
            "_id": 0, "level": 1, "medals": 1, "SP": 1, "SSR": 1, "SR": 1, "R": 1
        })
        victim_stats = users.find_one({
            "user_id": str(victim.id)}, {
            "_id": 0, "level": 1, "medals": 1, "SP": 1, "SSR": 1, "SR": 1, "R": 1
        })

        criteria_raid_success = [
            ["level", 0.15], ["medals", 0.15], ["SP", 0.09], ["SSR", 0.07], ["SR", 0.03], ["R", 0.01],
        ]

        chance_added = 0
        for criterion in criteria_raid_success:
            chance_added += self.calculate(raider_stats[criterion[0]], victim_stats[criterion[0]], criterion[1])

        return round((0.5 + chance_added) * 100)

    def get_raid_count(self, victim):
        return users.find_one({"user_id": str(victim.id)}, {"_id": 0, "raided_count": 1})["raided_count"]

    @commands.command(aliases=["raidable", "rdb"])
    @commands.guild_only()
    async def raid_perform_check_users(self, ctx):

        listings_raidable, listings_raidable_formatted = [], []

        for member in users.find({"raided_count": {"$lt": 3}}, {"user_id": 1, "level": 1, "raided_count": 1}):
            try:
                member_name = ctx.guild.get_member(int(member["user_id"]))
                if member_name is not None:
                    listings_raidable.append((member_name, member["level"], member["raided_count"]))
            except AttributeError:
                continue

        for member in sorted(listings_raidable, key=lambda x: x[1], reverse=True):
            listings_raidable_formatted.append(
                f"• `lvl.{lengthen_code_2(member[1])}`, `{member[2]}/3` | {member[0]}\n"
            )

        await self.raid_perform_check_users_paginate("Available Realms", ctx, listings_raidable_formatted)

    async def raid_perform_check_users_paginate(self, title, ctx, listings_formatted):

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
            return msg.id == r.message.id and str(r.emoji) in emojis_add and u.id == ctx.author.id

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

    async def raid_perform_help(self, ctx):

        embed = discord.Embed(
            title="raid, r", colour=colour,
            description="raids the tagged member, requires 1 🎟"
        )
        embed.add_field(
            name="Formats", inline=False,
            value=f"*`{self.prefix}raid @member`*\n"
                  f"*`{self.prefix}r <name#discriminator>`*",
        )
        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["raid", "r"])
    @commands.check(check_if_user_has_raid_tickets)
    @commands.guild_only()
    async def raid_perform(self, ctx, *, victim: discord.Member = None):

        if victim is None:
            await self.raid_perform_help(ctx)

        elif victim.name == ctx.author.name:
            await process_msg_reaction_add(ctx.message, "❌")

        elif victim.bot or victim.id == ctx.author.id:
            return

        else:
            try:
                raid_count = self.get_raid_count(victim)
            except (AttributeError, TypeError):
                raise discord.ext.commands.BadArgument(ctx.author)
            else:

                if raid_count >= 3:
                    embed = discord.Embed(
                        colour=victim.colour, description="Raids are capped at 3 times per day and per realm"
                    )
                    embed.set_author(name="Realm is under protection", icon_url=victim.avatar_url)
                    await process_msg_submit(ctx.channel, None, embed)

                elif raid_count < 4:

                    raider = ctx.author
                    raider_medals = users.find_one({"user_id": str(raider.id)}, {"_id": 0, "level": 1})["level"]
                    victim_medals = users.find_one({"user_id": str(victim.id)}, {"_id": 0, "level": 1})["level"]
                    level_diff = raider_medals - victim_medals
                    range_diff = 60

                    if abs(level_diff) <= range_diff:
                        users.update_one({"user_id": str(victim.id)}, {"$inc": {"raided_count": 1}})
                        users.update_one({"user_id": str(raider.id)}, {"$inc": {"realm_ticket": -1}})
                        await self.raid_perform_attack(victim, raider, ctx)
                        await perform_add_log("realm_ticket", -1, raider.id)

                    else:
                        embed = discord.Embed(
                            title=f"Invalid chosen realm", colour=raider.colour,
                            description=f"You can only raid realms with ±{range_diff:,d} of your level",
                        )
                        await process_msg_submit(ctx.channel, None, embed)

    async def raid_perform_attack(self, victim, raider, ctx):

        try:
            total_chance = self.get_raid_chance(raider, victim)

        except (KeyError, TypeError):
            raise discord.ext.commands.BadArgument(ctx.author)

        else:

            if random.uniform(0, 100) <= total_chance:
                coins, jades, medals, experience = 25000, 50, 25, 40
                embed = discord.Embed(
                    title="Realm raid", color=raider.colour, timestamp=get_timestamp(),
                    description=f"{raider.mention} raids {victim.display_name}'s realm!",
                )
                embed.add_field(
                    name=f"Results, `{total_chance}%`",
                    value=f"{raider.display_name} won!\n"
                          f"{coins:,d}{e_c}, {jades:,d}{e_j}, {medals:,d}{e_m}"
                )
                embed.set_footer(text=raider.display_name, icon_url=raider.avatar_url)
                await self.raid_perform_attack_giverewards_as_winner_raider(raider, coins, jades, medals, experience)
                await process_msg_submit(ctx.channel, None, embed)

            else:
                coins, jades, medals, experience = 50000, 100, 50, 20
                embed = discord.Embed(
                    title="Realm raid", color=raider.colour, timestamp=get_timestamp(),
                    description=f"{raider.mention} raids {victim.display_name}'s realm!",
                )
                embed.add_field(
                    name=f"Results, `{total_chance}%`",
                    value=f"{victim.display_name} won!\n"
                          f"{coins:,d}{e_c}, {jades:,d}{e_j}, {medals:,d}{e_m}"
                )
                embed.set_footer(text=raider.display_name, icon_url=raider.avatar_url)
                await self.raid_perform_attack_giverewards_as_winner_victim(
                    victim, raider, coins, jades, medals, experience
                )
                await process_msg_submit(ctx.channel, None, embed)

    async def raid_perform_attack_giverewards_as_winner_victim(self, victim, raider, coins, jades, medals, experience):

        users.update_one({"user_id": str(raider.id), "level": {"$lt": 60}}, {"$inc": {"experience": experience}})
        users.update_one({"user_id": str(victim.id)}, {"$inc": {"coins": coins, "jades": jades, "medals": medals}})

        await perform_add_log("coins", coins, victim.id)
        await perform_add_log("jades", jades, victim.id)
        await perform_add_log("medals", medals, victim.id)

    async def raid_perform_attack_giverewards_as_winner_raider(self, raider, coins, jades, medals, experience):

        users.update_one({"user_id": str(raider.id), "level": {"$lt": 60}}, {"$inc": {"experience": experience}})
        users.update_one({"user_id": str(raider.id)}, {"$inc": {"coins": coins, "jades": jades, "medals": medals}})

        await perform_add_log("coins", coins, raider.id)
        await perform_add_log("jades", jades, raider.id)
        await perform_add_log("medals", medals, raider.id)

    async def raid_perform_calculation_help(self, ctx):

        embed = discord.Embed(
            title="raidcalc, raidc, rc", colour=colour,
            description="calculates your odds of winning"
        )
        embed.add_field(
            name="Mechanics", inline=False,
            value="```"
                  "Base Chance :: + 50 %\n"
                  "Δ Level     :: ± 15 %\n"
                  "Δ Medal     :: ± 15 %\n"
                  "Δ SP        :: ±  9 %\n"
                  "Δ SSR       :: ±  7 %\n"
                  "Δ SR        :: ±  3 %\n"
                  "Δ R         :: ±  1 %\n"
                  "```",
        )
        embed.add_field(
            name="Formats", inline=False,
            value=f"*`{self.prefix}raidc @member`*\n"
                  f"*`{self.prefix}rc <name#discriminator>`*",
        )
        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["raidcalc", "raidc", "rc"])
    @commands.guild_only()
    async def raid_perform_calculation(self, ctx, *, victim: discord.Member = None):

        if victim is None:
            await self.raid_perform_calculation_help(ctx)

        elif victim == ctx.author or victim.bot is True:
            return

        elif victim != ctx.author:
            await self.raid_perform_calculation_submit(victim, ctx.author, ctx)

    async def raid_perform_calculation_submit(self, victim, raider, ctx):

        try:
            total_chance = self.get_raid_chance(raider, victim)

        except (KeyError, TypeError):
            raise discord.ext.commands.BadArgument(ctx.author)

        else:
            embed = discord.Embed(
                color=raider.colour, timestamp=get_timestamp(),
                title=f"{raider.display_name} vs {victim.display_name} :: {total_chance}%"
            )
            await process_msg_submit(ctx.channel, None, embed)


def setup(client):
    client.add_cog(Raid(client))
