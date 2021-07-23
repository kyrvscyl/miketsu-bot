"""
Economy Module
"Miketsu, 2021
"""

import collections
from itertools import cycle

from PIL import Image, ImageOps
from discord.ext import commands, tasks

from cogs.ext.initialize import *


class Economy(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.prefix = self.client.command_prefix

        self.prayer_heard = cycle(listings_1["prayer_heard"])
        self.prayer_ignored = cycle(listings_1["prayer_ignored"])

    async def economy_issue_rewards_reset_daily(self):

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
                        f"• wish for a shikigami shard using `{self.prefix}wish`"
        )
        spell_spam_channel = self.client.get_channel(int(id_spell_spam))
        await process_msg_submit(spell_spam_channel, None, embed)

    async def economy_issue_rewards_reset_weekly(self):

        users.update_many({}, {"$set": {"weekly": False}})

        embed = discord.Embed(
            title="💝 Weekly rewards reset", colour=colour,
            description=f"• claim yours using `{self.prefix}weekly`\n"
                        f"• Eboshi frames redistributed and wielders rewarded"
        )
        spell_spam_channel = self.client.get_channel(int(id_spell_spam))
        await process_msg_submit(spell_spam_channel, None, embed)

    @commands.Cog.listener()
    async def on_ready(self):

        self.economy_sushi_bento_increment.start()

    @tasks.loop(minutes=4)
    async def economy_sushi_bento_increment(self):

        users.update_many({"bento": {"$lt": 360}}, {"$inc": {"bento": 1}})

    @commands.command(aliases=["bento"])
    @commands.guild_only()
    async def economy_sushi_bento(self, ctx):

        user = ctx.author
        reserves = users.find_one({"user_id": str(user.id)}, {"_id": 0, "bento": 1})["bento"]

        def embed_new_create(strike):
            embed_new = discord.Embed(
                description=f"{strike}You currently have {reserves:,d}{get_emoji('sushi')} in your reserve{strike}",
                color=user.colour, timestamp=get_timestamp()
            )
            embed_new.set_footer(text=f"{user.display_name}", icon_url=user.avatar_url)
            return embed_new

        msg = await process_msg_submit(ctx.channel, None, embed_new_create(""))
        await process_msg_reaction_add(msg, "🍽️")

        def check(r, u):
            return u != self.client.user and \
                   r.message.id == msg.id and \
                   str(r.emoji) == "🍽️" and \
                   u.id == user.id

        while True:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=60, check=check)
            except asyncio.TimeoutError:
                await process_msg_reaction_clear(msg)
                break
            else:
                users.update_one({"user_id": str(user.id)}, {"$inc": {"sushi": reserves, "bento": -reserves}})
                await process_msg_edit(msg, None, embed_new_create("~~"))
                await perform_add_log("sushi", reserves, user.id)
                await process_msg_reaction_clear(msg)

    @commands.command(aliases=["sushi", "food", "ap", "hungry"])
    @commands.guild_only()
    @commands.cooldown(1, 60 * 60, commands.BucketType.guild)
    async def economy_sushi_bento_serve(self, ctx):

        minutes, sushi_claimers, timestamp, sushi = 10, [], get_timestamp(), 25
        sushchefs_id = guilds.find_one({"server": str(id_guild)}, {"_id": 0, "roles": 1})["roles"]["sushchefs"]

        def embed_new_create(listings_users, strike):
            embed = discord.Embed(
                title=f"{strike}Free sushi!{strike} 25🍣",
                description=f"claim your free sushi every hour! 🎉\n"
                            f"served {len(listings_users)} hungry {pluralize('Onmyoji', len(listings_users))}",
                color=colour, timestamp=timestamp
            )
            embed.set_footer(
                text=f"lasts {minutes} minutes",
                icon_url=self.client.user.avatar_url
            )
            return embed

        content = f"<@&{sushchefs_id}>!"
        msg = await process_msg_submit(ctx.channel, content, embed_new_create(sushi_claimers, ""))
        await process_msg_reaction_add(msg, "🍽️")

        def check(r, u):
            return u != self.client.user and \
                   r.message.id == msg.id and \
                   str(r.emoji) == "🍽️" and \
                   str(u.id) not in sushi_claimers

        while True:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=60 * minutes, check=check)
            except asyncio.TimeoutError:
                await process_msg_edit(msg, None, embed_new_create(sushi_claimers, "~~"))
                await process_msg_reaction_clear(msg)
                break
            else:
                users.update_one({"user_id": str(user.id)}, {"$inc": {"sushi": sushi}})
                sushi_claimers.append(str(user.id))
                await process_msg_edit(msg, content, embed_new_create(sushi_claimers, ""))
                await perform_add_log("sushi", sushi, user.id)

    @commands.command(aliases=["wish"])
    @commands.guild_only()
    async def economy_wish_perform(self, ctx, *, shikigami_name=None):

        user = ctx.author
        wish_status = users.find_one({"user_id": str(user.id)}, {"_id": 0, "wish": 1})["wish"]

        if shikigami_name is None:
            embed = discord.Embed(
                color=colour, title="wish",
                description=f"wish for a shikigami shard to manually summon it"
            )
            embed.add_field(name="Example", value=f"*`{self.prefix}wish inferno ibaraki`*")
            await process_msg_submit(ctx.channel, None, embed)

        elif wish_status is False:
            embed = discord.Embed(color=user.colour, description=f"Your wish has been fulfilled already today")
            await process_msg_submit(ctx.channel, None, embed)

        elif wish_status is not True:
            embed = discord.Embed(color=user.colour, description=f"Your wish has been placed already today")
            await process_msg_submit(ctx.channel, None, embed)

        elif wish_status is True and shikigami_name.lower() not in pool_all:
            await shikigami_post_approximate_results(ctx, shikigami_name.lower())

        elif wish_status is True and shikigami_name.lower() in pool_all:

            users.update_one({"user_id": str(user.id)}, {"$set": {"wish": shikigami_name.lower()}})
            query = users.find_one({
                "user_id": str(user.id),
                "shikigami.name": shikigami_name.lower()
            }, {
                "_id": 0, "shikigami.$": 1
            })

            if query is None:
                evolve, shards = False, 0
                if get_rarity_shikigami(shikigami_name.lower()) == "SP":
                    evolve, shards = True, 5
                shikigami_push_user(user.id, shikigami_name.lower(), evolve, 0)

            embed = discord.Embed(
                color=user.colour, title=f"Wish registered", timestamp=get_timestamp(),
                description=f"You have wished for {shikigami_name.title()} shard today"
            )
            embed.set_footer(icon_url=user.avatar_url, text=f"{user.display_name}")
            embed.set_thumbnail(url=get_shikigami_url(shikigami_name, "pre"))

            await process_msg_reaction_add(ctx.message, "✅")
            await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["wishlist", "wl"])
    @commands.guild_only()
    async def economy_wish_show_list(self, ctx):

        wish_users = []

        for d in users.find({"wish": {"$ne": True}}, {"_id": 0, "wish": 1, "user_id": 1}):
            member = ctx.guild.get_member(int(d["user_id"]))
            shikigami_name = d['wish']

            if shikigami_name is False:
                shikigami_name = "✅"

            wish_users.append(f"▫{member} | {shikigami_name.title()}\n")

        await self.economy_wish_show_list_paginate(ctx, wish_users)

    async def economy_wish_show_list_paginate(self, ctx, shard_wishes):

        page = 1
        max_lines = 10
        page_total = ceil(len(shard_wishes) / max_lines)
        if page_total == 0:
            page_total = 1

        ordinal = lambda n: "%d%s" % (n, "tsnrhtdd"[(n / 10 % 10 != 1) * (n % 10 < 4) * n % 10::4])
        nth = ordinal(get_time().timetuple().tm_yday)

        def embed_new_create(page_new):
            end = page_new * max_lines
            start = end - max_lines
            description = "".join(shard_wishes[start:end])

            embed_new = discord.Embed(
                color=colour, timestamp=get_timestamp(),
                title=f"🌟 Wish List [{nth} day]", description=f"{description}"
            )
            embed_new.set_footer(text=f"Page: {page_new} of {page_total}")
            return embed_new

        msg = await process_msg_submit(ctx.channel, None, embed_new_create(page))

        emojis_add = ["⬅", "➡"]
        for emoji in emojis_add:
            await process_msg_reaction_add(msg, emoji)

        def check(r, u):
            return u != self.client.user and msg.id == r.message.id and str(r.emoji) in emojis_add

        while True:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=60, check=check)
            except asyncio.TimeoutError:
                await process_msg_reaction_clear(msg)
                break
            else:
                if str(reaction.emoji) == emojis_add[1]:
                    page += 1
                elif str(reaction.emoji) == emojis_add[0]:
                    page -= 1
                if page == 0:
                    page = page_total
                elif page > page_total:
                    page = 1
                await process_msg_edit(msg, None, embed_new_create(page))
                await process_msg_reaction_remove(msg, str(reaction.emoji), user)

    async def economy_wish_fulfill_help(self, ctx):

        embed = discord.Embed(
            color=ctx.author.colour, title=f"fulfill, ff",
            description=f"fulfill a wish from a member in *`{self.prefix}wishlist`*\n"
        )
        embed.add_field(name="Format", value=f"*`{self.prefix}ff <@member>`*")
        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["fulfill", "ff"])
    @commands.guild_only()
    async def economy_wish_fulfill(self, ctx, *, member: discord.Member = None):

        if member is None:
            await self.economy_wish_fulfill_help(ctx)

        else:
            user = ctx.author
            query = users.find_one({"user_id": str(member.id)}, {"_id": 0, "wish": 1})["wish"]

            if query is None:
                await process_msg_invalid_member(ctx)

            elif query is True:
                embed = discord.Embed(
                    color=user.colour, title=f"Invalid member",
                    description=f"member has not placed their daily wish yet",
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif query is False:
                embed = discord.Embed(
                    color=user.colour, title=f"Wish fulfillment failed",
                    description=f"this member has their wish fulfilled already",
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif check_if_user_has_any_alt_roles(member):
                await process_msg_reaction_add(ctx.message, "❌")

            else:
                shikigami_name = query
                user_shikigami = users.find_one({
                    "user_id": str(user.id),
                    "shikigami.name": shikigami_name
                }, {
                    "_id": 0, "shikigami.$": 1
                })

                if user_shikigami is None or user_shikigami["shikigami"][0]["shards"] == 0:
                    embed = discord.Embed(title=f"Insufficient shards", description=f"lacks a shard to donate")
                    await process_msg_submit(ctx.channel, None, embed)

                elif user_shikigami["shikigami"][0]["shards"] > 0:
                    shard, friendship_pass, friendship = -1, 3, 10

                    users.update_one({
                        "user_id": str(user.id), "shikigami.name": shikigami_name
                    }, {
                        "$inc": {
                            "shikigami.$.shards": shard,
                            "friendship_pass": friendship_pass,
                            "friendship": friendship
                        }
                    })
                    await perform_add_log("friendship_pass", friendship_pass, user.id)
                    await perform_add_log("friendship", friendship, user.id)

                    users.update_one({
                        "user_id": str(member.id),
                        "shikigami.name": shikigami_name}, {
                        "$inc": {
                            "shikigami.$.shards": 1
                        },
                        "$set": {
                            "wish": False
                        }
                    })

                    embed = discord.Embed(
                        color=user.colour, title=f"Wish fulfilled", timestamp=get_timestamp(),
                        description=f"Donated 1 {shikigami_name.title()} shard to {member.mention}\n"
                                    f"Also acquired {friendship}{e_f} and {friendship_pass}{e_fp}",
                    )
                    embed.set_footer(text=f"{user.display_name}", icon_url=user.avatar_url)
                    embed.set_thumbnail(url=get_shikigami_url(shikigami_name, "pre"))
                    await process_msg_submit(ctx.channel, None, embed)

    async def economy_stat_shikigami_help(self, ctx):

        embed = discord.Embed(
            title="stats",
            colour=colour,
            description="shows shikigami pulls statistics"
        )
        embed.add_field(
            name="Example", inline=False,
            value=f"*`{self.prefix}stat tamamonomae`*\n"
                  f"*`{self.prefix}stat all`*\n"
        )
        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["stat", "st"])
    @commands.guild_only()
    async def economy_stat_shikigami(self, ctx, *, args=None):

        if args is None:
            await self.economy_stat_shikigami(ctx)

        else:
            shikigami_name = args.lower()

            if shikigami_name.lower() in ["sm", "all"]:
                await self.economy_stat_shikigami_all(ctx)

            elif shikigami_name.lower() not in pool_all:
                await shikigami_post_approximate_results(ctx, shikigami_name.lower())

            elif shikigami_name.lower() in pool_all:
                await self.economy_stat_shikigami_one(ctx, shikigami_name)

    async def economy_stat_shikigami_all(self, ctx):

        rarity_evolved = [0]
        count_all = []

        for rarity in rarities:
            for result in users.aggregate([{
                "$match": {"shikigami.evolved": True}
            }, {
                "$unwind": {"path": "$shikigami"}
            }, {
                "$project": {"shikigami": 1}
            }, {
                "$match": {"shikigami.evolved": True, "shikigami.rarity": rarity}
            }, {
                "$count": "count"
            }]):
                rarity_evolved.append(result["count"])

        for rarity in rarities:
            for result in users.aggregate([{
                "$project": {"_id": 0, "user_id": 1, "shikigami": 1}
            }, {
                "$unwind": {"path": "$shikigami"}
            }, {
                "$match": {"shikigami.rarity": rarity}
            }, {
                "$group": {"_id": "", "evolved": {"$sum": "$shikigami.owned"}}}
            ]):
                count_all.append(result["evolved"])

        count_1 = count_all[0] + rarity_evolved[0]
        count_2 = count_all[1] + rarity_evolved[1] * 1
        count_3 = count_all[2] + rarity_evolved[2] * 10
        count_4 = count_all[3] + rarity_evolved[3] * 20
        count_total = count_1 + count_2 + count_3 + count_4

        distribution_1 = round(count_1 / count_total * 100, 3)
        distribution_2 = round(count_2 / count_total * 100, 3)
        distribution_3 = round(count_3 / count_total * 100, 3)
        distribution_4 = round(count_4 / count_total * 100, 3)

        embed = discord.Embed(
            color=colour, timestamp=get_timestamp(),
            description=f"```"
                        f"Rarity\n"
                        f"SP    ::    {distribution_1}%  ::   {count_1:,d}\n"
                        f"SSR   ::    {distribution_2}%  ::   {count_2:,d}\n"
                        f"SR    ::   {distribution_3}%  ::   {count_3:,d}\n"
                        f"R     ::   {distribution_4}%  ::   {count_4:,d}"
                        f"```"
        )
        embed.set_author(name="Summon Pull Statistics")
        embed.add_field(name="Total Amulets Spent", value=f"{count_total:,d}")
        await process_msg_submit(ctx.channel, None, embed)

    async def economy_stat_shikigami_one(self, ctx, shikigami_name):

        listings_owned = []
        for entry in users.aggregate([{
            "$match": {"shikigami.name": shikigami_name.lower()}
        }, {
            "$project": {"_id": 0, "user_id": 1, "shikigami.name": 1}
        }, {
            "$unwind": {"path": "$shikigami"}
        }, {
            "$match": {"shikigami.name": shikigami_name.lower()}
        }]):
            try:
                listings_owned.append(ctx.guild.get_member(int(entry["user_id"])).display_name)
            except AttributeError:
                continue

        count_pre_evo = 0
        count_evolved = 0

        for result_pre_evo in users.aggregate([{
            "$match": {"shikigami.name": shikigami_name.lower()}
        }, {
            "$project": {"_id": 0, "user_id": 1, "shikigami": 1
                         }
        }, {
            "$unwind": {"path": "$shikigami"}
        }, {
            "$match": {"shikigami.name": shikigami_name.lower(), "shikigami.evolved": False}
        }, {
            "$count": "pre_evo"
        }]):
            count_pre_evo = result_pre_evo["pre_evo"]

        for result_evolved in users.aggregate([{
            "$match": {"shikigami.name": shikigami_name.lower()}
        }, {
            "$project": {"_id": 0, "user_id": 1, "shikigami": 1}
        }, {
            "$unwind": {"path": "$shikigami"}
        }, {
            "$match": {"shikigami.name": shikigami_name.lower(), "shikigami.evolved": True}
        }, {
            "$count": "evolved"
        }]):
            count_evolved = result_evolved["evolved"]

        embed = discord.Embed(
            colour=ctx.author.colour, timestamp=get_timestamp(),
            description=f"```"
                        f"Pre-evolve    ::   {count_pre_evo}\n"
                        f"Evolved       ::   {count_evolved}"
                        f"```",
        )
        embed.set_author(
            name=f"Stats for {shikigami_name.title()}",
            icon_url=get_shikigami_url(shikigami_name, "pre")
        )
        listings_formatted = ", ".join(listings_owned)

        if len(listings_owned) == 0:
            listings_formatted = "None"

        embed.set_thumbnail(url=get_shikigami_url(shikigami_name, "evo"))
        embed.add_field(
            name=f"Owned by {len(listings_owned)} {pluralize('member', len(listings_owned))}",
            value=f"{listings_formatted}"
        )
        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["parade", "prd"])
    @commands.guild_only()
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def economy_perform_parade(self, ctx):

        user = ctx.author

        if not check_if_user_has_parade_tickets(ctx):
            embed = discord.Embed(
                title="Insufficient parade tickets", colour=user.colour,
                description=f"Claim your dailies to acquire tickets"
            )
            await process_msg_submit(ctx.channel, None, embed)

        else:
            users.update_one({"user_id": str(user.id)}, {"$inc": {"parade_tickets": -1}})
            await perform_add_log("parade_tickets", -1, user.id)

            dimensions, beans, beaned_shikigamis, parade_pull, timeout = 7, 10, [], [], 25

            for x in range(1, 50):
                roll = random.uniform(0, 100)

                if roll < 7:
                    p = random.uniform(0, 1.2)
                    if p >= 126 / 109:
                        parade_pull.append(random.choice(pool_sp))
                    else:
                        if random.uniform(1, 100) >= 75:
                            parade_pull.append(random.choice(pool_ssr))
                        else:
                            parade_pull.append(random.choice(pool_ssn))
                elif roll <= 10:
                    parade_pull.append(random.choice(pool_others))
                elif roll <= 25:
                    parade_pull.append(random.choice(pool_sr))
                else:
                    parade_pull.append(random.choice(pool_r))

            x_init, y_init = random.randint(1, dimensions), random.randint(1, dimensions)
            attachment_link = await self.economy_perform_parade_generate_image(
                ctx, dimensions, parade_pull, x_init, y_init
            )

            def embed_new_create(listings_shikis, remaining_chances):
                value = ", ".join([shiki.title() for shiki in listings_shikis])
                if len(value) == 0:
                    value = None

                embed_new = discord.Embed(
                    color=user.color,
                    title="🎏 Demon Parade",
                    description=f"Beans: 10\n"
                                f"Time Limit: {timeout} seconds, resets for every bean\n"
                                f"Note: Cannot bean the same shikigami twice",
                    timestamp=get_timestamp()
                )
                embed_new.set_image(url=attachment_link)
                embed_new.add_field(name="Beaned shikigamis", value=value)
                embed_new.set_footer(text=f"{remaining_chances} beans", icon_url=user.avatar_url)
                return embed_new

            msg = await process_msg_submit(ctx.channel, None, embed_new_create(beaned_shikigamis, beans))

            emojis_add = ["⬅", "⬆", "⬇", "➡"]
            for arrow in emojis_add:
                await msg.add_reaction(arrow)

            def check(r, u):
                return msg.id == r.message.id and str(r.emoji) in emojis_add and u.id == user.id

            def get_new_coordinates(x_coor, y_coor, emoji):

                dictionary = {"⬅": -1, "⬆": -1, "⬇": 1, "➡": 1}
                new_x, new_y = x_coor, y_coor

                if emoji in ["⬅", "➡"]:
                    new_x, new_y = x_coor + dictionary[emoji], y_coor
                    if new_x > dimensions:
                        new_x = 1
                    if new_x < 1:
                        new_x = dimensions

                elif emoji in ["⬇", "⬆"]:
                    new_x, new_y = x_coor, y_coor + dictionary[emoji]
                    if new_y > dimensions:
                        new_y = 1
                    if new_y < 1:
                        new_y = dimensions

                return new_x, new_y

            while beans != -1:
                try:
                    reaction, user = await self.client.wait_for("reaction_add", timeout=timeout, check=check)
                except asyncio.TimeoutError:
                    await process_msg_reaction_clear(msg)
                    break
                else:
                    bean_x, bean_y = get_new_coordinates(x_init, y_init, str(reaction.emoji))

                    def get_bean_shikigami(x_coor_get, y_coor_get):
                        index_bean = (dimensions * y_coor_get) - (dimensions - x_coor_get)
                        return parade_pull[index_bean - 1]

                    shikigami_beaned = get_bean_shikigami(bean_x, bean_y)

                    if shikigami_beaned not in beaned_shikigamis:
                        beaned_shikigamis.append(shikigami_beaned)

                    await process_msg_edit(msg, None, embed_new_create(beaned_shikigamis, beans))
                    await process_msg_reaction_remove(msg, str(reaction.emoji), user)
                    x_init, y_init = bean_x, bean_y
                    beans -= 1

            await self.economy_perform_parade_issue_shards(user, beaned_shikigamis, ctx, msg)

    async def economy_perform_parade_generate_image(self, ctx, max_rows, parade_pull, x_init, y_init):

        achievements_address = []
        for entry in parade_pull:
            try:
                roll = random.uniform(0, 100)
                suffix = "_pre"
                if roll < 30:
                    suffix = "_evo"
                achievements_address.append(f"data/shikigamis/{entry}{suffix}.jpg")
            except KeyError:
                continue

        images = list(map(Image.open, achievements_address))
        new_im = Image.new("RGBA", (max_rows * 90, max_rows * 90))

        def get_coordinates(c):
            a = (c * 90 - (ceil(c / max_rows) - 1) * max_rows * 90) - 90
            b = (ceil(c / max_rows) * 90) - 90
            return a, b

        def add_border(input_image):
            border1, border2 = 9, 9
            address_temp = f"temp/{ctx.message.id}.jpg"
            bordered_thumbnail = ImageOps.expand(input_image, border=(border1, border2), fill=ctx.author.color.to_rgb())
            bordered_thumbnail.save(address_temp)
            img = Image.open(address_temp)
            return img.resize((90, 90))

        def get_bean_shikigami_initial(x_coor_get, y_coor_get):
            index_bean = (max_rows * y_coor_get) - (max_rows - x_coor_get)
            return index_bean - 1

        index_initial = get_bean_shikigami_initial(x_init, y_init)

        for index, item in enumerate(images):
            if index == index_initial:
                new_im.paste(add_border(images[index]), (get_coordinates(index + 1)))
            else:
                new_im.paste(images[index], (get_coordinates(index + 1)))

        address = f"temp/{ctx.author.id}.png"
        new_im.save(address)
        image_file = discord.File(address, filename=f"{ctx.message.id}.png")
        hosting_channel = self.client.get_channel(int(id_hosting))
        msg = await process_msg_submit_file(hosting_channel, image_file)
        attachment_link = msg.attachments[0].url

        return attachment_link

    async def economy_perform_parade_issue_shards(self, user, beaned_shikigamis, ctx, msg):

        await process_msg_reaction_clear(msg)
        self.client.get_command("economy_perform_parade").reset_cooldown(ctx)

        rarities_beaned = []
        for beaned_shikigami in beaned_shikigamis:

            query = users.find_one({
                "user_id": str(user.id),
                "shikigami.name": beaned_shikigami
            }, {
                "_id": 0, "shikigami.$": 1
            })
            rarities_beaned.append(get_rarity_shikigami(beaned_shikigami))

            if query is None:
                evolve, shards = False, 0
                if get_rarity_shikigami(beaned_shikigami) == "SP":
                    evolve, shards = True, 0
                shikigami_push_user(user.id, beaned_shikigami, evolve, shards)

            users.update_one({
                "user_id": str(ctx.author.id),
                "shikigami.name": beaned_shikigami
            }, {
                "$inc": {
                    "shikigami.$.shards": 1
                }
            })

        try:
            counter = collections.Counter(rarities_beaned)
            ssr_count = dict(counter)["SSR"]
            if ssr_count >= 4:
                spell_spam_channel = self.client.get_channel(int(id_spell_spam))
                await frame_acquisition(user, "Flower Fest", 3500, spell_spam_channel)

        except KeyError:
            pass

    @commands.command(aliases=["pray"])
    @commands.guild_only()
    @commands.cooldown(1, 150, commands.BucketType.user)
    async def economy_pray_use(self, ctx):

        user = ctx.author

        if not check_if_user_has_prayers(ctx):
            embed = discord.Embed(
                colour=user.colour, title=f"Insufficient prayers",
                description=f"You have used up all your prayers today",
            )
            await process_msg_submit(ctx.channel, None, embed)

        else:
            embed = discord.Embed(
                title="Pray to the Goddess of Hope and Prosperity!", color=user.colour,
                description="45% chance to obtain rich rewards", timestamp=get_timestamp()
            )
            embed.set_footer(text=f"{user.display_name}", icon_url=user.avatar_url)
            msg = await process_msg_submit(ctx.channel, None, embed)

            roll = random.randint(1, 100)
            rewards_emoji = [e_j, e_f, e_a, e_c, e_t, e_m, e_s]
            rewards_selection = []

            for x in range(0, 3):
                emoji = random.choice(rewards_emoji)
                await process_msg_reaction_add(msg, emoji.replace("<", "").replace(">", ""))
                rewards_emoji.remove(emoji)
                rewards_selection.append(emoji)

            def check(r, u):
                return str(r.emoji) in rewards_selection and u == user and msg.id == r.message.id

            def get_rewards(y):
                rewards_amount = {
                    e_j: 350, e_f: 75, e_a: 5, e_c: 500000, e_t: 2500, e_m: 250, e_s: 50
                }
                rewards_text = {
                    e_j: "jades",
                    e_f: "friendship",
                    e_a: "amulets",
                    e_c: "coins",
                    e_t: "talisman",
                    e_m: "medals",
                    e_s: "sushi"
                }
                return rewards_amount[y], rewards_text[y]

            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=150, check=check)
            except asyncio.TimeoutError:
                users.update_one({"user_id": str(user.id)}, {"$inc": {"prayers": -1}})
                await perform_add_log("prayers", -1, user.id)
            else:
                users.update_one({"user_id": str(user.id)}, {"$inc": {"prayers": -1}})
                await perform_add_log("prayers", -1, user.id)

                if roll >= 55:
                    embed = discord.Embed(
                        title=f"Prayer results", color=user.colour,
                        description=f"{next(self.prayer_ignored)}", timestamp=get_timestamp()
                    )
                    embed.set_footer(text=f"{user.display_name}", icon_url=user.avatar_url)
                    await process_msg_edit(msg, None, embed)
                else:
                    amount, rewards = get_rewards(str(reaction.emoji))
                    embed = discord.Embed(
                        title=f"Prayer results", color=user.colour, timestamp=get_timestamp(),
                        description=f"{next(self.prayer_heard)} You obtained {amount:,d}{str(reaction.emoji)}",
                    )
                    embed.set_footer(text=f"{user.display_name}", icon_url=user.avatar_url)
                    users.update_one({"user_id": str(user.id)}, {"$inc": {rewards: amount}})

                    await perform_add_log(rewards, amount, user.id)
                    await process_msg_edit(msg, None, embed)
            finally:
                self.client.get_command("economy_pray_use").reset_cooldown(ctx)

    @commands.command(aliases=["daily"])
    @commands.guild_only()
    async def economy_claim_rewards_daily(self, ctx):

        user = ctx.author
        query = users.find_one({"user_id": str(user.id)}, {"_id": 0, "daily": 1})

        if query["daily"] is False:
            await self.economy_claim_rewards_daily_give(user, ctx)

        elif query["daily"] is True:
            embed = discord.Embed(
                title="Collection failed", colour=colour,
                description=f"already collected today, check back tomorrow"
            )
            await process_msg_submit(ctx.channel, None, embed)

    async def economy_claim_rewards_daily_give(self, user, ctx):

        friendship_pass, jades, coins, realm_ticket = 5, 150, 150000, 6
        encounter_ticket, parade_tickets, sushi = 10, 2, 200

        users.update_one({"user_id": str(user.id)}, {
            "$inc": {
                "friendship_pass": friendship_pass,
                "jades": jades,
                "coins": coins,
                "realm_ticket": realm_ticket,
                "encounter_ticket": encounter_ticket,
                "parade_tickets": parade_tickets,
                "sushi": sushi
            },
            "$set": {
                "daily": True
            }
        })

        await perform_add_log("friendship_pass", friendship_pass, user.id)
        await perform_add_log("jades", jades, user.id)
        await perform_add_log("coins", coins, user.id)
        await perform_add_log("realm_ticket", realm_ticket, user.id)
        await perform_add_log("encounter_ticket", encounter_ticket, user.id)
        await perform_add_log("parade_tickets", parade_tickets, user.id)
        await perform_add_log("sushi", sushi, user.id)

        embed = discord.Embed(
            color=ctx.author.colour, title="🎁 Daily rewards", timestamp=get_timestamp(),
            description=f"A box containing "
                        f"{friendship_pass:,d}{e_fp}, {jades:,d}{e_j}, {coins:,d}{e_c}, "
                        f"{realm_ticket:,d} {e_r}, "
                        f"{encounter_ticket:,d} {e_e}, "
                        f"{parade_tickets:,d} {e_p}, & "
                        f"{sushi:,d} {e_s}",
        )
        embed.set_footer(text=f"Opened by {user.display_name}", icon_url=user.avatar_url)
        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["weekly"])
    @commands.guild_only()
    async def economy_claim_rewards_weekly(self, ctx):

        user = ctx.author
        query = users.find_one({"user_id": str(user.id)}, {"_id": 0, "weekly": 1})

        if query["weekly"] is False:
            await self.economy_claim_rewards_weekly_give(user, ctx)

        elif query["weekly"] is True:
            embed = discord.Embed(
                title="Collection Failed", colour=colour,
                description=f"already collected this reset, check back next week"
            )
            await process_msg_submit(ctx.channel, None, embed)

    async def economy_claim_rewards_weekly_give(self, user, ctx):

        jades, coins, amulets, sushi = 1000, 450000, 15, 250

        users.update_one({"user_id": str(user.id)}, {
            "$inc": {
                "jades": jades,
                "coins": coins,
                "amulets": amulets,
                "sushi": sushi
            },
            "$set": {
                "weekly": True
            }
        })
        await perform_add_log("jades", jades, user.id)
        await perform_add_log("coins", coins, user.id)
        await perform_add_log("amulets", amulets, user.id)
        await perform_add_log("sushi", sushi, user.id)

        embed = discord.Embed(
            color=user.colour, timestamp=get_timestamp(), title="💝 Weekly rewards",
            description=f"A mythical box containing {jades:,d}{e_j}, {coins:,d}{e_c}, "
                        f"{amulets:,d}{e_a}, & {sushi:,d}{e_s}",
        )
        embed.set_footer(text=f"Opened by {user.display_name}", icon_url=user.avatar_url)
        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["profile", "p"])
    @commands.guild_only()
    async def economy_profile_show(self, ctx, *, member: discord.Member = None):

        if member is None:
            await self.economy_profile_post(ctx.author, ctx)

        else:
            await self.economy_profile_post(member, ctx)

    async def economy_profile_post(self, member, ctx):

        q = users.find_one({"user_id": str(member.id)}, {"id": 0, "shikigami": 0, "cards": 0, "souls": 0})

        if q is None:
            await process_msg_invalid_member(ctx)

        else:
            count = ships.count_documents({"code": {"$regex": f".*{ctx.author.id}.*"}})

            amulets, amulets_b = q["amulets"], q["amulets_b"]
            amulets_spent, amulets_spent_b = q["amulets_spent"], q["amulets_spent_b"]
            experience, level, level_exp_next = q["experience"], q["level"], q["level_exp_next"]
            jades, talismans, coins, medals, sushi = q["jades"], q["talisman"], q["coins"], q["medals"], q["sushi"]
            friendship_points, parade, prayers = q["friendship"], q["parade_tickets"], q["prayers"]
            realm_ticket, enc_ticket, fp_pass = q["realm_ticket"], q["encounter_ticket"], q["friendship_pass"]
            display, nether_pass, achievements = q["display"], q["nether_pass"], q["achievements"]
            boss_damage, raid_successes, raid_failures = q["boss_damage"], q["raid_successes"], q["raid_failures"]

            embed = discord.Embed(color=member.colour, timestamp=get_timestamp())

            if display is not None:
                evo = users.find_one({
                    "user_id": str(member.id), "shikigami.name": display}, {
                    "shikigami.$": 1
                })["shikigami"][0]["evolved"]
                thumbnail = get_shikigami_url(display.lower(), get_evo_link(evo))
                embed.set_thumbnail(url=thumbnail)

            else:
                embed.set_thumbnail(url=member.default_avatar_url)

            def get_emoji_nether(x):
                if x is False:
                    return "❌"
                return "✅"

            embed.set_author(name=f"{member.display_name}'s profile", icon_url=member.default_avatar_url)
            embed.add_field(
                name=f"{e_x} Experience | Nether Pass",
                value=f"Lvl.{level} [{experience:,d}/{level_exp_next:,d}] | {get_emoji_nether(nether_pass)}"
            )
            embed.add_field(
                name=f"{e_1} | {e_2} | {e_3} | {e_4} | {e_5} | {e_6}",
                value=f"{q['SP']} | {q['SSR']} | {q['SR']} | {q['R']:,d} | {q['N']:,d} | {q['SSN']:,d}",
                inline=False
            )
            embed.add_field(
                name=f"Amulets Have/Spent [{e_b} | {e_a}]",
                value=f"[{amulets_b:,d}/{amulets_spent_b:,d} | {amulets:,d}/{amulets_spent:,d}]"
            )
            embed.add_field(
                name=f"Boss Damage Dealt | Raid [Success/Fail]",
                value=f"{boss_damage:,d} | [{raid_successes:,d}/{raid_failures:,d}]",
                inline=False
            )
            embed.add_field(
                name=f"{e_fp} | 🎟 | 🎫 | 🚢 | 🙏 | 🎏",
                value=f"{fp_pass} | {realm_ticket:,d} | {enc_ticket:,d} | {count} | {prayers} | {parade}",
                inline=False
            )
            embed.add_field(
                name=f"🍣 | {e_f} | {e_t} | {e_m} | {e_j} | {e_c}",
                value=f"{sushi:,d} | {friendship_points:,d} | {talismans:,d} | {medals:,d} | {jades:,d} | {coins:,d}"
            )

            msg = await process_msg_submit(ctx.channel, None, embed)
            await process_msg_reaction_add(msg, "🖼")
            await process_msg_reaction_add(msg, "🖼")

            def check(r, u):
                return str(r.emoji) in ["🖼"] and r.message.id == msg.id and u.bot is False

            def check2(r, u):
                return str(r.emoji) in ["➡"] and r.message.id == msg.id and u.bot is False

            async def embed_new_create(page_new):

                frame_new_url = await self.economy_profile_generate_frame_image_new(member, achievements, page_new)
                embed_new = discord.Embed(color=member.colour, timestamp=get_timestamp())
                embed_new.set_author(
                    name=f"{member.display_name}'s achievements [{len(achievements)}]",
                    icon_url=member.default_avatar_url
                )
                embed_new.set_image(url=frame_new_url)
                embed_new.set_footer(text="Hall of Frames")
                return embed_new

            page = 1
            page_total = ceil(len(achievements) / 20)

            try:
                await self.client.wait_for("reaction_add", timeout=15, check=check)
            except asyncio.TimeoutError:
                await process_msg_reaction_clear(msg)
                return
            else:
                await process_msg_edit(msg, None, await embed_new_create(page))
                await process_msg_reaction_clear(msg)
                await process_msg_reaction_add(msg, "➡")

            while True:
                try:
                    reaction, user = await self.client.wait_for("reaction_add", timeout=15, check=check2)
                except asyncio.TimeoutError:
                    await process_msg_reaction_clear(msg)
                    break
                else:
                    if str(reaction.emoji) == "➡":
                        page += 1
                    if page > page_total:
                        page = 1
                    await process_msg_edit(msg, None, await embed_new_create(page))

    async def economy_profile_generate_frame_image_new(self, member, achievements, page_new):

        end = page_new * 20
        start = end - 20

        achievements_address = []
        for entry in achievements:
            try:
                achievements_address.append(f"data/achievements/{entry['name']}.png")
            except KeyError:
                continue

        images = list(map(Image.open, achievements_address[start:end]))

        width, height = 1000, 800
        new_im = Image.new("RGBA", (width, height))

        def get_coordinates(c):
            x = (c * 200 - (ceil(c / 5) - 1) * 1000) - 200
            y = (ceil(c / 5) * 200) - 200
            return x, y

        for q, item in enumerate(images):
            new_im.paste(images[q], (get_coordinates(q + 1)))

        address = f"temp/{member.id}.png"
        new_im.save(address)
        image_file = discord.File(address, filename=f"{member.id}.png")
        hosting_channel = self.client.get_channel(int(id_hosting))
        msg = await process_msg_submit_file(hosting_channel, image_file)
        attachment_link = msg.attachments[0].url
        return attachment_link

    @commands.command(aliases=["shop"])
    @commands.guild_only()
    async def economy_shop_buy_items_show_all(self, ctx):

        embed = discord.Embed(
            title="Mystic Trader", colour=colour,
            description="exchange various economy items"
        )
        embed.set_thumbnail(url=seller_img)
        embed.add_field(name="Trading List", value="".join(trading_list_formatted), inline=False)
        embed.add_field(name="Example", value=f"*`{self.prefix}buy amulets 11`*", inline=False)

        msg = await process_msg_submit(ctx.channel, None, embed)
        await process_msg_reaction_add(msg, "🖼")

        def check(r, u):
            return str(r.emoji) == "🖼" and r.message.id == msg.id and self.client.user != u

        try:
            await self.client.wait_for("reaction_add", timeout=30, check=check)
        except asyncio.TimeoutError:
            await process_msg_reaction_clear(msg)
        else:
            seller = self.client.get_user(518416258312699906)

            embed = discord.Embed(
                title=f"{seller.name}'s Frame Shop", colour=colour,
                description="purchase premium frames for premium prices"
            )

            try:
                embed.set_thumbnail(url=seller.avatar_url)
            except AttributeError:
                pass

            for frame in frames.find({"purchase": True}, {"currency": 1, "amount": 1, "name": 1, "emoji": 1}):
                embed.add_field(
                    name=f"{frame['emoji']} {frame['name']}",
                    value=f"Acquire for {frame['amount']:,d}{get_emoji(frame['currency'])}",
                    inline=False
                )
            embed.add_field(name=f"Format", value=f"*`{self.prefix}buy frame <name>`*", inline=False)
            await process_msg_edit(msg, None, embed)

    @commands.command(aliases=["buy"])
    @commands.guild_only()
    async def economy_shop_buy_items(self, ctx, *args):

        user = ctx.author

        if len(args) == 0:
            embed = discord.Embed(
                title="buy", colour=colour,
                description=f"purchase from the list of items from the *`{self.prefix}shop`*"
            )
            embed.add_field(
                name="Format", inline=False,
                value=f"*`{self.prefix}buy <purchase_code>`*\n*`{self.prefix}buy frame <frame_name>`*"
            )
            await process_msg_submit(ctx.channel, None, embed)

        elif args[0].lower() in ["frame"] and len(args) > 1 and " ".join(args[1::]).lower() in shop_frames:

            frame_name = " ".join(args[1::]).lower().title()
            seller = self.client.get_user(518416258312699906)
            query = frames.find_one({"name": frame_name}, {"_id": 0})
            currency, amount = query["currency"], query["amount"]
            cost_item_have = users.find_one({"user_id": str(user.id)}, {"_id": 0, currency: 1})[currency]

            embed = discord.Embed(title="Confirm purchase?", color=ctx.author.colour, timestamp=get_timestamp())
            embed.description = f"{frame_name} frame for {amount:,d} {get_emoji(currency)}"
            embed.add_field(name="Inventory", value=f"{cost_item_have:,d} {get_emoji(currency)}", inline=False)
            embed.set_footer(icon_url=user.avatar_url, text=user.display_name)

            try:
                embed.set_thumbnail(url=seller.avatar_url)
            except AttributeError:
                pass

            msg = await process_msg_submit(ctx.channel, None, embed)
            await process_msg_reaction_add(msg, "✅")
            confirmation_answer = await self.economy_shop_buy_items_confirmation(ctx, msg)

            if confirmation_answer is True:
                await self.economy_shop_buy_items_process_purchase_frame(ctx, user, currency, amount, frame_name)

        else:
            try:
                offer_item, offer_amount, cost_item, cost_amount = get_offer_and_cost(args)

            except (KeyError, IndexError):
                embed = discord.Embed(
                    title="Invalid purchase code", colour=colour,
                    description=f"You entered an invalid purchase code",
                )
                await process_msg_submit(ctx.channel, None, embed)

            else:
                cost_item_have = users.find_one({"user_id": str(user.id)}, {"_id": 0, cost_item: 1})[cost_item]
                offer_item_have = users.find_one({"user_id": str(user.id)}, {"_id": 0, offer_item: 1})[offer_item]

                embed = discord.Embed(title="Confirm purchase?", colour=user.colour, timestamp=get_timestamp())
                embed.set_footer(icon_url=user.avatar_url, text=user.display_name)
                embed.description = \
                    f"{offer_amount} {get_emoji(offer_item)} for " \
                    f"{cost_amount:,d} {get_emoji(cost_item)}\n\n"
                embed.add_field(
                    name="Inventory",
                    value=f"{offer_item_have:,d} {get_emoji(offer_item)} | "
                          f"{cost_item_have:,d} {get_emoji(cost_item)}"
                )
                embed.set_thumbnail(url=seller_img)

                msg = await process_msg_submit(ctx.channel, None, embed)
                await process_msg_reaction_add(msg, "✅")
                confirmation_answer = await self.economy_shop_buy_items_confirmation(ctx, msg)

                if confirmation_answer is True:
                    await self.economy_shop_buy_items_process_purchase(
                        user, ctx, offer_item, offer_amount, cost_item, cost_amount, msg
                    )

    async def economy_shop_buy_items_confirmation(self, ctx, msg):

        def check(r, u):
            return u == ctx.author and str(r.emoji) == "✅" and msg.id == r.message.id

        try:
            await self.client.wait_for("reaction_add", timeout=7.0, check=check)
        except asyncio.TimeoutError:
            embed = discord.Embed(
                title="Timeout!", colour=ctx.author.colour, timestamp=get_timestamp(),
                description=f"No confirmation was received",
            )
            embed.set_footer(text=f"{ctx.author.display_name}", icon_url=ctx.author.avatar_url)
            embed.set_thumbnail(url=seller_img)
            await process_msg_edit(msg, None, embed)
            await process_msg_reaction_clear(msg)
            return False
        else:
            await process_msg_reaction_clear(msg)
            return True

    async def economy_shop_buy_items_process_purchase(self, user, ctx, offer_i, offer_a, cost_i, cost_a, msg):

        if users.find_one({"user_id": str(user.id)}, {"_id": 0, cost_i: 1})[cost_i] >= int(cost_a):
            users.update_one({
                "user_id": str(user.id)}, {
                "$inc": {
                    offer_i: int(offer_a),
                    cost_i: -int(cost_a)
                }
            })
            await perform_add_log(offer_i, offer_a, user.id)
            await perform_add_log(cost_i, -cost_a, user.id)

            cost_item_have = users.find_one({"user_id": str(user.id)}, {"_id": 0, cost_i: 1})[cost_i]
            offer_item_have = users.find_one({"user_id": str(user.id)}, {"_id": 0, offer_i: 1})[offer_i]

            embed = discord.Embed(title="Purchase successful", colour=user.color, timestamp=get_timestamp())
            embed.set_footer(icon_url=user.avatar_url, text=f"{user.display_name}")
            embed.description = f"You acquired {offer_a:,d}{get_emoji(offer_i)} " \
                                f"in exchange for {cost_a:,d}{get_emoji(cost_i)}"
            embed.set_thumbnail(url=seller_img)
            embed.add_field(
                name="Inventory",
                value=f"{offer_item_have:,d} {get_emoji(offer_i)} | "
                      f"{cost_item_have:,d} {get_emoji(cost_i)}"
            )
            await process_msg_edit(msg, None, embed)

        else:
            embed = discord.Embed(
                title="Purchase failure", colour=colour,
                description=f"You have insufficient {get_emoji(cost_i)}",
            )
            embed.set_footer(icon_url=user.avatar_url, text=f"{user.display_name}")
            await process_msg_submit(ctx.channel, None, embed)

    async def economy_shop_buy_items_process_purchase_frame(self, ctx, user, currency, amount, frame_name):

        if users.find_one({"user_id": str(user.id)}, {"_id": 0, currency: 1})[currency] >= amount:

            if users.find_one({"user_id": str(user.id), "achievements.name": frame_name}, {"_id": 0}) is None:
                users.update_one({
                    "user_id": str(user.id)}, {
                    "$inc": {
                        currency: -amount
                    },
                    "$push": {
                        "achievements": {
                            "name": frame_name,
                            "date_acquired": get_time()
                        }
                    }
                })
                await perform_add_log(currency, -amount, user.id)

                embed = discord.Embed(
                    title="Confirmation receipt", colour=colour, timestamp=get_timestamp(),
                    description=f"You acquired {frame_name} in exchange for {amount:,d}{get_emoji(currency)}",
                )
                embed.set_footer(text=ctx.author.display_name, icon_url=ctx.author.avatar_url)
                await process_msg_submit(ctx.channel, None, embed)

            else:
                embed = discord.Embed(
                    title="Purchase failure", colour=colour,
                    description=f"this frame is already in your possession",
                )
                await process_msg_submit(ctx.channel, None, embed)

        else:
            embed = discord.Embed(
                title="Purchase failure", colour=colour,
                description=f" You have insufficient {get_emoji(currency)}",
            )
            await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["logs"])
    @commands.guild_only()
    async def economy_logs_show(self, ctx, *, member: discord.Member = None):

        if member is None:
            await self.economy_logs_show_member(ctx, ctx.author)

        elif member is not None:
            try:
                member.id
            except AttributeError:
                await process_msg_invalid_member(ctx)
            else:
                await self.economy_logs_show_member(ctx, member)

    async def economy_logs_show_member(self, ctx, member):

        listings_formatted = []

        for entry in logs.find_one({"user_id": str(member.id)}, {"_id": 0, "logs": 1})["logs"][:200]:
            operator = "+"
            if entry['amount'] < 0:
                operator = ""

            emoji = get_emoji(entry['currency'])
            timestamp = get_time_converted(entry['date'])
            listings_formatted.append(
                f"`[{timestamp.strftime('%d.%b %H:%M')}]` | `{operator}{entry['amount']:,d}`{emoji}\n"
            )

        await self.economy_logs_show_paginate(ctx.channel, listings_formatted, member)

    async def economy_logs_show_paginate(self, channel, listings_formatted, member):

        page, max_lines = 1, 15
        page_total = ceil(len(listings_formatted) / max_lines)
        if page_total == 0:
            page_total = 1

        def embed_new_create(page_new):
            end = page * max_lines
            start = end - max_lines
            description = "".join(listings_formatted[start:end])

            embed_new = discord.Embed(color=member.colour, description=description)
            embed_new.set_author(name=f"{member.display_name}", icon_url=member.default_avatar_url)
            embed_new.set_footer(text=f"Last 200 only | Page: {page_new} of {page_total}")

            return embed_new

        msg = await process_msg_submit(channel, None, embed_new_create(page))

        emojis_add = ["⬅", "➡"]
        for emoji in emojis_add:
            await process_msg_reaction_add(msg, emoji)

        def check(r, u):
            return u != self.client.user and r.message.id == msg.id and str(r.emoji) in emojis_add

        while True:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=60, check=check)
            except asyncio.TimeoutError:
                await process_msg_reaction_clear(msg)
                break
            else:
                if str(reaction.emoji) == emojis_add[1]:
                    page += 1
                elif str(reaction.emoji) == emojis_add[0]:
                    page -= 1
                if page == 0:
                    page = page_total
                elif page > page_total:
                    page = 1
                await process_msg_edit(msg, None, embed_new_create(page))
                await process_msg_reaction_remove(msg, str(reaction.emoji), user)


def setup(client):
    client.add_cog(Economy(client))
