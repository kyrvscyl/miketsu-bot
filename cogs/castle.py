"""
Castle Module
Miketsu, 2020
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

            count = highlights.count_documents({"channel": str(msg.channel.id)})
            headlines_channel = self.client.get_channel(int(id_headlines))

            ordinal = lambda n: "%d%s" % (n, "tsnrhtdd"[(n / 10 % 10 != 1) * (n % 10 < 4) * n % 10::4])
            nth = ordinal(count)

            embed = discord.Embed(
                description=f"{query['content']}\n\n[Link here!]({query['msg_link']})",
                timestamp=get_timestamp(),
                color=msg.author.colour
            )
            embed.set_author(name=f"{msg.author.display_name}'s reckoning", icon_url=msg.author.avatar_url)

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

    def create_listings_formatted(self, channel):

        listings, listings_formatted = [], []

        for page in pages.find({"section": str(channel.name)}, {"_id": 0}):
            listings.append([page["#"], page["title"], page["link"]])

        for line in listings:
            listings_formatted.append(f"• `#{line[0]}` | [Link]({line[2]}) | {line[1][:45]}...\n")

        return listings_formatted

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

    @commands.command(aliases=["duel", "d"])
    @commands.guild_only()
    async def castle_duel(self, ctx, *args):

        invoke = "duel"
        args_v = ["help", "add", "delete", "update", "show"]

        if not check_if_channel_is_pvp(ctx):
            return

        elif len(args) == 0:
            await self.castle_duel_help(ctx, invoke, args_v)

        elif args[0].lower() in [args_v[0], args_v[0][:1]]:
            await self.castle_duel_help(ctx, invoke, args_v)

        elif args[0].lower() in [args_v[1], args_v[1][:1]]:

            if len(args) <= 1:

                embed = discord.Embed(
                    title=f"{invoke} {args_v[1]}, {invoke[:1]} {args_v[1][:1]}", colour=colour,
                    description="add a new duelist in the database"
                )
                embed.add_field(name="Format", value=f"*`{self.prefix}{invoke} {args_v[1]} <name>`*", inline=False)
                await process_msg_submit(ctx.channel, None, embed)

            elif len(args) == 2:
                await self.castle_duel_profile_member_add(ctx, args)

            else:
                await process_msg_reaction_add(ctx.message, "❌")

        elif args[0].lower() in [args_v[2], args_v[2][:1]]:

            if len(args) <= 1:

                embed = discord.Embed(
                    title=f"{invoke} {args_v[2]}, {invoke[:1]} d", colour=colour,
                    description="removes a duelist in the database"
                )
                embed.add_field(
                    name="Format", inline=False,
                    value=f"*`{self.prefix}{invoke} {args_v[2]} <exact_name>`*"
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif len(args) == 2:
                await self.castle_duel_profile_member_delete(ctx, args)

            else:
                await process_msg_reaction_add(ctx.message, "❌")

        elif args[0].lower() in [args_v[3], args_v[3][:1]]:

            if len(args) <= 1:
                embed = discord.Embed(
                    title=f"{invoke} {args_v[3]}, {invoke[:1]} {args_v[3][:1]}", colour=colour,
                    description="updates a duelist's profile"
                )
                embed.add_field(
                    name="Format", inline=False,
                    value=f"*`{self.prefix}{invoke[:1]} {args_v[3][:1]} <name or id> <field> <value>`*"
                )
                embed.add_field(
                    name="field :: value", inline=False,
                    value=f"• **name** :: <new_name>\n"
                          f"• **notes** :: *<any member notes>*\n"
                          f"• **ban/unban** :: *<shikigami>*\n"
                          f"• **core/uncore** :: *<shikigami>*\n"
                          f"• **lineup** :: *attach a photo upon sending*",
                )
                embed.add_field(
                    name="Example", inline=False,
                    value=f"*`{self.prefix}{invoke[:1]} {args_v[3][:1]} 1 ban enma`*\n"
                          f"*`{self.prefix}{invoke[:1]} {args_v[3][:1]} 100 notes benefits more on first turners`*",
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif len(args) == 2:

                fields_formatted = []
                for field in self.duel_fields:
                    fields_formatted.append(f"`{field}`")

                embed = discord.Embed(
                    colour=colour, title="No field and value provided",
                    description=f"Valid fields: *{', '.join(fields_formatted)}*"
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif args[2].lower() not in self.duel_fields and len(args) >= 3:

                fields_formatted = []
                for field in self.duel_fields:
                    fields_formatted.append(f"`{field}`")

                embed = discord.Embed(
                    colour=colour,
                    title="Invalid field update request",
                    description=f"Valid fields: *{', '.join(fields_formatted)}*"
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif len(args) == 3 and args[2].lower() in ["lineup", "lineups"]:
                await self.castle_duel_profile_update_field(ctx, args)

            elif len(args) == 3 and args[2].lower() in self.duel_fields:
                embed = discord.Embed(
                    colour=colour, title="Invalid field update request",
                    description=f"No value provided for the field {args[2].lower()}"
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif len(args) >= 4 and args[2].lower() in self.duel_fields:
                await self.castle_duel_profile_update_field(ctx, args)

            else:
                await process_msg_reaction_add(ctx.message, "❌")

        elif args[0].lower() in [args_v[4], args_v[4][:1]]:

            if len(args) == 1:
                embed = discord.Embed(
                    title=f"{invoke} {args_v[4]}, {invoke[:1]} {args_v[4][:1]}", colour=colour,
                    description="queries the duelists database"
                )
                embed.add_field(
                    name="Formats", inline=False,
                    value=f"• *`{self.prefix}{invoke[:1]} {args_v[4][:1]} all <opt: [<startswith>]>`*\n"
                          f"• *`{self.prefix}{invoke[:1]} {args_v[4][:1]} <name or id_num>`*",
                )
                embed.add_field(
                    name="Examples", inline=False,
                    value=f"• *`{self.prefix}{invoke[:1]} {args_v[4][:1]} all`*\n"
                          f"• *`{self.prefix}{invoke[:1]} {args_v[4][:1]} all aki`*\n"
                          f"• *`{self.prefix}{invoke[:1]} {args_v[4][:1]} 120`*\n",
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif len(args) == 2 and args[1].lower() == "all":
                await self.castle_duel_profile_show_all(ctx)

            elif len(args) == 3 and args[1].lower() == "all":
                await self.castle_duel_profile_show_startswith(ctx, args)

            elif len(args) == 2 and args[1].lower() != "all":
                await self.castle_duel_profile_show_profile(ctx, args, invoke, args_v)

            else:
                await process_msg_reaction_add(ctx.message, "❌")

        else:
            await process_msg_reaction_add(ctx.message, "❌")

    async def castle_duel_profile_show_profile(self, ctx, args, invoke, args_v):

        try:
            name_id = int(args[1])
        except ValueError:
            query = {"name_lower": args[1].lower()}
            member = duelists.find_one(query, {"_id": 0})
        else:
            query = {"#": name_id}
            member = duelists.find_one(query, {"_id": 0})

        if member is None:
            await self.castle_duel_profile_show_approximate(ctx, args[1])

        else:
            code, name, bans, cores = member['#'], member['name'], member['ban'], member['core']

            embed = discord.Embed(
                color=ctx.author.colour, timestamp=get_timestamp(),
                title=f"{lengthen_code_3(code)} : {name}",
            )
            embed.set_thumbnail(url=ctx.guild.icon_url)
            embed.add_field(name="📸 Stats", inline=False, value=f"Bans: {len(bans)} | Cores: {len(cores)}", )

            if not member["notes"]:
                embed.add_field(name="🗒 Notes", value="No notes yet.")

            elif len(member["notes"]) != 0:
                notes = ""
                for note in member["notes"]:
                    entry = f"[{note['time'].strftime('%d.%b %y')} | {note['member']}]: {note['note']}\n"
                    notes += entry
                embed.add_field(name="🗒 Notes", value=notes)

            if len(member["ban"]) != member["ban_count"] or len(member["core"]) != member["core_count"]:
                link = await self.castle_duel_profile_generate_image(member["ban"], member["core"], ctx)
                duelists.update_one(query, {
                    "$set": {
                        "link": link,
                        "ban_count": len(member["ban"]),
                        "core_count": len(member["core"])
                    }})
            else:
                link = member["link"]

            embed.set_image(url=link)
            msg = await process_msg_submit(ctx.channel, None, embed)

            emojis_add = ["⬅", "➡"]
            for emoji in emojis_add:
                await process_msg_reaction_add(msg, emoji)

            def check(r, u):
                return str(r.emoji) in emojis_add and msg.id == r.message.id and u.id != self.client.user.id

            page = 0
            while True:
                try:
                    await self.client.wait_for("reaction_add", timeout=180, check=check)
                except asyncio.TimeoutError:
                    await process_msg_reaction_clear(msg)
                    break
                else:
                    links = member["lineup"]

                    def embed_new_create_lineup(x):

                        embed_new = discord.Embed(
                            title=f"🖼 Lineup Archives for {name}",
                            color=ctx.author.colour, timestamp=get_timestamp()
                        )
                        if len(links) > 0:
                            embed_new.set_image(url=links[page - 1])
                            embed_new.set_footer(text=f"Page: {page} of {len(links)}")
                        else:
                            embed_new.description = f"this duelist has no lineup records yet\n\n" \
                                                    f"to add, use " \
                                                    f"*`{self.prefix}{invoke} {args_v[3]} <ID/name> lineup`*\n" \
                                                    f"send it with an image uploaded with the message"
                            embed_new.set_footer(text=f"Page: {x} of 1")

                        return embed_new

                    page += 1
                    if page > len(links):
                        page = 1
                    elif page < 1:
                        page = len(links) - 1

                    await process_msg_edit(msg, None, embed_new_create_lineup(page))

    async def castle_duel_profile_show_all(self, ctx):

        listings_formatted = []
        find_query = {}
        project = {"_id": 0, "#": 1, "name": 1}

        for duelist in duelists.find(find_query, project).sort([("#", 1)]):
            number = lengthen_code_3(duelist["#"])
            listings_formatted.append(f"`{number}:` | {duelist['name']}\n")

        noun = pluralize("duelist", len(listings_formatted))
        content = f"There are {len(listings_formatted)} registered {noun}"
        await self.castle_duel_profile_paginate_embeds(ctx, listings_formatted, content)

    async def castle_duel_profile_show_startswith(self, ctx, args):

        listings_formatted = []
        find_query = {"name_lower": {"$regex": f"^{args[2].lower()}"}}
        project = {"_id": 0, "#": 1, "name": 1}

        for duelist in duelists.find(find_query, project).sort([("name_lower", 1)]):
            number = lengthen_code_3(duelist["#"])
            listings_formatted.append(f"`{number}:` | {duelist['name']}\n")

        noun = pluralize("result", len(listings_formatted))
        content = f"I've got {len(listings_formatted)} {noun} for duelists starting with __{args[2].lower()}__"
        await self.castle_duel_profile_paginate_embeds(ctx, listings_formatted, content)

    async def castle_duel_profile_show_approximate(self, ctx, member_name):

        members_search = duelists.find({"name_lower": {"$regex": f"^{member_name[:2].lower()}"}}, {"_id": 0})

        results_approximate = []
        for result in members_search:
            results_approximate.append(f"{result['#']}/{result['name_lower']}")

        embed = discord.Embed(
            colour=colour, title="Invalid query",
            description=f"the ID/name `{member_name}` returned no results"
        )
        embed.add_field(name="Possible matches", value="*{}*".format(", ".join(results_approximate)))
        await process_msg_submit(ctx.channel, None, embed)

    async def castle_duel_profile_update_field(self, ctx, args):
        try:
            name_id = int(args[1])
            find_query = {"#": name_id}
            name = "kyrvscyl"

        except ValueError:
            find_query = {"name_lower": args[1].lower()}
            name_id = 1
            name = args[1].lower()

        if duelists.find_one({"name_lower": name}) is None or duelists.find_one({"#": name_id}) is None:
            await self.castle_duel_profile_show_approximate(ctx, args[1])

        elif args[2].lower() in ["notes", "note"]:
            duelists.update_one(find_query, {
                "$push": {
                    "note": {
                        "member": ctx.author.name,
                        "time": get_time(),
                        "note": " ".join(args[3::])
                    }
                },
                "$set": {
                    "last_update": get_time()
                }
            })
            await process_msg_reaction_add(ctx.message, "✅")

        elif args[2].lower() == "name":
            duelists.update_one(find_query, {"$set": {
                "name": args[3], "name_lower": args[3].lower(), "last_update": get_time()
            }})
            await process_msg_reaction_add(ctx.message, "✅")

        elif args[2].lower() in ["unban", "uncore"] and " ".join(args[3:]).lower() in pool_all:
            duelists.update_one(find_query, {
                "$pull": {
                    args[2].lower()[2:]: " ".join(args[3:]).lower()
                },
                "$set": {
                    "last_update": get_time()
                }
            })
            await process_msg_reaction_add(ctx.message, "✅")

        elif args[2].lower() in ["ban", "core"] and " ".join(args[3:]).lower() in pool_all:
            duelists.update_one(find_query, {
                "$push": {
                    args[2].lower(): " ".join(args[3:]).lower()
                },
                "$set": {
                    "last_update": get_time()
                }
            })
            await process_msg_reaction_add(ctx.message, "✅")

        elif args[2].lower() in ["lineup", "lineups"]:
            image_link = ctx.message.attachments[0].url
            duelists.update_one(find_query, {
                "$push": {
                    "lineup": image_link
                },
                "$set": {
                    "last_update": get_time()
                }
            })
            await process_msg_reaction_add(ctx.message, "✅")

        else:
            await process_msg_reaction_add(ctx.message, "❌")

    async def castle_duel_profile_member_delete(self, ctx, args):

        if duelists.find_one({"name": args[1]}) is not None:
            duelists.delete_one({"name": args[1]})
            await process_msg_reaction_add(ctx.message, "✅")

            name_id = 1
            for member in duelists.find({}, {"_id": 0, "name": 1}):
                duelists.update_one({"name": member["name"]}, {"$set": {"#": name_id}})
                name_id += 1

        else:
            await self.castle_duel_profile_show_approximate(ctx, args[1])

    async def castle_duel_profile_member_add(self, ctx, args):

        if duelists.find_one({"name_lower": args[1].lower()}) is None:
            duelists.insert_one({
                "#": duelists.count_documents({}) + 1,
                "name": args[1],
                "name_lower": args[1].lower(),
                "ban": [],
                "ban_count": -1,
                "core": [],
                "core_count": -1,
                "lineup": [],
                "notes": [],
                "link": None,
                "last_update": get_time()
            })
            await process_msg_reaction_add(ctx.message, "✅")

        else:
            embed = discord.Embed(
                title="Invalid duelist", colour=colour,
                description="that name already exists in the database"
            )
            await process_msg_submit(ctx.channel, None, embed)

    async def castle_duel_profile_generate_image(self, bans, cores, ctx):

        bans_address = []
        for name in bans:
            bans_address.append(f"data/shikigamis/{name}_pre.jpg")

        cores_address = []
        for name in cores:
            cores_address.append(f"data/shikigamis/{name}_pre.jpg")

        x, y, max_cols = 4, 0, 7
        font = font_create(30)

        def get_coordinates(c):
            a = (c * 90 - (ceil(c / max_cols) - 1) * max_cols * 90) - 90
            b = (ceil(c / max_cols) * 90) - 90
            return a, b

        def generate_shikigami_list(listings, text, color_fill):

            im = Image.new('RGBA', (90 * max_cols, 20 + (ceil(len(listings) / max_cols) * 90)), (255, 0, 0, 0))
            outline = ImageDraw.Draw(im)
            outline.text((x, y), text, font=font, fill=color_fill)
            im_shikigamis = list(map(Image.open, listings))
            im_shikigamis_plain = Image.new("RGBA", (max_cols * 90, max_cols * 90))

            for i, j in enumerate(im_shikigamis):
                im_shikigamis_plain.paste(im_shikigamis[i], (get_coordinates(i + 1)))

            im.paste(im_shikigamis_plain, (0, 25))
            return im

        font_color = tuple(int((str(ctx.author.colour)).lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))

        im_bans = generate_shikigami_list(bans_address, "Recommended Bans", font_color)
        im_cores = generate_shikigami_list(cores_address, "Core Shikigamis", font_color)

        widths, heights = zip(*(i.size for i in [im_bans, im_cores]))
        max_height, max_width = max(heights), max(widths)

        temp_address = f"temp/{ctx.message.id}.png"
        combined_img = Image.new('RGBA', (max_width, (max_height * 2) + 7), (255, 0, 0, 0))
        combined_img.paste(im_bans, (0, 0))
        combined_img.paste(im_cores, (0, int(max_height) + 7))
        combined_img.save(temp_address)

        image_file = discord.File(temp_address, filename=f"{ctx.message.id}.png")
        hosting_channel = self.client.get_channel(int(id_hosting))
        msg = await process_msg_submit_file(hosting_channel, image_file)
        attachment_link = msg.attachments[0].url

        return attachment_link

    async def castle_duel_profile_paginate_embeds(self, ctx, listings_formatted, content):

        page, max_lines = 1, 20
        page_total = ceil(len(listings_formatted) / max_lines)
        if page_total == 0:
            page_total = 1

        def embed_new_create(page_new):
            end = page_new * max_lines
            start = end - max_lines
            description_new = "".join(listings_formatted[start:end])

            embed_new = discord.Embed(
                color=ctx.author.colour, timestamp=get_timestamp(),
                title="🎌 Secret Duelling Book", description=f"{description_new}",
            )
            embed_new.set_footer(text=f"Page: {page_new} of {page_total}")
            embed_new.set_thumbnail(url=ctx.guild.icon_url)
            return embed_new

        msg = await process_msg_submit(ctx.channel, content, embed_new_create(page))

        emojis_add = ["⬅", "➡"]
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
    client.add_cog(Castle(client))
