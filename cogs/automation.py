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

        for entry in books.find({}, {"_id": 0, "server": 1, "prefects": 1}):
            server = entry["server"]
            role_bathroom = discord.utils.get(self.client.get_guild(int(server)).roles, name="🚿")

            if len(role_bathroom.members) == 0:
                return

            else:
                for member in role_bathroom.members:
                    await member.remove_roles(role_bathroom)

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
        await ctx.channel.send("Re-arranging..")

        guild_id = ctx.guild.id
        server = books.find_one({"server": str(guild_id)}, {"_id": 0, "castle": 1, "prefects": 1})
        castle_id = server["castle"]

        castle = self.client.get_channel(int(castle_id))
        prefects = self.client.get_channel(int(server["prefects"]))

        for channel in castle.text_channels:
            new_floor = random.randint(1, len(castle.text_channels)) - 1
            await channel.edit(position=new_floor)
            await asyncio.sleep(1)

        await prefects.edit(position=7)
        await asyncio.sleep(5)
        await self.change_topic_floor(castle_id, prefects)

    async def change_topic_floor(self, castle_id, prefects):
        ordinal = lambda n: "%d%s" % (n, "tsnrhtdd"[(n // 10 % 10 != 1) * (n % 10 < 4) * n % 10::4])
        new_castle = self.client.get_channel(int(castle_id))

        i = 0
        while i < len(new_castle.text_channels):

            if new_castle.text_channels[i].name != "prefects-bathroom":
                channel_topic = new_castle.text_channels[i].topic[12:]
                floor = i + 1
                await new_castle.text_channels[i].edit(topic=f"{ordinal(floor)} Floor -\n{channel_topic}")
                print(f"{ordinal(floor)} Floor -\n{channel_topic}")
                i += 1

            else:
                i += 1

        await prefects.edit(position=5)

    # Whenever a shard post is pinned/edited
    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):

        if "pinned" not in payload.data:
            return

        elif payload.data["pinned"] is True:
            try:
                request = books.find_one({"server": f"{payload.data['guild_id']}"},
                                         {"_id": 0, "shard-trading": 1, "headlines": 1})

                if str(payload.data["channel_id"]) == request["shard-trading"]:
                    time_stamp = datetime.now(tz=tz_target).strftime("%b %d, %Y %I:%M EST")
                    headlines = self.client.get_channel(int(request["headlines"]))
                    user = self.client.get_user(int(payload.data["author"]["id"]))
                    shard_trading = self.client.get_channel(int(request["shard-trading"]))

                    embed = discord.Embed(color=0xffff80, title=f"{user.name} is looking for shards!",
                                          description=f"{payload.data['content']}")

                    if len(payload.data["attachments"]) != 0:
                        embed.set_image(url=payload.data["attachments"][0]["url"])

                    embed.set_thumbnail(url=user.avatar_url)
                    embed.set_footer(text=f"#{shard_trading.name} | {time_stamp}")
                    await headlines.send(embed=embed)

            except KeyError:
                print(payload.data["author"]["id"])

    # Whenever a member joins
    @commands.Cog.listener()
    async def on_member_join(self, member):
        time_stamp = datetime.now(tz=tz_target).strftime("%b %d, %Y %m:%M EST")
        request = books.find_one({"server": f"{member.guild.id}"},
                                 {"_id": 0, "welcome": 1, "sorting": 1, "landing_zone": 1, "scroll-of-everything": 1,
                                  "default_role": 1})
        landing_zone = self.client.get_channel(int(request["landing_zone"]))
        record_scroll = self.client.get_channel(int(request["scroll-of-everything"]))

        # Sets default role
        default_role2 = member.guild.get_role(int(request["default_role"]))
        await member.add_roles(default_role2)

        # Landing Zone
        msg = f":sparkles:Welcome to Patronus, {member.mention}. Kindly read your acceptance letter first"
        await landing_zone.send(msg)

        # Acceptance Letter
        description = f"Dear {member.display_name},\n\nWe are pleased to accept you at House Patronus.\nDo browse " \
            f"the server's <#{request['welcome']}> channel for the basics and essentials of the guild then " \
            f"proceed to <#{request['sorting']}> to assign yourself some roles.\n\nWe await your return owl.\n\n" \
            f"Yours Truly,\nThe Headmaster "
        embed = discord.Embed(color=0xffff80, title=":love_letter: Acceptance Letter", description=description)
        await member.send(embed=embed)

        # Scroll of Everything
        embed = discord.Embed(color=0xffffff)
        embed.set_author(name=f"{member.display_name} has joined the house!")
        embed.set_footer(text=f"{member.guild.member_count} members | {time_stamp}", icon_url=member.avatar_url)
        await record_scroll.send(embed=embed)

    # Whenever a member leaves
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        users.delete_one({"user_id": str(member.id)})
        time_stamp = datetime.now(tz=tz_target).strftime("%b %d, %Y %m:%M EST")
        request = books.find_one({"server": str(member.guild.id)}, {"_id": 0, "scroll-of-everything": 1})
        record_scroll = self.client.get_channel(int(request["scroll-of-everything"]))

        embed = discord.Embed(color=0xffffff)
        embed.set_author(name=f"{member.display_name} has left the house!")
        embed.set_footer(text=f"{member.guild.member_count} members | {time_stamp}", icon_url=member.avatar_url)
        await record_scroll.send(embed=embed)

    # Spying members
    @commands.Cog.listener()
    async def on_member_update(self, before, after):

        time_stamp = datetime.now(tz=tz_target).strftime("%b %d, %Y %m:%M EST")
        request = books.find_one({"server": str(before.guild.id)},
                                 {"_id": 0, "scroll-of-everything": 1, "auror-department": 1})
        record_scroll = self.client.get_channel(int(request["scroll-of-everything"]))

        if before.roles != after.roles:
            changed_role1 = list(set(after.roles) - set(before.roles))
            changed_role2 = list(set(before.roles) - set(after.roles))

            if not changed_role1:
                embed = discord.Embed(color=0x50e3c2,
                                      title=f"Removed {changed_role2[0].display_name} role for {after.display_name}")
                embed.set_footer(text=f"{time_stamp}", icon_url=before.avatar_url)

                await record_scroll.send(embed=embed)

            elif not changed_role2:
                embed = discord.Embed(color=0x50e3c2,
                                      title=f"Added {changed_role1[0].display_name} role for {after.display_name}")
                embed.set_footer(text=f"{time_stamp}", icon_url=before.avatar_url)

                await record_scroll.send(embed=embed)

                if changed_role1[0].name == "Auror":

                    auror_channel = self.client.get_channel(int(request["auror-department"]))
                    embed = discord.Embed(color=0x50e3c2,
                                          title=f"{before.display_name} has been promoted to :fleur_de_lis: Auror")
                    embed.set_footer(text=f"{time_stamp}", icon_url=before.avatar_url)
                    await auror_channel.send(embed=embed)

        elif before.nick != after.nick:

            embed = discord.Embed(color=0x7ed321)
            embed.set_footer(text=f"{time_stamp}", icon_url=before.avatar_url)
            embed.add_field(name="Before | New nickname:", value=f"{before.display_name} | {after.display_name}")

            await record_scroll.send(embed=embed)


def setup(client):
    client.add_cog(Events(client))
