"""
Automation Module
Miketsu, 2020
"""

from discord.ext import commands

from cogs.ext.initialize import *
from cogs.level import Level


class Automation(commands.Cog):

    def __init__(self, client):
        self.client = client

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
            if str(payload.data["channel_id"]) == id_shard_trading and payload.data["pinned"] is True:

                user_id = payload.data["author"]["id"]
                attachments = payload.data["attachments"]
                link = f"https://discordapp.com/channels/{id_guild}/{id_shard_trading}/{payload.data['id']}"
                description = payload.data["content"] + f"\n\n[Link here!]({link})"

                guild = self.client.get_guild(int(id_guild))
                member = guild.get_member(int(user_id))

                headlines_channel = self.client.get_channel(int(id_headlines))
                shard_trading_channel = self.client.get_channel(int(id_shard_trading))

                content = f"<@&{id_shard_seeker}>!"
                embed = discord.Embed(
                    color=member.colour,
                    description=description,
                    timestamp=get_timestamp()
                )
                embed.set_author(
                    name=f"{member.display_name} is seeking for shards!",
                    icon_url=member.avatar_url
                )
                embed.set_footer(text=f"#{shard_trading_channel.name}")

                if len(attachments) > 0:
                    embed.set_image(url=attachments[0]["url"])

                await process_msg_submit(headlines_channel, content, embed)

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

        await Level(self.client).level_create_user(member)

        query = guilds.find_one({
            "server": f"{member.guild.id}"}, {
            "_id": 0, "channels": 1, "roles": 1, "letters": 1
        })

        try:
            common_room_id = query["channels"]["the-common-room"]
            record_scroll_id = query["channels"]["scroll-of-everything"]
            sorting_hat_id = query["channels"]["sorting-hat"]
            welcome_id = query["channels"]["welcome"]
            no_maj_role_id = query["roles"]["no-maj"]
            acceptance_letter = query["letters"]["acceptance"].replace("\\n", "\n")
            welcome_message = query["letters"]["welcome"]
            bot_intro = query["letters"]["bot_intro"]
        except KeyError:
            return

        embed3 = discord.Embed(
            color=0xffffff,
            description=welcome_message.format(member.mention),
            timestamp=get_timestamp()
        )
        common_room_channel = self.client.get_channel(int(common_room_id))
        await process_msg_submit(common_room_channel, None, embed3)

        embed1 = discord.Embed(
            color=0xffff80,
            title="✉ Acceptance Letter",
            description=acceptance_letter.format(member.display_name, welcome_id, sorting_hat_id),
            timestamp=get_timestamp()
        )
        content = bot_intro.format(self.client.user.name, self.client.command_prefix)
        await process_msg_submit(member, None, embed1)
        await process_msg_submit(member, content, None)

        embed2 = discord.Embed(color=0xffffff, timestamp=get_timestamp())
        embed2.set_author(name=f"{member} has joined the house!")
        embed2.set_footer(
            text=f"{member.guild.member_count} members",
            icon_url=member.avatar_url
        )
        record_scroll_channel = self.client.get_channel(int(record_scroll_id))
        await process_msg_submit(record_scroll_channel, None, embed2)

        no_maj_role = member.guild.get_role(int(no_maj_role_id))

        try:
            await member.add_roles(no_maj_role)
        except discord.errors.Forbidden:
            pass
        except discord.errors.HTTPException:
            pass

    @commands.Cog.listener()
    async def on_member_remove(self, member):

        record_scroll_channel = self.client.get_channel(int(id_scroll))

        embed = discord.Embed(
            color=0xffffff,
            timestamp=get_timestamp()
        )
        embed.set_author(
            name=f"{member} [{member.display_name}] has left the house!"
        )
        embed.set_footer(
            text=f"{member.guild.member_count} members",
            icon_url=member.avatar_url
        )
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
                    color=0x50e3c2,
                    title=f"Removed {changed_role2[0].name} role from {before} [{before.display_name}]",
                    timestamp=get_timestamp()
                )
                embed.set_footer(
                    text=f"{len(after.roles)} {pluralize('role', len(after.roles))}",
                    icon_url=before.avatar_url
                )
                await process_msg_submit(record_scroll_channel, None, embed)

            elif not changed_role2:
                embed = discord.Embed(
                    color=0x50e3c2,
                    title=f"Added {changed_role1[0].name} role to {before} [{before.display_name}]",
                    timestamp=get_timestamp()
                )
                embed.set_footer(text=f"{len(after.roles)} roles", icon_url=before.avatar_url)
                await process_msg_submit(record_scroll_channel, None, embed)

                if changed_role1[0].name == "Auror":
                    embed = discord.Embed(
                        color=0x50e3c2,
                        title=f"{before.display_name} has been promoted to ⚜ Auror",
                        timestamp=get_timestamp()
                    )
                    embed.set_footer(icon_url=before.avatar_url)
                    await process_msg_submit(auror_department_channel, None, embed)

        elif before.name != after.name:
            embed = discord.Embed(
                color=0x7ed321,
                description=f"{before.name} → {after.name}",
                timestamp=get_timestamp()
            )
            embed.set_author(
                name=f"Username change",
                icon_url=before.avatar_url
            )
            await process_msg_submit(record_scroll_channel, None, embed)

        elif before.nick != after.nick:
            embed = discord.Embed(
                color=0x7ed321,
                description=f"{before.display_name} → {after.mention}",
                timestamp=get_timestamp()
            )
            embed.set_author(
                name=f"Nickname change",
                icon_url=before.avatar_url
            )
            await process_msg_submit(record_scroll_channel, None, embed)


def setup(client):
    client.add_cog(Automation(client))
