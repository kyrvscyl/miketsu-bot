"""
Frames Module
Miketsu, 2019
"""

import asyncio
from datetime import datetime
from math import ceil

import discord
import pytz
from discord.ext import commands

from cogs.mongo.db import get_collections
from cogs.startup import primary_id, e_j

# Collections
books = get_collections("bukkuman", "books")
frames = get_collections("miketsu", "frames")
users = get_collections("miketsu", "users")
shikigamis = get_collections("miketsu", "shikigamis")


total_sp = 0
for entry in shikigamis.find_one({"rarity": "SP"}, {"_id": 0, "shikigami.name": 1}):
    total_sp += 1

total_ssr = 0
for entry in shikigamis.find_one({"rarity": "SSR"}, {"_id": 0, "shikigami.name": 1}):
    total_ssr += 1

total_sr = 0
for entry in shikigamis.find_one({"rarity": "SR"}, {"_id": 0, "shikigami.name": 1}):
    total_sr += 1

total_r = 0
for entry in shikigamis.find_one({"rarity": "R"}, {"_id": 0, "shikigami.name": 1}):
    total_r += 1


def get_timestamp():
    return datetime.utcfromtimestamp(datetime.timestamp(datetime.now()))


def get_time():
    tz_target = pytz.timezone("America/Atikokan")
    return datetime.now(tz=tz_target)


def get_frame_thumbnail(frame):
    request = frames.find_one({"name": frame}, {"_id": 0, "link": 1})
    return request["link"]


async def frame_acquisition(user, frame_name, channel, jades):

    for result in users.aggregate([
        {
            "$match": {
                "user_id": str(user.id)
            }
        }, {
            "$unwind": {
                "path": "$achievements"
            }
        }, {
            "$project": {
                "achievements": 1
            }
        }, {
            "$match": {
                "achievements.name": frame_name
            }
        }, {
            "$count": "count"
        }
    ]):
        if result["count"] != 0:
            return

    users.update_one({
        "user_id": str(user.id)}, {
        "$push": {
            "achievements": {
                "name": frame_name,
                "date_acquired": get_time()
            }
        },
        "$inc": {
            "jades": jades
        }
    })
    embed = discord.Embed(
        color=user.colour,
        title="Frame Acquisition",
        description=f"{user.mention}, you acquired the {frame_name.title()} frame and {jades:,d}{e_j}"
    )
    embed.set_thumbnail(url=get_frame_thumbnail(frame_name.title()))
    await channel.send(embed=embed)


