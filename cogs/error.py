"""
Error Module
Miketsu, 2020
"""

from discord.ext import commands

from cogs.ext.initialize import *


class Error(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.prefix = self.client.command_prefix

        self.functions_is_owner = [
            "changelog_add_line",
            "cogs_extension_initialize",
            "cogs_extension_load",
            "cogs_extension_reload",
            "cogs_extension_shutdown",
            "cogs_extension_unload",
            "compensate_economy_items",
            "compensate_increase_level",
            "compensate_increase_shikigami_level",
            "compensate_push_shikigami_manually",
            "edit_message_quest_selection",
            "edit_special_roles",
            "manual_process_achievements_daily",
            "manual_process_achievements_hourly",
            "manual_process_frames_daily",
            "post_message_quest1",
            "post_sorting_messages",
            "realm_card_add",
        ]

        self.functions_ignore_check = [
            "edit_special_roles"
            "encounter_add_quiz",
            "events_manipulate",
            "management_guild",
            "perform_reset",
            "post_memorandum",
            "post_message_user",
            "purge_messages",
        ]
    
    async def submit_error(self, ctx, error, exception):

        record_scroll = self.client.get_channel(int(id_scroll))

        embed = discord.Embed(
            colour=colour,
            title=f"Command Error Report",
            timestamp=get_timestamp()
        )
        embed.add_field(name=f"function call: {ctx.command} | {exception}", value=error, inline=False)

        try:
            link = f"https://discordapp.com/channels/{ctx.message.guild.id}/{ctx.message.channel.id}/{ctx.message.id}"
            embed.add_field(
                name=f"Error Traceback",
                value=f"User | Channel | Source :: {ctx.author} | #{ctx.channel} | [message link]({link})",
                inline=False
            )
            await record_scroll.send(embed=embed)

        except AttributeError:
            embed.add_field(
                name=f"Error Traceback",
                value=f"User | DMchannel :: {ctx.author} | #{ctx.channel}\n",
                inline=False
            )
            await record_scroll.send(embed=embed)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):

        if isinstance(error, commands.MissingRequiredArgument):

            if str(ctx.command) == "raid_perform":
                embed = discord.Embed(
                    title="raid, r", colour=colour,
                    description="raids the tagged member, requires 1 🎟"
                )
                embed.add_field(
                    name="Formats",
                    value=f"*`{self.prefix}raid @member`*\n"
                          f"*`{self.prefix}r <name#discriminator>`*",
                    inline=False
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif str(ctx.command) == "raid_perform":
                embed = discord.Embed(
                    title="raid, r", colour=colour,
                    description="raids the tagged member, requires 1 🎟"
                )
                embed.add_field(
                    name="Formats",
                    value=f"*`{self.prefix}raid @member`*\n"
                          f"*`{self.prefix}r <name#discriminator>`*",
                    inline=False
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif str(ctx.command) == "shikigami_list_show_collected":
                embed = discord.Embed(
                    title="shikilist, sl", colour=colour,
                    description="shows your shikigami listings by rarity "
                )
                embed.add_field(
                    name="Formats",
                    value=f"*`{self.prefix}shikilist <rarity>`*",
                    inline=False
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif str(ctx.command) == "shikigami_show_post_shiki":
                embed = discord.Embed(
                    title="shikigami, shiki", colour=colour,
                    description="shows your shikigami profile stats"
                )
                embed.add_field(
                    name="Formats",
                    value=f"*`{self.prefix}shikigami <shikigami>`*",
                    inline=False
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif str(ctx.command) == "raid_perform_calculation":
                embed = discord.Embed(
                    title="raidcalc, raidc, rc", colour=colour,
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
                await process_msg_submit(ctx.channel, None, embed)

            elif str(ctx.command) == "post_memorandum":
                embed = discord.Embed(
                    title="memo",
                    colour=colour,
                    description="submit an official paperwork memo"
                )
                embed.add_field(
                    name="Format", value=f"*`{self.prefix}memo <#channel>`*",
                    inline=False
                )
                embed.add_field(
                    name="Notes",
                    value=f"follow the step by step procedure\n"
                          f"enter any non-image link text to remove the memorandum's embedded image",
                    inline=False
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif str(ctx.command) == "suggestions_collect":
                embed = discord.Embed(
                    title="suggest, report",
                    colour=colour,
                    description="submit suggestions/reports for the bot or guild\n"
                                "available to use through direct message"
                )
                embed.add_field(
                    name="Example", value=f"*`{self.prefix}suggest add new in-game stickers!`*",
                    inline=False
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif str(ctx.command) in ["perform_exploration"]:
                embed = discord.Embed(
                    title="explore, exp",
                    colour=colour,
                    description=f"explore unlocked chapters\n"
                                f"consumes sushi, set a shikigami first via `{self.prefix}set`\n"
                )
                embed.add_field(
                    name="Clear chance parameters",
                    value="Onmyoji, shikigami, and chapter level, shikigami evolution",
                    inline=False
                )
                embed.add_field(
                    name="Formats",
                    value=f"*`{self.prefix}exp <unlocked chapter#>`*\n"
                          f"*`{self.prefix}explore <last | unfinished | unf>`*\n",
                    inline=False
                )
                await process_msg_submit(ctx.channel, None, embed)
                self.client.get_command("perform_exploration").reset_cooldown(ctx)

            elif str(ctx.command) == "stat_shikigami":
                embed = discord.Embed(
                    title="stats",
                    colour=colour,
                    description="shows shikigami pulls statistics"
                )
                embed.add_field(name="Example", value=f"*`{self.prefix}stat tamamonomae`*", inline=False)
                await process_msg_submit(ctx.channel, None, embed)

            elif str(ctx.command) == "sticker_add_new":
                embed = discord.Embed(
                    title="newsticker, ns",
                    colour=colour,
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
                await process_msg_submit(ctx.channel, None, embed)

            elif str(ctx.command) == "shikigami_shrine":
                embed = discord.Embed(
                    title="shrine", colour=colour,
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
                await process_msg_submit(ctx.channel, None, embed)

            elif str(ctx.command) == "leaderboard_show":
                embed = discord.Embed(
                    title="leaderboard, lb", colour=colour,
                    description="shows various leaderboards"
                )
                embed.add_field(
                    name="Arguments",
                    value=f"*SP, SSR, SR, SSN, level, medals, amulets, friendship, ships, streak, frames*",
                    inline=False
                )
                embed.add_field(name="Example", value=f"*`{self.prefix}leaderboard friendship`*", inline=False)
                await process_msg_submit(ctx.channel, None, embed)

            elif str(ctx.command) in [
                "shikigami_image_show_collected"
            ]:
                embed = discord.Embed(
                    title="collection, col", colour=colour,
                    description="shows your or tagged member's shikigami pulls by rarity without the count"
                )
                embed.add_field(
                    name="Format", inline=False,
                    value=f"*`{self.prefix}collection <rarity> <optional: @member>`*"
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif str(ctx.command) in [
                "shikigami_show_post_shiki"
            ]:
                embed = discord.Embed(
                    title="shikigami, shiki", colour=colour,
                    description="shows your owned shikigami stats"
                )
                embed.add_field(
                    name="Format", inline=False,
                    value=f"*`{self.prefix}shiki <shikigami>`*"
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif str(ctx.command) in [
                "shikigami_show_post_shikis"
            ]:
                embed = discord.Embed(
                    title="shikigamis, shikis", colour=colour,
                    description="shows your or tagged member's shikigami pulls by rarity"
                )
                embed.add_field(
                    name="Format", inline=False,
                    value=f"*`{self.prefix}shikis <rarity> <optional: @member>`*"
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif str(ctx.command) in ["shikigami_show_post_shards"]:
                embed = discord.Embed(
                    title="shards", colour=colour,
                    description="shows your or tagged member's shikigami shards count by rarity"
                )
                embed.add_field(
                    name="Format", inline=False,
                    value=f"*`{self.prefix}shards <rarity> <optional: @member>`*"
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif str(ctx.command) == "profile_change_shikigami_main":
                embed = discord.Embed(
                    title="display", colour=colour,
                    description="changes your profile display thumbnail"
                )
                embed.add_field(name="Example", value=f"*`{self.prefix}set inferno ibaraki`*", inline=False)
                await process_msg_submit(ctx.channel, None, embed)

            elif str(ctx.command) == "summon_perform_mystery":
                embed = discord.Embed(
                    title="summon, s", colour=colour,
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
                await process_msg_submit(ctx.channel, None, embed)

            elif str(ctx.command) in [
                "bounty_query",
                "bounty_add_location",
                "bounty_add_alias"
            ]:
                embed = discord.Embed(
                    title="bounty, b",
                    colour=colour,
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
                await process_msg_submit(ctx.channel, None, embed)

            elif str(ctx.command) == "castle_portrait_customize":
                embed = discord.Embed(
                    title="portrait, portraits", colour=colour,
                    description=f"customize your own guild portrait\n"
                                f"appears in the castle's floors via `{self.prefix}wander`"
                )
                embed.add_field(
                    name="Example",
                    value=f"*`;portraits`*\n"
                          f"*`{self.prefix}portrait <edit/add>`*",
                    inline=False
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif str(ctx.command) == "post_memorandum":
                embed = discord.Embed(
                    title="announce", colour=colour,
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
                await process_msg_submit(ctx.channel, None, embed)

            elif str(ctx.command) == "post_message_channel":
                embed = discord.Embed(
                    colour=colour,
                    title="say",
                    description="allows me to repeat a text message"
                )
                embed.add_field(name="Format", value=f"*`{self.prefix}say <#channel or channel_id> <any message>`*")
                await process_msg_submit(ctx.channel, None, embed)

            elif str(ctx.command) == "post_message_user":
                embed = discord.Embed(
                    colour=colour,
                    title="dm",
                    description="allows me to message a user"
                )
                embed.add_field(name="Format", value=f"*`{self.prefix}dm <@member or member_id> <any message>`*")
                await process_msg_submit(ctx.channel, None, embed)

            elif str(ctx.command) == "show_cycle_quest1":
                embed = discord.Embed(
                    colour=colour,
                    title="cycle",
                    description="Patronus quest command participants only"
                )
                embed.add_field(
                    name="Format", value=f"*`{self.prefix}cycle <cycle#1> <optional: @member>`*"
                )
                embed.add_field(name="Example", value=f"*`{self.prefix}cycle 1`*")
                await process_msg_submit(ctx.channel, None, embed)

            elif str(ctx.command) == "post_book_reference":
                await process_msg_reaction_add(ctx.message, "❌")

            elif str(ctx.command) in ["post_patch_notes"]:
                await process_msg_reaction_add(ctx.message, "❌")

            else:
                await self.submit_error(ctx, error, "MissingRequiredArgument")

        elif isinstance(error, commands.UserInputError):

            if str(ctx.command) in [
                "wish_grant",
                "friendship_change_name",
                "friendship_check_sail"
            ]:
                return

            elif str(ctx.command) in ["post_memorandum "]:
                embed = discord.Embed(
                    colour=colour,
                    title="Invalid input",
                    description="tag a valid channel"
                )
                await process_msg_submit(ctx.channel, None, embed)

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
                    "perform_exploration_check_clears",
                    "friendship_check_sail",
                    "shikigami_show_post_shikis",
                    "realm_card_use"
                ]:
                    embed = discord.Embed(
                        title="Invalid member", colour=colour,
                        description="That member does not exist or does not have a profile in this guild"
                    )
                    await process_msg_submit(ctx.channel, None, embed)

                else:
                    await self.submit_error(ctx, error, "BadArgument")

            else:
                await self.submit_error(ctx, error, "UserInputError")

        elif isinstance(error, commands.CheckFailure):

            if str(ctx.command) in self.functions_is_owner:
                return

            elif str(ctx.command) == "pray_use":
                embed = discord.Embed(
                    colour=colour,
                    title=f"Insufficient prayers",
                    description=f"You have used up all your prayers today 🙏",
                    timestamp=get_timestamp()
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif str(ctx.command) == "raid_perform":
                embed = discord.Embed(
                    title=f"Insufficient realm tickets", colour=colour,
                    description="purchase at the shop or get your daily rewards"
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif str(ctx.command) == "perform_parade":
                embed = discord.Embed(
                    title="Insufficient parade tickets", colour=colour,
                    description=f"{ctx.author.mention}, claim your dailies to acquire tickets"
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif str(ctx.command) == "encounter_search":
                embed = discord.Embed(
                    colour=ctx.author.colour,
                    title="Insufficient tickets",
                    description=f"purchase at the shop to obtain more"
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif str(ctx.command) == "post_message_user":
                embed = discord.Embed(
                    colour=ctx.author.colour,
                    description=f"Missing required roles"
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif str(ctx.command) == "castle_wander":
                embed = discord.Embed(
                    title="wander, w",
                    colour=colour,
                    description="usable only at the castle's channels with valid floors\n"
                                "check the channel topics for the floor number\n"
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif str(ctx.command) in ["perform_exploration"]:
                embed = discord.Embed(
                    title="explore, exp",
                    colour=colour,
                    description=f"explore unlocked chapters\n"
                                f"requires sushi, set a shikigami first via `{self.prefix}set`\n"
                )
                embed.add_field(
                    name="Clear chance parameters",
                    value="Onmyoji, shikigami, and chapter level, shikigami evolution",
                    inline=False
                )
                embed.add_field(
                    name="Formats",
                    value=f"*`{self.prefix}exp <unlocked chapter#>`*\n"
                          f"*`{self.prefix}explore <last | unfinished | unf>`*\n",
                    inline=False
                )
                await process_msg_submit(ctx.channel, None, embed)
                self.client.get_command("perform_exploration").reset_cooldown(ctx)

            elif isinstance(error, commands.NoPrivateMessage):
                embed = discord.Embed(
                    title="Invalid channel", colour=colour,
                    description="This command can only be used inside the guild"
                )
                await process_msg_submit(ctx.channel, None, embed)

            else:
                await self.submit_error(ctx, error, "CheckFailure")

        elif isinstance(error, commands.CommandOnCooldown):

            if str(ctx.command) in [
                "encounter_search",
                "summon_perform_mystery",
                "friendship_give",
                "perform_parade",
                "pray_use",
                "perform_exploration",
                "summon_perform_broken",
                "shikigami_shrine"
            ]:
                return

            if str(ctx.command) == "sushi_bento_serve":

                role = guilds.find_one({"server": str(id_guild)}, {
                    "_id": 0, "roles.sushchefs": 1
                })["roles"]["sushchefs"]

                embed = discord.Embed(
                    title="sushi, food, hungry, ap",
                    colour=colour,
                    description=f"request for hourly free food servings\n"
                                f"pings the <@&{role}> role"
                )
                embed.add_field(
                    name="Next serving",
                    value=f"In {int(error.retry_after / 60)} {pluralize('minute', int(error.retry_after / 60))}"
                )
                await process_msg_submit(ctx.channel, None, embed)

            else:
                await self.submit_error(ctx, error, "CommandOnCooldown")

        elif isinstance(error, commands.CommandNotFound):

            if isinstance(ctx.channel, discord.DMChannel):

                embed = discord.Embed(
                    title="Invalid channel",
                    colour=colour,
                    description=f"Certain commands are not available through direct message channels.\n"
                                f"Use them at the <#{id_spell_spam}>"
                )
                await ctx.author.send(embed=embed)

        elif isinstance(error, commands.CommandInvokeError):

            if str(ctx.command) == "post_message_channel":
                embed = discord.Embed(
                    title="Invalid syntax", colour=colour,
                    description="Provide a valid channel"
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif str(ctx.command) == "post_message_user":
                embed = discord.Embed(
                    title="Invalid syntax", colour=colour,
                    description="Provide a valid member ID or tag them"
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif str(ctx.command) in [
                "perform_parade",
                "sushi_bento_serve",
                "raid_perform"
            ]:
                return

            else:
                await self.submit_error(ctx, error, "CommandInvokeError")

        elif isinstance(error, commands.NotOwner):
            await self.submit_error(ctx, error, "NotOwner")

        elif isinstance(error, commands.ExtensionError):
            await self.submit_error(ctx, error, "ExtensionError")

        else:
            await self.submit_error(ctx, error, None)


def setup(client):
    client.add_cog(Error(client))
