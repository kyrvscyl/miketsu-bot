"""
Admin Module
Miketsu, 2019
"""

import asyncio
import os
import re
from datetime import datetime
from math import ceil

import discord
import pytz
from discord.ext import commands

from cogs.mongo.database import get_collections

# Collections
config = get_collections("config")
frames = get_collections("frames")
guilds = get_collections("guilds")
members = get_collections("members")
memos = get_collections("memos")
ships = get_collections("ships")
users = get_collections("users")

# Instantiations
id_guild = int(os.environ.get("SERVER"))


class Admin(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.prefix = self.client.command_prefix

        self.colour = config.find_one({"var": 1}, {"_id": 0, "embed_color": 1})["embed_color"]
        self.timezone = config.find_one({"var": 1}, {"_id": 0, "timezone": 1})["timezone"]

        self.listings = config.find_one({"list": 1}, {"_id": 0})

        self.fields = config.find_one({"list": 1}, {"_id": 0, "fields": 1})["fields"]
        self.member_status = config.find_one({"list": 1}, {"_id": 0, "member_status": 1})["member_status"]
        self.roles = config.find_one({"list": 1}, {"_id": 0, "roles": 1})["roles"]

        self.roles_emoji = config.find_one({"dict": 1}, {"_id": 0, "roles_emoji": 1})["roles_emoji"]
        self.shortened = config.find_one({"dict": 1}, {"_id": 0, "shortened": 1})["shortened"]
        self.status_batch = config.find_one({"dict": 1}, {"_id": 0, "status_batch": 1})["status_batch"]

        self.admin_roles = self.listings["admin_roles"]

    def check_if_user_has_any_admin_roles(self):
        def predicate(ctx):
            for role in reversed(ctx.author.roles):
                if role.name in self.admin_roles:
                    return True
            return False
        return commands.check(predicate)

    def get_guild_quest_converted(self, key):
        dictionary = {"inactive": "30", "semi-active": "60", "active": "90"}
        return dictionary[str(key)]

    def get_time(self):
        return datetime.now(tz=pytz.timezone(self.timezone))

    def get_timestamp(self):
        return datetime.utcfromtimestamp(datetime.timestamp(datetime.now()))

    def get_status(self, key):
        dictionary = {"30": "inactive", "60": "semi-active", "90": "active"}
        return dictionary[str(key)]

    def lengthen_code(self, index):
        prefix = "#{}"
        if index < 10:
            prefix = "#00{}"
        elif index < 100:
            prefix = "#0{}"
        return prefix.format(index)

    def lengthen_memo(self, index):
        prefix = "{}"
        if index < 10:
            prefix = "000{}"
        elif index < 100:
            prefix = "00{}"
        elif index < 1000:
            prefix = "0{}"
        return prefix.format(index)

    def pluralize(self, singular, count):
        if count > 1:
            if singular[-1:] == "s":
                return singular + "es"
            return singular + "s"
        else:
            return singular

    def shorten_code(self, key):
        return self.shortened[key]

    @commands.command(aliases=["memo"])
    @commands.guild_only()
    @commands.check(check_if_user_has_any_admin_roles)
    async def announcement_post_memorandum(self, ctx, channel: discord.TextChannel = None):

        if channel is None:
            raise commands.MissingRequiredArgument(ctx.author)

        link_default = "https://media.discordapp.net/attachments/580859502379794452/646734006624190486/image0.png"
        memos_count = memos.count()

        request = guilds.find_one({"server": str(id_guild)}, {"_id": 0, "channels": 1, "roles": 1})
        head_id = request["roles"]["head"]
        memorandum_channel_id = request["channels"]["memorandum"]
        memorandum_channel = self.client.get_channel(int(memorandum_channel_id))

        def create_content(content):
            return content

        def create_embed(title, description, link):
            embed_created = discord.Embed(
                colour=ctx.author.self.colour,
                title=title,
                description=description,
                timestamp=self.get_timestamp()
            )
            embed_created.set_thumbnail(url=ctx.guild.icon_url)
            embed_created.set_footer(
                text=f"#{memorandum_channel.name}-{self.lengthen_memo(memos_count + 1)}",
                icon_url=ctx.author.avatar_url
            )
            if link is not None:
                embed_created.set_image(url=link)

            return embed_created

        details = [
            "Step 1: <Optional> Enter message content (useful for pinging roles)",
            "Step 2: <Optional> Enter the embed title",
            "Step 3: <Required> Enter the embed description:\n\nNote: Maximum of 2000 characters",
            link_default
        ]

        msg = await ctx.channel.send(
            content=create_content(details[0]),
            embed=create_embed(details[1], details[2], details[3])
        )

        def check(m):
            return m.author == ctx.author and m.channel.id == ctx.channel.id

        for index, item in enumerate(details):
            try:
                answer = await self.client.wait_for("message", timeout=120, check=check)
            except asyncio.TimeoutError:
                break
            else:
                details[index] = answer.content
                await answer.add_reaction("✅")
                try:
                    await msg.edit(
                        content=create_content(details[0]),
                        embed=create_embed(details[1], details[2], details[3])
                    )
                except discord.errors.HTTPException:
                    details[index] = None
                    await msg.edit(
                        content=create_content(details[0]),
                        embed=create_embed(details[1], details[2], None)
                    )
                continue

        profile = {
            "#": memos_count + 1,
            "timestamp": self.get_time(),
            "user_id": str(ctx.author.id),
            "content": details[0],
            "title": details[1],
            "description": details[2],
            "image": details[3],
        }
        memos.insert_one(profile)

        embed = discord.Embed(
            colour=ctx.author.self.colour,
            title="Confirm issuance",
            description="Do you want to send the memo drafted above?\nAnnounces immediately",
            timestamp=self.get_timestamp()
        )
        embed.set_footer(
            text=f"{ctx.author.display_name}",
            icon_url=ctx.author.avatar_url
        )
        msg1 = await ctx.channel.send(embed=embed)
        await msg1.add_reaction("✅")

        def check2(r, u):
            return u == ctx.author and str(r.emoji) == "✅"

        try:
            await self.client.wait_for("reaction_add", check=check2, timeout=30)
        except asyncio.TimeoutError:
            return
        else:
            await channel.send(
                content=create_content(details[0]),
                embed=create_embed(details[1], details[2], details[3])
            )

            await memorandum_channel.send(
                content=f"*<@&{head_id}>, a new memo has been issued:*" + "\n" + create_content(details[0]),
                embed=create_embed(details[1], details[2], details[3])
            )

    @commands.command(aliases=["say"])
    @commands.guild_only()
    @commands.check(check_if_user_has_any_admin_roles)
    async def announcement_post_message(self, ctx, arg1, *, args):

        try:
            channel_id = re.sub("[<>#]", "", arg1)
            channel_target = self.client.get_channel(int(channel_id))
            await channel_target.send(args)
            await ctx.message.add_reaction("✅")

        except AttributeError:
            embed = discord.Embed(
                colour=self.colour,
                description="the specified channel ID was not found."
            )
            await ctx.channel.send(embed=embed)
        except discord.errors.Forbidden:
            return
        except discord.errors.HTTPException:
            return

    @commands.command(aliases=["clear", "cl"])
    @commands.guild_only()
    @commands.check(check_if_user_has_any_admin_roles)
    async def purge_messages(self, ctx, amount=2):
        try:
            await ctx.channel.purge(limit=amount + 1)
        except discord.errors.Forbidden:
            pass
        except discord.errors.HTTPException:
            pass

    @commands.command(aliases=["m", "manage"])
    @commands.guild_only()
    @commands.check(check_if_user_has_any_admin_roles)
    async def management_guild(self, ctx, *args):

        if args[0].lower() in ["help", "h"]:

            if len(args) >= 1:
                embed = discord.Embed(
                    title="manage, m", colour=self.colour,
                    description="shows the help prompt for the first 3 arguments"
                )
                embed.add_field(name="Arguments", value="*add, update, show, delete, stats*", inline=False)
                embed.add_field(name="Example", value=f"*`{self.prefix}manage add`*", inline=False)
                await ctx.channel.send(embed=embed)

            else:
                await ctx.message.add_reaction("❌")

        elif args[0].lower() in ["add", "a"]:

            if len(args) <= 2:
                embed = discord.Embed(
                    title="manage add, m a", colour=self.colour,
                    description="adds a new guild member in the database"
                )
                embed.add_field(name="Format", value=f"*`{self.prefix}manage add <role> <name>`*", inline=False)
                embed.add_field(name="Roles", value=f"*{', '.join(self.roles)}*", inline=False)
                await ctx.channel.send(embed=embed)

            elif len(args) == 3 and args[1].lower() in self.roles:
                await self.management_guild_add_member(ctx, args)

            else:
                await ctx.message.add_reaction("❌")

        elif args[0].lower() in ["delete", "del", "d"]:

            if len(args) <= 1:
                embed = discord.Embed(
                    title="manage delete, m d", colour=self.colour,
                    description="removes a member in the database"
                )
                embed.add_field(name="Format", value=f"*`{self.prefix}manage delete <exact_name>`*", inline=False)
                await ctx.channel.send(embed=embed)

            elif len(args) == 2:
                await self.management_guild_add_delete(ctx, args)

            else:
                await ctx.message.add_reaction("❌")

        elif args[0].lower() in ["update", "u"]:

            if len(args) <= 1:
                embed = discord.Embed(
                    title="manage update, m u", colour=self.colour,
                    description="updates a guild member's profile"
                )
                embed.add_field(
                    name="field :: value",
                    value=f"• **name** :: <new_name>\n"
                          f"• **notes** :: *<any officer notes>*\n"
                          f"• **role** :: *{', '.join(self.roles)}*\n"
                          f"• **status** :: *{', '.join(self.member_status)}*",
                    inline=False
                )
                embed.add_field(name="Format", value=f"*`{self.prefix}m u <name or id> <field> <value>`*")
                embed.add_field(
                    name="Batch updating",
                    value="available for inactives & semi-actives [pluralized form]",
                    inline=False
                )
                embed.add_field(
                    name="Example",
                    value=f"*`{self.prefix}m u 1 role member`*\n"
                          f"*`{self.prefix}m u 100 notes alt account`*\n"
                          f"*`{self.prefix}m u inactives`*",
                    inline=False
                )
                await ctx.channel.send(embed=embed)

            elif args[1].lower() in list(self.status_batch) and len(args) == 2:
                await self.management_guild_update_performance(
                    ctx, args[1].lower()[:-1], self.status_batch[args[1].lower()]
                )

            elif args[1].lower() == "feats" and len(args) == 2:
                await self.management_guild_update_feats(ctx)

            elif len(args) == 2:
                fields_formatted = []
                for field in self.fields:
                    fields_formatted.append(f"{field}")

                embed = discord.Embed(
                    colour=self.colour,
                    title="Invalid `update` syntax",
                    description="no field and value provided"
                )
                embed.add_field(
                    name="Valid fields",
                    value="*" + ', '.join(fields_formatted) + "*"
                )
                embed.add_field(
                    name="Example",
                    value=f"*`{self.prefix}m u 1 role member`*\n",
                    inline=False
                )
                await ctx.channel.send(embed=embed)

            elif args[2].lower() not in self.fields and len(args) >= 3:
                fields_formatted = []
                for field in self.fields:
                    fields_formatted.append(f"{field}")

                embed = discord.Embed(
                    colour=self.colour,
                    title="Invalid `update` syntax",
                    description="field entered is not valid"
                )
                embed.add_field(
                    name="Valid fields",
                    value="*" + ', '.join(fields_formatted) + "*"
                )
                await ctx.channel.send(embed=embed)

            elif args[2].lower() in self.fields and len(args) == 3:
                embed = discord.Embed(
                    colour=self.colour,
                    title="Invalid `update` syntax",
                    description="no value provided for the field"
                )
                await ctx.channel.send(embed=embed)

            elif len(args) >= 4 and args[2].lower() in self.fields:
                await self.management_guild_update_field(ctx, args)

            else:
                await ctx.message.add_reaction("❌")

        elif args[0].lower() in ["show", "s"]:

            if len(args) == 1:
                embed = discord.Embed(
                    title="manage show, m s", colour=self.colour,
                    description="queries the guild database"
                )
                embed.add_field(
                    name="Formats",
                    value=f"• *`{self.prefix}m s all <opt: [<startswith> or guild]>`*\n"
                          f"• *`{self.prefix}m s all <role or status> <value>`*\n"
                          f"• *`{self.prefix}m s <name or id_num>`*",
                    inline=False
                )
                embed.add_field(
                    name="Examples",
                    value=f"• *`{self.prefix}m s all`*\n"
                          f"• *`{self.prefix}m s all aki`*\n"
                          f"• *`{self.prefix}m s all status inactive`*\n"
                          f"• *`{self.prefix}m s 120`*\n"
                          f"• *`{self.prefix}m s all <guild/abc/123>`*",
                    inline=False
                )
                await ctx.channel.send(embed=embed)

            elif len(args) == 2 and args[1].lower() == "role":
                roles_formatted = []
                for role in self.roles:
                    roles_formatted.append(f"{role}")

                embed = discord.Embed(
                    colour=self.colour,
                    title="Invalid `show` syntax",
                    description="provide a role value to show"
                )
                embed.add_field(
                    name="Valid statuses",
                    value="*" + ', '.join(roles_formatted) + "*"
                )
                await ctx.channel.send(embed=embed)

            elif len(args) == 2 and args[1].lower() == "status":
                statuses_formatted = []
                for status in self.member_status:
                    statuses_formatted.append(f"{status}")

                embed = discord.Embed(
                    colour=self.colour,
                    title="Invalid `show` syntax",
                    description="provide a status value to show"
                )
                embed.add_field(
                    name="Valid statuses",
                    value="*" + ', '.join(statuses_formatted) + "*"
                )
                await ctx.channel.send(embed=embed)

            elif len(args) == 2 and args[1].lower() == "all":
                await self.management_guild_show_all(ctx, [("name_lower", 1)])

            elif len(args) == 3 and args[1].lower() == "all" \
                    and args[2].lower() in ["abc", "123"]:

                if args[2].lower() == "abc":
                    await self.management_guild_show_all(ctx, [("name_lower", 1)])

                elif args[2].lower() == "123":
                    await self.management_guild_show_all(ctx, [("#", 1)])

                else:
                    await ctx.message.add_reaction("❌")

            elif len(args) == 3 \
                    and args[1].lower() == "all" and args[2].lower() == "guild":
                await self.management_guild_show_current_members(ctx)

            elif len(args) == 3 and args[1].lower() == "all":
                await self.management_guild_show_startswith(ctx, args)

            elif len(args) == 2 and args[1].lower() != "all" \
                    and args[1].lower() not in self.fields:
                await self.management_guild_show_profile(ctx, args)

            elif len(args) == 3 and args[1].lower() == "status" \
                    and args[2].lower() in self.member_status:
                await self.management_guild_show_field_status(ctx, args)

            elif len(args) == 3 and \
                    args[1].lower() == "role" and args[2].lower() in self.roles:
                await self.management_guild_show_field_role(ctx, args)

            else:
                await ctx.message.add_reaction("❌")

        elif args[0].lower() in ["stats"]:

            if len(args) >= 1:
                await self.management_guild_show_stats(ctx)

            else:
                await ctx.message.add_reaction("❌")

        else:
            await ctx.message.add_reaction("❌")

    async def management_guild_update_feats(self, ctx):

        embed = discord.Embed(
            colour=self.colour,
            title="opening the environment for batch updating of `inactives`.."
        )
        msg = await ctx.channel.send(embed=embed)
        await asyncio.sleep(3)
        embed = discord.Embed(
            colour=self.colour,
            title="enter stop/skip to exit the environment or skip a member, respectively.."
        )
        await msg.edit(embed=embed)
        await asyncio.sleep(3)

        embed = discord.Embed(
            color=ctx.author.colour,
            title="Performing initial calculations ...",
            description="iterating first..."
        )
        msg = await ctx.channel.send("Enter the total feats for: ", embed=embed)

        def check(m):
            try:
                int(m.content)
            except ValueError:
                if m.content.lower() == "stop" \
                        and m.author == ctx.message.author and m.channel == ctx.channel:
                    raise TypeError
                elif m.content.lower() == "skip" \
                        and m.author == ctx.message.author and m.channel == ctx.channel:
                    raise IndexError
                elif m.content.lower() not in ["stop", "skip"] \
                        and m.author == ctx.message.author and m.channel == ctx.channel:
                    raise KeyError
            return m.author == ctx.message.author and m.channel == ctx.channel

        find_query = {"role": {"$in": ["officer", "member", "leader"]}}
        project = {
            "_id": 0, "name": 1, "role": 1, "#": 1, "status": 1, "total_feats": 1, "weekly_gq": 1, "status_update": 1
        }

        for member in members.find(find_query, project).sort([("total_feats", 1)]):
            embed = discord.Embed(
                color=ctx.author.colour,
                title=f"#{member['#']} : {member['name']} | 🎀 {member['role']}"
            )
            embed.set_thumbnail(url=ctx.guild.icon_url)
            embed.add_field(
                name="⛳ Status",
                value=f"{member['status']} [{member['status_update'].strftime('%d.%b %y')}]"
            )
            embed.add_field(
                name="🏆 Feats | GQ",
                value=f"{member['total_feats']} | {member['weekly_gq']} [Wk{self.get_time().isocalendar()[1]}]"
            )
            await asyncio.sleep(1)
            await msg.edit(embed=embed)

            i = 0
            while i < 1:
                try:
                    answer = await self.client.wait_for("message", timeout=180, check=check)
                except IndexError:
                    break
                except TypeError:
                    embed = discord.Embed(colour=self.colour, title="Exiting environment..")
                    msg = await ctx.channel.send(embed=embed)
                    await msg.add_reaction("✅")
                    i = "cancel"
                    break
                except KeyError:
                    embed = discord.Embed(colour=self.colour, title="Invalid input")
                    msg = await ctx.channel.send(embed=embed)
                    await asyncio.sleep(2)
                    await msg.delete()
                    i = 0
                except asyncio.TimeoutError:
                    embed = discord.Embed(colour=self.colour, title="Timeout! Exiting...")
                    msg = await ctx.channel.send(embed=embed)
                    await asyncio.sleep(1)
                    await msg.add_reaction("✅")
                    i = "cancel"
                    break
                else:
                    value = int(answer.content)
                    members.update_one({"name": str(member["name"])}, {"$set": {"total_feats": value}})
                    await answer.add_reaction("✅")
                    await asyncio.sleep(2)
                    await answer.delete()
                    break
            if i == "cancel":
                break
            else:
                continue

    async def management_guild_update_field(self, ctx, args):
        try:
            reference_id = int(args[1])
            find_query = {"#": reference_id}
            name = "kyrvscyl"

        except ValueError:
            find_query = {"name_lower": args[1].lower()}
            reference_id = 1
            name = args[1].lower()

        if members.find_one({"name_lower": name}) is None or members.find_one({"#": reference_id}) is None:
            await self.management_guild_show_approximate(ctx, args[1])

        elif args[2].lower() == "status" and args[3].lower() in self.member_status:
            update = {"status": args[3].lower(), "status_update": self.get_time()}

            if args[3].lower() in ["active", "inactive", "semi-active"]:
                update.update({"weekly_gq": self.get_guild_quest_converted(args[3].lower()), "role": "member"})

            if args[3].lower() in ["away", "left", "kicked"]:
                update.update({"role": "ex-member"})

            members.update_one(find_query, {"$set": update})
            await ctx.message.add_reaction("✅")

        elif args[2].lower() in ["notes", "note"]:
            members.update_one(find_query, {
                "$push": {
                    "notes": {
                        "officer": ctx.author.name,
                        "time": self.get_time(),
                        "note": " ".join(args[3::])
                    }
                }
            })
            await ctx.message.add_reaction("✅")

        elif args[2].lower() == "name":
            members.update_one(find_query, {"$set": {"name": args[3], "name_lower": args[3].lower()}})
            await ctx.message.add_reaction("✅")

        elif args[2].lower() == "role" and args[3].lower() in self.roles:
            members.update_one(find_query, {"$set": {"role": args[3].lower()}})
            await ctx.message.add_reaction("✅")

            embed = discord.Embed(
                colour=self.colour,
                title="Role updating notice",
                description="Role changes may require to adjust their status as well"
            )
            msg = await ctx.channel.send(embed=embed)
            await msg.delete(delay=7)

        elif args[2].lower() == "tfeat":
            try:
                total_feat_new = int(args[3])
                members.update_one(find_query, {"$set": {"total_feats": total_feat_new}})
                await ctx.message.add_reaction("✅")

            except ValueError:
                await ctx.message.add_reaction("❌")

        elif args[2].lower() == "gq":
            try:
                value = int(args[3])
                if value in [30, 60, 90]:
                    members.update_one(find_query, {
                        "$set": dict(
                            status=self.get_status(value),
                            status_update=self.get_time(),
                            weekly_gq=value
                        )
                    })
                else:
                    await ctx.message.add_reaction("❌")

            except ValueError:
                await ctx.message.add_reaction("❌")

        else:
            await ctx.message.add_reaction("❌")

    async def management_guild_update_performance(self, ctx, status, weekly_gq):

        embed = discord.Embed(
            color=ctx.author.colour,
            description=f"enter the ID/names of the {status} members separated by spaces"
        )
        embed.add_field(name="Example", value="*`kyrvsycl xann happybunny shaly, 5, 7, 172`*")
        await ctx.channel.send(embed=embed)

        def check(m):
            return m.author == ctx.message.author and m.channel.id == ctx.channel.id

        async with ctx.channel.typing():
            try:
                submitted_list = await self.client.wait_for("message", timeout=360, check=check)
            except asyncio.TimeoutError:
                embed = discord.Embed(
                    colour=self.colour, title="Batch update cancelled",
                    description=f"the submission time lapsed"
                )
                await ctx.channel.send(embed=embed)
                return
            else:
                accepted, not_accepted, already_inactive = [], [], []
                for member in submitted_list.content.split(" "):
                    try:
                        search = int(member)
                        find_query = {"#": search}
                    except ValueError:
                        search = member.lower()
                        find_query = {"name_lower": search}

                    if members.find_one(find_query) is not None:
                        profile = members.find_one(find_query, {"_id": 0, "name": 1, "status": 1})
                        if profile["status"] == status:
                            already_inactive.append(profile["name"])
                        else:
                            accepted.append(profile["name"])
                    else:
                        not_accepted.append(member)

        values = [already_inactive, accepted, not_accepted, ]
        values_formatted = []

        for value in values:
            if len(value) == 0:
                values_formatted.append("None")
            else:
                values_formatted.append(", ".join(value))

        timeout = 120
        embed = discord.Embed(
            colour=ctx.author.colour, title="Revision summary",
            description=f"react within {timeout} seconds to confirm the changes", timestamp=self.get_timestamp()
        )
        embed.add_field(
            name=f"{len(not_accepted)} already inactive {self.pluralize('member', len(not_accepted))}",
            value=values_formatted[0],
            inline=False
        )
        embed.add_field(
            name=f"{len(accepted)} new inactive {self.pluralize('member', len(accepted))}",
            value=values_formatted[1],
            inline=False
        )
        embed.add_field(
            name=f"{len(not_accepted)} invalid {self.pluralize('member', len(not_accepted))}",
            value=values_formatted[2],
            inline=False
        )
        msg = await ctx.channel.send(embed=embed)
        await msg.add_reaction("✅")

        def check(r, u):
            return u == ctx.author and str(r.emoji) == "✅" and msg.id == r.message.id

        try:
            await self.client.wait_for("reaction_add", timeout=timeout, check=check)
        except asyncio.TimeoutError:
            embed = discord.Embed(
                colour=self.colour,
                description=f"there was no confirmation received",
                title="Batch update cancelled",
                timestamp=self.get_timestamp()
            )
            await ctx.channel.send(embed=embed)
        else:
            async with ctx.channel.typing():
                for member in accepted:
                    members.update_one({
                        "name_lower": member.lower()}, {
                        "$set": {
                            "status": status,
                            "weekly_gq": weekly_gq,
                            "status_update": self.get_time()
                        }
                    })

                embed = discord.Embed(
                    colour=ctx.author.colour,
                    title=f"{status.capitalize()} list batch update successful",
                    description=", ".join(accepted),
                    timestamp=self.get_timestamp()
                )
                embed.set_footer(text=f"{len(accepted)} inactive {self.pluralize('member', len(accepted))}")
                await ctx.channel.send(embed=embed)

    async def management_guild_show_field_status(self, ctx, args):

        formatted_list = []
        find_query = {"status": args[2]}
        project = {"_id": 0, "name": 1, "status_update": 1, "#": 1}

        for member in members.find(find_query, project).sort([("status_update", 1)]):
            number = self.lengthen_code(member["#"])
            status_update_formatted = member["status_update"].strftime("%d.%b %y")
            formatted_list.append(f"`{number}: {status_update_formatted}` | {member['name']}\n")

        noun = self.pluralize("result", len(formatted_list))
        content = f"I've got {len(formatted_list)} {noun} for members with status {args[2].lower()}"
        await self.management_guild_paginate_embeds(ctx, formatted_list, content)

    async def management_guild_show_current_members(self, ctx):

        formatted_list = []
        find_query = {"role": {"$in": ["officer", "member", "leader", "trader"]}}
        project = {"_id": 0, "name": 1, "role": 1, "#": 1, "status": 1}

        for member in members.find(find_query, project).sort([("total_feats", -1)]):
            role = self.shorten_code(member["role"])
            status = self.shorten_code(member["status"])
            number = self.lengthen_code(member["#"])
            formatted_list.append(f"`{number}: {role}` | `{status}` | {member['name']}\n")

        noun = self.pluralize("member", len(formatted_list))
        content = f"There are {len(formatted_list)} {noun} currently in the guild"
        await self.management_guild_paginate_embeds(ctx, formatted_list, content)

    async def management_guild_show_startswith(self, ctx, args):

        formatted_list = []
        find_query = {"name_lower": {"$regex": f"^{args[2].lower()}"}}
        project = {"_id": 0, "name": 1, "role": 1, "#": 1, "status": 1}

        for member in members.find(find_query, project).sort([("name_lower", 1)]):
            role = self.shorten_code(member["role"])
            status = self.shorten_code(member["status"])
            number = self.lengthen_code(member["#"])
            formatted_list.append(f"`{number}: {role}` | `{status}` | {member['name']}\n")

        noun = self.pluralize("result", len(formatted_list))
        content = f"I've got {len(formatted_list)} {noun} for names starting with __{args[2].lower()}__"
        await self.management_guild_paginate_embeds(ctx, formatted_list, content)

    async def management_guild_show_stats(self, ctx):

        guild_members_all = members.count({
            "role": {
                "$in": ["officer", "member", "leader", "trader"]}
        })
        guild_members_actv = members.count({
            "role": {
                "$in": ["officer", "member", "leader", "trader"]},
            "status": "active"
        })
        guild_members_inac = members.count({
            "role": {
                "$in": ["officer", "member", "leader", "trader"]},
            "status": "inactive"
        })
        guild_members_onlv = members.count({
            "role": {
                "$in": ["officer", "member", "leader", "trader"]},
            "status": "on-leave"
        })
        guild_members_smac = members.count({
            "role": {
                "$in": ["officer", "member", "leader", "trader"]},
            "status": "semi-active"
        })
        guild_members_away = members.count({
            "role": "ex-member", "status": "away"
        })
        guild_applicants = members.count({
            "role": "applicant"
        })
        guild_blacklists = members.count({
            "role": "blacklist"
        })
        guild_traders = members.count({
            "role": "trader"
        })

        description = \
            f"```" \
            f"• Total Accounts    :: {members.count():,d}\n" \
            f"• Guild Occupancy   :: {guild_members_all:,d}/170\n" \
            f"  • Traders         :: {guild_traders:,d}\n" \
            f"  • Active          :: {guild_members_actv:,d}\n" \
            f"  • Semi-active     :: {guild_members_smac:,d}\n" \
            f"  • Inactive        :: {guild_members_inac:,d}\n" \
            f"  • On-leave        :: {guild_members_onlv:,d}\n" \
            f"  • Away            :: {guild_members_away:,d}\n" \
            f"  • ~ GQ/week       :: {guild_members_actv * 90 + guild_members_smac * 30:,d}\n" \
            f"• Applicants        :: {guild_applicants:,d}\n" \
            f"• Blacklisted       :: {guild_blacklists:,d}" \
            f"```"

        embed = discord.Embed(
            color=ctx.author.colour, title="🔱 Guild Statistics",
            description=f"{description}", timestamp=self.get_timestamp()
        )
        embed.set_thumbnail(url=ctx.guild.icon_url)
        await ctx.channel.send(embed=embed)

    async def management_guild_show_all(self, ctx, sort):

        formatted_list = []
        find_query = {}
        project = {"_id": 0, "name": 1, "role": 1, "#": 1, "status": 1}

        for member in members.find(find_query, project).sort(sort):
            role = self.shorten_code(member["role"])
            status = self.shorten_code(member["status"])
            number = self.lengthen_code(member["#"])
            name = member['name']
            formatted_list.append(f"`{number}: {role}` | `{status}` | {name} \n")

        noun = self.pluralize("account", len(formatted_list))
        content = f"There are {len(formatted_list)} registered {noun}"
        await self.management_guild_paginate_embeds(ctx, formatted_list, content)

    async def management_guild_show_field_role(self, ctx, args):

        formatted_list = []
        filter_query = {"role": args[2]}
        project = {"_id": 0, "name": 1, "status_update": 1, "#": 1, "role": 1}

        for member in members.find(filter_query, project).sort([("status_update", 1)]):
            number = self.lengthen_code(member["#"])
            status_update_formatted = member["status_update"].strftime("%d.%b %y")
            formatted_list.append(f"`{number}: {status_update_formatted}` | {member['name']}\n")

        noun = self.pluralize("result", len(formatted_list))
        content = f"I've got {len(formatted_list)} {noun} for members with role {args[2].lower()}"
        await self.management_guild_paginate_embeds(ctx, formatted_list, content)

    async def management_guild_show_profile(self, ctx, args):
        try:
            name_id = int(args[1])
            member = members.find_one({"#": name_id}, {"_id": 0})

        except ValueError:
            member = members.find_one({"name_lower": args[1].lower()}, {"_id": 0})

        try:
            def get_emoji_role(x):
                return self.roles_emoji[x]

            embed = discord.Embed(
                color=ctx.author.colour,
                title=f"#{member['#']} : {member['name']} | {get_emoji_role(member['role'])} {member['role'].title()}",
                timestamp=self.get_timestamp()
            )
            embed.set_thumbnail(url=ctx.guild.icon_url)
            embed.add_field(
                name="⛳ Status",
                value=f"{member['status'].title()} [{member['status_update'].strftime('%d.%b %y')}]"
            )

            if not member["notes"]:
                embed.add_field(name="🗒 Notes", value="No notes yet.")

            elif len(member["notes"]) != 0:
                notes = ""
                for note in member["notes"]:
                    entry = f"[{note['time'].strftime('%d.%b %y')} | {note['officer']}]: {note['note']}\n"
                    notes += entry

                embed.add_field(name="🗒 Notes", value=notes, inline=False)
            await ctx.channel.send(embed=embed)

        except TypeError:
            await self.management_guild_show_approximate(ctx, args[1])

    async def management_guild_show_approximate(self, ctx, query):
        members_search = members.find({"name_lower": {"$regex": f"^{query[:2].lower()}"}}, {"_id": 0})

        approximate_results = []
        for result in members_search:
            approximate_results.append(f"{result['#']}/{result['name']}")

        embed = discord.Embed(
            colour=self.colour,
            title="Invalid query",
            description=f"The ID/name `{query}` returned no results"
        )
        embed.add_field(
            name="Possible matches",
            value="*{}*".format(", ".join(approximate_results))
        )
        await ctx.channel.send(embed=embed)

    async def management_guild_add_member(self, ctx, args):
        if members.find_one({"name_lower": args[2].lower()}) is None:

            profile = {
                "#": members.count() + 1,
                "name": args[2],
                "role": args[1].lower(),
                "status": "active",
                "notes": [],
                "name_lower": args[2].lower(),
                "total_feats": 0,
                "weekly_gq": 30,
                "status_update": self.get_time()
            }
            members.insert_one(profile)
            await ctx.message.add_reaction("✅")

        else:
            embed = discord.Embed(
                title="Invalid name", colour=self.colour,
                description="that name already exists in the database"
            )
            await ctx.channel.send(embed=embed)

    async def management_guild_add_delete(self, ctx, args):
        if members.find_one({"name": args[1]}) is not None:
            members.delete_one({"name": args[1]})
            await ctx.message.add_reaction("✅")

            name_id = 1
            for member in members.find({}, {"_id": 0, "name": 1}):
                members.update_one({"name": member["name"]}, {"$set": {"#": name_id}})
                name_id += 1

        else:
            embed = discord.Embed(
                colour=self.colour,
                title="Invalid user",
                descrption="Input the exact name including the letter cases"
            )
            await ctx.channel.send(embed=embed)

    async def management_guild_paginate_embeds(self, ctx, list_formatted, caption):

        page, lines_max = 1, 20
        page_total = ceil(len(list_formatted) / lines_max)
        if page_total == 0:
            page_total = 1

        def embed_create_page_new(page_new):
            end = page_new * lines_max
            start = end - lines_max
            description_new = "".join(list_formatted[start:end])

            embed_new = discord.Embed(
                color=ctx.author.colour, title="🔱 Guild Registry",
                description=f"{description_new}", timestamp=self.get_timestamp()
            )
            embed_new.set_footer(text=f"Page: {page_new} of {page_total}")
            embed_new.set_thumbnail(url=ctx.guild.icon_url)
            return embed_new

        msg = await ctx.channel.send(content=caption, embed=embed_create_page_new(page))
        await msg.add_reaction("⬅")
        await msg.add_reaction("➡")

        def check(r, u):
            return u != self.client.user and r.message.id == msg.id

        while True:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=180, check=check)
            except asyncio.TimeoutError:
                await msg.clear_reactions()
                break
            else:
                if str(reaction.emoji) == "➡":
                    page += 1
                elif str(reaction.emoji) == "⬅":
                    page -= 1
                if page == 0:
                    page = page_total
                elif page > page_total:
                    page = 1
                await msg.edit(embed=embed_create_page_new(page))


def setup(client):
    client.add_cog(Admin(client))