class Frames(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(aliases=["af"])
    @commands.is_owner()
    @commands.guild_only()
    async def achievements_add_new(self, ctx, arg1, arg2, link, *, requirement):

        profile = {
            "name": arg1.replace("_", " "),
            "requirement": requirement,
            "link": link,
            "emoji": arg2
        }
        frames.insert_one(profile)
        await ctx.message.add_reaction("✅")

    @commands.command(aliases=["frames"])
    @commands.guild_only()
    async def achievements_show_info(self, ctx):

        frames_listings = []
        for document in frames.find({}, {"_id": 0}):
            try:
                frames_listings.append([document["name"], document["requirement"], document["emoji"]])
            except KeyError:
                continue

        page = 1
        page_total = ceil(len(frames_listings) / 5)

        def check(r, u):
            return u != self.client.user and r.message.id == msg.id

        def create_new_embed_page(page_new):
            end = page_new * 5
            start = end - 5
            embed = discord.Embed(
                title="frames", colour=ctx.author.colour,
                description="collect frames based on their stated requirements\n"
                            "certain achievements are calculated every hour movement"
            )
            embed.set_footer(text=f"Page: {page_new} of {page_total}")

            while start < end:
                try:
                    embed.add_field(
                        name=f"{frames_listings[start][2]} {frames_listings[start][0]}",
                        value=f"{frames_listings[start][1]}",
                        inline=False
                    )
                    start += 1
                except IndexError:
                    break
            return embed

        msg = await ctx.channel.send(embed=create_new_embed_page(1))
        await msg.add_reaction("⬅")
        await msg.add_reaction("➡")

        while True:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=180, check=check)

                if str(reaction.emoji) == "➡":
                    page += 1
                elif str(reaction.emoji) == "⬅":
                    page -= 1

                if page == 0:
                    page = page_total
                elif page > page_total:
                    page = 1

                await msg.edit(embed=create_new_embed_page(page))
            except asyncio.TimeoutError:
                return False

    async def achievements_process_hourly(self):

        guild = self.client.get_guild(int(primary_id))
        query = users.find({}, {
            "_id": 0, "user_id": 1, "level": 1, "achievements": 1, "amulets_spent": 1, "coins": 1, "medals": 1
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

            count_sr = 0
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
                count_sr = result["count"]

            maple_evolve = []
            for result in users.aggregate([
                {
                    "$match": {
                        "user_id": "437941992748482562"
                    }
                }, {
                    "$unwind": {
                        "path": "$shikigami"
                    }
                }, {
                    "$match": {
                        "shikigami.name": {
                            "$in": [
                                "Shuten Doji", "Momiji"
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

            if document["amulets_spent"] >= 2000 and "Red Carp" not in user_frames:
                users.update_one({
                    "user_id": document["user_id"]}, {
                    "$push": {
                        "achievements": {
                            "name": "Red Carp",
                            "date_acquired": get_time()
                        }
                    },
                    "$inc": {
                        "jades": 4500
                    }
                })
                await self.achievements_process_record_user(member, "Red Carp")

            if document["level"] >= 30 and "Ubumomma" not in user_frames:
                users.update_one({
                    "user_id": document["user_id"]}, {
                    "$push": {
                        "achievements": {
                            "name": "Ubumomma",
                            "date_acquired": get_time()
                        }
                    },
                    "$inc": {
                        "jades": 1500
                    }
                })
                await self.achievements_process_record_user(member, "Ubumomma")

            if document["level"] >= 50 and "Pine of Kisaragi" not in user_frames:
                users.update_one({
                    "user_id": document["user_id"]}, {
                    "$push": {
                        "achievements": {
                            "name": "Pine of Kisaragi",
                            "date_acquired": get_time()
                        }
                    },
                    "$inc": {
                        "jades": 2500
                    }
                })
                await self.achievements_process_record_user(member, "Pine of Kisaragi")

            if document["level"] == 60 and "Cold of Mutsuki" not in user_frames:
                users.update_one({
                    "user_id": document["user_id"]}, {
                    "$push": {
                        "achievements": {
                            "name": "Cold of Mutsuki",
                            "date_acquired": get_time()
                        }
                    },
                    "$inc": {
                        "jades": 5000
                    }
                })
                await self.achievements_process_record_user(member, "Cold of Mutsuki")

            if count_sr == total_sr and "Kitsune" not in user_frames:
                users.update_one({
                    "user_id": document["user_id"]}, {
                    "$push": {
                        "achievements": {
                            "name": "Kitsune",
                            "date_acquired": get_time()
                        }
                    },
                    "$inc": {
                        "jades": 2500
                    }
                })
                await self.achievements_process_record_user(member, "Kitsune")

            if document["coins"] >= 100000000 and "Limited Gold" not in user_frames:
                users.update_one({
                    "user_id": document["user_id"]}, {
                    "$push": {
                        "achievements": {
                            "name": "Limited Gold",
                            "date_acquired": get_time()
                        }
                    },
                    "$inc": {
                        "jades": 5000
                    }
                })
                await self.achievements_process_record_user(member, "Limited Gold")

            if len(maple_evolve) == 2 and "Red Maple Frost" not in user_frames:

                if maple_evolve[0] == "True" and maple_evolve[1] == "True":
                    users.update_one({
                        "user_id": document["user_id"]}, {
                        "$push": {
                            "achievements": {
                                "name": "Red Maple Frost",
                                "date_acquired": get_time()
                            }
                        },
                        "$inc": {
                            "jades": 2500
                        }
                    })
                    await self.achievements_process_record_user(member, "Red Maple Frost")

            if document["medals"] >= 500:

                medal_achievements = [
                    ["Novice", 500],
                    ["Practitioner", 1500],
                    ["Achiever", 5000],
                    ["Magic Practitioner", 10000],
                    ["Privilege Wizard", 29000],
                    ["Wizarding Master", 40000],
                    ["The Imperishable", 100000]
                ]

                for reward in medal_achievements:
                    if document["medals"] >= reward[1] and reward[0] not in user_frames:
                        users.update_one({
                            "user_id": document["user_id"]}, {
                            "$push": {
                                "achievements": {
                                    "name": reward[0],
                                    "date_acquired": get_time()
                                }
                            },
                            "$inc": {
                                "jades": 750
                            }
                        })
                        await self.achievements_process_record_user(member, reward[0])

    async def achievements_process_weekly(self):

        request = books.find_one({"server": str(primary_id)}, {"_id": 0, "channels": 1})
        spell_spam_id = request["channels"]["spell-spam"]
        spell_spam_channel = self.client.get_channel(int(spell_spam_id))
        users.update_many({"achievements.name": "Eboshi"}, {"$pull": {"achievements.name": "Eboshi"}})

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
            await frame_acquisition(user, "Eboshi", spell_spam_channel, jades=750)
            i += 1

    async def achievements_process_daily(self):

        guild = self.client.get_guild(int(primary_id))
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
                users.update_one({
                    "user_id": document["user_id"]}, {
                    "$push": {
                        "achievements": {
                            "name": "Recalling the Past",
                            "date_acquired": get_time()
                        }
                    },
                    "$inc": {
                        "jades": 5000
                    }
                })
                await self.achievements_process_record_user(member, "Recalling the Past")

            if delta_days >= 365 and "Loyal Company" not in user_frames:
                users.update_one({
                    "user_id": document["user_id"]}, {
                    "$push": {
                        "achievements": {
                            "name": "Loyal Company",
                            "date_acquired": get_time()
                        }
                    },
                    "$inc": {
                        "jades": 10000
                    }
                })
                await self.achievements_process_record_user(member, "Loyal Company")

            if guild_1st_anniversary > date_joined and "One Year Anniversary" not in user_frames:
                users.update_one({
                    "user_id": document["user_id"]}, {
                    "$push": {
                        "achievements": {
                            "name": "One Year Anniversary",
                            "date_acquired": get_time()
                        }
                    },
                    "$inc": {
                        "jades": 3500
                    }
                })
                await self.achievements_process_record_user(member, "One Year Anniversary")

            if "Starlight Sky" in user_frames and "Blazing Sun" in user_frames and "The Sun & Moon" not in user_frames:
                users.update_one({
                    "user_id": document["user_id"]}, {
                    "$push": {
                        "achievements": {
                            "name": "The Sun & Moon",
                            "date_acquired": get_time()
                        }
                    },
                    "$inc": {
                        "jades": 5000
                    }
                })
                await self.achievements_process_record_user(member, "The Sun & Moon")

    async def achievements_process_record_user(self, member, frame_name):

        request = books.find_one({"server": str(primary_id)}, {"_id": 0, "channels.scroll-of-everything": 1})
        record_scroll_id = request["channels"]["scroll-of-everything"]
        record_scroll_channel = self.client.get_channel(int(record_scroll_id))

        embed = discord.Embed(color=0xe99ac9, timestamp=get_timestamp())
        embed.set_author(
            name=f"Added {frame_name} achievement for {member}",
            icon_url=member.avatar_url
        )
        await record_scroll_channel.send(embed=embed)
        await asyncio.sleep(2)


def setup(client):
    client.add_cog(Frames(client))
