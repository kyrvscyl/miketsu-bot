"""
Embeds Module
Miketsu, 2020
"""
import asyncio
import os
import urllib.request
from datetime import datetime
from math import ceil

import discord
from discord.ext import commands

from cogs.ext.database import get_collections

# Collections
guilds = get_collections("guilds")
config = get_collections("config")
sortings = get_collections("sortings")

# Instantiations
id_guild = int(os.environ.get("SERVER"))


def check_if_user_has_any_admin_roles(ctx):
    for role in reversed(ctx.author.roles):
        if role.name in config.find_one({"list": 1}, {"_id": 0})["admin_roles"]:
            return True
    return False


class Embeds(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.prefix = self.client.command_prefix

        self.listings = config.find_one({"list": 1}, {"_id": 0})
        self.emojis = config.find_one({"dict": 1}, {"_id": 0, "emojis": 1})["emojis"]

        self.admin_roles = self.listings["admin_roles"]

        self.msg_id_list = []
        self.e_c = self.emojis["c"]

        for role_select_msg in sortings.find({"title": {"$ne": "Quest Selection & Acceptance"}}, {"_id": 0}):
            self.msg_id_list.append(role_select_msg["msg_id"])


    def get_timestamp(self):
        return datetime.utcfromtimestamp(datetime.timestamp(datetime.now()))

    @commands.command(aliases=["patch"])
    @commands.check(check_if_user_has_any_admin_roles)
    async def post_patch_notes(self, ctx, arg1, *, args):

        guild = self.client.get_guild(int(id_guild))
        request = guilds.find_one({"server": str(guild.id)}, {"_id": 0, "channels": 1})
        headlines_id = request["channels"]["headlines"]
        headlines_channel = self.client.get_channel(int(headlines_id))

        link = f"https://pastebin.com/raw/{arg1}"
        f = urllib.request.urlopen(link)
        text = f.read().decode('utf-8')
        split_text = text.replace("\r", "\\n").split("\n")
        cap = 1500
        max_embeds = ceil(len(text) / cap)

        lines = 0
        lines_start = 0
        description_length = 0
        lines_end = len(split_text)

        for x in range(0, max_embeds):
            for entry in split_text[lines_start:lines_end]:
                description_length += len(entry)
                if description_length > cap:
                    break
                lines += 1

            description = "".join(split_text[lines_start:lines]).replace("\\n", "\n")
            lines_start = lines
            description_length = 0

            embed = discord.Embed(color=ctx.author.colour, description=description)
            if max_embeds - 1 == x:
                embed.set_image(url=args)

            await headlines_channel.send(embed=embed)
            await asyncio.sleep(1)

    @commands.command(aliases=["welcome"])
    @commands.check(check_if_user_has_any_admin_roles)
    async def edit_message_welcome(self, ctx):

        request = guilds.find_one({
            "server": f"{id_guild}"}, {
            "_id": 0,
            "channels": 1,
            "roles.patronus": 1,
            "messages": 1,
            "links": 1
        })

        welcome_id = request["channels"]["welcome"]
        sorting_id = request["channels"]["sorting-hat"]
        patronus_role_id = request["roles"]["seers"]
        absence_app_id = request["channels"]["absence-applications"]
        welcome_channel = self.client.get_channel(int(welcome_id))
        crest_link = request["links"]["crest"]
        rules_link = request["links"]["rules_link"]
        banners = request["links"]["banners"]

        embed1 = discord.Embed(
            colour=discord.Colour(0xe77eff),
            title="Welcome to House Patronus!",
            description="Herewith are the rules and information of our server!\n\n"
                        "Crest designed by <@!281223518103011340>"
        )
        embed1.set_thumbnail(url=crest_link)

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
            value="• Transformed members; Bots",
            inline=False
        )

        embed3 = discord.Embed(
            title="📋 Rules",
            colour=discord.Colour(0xf8e71c),
            description="• Useless and official warnings may be issued!\n​ "
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
            value="• For members as well as traders, min 90 weekly GQ\n"
                  "• Consistent inactivity will be forewarned by Head\n"
                  "• AQ is not the only option to fulfill GQs\n​ ",
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
            value="• Top 10 guild in overall activeness ranking\n"
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
            name="# 5. Absenteeism/Leave",
            value=f"• File your leave prior long vacation via <#{absence_app_id}> or contact any Head\n"
                  f"• Your maximum inactivity is assessed based on your guild retention/feats",
            inline=False
        )
        embed4.add_field(
            name="# 6. Shard Trading",
            value=f"• If leaving for shards, contact any Head & specify amount of days\n"
                  f"• If inviting a trader, notify a Head in advance\n"
                  f"• Traders are required to fulfill our minimum GQ requirements or they will be kicked\n​ ",
            inline=False
        )

        embed4.set_image(url=rules_link)

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
            url=banners[0]
        )
        embed6.set_footer(
            text="Assets: Official Onmyoji art; Designed by: xann#8194"
        )

        msg_intro = await welcome_channel.fetch_message(int(request["messages"]["intro"]))
        msg_roles = await welcome_channel.fetch_message(int(request["messages"]["roles"]))
        msg_rules = await welcome_channel.fetch_message(int(request["messages"]["rules"]))
        msg_benefits = await welcome_channel.fetch_message(int(request["messages"]["benefits"]))
        msg_events = await welcome_channel.fetch_message(int(request["messages"]["events"]))
        msg_banner = await welcome_channel.fetch_message(int(request["messages"]["banner"]))
        msg_invite = await welcome_channel.fetch_message(int(request["messages"]["invite"]))

        await msg_intro.edit(embed=embed1)
        await msg_roles.edit(embed=embed2)
        await msg_rules.edit(embed=embed3)
        await msg_benefits.edit(embed=embed4)
        await msg_events.edit(embed=embed5)
        await msg_banner.edit(embed=embed6)
        await msg_invite.edit(content="Our invite link: https://discord.gg/H6N8AHB")
        await ctx.message.delete()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):

        if self.client.get_user(int(payload.user_id)).bot:
            return

        request = guilds.find_one({
            "server": f"{id_guild}"}, {
            "_id": 0,
            "channels": 1,
            "messages": 1,
            "links": 1
        })

        msg_banner = request["messages"]["banner"]
        banners = request["links"]["banners"]

        if str(payload.message_id) == msg_banner and str(payload.emoji) in ["⬅", "➡"]:

            welcome_id = request["channels"]["welcome"]
            welcome_channel = self.client.get_channel(int(welcome_id))
            banner_msg = await welcome_channel.fetch_message(int(request["messages"]["banner"]))

            current_thumbnail = banner_msg.embeds[0].image.url
            current_index = banners.index(current_thumbnail)

            def get_new_banner(index):
                if str(payload.emoji) == "⬅":
                    new_index = index - 1
                    if index < 0:
                        return len(banners) - 1
                    else:
                        return new_index
                else:
                    new_index = index + 1
                    print(index)
                    if index >= len(banners) - 1:
                        return 0
                    else:
                        return new_index

            embed6 = discord.Embed(
                colour=discord.Colour(0xffd6ab),
                title="🎏 Banner"
            )
            embed6.set_image(
                url=banners[get_new_banner(current_index)]
            )
            embed6.set_footer(
                text="Assets: Official Onmyoji art; Designed by: xann#8194"
            )
            await banner_msg.edit(embed=embed6)

    @commands.command(aliases=["beasts"])
    @commands.check(check_if_user_has_any_admin_roles)
    async def edit_message_beasts_selection(self, ctx):

        guild_roles = ctx.guild.roles
        request = guilds.find_one({
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
            description="• Freely select your preferred Animagus form"
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

    @commands.command()
    @commands.is_owner()
    async def edit_message_quest_selection(self, ctx):

        request = guilds.find_one({
            "server": f"{ctx.guild.id}"}, {
            "_id": 0, "messages.quests": 1, "channels.sorting-hat": 1
        })

        sorting = self.client.get_channel(int(request["channels"]["sorting-hat"]))
        quests_msg = await sorting.fetch_message(int(request['messages']["quests"]))

        embed = discord.Embed(
            colour=discord.Colour(0xa661da),
            title="Quest Selection & Acceptance",
            description="Only when you finished your current quest, can make you able to restart a "
                        "new quest and have different outcome and score."
        )

        link = "https://discordapp.com/channels/412057028887052288/562671830331293716/599522202466910208"
        embed.add_field(
            name="🐬 Quest #1: Show us your Patronus!",
            value=f"Learn how to summon one. Refer to the quest mechanics [here!]({link})"
        )
        embed.add_field(
            name="🍵 Quest #2: Saving Fluffy Birb!",
            value=f"To be announced far from soon."
        )
        await quests_msg.edit(embed=embed)

    @commands.command(aliases=["special"])
    @commands.is_owner()
    async def edit_special_roles(self, ctx):

        request = guilds.find_one({
            "server": f"{ctx.guild.id}"}, {
            "_id": 0, "messages.special_roles": 1, "channels.sorting-hat": 1, "channels.co-op-team": 1
        })
        sorting_id = request["channels"]["sorting-hat"]
        coop_channel_id = request["channels"]["co-op-team"]
        special_roles_id = request["messages"]["special_roles"]
        sorting_channel = self.client.get_channel(int(sorting_id))

        embed = discord.Embed(
            colour=discord.Colour(0x50e3c2),
            title="Special Roles",
            description="Members can react to multiple roles below\nClearing your reaction removes the role"
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
            value=f"Mentionable role if you're looking for cooperative teams, use this at <#{coop_channel_id}>",
            inline=False
        )
        embed.add_field(
            name="🏁 Boss Busters",
            value="Mentionable role for fake rare boss assembly spawns, this is a dangerous role to acquire",
            inline=False
        )
        embed.add_field(
            name="⚾ Shard Seekers",
            value="Auto-pinged whenever people pin their shard list for trading",
            inline=False
        )
        embed.add_field(
            name="💿 Silver Sickles",
            value="Auto-pinged for Fortune Temple, Shrine, & Coin Chaos resets ending reminders",
            inline=False
        )
        embed.add_field(
            name="<:zzcoin:574965942912811016> Golden Galleons",
            value="Auto-pinged whenever a new round of showdown bidding has started or during Fortune Temple, Shrine, "
                  "& Coin Chaos resets, and a couple of other event ending reminders",
            inline=False
        )
        special_select_msg = await sorting_channel.fetch_message(int(special_roles_id))
        await special_select_msg.edit(embed=embed)
        await ctx.message.delete()

    @commands.command(aliases=["start"])
    @commands.is_owner()
    async def post_message_quest1(self, ctx):

        request = guilds.find_one({
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
            value=f"• Allow direct messages from our bot Miketsu to join. Try `{self.prefix}help dm`\n"
                  f"• Interested players can start by reacting at the <#{sorting.id}>\n"
                  f"• Hints will be available to use via `{self.prefix}hint`\n"
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
            value=f"• Two current guild members will win Nitro\n"
                  f"• The 1st one to ever complete a quest cycle with 999+ points; and\n"
                  f"• The 1st one to complete a quest cycle without moving a path\n​\n "
                  f"• Note: Commands `{self.prefix}progress` and `{self.prefix}cycle` "
                  f"are unlocked once your first cycle is finished\n\n​ "
                  f":four_leaf_clover: Good luck!​\n "
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
            name="🍵 Quest #2: Saving Fluffy Birb!",
            value=f"Quickly before it's too late. Refer to the quest mechanics [here!]({link})"
        )

        msg2 = await sorting.send(embed=embed)
        await msg2.add_reaction("🍵")

        guilds.update_one({
            "server": str(ctx.guild.id)}, {
            "$set": {
                "messages.quests.quest2": str(msg2.id)
            }}
        )
        await ctx.message.delete()

    @commands.command(aliases=["sorting"])
    @commands.is_owner()
    async def post_sorting_messages(self, ctx):

        request = guilds.find_one({
            "server": f"{id_guild}"}, {
            "_id": 0, "channels": 1
        })

        sorting_id = request["channels"]["sorting-hat"]
        sorting_channel = self.client.get_channel(int(sorting_id))

        guild = self.client.get_guild(int(id_guild))

        for document in sortings.find({}, {"_id": 0}):

            embed = discord.Embed(
                title=document["title"],
                description=document["description"].replace('\\n', '\n'),
                timestamp=self.get_timestamp(),
                color=document["color"]
            )

            members_count = []
            role_emojis = []
            for field in document["fields"]:

                role_id = field["role_id"]
                role = discord.utils.get(ctx.guild.roles, id=int(role_id))
                role_emojis.append(field["emoji"])
                count = len(role.members)
                members_count.append(count)

                if document["title"] != "Role Color Selection":
                    embed.add_field(
                        name=f"{field['emoji']} {field['role']} [{count}]",
                        value=f"{field['description']}"
                    )

                else:
                    embed.add_field(
                        name=f"{field['emoji']} {field['role']} [{count}]",
                        value="<@&{}>{}".format(field['role_id'], field['description'])
                    )

            if document["multiple"] is False:
                embed.set_footer(text=f"{sum(members_count)}/{len(guild.members)} sorted members")
            else:
                embed.set_footer(text=f"{sum(members_count)} special roles issued")

            query = sortings.find_one({"title": document["title"]}, {"_id": 0})
            msg = await sorting_channel.fetch_message(int(query["msg_id"]))

            emoji_existing = []
            for emoji1 in msg.reactions:
                emoji_existing.append(emoji1)

            for emoji2 in role_emojis:
                if emoji2 not in emoji_existing:
                    await msg.add_reaction(emoji2)

            await msg.edit(embed=embed)
            await asyncio.sleep(2)

        await ctx.message.delete()


def setup(client):
    client.add_cog(Embeds(client))
