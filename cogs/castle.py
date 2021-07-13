"""
Castle Module
"Miketsu, 2021
"""

import urllib.request
from itertools import cycle

from PIL import Image
from discord.ext import commands

from cogs.ext.initialize import *


class Castle(commands.Cog):

    def __init__(self, client):

        self.client = client
        self.prefix = self.client.command_prefix

        self.duel_fields = listings_1["duel_fields"]

        self.primary_emojis = dictionaries["primary_emojis"]
        self.primary_roles = listings_1["primary_roles"]

    def castle_get_emoji_primary_role(self, role):
        return self.primary_emojis[role]

    def create_listings_formatted(self, channel):

        listings, listings_formatted = [], []

        for page in pages.find({"section": str(channel.name)}, {"_id": 0}):
            listings.append([page["#"], page["title"], page["link"]])

        for line in listings:
            listings_formatted.append(f"• `#{lengthen_code_2(int(line[0]))}` | [Link]({line[2]}) | {line[1][:45]}...\n")

        return listings_formatted

    def embed_new_create_contents(self, listings_formatted, page_new):

        lines_max = 8
        page_total = ceil(len(listings_formatted) / lines_max)
        if page_total == 0:
            page_total = 1

        end = page_new * lines_max
        start = end - lines_max
        description_new = "".join(listings_formatted[start:end])

        embed_new = discord.Embed(
            colour=colour, title="Table of Contents",
            description=f"{description_new}", timestamp=get_timestamp()
        )
        embed_new.set_footer(text=f"Page: {page_new} of {page_total}")
        return embed_new

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author == self.client.user:
            return

        elif str(message.channel.id) in [id_unleash, id_showcase]:

            if len(message.attachments) > 0:

                reactions_showcase, reactions_unleash = ["🔥"], ["🧂", "💣"]

                if str(message.channel.id) == id_showcase:
                    await process_msg_reaction_add(message, random.choice(reactions_showcase))
                else:
                    await process_msg_reaction_add(message, random.choice(reactions_unleash))

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):

        if str(payload.user_id) == str(self.client.user.id):
            return

        elif not str(payload.channel_id) in [id_reference, id_restricted, id_unleash, id_showcase, id_coop]:
            return

        elif str(payload.channel_id) in [id_coop]:

            if str(payload.emoji) in ["⬅", "➡"]:

                channel = self.client.get_channel(int(payload.channel_id))
                msg = await channel.fetch_message(int(payload.message_id))
                current_page, page_total = None, None
                user = channel.guild.get_member(int(payload.user_id))

                try:
                    current_page = int(msg.embeds[0].footer.text[6:][0])
                    page_total = int(msg.embeds[0].footer.text[-1:])
                except TypeError:
                    current_page, page_total = 1, 2
                finally:
                    if str(payload.emoji) == "➡":
                        current_page += 1
                    elif str(payload.emoji) == "⬅":
                        current_page -= 1
                    if current_page == 0:
                        current_page = page_total
                    elif current_page > page_total:
                        current_page = 1

                embed = await self.embed_new_create_coop(channel, current_page)
                await process_msg_edit(msg, None, embed)
                await process_msg_reaction_remove(msg, str(payload.emoji), user)

        elif str(payload.channel_id) in [id_reference, id_restricted]:

            if str(payload.emoji) in ["📖", "📚", "📘", "📕", "📗", "📙", "🔖", "📑", "📔"]:

                channel = self.client.get_channel(int(payload.channel_id))
                link = f"https://discordapp.com/channels/{id_guild}/{payload.channel_id}/{payload.message_id}"
                msg = await channel.fetch_message(int(payload.message_id))

                total_books = pages.count_documents({"section": str(channel.name)})
                pages.insert_one({
                    "#": total_books + 1,
                    "link": link,
                    "title": msg.content,
                    "section": str(channel.name),
                    "user_id": str(payload.user_id),
                    "timestamp": get_time()
                })

                record_scroll_channel = self.client.get_channel(int(id_scroll))
                embed = discord.Embed(
                    color=colour, timestamp=get_timestamp(),
                    description=f"A new book has been published at {channel.mention} | [Link]({link})"
                )
                embed.set_footer(text=f"Total books: {total_books + 1}")
                await process_msg_submit(record_scroll_channel, None, embed)

            elif str(payload.emoji) in ["⬅", "➡"]:

                channel = self.client.get_channel(int(payload.channel_id))
                query = guilds.find_one({"server": str(id_guild)}, {"_id": 0, "messages": 1})

                if str(payload.message_id) == query["messages"][str(channel.name)]:

                    listings_formatted = self.create_listings_formatted(channel)
                    msg = await channel.fetch_message(int(payload.message_id))
                    current_page = int(msg.embeds[0].footer.text[6:][0])
                    page_total = int(msg.embeds[0].footer.text[-1:])

                    if str(payload.emoji) == "➡":
                        current_page += 1
                    elif str(payload.emoji) == "⬅":
                        current_page -= 1
                    if current_page == 0:
                        current_page = page_total
                    elif current_page > page_total:
                        current_page = 1
                    await process_msg_edit(msg, None, self.embed_new_create_contents(listings_formatted, current_page))

        else:

            channel = self.client.get_channel(int(payload.channel_id))
            link = f"https://discordapp.com/channels/{id_guild}/{payload.channel_id}/{payload.message_id}"
            msg = await channel.fetch_message(int(payload.message_id))

            if highlights.find_one({"msg_id": str(msg.id)}, {"_id": 0}) is None:

                try:
                    attachment_link = msg.attachments[0].url
                except (TypeError, IndexError):
                    attachment_link = None

                highlights.insert_one({
                    "user_id": str(msg.author.id),
                    "user_name": msg.author.name,
                    "channel": str(channel.id),
                    "msg_id": str(msg.id),
                    "msg_link": link,
                    "content": msg.content,
                    "attachment_link": attachment_link,
                    "stars": 1,
                    "starers": [str(payload.user_id)],
                    "submitted": False,
                    "guild": str(msg.guild.id)
                })

            else:
                starers_listing = highlights.find_one({"msg_id": str(msg.id)}, {"_id": 0, "starers": 1})['starers']

                if not str(payload.user_id) in starers_listing:
                    highlights.update_one({
                        "msg_id": str(msg.id)}, {
                        "$inc": {
                            "stars": 1
                        },
                        "$push": {
                            "starers": str(payload.user_id)
                        }
                    })
                await self.castle_process_star_boards(msg)

    async def castle_process_star_boards(self, msg):

        query = highlights.find_one({"msg_id": str(msg.id)}, {"_id": 0})

        if query["stars"] == 5 and query['submitted'] is False:

            count = highlights.count_documents({"channel": str(msg.channel.id), "submitted": True})
            headlines_channel = self.client.get_channel(int(id_headlines))

            ordinal = lambda n: "%d%s" % (n, "tsnrhtdd"[(n / 10 % 10 != 1) * (n % 10 < 4) * n % 10::4])
            nth = ordinal(count)

            embed = discord.Embed(
                description=f"{query['content']}\n\n[Link here!]({query['msg_link']})",
                timestamp=get_timestamp(),
                color=msg.author.colour
            )
            embed.set_author(name=f"{msg.author.display_name}'s", icon_url=msg.author.avatar_url)

            if query['attachment_link'] is not None:
                embed.set_image(url=query['attachment_link'])

            embed.set_footer(
                text=f"{nth} Entry | #{msg.channel.name}"
            )
            msg1 = await process_msg_submit(headlines_channel, None, embed)

            if str(msg.channel.name) == "showcase":
                emojis_add = ["🔥", "🧂", "👍"]
                for emoji in emojis_add:
                    await process_msg_reaction_add(msg1, emoji)

            else:
                emojis_add = ["🔥", "🧂", "🇫"]
                for emoji in emojis_add:
                    await process_msg_reaction_add(msg1, emoji)

            highlights.update_one({"msg_id": str(msg.id)}, {"$set": {"submitted": True}})

    async def embed_new_create_coop(self, channel, page):

        listings_msg_id = []
        for entry in coops.find({"channel_id": str(channel.id)}, {"_id": 0}):
            try:
                await channel.fetch_message(int(entry["msg_id"]))
            except discord.errors.NotFound:
                coops.delete_one({"msg_id": listings_msg_id[page + 1]})
                continue
            except TypeError:
                listings_msg_id.append(entry['msg_id'])
            else:
                listings_msg_id.append(entry['msg_id'])

        if page <= 1 or page > coops.count_documents({}):

            embed_new = discord.Embed(
                colour=colour, title=f"🔍 Coop Finder", timestamp=get_timestamp(),
                description=f""
                f"Pin your team information & requirements in this channel.\n"
                f"You can edit it to update or delete it to unregister anytime\n\n",
            )
            embed_new.set_footer(text=f"Page: 1 of {coops.count_documents({})}")
            return embed_new

        else:
            profile = coops.find_one({"msg_id": listings_msg_id[page - 1]}, {"_id": 0})
            guild = self.client.get_guild(int(id_guild))
            member = guild.get_member(int(profile['user_id']))

            msg = await channel.fetch_message(int(listings_msg_id[page - 1]))

            embed_new = discord.Embed(
                colour=member.colour, description=f"{msg.content}", timestamp=get_timestamp(),
                title=f"🔍 {member.display_name}'s Coop Profile"
            )
            embed_new.set_footer(text=f"Page: {page} of {coops.count_documents({})}")
            embed_new.set_thumbnail(url=member.avatar_url)
            return embed_new

    async def castle_edit_contents(self, channel, msg_id, p):

        listings_formatted = self.create_listings_formatted(channel)

        msg_new = await process_msg_submit(
            channel, None, self.embed_new_create_contents(listings_formatted, p)
        )

        try:
            msg_old = await channel.fetch_message(int(msg_id))
            await msg_old.delete()
        except discord.errors.NotFound:
            pass

        guilds.update_one({"server": str(id_guild)}, {"$set": {f"messages.{channel.name}": str(msg_new.id)}})

    async def castle_submit_contents(self, channel, msg_id, p):

        listings_formatted = self.create_listings_formatted(channel)

        msg_new = await process_msg_submit(
            channel, None, self.embed_new_create_contents(listings_formatted, p)
        )

        emojis_add = ["⬅", "➡"]
        for emoji in emojis_add:
            await process_msg_reaction_add(msg_new, emoji)

        try:
            msg_old = await channel.fetch_message(int(msg_id))
            await msg_old.delete()
        except discord.errors.NotFound:
            pass

        guilds.update_one({"server": str(id_guild)}, {"$set": {f"messages.{channel.name}": str(msg_new.id)}})

    async def castle_submit_contents_periodic(self):

        for section in [id_restricted, id_reference]:

            channel = self.client.get_channel(int(section))
            channel_msg_id_last = channel.last_message_id

            query = guilds.find_one({"server": str(id_guild)}, {"_id": 0, f"messages.{channel.name}": 1})
            msg_id = query["messages"][str(channel.name)]

            try:
                msg = await channel.fetch_message(int(channel_msg_id_last))
            except discord.errors.NotFound:
                await self.castle_submit_contents(channel, msg_id, 1)
            else:
                if str(msg.id) != msg_id:
                    await self.castle_submit_contents(channel, msg_id, 1)

    async def castle_submit_coops(self):

        channel = self.client.get_channel(int(id_coop))
        query = guilds.find_castle_submit_coopsone({"server": str(id_guild)}, {"_id": 0, f"messages.coop": 1})
        msg_id = query["messages"]["coop"]

        msg = await channel.fetch_message(int(msg_id))
        try:
            current_page = int(msg.embeds[0].footer.text[6:][0])
        except (IndexError, TypeError):
            current_page = 1

        embed = await self.embed_new_create_coop(channel, current_page)
        msg_new = await process_msg_submit(channel, None, embed)

        emojis_add = ["⬅", "➡"]
        for emoji in emojis_add:
            await process_msg_reaction_add(msg_new, emoji)

        try:
            msg_old = await channel.fetch_message(int(msg_id))
            await msg_old.delete()
        except discord.errors.NotFound:
            pass

        guilds.update_one({"server": str(id_guild)}, {"$set": {f"messages.coop": str(msg_new.id)}})

    async def castle_submit_coops_periodic(self):

        channel = self.client.get_channel(int(id_coop))
        channel_msg_id_last = channel.last_message_id

        query = guilds.find_one({"server": str(id_guild)}, {"_id": 0, f"messages.coop": 1})
        msg_id = query["messages"][str(channel.name)]

        try:
            msg = await channel.fetch_message(int(channel_msg_id_last))
        except discord.errors.NotFound:
            await self.castle_submit_contents(channel, msg_id, 1)
        else:
            if str(msg.id) != msg_id:
                await self.castle_submit_contents(channel, msg_id, 1)

    async def castle_retitle_help(self, ctx):

        embed = discord.Embed(
            title="retitle, rt", colour=colour,
            description="retitle a book in the library, adapts based on the channel name"
        )
        embed.add_field(
            name="Formats", inline=False,
            value=f"*`{self.prefix}retitle <number> <new title>`*",
        )
        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["retitle", "rt"])
    @commands.guild_only()
    async def castle_retitle(self, ctx, number=None, *, args=None):

        if number is None or args is None:
            await self.castle_retitle_help(ctx)

        try:
            number = int(number)
        except ValueError:
            pass
        else:
            query = pages.find_one({"section": str(ctx.channel.name), "#": number}, {"_id": 0})
            if query is not None:
                x = pages.update_one({"section": str(ctx.channel.name), "#": number}, {
                    "$set": {
                        "title": args
                    }
                })
                if x.modified_count > 0:
                    await process_msg_reaction_add(ctx.message, "✅")
                    await ctx.message.delete(delay=180)

            else:
                await process_msg_reaction_add(ctx.message, "❌")

    @commands.command(aliases=["contents"])
    @commands.is_owner()
    async def castle_submit_contents_manual(self, ctx):

        await self.castle_submit_contents_periodic()
        await process_msg_reaction_add(ctx.message, "✅")

    @commands.command(aliases=["portraits"])
    @commands.guild_only()
    async def castle_portrait_show_all(self, ctx):

        user = ctx.author
        count = portraits.count_documents({})
        portraits_listings = {}

        def generate_value_floors(f):
            try:
                portraits_listings[str(f)]
            except KeyError:
                return None
            return ", ".join(portraits_listings[str(f)])

        embed = discord.Embed(
            title="Patronus Portraits", color=user.colour, timestamp=get_timestamp(),
            description=f"There are {count} frames hanging in the castle"
        )

        for floor in reversed(range(1, 8)):

            floor_frames = []
            for frame in portraits.find({"floor": floor}, {"_id": 0, "floor": 1, "in_game_name": 1}):
                floor_frames.append(frame["in_game_name"])
                portraits_listings.update({str(floor): floor_frames})

            embed.add_field(name=f"Floor {floor}", value="*{}*".format(generate_value_floors(floor)), inline=False)

        await process_msg_submit(ctx.channel, None, embed)

    async def castle_portraits_wander_help(self, ctx):

        embed = discord.Embed(
            title="wander, w", colour=colour,
            description="usable only at the castle's channels with valid floors\n"
                        "check the channel topics for the floor number\n"
        )
        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["wander", "w"])
    @commands.guild_only()
    async def castle_portraits_wander(self, ctx):

        if not check_if_valid_and_castle:
            await self.castle_portraits_wander_help(ctx)

        else:
            try:
                floor_num = int(ctx.channel.topic[:1])
            except ValueError:
                pass
            else:
                floor_frames = cycle(list(portraits.find({"floor": floor_num}, {"_id": 0})))

                def embed_new_create():
                    preview_frame = next(floor_frames)

                    find_role, in_game_name = preview_frame["role"], preview_frame["in_game_name"]
                    floor, frame_number = preview_frame["floor"], preview_frame["frame"]

                    image_link = preview_frame["image_link"] + "?size=2048"
                    description = preview_frame["description"].replace("\\n", "\n")

                    embed_new = discord.Embed(
                        color=colour, title=f"{self.castle_get_emoji_primary_role(find_role)} {in_game_name}",
                        description=description, timestamp=get_timestamp()
                    )
                    embed_new.set_image(url=image_link)
                    embed_new.set_footer(text=f"Floor {floor} | Frame {frame_number}")
                    return embed_new

                msg = await process_msg_submit(ctx.channel, None, embed_new_create())

                emojis_add = ["➡"]
                for emoji in emojis_add:
                    await process_msg_reaction_add(msg, emoji)

                def check(r, u):
                    return u != self.client.user and r.message.id == msg.id and str(r.emoji) in emojis_add

                while True:
                    try:
                        reaction, user = await self.client.wait_for("reaction_add", timeout=180, check=check)
                    except asyncio.TimeoutError:
                        await process_msg_reaction_clear(msg)
                        break
                    else:
                        if str(reaction.emoji) == emojis_add[0]:
                            await process_msg_edit(msg, None, embed_new_create())

    @commands.command(aliases=["portrait"])
    @commands.guild_only()
    async def castle_portraits_customize(self, ctx, arg1=None, *, args=None):

        user = ctx.author

        if arg1 is None:

            embed = discord.Embed(
                title="portrait, portraits", colour=colour,
                description=f"customize your own guild portrait\n"
                            f"appears in the castle's floors via `{self.prefix}wander`"
            )
            embed.add_field(
                name="Example", inline=False,
                value=f"*`;portraits`*\n"
                      f"*`{self.prefix}portrait <edit/add>`*",
            )
            await process_msg_submit(ctx.channel, None, embed)

        elif arg1.lower() in ["edit", "add"] and args is None:

            embed = discord.Embed(
                title="portrait add, portrait edit", colour=colour,
                description=f"use `add` first before using `edit`\n"
                            f"use square photos for best results"
            )
            embed.add_field(
                name="Format", inline=False,
                value=f"*`{self.prefix}portrait add <name> <floor#1-7> <img_link]/default> <desc.>`*",
            )
            embed.add_field(
                name="Example", inline=False,
                value=f"*`{self.prefix}portrait add xann 6 default Devil`*",
            )
            await process_msg_submit(ctx.channel, None, embed)

        elif arg1.lower() in ["edit", "add"] and args is not None:

            args_split = args.split(" ", 3)

            try:
                floor = int(args_split[1])
            except ValueError:
                embed = discord.Embed(colour=colour, title="Invalid floor#", description="available floors: 1-6 only")
                await process_msg_submit(ctx.channel, None, embed)
            else:
                name = args_split[0]
                image_link = args_split[2]
                caption = args_split[3].replace("\\n", "\n")

                if image_link.lower() == "default":
                    image_link = user.avatar_url

                find_role = ""
                for role in reversed(ctx.guild.get_member(user.id).roles):
                    if role.name in self.primary_roles:
                        find_role = role.name
                        break

                query = portraits.find_one({"frame_id": str(user.id)}, {"_id": 0})

                if query is not None:
                    embed = discord.Embed(
                        colour=colour, description=f"portrait already exists, use `{self.prefix}frame edit`"
                    )
                    await process_msg_submit(ctx.channel, None, embed)

                elif floor not in list(range(1, 7)):
                    embed = discord.Embed(
                        colour=colour, title="Invalid floor#", description=f"available floors: {list(range(1, 7))}"
                    )
                    await process_msg_submit(ctx.channel, None, embed)

                elif arg1.lower() in ["others"]:

                    frame_num = portraits.count_documents({}) + 1
                    link = await self.castle_portraits_customize_process(
                        str(image_link), name, "Head", ctx, caption, floor, frame_num, user
                    )
                    portraits.insert_one({
                        "frame_id": None,
                        "floor": floor,
                        "frame": frame_num,
                        "in_game_name": name,
                        "role": "Head",
                        "image_link": link,
                        "description": caption
                    })

                elif arg1.lower() in ["edit"] and query is not None:

                    frame_num = portraits.count_documents({}) + 1
                    link = await self.castle_portraits_customize_process(
                        str(image_link), name, find_role, ctx, caption, floor, frame_num, user
                    )
                    portraits.update_one({
                        "frame_id": str(ctx.author.id)}, {
                        "$set": {
                            "floor": floor,
                            "frame": frame_num,
                            "in_game_name": name,
                            "role": find_role,
                            "image_link": link,
                            "description": caption

                        }
                    })

    async def castle_portraits_customize_process(self, img_link, name, role, ctx, caption, floor, num, user):

        async with ctx.channel.typing():
            embed = discord.Embed(colour=colour, title="Processing the image..", timestamp=get_timestamp())
            msg1 = await process_msg_submit(ctx.channel, None, embed)
            await asyncio.sleep(2)
            embed = discord.Embed(
                colour=colour, timestamp=get_timestamp(),
                title="Adding a fancy frame based on your highest primary server role.."
            )
            await process_msg_edit(msg1, None, embed)

            opener = urllib.request.build_opener()
            opener.addheaders = [('User-agent', 'Mozilla/5.0')]
            urllib.request.install_opener(opener)
            temp_address = f"temp/{name}_temp.jpg"
            urllib.request.urlretrieve(img_link, temp_address)
            role_frame = f"data/frames/{role.lower()}.png"

            background = Image.open(temp_address)
            width, height = background.size
            new_foreground = Image.open(role_frame).resize((width, height), Image.NEAREST)
            background.paste(new_foreground, (0, 0), new_foreground)

            new_address = f"temp/{name}.png"
            background.save(new_address)

            image_file = discord.File(new_address, filename=f"{name}.png")
            hosting_channel = self.client.get_channel(int(id_hosting))
            msg = await process_msg_submit_file(hosting_channel, image_file)

            await asyncio.sleep(3)

            attachment_link = msg.attachments[0].url

            embed = discord.Embed(
                color=user.colour, timestamp=get_timestamp(),
                title=f"{self.castle_get_emoji_primary_role(role)} {name}", description=caption
            )
            embed.set_image(url=attachment_link)
            embed.set_footer(text=f"Floor {floor} | Frame# {num}")
            await process_msg_submit(ctx.channel, None, embed)
            await asyncio.sleep(2)
            await process_msg_delete(msg1, None)

        return attachment_link

    async def castle_duel_help(self, ctx, invoke, args_v):

        embed = discord.Embed(
            title=f"{invoke}, {invoke[:1]}", colour=colour,
            description="recognizable first arguments for this command"
        )
        embed.add_field(name="Arguments", inline=False, value=f"*{', '.join(args_v)}*", )
        embed.add_field(
            name="Example", inline=False,
            value=f"*`{self.prefix}{invoke} {random.choice(args_v)}`*",
        )
        await process_msg_submit(ctx.channel, None, embed)


def setup(client):
    client.add_cog(Castle(client))
