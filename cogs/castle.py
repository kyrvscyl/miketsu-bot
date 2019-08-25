"""
Castle Module
Miketsu, 2019
"""

import asyncio
import random
import urllib.request
from datetime import datetime
from math import ceil

import discord
import pytz
from PIL import Image, ImageFont, ImageDraw
from discord.ext import commands

from cogs.mongo.database import get_collections
from cogs.startup import primary_id, embed_color, pluralize

# Collections
portraits = get_collections("bukkuman", "portraits")
books = get_collections("bukkuman", "books")
duelists = get_collections("bukkuman", "duelists")
shikigamis = get_collections("miketsu", "shikigamis")

# Listings
primary_roles = ["Head", "Auror", "Patronus", "No-Maj"]
invalid_channels = ["auror-department", "gift-game", "pvp-fair", "duelling-room"]
duelling_room_id = []
castles_id = []
pool_all = []
fields = ["name", "notes", "ban", "core", "lineup"]

for document in books.find({}, {"_id": 0, "categories.castle": 1}):
    try:
        castles_id.append(document["categories"]["castle"])
    except KeyError:
        continue


for document in books.find({}, {"_id": 0, "channels.duelling-room": 1}):
    try:
        duelling_room_id.append(document["channels"]["duelling-room"])
    except KeyError:
        continue


for document in shikigamis.find({}, {"_id": 0, "name": 1}):
    pool_all.append(document["name"])


def get_time():
    tz_target = pytz.timezone("America/Atikokan")
    return datetime.now(tz=tz_target)


def lengthen(index):
    prefix = "#{}"
    if index < 10:
        prefix = "#00{}"
    elif index < 100:
        prefix = "#0{}"
    return prefix.format(index)


def get_timestamp():
    return datetime.utcfromtimestamp(datetime.timestamp(datetime.now()))


def check_if_valid_and_castle(ctx):
    return str(ctx.channel.category.id) in castles_id and str(ctx.channel.name) not in invalid_channels


def check_if_guild_is_patronus(ctx):
    return ctx.guild.id == 412057028887052288


def get_emoji_primary_role(role):
    dictionary = {"Auror": "⚜", "Head": "🔱", "Patronus": "🔮", "No-Maj": "🔥"}
    return dictionary[role]


def check_if_channel_is_pvp(ctx):
    return str(ctx.channel.id) in duelling_room_id


async def duel_profile_update_field(ctx, args):
    try:
        reference_id = int(args[1])
        find_query = {"#": reference_id}
        name = "kyrvscyl"

    except ValueError:
        find_query = {"name_lower": args[1].lower()}
        reference_id = 1
        name = args[1].lower()

    if duelists.find_one({"name_lower": name}) is None or duelists.find_one({"#": reference_id}) is None:
        embed = discord.Embed(colour=discord.Colour(embed_color), title="No such duelist is found in the database")
        await ctx.channel.send(embed=embed)

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
        await ctx.message.add_reaction("✅")

    elif args[2].lower() == "name":
        duelists.update_one(find_query, {"$set": {
            "name": args[3], "name_lower": args[3].lower(), "last_update": get_time()
        }})
        await ctx.message.add_reaction("✅")

    elif args[2].lower() in ["ban", "core"] and " ".join(args[3:]).lower() in pool_all:
        duelists.update_one(find_query, {
            "$push": {
                args[2].lower(): " ".join(args[3:]).lower()
            },
            "$set": {
                "last_update": get_time()
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
                "last_update": get_time()
            }
        })
        await ctx.message.add_reaction("✅")

    else:
        await ctx.message.add_reaction("❌")


async def duel_profile_add_member(ctx, args):

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
            "last_update": get_time()
        }
        duelists.insert_one(profile)
        await ctx.message.add_reaction("✅")

    else:
        embed = discord.Embed(
            title="Invalid duelist", colour=discord.Colour(embed_color),
            description="That name already exists in the database"
        )
        await ctx.channel.send(embed=embed)


