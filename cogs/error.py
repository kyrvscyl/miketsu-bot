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
            "development_perform_reset",
            "development_shikigami_add",
            "development_compensate_items",
            "development_compensate_increase_level_user",
            "development_compensate_increase_level_shikigami",
            "development_compensate_push_shikigami",
            "development_manual_achievements_process_daily",
            "development_manual_achievements_process_hourly",
            "development_manual_frame_automate",
            "edit_message_quest_selection",
            "edit_special_roles",
            "post_message_quest1",
            "roles_post_sorting_messages",
            "realm_card_add",
            "development_perform_reset",
            "embeds_welcome_edit",
            "roles_post_sorting_messages"
        ]

        self.functions_admin = [
            "admin_post_patch_notes",
            "admin_post_memorandum",
            "admin_post_message_textchannel",
            "admin_post_message_user",
            "admin_purge_messages",
            "admin_manage_guild",
            "clock_start_manual"
        ]

        self.functions_guild_only = [
            "admin_manage_guild",
            "admin_post_memorandum",
            "admin_post_message_textchannel",
            "admin_post_message_user",
            "admin_post_patch_notes",
            "admin_purge_messages",
            "castle_duel",
            "castle_portrait_show_all",
            "castle_portraits_customize",
            "castle_portraits_wander",
            "castle_post_guides",
            "castle_post_guides_book_open",
            "changelog_show",
            "clock_start_manual",
            "economy_claim_rewards_daily",
            "economy_claim_rewards_weekly",
            "economy_logs_show",
            "economy_perform_parade",
            "economy_pray_use",
            "economy_profile_show",
            "economy_shop_buy_items",
            "economy_shop_buy_items_show_all",
            "economy_stat_shikigami",
            "economy_sushi_bento",
            "economy_sushi_bento_serve",
            "economy_wish_fulfill",
            "economy_wish_perform",
            "economy_wish_show_list",
            "enc_boss_stats",
            "enc_nether_info",
            "enc_roll",
            "expecto_patronus_show",
            "expecto_show_cycle",
            "expecto_transact_emporium"
            "exploration_check_clears",
            "exploration_process",
            "exploration_zones",
            "frames_add_new",
            "frames_show_information",
            "friendship_change_name",
            "friendship_check_sail",
            "friendship_give",
            "friendship_ship_show_all",
            "friendship_ship_show_one",
            "funfun_sticker_add_new",
            "funfun_stickers_help",
            "leaderboard_show",
            "profile_change_shikigami",
            "raid_perform",
            "raid_perform_calculation",
            "raid_perform_check_users",
            "realm_card_collect",
            "realm_card_show_all",
            "realm_card_show_user",
            "realm_card_use",
            "shikigami_bounty_add_alias",
            "shikigami_bounty_add_location",
            "shikigami_bounty_query",
            "shikigami_image_show_collected",
            "shikigami_list_show_collected",
            "shikigami_show_post_shards",
            "shikigami_show_post_shiki",
            "shikigami_show_post_shikis",
            "shikigami_shrine",
            "souls_process",
            "summon_perform",
        ]

        self.functions_with_cooldown = [
            "economy_perform_parade",
            "economy_pray_use",
            "economy_sushi_bento_serve",
            "enc_roll",
            "exploration_process",
            "friendship_give",
            "shikigami_shrine",
        ]

        self.functions_development = [
            "development_shikigami_add",
            "frames_add_new",
            "expecto_patronus_show"
        ]

        self.functions_member_tagging = [
            "development_compensate_increase_level_shikigami",
            "development_compensate_increase_level_user",
            "development_compensate_items",
            "development_compensate_push_shikigami",
            "economy_logs_show",
            "economy_profile_show",
            "economy_wish_fulfill",
            "exploration_check_clears",
            "exploration_check_clears",
            "friendship_check_sail",
            "friendship_check_sail",
            "friendship_ship_show_all",
            "raid_perform",
            "realm_card_collect",
            "realm_card_show_user"
            "realm_card_use",
            "shikigami_image_show_collected",
            "shikigami_list_show_collected",
            "shikigami_show_post_shards",
            "shikigami_show_post_shikis"
            "shikigami_show_post_shikis",
        ]

        self.functions_role_only = [
            "hint_request",
            "expecto_progress",
            "expecto_transact_emporium",
            "expecto_buy_items"
        ]
    
    async def submit_error(self, ctx, error, exception):

        record_scroll = self.client.get_channel(int(id_scroll))

        embed = discord.Embed(colour=colour, title=f"Command Error Report", timestamp=get_timestamp())
        embed.add_field(name=f"function call: {ctx.command} | {exception}", value=error, inline=False)

        try:
            link = f"https://discordapp.com/channels/" \
                   f"{ctx.message.guild.id}/{ctx.message.channel.id}/{ctx.message.id}"
        except AttributeError:
            embed.add_field(
                name=f"Error Traceback", inline=False,
                value=f"User | DMchannel :: {ctx.author} | #{ctx.channel}\n",
            )
        else:
            embed.add_field(
                name=f"Error Traceback", inline=False,
                value=f"User | Channel | Source :: {ctx.author} | #{ctx.channel} | [message link]({link})",
            )
        finally:
            await process_msg_submit(record_scroll, None, embed)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):

        if isinstance(error, commands.MissingRequiredArgument):
            await self.submit_error(ctx, error, "MissingRequiredArgument")

        elif isinstance(error, commands.UserInputError):

            if isinstance(error, commands.BadArgument):

                if str(ctx.command) in self.functions_member_tagging:
                    await process_msg_invalid_member(ctx)

                else:
                    await self.submit_error(ctx, error, "BadArgument")

            else:
                await self.submit_error(ctx, error, "UserInputError")

        elif isinstance(error, commands.CheckFailure):

            if str(ctx.command) in self.functions_is_owner:
                return

            elif str(ctx.command) in self.functions_role_only:
                return

            elif isinstance(error, commands.NoPrivateMessage):
                embed = discord.Embed(
                    title="Invalid channel", colour=colour,
                    description="This command can only be used inside the guild"
                )
                await process_msg_submit(ctx.channel, None, embed)

            else:
                await self.submit_error(ctx, error, "CheckFailure")

        elif isinstance(error, commands.CommandOnCooldown):

            if str(ctx.command) == "economy_sushi_bento_serve":

                embed = discord.Embed(
                    title="sushi, food, hungry, ap", colour=colour,
                    description=f"request for hourly free food servings\n"
                                f"pings the <@&{id_sushchefs}> role"
                )
                embed.add_field(
                    name="Next serving", inline=False,
                    value=f"In {int(error.retry_after / 60)} {pluralize('minute', int(error.retry_after / 60))}"
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif str(ctx.command) in self.functions_with_cooldown:
                return

            else:
                await self.submit_error(ctx, error, "CommandOnCooldown")

        elif isinstance(error, commands.CommandNotFound):

            if isinstance(ctx.channel, discord.DMChannel):

                embed = discord.Embed(
                    title="Invalid channel", colour=colour,
                    description=f"Certain commands are not available through direct message channels.\n"
                                f"Use them at the <#{id_spell_spam}>"
                )
                await process_msg_submit(ctx.author, None, embed)

        elif isinstance(error, commands.CommandInvokeError):
            await self.submit_error(ctx, error, "CommandInvokeError")

        elif isinstance(error, commands.NotOwner):
            await self.submit_error(ctx, error, "NotOwner")

        elif isinstance(error, commands.ExtensionError):
            await self.submit_error(ctx, error, "ExtensionError")

        else:
            await self.submit_error(ctx, error, None)


def setup(client):
    client.add_cog(Error(client))
