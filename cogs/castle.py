"""
Castle Module
Miketsu, 2019
"""

import asyncio
import os
import urllib.request
from datetime import datetime
from itertools import cycle
from math import ceil

import discord
import pytz
from PIL import Image, ImageFont, ImageDraw
from discord.ext import commands
from discord_webhook import DiscordWebhook, DiscordEmbed

from cogs.mongo.database import get_collections

# Collections
books = get_collections("books")
config = get_collections("config")
duelists = get_collections("duelists")
guilds = get_collections("guilds")
portraits = get_collections("portraits")
shikigamis = get_collections("shikigamis")

# Lists
pool_all = []
lists_souls = []
lists_souls_raw = []

duel_fields = config.find_one({"list": 1}, {"_id": 0, "duel_fields": 1})["duel_fields"]
invalid_channels = config.find_one({"list": 1}, {"_id": 0, "invalid_channels": 1})["invalid_channels"]
primary_roles = config.find_one({"list": 1}, {"_id": 0, "primary_roles": 1})["primary_roles"]

# Variables
id_guild = int(os.environ.get("SERVER"))
colour = config.find_one({"var": 1}, {"_id": 0, "embed_color": 1})["embed_color"]

id_castle = int(guilds.find_one({"server": str(id_guild)}, {"_id": 0, "categories": 1})["categories"]["castle"])
id_duelling_room = guilds.find_one({"server": str(id_guild)}, {"_id": 0, "channels": 1})["channels"]["duelling-room"]
id_hosting = guilds.find_one({"server": str(id_guild)}, {"_id": 0, "channels": 1})["channels"]["bot-sparring"]
id_reference = guilds.find_one({"server": str(id_guild)}, {"_id": 0, "channels": 1})["channels"]["reference-section"]
id_restricted = guilds.find_one({"server": str(id_guild)}, {"_id": 0, "channels": 1})["channels"]["restricted-section"]

timezone = config.find_one({"var": 1}, {"_id": 0, "timezone": 1})["timezone"]

# Dictionaries
primary_emojis = config.find_one({"dict": 1}, {"_id": 0, "primary_emojis": 1})["primary_emojis"]

# Instantiations

for soul in books.find({"section": "sbs", "index": {"$nin": ["1", "2", "3"]}}, {"_id": 0, "index": 1}):
    lists_souls.append("`{}`".format(soul["index"].lower()))
    lists_souls_raw.append(soul["index"].lower())

for document in shikigamis.find({}, {"_id": 0, "name": 1}):
    pool_all.append(document["name"])


def check_if_valid_and_castle(ctx):
    return ctx.channel.category.id == id_castle and str(ctx.channel.name) not in invalid_channels


def check_if_channel_is_pvp(ctx):
    return str(ctx.channel.id) == id_duelling_room


def check_if_reference_section(ctx):
    return str(ctx.channel.id) == id_reference


def check_if_restricted_section(ctx):
    return str(ctx.channel.id) == id_restricted


