"""
Admin Module
Miketsu, 2019
"""

import asyncio
import re
from datetime import datetime
from math import ceil

import discord
import pytz
from discord.ext import commands

from cogs.mongo.database import get_collections
from cogs.startup import pluralize, primary_id, embed_color

# Collections
books = get_collections("bukkuman", "books")
members = get_collections("bukkuman", "members")
frames = get_collections("miketsu", "frames")
users = get_collections("miketsu", "users")
ships = get_collections("miketsu", "ships")

# Listings
fields = ["name", "role", "status", "notes", "note", "tfeat", "gq"]
roles = ["member", "ex-member", "officer", "leader", "blacklist"]
status_values = ["active", "inactive", "on-leave", "kicked", "semi-active", "away", "left", "trade"]
status_batch = {"inactives": 30, "semi-actives": 60}
admin_roles = ["Head", "Alpha", "📝"]


def check_if_has_any_role(ctx):
    for role in reversed(ctx.author.roles):
        if role.name in admin_roles:
            return True
    return False


def check_if_guild_is_primary(ctx):
    if ctx.author.id == 180717337475809281:
        return True
    return ctx.guild.id == primary_id


def get_time():
    tz_target = pytz.timezone("America/Atikokan")
    return datetime.now(tz=tz_target)


def get_timestamp():
    return datetime.utcfromtimestamp(datetime.timestamp(datetime.now()))


def get_status(key):
    dictionary = {"30": "inactive", "60": "semi-active", "90": "active"}
    return dictionary[str(key)]


def get_gq(key):
    dictionary = {"inactive": "30", "semi-active": "60", "active": "90"}
    return dictionary[str(key)]


def shorten(key):
    dictionary = {
        "leader": "LDR", "member": "MEM", "officer": "OFR", "ex-member": "EXM", "active": "ACTV", "inactive": "INAC",
        "on-leave": "ONLV", "semi-active": "SMAC", "away": "AWAY", "left": "LEFT", "kicked": "KCKD", "trade": "TRDE"
    }
    return dictionary[key]


def lengthen(index):
    prefix = "#{}"
    if index < 10:
        prefix = "#00{}"
    elif index < 100:
        prefix = "#0{}"
    return prefix.format(index)


async def management_guild_show_stats(ctx):
    guild_members_all = members.count({
        "role": {
            "$in": ["officer", "member", "leader"]}
    })
    guild_members_actv = members.count({
        "role": {
            "$in": ["officer", "member", "leader"]},
        "status": "active"
    })
    guild_members_inac = members.count({
        "role": {
            "$in": ["officer", "member", "leader"]},
        "status": "inactive"
    })
    guild_members_onlv = members.count({
        "role": {
            "$in": ["officer", "member", "leader"]},
        "status": "on-leave"
    })
    guild_members_smac = members.count({
        "role": {
            "$in": ["officer", "member", "leader"]},
        "status": "semi-active"
    })
    guild_members_trde = members.count({
        "role": {
            "$in": ["officer", "member", "leader"]},
        "status": "trade"
    })
    guild_members_away = members.count({
        "role": "ex-member", "status": "away"
    })

    description = \
        f"```" \
        f"• Total Accounts    :: {members.count()}\n" \
        f"• Guild Occupancy   :: {guild_members_all}/170\n" \
        f"  • Active          :: {guild_members_actv}\n" \
        f"  • Semi-active     :: {guild_members_smac}\n" \
        f"  • Inactive        :: {guild_members_inac}\n" \
        f"  • On-leave        :: {guild_members_onlv}\n" \
        f"  • Trade           :: {guild_members_trde}\n" \
        f"  • Away            :: {guild_members_away}\n" \
        f"  • ~ GQ/week       :: {guild_members_actv * 90 + guild_members_smac * 30:,d}" \
        f"```"

    embed = discord.Embed(
        color=ctx.author.colour, title="🔱 Guild Statistics", description=f"{description}", timestamp=get_timestamp()
    )
    embed.set_thumbnail(url=ctx.guild.icon_url)
    await ctx.channel.send(embed=embed)


