"""
Raid Module
Miketsu, 2020
"""
import asyncio
from math import ceil

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

    def get_raid_count(self, victim):
        return users.find_one({"user_id": str(victim.id)}, {"_id": 0, "raided_count": 1})["raided_count"]

    @commands.command(aliases=["raidable", "rdb"])
    @commands.guild_only()
    async def raid_perform_check_users(self, ctx):

        listings_raidable = []
        listings_raidable_formatted = []

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

        page = 1
        max_lines = 15
        page_total = ceil(len(listings_formatted) / max_lines)
        if page_total == 0:
            page_total = 1

        def embed_new_create(page_new):
            end = page * max_lines
            start = end - max_lines
            description = "".join(listings_formatted[start:end])

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
            return msg.id == r.message.id and \
                   str(r.emoji) in emoji_arrows and \
                   u.id == ctx.author.id

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
                await process_msg_reaction_remove(msg, str(reaction.emoji), user)

    @commands.command(aliases=["raid", "r"])
    @commands.check(check_if_user_has_raid_tickets)
    @commands.guild_only()
    async def raid_perform(self, ctx, *, victim: discord.Member = None):

        if victim is None:
            raise discord.ext.commands.MissingRequiredArgument(ctx.author)

        elif victim.name in ctx.author.name:
            await process_msg_reaction_add(ctx.message, "❌")

        elif victim.bot or victim.id == ctx.author.id:
            return

        else:
            try:
                raid_count = self.get_raid_count(victim)

                if raid_count >= 3:
                    embed = discord.Embed(
                        colour=colour,
                        description="raids are capped at 3 times per day and per realm"
                    )
                    embed.set_author(
                        name="Realm is under protection",
                        icon_url=victim.avatar_url
                    )
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
                            title=f"Invalid chosen realm", colour=colour,
                            description=f"You can only raid realms with ±{range_diff:,d} of your level",
                        )
                        await process_msg_submit(ctx.channel, None, embed)

            except AttributeError:
                raise discord.ext.commands.BadArgument(ctx.author)
            except TypeError:
                raise discord.ext.commands.BadArgument(ctx.author)

    async def raid_perform_attack(self, victim, raider, ctx):
        try:
            profile_raider = users.find_one({
                "user_id": str(raider.id)}, {
                "_id": 0, "level": 1, "medals": 1, "SP": 1, "SSR": 1, "SR": 1, "R": 1
            })
            profile_victim = users.find_one({
                "user_id": str(victim.id)}, {
                "_id": 0, "level": 1, "medals": 1, "SP": 1, "SSR": 1, "SR": 1, "R": 1
            })

            chance1 = self.calculate(profile_raider["level"], profile_victim["level"], 0.15)
            chance2 = self.calculate(profile_raider["medals"], profile_victim["medals"], 0.15)
            chance3 = self.calculate(profile_raider["SP"], profile_victim["SP"], 0.09)
            chance4 = self.calculate(profile_raider["SSR"], profile_victim["SSR"], 0.07)
            chance5 = self.calculate(profile_raider["SR"], profile_victim["SR"], 0.03)
            chance6 = self.calculate(profile_raider["R"], profile_victim["R"], 0.01)
            total_chance = round((0.5 + chance1 + chance2 + chance3 + chance4 + chance5 + chance6) * 100)
            roll = random.uniform(0, 100)

            if roll <= total_chance:
                coins, jades, medals, exp = 25000, 50, 25, 40
                embed = discord.Embed(
                    title="Realm raid", color=raider.colour,
                    description=f"{raider.mention} raids {victim.display_name}'s realm!",
                    timestamp=get_timestamp()
                )
                embed.add_field(
                    name=f"Results, `{total_chance}%`",
                    value=f"{raider.display_name} won!\n"
                          f"{coins:,d}{e_c}, {jades:,d}{e_j}, {medals:,d}{e_m}"
                )
                embed.set_footer(text=raider.display_name, icon_url=raider.avatar_url)
                await self.raid_perform_attack_giverewards_as_winner_raider(raider, coins, jades, medals, exp)
                await process_msg_submit(ctx.channel, None, embed)

            else:
                coins, jades, medals, exp = 50000, 100, 50, 20
                embed = discord.Embed(
                    title="Realm raid", color=raider.colour,
                    description=f"{raider.mention} raids {victim.display_name}'s realm!",
                    timestamp=get_timestamp()
                )
                embed.add_field(
                    name=f"Results, `{total_chance}%`",
                    value=f"{victim.display_name} won!\n"
                          f"{coins:,d}{e_c}, {jades:,d}{e_j}, {medals:,d}{e_m}"
                )
                embed.set_footer(text=raider.display_name, icon_url=raider.avatar_url)
                await self.raid_perform_attack_giverewards_as_winner_victim(victim, raider, coins, jades, medals, exp)
                await process_msg_submit(ctx.channel, None, embed)

        except KeyError:
            raise discord.ext.commands.BadArgument(ctx.author)

        except TypeError:
            return

    async def raid_perform_attack_giverewards_as_winner_victim(self, victim, raider, coins, jades, medals, exp):
        users.update_one({"user_id": str(raider.id), "level": {"$lt": 60}}, {"$inc": {"experience": exp}})
        users.update_one({"user_id": str(victim.id)}, {"$inc": {"coins": coins, "jades": jades, "medals": medals}})

        await perform_add_log("coins", coins, victim.id)
        await perform_add_log("jades", jades, victim.id)
        await perform_add_log("medals", medals, victim.id)

    async def raid_perform_attack_giverewards_as_winner_raider(self, raider, coins, jades, medals, exp):
        users.update_one({"user_id": str(raider.id), "level": {"$lt": 60}}, {"$inc": {"experience": exp}})
        users.update_one({"user_id": str(raider.id)}, {"$inc": {"coins": coins, "jades": jades, "medals": medals}})

        await perform_add_log("coins", coins, raider.id)
        await perform_add_log("jades", jades, raider.id)
        await perform_add_log("medals", medals, raider.id)

    @commands.command(aliases=["raidcalc", "raidc", "rc"])
    @commands.guild_only()
    async def raid_perform_calculation(self, ctx, *, victim: discord.Member = None):

        if victim is None:
            raise discord.ext.commands.MissingRequiredArgument(ctx.author)

        elif victim == ctx.author or victim.bot is True:
            return

        elif victim != ctx.author:
            await self.raid_perform_calculation_submit(victim, ctx.author, ctx)

    async def raid_perform_calculation_submit(self, victim, raider, ctx):
        try:
            profile_raider = users.find_one({
                "user_id": str(raider.id)}, {
                "_id": 0, "level": 1, "medals": 1, "SP": 1, "SSR": 1, "SR": 1, "R": 1
            })
            profile_victim = users.find_one({
                "user_id": str(victim.id)}, {
                "_id": 0, "level": 1, "medals": 1, "SP": 1, "SSR": 1, "SR": 1, "R": 1
            })

            chance1 = self.calculate(profile_raider["level"], profile_victim["level"], 0.15)
            chance2 = self.calculate(profile_raider["medals"], profile_victim["medals"], 0.15)
            chance3 = self.calculate(profile_raider["SP"], profile_victim["SP"], 0.09)
            chance4 = self.calculate(profile_raider["SSR"], profile_victim["SSR"], 0.07)
            chance5 = self.calculate(profile_raider["SR"], profile_victim["SR"], 0.03)
            chance6 = self.calculate(profile_raider["R"], profile_victim["R"], 0.01)
            total_chance = round((0.5 + chance1 + chance2 + chance3 + chance4 + chance5 + chance6) * 100)

            embed = discord.Embed(
                color=raider.colour,
                title=f"{raider.display_name} vs {victim.display_name} :: {total_chance}%"
            )
            await process_msg_submit(ctx.channel, None, embed)

        except KeyError:
            raise discord.ext.commands.BadArgument(ctx.author)

        except TypeError:
            return


def setup(client):
    client.add_cog(Raid(client))
