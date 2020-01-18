"""
Souls Module
Miketsu, 2020
"""

from math import floor

from PIL import Image
from discord.ext import commands

from cogs.ext.initialize import *


class Souls(commands.Cog):

    def __init__(self, client):

        self.client = client
        self.prefix = self.client.command_prefix

        self.soul_raw_address = "data/raw/soul_slot.png"

        self.souls_rewards = []
        self.souls_rewards_generate()

    def souls_rewards_generate(self):

        day = get_time().strftime("%a").lower()
        self.souls_rewards.clear()

        if day in ["sat", "sun"]:
            for document in souls.find({"source.souls_weekend": True}, {"_id": 0, "name": 1}):
                self.souls_rewards.append(document["name"])

        for document in souls.find({"source.souls_weekday": day}, {"_id": 0, "name": 1}):
            self.souls_rewards.append(document["name"])

    async def souls_equip_help(self, ctx):

        embed = discord.Embed(
            title="equip, eq", color=colour,
            description=f"equip your shikigami with souls to obtain bonus clear chances",
        )
        embed.add_field(name="Formats", inline=False, value=f"*`{self.prefix}equip 6 watcher`*")
        await process_msg_submit(ctx.channel, None, embed)

    async def souls_help(self, ctx):

        embed = discord.Embed(
            title="souls", color=colour,
            description="shows your souls inventory or challenge one"
        )
        embed.add_field(
            name="Formats", inline=False,
            value=f"*`{self.prefix}souls <name>`*\n"
                  f"*`{self.prefix}souls <1-10>`*"
        )
        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["equip", "eq"])
    @commands.guild_only()
    async def souls_shikigami_equip(self, ctx, slot=None, *, args=None):

        if slot is None or args is None:
            await self.souls_equip_help(ctx)

        elif args not in souls_all:
            await self.souls_show_approximate(ctx, args)

        elif slot in [f"{x}" for x in list(range(1, 7))] and args.lower() in souls_all:

            user = ctx.author
            soul_select = args.lower()
            shikigami_set = get_shikigami_display(user)

            query = users.find_one({
                "user_id": str(user.id), f"souls.{soul_select}.slot": int(slot)
            }, {
                "_id": 0,
                f"souls.{soul_select}.$.{slot}": 1
            })

            if query is None:
                embed = discord.Embed(
                    title="Invalid soul slot", color=user.colour, timestamp=get_timestamp(),
                    description=f"You do not own a `{soul_select.title()}` soul slot `#{slot}` yet",
                )
                embed.set_footer(text=user.display_name, icon_url=user.avatar_url)
                embed.set_thumbnail(url=get_soul_url(soul_select))
                await process_msg_submit(ctx.channel, None, embed)

            elif query is not None:

                users.update_one({
                    "user_id": str(user.id),
                    "shikigami.name": shikigami_set
                }, {
                    "$set": {
                        f"shikigami.$.souls.{slot}": soul_select,
                    }
                })
                shikigami_set_equipped = query["souls"][soul_select][0]["equipped"]

                if shikigami_set_equipped != shikigami_set:
                    users.update_one({
                        "user_id": str(user.id),
                        "shikigami": {
                            "$elemMatch": {
                                "name": shikigami_set_equipped,
                                f"souls.{slot}": soul_select
                            }}
                    }, {
                        "$set": {
                            f"shikigami.$.souls.{slot}": None
                        }
                    })

                users.update_one({
                    "user_id": str(user.id),
                    f"souls.{soul_select}.slot": int(slot)
                }, {
                    "$set": {
                        f"souls.{soul_select}.$.equipped": shikigami_set
                    }
                })
                await process_msg_reaction_add(ctx.message, "✅")

    async def souls_show_approximate(self, ctx, query):

        soul_search = souls.find({
            "name": {"$regex": f"^{query[:2].lower()}"}
        }, {"_id": 0, "name": 1})

        listings_souls = []
        for result in soul_search:
            listings_souls.append(f"{result['name'].title()}")

        embed = discord.Embed(
            title="Invalid soul", colour=colour,
            description=f"check the spelling of the soul"
        )
        embed.add_field(
            name="Possible matches",
            value="*{}*".format(", ".join(listings_souls)),
            inline=False
        )
        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["soul"])
    @commands.guild_only()
    async def souls_process(self, ctx, *, args=None):

        if args is None:
            await self.souls_help(ctx)

        elif args.lower() is not None and args in souls_all:
            await self.souls_show_users(ctx, ctx.author, args.lower())

        elif args.lower() is not None and args in soul_dungeons:

            query = users.find_one({"user_id": str(ctx.author.id)}, {"_id": 0, "souls_unlocked": 1})
            souls_stage_unlocked = query["souls_unlocked"]

            if souls_stage_unlocked >= int(args):
                await self.souls_explore(args.lower(), ctx.author, ctx, souls_stage_unlocked)

            else:
                embed = discord.Embed(
                    title="Invalid stage", color=ctx.author.colour,
                    description=f"You only have access up to {souls_stage_unlocked}",
                )
                await process_msg_submit(ctx.channel, None, embed)

    async def souls_explore(self, stage, user, ctx, unlocked):

        sushi_required, stage_adj, rounds, progress = 4, int(stage) * 3, 1, []
        users.update_one({"user_id": str(user.id)}, {"$inc": {"sushi": - sushi_required}})
        await perform_add_log("sushi", -sushi_required, user.id)

        total_chance, shikigami_name, shikigami_evolved = get_chance_soul_explore(user, 50, stage_adj, [2, 2.5],
                                                                                  0.75, 1)
        thumbnail = get_shikigami_url(shikigami_name, get_evo_link(shikigami_evolved))
        adjusted_chance = random.uniform(total_chance * 0.97, total_chance)

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

        def embed_new_create(r, strike):

            description2 = ""
            for log in progress:
                description2 += log

            embed_new_souls = discord.Embed(
                color=user.colour, timestamp=get_timestamp(), description=description2,
                title=f"{strike}Soul Stage: {stage} :: Round {r} of 3{strike}",
            )
            embed_new_souls.set_footer(text=user.display_name, icon_url=user.avatar_url)
            embed_new_souls.set_thumbnail(url=thumbnail)

            shiki_exp, shiki_exp_next, shiki_lvl, user_sushi = get_shiki_exp_lvl_next_sushi(user, shikigami_name)
            embed_new_souls.add_field(
                name=f"Shikigami: {shikigami_name.title()} | {user_sushi} {e_s}",
                value=f"Level: {shiki_lvl} | Experience: {shiki_exp}/{shiki_exp_next}\n"
                      f"Clear Chance: ~{round(total_chance, 2)}%"
            )
            return embed_new_souls

        msg = await process_msg_submit(ctx.channel, None, embed_new_create(rounds, ""))

        emojis_add = ["🏹"]
        for emoji in emojis_add:
            await process_msg_reaction_add(msg, emoji)

        def check(r, u):
            return msg.id == r.message.id and str(r.emoji) in emojis_add and u.id == ctx.author.id

        while True:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=60, check=check)
            except asyncio.TimeoutError:
                await process_msg_reaction_clear(msg)
                break
            else:
                if random.uniform(0, 100) > adjusted_chance:
                    explores.update_one({
                        "user_id": str(user.id), "souls.completion": None
                    }, {
                        "$inc": {
                            "souls.0.attempts": 1,
                            "souls.0.clears": 0,
                        },
                        "$set": {
                            "souls.0.completion": False
                        }
                    })
                    progress.append("❌")
                    await process_msg_edit(msg, None, embed_new_create(rounds, "~~"))
                    await process_msg_reaction_clear(msg)
                else:
                    explores.update_one({
                        "user_id": str(user.id), "souls.completion": None
                    }, {
                        "$inc": {
                            "souls.0.attempts": 1,
                            "souls.0.clears": 1,
                        }
                    })
                    progress.append("✅")

                    last_souls = explores.find_one({
                        "user_id": str(user.id)
                    }, {
                        "_id": 0, "explores": 0, "souls": {"$slice": 1}
                    })["souls"][0]

                    if last_souls["required"] == last_souls["clears"]:
                        embed_last = embed_new_create(rounds, "~~")
                        await self.souls_explore_rewards_generate_link(
                            embed_last, user, stage, msg, ctx, unlocked
                        )
                        await process_msg_reaction_clear(msg)
                        break
                    else:
                        rounds += 1
                        await process_msg_reaction_remove(msg, str(reaction.emoji), user)
                        await process_msg_edit(msg, None, embed_new_create(rounds, ""))

    async def souls_explore_rewards_generate_link(self, embed, user, stage, msg, ctx, unlocked):

        def get_soul_slot(s):
            dictionary = {0: 1, 1: 2, 2: 3, 4: 4, 5: 5, 6: 6}
            return dictionary[s]

        def get_soul_amount(s):
            dictionary = {
                1: [3, 0], 2: [3, 0], 3: [4, 1], 4: [5, 1], 5: [5, 1],
                6: [5, 1], 7: [6, 2], 8: [7, 3], 9: [7, 4], 10: [8, 5],
            }
            min_souls = dictionary[s][0]
            max_souls = dictionary[s][0] + dictionary[s][1]
            return min_souls, max_souls

        def get_soul_experience(s):
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

        def get_soul_y_off(index):
            return floor(index / 6)

        def generate_soul_experience_image(text):

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

        font = font_create(20)

        soul_slots, listings_soul_exp = [0, 1, 2, 4, 5, 6], []
        x_outline, y_outline, x_off, d, c = 22, 0, 0, 136, 16
        max_width_soul, max_height_soul, max_souls_line = 120, 100, 6

        a, b = get_soul_amount(int(stage))
        total_souls_drop = random.choice(list(range(a, b + 1)))
        total_height = ceil(total_souls_drop / max_souls_line) * max_height_soul
        total_width = max_souls_line * max_width_soul

        bd = Image.new("RGBA", (total_width, total_height))

        for i, document in enumerate(range(1, total_souls_drop + 1)):

            if i % 6 == 0:
                x_off = 0

            soul_drop = random.choice(self.souls_rewards)
            soul_im = Image.open(f"data/souls/{soul_drop}.png")
            w, h = soul_im.size

            slot = random.choice(soul_slots)
            rotation = slot * 45

            exp_total = 9
            for e in range(1, get_soul_experience(int(stage))):
                exp_total *= 3

            total_exp_adj = round(random.uniform(exp_total * 0.9, exp_total))
            listings_soul_exp.append([soul_drop, total_exp_adj, get_soul_slot(slot)])
            im_soul_exp = generate_soul_experience_image(str(total_exp_adj))

            soul_im.paste(im_soul_exp, (0, 60), im_soul_exp)

            if rotation in [45, 45 + 180]:
                soul_final_im = Image.open(self.soul_raw_address).rotate(
                    rotation, resample=Image.BICUBIC, expand=True
                ).resize((d, d), Image.ANTIALIAS)
                soul_final_im.paste(soul_im, (int(d / 4) - 6, int(d / 4) - 6), soul_im)

                w_f, h_f = soul_final_im.size
                if rotation == 45:
                    top = int(((h_f - 90) / 2) - 5)
                    left, right, bottom = 0, int(d - (d - 90) + 30), int(d - top)
                else:
                    top = int(((h_f - 90) / 2) - 5)
                    left, right, bottom = int(136 - (d - (d - 90) + 30)), d, int(d - top)

                soul_final_im_cropped = soul_final_im.crop((left, top, right, bottom))
                bd.paste(soul_final_im_cropped, (x_off, get_soul_y_off(i) * 100))
                w_f, h_f = soul_final_im_cropped.size
                x_off += w_f
            else:
                h_f, w_f = h + c, w + c
                soul_final_im = Image.open(self.soul_raw_address).rotate(
                    rotation, resample=Image.BICUBIC, expand=True
                ).resize((w_f, h_f), Image.ANTIALIAS)

                soul_final_im.paste(soul_im, (0 + int(c / 2), 0 + int(c / 2)), soul_im)
                bd.paste(soul_final_im, (x_off, get_soul_y_off(i) * 100))
                w_f, h_f = soul_final_im.size
                x_off += w_f

        temp_address = f"temp/{user.id}.png"
        bd.save(temp_address, quality=95)

        image_file = discord.File(temp_address, filename=f"{ctx.message.id}.png")
        hosting_channel = self.client.get_channel(int(id_hosting))
        msg1 = await process_msg_submit_file(hosting_channel, image_file)

        attachment_link = msg1.attachments[0].url

        scales, scales_rev = 0, 0
        if int(stage) >= 8:
            scales += random.choice([0, 0, 1, 2])
            if int(stage) >= 9:
                scales += random.choice([1, 1, 2])
                scales_rev += random.choice([0, 0, 1])
            if int(stage) == 0:
                scales_rev += random.choice([1, 1, 1, 2, 2])

        users.update_one({"user_id": str(user.id)}, {"$inc": {"scales": scales, "scales_rev": scales_rev}})

        embed.add_field(
            name="Rewards", inline=False,
            value=f"Reversed scales: `{scales_rev}`\n"
                  f"Normal Scales: `{scales}`\n"
                  f"# Dropped of Souls: `{total_souls_drop}`",
        )
        embed.set_image(url=attachment_link)
        await self.souls_experience_add(user, listings_soul_exp)
        await process_msg_edit(msg, None, embed)

        if unlocked == int(stage):
            users.update_one({"user_id": str(user.id), "souls_unlocked": {"$lt": 10}}, {"$inc": {"souls_unlocked": 1}})

    async def souls_experience_add(self, user, soul_exp_list):

        for s in soul_exp_list:
            s_type, experience, slot = s[0], s[1], s[2]

            if users.find_one({"user_id": str(user.id), f"souls.{s_type}": {"$type": "object"}}, {"_id": 0}) is None:
                users.update_one({"user_id": str(user.id)}, {"$set": {f"souls.{s_type}": []}})

            x = users.update_one({
                "user_id": str(user.id), "$and": [{
                    f"souls.{s_type}": {"$elemMatch": {"slot": slot, "grade": {"$lt": 6}}}
                }]
            }, {
                "$inc": {
                    f"souls.{s_type}.$.exp": experience
                }
            })

            if x.modified_count == 0:
                users.update_one({"user_id": str(user.id)}, {
                    "$push": {
                        f"souls.{s_type}": {
                            "grade": 1,
                            "slot": slot,
                            "exp": experience,
                            "lvl_exp_next": 7000,
                            "equipped": None
                        }
                    }
                })

            await self.souls_level_up(user, s_type, slot)

    async def souls_level_up(self, user, soul_name, slot):

        soul_data = users.find_one({
            "user_id": str(user.id),
            "$and": [{f"souls.{soul_name}": {"$elemMatch": {"slot": slot}}}]
        }, {
            "_id": 0,
            f"souls.{soul_name}.$": 1
        })

        if soul_data["souls"][soul_name][0]["grade"] == 6:
            pass

        elif soul_data["souls"][soul_name][0]["exp"] >= soul_data["souls"][soul_name][0]["lvl_exp_next"]:

            def get_lvl_exp_next_new(g):
                dictionary = {1: 7000, 2: 21000, 3: 63000, 4: 189000, 5: 567000}
                return dictionary[g]

            lvl_exp_next_new = get_lvl_exp_next_new(soul_data["souls"][soul_name][0]["grade"] + 1)

            users.update_one({
                "user_id": str(user.id),
                "$and": [{f"souls.{soul_name}": {"$elemMatch": {"slot": slot}}}]
            }, {
                "$set": {
                    f"souls.{soul_name}.$.lvl_exp_next": lvl_exp_next_new,
                    f"souls.{soul_name}.$.exp": lvl_exp_next_new,
                },
                "$inc": {
                    f"souls.{soul_name}.$.grade": 1
                }
            })

    async def souls_show_users(self, ctx, user, soul_select):

        try:
            user_souls = users.find_one({"user_id": str(user.id)}, {"_id": 0, f"souls": 1})["souls"]

        except (KeyError, TypeError):
            await self.souls_show_users_invalid(ctx)

        else:
            soul_pagination = []
            for x in user_souls:
                soul_pagination.append(x)

            if soul_select not in soul_pagination:
                await self.souls_show_users_invalid(ctx)

            else:
                def embed_new_create(soul_select_new):

                    souls_formatted = []
                    for s in user_souls[soul_select_new]:
                        souls_formatted.append(
                            [s["slot"], s["grade"], s["exp"], s["lvl_exp_next"], s["equipped"]]
                        )

                    embed_new = discord.Embed(color=user.colour, timestamp=get_timestamp())
                    embed_new.set_author(name=f"{soul_select_new.title()} Souls Stats", icon_url=user.avatar_url)
                    embed_new.set_thumbnail(url=get_soul_url(soul_select_new))

                    for s in sorted(souls_formatted, key=lambda z: z[0], reverse=False):

                        try:
                            shiki = s[4].title()
                        except AttributeError:
                            shiki = "`None`"

                        embed_new.add_field(
                            name=f"`[Slot {s[0]}]` | Grade {s[1]}", inline=False,
                            value=f"Experience: `{s[2]}/{s[3]}`\n"
                                  f"Equipped to: {shiki}",
                        )
                    return embed_new

                page = soul_pagination.index(soul_select)
                page_total = len(soul_pagination) - 1
                msg = await process_msg_submit(ctx.channel, None, embed_new_create(soul_select))

                emojis_valid = ["⬅", "➡"]
                for emoji in emojis_valid:
                    await process_msg_reaction_add(msg, emoji)

                def check(r, u):
                    return u != self.client.user and r.message.id == msg.id and str(r.emoji) in emojis_valid

                while True:
                    try:
                        reaction, user = await self.client.wait_for("reaction_add", timeout=180, check=check)
                    except asyncio.TimeoutError:
                        await process_msg_reaction_clear(msg)
                        break
                    else:
                        if str(reaction.emoji) == emojis_valid[1]:
                            page += 1
                        elif str(reaction.emoji) == emojis_valid[0]:
                            page -= 1
                        if page == 0:
                            page = page_total
                        elif page > page_total:
                            page = 1
                        await process_msg_edit(msg, None, embed_new_create(soul_pagination[page]))
                        await process_msg_reaction_remove(msg, str(reaction.emoji), user)

    async def souls_show_users_invalid(self, ctx):

        embed = discord.Embed(
            color=ctx.author.colour, title=f"Invalid soul", description=f"You do not own any of this soul"
        )
        await process_msg_submit(ctx.channel, None, embed)


def setup(client):
    client.add_cog(Souls(client))
