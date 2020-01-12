"""
Development Module
Miketsu, 2020
"""

from discord.ext import commands

from cogs.economy import Economy
from cogs.encounter import Encounter
from cogs.ext.initialize import *
from cogs.frames import Frames
from cogs.summon import Summon


class Development(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.prefix = self.client.command_prefix

    @commands.command(aliases=["reset"])
    @commands.is_owner()
    async def development_perform_reset(self, ctx, *, args):

        valid_arguments = ["daily", "weekly", "boss"]

        if args == "daily":
            await Economy(self.client).economy_issue_rewards_reset_daily()
            await process_msg_reaction_add(ctx.message, "✅")

        elif args == "weekly":
            await Economy(self.client).economy_issue_rewards_reset_weekly()
            await Frames(self.client).achievements_process_weekly()
            await process_msg_reaction_add(ctx.message, "✅")

        elif args == "boss":
            await Encounter(self.client).encounter_perform_reset_boss()
            await process_msg_reaction_add(ctx.message, "✅")

        elif args not in valid_arguments:
            embed = discord.Embed(
                colour=colour, title="Invalid argument",
                description=f"provide a valid argument: {valid_arguments}"
            )
            await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["addshiki", "as"])
    @commands.check(check_if_user_has_development_role)
    async def development_shikigami_add(self, ctx, *args):

        # ;addshiki <rarity> <shikigami_name> <yes/no> <broken/mystery> <pre_img_link> <evo_img_link>

        if len(args) == 6:

            shrine = False
            if args[2].lower() == "yes":
                shrine = True

            shikigamis.insert_one({
                "name": (args[1].replace("_", " ")).lower(),
                "rarity": args[0].upper(),
                "shrine": shrine,
                "thumbnail": {
                    "pre": args[4],
                    "evo": args[5]
                },
                "demon_quiz": None,
                "amulet": args[3].lower()
            })
            await process_msg_reaction_add(ctx.message, "✅")

        else:
            await process_msg_reaction_add(ctx.message, "❌")

    @commands.command(aliases=["dcils"])
    @commands.is_owner()
    async def development_compensate_increase_level_shikigami(self, ctx, member: discord.Member = None, *, args):

        shikigami_name = args.lower()

        if shikigami_name in pool_all:

            query = users.find_one({
                "user_id": str(member.id),
                "shikigami.name": shikigami_name}, {
                "_id": 0, "shikigami.$": 1
            })

            if query is not None:
                users.update_one({
                    "user_id": str(member.id),
                    "shikigami.name": shikigami_name}, {
                    "$set": {
                        "shikigami.$.level": 40,
                        "shikigami.$.exp": 10000,
                        "shikigami.$.level_exp_next": 10000
                    }
                })
                await process_msg_reaction_add(ctx.message, "✅")

    @commands.command(aliases=["dcilu"])
    @commands.is_owner()
    async def development_compensate_increase_level_user(self, ctx, member: discord.Member = None):

        current_level = users.find_one({"user_id": str(member.id)}, {"_id": 0, "level": 1})["level"]

        if current_level != 60:
            users.update_one({
                "user_id": str(member.id)}, {
                "$set": {
                    "level": 60, "experience": 100000, "level_exp_next": 100000
                },
                "$inc": {
                    "amulets": (60 - current_level) * 10
                }
            })
            await process_msg_reaction_add(ctx.message, "✅")

    @commands.command(aliases=["dci"])
    @commands.is_owner()
    async def development_compensate_items(self, ctx, member: discord.Member = None):

        users.update_one({
            "user_id": str(member.id)}, {
            "$inc": {
                "amulets": 2500,
                "jades": 30000,
                "coins": 50000000,
                "amulets_b": 750,
                "sushi": 2500,
                "realm_ticket": 250,
                "encounter_ticket": 150,
                "parade_tickets": 100,
                "talisman": 500000,
                "friendship_pass": 250,
                "friendship": 2000
            }
        })
        await process_msg_reaction_add(ctx.message, "✅")

    @commands.command(aliases=["dcps"])
    @commands.is_owner()
    async def development_compensate_push_shikigami(self, ctx, member: discord.Member = None, *, args):

        shiki = args.lower()
        if shiki in pool_all:

            query = users.find_one({
                "user_id": str(member.id),
                "shikigami.name": shiki}, {
                "_id": 0, "shikigami.$": 1
            })

            if query is None:
                evolve, shards = False, 0
                if get_rarity_shikigami(shiki) == "SP":
                    evolve, shards = True, 5
                shikigami_push_user(member.id, shiki, evolve, shards)

            users.update_one({
                "user_id": str(member.id),
                "shikigami.name": shiki}, {
                "$inc": {
                    "shikigami.$.owned": 1
                }
            })
            users.update_one({
                "user_id": str(member.id)
            }, {
                "$inc": {
                    get_rarity_shikigami(shiki): 1
                }
            })
            await process_msg_reaction_add(ctx.message, "✅")

    @commands.command(aliases=["dmaph"])
    @commands.is_owner()
    async def development_manual_achievements_process_hourly(self, ctx):

        await process_msg_reaction_add(ctx.message, "✅")
        await Frames(self.client).achievements_process_hourly()

    @commands.command(aliases=["dmapd"])
    @commands.is_owner()
    async def development_manual_achievements_process_daily(self, ctx):

        await process_msg_reaction_add(ctx.message, "✅")
        await Frames(self.client).achievements_process_daily()

    @commands.command(aliases=["dmfa"])
    @commands.is_owner()
    async def development_manual_frame_automate(self, ctx):

        await process_msg_reaction_add(ctx.message, "✅")
        await Frames(self.client).frame_automate()
        await Summon(self.client).summon_perform_streak_penalize()


def setup(client):
    client.add_cog(Development(client))
