"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""

import asyncio
import os
import re
from datetime import datetime

import discord
import pytz
from discord.ext import commands

from cogs.mongo.db import boss, members, users, friendship, books
from cogs.startup import pluralize, emoji_j

file = os.path.basename(__file__)[:-3:]
fields = ["name", "role", "status", "notes", "note", "tfeat", "gq"]
roles = ["member", "ex-member", "officer", "leader"]
status_values = ["active", "inactive", "on-leave", "kicked", "semi-active", "away", "left"]

spell_spams_id = []
for document in books.find({}, {"_id": 0, "channels.spell-spam": 1}):
    try:
        spell_spams_id.append(document["channels"]["spell-spam"])
    except KeyError:
        continue


def get_time_est():
    tz_target = pytz.timezone("America/Atikokan")
    return datetime.now(tz=tz_target)


def get_status(v):
    status = {
        "30": "Inactive",
        "60": "Semi-active",
        "90": "Active"
    }
    return status[str(v)]


def shorten(key):
    keyword = {
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
        "Kicked": "KCKD"
    }
    return keyword[key]


def lengthen(index):
    if index < 10:
        prefix = "#00{}"
    elif index < 100:
        prefix = "#0{}"
    else:
        prefix = "#{}"
    return prefix.format(index)


def create_embed(ctx, page, query_list, time, color):
    end = page * 20
    start = end - 20
    description = "".join(query_list[start:end])

    embed = discord.Embed(
        color=color,
        title="🔱 Guild Registry",
        description=f"{description}"
    )
    embed.set_footer(text=f"Page: {page} | Queried on {time}")
    embed.set_thumbnail(url=ctx.guild.icon_url)
    return embed


def check_if_guild_is_patronus(ctx):
    return ctx.guild.id == 412057028887052288


