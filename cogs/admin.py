"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""

import asyncio
import re
from datetime import datetime

import discord
import pytz
from discord.ext import commands

from cogs.mongo.db import daily, boss, members, users, friendship, books

# Timezone
tz_target = pytz.timezone("America/Atikokan")

# Global Variables
fields = ["name", "role", "status", "notes", "note", "tfeat", "gq"]
roles = ["member", "ex-member", "officer", "leader"]
status_values = ["active", "inactive", "on-leave", "kicked", "semi-active", "away", "left"]
emoji_j = "<:jade:555630314282811412>"


# noinspection PyShadowingNames,PyShadowingBuiltins,PyMethodMayBeStatic,PyUnusedLocal,PyUnboundLocalVariable
class Admin(commands.Cog):

    def __init__(self, client):
        self.client = client

    def pluralize(self, singular, count):
        if count > 1:
            return singular + "s"
        else:
            return singular

    @commands.command(aliases=["welcome"])
    @commands.is_owner()
    async def post_welcome(self, ctx):
        request = books.find_one({"server": f"{ctx.guild.id}"}, {"_id": 0})
        welcome = self.client.get_channel(int(request["welcome"]))
        sorting = request["sorting"]
        patronus_role = request["patronus_role"]

        # Welcome
        embed1 = discord.Embed(title="Welcome to House Patronus!", colour=discord.Colour(0xe77eff),
                               description="Herewith are the rules and information of our server!\n\n"
                                           "Crest designed by <@!281223518103011340>")
        embed1.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/556032841897607178/584001678316142607/Patronus_Crest.png")

        # Server roles
        embed2 = discord.Embed(title="Primary Server Roles", colour=discord.Colour(0xff44),
                               description=f"• Sub roles are provided at the <#{sorting}>")
        embed2.add_field(name=":trident: Head", value="• The Ministers of Patronus")
        embed2.add_field(name=":fleur_de_lis: Auror", value="• Prime Witches, Wizards, & Spirits of Patronus",
                         inline=False)
        embed2.add_field(name=":crystal_ball: Patronus", value="• Existing members of the guild", inline=False)
        embed2.add_field(name=":fire: No-Maj", value="• Obliviated, former members, guests", inline=False)
        embed2.add_field(name=":panda_face: Animagus", value="• Transformed members during Night time, Bots",
                         inline=False)

        # Rules
        embed3 = discord.Embed(title=":clipboard: Rules", colour=discord.Colour(0xf8e71c),
                               description="• Useless warnings may be given!")

        embed3.add_field(name="# 1. Server nickname", value="• It must contain your actual in-game name\n​ ")
        embed3.add_field(name="# 2. Message content",
                         value="• No any form of harassment, racism, toxicity, etc.\n• Avoid posting NSFW or NSFL\n​ ",
                         inline=False)
        embed3.add_field(name="# 3. Role/member mention",
                         value="• Avoid unnecessary pinging\n• Check for the specific roles for free pinging\n​ ",
                         inline=False)
        embed3.add_field(name="# 4. Spamming",
                         value="• Posting at the wrong channel is spamming\n• Channels are provided for spamming bot "
                               "commands\n​ ",
                         inline=False)
        embed3.add_field(name="# 5. No unsolicited promotions",
                         value="• Like advertising of other guilds/servers without permission\n​ ", inline=False)
        embed3.add_field(name="# 6. Extensions",
                         value="• Above rules apply on members' direct messages\n• Follow [Discord Community "
                               "Guidelines](https://discordapp.com/guidelines)\n​ ",
                         inline=False)

        # Requirements
        embed4 = discord.Embed(title=":ribbon: Benefits & Requirements", colour=discord.Colour(0xb8e986),
                               description=f"• <@&{patronus_role}> are requested to be guided for #5")

        embed4.add_field(name="# 1. No duel/tier requirements", value="• But do test your limits and improve!\n​ ")
        embed4.add_field(name="# 2. Guild Quest (GQ) requirements",
                         value="• For apprentices, min 30 weekly GQ\n• For qualified mentors, min 90 weekly GQ\n​ ",
                         inline=False)
        embed4.add_field(name="# 3. Alternate Accounts",
                         value="• We can accommodate if slots are available\n• Notify the Head before applying\n​ ",
                         inline=False)
        embed4.add_field(name="# 4. Guild Bonuses",
                         value="• Top 10 guild in overall activeness ranking\n• Rated at 60-70 guild packs per "
                               "week\n• Weekly 1-hour soul & evo bonus\n• 24/7 exp, coin, & medal buffs\n• Max guild "
                               "feast rewards\n• Ultimate Orochi carries\n• Souls 10 carries\n• Rich Discord "
                               "contents\n• Fun, playful, & experienced members\n​ ",
                         inline=False)
        embed4.add_field(name="# 5. Absenteeism/leave",
                         value="• If leaving for shards, specify amount of days\n• File your applications "
                               "prior long vacations\n• Up to 25-35 days of leave for old members\n​ ",
                         inline=False)

        # Events
        embed5 = discord.Embed(title=":confetti_ball: Events & Timings", colour=discord.Colour(0x50e3c2),
                               description=f"• <@&{patronus_role}> role is pinged for events #2-5")

        embed5.add_field(name="# 1. Guild Raid", value="• `05:00 EST` | Resets Everyday \n​")
        embed5.add_field(name="# 2. Kirin Hunt", value="• `19:00 EST` | Every Mon to Thu\n​", inline=False)
        embed5.add_field(name="# 3. Guild Feast", value="• `10:00 EST` | Every Sat \n• `00:00 EST` | Every Sun\n​",
                         inline=False)
        embed5.add_field(name="# 4. Boss Defense", value="• `10:15 EST` | Every Sat \n​", inline=False)
        embed5.add_field(name="# 5. Exclusive Guild Contests", value="• Announced once in a while in Discord\n​ ",
                         inline=False)

        # Message posting
        msg1 = await welcome.send(embed=embed1)
        msg2 = await welcome.send(embed=embed2)
        msg3 = await welcome.send(embed=embed3)
        msg4 = await welcome.send(embed=embed4)
        msg5 = await welcome.send(embed=embed5)
        msg6 = await welcome.send(content="Our invite link: https://discord.gg/H6N8AHB")

        # Post processing
        await ctx.message.delete()
        books.update_one({"server": f"{ctx.guild.id}"}, {"$set": {
            "intro_id": str(msg1.id), "roles_id": str(msg2.id), "rules_id": str(msg3.id),
            "requirements_id": str(msg4.id), "events_id": str(msg5.id), "invite_id": str(msg6.id),
        }})

    @commands.command(aliases=["start"])
    @commands.is_owner()
    async def post_announcement_magic(self, ctx):
        request = books.find_one({"server": f"{ctx.guild.id}"},
                                 {"_id": 0, "sorting": 1, "patronus_role": 1, "headlines": 1})

        headlines = self.client.get_channel(int(request["headlines"]))
        sorting = self.client.get_channel(int(request["sorting"]))
        patronus = ctx.guild.get_role(int(request['patronus_role']))

        embed = discord.Embed(title=":confetti_ball: Special Guild Contest", colour=discord.Colour(0x50e3c2),
                              description=f"{patronus.mention}, in late celebration of our not so recent merge "
                              f"with Crusaders, it is timely to have our next once in a while Discord Event!\n")

        embed.add_field(name=":tada: Event Overview",
                        value="Members can role-play as a wizard/witch/spirit in the wizarding server of Patronusverse "
                              "where you will be given a quest to complete. This quest can be casually interacted in "
                              "the server and it will be an idle and riddle kind of game.\n")
        embed.add_field(name=":notepad_spiral:  Game Mechanics",
                        value=f"`1. `You must allow direct messages from our bot Miketsu to be able to join. "
                        f"Use command `;help dm` to test if Miketsu can direct message you.\n"
                        f"`2. ` Interested players can voluntarily accept the quest at the {sorting.name} to "
                        f"kick start their adventure.\n"
                        f"`3. `Messages sent to the players may be crucial to finish the quest.\n`"
                        f"4. `Hints will be available to use via command `;hint`\n"
                        f"`5. `Also, once the clock ticks a new hour, various events can happen, "
                        f"it's up for players to learn and notice them.\n"
                        f"`6. `Quest cycle can be checked via command `;progress`\n")
        embed.add_field(name=":goal: Scoring System",
                        value="`1. `Players will have a base score of 1000 points\n`2. `Every hour that passes reduces "
                              "their score by 2 points\n`3. `Every hint revealed reduces their score by 10 points \n"
                              "`4. `Certain wrong and irrelevant actions made can reduce their score as well\n")
        embed.add_field(name=":gift_heart: Rewards System",
                        value="`1. `Two players will win the event. One is a pre-merge Patronus member and the other "
                              "is a pre-merge Crusaders member.\n`2. `The 1st person to complete the quest will "
                              "automatically earn themselves 1-month Discord Nitro\n`3. `Whereas, the next 5 people "
                              "who completed the quest for the 2nd time will compete for the highest 2nd cycle score "
                              "to earn another Discord Nitro.\n\n__Note: The 5 people who will compete for the 2nd "
                              "reward will be of the same pre-merge Guild as opposed to the Guild of the 1st "
                              "winner.__ Moreover, the 2nd cycle means that you need to re-do the whole quest AFTER "
                              "you finished the 1st cycle to get a higher score than your previous one.")
        msg = await headlines.send(embed=embed)

        embed = discord.Embed(title="Quest Selection & Acceptance", colour=discord.Colour(0xa661da),
                              description="Only when you finished your current quest, can make you able to restart a "
                                          "new quest and have different outcome and score.")

        link = f"https://discordapp.com/channels/{msg.guild.id}/{msg.channel.id}/{msg.id}"
        embed.add_field(name=":dolphin: Quest #1: Show us your Patronus!",
                        value=f"Learn how to summon one. Refer to the quest mechanics [here!]({link})")

        msg2 = await sorting.send(embed=embed)
        await msg2.add_reaction("🐬")
        books.update_one({"server": str(ctx.guild.id)}, {"$set": {"letter": str(msg2.id)}})
        await ctx.message.delete()

    @commands.command(aliases=["specialrole"])
    @commands.is_owner()
    async def post_specialrole(self, ctx):
        embed = discord.Embed(title="Special Roles", colour=discord.Colour(0x50e3c2),
                              description="Members can react to multiple roles below\n"
                                          "Clearing your reaction removes the role")

        embed.add_field(name=":books: Apprentice",
                        value="Patronus can apply as long term associate and later on graduate to Auror", inline=False)
        embed.add_field(name=":tada: Funfun", value="Mentionable role for people looking for playmates", inline=False)
        embed.add_field(name=":mag: Coop Find",
                        value="Mentionable role if you're looking for accompany quest completion", inline=False)
        embed.add_field(name=":checkered_flag: Boss Busters", value="Mentionable role for rare boss assembly spawns",
                        inline=False)

        await ctx.channel.send(embed=embed)

    async def reset_daily(self, channel):
        for entry in daily.find({"key": "daily"}, {"key": 0, "_id": 0}):
            for user_id in entry:
                daily.update_one({"key": "daily"}, {"$set": {f"{user_id}.rewards": "unclaimed"}})

        for user_id in daily.find_one({"key": "raid"}, {"_id": 0, "key": 0}):
            daily.update_one({"key": "raid"}, {"$set": {f"{user_id}.raid_count": 0}})

        query_list = []
        for ship in friendship.find({}, {"ship_name": 1, "shipper1": 1, "shipper2": 1, "level": 1}):
            if ship["level"] > 1:
                rewards = ship["level"] * 25
                query_list.append(f":small_orange_diamond: {ship['ship_name']}, {rewards}{emoji_j}\n")
                users.update_one({"user_id": ship["shipper1"]}, {"$inc": {"jades": rewards}})
                users.update_one({"user_id": ship["shipper2"]}, {"$inc": {"jades": rewards}})

        description = "".join(query_list[0:10])
        embed = discord.Embed(color=0xffff80, title=":ship: Daily Ship Sail Rewards", description=description)
        embed.set_footer(text="Page 1")
        msg = await channel.send("🎊 Daily rewards have been reset.", embed=embed)

        await msg.add_reaction("⬅")
        await msg.add_reaction("➡")

        def create_embed(page):
            end = page * 10
            start = end - 10
            description = "".join(query_list[start:end])
            embed = discord.Embed(color=0xffff80, title=":ship: Daily Ship Sail Rewards", description=description)
            embed.set_footer(text=f"Page: {page}")
            return embed

        def check(reaction, user):
            return user != self.client.user and reaction.message.id == msg.id

        page = 1
        while True:
            try:
                timeout = 60
                reaction, user = await self.client.wait_for("reaction_add", timeout=timeout, check=check)
                if str(reaction.emoji) == "➡":
                    page += 1
                elif str(reaction.emoji) == "⬅":
                    page -= 1
                if page == 0:
                    page = 1

                await msg.edit(embed=create_embed(page))
            except asyncio.TimeoutError:
                return False

    async def reset_weekly(self, channel):
        for entry in daily.find({"key": "weekly"}, {"key": 0, "_id": 0}):
            for user in entry:
                daily.update({"key": "weekly"}, {"$set": {f"{user}.rewards": "unclaimed"}})

        await channel.send("🎊 Weekly rewards have been reset.")

    async def reset_boss(self, channel):
        boss.update_many({}, {"$set": {"discoverer": 0, "level": 0, "damage_cap": 0, "total_hp": 0, "current_hp": 0,
                                       "challengers": [], "rewards": {}}})

        await channel.send("Assembly Boss encounter has been reset.")

    @commands.command()
    @commands.is_owner()
    async def reset(self, ctx, *args):

        # Resets daily
        if args[0] == "daily":
            await self.reset_daily(ctx.channel)

        # Resets weekly
        elif args[0] == "weekly":
            await self.reset_weekly(ctx.channel)

        # Resets the boss
        elif args[0] == "boss":
            await self.reset_boss(ctx.channel)

        else:
            await ctx.channel.send("Provide a valid argument: daily, weekly, or boss")

    @commands.command(aliases=["c", "clear", "purge", "cl", "prune"])
    @commands.has_role("Head")
    async def purge_messages(self, ctx, amount=2):
        await ctx.channel.purge(limit=amount + 1)

    @commands.command(aliases=["bc"])
    @commands.has_role("Head")
    async def broadcast(self, ctx, *args):
        channel = self.client.get_channel(int(re.sub("[<>#]", "", args[0])))
        await channel.send(f"{' '.join(args[1:])}")
        await ctx.message.add_reaction("✅")

    @commands.command(aliases=["m"])
    @commands.has_role("Head")
    async def management_guild(self, ctx, *args):

        # No argument passed
        if len(args) == 0 or args[0].lower() == "help" or args[0].lower() == "h":
            embed = discord.Embed(color=0xffff80, title="🔱 Management Commands",
                                  description="• `;m help` - shows this help\n"
                                              "• `;m add` - adding new accounts\n"
                                              "• `;m update` - updating member profiles\n"
                                              "• `;m show` - querying the registry\n"
                                              "• `;m stats` - guild statistics")
            embed.set_thumbnail(url=ctx.guild.icon_url)
            await ctx.channel.send(embed=embed)

        # ;m add {onmyoji}
        elif args[0].lower() == "add" and len(args) <= 2:
            embed = discord.Embed(color=0xffff80, title="🔱 Adding Members",
                                  description="• `;m add {role} {name}`\n")
            embed.add_field(name=":ribbon: Role Selection", value="member, ex-member, officer")
            embed.set_thumbnail(url=ctx.guild.icon_url)
            await ctx.channel.send(embed=embed)

        # ;m add <role> <name>
        elif args[0].lower() == "add" and len(args) == 3 and args[1] in roles:
            members_registered = []
            for member in members.find({}, {"_id": 0, "name_lower": 1, "#": 1}):
                members_registered.append(member["name_lower"])

            if args[2].lower() not in members_registered:
                count = members.count() + 1
                time1 = (datetime.now(tz=tz_target)).strftime("%d.%b %y")
                time2 = (datetime.now(tz=tz_target)).strftime("%Y:%m:%d")

                profile = {"#": count, "name": args[2], "role": args[1].capitalize(), "status": "Active",
                           "status_update1": time1, "status_update2": time2, "country": "<CC>", "timezone": "['/']",
                           "notes": [], "name_lower": args[2].lower()}
                members.insert_one(profile)
                await ctx.message.add_reaction("✅")

            else:
                await ctx.message.add_reaction("❌")

        # ;m update <onmyoji or #> <field> <value>
        elif args[0].lower() in ("update", "u") and len(args) <= 1:
            embed = discord.Embed(color=0xffff80, title="🔱 Updating Members",
                                  description="• `;m update {name} {field} {value}`\n"
                                              "• `;m update {#} {field} {value}`\n"
                                              "• `;m update feats` - batch updating\n"
                                              "• `;m update inactives` - batch updating")
            embed.add_field(name=":ribbon: Roles", value="member, ex-member, officer")
            embed.add_field(name=":golf: Status", value="active, inactive, on-leave, kicked, semi-active, away, left")
            embed.add_field(name="🗒 Notes", value="Any officer notes")
            embed.set_footer(text="Use name as field to revise name")
            embed.set_thumbnail(url=ctx.guild.icon_url)
            await ctx.channel.send(embed=embed)

        # ;m update feats
        elif args[0].lower() in ("update", "u") and args[1].lower() == "inactives" and len(args) == 2:
            await self.management_update_performance(ctx, args)

        # ;m update feats
        elif args[0].lower() in ("update", "u") and args[1].lower() == "feats" and len(args) == 2:
            await self.management_update_feats(ctx, args)

        # ;m update 1
        elif args[0].lower() in ("update", "u") and len(args) == 2:
            await ctx.channel.send("No field and value provided. Valid fields: `name`, `role`, `status`, `notes`")

        # ;m update weird active
        elif args[0].lower() in ("update", "u") and args[2].lower() not in fields and len(
                args) >= 3:
            await ctx.channel.send("Invalid field update request. Valid fields: `name`, `role`, `status`, `notes`")

        # ;m update 1 name
        elif args[0].lower() in ("update", "u") and args[2].lower() in fields and len(args) == 3:
            await ctx.channel.send("No value provided for the field.")

        # ;m update 1 status active
        elif args[0].lower() in ("update", "u") and len(args) >= 4 and args[2].lower() in fields:
            await self.management_update_field(ctx, args)

        # ;m show
        elif args[0].lower() == "show" and len(args) == 1:
            embed = discord.Embed(color=0xffff80, title="🔱 Querying Members",
                                  description="• `;m show all`\n"
                                              "• `;m show all {[a-z or 1-9]}`\n"
                                              "• `;m show all guild`\n"
                                              "• `;m show {name or #}`\n"
                                              "• `;m show {field} {data}`")
            embed.add_field(name=":ribbon: Role", value="member, ex-member, officer")
            embed.add_field(name=":golf: Status", value="active, inactive, on-leave, kicked, semi-active, away, left")
            embed.set_thumbnail(url=ctx.guild.icon_url)
            await ctx.channel.send(embed=embed)

        # ;m show role
        elif args[0].lower() == "show" and len(args) == 2 and args[1].lower() == "role":
            await ctx.channel.send("Provide a role value to show. `;m show role {member, ex-member, etc..}`")

        # ;m show status
        elif args[0].lower() == "show" and len(args) == 2 and (args[1].lower() == "status"):
            await ctx.channel.send("Provide a status value to show. `;m show status {active, inactive, etc..}`")

        # ;m show all
        elif args[0].lower() == "show" and len(args) == 2 and args[1].lower() == "all":
            await self.management_show_guild_specific(ctx, args)

        # ;m show all guild
        elif args[0].lower() == "show" and len(args) == 3 and args[1].lower() == "all" and args[2].lower() == "guild":
            await self.management_show_guild_current(ctx, args)

        # ;m show all a
        elif args[0].lower() == "show" and len(args) == 3 and args[1].lower() == "all":
            await self.management_show_guild_first(ctx, args)

        elif args[0].lower() == "show" and len(args) == 2 and args[1].lower() != "all" \
                and args[1].lower() not in fields:
            await self.management_show_profile(ctx, args)

        # ;m show status <value>
        elif args[0].lower() == "show" and len(args) == 3 and args[1].lower() == "status" \
                and args[2].lower() in status_values:
            await self.management_show_field_status(ctx, args)

        # ;m show role <value>
        elif args[0].lower() == "show" and len(args) == 3 and args[1].lower() == "role" and args[2].lower() in roles:
            await self.management_show_field_role(ctx, args)

        # ;m show role <value>
        elif args[0].lower() == "stats" and len(args) == 1:
            await self.management_stats(ctx)

        # No command hit
        else:
            await ctx.message.add_reaction("❌")

    async def management_update_performance(self, ctx, args):

        time = (datetime.now(tz=tz_target)).strftime("%d.%b %Y %H:%M EST")
        week_number = datetime.now(tz=tz_target).isocalendar()[1]

        await ctx.channel.send("Opening environment for batch updating of inactives...")
        await asyncio.sleep(3)

        await ctx.channel.send("Enter `stop`/`skip` to exit the environment or skip a member, respectively...")
        await asyncio.sleep(3)

        description = "• `90` : `ACTV` | `>= 90 GQ`\n" \
                      "• `60` : `SMAC` | `90 > GQ > 30`\n" \
                      "• `30` : `INAC` | `<30 GQ`"

        embed = discord.Embed(color=0xffff80, title="GQ Codes", description=description)
        await ctx.channel.send(embed=embed)
        await asyncio.sleep(4)

        embed = discord.Embed(color=0xffff80, title="Performing initial calculations...")
        msg = await ctx.channel.send("Enter the GQ code `(90/60/30)` for: ", embed=embed)

        for member in members.find({"role": {"$in": ["Officer", "Member", "Leader"]},
                                    "status": {"$in": ["Semi-active", "Inactive"]}},
                                   {"_id": 0, "name": 1, "role": 1, "#": 1, "status": 1,
                                    "total_feats": 1, "weekly_gq": 1,
                                    "status_update1": 1}).sort([("total_feats", -1)]):

            embed = discord.Embed(color=0xffff80,
                                  title=f"#{member['#']} : {member['name']} | :ribbon: {member['role']}")
            embed.set_thumbnail(url=ctx.guild.icon_url)
            embed.set_footer(text=f"Queried on {time}")
            embed.add_field(name=":golf: Status", value=f"{member['status']} [{member['status_update1']}]")
            embed.add_field(name=":trophy: Feats | GQ",
                            value=f"{member['total_feats']} | {member['weekly_gq']} [Wk{week_number}]")

            await asyncio.sleep(2)
            await msg.edit(embed=embed)

            def check(feat):
                try:
                    value = int(feat.content)

                    if value not in [90, 60, 30]:
                        raise KeyError

                except ValueError:

                    if feat.content.lower() == "stop":
                        raise TypeError

                    elif feat.content.lower() == "skip":
                        raise IndexError

                    else:
                        raise KeyError

                return feat.author == ctx.message.author

            i = 0
            while i < 1:

                try:
                    timeout = 180
                    answer = await self.client.wait_for("message", timeout=timeout, check=check)
                    value = int(answer.content)
                    time1 = (datetime.now(tz=tz_target)).strftime("%d.%b %y")
                    time2 = (datetime.now(tz=tz_target)).strftime("%Y:%m:%d")

                    if value == 30:
                        members.update_one({"name": str(member["name"])}, {"$set": {"status": "Inactive",
                                                                                    "status_update1": time1,
                                                                                    "status_update2": time2}})
                    elif value == 60:
                        members.update_one({"name": str(member["name"])}, {"$set": {"status": "Semi-active",
                                                                                    "status_update1": time1,
                                                                                    "status_update2": time2}})
                    elif value == 90:
                        members.update_one({"name": str(member["name"])}, {"$set": {"status": "Active",
                                                                                    "status_update1": time1,
                                                                                    "status_update2": time2}})

                    members.update_one({"name": str(member["name"])}, {"$set": {"weekly_gq": value}})

                    await answer.add_reaction("✅")
                    await asyncio.sleep(2)
                    await answer.delete()
                    i += 1

                except IndexError:
                    i = 4

                except TypeError:
                    msg = await ctx.channel.send("Exiting environment..")
                    await msg.add_reaction("✅")
                    i = 5

                except KeyError:
                    msg = await ctx.channel.send("Invalid input")
                    await asyncio.sleep(2)
                    await msg.delete()
                    i = 0

                except asyncio.TimeoutError:
                    msg = await ctx.channel.send("Exiting environment due to timeout error")
                    await asyncio.sleep(1)
                    await msg.add_reaction("✅")
                    i += 1

            if i == 5:
                break

            elif i == 4:
                continue

    async def management_update_feats(self, ctx, args):

        time = (datetime.now(tz=tz_target)).strftime("%d.%b %Y %H:%M EST")
        week_number = datetime.now(tz=tz_target).isocalendar()[1]

        await ctx.channel.send("Opening environment for batch updating of inactives...")
        await asyncio.sleep(3)

        await ctx.channel.send("Enter `stop`/`skip` to exit the environment or skip a member, respectively...")
        await asyncio.sleep(3)

        embed = discord.Embed(color=0xffff80, title="Performing initial calculations...")
        msg = await ctx.channel.send("Enter the total feats for: ", embed=embed)

        for member in members.find({"role": {"$in": ["Officer", "Member", "Leader"]}},
                                   {"_id": 0, "name": 1, "role": 1, "#": 1, "status": 1,
                                    "total_feats": 1, "weekly_gq": 1,
                                    "status_update1": 1}).sort([("total_feats", 1)]):

            embed = discord.Embed(color=0xffff80,
                                  title=f"#{member['#']} : {member['name']} | :ribbon: {member['role']}")
            embed.set_thumbnail(url=ctx.guild.icon_url)
            embed.add_field(name=":golf: Status", value=f"{member['status']} [{member['status_update1']}]")
            embed.add_field(name=":trophy: Feats | GQ",
                            value=f"{member['total_feats']} | {member['weekly_gq']} [Wk{week_number}]")

            await asyncio.sleep(2)
            await msg.edit(embed=embed)

            def check(feat):
                try:
                    value = int(feat.content)

                except ValueError:

                    if feat.content.lower() == "stop":
                        raise TypeError

                    elif feat.content.lower() == "skip":
                        raise IndexError

                    else:
                        raise KeyError

                return feat.author == ctx.message.author

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
                    i += 1

                except IndexError:
                    i = 4

                except TypeError:
                    msg = await ctx.channel.send("Exiting environment..")
                    await msg.add_reaction("✅")
                    i = 5

                except KeyError:
                    msg = await ctx.channel.send("Invalid input")
                    await asyncio.sleep(2)
                    await msg.delete()
                    i = 0

                except asyncio.TimeoutError:
                    msg = await ctx.channel.send("Exiting environment due to timeout error")
                    await asyncio.sleep(1)
                    await msg.add_reaction("✅")
                    i += 1

            if i == 5:
                break

            elif i == 4:
                continue

    async def management_stats(self, ctx):

        time = (datetime.now(tz=tz_target)).strftime("%d.%b %Y %H:%M EST")
        registered_users = members.count()
        guild_members = members.count({"role": {"$in": ["Officer", "Member", "Leader"]}})
        guild_members_actv = members.count({"role": {"$in": ["Officer", "Member", "Leader"]}, "status": "Active"})
        guild_members_inac = members.count({"role": {"$in": ["Officer", "Member", "Leader"]}, "status": "Inactive"})
        guild_members_onlv = members.count({"role": {"$in": ["Officer", "Member", "Leader"]}, "status": "On-leave"})
        guild_members_smac = members.count({"role": {"$in": ["Officer", "Member", "Leader"]}, "status": "Semi-active"})
        ex_members_away = members.count({"role": "Ex-member", "status": "Away"})

        description = f"Registered Accounts: `{registered_users}`\n" \
            f"Guild Occupancy: `{guild_members}/160`\n" \
            f"▫ Active: `{guild_members_actv}`\n" \
            f"▫ Semi-active: `{guild_members_smac}`\n" \
            f"▫ Inactive: `{guild_members_inac}`\n" \
            f"▫ On-leave: `{guild_members_onlv}`\n" \
            f"🔹 Away: `{ex_members_away}`"

        msg = f"Estimated guild quests per week: {guild_members_actv * 90 + guild_members_smac * 30:,d}"
        embed = discord.Embed(color=0xffff80, title="🔱 Guild Statistics", description=f"{description}")
        embed.set_footer(text=f"Queried on {time}")
        embed.set_thumbnail(url=ctx.guild.icon_url)
        await ctx.channel.send(msg, embed=embed)

    async def management_show_guild_current(self, ctx, args):
        time = (datetime.now(tz=tz_target)).strftime("%d.%b %Y %H:%M EST")
        query_list = []

        for member in members.find({"role": {"$in": ["Officer", "Member", "Leader"]}},
                                   {"_id": 0, "name": 1, "role": 1, "#": 1, "status": 1}).sort([("total_feats", -1)]):

            if member['role'] == "Leader":
                role = "LDR"
            elif member['role'] == "Member":
                role = "MEM"
            elif member['role'] == "Officer":
                role = "OFR"

            if member['status'] == "Active":
                status = "ACTV"
            elif member['status'] == "Inactive":
                status = "INAC"
            elif member['status'] == "On-leave":
                status = "ONLV"
            elif member['status'] == "Kicked":
                status = "KCKD"
            elif member['status'] == "Semi-active":
                status = "SMAC"
            elif member['status'] == "Away":
                status = "AWAY"
            elif member['status'] == "Left":
                status = "LEFT"

            if member['#'] < 10:
                query_list.append(f"`#00{member['#']}: {role}` | `{status}` | {member['name']}\n")
            elif member['#'] < 100:
                query_list.append(f"`#0{member['#']}: {role}` | `{status}` | {member['name']}\n")
            elif member['#'] >= 100:
                query_list.append(f"`#{member['#']}: {role}` | `{status}` | {member['name']}\n")

        description = "".join(query_list[0:20])
        embed = discord.Embed(color=0xffff80, title="🔱 Guild Registry", description=f"{description}")
        embed.set_footer(text=f"Page: 1 | Queried on {time}")
        embed.set_thumbnail(url=ctx.guild.icon_url)

        noun = self.pluralize("member", len(query_list))
        msg = await ctx.channel.send(f"There are {len(query_list)} {noun} currently in the guild",
                                     embed=embed)

        await msg.add_reaction("⬅")
        await msg.add_reaction("➡")

        def create_embed(page):
            end = page * 20
            start = end - 20
            description = "".join(query_list[start:end])
            embed = discord.Embed(color=0xffff80, title="🔱 Guild Registry", description=f"{description}")
            embed.set_footer(text=f"Page: {page} | Queried on {time}")
            embed.set_thumbnail(url=ctx.guild.icon_url)
            return embed

        def check(reaction, user):
            return user != self.client.user and reaction.message.id == msg.id

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
                    page = 1
                await msg.edit(embed=create_embed(page))
            except asyncio.TimeoutError:
                return False

    async def management_show_guild_first(self, ctx, args):
        time = (datetime.now(tz=tz_target)).strftime("%d.%b %Y %H:%M EST")
        query_list = []

        for member in members.find({"name_lower": {"$regex": f"^{args[2].lower()}"}},
                                   {"_id": 0, "name": 1, "role": 1, "#": 1, "status": 1}).sort([("name_lower", 1)]):

            if member['role'] == "Leader":
                role = "LDR"
            elif member['role'] == "Member":
                role = "MEM"
            elif member['role'] == "Ex-member":
                role = "EXM"
            elif member['role'] == "Officer":
                role = "OFR"

            if member['status'] == "Active":
                status = "ACTV"
            elif member['status'] == "Inactive":
                status = "INAC"
            elif member['status'] == "On-leave":
                status = "ONLV"
            elif member['status'] == "Kicked":
                status = "KCKD"
            elif member['status'] == "Semi-active":
                status = "SMAC"
            elif member['status'] == "Away":
                status = "AWAY"
            elif member['status'] == "Left":
                status = "LEFT"

            if member['#'] < 10:
                query_list.append(f"`#00{member['#']}: {role}` | `{status}` | {member['name']}\n")
            elif member['#'] < 100:
                query_list.append(f"`#0{member['#']}: {role}` | `{status}` | {member['name']}\n")
            elif member['#'] >= 100:
                query_list.append(f"`#{member['#']}: {role}` | `{status}` | {member['name']}\n")

        description = "".join(query_list[0:20])
        embed = discord.Embed(color=0xffff80, title="🔱 Guild Registry", description=f"{description}")
        embed.set_footer(text=f"Page: 1 | Queried on {time}")
        embed.set_thumbnail(url=ctx.guild.icon_url)

        noun = self.pluralize("result", len(query_list))
        msg = await ctx.channel.send(f"I've got {len(query_list)} {noun} for names starting with {args[2].lower()}",
                                     embed=embed)

        await msg.add_reaction("⬅")
        await msg.add_reaction("➡")

        def create_embed(page):
            end = page * 20
            start = end - 20
            description = "".join(query_list[start:end])
            embed = discord.Embed(color=0xffff80, title="🔱 Guild Registry", description=f"{description}")
            embed.set_footer(text=f"Page: {page} | Queried on {time}")
            embed.set_thumbnail(url=ctx.guild.icon_url)
            return embed

        def check(reaction, user):
            return user != self.client.user and reaction.message.id == msg.id

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
                    page = 1
                await msg.edit(embed=create_embed(page))
            except asyncio.TimeoutError:
                return False

    async def management_show_guild_specific(self, ctx, args):
        time = (datetime.now(tz=tz_target)).strftime("%d.%b %Y %H:%M EST")
        query_list = []

        for member in members.find({}, {"_id": 0, "name": 1, "role": 1, "#": 1}).sort([("#", 1)]).sort(
                [("name_lower", 1)]):

            if member['role'] == "Leader":
                role = "LDR"
            elif member['role'] == "Member":
                role = "MEM"
            elif member['role'] == "Ex-member":
                role = "EXM"
            elif member['role'] == "Officer":
                role = "OFR"

            if member['status'] == "Active":
                status = "ACTV"
            elif member['status'] == "Inactive":
                status = "INAC"
            elif member['status'] == "On-leave":
                status = "ONLV"
            elif member['status'] == "Kicked":
                status = "KCKD"
            elif member['status'] == "Semi-active":
                status = "SMAC"
            elif member['status'] == "Away":
                status = "AWAY"
            elif member['status'] == "Left":
                status = "LEFT"

            if member['#'] < 10:
                query_list.append(f"`#00{member['#']}: {role}` | `{status}` | {member['name']}\n")
            elif member['#'] < 100:
                query_list.append(f"`#0{member['#']}: {role}` | `{status}` | {member['name']}\n")
            elif member['#'] >= 100:
                query_list.append(f"`#{member['#']}: {role}` | `{status}` | {member['name']}\n")

        description = "".join(query_list[0:20])
        embed = discord.Embed(color=0xffff80, title="🔱 Guild Registry", description=f"{description}")
        embed.set_footer(text=f"Page: 1 | Queried on {time}")
        embed.set_thumbnail(url=ctx.guild.icon_url)

        noun = self.pluralize("account", len(query_list))
        msg = await ctx.channel.send(f"There are {len(query_list)} registered {noun}", embed=embed)

        await msg.add_reaction("⬅")
        await msg.add_reaction("➡")

        def create_embed(page):
            end = page * 20
            start = end - 20
            description = "".join(query_list[start:end])
            embed = discord.Embed(color=0xffff80, title="🔱 Guild Registry", description=f"{description}")
            embed.set_footer(text=f"Page: {page} | Queried on {time}")
            embed.set_thumbnail(url=ctx.guild.icon_url)
            return embed

        def check(reaction, user):
            return user != self.client.user and reaction.message.id == msg.id

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
                    page = 1
                await msg.edit(embed=create_embed(page))
            except asyncio.TimeoutError:
                return False

    async def management_show_field_role(self, ctx, args):
        time = (datetime.now(tz=tz_target)).strftime("%d.%b %Y %H:%M EST")
        query_list = []
        for member in members.find({"role": args[2].capitalize()},
                                   {"_id": 0, "name": 1, "status_update1": 1,
                                    "status_update2": 1, "#": 1, "role": 1}).sort([("status_update2", 1)]):
            if member['#'] < 10:
                query_list.append(f"`#00{member['#']}: {member['status_update1']}` | {member['name']}\n")
            elif member['#'] < 100:
                query_list.append(f"`#0{member['#']}: {member['status_update1']}` | {member['name']}\n")
            elif member['#'] >= 100:
                query_list.append(f"`#{member['#']}: {member['status_update1']}` | {member['name']}\n")

        description = "".join(query_list[0:20])
        embed = discord.Embed(color=0xffff80, title="🔱 Guild Registry", description=description)
        embed.set_footer(text=f"Page: 1 | Queried on {time}")
        embed.set_thumbnail(url=ctx.guild.icon_url)

        noun = self.pluralize("result", len(query_list))
        msg = await ctx.channel.send(f"I've got {len(query_list)} {noun} for members with role {args[2].lower()}",
                                     embed=embed)

        await msg.add_reaction("⬅")
        await msg.add_reaction("➡")

        def create_embed(page):
            end = page * 20
            start = end - 20
            description = "".join(query_list[start:end])
            embed = discord.Embed(color=0xffff80, title="🔱 Guild Registry", description=description)
            embed.set_footer(text=f"Page: {page} | Queried on {time}")
            embed.set_thumbnail(url=ctx.guild.icon_url)
            return embed

        def check(reaction, user):
            return user != self.client.user and reaction.message.id == msg.id

        page = 1
        while True:
            try:
                timeout = 60
                reaction, user = await self.client.wait_for("reaction_add", timeout=timeout, check=check)
                if str(reaction.emoji) == "➡":
                    page += 1
                elif str(reaction.emoji) == "⬅":
                    page -= 1
                if page == 0:
                    page = 1

                await msg.edit(embed=create_embed(page))
            except asyncio.TimeoutError:
                return False

    async def management_show_field_status(self, ctx, args):
        time = (datetime.now(tz=tz_target)).strftime("%d.%b %Y %H:%M EST")
        query_list = []
        for member in members.find({"status": args[2].capitalize()},
                                   {"_id": 0, "name": 1, "status_update1": 1,
                                    "status_update2": 1, "#": 1}).sort([("status_update2", 1)]):
            if member['#'] < 10:
                query_list.append(f"`#00{member['#']}: {member['status_update1']}` | {member['name']}\n")
            elif member['#'] < 100:
                query_list.append(f"`#0{member['#']}: {member['status_update1']}` | {member['name']}\n")
            elif member['#'] >= 100:
                query_list.append(f"`#{member['#']}: {member['status_update1']}` | {member['name']}\n")

        description = "".join(query_list[0:20])
        embed = discord.Embed(color=0xffff80, title=f"🔱 Guild Registry", description=description)
        embed.set_footer(text=f"Page: 1 | Queried on {time}")
        embed.set_thumbnail(url=ctx.guild.icon_url)
        noun = self.pluralize("result", len(query_list))
        msg = await ctx.channel.send(f"I've got {len(query_list)} {noun} for members with status {args[2].lower()}",
                                     embed=embed)

        await msg.add_reaction("⬅")
        await msg.add_reaction("➡")

        def create_embed(page):
            end = page * 20
            start = end - 20
            description = "".join(query_list[start:end])
            embed = discord.Embed(color=0xffff80, title=f"🔱 Guild Registry", description=description)
            embed.set_footer(text=f"Page: {page} | Queried on {time}")
            embed.set_thumbnail(url=ctx.guild.icon_url)
            return embed

        def check(reaction, user):
            return user != self.client.user and reaction.message.id == msg.id

        page = 1
        while True:
            try:
                timeout = 60
                reaction, user = await self.client.wait_for("reaction_add", timeout=timeout, check=check)
                if str(reaction.emoji) == "➡":
                    page += 1
                elif str(reaction.emoji) == "⬅":
                    page -= 1
                if page == 0:
                    page = 1
                await msg.edit(embed=create_embed(page))
            except asyncio.TimeoutError:
                return False

    async def management_show_profile(self, ctx, args):
        time = (datetime.now(tz=tz_target)).strftime("%d.%b %Y %H:%M EST")

        try:
            id = int(args[1])
            member = members.find_one({"#": id}, {"_id": 0})

        except ValueError:
            member = members.find_one({"name_lower": args[1].lower()}, {"_id": 0})

        try:
            embed = discord.Embed(color=0xffff80,
                                  title=f"#{member['#']} : {member['name']} | :ribbon: {member['role']}")
            embed.add_field(name=":golf: Status", value=f"{member['status']} [{member['status_update1']}]")

            if not member["notes"]:
                embed.add_field(name="🗒 Notes", value="No notes yet.")

            elif len(member["notes"]) != 0:
                notes = ""
                for note in member["notes"]:
                    entry = f"[{note['time']} | {note['officer']}]: {note['note']}\n"
                    notes += entry
                embed.add_field(name="🗒 Notes", value=notes)

            embed.set_footer(text=f"Queried on {time}")
            embed.set_thumbnail(url=ctx.guild.icon_url)
            await ctx.channel.send(embed=embed)

        except TypeError:
            await ctx.channel.send("That member is not in the guild database")

    async def management_update_field(self, ctx, args):
        members_registered = []
        ids_registered = []

        for member in members.find({}, {"_id": 0, "name": 1, "#": 1}):
            members_registered.append(member["name"].lower())
            ids_registered.append(member["#"])

        try:  # check if code is provided
            time1 = (datetime.now(tz=tz_target)).strftime("%d.%b %y")
            time2 = (datetime.now(tz=tz_target)).strftime("%Y:%m:%d")
            id = int(args[1])

            # Check if registered
            if id not in ids_registered:
                await ctx.channel.send("Provided name or number is not in the guild database")

            # Updating the Status
            elif args[2].lower() == "status" and args[3].lower() in status_values:
                members.update_one({"#": id}, {"$set": {"status": args[3].capitalize()}})
                members.update_one({"#": id}, {"$set": {"status_update1": time1}})
                members.update_one({"#": id}, {"$set": {"status_update2": time2}})

                if args[3].lower() in ["away", "left", "kicked"]:
                    members.update_one({"#": id}, {"$set": {"role": "Ex-member"}})

                await ctx.message.add_reaction("✅")

            # Updating the notes
            elif args[2].lower() in ("notes", "note"):
                new_note = " ".join(args[3::])
                members.update_one({"#": id},
                                   {"$push": {"notes": {"officer": ctx.author.name, "time": time1, "note": new_note}}})
                await ctx.message.add_reaction("✅")

            # Updating the name
            elif args[2].lower() == "name":
                members.update_one({"#": id},
                                   {"$set": {"name": args[3], "name_lower": args[3].lower()}})
                await ctx.message.add_reaction("✅")

            # Updating the role
            elif args[2].lower() == "role" and args[3].lower() in roles:
                members.update_one({"#": id}, {"$set": {"role": args[3].capitalize()}})
                await ctx.message.add_reaction("✅")

            # Updating the tfeat
            elif args[2].lower() == "tfeat":

                try:
                    total_feat_new = int(args[3])
                    members.update_one({"#": id}, {"$set": {"total_feats": total_feat_new}})
                    await ctx.message.add_reaction("✅")

                except ValueError:
                    await ctx.message.add_reaction("❌")

            # Updating the tfeat
            elif args[2].lower() == "gq":

                try:
                    new_gq = int(args[3])

                    if new_gq == 30:
                        await ctx.message.add_reaction("✅")
                        members.update_one({"#": id},
                                           {"$set": {"status": "Inactive",
                                                     "status_update1": time1, "status_update2": time2,
                                                     "weekly_gq": new_gq}})
                    elif new_gq == 60:
                        await ctx.message.add_reaction("✅")
                        members.update_one({"#": id},
                                           {"$set": {"status": "Semi-active",
                                                     "status_update1": time1, "status_update2": time2,
                                                     "weekly_gq": new_gq}})
                    elif new_gq == 90:
                        await ctx.message.add_reaction("✅")
                        members.update_one({"#": id},
                                           {"$set": {"status": "Active",
                                                     "status_update1": time1, "status_update2": time2,
                                                     "weekly_gq": new_gq}})
                    else:
                        await ctx.message.add_reaction("❌")

                except ValueError:
                    await ctx.message.add_reaction("❌")

            else:
                await ctx.message.add_reaction("❌")

        # name instead is provided
        except ValueError:
            time1 = (datetime.now(tz=tz_target)).strftime("%d.%b %y")
            time2 = (datetime.now(tz=tz_target)).strftime("%Y:%m:%d")

            # Not in the registered ones
            if args[1].lower() not in members_registered:
                await ctx.channel.send("That user is not in the guild database")

            # Updating the Status
            elif args[2] == "status" and args[3].lower() in status_values:
                members.update_one({"name_lower": args[1].lower()},
                                   {"$set": {"status": args[3].capitalize()}})
                members.update_one({"name_lower": args[1].lower()},
                                   {"$set": {"status_update1": time1}})
                members.update_one({"name_lower": args[1].lower()},
                                   {"$set": {"status_update2": time2}})
                await ctx.message.add_reaction("✅")

            # Updating the notes
            elif args[2] == "notes" or args[2] == "note":
                new_note = " ".join(args[3::])
                members.update_one({"name_lower": args[1].lower()},
                                   {"$push": {"notes": {"officer": ctx.author.name, "time": time1, "note": new_note}}})
                await ctx.message.add_reaction("✅")

            # Updating the name
            elif args[2].lower() == "name":
                members.update_one({"name_lower": args[1].lower()},
                                   {"$set": {"name": args[3], "name_lower": args[3].lower()}})
                await ctx.message.add_reaction("✅")

            # Updating the role
            elif args[2].lower() == "role" and args[3].lower() in roles:
                members.update_one({"name_lower": args[1].lower()},
                                   {"$set": {"role": args[3].capitalize()}})
                await ctx.message.add_reaction("✅")

            # Updating the tfeat
            elif args[2].lower() == "tfeat":

                try:
                    total_feat_new = int(args[3])
                    members.update_one({"name_lower": args[1].lower()}, {"$set": {"total_feats": total_feat_new}})
                    await ctx.message.add_reaction("✅")

                except ValueError:
                    await ctx.message.add_reaction("❌")

            # Updating the GQ
            elif args[2].lower() == "gq":

                try:
                    new_gq = int(args[3])

                    if new_gq == 30:
                        await ctx.message.add_reaction("✅")
                        members.update_one({"name_lower": args[1].lower()},
                                           {"$set": {"status": "Inactive",
                                                     "status_update1": time1, "status_update2": time2,
                                                     "weekly_gq": new_gq}})
                    elif new_gq == 60:
                        await ctx.message.add_reaction("✅")
                        members.update_one({"name_lower": args[1].lower()},
                                           {"$set": {"status": "Semi-active",
                                                     "status_update1": time1, "status_update2": time2,
                                                     "weekly_gq": new_gq}})
                    elif new_gq == 90:
                        await ctx.message.add_reaction("✅")
                        members.update_one({"name_lower": args[1].lower()},
                                           {"$set": {"status": "Active",
                                                     "status_update1": time1, "status_update2": time2,
                                                     "weekly_gq": new_gq}})

                    else:
                        await ctx.message.add_reaction("❌")

                except ValueError:
                    await ctx.message.add_reaction("❌")

            else:
                await ctx.message.add_reaction("❌")


def setup(client):
    client.add_cog(Admin(client))
