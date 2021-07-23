"""
Frames Module
"Miketsu, 2021
"""

from PIL import Image
from discord.ext import commands

from cogs.ext.initialize import *


class Frames(commands.Cog):

    def __init__(self, client):

        self.client = client
        self.prefix = self.client.command_prefix

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
        
        self.dog_loving = [
            "ootengu", "lord arakawa", "aoandon", "ichimokuren", "susabi", "higanbana", "yamakaze", "tamamonomae",
            "blazing tamamonomae", "miketsu", "menreiki", "onikiri", "jr ootengu", "divine miketsu", 
            "azurestorm ichimokuren"
        ]
        self.cat_loving = [
            "shuten doji", "enma", "ibaraki doji", "yoto hime", "hana", "kaguya", "yuki", "shiranui", "shishio",
            "inferno ibaraki doji", "demoniac shuten doji", "crimson yoto", "vengeful hannya", "hakusozu",
            "takiyashahime"
        ]

        self.medal_achievements = []
        self.boss_damage_achievements = []

        for m in frames.find({"achievement": "medals"}, {"_id": 0, "required": 1, "name": 1}).sort([("required", 1)]):
            self.medal_achievements.append([m['name'], m['required']])

        for b in frames.find({
            "achievement": "boss_damage"}, {
            "_id": 0, "required": 1, "name": 1
        }).sort([("required", 1)]):
            self.boss_damage_achievements.append([b['name'], b['required']])

    def get_coordinates(self, c):
        return (c * 200 - (ceil(c / 5) - 1) * 1000) - 200, (ceil(c / 5) * 200) - 200

    async def frames_automate(self):

        spell_spam_channel = self.client.get_channel(int(id_spell_spam))
        guild = self.client.get_guild(int(id_guild))

        await self.frames_automate_starlight(guild, spell_spam_channel)
        await asyncio.sleep(1)
        await self.frames_automate_blazing(guild, spell_spam_channel)

    async def frames_automate_starlight(self, guild, channel):

        frame_name, listings = "Starlight Sky", []
        role = discord.utils.get(guild.roles, name=frame_name)

        for member in streaks.find({}, {"_id": 0}).sort([("SSR_current", -1)]).limit(2):
            listings.append(member)

        role_new = guild.get_member(int(listings[0]["user_id"]))
        role_current = role.members[0]

        if len(role.members) == 0:

            await process_role_add(role_new, role)
            await asyncio.sleep(3)

            description = \
                f"{role_new.mention}\"s undying luck of not summoning an SSR has " \
                f"earned themselves the Rare {frame_name} Frame!\n\n" \
                f"🍀 No SSR streak record of {listings[0]['SSR_record']} summons!"

            embed = discord.Embed(
                color=0xac330f, description=description, timestamp=get_timestamp(), title="📨 Hall of Framers update",
            )
            embed.set_thumbnail(url=get_frame_thumbnail(frame_name))
            await process_msg_submit(channel, None, embed)
            await frame_acquisition(role_new, frame_name, 2500, channel)

        elif role_current == role_new:

            jades = 2000
            users.update_one({"user_id": str(role_current.id)}, {"$inc": {"jades": jades}})
            await perform_add_log("jades", jades, role_current.id)
            msg = f"{role_current.mention} has earned {jades:,d}{e_j} for wielding the Starlight Sky frame for a day!"
            await process_msg_submit(channel, msg, None)

        else:
            await process_role_add(role_new, role)
            await asyncio.sleep(1)
            await process_role_remove(role_current, role)
            await asyncio.sleep(1)

            adverb, verb = random.choice(self.steal_adverb), random.choice(self.steal_verb)
            noun, comment = random.choice(self.steal_noun), random.choice(self.steal_comment)

            description = \
                f"{role_new.mention} {adverb} {verb} the Rare {frame_name} Frame from {role_current.mention}\"s " \
                f"{noun}!! {comment}\n\n🍀 No SSR streak record of {listings[0]['SSR_record']} summons! " \
                f"Cuts in three fourths every reset!"

            embed = discord.Embed(
                color=0xac330f, title="📨 Hall of Framers update", description=description, timestamp=get_timestamp()
            )
            embed.set_thumbnail(url=get_frame_thumbnail(frame_name))
            await process_msg_submit(channel, None, embed)
            await frame_acquisition(role_new, frame_name, 2500, channel)

    async def frames_automate_blazing(self, guild, channel):

        frame_name, listings = "Blazing Sun", []
        role = discord.utils.get(guild.roles, name=frame_name)

        for member in role.members:
            listings.append(member.name)
            users.update_one({"user_id": str(member.id)}, {"$inc": {"amulets": 10}})
            await perform_add_log("amulets", 10, member.id)

        embed = discord.Embed(
            title=f"{frame_name} Frames", color=colour, timestamp=get_timestamp(),
            description=f"completed the SSR shikigami collection\nearns 10{e_a} every reset",
        )
        embed.add_field(name="Frame Wielders", value=f"{', '.join(listings)}")
        embed.set_thumbnail(url=get_frame_thumbnail(frame_name))
        await process_msg_submit(channel, None, embed)

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
    @commands.guild_only()
    @commands.check(check_if_user_has_development_role)
    async def frames_add_new(self, ctx, arg1, link, *, requirement):

        frames.insert_one({
            "name": arg1.replace("_", " ").title(),
            "requirement": requirement,
            "link": link
        })
        await process_msg_reaction_add(ctx.message, "✅")
        await self.frames_add_new_generate_image()

    async def frames_add_new_generate_image(self):

        listings_frames = []
        for document in frames.find({}, {"_id": 0}):
            try:
                listings_frames.append([document["name"], document["requirement"]])
            except KeyError:
                continue

        pages = ceil(len(listings_frames) / 5)
        start = ((pages - 1) * 5) + 1

        achievements_address = []
        for entry in listings_frames[start - 1:]:
            try:
                achievements_address.append(f"data/achievements/{entry[0]}.png")
            except KeyError:
                continue

        images = list(map(Image.open, achievements_address))
        new_im = Image.new("RGBA", (1000, 200))

        for index, item in enumerate(images):
            new_im.paste(images[index], (self.get_coordinates(index + 1)))

        address = f"temp/frames.png"
        new_im.save(address)
        image_file = discord.File(address, filename=f"frames.png")
        hosting_channel = self.client.get_channel(int(id_hosting))
        msg = await process_msg_submit_file(hosting_channel, image_file)
        attachment_link = msg.attachments[0].url

        if len(listings_frames[start - 1:]) != 1:
            config.update_one({"list": 1}, {"$pop": {"frames_listings": 1}})

        config.update_one({"list": 1}, {"$push": {"frames_listings": attachment_link}})

    @commands.command(aliases=["frames"])
    @commands.guild_only()
    async def frames_show_information(self, ctx):

        frames_listings = []
        for document in frames.find({}, {"_id": 0}):
            try:
                frames_listings.append([document["name"], document["requirement"]])
            except KeyError:
                continue

        page = 1
        page_total = ceil(len(frames_listings) / 5)

        async def embed_new_create(page_new):
            end = page_new * 5
            start = end - 5
            embed_new = discord.Embed(
                title="frames", colour=ctx.author.colour,
                description="collect frames based on their stated requirements\n"
                            "certain achievements are verified and issued every hour"
            )

            embed_new.set_footer(text=f"Page: {page_new} of {page_total}")
            embed_new.set_image(url=await self.frames_show_images_get(page_new))
            while start < end:
                try:
                    embed_new.add_field(
                        name=f"{frames_listings[start][0]}", value=f"{frames_listings[start][1]}", inline=False
                    )
                    start += 1

                except IndexError:
                    break

            return embed_new

        msg = await process_msg_submit(ctx.channel, None, await embed_new_create(1))

        emojis_add = ["⬅", "➡"]
        for emoji in emojis_add:
            await process_msg_reaction_add(msg, emoji)

        def check(r, u):
            return u != self.client.user and msg.id == r.message.id and str(r.emoji) in emojis_add

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

                await process_msg_edit(msg, None, await embed_new_create(page))
                await process_msg_reaction_remove(msg, str(reaction.emoji), user)

    async def frames_show_images_get(self, page_frames):

        query = config.find_one({"list": 1}, {"_id": 0, "frames_listings": 1})

        try:
            return query["frames_listings"][page_frames - 1]
        except IndexError:
            return await self.frames_show_images_generate(page_frames)

    async def frames_show_images_generate(self, page_frames):

        listings_frames = []
        for document in frames.find({}, {"_id": 0}):
            try:
                listings_frames.append([document["name"], document["requirement"]])
            except KeyError:
                continue

        pages = ceil(len(listings_frames) / 5)
        end = page_frames * 5
        start = end - 5

        listings_address = []
        for entry in listings_frames[start:end]:
            try:
                listings_address.append(f"data/achievements/{entry[0]}.png")
            except KeyError:
                continue

        images = list(map(Image.open, listings_address))
        new_im = Image.new("RGBA", (1000, 200))

        for index, item in enumerate(images):
            new_im.paste(images[index], (self.get_coordinates(index + 1)))

        address = f"temp/frames.png"
        new_im.save(address)
        image_file = discord.File(address, filename=f"frames.png")
        hosting_channel = self.client.get_channel(int(id_hosting))
        msg = await process_msg_submit_file(hosting_channel, image_file)
        link_file = msg.attachments[0].url

        query = config.find_one({"list": 1}, {"_id": 0, "frames_listings": 1, "frames_imaged": 1})
        pages_imaged = len(query["frames_listings"])
        total_frames_imaged = query["frames_imaged"]
        count = ((page_frames * 5) - 1) + len(listings_frames[start:end])

        if pages == pages_imaged and total_frames_imaged != listings_frames:
            config.update_one({"list": 1}, {"$pop": {"frames_listings": 1}})

        config.update_one({"list": 1}, {"$push": {"frames_listings": link_file}, "$set": {"frames_imaged": count}})
        return link_file

    async def frames_automate_hourly(self):

        print("Processing hourly achievements")
        jades = 3500
        guild = self.client.get_guild(int(id_guild))
        guild_owner_id = guild.owner.id

        for document in users.find({}, {
            "_id": 0, "user_id": 1, "level": 1, "achievements": 1, "amulets_spent": 1, "coins": 1, "medals": 1,
            "friendship": 1, "exploration": 1, "achievements_count": 1, "boss_damage": 1,
            "raid_failures": 1, "raid_successes": 1
        }):
            member = guild.get_member(int(document["user_id"]))
            if member is None:
                continue

            user_frames = []
            for achievement in document["achievements"]:
                user_frames.append(achievement["name"])

            frame_name = "The Scholar"
            if frame_name not in user_frames:
                profile = users.find_one({
                    "user_id": str(member.id), "shikigami.name": "koi"}, {
                    "_id": 0, "shikigami.$": 1
                })
                if profile is None:
                    pass

                elif profile["shikigami"][0]["owned"] >= 100:
                    await self.frames_automate_announcement(member, frame_name, jades)

            frame_name = "Cursed Blade"
            if frame_name not in user_frames:
                profile = users.find_one({
                    "user_id": str(member.id), "shikigami.name": "yoto hime"}, {
                    "_id": 0, "shikigami.$": 1
                })
                if profile is None:
                    pass

                elif profile["shikigami"][0]["evolved"] is True:
                    await self.frames_automate_announcement(member, frame_name, jades)

            frame_name = "Sword Swallowing-Snake"
            if frame_name not in user_frames:
                profile = users.find_one({
                    "user_id": str(member.id), "shikigami.name": "orochi"}, {
                    "_id": 0, "shikigami.$": 1
                })
                if profile is None:
                    pass

                elif profile["shikigami"][0]["evolved"] is True:
                    await self.frames_automate_announcement(member, frame_name, jades)

            frame_name = "Dawn of the Thrilling Spring"
            if frame_name not in user_frames:
                if document["friendship"] >= 1000:
                    await self.frames_automate_announcement(member, frame_name, jades)

            frame_name = "Genteel Women's Reflection"
            if frame_name not in user_frames:
                total_rewards = 0
                for ship in ships.find({"level": {"$gt": 1}, "code": {"$regex": f".*{str(member.id)}.*"}}):
                    total_rewards += ship["level"] * 25

                if total_rewards >= 1000:
                    await self.frames_automate_announcement(member, frame_name, jades)

            frame_name = "Vampire Blood"
            if frame_name not in user_frames:
                profile = users.find_one({
                    "user_id": str(member.id), "shikigami.name": "vampira"}, {
                    "_id": 0, "shikigami.$": 1
                })
                if profile is None:
                    pass

                elif profile["shikigami"][0]["owned"] >= 30:
                    await self.frames_automate_announcement(member, frame_name, jades)

            frame_name = "Taste of the Sea"
            if frame_name not in user_frames:
                if document["amulets_spent"] >= 1000:
                    await self.frames_automate_announcement(member, frame_name, jades)

            frame_name = "Red Carp"
            if frame_name not in user_frames:
                if document["amulets_spent"] >= 2000:
                    await self.frames_automate_announcement(member, frame_name, jades)

            frame_name = "Ubumomma"
            if frame_name not in user_frames:
                if document["level"] >= 30:
                    await self.frames_automate_announcement(member, frame_name, jades)

            frame_name = "Pine Of Kisaragi"
            if frame_name not in user_frames:
                if document["level"] >= 50:
                    await self.frames_automate_announcement(member, frame_name, jades)

            frame_name = "Cold of Mutsuki"
            if frame_name not in user_frames:
                if document["level"] == 60:
                    await self.frames_automate_announcement(member, frame_name, jades)

            frame_name = "Kitsune"
            if frame_name not in user_frames:
                count_sr = 0
                for result in users.aggregate([{
                    "$match": {"user_id": str(member.id)}}, {
                    "$unwind": {"path": "$shikigami"}}, {
                    "$match": {"shikigami.rarity": "SR", "shikigami.owned": {"$gt": 0}}}, {
                    "$count": "count"
                }]):
                    count_sr = result["count"]

                if count_sr == self.total_sr:
                    await self.frames_automate_announcement(member, frame_name, jades)

            frame_name = "Blazing Sun"
            if frame_name not in user_frames:
                count_ssr = 0
                for result in users.aggregate([{
                    "$match": {"user_id": str(member.id)}}, {
                    "$unwind": {"path": "$shikigami"}}, {
                    "$match": {"shikigami.rarity": "SSR", "shikigami.owned": {"$gt": 0}}}, {
                    "$count": "count"
                }]):
                    count_ssr = result["count"]

                if count_ssr == self.total_ssr:
                    await self.frames_automate_announcement(member, frame_name, jades)
                    await process_role_add(member, discord.utils.get(guild.roles, name=frame_name))

            frame_name = "Limited Gold"
            if frame_name not in user_frames:
                if document["coins"] >= 70000000:
                    await self.frames_automate_announcement(member, frame_name, jades)

            frame_name = "Red Maple Frost"
            if frame_name not in user_frames:
                maple_evolve = []
                for result in users.aggregate([{
                    "$match": {"user_id": str(member.id)}}, {
                    "$unwind": {"path": "$shikigami"}}, {
                    "$match": {"shikigami.name": {"$in": ["shuten doji", "momiji"]}}}, {
                    "$project": {"shikigami.name": 1, "shikigami.evolved": 1}
                }]):
                    maple_evolve.append(result["shikigami"]["evolved"])

                if len(maple_evolve) == 2:
                    if maple_evolve[0] is True and maple_evolve[1] is True:
                        await self.frames_automate_announcement(member, frame_name, jades)

            frame_name = "Festival of Cherries"
            if frame_name not in user_frames:
                cherries_evolved = []
                for result in users.aggregate([{
                    "$match": {"user_id": str(member.id)}}, {
                    "$unwind": {"path": "$shikigami"}}, {
                    "$match": {"shikigami.name": {"$in": ["momo", "sakura"]}}}, {
                    "$project": {"shikigami.name": 1, "shikigami.evolved": 1}
                }]):
                    cherries_evolved.append(result["shikigami"]["evolved"])

                if len(cherries_evolved) == 2:
                    if cherries_evolved[0] is True and cherries_evolved[1] is True:
                        await self.frames_automate_announcement(member, frame_name, jades)

            frame_name = "Famous in Patronus"
            if frame_name not in user_frames:
                if len(user_frames) >= 15:
                    await self.frames_automate_announcement(member, frame_name, jades)

            if document["medals"] >= 2000:
                for reward in self.medal_achievements:
                    if document["medals"] >= reward[1] and reward[0] not in user_frames:
                        await self.frames_automate_announcement(member, reward[0], jades)

            if document["exploration"] >= 28:
                total_explorations = 0
                for result in explores.aggregate([{
                    "$match": {"user_id": str(member.id)}}, {
                    "$unwind": {"path": "$explores"}}, {
                    "$count": "count"
                }]):
                    total_explorations = result["count"]

                exploration_achievements = [["The Scout", 50], ["The Hunter", 100], ["The Captain", 200]]
                for reward in exploration_achievements:
                    if total_explorations >= reward[1] and reward[0] not in user_frames:
                        await self.frames_automate_announcement(member, reward[0], jades)

            frame_name = "River of Moon"
            if frame_name not in user_frames:
                count_r = 0
                for result in users.aggregate([{
                    "$match": {"user_id": str(member.id)}}, {
                    "$unwind": {"path": "$shikigami"}}, {
                    "$match": {"shikigami.rarity": "R"}}, {
                    "$count": "count"
                }]):
                    count_r = result["count"]

                if count_r == self.total_r:
                    await self.frames_automate_announcement(member, frame_name, jades)

            frame_name = "Fortune Cat"
            if frame_name not in user_frames:
                count_n = 0
                for result in users.aggregate([{
                    "$match": {"user_id": str(member.id)}}, {
                    "$unwind": {"path": "$shikigami"}}, {
                    "$match": {"shikigami.rarity": "N"}}, {
                    "$count": "count"
                }]):
                    count_n = result["count"]

                if count_n == self.total_n:
                    await self.frames_automate_announcement(member, frame_name, jades)

            frame_name = "Kero-Kero"
            if frame_name not in user_frames:
                count_ssn = 0
                for result in users.aggregate([{
                    "$match": {"user_id": str(member.id)}}, {
                    "$unwind": {"path": "$shikigami"}}, {
                    "$match": {"shikigami.rarity": "SSN", "shikigami.owned": {"$gt": 0}}}, {
                    "$count": "count"}
                ]):
                    count_ssn = result["count"]

                if count_ssn == self.total_ssn:
                    await self.frames_automate_announcement(member, frame_name, jades)

            frame_name = "Frameous"
            if frame_name not in user_frames:
                if len(user_frames) >= 40:
                    await self.frames_automate_announcement(member, frame_name, jades)

            frame_name = "Fortune Puppies"
            if frame_name not in user_frames:
                levels = []
                for result in users.aggregate([{
                    "$match": {"user_id": str(member.id)}}, {
                    "$unwind": {"path": "$shikigami"}}, {
                    "$match": {"$or": [{"shikigami.name": {"$in": self.dog_loving}}]}}, {
                    "$project": {"shikigami.level": 1}
                }]):
                    levels.append(result["shikigami"]["level"])

                if 40 in levels:
                    await self.frames_automate_announcement(member, frame_name, jades)

            frame_name = "Fortune Kitties"
            if frame_name not in user_frames:
                levels = []
                for result in users.aggregate([{
                    "$match": {"user_id": str(member.id)}}, {
                    "$unwind": {"path": "$shikigami"}}, {
                    "$match": {"$or": [{"shikigami.name": {"$in": self.cat_loving}}]}}, {
                    "$project": {"shikigami.level": 1}
                }]):
                    levels.append(result["shikigami"]["level"])

                if 40 in levels:
                    await self.frames_automate_announcement(member, frame_name, jades)

            frame_name = "Spring Rabbit"
            if frame_name not in user_frames:
                profile = users.find_one({
                    "user_id": str(member.id), "shikigami.name": "usagi"}, {
                    "_id": 0, "shikigami.$": 1
                })
                if profile is None:
                    pass

                elif profile["shikigami"][0]["evolved"] is True:
                    await self.frames_automate_announcement(member, frame_name, jades)

            frame_name = "King Of The Jungle"
            if frame_name not in user_frames:
                profile = users.find_one({
                    "user_id": str(member.id), "shikigami.name": "yamakaze"}, {
                    "_id": 0, "shikigami.$": 1
                })
                if profile is None:
                    pass

                elif profile["shikigami"][0]["evolved"] is True and profile["shikigami"][0]["level"] == 40:
                    await self.frames_automate_announcement(member, frame_name, jades)

            frame_name = "In The Clouds"
            if frame_name not in user_frames:
                if document["exploration"] >= 28:
                    await self.frames_automate_announcement(member, frame_name, jades)

            frame_name = "The Drunken Evil"
            if frame_name not in user_frames:
                profile = users.find_one({
                    "user_id": str(member.id), "shikigami.name": "demoniac shuten doji"}, {
                    "_id": 0, "shikigami.$": 1
                })
                if profile is None:
                    pass

                elif profile["shikigami"][0]["level"] >= 40:
                    await self.frames_automate_announcement(member, frame_name, jades)

            frame_name = "The Nine-Tailed Foxes"
            if frame_name not in user_frames:
                total_level = 0
                for result in users.aggregate([{
                    "$match": {"user_id": str(member.id)}}, {
                    "$unwind": {"path": "$shikigami"}}, {
                    "$match": {"$or": [{"shikigami.name": {"$in": ["blazing tamamonomae", "tamamonomae"]}}]}}, {
                    "$project": {"shikigami": 1}}, {
                    "$group": {"_id": "", "total_level": {"$sum": "$shikigami.level"}}
                }]):
                    total_level = result["total_level"]

                if total_level == 80:
                    await self.frames_automate_announcement(member, frame_name, jades)

            frame_name = "Spitz Puppy"
            if frame_name not in user_frames:
                profile = users.find_one({
                    "user_id": str(member.id), "shikigami.name": "inugami"}, {
                    "_id": 0, "shikigami.$": 1
                })
                if profile is None:
                    pass

                elif profile["shikigami"][0]["level"] >= 40:
                    await self.frames_automate_announcement(member, frame_name, jades)

            frame_name = "The Seven Masks"
            if frame_name not in user_frames:
                profile = users.find_one({
                    "user_id": str(member.id), "shikigami.name": "menreiki"}, {
                    "_id": 0, "shikigami.$": 1
                })
                if profile is None:
                    pass

                elif profile["shikigami"][0]["shards"] >= 40:
                    await self.frames_automate_announcement(member, frame_name, jades)

            frame_name = "Hannya of the Ghoul Mask"
            if frame_name not in user_frames:
                total_level = 0
                for result in users.aggregate([{
                    "$match": {"user_id": str(member.id)}}, {
                    "$unwind": {"path": "$shikigami"}}, {
                    "$match": {"$or": [{"shikigami.name": {"$in": ["vengeful hannya", "hannya"]}}]}}, {
                    "$project": {"shikigami": 1}}, {
                    "$group": {"_id": "", "total_level": {"$sum": "$shikigami.level"}}
                }]):
                    total_level = result["total_level"]

                if total_level == 80:
                    await self.frames_automate_announcement(member, frame_name, jades)

            frame_name = "Moonlight Shell"
            if frame_name not in user_frames:
                for x in users.aggregate([{
                    '$match': {'user_id': str(member.id)}}, {
                    '$project': {'souls': {'$objectToArray': '$souls'}, 'user_id': 1}}, {
                    '$unwind': {'path': '$souls'}}
                ]):
                    if len(x['souls']['v']) == 6:
                        total_grade = 0
                        for y in x['souls']['v']:
                            if y['grade'] == 6:
                                total_grade += 6
                        if total_grade == 36:
                            await self.frames_automate_announcement(member, frame_name, jades)
                            break

            frame_name = "Auspicious Dragon Chant"
            if frame_name not in user_frames:
                eq_1, eq_2 = "$souls.stage", "$souls.clears"

                for x in explores.aggregate([{
                    '$match': {'user_id': str(member.id)}}, {
                    '$project': {'souls': 1}}, {
                    '$unwind': {'path': '$souls'}}, {
                    '$group': {
                        "_id": None,
                        f'10_clear': {"$sum": {"$cond": [{"$and": [{"$eq": [eq_1, 10]}, {"$eq": [eq_2, 3]}]}, 1, 0]}}
                    }}
                ]):
                    if x["10_clear"] >= 1000:
                        await self.frames_automate_announcement(member, frame_name, jades)
                        break

            frame_name = "Master Of Patronus"
            if frame_name not in user_frames:
                if str(guild_owner_id) == str(member.id):
                    await self.frames_automate_announcement(member, frame_name, jades)

            if document["boss_damage"] >= 250000:
                for reward in self.medal_achievements:
                    if document["boss_damage"] >= reward[1] and reward[0] not in user_frames:
                        await self.frames_automate_announcement(member, reward[0], jades)

            frame_name = "Water's Exquisitiveness"
            if frame_name not in user_frames:
                for x in users.aggregate([{
                    '$match': {'user_id': str(member.id)}}, {
                    '$unwind': {'path': '$shikigami'}}, {
                    '$match': {'shikigami.level': 40}}, {
                    '$count': 'count'}
                ]):
                    if x['count'] >= 20:
                        await self.frames_automate_announcement(member, frame_name, jades)

            frame_name = "The 365"
            if frame_name not in user_frames:
                if document["raid_successes"] - document["raid_failures"] >= 365:
                    await self.frames_automate_announcement(member, frame_name, jades)

            frame_name = "Phoenix Fire"
            if frame_name not in user_frames:
                count_sp = 0
                for result in users.aggregate([{
                    "$match": {"user_id": str(member.id)}}, {
                    "$unwind": {"path": "$shikigami"}}, {
                    "$match": {"shikigami.rarity": "SP", "shikigami.owned": {"$gt": 0}}}, {
                    "$count": "count"
                }]):
                    count_sp = result["count"]

                if count_sp == self.total_sp:
                    await self.frames_automate_announcement(member, frame_name, jades)

            frame_name = "Evergreen Vine"
            if frame_name not in user_frames:
                soul_set_total = 0
                for x in users.aggregate([{
                    '$match': {'user_id': str(member.id)}}, {
                    '$project': {'souls': {'$objectToArray': '$souls'}, 'user_id': 1}}, {
                    '$unwind': {'path': '$souls'}}
                ]):
                    if len(x['souls']['v']) == 6:
                        total_grade = 0
                        for y in x['souls']['v']:
                            if y['grade'] == 6:
                                total_grade += 6
                        if total_grade == 36:
                            soul_set_total += 1

                if soul_set_total == 12:
                    await self.frames_automate_announcement(member, frame_name, jades)

    async def frames_automate_weekly(self):

        frame_name, jades, listings, i = "Eboshi", 750, [], 0
        users.update_many({"achievements.name": frame_name}, {"$pull": {"achievements": {"name": frame_name}}})

        for member in users.find({}, {"_id": 0, "user_id": 1, "medals": 1}):
            listings.append((member["user_id"], member["medals"]))

        listings_sorted = sorted(listings, key=lambda x: x[1], reverse=True)

        while i < 3:
            member = self.client.get_user(int(listings_sorted[i][0]))
            if member is not None:
                await self.frames_automate_announcement(member, frame_name, jades)
                await asyncio.sleep(0.5)
            i += 1

    async def frames_automate_daily(self):

        jades = 5000
        guild = self.client.get_guild(int(id_guild))
        guild_1st_anniversary = datetime.strptime("2019-Feb-01", "%Y-%b-%d")

        for document in users.find({}, {
            "_id": 0, "user_id": 1, "level": 1, "achievements": 1, "amulets_spent": 1, "coins": 1, "medals": 1
        }):
            member = guild.get_member(int(document["user_id"]))
            if member is None:
                continue

            date_joined = member.joined_at
            delta_days = (datetime.now() - date_joined).days

            user_frames = []
            for achievement in document["achievements"]:
                user_frames.append(achievement["name"])

            frame_name = "Recalling the Past"
            if delta_days >= 100 and frame_name not in user_frames:
                await self.frames_automate_announcement(member, frame_name, jades)

            frame_name = "Loyal Company"
            if delta_days >= 365 and frame_name not in user_frames:
                await self.frames_automate_announcement(member, frame_name, jades)

            frame_name = "One Year Anniversary"
            if guild_1st_anniversary > date_joined and frame_name not in user_frames:
                await self.frames_automate_announcement(member, frame_name, jades)

            frame_name = "The Sun & Moon"
            if "Starlight Sky" in user_frames and "Blazing Sun" in user_frames and "The Sun & Moon" not in user_frames:
                await self.frames_automate_announcement(member, frame_name, jades)

    async def frames_automate_announcement(self, member, frame_name, jades):

        spell_spam_channel = self.client.get_channel(int(id_spell_spam))

        if users.find_one({
            "user_id": str(member.id), "achievements.name": f"{frame_name}"}, {
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
                    "jades": jades,
                    "achievements_count": 1
                }
            })

            intro_caption = " The "
            if frame_name[:3] == "The":
                intro_caption = " "

            embed = discord.Embed(
                color=member.colour, title="Frame acquisition", timestamp=get_timestamp(),
                description=f"{member.mention} has obtained{intro_caption}{frame_name} frame!\n"
                            f"Acquired {jades:,d}{e_j} as bonus rewards!",
            )
            embed.set_footer(icon_url=member.default_avatar_url, text=f"{member.display_name}")
            embed.set_thumbnail(url=get_frame_thumbnail(frame_name))
            await perform_add_log("jades", jades, member.id)
            await process_msg_submit(spell_spam_channel, None, embed)
            await asyncio.sleep(1)


def setup(client):
    client.add_cog(Frames(client))
