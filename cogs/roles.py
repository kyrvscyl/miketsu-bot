"""
Embeds Module
Miketsu, 2020
"""
import asyncio

from discord.ext import commands

from cogs.ext.initialize import *


class Roles(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.prefix = self.client.command_prefix

        self.msg_id_list = []
        self.roles_emoji = {}

        for role_select_msg in sortings.find({"title": {"$ne": "Quest Selection & Acceptance"}}, {"_id": 0}):
            self.msg_id_list.append(role_select_msg["msg_id"])

            for roles_emoji_entry in role_select_msg["fields"]:
                self.roles_emoji.update({roles_emoji_entry['emoji']: f"{roles_emoji_entry['role_id']}"})

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):

        if self.client.get_user(int(payload.user_id)).bot:
            return

        elif str(payload.message_id) in self.msg_id_list:

            guild = self.client.get_guild(int(id_guild))
            request_2 = sortings.find_one({"msg_id": str(payload.message_id)}, {"_id": 0})

            member = guild.get_member(int(payload.user_id))
            sorting_channel = self.client.get_channel(int(id_sorting))
            role_selection_msg = await sorting_channel.fetch_message(int(payload.message_id))

            role_id = sortings.find_one({
                "msg_id": str(payload.message_id),
                "fields.emoji": str(payload.emoji)
            }, {"_id": 0, "fields.$.role_id": 1})["fields"][0]["role_id"]

            valid_emojis = []
            valid_emojis_remove = []
            for field in request_2["fields"]:
                valid_emojis.append(field["emoji"])
                valid_emojis_remove.append(field["emoji"])

            if str(payload.emoji) in valid_emojis and request_2["multiple"] is True:

                role_add = discord.utils.get(guild.roles, id=int(role_id))
                await member.add_roles(role_add)
                await asyncio.sleep(7)
                await self.edit_msg_role_selection_members_count(str(payload.message_id), guild)

            elif str(payload.emoji) in valid_emojis and request_2["multiple"] is False:

                role_id = sortings.find_one({
                    "msg_id": str(payload.message_id),
                    "fields.emoji": str(payload.emoji)
                }, {"_id": 0, "fields.$.role_id": 1})["fields"][0]["role_id"]

                valid_emojis_remove.remove(str(payload.emoji))

                for emoji in valid_emojis_remove:
                    await role_selection_msg.remove_reaction(emoji, member)

                role_add = discord.utils.get(guild.roles, id=int(role_id))
                await member.add_roles(role_add)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):

        if self.client.get_user(int(payload.user_id)).bot:
            return

        elif str(payload.message_id) in self.msg_id_list:

            guild = self.client.get_guild(int(id_guild))
            role_id = self.roles_emoji[str(payload.emoji)]
            role_remove = discord.utils.get(guild.roles, id=int(role_id))
            member = guild.get_member(int(payload.user_id))
            await member.remove_roles(role_remove)
            await asyncio.sleep(10)
            await self.edit_msg_role_selection_members_count(str(payload.message_id), guild)

    async def edit_msg_role_selection_members_count(self, msg_id, guild):

        request = sortings.find_one({"msg_id": str(msg_id)}, {"_id": 0})
        sorting_channel = self.client.get_channel(int(id_sorting))

        embed = discord.Embed(
            title=request["title"],
            description=request["description"].replace('\\n', '\n'),
            timestamp=get_timestamp(),
            color=request["color"]
        )

        members_count = []
        role_emojis = []
        for field in request["fields"]:

            role_id = field["role_id"]
            role = discord.utils.get(guild.roles, id=int(role_id))
            role_emojis.append(field["emoji"])
            count = len(role.members)
            members_count.append(count)

            if request["title"] != "Role Color Selection":
                embed.add_field(
                    name=f"{field['emoji']} {field['role']} [{count}]",
                    value=f"{field['description']}"
                )

            else:
                embed.add_field(
                    name=f"{field['emoji']} {field['role']} [{count}]",
                    value="<@&{}>{}".format(field['role_id'], field['description'])
                )

        if request["multiple"] is False:
            embed.set_footer(text=f"{sum(members_count)}/{len(guild.members)} sorted members")
        else:
            embed.set_footer(text=f"{sum(members_count)} special roles issued")

        roles_msg = await sorting_channel.fetch_message(int(msg_id))
        await roles_msg.edit(embed=embed)


def setup(client):
    client.add_cog(Roles(client))
