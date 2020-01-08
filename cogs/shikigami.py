"""
Shikigami Module
Miketsu, 2020
"""
import asyncio
from math import ceil

from PIL import Image, ImageDraw
from discord.ext import commands

from cogs.ext.initialize import *


class Shikigami(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.prefix = self.client.command_prefix

    @commands.command(aliases=["collection", "col", "collections"])
    @commands.guild_only()
    async def shikigami_image_show_collected(self, ctx, arg1, *, member: discord.Member = None):

        rarity = str(arg1.upper())

        if rarity not in rarities:
            raise commands.MissingRequiredArgument(ctx.author)

        elif member is None:
            await self.shikigami_show_post_collected(ctx.author, rarity, ctx)

        else:
            await self.shikigami_show_post_collected(member, rarity, ctx)

    async def shikigami_show_post_collected(self, member, rarity, ctx):

        user_shikigamis_with_evo = []
        user_shikigamis = []
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
            user_shikigamis_with_evo.append((entry["shikigami"]["name"], entry["shikigami"]["evolved"]))
            user_shikigamis.append(entry["shikigami"]["name"])

        pool_rarity_select = []
        for entry in shikigamis.find({"rarity": rarity}, {"_id": 0, "name": 1}):
            pool_rarity_select.append(entry["name"])

        uncollected_list = list(set(pool_rarity_select) - set(user_shikigamis))

        link = await self.shikigami_show_post_collected_generate(
            user_shikigamis_with_evo, uncollected_list, pool_rarity_select, rarity, member
        )

        embed = discord.Embed(
            title=f"{get_rarity_emoji(rarity)} Collection",
            color=member.colour,
            timestamp=get_timestamp()
        )
        embed.set_image(url=link)
        embed.set_footer(icon_url=member.avatar_url, text=f"{member.display_name}")
        await process_msg_submit(ctx.channel, None, embed)

    async def shikigami_show_post_collected_generate(self, user_shikis, user_unc, pool_rarity_select, rarity, member):

        images = []
        for entry in user_shikis:
            address = f"data/shikigamis/{entry[0]}_pre.jpg"
            if entry[1] is True:
                address = f"data/shikigamis/{entry[0]}_evo.jpg"
            images.append(Image.open(address))

        for entry in user_unc:
            address = f"data/shikigamis/{entry}_pre.jpg"
            images.append(Image.open(address).convert("LA"))

        w = get_variables(rarity)[0]
        col = get_variables(rarity)[1]

        def get_image_variables(x):
            total_shikis = len(x)
            h = ceil(total_shikis / col) * 90
            return w, h

        width, height = get_image_variables(pool_rarity_select)
        new_im = Image.new("RGBA", (width, height))

        def get_coordinates(c):
            a = (c * 90 - (ceil(c / col) - 1) * w) - 90
            b = (ceil(c / col) * 90) - 90
            return a, b

        for index, item in enumerate(images):
            new_im.paste(images[index], (get_coordinates(index + 1)))

        address = f"temp/{member.id}.png"
        new_im.save(address)
        new_photo = discord.File(address, filename=f"{member.id}.png")
        hosting_channel = self.client.get_channel(int(id_hosting))
        msg = await hosting_channel.send(file=new_photo)
        attachment_link = msg.attachments[0].url
        return attachment_link

    @commands.command(aliases=["shikilist", "sl"])
    @commands.guild_only()
    async def shikigami_list_show_collected(self, ctx, arg1, *, member: discord.Member = None):

        rarity = str(arg1.upper())

        if rarity not in rarities:
            raise commands.MissingRequiredArgument(ctx.author)

        elif member is None:
            await self.shikigami_list_post_collected(ctx.author, rarity, ctx)

        else:
            await self.shikigami_list_post_collected(member, rarity, ctx)

    async def shikigami_list_post_collected(self, member, rarity, ctx):

        user_shikigamis = []
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
            user_shikigamis.append((
                entry["shikigami"]["name"],
                entry["shikigami"]["owned"],
                entry["shikigami"]["shards"]
            ))

        user_shikigamis_sorted = sorted(user_shikigamis, key=lambda x: x[1], reverse=True)

        formatted_list = []
        for shiki in user_shikigamis_sorted:
            formatted_list.append(f"• {shiki[0].title()} | `x{shiki[1]} [{shiki[2]} shards]`\n")

        await self.shikigami_list_paginate(member, formatted_list, rarity, ctx, "Shikigamis")

    async def shikigami_list_paginate(self, member, formatted_list, rarity, ctx, title):

        page = 1
        max_lines = 10
        page_total = ceil(len(formatted_list) / max_lines)
        if page_total == 0:
            page_total = 1

        def embed_new_create(page_new):
            end = page_new * max_lines
            start = end - max_lines
            embed_new = discord.Embed(color=member.colour, timestamp=get_timestamp())
            embed_new.title = f"{get_rarity_emoji(rarity.upper())} {title}"
            embed_new.description = "".join(formatted_list[start:end])
            embed_new.set_footer(
                text=f"Page: {page_new} of {page_total}",
                icon_url=member.avatar_url
            )
            return embed_new

        msg = await ctx.channel.send(embed=embed_new_create(1))
        emoji_arrows = ["⬅", "➡"]
        for emoji in emoji_arrows:
            await process_msg_reaction_add(msg, emoji)

        def check(r, m):
            return m != self.client.user and r.message.id == msg.id

        while True:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=60, check=check)
            except asyncio.TimeoutError:
                await process_msg_reaction_clear(msg)
                break
            else:
                if str(reaction.emoji) == emoji_arrows[1]:
                    page += 1
                elif str(reaction.emoji) == emoji_arrows[0]:
                    page -= 1
                if page == 0:
                    page = page_total
                elif page > page_total:
                    page = 1
                await process_msg_edit(msg, None, embed_new_create(page))

    @commands.command(aliases=["shards"])
    @commands.guild_only()
    async def shikigami_show_post_shards(self, ctx, arg1, *, member: discord.Member = None):

        rarity = str(arg1.upper())

        if rarity not in rarities:
            raise commands.MissingRequiredArgument(ctx.author)

        elif member is None:
            await self.shikigami_show_post_shards_user(ctx.author, rarity, ctx)

        else:
            await self.shikigami_show_post_shards_user(member, rarity, ctx)

    async def shikigami_show_post_shards_user(self, member, rarity, ctx):

        user_shikigamis_with_evo = []
        user_shikigamis = []
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
            user_shikigamis_with_evo.append(
                (entry["shikigami"]["name"], entry["shikigami"]["evolved"], entry["shikigami"]["shards"])
            )
            user_shikigamis.append(entry["shikigami"]["name"])

        pool_rarity_select = []
        for entry in shikigamis.find({"rarity": rarity}, {"_id": 0, "name": 1}):
            pool_rarity_select.append(entry["name"])

        uncollected_list = list(set(pool_rarity_select) - set(user_shikigamis))

        link = await self.shikigami_show_post_shards_generate(
            user_shikigamis_with_evo, uncollected_list, pool_rarity_select, rarity, member
        )

        embed = discord.Embed(
            title=f"{get_rarity_emoji(rarity)} Collection - Shards",
            color=member.colour,
            timestamp=get_timestamp()
        )
        embed.set_image(url=link)
        embed.set_footer(icon_url=member.avatar_url, text=f"{member.display_name}")
        await process_msg_submit(ctx.channel, None, embed)

    async def shikigami_show_post_shards_generate(self, user_shikis, user_unc, pool_rarity_select, rarity, member):

        images = []

        x, y = 1, 60

        def generate_shikigami_with_shard(shikigami_thumbnail_select, shards_count):

            outline = ImageDraw.Draw(shikigami_thumbnail_select)
            outline.text((x - 1, y - 1), str(shards_count), font=font, fill="black")
            outline.text((x + 1, y - 1), str(shards_count), font=font, fill="black")
            outline.text((x - 1, y + 1), str(shards_count), font=font, fill="black")
            outline.text((x + 1, y + 1), str(shards_count), font=font, fill="black")
            outline.text((x, y), str(shards_count), font=font)

            return shikigami_thumbnail_select

        def get_shard_uncollected(user_id, rarity_selected, shikigami_name):
            try:
                for result in users.aggregate([
                    {
                        '$match': {
                            'user_id': str(user_id)
                        }
                    }, {
                        '$unwind': {
                            'path': '$shikigami'
                        }
                    }, {
                        '$match': {
                            'shikigami.rarity': rarity_selected
                        }
                    }, {
                        '$project': {
                            '_id': 0,
                            'shikigami.name': 1,
                            'shikigami.shards': 1,
                        }
                    }, {
                        '$match': {
                            'shikigami.name': shikigami_name
                        }
                    }
                ]):
                    return result["shikigami"]["shards"]

            except KeyError:
                return 0

        for entry in user_shikis:
            address = f"data/shikigamis/{entry[0]}_pre.jpg"
            if entry[1] is True:
                address = f"data/shikigamis/{entry[0]}_evo.jpg"

            shikigami_thumbnail = Image.open(address)
            shikigami_image_final = generate_shikigami_with_shard(shikigami_thumbnail, entry[2])
            images.append(shikigami_image_final)

        for entry in user_unc:
            address = f"data/shikigamis/{entry}_pre.jpg"
            count = get_shard_uncollected(member.id, rarity, entry)

            if count is None:
                count = 0

            shikigami_thumbnail = Image.open(address).convert("LA")
            shikigami_image_final = generate_shikigami_with_shard(shikigami_thumbnail, count)
            images.append(shikigami_image_final)

        w = get_variables(rarity)[0]
        col = get_variables(rarity)[1]

        def get_image_variables(a):
            total_shikis = len(a)
            h = ceil(total_shikis / col) * 90
            return w, h

        width, height = get_image_variables(pool_rarity_select)
        new_im = Image.new("RGBA", (width, height))

        def get_coordinates(c):
            a = (c * 90 - (ceil(c / col) - 1) * w) - 90
            b = (ceil(c / col) * 90) - 90
            return a, b

        for index, item in enumerate(images):
            new_im.paste(images[index], (get_coordinates(index + 1)))

        address = f"temp/{member.id}.png"
        new_im.save(address)
        new_photo = discord.File(address, filename=f"{member.id}.png")
        hosting_channel = self.client.get_channel(int(id_hosting))
        msg = await hosting_channel.send(file=new_photo)
        attachment_link = msg.attachments[0].url
        return attachment_link

    @commands.command(aliases=["shiki", "shikigami"])
    @commands.guild_only()
    async def shikigami_show_post_shiki(self, ctx, *, arg1):

        shiki = arg1.lower()
        user = ctx.author
        user_shikigami = users.find_one({
            "user_id": str(user.id), "shikigami.name": shiki}, {
            "_id": 0, "shikigami.$": 1
        })

        if shiki not in pool_all_mystery and shiki not in pool_all_broken:
            await shikigami_post_approximate_results(ctx, shiki)

        elif user_shikigami is None:
            embed = discord.Embed(
                colour=colour,
                title="Invalid selection",
                description=f"this shikigami is not in your possession"
            )
            await process_msg_submit(ctx.channel, None, embed)

        else:
            await self.shikigami_show_post_shiki_user(user, user_shikigami, shiki, ctx)

    async def shikigami_show_post_shiki_user(self, user, user_shikigami, shiki, ctx):

        shiki_profile = user_shikigami["shikigami"]
        evolve = "pre"
        if shiki_profile[0]["evolved"] is True:
            evolve = "evo"

        thumbnail = get_thumbnail_shikigami(shiki, evolve)

        embed = discord.Embed(
            colour=user.colour,
            description=f"```"
                        f"Level    ::   {shiki_profile[0]['level']}\n"
                        f"Exp      ::   {shiki_profile[0]['exp']}/{shiki_profile[0]['level_exp_next']}\n"
                        f"Grade    ::   {shiki_profile[0]['grade']}\n"
                        f"Owned    ::   {shiki_profile[0]['owned']}\n"
                        f"Shards   ::   {shiki_profile[0]['shards']}\n"
                        f"```",
            timestamp=get_timestamp()
        )
        embed.set_thumbnail(url=thumbnail)
        embed.set_author(
            name=f"{user.display_name}'s {shiki.title()}",
            icon_url=user.avatar_url
        )
        embed.set_footer(text=f"Rarity: {shiki_profile[0]['rarity']}")
        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["shikis", "shikigamis"])
    @commands.guild_only()
    async def shikigami_show_post_shikis(self, ctx, arg1, *, member: discord.Member = None):

        rarity = str(arg1.upper())

        if rarity not in rarities:
            embed = discord.Embed(
                title="Invalid rarity", color=colour,
                description=f"you provided an invalid shikigami rarity"
            )
            embed.add_field(
                name="Rarities",
                value="SP, SSR, SR, R, N, SSN"
            )
            await process_msg_submit(ctx.channel, None, embed)

        elif member is None:
            await self.shikigami_show_post_shikis_user(ctx.author, rarity, ctx)

        else:
            await self.shikigami_show_post_shikis_user(member, rarity, ctx)

    async def shikigami_show_post_shikis_user(self, member, rarity, ctx):

        user_shikigamis_with_evo = []
        user_shikigamis = []
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
            user_shikigamis_with_evo.append(
                (entry["shikigami"]["name"], entry["shikigami"]["evolved"], entry["shikigami"]["owned"])
            )
            user_shikigamis.append(entry["shikigami"]["name"])

        pool_rarity_select = []
        for entry in shikigamis.find({"rarity": rarity}, {"_id": 0, "name": 1}):
            pool_rarity_select.append(entry["name"])

        uncollected_list = list(set(pool_rarity_select) - set(user_shikigamis))

        link = await self.shikigami_show_post_shikis_generate(
            user_shikigamis_with_evo, uncollected_list, pool_rarity_select, rarity, member
        )

        embed = discord.Embed(
            title=f"{get_rarity_emoji(rarity)} Collection - Count",
            color=member.colour,
            timestamp=get_timestamp()
        )
        embed.set_image(url=link)
        embed.set_footer(icon_url=member.avatar_url, text=f"{member.display_name}")
        await process_msg_submit(ctx.channel, None, embed)

    async def shikigami_show_post_shikis_generate(self, user_shikis, user_unc, pool_rarity_select, rarity, member):

        images = []

        x, y = 1, 60

        def generate_shikigami_with_count(shikigami_thumbnail_select, owned_count):

            outline = ImageDraw.Draw(shikigami_thumbnail_select)
            outline.text((x - 1, y - 1), str(owned_count), font=font, fill="black")
            outline.text((x + 1, y - 1), str(owned_count), font=font, fill="black")
            outline.text((x - 1, y + 1), str(owned_count), font=font, fill="black")
            outline.text((x + 1, y + 1), str(owned_count), font=font, fill="black")
            outline.text((x, y), str(owned_count), font=font)

            return shikigami_thumbnail_select

        for entry in user_shikis:
            address = f"data/shikigamis/{entry[0]}_pre.jpg"
            if entry[1] is True:
                address = f"data/shikigamis/{entry[0]}_evo.jpg"

            shikigami_thumbnail = Image.open(address)
            shikigami_image_final = generate_shikigami_with_count(shikigami_thumbnail, entry[2])
            images.append(shikigami_image_final)

        for entry in user_unc:
            address = f"data/shikigamis/{entry}_pre.jpg"
            shikigami_thumbnail = Image.open(address).convert("LA")
            shikigami_image_final = generate_shikigami_with_count(shikigami_thumbnail, 0)
            images.append(shikigami_image_final)

        w = get_variables(rarity)[0]
        col = get_variables(rarity)[1]

        def get_image_variables(a):
            total_shikis = len(a)
            h = ceil(total_shikis / col) * 90
            return w, h

        width, height = get_image_variables(pool_rarity_select)
        new_im = Image.new("RGBA", (width, height))

        def get_coordinates(c):
            a = (c * 90 - (ceil(c / col) - 1) * w) - 90
            b = (ceil(c / col) * 90) - 90
            return a, b

        for index, item in enumerate(images):
            new_im.paste(images[index], (get_coordinates(index + 1)))

        address = f"temp/{member.id}.png"
        new_im.save(address)
        new_photo = discord.File(address, filename=f"{member.id}.png")
        hosting_channel = self.client.get_channel(int(id_hosting))
        msg = await hosting_channel.send(file=new_photo)
        attachment_link = msg.attachments[0].url
        return attachment_link

    @commands.command(aliases=["set", "display"])
    @commands.guild_only()
    async def profile_change_shikigami(self, ctx, *, select):

        user = ctx.author
        select_formatted = select.lower()

        if select_formatted is None:
            users.update_one({"user_id": str(user.id)}, {"$set": {"display": select_formatted}})
            await process_msg_reaction_add(ctx.message, "✅")

        elif select_formatted not in pool_all_mystery:
            await shikigami_post_approximate_results(ctx, select_formatted)

        elif select_formatted in pool_all_mystery:
            count = users.count_documents({"user_id": str(user.id), "shikigami.name": select_formatted})

            if count != 1:
                embed = discord.Embed(
                    colour=colour,
                    title="Invalid selection",
                    description=f"this shikigami is not in your possession"
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif count == 1:
                users.update_one({"user_id": str(user.id)}, {"$set": {"display": select_formatted}})
                await process_msg_reaction_add(ctx.message, "✅")

    @commands.command(aliases=["shrine", "shr"])
    @commands.guild_only()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def shikigami_shrine(self, ctx, arg1="", *, args=""):

        user = ctx.author
        shiki = args.lower()

        def get_talisman_required(x):
            dictionary = {"SSR": 350000, "SR": 150000, "R": 50000}
            return dictionary[x]

        if arg1.lower() not in ["sacrifice", "exchange", "s", "exc"]:
            raise commands.MissingRequiredArgument(ctx.author)

        elif arg1.lower() in ["sacrifice", "s"] and len(args) == 0:
            embed = discord.Embed(
                title="shrine sacrifice, shr s", colour=colour,
                description="sacrifice your shikigamis to the shrine in exchange for talismans"
            )
            embed.add_field(
                name="Rarity :: Talisman",
                value="```"
                      "SP     ::  50,000\n"
                      "SSR    ::  25,000\n"
                      "SR     ::   1,000\n"
                      "R      ::      75\n"
                      "```",
                inline=False
            )
            embed.add_field(
                name="Format",
                value=f"*`{self.prefix}shrine s <shikigami>`*"
            )
            await process_msg_submit(ctx.channel, None, embed)

        elif arg1.lower() in ["exchange", "exc"] and len(args) == 0:
            embed = discord.Embed(
                title="shrine exchange, shrine exc", colour=colour,
                description="exchange your talismans for exclusive shrine only shikigamis"
            )
            embed.add_field(
                name="Shikigami :: Talisman",
                value="```"
                      "Juzu          ::     50,000\n"
                      "Usagi         ::     50,000\n"
                      "Tenjo Kudari  ::     50,000\n"
                      "Mannendake    ::    150,000\n"
                      "Jinmenju      ::    150,000\n"
                      "Kainin        ::    150,000\n"
                      "Ryomen        ::    350,000"
                      "```",
                inline=False
            )
            embed.add_field(
                name="Formats",
                value=f"*`{self.prefix}shrine exc <shikigami>`*"
            )
            await process_msg_submit(ctx.channel, None, embed)

        elif arg1.lower() in ["sacrifice", "s"] and shiki not in pool_all_mystery:
            await shikigami_post_approximate_results(ctx, shiki)

        elif arg1.lower() in ["exchange", "exc"] and shiki not in pool_shrine:
            await shikigami_post_approximate_results(ctx, shiki)

        elif arg1.lower() in ["sacrifice", "s"] and shiki in pool_all_mystery:

            try:
                request = users.find_one({
                    "user_id": str(user.id), "shikigami.name": shiki}, {
                    "_id": 0, "shikigami.$.name": 1
                })
                count_shikigami = request["shikigami"][0]["owned"]
                rarity = request["shikigami"][0]["rarity"]
                talismans = get_talisman_acquire(rarity)

            except TypeError:
                embed = discord.Embed(
                    colour=user.colour,
                    title=f"Invalid shikigami",
                    description=f"no shikigami {shiki.title()} in your possession yet"
                )
                await process_msg_submit(ctx.channel, None, embed)
                return

            def check(m):
                try:
                    int(m.content)
                    return m.author == ctx.author and m.channel == ctx.channel
                except TypeError:
                    return
                except ValueError:
                    return

            try:
                embed = discord.Embed(
                    colour=user.colour,
                    title=f"Specify amount",
                    description=f"You currently have {count_shikigami:,d} {shiki.title()}",
                    timestamp=get_timestamp()
                )
                embed.set_thumbnail(url=get_thumbnail_shikigami(shiki, "evo"))
                embed.set_footer(text=f"{user.display_name}", icon_url=user.avatar_url)
                msg = await process_msg_submit(ctx.channel, None, embed)
                answer = await self.client.wait_for("message", timeout=15, check=check)

            except asyncio.TimeoutError:
                embed = discord.Embed(
                    title="Invalid amount", colour=user.colour,
                    description=f"provide a valid integer",
                )
                embed.set_thumbnail(url=get_thumbnail_shikigami(shiki, "evo"))
                embed.set_footer(text=f"{user.display_name}", icon_url=user.avatar_url)
                await process_msg_submit(ctx.channel, None, embed)

            else:
                request_shrine = int(answer.content)
                if count_shikigami >= request_shrine:
                    final_talismans = talismans * request_shrine
                    users.update_one({
                        "user_id": str(user.id),
                        "shikigami.name": shiki}, {
                        "$inc": {
                            "shikigami.$.owned": - request_shrine,
                            "talisman": final_talismans,
                            f"{rarity}": - request_shrine
                        }
                    })
                    await perform_add_log("talisman", final_talismans, user.id)
                    embed = discord.Embed(
                        title="Shrine successful", colour=user.colour,
                        description=f"You shrined {shiki.title()} for {final_talismans:,d}{e_t}",
                        timestamp=get_timestamp()
                    )
                    embed.set_thumbnail(url=get_thumbnail_shikigami(shiki, "evo"))
                    embed.set_footer(text=f"{user.display_name}", icon_url=user.avatar_url)
                    await msg.edit(embed=embed)

                else:
                    embed = discord.Embed(
                        title="Insufficient shikigamis", colour=user.colour,
                        description=f"You lack that amount of shikigami {shiki.title()}",
                        timestamp=get_timestamp()
                    )
                    embed.set_thumbnail(url=get_thumbnail_shikigami(shiki, "evo"))
                    embed.set_footer(text=f"{user.display_name}", icon_url=user.avatar_url)
                    await process_msg_submit(ctx.channel, None, embed)

        elif arg1.lower() in ["exchange", "exc"] and shiki in pool_shrine:

            rarity = shikigamis.find_one({"name": shiki}, {"_id": 0, "rarity": 1})["rarity"]
            talisman = users.find_one({"user_id": str(user.id)}, {"_id": 0, "talisman": 1})["talisman"]
            required_talisman = get_talisman_required(rarity)

            if talisman >= required_talisman:
                embed = discord.Embed(
                    title="Exchange confirmation", colour=colour,
                    description=f"confirm exchange of {required_talisman:,d}{e_t} for a {shiki.title()}",
                    timestamp=get_timestamp()
                )
                embed.set_footer(icon_url=user.avatar_url, text=f"{user.display_name}")
                confirm_ = await process_msg_submit(ctx.channel, None, embed)
                await confirm_.add_reaction("✅")

                def check(r, u):
                    return u == ctx.author and str(r.emoji) == "✅"

                try:
                    await self.client.wait_for("reaction_add", timeout=10.0, check=check)

                except asyncio.TimeoutError:
                    embed = discord.Embed(
                        title="Timeout!", colour=colour,
                        description=f"no confirmation received for {e_t} exchange",
                    )
                    embed.set_footer(icon_url=user.avatar_url, text=f"{user.display_name}")
                    await confirm_.edit(embed=embed)
                    await confirm_.clear_reactions()

                else:
                    query = users.find_one({
                        "user_id": str(user.id),
                        "shikigami.name": shiki}, {
                        "_id": 0, "shikigami.$": 1
                    })

                    if query is None:
                        evolve, shards = False, 0
                        if get_rarity_shikigami(shiki) == "SP":
                            evolve, shards = True, 5
                        shikigami_push_user(user.id, shiki, evolve, shards)

                    users.update_one({
                        "user_id": str(user.id),
                        "shikigami.name": shiki}, {
                        "$inc": {
                            "shikigami.$.owned": 1,
                            "talisman": - required_talisman,
                            f"{rarity}": 1
                        }
                    })
                    await perform_add_log("talisman", - required_talisman, user.id)
                    embed = discord.Embed(
                        title="Exchange success!", colour=colour,
                        description=f"You acquired {shiki.title()} for {required_talisman:,d}{e_t}",
                        timestamp=get_timestamp()
                    )
                    embed.set_footer(icon_url=user.avatar_url, text=f"{user.display_name}")
                    await confirm_.edit(embed=embed)

            elif talisman < required_talisman:
                embed = discord.Embed(
                    title="Insufficient talismans", colour=colour,
                    description=f"You lack {required_talisman - talisman:,d}{e_t}",
                )
                embed.set_footer(icon_url=user.avatar_url, text=f"{user.display_name}")
                await process_msg_submit(ctx.channel, None, embed)

        self.client.get_command("shikigami_shrine").reset_cooldown(ctx)

    @commands.command(aliases=["evolve", "evo"])
    async def perform_evolution(self, ctx, *args):

        user = ctx.author
        query = (" ".join(args)).lower()
        profile_my_shikigami = users.find_one({
            "user_id": str(user.id)}, {
            "_id": 0,
            "shikigami": {
                "$elemMatch": {
                    "name": query
                }}
        })

        if len(query) < 2:
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

        elif shikigamis.find_one({"name": query}, {"_id": 0}) is None:
            await shikigami_post_approximate_results(ctx, query)

        elif profile_my_shikigami == {}:
            embed = discord.Embed(
                title="Invalid selection", colour=colour,
                description=f"this shikigami is not in your possession yet",
            )
            await process_msg_submit(ctx.channel, None, embed)

        elif profile_my_shikigami != {}:
            rarity = profile_my_shikigami["shikigami"][0]["rarity"]
            count = profile_my_shikigami["shikigami"][0]["owned"]
            evo = profile_my_shikigami["shikigami"][0]["evolved"]
            await self.perform_evolution_shikigami(ctx, rarity, evo, user, query, count)

    async def perform_evolution_shikigami(self, ctx, rarity, evo, user, query, count):
        if rarity == "SP":
            embed = discord.Embed(
                colour=colour,
                title="Invalid shikigami",
                description=f"this shikigami is already evolved upon summoning"
            )
            await process_msg_submit(ctx.channel, None, embed)

        elif evo is True:
            embed = discord.Embed(
                colour=colour,
                title="Evolution failed",
                description=f"Your {query.title()} is already evolved",
            )
            embed.set_footer(icon_url=user.avatar_url, text=f"{user.display_name}")
            embed.set_thumbnail(url=get_thumbnail_shikigami(query, "evo"))
            await process_msg_submit(ctx.channel, None, embed)

        elif evo is False:
            rarity_count = get_evo_requirement(rarity)

            if count >= rarity_count:

                users.update_one({
                    "user_id": str(user.id),
                    "shikigami.name": query}, {
                    "$inc": {
                        "shikigami.$.owned": -(rarity_count - 1),
                        f"{rarity}": -(rarity_count - 1)
                    },
                    "$set": {
                        "shikigami.$.evolved": True,
                        "shikigami.$.shards": 5
                    }
                })

                shikigami_profile = shikigamis.find_one({"name": query}, {"_id": 0, "thumbnail": 1})
                image_url = shikigami_profile["thumbnail"]["evo"]

                embed = discord.Embed(
                    colour=user.colour,
                    title="Evolution successful",
                    description=f"You have evolved your {query.title()}\n"
                                f"Also acquired 5 shards of this shikigami",
                    timestamp=get_timestamp()
                )
                embed.set_footer(icon_url=user.avatar_url, text=f"{user.display_name}")
                embed.set_thumbnail(url=image_url)
                await process_msg_submit(ctx.channel, None, embed)

            elif count == 0:
                embed = discord.Embed(
                    colour=colour,
                    title="Invalid selection",
                    description=f"this shikigami is not in your possession"
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif count <= (get_evo_requirement(rarity) - 1):
                required = rarity_count - count
                noun_duplicate = pluralize('dupe', required)
                embed = discord.Embed(
                    colour=colour,
                    title="Insufficient shikigamis",
                    description=f"You lack {required} more {query.title()} {noun_duplicate} to evolve",
                )
                await process_msg_submit(ctx.channel, None, embed)


def setup(client):
    client.add_cog(Shikigami(client))