async def management_guild_show_profile(ctx, args):
    try:
        reference_id = int(args[1])
        member = members.find_one({"#": reference_id}, {"_id": 0})

    except ValueError:
        member = members.find_one({"name_lower": args[1].lower()}, {"_id": 0})

    try:
        embed = discord.Embed(
            color=ctx.author.colour,
            title=f"#{member['#']} : {member['name']} | 🎀 {member['role']}", timestamp=get_timestamp()
        )
        embed.set_thumbnail(url=ctx.guild.icon_url)
        embed.add_field(
            name="⛳ Status",
            value=f"{member['status']} [{member['status_update1']}]"
        )

        if not member["notes"]:
            embed.add_field(name="🗒 Notes", value="No notes yet.")

        elif len(member["notes"]) != 0:
            notes = ""
            for note in member["notes"]:
                entry = f"[{note['time']} | {note['officer']}]: {note['note']}\n"
                notes += entry

            embed.add_field(name="🗒 Notes", value=notes)
        await ctx.channel.send(embed=embed)

    except TypeError:
        embed = discord.Embed(colour=discord.Colour(embed_color), title="No such member is found in the database")
        await ctx.channel.send(embed=embed)


async def management_guild_update_field(ctx, args):
    try:
        reference_id = int(args[1])
        find_query = {"#": reference_id}
        name = "kyrvscyl"

    except ValueError:
        find_query = {"name_lower": args[1].lower()}
        reference_id = 1
        name = args[1].lower()

    if members.find_one({"name_lower": name}) is None or members.find_one({"#": reference_id}) is None:
        embed = discord.Embed(colour=discord.Colour(embed_color), title="No such member is found in the database")
        await ctx.channel.send(embed=embed)

    elif args[2].lower() == "status" and args[3].lower() in status_values:

        update = {"$set": {"status": args[3].lower(), "status_update": get_time()}}

        if args[3].lower() in ["active", "inactive", "semi-active"]:
            weekly_gq_add = {"weekly_gq": get_gq(args[3].lower())}
            set_dict = update["$set"]
            set_dict.update(weekly_gq_add)
            update.update(set_dict)

        if args[3].lower() in ["away", "left", "kicked"]:
            new_role = {"role": "ex-member"}
            set_dict = update["$set"]
            set_dict.update(new_role)
            update.update(set_dict)

        members.update_one(find_query, update)
        await ctx.message.add_reaction("✅")

    elif args[2].lower() in ["notes", "note"]:
        members.update_one(find_query, {
            "$push": {
                "notes": {
                    "officer": ctx.author.name,
                    "time": get_time(),
                    "note": " ".join(args[3::])
                }
            }
        })
        await ctx.message.add_reaction("✅")

    elif args[2].lower() == "name":
        members.update_one(find_query, {"$set": {"name": args[3], "name_lower": args[3].lower()}})
        await ctx.message.add_reaction("✅")

    elif args[2].lower() == "role" and args[3].lower() in roles:
        members.update_one(find_query, {"$set": {"role": args[3].lower()}})
        await ctx.message.add_reaction("✅")
        embed = discord.Embed(
            colour=discord.Colour(embed_color),
            title="Role Update Notice",
            description="Changing the member's role may require to change the status also"
        )
        msg = await ctx.channel.send(embed=embed)
        await msg.delete(delay=10)

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
                        status=get_status(value),
                        status_update=get_time(),
                        weekly_gq=value
                    )
                })
            else:
                await ctx.message.add_reaction("❌")

        except ValueError:
            await ctx.message.add_reaction("❌")

    else:
        await ctx.message.add_reaction("❌")


async def management_guild_add_member(ctx, args):
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
            "status_update": get_time()
        }
        members.insert_one(profile)
        await ctx.message.add_reaction("✅")

    else:
        embed = discord.Embed(
            title="Invalid name", colour=discord.Colour(embed_color),
            description="That name already exists in the database"
        )
        await ctx.channel.send(embed=embed)


