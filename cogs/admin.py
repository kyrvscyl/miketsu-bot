"""
Admin Module
Miketsu, 2019
"""

import asyncio
import re
from datetime import datetime

import discord
import pytz
from discord.ext import commands

from cogs.mongo.db import get_collections
from cogs.startup import pluralize, primary_id, embed_color

# Collections
books = get_collections("bukkuman", "books")
members = get_collections("bukkuman", "members")
frames = get_collections("miketsu", "frames")
users = get_collections("miketsu", "users")
ships = get_collections("miketsu", "ships")
shikigamis = get_collections("miketsu", "shikigamis")

# Listings
fields = ["name", "role", "status", "notes", "note", "tfeat", "gq"]
roles = ["member", "ex-member", "officer", "leader"]
status_values = ["active", "inactive", "on-leave", "kicked", "semi-active", "away", "left", "trade"]
valid_roles = ["Head", "Alpha"]


def check_if_has_any_role(ctx):
    for role in reversed(ctx.author.roles):
        if role.name in valid_roles:
            return True
    return False


def check_if_guild_is_primary(ctx):
    return ctx.guild.id == primary_id


def get_time_est():
    tz_target = pytz.timezone("America/Atikokan")
    return datetime.now(tz=tz_target)


def get_timestamp():
    return datetime.utcfromtimestamp(datetime.timestamp(datetime.now()))


def get_status(key):
    dictionary = {"30": "Inactive", "60": "Semi-active", "90": "Active"}
    return dictionary[str(key)]


def shorten(key):
    dictionary = {
        "Leader": "LDR",
        "Member": "MEM",
        "Officer": "OFR",
        "Ex-member": "EXM",
        "Active": "ACTV",
        "Inactive": "INAC",
        "On-leave": "ONLV",
        "Semi-active": "SMAC",
        "Away": "AWAY",
        "Left": "LEFT",
        "Kicked": "KCKD",
        "Trade": "TRDE"
    }
    return dictionary[key]


def lengthen(index):
    prefix = "#{}"
    if index < 10:
        prefix = "#00{}"
    elif index < 100:
        prefix = "#0{}"
    return prefix.format(index)


async def management_show_stats(ctx):
    guild_members_all = members.count({
        "role": {
            "$in": ["Officer", "Member", "Leader"]}
    })
    guild_members_actv = members.count({
        "role": {
            "$in": ["Officer", "Member", "Leader"]},
        "status": "Active"
    })
    guild_members_inac = members.count({
        "role": {
            "$in": ["Officer", "Member", "Leader"]},
        "status": "Inactive"
    })
    guild_members_onlv = members.count({
        "role": {
            "$in": ["Officer", "Member", "Leader"]},
        "status": "On-leave"
    })
    guild_members_smac = members.count({
        "role": {
            "$in": ["Officer", "Member", "Leader"]},
        "status": "Semi-active"
    })

    ex_members_away = members.count({"role": "Ex-member", "status": "Away"})
    description = \
        f"```" \
        f"• Total Accounts    :: {members.count()}\n" \
        f"• Guild Occupancy   :: {guild_members_all}/160\n" \
        f"  • Active          :: {guild_members_actv}\n" \
        f"  • Semi-active     :: {guild_members_smac}\n" \
        f"  • Inactive        :: {guild_members_inac}\n" \
        f"  • On-leave        :: {guild_members_onlv}\n" \
        f"  • Away            :: {ex_members_away}\n" \
        f"  • ~ GQ/week       :: {guild_members_actv * 90 + guild_members_smac * 30:,d}" \
        f"```"

    embed = discord.Embed(
        color=ctx.author.colour, title="🔱 Guild Statistics", description=f"{description}", timestamp=get_timestamp()
    )
    embed.set_thumbnail(url=ctx.guild.icon_url)
    await ctx.channel.send(embed=embed)


async def management_show_profile(ctx, args):
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

        embed.set_thumbnail(url=ctx.guild.icon_url)
        await ctx.channel.send(embed=embed)

    except TypeError:
        embed = discord.Embed(colour=discord.Colour(embed_color), title="That member is not in the guild database")
        await ctx.channel.send(embed=embed)


