"""
Roles Module
Miketsu, 2020
"""

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
            query = sortings.find_one({"msg_id": str(payload.message_id)}, {"_id": 0})

            member = guild.get_member(int(payload.user_id))
            sorting_channel = self.client.get_channel(int(id_sorting))
            msg = await sorting_channel.fetch_message(int(payload.message_id))

            role_id = sortings.find_one({
                "msg_id": str(payload.message_id),
                "fields.emoji": str(payload.emoji)
            }, {"_id": 0, "fields.$.role_id": 1})["fields"][0]["role_id"]

            valid_emojis = []
            valid_emojis_remove = []
            for field in query["fields"]:
                valid_emojis.append(field["emoji"])
                valid_emojis_remove.append(field["emoji"])

            if str(payload.emoji) in valid_emojis and query["multiple"] is True:

                role_add = discord.utils.get(guild.roles, id=int(role_id))
                await process_role_add(member, role_add)
                await asyncio.sleep(7)
                await self.edit_msg_role_selection_members_count(str(payload.message_id), guild)

            elif str(payload.emoji) in valid_emojis and query["multiple"] is False:

                valid_emojis_remove.remove(str(payload.emoji))

                for emoji in valid_emojis_remove:
                    await process_msg_reaction_remove(msg, emoji, member)

                role_add = discord.utils.get(guild.roles, id=int(role_id))
                await process_role_add(member, role_add)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):

        if self.client.get_user(int(payload.user_id)).bot:
            return

        elif str(payload.message_id) in self.msg_id_list:

            guild = self.client.get_guild(int(id_guild))
            role_id = self.roles_emoji[str(payload.emoji)]
            role_remove = discord.utils.get(guild.roles, id=int(role_id))
            member = guild.get_member(int(payload.user_id))

            await process_role_remove(member, role_remove)
            await asyncio.sleep(10)
            await self.edit_msg_role_selection_members_count(str(payload.message_id), guild)

    async def edit_msg_role_selection_members_count(self, msg_id, guild):

        query = sortings.find_one({"msg_id": str(msg_id)}, {"_id": 0})
        sorting_channel = self.client.get_channel(int(id_sorting))

        embed = discord.Embed(
            title=query["title"], description=query["description"].replace('\\n', '\n'),
            timestamp=get_timestamp(), color=query["color"]
        )

        members_count = []
        role_emojis = []
        for field in query["fields"]:

            role_id = field["role_id"]
            role = discord.utils.get(guild.roles, id=int(role_id))
            role_emojis.append(field["emoji"])
            count = len(role.members)
            members_count.append(count)

            if query["title"] != "Role Color Selection":
                embed.add_field(
                    name=f"{field['emoji']} {field['role']} [{count}]",
                    value=f"{field['description']}"
                )

            else:
                embed.add_field(
                    name=f"{field['emoji']} {field['role']} [{count}]",
                    value="<@&{}>{}".format(field['role_id'], field['description'])
                )

        if query["multiple"] is False:
            embed.set_footer(text=f"{sum(members_count)}/{len(guild.members)} sorted members")
        else:
            embed.set_footer(text=f"{sum(members_count)} special roles issued")

        roles_msg = await sorting_channel.fetch_message(int(msg_id))
        await process_msg_edit(roles_msg, None, embed)

    @commands.command(aliases=["sorting"])
    @commands.is_owner()
    async def roles_post_sorting_messages(self, ctx):

        guild = self.client.get_guild(int(id_guild))
        sorting_channel = self.client.get_channel(int(id_sorting))

        for role_doc in sortings.find({}, {"_id": 0}):

            embed = discord.Embed(
                title=role_doc["title"], description=role_doc["description"].replace('\\n', '\n'),
                timestamp=get_timestamp(), color=role_doc["color"]
            )

            members_count, role_emojis = [], []

            for field in role_doc["fields"]:

                role_id = field["role_id"]
                role = discord.utils.get(ctx.guild.roles, id=int(role_id))
                role_emojis.append(field["emoji"])
                count = len(role.members)
                members_count.append(count)

                if role_doc["title"] != "Role Color Selection":
                    embed.add_field(
                        name=f"{field['emoji']} {field['role']} [{count}]",
                        value=f"{field['description']}"
                    )
                else:
                    embed.add_field(
                        name=f"{field['emoji']} {field['role']} [{count}]",
                        value="<@&{}>{}".format(field['role_id'], field['description'])
                    )

            if role_doc["multiple"] is False:
                embed.set_footer(text=f"{sum(members_count)}/{len(guild.members)} sorted members")
            else:
                embed.set_footer(text=f"{sum(members_count)} special roles issued")

            query = sortings.find_one({"title": role_doc["title"]}, {"_id": 0})
            msg = await sorting_channel.fetch_message(int(query["msg_id"]))

            emoji_existing = []
            for emoji1 in msg.reactions:
                emoji_existing.append(emoji1)

            for emoji2 in role_emojis:
                if emoji2 not in emoji_existing:
                    await msg.add_reaction(emoji2)

            await process_msg_edit(msg, None, embed)
            await asyncio.sleep(2)

        await process_msg_delete(ctx.message, 0)


def setup(client):
    client.add_cog(Roles(client))