async def management_show_stats(ctx):
    registered_users = members.count()

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
            f"• Total Accounts    :: {registered_users}\n" \
            f"• Guild Occupancy   :: {guild_members_all}/160\n" \
            f"  • Active          :: {guild_members_actv}\n" \
            f"  • Semi-active     :: {guild_members_smac}\n" \
            f"  • Inactive        :: {guild_members_inac}\n" \
            f"  • On-leave        :: {guild_members_onlv}\n" \
            f"  • Away            :: {ex_members_away}\n" \
            f"  • ~ GQ/week       :: {guild_members_actv * 90 + guild_members_smac * 30:,d}" \
            f"```"

    embed = discord.Embed(
        color=ctx.author.colour,
        title="🔱 Guild Statistics",
        description=f"{description}"
    )
    embed.set_thumbnail(url=ctx.guild.icon_url)
    embed.set_footer(text=f"Queried on {get_time_est().strftime('%b %d, %Y %H:%M EST')}")
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
            title=f"#{member['#']} : {member['name']} | 🎀 {member['role']}"
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

        embed.set_footer(text=f"Queried on {get_time_est().strftime('%b %d, %Y %H:%M EST')}")
        embed.set_thumbnail(url=ctx.guild.icon_url)
        await ctx.channel.send(embed=embed)

    except TypeError:
        embed = discord.Embed(
            colour=discord.Colour(0xffe6a7),
            title="That member is not in the guild database"
        )
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
        embed = discord.Embed(
            colour=discord.Colour(0xffe6a7),
            title="Provided ID/name is not in the guild database"
        )
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
            colour=discord.Colour(0xffe6a7),
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

    @commands.command()
    @commands.is_owner()
    async def reset(self, ctx, *, args):

        if args == "daily":
            await self.reset_daily()

        elif args == "weekly":
            await self.reset_weekly()

        elif args == "boss":
            await self.reset_boss()

        elif args not in ["daily", "weekly", "boss"]:
            embed = discord.Embed(
                colour=discord.Colour(0xffe6a7),
                title="Invalid argument",
                description="Provide a valid argument: `daily`, `weekly`, or `boss`"
            )
            await ctx.channel.send(embed=embed)

    async def reset_daily(self):

        users.update_many({}, {"$set": {"daily": False, "raided_count": 0}})

        valid_ships = []
        for ship in friendship.find({"level": {"$gt": 1}}, {"ship_name": 1, "shipper1": 1, "shipper2": 1, "level": 1}):
            rewards = ship["level"] * 25
            valid_ships.append(f"• {ship['ship_name']}, {rewards}{emoji_j}\n")
            users.update_one({"user_id": ship["shipper1"]}, {"$inc": {"jades": rewards}})
            users.update_one({"user_id": ship["shipper2"]}, {"$inc": {"jades": rewards}})

        description = "".join(valid_ships[0:10])
        title = "🚢 Daily Ship Sail Rewards"
        color = 0xffff80
        embed = discord.Embed(color=color, title=title, description=description)
        embed.set_footer(text="Page 1")

        for channel in spell_spams_id:
            current_channel = self.client.get_channel(int(channel))
            msg = await current_channel.send("🎊 Daily rewards have been reset.", embed=embed)
            await msg.add_reaction("⬅")
            await msg.add_reaction("➡")

            def create_embed_ships(new_page):
                end = new_page * 10
                start = end - 10
                description_new = "".join(valid_ships[start:end])
                embed_new = discord.Embed(color=color, title=title, description=description_new)
                embed_new.set_footer(text=f"Page: {new_page}")
                return embed_new

            def check(r, u):
                return u != self.client.user and r.message.id == msg.id

            page = 1
            while True:
                try:
                    timeout = 30
                    reaction, user = await self.client.wait_for("reaction_add", timeout=timeout, check=check)
                    if str(reaction.emoji) == "➡":
                        page += 1
                    elif str(reaction.emoji) == "⬅":
                        page -= 1
                    if page == 0:
                        page = 1
                    await msg.edit(embed=create_embed_ships(page))
                except asyncio.TimeoutError:
                    return False

    async def reset_weekly(self):

        users.update_many({}, {"$set": {"weekly": False}})

        embed = discord.Embed(
            title="💝 Weekly rewards have been reset", colour=discord.Colour(0xffe6a7),
            description=" Claim yours using `;weekly`"
        )
        for channel in spell_spams_id:
            current_channel = self.client.get_channel(int(channel))
            try:
                await current_channel.send(embed=embed)
            except AttributeError:
                continue
            except discord.errors.Forbidden:
                return
            except discord.errors.HTTPException:
                return

    async def reset_boss(self):

        boss.update_many({}, {
            "$set": {
                "discoverer": 0,
                "level": 0,
                "damage_cap": 0,
                "total_hp": 0,
                "current_hp": 0,
                "challengers": [],
                "rewards": {}
            }
        })
        embed = discord.Embed(
            colour=discord.Colour(0xffe6a7),
            title="Assembly Boss encounter has been reset."
        )
        for channel in spell_spams_id:
            current_channel = self.client.get_channel(int(channel))
            try:
                await current_channel.send(embed=embed)
            except AttributeError:
                continue
            except discord.errors.Forbidden:
                return
            except discord.errors.HTTPException:
                return

    @commands.command(aliases=["announce"])
    @commands.has_role("Head")
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

    @commands.command(aliases=["c", "clear", "purge", "cl", "prune"])
    @commands.has_role("Head")
    async def purge_messages(self, ctx, amount=2):
        try:
            await ctx.channel.purge(limit=amount + 1)
        except discord.errors.Forbidden:
            pass
        except discord.errors.HTTPException:
            pass

    @commands.command(aliases=["say"])
    @commands.has_role("Head")
    async def announcement_post_message(self, ctx, arg1, *, args):

        try:
            channel_id = re.sub("[<>#]", "", arg1)
            channel_target = self.client.get_channel(int(channel_id))
            await channel_target.send(args)
            await ctx.message.add_reaction("✅")
        except AttributeError:
            embed = discord.Embed(
                colour=discord.Colour(0xffe6a7),
                description="The specified channel ID was not found."
            )
            await ctx.channel.send(embed=embed)
        except discord.errors.Forbidden:
            return
        except discord.errors.HTTPException:
            return

    @commands.command(aliases=["m", "manage"])
    @commands.has_role("Head")
    @commands.check(check_if_guild_is_patronus)
    async def management_guild(self, ctx, *args):

        if len(args) == 0 or args[0].lower() in ["help", "h"]:
            embed = discord.Embed(
                title="manage, m", colour=discord.Colour(0xffe6a7),
                description="shows the help prompt for the first 3 arguments"
            )
            embed.add_field(name="Arguments", value="*add, update, show, stats*", inline=False)
            embed.add_field(name="Example", value="*`;manage add`*", inline=False)
            await ctx.channel.send(embed=embed)

        elif args[0].lower() == "add" and len(args) <= 2:
            embed = discord.Embed(
                title="manage add, m add", colour=discord.Colour(0xffe6a7),
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
                title="manage update, m u", colour=discord.Colour(0xffe6a7),
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
            await self.management_update_performance(ctx)

        elif args[0].lower() in ["update", "u"] and args[1].lower() == "feats" and len(args) == 2:
            await self.management_update_feats(ctx)

        elif args[0].lower() in ["update", "u"] and len(args) == 2:
            embed = discord.Embed(
                colour=discord.Colour(0xffe6a7),
                title="No field and value provided",
                description="Valid fields: `name`, `role`, `status`, `notes`"
            )
            await ctx.channel.send(embed=embed)

        elif args[0].lower() in ["update", "u"] and args[2].lower() not in fields and len(
                args) >= 3:
            embed = discord.Embed(
                colour=discord.Colour(0xffe6a7),
                title="Invalid field update request",
                description="Valid fields: `name`, `role`, `status`, `notes`"
            )
            await ctx.channel.send(embed=embed)

        elif args[0].lower() in ["update", "u"] and args[2].lower() in fields and len(args) == 3:
            embed = discord.Embed(
                colour=discord.Colour(0xffe6a7),
                title="Invalid field update request",
                description="No value provided for the field."
            )
            await ctx.channel.send(embed=embed)

        elif args[0].lower() in ["update", "u"] and len(args) >= 4 and args[2].lower() in fields:
            await management_update_field(ctx, args)

        elif args[0].lower() in ["show", "s"] and len(args) == 1:
            embed = discord.Embed(
                title="manage show, m s", colour=discord.Colour(0xffe6a7),
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
                colour=discord.Colour(0xffe6a7),
                title="Provide a role value to show",
                description="Example: `;m show role <member, ex-member, etc..>`"
            )
            await ctx.channel.send(embed=embed)

        elif args[0].lower() in ["show", "s"] and len(args) == 2 and (args[1].lower() == "status"):
            embed = discord.Embed(
                colour=discord.Colour(0xffe6a7),
                title="Provide a status value to show",
                description="Example: `;m show status <active, inactive, etc..>`"
            )
            await ctx.channel.send(embed=embed)

        elif args[0].lower() in ["show", "s"] and len(args) == 2 and args[1].lower() == "all":
            await self.management_show_guild_specific(ctx)

        elif args[0].lower() in ["show", "s"] and len(args) == 3 \
                and args[1].lower() == "all" and args[2].lower() == "guild":
            await self.management_show_guild_current(ctx)

        elif args[0].lower() in ["show", "s"] and len(args) == 3 and args[1].lower() == "all":
            await self.management_show_guild_first(ctx, args)

        elif args[0].lower() in ["show", "s"] and len(args) == 2 and args[1].lower() != "all" \
                and args[1].lower() not in fields:
            await management_show_profile(ctx, args)

        elif args[0].lower() in ["show", "s"] and len(args) == 3 and args[1].lower() == "status" \
                and args[2].lower() in status_values:
            await self.management_show_field_status(ctx, args)

        elif args[0].lower() in ["show", "s"] and len(args) == 3 and \
                args[1].lower() == "role" and args[2].lower() in roles:
            await self.management_show_field_role(ctx, args)

        elif args[0].lower() == "stats" and len(args) == 1:
            await management_show_stats(ctx)

        else:
            await ctx.message.add_reaction("❌")

    async def management_update_performance(self, ctx):

        embed = discord.Embed(
            colour=discord.Colour(0xffe6a7),
            title="Opening environment for batch updating of inactives.."
        )
        msg = await ctx.channel.send(embed=embed)
        await asyncio.sleep(3)
        embed = discord.Embed(
            colour=discord.Colour(0xffe6a7),
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

        query = members.find({
            "role": {
                "$in": ["Officer", "Member", "Leader"]},
            "status": {
                "$in": ["Semi-active", "Inactive"]}}, {
            "_id": 0, "name": 1, "role": 1, "#": 1, "status": 1, "total_feats": 1, "weekly_gq": 1, "status_update1": 1
        })

        async def check(feat):
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

        for member in query.sort([("total_feats", -1)]):
            embed = discord.Embed(
                color=ctx.author.colour,
                title=f"#{member['#']} : {member['name']} | 🎀 {member['role']}"
            )
            embed.set_thumbnail(url=ctx.guild.icon_url)
            embed.set_footer(text=f"Queried on {get_time_est().strftime('%b %d, %Y %H:%M EST')}")
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
                    embed = discord.Embed(colour=discord.Colour(0xffe6a7), title="Exiting environment..")
                    msg = await ctx.channel.send(embed=embed)
                    await msg.add_reaction("✅")
                    i = "cancel"
                    break
                except KeyError:
                    embed = discord.Embed(colour=discord.Colour(0xffe6a7), title="Invalid input")
                    msg = await ctx.channel.send(embed=embed)
                    await asyncio.sleep(2)
                    await msg.delete()
                    i = 0
                except asyncio.TimeoutError:
                    embed = discord.Embed(colour=discord.Colour(0xffe6a7), title="Timeout! Exiting...")
                    msg = await ctx.channel.send(embed=embed)
                    await asyncio.sleep(1)
                    await msg.add_reaction("✅")
                    i = "cancel"
                    break

            if i == "cancel":
                break
            else:
                continue

    async def management_update_feats(self, ctx):

        embed = discord.Embed(
            colour=discord.Colour(0xffe6a7),
            title="Opening environment for batch updating of inactives.."
        )
        msg = await ctx.channel.send(embed=embed)
        await asyncio.sleep(3)
        embed = discord.Embed(
            colour=discord.Colour(0xffe6a7),
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

        query = members.find({
            "role": {
                "$in": ["Officer", "Member", "Leader"]}}, {
            "_id": 0, "name": 1, "role": 1, "#": 1, "status": 1, "total_feats": 1, "weekly_gq": 1, "status_update1": 1
        })

        for member in query.sort([("total_feats", 1)]):
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
                    embed = discord.Embed(colour=discord.Colour(0xffe6a7), title="Exiting environment..")
                    msg = await ctx.channel.send(embed=embed)
                    await msg.add_reaction("✅")
                    i = "cancel"
                    break
                except KeyError:
                    embed = discord.Embed(colour=discord.Colour(0xffe6a7), title="Invalid input")
                    msg = await ctx.channel.send(embed=embed)
                    await asyncio.sleep(2)
                    await msg.delete()
                    i = 0
                except asyncio.TimeoutError:
                    embed = discord.Embed(colour=discord.Colour(0xffe6a7), title="Timeout! Exiting...")
                    msg = await ctx.channel.send(embed=embed)
                    await asyncio.sleep(1)
                    await msg.add_reaction("✅")
                    i = "cancel"
                    break
            if i == "cancel":
                break
            else:
                continue

    async def management_show_guild_current(self, ctx):

        query_list = []
        query = members.find({
            "role": {"$in": ["Officer", "Member", "Leader"]}}, {
            "_id": 0, "name": 1, "role": 1, "#": 1, "status": 1
        })

        for member in query.sort([("total_feats", -1)]):
            role = member['role']
            status = member['status']
            number = member['#']
            query_list.append(f"`{lengthen(number)}: {shorten(role)}` | `{shorten(status)}` | {member['name']}\n")

        description = "".join(query_list[0:20])
        embed = discord.Embed(
            color=ctx.author.colour,
            title="🔱 Guild Registry",
            description=f"{description}"
        )
        embed.set_footer(text=f"Page: 1 | Queried on {get_time_est().strftime('%b %d, %Y %H:%M EST')}")
        embed.set_thumbnail(url=ctx.guild.icon_url)
        noun = pluralize("member", len(query_list))
        content = f"There are {len(query_list)} {noun} currently in the guild"

        msg = await ctx.channel.send(content=content, embed=embed)
        await self.management_paginate_embeds(ctx, msg, query_list, get_time_est().strftime('%b %d, %Y %H:%M EST'))

    async def management_show_guild_first(self, ctx, args):

        query_list = []
        query = members.find({
            "name_lower": {"$regex": f"^{args[2].lower()}"}}, {
            "_id": 0, "name": 1, "role": 1, "#": 1, "status": 1
        })

        for member in query.sort([("name_lower", 1)]):
            role = member['role']
            status = member['status']
            number = member['#']
            query_list.append(f"`{lengthen(number)}: {shorten(role)}` | `{shorten(status)}` | {member['name']}\n")

        description = "".join(query_list[0:20])

        embed = discord.Embed(
            color=ctx.author.colour,
            title="🔱 Guild Registry",
            description=f"{description}"
        )
        embed.set_footer(text=f"Page: 1 | Queried on {get_time_est().strftime('%b %d, %Y %H:%M EST')}")
        embed.set_thumbnail(url=ctx.guild.icon_url)

        noun = pluralize("result", len(query_list))
        content = f"I've got {len(query_list)} {noun} for names starting with {args[2].lower()}"

        msg = await ctx.channel.send(content=content, embed=embed)
        await self.management_paginate_embeds(ctx, msg, query_list, get_time_est().strftime('%b %d, %Y %H:%M EST'))

    async def management_show_guild_specific(self, ctx):

        query_list = []
        query = members.find({}, {"_id": 0, "name": 1, "role": 1, "#": 1, "status": 1})

        for member in query.sort([("name_lower", 1)]):
            role = member['role']
            status = member['status']
            number = member['#']
            query_list.append(f"`{lengthen(number)}: {shorten(role)}` | `{shorten(status)}` | {member['name']}\n")

        description = "".join(query_list[0:20])
        embed = discord.Embed(
            color=ctx.author.colour,
            title="🔱 Guild Registry",
            description=f"{description}"
        )
        embed.set_footer(text=f"Page: 1 | Queried on {get_time_est().strftime('%b %d, %Y %H:%M EST')}")
        embed.set_thumbnail(url=ctx.guild.icon_url)
        noun = pluralize("account", len(query_list))
        content = f"There are {len(query_list)} registered {noun}"

        msg = await ctx.channel.send(content=content, embed=embed)
        await self.management_paginate_embeds(ctx, msg, query_list, get_time_est().strftime('%b %d, %Y %H:%M EST'))

    async def management_show_field_role(self, ctx, args):

        query_list = []
        query = members.find({
            "role": args[2].capitalize()}, {
            "_id": 0, "name": 1, "status_update1": 1, "status_update2": 1, "#": 1, "role": 1
        })

        for member in query.sort([("status_update2", 1)]):
            number = member['#']
            query_list.append(f"`{lengthen(number)}: {member['status_update1']}` | {member['name']}\n")

        description = "".join(query_list[0:20])
        embed = discord.Embed(
            color=ctx.author.colour,
            title="🔱 Guild Registry",
            description=description
        )
        embed.set_footer(text=f"Page: 1 | Queried on {get_time_est().strftime('%b %d, %Y %H:%M EST')}")
        embed.set_thumbnail(url=ctx.guild.icon_url)
        noun = pluralize("result", len(query_list))
        content = f"I've got {len(query_list)} {noun} for members with role {args[2].lower()}"

        msg = await ctx.channel.send(content=content, embed=embed)
        await self.management_paginate_embeds(ctx, msg, query_list, get_time_est().strftime('%b %d, %Y %H:%M EST'))

    async def management_show_field_status(self, ctx, args):

        query_list = []
        query = members.find({
            "status": args[2].capitalize()}, {
            "_id": 0, "name": 1, "status_update1": 1, "status_update2": 1, "#": 1
        })

        for member in query.sort([("status_update2", 1)]):
            number = member['#']
            query_list.append(f"`{lengthen(number)}: {member['status_update1']}` | {member['name']}\n")

        description = "".join(query_list[0:20])

        embed = discord.Embed(
            color=ctx.author.colour,
            title=f"🔱 Guild Registry",
            description=description
        )
        embed.set_footer(text=f"Page: 1 | Queried on {get_time_est().strftime('%b %d, %Y %H:%M EST')}")
        embed.set_thumbnail(url=ctx.guild.icon_url)
        noun = pluralize("result", len(query_list))
        content = f"I've got {len(query_list)} {noun} for members with status {args[2].lower()}"

        msg = await ctx.channel.send(content=content, embed=embed)
        await self.management_paginate_embeds(ctx, msg, query_list, get_time_est().strftime('%b %d, %Y %H:%M EST'))

    async def management_paginate_embeds(self, ctx, msg, query_list, time):

        await msg.add_reaction("⬅")
        await msg.add_reaction("➡")

        def check_pagination(r, u):
            return u != self.client.user and r.message.id == msg.id

        page = 1
        while True:
            try:
                timeout = 180
                reaction, user = await self.client.wait_for("reaction_add", timeout=timeout, check=check_pagination)
                if str(reaction.emoji) == "➡":
                    page += 1
                elif str(reaction.emoji) == "⬅":
                    page -= 1
                if page == 0:
                    page = 1
                await msg.edit(embed=create_embed(ctx, page, query_list, time, ctx.author.colour))
            except asyncio.TimeoutError:
                return False


def setup(client):
    client.add_cog(Admin(client))