async def management_update_field(ctx, args):
    try:
        reference_id = int(args[1])
        find_query = {"#": reference_id}
        name = "kyrvscyl"

    except ValueError:
        find_query = {"name_lower": args[1].lower()}
        reference_id = 1
        name = args[1].lower()

    if members.find_one({"name_lower": name}) is None or members.find_one({"#": reference_id}) is None:
        embed = discord.Embed(colour=discord.Colour(embed_color), title="Provided ID/name is not in the guild database")
        await ctx.channel.send(embed=embed)

    elif args[2].lower() == "status" and args[3].lower() in status_values:
        members.update_one(find_query, {
            "$set": {
                "status": args[3].capitalize(),
                "status_update1": get_time_est().strftime('%d.%b %y'),
                "status_update2": get_time_est().strftime('%Y:%m:%d')
            }
        })

        if args[3].lower() in ["away", "left", "kicked"]:
            members.update_one(find_query, {"$set": {"role": "Ex-member"}})
        await ctx.message.add_reaction("✅")

    elif args[2].lower() in ("notes", "note"):
        new_note = " ".join(args[3::])
        members.update_one(find_query, {
            "$push": {
                "notes": {
                    "officer": ctx.author.name,
                    "time": get_time_est().strftime('%d.%b %y'),
                    "note": new_note
                }
            }
        })
        await ctx.message.add_reaction("✅")

    elif args[2].lower() == "name":
        members.update_one(find_query, {
            "$set": {
                "name": args[3],
                "name_lower": args[3].lower()
            }
        })
        await ctx.message.add_reaction("✅")

    elif args[2].lower() == "role" and args[3].lower() in roles:
        members.update_one(find_query, {"$set": {"role": args[3].capitalize()}})
        await ctx.message.add_reaction("✅")
        embed = discord.Embed(
            colour=discord.Colour(embed_color),
            title="Changing the a member role may require to change the status also"
        )
        msg = await ctx.channel.send(embed=embed)
        await msg.delete(delay=5)

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
                        status_update1=get_time_est().strftime('%d.%b %y'),
                        status_update2=get_time_est().strftime('%Y:%m:%d'),
                        weekly_gq=value
                    )
                })
            else:
                await ctx.message.add_reaction("❌")

        except ValueError:
            await ctx.message.add_reaction("❌")

    else:
        await ctx.message.add_reaction("❌")


