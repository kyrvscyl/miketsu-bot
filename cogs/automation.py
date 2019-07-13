"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
from datetime import datetime

import discord
import pytz
import random
import asyncio
from discord.ext import commands

from cogs.mongo.db import books, users

# Timezone
tz_target = pytz.timezone("America/Atikokan")


class Events(commands.Cog):

    def __init__(self, client):
        self.client = client

    async def reset_prefects(self):
        query = books.find({}, {"_id": 0, "server": 1, "prefects": 1})

        for entry in query:
            try:
                server = int(entry["server"])
                role_bathroom = discord.utils.get(self.client.get_guild(server).roles, name="🚿")

                if len(role_bathroom.members) == 0:
                    return
                elif len(role_bathroom.members) != 0:
                    for member in role_bathroom.members:
                        await member.remove_roles(role_bathroom)
            except AttributeError:
                continue

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.content.lower() != "pine fresh":
            return

        elif message.channel.position != 4:
            return

        elif message.channel.position == 4 and str(message.channel.category) == "🏰 Patronus Castle":
            role_bathroom = discord.utils.get(message.guild.roles, name="🚿")

            await message.author.add_roles(role_bathroom)

    @commands.command(aliases=["change"])
    @commands.is_owner()
    async def change_castle(self, ctx):

        server = books.find_one({"server": str(ctx.guild.id)}, {"_id": 0, "castle": 1, "prefects": 1})
        castle_id = int(server["castle"])
        prefects_id = int(server["prefects"])
        castle_category = self.client.get_channel(castle_id)
        prefects_channel = self.client.get_channel(prefects_id)

        for channel in castle_category.text_channels:
            new_floor = random.randint(1, len(castle_category.text_channels)) - 1

            await channel.edit(position=new_floor)
            await asyncio.sleep(1)

        await prefects_channel.edit(position=7)
        await asyncio.sleep(5)
        await self.change_topic_floor(castle_id, prefects_channel)

    async def change_topic_floor(self, castle_id, prefects_channel):

        ordinal = lambda n: "%d%s" % (n, "tsnrhtdd"[(n // 10 % 10 != 1) * (n % 10 < 4) * n % 10::4])
        castle_category = self.client.get_channel(castle_id)

        i = 0
        while i < len(castle_category.text_channels):
            if castle_category.text_channels[i].name != "prefects-bathroom":
                channel_topic = castle_category.text_channels[i].topic[12:]
                await castle_category.text_channels[i].edit(topic=f"{ordinal(i + 1)} Floor -\n{channel_topic}")
                i += 1

            elif castle_category.text_channels[i].name == "prefects-bathroom":
                i += 1

        await prefects_channel.edit(position=5)

    # Whenever a shard post is pinned/edited
    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):

        if "pinned" not in payload.data:
            return

        elif payload.data["pinned"] is True:

            try:
                request = books.find_one(
                    {"server": f"{payload.data['guild_id']}"},
                    {"_id": 0, "shard-trading": 1, "headlines": 1}
                )

                if str(payload.data["channel_id"]) == request["shard-trading"]:

                    time_stamp = datetime.now(tz=tz_target).strftime("%b %d, %Y %I:%M EST")
                    headlines_channel = self.client.get_channel(int(request["headlines"]))
                    user = self.client.get_user(int(payload.data["author"]["id"]))
                    shard_trading = self.client.get_channel(int(request["shard-trading"]))

                    embed = discord.Embed(
                        color=user.colour,
                        description=f"{payload.data['content']}"
                    )
                    embed.set_author(
                        name=f"{user.name} is looking for shards!",
                        icon_url=user.avatar_url
                    )
                    embed.set_footer(text=f"#{shard_trading.name} | {time_stamp}")

                    if len(payload.data["attachments"]) != 0:
                        embed.set_image(url=payload.data["attachments"][0]["url"])

                    await headlines_channel.send(embed=embed)

            except KeyError:
                return

    # Whenever a member joins
    @commands.Cog.listener()
    async def on_member_join(self, member):

        time_stamp = datetime.now(tz=tz_target).strftime("%b %d, %Y %m:%M EST")
        request = books.find_one({
            "server": f"{member.guild.id}"}, {
            "_id": 0, "welcome": 1, "sorting": 1, "landing_zone": 1, "scroll-of-everything": 1, "default_role": 1
        })

        landing_zone_channel = self.client.get_channel(int(request["landing_zone"]))
        record_scroll_channel = self.client.get_channel(int(request["scroll-of-everything"]))
        default_role = member.guild.get_role(int(request["default_role"]))
        msg = f":sparkles:Welcome to House Patronus, {member.mention}. Kindly read your acceptance letter first"

        # Welcome DM message
        description = \
            f"Dear {member.display_name},\n\n" \
            f"We are pleased to accept you at House Patronus.\n" \
            f"Do browse the server's <#{request['welcome']}> channel for the basics and essentials of the guild then " \
            f"proceed to <#{request['sorting']}> to assign yourself some roles.\n\n" \
            f"We await your return owl.\n\n" \
            f"Yours Truly,\nThe Headmaster "

        embed1 = discord.Embed(
            color=0xffff80,
            title=":envelope: Acceptance Letter",
            description=description
        )
        # Record Scroll
        embed2 = discord.Embed(color=0xffffff)
        embed2.set_author(
            name=f"{member.display_name} has joined the house!"
        )
        embed2.set_footer(
            text=f"{member.guild.member_count} members | {time_stamp}",
            icon_url=member.avatar_url
        )
        await member.add_roles(default_role)
        await landing_zone_channel.send(msg)
        await member.send(embed=embed1)
        await record_scroll_channel.send(embed=embed2)

    # Whenever a member leaves
    @commands.Cog.listener()
    async def on_member_remove(self, member):

        users.delete_one({"user_id": str(member.id)})
        time_stamp = datetime.now(tz=tz_target).strftime("%b %d, %Y %m:%M EST")
        request = books.find_one({
            "server": str(member.guild.id)}, {
            "_id": 0, "scroll-of-everything": 1
        })
        record_scroll = self.client.get_channel(int(request["scroll-of-everything"]))

        embed = discord.Embed(color=0xffffff)
        embed.set_author(name=f"{member.display_name} has left the house!")
        embed.set_footer(
            text=f"{member.guild.member_count} members | {time_stamp}",
            icon_url=member.avatar_url
        )
        await record_scroll.send(embed=embed)

    # Spying members
    @commands.Cog.listener()
    async def on_member_update(self, before, after):

        time_stamp = datetime.now(tz=tz_target).strftime("%b %d, %Y %m:%M EST")
        request = books.find_one({
            "server": str(before.guild.id)}, {
            "_id": 0, "scroll-of-everything": 1, "auror-department": 1}
        )
        record_scroll = self.client.get_channel(int(request["scroll-of-everything"]))

        if before.roles != after.roles:
            changed_role1 = list(set(after.roles) - set(before.roles))
            changed_role2 = list(set(before.roles) - set(after.roles))

            if not changed_role1:
                embed = discord.Embed(
                    color=0x50e3c2,
                    title=f"Removed {changed_role2[0].name} role for {after.display_name}"
                )
                embed.set_footer(
                    text=f"{time_stamp}",
                    icon_url=before.avatar_url
                )
                await record_scroll.send(embed=embed)

            elif not changed_role2:
                embed = discord.Embed(
                    color=0x50e3c2,
                    title=f"Added {changed_role1[0].name} role for {after.display_name}"
                )
                embed.set_footer(
                    text=f"{time_stamp}",
                    icon_url=before.avatar_url
                )
                await record_scroll.send(embed=embed)

                if changed_role1[0].name == "Auror":
                    auror_channel = self.client.get_channel(int(request["auror-department"]))
                    embed = discord.Embed(
                        color=0x50e3c2,
                        title=f"{before.display_name} has been promoted to ⚜ Auror"
                    )
                    embed.set_footer(
                        text=f"{time_stamp}",
                        icon_url=before.avatar_url
                    )
                    await auror_channel.send(embed=embed)

        elif before.nick != after.nick:
            embed = discord.Embed(color=0x7ed321)
            embed.set_footer(
                text=f"{time_stamp}",
                icon_url=before.avatar_url
            )
            embed.add_field(
                name="Before | New nickname:",
                value=f"{before.display_name} | {after.display_name}"
            )
            await record_scroll.send(embed=embed)

        elif before.name != after.name:
            embed = discord.Embed(color=0x7ed321)
            embed.set_footer(
                text=f"{time_stamp}",
                icon_url=before.avatar_url
            )
            embed.add_field(
                name="Before | New username:",
                value=f"{before.name} | {after.name}"
            )
            await record_scroll.send(embed=embed)


def setup(client):
    client.add_cog(Events(client))
