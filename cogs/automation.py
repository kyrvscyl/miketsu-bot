"""
Automation Module
Miketsu, 2019
"""
import os
from datetime import datetime

import discord
import pytz
from discord.ext import commands

from cogs.level import Level
from cogs.mongo.database import get_collections

# Collections
config = get_collections("config")
guilds = get_collections("guilds")

# Variables
guild_id = int(os.environ.get("SERVER"))

id_auror_dept = guilds.find_one({"server": str(guild_id)}, {"_id": 0, "channels": 1})["channels"]["auror-department"]
id_headlines = guilds.find_one({"server": str(guild_id)}, {"_id": 0, "channels": 1})["channels"]["headlines"]
id_office = guilds.find_one({"server": str(guild_id)}, {"_id": 0, "channels": 1})["channels"]["headmasters-office"]
id_scroll = guilds.find_one({"server": str(guild_id)}, {"_id": 0, "channels": 1})["channels"]["scroll-of-everything"]
id_shard_seeker = guilds.find_one({"server": str(guild_id)}, {"_id": 0, "roles": 1})["roles"]["shard_seekers"]
id_shard_trading = guilds.find_one({"server": str(guild_id)}, {"_id": 0, "channels": 1})["channels"]["shard-trading"]

timezone = config.find_one({"var": 1}, {"_id": 0, "timezone": 1})["timezone"]


class Automation(commands.Cog):

    def __init__(self, client):
        self.client = client

    def get_time(self):
        return datetime.now(tz=pytz.timezone(timezone))

    def get_timestamp(self):
        return datetime.utcfromtimestamp(datetime.timestamp(datetime.now()))

    def pluralize(self, singular, count):
        if count > 1:
            if singular[-1:] == "s":
                return singular + "es"
            return singular + "s"
        else:
            return singular

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author.bot is True:
            return

        elif str(message.channel).startswith("Direct Message") is True:
            record_scroll_channel = self.client.get_channel(int(id_scroll))
            await record_scroll_channel.send(f"{message.author}: {message.content}")

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):

        try:

            if str(payload.data["channel_id"]) == id_shard_trading and payload.data["pinned"] is True:

                user_id = payload.data["author"]["id"]
                attachments = payload.data["attachments"]
                link = f"https://discordapp.com/channels/{guild_id}/{id_shard_trading}/{payload.data['id']}"
                description = payload.data["content"] + f"\n\n[Link here!]({link})"

                guild = self.client.get_guild(int(guild_id))
                member = guild.get_member(int(user_id))
                headlines_channel = self.client.get_channel(int(id_headlines))
                shard_trading_channel = self.client.get_channel(int(id_shard_trading))

                content = f"<@&{id_shard_seeker}>!"
                embed = discord.Embed(color=member.colour, description=description, timestamp=self.get_timestamp())
                embed.set_author(name=f"{member.display_name} is seeking for shards!", icon_url=member.avatar_url)
                embed.set_footer(text=f"#{shard_trading_channel.name}")

                if len(attachments) > 0:
                    embed.set_image(url=attachments[0]["url"])

                await headlines_channel.send(content=content, embed=embed)

        except KeyError:
            pass

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):

        if str(payload.emoji) != "📌":
            return

        else:
            channel = self.client.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            await message.pin()

    @commands.Cog.listener()
    async def on_member_join(self, member):

        await Level(self).level_create_user(member)
        request = guilds.find_one({"server": f"{member.guild.id}"}, {"_id": 0, "channels": 1, "roles": 1, "letters": 1})

        try:
            common_room_id = request["channels"]["the-common-room"]
            record_scroll_id = request["channels"]["scroll-of-everything"]
            sorting_hat_id = request["channels"]["sorting-hat"]
            welcome_id = request["channels"]["welcome"]
            no_maj_role_id = request["roles"]["no-maj"]
            acceptance_letter = request["letters"]["acceptance"].replace("\\n", "\n")
            welcome_message = request["letters"]["welcome"]
            bot_intro = request["letters"]["bot_intro"]

        except KeyError:
            return

        try:
            embed3 = discord.Embed(
                color=0xffffff,
                description=welcome_message.format(member.mention),
                timestamp=self.get_timestamp()
            )
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
                description=acceptance_letter.format(member.display_name, welcome_id, sorting_hat_id),
                timestamp=self.get_timestamp()
            )
            content = bot_intro.format(self.client.user.name, self.client.command_prefix)
            await member.send(embed=embed1)
            await member.send(content=content)
        except discord.errors.Forbidden:
            pass
        except discord.errors.HTTPException:
            pass

        try:
            embed2 = discord.Embed(color=0xffffff, timestamp=self.get_timestamp())
            embed2.set_author(name=f"{member} has joined the house!")
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

        record_scroll_channel = self.client.get_channel(int(id_scroll))

        embed = discord.Embed(color=0xffffff, timestamp=self.get_timestamp())
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

        record_scroll_channel = self.client.get_channel(int(id_scroll))
        auror_department_channel = self.client.get_channel(int(id_auror_dept))

        if before.roles != after.roles:
            changed_role1 = list(set(after.roles) - set(before.roles))
            changed_role2 = list(set(before.roles) - set(after.roles))

            if not changed_role1:
                try:
                    embed = discord.Embed(
                        color=0x50e3c2,
                        title=f"Removed {changed_role2[0].name} role from {before} [{before.display_name}]",
                        timestamp=self.get_timestamp()
                    )
                    embed.set_footer(
                        text=f"{len(after.roles)} {self.pluralize('role', len(after.roles))}",
                        icon_url=before.avatar_url
                    )
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
                        title=f"Added {changed_role1[0].name} role to {before} [{before.display_name}]",
                        timestamp=self.get_timestamp()
                    )
                    embed.set_footer(text=f"{len(after.roles)} roles", icon_url=before.avatar_url)
                    await record_scroll_channel.send(embed=embed)
                except AttributeError:
                    pass
                except discord.errors.Forbidden:
                    pass
                except discord.errors.HTTPException:
                    pass

                if changed_role1[0].name == "Auror":

                    try:
                        embed = discord.Embed(
                            color=0x50e3c2,
                            title=f"{before.display_name} has been promoted to ⚜ Auror",
                            timestamp=self.get_timestamp()
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
                    description=f"{before.name} → {after.name}",
                    timestamp=self.get_timestamp()
                )
                embed.set_author(name=f"Username change", icon_url=before.avatar_url)
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
                    description=f"{before.display_name} → {after.mention}",
                    timestamp=self.get_timestamp()
                )
                embed.set_author(name=f"Nickname change", icon_url=before.avatar_url)
                await record_scroll_channel.send(embed=embed)
            except AttributeError:
                pass
            except discord.errors.Forbidden:
                pass
            except discord.errors.HTTPException:
                pass


def setup(client):
    client.add_cog(Automation(client))
