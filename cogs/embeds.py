"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import discord
from discord.ext import commands

from cogs.mongo.db import books


class Embeds(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(aliases=["welcome"])
    @commands.is_owner()
    async def edit_message_welcome(self, ctx):

        request = books.find_one({
            "server": f"{ctx.guild.id}"}, {
            "_id": 0,
            "channels": 1,
            "roles.patronus": 1,
            "messages": 1
        })
        welcome_id = request["channels"]["welcome"]
        sorting_id = request["channels"]["sorting-hat"]
        patronus_role_id = request["roles"]["patronus"]
        welcome_channel = self.client.get_channel(int(welcome_id))

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

        introduction_msg = await welcome_channel.fetch_message(int(request["messages"]["introduction"]))
        roles_information_msg = await welcome_channel.fetch_message(int(request["messages"]["roles_information"]))
        rules_msg = await welcome_channel.fetch_message(int(request["messages"]["rules"]))
        requirements_msg = await welcome_channel.fetch_message(int(request["messages"]["requirements"]))
        events_schedule_msg = await welcome_channel.fetch_message(int(request["messages"]["events_schedule"]))
        banner_msg = await welcome_channel.fetch_message(int(request["messages"]["banner"]))
        invite_link_msg = await welcome_channel.fetch_message(int(request["messages"]["invite_link"]))

        await introduction_msg.edit(embed=embed1)
        await roles_information_msg.edit(embed=embed2)
        await rules_msg.edit(embed=embed3)
        await requirements_msg.edit(embed=embed4)
        await events_schedule_msg.edit(embed=embed5)
        await banner_msg.edit(embed=embed6)
        await invite_link_msg.edit(content="Our invite link: https://discord.gg/H6N8AHB")
        await ctx.message.delete()

    @commands.command(aliases=["beasts"])
    @commands.is_owner()
    async def edit_message_beasts_selection(self, ctx):

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

    @commands.command()
    @commands.is_owner()
    async def edit_message_quest_selection(self, ctx):

        request = books.find_one({
            "server": f"{ctx.guild.id}"}, {
            "_id": 0, "messages.quests": 1, "channels.sorting-hat": 1
        })

        sorting = self.client.get_channel(int(request["channels"]["sorting-hat"]))
        quests_msg = sorting.fetch_message(int(request['messages']["quests"]))

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

        request = books.find_one({
            "server": f"{ctx.guild.id}"}, {
            "_id": 0, "messages.special_roles": 1, "channels.sorting-hat": 1, "co-op-team": 1
        })
        sorting_id = request["channels"]["sorting-hat"]
        coop_channel_id = request["channels"]["co-op-team"]
        special_roles_id = request["channels"]["special_roles"]
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
            value="Auto-pinged whenever people post their shard list for trading",
            inline=False
        )
        embed.add_field(
            name="🎰 Big Spenders",
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
            name="🍵 Quest #2: Saving Fluffy Birb!",
            value=f"Quickly before it's too late. Refer to the quest mechanics [here!]({link})"
        )

        msg2 = await sorting.send(embed=embed)
        await msg2.add_reaction("🍵")

        books.update_one({
            "server": str(ctx.guild.id)}, {
            "$set": {
                "messages.quests.quest2": str(msg2.id)
            }}
        )
        await ctx.message.delete()


def setup(client):
    client.add_cog(Embeds(client))
