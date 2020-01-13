"""
Exploration Module
Miketsu, 2020
"""

import asyncio

from PIL import Image
from discord.ext import commands

from cogs.ext.initialize import *


class Exploration(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.prefix = self.client.command_prefix

    def push_new_exploration(self, user, chapter, spirits):

        if explores.find_one({"user_id": str(user.id)}, {"_id": 0}) is None:
            explores.insert_one({
                "user_id": str(user.id),
                "explores": []
            })

        if explores.find_one({
            "user_id": str(user.id),
            "explores.completion": False,
            "explores": {
                "$elemMatch": {"completion": False, "chapter": chapter}
            }
        }, {
            "_id": 0, "explores.$": 1
        }) is None:
            explores.update_one({
                "user_id": str(user.id)
            }, {
                "$push": {
                    "explores": {
                        "$each": [{
                            "attempts": 0,
                            "logs": [],
                            "required": spirits,
                            "chapter": chapter,
                            "completion": False,
                            "date": get_time(),
                        }],
                        "$position": 0
                    }
                }
            })

    @commands.command(aliases=["explores", "exps"])
    @commands.guild_only()
    async def perform_exploration_check_clears(self, ctx, *, member: discord.Member = None):

        if member is None:
            await self.perform_exploration_check_clears_post(ctx.author, ctx)
        else:
            await self.perform_exploration_check_clears_post(member, ctx)

    async def perform_exploration_check_clears_post(self, member, ctx):

        total_explorations = 0
        for result in explores.aggregate([
            {
                '$match': {
                    'user_id': str(member.id)
                }
            }, {
                '$unwind': {
                    'path': '$explores'
                }
            }, {
                '$match': {
                    'explores.completion': True
                }
            }, {
                '$count': 'count'
            }
        ]):
            total_explorations = result["count"]

        embed = discord.Embed(
            colour=ctx.author.colour,
            description=f"Your total exploration clears: {total_explorations}",
            timestamp=get_timestamp()
        )
        embed.set_footer(
            text=f"{member.display_name}",
            icon_url=member.avatar_url
        )
        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["explore", "exp"])
    @commands.guild_only()
    @commands.check(check_if_user_has_sushi_1)
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def perform_exploration(self, ctx, *, arg):

        user = ctx.author

        if not check_if_user_has_shiki_set:
            embed = discord.Embed(
                color=user.colour,
                title="Invalid shikigami",
                description=f"set a shikigami first using `{self.prefix}set`",
            )
            await process_msg_submit(ctx.channel, None, embed)

        elif check_if_user_has_shiki_set:
            user_profile = users.find_one({"user_id": str(user.id)}, {"level": 1, "display": 1, "exploration": 1})

            try:
                chapter = int(arg)
            except ValueError:

                if arg.lower() not in ["last", "unf", "unfinished"]:
                    embed = discord.Embed(
                        color=ctx.author.colour,
                        title="Invalid chapter",
                        description=f"that is not a valid chapter",
                    )
                    await process_msg_submit(ctx.channel, None, embed)

                elif arg.lower() in ["last", "unf", "unfinished"]:
                    query = explores.find_one({
                        "user_id": str(user.id),
                        "explores.completion": False}, {
                        "_id": 0, "explores.$": 1
                    })

                    if query is None:
                        embed = discord.Embed(
                            color=ctx.author.colour, timestamp=get_timestamp(),
                            description=f"You have no pending explorations",
                        )
                        embed.set_footer(text=user.display_name, icon_url=user.avatar_url)
                        await process_msg_submit(ctx.channel, None, embed)

                    elif query is not None:
                        chapter = query["explores"][0]["chapter"]
                        await self.perform_exploration_by_chapter(chapter, user, ctx)

            else:
                if chapter > user_profile["exploration"]:
                    embed = discord.Embed(
                        color=user.colour,
                        title="Invalid chapter",
                        description=f"you have not yet unlocked this chapter",
                    )
                    await process_msg_submit(ctx.channel, None, embed)

                elif chapter in range(1, (zones.count_documents({}) + 1)):
                    await self.perform_exploration_by_chapter(chapter, user, ctx)

                else:
                    embed = discord.Embed(
                        color=ctx.author.colour,
                        title="Invalid chapter",
                        description=f"that is not a valid chapter, < {zones.count_documents({})}",
                    )
                    await process_msg_submit(ctx.channel, None, embed)

            finally:
                self.client.get_command("perform_exploration").reset_cooldown(ctx)

    async def perform_exploration_by_chapter(self, chapter, user, ctx):

        zone = zones.find_one({"chapter": chapter}, {"_id": 0})
        spirits, sushi_required = zone["spirits"], zone["sushi_required"]
        experience = 5 * round((chapter + 1) / 2)

        self.push_new_exploration(user, chapter, spirits)

        total_chance, shikigami_name, shikigami_evolved = get_clear_chance_soul_explore(user, 40, chapter, [0, 0], 0.75,
                                                                                        1)
        thumbnail = get_thumbnail_shikigami(shikigami_name, get_evo_link(shikigami_evolved))

        adjusted_chance = random.uniform(total_chance * 0.95, total_chance)

        def embed_new_create(stage_new, progress, strike):

            description2 = ""
            for log in progress:
                description2 += log

            exploration_stage_new = stage_new + 1
            if exploration_stage_new > spirits:
                exploration_stage_new = spirits

            shiki_exp, shiki_exp_next, shiki_lvl, user_sushi = get_shiki_exp_lvl_next_sushi(user, shikigami_name)

            embed_new = discord.Embed(
                color=ctx.author.colour,
                title=f"{strike}Exploration stage: {exploration_stage_new}/{spirits}{strike}",
                description=f"Chapter {chapter}: {zone['name']}\n{description2}",
                timestamp=get_timestamp()
            )
            embed_new.add_field(
                name=f"Shikigami: {shikigami_name.title()} | {user_sushi} {e_s}",
                value=f"Level: {shiki_lvl} | Experience: {shiki_exp}/{shiki_exp_next}\n"
                      f"Clear Chance: ~{round(total_chance, 2)}%"
            )
            embed_new.set_footer(text=f"{ctx.author.display_name}", icon_url=ctx.author.avatar_url)
            embed_new.set_thumbnail(url=thumbnail)

            return embed_new

        explore_attempts = explores.find_one({
            "user_id": str(user.id),
            "explores.completion": False,
            "explores": {
                "$elemMatch": {
                    "completion": False,
                    "chapter": chapter
                }
            }
        }, {
            "_id": 0,
            "explores.$": 1
        })['explores'][0]['attempts']

        msg = await ctx.channel.send(embed=embed_new_create(explore_attempts, [], ""))
        await process_msg_reaction_add(msg, "🏹")

        def check(r, u):
            return \
                msg.id == r.message.id and \
                str(r.emoji) == "🏹" and \
                u.id == ctx.author.id and \
                check_if_user_has_sushi_2(ctx, sushi_required)

        while True:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=60, check=check)
            except asyncio.TimeoutError:
                await process_msg_reaction_clear(msg)
                break
            else:
                users.update_one({"user_id": str(user.id)}, {"$inc": {"sushi": - sushi_required}})
                await perform_add_log("sushi", -sushi_required, ctx.author.id)

                roll = random.uniform(0, 100)
                if roll < adjusted_chance:
                    explores.update_one({
                        "user_id": str(user.id), "explores.completion": False}, {
                        "$push": {"explores.$.logs": "✅"},
                        "$inc": {"explores.$.attempts": 1}
                    })

                    shikigami_experience_add(user, shikigami_name, experience)

                    query = explores.find_one({
                        "user_id": str(user.id), "explores.completion": False}, {
                        "_id": 0,
                        "explores.$": 1,
                    })
                    explore_report = query["explores"][0]["logs"]
                    explore_attempts = query['explores'][0]['attempts']
                    await msg.edit(embed=embed_new_create(explore_attempts, explore_report, ""))

                    if explore_attempts == spirits:

                        explores.update_one({
                            "user_id": str(user.id),
                            "explores.completion": False}, {
                            "$set": {
                                "explores.$.completion": True
                            }
                        })
                        explore_report = explores.find_one({
                            "user_id": str(user.id), "explores.completion": True}, {
                            "_id": 0, "explores.$": 1,
                        })["explores"][0]["logs"]

                        await msg.edit(embed=embed_new_create(spirits, explore_report, "~~"))
                        await process_msg_reaction_clear(msg)

                        embed_final = embed_new_create(spirits, explore_report, "~~")
                        await self.perform_exploration_process_rewards(user.id, msg, embed_final, zone)
                        exploration_check_add_unlocked(user, chapter)
                        break

                else:
                    explores.update_one({
                        "user_id": str(user.id), "explores.completion": False}, {
                        "$push": {"explores.$.logs": "❌"}
                    })
                    query = explores.find_one({
                        "user_id": str(user.id), "explores.completion": False}, {
                        "_id": 0,
                        "explores.$": 1,
                    })
                    explore_report = query["explores"][0]["logs"]
                    explore_attempts = query['explores'][0]['attempts']
                    await msg.edit(embed=embed_new_create(explore_attempts, explore_report, ""))

                await msg.remove_reaction(str(reaction.emoji), user)

    async def perform_exploration_process_rewards(self, user_id, msg, embed_final, zone):

        lower, upper = 0.8, 1.1
        jades = round(random.uniform(zone["rewards_exact"]["jades"] * lower, zone["rewards_exact"]["jades"] * upper))
        coins = round(random.uniform(zone["rewards_exact"]["coins"] * lower, zone["rewards_exact"]["coins"] * upper))
        medals = round(random.uniform(zone["rewards_exact"]["medals"] * lower, zone["rewards_exact"]["medals"] * upper))
        amulets_b = zone["rewards_exact"]["amulets_b"] + random.randint(0, 2)

        users.update_one({
            "user_id": str(user_id)
        }, {
            "$inc": {
                "jades": jades,
                "coins": coins,
                "medals": medals,
                "amulets_b": amulets_b,
            }
        })
        await perform_add_log("jades", jades, user_id)
        await perform_add_log("coins", coins, user_id)
        await perform_add_log("medals", medals, user_id)
        await perform_add_log("amulets_b", amulets_b, user_id)

        shikigami_pool = pool_ssr + pool_sp + pool_sr + pool_r + pool_n
        shikigami_pool_count = {shiki: 0 for shiki in shikigami_pool}

        for rarity in zone["shards_count"]:
            i = 0
            while i < zone["shards_count"][rarity]:
                shikigami_shard = get_random_shikigami(rarity)
                shikigami_pool_count[shikigami_shard] += 1
                i += 1

        shards_reward = list(shikigami_pool_count.items())
        await self.perform_exploration_issue_shard_rewards(user_id, shards_reward)

        link = await self.perform_exploration_generate_shards(user_id, shards_reward)
        embed_final.set_image(url=link)
        embed_final.add_field(
            name="Completion rewards",
            value=f"{jades:,d}{get_emoji('jades')}, "
                  f"{coins:,d}{get_emoji('coins')}, "
                  f"{medals:,d}{get_emoji('medals')}, "
                  f"{amulets_b:,d}{get_emoji('amulets_b')}",
            inline=False
        )
        await process_msg_edit(msg, None, embed_final)

    async def perform_exploration_generate_shards(self, user_id, shards_reward):

        images, font = [], font_create(30)
        x, y, cols = 1, 60, 8
        rows = 90 * cols

        for entry in shards_reward:
            if entry[1] != 0:
                address = f"data/shikigamis/{entry[0]}_pre.jpg"

                shikigami_thumbnail = Image.open(address)
                shikigami_image_final = generate_shikigami_with_shard(shikigami_thumbnail, entry[1], font, x, y)
                images.append(shikigami_image_final)
            else:
                continue

        width, height = get_image_variables(images, cols, rows)
        new_im = Image.new("RGBA", (width, height))

        for index, item in enumerate(images):
            new_im.paste(images[index], (get_shiki_tile_coordinates(index + 1, cols, rows)))

        address = f"temp/{user_id}.png"
        new_im.save(address)
        image_file = discord.File(address, filename=f"{user_id}.png")
        hosting_channel = self.client.get_channel(int(id_hosting))
        msg = await process_msg_submit_file(hosting_channel, image_file)
        attachment_link = msg.attachments[0].url
        return attachment_link

    async def perform_exploration_issue_shard_rewards(self, user_id, shards_reward):
        trimmed = []
        for entry in shards_reward:
            if entry[1] != 0:
                trimmed.append(entry)
            else:
                continue

        for shikigami_shard in trimmed:

            query = users.find_one({
                "user_id": str(user_id),
                "shikigami.name": shikigami_shard[0]}, {
                "_id": 0, "shikigami.$": 1
            })

            if query is None:
                evolve, shards = False, 0
                if get_rarity_shikigami(shikigami_shard[0]) == "SP":
                    evolve, shards = True, 0
                shikigami_push_user(user_id, shikigami_shard[0], evolve, shards)

            users.update_one({"user_id": str(user_id), "shikigami.name": shikigami_shard[0]}, {
                "$inc": {
                    "shikigami.$.shards": 1
                }
            })

    @commands.command(aliases=["chapter", "ch"])
    @commands.guild_only()
    async def show_exploration_zones(self, ctx, *, arg1=None):

        if arg1 is None:
            embed = discord.Embed(
                title=f"chapter, ch", color=colour,
                description=f"shows chapter information and unlocked chapters"
            )
            embed.add_field(
                name="Format", inline=False,
                value=f"*`{self.prefix}chapter <chapter#1-28>`*\n"
                      f"*`{self.prefix}chapter unlocked`*\n"
            )
            await process_msg_submit(ctx.channel, None, embed)

        elif arg1.lower() in ["unlocked"]:

            ch_unlocked = users.find_one({"user_id": str(ctx.author.id)}, {"_id": 0, "exploration": 1})['exploration']
            embed = discord.Embed(
                color=ctx.author.colour,
                description=f"You have access up to chapter {ch_unlocked}",
                timestamp=get_timestamp()
            )
            embed.set_footer(text=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            await process_msg_submit(ctx.channel, None, embed)

        else:
            try:
                chapter = int(arg1)
            except ValueError:
                return

            ch_unlocked = zones.find_one({"chapter": chapter}, {"_id": 0})

            try:
                description = f"```" \
                              f"Spirits          ::    {ch_unlocked['spirits']}\n" \
                              f"Sushi/explore    ::    {ch_unlocked['sushi_required']}" \
                              f"```"

                jades = ch_unlocked["rewards_exact"]["jades"]
                coins = ch_unlocked["rewards_exact"]["coins"]
                medals = ch_unlocked["rewards_exact"]["medals"]
                amulets_b = ch_unlocked["rewards_exact"]["amulets_b"]

                shards_sp = ch_unlocked["shards_count"]["SP"]
                shards_ssr = ch_unlocked["shards_count"]["SSR"]
                shards_sr = ch_unlocked["shards_count"]["SR"]
                shards_r = ch_unlocked["shards_count"]["R"]
                shards_n = ch_unlocked["shards_count"]["N"]

                embed = discord.Embed(
                    title=f"Chapter {chapter}: {ch_unlocked['name']}",
                    color=ctx.author.colour,
                    description=description
                )
                embed.add_field(
                    name="Completion rewards",
                    value=f"~{jades:,d}{get_emoji('jades')}, "
                          f"~{coins:,d}{get_emoji('coins')}, "
                          f"~{medals:,d}{get_emoji('medals')}, "
                          f"~{amulets_b:,d}{get_emoji('amulets_b')}",
                    inline=False
                )
                embed.add_field(
                    name="Shards drop count",
                    value=f"{e_1} {shards_sp} | {e_2} {shards_ssr} | {e_3} {shards_sr} | "
                          f"{e_4} {shards_r} | {e_5} {shards_n}",
                    inline=False
                )
                await process_msg_submit(ctx.channel, None, embed)

            except TypeError:
                embed = discord.Embed(
                    title=f"Invalid chapter",
                    color=colour,
                    description="Available chapters: 1-28 only"
                )
                await process_msg_submit(ctx.channel, None, embed)


def setup(client):
    client.add_cog(Exploration(client))
