"""
Automation Module
Miketsu, 2020
"""

import sys

from discord.ext import commands

from cogs.ext.initialize import *
from cogs.level import Level


class Automation(commands.Cog):

    def __init__(self, client):

        self.client = client
        self.prefix = self.client.command_prefix

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author.bot is True:
            return

        elif str(message.channel).startswith("Direct Message") is True:

            record_scroll_channel = self.client.get_channel(int(id_scroll))
            await process_msg_submit(record_scroll_channel, f"{message.author}: {message.content}", None)

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):

        try:
            pinned = payload.data["pinned"]
            channel_id = payload.data["channel_id"]

        except KeyError:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            pb.push_note("Miketsu Bot", f"{exc_type}, Line {exc_tb.tb_lineno}")

        else:
            if str(channel_id) == id_shard_trading and pinned is True:

                user_id = payload.data["author"]["id"]
                attachments = payload.data["attachments"]
                link = f"https://discordapp.com/channels/{id_guild}/{id_shard_trading}/{payload.data['id']}"
                description = payload.data["content"] + f"\n\n[Link here!]({link})"

                member = self.client.get_guild(int(id_guild)).get_member(int(user_id))

                headlines_channel = self.client.get_channel(int(id_headlines))
                shard_trading_channel = self.client.get_channel(int(id_shard_trading))

                content = f"<@&{id_shard_seeker}>!"
                embed = discord.Embed(color=member.colour, description=description, timestamp=get_timestamp())
                embed.set_author(
                    name=f"{member.display_name} is seeking for shards!",
                    icon_url=member.avatar_url
                )
                embed.set_footer(text=f"#{shard_trading_channel.name}")

                if len(attachments) > 0:
                    embed.set_image(url=attachments[0]["url"])

                await process_msg_submit(headlines_channel, content, embed)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):

        if str(payload.emoji) not in ["📌"]:
            return

        else:
            channel = self.client.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            await process_msg_pin(message)

    @commands.Cog.listener()
    async def on_member_join(self, member):

        if str(id_guild) != str(member.guild.id):
            return

        elif str(id_guild) == str(member.guild.id):

            query = guilds.find_one({"server": str(id_guild)}, {"_id": 0, "channels": 1, "roles": 1, "letters": 1})

            try:
                id_common_room = query["channels"]["the-common-room"]
                id_no_maj_role = query["roles"]["no-maj"]
                msg_acceptance = query["letters"]["acceptance"].replace("\\n", "\n")
                msg_welcome = query["letters"]["welcome"]
                msg_bot_intro = query["letters"]["bot_intro"]

            except KeyError:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                pb.push_note("Miketsu Bot", f"{exc_type}, Line {exc_tb.tb_lineno}")

            else:
                embed3 = discord.Embed(
                    color=0xffffff, timestamp=get_timestamp(), description=msg_welcome.format(member.mention)
                )
                common_room_channel = self.client.get_channel(int(id_common_room))
                await process_msg_submit(common_room_channel, None, embed3)

                embed1 = discord.Embed(
                    color=0xffff80, timestamp=get_timestamp(), title="✉ Acceptance Letter",
                    description=msg_acceptance.format(member.display_name, id_welcome, id_sorting),
                )
                content = msg_bot_intro.format(self.client.user.name, self.client.command_prefix)
                await process_msg_submit(member, None, embed1)
                await process_msg_submit(member, content, None)

                embed2 = discord.Embed(color=0xffffff, timestamp=get_timestamp())
                embed2.set_author(name=f"{member} has joined the house!")
                embed2.set_footer(
                    text=f"{member.guild.member_count} members",
                    icon_url=member.avatar_url
                )
                record_scroll_channel = self.client.get_channel(int(id_scroll))
                await process_msg_submit(record_scroll_channel, None, embed2)

                no_maj_role = member.guild.get_role(int(id_no_maj_role))
                await process_role_add(member, no_maj_role)

            finally:
                await Level(self.client).level_create_user(member)

    @commands.Cog.listener()
    async def on_member_remove(self, member):

        embed = discord.Embed(color=0xffffff, timestamp=get_timestamp())
        embed.set_author(name=f"{member} [{member.display_name}] has left the house!")
        embed.set_footer(
            text=f"{member.guild.member_count} members",
            icon_url=member.avatar_url
        )

        record_scroll_channel = self.client.get_channel(int(id_scroll))
        await process_msg_submit(record_scroll_channel, None, embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):

        record_scroll_channel = self.client.get_channel(int(id_scroll))
        auror_department_channel = self.client.get_channel(int(id_auror_dept))

        if before.roles != after.roles:
            changed_role1 = list(set(after.roles) - set(before.roles))
            changed_role2 = list(set(before.roles) - set(after.roles))

            if not changed_role1:
                embed = discord.Embed(
                    color=0x50e3c2, timestamp=get_timestamp(),
                    title=f"Removed {changed_role2[0].name} role from {before} [{before.display_name}]"
                )
                embed.set_footer(
                    text=f"{len(after.roles)} {pluralize('role', len(after.roles))}",
                    icon_url=before.avatar_url
                )
                await process_msg_submit(record_scroll_channel, None, embed)

            elif not changed_role2:
                embed = discord.Embed(
                    color=0x50e3c2, timestamp=get_timestamp(),
                    title=f"Added {changed_role1[0].name} role to {before} [{before.display_name}]"
                )
                embed.set_footer(text=f"{len(after.roles)} roles", icon_url=before.avatar_url)
                await process_msg_submit(record_scroll_channel, None, embed)

                if changed_role1[0].name == "Auror":
                    embed = discord.Embed(
                        color=0x50e3c2, timestamp=get_timestamp(),
                        title=f"{before.display_name} has been promoted to ⚜ Auror"
                    )
                    embed.set_footer(icon_url=before.avatar_url)
                    await process_msg_submit(auror_department_channel, None, embed)

        elif before.name != after.name:
            embed = discord.Embed(
                color=0x7ed321, timestamp=get_timestamp(),
                description=f"{before.name} → {after.name}",
            )
            embed.set_author(
                name=f"Username change",
                icon_url=before.avatar_url
            )
            await process_msg_submit(record_scroll_channel, None, embed)

        elif before.nick != after.nick:
            embed = discord.Embed(
                color=0x7ed321, timestamp=get_timestamp(),
                description=f"{before.display_name} → {after.mention}",
            )
            embed.set_author(
                name=f"Nickname change",
                icon_url=before.avatar_url
            )
            await process_msg_submit(record_scroll_channel, None, embed)


def setup(client):
    client.add_cog(Automation(client))
