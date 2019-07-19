"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import asyncio
import os
import random
import urllib.request

import discord
from PIL import Image
from discord.ext import commands

from cogs.error import logging, get_f
from cogs.mongo.db import frames, books

file = os.path.basename(__file__)[:-3:]


primary_roles = ["Head", "Auror", "Patronus", "No-Maj"]
invalid_channels = ["auror-department", "gift-game", "pvp-fair", "duelling-room"]


castles_id = []
for document in books.find({}, {"_id": 0, "categories.castle": 1}):
    try:
        castles_id.append(document["categories"]["castle"])
    except KeyError:
        continue


def check_if_valid_and_castle(ctx):
    return str(ctx.channel.category.id) in castles_id and str(ctx.channel.name) not in invalid_channels


def get_primary_role(x):
    dictionary = {
        "Auror": "⚜",
        "Head": "🔱",
        "Patronus": "🔮",
        "No-Maj": "🔥",
    }
    return dictionary[x]


class Castle(commands.Cog):

    def __init__(self, client):
        self.client = client


    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author == self.client.user or message.author.bot:
            return

        elif message.content.lower() != "pine fresh":
            return

        elif message.channel.position != 4:
            return

        elif message.channel.position == 4 and str(message.channel.category.id) in castles_id:

            try:
                role_bathroom = discord.utils.get(message.guild.roles, name="🚿")
                await message.author.add_roles(role_bathroom)
            except discord.errors.Forbidden:
                logging(file, get_f(), "discord.errors.Forbidden")
            except discord.errors.HTTPException:
                logging(file, get_f(), "discord.errors.HTTPException")


    @commands.command()
    async def test_shuffle(self, ctx):

        await self.castle_shuffle()
        await ctx.message.delete()


    async def castle_shuffle(self):

        for entry in books.find({}, {"server": 1, "_id": 0}):
            guild = self.client.get_guild(int(entry["server"]))

            if guild is not None:
                server = books.find_one({
                    "server": str(guild.id)}, {
                    "_id": 0,
                    "categories.castle": 1,
                    "channels.duelling-room": 1,
                    "channels.gift-game": 1,
                    "channels.auror-department": 1,
                })

                try:
                    castle_id = server["categories"]["castle"]
                    gift_game_id = server["channels"]["gift-game"]
                    duelling_room_id = server["channels"]["duelling-room"]
                    auror_department_id = server["channels"]["auror-department"]
                except KeyError:
                    logging(file, get_f(), "KeyError")
                    return

                try:
                    castle_channel = self.client.get_channel(int(castle_id))
                    gift_channel = self.client.get_channel(int(gift_game_id))
                    auror_channel = self.client.get_channel(int(auror_department_id))
                    duel_channel = self.client.get_channel(int(duelling_room_id))

                    ref_num = castle_channel.text_channels[0].position
                    end_num = ref_num + len(castle_channel.text_channels) - 1

                    for channel in castle_channel.text_channels:
                        try:
                            new_floor = random.randint(ref_num, end_num)
                            await channel.edit(position=new_floor)
                            await asyncio.sleep(0.5)
                        except discord.errors.InvalidArgument:
                            logging(file, get_f(), "discord.errors.InvalidArgument")
                            continue
                        except discord.errors.Forbidden:
                            logging(file, get_f(), "discord.errors.Forbidden")
                            continue
                        except discord.errors.HTTPException:
                            logging(file, get_f(), "discord.errors.HTTPException")
                            continue

                except AttributeError:
                    logging(file, get_f(), "AttributeError")
                    return

                try:
                    await gift_channel.edit(position=end_num)
                    await auror_channel.edit(position=end_num)
                    await duel_channel.edit(position=end_num)
                    await asyncio.sleep(0.5)
                except discord.errors.InvalidArgument:
                    logging(file, get_f(), "discord.errors.InvalidArgument")
                except discord.errors.Forbidden:
                    logging(file, get_f(), "discord.errors.Forbidden")
                except discord.errors.HTTPException:
                    logging(file, get_f(), "discord.errors.HTTPException")

                await self.castle_shuffle_topic(
                    castle_id, gift_channel, auror_channel, duel_channel, ref_num, end_num
                )


    async def castle_shuffle_topic(self, castle_id, gift_channel, auror_channel, duel_channel, ref_num, end_num):

        ordinal = lambda n: "%d%s" % (n, "tsnrhtdd"[(n // 10 % 10 != 1) * (n % 10 < 4) * n % 10::4])

        try:
            castle_channel = self.client.get_channel(int(castle_id))
            castle_channels = castle_channel.text_channels
        except AttributeError:
            logging(file, get_f(), "AttributeError")
            return

        def new_floor_position(x):
            dictionary = {
                f"{ref_num + 0}": 7,
                f"{ref_num + 1}": 6,
                f"{ref_num + 2}": 5,
                f"{ref_num + 3}": 4,
                f"{ref_num + 4}": 3,
                f"{ref_num + 5}": 2,
                f"{ref_num + 6}": 1
            }
            return dictionary[str(x)]


        for channel in castle_channels:

            if channel.name not in ["auror-department", "gift-game", "duelling-room"]:
                try:
                    current_channel_topic = channel.topic[12:]
                    position = channel.position
                    new_channel_topic = f"{ordinal(new_floor_position(position))} Floor -\n{current_channel_topic}"
                    await channel.edit(topic=new_channel_topic)
                except KeyError:
                    continue
                except discord.errors.InvalidArgument:
                    logging(file, get_f(), "discord.errors.InvalidArgument")
                except discord.errors.Forbidden:
                    logging(file, get_f(), "discord.errors.Forbidden")
                except discord.errors.HTTPException:
                    logging(file, get_f(), "discord.errors.HTTPException")

            else:
                continue

        try:
            await auror_channel.edit(position=ref_num + 1)
            await gift_channel.edit(position=end_num - 1)
            await duel_channel.edit(position=end_num)
        except discord.errors.InvalidArgument:
            logging(file, get_f(), "discord.errors.InvalidArgument")
        except discord.errors.Forbidden:
            logging(file, get_f(), "discord.errors.Forbidden")
        except discord.errors.HTTPException:
            logging(file, get_f(), "discord.errors.HTTPException")


    async def reset_prefects(self):

        query = books.find({}, {"_id": 0, "server": 1, "channels.prefects-bathroom": 1})

        for result in query:
            try:
                guild_id = result["server"]
                guild = self.client.get_guild(int(guild_id))
                role_bathroom = discord.utils.get(guild.roles, name="🚿")

                if len(role_bathroom.members) == 0:
                    return

                elif len(role_bathroom.members) > 0:
                    for member in role_bathroom.members:
                        try:
                            await member.remove_roles(role_bathroom)
                        except discord.errors.Forbidden:
                            logging(file, get_f(), "discord.errors.Forbidden")
                            continue
                        except discord.errors.HTTPException:
                            logging(file, get_f(), "discord.errors.HTTPException")
                            continue

            except AttributeError:
                logging(file, get_f(), "AttributeError")
                continue


    @commands.command(aliases=["wander"])
    @commands.guild_only()
    @commands.check(check_if_valid_and_castle)
    async def castle_wander(self, ctx):

        try:
            floor_num = int(ctx.channel.topic[:1])
        except ValueError:
            logging(file, get_f(), "ValueError")
            return

        floor_frames = []
        for frame in frames.find({"floor": floor_num}):
            floor_frames.append(frame["frame"])

        try:
            random_frame = random.choice(floor_frames)
        except IndexError:
            logging(file, get_f(), "IndexError")
            return

        frame_profile = frames.find_one({"frame": random_frame}, {"_id": 0})

        try:
            find_role = frame_profile["role"]
            in_game_name = frame_profile["in_game_name"]
            image_link = frame_profile["image_link"]
            floor = frame_profile["floor"]
            frame_number = frame_profile["frame"]
            description = frame_profile["description"].replace("\\n", "\n")
        except KeyError:
            logging(file, get_f(), "KeyError")
            return

        embed = discord.Embed(
            color=ctx.author.colour,
            title=f"{get_primary_role(find_role)} {in_game_name}",
            description=description
        )
        embed.set_image(url=image_link)
        embed.set_footer(
            text=f"Floor {floor} | Frame {frame_number}"
        )
        msg = await ctx.channel.send(embed=embed)
        await msg.delete(delay=15)


    @commands.command(aliases=["frame"])
    @commands.guild_only()
    async def castle_customize_frame(self, ctx, arg1, *, args):

        argument = args.split(" ", 3)
        frame_id = str(ctx.author.id)
        member = ctx.guild.get_member(ctx.author.id)
        user_roles = member.roles
        frame_profile = frames.find_one({"frame_id": str(frame_id)}, {"_id": 0})

        try:
            in_game_name = argument[0]
            floor = int(argument[1])
            image_link = argument[2]
            description = argument[3].replace("\\n", "\n")
            frame_num = frames.count() + 1

            if image_link.lower() == "default":
                image_link = ctx.author.avatar_url

        except ValueError:
            await ctx.channel.send("Invalid floor and/or frame number")
            return
        except KeyError:
            await ctx.channel.send("Invalid argument, probably lacks inputs")
            return

        frames_current = []
        for frame in frames.find({"frame": {"$exists": True}}):
            frames_current.append(frame["frame"])

        find_role = ""
        for role in reversed(user_roles):
            if role.name in primary_roles:
                find_role = role.name
                break

        if floor not in [1, 2, 3, 4, 5, 6, 7]:
            await ctx.channel.send("Invalid floor number 1-6 only")
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
            frames.insert_one(profile)

        elif arg1.lower() == "edit" and frame_profile is not None:

            attachment_link = await self.post_process_frame(
                str(image_link), in_game_name, find_role, ctx, description, floor, frame_num
            )

            frames.update_one({"frame_id": str(ctx.author.id)}, {
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

            msg1 = await ctx.channel.send("Processing the image.. ")
            await asyncio.sleep(2)
            await msg1.edit(content="Adding fancy frames...")

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
                title=f"{get_primary_role(find_role)} {in_game_name}",
                description=description
            )
            embed.set_image(url=attachment_link)
            embed.set_footer(
                text=f"Floor {floor} | Frame {frame_num}"
            )
            await ctx.channel.send(embed=embed)
            await asyncio.sleep(2)
            await msg1.delete()

        return attachment_link


def setup(client):
    client.add_cog(Castle(client))
