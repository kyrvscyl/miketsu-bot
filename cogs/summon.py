"""
Summon Module
Miketsu, 2020
"""

from itertools import cycle

from discord.ext import commands

from cogs.ext.initialize import *


class Summon(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.prefix = self.client.command_prefix

        self.summon_captions = cycle(listings_1["summon_captions"])

    @commands.command(aliases=["summon", "s"])
    @commands.guild_only()
    async def summon_perform(self, ctx, *, shikigami_name=None):

        if shikigami_name is None:

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
                value=f"*`{self.prefix}summon <shikigami name>`*\n"
                      f"*`{self.prefix}sb`*\n"
                      f"*`{self.prefix}sm <1 or 10>`*\n",
                inline=False
            )
            await process_msg_submit(ctx.channel, None, embed)

        elif shikigami_name is not None:

            shikigami_name = shikigami_name.lower()

            if shikigami_name in pool_all:
                await self.summon_perform_shards(ctx, shikigami_name, ctx.author)

            elif shikigami_name not in pool_all:
                await shikigami_post_approximate_results(ctx, shikigami_name)

    async def summon_perform_shards(self, ctx, shikigami_name, user):

        try:
            shards_current = users.find_one({
                "user_id": str(user.id),
                "shikigami.name": shikigami_name
            }, {
                "_id": 0, "shikigami.$.name": 1
            })["shikigami"][0]["shards"]

        except TypeError:
            embed = discord.Embed(
                title="Summon failed", colour=colour,
                description=f"You have no shards of {shikigami_name.title()}",
                timestamp=get_timestamp()
            )
            await process_msg_submit(ctx.channel, None, embed)

        else:
            shards_required, rarity = get_shard_requirement(shikigami_name)

            if shards_current >= shards_required:
                query = users.find_one({
                    "user_id": str(user.id),
                    "shikigami.name": shikigami_name
                }, {
                    "_id": 0, "shikigami.$": 1
                })

                if query is None:
                    evolve, shards_current = False, 0
                    if rarity == "SP":
                        evolve, shards_current = True, 0
                    shikigami_push_user(user.id, shikigami_name, evolve, shards_current)

                users.update_one({
                    "user_id": str(user.id),
                    "shikigami.name": shikigami_name}, {
                    "$inc": {
                        f"{rarity}": 1,
                        "shikigami.$.owned": 1,
                        "shikigami.$.shards": -shards_required
                    }
                })
                embed = discord.Embed(
                    title="Summon success", colour=colour,
                    description=f"You acquired the {rarity} shikigami {shikigami_name.title()}!",
                    timestamp=get_timestamp()
                )
                embed.set_footer(text=f"{user.display_name}", icon_url=user.avatar_url)
                embed.set_thumbnail(url=get_thumbnail_shikigami(shikigami_name, "pre"))
                await process_msg_submit(ctx.channel, None, embed)

            elif shards_current < shards_required:

                embed = discord.Embed(
                    title="Summon failed", colour=colour, timestamp=get_timestamp(),
                    description=f"You lack {shards_required - shards_current} {shikigami_name.title()} shards",
                )
                embed.set_thumbnail(url=get_thumbnail_shikigami(shikigami_name, "pre"))
                await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["sb"])
    @commands.guild_only()
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def summon_perform_broken(self, ctx):

        user = ctx.author
        amulets_current = users.find_one({"user_id": str(user.id)}, {"_id": 0, "amulets_b": 1})["amulets_b"]

        if amulets_current < 1:
            embed = discord.Embed(
                title="Insufficient amulets", colour=colour,
                description="perform exploration to obtain more",
            )
            await process_msg_submit(ctx.channel, None, embed)

        elif amulets_current > 0:

            if amulets_current >= 5:
                await self.summon_perform_broken_pull(ctx, user, 5)

            elif 0 < amulets_current < 5:
                await self.summon_perform_broken_pull(ctx, user, amulets_current)

        self.client.get_command("summon_perform_broken").reset_cooldown(ctx)

    async def summon_perform_broken_pull(self, ctx, user, amulets_pulled):

        summon_pool = []
        for amulet in range(amulets_pulled):
            roll = random.uniform(0, 100)

            if roll < 1:
                summon_pool.append(("SSN", "||{}||".format(random.choice(pool_ssn))))
            else:
                roll = random.uniform(0, 100)
                if roll <= 13:
                    summon_pool.append(("R", "{}".format(random.choice(pool_r))))
                else:
                    summon_pool.append(("N", random.choice(pool_n)))

        s_1 = sum(x.count("SSN") for x in summon_pool)
        s_2 = sum(x.count("R") for x in summon_pool)
        s_3 = sum(x.count("N") for x in summon_pool)

        f_1 = f"{s_1} {pluralize('SSN', s_1)}"
        f_2 = f"{s_2} {pluralize('R', s_2)}"
        f_3 = f"{s_3} {pluralize('N', s_3)}"

        description = ""
        for x in summon_pool:
            description += "🔸{}\n".format(x[1].title())

        embed = discord.Embed(
            color=user.colour, title="🎊 Summon results", description=description, timestamp=get_timestamp()
        )
        embed.set_footer(text=f"{f_1}; {f_2}; {f_3}", icon_url=user.avatar_url)

        caption = "{}".format(next(self.summon_captions)).format(user.mention)

        await process_msg_submit(ctx.channel, caption, embed)
        await self.summon_perform_broken_pull_push(user, s_1, s_2, s_3, amulets_pulled, summon_pool)

    async def summon_perform_broken_pull_push(self, user, s_1, s_2, s_3, amulets_pulled, summon_pool):

        users.update_one({
            "user_id": str(user.id)}, {
            "$inc": {
                "SSN": s_1,
                "R": s_2,
                "N": s_3,
                "amulets_spent_b": amulets_pulled,
                "amulets_b": -amulets_pulled
            }
        })

        for summon in summon_pool:

            query = users.find_one({
                "user_id": str(user.id),
                "shikigami.name": summon[1].replace("||", "")}, {
                "_id": 0, "shikigami.$": 1
            })

            if query is None:
                evolve, shards = False, 0
                shikigami_push_user(user.id, summon[1].replace("||", ""), evolve, shards)

            users.update_one({
                "user_id": str(user.id),
                "shikigami.name": summon[1].replace("||", "")}, {
                "$inc": {
                    "shikigami.$.owned": 1
                }
            })

    @commands.command(aliases=["sm"])
    @commands.guild_only()
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def summon_perform_mystery(self, ctx, *, args=None):

        user = ctx.author

        try:
            amulets_pulled = int(args)
            amulets_current = users.find_one({"user_id": str(user.id)}, {"_id": 0, "amulets": 1})["amulets"]
        except ValueError:
            pass
        except TypeError:
            raise commands.MissingRequiredArgument(ctx.author)
        else:
            if amulets_current < 1:
                embed = discord.Embed(
                    title="Insufficient amulets", colour=colour,
                    description="exchange at the shop to obtain more",
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif args not in ["1", "10"]:
                raise commands.MissingRequiredArgument(ctx.author)

            elif amulets_current > 0:

                if amulets_pulled > amulets_current:
                    embed = discord.Embed(
                        title="Insufficient amulets", colour=colour,
                        description=f"You only have {amulets_current}{e_a} in possession"
                    )
                    embed.set_footer(icon_url=user.avatar_url, text=user.display_name)
                    await process_msg_submit(ctx.channel, None, embed)

                elif amulets_pulled == 10 and amulets_current >= 10:
                    await self.summon_perform_mystery_pull(ctx, user, amulets_pulled)

                elif amulets_pulled == 1 and amulets_current >= 1:
                    await self.summon_perform_mystery_pull(ctx, user, amulets_pulled)
        finally:
            self.client.get_command("summon_perform_mystery").reset_cooldown(ctx)

    async def summon_perform_mystery_pull(self, ctx, user, amulets_pulled):

        summon_pool = []

        for amulet in range(amulets_pulled):

            roll = random.uniform(0, 100)
            if roll < 1.2:
                p = random.uniform(0, 1.2)
                if p >= 126 / 109:
                    summon_pool.append(("SP", "||{}||".format(random.choice(pool_sp))))
                else:
                    summon_pool.append(("SSR", "||{}||".format(random.choice(pool_ssr))))
            elif roll <= 18.8:
                summon_pool.append(("SR", random.choice(pool_sr)))
            else:
                summon_pool.append(("R", random.choice(pool_r)))

        s_1 = sum(x.count("SP") for x in summon_pool)
        s_2 = sum(x.count("SSR") for x in summon_pool)
        s_3 = sum(x.count("SR") for x in summon_pool)
        s_4 = sum(x.count("R") for x in summon_pool)

        f_1 = f"{s_1} {pluralize('SP', s_1)}"
        f_2 = f"{s_2} {pluralize('SSR', s_2)}"
        f_3 = f"{s_3} {pluralize('SR', s_3)}"
        f_4 = f"{s_4} {pluralize('R', s_4)}"

        description = ""
        for x in summon_pool:
            description += "🔸{}\n".format(x[1].title())

        embed = discord.Embed(
            color=user.colour, title="🎊 Summon results", description=description, timestamp=get_timestamp()
        )

        if amulets_pulled == 10:
            embed.set_footer(text=f"{f_1}; {f_2}; {f_3}; {f_4}", icon_url=user.avatar_url)

        elif amulets_pulled == 1:
            shikigami_pulled = summon_pool[0][1].replace("||", "")
            embed.set_thumbnail(url=get_thumbnail_shikigami(shikigami_pulled, "pre"))

        caption = "{}".format(next(self.summon_captions)).format(user.mention)

        await process_msg_submit(ctx.channel, caption, embed)
        await self.summon_perform_mystery_pull_push(user, s_1, s_2, s_3, s_4, amulets_pulled, summon_pool)
        await self.summon_perform_mystery_pull_push_streak(user, summon_pool)

    async def summon_perform_mystery_pull_push(self, user, s_1, s_2, s_3, s_4, amulets_pulled, summon_pool):

        users.update_one({
            "user_id": str(user.id)
        }, {
            "$inc": {
                "SP": s_1,
                "SSR": s_2,
                "SR": s_3,
                "R": s_4,
                "amulets_spent": amulets_pulled,
                "amulets": -amulets_pulled
            }
        })
        await perform_add_log("amulets", -amulets_pulled, user.id)

        for summon in summon_pool:
            shikigami_name = summon[1].replace("||", "")
            query = users.find_one({
                "user_id": str(user.id), "shikigami.name": shikigami_name
            }, {
                "_id": 0, "shikigami.$": 1
            })

            if query is None:
                evolve, shards = False, 0
                if summon[0] == "SP":
                    evolve, shards = True, 5
                shikigami_push_user(user.id, shikigami_name, evolve, shards)

            users.update_one({
                "user_id": str(user.id), "shikigami.name": shikigami_name
            }, {
                "$inc": {
                    "shikigami.$.owned": 1
                }
            })

    async def summon_perform_mystery_pull_push_streak(self, user, summon_pull):

        if streaks.find_one({"user_id": str(user.id)}, {"_id": 0}) is None:
            streaks.insert_one({"user_id": str(user.id), "SSR_current": 0, "SSR_record": 0})

        for summon in summon_pull:
            ssr_current = streaks.find_one({"user_id": str(user.id)}, {"_id": 0})["SSR_current"]
            ssr_record = streaks.find_one({"user_id": str(user.id)}, {"_id": 0})["SSR_record"]

            if summon[0] in ["SP", "SR", "R"]:
                if ssr_current == ssr_record:
                    streaks.update_one({"user_id": str(user.id)}, {"$inc": {"SSR_current": 1, "SSR_record": 1}})
                else:
                    streaks.update_one({"user_id": str(user.id)}, {"$inc": {"SSR_current": 1}})

            elif summon[0] == "SSR":
                streaks.update_one({"user_id": str(user.id)}, {"$set": {"SSR_current": 0}})


def setup(client):
    client.add_cog(Summon(client))