class Castle(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(aliases=["portraits"])
    @commands.guild_only()
    async def castle_portrait_show_all(self, ctx):

        count = portraits.count({})
        portraits_listings = {}

        def generate_value_floors(floor):
            try:
                value = ", ".join(portraits_listings[str(floor)])
            except KeyError:
                value = "None"
            return value

        embed = discord.Embed(
            title="Patronus Portraits", color=ctx.author.colour,
            description=f"There are {count} frames hanging in the castle."
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
    @commands.guild_only()
    async def castle_wander(self, ctx):
        await ctx.message.delete()

        if not str(ctx.channel.category.id) in castles_id and str(ctx.channel.name) not in invalid_channels:
            embed = discord.Embed(
                title="wander, w",
                colour=discord.Colour(embed_color),
                description="usable only at the castle's channels with valid floors\n"
                            "check the channel topics for the floor number\n"
                            "automatically deletes the command & frame after a few secs"
            )
            await ctx.channel.send(embed=embed)
            return

        try:
            floor_num = int(ctx.channel.topic[:1])
        except ValueError:
            return

        floor_frames = []
        for frame in portraits.find({"floor": floor_num}):
            floor_frames.append(frame["frame"])

        try:
            random_frame = random.choice(floor_frames)
        except IndexError:
            return

        frame_profile = portraits.find_one({"frame": random_frame}, {"_id": 0})
        find_role = frame_profile["role"]
        in_game_name = frame_profile["in_game_name"]
        image_link = frame_profile["image_link"] + "?width=200&height=200"
        floor = frame_profile["floor"]
        frame_number = frame_profile["frame"]
        description = frame_profile["description"].replace("\\n", "\n")

        embed = discord.Embed(
            color=ctx.author.colour,
            title=f"{get_emoji_primary_role(find_role)} {in_game_name}",
            description=description
        )
        embed.set_image(url=image_link)
        embed.set_footer(
            text=f"Floor {floor} | Frame {frame_number}"
        )
        msg = await ctx.channel.send(embed=embed)
        await msg.delete(delay=10)

    @commands.command(aliases=["portrait"])
    @commands.guild_only()
    async def castle_customize_portrait(self, ctx, arg1, *, args):

        argument = args.split(" ", 3)
        frame_id = str(ctx.author.id)
        member = ctx.guild.get_member(ctx.author.id)
        user_roles = member.roles
        frame_profile = portraits.find_one({"frame_id": str(frame_id)}, {"_id": 0})

        try:
            in_game_name = argument[0]
            floor = int(argument[1])
            image_link = argument[2]
            description = argument[3].replace("\\n", "\n")
            frame_num = portraits.count() + 1

            if image_link.lower() == "default":
                image_link = ctx.author.avatar_url

        except ValueError:
            embed = discord.Embed(
                colour=discord.Colour(embed_color),
                title="Invalid floor number",
                description="Available floors: 1-6 only"
            )
            await ctx.channel.send(embed=embed)
            return

        frames_current = []
        for frame in portraits.find({"frame": {"$exists": True}}):
            frames_current.append(frame["frame"])

        find_role = ""
        for role in reversed(user_roles):
            if role.name in primary_roles:
                find_role = role.name
                break

        if portraits.find({"frame_id": str(ctx.author.id)}, {"_id": 0}) is not None:
            embed = discord.Embed(
                colour=discord.Colour(embed_color),
                description="Frame exists for this user, use `;frame edit <...>`"
            )
            await ctx.channel.send(embed=embed)

        elif floor not in [1, 2, 3, 4, 5, 6]:
            embed = discord.Embed(
                colour=discord.Colour(embed_color),
                title="Invalid floor number",
                description="Available floors: 1-6 only"
            )
            await ctx.channel.send(embed=embed)
            return

        if arg1.lower() in ["add", "others"]:

            if arg1.lower == "add" and frame_profile is not None:
                return

            if arg1.lower() == "others":
                frame_id = None
                find_role = "Head"

            attachment_link = await self.post_process_frame(
                str(image_link), in_game_name, find_role, ctx, description, floor, frame_num
            )

            profile = {
                "frame_id": frame_id,
                "floor": floor,
                "frame": frame_num,
                "in_game_name": in_game_name,
                "role": find_role,
                "image_link": attachment_link,
                "description": description
            }
            portraits.insert_one(profile)

        elif arg1.lower() == "edit" and frame_profile is not None:

            attachment_link = await self.post_process_frame(
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

    async def post_process_frame(self, image_link, in_game_name, find_role, ctx, description, floor, frame_num):

        async with ctx.channel.typing():
            embed = discord.Embed(colour=discord.Colour(embed_color), title="Processing the image.. ")
            msg1 = await ctx.channel.send(embed=embed)
            await asyncio.sleep(2)
            embed = discord.Embed(
                colour=discord.Colour(embed_color),
                title="Adding a fancy frame based on your highest primary server role.."
            )
            await msg1.edit(embed=embed)

            opener = urllib.request.build_opener()
            opener.addheaders = [('User-agent', 'Mozilla/5.0')]
            urllib.request.install_opener(opener)
            temp_address = f"temp/{in_game_name}_temp.jpg"
            urllib.request.urlretrieve(image_link, temp_address)
            role_frame = f"data/frames/{find_role.lower()}.png"

            background = Image.open(temp_address)
            width, height = background.size
            new_foreground = Image.open(role_frame).resize((width, height), Image.NEAREST)
            background.paste(new_foreground, (0, 0), new_foreground)

            new_address = f"temp/{in_game_name}.png"
            background.save(new_address)

            new_photo = discord.File(new_address, filename=f"{in_game_name}.png")
            hosting_channel = self.client.get_channel(556032841897607178)
            msg = await hosting_channel.send(file=new_photo)

            await asyncio.sleep(3)
            await asyncio.sleep(2)

            attachment_link = msg.attachments[0].url

            embed = discord.Embed(
                color=ctx.author.colour,
                title=f"{get_emoji_primary_role(find_role)} {in_game_name}",
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

    @commands.command(aliases=["transform"])
    @commands.is_owner()
    async def transformation_trigger(self, ctx, *, args):

        if args.lower() == "start":
            await self.transformation_start()
            await ctx.message.delete()

        elif args.lower() == "end":
            await self.transformation_end()
            await ctx.message.delete()

    async def transformation_end(self):

        request = books.find_one({"server": str(primary_id)}, {"_id": 0, "server": 1})
        roles = ["No-Maj", "Patronus", "Auror", "Dementor", "Junior Duel Champion", "Senior Duel Champion"]
        server = self.client.get_guild(int(request["server"]))

        try:
            reference_role = discord.utils.get(server.roles, name="Head")
        except AttributeError:
            return

        for role in roles:
            try:
                current_role = discord.utils.get(server.roles, name=role)
                await current_role.edit(position=reference_role.position - 1)
                await asyncio.sleep(1)
            except AttributeError:
                continue
            except discord.errors.Forbidden:
                continue
            except discord.errors.HTTPException:
                continue
            except discord.errors.InvalidArgument:
                continue

    async def transformation_start(self):

        request = books.find_one({"server": str(primary_id)}, {"_id": 0, "server": 1})
        roles = ["No-Maj", "Patronus", "Auror", "Dementor", "Junior Duel Champion", "Senior Duel Champion"]
        server = self.client.get_guild(int(request["server"]))

        try:
            reference_role = discord.utils.get(server.roles, name="🏆")
        except AttributeError:
            return

        for role in roles:
            try:
                current_role = discord.utils.get(server.roles, name=role)
                await current_role.edit(position=reference_role.position - 1)
                await asyncio.sleep(1)
            except AttributeError:
                continue
            except discord.errors.Forbidden:
                continue
            except discord.errors.HTTPException:
                continue
            except discord.errors.InvalidArgument:
                continue

    @commands.command(aliases=["duel", "d"])
    @commands.check(check_if_channel_is_pvp)
    async def management_duel(self, ctx, *args):

        if len(args) == 0 or args[0].lower() in ["help", "h"]:
            embed = discord.Embed(
                title="duel, d", colour=discord.Colour(embed_color),
                description="shows the help prompt for the first 3 arguments"
            )
            embed.add_field(name="Arguments", value="*add, update, show, stats*", inline=False)
            embed.add_field(name="Example", value="*`;duel add`*", inline=False)
            await ctx.channel.send(embed=embed)

        elif args[0].lower() == "add" and len(args) <= 1:
            embed = discord.Embed(
                title="duel add, d a", colour=discord.Colour(embed_color),
                description="add a new duelist in the database"
            )
            embed.add_field(name="Format", value="*`;duel add <name>`*", inline=False)
            await ctx.channel.send(embed=embed)

        elif args[0].lower() in ["add", "a"] and len(args) == 2:
            await duel_profile_add_member(ctx, args)

        elif args[0].lower() in ["update", "u"] and len(args) <= 1:
            embed = discord.Embed(
                title="duel update, d u", colour=discord.Colour(embed_color),
                description="updates a duelist's profile"
            )
            embed.add_field(name="Format", value="*`;d u <name or id> <field> <value>`*")
            embed.add_field(
                name="field :: value",
                value=f"• **name** :: <new_name>\n"
                      f"• **notes** :: *<any member notes>*\n"
                      f"• **ban** :: *<shikigami>*\n"
                      f"• **core** :: *<shikigami>*\n"
                      f"• **lineup** :: *attach a photo upon sending*",
                inline=False
            )
            embed.add_field(
                name="Example",
                value="*`;d u 1 ban enma`*\n"
                      "*`;d u 100 notes benefits more on upper-hand teams`*",
                inline=False
            )
            await ctx.channel.send(embed=embed)

        elif args[0].lower() in ["update", "u"] and len(args) == 2:
            fields_formatted = []
            for field in fields:
                fields_formatted.append(f"`{field}`")

            embed = discord.Embed(
                colour=discord.Colour(embed_color),
                title="No field and value provided",
                description=f"Valid fields: *{', '.join(fields_formatted)}*"
            )
            await ctx.channel.send(embed=embed)

        elif args[0].lower() in ["update", "u"] and args[2].lower() not in fields and len(args) >= 3:
            fields_formatted = []
            for field in fields:
                fields_formatted.append(f"`{field}`")

            embed = discord.Embed(
                colour=discord.Colour(embed_color),
                title="Invalid field update request",
                description=f"Valid fields: *{', '.join(fields_formatted)}*"
            )
            await ctx.channel.send(embed=embed)

        elif args[0].lower() in ["update", "u"] and len(args) == 3 and args[2].lower() in ["lineup", "lineups"]:
            await duel_profile_update_field(ctx, args)

        elif args[0].lower() in ["update", "u"] and args[2].lower() in fields and len(args) == 3:
            embed = discord.Embed(
                colour=discord.Colour(embed_color),
                title="Invalid field update request",
                description=f"No value provided for the field {args[2].lower()}"
            )
            await ctx.channel.send(embed=embed)

        elif args[0].lower() in ["update", "u"] and len(args) >= 4 and args[2].lower() in fields:
            await duel_profile_update_field(ctx, args)

        elif args[0].lower() in ["show", "s"] and len(args) == 1:
            embed = discord.Embed(
                title="duel show, d s", colour=discord.Colour(embed_color),
                description="queries the duelists database"
            )
            embed.add_field(
                name="Formats",
                value="• *`;d s all <opt: [<startswith>]>`*\n"
                      "• *`;d s <name or id_num>`*",
                inline=False
            )
            embed.add_field(
                name="Examples",
                value="• *`;d s all`*\n"
                      "• *`;d s all aki`*\n"
                      "• *`;d s 120`*\n",
                inline=False
            )
            await ctx.channel.send(embed=embed)

        elif args[0].lower() in ["show", "s"] and len(args) == 2 and args[1].lower() == "all":
            await self.duel_profile_show_all(ctx)

        elif args[0].lower() in ["show", "s"] and len(args) == 3 and args[1].lower() == "all":
            await self.management_guild_show_startswith(ctx, args)

        elif args[0].lower() in ["show", "s"] and len(args) == 2 and args[1].lower() != "all":
            await self.duel_profile_show_profile(ctx, args)

        else:
            await ctx.message.add_reaction("❌")

    # noinspection PyMethodMayBeStatic
    async def duel_profile_show_profile(self, ctx, args):
        try:
            reference_id = int(args[1])
            query = {"#": reference_id}
            member = duelists.find_one(query, {"_id": 0})

        except ValueError:
            query = {"name_lower": args[1].lower()}
            member = duelists.find_one(query, {"_id": 0})

        try:
            embed = discord.Embed(
                color=ctx.author.colour,
                title=f"{lengthen(member['#'])} : {member['name']}",
                timestamp=get_timestamp()
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
                link = await self.duel_profile_generate_image(member["ban"], member["core"], ctx)
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
                    break
                else:
                    links = member["lineup"]

                    def generate_embed_lineup(x):
                        embed_new = discord.Embed(
                            title=f"🖼 Lineup Archives for {member['name']}",
                            color=ctx.author.colour,
                            timestamp=get_timestamp()
                        )
                        if len(links) > 0:
                            embed_new.set_image(url=links[page - 1])
                            embed_new.set_footer(text=f"Page: {page} of {len(links)}")
                        else:
                            embed_new.description = "This duelist has no lineup records yet\n\n" \
                                                    "To add, use " \
                                                    "*`;duel update <name> lineup`*\n" \
                                                    "send it with an image uploaded in the message"
                            embed_new.set_footer(text=f"Page: {x} of 1")

                        return embed_new

                    page += 1
                    if page > len(links):
                        page = 1
                    elif page < 1:
                        page = len(links) - 1

                    await msg.edit(embed=generate_embed_lineup(page))

        except TypeError:
            embed = discord.Embed(colour=discord.Colour(embed_color), title="No such duelist is found in the database")
            await ctx.channel.send(embed=embed)

    async def duel_profile_generate_image(self, bans, cores, ctx):

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
            """
            outline.text((x - 1, y - 1), text, font=font, fill=color_outline)
            outline.text((x + 1, y - 1), text, font=font, fill=color_outline)
            outline.text((x - 1, y + 1), text, font=font, fill=color_outline)
            outline.text((x + 1, y + 1), text, font=font, fill=color_outline)
            """
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
        hosting_channel = self.client.get_channel(556032841897607178)
        msg = await hosting_channel.send(file=new_photo)
        attachment_link = msg.attachments[0].url
        return attachment_link

    async def duel_profile_show_all(self, ctx):

        formatted_list = []
        find_query = {}
        project = {"_id": 0, "#": 1, "name": 1}

        for duelist in duelists.find(find_query, project).sort([("name_lower", 1)]):
            number = lengthen(duelist["#"])
            formatted_list.append(f"`{number}:` | {duelist['name']}\n")

        noun = pluralize("duelist", len(formatted_list))
        content = f"There are {len(formatted_list)} registered {noun}"
        await self.duel_profile_paginate_embeds(ctx, formatted_list, content)

    async def management_guild_show_startswith(self, ctx, args):

        formatted_list = []
        find_query = {"name_lower": {"$regex": f"^{args[2].lower()}"}}
        project = {"_id": 0, "#": 1, "name": 1}

        for duelist in duelists.find(find_query, project).sort([("name_lower", 1)]):
            number = lengthen(duelist["#"])
            formatted_list.append(f"`{number}:` | {duelist['name']}\n")

        noun = pluralize("result", len(formatted_list))
        content = f"I've got {len(formatted_list)} {noun} for duelists starting with __{args[2].lower()}__"
        await self.duel_profile_paginate_embeds(ctx, formatted_list, content)

    async def duel_profile_paginate_embeds(self, ctx, formatted_list, content):

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
                color=ctx.author.colour, title="🎌 Duel Colosseum",
                description=f"{description_new}", timestamp=get_timestamp()
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