class Admin(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(aliases=["announce"])
    @commands.check(check_if_has_any_role)
    async def announcement_post_embed(self, ctx, channel: discord.TextChannel = None, *, args):

        list_msg = args.split("|", 2)
        embed = discord.Embed(color=ctx.author.colour)

        if len(list_msg) == 1:
            embed.description = list_msg[0]

        elif len(list_msg) == 2:
            embed.title = list_msg[0]
            embed.description = list_msg[1]

        elif len(list_msg) == 3:
            embed.title = list_msg[0]
            embed.description = list_msg[1]
            embed.set_image(url=list_msg[2])
        else:
            return

        try:
            await channel.send(embed=embed)
            await ctx.message.add_reaction("✅")
        except AttributeError:
            return
        except discord.errors.Forbidden:
            return
        except discord.errors.HTTPException:
            return

    @commands.command(aliases=["say"])
    @commands.check(check_if_has_any_role)
    async def announcement_post_message(self, ctx, arg1, *, args):

        try:
            channel_id = re.sub("[<>#]", "", arg1)
            channel_target = self.client.get_channel(int(channel_id))
            await channel_target.send(args)
            await ctx.message.add_reaction("✅")

        except AttributeError:
            embed = discord.Embed(
                colour=discord.Colour(embed_color),
                description="The specified channel ID was not found."
            )
            await ctx.channel.send(embed=embed)
        except discord.errors.Forbidden:
            return
        except discord.errors.HTTPException:
            return

    @commands.command(aliases=["clear", "cl"])
    @commands.check(check_if_has_any_role)
    async def purge_messages(self, ctx, amount=2):
        try:
            await ctx.channel.purge(limit=amount + 1)
        except discord.errors.Forbidden:
            pass
        except discord.errors.HTTPException:
            pass

    @commands.command(aliases=["m", "manage"])
    @commands.check(check_if_has_any_role)
    @commands.check(check_if_guild_is_primary)
    async def management_guild(self, ctx, *args):

        if len(args) == 0 or args[0].lower() in ["help", "h"]:
            embed = discord.Embed(
                title="manage, m", colour=discord.Colour(embed_color),
                description="shows the help prompt for the first 3 arguments"
            )
            embed.add_field(name="Arguments", value="*add, update, show, stats*", inline=False)
            embed.add_field(name="Example", value="*`;manage add`*", inline=False)
            await ctx.channel.send(embed=embed)

        elif args[0].lower() == "add" and len(args) <= 2:
            embed = discord.Embed(
                title="manage add, m add", colour=discord.Colour(embed_color),
                description="add a new guild member in the database"
            )
            embed.add_field(name="Format", value="*`;manage add <role> <name>`*", inline=False)
            embed.add_field(name="Roles", value="*member, ex-member, officer*", inline=False)
            await ctx.channel.send(embed=embed)

        elif args[0].lower() in ["add", "a"] and len(args) == 3 and args[1].lower() in roles:
            await management_guild_add_member(ctx, args)

        elif args[0].lower() in ["update", "u"] and len(args) <= 1:
            embed = discord.Embed(
                title="manage update, m u", colour=discord.Colour(embed_color),
                description="updates a guild member's profile"
            )
            embed.add_field(name="Format", value="*`;m u <name or id> <field> <value>`*")
            embed.add_field(
                name="field :: value",
                value=f"• **name** :: <new_name>\n"
                      f"• **notes** :: *<any officer notes>*\n"
                      f"• **role** :: *{', '.join(roles)}*\n"
                      f"• **status** :: *{', '.join(status_values)}*",
                inline=False
            )
            embed.add_field(
                name="Batch updating",
                value="Available for inactives & semi-actives [pluralized form]",
                inline=False
            )
            embed.add_field(
                name="Example",
                value="*`;m u 1 role member`*\n"
                      "*`;m u 100 notes alt account`*\n"
                      "*`;m u inactives`*",
                inline=False
            )
            await ctx.channel.send(embed=embed)

        elif args[0].lower() in ["update", "u"] and args[1].lower() in list(status_batch) and len(args) == 2:
            await self.management_guild_update_performance(ctx, args[1].lower(), status_batch[args[1].lower()])

        elif args[0].lower() in ["update", "u"] and args[1].lower() == "feats" and len(args) == 2:
            await self.management_guild_update_feats(ctx)

        elif args[0].lower() in ["update", "u"] and len(args) == 2:
            fields_formatted = []
            for field in fields:
                fields_formatted.append(f"`{field}`")

            embed = discord.Embed(
                colour=discord.Colour(embed_color),
                title="No field and value provided",
                description=f"Valid fields: *{', '.join(fields_formatted)}*"
            )
            await ctx.channel.send(embed=embed)

        elif args[0].lower() in ["update", "u"] and args[2].lower() not in fields and len(args) >= 3:
            fields_formatted = []
            for field in fields:
                fields_formatted.append(f"`{field}`")

            embed = discord.Embed(
                colour=discord.Colour(embed_color),
                title="Invalid field update request",
                description=f"Valid fields: *{', '.join(fields_formatted)}*"
            )
            await ctx.channel.send(embed=embed)

        elif args[0].lower() in ["update", "u"] and args[2].lower() in fields and len(args) == 3:
            embed = discord.Embed(
                colour=discord.Colour(embed_color),
                title="Invalid field update request",
                description=f"No value provided for the field {args[2].lower()}"
            )
            await ctx.channel.send(embed=embed)

        elif args[0].lower() in ["update", "u"] and len(args) >= 4 and args[2].lower() in fields:
            await management_guild_update_field(ctx, args)

        elif args[0].lower() in ["show", "s"] and len(args) == 1:
            embed = discord.Embed(
                title="manage show, m s", colour=discord.Colour(embed_color),
                description="queries the guild database"
            )
            embed.add_field(
                name="Formats",
                value="• *`;m s all <opt: [<startswith> or guild]>`*\n"
                      "• *`;m s all <role or status> <value>`*\n"
                      "• *`;m s <name or id_num>`*",
                inline=False
            )
            embed.add_field(
                name="Examples",
                value="• *`;m s all`*\n"
                      "• *`;m s all aki`*\n"
                      "• *`;m s all status inactive`*\n"
                      "• *`;m s 120`*\n"
                      "• *`;m s all guild`*",
                inline=False
            )
            await ctx.channel.send(embed=embed)

        elif args[0].lower() in ["show", "s"] and len(args) == 2 and args[1].lower() == "role":
            roles_formatted = []
            for role in roles:
                roles_formatted.append(f"`{role}`")

            embed = discord.Embed(
                colour=discord.Colour(embed_color),
                title="Provide a role value to show",
                description=f"Valid values: *`{', '.join(roles_formatted)}`*"
            )
            await ctx.channel.send(embed=embed)

        elif args[0].lower() in ["show", "s"] and len(args) == 2 and args[1].lower() == "status":
            statuses_formatted = []
            for status in status_values:
                statuses_formatted.append(f"`{status}`")

            embed = discord.Embed(
                colour=discord.Colour(embed_color),
                title="Provide a status value to show",
                description=f"Valid values: *`{', '.join(statuses_formatted)}`*"
            )
            await ctx.channel.send(embed=embed)

        elif args[0].lower() in ["show", "s"] and len(args) == 2 and args[1].lower() == "all":
            await self.management_guild_show_all(ctx)

        elif args[0].lower() in ["show", "s"] and len(args) == 3 \
                and args[1].lower() == "all" and args[2].lower() == "guild":
            await self.management_guild_show_current_members(ctx)

        elif args[0].lower() in ["show", "s"] and len(args) == 3 and args[1].lower() == "all":
            await self.management_guild_show_startswith(ctx, args)

        elif args[0].lower() in ["show", "s"] and len(args) == 2 and args[1].lower() != "all" \
                and args[1].lower() not in fields:
            await management_guild_show_profile(ctx, args)

        elif args[0].lower() in ["show", "s"] and len(args) == 3 and args[1].lower() == "status" \
                and args[2].lower() in status_values:
            await self.management_guild_show_field_status(ctx, args)

        elif args[0].lower() in ["show", "s"] and len(args) == 3 and \
                args[1].lower() == "role" and args[2].lower() in roles:
            await self.management_guild_show_field_role(ctx, args)

        elif args[0].lower() == "stats" and len(args) == 1:
            await management_guild_show_stats(ctx)

        else:
            await ctx.message.add_reaction("❌")

    async def management_guild_update_performance(self, ctx, status, weekly_gq):

        embed = discord.Embed(
            color=ctx.author.colour,
            description=f"Enter the names or codes of the {status} members separated by spaces"
        )
        embed.add_field(name="Example", value="*`kyrvsycl xann happybunny shaly`*")
        await ctx.channel.send(embed=embed)

        def check(m):
            return m.author == ctx.message.author and m.channel.id == ctx.channel.id

        async with ctx.channel.typing():
            try:
                submitted_list = await self.client.wait_for("message", timeout=360, check=check)
            except asyncio.TimeoutError:
                embed = discord.Embed(
                    colour=discord.Colour(embed_color), title="Batch update cancelled",
                    description=f"{ctx.author.mention}, you did not submit on time"
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
            colour=ctx.author.colour, title="Revision Summary",
            description=f"react within {timeout} seconds to confirm the changes", timestamp=get_timestamp()
        )
        embed.add_field(
            name=f"{len(not_accepted)} already inactive {pluralize('member', len(not_accepted))}",
            value=values_formatted[0],
            inline=False
        )
        embed.add_field(
            name=f"{len(accepted)} new inactive {pluralize('member', len(accepted))}",
            value=values_formatted[1],
            inline=False
        )
        embed.add_field(
            name=f"{len(not_accepted)} invalid {pluralize('member', len(not_accepted))}",
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
                colour=discord.Colour(embed_color),
                description=f"{ctx.author.mention}, you did not confirm on time",
                title="Batch update cancelled",
                timestamp=get_timestamp()
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
                            "status_update": get_time()
                        }
                    })

                embed = discord.Embed(
                    colour=ctx.author.colour,
                    title=f"{status.capitalize()} list batch update successful",
                    description=", ".join(accepted),
                    timestamp=get_timestamp()
                )
                embed.set_footer(text=f"{len(accepted)} inactive {pluralize('member', len(accepted))}")
                await ctx.channel.send(embed=embed)

    async def management_guild_update_feats(self, ctx):

        embed = discord.Embed(
            colour=discord.Colour(embed_color),
            title="Opening environment for batch updating of inactives.."
        )
        msg = await ctx.channel.send(embed=embed)
        await asyncio.sleep(3)
        embed = discord.Embed(
            colour=discord.Colour(embed_color),
            title="Enter stop/skip to exit the environment or skip a member, respectively.."
        )
        await msg.edit(embed=embed)
        await asyncio.sleep(3)

        embed = discord.Embed(
            color=ctx.author.colour,
            title="Performing initial calculations...",
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
            "_id": 0, "name": 1, "role": 1, "#": 1, "status": 1, "total_feats": 1, "weekly_gq": 1, "status_update1": 1
        }

        for member in members.find(find_query, project).sort([("total_feats", 1)]):
            embed = discord.Embed(
                color=ctx.author.colour,
                title=f"#{member['#']} : {member['name']} | 🎀 {member['role']}"
            )
            embed.set_thumbnail(url=ctx.guild.icon_url)
            embed.add_field(
                name="⛳ Status",
                value=f"{member['status']} [{member['status_update1']}]"
            )
            embed.add_field(
                name="🏆 Feats | GQ",
                value=f"{member['total_feats']} | {member['weekly_gq']} [Wk{get_time().isocalendar()[1]}]"
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
                    embed = discord.Embed(colour=discord.Colour(embed_color), title="Exiting environment..")
                    msg = await ctx.channel.send(embed=embed)
                    await msg.add_reaction("✅")
                    i = "cancel"
                    break
                except KeyError:
                    embed = discord.Embed(colour=discord.Colour(embed_color), title="Invalid input")
                    msg = await ctx.channel.send(embed=embed)
                    await asyncio.sleep(2)
                    await msg.delete()
                    i = 0
                except asyncio.TimeoutError:
                    embed = discord.Embed(colour=discord.Colour(embed_color), title="Timeout! Exiting...")
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

    async def management_guild_show_current_members(self, ctx):

        formatted_list = []
        find_query = {"role": {"$in": ["officer", "member", "leader"]}}
        project = {"_id": 0, "name": 1, "role": 1, "#": 1, "status": 1}

        for member in members.find(find_query, project).sort([("total_feats", -1)]):
            role = shorten(member["role"])
            status = shorten(member["status"])
            number = lengthen(member["#"])
            formatted_list.append(f"`{number}: {role}` | `{status}` | {member['name']}\n")

        noun = pluralize("member", len(formatted_list))
        content = f"There are {len(formatted_list)} {noun} currently in the guild"
        await self.management_guild_paginate_embeds(ctx, formatted_list, content)

    async def management_guild_show_startswith(self, ctx, args):

        formatted_list = []
        find_query = {"name_lower": {"$regex": f"^{args[2].lower()}"}}
        project = {"_id": 0, "name": 1, "role": 1, "#": 1, "status": 1}

        for member in members.find(find_query, project).sort([("name_lower", 1)]):
            role = shorten(member["role"])
            status = shorten(member["status"])
            number = lengthen(member["#"])
            formatted_list.append(f"`{number}: {role}` | `{status}` | {member['name']}\n")

        noun = pluralize("result", len(formatted_list))
        content = f"I've got {len(formatted_list)} {noun} for names starting with __{args[2].lower()}__"
        await self.management_guild_paginate_embeds(ctx, formatted_list, content)

    async def management_guild_show_all(self, ctx):

        formatted_list = []
        find_query = {}
        project = {"_id": 0, "name": 1, "role": 1, "#": 1, "status": 1}

        for member in members.find(find_query, project).sort([("name_lower", 1)]):
            role = shorten(member["role"])
            status = shorten(member["status"])
            number = lengthen(member["#"])
            formatted_list.append(f"`{number}: {role}` | `{status}` | {member['name']}\n")

        noun = pluralize("account", len(formatted_list))
        content = f"There are {len(formatted_list)} registered {noun}"
        await self.management_guild_paginate_embeds(ctx, formatted_list, content)

    async def management_guild_show_field_role(self, ctx, args):

        formatted_list = []
        filter_query = {"role": args[2]}
        project = {"_id": 0, "name": 1, "status_update": 1, "#": 1, "role": 1}

        for member in members.find(filter_query, project).sort([("status_update", 1)]):
            number = lengthen(member["#"])
            status_update_formatted = member["status_update"].strftime("%d.%b %y")
            formatted_list.append(f"`{number}: {status_update_formatted}` | {member['name']}\n")

        noun = pluralize("result", len(formatted_list))
        content = f"I've got {len(formatted_list)} {noun} for members with role {args[2].lower()}"
        await self.management_guild_paginate_embeds(ctx, formatted_list, content)

    async def management_guild_show_field_status(self, ctx, args):

        formatted_list = []
        find_query = {"status": args[2]}
        project = {"_id": 0, "name": 1, "status_update": 1, "#": 1}

        for member in members.find(find_query, project).sort([("status_update", 1)]):
            number = lengthen(member["#"])
            status_update_formatted = member["status_update"].strftime("%d.%b %y")
            formatted_list.append(f"`{number}: {status_update_formatted}` | {member['name']}\n")

        noun = pluralize("result", len(formatted_list))
        content = f"I've got {len(formatted_list)} {noun} for members with status {args[2].lower()}"

        await self.management_guild_paginate_embeds(ctx, formatted_list, content)

    async def management_guild_paginate_embeds(self, ctx, formatted_list, content):

        page = 1
        max_lines = 20
        page_total = ceil(len(formatted_list) / max_lines)
        if page_total == 0:
            page_total = 1

        def create_new_embed_page(page_new):
            end = page_new * max_lines
            start = end - max_lines
            description_new = "".join(formatted_list[start:end])

            embed_new = discord.Embed(
                color=ctx.author.colour, title="🔱 Guild Registry",
                description=f"{description_new}", timestamp=get_timestamp()
            )
            embed_new.set_footer(text=f"Page: {page_new} of {page_total}")
            embed_new.set_thumbnail(url=ctx.guild.icon_url)
            return embed_new

        msg = await ctx.channel.send(content=content, embed=create_new_embed_page(page))
        await msg.add_reaction("⬅")
        await msg.add_reaction("➡")

        def check(r, u):
            return u != self.client.user and r.message.id == msg.id

        while True:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=180, check=check)
            except asyncio.TimeoutError:
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
                await msg.edit(embed=create_new_embed_page(page))


def setup(client):
    client.add_cog(Admin(client))
