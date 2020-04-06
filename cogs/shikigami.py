"""
Shikigami Module
Miketsu, 2020
"""

from PIL import Image
from discord.ext import commands

from cogs.ext.initialize import *


class Shikigami(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.prefix = self.client.command_prefix

    async def shikigami_image_show_collected_help(self, ctx):

        embed = discord.Embed(
            title="collection, col", colour=colour,
            description="shows your or tagged member's shikigami pulls by rarity without the count"
        )
        embed.add_field(
            name="Format", inline=False,
            value=f"*`{self.prefix}col <rarity> <optional: @member>`*"
        )
        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["collection", "col", "collections"])
    @commands.guild_only()
    async def shikigami_image_show_collected(self, ctx, rarity=None, *, member: discord.Member = None):

        if rarity is None:
            await self.shikigami_image_show_collected_help(ctx)

        else:
            rarity_upper = rarity.upper()

            if rarity_upper not in rarities:
                await self.shikigami_image_show_collected_help(ctx)

            elif member is None:
                await self.shikigami_show_post_collected(ctx.author, rarity_upper, ctx)

            else:
                try:
                    member.id
                except AttributeError:
                    await process_msg_invalid_member(ctx)
                else:
                    await self.shikigami_show_post_collected(member, rarity_upper, ctx)

    async def shikigami_show_post_collected(self, member, rarity, ctx):

        listings_shikis_evo, listings_shikis, listings_rarity_all = [], [], get_pool_rarity(rarity)
        for entry in users.aggregate([{
            "$match": {
                "user_id": str(member.id)}}, {
            "$unwind": {
                "path": "$shikigami"}}, {
            "$match": {
                "shikigami.rarity": rarity}}, {
            "$project": {
                "_id": 0,
                "shikigami.name": 1,
                "shikigami.owned": 1,
                "shikigami.shards": 1,
                "shikigami.evolved": 1
            }}, {
            "$match": {
                "shikigami.owned": {
                    "$gt": 0
                }}}
        ]):
            listings_shikis_evo.append((entry["shikigami"]["name"], entry["shikigami"]["evolved"]))
            listings_shikis.append(entry["shikigami"]["name"])

        listings_uncollected = list(set(listings_rarity_all) - set(listings_shikis))

        link = await self.shikigami_show_post_collected_generate(
            listings_shikis_evo, listings_uncollected, listings_rarity_all, rarity, member
        )

        embed = discord.Embed(
            title=f"{get_rarity_emoji(rarity)} Collection",
            color=member.colour, timestamp=get_timestamp()
        )
        embed.set_image(url=link)
        embed.set_footer(icon_url=member.avatar_url, text=f"{member.display_name}")
        await process_msg_submit(ctx.channel, None, embed)

    async def shikigami_show_post_collected_generate(self, shikis, shikis_unc, listings_rarity_all, rarity, member):

        rows, cols = get_variables(rarity)
        print(rows, cols, listings_rarity_all)
        width, height = get_image_variables(listings_rarity_all, cols, rows)

        print(width, height)
        new_im = Image.new("RGBA", (width, height))

        images = []
        for entry in shikis:
            address = f"data/shikigamis/{entry[0]}_pre.jpg"
            if entry[1] is True:
                address = f"data/shikigamis/{entry[0]}_evo.jpg"
            images.append(Image.open(address))

        for entry in shikis_unc:
            address = f"data/shikigamis/{entry}_pre.jpg"
            images.append(Image.open(address).convert("LA"))

        for index, item in enumerate(images):
            new_im.paste(images[index], (get_shiki_tile_coordinates(index + 1, cols, rows)))

        address_temp = f"temp/{member.id}.png"
        new_im.save(address_temp)

        image_file = discord.File(address_temp, filename=f"{member.id}.png")
        hosting_channel = self.client.get_channel(int(id_hosting))
        msg = await process_msg_submit_file(hosting_channel, image_file)
        attachment_link = msg.attachments[0].url

        return attachment_link

    async def shikigami_list_show_collected_help(self, ctx):

        embed = discord.Embed(
            title="shikilist, sl", colour=colour,
            description="shows your shikigami listings by rarity "
        )
        embed.add_field(
            name="Formats", inline=False,
            value=f"*`{self.prefix}shikilist <rarity>`*",
        )
        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["shikilist", "sl"])
    @commands.guild_only()
    async def shikigami_list_show_collected(self, ctx, rarity=None, *, member: discord.Member = None):

        if rarity is None:
            await self.shikigami_list_show_collected_help(ctx)

        else:
            rarity_upper = rarity.upper()

            if rarity_upper not in rarities:
                await self.shikigami_list_show_collected_help(ctx)

            elif member is None:
                await self.shikigami_list_post_collected(ctx.author, rarity_upper, ctx)

            else:
                try:
                    member.id
                except AttributeError:
                    await process_msg_invalid_member(ctx)
                else:
                    await self.shikigami_list_post_collected(member, rarity_upper, ctx)

    async def shikigami_list_post_collected(self, member, rarity, ctx):

        listings_shikis, listings_shikis_formatted = [], []
        for entry in users.aggregate([{
            "$match": {
                "user_id": str(member.id)
            }}, {
            "$unwind": {
                "path": "$shikigami"
            }}, {
            "$match": {
                "shikigami.rarity": rarity
            }}, {
            "$project": {
                "_id": 0,
                "shikigami.name": 1,
                "shikigami.owned": 1,
                "shikigami.shards": 1
            }
        }]):
            listings_shikis.append((
                entry["shikigami"]["name"], entry["shikigami"]["owned"], entry["shikigami"]["shards"]
            ))

        user_shikigamis_sorted = sorted(listings_shikis, key=lambda x: x[1], reverse=True)

        for shiki in user_shikigamis_sorted:
            listings_shikis_formatted.append(f"• {shiki[0].title()} | `x{shiki[1]} [{shiki[2]} shards]`\n")

        await self.shikigami_list_paginate(member, listings_shikis_formatted, rarity, ctx, "Shikigamis")

    async def shikigami_list_paginate(self, member, listings_formatted, rarity, ctx, title):

        page, max_lines = 1, 10
        page_total = ceil(len(listings_formatted) / max_lines)
        if page_total == 0:
            page_total = 1

        def embed_new_create(page_new):
            end = page_new * max_lines
            start = end - max_lines

            embed_new = discord.Embed(
                color=member.colour, timestamp=get_timestamp(),
                title=f"{get_rarity_emoji(rarity)} {title}",
                description="".join(listings_formatted[start:end])
            )
            embed_new.set_footer(
                text=f"Page: {page_new} of {page_total}",
                icon_url=member.avatar_url
            )
            return embed_new

        msg = await process_msg_submit(ctx.channel, None, embed_new_create(1))

        emojis_add = ["⬅", "➡"]
        for emoji in emojis_add:
            await process_msg_reaction_add(msg, emoji)

        def check(r, m):
            return m != self.client.user and r.message.id == msg.id and str(r.emoji) in emojis_add

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

    async def shikigami_show_post_shards_help(self, ctx):

        embed = discord.Embed(
            title="shards", colour=colour,
            description="shows your or tagged member's shikigami shards count by rarity"
        )
        embed.add_field(
            name="Format", inline=False,
            value=f"*`{self.prefix}shards <rarity> <optional: @member>`*"
        )
        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["shards"])
    @commands.guild_only()
    async def shikigami_show_post_shards(self, ctx, rarity=None, *, member: discord.Member = None):

        if rarity is None:
            await self.shikigami_image_show_collected_help(ctx)

        else:
            rarity_upper = rarity.upper()

            if rarity_upper not in rarities:
                await self.shikigami_image_show_collected_help(ctx)

            elif member is None:
                await self.shikigami_show_post_shards_user(ctx.author, rarity_upper, ctx)

            else:
                try:
                    member.id
                except AttributeError:
                    await process_msg_invalid_member(ctx)
                else:
                    await self.shikigami_show_post_shards_user(member, rarity_upper, ctx)

    async def shikigami_show_post_shards_user(self, member, rarity, ctx):

        listings_shikis_evo, listings_shikis, pool_rarity = [], [], get_pool_rarity(rarity)
        for entry in users.aggregate([{
            "$match": {
                "user_id": str(member.id)}}, {
            "$unwind": {
                "path": "$shikigami"}}, {
            "$match": {
                "shikigami.rarity": rarity}}, {
            "$project": {
                "_id": 0,
                "shikigami.name": 1,
                "shikigami.owned": 1,
                "shikigami.shards": 1,
                "shikigami.evolved": 1
            }}, {
            "$match": {
                "shikigami.owned": {
                    "$gt": 0
                }}}
        ]):
            listings_shikis_evo.append(
                (entry["shikigami"]["name"], entry["shikigami"]["evolved"], entry["shikigami"]["shards"])
            )
            listings_shikis.append(entry["shikigami"]["name"])

        uncollected_list = list(set(pool_rarity) - set(listings_shikis))

        link = await self.shikigami_show_post_shards_generate(
            listings_shikis_evo, uncollected_list, pool_rarity, rarity, member
        )

        embed = discord.Embed(
            title=f"{get_rarity_emoji(rarity)} Collection - Shards",
            color=member.colour, timestamp=get_timestamp()
        )
        embed.set_image(url=link)
        embed.set_footer(icon_url=member.avatar_url, text=f"{member.display_name}")
        await process_msg_submit(ctx.channel, None, embed)

    async def shikigami_show_post_shards_generate(self, shikis, shikis_unc, pool_rarity, rarity, member):

        def get_shard_uncollected(shikigami_name):
            try:
                for result in users.aggregate([{
                    '$match': {'user_id': str(member.id)}}, {
                    '$unwind': {'path': '$shikigami'}}, {
                    '$match': {'shikigami.rarity': rarity}}, {
                    '$project': {'_id': 0, 'shikigami.name': 1, 'shikigami.shards': 1}}, {
                    '$match': {'shikigami.name': shikigami_name}
                }]):
                    return result["shikigami"]["shards"]
            except KeyError:
                return 0

        images, font, x, y = [], font_create(30), 1, 60
        rows, cols = get_variables(rarity)

        width, height = get_image_variables(pool_rarity, cols, rows)
        new_im = Image.new("RGBA", (width, height))

        for entry in shikis:
            address = f"data/shikigamis/{entry[0]}_pre.jpg"
            if entry[1] is True:
                address = f"data/shikigamis/{entry[0]}_evo.jpg"

            shikigami_thumbnail = Image.open(address)
            shikigami_image_final = shikigami_shards_count_generate(shikigami_thumbnail, entry[2], font, x, y)
            images.append(shikigami_image_final)

        for entry in shikis_unc:
            address = f"data/shikigamis/{entry}_pre.jpg"
            count = get_shard_uncollected(entry)
            if count is None:
                count = 0

            shikigami_thumbnail = Image.open(address).convert("LA")
            shikigami_image_final = shikigami_shards_count_generate(shikigami_thumbnail, count, font, x, y)
            images.append(shikigami_image_final)

        for index, item in enumerate(images):
            new_im.paste(images[index], (get_shiki_tile_coordinates(index + 1, cols, rows)))

        address_temp = f"temp/{member.id}.png"
        new_im.save(address_temp)
        image_file = discord.File(address_temp, filename=f"{member.id}.png")
        hosting_channel = self.client.get_channel(int(id_hosting))
        msg = await process_msg_submit_file(hosting_channel, image_file)
        attachment_link = msg.attachments[0].url
        return attachment_link

    async def shikigami_show_post_shiki_help(self, ctx):

        embed = discord.Embed(
            title="shikigami, shiki", colour=colour,
            description="shows your shikigami profile stats"
        )
        embed.add_field(
            name="Formats", inline=False,
            value=f"*`{self.prefix}shikigami <shikigami name>`*"
        )
        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["shiki", "shikigami"])
    @commands.guild_only()
    async def shikigami_show_post_shiki(self, ctx, *, shikigami_name=None):

        if shikigami_name is None and not check_if_user_has_shiki_set(ctx):
            await self.shikigami_show_post_shiki_help(ctx)

        elif shikigami_name is None and check_if_user_has_shiki_set(ctx):
            shikigami_name_lowered = get_shikigami_display(ctx.author)
            query = users.find_one({
                "user_id": str(ctx.author.id),
                "shikigami.name": shikigami_name_lowered
            }, {
                "_id": 0, "shikigami.$": 1
            })
            await self.shikigami_show_post_shiki_user(ctx.author, query, shikigami_name_lowered, ctx)

        else:
            shikigami_name_lowered = shikigami_name.lower()
            query = users.find_one({
                "user_id": str(ctx.author.id),
                "shikigami.name": shikigami_name_lowered
            }, {
                "_id": 0, "shikigami.$": 1
            })

            if shikigami_name_lowered not in pool_all:
                await shikigami_post_approximate_results(ctx, shikigami_name_lowered)

            elif query is None:
                embed = discord.Embed(
                    colour=ctx.author.colour, title="Invalid selection",
                    description=f"this shikigami is not in your possession"
                )
                await process_msg_submit(ctx.channel, None, embed)

            else:
                await self.shikigami_show_post_shiki_user(ctx.author, query, shikigami_name_lowered, ctx)

    async def shikigami_show_post_shiki_user(self, user, query, shikigami_name, ctx):

        shiki_profile = query["shikigami"][0]
        listings_souls_slots, listings_souls, evolve = [], [], "pre"

        if shiki_profile["evolved"] is True:
            evolve = "evo"

        thumbnail = get_shikigami_url(shikigami_name, evolve)

        for result in users.aggregate([{
            '$match': {'user_id': str(user.id)}
        }, {
            '$project': {'souls': 1}
        }, {
            '$project': {'souls': {'$objectToArray': '$souls'}}
        }, {
            '$unwind': {'path': '$souls'}
        }, {
            '$unwind': {'path': '$souls.v'}
        }, {
            '$match': {'souls.v.equipped': shikigami_name}
        }
        ]):
            listings_souls.append([
                result["souls"]["k"], result["souls"]["v"]["grade"], result["souls"]["v"]["slot"]
            ])
            listings_souls_slots.append(result["souls"]["v"]["slot"])

        for i in range(1, 7):
            if i not in listings_souls_slots:
                listings_souls.append([None, 0, i])

        listings_souls = sorted(listings_souls, key=lambda z: z[2], reverse=False)
        print(listings_souls)

        embed = discord.Embed(
            colour=user.colour, timestamp=get_timestamp(),
            description=f"```"
                        f"Level  ::   {shiki_profile['level']}\n"
                        f"Exp    ::   {shiki_profile['exp']}/{shiki_profile['level_exp_next']}\n"
                        f"Grade  ::   {shiki_profile['grade']}\n"
                        f"Owned  ::   {shiki_profile['owned']}\n"
                        f"Shards ::   {shiki_profile['shards']}\n"
                        f"```",
        )

        embed.set_thumbnail(url=thumbnail)
        embed.set_author(
            name=f"{user.display_name}'s {shikigami_name.title()}",
            icon_url=user.avatar_url
        )
        embed.set_footer(text=f"Rarity: {shiki_profile['rarity']}")
        msg = await process_msg_submit(ctx.channel, None, embed)

        emojis_add = ["🏵️"]
        for emoji in emojis_add:
            await process_msg_reaction_add(msg, emoji)

        def check(r, u):
            return u != self.client.user and str(r.emoji) in emojis_add and r.message.id == msg.id

        try:
            await self.client.wait_for("reaction_add", timeout=10, check=check)
        except asyncio.TimeoutError:
            await process_msg_reaction_clear(msg)
        else:
            link = await self.shikigami_show_post_shiki_user_soul_generate(ctx, shikigami_name, evolve, listings_souls)
            embed.set_image(url=link)
            await process_msg_edit(msg, None, embed)
            await process_msg_reaction_clear(msg)

    async def shikigami_show_post_shiki_user_soul_generate(self, ctx, shikigami_name, evo, listings_souls):

        width, height, d, height_base = int(348.48), int(348.48), 72, 17
        w_hex, h_hex = 1.95 * 96, 1.7 * 96
        x_coor, y_coor = int((width / 2) - (90 / 2)), int((height / 2) - (90 / 2))

        im = Image.new('RGBA', (width, height), (255, 0, 0, 0))
        bd = Image.open("data/raw/souls.png").resize((width, height), Image.ANTIALIAS)
        shiki_im = Image.open(f"data/shikigamis/{shikigami_name}_{evo}.jpg")

        im.paste(shiki_im, (x_coor, y_coor))
        im.paste(bd, (0, 0), bd)

        def create_magatama_grade(g, magatama_raw):
            im_new = Image.new('RGBA', (w + (35 * (g - 1)), h), (255, 0, 0, 0))

            def get_new_coor_magatama(i):
                return (i - 1) * 35, 0

            for y in list(range(1, g + 1)):
                im_new.paste(magatama_raw, get_new_coor_magatama(y), magatama_raw)

            return im_new

        def get_soul_coordinates(s):
            soul_coordinates_plot = {
                "1": [((width - 90) / 2) - (d / 2), ((height - h_hex) / 2) - (d / 2)],
                "2": [((width - w_hex) / 2) - (d / 2) + 2, (height / 2) - (d / 2)],
                "3": [((width - 90) / 2) - (d / 2), (((height - h_hex) / 2) + h_hex) - (d / 2)],
                "4": [(((width - 90) / 2) + 94) - (d / 2), (((height - h_hex) / 2) + h_hex) - (d / 2)],
                "5": [((width - w_hex) / 2) - (d / 2) + 2 + w_hex, (height / 2) - (d / 2)],
                "6": [(((width - 90) / 2) + 94) - (d / 2), ((height - h_hex) / 2) - (d / 2)],
            }
            return int(soul_coordinates_plot[s][0]), int(soul_coordinates_plot[s][1])

        for index, q in enumerate(range(1, 7)):

            if listings_souls[index][0] is not None:
                im_magatama = Image.open("data/raw/magatama.png")
                w, h = im_magatama.size
                magatama_graded = create_magatama_grade(listings_souls[index][1], im_magatama)

                h_percent = (height_base / float(magatama_graded.size[1]))
                w_size = int((float(magatama_graded.size[0]) * float(h_percent)))
                x = magatama_graded.resize((w_size, height_base), Image.ANTIALIAS)
                souls_im = Image.open(f"data/souls/{listings_souls[index][0]}.png").resize((d, d), Image.ANTIALIAS)
                im.paste(souls_im, (get_soul_coordinates(str(index + 1))), souls_im)
                im.paste(
                    x,
                    (
                        get_soul_coordinates(str(index + 1))[0] + int(d / 2) - int(w_size / 2),
                        get_soul_coordinates(str(index + 1))[1] + d - height_base
                    ),
                    x
                )

        address_temp = f"temp/{ctx.author.id}.png"
        im.save(address_temp, quality=95)
        image_file = discord.File(address_temp, filename=f"{ctx.message.id}.png")
        hosting_channel = self.client.get_channel(int(id_hosting))
        msg = await process_msg_submit_file(hosting_channel, image_file)
        attachment_link = msg.attachments[0].url
        return attachment_link

    async def shikigami_show_post_shikis_help(self, ctx):

        embed = discord.Embed(
            title="shikigamis, shikis", colour=colour,
            description="shows your or tagged member's shikigami pulls by rarity"
        )
        embed.add_field(
            name="Format", inline=False,
            value=f"*`{self.prefix}shikis <rarity> <optional: @member>`*"
        )
        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["shikis", "shikigamis"])
    @commands.guild_only()
    async def shikigami_show_post_shikis(self, ctx, rarity=None, *, member: discord.Member = None):

        if rarity is None:
            await self.shikigami_show_post_shikis_help(ctx)

        else:
            rarity_upper = rarity.upper()

            if rarity_upper not in rarities:
                await self.shikigami_show_post_shikis_help(ctx)

            elif member is None:
                await self.shikigami_show_post_shikis_user(ctx.author, rarity_upper, ctx)

            else:
                try:
                    member.id
                except AttributeError:
                    await process_msg_invalid_member(ctx)
                else:
                    await self.shikigami_show_post_shikis_user(member, rarity_upper, ctx)

    async def shikigami_show_post_shikis_user(self, member, rarity, ctx):

        listings_shikis_evo, listings_shikis, pool_rarity = [], [], get_pool_rarity(rarity)
        for entry in users.aggregate([{
            "$match": {
                "user_id": str(member.id)}}, {
            "$unwind": {
                "path": "$shikigami"}}, {
            "$match": {
                "shikigami.rarity": rarity}}, {
            "$project": {
                "_id": 0,
                "shikigami.name": 1,
                "shikigami.owned": 1,
                "shikigami.shards": 1,
                "shikigami.evolved": 1
            }}, {
            "$match": {
                "shikigami.owned": {
                    "$gt": 0
                }}}
        ]):
            listings_shikis_evo.append(
                (entry["shikigami"]["name"], entry["shikigami"]["evolved"], entry["shikigami"]["owned"])
            )
            listings_shikis.append(entry["shikigami"]["name"])

        uncollected_list = list(set(pool_rarity) - set(listings_shikis))

        link = await self.shikigami_show_post_shikis_generate(
            listings_shikis_evo, uncollected_list, pool_rarity, rarity, member
        )

        embed = discord.Embed(
            title=f"{get_rarity_emoji(rarity)} Collection - Count",
            color=member.colour, timestamp=get_timestamp()
        )
        embed.set_image(url=link)
        embed.set_footer(icon_url=member.avatar_url, text=f"{member.display_name}")
        await process_msg_submit(ctx.channel, None, embed)

    async def shikigami_show_post_shikis_generate(self, shikis, shikis_unc, pool_rarity, rarity, member):

        images, font, x, y = [], font_create(30), 1, 60
        rows, cols = get_variables(rarity)

        width, height = get_image_variables(pool_rarity, cols, rows)
        new_im = Image.new("RGBA", (width, height))

        for entry in shikis:
            address = f"data/shikigamis/{entry[0]}_pre.jpg"
            if entry[1] is True:
                address = f"data/shikigamis/{entry[0]}_evo.jpg"

            shikigami_thumbnail = Image.open(address)
            shikigami_image_final = shikigami_shards_count_generate(shikigami_thumbnail, entry[2], font, x, y)
            images.append(shikigami_image_final)

        for entry in shikis_unc:
            address = f"data/shikigamis/{entry}_pre.jpg"
            shikigami_thumbnail = Image.open(address).convert("LA")
            shikigami_image_final = shikigami_shards_count_generate(shikigami_thumbnail, 0, font, x, y)
            images.append(shikigami_image_final)

        for index, item in enumerate(images):
            new_im.paste(images[index], (get_shiki_tile_coordinates(index + 1, cols, rows)))

        address_temp = f"temp/{member.id}.png"
        new_im.save(address_temp)
        image_file = discord.File(address_temp, filename=f"{member.id}.png")
        hosting_channel = self.client.get_channel(int(id_hosting))
        msg = await process_msg_submit_file(hosting_channel, image_file)
        attachment_link = msg.attachments[0].url
        return attachment_link

    async def profile_change_shikigami_help(self, ctx):

        embed = discord.Embed(
            title="display", colour=colour,
            description="changes your profile display thumbnail"
        )
        embed.add_field(name="Example", value=f"*`{self.prefix}set inferno ibaraki`*", inline=False)
        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["set", "display"])
    @commands.guild_only()
    async def profile_change_shikigami(self, ctx, *, shikigami_name=None):

        if shikigami_name is None:
            await self.profile_change_shikigami_help(ctx)

        else:
            shikigami_name_lower = shikigami_name.lower()

            if shikigami_name_lower is None:
                users.update_one({"user_id": str(ctx.author.id)}, {"$set": {"display": shikigami_name_lower}})
                await process_msg_reaction_add(ctx.message, "✅")

            elif shikigami_name_lower not in pool_all:
                await shikigami_post_approximate_results(ctx, shikigami_name_lower)

            elif shikigami_name_lower in pool_all:
                count = users.count_documents({"user_id": str(ctx.author.id), "shikigami.name": shikigami_name_lower})

                if count != 1:
                    embed = discord.Embed(
                        colour=ctx.author.colour, title="Invalid selection",
                        description=f"This shikigami is not in your possession"
                    )
                    await process_msg_submit(ctx.channel, None, embed)

                elif count >= 1:
                    users.update_one({"user_id": str(ctx.author.id)}, {"$set": {"display": shikigami_name_lower}})
                    await process_msg_reaction_add(ctx.message, "✅")

    async def shikigami_shrine_help(self, ctx, action):

        if action is None:

            embed = discord.Embed(
                title="shrine", colour=colour,
                description="exchange your shikigamis for talismans to acquire exclusive shikigamis"
            )
            embed.add_field(name="Arguments", value=f"*sacrifice, exchange*", inline=False)
            embed.add_field(name="Example", value=f"*`{self.prefix}shrine exchange`*", inline=False)

        elif action is True:

            embed = discord.Embed(
                title="shrine sacrifice, shr s", colour=colour,
                description="sacrifice your shikigamis to the shrine in exchange for talismans"
            )
            embed.add_field(
                name="Rarity :: Talisman", inline=False,
                value="```"
                      "SP     ::  50,000\n"
                      "SSR    ::  25,000\n"
                      "SR     ::   1,000\n"
                      "R      ::      75\n"
                      "```",
            )
            embed.add_field(name="Format", value=f"*`{self.prefix}shrine s <shikigami>`*")

        else:
            embed = discord.Embed(
                title="shrine exchange, shrine exc", colour=colour,
                description="exchange your talismans for exclusive shrine only shikigamis"
            )
            embed.add_field(
                name="Shikigami :: Talisman", inline=False,
                value="```"
                      "Juzu          ::     50,000\n"
                      "Usagi         ::     50,000\n"
                      "Tenjo Kudari  ::     50,000\n"
                      "Mannendake    ::    150,000\n"
                      "Jinmenju      ::    150,000\n"
                      "Kainin        ::    150,000\n"
                      "Ryomen        ::    350,000"
                      "```",
            )
            embed.add_field(name="Formats", value=f"*`{self.prefix}shrine exc <shikigami>`*")

        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["shrine", "shr"])
    @commands.guild_only()
    @commands.cooldown(1, 90, commands.BucketType.user)
    async def shikigami_shrine(self, ctx, action=None, *, shikigami_name=None):

        user = ctx.author

        if action is None and shikigami_name is None:
            await self.shikigami_shrine_help(ctx, None)

        elif action.lower() in ["sacrifice", "s"] and shikigami_name is None:
            await self.shikigami_shrine_help(ctx, True)

        elif action.lower() in ["exchange", "exc"] and shikigami_name is None:
            await self.shikigami_shrine_help(ctx, False)

        elif action.lower() in ["sacrifice", "s"] and shikigami_name.lower() not in pool_all_mystery:
            await shikigami_post_approximate_results(ctx, shikigami_name.lower())

        elif action.lower() in ["exchange", "exc"] and shikigami_name.lower() not in pool_shrine:
            await shikigami_post_approximate_results(ctx, shikigami_name.lower())

        elif action.lower() in ["sacrifice", "s"] and shikigami_name.lower() in pool_all_mystery:
            await self.shikigami_shrine_sacrifice(shikigami_name.lower(), user, ctx)

        elif action.lower() in ["exchange", "exc"] and shikigami_name.lower() in pool_shrine:
            await self.shikigami_shrine_exchange(shikigami_name.lower(), user, ctx)

        self.client.get_command("shikigami_shrine").reset_cooldown(ctx)

    async def shikigami_shrine_sacrifice(self, shikigami_name, user, ctx):

        shikigami_name_lower = shikigami_name.lower()

        query = users.find_one({
            "user_id": str(user.id), "shikigami.name": shikigami_name_lower
        }, {
            "_id": 0, "shikigami.$.name": 1
        })

        if query is None:
            embed = discord.Embed(
                colour=user.colour, title=f"Invalid shikigami",
                description=f"no shikigami {shikigami_name_lower.title()} in your possession yet"
            )
            await process_msg_submit(ctx.channel, None, embed)
        else:
            count_shikigami, rarity = query["shikigami"][0]["owned"], query["shikigami"][0]["rarity"]
            talisman_per = get_talisman_acquire(rarity)

            def check(m):
                try:
                    int(m.content)
                except (TypeError, ValueError):
                    raise KeyboardInterrupt
                else:
                    return m.author == ctx.author and m.channel == ctx.channel

            embed = discord.Embed(
                colour=user.colour, timestamp=get_timestamp(), title=f"Specify amount",
                description=f"You currently have {count_shikigami:,d} {shikigami_name_lower.title()}",
            )
            embed.set_thumbnail(url=get_shikigami_url(shikigami_name_lower, "evo"))
            embed.set_footer(text=f"{user.display_name}", icon_url=user.avatar_url)
            msg = await process_msg_submit(ctx.channel, None, embed)

            try:
                message = await self.client.wait_for("message", timeout=15, check=check)
            except asyncio.TimeoutError:
                embed = discord.Embed(
                    title="Timeout!", colour=user.colour,
                    description=f"Enter the amount on time", timestamp=get_timestamp()
                )
                embed.set_footer(text=f"{user.display_name}", icon_url=user.avatar_url)
                await process_msg_edit(msg, None, embed)
            except KeyboardInterrupt:
                embed = discord.Embed(
                    title="Invalid amount", colour=user.colour,
                    description=f"provide a valid integer", timestamp=get_timestamp()
                )
                embed.set_thumbnail(url=get_shikigami_url(shikigami_name_lower, "evo"))
                embed.set_footer(text=f"{user.display_name}", icon_url=user.avatar_url)
                await process_msg_edit(msg, None, embed)

            else:
                request_shrine = int(message.content)

                if count_shikigami >= request_shrine:
                    final_talismans = talisman_per * request_shrine
                    users.update_one({
                        "user_id": str(user.id),
                        "shikigami.name": shikigami_name_lower}, {
                        "$inc": {
                            "shikigami.$.owned": - request_shrine,
                            "talisman": final_talismans,
                            f"{rarity}": - request_shrine
                        }
                    })
                    await perform_add_log("talisman", final_talismans, user.id)
                    embed = discord.Embed(
                        title="Shrine successful", colour=user.colour, timestamp=get_timestamp(),
                        description=f"You shrined {shikigami_name_lower.title()} for {final_talismans:,d}{e_t}",
                    )
                    embed.set_thumbnail(url=get_shikigami_url(shikigami_name_lower, "evo"))
                    embed.set_footer(text=f"{user.display_name}", icon_url=user.avatar_url)
                    await process_msg_edit(msg, None, embed)

                else:
                    embed = discord.Embed(
                        title="Insufficient shikigamis", colour=user.colour, timestamp=get_timestamp(),
                        description=f"You lack that amount of shikigami {shikigami_name_lower.title()}",
                    )
                    embed.set_thumbnail(url=get_shikigami_url(shikigami_name_lower, "evo"))
                    embed.set_footer(text=f"{user.display_name}", icon_url=user.avatar_url)
                    await process_msg_submit(ctx.channel, None, embed)

            finally:
                self.client.get_command("shikigami_shrine").reset_cooldown(ctx)

    async def shikigami_shrine_exchange(self, shikigami_name, user, ctx):

        shikigami_name_lower = shikigami_name.lower()
        rarity = shikigamis.find_one({"name": shikigami_name_lower}, {"_id": 0, "rarity": 1})["rarity"]
        talisman = users.find_one({"user_id": str(user.id)}, {"_id": 0, "talisman": 1})["talisman"]

        def get_talisman_required(x):
            return {"SSR": 350000, "SR": 150000, "R": 50000}[x]

        talisman_req = get_talisman_required(rarity)

        if talisman >= talisman_req:
            embed = discord.Embed(
                title="Exchange confirmation", colour=colour, timestamp=get_timestamp(),
                description=f"Confirm exchange of {talisman_req:,d}{e_t} for a {shikigami_name_lower.title()}",
            )
            embed.set_footer(icon_url=user.avatar_url, text=f"{user.display_name}")
            msg = await process_msg_submit(ctx.channel, None, embed)

            await process_msg_reaction_add(msg, "✅")

            def check(r, u):
                return u == ctx.author and str(r.emoji) == "✅" and r.message.id == msg.id

            try:
                await self.client.wait_for("reaction_add", timeout=10.0, check=check)
            except asyncio.TimeoutError:
                await process_msg_reaction_clear(msg)
            else:
                query = users.find_one({
                    "user_id": str(user.id),
                    "shikigami.name": shikigami_name_lower}, {
                    "_id": 0, "shikigami.$": 1
                })

                if query is None:
                    evolve, shards = False, 0
                    if get_rarity_shikigami(shikigami_name_lower) == "SP":
                        evolve, shards = True, 5
                    shikigami_push_user(user.id, shikigami_name_lower, evolve, shards)

                users.update_one({
                    "user_id": str(user.id),
                    "shikigami.name": shikigami_name_lower}, {
                    "$inc": {
                        "shikigami.$.owned": 1,
                        "talisman": - talisman_req,
                        f"{rarity}": 1
                    }
                })
                await perform_add_log("talisman", - talisman_req, user.id)
                embed = discord.Embed(
                    title="Exchange success!", colour=colour, timestamp=get_timestamp(),
                    description=f"You acquired {shikigami_name_lower.title()} for {talisman_req:,d}{e_t}",
                )
                embed.set_footer(icon_url=user.avatar_url, text=f"{user.display_name}")
                await process_msg_edit(msg, None, embed)
                await process_msg_reaction_clear(msg)

            finally:
                self.client.get_command("shikigami_shrine").reset_cooldown(ctx)

        elif talisman < talisman_req:
            embed = discord.Embed(
                title="Insufficient talismans", colour=colour, timestamp=get_timestamp(),
                description=f"You lack {talisman_req - talisman:,d}{e_t}",
            )
            embed.set_footer(icon_url=user.avatar_url, text=f"{user.display_name}")
            await process_msg_submit(ctx.channel, None, embed)

    async def perform_evolution_help(self, ctx):

        embed = discord.Embed(
            title="evolve, evo", colour=colour,
            description="perform evolution of owned shikigami"
        )
        embed.add_field(
            name="Mechanics",
            inline=False,
            value="```"
                  "• SP  :: pre-evolved\n"
                  "• SSR :: requires 1 dupe\n"
                  "• SR  :: requires 10 dupes\n"
                  "• R   :: requires 20 dupes"
                  "```"
        )
        embed.add_field(name="Format", value=f"*`{self.prefix}evolve <shikigami>`*")
        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["evolve", "evo"])
    @commands.guild_only()
    async def perform_evolution(self, ctx, *, shikigami_name=None):

        if shikigami_name is None:
            await self.perform_evolution_help(ctx)

        elif shikigami_name is not None:

            shikigami_name_lower = shikigami_name.lower()

            if shikigami_name_lower not in pool_all:
                await shikigami_post_approximate_results(ctx, shikigami_name_lower)

            else:
                user = ctx.author
                query = users.find_one({
                    "user_id": str(user.id), "shikigami.name": shikigami_name_lower}, {
                    "_id": 0,
                    "shikigami.$": 1
                })

                if query is None:
                    embed = discord.Embed(
                        title="Invalid shikigami", colour=user.colour, timestamp=get_timestamp(),
                        description=f"This shikigami is not in your possession yet",
                    )
                    await process_msg_submit(ctx.channel, None, embed)

                elif query is not None:
                    rarity = query["shikigami"][0]["rarity"]
                    count = query["shikigami"][0]["owned"]
                    evo = query["shikigami"][0]["evolved"]
                    await self.perform_evolution_shikigami(ctx, rarity, evo, user, shikigami_name_lower, count)

    async def perform_evolution_shikigami(self, ctx, rarity, evo, user, shikigami_name, count):

        if rarity == "SP":
            embed = discord.Embed(
                colour=user.colour, title="Invalid shikigami", timestamp=get_timestamp(),
                description=f"this shikigami is already evolved upon summoning"
            )
            await process_msg_submit(ctx.channel, None, embed)

        elif evo is True:
            embed = discord.Embed(
                colour=colour, title="Evolution failed", timestamp=get_timestamp(),
                description=f"Your {shikigami_name.title()} is already evolved",
            )
            embed.set_footer(icon_url=user.avatar_url, text=f"{user.display_name}")
            embed.set_thumbnail(url=get_shikigami_url(shikigami_name, "evo"))
            await process_msg_submit(ctx.channel, None, embed)

        elif evo is False:
            rarity_count = get_evo_requirement(rarity)

            if count >= rarity_count:

                shards = 5
                users.update_one({
                    "user_id": str(user.id),
                    "shikigami.name": shikigami_name}, {
                    "$inc": {
                        "shikigami.$.owned": -(rarity_count - 1),
                        f"{rarity}": -(rarity_count - 1),
                        "shikigami.$.shards": shards
                    },
                    "$set": {
                        "shikigami.$.evolved": True,
                    }
                })

                embed = discord.Embed(
                    colour=user.colour,
                    title="Evolution successful", timestamp=get_timestamp(),
                    description=f"You have evolved your {shikigami_name.title()}\n"
                                f"Also acquired `{shards}` shards of this shikigami",
                )
                embed.set_footer(icon_url=user.avatar_url, text=f"{user.display_name}")
                embed.set_thumbnail(url=get_shikigami_url(shikigami_name, "evo"))
                await process_msg_submit(ctx.channel, None, embed)

            elif count <= 0:
                embed = discord.Embed(
                    title="Invalid shikigami", colour=user.colour, timestamp=get_timestamp(),
                    description=f"This shikigami is not in your possession yet",
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif count <= (get_evo_requirement(rarity) - 1):
                required = rarity_count - count
                noun_duplicate = pluralize('dupe', required)
                embed = discord.Embed(
                    colour=colour, timestamp=get_timestamp(), title="Insufficient shikigamis",
                    description=f"You lack `{required}` more {shikigami_name.title()} {noun_duplicate} to evolve",
                )
                await process_msg_submit(ctx.channel, None, embed)


def setup(client):
    client.add_cog(Shikigami(client))
