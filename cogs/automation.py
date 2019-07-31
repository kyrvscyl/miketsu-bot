"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
from datetime import datetime

import discord
import pytz
from discord.ext import commands

from cogs.mongo.db import books

shard_trading_ids = []
for document in books.find({}, {"_id": 0, "channels.shard-trading": 1}):
    try:
        shard_trading_ids.append(document["channels"]["shard-trading"])
    except KeyError:
        continue


def get_timestamp():
    return datetime.utcfromtimestamp(datetime.timestamp(datetime.now()))


def get_time_est():
    tz_target = pytz.timezone("America/Atikokan")
    return datetime.now(tz=tz_target)


class Events(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):

        if str(payload.data["channel_id"]) not in shard_trading_ids:
            return

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

            guild_id = payload.data['guild_id']
            user_id = payload.data["author"]["id"]
            headlines_id = request["channels"]["headlines"]
            shard_trading_id = request["channels"]["shard-trading"]
            shard_seeker_id = request["roles"]["shard_seekers"]
            attachments = payload.data["attachments"]
            description = payload.data["content"]

            guild = self.client.get_guild(int(guild_id))
            user = guild.get_member(int(user_id))
            headlines_channel = self.client.get_channel(int(headlines_id))
            shard_trading_channel = self.client.get_channel(int(shard_trading_id))
            shard_seeker_role = guild.get_role(int(shard_seeker_id))

            content = f"{shard_seeker_role.mention}"
            embed = discord.Embed(color=user.colour, description=description, timestamp=get_timestamp())
            embed.set_author(
                name=f"{user.display_name} is looking for shards!",
                icon_url=user.avatar_url
            )
            embed.set_footer(text=f"#{shard_trading_channel.name}")

            if len(attachments) > 0:
                embed.set_image(url=attachments[0]["url"])

            await headlines_channel.send(content=content, embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):

        request = books.find_one({"server": f"{member.guild.id}"}, {
            "_id": 0, "channels": 1, "roles": 1, "letters": 1
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
            return

        try:
            embed3 = discord.Embed(color=0xffffff, description=welcome_message.format(member.mention))
            common_room_channel = self.client.get_channel(int(common_room_id))
            await common_room_channel.send(embed=embed3)
        except AttributeError:
            pass
        except discord.errors.Forbidden:
            pass
        except discord.errors.HTTPException:
            pass

        try:
            embed1 = discord.Embed(
                color=0xffff80,
                title="✉ Acceptance Letter",
                description=acceptance_letter.format(member.display_name, welcome_id, sorting_hat_id)
            )
            await member.send(embed=embed1)
        except discord.errors.Forbidden:
            pass
        except discord.errors.HTTPException:
            pass

        try:
            embed2 = discord.Embed(color=0xffffff, timestamp=get_timestamp())
            embed2.set_author(
                name=f"{member} has joined the house!"
            )
            embed2.set_footer(
                text=f"{member.guild.member_count} members",
                icon_url=member.avatar_url
            )

            record_scroll_channel = self.client.get_channel(int(record_scroll_id))
            await record_scroll_channel.send(embed=embed2)
        except AttributeError:
            pass
        except discord.errors.Forbidden:
            pass
        except discord.errors.HTTPException:
            pass

        try:
            no_maj_role = member.guild.get_role(int(no_maj_role_id))
            await member.add_roles(no_maj_role)
        except discord.errors.Forbidden:
            pass
        except discord.errors.HTTPException:
            pass

    @commands.Cog.listener()
    async def on_member_remove(self, member):

        request = books.find_one({"server": str(member.guild.id)}, {
            "_id": 0, "channels.scroll-of-everything": 1
        })
        record_scroll_id = request["channels"]["scroll-of-everything"]
        record_scroll_channel = self.client.get_channel(int(record_scroll_id))

        embed = discord.Embed(color=0xffffff, timestamp=get_timestamp())
        embed.set_author(name=f"{member} [{member.display_name}] has left the house!")
        embed.set_footer(
            text=f"{member.guild.member_count} members",
            icon_url=member.avatar_url
        )

        try:
            await record_scroll_channel.send(embed=embed)
        except AttributeError:
            pass
        except discord.errors.Forbidden:
            pass
        except discord.errors.HTTPException:
            pass

    @commands.Cog.listener()
    async def on_member_update(self, before, after):

        request = books.find_one({
            "server": str(before.guild.id)}, {
            "_id": 0,
            "channels.scroll-of-everything": 1,
            "channels.auror-department": 1}
        )
        record_scroll_id = request["channels"]["scroll-of-everything"]
        record_scroll_channel = self.client.get_channel(int(record_scroll_id))

        if before.roles != after.roles:
            changed_role1 = list(set(after.roles) - set(before.roles))
            changed_role2 = list(set(before.roles) - set(after.roles))

            if not changed_role1:
                try:
                    embed = discord.Embed(
                        color=0x50e3c2,
                        title=f"Removed {changed_role2[0].name} role for {before.display_name}",
                        timestamp=get_timestamp()
                    )
                    embed.set_footer(icon_url=before.avatar_url)
                    await record_scroll_channel.send(embed=embed)
                except AttributeError:
                    pass
                except discord.errors.Forbidden:
                    pass
                except discord.errors.HTTPException:
                    pass

            elif not changed_role2:
                try:
                    embed = discord.Embed(
                        color=0x50e3c2,
                        title=f"Added {changed_role1[0].name} role for {before.display_name}",
                        timestamp=get_timestamp()
                    )
                    embed.set_footer(icon_url=before.avatar_url)
                    await record_scroll_channel.send(embed=embed)
                except AttributeError:
                    pass
                except discord.errors.Forbidden:
                    pass
                except discord.errors.HTTPException:
                    pass

                if changed_role1[0].name == "Auror":
                    auror_department_id = request["channels"]["auror-department"]
                    auror_department_channel = self.client.get_channel(int(auror_department_id))

                    try:
                        embed = discord.Embed(
                            color=0x50e3c2,
                            title=f"{before.display_name} has been promoted to ⚜ Auror",
                            timestamp=get_timestamp()
                        )
                        embed.set_footer(icon_url=before.avatar_url)
                        await auror_department_channel.send(embed=embed)
                    except AttributeError:
                        pass
                    except discord.errors.Forbidden:
                        pass
                    except discord.errors.HTTPException:
                        pass

        elif before.name != after.name:
            try:
                embed = discord.Embed(
                    color=0x7ed321,
                    title="Before | New username:",
                    value=f"{before.name} | {after.name}",
                    timestamp=get_timestamp()
                )
                embed.set_footer(icon_url=before.avatar_url)
                await record_scroll_channel.send(embed=embed)
            except AttributeError:
                pass
            except discord.errors.Forbidden:
                pass
            except discord.errors.HTTPException:
                pass

        elif before.nick != after.nick:
            try:
                embed = discord.Embed(
                    color=0x7ed321,
                    title="Before | New nickname:",
                    description=f"{before.display_name} | {after.display_name}",
                    timestamp=get_timestamp()
                )
                embed.set_footer(icon_url=before.avatar_url)
                await record_scroll_channel.send(embed=embed)
            except AttributeError:
                pass
            except discord.errors.Forbidden:
                pass
            except discord.errors.HTTPException:
                pass


def setup(client):
    client.add_cog(Events(client))