class Admin(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(aliases=["announce"])
    @commands.check(check_if_has_any_role)
    async def announcement_post_embed(self, ctx, channel: discord.TextChannel = None, *, args):

        list_msg = args.split("|", 2)
        embed = discord.Embed(
            color=ctx.author.colour
        )

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

    @commands.command(aliases=["c", "clear", "purge", "cl", "prune"])
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

        elif args[0].lower() in ["add", "a"] and len(args) == 3 and args[1] in roles:
            if members.find_one({"name_lower": args[2].lower()}) is None:
                count = members.count() + 1

                profile = {
                    "#": count,
                    "name": args[2],
                    "role": args[1].capitalize(),
                    "status": "Active",
                    "status_update1": get_time_est().strftime('%d.%b %y'),
                    "status_update2": get_time_est().strftime('%Y:%m:%d'),
                    "country": "<CC>",
                    "timezone": "['/']",
                    "notes": [],
                    "name_lower": args[2].lower()
                }
                members.insert_one(profile)
                await ctx.message.add_reaction("✅")

            else:
                await ctx.message.add_reaction("❌")

        elif args[0].lower() in ["update", "u"] and len(args) <= 1:
            embed = discord.Embed(
                title="manage update, m u", colour=discord.Colour(embed_color),
                description="updates a guild member's profile"
            )
            embed.add_field(name="Format", value="*`;m u <name or id> <field> <value>`*")
            embed.add_field(
                name="field :: value",
                value="• **name** :: <new_name>\n"
                      "• **notes** :: *<any officer notes>*\n"
                      "• **role** :: *member, ex-member, officer*\n"
                      "• **status** :: *active, inactive, on-leave, kicked, semi-active, away, left*",
                inline=False
            )
            embed.add_field(
                name="Example",
                value="`;m u 1 role member`",
                inline=False
            )
            await ctx.channel.send(embed=embed)

        elif args[0].lower() in ["update", "u"] and args[1].lower() == "inactives" and len(args) == 2:
            await self.management_guild_update_performance(ctx)

        elif args[0].lower() in ["update", "u"] and args[1].lower() == "feats" and len(args) == 2:
            await self.management_guild_update_feats(ctx)

        elif args[0].lower() in ["update", "u"] and len(args) == 2:
            embed = discord.Embed(
                colour=discord.Colour(embed_color),
                title="No field and value provided",
                description="Valid fields: `name`, `role`, `status`, `notes`"
            )
            await ctx.channel.send(embed=embed)

        elif args[0].lower() in ["update", "u"] and args[2].lower() not in fields and len(args) >= 3:
            embed = discord.Embed(
                colour=discord.Colour(embed_color),
                title="Invalid field update request",
                description="Valid fields: `name`, `role`, `status`, `notes`"
            )
            await ctx.channel.send(embed=embed)

        elif args[0].lower() in ["update", "u"] and args[2].lower() in fields and len(args) == 3:
            embed = discord.Embed(
                colour=discord.Colour(embed_color),
                title="Invalid field update request",
                description="No value provided for the field."
            )
            await ctx.channel.send(embed=embed)

        elif args[0].lower() in ["update", "u"] and len(args) >= 4 and args[2].lower() in fields:
            await management_update_field(ctx, args)

        elif args[0].lower() in ["show", "s"] and len(args) == 1:
            embed = discord.Embed(
                title="manage show, m s", colour=discord.Colour(embed_color),
                description="queries the guild database")

            embed.add_field(
                name="Formats",
                value="• *`;m s all <opt: [<startswith> or guild]>`*\n"
                      "• *`;m s all <role or status> <value>`*\n"
                      "• *`;m s <name or id_num>`*",
                inline=False
            )
            embed.add_field(
                name="Examples",
                value="• *`;m s all aki`*\n"
                      "• *`;m s all status inactive`*\n"
                      "• *`;m s all guild`*",
                inline=False
            )
            await ctx.channel.send(embed=embed)

        elif args[0].lower() in ["show", "s"] and len(args) == 2 and args[1].lower() == "role":
            embed = discord.Embed(
                colour=discord.Colour(embed_color),
                title="Provide a role value to show",
                description="Example: `;m show role <member, ex-member, etc..>`"
            )
            await ctx.channel.send(embed=embed)

        elif args[0].lower() in ["show", "s"] and len(args) == 2 and (args[1].lower() == "status"):
            embed = discord.Embed(
                colour=discord.Colour(embed_color),
                title="Provide a status value to show",
                description="Example: `;m show status <active, inactive, etc..>`"
            )
            await ctx.channel.send(embed=embed)

        elif args[0].lower() in ["show", "s"] and len(args) == 2 and args[1].lower() == "all":
            await self.management_guild_show_all(ctx)

        elif args[0].lower() in ["show", "s"] and len(args) == 3 \
                and args[1].lower() == "all" and args[2].lower() == "guild":
            await self.management_guild_show_current_members(ctx)

        elif args[0].lower() in ["show", "s"] and len(args) == 3 and args[1].lower() == "all":
            await self.management_guild_show_characters(ctx, args)

        elif args[0].lower() in ["show", "s"] and len(args) == 2 and args[1].lower() != "all" \
                and args[1].lower() not in fields:
            await management_show_profile(ctx, args)

        elif args[0].lower() in ["show", "s"] and len(args) == 3 and args[1].lower() == "status" \
                and args[2].lower() in status_values:
            await self.management_guild_show_field_status(ctx, args)

        elif args[0].lower() in ["show", "s"] and len(args) == 3 and \
                args[1].lower() == "role" and args[2].lower() in roles:
            await self.management_guild_show_field_role(ctx, args)

        elif args[0].lower() == "stats" and len(args) == 1:
            await management_show_stats(ctx)

        else:
            await ctx.message.add_reaction("❌")

    async def management_guild_update_performance(self, ctx):

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

        description = \
            "• `90` : `ACTV` | `>= 90 GQ`\n" \
            "• `60` : `SMAC` | `90 > GQ > 30`\n" \
            "• `30` : `INAC` | `<30 GQ`"

        embed1 = discord.Embed(
            color=ctx.author.colour,
            title="GQ Codes",
            description=description
        )
        embed2 = discord.Embed(
            color=ctx.author.colour,
            title="Performing initial calculations...",
            description="iterating first..."
        )
        await msg.edit(embed=embed1)
        await asyncio.sleep(4)
        msg = await ctx.channel.send("Enter the GQ code `(90/60/30)` for: ", embed=embed2)

        query = {"role": {"$in": ["Officer", "Member", "Leader"]}, "status": {"$in": ["Semi-active", "Inactive"]}}
        project = {
            "_id": 0, "name": 1, "role": 1, "#": 1, "status": 1, "total_feats": 1, "weekly_gq": 1, "status_update1": 1
        }

        def check(feat):
            try:
                x = int(feat.content)
                if x not in [90, 60, 30] and feat.author == ctx.message.author and feat.channel == ctx.channel:
                    raise KeyError
            except ValueError:
                if feat.content.lower() == "stop" \
                        and feat.author == ctx.message.author and feat.channel == ctx.channel:
                    raise TypeError
                elif feat.content.lower() == "skip" \
                        and feat.author == ctx.message.author and feat.channel == ctx.channel:
                    raise IndexError
                elif feat.content.lower() not in ["stop", "skip"] \
                        and feat.author == ctx.message.author and feat.channel == ctx.channel:
                    raise KeyError
            return feat.author == ctx.message.author and feat.channel == ctx.channel

        for member in members.find(query, project).sort([("total_feats", -1)]):
            embed = discord.Embed(
                color=ctx.author.colour,
                title=f"#{member['#']} : {member['name']} | 🎀 {member['role']}",
                timestamp=get_timestamp()
            )
            embed.set_thumbnail(url=ctx.guild.icon_url)
            embed.add_field(
                name="⛳ Status",
                value=f"{member['status']} [{member['status_update1']}]"
            )
            embed.add_field(
                name="🏆 Feats | GQ",
                value=f"{member['total_feats']} | {member['weekly_gq']} [Wk{get_time_est().isocalendar()[1]}]"
            )
            await asyncio.sleep(2)
            await msg.edit(embed=embed)

            i = 0
            while i < 1:
                try:
                    timeout = 180
                    answer = await self.client.wait_for("message", timeout=timeout, check=check)
                    value = int(answer.content)
                    members.update_one({"name": str(member["name"])}, {
                        "$set": dict(
                            status=get_status(value),
                            status_update1=get_time_est().strftime('%d.%b %y'),
                            status_update2=get_time_est().strftime('%Y:%m:%d'),
                            weekly_gq=value)
                    })
                    await answer.add_reaction("✅")
                    await asyncio.sleep(3)
                    await answer.delete()
                    break
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

            if i == "cancel":
                break
            else:
                continue

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

        def check(feat):
            try:
                int(feat.content)
            except ValueError:
                if feat.content.lower() == "stop" \
                        and feat.author == ctx.message.author and feat.channel == ctx.channel:
                    raise TypeError
                elif feat.content.lower() == "skip" \
                        and feat.author == ctx.message.author and feat.channel == ctx.channel:
                    raise IndexError
                elif feat.content.lower() not in ["stop", "skip"] \
                        and feat.author == ctx.message.author and feat.channel == ctx.channel:
                    raise KeyError
            return feat.author == ctx.message.author and feat.channel == ctx.channel

        query = {"role": {"$in": ["Officer", "Member", "Leader"]}}
        project = {
            "_id": 0, "name": 1, "role": 1, "#": 1, "status": 1, "total_feats": 1, "weekly_gq": 1, "status_update1": 1
        }

        for member in members.find(query, project).sort([("total_feats", 1)]):
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
                value=f"{member['total_feats']} | {member['weekly_gq']} [Wk{get_time_est().isocalendar()[1]}]"
            )
            await asyncio.sleep(1)
            await msg.edit(embed=embed)

            i = 0
            while i < 1:
                try:
                    timeout = 180
                    answer = await self.client.wait_for("message", timeout=timeout, check=check)
                    value = int(answer.content)
                    members.update_one({"name": str(member["name"])}, {"$set": {"total_feats": value}})
                    await answer.add_reaction("✅")
                    await asyncio.sleep(2)
                    await answer.delete()
                    break

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
            if i == "cancel":
                break
            else:
                continue

    async def management_guild_show_current_members(self, ctx):

        listings = []
        query = {"role": {"$in": ["Officer", "Member", "Leader"]}}
        project = {"_id": 0, "name": 1, "role": 1, "#": 1, "status": 1}

        for member in members.find(query, project).sort([("total_feats", -1)]):
            role = shorten(member['role'])
            status = shorten(member['status'])
            number = lengthen(member['#'])
            listings.append(f"`{number}: {role}` | `{status}` | {member['name']}\n")

        noun = pluralize("member", len(listings))
        content = f"There are {len(listings)} {noun} currently in the guild"
        await self.management_guild_paginate_embeds(ctx, listings, content)

    async def management_guild_show_characters(self, ctx, args):

        listings = []
        query = {"name_lower": {"$regex": f"^{args[2].lower()}"}}
        project = {"_id": 0, "name": 1, "role": 1, "#": 1, "status": 1}

        for member in members.find(query, project).sort([("name_lower", 1)]):
            role = shorten(member['role'])
            status = shorten(member['status'])
            number = lengthen(member['#'])
            listings.append(f"`{number}: {role}` | `{status}` | {member['name']}\n")

        noun = pluralize("result", len(listings))
        content = f"I've got {len(listings)} {noun} for names starting with {args[2].lower()}"
        await self.management_guild_paginate_embeds(ctx, listings, content)

    async def management_guild_show_all(self, ctx):

        listings = []
        query = {}
        project = {"_id": 0, "name": 1, "role": 1, "#": 1, "status": 1}

        for member in members.find(query, project).sort([("name_lower", 1)]):
            role = shorten(member['role'])
            status = shorten(member['status'])
            number = lengthen(member['#'])
            listings.append(f"`{number}: {role}` | `{status}` | {member['name']}\n")

        noun = pluralize("account", len(listings))
        content = f"There are {len(listings)} registered {noun}"
        await self.management_guild_paginate_embeds(ctx, listings, content)

    async def management_guild_show_field_role(self, ctx, args):

        listings = []
        query = {"role": args[2].capitalize()}
        project = {"_id": 0, "name": 1, "status_update1": 1, "status_update2": 1, "#": 1, "role": 1}

        for member in members.find(query, project).sort([("status_update2", 1)]):
            number = lengthen(member['#'])
            listings.append(f"`{number}: {member['status_update1']}` | {member['name']}\n")

        noun = pluralize("result", len(listings))
        content = f"I've got {len(listings)} {noun} for members with role {args[2].lower()}"
        await self.management_guild_paginate_embeds(ctx, listings, content)

    async def management_guild_show_field_status(self, ctx, args):

        listings = []
        query = {"status": args[2].capitalize()}
        project = {"_id": 0, "name": 1, "status_update1": 1, "status_update2": 1, "#": 1}

        for member in members.find(query, project).sort([("status_update2", 1)]):
            number = lengthen(member['#'])
            listings.append(f"`{number}: {member['status_update1']}` | {member['name']}\n")

        noun = pluralize("result", len(listings))
        content = f"I've got {len(listings)} {noun} for members with status {args[2].lower()}"

        await self.management_guild_paginate_embeds(ctx, listings, content)

    async def management_guild_paginate_embeds(self, ctx, listings, content):

        description = "".join(listings[0:20])
        page_total = int(len(listings) / 20)
        embed = discord.Embed(
            color=ctx.author.colour, title=f"🔱 Guild Registry", description=description, timestamp=get_timestamp()
        )
        embed.set_footer(text=f"Page: 1 of page {page_total}")
        embed.set_thumbnail(url=ctx.guild.icon_url)

        msg = await ctx.channel.send(content=content, embed=embed)
        await msg.add_reaction("⬅")
        await msg.add_reaction("➡")

        def check(r, u):
            return u != self.client.user and r.message.id == msg.id

        def create_new_embed_page(page_new, listings_new):
            end = page_new * 20
            start = end - 20
            description_new = "".join(listings_new[start:end])

            embed_new = discord.Embed(
                color=ctx.author.colour,
                title="🔱 Guild Registry",
                description=f"{description_new}",
                timestamp=get_timestamp()
            )
            embed_new.set_footer(text=f"Page: {page_new} of {page_total}")
            embed_new.set_thumbnail(url=ctx.guild.icon_url)
            return embed_new

        page = 1
        while True:
            try:
                timeout = 180
                reaction, user = await self.client.wait_for("reaction_add", timeout=timeout, check=check)

                if str(reaction.emoji) == "➡":
                    page += 1
                elif str(reaction.emoji) == "⬅":
                    page -= 1

                if page == 0:
                    page = page_total
                elif page > page_total:
                    page = 1

                await msg.edit(embed=create_new_embed_page(page, listings))

            except asyncio.TimeoutError:
                break


def setup(client):
    client.add_cog(Admin(client))
