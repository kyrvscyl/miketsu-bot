"""
Error Module
Miketsu, 2020
"""
import asyncio
import random
from math import ceil, floor

from PIL import Image, ImageDraw, ImageFont
from discord.ext import commands

from cogs.ext.initialize import *


class Beta(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.prefix = self.client.command_prefix

    @commands.command(aliases=["souls"])
    @commands.guild_only()
    async def process_souls(self, ctx, *, args=None):

        if args is None:
            embed = discord.Embed(
                title="souls",
                description="shows your souls inventory or challenge one",
                color=colour
            )
            embed.add_field(
                name="Formats",
                value=f"*`{self.prefix}souls <name>`*\n"
                      f"*`{self.prefix}souls <1-10>`*"
            )
            await process_msg_submit(ctx.channel, None, embed)

        elif args.lower() is not None and args in souls_all:
            await self.process_souls_show_users(ctx, ctx.author, args.lower())

        elif args.lower() is not None and args in soul_dungeons:
            query = users.find_one({"user_id": str(ctx.author.id)}, {"_id": 0, "souls_unlocked": 1})

            if query["souls_unlocked"] >= int(args):
                await self.process_souls_explore(args.lower(), ctx.author, ctx, query["souls_unlocked"])
            else:
                embed = discord.Embed(
                    title="Invalid stage",
                    description=f"You only have access up to {query['souls_unlocked']}",
                    color=colour
                )
                await process_msg_submit(ctx.channel, None, embed)

    async def process_souls_explore(self, stage, user, ctx, unlocked):

        sushi_required = 4
        users.update_one({
            "user_id": str(user.id)
        }, {
            "$inc": {
                "sushi": - sushi_required
            }
        })
        await perform_add_log("sushi", -sushi_required, user.id)

        def get_shikigami_stats(user_id, shiki):
            p = users.find_one({
                "user_id": str(user_id), "shikigami.name": shiki
            }, {
                "_id": 0,
                "shikigami.$": 1
            })
            return p["shikigami"][0]["level"], p["shikigami"][0]["evolved"], p["shikigami"][0]["exp"], \
                   p["shikigami"][0]["level_exp_next"]


        user_profile = users.find_one({"user_id": str(user.id)}, {"_id": 0, "level": 1, "display": 1, "exploration": 1})
        user_level = user_profile["level"]
        shikigami_set = user_profile["display"]
        shikigami_level, shikigami_evolved, shikigami_exp, shikigami_exp_x = get_shikigami_stats(user.id, shikigami_set)

        thumbnail = get_thumbnail_shikigami(shikigami_set, get_evo_link(shikigami_evolved))

        evo_adjustment = 1
        if shikigami_evolved is True:
            evo_adjustment = 0.75

        total_chance = user_level + shikigami_level - (int(stage) * 3) * evo_adjustment

        if total_chance <= 50:
            total_chance = 50

        adjusted_chance = random.uniform(total_chance * 0.95, total_chance)
        rounds = 1

        if explores.find_one({"user_id": str(user.id)}, {"_id": 0, "souls": 1}) is None:
            explores.update({"user_id": str(user.id)}, {"$set": {"souls": []}})

        explores.update_one({
            "user_id": str(user.id)
        }, {
            "$push": {
                "souls": {
                    "$each": [{
                        "attempts": 0,
                        "clears": 0,
                        "required": 3,
                        "stage": int(stage),
                        "completion": None,
                        "date": get_time(),
                    }],
                    "$position": 0
                }
            }
        })

        progress = []

        def embed_new_create(r, strike):

            description2 = ""
            for log in progress:
                description2 += log

            embed_new_souls = discord.Embed(
                color=user.colour,
                title=f"{strike}Soul Stage: {stage} :: Round {r} of 3{strike}",
                description=description2,
                timestamp=get_timestamp()
            )
            embed_new_souls.set_footer(text=user.display_name, icon_url=user.avatar_url)
            embed_new_souls.set_thumbnail(url=thumbnail)

            user_profile_new = users.find_one({
                "user_id": str(user.id), "shikigami.name": user_profile["display"]
            }, {
                "_id": 0, "shikigami.$": 1, "sushi": 1
            })

            embed_new_souls.add_field(
                name=f"Shikigami: {shikigami_set.title()} | {user_profile_new['sushi']} {e_s}",
                value=f"Level: {shikigami_level} | Experience: {shikigami_exp}/{shikigami_exp_x}\n"
                      f"Clear Chance: ~{round(total_chance, 2)}%"
            )

            """def get_soul_stage_thumbnail(s, r_):
                query = config.find_one({"list": 1}, {"_id": 0, "souls": 1})["souls"]
                return query[s][r_ - 1]

            embed_new_souls.set_image(url=get_soul_stage_thumbnail(stage, r))"""
            return embed_new_souls

        msg = await ctx.channel.send(embed=embed_new_create(rounds, ""))
        await msg.add_reaction("🏹")

        def check(r, u):
            return msg.id == r.message.id and str(r.emoji) == "🏹" and u.id == ctx.author.id

        while True:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=60, check=check)
            except asyncio.TimeoutError:
                await process_msg_reaction_clear(msg)
                break
            else:
                roll = random.uniform(0, 100)
                if roll > adjusted_chance:
                    explores.update_one({
                        "user_id": str(user.id), "souls.completion": None}, {
                        "$inc": {
                            "souls.0.attempts": 1,
                            "souls.0.clears": 0,
                        },
                        "$set": {
                            "souls.0.completion": False
                        }
                    })
                    progress.append("❌")
                    await msg.edit(embed=embed_new_create(rounds, "~~"))
                    await process_msg_reaction_clear(msg)
                    break
                else:
                    explores.update_one({
                        "user_id": str(user.id), "souls.completion": None}, {
                        "$inc": {
                            "souls.0.attempts": 1,
                            "souls.0.clears": 1,
                        }
                    })
                    progress.append("✅")

                    last_souls = explores.find_one({"user_id": str(user.id)}, {
                        "_id": 0, "explores": 0, "souls": {"$slice": 1}
                    })["souls"][0]

                    if last_souls["required"] == last_souls["clears"]:
                        embed_complete = embed_new_create(rounds, "~~")
                        await self.process_souls_explore_rewards(embed_complete, user, stage, msg, ctx, unlocked)
                        await process_msg_reaction_clear(msg)
                        break

                    else:
                        rounds += 1
                        await msg.edit(embed=embed_new_create(rounds, ""))

    async def process_souls_explore_rewards(self, embed, user, stage, msg, ctx, unlocked):

        def get_slot(s):
            dictionary = {
                0: 1,
                1: 2,
                2: 3,
                4: 4,
                5: 5,
                6: 6,
            }
            return dictionary[s]

        def generate_amount_soul(s):
            dictionary = {
                1: [3, 2],
                2: [3, 2],
                3: [4, 2],
                4: [5, 3],
                5: [5, 3],
                6: [5, 4],
                7: [6, 5],
                8: [7, 6],
                9: [7, 7],
                10: [8, 8],
            }
            min_souls = dictionary[s][0]
            max_souls = dictionary[s][0] + dictionary[s][1]
            return min_souls, max_souls

        def generate_exp_soul(s):
            dictionary = {
                1: [1, 0.25, 0, 0, 0, 0],
                2: [1, 0.15, 0.2, 0, 0, 0],
                3: [1, 0.25, 0.25, 0.1, 0, 0],
                4: [0, 1, 0.5, 0.25, 0, 0],
                5: [0, 1, 0.35, 0.4, 0, 0],
                6: [0, 1, 0.25, 0.45, 0.1, 0],
                7: [0, 0, 1, 0.5, 0.25, 0],
                8: [0, 0, 1, 0.55, 0.35, 0],
                9: [0, 0, 0, 1, 0.45, 0.1],
                10: [0, 0, 0, 1, 0.5, 0.15],
            }
            select_list = list(reversed(dictionary[s]))
            for index, entry in enumerate(select_list):
                roll = random.uniform(0, 1)
                if roll <= entry:
                    return 6 - index

        def get_y_off(index):
            return floor(index/6)

        def generate_shikigami_list(text):
            font = ImageFont.truetype('data/marker_felt_wide.ttf', 20)
            im = Image.new('RGBA', (w, 22), (255, 0, 0, 0))
            outline = ImageDraw.Draw(im)
            outline.text((x_outline, y_outline + 1), text, font=font, fill=(255, 255, 255, 128))

            outline = ImageDraw.Draw(im)
            outline.text((x_outline - 1, y_outline - 1), text, font=font, fill="black")
            outline.text((x_outline + 1, y_outline - 1), text, font=font, fill="black")
            outline.text((x_outline - 1, y_outline + 1), text, font=font, fill="black")
            outline.text((x_outline + 1, y_outline + 1), text, font=font, fill="black")
            outline.text((x_outline, y_outline), text, font=font)

            return im

        day = get_time().strftime("%a").lower()
        souls_rewards = []
        soul_slots = [0, 1, 2, 4, 5, 6]
        x_outline, y_outline = 22, 0
        max_width_soul, max_height_soul = 120, 100
        max_souls_line = 6
        x_off = 0

        if day in ["sat", "sun"]:
            for document in souls.find({"source.souls_weekend": True}, {"_id": 0, "name": 1}):
                souls_rewards.append(document["name"])

        for document in souls.find({"source.souls_weekday": day}, {"_id": 0, "name": 1}):
            souls_rewards.append(document["name"])

        soul_raw_address = "data/raw/soul_slot.png"
        a, b = generate_amount_soul(int(stage))
        souls_rewards_total = random.choice(list(range(a, b + 1)))
        total_height = ceil(souls_rewards_total/max_souls_line) * max_height_soul
        total_width = max_souls_line * max_width_soul

        bd = Image.new("RGBA", (total_width, total_height))

        soul_exp_list = []

        for i, document in enumerate(range(1, souls_rewards_total + 1)):

            if i % 6 == 0:
                x_off = 0

            soul_select = random.choice(souls_rewards)
            soul1_address = f"data/souls/{soul_select}.png"
            soul_im = Image.open(soul1_address)
            w, h = soul_im.size

            slot = random.choice(soul_slots)
            rotation = slot * 45
            exp_multiplier = generate_exp_soul(int(stage))

            exp_total = 30
            for e in range(1, exp_multiplier):
                exp_total *= 3

            adjusted_exp_total = round(random.uniform(exp_total * 0.95, exp_total * 1.05))
            soul_exp_list.append([soul_select, adjusted_exp_total, get_slot(slot)])
            adjusted_exp_total_ = generate_shikigami_list(str(adjusted_exp_total))

            soul_im.paste(adjusted_exp_total_, (0, 60), adjusted_exp_total_)

            if rotation in [45, 45 + 180]:
                d = 136
                soul_final_im = Image.open(soul_raw_address).rotate(rotation, resample=Image.BICUBIC, expand=True).\
                    resize((d, d), Image.ANTIALIAS)
                soul_final_im.paste(soul_im, (int(d / 4) - 6, int(d / 4) - 6), soul_im)

                w_, h_ = soul_final_im.size

                if rotation == 45:
                    left = 0
                    top = int(((h_ - 90) / 2) - 5)
                    right = int(d - (d - 90) + 30)
                    bottom = int(d - top)
                else:
                    left = int(136 - (d - (d - 90) + 30))
                    top = int(((h_ - 90) / 2) - 5)
                    right = d
                    bottom = int(d - top)

                x__ = soul_final_im.crop((left, top, right, bottom))
                bd.paste(x__, (x_off, get_y_off(i) * 100))
                w_, h_ = x__.size
                x_off += w_
            else:
                adj = 16
                h_f = h + adj
                w_f = w + adj
                soul_final_im = Image.open(soul_raw_address).rotate(rotation, resample=Image.BICUBIC, expand=True).\
                    resize((w_f, h_f), Image.ANTIALIAS)
                soul_final_im.paste(soul_im, (0 + int(adj / 2), 0 + int(adj / 2)), soul_im)
                bd.paste(soul_final_im, (x_off, get_y_off(i) * 100))
                w_, h_ = soul_final_im.size
                x_off += w_

        temp_address = f"temp/{user.id}.png"
        bd.save(temp_address, quality=95)

        new_photo = discord.File(temp_address, filename=f"{ctx.message.id}.png")
        hosting_channel = self.client.get_channel(int(id_hosting))
        msg1 = await hosting_channel.send(file=new_photo)
        attachment_link = msg1.attachments[0].url

        scales = 0
        scales_rev = 0

        embed.add_field(
            name="Rewards",
            value=f"Reversed scales: `{scales_rev}`\n"
                  f"Normal Scales: `{scales}`\n"
                  f"# Dropped of Souls: `{souls_rewards_total}`",
            inline=False
        )
        embed.set_image(url=attachment_link)
        await self.process_souls_experience_add(user, soul_exp_list)
        await msg.edit(embed=embed)

        if unlocked == int(stage):
            users.update_one({"user_id": str(user.id), "souls_unlocked": {"$lt": 10}}, {"$inc": {"souls_unlocked": 1}})

    async def process_souls_experience_add(self, user, soul_exp_list):

        for s in soul_exp_list:
            s, exp, slot = s[0], s[1], s[2]

            if users.find_one({"user_id": str(user.id), f"souls.{s}": {"$type": "object"}}, {"_id": 0}) is None:
                users.update_one({"user_id": str(user.id)}, {"$set": {f"souls.{s}": []}})

            x = users.update_one({
                "user_id": str(user.id), "$and": [{f"souls.{s}": {"$elemMatch": {"slot": slot}}}]
            }, {
                "$inc": {
                    f"souls.{s}.$.exp": exp
                }
            })

            if x.modified_count == 0:
                users.update_one({"user_id": str(user.id)}, {
                    "$push": {
                        f"souls.{s}": {
                            "grade": 1,
                            "slot": slot,
                            "level": 1,
                            "exp": exp,
                            "lvl_exp_next": 7000,
                            "equipped": None
                        }
                    }
                })

            await self.process_souls_level_up(user, s, slot)

    async def process_souls_level_up(self, user, soul_name, slot):

        soul_data = users.find_one({
            "user_id": str(user.id), "$and": [{f"souls.{soul_name}": {"$elemMatch": {"slot": slot}}}]
        }, {
            "_id": 0,
            f"souls.{soul_name}": 1
        })
        if soul_data["souls"][soul_name][0]["lvl_exp_next"] >= soul_data["souls"][soul_name][0]["exp"]:
            def get_lvl_exp_next_new(g):
                dictionary = {
                    1: 0,
                    2: 7000,
                    3: 21000,
                    4: 63000,
                    5: 189000,
                    6: 567000
                }
                return dictionary[g]

            grade_next = soul_data["souls"][soul_name][0]["grade"] + 1
            lvl_exp_next_new = get_lvl_exp_next_new(grade_next)
            users.update_one({
                "user_id": str(user.id),
                "$and": [{f"souls.{soul_name}": {"$elemMatch": {"slot": slot}}}]
            }, {
                "$set": {
                    f"souls.{soul_name}.$.lvl_exp_next": lvl_exp_next_new
                }
            })

    async def process_souls_show_users(self, ctx, user, soul_select):

        embed = discord.Embed(
            color=ctx.author.colour,
            timestamp=get_timestamp()
        )
        embed.set_author(
            name=f"{soul_select.title()} Souls Stats",
            icon_url=ctx.author.avatar_url
        )
        embed.set_thumbnail(url=get_soul_thumbnail(soul_select))

        try:
            user_souls = users.find_one({
                "user_id": str(user.id)}, {
                "_id": 0,  f"souls.{soul_select}": 1
            })["souls"][soul_select]

        except KeyError:
            embed = discord.Embed(
                color=colour,
                title=f"Invalid soul",
                description=f"You do not own any of this soul"
            )
            await process_msg_submit(ctx.channel, None, embed)
            return

        except TypeError:
            embed = discord.Embed(
                color=colour,
                title=f"Invalid soul",
                description=f"You do not own any of this soul"
            )
            await process_msg_submit(ctx.channel, None, embed)
            return

        souls_formatted = []

        for s in user_souls:
            souls_formatted.append(
                [s["slot"], s["grade"], s["level"], s["exp"], s["lvl_exp_next"], s["equipped"]]
            )

        for s in sorted(souls_formatted, key=lambda x: x[0], reverse=True):

            try:
                shiki = s[5].title()
            except AttributeError:
                shiki = "`None`"

            embed.add_field(
                name=f"`[Slot {s[0]}]` | Grade {s[1]}",
                value=f"Level: `{s[2]}/15` :: Exp: `{s[3]}/{s[4]}`\n"
                      f"Equipped to: {shiki}",
                inline=False
            )

        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["rca"])
    @commands.is_owner()
    async def realm_card_add(self, ctx, args):

        # ;rc moon 1 experience 130 link

        profile = {
            "name": args[0].lower(),
            "base": int(args[1]),
            "rewards": args[2],
            "link": args[4]
        }
        realms.insert_one(profile)
        await process_msg_reaction_add(ctx.message, "✅")


def setup(client):
    client.add_cog(Beta(client))
