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

from cogs.error import logging, get_f
from cogs.mongo.db import daily, boss, members, users, friendship, books
from cogs.startup import pluralize

file = os.path.basename(__file__)[:-3:]
fields = ["name", "role", "status", "notes", "note", "tfeat", "gq"]
roles = ["member", "ex-member", "officer", "leader"]
status_values = ["active", "inactive", "on-leave", "kicked", "semi-active", "away", "left"]
emoji_j = "<:jade:555630314282811412>"


channels_announcement = []
for document in books.find({}, {"_id": 0, "channels.spell-spam": 1}):
    try:
        channels_announcement.append(document["channels"]["spell-spam"])
    except KeyError:
        continue


def get_time():
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


async def management_stats(ctx):

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
    content = f"Estimated guild quests per week: {guild_members_actv * 90 + guild_members_smac * 30:,d}"
    description = \
        f"Registered Accounts: `{registered_users}`\n" \
            f"Guild Occupancy: `{guild_members_all}/160`\n" \
            f"▫ Active: `{guild_members_actv}`\n" \
            f"▫ Semi-active: `{guild_members_smac}`\n" \
            f"▫ Inactive: `{guild_members_inac}`\n" \
            f"▫ On-leave: `{guild_members_onlv}`\n" \
            f"🔹 Away: `{ex_members_away}`"

    embed = discord.Embed(
        color=ctx.author.colour,
        title="🔱 Guild Statistics",
        description=f"{description}"
    )
    embed.set_footer(text=f"Queried on {get_time().strftime('%b %d, %Y %H:%M EST')}")
    embed.set_thumbnail(url=ctx.guild.icon_url)
    await ctx.channel.send(content=content, embed=embed)


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

        embed.set_footer(text=f"Queried on {get_time().strftime('%b %d, %Y %H:%M EST')}")
        embed.set_thumbnail(url=ctx.guild.icon_url)
        await ctx.channel.send(embed=embed)

    except TypeError:
        await ctx.channel.send("That member is not in the guild database")


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
        await ctx.channel.send("Provided ID/name is not in the guild database")

    elif args[2].lower() == "status" and args[3].lower() in status_values:
        members.update_one(find_query, {
            "$set": {
                "status": args[3].capitalize(),
                "status_update1": get_time().strftime('%d.%b %y'),
                "status_update2": get_time().strftime('%Y:%m:%d')
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
                    "time": get_time().strftime('%d.%b %y'),
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
        await ctx.channel.send("Changing the a member role may require to change the status as well")

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
                        status_update1=get_time().strftime('%d.%b %y'),
                        status_update2=get_time().strftime('%Y:%m:%d'),
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

    @commands.command(aliases=["welcome"])
    @commands.is_owner()
    async def post_welcome(self, ctx):

        request = books.find_one({
            "server": f"{ctx.guild.id}"}, {
            "_id": 0,
            "channels": 1,
            "roles.patronus": 1
        })
        welcome_id = request["channels"]["welcome"]
        sorting_id = request["channels"]["sorting-hat"]
        patronus_role_id = request["roles"]["patronus"]
        welcome = self.client.get_channel(int(welcome_id))

        embed1 = discord.Embed(
            colour=discord.Colour(0xe77eff),
            title="Welcome to House Patronus!",
            description="Herewith are the rules and information of our server!\n\n"
                        "Crest designed by <@!281223518103011340>"
        )
        embed1.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/556032841897607178/584001678316142607/Patronus_Crest.png"
        )

        embed2 = discord.Embed(
            colour=discord.Colour(0xff44),
            title="Primary Server Roles",
            description=f"Sub roles are provided at the <#{sorting_id}>"
        )
        embed2.add_field(
            name="🔱 Head",
            value="• The Ministers of Patronus",
            inline=False
        )
        embed2.add_field(
            name="⚜ Auror",
            value="• The Prime Witches, Wizards, & Spirits",
            inline=False
        )
        embed2.add_field(
            name="🔮 Patronus",
            value="• Existing members of the guild",
            inline=False
        )
        embed2.add_field(
            name="🔥 No-Maj",
            value="• Obliviated, former members; guests",
            inline=False
        )
        embed2.add_field(
            name="🐼 Animagus",
            value="• Transformed members during Night; Bots",
            inline=False
        )

        embed3 = discord.Embed(
            title="📋 Rules",
            colour=discord.Colour(0xf8e71c),
            description="• Useless warnings may be issued!\n​ "
        )
        embed3.add_field(
            name="# 1. Server nickname",
            value="• It must contain your actual in-game name\n​ "
        )
        embed3.add_field(
            name="# 2. Message content",
            value="• No any form of harassment, racism, toxicity, etc.\n"
                  "• Avoid posting NSFW or NSFL\n​ ",
            inline=False
        )
        embed3.add_field(
            name="# 3. Role/member mention",
            value="• Avoid unnecessary pinging\n"
                  "• Check for the specific roles for free pinging\n​ ",
            inline=False
        )
        embed3.add_field(
            name="# 4. Spamming",
            value="• Posting at the wrong channel is spamming\n"
                  "• Channels are provided for spamming bot commands\n​ ",
            inline=False
        )
        embed3.add_field(
            name="# 5. No unsolicited promotions",
            value="• Like advertising of other guilds/servers without permission\n​ ",
            inline=False
        )
        embed3.add_field(
            name="# 6. Extensions",
            value="• Above rules apply on members' direct messages\n"
                  "• Follow [Discord Community Guidelines](https://discordapp.com/guidelines)\n​ ",
            inline=False
        )

        embed4 = discord.Embed(
            colour=discord.Colour(0xb8e986),
            title="🎀 Benefits & Requirements",
            description=f"• <@&{patronus_role_id}> must be fully guided for #2&5\n​ ",
            inline=False
        )
        embed4.add_field(
            name="# 1. No duel/tier requirements",
            value="• But do test your limits and improve!\n​ ",
            inline=False
        )
        embed4.add_field(
            name="# 2. Guild Quest (GQ) requirements",
            value="• For apprentices, min 30 weekly GQ\n"
                  "• For qualified mentors, min 90 weekly GQ\n"
                  "• 2-weeks consistent inactivity will be forewarned\n​ ",
            inline=False
        )
        embed4.add_field(
            name="# 3. Alternate Accounts",
            value="• We can accommodate if slots are available\n"
                  "• Notify a Head before applying\n​ ",
            inline=False
        )
        embed4.add_field(
            name="# 4. Guild Bonuses",
            value="• Top 15 guild in overall activeness ranking\n"
                  "• Rated at 60-70 guild packs per week\n"
                  "• Weekly 1-hour soul & evo bonus\n"
                  "• 24/7 exp, coin, & medal buffs\n"
                  "• Max guild feast rewards\n"
                  "• Ultimate Orochi carries\n"
                  "• Souls 10 carries\n"
                  "• Rich Discord content\n"
                  "• Fun, playful, & experienced members\n​ ",
            inline=False
        )
        embed4.add_field(
            name="# 5. Absenteeism/leave",
            value="• If leaving for shards, specify amount of days\n"
                  "• File your applications prior long vacations\n"
                  "• Up to 20-30 days of leave for old members\n​ ",
            inline=False
        )

        embed5 = discord.Embed(
            colour=discord.Colour(0x50e3c2),
            title="🎊 Events & Timings",
            description=f"• <@&{patronus_role_id}> role is pinged for events #2-5\n​ "
        )
        embed5.add_field(
            name="# 1. Guild Raid",
            value="• `05:00 EST` | Resets Everyday \n​"
        )
        embed5.add_field(
            name="# 2. Kirin Hunt",
            value="• `19:00 EST` | Every Mon to Thu\n​",
            inline=False
        )
        embed5.add_field(
            name="# 3. Guild Feast",
            value="• `10:00 EST` | Every Sat \n"
                  "• `00:00 EST` | Every Sun\n​",
            inline=False
        )
        embed5.add_field(
            name="# 4. Boss Defense",
            value="• `10:15 EST` | Every Sat \n​",
            inline=False
        )
        embed5.add_field(
            name="# 5. Exclusive Guild Contests",
            value="• Announced once in a while in Discord\n​ ",
            inline=False
        )

        embed6 = discord.Embed(
            colour=discord.Colour(0xffd6ab),
            title="🎏 Banner"
        )
        embed6.set_image(
            url="https://media.discordapp.net/attachments/556032841897607178/600170789722914847/patronus.png"
        )
        embed6.set_footer(
            text="Assets: Official Onmyoji art; Designed by: xann#8194"
        )

        msg1 = await welcome.send(embed=embed1)
        msg2 = await welcome.send(embed=embed2)
        msg3 = await welcome.send(embed=embed3)
        msg4 = await welcome.send(embed=embed4)
        msg5 = await welcome.send(embed=embed5)
        msg6 = await welcome.send(embed=embed6)
        msg7 = await welcome.send(content="Our invite link: https://discord.gg/H6N8AHB")
        await ctx.message.delete()

        list_welcome = {
            "introduction": str(msg1.id),
            "roles_information": str(msg2.id),
            "rules": str(msg3.id),
            "requirements": str(msg4.id),
            "events_schedule": str(msg5.id),
            "banner": str(msg6.id),
            "invite_link": str(msg7.id)
        }

        books.update_one(
            {"server": f"{ctx.guild.id}"},
            {"$set": {
                "messages": list_welcome
            }}
        )

    @commands.command(aliases=["beasts"])
    @commands.is_owner()
    async def edit_beasts_selection(self, ctx):

        guild_roles = ctx.guild.roles
        request = books.find_one({
            "server": f"{ctx.guild.id}"}, {
            "_id": 0,
            "channels.sorting-hat": 1,
            "messages.beasts_selection": 1
        })
        sorting_id = request["channels"]["sorting-hat"]
        beasts_selection_id = request["messages"]["beasts_selection"]
        sorting_channel = self.client.get_channel(int(sorting_id))

        thunderbirds = discord.utils.get(guild_roles, name="Thunderbirds")
        maledictus = discord.utils.get(guild_roles, name="Maledictus")
        graphorns = discord.utils.get(guild_roles, name="Graphorns")
        phoenixes = discord.utils.get(guild_roles, name="Phoenixes")
        obscurus = discord.utils.get(guild_roles, name="Obscurus")
        zouwus = discord.utils.get(guild_roles, name="Zouwus")
        kelpies = discord.utils.get(guild_roles, name="Kelpies")
        mooncalves = discord.utils.get(guild_roles, name="Mooncalves")
        bowtruckles = discord.utils.get(guild_roles, name="Bowtruckles")
        streelers = discord.utils.get(guild_roles, name="Streelers")

        embed = discord.Embed(
            title="Role Color Selection",
            colour=discord.Colour(0x3b70ff),
            description="• Freely select your preferred Animagus form. Transformation time: 19:00-06:00"
        )
        embed.add_field(
            name=":eagle: Thunderbirds",
            value=f"{thunderbirds.mention} are able to create storms as they fly"
        )
        embed.add_field(
            name=":snake: Maledictus",
            value=f"{maledictus.mention} can transform into anything but they are cursed"
        )
        embed.add_field(
            name=":rhino: Graphorns",
            value=f"{graphorns.mention} are large beasts with extremely aggressive nature"
        )
        embed.add_field(
            name=":bird: Phoenixes",
            value=f"{phoenixes.mention} are immensely old creatures and can regenerate through bursting in flames"
        )
        embed.add_field(
            name=":eye_in_speech_bubble: Obscurus",
            value=f"{obscurus.mention} are very dark parasitical magical entities, beware"
        )
        embed.add_field(
            name=":lion: Zouwus",
            value=f"{zouwus.mention}, gigantic elephant-sized cats easily tamed by furry-balls"
        )
        embed.add_field(
            name=":dragon_face: Kelpies",
            value=f"{kelpies.mention} are shape-shifting, demonic, and water-dwelling creatures"
        )
        embed.add_field(
            name=":cow: Mooncalves",
            value=f"{mooncalves.mention}, shy magical bulging blue eyed creatures who only comes out during the night"
        )
        embed.add_field(
            name=":seedling: Bowtruckles",
            value=f"{bowtruckles.mention}, they are very smart, bipedal twig-like creatures"
        )
        embed.add_field(
            name=":snail: Streelers",
            value=f"{streelers.mention}, dangerous and huge poisonous color-changing snails"
        )

        beast_selection_msg = await sorting_channel.fetch_message(int(beasts_selection_id))
        await beast_selection_msg.edit(embed=embed)
        await ctx.message.delete()

    @commands.command(aliases=["start"])
    @commands.is_owner()
    async def post_announcement_magic(self, ctx):

        request = books.find_one({
            "server": f"{ctx.guild.id}"}, {
            "_id": 0, "sorting": 1, "patronus_role": 1, "headlines": 1, "gift-game": 1
        })

        headlines = self.client.get_channel(int(request["headlines"]))
        gift_game = self.client.get_channel(int(request["gift-game"]))
        sorting = self.client.get_channel(int(request["sorting"]))
        patronus = ctx.guild.get_role(int(request['patronus_role']))

        description = f"{patronus.mention}, Time for another Gift Game!\n​ "

        embed = discord.Embed(
            colour=discord.Colour(0x50e3c2),
            title="🎊 Patronus Guild Contest",
            description=description
        )
        embed.set_image(
            url="https://media.discordapp.net/attachments/473127659136614431/"
                "599172714057695242/show_us_ur_patronus.png")
        embed.add_field(
            name="🎉 Event Overview",
            value="@everyone can role-play in the wizarding server of Patronusverse, "
                  "where you will be given a quest to complete. "
                  "This quest can be casually interacted in the server and it will be a riddle kind of game.\n​ "
        )
        embed.add_field(
            name="🗒 Game Mechanics",
            value=f"• Allow direct messages from our bot Miketsu to join. Try `;help dm`\n"
            f"• Interested players can start by reacting at the <#{sorting.id}>\n"
            f"• Hints will be available to use via `;hint`\n"
            f"• When the clock ticks a new hour, various events can happen\n"
            f"• Use <#{gift_game.id}> for any discussion, visible once accepted\n​ "
        )
        embed.add_field(
            name="🥅 Scoring System",
            value="• Players will have a base score of 1000 points\n"
                  "• Reduced by 5 points every hour\n"
                  "• Reduced by every hint unlocked \n"
                  "• Reduced by any irrelevant actions done\n​ "
        )
        embed.add_field(
            name="💝 Rewards System",
            value="• Two current guild members will win Nitro\n"
                  "• The 1st one to ever complete a quest cycle with 999+ points; and\n"
                  "• The 1st one to complete a quest cycle without moving a path\n​\n "
                  "• Note: Commands `;progress` and `;cycle` are unlocked once your first cycle is finished\n\n​ "
                  ":four_leaf_clover: Good luck!​\n "
        )
        embed.set_footer(
            text="special thanks to xann! :3"
        )
        msg = await headlines.send(embed=embed)

        embed = discord.Embed(
            colour=discord.Colour(0xa661da),
            title="Quest Selection & Acceptance",
            description="Only when you finished your current quest, can make you able to restart a "
                        "new quest and have different outcome and score."
        )

        link = f"https://discordapp.com/channels/{msg.guild.id}/{msg.channel.id}/{msg.id}"
        embed.add_field(
            name="🐬 Quest #1: Show us your Patronus!",
            value=f"Learn how to summon one. Refer to the quest mechanics [here!]({link})"
        )

        msg2 = await sorting.send(embed=embed)
        await msg2.add_reaction("🐬")

        books.update_one(
            {"server": str(ctx.guild.id)},
            {"$set": {"letter": str(msg2.id)}}
        )
        await ctx.message.delete()

    @commands.command(aliases=["special"])
    @commands.is_owner()
    async def edit_special_roles(self, ctx):

        request = books.find_one({
            "server": f"{ctx.guild.id}"}, {
            "_id": 0, "messages.special_roles": 1, "channels.sorting-hat": 1
        })
        sorting_id = request["channels"]["sorting-hat"]
        special_roles_id = request["channels"]["special_roles"]
        sorting_channel = self.client.get_channel(int(sorting_id))

        embed = discord.Embed(
            colour=discord.Colour(0x50e3c2),
            title="Special Roles",
            description="Members can react to multiple roles below\n"
                        "Clearing your reaction removes the role"
        )
        embed.add_field(
            name="📚 Apprentice",
            value="Patronus can apply as long term associate and later on graduate to Auror",
            inline=False
        )
        embed.add_field(
            name="🎉 Funfun",
            value="Mentionable role for people looking for playmates",
            inline=False
        )
        embed.add_field(
            name="🔍 Co-op Find",
            value="Mentionable role if you're looking for cooperative teams",
            inline=False
        )
        embed.add_field(
            name="🏁 Boss Busters",
            value="Mentionable role for fake rare boss assembly spawns",
            inline=False
        )
        embed.add_field(
            name="⚾ Shard Seekers",
            value="Auto-pinged whenever people post their shard list for trading",
            inline=False
        )
        embed.add_field(
            name="🎰 Big Spenders",
            value="Auto-pinged whenever a new round of showdown bidding has started",
            inline=False
        )
        special_select_msg = await sorting_channel.fetch_message(int(special_roles_id))
        await special_select_msg.edit(embed=embed)
        await ctx.message.delete()

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
            try:
                await ctx.channel.send("Provide a valid argument: `daily`, `weekly`, or `boss`")
            except AttributeError:
                logging(file, get_f(), "AttributeError")
            except discord.errors.Forbidden:
                logging(file, get_f(), "discord.errors.Forbidden")
            except discord.errors.HTTPException:
                logging(file, get_f(), "discord.errors.HTTPException")

    async def reset_daily(self):

        for entry in daily.find({"key": "daily"}, {"key": 0, "_id": 0}):
            for user_id in entry:
                daily.update_one({"key": "daily"}, {"$set": {f"{user_id}.rewards": "unclaimed"}})

        for user_id in daily.find_one({"key": "raid"}, {"_id": 0, "key": 0}):
            daily.update_one({"key": "raid"}, {"$set": {f"{user_id}.raid_count": 0}})

        query_list = []

        for ship in friendship.find({}, {"ship_name": 1, "shipper1": 1, "shipper2": 1, "level": 1}):
            if ship["level"] > 1:
                rewards = ship["level"] * 25
                query_list.append(f"• {ship['ship_name']}, {rewards}{emoji_j}\n")
                users.update_one({"user_id": ship["shipper1"]}, {"$inc": {"jades": rewards}})
                users.update_one({"user_id": ship["shipper2"]}, {"$inc": {"jades": rewards}})

        description = "".join(query_list[0:10])

        embed = discord.Embed(
            color=0xffff80,
            title="🚢 Daily Ship Sail Rewards",
            description=description
        )
        embed.set_footer(text="Only the first 10 ships are shown~")

        for channel in channels_announcement:
            current_channel = self.client.get_channel(int(channel))
            try:
                await current_channel.send("🎊 Daily rewards have been reset.", embed=embed)
            except discord.errors.Forbidden:
                logging(file, get_f(), "discord.errors.Forbidden")
            except discord.errors.HTTPException:
                logging(file, get_f(), "discord.errors.HTTPException")

    async def reset_weekly(self):

        for entry in daily.find({"key": "weekly"}, {"key": 0, "_id": 0}):
            for user in entry:
                daily.update({"key": "weekly"}, {
                    "$set": {
                        f"{user}.rewards": "unclaimed"
                    }
                })

        for channel in channels_announcement:
            current_channel = self.client.get_channel(int(channel))
            try:
                await current_channel.send("🎊 Weekly rewards have been reset.")
            except discord.errors.Forbidden:
                logging(file, get_f(), "discord.errors.Forbidden")
            except discord.errors.HTTPException:
                logging(file, get_f(), "discord.errors.HTTPException")

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
        for channel in channels_announcement:
            current_channel = self.client.get_channel(int(channel))
            try:
                await current_channel.send("Assembly Boss encounter has been reset.")
            except discord.errors.Forbidden:
                logging(file, get_f(), "discord.errors.Forbidden")
            except discord.errors.HTTPException:
                logging(file, get_f(), "discord.errors.HTTPException")

    @commands.command(aliases=["c", "clear", "purge", "cl", "prune"])
    @commands.has_role("Head")
    async def purge_messages(self, ctx, amount=2):
        try:
            await ctx.channel.purge(limit=amount + 1)
        except discord.errors.Forbidden:
            logging(file, get_f(), "discord.errors.Forbidden")
        except discord.errors.HTTPException:
            logging(file, get_f(), "discord.errors.HTTPException")

    @commands.command(aliases=["bc"])
    @commands.has_role("Head")
    async def broadcast(self, ctx, arg1, *args):

        channel_id = re.sub("[<>#]", "", arg1)
        channel_target = self.client.get_channel(int(channel_id))

        try:
            await channel_target.send(args)
        except AttributeError:
            try:
                await ctx.channel.send(f"The specified channel ID was not found: `{channel_id}`")
            except discord.errors.Forbidden:
                logging(file, get_f(), "discord.errors.Forbidden")
            except discord.errors.HTTPException:
                logging(file, get_f(), "discord.errors.HTTPException")
        except discord.errors.Forbidden:
            logging(file, get_f(), "discord.errors.Forbidden")
        except discord.errors.HTTPException:
            logging(file, get_f(), "discord.errors.HTTPException")

        try:
            await ctx.message.add_reaction("✅")
        except discord.errors.Forbidden:
            logging(file, get_f(), "discord.errors.Forbidden")
        except discord.errors.HTTPException:
            logging(file, get_f(), "discord.errors.HTTPException")

    @commands.command(aliases=["m", "manage"])
    @commands.has_role("Head")
    @commands.check(check_if_guild_is_patronus)
    async def management_guild(self, ctx, *args):

        if len(args) == 0 or args[0].lower() in ["help", "h"]:
            embed = discord.Embed(
                color=ctx.author.colour,
                title="🔱 Management Commands",
                description="• `;m help` - shows this help\n"
                            "• `;m add` - adding new accounts\n"
                            "• `;m update` - updating member profiles\n"
                            "• `;m show` - querying the registry\n"
                            "• `;m stats` - guild statistics"
            )
            embed.set_thumbnail(url=ctx.guild.icon_url)
            await ctx.channel.send(embed=embed)

        elif args[0].lower() == "add" and len(args) <= 2:
            embed = discord.Embed(
                color=ctx.author.colour,
                title="🔱 Adding Members",
                description="• `;m add {role} {name}`"
            )
            embed.add_field(
                name="🎀 Role Selection",
                value="member, ex-member, officer"
            )
            embed.set_thumbnail(url=ctx.guild.icon_url)
            await ctx.channel.send(embed=embed)

        elif args[0].lower() in ["add", "a"] and len(args) == 3 and args[1] in roles:

            if members.find_one({"name_lower": args[2].lower()}) is None:
                count = members.count() + 1

                profile = {
                    "#": count,
                    "name": args[2],
                    "role": args[1].capitalize(),
                    "status": "Active",
                    "status_update1": get_time().strftime('%d.%b %y'),
                    "status_update2": get_time().strftime('%Y:%m:%d'),
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
                color=ctx.author.colour,
                title="🔱 Updating Members",
                description="• `;m update {name} {field} {value}`\n"
                            "• `;m update {#} {field} {value}`\n"
                            "• `;m update feats` - batch updating\n"
                            "• `;m update inactives` - batch updating"
            )
            embed.add_field(
                name="🎀 Roles",
                value="member, ex-member, officer"
            )
            embed.add_field(
                name="⛳ Status",
                value="active, inactive, on-leave, kicked, semi-active, away, left"
            )
            embed.add_field(
                name="🗒 Notes",
                value="Any officer notes"
            )
            embed.set_footer(text="Use name as field to revise name")
            embed.set_thumbnail(url=ctx.guild.icon_url)
            await ctx.channel.send(embed=embed)

        elif args[0].lower() in ["update", "u"] and args[1].lower() == "inactives" and len(args) == 2:
            await self.management_update_performance(ctx)

        elif args[0].lower() in ["update", "u"] and args[1].lower() == "feats" and len(args) == 2:
            await self.management_update_feats(ctx)

        elif args[0].lower() in ["update", "u"] and len(args) == 2:
            await ctx.channel.send("No field and value provided. Valid fields: `name`, `role`, `status`, `notes`")

        elif args[0].lower() in ["update", "u"] and args[2].lower() not in fields and len(
                args) >= 3:
            await ctx.channel.send("Invalid field update request. Valid fields: `name`, `role`, `status`, `notes`")

        elif args[0].lower() in ["update", "u"] and args[2].lower() in fields and len(args) == 3:
            await ctx.channel.send("No value provided for the field.")

        elif args[0].lower() in ["update", "u"] and len(args) >= 4 and args[2].lower() in fields:
            await management_update_field(ctx, args)

        elif args[0].lower() in ["show", "s"] and len(args) == 1:
            embed = discord.Embed(
                color=ctx.author.colour,
                title="🔱 Querying Members",
                description="• `;m show all`\n"
                            "• `;m show all {[a-z or 1-9]}`\n"
                            "• `;m show all guild`\n"
                            "• `;m show {name or #}`\n"
                            "• `;m show {field} {data}`"
            )
            embed.add_field(
                name="🎀 Role",
                value="member, ex-member, officer"
            )
            embed.add_field(
                name="⛳ Status",
                value="active, inactive, on-leave, kicked, semi-active, away, left"
            )
            embed.set_thumbnail(url=ctx.guild.icon_url)
            await ctx.channel.send(embed=embed)

        elif args[0].lower() in ["show", "s"] and len(args) == 2 and args[1].lower() == "role":
            await ctx.channel.send("Provide a role value to show. `;m show role {member, ex-member, etc..}`")

        elif args[0].lower() in ["show", "s"] and len(args) == 2 and (args[1].lower() == "status"):
            await ctx.channel.send("Provide a status value to show. `;m show status {active, inactive, etc..}`")

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
            await management_stats(ctx)

        else:
            await ctx.message.add_reaction("❌")

    async def management_update_performance(self, ctx):

        await ctx.channel.send("Opening environment for batch updating of inactives...")
        await asyncio.sleep(3)
        await ctx.channel.send("Enter `stop`/`skip` to exit the environment or skip a member, respectively...")
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
            title="Performing initial calculations..."
        )

        await ctx.channel.send(embed=embed1)
        await asyncio.sleep(4)
        msg = await ctx.channel.send("Enter the GQ code `(90/60/30)` for: ", embed=embed2)

        query = members.find({
            "role": {
                "$in": ["Officer", "Member", "Leader"]},
            "status": {
                "$in": ["Semi-active", "Inactive"]}}, {
            "_id": 0, "name": 1, "role": 1, "#": 1, "status": 1, "total_feats": 1, "weekly_gq": 1, "status_update1": 1
        })

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

        for member in query.sort([("total_feats", -1)]):
            embed = discord.Embed(
                color=ctx.author.colour,
                title=f"#{member['#']} : {member['name']} | 🎀 {member['role']}"
            )
            embed.set_thumbnail(url=ctx.guild.icon_url)
            embed.set_footer(text=f"Queried on {get_time().strftime('%b %d, %Y %H:%M EST')}")
            embed.add_field(
                name="⛳ Status",
                value=f"{member['status']} [{member['status_update1']}]"
            )
            embed.add_field(
                name="🏆 Feats | GQ",
                value=f"{member['total_feats']} | {member['weekly_gq']} [Wk{get_time().isocalendar()[1]}]"
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
                            status_update1=get_time().strftime('%d.%b %y'),
                            status_update2=get_time().strftime('%Y:%m:%d'),
                            weekly_gq=value)
                    })
                    await answer.add_reaction("✅")
                    await asyncio.sleep(3)
                    await answer.delete()
                    break
                except IndexError:
                    break
                except TypeError:
                    msg1 = await ctx.channel.send("Exiting environment..")
                    await msg1.add_reaction("✅")
                    i = "cancel"
                    break
                except KeyError:
                    msg2 = await ctx.channel.send("Invalid input")
                    await asyncio.sleep(2)
                    await msg2.delete()
                    i = 0
                except asyncio.TimeoutError:
                    msg3 = await ctx.channel.send("Exiting environment due to timeout error")
                    await asyncio.sleep(1)
                    await msg3.add_reaction("✅")
                    i = "cancel"
                    break

            if i == "cancel":
                break
            else:
                continue

        await ctx.channel.send("Batch update ended.")

    async def management_update_feats(self, ctx):

        await ctx.channel.send("Opening environment for batch updating of inactives...")
        await asyncio.sleep(3)
        await ctx.channel.send("Enter `stop`/`skip` to exit the environment or skip a member, respectively...")
        await asyncio.sleep(3)

        embed = discord.Embed(
            color=ctx.author.colour,
            title="Performing initial calculations..."
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
                value=f"{member['total_feats']} | {member['weekly_gq']} [Wk{get_time().isocalendar()[1]}]"
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
                    msg = await ctx.channel.send("Exiting environment..")
                    await msg.add_reaction("✅")
                    i = "cancel"
                    break
                except KeyError:
                    msg = await ctx.channel.send("Invalid input")
                    await asyncio.sleep(2)
                    await msg.delete()
                    i = 0
                except asyncio.TimeoutError:
                    msg = await ctx.channel.send("Exiting environment due to timeout error")
                    await asyncio.sleep(1)
                    await msg.add_reaction("✅")
                    i = "cancel"
                    break
            if i == "cancel":
                break
            else:
                continue

        await ctx.channel.send("Batch update ended.")

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
        embed.set_footer(text=f"Page: 1 | Queried on {get_time().strftime('%b %d, %Y %H:%M EST')}")
        embed.set_thumbnail(url=ctx.guild.icon_url)
        noun = pluralize("member", len(query_list))
        content = f"There are {len(query_list)} {noun} currently in the guild"

        msg = await ctx.channel.send(content=content, embed=embed)
        await self.management_paginate_embeds(ctx, msg, query_list, get_time().strftime('%b %d, %Y %H:%M EST'))

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
        embed.set_footer(text=f"Page: 1 | Queried on {get_time().strftime('%b %d, %Y %H:%M EST')}")
        embed.set_thumbnail(url=ctx.guild.icon_url)

        noun = pluralize("result", len(query_list))
        content = f"I've got {len(query_list)} {noun} for names starting with {args[2].lower()}"

        msg = await ctx.channel.send(content=content, embed=embed)
        await self.management_paginate_embeds(ctx, msg, query_list, get_time().strftime('%b %d, %Y %H:%M EST'))

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
        embed.set_footer(text=f"Page: 1 | Queried on {get_time().strftime('%b %d, %Y %H:%M EST')}")
        embed.set_thumbnail(url=ctx.guild.icon_url)
        noun = pluralize("account", len(query_list))
        content = f"There are {len(query_list)} registered {noun}"

        msg = await ctx.channel.send(content=content, embed=embed)
        await self.management_paginate_embeds(ctx, msg, query_list, get_time().strftime('%b %d, %Y %H:%M EST'))

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
        embed.set_footer(text=f"Page: 1 | Queried on {get_time().strftime('%b %d, %Y %H:%M EST')}")
        embed.set_thumbnail(url=ctx.guild.icon_url)
        noun = pluralize("result", len(query_list))
        content = f"I've got {len(query_list)} {noun} for members with role {args[2].lower()}"

        msg = await ctx.channel.send(content=content, embed=embed)
        await self.management_paginate_embeds(ctx, msg, query_list, get_time().strftime('%b %d, %Y %H:%M EST'))

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
        embed.set_footer(text=f"Page: 1 | Queried on {get_time().strftime('%b %d, %Y %H:%M EST')}")
        embed.set_thumbnail(url=ctx.guild.icon_url)
        noun = pluralize("result", len(query_list))
        content = f"I've got {len(query_list)} {noun} for members with status {args[2].lower()}"

        msg = await ctx.channel.send(content=content, embed=embed)
        await self.management_paginate_embeds(ctx, msg, query_list, get_time().strftime('%b %d, %Y %H:%M EST'))

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
