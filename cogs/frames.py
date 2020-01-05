"""
Frames Module
Miketsu, 2020
"""

import asyncio
import os
from datetime import datetime
from math import ceil

import discord
import pytz
from PIL import Image
from discord.ext import commands

from cogs.ext.database import get_collections

# Collections
config = get_collections("config")
explores = get_collections("explores")
frames = get_collections("frames")
guilds = get_collections("guilds")
shikigamis = get_collections("shikigamis")
ships = get_collections("ships")
users = get_collections("users")

# Instantiations
id_guild = int(os.environ.get("SERVER"))


def check_if_developer_team(ctx):
    return str(ctx.author.id) in guilds.find_one({"server": str(id_guild)}, {"_id": 0, "developers": 1})["developers"]


class Frames(commands.Cog):

    def __init__(self, client):
        self.client = client

        self.colour = config.find_one({"var": 1}, {"_id": 0, "embed_color": 1})["embed_color"]
        self.timezone = config.find_one({"var": 1}, {"_id": 0, "timezone": 1})["timezone"]

        self.emojis = config.find_one({"dict": 1}, {"_id": 0, "emojis": 1})["emojis"]

        self.channels = guilds.find_one({"server": str(id_guild)}, {"_id": 0, "channels": 1})

        self.id_spell_spam = self.channels["channels"]["spell-spam"]
        self.id_hosting = self.channels["channels"]["bot-sparring"]

        self.e_j = self.emojis["j"]

        self.total_sp = shikigamis.count_documents({"rarity": "SP"})
        self.total_ssr = shikigamis.count_documents({"rarity": "SSR"})
        self.total_sr = shikigamis.count_documents({"rarity": "SR"})
        self.total_r = shikigamis.count_documents({"rarity": "R"})
        self.total_n = shikigamis.count_documents({"rarity": "N"})
        self.total_ssn = shikigamis.count_documents({"rarity": "SSN"})

        self.medal_achievements = []

        for m in frames.find({"achievement": "medals"}, {"_id": 0, "required": 1, "name": 1}):
            self.medal_achievements.append([m['name'], m['required']])

    def get_timestamp(self):
        return datetime.utcfromtimestamp(datetime.timestamp(datetime.now()))
    
    def get_time(self):
        return datetime.now(tz=pytz.timezone(self.timezone))
    
    def get_frame_thumbnail(self, frame):
        return frames.find_one({"name": frame}, {"_id": 0, "link": 1})["link"]
    
    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author.bot is True:
            return

        elif self.get_time().strftime("%b %d") != "Dec 25":
            return

        elif f"{self.client.user.id}" in message.content.lower():

            greet, match, jades = ["merry", "christmas"], 0, 3500
            for x in greet:
                if x in message.content.lower().split(" "):
                    match += 1

            if match == len(greet):
                await message.add_reaction("🎄")
                await self.achievements_process_announce(message.author, "Tree in Winter", jades)

    @commands.command(aliases=["af"])
    @commands.check(check_if_developer_team)
    @commands.guild_only()
    async def achievements_add_new(self, ctx, arg1, link, *, requirement):

        profile = {
            "name": arg1.replace("_", " "),
            "requirement": requirement,
            "link": link
        }
        frames.insert_one(profile)
        await ctx.message.add_reaction("✅")
        await self.achievements_generate_frame_images_newly()

    async def achievements_generate_frame_images_newly(self):

        frames_listings = []
        for document in frames.find({}, {"_id": 0}):
            try:
                frames_listings.append([document["name"], document["requirement"]])
            except KeyError:
                continue

        pages = ceil(len(frames_listings) / 5)
        start = ((pages - 1) * 5) + 1

        achievements_address = []
        for entry in frames_listings[start - 1:]:
            try:
                achievements_address.append(f"data/achievements/{entry[0]}.png")
            except KeyError:
                continue

        images = list(map(Image.open, achievements_address))
        new_im = Image.new("RGBA", (1000, 200))

        def get_coordinates(c):
            x = (c * 200 - (ceil(c / 5) - 1) * 1000) - 200
            y = (ceil(c / 5) * 200) - 200
            return x, y

        for index, item in enumerate(images):
            new_im.paste(images[index], (get_coordinates(index + 1)))

        address = f"temp/frames1.png"
        new_im.save(address)
        new_photo = discord.File(address, filename=f"frames1.png")
        hosting_channel = self.client.get_channel(int(self.id_hosting))
        msg = await hosting_channel.send(file=new_photo)
        attachment_link = msg.attachments[0].url

        if len(frames_listings[start - 1:]) != 1:
            config.update_one({
                "list": 1,
            }, {
                "$pop": {
                    "frames_listings": 1
                }
            })

        config.update_one({
            "list": 1,
        }, {
            "$push": {
                "frames_listings": attachment_link
            }
        })

    @commands.command(aliases=["frames"])
    @commands.guild_only()
    async def achievements_show_info(self, ctx):

        frames_listings = []
        for document in frames.find({}, {"_id": 0}):
            try:
                frames_listings.append([document["name"], document["requirement"]])
            except KeyError:
                continue

        page = 1
        page_total = ceil(len(frames_listings) / 5)

        def check(r, u):
            return u != self.client.user and r.message.id == msg.id

        async def create_new_embed_page(page_new):
            end = page_new * 5
            start = end - 5
            embed = discord.Embed(
                title="frames", colour=ctx.author.colour,
                description="collect frames based on their stated requirements\n"
                            "certain achievements are verified and issued every hour"
            )

            embed.set_footer(text=f"Page: {page_new} of {page_total}")
            embed.set_image(url=await self.get_frames_image(page_new))
            while start < end:
                try:
                    embed.add_field(
                        name=f"{frames_listings[start][0]}",
                        value=f"{frames_listings[start][1]}",
                        inline=False
                    )
                    start += 1

                except IndexError:
                    break

            return embed

        msg = await ctx.channel.send(embed=await create_new_embed_page(1))
        await msg.add_reaction("⬅")
        await msg.add_reaction("➡")

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

                await msg.edit(embed=await create_new_embed_page(page))

    async def get_frames_image(self, page_frames):
        try:
            request = config.find_one({
                "list": 1,
            }, {
                "_id": 0,
                "frames_listings": 1
            })
            return request["frames_listings"][page_frames - 1]
        except IndexError:
            return await self.achievements_generate_frame_images(page_frames)

    async def achievements_generate_frame_images(self, page_frames):

        frames_listings = []
        for document in frames.find({}, {"_id": 0}):
            try:
                frames_listings.append([document["name"], document["requirement"]])
            except KeyError:
                continue

        pages = ceil(len(frames_listings) / 5)
        end = page_frames * 5
        start = end - 5

        achievements_address = []
        for entry in frames_listings[start:end]:
            try:
                achievements_address.append(f"data/achievements/{entry[0]}.png")
            except KeyError:
                continue

        images = list(map(Image.open, achievements_address))
        new_im = Image.new("RGBA", (1000, 200))

        def get_coordinates(c):
            x = (c * 200 - (ceil(c / 5) - 1) * 1000) - 200
            y = (ceil(c / 5) * 200) - 200
            return x, y

        for index, item in enumerate(images):
            new_im.paste(images[index], (get_coordinates(index + 1)))

        address = f"temp/frames1.png"
        new_im.save(address)
        new_photo = discord.File(address, filename=f"frames1.png")
        hosting_channel = self.client.get_channel(int(self.id_hosting))
        msg = await hosting_channel.send(file=new_photo)
        attachment_link = msg.attachments[0].url

        request = config.find_one({"list": 1}, {"_id": 0, "frames_listings": 1, "frames_imaged": 1})
        pages_imaged = len(request["frames_listings"])
        total_frames_imaged = request["frames_imaged"]

        if pages == pages_imaged and total_frames_imaged != frames_listings:
            config.update_one({
                "list": 1,
            }, {
                "$pop": {
                    "frames_listings": 1
                }
            })

        config.update_one({
            "list": 1,
        }, {
            "$push": {
                "frames_listings": attachment_link
            },
            "$set": {
                "frames_imaged": ((page_frames * 5) - 1) + len(frames_listings[start:end])
            }
        })
        return attachment_link

    async def achievements_process_hourly(self):

        print("Processing hourly achievements")
        jades = 3500
        guild = self.client.get_guild(int(id_guild))
        query = users.find({}, {
            "_id": 0, "user_id": 1, "level": 1, "achievements": 1, "amulets_spent": 1, "coins": 1, "medals": 1,
            "friendship": 1, "exploration": 1
        })

        for document in query:
            member = guild.get_member(int(document["user_id"]))
            if member is None:
                continue

            user_frames = []
            for achievement in document["achievements"]:
                try:
                    user_frames.append(achievement["name"])
                except KeyError:
                    continue

            if "The Scholar" not in user_frames:
                profile = users.find_one({
                    "user_id": document["user_id"], "shikigami.name": "koi"}, {
                    "_id": 0, "shikigami.$": 1
                })

                if profile is None:
                    pass

                elif profile["shikigami"][0]["owned"] >= 100:
                    await self.achievements_process_announce(member, "The Scholar", jades)

            if "Cursed Blade" not in user_frames:
                profile = users.find_one({
                    "user_id": document["user_id"], "shikigami.name": "yoto hime"}, {
                    "_id": 0, "shikigami.$": 1
                })

                if profile is None:
                    pass

                elif profile["shikigami"][0]["evolved"] is True:
                    await self.achievements_process_announce(member, "Cursed Blade", jades)

            if "Sword Swallowing-Snake" not in user_frames:
                profile = users.find_one({
                    "user_id": document["user_id"], "shikigami.name": "orochi"}, {
                    "_id": 0, "shikigami.$": 1
                })

                if profile is None:
                    pass

                elif profile["shikigami"][0]["evolved"] is True:
                    await self.achievements_process_announce(member, "Sword Swallowing-Snake", jades)

            if "Dawn of the Thrilling Spring" not in user_frames:
                if document["friendship"] >= 1000:
                    await self.achievements_process_announce(member, "Dawn of the Thrilling Spring", jades)

            if "Genteel Women's Reflection" not in user_frames:

                request = ships.find({"level": {"$gt": 1}, "code": {"$regex": f".*{document['user_id']}.*"}})
                total_rewards = 0

                for ship in request:
                    total_rewards += ship["level"] * 25

                if total_rewards >= 1000:
                    await self.achievements_process_announce(member, "Genteel Women's Reflection", jades)

            if "Vampire Blood" not in user_frames:
                profile = users.find_one({
                    "user_id": document["user_id"], "shikigami.name": "vampira"}, {
                    "_id": 0, "shikigami.$": 1
                })

                if profile is None:
                    pass

                elif profile["shikigami"][0]["owned"] >= 30:
                    await self.achievements_process_announce(member, "Vampire Blood", jades)

            if "Taste of the Sea" not in user_frames:
                if document["amulets_spent"] >= 1000:
                    await self.achievements_process_announce(member, "Taste of the Sea", jades)

            if "Red Carp" not in user_frames:
                if document["amulets_spent"] >= 2000:
                    await self.achievements_process_announce(member, "Red Carp", jades)

            if "Ubumomma" not in user_frames:
                if document["level"] >= 30:
                    await self.achievements_process_announce(member, "Ubumomma", jades)

            if "Pine Of Kisaragi" not in user_frames:
                if document["level"] >= 50:
                    await self.achievements_process_announce(member, "Pine Of Kisaragi", jades)

            if "Cold of Mutsuki" not in user_frames:
                if document["level"] == 60:
                    await self.achievements_process_announce(member, "Cold of Mutsuki", jades)

            if "Kitsune" not in user_frames:

                count_ssn = 0
                for result in users.aggregate([
                    {
                        "$match": {
                            "user_id": str(member.id)
                        }
                    }, {
                        "$unwind": {
                            "path": "$shikigami"
                        }
                    }, {
                        "$match": {
                            "shikigami.rarity": "SR"
                        }
                    }, {
                        "$count": "count"
                    }
                ]):
                    count_ssn = result["count"]

                if count_ssn == self.total_sr:
                    await self.achievements_process_announce(member, "Kitsune", jades)

            if "Blazing Sun" not in user_frames:

                count_ssr = 0
                for result in users.aggregate([
                    {
                        "$match": {
                            "user_id": str(member.id)
                        }
                    }, {
                        "$unwind": {
                            "path": "$shikigami"
                        }
                    }, {
                        "$match": {
                            "shikigami.rarity": "SSR",
                            "shikigami.owned": {
                                "$gt": 0
                            }
                        }
                    }, {
                        "$count": "count"
                    }
                ]):
                    count_ssr = result["count"]

                if count_ssr == self.total_ssr:
                    await self.achievements_process_announce(member, "Blazing Sun", jades)
                    blazing_role = discord.utils.get(guild.roles, name="Blazing Sun")
                    await member.add_roles(blazing_role)

            if "Limited Gold" not in user_frames:
                if document["coins"] >= 70000000:
                    await self.achievements_process_announce(member, "Limited Gold", jades)

            if "Red Maple Frost" not in user_frames:

                maple_evolve = []
                for result in users.aggregate([
                    {
                        "$match": {
                            "user_id": document["user_id"]
                        }
                    }, {
                        "$unwind": {
                            "path": "$shikigami"
                        }
                    }, {
                        "$match": {
                            "shikigami.name": {
                                "$in": [
                                    "shuten doji", "momiji"
                                ]
                            }
                        }
                    }, {
                        "$project": {
                            "shikigami.name": 1,
                            "shikigami.evolved": 1
                        }
                    }
                ]):
                    maple_evolve.append(result["shikigami"]["evolved"])

                if len(maple_evolve) == 2:

                    if maple_evolve[0] is True and maple_evolve[1] is True:
                        await self.achievements_process_announce(member, "Red Maple Frost", jades)

            if "Festival of Cherries" not in user_frames:

                cherries_evolved = []
                for result in users.aggregate([
                    {
                        "$match": {
                            "user_id": document["user_id"]
                        }
                    }, {
                        "$unwind": {
                            "path": "$shikigami"
                        }
                    }, {
                        "$match": {
                            "shikigami.name": {
                                "$in": [
                                    "momo", "sakura"
                                ]
                            }
                        }
                    }, {
                        "$project": {
                            "shikigami.name": 1,
                            "shikigami.evolved": 1
                        }
                    }
                ]):
                    cherries_evolved.append(result["shikigami"]["evolved"])

                if len(cherries_evolved) == 2:

                    if cherries_evolved[0] is True and cherries_evolved[1] is True:
                        await self.achievements_process_announce(member, "Festival of Cherries", jades)

            if "Famous in Patronus" not in user_frames:
                if len(user_frames) >= 15:
                    await self.achievements_process_announce(member, "Famous in Patronus", jades)

            if document["medals"] >= 2000:

                for reward in self.medal_achievements:
                    if document["medals"] >= reward[1] and reward[0] not in user_frames:
                        await self.achievements_process_announce(member, reward[0], jades)

            if document["exploration"] >= 28:
                total_explorations = 0
                for result in explores.aggregate([
                    {
                        '$match': {
                            'user_id': document["user_id"]
                        }
                    }, {
                        '$unwind': {
                            'path': '$explores'
                        }
                    }, {
                        '$count': 'count'
                    }
                ]):
                    total_explorations = result["count"]

                exploration_achievements = [
                    ["The Scout", 50],
                    ["The Hunter", 100],
                    ["The Captain", 200]
                ]

                for reward in exploration_achievements:
                    if total_explorations >= reward[1] and reward[0] not in user_frames:
                        await self.achievements_process_announce(member, reward[0], jades)

            if "River of Moon" not in user_frames:

                count_r = 0
                for result in users.aggregate([
                    {
                        "$match": {
                            "user_id": document["user_id"]
                        }
                    }, {
                        "$unwind": {
                            "path": "$shikigami"
                        }
                    }, {
                        "$match": {
                            "shikigami.rarity": "R"
                        }
                    }, {
                        "$count": "count"
                    }
                ]):
                    count_r = result["count"]

                if count_r == self.total_r:
                    await self.achievements_process_announce(member, "River of Moon", jades)

            if "Fortune Cat" not in user_frames:

                count_n = 0
                for result in users.aggregate([
                    {
                        "$match": {
                            "user_id": document["user_id"]
                        }
                    }, {
                        "$unwind": {
                            "path": "$shikigami"
                        }
                    }, {
                        "$match": {
                            "shikigami.rarity": "N"
                        }
                    }, {
                        "$count": "count"
                    }
                ]):
                    count_n = result["count"]

                if count_n == self.total_n:
                    await self.achievements_process_announce(member, "Fortune Cat", jades)

            if "Kero-Kero" not in user_frames:

                count_ssn = 0
                for result in users.aggregate([
                    {
                        "$match": {
                            "user_id": str(member.id)
                        }
                    }, {
                        "$unwind": {
                            "path": "$shikigami"
                        }
                    }, {
                        "$match": {
                            "shikigami.rarity": "SSN",
                            "shikigami.owned": {
                                "$gt": 0
                            }
                        }
                    }, {
                        "$count": "count"
                    }
                ]):
                    count_ssn = result["count"]

                if count_ssn == self.total_ssn:
                    await self.achievements_process_announce(member, "Kero-Kero", jades)

            if "Frameous" not in user_frames:
                if len(user_frames) >= 40:
                    await self.achievements_process_announce(member, "Frameous", jades)

            if "Fortune Puppies" not in user_frames:
                levels = []
                for result in users.aggregate([
                    {
                        '$match': {
                            'user_id': document["user_id"]
                        }
                    }, {
                        '$unwind': {
                            'path': '$shikigami'
                        }
                    }, {
                        '$match': {
                            '$or': [
                                {
                                    'shikigami.name': 'ootengu'
                                }, {
                                    'shikigami.name': 'lord arakawa'
                                }, {
                                    'shikigami.name': 'aoandon'
                                }, {
                                    'shikigami.name': 'ichimokuren'
                                }, {
                                    'shikigami.name': 'susabi'
                                }, {
                                    'shikigami.name': 'higanbana'
                                }, {
                                    'shikigami.name': 'yamakaze'
                                }, {
                                    'shikigami.name': 'tamamonomae'
                                }, {
                                    'shikigami.name': 'blazing tamamonomae'
                                }, {
                                    'shikigami.name': 'miketsu'
                                }, {
                                    'shikigami.name': 'menreiki'
                                }, {
                                    'shikigami.name': 'onikiri'
                                }, {
                                    'shikigami.name': 'jr ootengu'
                                }, {
                                    'shikigami.name': 'divine miketsu'
                                }, {
                                    'shikigami.name': 'azurestorm ichimokuren'
                                }
                            ]
                        }
                    }, {
                        '$project': {
                            'shikigami.level': 1
                        }
                    }
                ]):
                    levels.append(result["shikigami"]["level"])

                if 40 in levels:
                    await self.achievements_process_announce(member, "Fortune Puppies", jades)

            if "Fortune Kitties" not in user_frames:
                levels = []
                for result in users.aggregate([
                    {
                        '$match': {
                            'user_id': document["user_id"]
                        }
                    }, {
                        '$unwind': {
                            'path': '$shikigami'
                        }
                    }, {
                        '$match': {
                            '$or': [
                                {
                                    'shikigami.name': 'shuten doji'
                                }, {
                                    'shikigami.name': 'enma'
                                }, {
                                    'shikigami.name': 'ibaraki doji'
                                }, {
                                    'shikigami.name': 'yoto hime'
                                }, {
                                    'shikigami.name': 'hana'
                                }, {
                                    'shikigami.name': 'kaguya'
                                }, {
                                    'shikigami.name': 'yuki'
                                }, {
                                    'shikigami.name': 'shiranui'
                                }, {
                                    'shikigami.name': 'shishio'
                                }, {
                                    'shikigami.name': 'inferno ibaraki doji'
                                }, {
                                    'shikigami.name': 'demoniac shuten doji'
                                }, {
                                    'shikigami.name': 'crimson yoto'
                                }, {
                                    'shikigami.name': 'vengeful hannya'
                                }, {
                                    'shikigami.name': 'hakusozu'
                                }, {
                                    'shikigami.name': 'takiyashahime'
                                }
                            ]
                        }
                    }, {
                        '$project': {
                            'shikigami.level': 1
                        }
                    }
                ]):
                    levels.append(result["shikigami"]["level"])

                if 40 in levels:
                    await self.achievements_process_announce(member, "Fortune Kitties", jades)

            if "Spring Rabbit" not in user_frames:
                profile = users.find_one({
                    "user_id": document["user_id"], "shikigami.name": "usagi"}, {
                    "_id": 0, "shikigami.$": 1
                })

                if profile is None:
                    pass

                elif profile["shikigami"][0]["evolved"] is True:
                    await self.achievements_process_announce(member, "Spring Rabbit", jades)

            if "King Of The Jungle" not in user_frames:
                profile = users.find_one({
                    "user_id": document["user_id"], "shikigami.name": "yamakaze"}, {
                    "_id": 0, "shikigami.$": 1
                })

                if profile is None:
                    pass

                elif profile["shikigami"][0]["evolved"] is True and profile["shikigami"][0]["level"] == 40:
                    await self.achievements_process_announce(member, "King Of The Jungle", jades)

            if "In The Clouds" not in user_frames:
                if document["exploration"] >= 28:
                    await self.achievements_process_announce(member, "In The Clouds", jades)

            if "The Drunken Evil" not in user_frames:
                profile = users.find_one({
                    "user_id": document["user_id"], "shikigami.name": "demoniac shuten doji"}, {
                    "_id": 0, "shikigami.$": 1
                })

                if profile is None:
                    pass

                elif profile["shikigami"][0]["level"] >= 40:
                    await self.achievements_process_announce(member, "The Drunken Evil", jades)

            if "The Nine-Tailed Foxes" not in user_frames:
                total_level = 0
                for result in users.aggregate([
                    {
                        '$match': {
                            'user_id': document["user_id"]
                        }
                    }, {
                        '$unwind': {
                            'path': '$shikigami'
                        }
                    }, {
                        '$match': {
                            '$or': [
                                {
                                    'shikigami.name': 'blazing tamamonomae'
                                }, {
                                    'shikigami.name': 'tamamonomae'
                                }
                            ]
                        }
                    }, {
                        '$project': {
                            'shikigami': 1
                        }
                    }, {
                        '$group': {
                            '_id': '',
                            'total_level': {
                                '$sum': '$shikigami.level'
                            }
                        }
                    }
                ]):
                    total_level = result["total_level"]

                if total_level == 80:
                    await self.achievements_process_announce(member, "The Nine-Tailed Foxes", jades)

            if "Spitz Puppy" not in user_frames:
                profile = users.find_one({
                    "user_id": document["user_id"], "shikigami.name": "inugami"}, {
                    "_id": 0, "shikigami.$": 1
                })

                if profile is None:
                    pass

                elif profile["shikigami"][0]["level"] >= 40:
                    await self.achievements_process_announce(member, "Spitz Puppy", jades)

            if "The Seven Masks" not in user_frames:
                profile = users.find_one({
                    "user_id": document["user_id"], "shikigami.name": "menreiki"}, {
                    "_id": 0, "shikigami.$": 1
                })

                if profile is None:
                    pass

                elif profile["shikigami"][0]["shards"] >= 40:
                    await self.achievements_process_announce(member, "The Seven Masks", jades)

            if "Hannya of the Ghoul Mask" not in user_frames:
                total_level = 0
                for result in users.aggregate([
                    {
                        '$match': {
                            'user_id': document["user_id"]
                        }
                    }, {
                        '$unwind': {
                            'path': '$shikigami'
                        }
                    }, {
                        '$match': {
                            '$or': [
                                {
                                    'shikigami.name': 'vengeful hannya'
                                }, {
                                    'shikigami.name': 'hannya'
                                }
                            ]
                        }
                    }, {
                        '$project': {
                            'shikigami': 1
                        }
                    }, {
                        '$group': {
                            '_id': '',
                            'total_level': {
                                '$sum': '$shikigami.level'
                            }
                        }
                    }
                ]):
                    total_level = result["total_level"]

                if total_level == 80:
                    await self.achievements_process_announce(member, "Hannya of the Ghoul Mask", jades)

    async def achievements_process_weekly(self):

        print("Processing weekly achievements")
        jades = 750
        users.update_many({"achievements.name": "Eboshi"}, {"$pull": {"achievements": {"name": "Eboshi"}}})

        medal_board1 = []
        query = users.find({}, {"_id": 0, "user_id": 1, "medals": 1})

        for user in query:
            try:
                medal_board1.append((user["user_id"], user["medals"]))
            except AttributeError:
                continue

        medal_board2 = sorted(medal_board1, key=lambda x: x[1], reverse=True)

        i = 0
        while i < 3:
            user = self.client.get_user(int(medal_board2[i][0]))
            if user is None:
                continue
            await self.achievements_process_announce(user, "Eboshi", jades)
            await asyncio.sleep(1)
            i += 1

    async def achievements_process_daily(self):

        print("Processing daily achievements")
        jades = 5000
        guild = self.client.get_guild(int(id_guild))
        guild_1st_anniversary = datetime.strptime("2019-Feb-01", "%Y-%b-%d")

        query = users.find({}, {
            "_id": 0, "user_id": 1, "level": 1, "achievements": 1, "amulets_spent": 1, "coins": 1, "medals": 1
        })

        for document in query:
            member = guild.get_member(int(document["user_id"]))
            if member is None:
                continue

            date_joined = member.joined_at
            delta_days = (datetime.now() - date_joined).days

            user_frames = []
            for achievement in document["achievements"]:
                try:
                    user_frames.append(achievement["name"])
                except KeyError:
                    continue

            if delta_days >= 100 and "Recalling the Past" not in user_frames:
                await self.achievements_process_announce(member, "Recalling the Past", jades)

            if delta_days >= 365 and "Loyal Company" not in user_frames:
                await self.achievements_process_announce(member, "Loyal Company", jades)

            if guild_1st_anniversary > date_joined and "One Year Anniversary" not in user_frames:
                await self.achievements_process_announce(member, "One Year Anniversary", jades)

            if "Starlight Sky" in user_frames and "Blazing Sun" in user_frames and "The Sun & Moon" not in user_frames:
                await self.achievements_process_announce(member, "The Sun & Moon", jades)

    async def achievements_process_announce(self, member, frame_name, jades):

        spell_spam_channel = self.client.get_channel(int(self.id_spell_spam))

        if users.find_one({
            "user_id": str(member.id), "achievements.name": f"{frame_name}"
        }, {
            "_id": 0, "achievements.$": 1
        }) is None:

            users.update_one({
                "user_id": str(member.id)}, {
                "$push": {
                    "achievements": {
                        "name": frame_name,
                        "date_acquired": self.get_time()
                    }
                },
                "$inc": {
                    "jades": jades
                }
            })

            intro_caption = " The "
            if frame_name[:3] == "The":
                intro_caption = " "

            embed = discord.Embed(
                color=member.colour,
                title="Frame acquisition",
                description=f"{member.mention} has obtained{intro_caption}{frame_name} frame!\n"
                            f"Acquired {jades:,d}{self.e_j} as bonus rewards!",
                timestamp=self.get_timestamp()
            )
            embed.set_footer(icon_url=member.avatar_url, text=f"{member.display_name}")
            embed.set_thumbnail(url=self.get_frame_thumbnail(frame_name))
            await spell_spam_channel.send(embed=embed)
            await asyncio.sleep(1)
        else:
            print("already have the frame")


def setup(client):
    client.add_cog(Frames(client))
