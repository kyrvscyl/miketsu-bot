"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import asyncio
import random
import urllib.request

import discord
from PIL import Image
from discord.ext import commands

from cogs.mongo.db import frames, books

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

    @commands.command(aliases=["wander"])
    @commands.guild_only()
    async def castle_wander(self, ctx):

        if not str(ctx.channel.category.id) in castles_id and str(ctx.channel.name) not in invalid_channels:
            embed = discord.Embed(
                title="wander",
                colour=discord.Colour(0xffe6a7),
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
        for frame in frames.find({"floor": floor_num}):
            floor_frames.append(frame["frame"])

        try:
            random_frame = random.choice(floor_frames)
        except IndexError:
            return

        frame_profile = frames.find_one({"frame": random_frame}, {"_id": 0})
        find_role = frame_profile["role"]
        in_game_name = frame_profile["in_game_name"]
        image_link = frame_profile["image_link"] + "?width=200&height=200"
        floor = frame_profile["floor"]
        frame_number = frame_profile["frame"]
        description = frame_profile["description"].replace("\\n", "\n")

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
        await ctx.message.delete()
        await msg.delete(delay=10)

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
            embed = discord.Embed(
                colour=discord.Colour(0xffe6a7),
                title="Invalid floor number",
                description="Available floors: 1-6 only"
            )
            await ctx.channel.send(embed=embed)
            return

        frames_current = []
        for frame in frames.find({"frame": {"$exists": True}}):
            frames_current.append(frame["frame"])

        find_role = ""
        for role in reversed(user_roles):
            if role.name in primary_roles:
                find_role = role.name
                break

        if floor not in [1, 2, 3, 4, 5, 6]:
            embed = discord.Embed(
                colour=discord.Colour(0xffe6a7),
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
            embed = discord.Embed(
                colour=discord.Colour(0xffe6a7),
                title="Processing the image.. "
            )
            msg1 = await ctx.channel.send(embed=embed)
            await asyncio.sleep(2)
            embed = discord.Embed(
                colour=discord.Colour(0xffe6a7),
                title="Adding fancy frame based on your highest primary server role.."
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
