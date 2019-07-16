"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import asyncio
import os
import random
from datetime import datetime

import discord
import pytz
from discord.ext import commands

from cogs.error import logging, get_f
from cogs.mongo.db import books, users

file = os.path.basename(__file__)[:-3:]

castles_id = []
for document in books.find({}, {"_id": 0, "categories.castle": 1}):
    try:
        castles_id.append(document["categories"]["castle"])
    except KeyError:
        continue


def get_time():
    tz_target = pytz.timezone("America/Atikokan")
    return datetime.now(tz=tz_target)


class Events(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author == self.client.user or message.author.bot:
            return

        elif message.content.lower() != "pine fresh":
            return

        elif message.channel.position != 4:
            return

        elif message.channel.position == 4 and str(message.channel.category.id) in castles_id:

            try:
                role_bathroom = discord.utils.get(message.guild.roles, name="🚿")
                await message.author.add_roles(role_bathroom)
            except discord.errors.Forbidden:
                logging(file, get_f(), "discord.errors.Forbidden")
            except discord.errors.HTTPException:
                logging(file, get_f(), "discord.errors.HTTPException")

    @commands.command(aliases=["shuffle"])
    @commands.is_owner()
    async def castle_shuffle(self, ctx):

        server = books.find_one({
            "server": str(ctx.guild.id)}, {
            "_id": 0,
            "categories.castle": 1,
            "channels.prefects-bathroom": 1
        })

        try:
            castle_id = server["categories"]["castle"]
            prefects_id = server["channels"]["prefects-bathroom"]
        except KeyError:
            logging(file, get_f(), "KeyError")
            return

        try:
            castle_channel = self.client.get_channel(int(castle_id))
            prefects_channel = self.client.get_channel(int(prefects_id))

            for channel in castle_channel.text_channels:
                try:
                    new_floor = random.randint(1, len(castle_channel.text_channels)) - 1
                    await channel.edit(position=new_floor)
                    await asyncio.sleep(1)
                except discord.errors.InvalidArgument:
                    logging(file, get_f(), "discord.errors.InvalidArgument")
                    continue
                except discord.errors.Forbidden:
                    logging(file, get_f(), "discord.errors.Forbidden")
                    continue
                except discord.errors.HTTPException:
                    logging(file, get_f(), "discord.errors.HTTPException")
                    continue

        except AttributeError:
            logging(file, get_f(), "AttributeError")
            return

        try:
            await prefects_channel.edit(position=7)
            await asyncio.sleep(5)
        except discord.errors.InvalidArgument:
            logging(file, get_f(), "discord.errors.InvalidArgument")
        except discord.errors.Forbidden:
            logging(file, get_f(), "discord.errors.Forbidden")
        except discord.errors.HTTPException:
            logging(file, get_f(), "discord.errors.HTTPException")

        await self.castle_shuffle_topic(castle_id, prefects_channel)

    async def castle_shuffle_topic(self, castle_id, prefects_channel):

        ordinal = lambda n: "%d%s" % (n, "tsnrhtdd"[(n // 10 % 10 != 1) * (n % 10 < 4) * n % 10::4])

        try:
            castle_channel = self.client.get_channel(int(castle_id))
            castle_channels = castle_channel.text_channels
        except AttributeError:
            logging(file, get_f(), "AttributeError")
            return

        i = 0
        while i < len(castle_channels):

            if castle_channels[i].name != "prefects-bathroom":
                try:
                    current_channel_topic = castle_channels[i].topic[12:]
                    current_channel = castle_channels[i]
                    new_channel_topic = f"{ordinal(i + 1)} Floor -\n{current_channel_topic}"
                    await current_channel.edit(topic=new_channel_topic)
                    i += 1
                except discord.errors.InvalidArgument:
                    logging(file, get_f(), "discord.errors.InvalidArgument")
                    i += 1
                except discord.errors.Forbidden:
                    logging(file, get_f(), "discord.errors.Forbidden")
                    i += 1
                except discord.errors.HTTPException:
                    logging(file, get_f(), "discord.errors.HTTPException")
                    i += 1

            elif castle_channels[i].name == "prefects-bathroom":
                i += 1

        try:
            await prefects_channel.edit(position=5)
        except discord.errors.InvalidArgument:
            logging(file, get_f(), "discord.errors.InvalidArgument")
        except discord.errors.Forbidden:
            logging(file, get_f(), "discord.errors.Forbidden")
        except discord.errors.HTTPException:
            logging(file, get_f(), "discord.errors.HTTPException")

    async def reset_prefects(self):
        query = books.find({}, {"_id": 0, "server": 1, "channels.prefects-bathroom": 1})

        for result in query:
            try:
                guild_id = result["server"]
                guild = self.client.get_guild(int(guild_id))
                role_bathroom = discord.utils.get(guild.roles, name="🚿")

                if len(role_bathroom.members) == 0:
                    return

                elif len(role_bathroom.members) > 0:
                    for member in role_bathroom.members:
                        try:
                            await member.remove_roles(role_bathroom)
                        except discord.errors.Forbidden:
                            logging(file, get_f(), "discord.errors.Forbidden")
                            continue
                        except discord.errors.HTTPException:
                            logging(file, get_f(), "discord.errors.HTTPException")
                            continue

            except AttributeError:
                logging(file, get_f(), "AttributeError")
                continue

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):

        if "pinned" not in payload.data:
            return

        elif payload.data["pinned"] is True:

            request = books.find_one({
                "server": f"{payload.data['guild_id']}"}, {
                "_id": 0,
                "channels.shard-trading": 1,
                "channels.headlines": 1,
                "roles.shard_seekers": 1
            })

            try:
                guild_id = payload.data['guild_id']
                user_id = payload.data["author"]["id"]
                channel_id = payload.data["channel_id"]
                headlines_id = request["channels"]["headlines"]
                shard_trading_id = request["channels"]["shard-trading"]
                shard_seeker_id = request["roles"]["shard_seekers"]
                attachments = payload.data["attachments"]
                attachments_url = payload.data["attachments"]
                description = payload.data["content"]

            except KeyError:
                logging(file, get_f(), "KeyError")
                return

            if str(channel_id) == shard_trading_id:

                guild = self.client.get_guild(int(guild_id))
                user = guild.get_member(int(user_id))
                headlines_channel = self.client.get_channel(int(headlines_id))
                shard_trading_channel = self.client.get_channel(int(shard_trading_id))
                shard_seeker_role = guild.get_role(int(shard_seeker_id))

                try:
                    content = f"{shard_seeker_role.mention}"

                    embed = discord.Embed(color=user.colour, description=description)
                    embed.set_author(
                        name=f"{user.display_name} is looking for shards!",
                        icon_url=user.avatar_url
                    )
                    embed.set_footer(
                        text=f"#{shard_trading_channel.name} | {get_time().strftime('%b %d, %Y %H:%M EST')}"
                    )

                    if len(attachments) > 0:
                        embed.set_image(url=attachments_url[0]["url"])

                    try:
                        await headlines_channel.send(content=content, embed=embed)
                    except AttributeError:
                        logging(file, get_f(), "AttributeError")
                    except discord.errors.Forbidden:
                        logging(file, get_f(), "discord.errors.Forbidden")
                    except discord.errors.HTTPException:
                        logging(file, get_f(), "discord.errors.HTTPException")

                except AttributeError:
                    logging(file, get_f(), "AttributeError")

    @commands.Cog.listener()
    async def on_member_join(self, member):

        request = books.find_one({
            "server": f"{member.guild.id}"}, {
            "_id": 0,
            "channels": 1,
            "roles": 1,
            "letters": 1
        })

        try:
            common_room_id = request["channels"]["the-common-room"]
            record_scroll_id = request["channels"]["scroll-of-everything"]
            sorting_hat_id = request["channels"]["sorting-hat"]
            welcome_id = request["channels"]["welcome"]
            no_maj_role_id = request["roles"]["no-maj"]
            acceptance_letter = request["letters"]["acceptance"].replace("\\n", "\n")
            welcome_message = request["letters"]["welcome"]

        except KeyError:
            logging(file, get_f(), "KeyError")
            return

        try:
            embed1 = discord.Embed(
                color=0xffff80,
                title="✉ Acceptance Letter",
                description=acceptance_letter.format(member.display_name, welcome_id, sorting_hat_id)
            )

            embed2 = discord.Embed(color=0xffffff)
            embed2.set_author(
                name=f"{member.display_name} has joined the house!"
            )
            embed2.set_footer(
                text=f"{member.guild.member_count} members | {get_time().strftime('%b %d, %Y %H:%M EST')}",
                icon_url=member.avatar_url
            )
        except AttributeError:
            logging(file, get_f(), "AttributeError")
            return

        try:
            common_room_channel = self.client.get_channel(int(common_room_id))
            await common_room_channel.send(welcome_message.format(member.mention))
        except AttributeError:
            logging(file, get_f(), "AttributeError")
        except discord.errors.Forbidden:
            logging(file, get_f(), "discord.errors.Forbidden")
        except discord.errors.HTTPException:
            pass

        try:
            await member.send(embed=embed1)
        except discord.errors.Forbidden:
            logging(file, get_f(), "discord.errors.Forbidden")
        except discord.errors.HTTPException:
            pass

        try:
            record_scroll_channel = self.client.get_channel(int(record_scroll_id))
            await record_scroll_channel.send(embed=embed2)
        except AttributeError:
            logging(file, get_f(), "AttributeError")
        except discord.errors.Forbidden:
            logging(file, get_f(), "discord.errors.Forbidden")
        except discord.errors.HTTPException:
            pass

        try:
            no_maj_role = member.guild.get_role(int(no_maj_role_id))
            await member.add_roles(no_maj_role)
        except discord.errors.Forbidden:
            logging(file, get_f(), "discord.errors.Forbidden")
        except discord.errors.HTTPException:
            pass

    @commands.Cog.listener()
    async def on_member_remove(self, member):

        users.delete_one({"user_id": str(member.id)})
        request = books.find_one({
            "server": str(member.guild.id)}, {
            "_id": 0,
            "channels.scroll-of-everything": 1
        })
        try:
            record_scroll_id = request["channels"]["scroll-of-everything"]
        except KeyError:
            logging(file, get_f(), "KeyError")
            return

        record_scroll_channel = self.client.get_channel(int(record_scroll_id))

        try:
            embed = discord.Embed(color=0xffffff)
            embed.set_author(name=f"{member.display_name} has left the house!")
            embed.set_footer(
                text=f"{member.guild.member_count} members | {get_time().strftime('%b %d, %Y %H:%M EST')}",
                icon_url=member.avatar_url
            )
        except AttributeError:
            logging(file, get_f(), "AttributeError")
            return

        try:
            await record_scroll_channel.send(embed=embed)
        except AttributeError:
            logging(file, get_f(), "AttributeError")
        except discord.errors.Forbidden:
            logging(file, get_f(), "discord.errors.Forbidden")
        except discord.errors.HTTPException:
            logging(file, get_f(), "discord.errors.HTTPException")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):

        request = books.find_one({
            "server": str(before.guild.id)}, {
            "_id": 0,
            "channels.scroll-of-everything": 1,
            "channels.auror-department": 1}
        )
        try:
            record_scroll_id = request["channels"]["scroll-of-everything"]
        except KeyError:
            logging(file, get_f(), "KeyError")
            return

        record_scroll_channel = self.client.get_channel(int(record_scroll_id))

        if before.roles != after.roles:
            changed_role1 = list(set(after.roles) - set(before.roles))
            changed_role2 = list(set(before.roles) - set(after.roles))

            if not changed_role1:
                embed = discord.Embed(
                    color=0x50e3c2,
                    title=f"Removed {changed_role2[0].name} role for {before.display_name}"
                )
                embed.set_footer(
                    text=f"{get_time().strftime('%b %d, %Y %H:%M EST')}",
                    icon_url=before.avatar_url
                )
                try:
                    await record_scroll_channel.send(embed=embed)
                except AttributeError:
                    logging(file, get_f(), "AttributeError")
                except discord.errors.Forbidden:
                    logging(file, get_f(), "discord.errors.Forbidden")
                except discord.errors.HTTPException:
                    logging(file, get_f(), "discord.errors.HTTPException")

            elif not changed_role2:
                embed = discord.Embed(
                    color=0x50e3c2,
                    title=f"Added {changed_role1[0].name} role for {before.display_name}"
                )
                embed.set_footer(
                    text=f"{get_time().strftime('%b %d, %Y %H:%M EST')}",
                    icon_url=before.avatar_url
                )
                try:
                    await record_scroll_channel.send(embed=embed)
                except AttributeError:
                    logging(file, get_f(), "AttributeError")
                except discord.errors.Forbidden:
                    logging(file, get_f(), "discord.errors.Forbidden")
                except discord.errors.HTTPException:
                    logging(file, get_f(), "discord.errors.HTTPException")


                if changed_role1[0].name == "Auror":
                    auror_department_id = request["channels"]["auror-department"]
                    auror_department_channel = self.client.get_channel(int(auror_department_id))

                    embed = discord.Embed(
                        color=0x50e3c2,
                        title=f"{before.display_name} has been promoted to ⚜ Auror"
                    )
                    embed.set_footer(
                        text=f"{get_time().strftime('%b %d, %Y %H:%M EST')}",
                        icon_url=before.avatar_url
                    )
                    try:
                        await auror_department_channel.send(embed=embed)
                    except AttributeError:
                        logging(file, get_f(), "AttributeError")
                    except discord.errors.Forbidden:
                        logging(file, get_f(), "discord.errors.Forbidden")
                    except discord.errors.HTTPException:
                        logging(file, get_f(), "discord.errors.HTTPException")

        elif before.nick != after.nick:
            embed = discord.Embed(color=0x7ed321)
            embed.set_footer(
                text=f"{get_time().strftime('%b %d, %Y %H:%M EST')}",
                icon_url=before.avatar_url
            )
            embed.add_field(
                name="Before | New nickname:",
                value=f"{before.display_name} | {after.display_name}"
            )
            try:
                await record_scroll_channel.send(embed=embed)
            except AttributeError:
                logging(file, get_f(), "AttributeError")
            except discord.errors.Forbidden:
                logging(file, get_f(), "discord.errors.Forbidden")
            except discord.errors.HTTPException:
                logging(file, get_f(), "discord.errors.HTTPException")

        elif before.name != after.name:
            embed = discord.Embed(color=0x7ed321)
            embed.set_footer(
                text=f"{get_time().strftime('%b %d, %Y %H:%M EST')}",
                icon_url=before.avatar_url
            )
            embed.add_field(
                name="Before | New username:",
                value=f"{before.name} | {after.name}"
            )
            try:
                await record_scroll_channel.send(embed=embed)
            except AttributeError:
                logging(file, get_f(), "AttributeError")
            except discord.errors.Forbidden:
                logging(file, get_f(), "discord.errors.Forbidden")
            except discord.errors.HTTPException:
                logging(file, get_f(), "discord.errors.HTTPException")


def setup(client):
    client.add_cog(Events(client))
