"""
Error Module
Miketsu, 2019
"""

from datetime import datetime

import discord
from discord.ext import commands

from cogs.mongo.database import get_collections
from cogs.startup import embed_color, guild_id

# Collections
guilds = get_collections("guilds")

# Variables
spell_spam_id = guilds.find_one({"server": str(guild_id)}, {"_id": 0, "channels": 1})["channels"]["spell-spam"]
scroll_id = guilds.find_one({"server": str(guild_id)}, {"_id": 0, "channels": 1})["channels"]["scroll-of-everything"]


def get_timestamp():
    return datetime.utcfromtimestamp(datetime.timestamp(datetime.now()))


class Error(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.prefix = self.client.command_prefix

    async def submit_error(self, ctx, error):

        channel = self.client.get_channel(int(scroll_id))

        embed = discord.Embed(
            colour=discord.Colour(embed_color),
            title=f"Command Error Report",
            timestamp=get_timestamp()
        )
        embed.add_field(name=f"function call: {ctx.command}", value=error, inline=False)

        try:
            link = f"https://discordapp.com/channels/{ctx.message.guild.id}/{ctx.message.channel.id}/{ctx.message.id}"
            embed.add_field(
                name=f"Error Traceback",
                value=f"User | Channel | Source :: {ctx.author} | #{ctx.channel} | [message link]({link})",
                inline=False
            )
            await channel.send(embed=embed)

        except AttributeError:
            embed.add_field(
                name=f"Error Traceback",
                value=f"User | DMchannel :: {ctx.author} | #{ctx.channel}\n",
                inline=False
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):

        if isinstance(error, commands.CheckFailure):

            if str(ctx.command) == "pray_use":
                embed = discord.Embed(
                    colour=embed_color,
                    title=f"Insufficient prayers",
                    description=f"You have used up all your prayers today 🙏",
                    timestamp=get_timestamp()
                )
                await ctx.channel.send(embed=embed)

            elif str(ctx.command) == "raid_perform":
                embed = discord.Embed(
                    title=f"Insufficient realm tickets", colour=discord.Colour(embed_color),
                    description="purchase at the shop or get your daily rewards"
                )
                await ctx.channel.send(embed=embed)

            elif str(ctx.command) == "perform_parade":
                embed = discord.Embed(
                    title="Insufficient parade tickets", colour=discord.Colour(embed_color),
                    description=f"{ctx.author.mention}, claim your dailies to acquire tickets"
                )
                await ctx.channel.send(embed=embed)

            elif str(ctx.command) == "encounter_search":
                embed = discord.Embed(
                    colour=ctx.author.colour,
                    title="Insufficient tickets",
                    description=f"purchase at the shop to obtain more"
                )
                await ctx.channel.send(embed=embed)

            elif str(ctx.command) == "announcement_post_message":
                embed = discord.Embed(
                    colour=ctx.author.colour,
                    description=f"Missing required roles"
                )
                await ctx.channel.send(embed=embed)

            elif str(ctx.command) == "castle_wander":
                embed = discord.Embed(
                    title="wander, w",
                    colour=discord.Colour(embed_color),
                    description="usable only at the castle's channels with valid floors\n"
                                "check the channel topics for the floor number\n"
                )
                await ctx.channel.send(embed=embed)

            elif str(ctx.command) in ["perform_exploration"]:
                embed = discord.Embed(
                    title="explore, exp",
                    colour=discord.Colour(embed_color),
                    description=f"explore unlocked chapters\n"
                                f"consumes sushi, set a shikigami first `{self.prefix}set`\n"
                                f"clear success:  `Onmoyji level + shikigami level - chapter level`"
                )
                embed.add_field(
                    name="Format",
                    value=f"*`{self.prefix}exp <unlocked chapter#>`*\n"
                          f"*`{self.prefix}explore unlocked`*\n",
                    inline=False
                )
                await ctx.channel.send(embed=embed)
                self.client.get_command("perform_exploration").reset_cooldown(ctx)

            elif str(ctx.command) in ["management_guild", "encounter_add_quiz"]:
                return

            elif isinstance(error, commands.NoPrivateMessage):
                embed = discord.Embed(
                    title="Invalid channel", colour=discord.Colour(embed_color),
                    description="This command can only be used inside the guild"
                )
                await ctx.channel.send(embed=embed)

            else:
                await self.submit_error(ctx, error)

        elif isinstance(error, commands.CommandOnCooldown):

            if str(ctx.command) in [
                "encounter_search",
                "summon_perform_mystery",
                "friendship_give",
                "perform_parade",
                "pray_use",
                "perform_exploration"
            ]:
                return

            else:
                await self.submit_error(ctx, error)

        elif isinstance(error, commands.MissingRequiredArgument):

            if str(ctx.command) == "raid_perform":
                embed = discord.Embed(
                    title="raid, r", colour=discord.Colour(embed_color),
                    description="raids the tagged member, requires 1 🎟"
                )
                embed.add_field(
                    name="Formats",
                    value=f"*`{self.prefix}raid @member`*\n"
                          f"*`{self.prefix}r <name#discriminator>`*",
                    inline=False
                )
                await ctx.channel.send(embed=embed)

            elif str(ctx.command) == "raid_perform_calculation":
                embed = discord.Embed(
                    title="raidcalc, raidc, rc", colour=discord.Colour(embed_color),
                    description="calculates your odds of winning"
                )
                embed.add_field(
                    name="Mechanics",
                    value="```"
                          "Base Chance :: + 50 %\n"
                          "Δ Level     :: ± 15 %\n"
                          "Δ Medal     :: ± 15 %\n"
                          "Δ SP        :: ±  9 %\n"
                          "Δ SSR       :: ±  7 %\n"
                          "Δ SR        :: ±  3 %\n"
                          "Δ R         :: ±  1 %\n"
                          "```",
                    inline=False
                )
                embed.add_field(
                    name="Formats",
                    value=f"*`{self.prefix}raidc @member`*\n"
                          f"*`{self.prefix}rc <name#discriminator>`*",
                    inline=False
                )
                await ctx.channel.send(embed=embed)

            elif str(ctx.command) == "announcement_post_memorandum":
                embed = discord.Embed(
                    title="memo",
                    colour=discord.Colour(embed_color),
                    description="submit an official paperwork memo"
                )
                embed.add_field(
                    name="Format", value=f"*`{self.prefix}memo <#channel>`*",
                    inline=False
                )
                embed.add_field(
                    name="Notes", value=f"follow the step by step procedure\n"
                                        f"enter any non-image link text to remove the memorandum's embedded image",
                    inline=False
                )
                await ctx.channel.send(embed=embed)

            elif str(ctx.command) == "collect_suggestions":
                embed = discord.Embed(
                    title="suggest, report",
                    colour=discord.Colour(embed_color),
                    description="submit suggestions/reports for the bot or guild\n"
                                "available to use through direct message"
                )
                embed.add_field(
                    name="Example", value=f"*`{self.prefix}suggest add new in-game stickers!`*",
                    inline=False
                )
                await ctx.channel.send(embed=embed)

            elif str(ctx.command) in ["perform_exploration"]:
                embed = discord.Embed(
                    title="explore, exp",
                    colour=discord.Colour(embed_color),
                    description=f"explore unlocked chapters\n"
                                f"consumes sushi, set a shikigami first `{self.prefix}set`\n"
                                f"clear success:  `Onmoyji level + shikigami level - chapter level`"
                )
                embed.add_field(
                    name="Format",
                    value=f"*`{self.prefix}exp <unlocked chapter#>`*\n"
                          f"*`{self.prefix}explore unlocked`*\n",
                    inline=False
                )
                await ctx.channel.send(embed=embed)
                self.client.get_command("perform_exploration").reset_cooldown(ctx)

            elif str(ctx.command) == "stat_shikigami":
                embed = discord.Embed(
                    title="stats",
                    colour=discord.Colour(embed_color),
                    description="shows shikigami pulls statistics"
                )
                embed.add_field(name="Example", value=f"*`{self.prefix}stat tamamonomae`*", inline=False)
                await ctx.channel.send(embed=embed)

            elif str(ctx.command) == "sticker_add_new":
                embed = discord.Embed(
                    title="newsticker, ns",
                    colour=discord.Colour(embed_color),
                    description="add new stickers in the database"
                )
                embed.add_field(
                    name="Format",
                    value=f"*`{self.prefix}ns <alias> <imgur link and png images only>`*",
                    inline=False
                )
                embed.add_field(
                    name="Example",
                    value=f"*`{self.prefix}ns feelinhurt https://i.imgur.com/371bCEa.png`*",
                    inline=False
                )
                await ctx.channel.send(embed=embed)

            elif str(ctx.command) == "shrine_shikigami":
                embed = discord.Embed(
                    title="shrine", colour=discord.Colour(embed_color),
                    description="exchange your shikigamis for talismans to acquire exclusive shikigamis"
                )
                embed.add_field(
                    name="Arguments",
                    value=f"*sacrifice, exchange*",
                    inline=False
                )
                embed.add_field(
                    name="Example",
                    value=f"*`{self.prefix}shrine exchange`*",
                    inline=False
                )
                await ctx.channel.send(embed=embed)

            elif str(ctx.command) == "leaderboard_show":
                embed = discord.Embed(
                    title="leaderboard, lb", colour=discord.Colour(embed_color),
                    description="shows various leaderboards"
                )
                embed.add_field(
                    name="Arguments",
                    value=f"*SP, SSR, SR, level, medals, amulets, friendship, ships, streak, frames*",
                    inline=False
                )
                embed.add_field(name="Example", value=f"*`{self.prefix}leaderboard friendship`*", inline=False)
                await ctx.channel.send(embed=embed)

            elif str(ctx.command) in [
                "shikigami_list_show_collected", "shikigami_image_show_collected"
            ]:
                embed = discord.Embed(
                    title="shikigamis, shikis, collections, col", colour=discord.Colour(embed_color),
                    description="shows your or tagged member's shikigami pulls by rarity"
                )
                embed.add_field(
                    name="Format", inline=False,
                    value=f"*`{self.prefix}shikis <rarity> <optional: @member>`*\n"
                          f"*`{self.prefix}unc <rarity> <optional: @member>`*"
                )
                await ctx.channel.send(embed=embed)

            elif str(ctx.command) in ["shikigami_show_post_shards"]:
                embed = discord.Embed(
                    title="shards", colour=discord.Colour(embed_color),
                    description="shows your or tagged member's shikigami shards count by rarity"
                )
                embed.add_field(
                    name="Format", inline=False,
                    value=f"*`{self.prefix}shards <rarity> <optional: @member>`*"
                )
                await ctx.channel.send(embed=embed)

            elif str(ctx.command) == "profile_change_shikigami_main":
                embed = discord.Embed(
                    title="display", colour=discord.Colour(embed_color),
                    description="changes your profile display thumbnail"
                )
                embed.add_field(name="Example", value=f"*`{self.prefix}set inferno ibaraki`*", inline=False)
                await ctx.channel.send(embed=embed)

            elif str(ctx.command) == "summon_perform_mystery":
                embed = discord.Embed(
                    title="summon, s", colour=discord.Colour(embed_color),
                    description="simulates summon and collect shikigamis"
                )
                embed.add_field(
                    name="Shard Requirement",
                    value=f"```"
                          "SP    ::   15\n"
                          "SSR   ::   12\n"
                          "SR    ::    9\n"
                          "R     ::    6\n"
                          "N     ::    3\n"
                          "SSN   ::   12\n"
                          "```",
                    inline=False
                )
                embed.add_field(
                    name="Formats",
                    value=f"*`{self.prefix}summon <shikigami>`*\n"
                          f"*`{self.prefix}sb`*\n"
                          f"*`{self.prefix}sm <1 or 10>`*\n",
                    inline=False
                )
                await ctx.channel.send(embed=embed)

            elif str(ctx.command) in ["bounty_query", "bounty_add_location", "bounty_add_alias"]:
                embed = discord.Embed(
                    title="bounty, b",
                    colour=discord.Colour(embed_color),
                    description="search shikigami bounty locations or modify them"
                )
                embed.add_field(
                    name="Format",
                    value=f"*"
                          f"`{self.prefix}bounty <shikigami>`\n"
                          f"`{self.prefix}baa <shikigami_name> <new alias/keyword>`\n"
                          f"`{self.prefix}bal <shikigami_name> <new location>`"
                          f"*",
                    inline=False
                )
                await ctx.channel.send(embed=embed)

            elif str(ctx.command) == "post_book_reference":
                await ctx.message.add_reaction("❌")

            elif str(ctx.command) == "castle_portrait_customize":
                embed = discord.Embed(
                    title="portrait, portraits", colour=discord.Colour(embed_color),
                    description=f"customize your own guild portrait\n"
                                f"appears in the castle's floors via `{self.prefix}wander`"
                )
                embed.add_field(
                    name="Example",
                    value=f"*`;portraits`*\n"
                          f"*`{self.prefix}portrait <edit/add>`*",
                    inline=False
                )
                await ctx.channel.send(embed=embed)

            elif str(ctx.command) == "announcement_post_memorandum":
                embed = discord.Embed(
                    title="announce", colour=discord.Colour(embed_color),
                    description="sends an embed message\n"
                                "prioritization: description > title > img_link\n"
                                "where title and img_link are optional"
                )
                embed.add_field(
                    name="Format",
                    value=f"*`{self.prefix}announce <#channel> <title>|<description>|<img_link>`*"
                )
                embed.add_field(
                    name="Example",
                    value=f"*`{self.prefix}announce #headlines @Patronus reminder to...`*",
                    inline=False
                )
                await ctx.channel.send(embed=embed)

            elif str(ctx.command) == "announcement_post_message":
                embed = discord.Embed(
                    colour=discord.Colour(embed_color),
                    title="say",
                    description="allows me to repeat a text message"
                )
                embed.add_field(name="Format", value=f"*`{self.prefix}say <#channel or channel_id> <any message>`*")
                await ctx.channel.send(embed=embed)

            elif str(ctx.command) == "show_cycle_quest1":
                embed = discord.Embed(
                    colour=discord.Colour(embed_color),
                    title="cycle",
                    description="Patronus quest command participants only"
                )
                embed.add_field(
                    name="Format", value=f"*`{self.prefix}cycle <cycle#1> <optional: @member>`*"
                )
                embed.add_field(name="Example", value=f"*`{self.prefix}cycle 1`*")
                await ctx.channel.send(embed=embed)

            elif str(ctx.command) in ["post_patch_notes"]:
                await ctx.message.add_reaction("❌")

            else:
                await self.submit_error(ctx, error)

        elif isinstance(error, commands.CommandNotFound):

            if isinstance(ctx.channel, discord.DMChannel):

                embed = discord.Embed(
                    title="Invalid channel",
                    colour=discord.Colour(embed_color),
                    description=f"Certain commands are not available through direct message channels.\n"
                                f"Use them at the <#{spell_spam_id}>"
                )
                await ctx.author.send(embed=embed)

        elif isinstance(error, commands.BadArgument):

            if str(ctx.command) in [
                "raid_perform",
                "raid_perform_calculation",
                "profile_show",
                "friendship_give",
                "wish_grant",
                "friendship_change_name",
                "friendship_ship",
                "shikigami_list_show_collected",
                "logs_show",
                "perform_exploration_check_clears"
            ]:
                embed = discord.Embed(
                    title="Invalid member", colour=discord.Colour(embed_color),
                    description="That member does not exist or does not have a profile in this guild"
                )
                await ctx.channel.send(embed=embed)

            else:
                await self.submit_error(ctx, error)

        elif isinstance(error, commands.CommandInvokeError):

            if str(ctx.command) == "announcement_post_message":
                embed = discord.Embed(
                    title="Invalid syntax", colour=discord.Colour(embed_color),
                    description="Provide a valid channel"
                )
                await ctx.channel.send(embed=embed)

            else:
                await self.submit_error(ctx, error)

        elif isinstance(error, commands.NotOwner):
            await self.submit_error(ctx, error)

        elif isinstance(error, commands.UserInputError):
            await self.submit_error(ctx, error)

        elif isinstance(error, commands.ExtensionError):
            await self.submit_error(ctx, error)

        else:
            await self.submit_error(ctx, error)


def setup(client):
    client.add_cog(Error(client))
