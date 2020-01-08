"""
Development Module
Miketsu, 2020
"""

from discord.ext import commands

from cogs.ext.initialize import *
from cogs.frames import Frames


class Development(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.prefix = self.client.command_prefix

    @commands.command(aliases=["reset"])
    @commands.check(check_if_user_has_development_role)
    async def perform_reset(self, ctx, *, args):

        valid_arguments = ["daily", "weekly", "boss"]

        if args == "daily":
            await self.perform_reset_rewards_daily()
            await process_msg_reaction_add(ctx.message, "✅")

        elif args == "weekly":
            await self.perform_reset_rewards_weekly()
            await Frames(self.client).achievements_process_weekly()
            await process_msg_reaction_add(ctx.message, "✅")

        elif args == "boss":
            await self.perform_reset_boss()
            await process_msg_reaction_add(ctx.message, "✅")

        elif args not in valid_arguments:
            embed = discord.Embed(
                colour=colour, title="Invalid argument",
                description=f"provide a valid argument: {valid_arguments}"
            )
            await process_msg_submit(ctx.channel, None, embed)

    async def perform_reset_rewards_daily(self):

        print("Resetting daily rewards")
        users.update_many({}, {"$set": {"daily": False, "raided_count": 0, "prayers": 3, "wish": True}})

        for ship in ships.find({"level": {"$gt": 1}}, {"ship_name": 1, "shipper1": 1, "shipper2": 1, "level": 1}):
            rewards = ship["level"] * 25
            users.update_one({"user_id": ship["shipper1"]}, {"$inc": {"jades": rewards}})
            users.update_one({"user_id": ship["shipper2"]}, {"$inc": {"jades": rewards}})

            await perform_add_log("jades", rewards, ship['shipper1'])
            await perform_add_log("jades", rewards, ship['shipper2'])

        embed = discord.Embed(
            title="🎁 Daily rewards reset",
            colour=colour, timestamp=get_timestamp(),
            description=f"• claim yours using `{self.prefix}daily`\n"
                        f"• check your income using `{self.prefix}sail`\n"
                        f"• wish for a shikigami shard using `{self.prefix}wish"
        )
        spell_spam_channel = self.client.get_channel(int(id_spell_spam))
        await process_msg_submit(spell_spam_channel, None, embed)

    async def perform_reset_rewards_weekly(self):

        print("Resetting weekly rewards")
        users.update_many({}, {"$set": {"weekly": False}})

        embed = discord.Embed(
            title="💝 Weekly rewards reset", colour=colour,
            description=f"• claim yours using `{self.prefix}weekly`\n"
                        f"• Eboshi frames redistributed and wielders rewarded"
        )
        spell_spam_channel = self.client.get_channel(int(id_spell_spam))
        await process_msg_submit(spell_spam_channel, None, embed)

    async def perform_reset_boss(self):

        bosses.update_many({}, {
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

    @commands.command(aliases=["addshiki", "as"])
    @commands.check(check_if_user_has_development_role)
    async def shikigami_add(self, ctx, *args):

        # ;addshiki <rarity> <shikigami_name> <yes/no> <broken/mystery> <pre_link> <evo_link>

        if len(args) < 6:
            return

        elif len(args) == 6:
            shrine = False

            if args[2].lower() == "yes":
                shrine = True

            profile = {
                "name": (args[1].replace("_", " ")).lower(),
                "rarity": args[0].upper(),
                "shrine": shrine,
                "thumbnail": {
                    "pre": args[4],
                    "evo": args[5]
                },
                "demon_quiz": None,
                "amulet": args[3].lower()
            }

            shikigamis.insert_one(profile)
            await process_msg_reaction_add(ctx.message, "✅")
        else:
            await process_msg_reaction_add(ctx.message, "❌")

    @commands.command(aliases=["update"])
    @commands.check(check_if_user_has_development_role)
    async def shikigami_update(self, ctx, *args):

        if len(args) == 0:
            return

        elif len(args) == 3:
            query = (args[0].replace("_", " ")).lower()
            profile_shikigami = shikigamis.find_one({
                "shikigami.name": query}, {
                "_id": 0,
                "shikigami": {
                    "$elemMatch": {
                        "name": query
                    }}
            })

            try:
                if profile_shikigami["shikigami"][0]["profiler"] != "":
                    await process_msg_reaction_add(ctx.message, "❌")

            except KeyError:
                try:
                    pre_evo = args[1]
                    evo = args[2]
                    profiler = ctx.author.display_name

                    shikigamis.update_one({"shikigami.name": query}, {
                        "$set": {
                            "shikigami.$.thumbnail.pre_evo": pre_evo,
                            "shikigami.$.thumbnail.evo": evo,
                            "shikigami.$.profiler": str(profiler)
                        }
                    })
                except KeyError:
                    await process_msg_reaction_add(ctx.message, "❌")
        else:
            await process_msg_reaction_add(ctx.message, "❌")

    @commands.command(aliases=["up"])
    @commands.is_owner()
    async def compensate_increase_shikigami_level(self, ctx, member: discord.Member = None, *, args):

        shiki = args.lower()
        if shiki in pool_all:

            query = users.find_one({
                "user_id": str(member.id),
                "shikigami.name": shiki}, {
                "_id": 0, "shikigami.$": 1
            })

            if query is not None:
                users.update_one({
                    "user_id": str(member.id),
                    "shikigami.name": shiki}, {
                    "$set": {
                        "shikigami.$.level": 40,
                        "shikigami.$.exp": 10000,
                        "shikigami.$.level_exp_next": 10000
                    }
                })
                await process_msg_reaction_add(ctx.message, "✅")

    @commands.command(aliases=["lvl"])
    @commands.is_owner()
    async def compensate_increase_level(self, ctx, member: discord.Member = None):

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

    @commands.command(aliases=["compensate"])
    @commands.is_owner()
    async def compensate_economy_items(self, ctx, member: discord.Member = None):

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

    @commands.command(aliases=["push"])
    @commands.is_owner()
    async def compensate_push_shikigami_manually(self, ctx, member: discord.Member = None, *, args):

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


def setup(client):
    client.add_cog(Development(client))
