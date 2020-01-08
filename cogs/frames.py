"""
Frames Module
Miketsu, 2020
"""

import asyncio
import random
from math import ceil

from PIL import Image
from discord.ext import commands

from cogs.ext.initialize import *


class Frames(commands.Cog):

    def __init__(self, client):
        self.client = client

        self.steal_adverb = listings_1["steal_adverb"]
        self.steal_verb = listings_1["steal_verb"]
        self.steal_noun = listings_1["steal_noun"]
        self.steal_comment = listings_1["steal_comment"]

        self.total_sp = shikigamis.count_documents({"rarity": "SP"})
        self.total_ssr = shikigamis.count_documents({"rarity": "SSR"})
        self.total_sr = shikigamis.count_documents({"rarity": "SR"})
        self.total_r = shikigamis.count_documents({"rarity": "R"})
        self.total_n = shikigamis.count_documents({"rarity": "N"})
        self.total_ssn = shikigamis.count_documents({"rarity": "SSN"})

        self.medal_achievements = []

        for m in frames.find({"achievement": "medals"}, {"_id": 0, "required": 1, "name": 1}):
            self.medal_achievements.append([m['name'], m['required']])

    async def frame_automate(self):

        print("Calculating frames distribution")
        spell_spam_channel = self.client.get_channel(int(id_spell_spam))
        guild = spell_spam_channel.guild

        await self.frame_automate_starlight(guild, spell_spam_channel)
        await asyncio.sleep(1)
        await self.frame_automate_blazing(guild, spell_spam_channel)

    async def frame_automate_starlight(self, guild, spell_spam_channel):
        starlight_role = discord.utils.get(guild.roles, name="Starlight Sky")

        streak_list = []
        for user in streaks.find({}, {"_id": 0, "user_id": 1, "SSR_current": 1}):
            streak_list.append((user["user_id"], user["SSR_current"]))

        streak_list_new = sorted(streak_list, key=lambda x: x[1], reverse=True)
        starlight_new = guild.get_member(int(streak_list_new[0][0]))
        starlight_current = starlight_role.members[0]

        if len(starlight_role.members) == 0:
            await starlight_new.add_roles(starlight_role)
            await asyncio.sleep(3)

            description = \
                f"{starlight_new.mention}\"s undying luck of not summoning an SSR has " \
                f"earned themselves the Rare Starlight Sky Frame!\n\n" \
                f"🍀 No SSR streak record of {streak_list_new[0][1]} summons!"

            embed = discord.Embed(
                color=0xac330f,
                title="📨 Hall of Framers update",
                description=description,
                timestamp=get_timestamp()
            )
            embed.set_thumbnail(url="https://vignette.wikia.nocookie.net/onmyoji/images/1/17/Frame7.png")
            await spell_spam_channel.send(embed=embed)
            await frame_acquisition(starlight_new, "Starlight Sky", 2500, spell_spam_channel)

        if starlight_current == starlight_new:
            jades = 2000
            users.update_one({"user_id": str(starlight_current.id)}, {"$inc": {"jades": jades}})
            await perform_add_log("jades", jades, starlight_current.id)
            msg = f"{starlight_current.mention} has earned {jades:,d}{e_j} " \
                  f"for wielding the Starlight Sky frame for a day!"
            await spell_spam_channel.send(msg)

        else:
            await starlight_new.add_roles(starlight_role)
            await asyncio.sleep(3)
            await starlight_current.remove_roles(starlight_role)
            await asyncio.sleep(3)

            description = \
                f"{starlight_new.mention} {random.choice(self.steal_adverb)} {random.choice(self.steal_verb)} " \
                f"the Rare Starlight Sky Frame from {starlight_current.mention}\"s " \
                f"{random.choice(self.steal_noun)}!! {random.choice(self.steal_comment)}\n\n" \
                f"🍀 No SSR streak record of {streak_list_new[0][1]} summons! " \
                f"Cuts in three fourths every reset!"

            embed = discord.Embed(
                color=0xac330f,
                title="📨 Hall of Framers update",
                description=description,
                timestamp=get_timestamp()
            )
            embed.set_thumbnail(url="https://vignette.wikia.nocookie.net/onmyoji/images/1/17/Frame7.png")
            await spell_spam_channel.send(embed=embed)
            await frame_acquisition(starlight_new, "Starlight Sky", 2500, spell_spam_channel)

    async def frame_automate_blazing(self, guild, spell_spam_channel):

        blazing_role = discord.utils.get(guild.roles, name="Blazing Sun")
        blazing_users = []

        for member in blazing_role.members:
            blazing_users.append(f"{member.display_name}")

            users.update_one({
                "user_id": str(member.id)
            }, {
                "$inc": {
                    "amulets": 10
                }
            })
            await perform_add_log("amulets", 10, member.id)

        embed = discord.Embed(
            title="Blazing Sun Frame Update",
            description=f"completed the SSR shikigami collection\n"
                        f"earns 10{e_a} every reset",
            color=colour,
            timestamp=get_timestamp()
        )
        embed.add_field(
            name="Frame Wielders",
            value=f"{', '.join(blazing_users)}"
        )
        embed.set_thumbnail(url=get_frame_thumbnail("Blazing Sun"))
        await spell_spam_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author.bot is True:
            return

        elif get_time().strftime("%b %d") != "Dec 25":
            return

        elif f"{self.client.user.id}" in message.content.lower():

            greet, match, jades = ["merry", "christmas"], 0, 3500
            for x in greet:
                if x in message.content.lower().split(" "):
                    match += 1

            if match == len(greet):
                await message.add_reaction("🎄")
                spell_spam_channel = self.client.get_channel(int(id_spell_spam))
                await frame_acquisition(message.author, "Tree in Winter", jades, spell_spam_channel)

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
        await process_msg_reaction_add(ctx.message, "✅")
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
        hosting_channel = self.client.get_channel(int(id_hosting))
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

        async def embed_new_create(page_new):
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

        msg = await ctx.channel.send(embed=await embed_new_create(1))
        emoji_arrows = ["⬅", "➡"]
        for emoji in emoji_arrows:
            await process_msg_reaction_add(msg, emoji)

        while True:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=180, check=check)
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

                await msg.edit(embed=await embed_new_create(page))

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
        hosting_channel = self.client.get_channel(int(id_hosting))
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

        spell_spam_channel = self.client.get_channel(int(id_spell_spam))

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
                        "date_acquired": get_time()
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
                            f"Acquired {jades:,d}{e_j} as bonus rewards!",
                timestamp=get_timestamp()
            )
            embed.set_footer(icon_url=member.avatar_url, text=f"{member.display_name}")
            embed.set_thumbnail(url=get_frame_thumbnail(frame_name))
            await spell_spam_channel.send(embed=embed)
            await asyncio.sleep(1)
        else:
            print("already have the frame")


def setup(client):
    client.add_cog(Frames(client))
