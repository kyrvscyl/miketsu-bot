"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
from datetime import datetime

import discord
import pytz
from discord.ext import commands

from cogs.mongo.db import books, users

# Timezone
tz_target = pytz.timezone("America/Atikokan")


class Events(commands.Cog):

    def __init__(self, client):
        self.client = client

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
        description = f"Dear {member.name},\n\nWe are pleased to accept you at House Patronus.\nDo browse " \
            f"the server's <#{request['welcome']}> channel for the basics and essentials of the guild then " \
            f"proceed to <#{request['sorting']}> to assign yourself some roles.\n\nWe await your return owl.\n\n" \
            f"Yours Truly,\nThe Headmaster "
        embed = discord.Embed(color=0xffff80, title=":love_letter: Acceptance Letter", description=description)
        await member.send(embed=embed)

        # Scroll of Everything
        embed = discord.Embed(color=0xffffff)
        embed.set_author(name=f"{member.name} has joined the house!")
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
        embed.set_author(name=f"{member.name} has left the house!")
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
                embed = discord.Embed(color=0x50e3c2, title=f"Removed {changed_role2[0].name} role for {after.name}")
                embed.set_footer(text=f"{time_stamp}", icon_url=before.avatar_url)
                await record_scroll.send(embed=embed)

            elif not changed_role2:
                embed = discord.Embed(color=0x50e3c2, title=f"Added {changed_role1[0].name} role for {after.name}")
                embed.set_footer(text=f"{time_stamp}", icon_url=before.avatar_url)
                await record_scroll.send(embed=embed)

                if changed_role1[0].name == "Auror":

                    if before.nick is None:
                        name = before.name
                    else:
                        name = before.nick

                    auror_channel = self.client.get_channel(int(request["auror-department"]))
                    embed = discord.Embed(color=0x50e3c2,
                                          title=f"{name} has been promoted to :fleur_de_lis: Auror")
                    embed.set_footer(text=f"{time_stamp}", icon_url=before.avatar_url)
                    await auror_channel.send(embed=embed)

        elif before.nick != after.nick:
            embed = discord.Embed(color=0x7ed321)
            embed.set_footer(text=f"{time_stamp}", icon_url=before.avatar_url)

            if before.nick is None:
                embed.add_field(name="Before | New nickname:", value=f"{before.name} | {after.nick}")
            else:
                embed.add_field(name="Before | New nickname:", value=f"{before.nick} | {after.nick}")

            await record_scroll.send(embed=embed)


def setup(client):
    client.add_cog(Events(client))
