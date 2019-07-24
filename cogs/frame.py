"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import asyncio
import random

import discord
from discord.ext import commands

from cogs.mongo.db import users, streak, books
from cogs.startup import emoji_j, emoji_a

adverb = ["deliberately", "forcefully", "unknowingly", "accidentally", "dishonestly"]
verb = ["snatched", "stole", "took", "looted", "shoplifted", "embezzled"]
noun = ["custody", "care", "control", "ownership"]
comment = ["Sneaky!", "Gruesome!", "Madness!"]

spell_spam_ids = []
for document in books.find({}, {"_id": 0, "channels.spell-spam": 1}):
    try:
        spell_spam_ids.append(document["channels"]["spell-spam"])
    except KeyError:
        continue


class Frame(commands.Cog):

    def __init__(self, client):
        self.client = client


    @commands.command()
    @commands.is_owner()
    async def frame_issuance(self, ctx):

        await self.frame_automate()
        await ctx.message.delete()


    async def frame_automate(self):

        await self.frame_starlight()
        await asyncio.sleep(1)
        await self.frame_blazing()

    async def frame_starlight(self):

        for channel in spell_spam_ids:
            spell_spam_channel = self.client.get_channel(int(channel))
            guild = spell_spam_channel.guild

            starlight_role = discord.utils.get(guild.roles, name="Starlight Sky")

            streak_list = []
            for user in streak.find({}, {"_id": 0, "user_id": 1, "SSR_current": 1}):
                streak_list.append((user["user_id"], user["SSR_current"]))

            streak_list_new = sorted(streak_list, key=lambda x: x[1], reverse=True)
            starlight_new = guild.get_member(int(streak_list_new[0][0]))
            starlight_current = starlight_role.members[0]

            if len(starlight_role.members) == 0:
                await starlight_new.add_roles(starlight_role)
                await asyncio.sleep(3)

                description = \
                    f"{starlight_new.mention}\"s undying luck of not summoning an SSR has " \
                        f"earned themselves the Rare Starlight Sky Frame!\n\n" \
                        f"🍀 No SSR streak as of posting: {streak_list_new[0][1]} summons!"

                embed = discord.Embed(
                    color=0xac330f,
                    title="📨 Hall of Framers Update",
                    description=description
                )
                embed.set_thumbnail(url="https://vignette.wikia.nocookie.net/onmyoji/images/1/17/Frame7.png")
                await channel.send(embed=embed)

            if starlight_current == starlight_new:
                users.update_one({"user_id": str(starlight_current.id)}, {"$inc": {"jades": 2000}})
                msg = f"{starlight_current.mention} has earned 2,000{emoji_j} " \
                    f"for wielding the Starlight Sky frame for a day!"
                await channel.send(msg)

            else:
                await starlight_new.add_roles(starlight_role)
                await asyncio.sleep(3)
                await starlight_current.remove_roles(starlight_role)
                await asyncio.sleep(3)

                description = \
                    f"{starlight_new.mention} {random.choice(adverb)} {random.choice(verb)} " \
                        f"the Rare Starlight Sky Frame from {starlight_current.mention}\"s " \
                        f"{random.choice(noun)}!! {random.choice(comment)}\n\n" \
                        f"🍀 No SSR streak record as of posting: {streak_list_new[0][1]} summons!"

                embed = discord.Embed(
                    color=0xac330f,
                    title="📨 Hall of Framers Update",
                    description=description
                )
                embed.set_thumbnail(url="https://vignette.wikia.nocookie.net/onmyoji/images/1/17/Frame7.png")
                await channel.send(embed=embed)

    async def frame_blazing(self):

        for channel in spell_spam_ids:
            spell_spam_channel = self.client.get_channel(int(channel))
            guild = spell_spam_channel.guild

            blazing_role = discord.utils.get(guild.roles, name="Blazing Sun")

            ssr_list = []
            for user in users.find({}, {"_id": 0, "user_id": 1, "SSR": 1}):
                ssr_list.append((user["user_id"], user["SSR"]))

            ssr_list_new = sorted(ssr_list, key=lambda x: x[1], reverse=True)
            blazing_new = guild.get_member(int(ssr_list_new[0][0]))
            blazing_current = blazing_role.members[0]

            if len(blazing_role.members) == 0:
                await blazing_new.add_roles(blazing_role)
                await asyncio.sleep(3)

                description = \
                    f"{blazing_new.mention}\"s fortune luck earned themselves the Rare Blazing Sun Frame!\n\n" \
                        f"🍀 Distinct SSRs under possession: {ssr_list_new[0][1]} shikigamis"

                embed = discord.Embed(
                    color=0xac330f,
                    title="📨 Hall of Framers Update",
                    description=description
                )
                embed.set_thumbnail(url="https://vignette.wikia.nocookie.net/onmyoji/images/7/72/Frame62.png")
                await channel.send(embed=embed)

            if blazing_current == blazing_new:
                users.update_one({"user_id": str(blazing_current.id)}, {"$inc": {"amulets": 10}})
                msg = f"{blazing_current.mention} has earned 10{emoji_a} for wielding the Blazing Sun frame for a day!"
                await channel.send(msg)

            else:
                await blazing_new.add_roles(blazing_role)
                await asyncio.sleep(3)
                await blazing_current.remove_roles(blazing_role)
                await asyncio.sleep(3)

                description = f"{blazing_new.mention} {random.choice(adverb)} {random.choice(verb)} " \
                    f"the Rare Blazing Sun Frame from {blazing_current.mention}\"s {random.choice(noun)}!! " \
                    f"{random.choice(comment)}\n\n: 🍀 Distinct SSRs under possession: {ssr_list_new[0][1]} shikigamis"

                embed = discord.Embed(
                    color=0xffff80,
                    title="📨 Hall of Framers Update",
                    description=description
                )
                embed.set_thumbnail(url="https://vignette.wikia.nocookie.net/onmyoji/images/7/72/Frame62.png")
                await channel.send(embed=embed)


def setup(client):
    client.add_cog(Frame(client))