class Castle(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.prefix = self.client.command_prefix
    
    def create_webhook_post(self, webhooks, book):

        bukkuman = webhooks[0]
        webhook = DiscordWebhook(
            content=book['content'],
            url=bukkuman.url,
            avatar_url="https://i.imgur.com/5FflHQ5.jpg",
            username="Professor Bukkuman"
        )

        def generate_embed_value_1(dictionary, key):
            try:
                value = dictionary[key]
            except KeyError:
                value = None
            return value

        try:
            for entry in book["embeds"]:
                embed = DiscordEmbed(color=generate_embed_value_1(entry, "color"))
                try:
                    embed.title = generate_embed_value_1(entry, "title")
                except AttributeError:
                    pass
                except TypeError:
                    pass

                try:
                    embed.description = generate_embed_value_1(entry, "description").replace("\\n", "\n")
                except AttributeError:
                    pass
                except TypeError:
                    pass

                try:
                    embed.set_thumbnail(url=generate_embed_value_1(entry, "thumbnail")["url"])
                except TypeError:
                    pass

                try:
                    embed.set_image(url=generate_embed_value_1(entry, "image")["url"])
                except TypeError:
                    pass

                try:
                    for field in entry["fields"]:
                        embed.add_embed_field(
                            name=field["name"],
                            value=field["value"].replace("\\n", "\n"),
                            inline=False
                        )
                except KeyError:
                    pass

                try:
                    user_id = generate_embed_value_1(entry, "author")["icon_url"]
                    user = self.client.get_user(int(user_id))
                    embed.set_author(
                        name=generate_embed_value_1(entry, "author")["name"],
                        icon_url=str(user.avatar_url_as(format="jpg", size=128))
                    )
                except ValueError:
                    return
                except TypeError:
                    pass
                except AttributeError:
                    pass

                try:
                    user_id = generate_embed_value_1(entry, "footer")["text"]
                    user = self.client.get_user(int(user_id))
                    embed.set_footer(
                        text=f"Guide by {user.name}",
                        icon_url=str(user.avatar_url_as(format="jpg", size=128))
                    )
                except ValueError:
                    embed.set_footer(
                        text=generate_embed_value_1(entry, "footer")["text"]
                    )
                except TypeError:
                    pass
                except AttributeError:
                    pass

                webhook.add_embed(embed)

        except KeyError:
            pass

        return webhook

    def get_time(self):
        return datetime.now(tz=pytz.timezone(timezone))

    def get_timestamp(self):
        return datetime.utcfromtimestamp(datetime.timestamp(datetime.now()))
    
    def get_emoji_primary_role(self, role):
        return primary_emojis[role]
    
    def lengthen(self, index):
        prefix = "#{}"
        if index < 10:
            prefix = "#00{}"
        elif index < 100:
            prefix = "#0{}"
        return prefix.format(index)
    
    def pluralize(self, singular, count):
        if count > 1:
            if singular[-1:] == "s":
                return singular + "es"
            return singular + "s"
        else:
            return singular

    async def post_process_books(self, ctx, query):
        books.update_one(query, {"$inc": {"borrows": 1}})
        await ctx.message.delete()

    @commands.command(aliases=["guides"])
    @commands.guild_only()
    async def post_table_of_content(self, ctx):

        if check_if_reference_section(ctx):

            await self.post_table_of_content_reference(ctx.channel)
            await ctx.message.delete()

        elif check_if_restricted_section(ctx):

            await self.post_table_of_content_restricted(ctx.channel)
            await ctx.message.delete()

        else:
            request = guilds.find_one({"server": str(ctx.guild.id)}, {
                "channels.restricted-section": 1, "channels.reference-section": 1
            })

            reference_section = f"{request['channels']['reference-section']}"
            restricted_section = f"{request['channels']['restricted-section']}"

            embed = discord.Embed(
                title="guides, guide", colour=discord.Colour(0xffe6a7),
                description="show the guild's game guides collection, usable only at the library"
            )
            embed.add_field(name="Libraries", value=f"<#{reference_section}>, <#{restricted_section}>")
            await ctx.channel.send(embed=embed)

    async def post_table_of_content_restricted(self, channel):
        try:
            webhooks = await channel.webhooks()
            bukkuman = webhooks[0]
            webhook = DiscordWebhook(url=bukkuman.url, avatar_url="https://i.imgur.com/5FflHQ5.jpg")
        except AttributeError:
            return False

        description = \
            "• To open a book use `;open [section] [index]`\n" \
            "• Example: `;open da 8`"

        embed = DiscordEmbed(
            title=":bookmark: Table of Contents",
            colour=discord.Colour(0xa0c29a),
            description=description
        )
        embed.add_embed_field(
            name=":notebook: Defense Against The Dark Arts `[DA]`",
            value="• `[1]` Wind Kirin\n"
                  "• `[2]` Fire Kirin\n"
                  "• `[3]` Lightning Kirin\n"
                  "• `[4]` Water Kirin\n"
                  "• `[5]` Namazu\n"
                  "• `[6]` Oboroguruma\n"
                  "• `[7]` Odokuro\n"
                  "• `[8]` Shinkirou\n"
                  "• `[9]` Tsuchigumo\n"
        )
        embed.add_embed_field(
            name=":notebook: Fantastic Beasts and How to Deal with Them `[FB]`",
            value="• `[1]` Winged Tsukinohime Guide\n"
                  "• `[2]` Song of the Isle and Sorrow Guide\n"
        )
        embed.add_embed_field(
            name=":notebook: The Dark Arts Outsmarted `[DAO]`",
            value="• `[1]` True Orochi Co-op Carry"
        )
        webhook.add_embed(embed)
        webhook.execute()
        return True

    async def post_table_of_content_reference(self, channel):
        try:
            webhooks = await channel.webhooks()
            bukkuman = webhooks[0]
            webhook = DiscordWebhook(url=bukkuman.url, avatar_url="https://i.imgur.com/5FflHQ5.jpg")
        except AttributeError:
            return False

        lists_souls_formatted = ", ".join(lists_souls)
        description = \
            "• To open a book use `;open [section] [index]`\n" \
            "• Example: `;open sbs 3`"

        embed = DiscordEmbed(
            title=":bookmark: Table of Magical Contents",
            colour=discord.Colour(0xa0c29a),
            description=description
        )
        embed.add_embed_field(
            name=":book: The Standard Book of Souls - Year 1 `[SBS]`",
            value="{}".format(lists_souls_formatted)
        )
        embed.add_embed_field(
            name=":book: The Standard Book of Souls - Year 5 `[SBS]`",
            value="• `[1]` Souls 10 Speed Run (24-25s)\n"
                  "• `[2]` Souls 10 Speed Run (20-21s)\n"
                  "• `[3]` Souls Moan Team Varieties"
        )
        embed.add_embed_field(
            name=":closed_book: Secret Duelling Books `[SDB]`",
            value="• `[1]` Curses & Counter-Curses by zu(IA)uz - Book 1\n"
                  "• `[2]` Curses & Counter-Curses by zu(IA)uz - Book 1\n"
                  "• `[3]` What if by Quinlynn - Book 1\n"
                  "• `[4]` What if by Quinlynn - Book 2"
        )
        embed.add_embed_field(
            name=":books: Assorted Books `[AB]`",
            value="• `[1]` Advanced Realm-Making\n"
                  "• `[2]` A Beginner's Guide to Shikigami Affection\n"
                  "• `[3]` Predicting the Unpredictable: Summon Odds\n"
                  "• `[4]` Spellman's Syllabary: Contractions"
        )
        webhook.add_embed(embed)
        webhook.execute()
        return True

    @commands.command(aliases=["open"])
    @commands.guild_only()
    async def post_book_reference(self, ctx, arg1, *, args="None"):

        if check_if_reference_section(ctx):

            webhooks = await ctx.channel.webhooks()
            query = {"section": arg1.lower(), "index": args.lower()}

            if arg1.lower() == "pb" and args.lower() == "bgt":
                query = {"section": arg1.lower(), "index": "0"}

            book = books.find_one(query, {"_id": 0})

            if arg1.lower() in ["ab", "sbs"] and args.lower() in ["3"]:

                opener = urllib.request.build_opener()
                opener.addheaders = [('User-agent', 'Mozilla/5.0')]
                urllib.request.install_opener(opener)
                urllib.request.urlretrieve(book["attachment"], book["address"])

                file = discord.File(book["address"], filename=book["filename"])
                contributor = self.client.get_user(int(book["contributor"]))
                await ctx.channel.send(
                    content=f"{book['content']} {contributor}",
                    file=file
                )
                await self.post_process_books(ctx, query)

            elif book is not None:

                webhook = self.create_webhook_post(webhooks, book)
                webhook.execute()
                await self.post_process_books(ctx, query)

        elif check_if_restricted_section(ctx):

            webhooks = await ctx.channel.webhooks()
            query = {"section": arg1.lower(), "index": args.lower()}
            book = books.find_one(query, {"_id": 0})

            if arg1.lower() in ["fb"] and args.lower() in ["1", "2"]:

                opener = urllib.request.build_opener()
                opener.addheaders = [('User-agent', 'Mozilla/5.0')]
                urllib.request.install_opener(opener)
                urllib.request.urlretrieve(book["attachment"], book["address"])

                file = discord.File(book["address"], filename=book["filename"])
                await ctx.channel.send(
                    content=f"{book['content']}",
                    file=file
                )
                await self.post_process_books(ctx, query)

            elif book is not None:

                webhook = self.create_webhook_post(webhooks, book)
                webhook.execute()
                await self.post_process_books(ctx, query)

    @commands.command(aliases=["portraits"])
    @commands.guild_only()
    async def castle_portrait_show_all(self, ctx):

        count = portraits.count({})
        portraits_listings = {}

        def generate_value_floors(floor):
            try:
                value = ", ".join(portraits_listings[str(floor)])
            except KeyError:
                value = None
            return value

        embed = discord.Embed(
            title="Patronus Portraits", color=ctx.author.colour,
            description=f"There are {count} frames hanging in the castle"
        )

        for x in reversed(range(1, 8)):
            floor_frames = []
            for frame in portraits.find({"floor": x}, {"_id": 0, "floor": 1, "in_game_name": 1}):
                floor_frames.append(frame["in_game_name"])
                entry = {str(x): floor_frames}
                portraits_listings.update(entry)

            embed.add_field(name=f"Floor {x}", value="*{}*".format(generate_value_floors(x)), inline=False)

        await ctx.channel.send(embed=embed)

    @commands.command(aliases=["wander", "w"])
    @commands.check(check_if_valid_and_castle)
    @commands.guild_only()
    async def castle_wander(self, ctx):

        try:
            floor_num = int(ctx.channel.topic[:1])
            floor_frames = cycle(list(portraits.find({"floor": floor_num})))

            def create_new_embed_page():
                frame_preview = next(floor_frames)
                find_role = frame_preview["role"]
                in_game_name = frame_preview["in_game_name"]
                image_link = frame_preview["image_link"] + "?size=2048"
                floor = frame_preview["floor"]
                frame_number = frame_preview["frame"]
                description = frame_preview["description"].replace("\\n", "\n")

                embed_new = discord.Embed(
                    color=ctx.author.colour,
                    title=f"{self.get_emoji_primary_role(find_role)} {in_game_name}",
                    description=description
                )
                embed_new.set_image(url=image_link)
                embed_new.set_footer(
                    text=f"Floor {floor} | Frame {frame_number}"
                )
                return embed_new

            msg = await ctx.channel.send(embed=create_new_embed_page())
            await msg.add_reaction("➡")

            def check(r, u):
                return u != self.client.user and r.message.id == msg.id

            while True:
                try:
                    reaction, user = await self.client.wait_for("reaction_add", timeout=180, check=check)
                except asyncio.TimeoutError:
                    await msg.clear_reactions()
                    break
                else:
                    if str(reaction.emoji) == "➡":
                        await msg.edit(embed=create_new_embed_page())
        except ValueError:
            return

    @commands.command(aliases=["portrait"])
    @commands.guild_only()
    async def castle_portrait_customize(self, ctx, arg1, *, args=None):

        if arg1.lower() not in ["edit", "add"]:
            embed = discord.Embed(
                title="portrait add, portrait edit", colour=discord.Colour(colour),
                description=f"use `add` first before using `edit`\n"
                            f"use square photos for best results"
            )
            embed.add_field(
                name="Format",
                value=f"*`{self.prefix}portrait add <name> <floor#1-7> <img_link/default> <desc.>`*",
                inline=False
            )
            embed.add_field(
                name="Example",
                value=f"*`{self.prefix}portrait add xann 6 default Headless`*",
                inline=False
            )
            await ctx.channel.send(embed=embed)

        elif arg1.lower() in ["edit", "add"]:
            frame_id = str(ctx.author.id)
            user_roles = ctx.guild.get_member(ctx.author.id).roles
            frame_profile = portraits.find_one({"frame_id": str(frame_id)}, {"_id": 0})

            argument = args.split(" ", 3)
            in_game_name = argument[0]
            image_link = argument[2]
            description = argument[3].replace("\\n", "\n")
            frame_num = portraits.count() + 1

            try:
                floor = int(argument[1])
            except ValueError:
                embed = discord.Embed(
                    colour=discord.Colour(colour),
                    title="Invalid floor number",
                    description="available floors: 1-6 only"
                )
                await ctx.channel.send(embed=embed)
                return

            if image_link.lower() == "default":
                image_link = ctx.author.avatar_url

            find_role = ""
            for role in reversed(user_roles):
                if role.name in primary_roles:
                    find_role = role.name
                    break

            if frame_profile is not None:
                embed = discord.Embed(
                    colour=discord.Colour(colour),
                    description=f"portrait already exists, use `{self.prefix}frame edit <...>`"
                )
                await ctx.channel.send(embed=embed)

            elif floor not in [1, 2, 3, 4, 5, 6]:
                embed = discord.Embed(
                    colour=discord.Colour(colour),
                    title="Invalid floor number",
                    description="available floors: 1-6 only"
                )
                await ctx.channel.send(embed=embed)
                return

            elif arg1.lower() == "others":
                attachment_link = await self.castle_portrait_customize_process(
                    str(image_link), in_game_name, "Head", ctx, description, floor, frame_num
                )

                profile = {
                    "frame_id": None,
                    "floor": floor,
                    "frame": frame_num,
                    "in_game_name": in_game_name,
                    "role": "Head",
                    "image_link": attachment_link,
                    "description": description
                }
                portraits.insert_one(profile)

            elif arg1.lower() == "edit" and frame_profile is not None:
                attachment_link = await self.castle_portrait_customize_process(
                    str(image_link), in_game_name, find_role, ctx, description, floor, frame_num
                )
                portraits.update_one({
                    "frame_id": str(ctx.author.id)}, {
                    "$set": {
                        "floor": floor,
                        "frame": frame_num,
                        "in_game_name": in_game_name,
                        "role": find_role,
                        "image_link": attachment_link,
                        "description": description

                    }
                })

    async def castle_portrait_customize_process(self, img_link, ign, find_role, ctx, description, floor, frame_num):

        async with ctx.channel.typing():
            embed = discord.Embed(colour=discord.Colour(colour), title="Processing the image.. ")
            msg1 = await ctx.channel.send(embed=embed)
            await asyncio.sleep(2)
            embed = discord.Embed(
                colour=discord.Colour(colour),
                title="Adding a fancy frame based on your highest primary server role.."
            )
            await msg1.edit(embed=embed)

            opener = urllib.request.build_opener()
            opener.addheaders = [('User-agent', 'Mozilla/5.0')]
            urllib.request.install_opener(opener)
            temp_address = f"temp/{ign}_temp.jpg"
            urllib.request.urlretrieve(img_link, temp_address)
            role_frame = f"data/frames/{find_role.lower()}.png"

            background = Image.open(temp_address)
            width, height = background.size
            new_foreground = Image.open(role_frame).resize((width, height), Image.NEAREST)
            background.paste(new_foreground, (0, 0), new_foreground)

            new_address = f"temp/{ign}.png"
            background.save(new_address)

            new_photo = discord.File(new_address, filename=f"{ign}.png")
            hosting_channel = self.client.get_channel(int(id_hosting))
            msg = await hosting_channel.send(file=new_photo)

            await asyncio.sleep(3)
            await asyncio.sleep(2)

            attachment_link = msg.attachments[0].url

            embed = discord.Embed(
                color=ctx.author.colour,
                title=f"{self.get_emoji_primary_role(find_role)} {ign}",
                description=description
            )
            embed.set_image(url=attachment_link)
            embed.set_footer(
                text=f"Floor {floor} | Frame# {frame_num}"
            )
            await ctx.channel.send(embed=embed)
            await asyncio.sleep(2)
            await msg1.delete()

        return attachment_link

    @commands.command(aliases=["duel", "d"])
    @commands.guild_only()
    @commands.check(check_if_channel_is_pvp)
    async def management_duel(self, ctx, *args):

        if len(args) == 0 or args[0].lower() in ["help", "h"]:
            embed = discord.Embed(
                title="duel, d", colour=discord.Colour(colour),
                description="shows the help prompt for the first 3 arguments"
            )
            embed.add_field(name="Arguments", value="*add, update, show, delete*", inline=False)
            embed.add_field(name=f"Example", value=f"*`{self.prefix}duel add`*", inline=False)
            await ctx.channel.send(embed=embed)

        elif args[0].lower() == "add" and len(args) <= 1:
            embed = discord.Embed(
                title="duel add, d a", colour=discord.Colour(colour),
                description="add a new duelist in the database"
            )
            embed.add_field(name="Format", value=f"*`{self.prefix}duel add <name>`*", inline=False)
            await ctx.channel.send(embed=embed)

        elif args[0].lower() == ["delete", "d"] and len(args) <= 1:
            embed = discord.Embed(
                title="duel delete, d d", colour=discord.Colour(colour),
                description="removes a duelist in the database"
            )
            embed.add_field(name="Format", value=f"*`{self.prefix}duel delete <exact_name>`*", inline=False)
            await ctx.channel.send(embed=embed)

        elif args[0].lower() in ["add", "a"] and len(args) == 2:
            await self.management_duel_profile_member_add(ctx, args)

        elif args[0].lower() in ["delete", "d"] and len(args) == 2:
            await self.management_duel_profile_member_delete(ctx, args)

        elif args[0].lower() in ["update", "u"] and len(args) <= 1:
            embed = discord.Embed(
                title="duel update, d u", colour=discord.Colour(colour),
                description="updates a duelist's profile"
            )
            embed.add_field(name="Format", value=f"*`{self.prefix}d u <name or id> <field> <value>`*")
            embed.add_field(
                name="field :: value",
                value=f"• **name** :: <new_name>\n"
                      f"• **notes** :: *<any member notes>*\n"
                      f"• **ban/unban** :: *<shikigami>*\n"
                      f"• **core/uncore** :: *<shikigami>*\n"
                      f"• **lineup** :: *attach a photo upon sending*",
                inline=False
            )
            embed.add_field(
                name="Example",
                value=f"*`{self.prefix}d u 1 ban enma`*\n"
                      f"*`{self.prefix}d u 100 notes benefits more on upper-hand teams`*",
                inline=False
            )
            await ctx.channel.send(embed=embed)

        elif args[0].lower() in ["update", "u"] and len(args) == 2:
            fields_formatted = []
            for field in duel_fields:
                fields_formatted.append(f"`{field}`")

            embed = discord.Embed(
                colour=discord.Colour(colour),
                title="No field and value provided",
                description=f"Valid fields: *{', '.join(fields_formatted)}*"
            )
            await ctx.channel.send(embed=embed)

        elif args[0].lower() in ["update", "u"] and args[2].lower() not in duel_fields and len(args) >= 3:
            fields_formatted = []
            for field in duel_fields:
                fields_formatted.append(f"`{field}`")

            embed = discord.Embed(
                colour=discord.Colour(colour),
                title="Invalid field update request",
                description=f"Valid fields: *{', '.join(fields_formatted)}*"
            )
            await ctx.channel.send(embed=embed)

        elif args[0].lower() in ["update", "u"] and len(args) == 3 and args[2].lower() in ["lineup", "lineups"]:
            await self.management_duel_profile_update_field(ctx, args)

        elif args[0].lower() in ["update", "u"] and args[2].lower() in duel_fields and len(args) == 3:
            embed = discord.Embed(
                colour=discord.Colour(colour),
                title="Invalid field update request",
                description=f"No value provided for the field {args[2].lower()}"
            )
            await ctx.channel.send(embed=embed)

        elif args[0].lower() in ["update", "u"] and len(args) >= 4 and args[2].lower() in duel_fields:
            await self.management_duel_profile_update_field(ctx, args)

        elif args[0].lower() in ["show", "s"] and len(args) == 1:
            embed = discord.Embed(
                title="duel show, d s", colour=discord.Colour(colour),
                description="queries the duelists database"
            )
            embed.add_field(
                name="Formats",
                value=f"• *`{self.prefix}d s all <opt: [<startswith>]>`*\n"
                      f"• *`{self.prefix}d s <name or id_num>`*",
                inline=False
            )
            embed.add_field(
                name="Examples",
                value=f"• *`{self.prefix}d s all`*\n"
                      f"• *`{self.prefix}d s all aki`*\n"
                      f"• *`{self.prefix}d s 120`*\n",
                inline=False
            )
            await ctx.channel.send(embed=embed)

        elif args[0].lower() in ["show", "s"] and len(args) == 2 and args[1].lower() == "all":
            await self.management_duel_profile_show_all(ctx)

        elif args[0].lower() in ["show", "s"] and len(args) == 3 and args[1].lower() == "all":
            await self.management_duel_profile_show_startswith(ctx, args)

        elif args[0].lower() in ["show", "s"] and len(args) == 2 and args[1].lower() != "all":
            await self.management_duel_profile_show_profile(ctx, args)

        else:
            await ctx.message.add_reaction("❌")

    async def management_duel_profile_show_profile(self, ctx, args):
        try:
            name_id = int(args[1])
            query = {"#": name_id}
            member = duelists.find_one(query, {"_id": 0})

        except ValueError:
            query = {"name_lower": args[1].lower()}
            member = duelists.find_one(query, {"_id": 0})

        try:
            embed = discord.Embed(
                color=ctx.author.colour,
                title=f"{self.lengthen(member['#'])} : {member['name']}",
                timestamp=self.get_timestamp()
            )
            embed.set_thumbnail(url=ctx.guild.icon_url)
            embed.add_field(
                name="📸 Stats",
                value=f"Bans: {len(member['ban'])} | Cores: {len(member['core'])}",
                inline=False
            )

            if not member["notes"]:
                embed.add_field(name="🗒 Notes", value="No notes yet.")

            elif len(member["notes"]) != 0:
                notes = ""
                for note in member["notes"]:
                    entry = f"[{note['time'].strftime('%d.%b %y')} | {note['member']}]: {note['note']}\n"
                    notes += entry

                embed.add_field(name="🗒 Notes", value=notes)

            if len(member["ban"]) != member["ban_count"] or len(member["core"]) != member["core_count"]:
                link = await self.management_duel_profile_generate_image(member["ban"], member["core"], ctx)
                duelists.update_one(query, {
                    "$set": {
                        "link": link,
                        "ban_count": len(member["ban"]),
                        "core_count": len(member["core"])
                    }})
            else:
                link = member["link"]

            embed.set_image(url=link)
            msg = await ctx.channel.send(embed=embed)
            await msg.add_reaction("⬅")
            await msg.add_reaction("➡")

            def check(r, u):
                return str(r.emoji) in ["⬅", "➡"] and msg.id == r.message.id and u.id != self.client.user.id

            page = 0
            while True:
                try:
                    await self.client.wait_for("reaction_add", timeout=180, check=check)
                except asyncio.TimeoutError:
                    await msg.clear_reactions()
                    break
                else:
                    links = member["lineup"]

                    def generate_embed_lineup(x):
                        embed_new = discord.Embed(
                            title=f"🖼 Lineup Archives for {member['name']}",
                            color=ctx.author.colour,
                            timestamp=self.get_timestamp()
                        )
                        if len(links) > 0:
                            embed_new.set_image(url=links[page - 1])
                            embed_new.set_footer(text=f"Page: {page} of {len(links)}")
                        else:
                            embed_new.description = f"this duelist has no lineup records yet\n\n" \
                                                    f"to add, use " \
                                                    f"*`{self.prefix}duel update <ID/name> lineup`*\n" \
                                                    f"send it with an image uploaded in the message"
                            embed_new.set_footer(text=f"Page: {x} of 1")

                        return embed_new

                    page += 1
                    if page > len(links):
                        page = 1
                    elif page < 1:
                        page = len(links) - 1

                    await msg.edit(embed=generate_embed_lineup(page))

        except TypeError:
            await self.management_duel_profile_show_approximate(ctx, args[1])

    async def management_duel_profile_show_all(self, ctx):

        formatted_list = []
        find_query = {}
        project = {"_id": 0, "#": 1, "name": 1}

        for duelist in duelists.find(find_query, project).sort([("#", 1)]):
            number = self.lengthen(duelist["#"])
            formatted_list.append(f"`{number}:` | {duelist['name']}\n")

        noun = self.pluralize("duelist", len(formatted_list))
        content = f"There are {len(formatted_list)} registered {noun}"
        await self.management_duel_profile_paginate_embeds(ctx, formatted_list, content)

    async def management_duel_profile_show_startswith(self, ctx, args):

        formatted_list = []
        find_query = {"name_lower": {"$regex": f"^{args[2].lower()}"}}
        project = {"_id": 0, "#": 1, "name": 1}

        for duelist in duelists.find(find_query, project).sort([("name_lower", 1)]):
            number = self.lengthen(duelist["#"])
            formatted_list.append(f"`{number}:` | {duelist['name']}\n")

        noun = self.pluralize("result", len(formatted_list))
        content = f"I've got {len(formatted_list)} {noun} for duelists starting with __{args[2].lower()}__"
        await self.management_duel_profile_paginate_embeds(ctx, formatted_list, content)

    async def management_duel_profile_show_approximate(self, ctx, member_name):
        members_search = duelists.find({"name_lower": {"$regex": f"^{member_name[:2].lower()}"}}, {"_id": 0})

        approximate_results = []
        for result in members_search:
            approximate_results.append(f"{result['#']}/{result['name_lower']}")

        embed = discord.Embed(
            colour=discord.Colour(colour),
            title="Invalid query",
            description=f"the ID/name `{member_name}` returned no results"
        )
        embed.add_field(
            name="Possible matches",
            value="*{}*".format(", ".join(approximate_results))
        )
        await ctx.channel.send(embed=embed)

    async def management_duel_profile_update_field(self, ctx, args):
        try:
            name_id = int(args[1])
            find_query = {"#": name_id}
            name = "kyrvscyl"

        except ValueError:
            find_query = {"name_lower": args[1].lower()}
            name_id = 1
            name = args[1].lower()

        if duelists.find_one({"name_lower": name}) is None or duelists.find_one({"#": name_id}) is None:
            await self.management_duel_profile_show_approximate(ctx, args[1])

        elif args[2].lower() in ["notes", "note"]:
            duelists.update_one(find_query, {
                "$push": {
                    "note": {
                        "member": ctx.author.name,
                        "time": self.get_time(),
                        "note": " ".join(args[3::])
                    }
                },
                "$set": {
                    "last_update": self.get_time()
                }
            })
            await ctx.message.add_reaction("✅")

        elif args[2].lower() == "name":
            duelists.update_one(find_query, {"$set": {
                "name": args[3], "name_lower": args[3].lower(), "last_update": self.get_time()
            }})
            await ctx.message.add_reaction("✅")

        elif args[2].lower() in ["unban", "uncore"] and " ".join(args[3:]).lower() in pool_all:
            duelists.update_one(find_query, {
                "$pull": {
                    args[2].lower()[2:]: " ".join(args[3:]).lower()
                },
                "$set": {
                    "last_update": self.get_time()
                }
            })
            await ctx.message.add_reaction("✅")

        elif args[2].lower() in ["ban", "core"] and " ".join(args[3:]).lower() in pool_all:
            duelists.update_one(find_query, {
                "$push": {
                    args[2].lower(): " ".join(args[3:]).lower()
                },
                "$set": {
                    "last_update": self.get_time()
                }
            })
            await ctx.message.add_reaction("✅")

        elif args[2].lower() in ["lineup", "lineups"]:
            image_link = ctx.message.attachments[0].url
            duelists.update_one(find_query, {
                "$push": {
                    "lineup": image_link
                },
                "$set": {
                    "last_update": self.get_time()
                }
            })
            await ctx.message.add_reaction("✅")

        else:
            await ctx.message.add_reaction("❌")

    async def management_duel_profile_member_delete(self, ctx, args):
        if duelists.find_one({"name": args[1]}) is not None:
            duelists.delete_one({"name": args[1]})
            await ctx.message.add_reaction("✅")

            name_id = 1
            for member in duelists.find({}, {"_id": 0, "name": 1}):
                duelists.update_one({"name": member["name"]}, {"$set": {"#": name_id}})
                name_id += 1

        else:
            await self.management_duel_profile_show_approximate(ctx, args[1])

    async def management_duel_profile_member_add(self, ctx, args):

        if duelists.find_one({"name_lower": args[1].lower()}) is None:

            profile = {
                "#": duelists.count() + 1,
                "name": args[1],
                "name_lower": args[1].lower(),
                "ban": [],
                "ban_count": -1,
                "core": [],
                "core_count": -1,
                "lineup": [],
                "notes": [],
                "link": None,
                "last_update": self.get_time()
            }
            duelists.insert_one(profile)
            await ctx.message.add_reaction("✅")

        else:
            embed = discord.Embed(
                title="Invalid duelist", colour=discord.Colour(colour),
                description="that name already exists in the database"
            )
            await ctx.channel.send(embed=embed)

    async def management_duel_profile_generate_image(self, bans, cores, ctx):

        bans_address = []
        for shikigami in bans:
            bans_address.append(f"data/shikigamis/{shikigami}_pre.jpg")

        cores_address = []
        for shikigami in cores:
            cores_address.append(f"data/shikigamis/{shikigami}_pre.jpg")

        x, y = 4, 0
        max_cols = 7

        def get_coordinates(c):
            a = (c * 90 - (ceil(c / max_cols) - 1) * max_cols * 90) - 90
            b = (ceil(c / max_cols) * 90) - 90
            return a, b

        def generate_shikigami_list(listings, text, color_fill):
            font = ImageFont.truetype('data/marker_felt_wide.ttf', 20)
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
        max_height = max(heights)
        max_width = max(widths)

        temp_address = f"temp/{ctx.message.id}.png"
        combined_img = Image.new('RGBA', (max_width, (max_height * 2) + 7), (255, 0, 0, 0))
        combined_img.paste(im_bans, (0, 0))
        combined_img.paste(im_cores, (0, int(max_height) + 7))
        combined_img.save(temp_address)

        new_photo = discord.File(temp_address, filename=f"{ctx.message.id}.png")
        hosting_channel = self.client.get_channel(int(id_hosting))
        msg = await hosting_channel.send(file=new_photo)
        attachment_link = msg.attachments[0].url
        return attachment_link

    async def management_duel_profile_paginate_embeds(self, ctx, formatted_list, content):

        page = 1
        max_lines = 20
        page_total = ceil(len(formatted_list) / max_lines)
        if page_total == 0:
            page_total = 1

        def create_new_embed_page(page_new):
            end = page_new * max_lines
            start = end - max_lines
            description_new = "".join(formatted_list[start:end])

            embed_new = discord.Embed(
                color=ctx.author.colour, title="🎌 Secret Duelling Book",
                description=f"{description_new}", timestamp=self.get_timestamp()
            )
            embed_new.set_footer(text=f"Page: {page_new} of {page_total}")
            embed_new.set_thumbnail(url=ctx.guild.icon_url)
            return embed_new

        msg = await ctx.channel.send(content=content, embed=create_new_embed_page(page))
        await msg.add_reaction("⬅")
        await msg.add_reaction("➡")

        def check(r, u):
            return u != self.client.user and r.message.id == msg.id

        while True:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=180, check=check)
            except asyncio.TimeoutError:
                await msg.clear_reactions()
                break
            else:
                if str(reaction.emoji) == "➡":
                    page += 1
                elif str(reaction.emoji) == "⬅":
                    page -= 1
                if page == 0:
                    page = page_total
                elif page > page_total:
                    page = 1
                await msg.edit(embed=create_new_embed_page(page))


def setup(client):
    client.add_cog(Castle(client))
