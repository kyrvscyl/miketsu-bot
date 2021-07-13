"""
Summon Module
"Miketsu, 2021
"""

from itertools import cycle

from discord.ext import commands

from cogs.ext.initialize import *


class Summon(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.prefix = self.client.command_prefix

        self.summon_captions = cycle(listings_1["summon_captions"])

    async def summon_perform_help_info(self, ctx):

        embed = discord.Embed(
            title="summon, s", colour=colour,
            description="simulates summon and collect shikigamis"
        )
        embed.add_field(
            name="Shards Requirement", inline=False,
            value=f"```"
                  "SP    ::   15\n"
                  "SSR   ::   12\n"
                  "SR    ::    9\n"
                  "R     ::    6\n"
                  "N     ::    3\n"
                  "SSN   ::   12\n"
                  "```",
        )
        embed.add_field(
            name="Formats", inline=False,
            value=f"*`{self.prefix}s <shikigami name>`*\n"
                  f"*`{self.prefix}s b`*\n"
                  f"*`{self.prefix}s <1 or 10>`*\n",
        )
        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["summon", "s"])
    @commands.guild_only()
    async def summon_perform(self, ctx, *, arg1=None):

        if arg1 is None:
            await self.summon_perform_help_info(ctx)

        elif arg1 is not None:

            try:
                amulets_pulled = int(arg1)

            except ValueError:
                arg1_lowered = arg1.lower()

                if arg1_lowered in ["broken", "b"]:
                    await self.summon_perform_broken(ctx, ctx.author)

                elif arg1_lowered in pool_all:
                    await self.summon_perform_shards(ctx, arg1_lowered, ctx.author)

                else:
                    await shikigami_post_approximate_results(ctx, arg1_lowered)

            else:
                if amulets_pulled not in [1, 10]:
                    await self.summon_perform_help_info(ctx)

                else:
                    await self.summon_perform_mystery(ctx, ctx.author, amulets_pulled)

        self.client.get_command("summon_perform").reset_cooldown(ctx)

    async def summon_perform_shards(self, ctx, shikigami_name, user):

        shikigami_profile = users.find_one({
            "user_id": str(user.id),
            "shikigami.name": shikigami_name
        }, {
            "_id": 0, "shikigami.$": 1
        })

        if shikigami_profile is None:

            embed = discord.Embed(
                title="Summon failed", colour=user.colour, timestamp=get_timestamp(),
                description=f"You have no shards of {shikigami_name.title()}"
            )
            await process_msg_submit(ctx.channel, None, embed)

        elif shikigami_profile is not None:

            shikigami_shard_current = shikigami_profile["shikigami"][0]["shards"]

            def get_shard_requirement():
                rarity = shikigamis.find_one({"name": shikigami_name}, {"_id": 0, "rarity": 1})["rarity"]
                return shard_requirement[rarity], rarity

            shikigami_shards_required, shikigami_rarity = get_shard_requirement()

            if shikigami_shard_current >= shikigami_shards_required:

                query = users.find_one({
                    "user_id": str(user.id),
                    "shikigami.name": shikigami_name
                }, {
                    "_id": 0, "shikigami.$": 1
                })

                if query is None:
                    evolve, shikigami_shard_current = False, 0
                    if shikigami_rarity == "SP":
                        evolve, shikigami_shard_current = True, 0
                    shikigami_push_user(user.id, shikigami_name, evolve, shikigami_shard_current)

                users.update_one({
                    "user_id": str(user.id),
                    "shikigami.name": shikigami_name
                }, {
                    "$inc": {
                        f"{shikigami_rarity}": 1,
                        "shikigami.$.owned": 1,
                        "shikigami.$.shards": -shikigami_shards_required
                    }
                })
                embed = discord.Embed(
                    title="Summon success", colour=user.colour, timestamp=get_timestamp(),
                    description=f"You acquired the {shikigami_rarity} shikigami {shikigami_name.title()}!",
                )
                embed.set_footer(text=f"{user.display_name}", icon_url=user.avatar_url)
                embed.set_thumbnail(url=get_shikigami_url(shikigami_name, "pre"))
                await process_msg_submit(ctx.channel, None, embed)

            elif shikigami_shard_current < shikigami_shards_required:

                shikigami_shards_lacking = shikigami_shards_required - shikigami_shard_current
                embed = discord.Embed(
                    title="Summon failed", colour=colour, timestamp=get_timestamp(),
                    description=f"You lack `{shikigami_shards_lacking}` {shikigami_name.title()} shards",
                )
                embed.set_thumbnail(url=get_shikigami_url(shikigami_name, "pre"))
                await process_msg_submit(ctx.channel, None, embed)

    async def summon_perform_broken(self, ctx, user):

        amulets_current = users.find_one({"user_id": str(user.id)}, {"_id": 0, "amulets_b": 1})["amulets_b"]

        if amulets_current < 1:
            embed = discord.Embed(
                title="Insufficient amulets", colour=user.colour,
                description="perform exploration to obtain more",
            )
            await process_msg_submit(ctx.channel, None, embed)

        elif amulets_current > 0:

            if amulets_current >= 5:
                await self.summon_perform_broken_pull(ctx, user, 5)

            elif 0 < amulets_current < 5:
                await self.summon_perform_broken_pull(ctx, user, amulets_current)

    async def summon_perform_broken_pull(self, ctx, user, amulets_pulled):

        shikigami_pulled = []
        s_1, s_2, s_3 = 0, 0, 0
        r_pull = ["SSN", "R", "N"]

        for amulet in range(amulets_pulled):

            if random.uniform(0, 100) <= 1:
                shikigami_pulled.append((r_pull[0], random.choice(pool_ssn)))
                s_1 += 1
            else:
                if random.uniform(0, 100) <= 13:
                    shikigami_pulled.append((r_pull[1], random.choice(pool_r)))
                    s_2 += 1
                else:
                    shikigami_pulled.append((r_pull[2], random.choice(pool_n)))
                    s_3 += 1

        shikigami_pulled_count = [[r_pull[0], s_1], [r_pull[1], s_2], [r_pull[2], s_3]]

        description = ""
        caption = "{}".format(next(self.summon_captions)).format(user.mention)
        text = [f"{x[1]} {pluralize(x[0], x[1])}" for x in shikigami_pulled_count]

        for x in shikigami_pulled:
            if x[0] not in ["SSN"]:
                description += "🔸{}\n".format(x[1].title())
            else:
                description += "🔸||{}||\n".format(x[1].title())

        embed = discord.Embed(
            color=user.colour, title="🎊 Summon results",
            description=description, timestamp=get_timestamp()
        )
        embed.set_footer(text=f"{'; '.join(text)}", icon_url=user.avatar_url)

        await process_msg_submit(ctx.channel, caption, embed)
        await self.summon_perform_broken_pull_push(user, shikigami_pulled_count, amulets_pulled, shikigami_pulled)

    async def summon_perform_broken_pull_push(self, user, shikigami_pulled_count, amulets_pulled, summon_pool):

        users.update_one({
            "user_id": str(user.id)}, {
            "$inc": {
                "SSN": shikigami_pulled_count[0][1],
                "R": shikigami_pulled_count[1][1],
                "N": shikigami_pulled_count[2][1],
                "amulets_spent_b": amulets_pulled,
                "amulets_b": -amulets_pulled
            }
        })

        for summon in summon_pool:

            query = users.find_one({
                "user_id": str(user.id),
                "shikigami.name": summon[1]
            }, {
                "_id": 0, "shikigami.$": 1
            })

            if query is None:
                evolve, shards = False, 0
                shikigami_push_user(user.id, summon[1], evolve, shards)

            users.update_one({
                "user_id": str(user.id),
                "shikigami.name": summon[1]
            }, {
                "$inc": {
                    "shikigami.$.owned": 1
                }
            })

    async def summon_perform_mystery(self, ctx, user, amulets_pulled):

        amulets_current = users.find_one({"user_id": str(user.id)}, {"_id": 0, "amulets": 1})["amulets"]

        if amulets_current < 1:
            embed = discord.Embed(
                title="Insufficient amulets", colour=user.colour,
                description="exchange at the shop to obtain more",
            )
            await process_msg_submit(ctx.channel, None, embed)

        elif amulets_current > 0:

            if amulets_pulled > amulets_current:
                embed = discord.Embed(
                    title="Insufficient amulets", colour=user.colour,
                    description=f"You only have `{amulets_current}`{e_a} in your possession"
                )
                embed.set_footer(icon_url=user.avatar_url, text=user.display_name)
                await process_msg_submit(ctx.channel, None, embed)

            elif amulets_pulled == 10 and amulets_current >= 10:
                await self.summon_perform_mystery_pull(ctx, user, amulets_pulled)

            elif amulets_pulled == 1 and amulets_current >= 1:
                await self.summon_perform_mystery_pull(ctx, user, amulets_pulled)

    async def summon_perform_mystery_pull(self, ctx, user, amulets_pulled):

        shikigami_pulled = []
        s_1, s_2, s_3, s_4 = 0, 0, 0, 0
        r_pull = ["SP", "SSR", "SR", "R"]

        for amulet in range(amulets_pulled):

            if random.uniform(0, 100) <= 1.2:

                if random.uniform(0, 1.2) >= 126 / 109:
                    shikigami_pulled.append((r_pull[0], random.choice(pool_sp)))
                    s_1 += 1
                else:
                    shikigami_pulled.append((r_pull[1], random.choice(pool_ssr)))
                    s_2 += 1

            elif random.uniform(0, 100) <= 18.8:
                shikigami_pulled.append((r_pull[2], random.choice(pool_sr)))
                s_3 += 1
            else:
                shikigami_pulled.append((r_pull[3], random.choice(pool_r)))
                s_4 += 1

        shikigami_pulled_count = [[r_pull[0], s_1], [r_pull[1], s_2], [r_pull[2], s_3], [r_pull[3], s_4]]

        description = ""
        caption = "{}".format(next(self.summon_captions)).format(user.mention)
        text = [f"{x[1]} {pluralize(x[0], x[1])}" for x in shikigami_pulled_count]

        for x in shikigami_pulled:
            if x[0] not in ["SSR", "SP"]:
                description += "🔸{}\n".format(x[1].title())
            else:
                description += "🔸||{}||\n".format(x[1].title())

        embed = discord.Embed(
            color=user.colour, title="🎊 Summon results",
            description=description, timestamp=get_timestamp()
        )
        embed.set_footer(text=f"{'; '.join(text)}", icon_url=user.avatar_url)

        if amulets_pulled == 10:
            embed.set_footer(text=f"{'; '.join(text)}", icon_url=user.avatar_url)

        elif amulets_pulled == 1:
            embed.set_thumbnail(url=get_shikigami_url(shikigami_pulled[0][1], "pre"))

        await process_msg_submit(ctx.channel, caption, embed)
        await self.summon_perform_mystery_pull_push(user, shikigami_pulled_count, amulets_pulled, shikigami_pulled)
        await self.summon_perform_mystery_pull_push_streak(user, shikigami_pulled)

    async def summon_perform_mystery_pull_push(self, user, shikigami_pulled_count, amulets_pulled, summon_pool):

        users.update_one({
            "user_id": str(user.id)
        }, {
            "$inc": {
                "SP": shikigami_pulled_count[0][1],
                "SSR": shikigami_pulled_count[1][1],
                "SR": shikigami_pulled_count[2][1],
                "R": shikigami_pulled_count[3][1],
                "amulets_spent": amulets_pulled,
                "amulets": -amulets_pulled
            }
        })
        await perform_add_log("amulets", -amulets_pulled, user.id)

        for summon in summon_pool:
            shikigami_name = summon[1]
            query = users.find_one({
                "user_id": str(user.id),
                "shikigami.name": shikigami_name
            }, {
                "_id": 0, "shikigami.$": 1
            })

            if query is None:
                evolve, shards = False, 0
                if summon[0] == "SP":
                    evolve, shards = True, 5
                shikigami_push_user(user.id, shikigami_name, evolve, shards)

            users.update_one({
                "user_id": str(user.id),
                "shikigami.name": shikigami_name
            }, {
                "$inc": {
                    "shikigami.$.owned": 1
                }
            })

    async def summon_perform_mystery_pull_push_streak(self, user, summon_pool):

        if streaks.find_one({"user_id": str(user.id)}, {"_id": 0}) is None:
            streaks.insert_one({"user_id": str(user.id), "SSR_current": 0, "SSR_record": 0})

        for summon in summon_pool:
            ssr_current = streaks.find_one({"user_id": str(user.id)}, {"_id": 0})["SSR_current"]
            ssr_record = streaks.find_one({"user_id": str(user.id)}, {"_id": 0})["SSR_record"]

            if summon[0] in ["SP", "SR", "R"]:
                if ssr_current == ssr_record:
                    streaks.update_one({"user_id": str(user.id)}, {"$inc": {"SSR_current": 1, "SSR_record": 1}})
                else:
                    streaks.update_one({"user_id": str(user.id)}, {"$inc": {"SSR_current": 1}})

            elif summon[0] == "SSR":
                streaks.update_one({"user_id": str(user.id)}, {"$set": {"SSR_current": 0}})

    async def summon_perform_streak_penalize(self):

        for streak in streaks.find({}, {"_id": 0}):
            new_streak = int(streak["SSR_current"] * (3 / 4))

            if new_streak > 1:
                streaks.update_one({
                    "user_id": streak["user_id"]}, {
                    "$set": {
                        "SSR_current": new_streak,
                        "SSR_record": new_streak
                    }
                })

            else:
                streaks.update_one({
                    "user_id": streak["user_id"]}, {
                    "$set": {
                        "SSR_current": 0,
                        "SSR_record": 0
                    }
                })


def setup(client):
    client.add_cog(Summon(client))
