"""
Realm Module
Miketsu, 2020
"""

import asyncio
import random
from math import ceil

from PIL import Image, ImageDraw, ImageFont
from discord.ext import commands

from cogs.ext.initialize import *


class Exploration(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.prefix = self.client.command_prefix

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
    @commands.check(check_if_user_has_shiki_set)
    @commands.cooldown(1, 500, commands.BucketType.user)
    async def perform_exploration(self, ctx, *, arg):
        user = ctx.author

        try:
            chapter = int(arg)
            await self.perform_exploration_by_chapter(chapter, user, ctx)
        except ValueError:
            if arg.lower() in ["last", "unf", "unfinished"]:
                query = explores.find_one({
                    "user_id": str(user.id),
                    "explores.completion": False
                }, {
                    "_id": 0,
                    "explores.$": 1
                })
                try:
                    chapter = query["explores"][0]["chapter"]
                    await self.perform_exploration_by_chapter(chapter, user, ctx)
                    self.client.get_command("perform_exploration").reset_cooldown(ctx)
                except TypeError:
                    embed = discord.Embed(
                        color=ctx.author.colour,
                        description=f"You have no pending explorations",
                        timestamp=get_timestamp()
                    )
                    embed.set_footer(text=user.display_name, icon_url=user.avatar_url)
                    await process_msg_submit(ctx.channel, None, embed)
                    self.client.get_command("perform_exploration").reset_cooldown(ctx)

            else:
                embed = discord.Embed(
                    color=ctx.author.colour,
                    title="Invalid chapter",
                    description=f"that is not a valid chapter",
                )
                await process_msg_submit(ctx.channel, None, embed)
                self.client.get_command("perform_exploration").reset_cooldown(ctx)

    async def perform_exploration_by_chapter(self, chapter, user, ctx):

        zone = zones.find_one({"chapter": chapter}, {"_id": 0})
        user_profile = users.find_one({"user_id": str(user.id)}, {"_id": 0, "level": 1, "display": 1, "exploration": 1})

        if chapter > zones.count():
            embed = discord.Embed(
                color=ctx.author.colour,
                title="Invalid chapter",
                description=f"that is not a valid chapter, < {zones.count()}",
            )
            await process_msg_submit(ctx.channel, None, embed)

        elif chapter > user_profile["exploration"]:
            embed = discord.Embed(
                color=user.colour,
                title="Invalid chapter",
                description=f"you have not yet unlocked this chapter",
            )
            await process_msg_submit(ctx.channel, None, embed)
            self.client.get_command("perform_exploration").reset_cooldown(ctx)

        else:
            def get_shikigami_stats(user_id, shiki):
                p = users.find_one({
                    "user_id": str(user_id), "shikigami.name": shiki
                }, {
                    "_id": 0,
                    "shikigami.$": 1
                })
                return p["shikigami"][0]["level"], p["shikigami"][0]["evolved"]

            spirits = zone["spirits"]
            sushi_required = zone["sushi_required"]
            user_level = user_profile["level"]
            shikigami_set = user_profile["display"]
            shikigami_level, shikigami_evolved = get_shikigami_stats(user.id, shikigami_set)

            thumbnail = get_thumbnail_shikigami(shikigami_set, get_evo_link(shikigami_evolved))

            evo_adjustment = 1
            if shikigami_evolved is True:
                evo_adjustment = 0.75

            total_chance = user_level + shikigami_level - chapter * evo_adjustment
            if total_chance <= 40:
                total_chance = 40

            adjusted_chance = random.uniform(total_chance * 0.95, total_chance)

            def create_embed_exploration(x, progress, strike):

                description2 = ""
                for log in progress:
                    description2 += log

                num = x + 1
                if num > spirits:
                    num = spirits

                user_profile_new = users.find_one({
                    "user_id": str(user.id), "shikigami.name": user_profile["display"]
                }, {
                    "_id": 0, "shikigami.$": 1, "sushi": 1
                })
                experience = user_profile_new["shikigami"][0]['exp']
                level_exp_next = user_profile_new["shikigami"][0]['level_exp_next']
                shiki_level = user_profile_new["shikigami"][0]['level']

                embed_explore = discord.Embed(
                    color=ctx.author.colour,
                    title=f"{strike}Exploration stage: {num}/{spirits}{strike}",
                    description=f"Chapter {chapter}: {zone['name']}\n{description2}",
                    timestamp=get_timestamp()
                )
                embed_explore.add_field(
                    name=f"Shikigami: {shikigami_set.title()} | {user_profile_new['sushi']} {e_s}",
                    value=f"Level: {shiki_level} | Experience: {experience}/{level_exp_next}\n"
                          f"Clear Chance: ~{round(total_chance, 2)}%"
                )
                embed_explore.set_footer(
                    text=f"{ctx.author.display_name}",
                    icon_url=ctx.author.avatar_url
                )
                embed_explore.set_thumbnail(url=thumbnail)

                return embed_explore

            if explores.find_one({"user_id": str(user.id)}, {"_id": 0}) is None:
                profile = {
                    "user_id": str(user.id),
                    "explores": []
                }
                explores.insert_one(profile)

            exploration_continuation = explores.find_one({
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
            })

            if exploration_continuation is None:
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

            new_explore = explores.find_one({
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
            })

            msg = await ctx.channel.send(
                embed=create_embed_exploration(new_explore['explores'][0]['attempts'], [], "")
            )
            await msg.add_reaction("🏹")

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
                    users.update_one({
                        "user_id": str(user.id)
                    }, {
                        "$inc": {
                            "sushi": - sushi_required
                        }
                    })
                    await perform_add_log("sushi", -sushi_required, ctx.author.id)

                    roll = random.uniform(0, 100)
                    if roll < adjusted_chance:
                        explores.update_one({
                            "user_id": str(user.id), "explores.completion": False}, {
                            "$inc": {
                                "explores.$.attempts": 1
                            }
                        })

                        explores.update_one({
                            "user_id": str(user.id), "explores.completion": False}, {
                            "$push": {
                                "explores.$.logs": "✅"
                            }
                        })
                        new_explore = explores.find_one({
                            "user_id": str(user.id), "explores.completion": False}, {
                            "_id": 0,
                            "explores.$": 1,
                        })
                        shikigami_add_exp = users.update_one({
                            "user_id": str(user.id),
                            "$and": [{
                                "shikigami": {
                                    "$elemMatch": {
                                        "name": user_profile["display"],
                                        "level": {"$lt": 40}}
                                }}]
                        }, {
                            "$inc": {
                                "shikigami.$.exp": 5 * round((chapter + 1) / 2)
                            }
                        })

                        if shikigami_add_exp.modified_count > 0:
                            await shikigami_process_levelup(user.id, user_profile["display"])

                        report = new_explore["explores"][0]["logs"]
                        await msg.edit(
                            embed=create_embed_exploration(new_explore['explores'][0]['attempts'], report, "")
                        )

                        if new_explore["explores"][0]["attempts"] == spirits:
                            explores.update_one({
                                "user_id": str(user.id), "explores.completion": False}, {
                                "$set": {
                                    "explores.$.completion": True
                                }
                            })
                            new_explore = explores.find_one({
                                "user_id": str(user.id), "explores.completion": True}, {
                                "_id": 0,
                                "explores.$": 1,
                            })
                            report = new_explore["explores"][0]["logs"]
                            await msg.edit(embed=create_embed_exploration(spirits, report, "~~"))
                            await process_msg_reaction_clear(msg)

                            embed_new = create_embed_exploration(spirits, report, "~~")
                            await self.perform_exploration_process_rewards(user.id, msg, embed_new, chapter)

                            explorations = users.find_one({"user_id": str(user.id)}, {"_id": 0, "exploration": 1})

                            if chapter == explorations["exploration"]:
                                users.update_one({
                                    "user_id": str(user.id),
                                    "exploration": {
                                        "$lt": 28
                                    }
                                }, {
                                    "$inc": {
                                        "exploration": 1
                                    }
                                })
                            break

                    else:
                        explores.update_one({
                            "user_id": str(user.id), "explores.completion": False}, {
                            "$push": {
                                "explores.$.logs": "❌"
                            }
                        })
                        new_explore = explores.find_one({
                            "user_id": str(user.id), "explores.completion": False}, {
                            "_id": 0,
                            "explores.$": 1,
                        })
                        report = new_explore["explores"][0]["logs"]
                        await msg.edit(
                            embed=create_embed_exploration(new_explore['explores'][0]['attempts'], report, "")
                        )

                    await msg.remove_reaction(str(reaction.emoji), user)

        self.client.get_command("perform_exploration").reset_cooldown(ctx)

    async def perform_exploration_process_rewards(self, user_id, msg, embed, chapter):

        zone = zones.find_one({"chapter": chapter})

        jades = round(random.uniform(zone["rewards_exact"]["jades"] * 0.8, zone["rewards_exact"]["jades"] * 1.1))
        coins = round(random.uniform(zone["rewards_exact"]["coins"] * 0.8, zone["rewards_exact"]["coins"] * 1.1))
        medals = round(random.uniform(zone["rewards_exact"]["medals"] * 0.8, zone["rewards_exact"]["medals"] * 1.1))
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

        shards_sp = zone["shards_count"]["SP"]
        shards_ssr = zone["shards_count"]["SSR"]
        shards_sr = zone["shards_count"]["SR"]
        shards_r = zone["shards_count"]["R"]
        shards_n = zone["shards_count"]["N"]

        shikigami_pool = {shiki: 0 for shiki in pool_ssr + pool_sp + pool_sr + pool_r + pool_n}

        i = 0
        while i < shards_sp:
            shikigami_shard = random.choice(pool_sp)
            shikigami_pool[shikigami_shard] += 1
            i += 1

        i = 0
        while i < shards_ssr:
            shikigami_shard = random.choice(pool_ssr)
            shikigami_pool[shikigami_shard] += 1
            i += 1

        i = 0
        while i < shards_sr:
            shikigami_shard = random.choice(pool_sr)
            shikigami_pool[shikigami_shard] += 1
            i += 1

        i = 0
        while i < shards_r:
            shikigami_shard = random.choice(pool_r)
            shikigami_pool[shikigami_shard] += 1
            i += 1

        i = 0
        while i < shards_n:
            shikigami_shard = random.choice(pool_n)
            shikigami_pool[shikigami_shard] += 1
            i += 1

        shards_reward = list(shikigami_pool.items())
        await self.perform_exploration_issue_shard_rewards(user_id, shards_reward)

        link = await self.perform_exploration_generate_shards(user_id, shards_reward)
        embed.set_image(url=link)

        embed.add_field(
            name="Completion rewards",
            value=f"{jades:,d}{get_emoji('jades')}, "
                  f"{coins:,d}{get_emoji('coins')}, "
                  f"{medals:,d}{get_emoji('medals')}, "
                  f"{amulets_b:,d}{get_emoji('amulets_b')}",
            inline=False
        )
        await msg.edit(embed=embed)

    async def perform_exploration_generate_shards(self, user_id, shards_reward):

        images = []

        font = ImageFont.truetype('data/marker_felt_wide.ttf', 30)
        x, y = 1, 60

        def generate_shikigami_with_shard(shikigami_thumbnail_select, shards_count):

            outline = ImageDraw.Draw(shikigami_thumbnail_select)
            outline.text((x - 1, y - 1), str(shards_count), font=font, fill="black")
            outline.text((x + 1, y - 1), str(shards_count), font=font, fill="black")
            outline.text((x - 1, y + 1), str(shards_count), font=font, fill="black")
            outline.text((x + 1, y + 1), str(shards_count), font=font, fill="black")
            outline.text((x, y), str(shards_count), font=font)

            return shikigami_thumbnail_select

        for entry in shards_reward:
            if entry[1] != 0:
                address = f"data/shikigamis/{entry[0]}_pre.jpg"

                shikigami_thumbnail = Image.open(address)
                shikigami_image_final = generate_shikigami_with_shard(shikigami_thumbnail, entry[1])
                images.append(shikigami_image_final)
            else:
                continue

        dimensions = 90
        max_c = 8
        w = 90 * max_c

        def get_image_variables(h):
            total_frames = len(h)
            h = ceil(total_frames / max_c) * dimensions
            return w, h

        width, height = get_image_variables(images)
        new_im = Image.new("RGBA", (width, height))

        def get_coordinates(c):
            a = (c * dimensions - (ceil(c / max_c) - 1) * (dimensions * max_c)) - dimensions
            b = (ceil(c / max_c) * dimensions) - dimensions
            return a, b

        for index, item in enumerate(images):
            new_im.paste(images[index], (get_coordinates(index + 1)))

        address = f"temp/{user_id}.png"
        new_im.save(address)
        new_photo = discord.File(address, filename=f"{user_id}.png")
        hosting_channel = self.client.get_channel(int(id_hosting))
        msg = await hosting_channel.send(file=new_photo)
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
