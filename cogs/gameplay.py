"""
Encounter Module
Miketsu, 2019
"""

import asyncio
import os
import random
from datetime import datetime, timedelta
from itertools import cycle
from math import floor, ceil

import discord
import pytz
from PIL import Image, ImageDraw, ImageFont
from discord.ext import commands

from cogs.economy import Economy
from cogs.mongo.database import get_collections

# Collections
bosses = get_collections("bosses")
config = get_collections("config")
frames = get_collections("frames")
guilds = get_collections("guilds")
logs = get_collections("logs")
realms = get_collections("realms")
shikigamis = get_collections("shikigamis")
users = get_collections("users")

# Instantiations
id_guild = int(os.environ.get("SERVER"))


class Gameplay(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.prefix = self.client.command_prefix

        self.colour = config.find_one({"var": 1}, {"_id": 0, "embed_color": 1})["embed_color"]
        self.timezone = config.find_one({"var": 1}, {"_id": 0, "timezone": 1})["timezone"]

        self.attack_verb = cycle(config.find_one({"dict": 1}, {"_id": 0, "attack_verb": 1})["attack_verb"])
        self.emojis = config.find_one({"dict": 1}, {"_id": 0, "emojis": 1})["emojis"]
        self.get_emojis = config.find_one({"dict": 1}, {"_id": 0, "get_emojis": 1})["get_emojis"]
        
        self.channels = guilds.find_one({"server": str(id_guild)}, {"_id": 0, "channels": 1})
        self.listings = config.find_one({"list": 1}, {"_id": 0})
        
        self.id_spell_spam = self.channels["channels"]["spell-spam"]
        self.id_hosting = self.channels["channels"]["bot-sparring"]

        self.admin_roles = self.listings["admin_roles"]

        self.e_m = self.emojis["m"]
        self.e_j = self.emojis["j"]
        self.e_c = self.emojis["c"]
        self.e_f = self.emojis["f"]
        self.e_a = self.emojis["a"]
        self.e_t = self.emojis["t"]
        self.e_1 = self.emojis["1"]
        self.e_2 = self.emojis["2"]
        self.e_6 = self.emojis["6"]
        self.e_x = self.emojis["x"]

        self.pool_sp = []
        self.pool_ssr = []
        self.pool_ssn = []

        self.demons = []
        self.quizzes = []
        self.pool_all = []
        self.description_nether = []
        self.actual_rewards = []
        self.realm_cards = []

        self.assemble_captions = cycle(self.listings["assemble_captions"])
        self.boss_comment = self.listings["boss_comment"]
        self.rewards_nether = self.listings["rewards_nether"]

        self.boss_spawn = False
        self.quizzes_shuffle = random.shuffle(self.quizzes)
        self.quizzes_cycle = cycle(self.quizzes)
        self.generate_nether_information()
        
        for card in realms.find({}, {"_id": 0}):
            self.realm_cards.append(f"{card['name'].lower()}")
        
        for shiki in shikigamis.find({}, {"_id": 0, "name": 1}):
            self.pool_all.append(shiki["name"])
        
        for quiz in shikigamis.find({"demon_quiz": {"$ne": None}}, {"_id": 0, "demon_quiz": 1, "name": 1}):
            self.quizzes.append(quiz)
        
        for document in bosses.find({}, {"_id": 0, "boss": 1}):
            self.demons.append(document["boss"])
        
        for shikigami in shikigamis.find({}, {"_id": 0, "name": 1, "rarity": 1}):
            if shikigami["rarity"] == "SP":
                self.pool_sp.append(shikigami["name"])
            elif shikigami["rarity"] == "SSR":
                self.pool_ssr.append(shikigami["name"])
            elif shikigami["rarity"] == "SSN":
                self.pool_ssn.append(shikigami["name"])

    def generate_nether_information(self):
        for index, reward in enumerate(range(1, 9)):
            lvl = index + 1
            jades = self.rewards_nether[0] * lvl
            coins = self.rewards_nether[1] * lvl
            exp = self.rewards_nether[2] * lvl
            medals = self.rewards_nether[3] * lvl
            shards_sp = int(self.rewards_nether[4] * lvl) + floor(lvl/8)
            shards_ssr = int(self.rewards_nether[5] * lvl) + floor(lvl/8)
            shards_ssn = int(self.rewards_nether[6] * lvl) + floor(lvl/8)
            self.actual_rewards.append([jades, coins, exp, medals, shards_sp, shards_ssr, shards_ssn])

    def status_set(self, x):
        self.boss_spawn = x
    
    def check_if_user_has_any_alt_roles(self, user):
        for role in reversed(user.roles):
            if role.name in ["Geminio"]:
                return True
        return False
    
    def check_if_user_has_any_admin_roles(self):
        def predicate(ctx):
            for role in reversed(ctx.author.roles):
                if role.name in self.admin_roles:
                    return True
            return False
        return commands.check(predicate)
    
    def check_if_user_has_encounter_tickets(self):
        def predicate(ctx):
            return users.find_one({
                "user_id": str(ctx.author.id)}, {"_id": 0, "encounter_ticket": 1}
            )["encounter_ticket"] > 0
        return commands.check(predicate)
    
    def check_if_user_has_raid_tickets(self):
        def predicate(ctx):
            return users.find_one({
                "user_id": str(ctx.author.id)}, {"_id": 0, "realm_ticket": 1}
            )["realm_ticket"] > 0
        return commands.check(predicate)
    
    def check_if_user_has_nether_pass(self, ctx):
        return users.find_one({
            "user_id": str(ctx.author.id)}, {"_id": 0, "nether_pass": 1}
        )["nether_pass"] is True
    
    def calculate(self, x, y, z):
        try:
            if x - y > 0:
                return ((x - y) / x) * z
            elif x - y < 0:
                return -((y - x) / y) * z
            else:
                return 0
        except ZeroDivisionError:
            return 0

    def get_emoji(self, item):
        return self.get_emojis[item]

    def get_frame_thumbnail(self, frame):
        return frames.find_one({"name": frame}, {"_id": 0, "link": 1})["link"]
    
    def get_rarity_shikigami(self, s):
        return shikigamis.find_one({"name": s}, {"_id": 0, "rarity": 1})["rarity"]

    def get_raid_count(self, victim):
        return users.find_one({"user_id": str(victim.id)}, {"_id": 0, "raided_count": 1})["raided_count"]
    
    def get_time(self):
        return datetime.now(tz=pytz.timezone(self.timezone))
    
    def get_timestamp(self):
        return datetime.utcfromtimestamp(datetime.timestamp(datetime.now()))

    def pluralize(self, singular, count):
        if count > 1:
            if singular[-1:] == "s":
                return singular + "es"
            return singular + "s"
        else:
            return singular

    def push_new_shikigami(self, user_id, s, evolve, shards):
        users.update_one({
            "user_id": str(user_id)}, {
            "$push": {
                "shikigami": {
                    "name": s,
                    "rarity": self.get_rarity_shikigami(s),
                    "grade": 1,
                    "owned": 0,
                    "evolved": evolve,
                    "shards": shards,
                    "level": 1,
                    "exp": 0,
                    "level_exp_next": 6
                }
            }
        })

    def encounter_roll_netherworld_generate_cards(self, user, waves):

        card_rewards = random.choice(self.realm_cards)
        if waves >= 60:
            grade = random.choice([5, 5, 6])
        elif waves >= 50:
            grade = random.choice([4, 4, 5])
        elif waves >= 40:
            grade = random.choice([3, 3, 4])
        elif waves >= 30:
            grade = random.choice([2, 2, 3])
        elif waves >= 20:
            grade = random.choice([1, 1, 2])
        else:
            grade = random.choice([1, 1, 2])

        users.update_one({"user_id": str(user.id)}, {
            "$push": {
                "cards": {
                    "name": card_rewards,
                    "grade": int(grade)
                }
            }
        })
        return card_rewards, grade

    async def shikigami_post_approximate_results(self, ctx, query):
        shikigamis_search = shikigamis.find({
            "name": {"$regex": f"^{query[:2].lower()}"}
        }, {"_id": 0, "name": 1})

        approximate_results = []
        for result in shikigamis_search:
            approximate_results.append(f"{result['name'].title()}")

        embed = discord.Embed(
            title="Invalid shikigami", colour=self.colour,
            description=f"check the spelling of the shikigami"
        )
        embed.add_field(
            name="Possible matches",
            value="*{}*".format(", ".join(approximate_results)),
            inline=False
        )
        await ctx.channel.send(embed=embed)
        
    async def perform_add_log(self, currency, amount, user_id):
    
        if logs.find_one({"user_id": str(user_id)}, {"_id": 0}) is None:
            profile = {"user_id": str(user_id), "logs": []}
            logs.insert_one(profile)
    
        logs.update_one({
            "user_id": str(user_id)
        }, {
            "$push": {
                "logs": {
                    "$each": [{
                        "currency": currency,
                        "amount": amount,
                        "date": self.get_time(),
                    }],
                    "$position": 0,
                    "$slice": 200
                }
            }
        })
    
    async def boss_daily_reset_check(self):
        print("Checking if boss will be reset")
        survivability = bosses.find({"current_hp": {"$gt": 0}}, {"_id": 1}).count()
        discoverability = bosses.find({"discoverer": {"$eq": 0}}, {"_id": 1}).count()
    
        if survivability == 0 and discoverability == 0:
            await Economy(self).perform_reset_boss()
    
    async def achievements_process_announce(self, member, frame_name, jades):

        spell_spam_channel = self.client.get_channel(int(self.id_spell_spam))

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
            description=f"{member.mention} has acquired{intro_caption}{frame_name} frame!\n"
                        f"Acquired {jades:,d}{self.e_j} as bonus rewards!",
            timestamp=self.get_timestamp()
        )
        embed.set_footer(icon_url=member.avatar_url, text=f"{member.display_name}")
        embed.set_thumbnail(url=self.get_frame_thumbnail(frame_name))
        await spell_spam_channel.send(embed=embed)
        await asyncio.sleep(1)

    async def encounter_roll_netherworld(self, user, channel, search_msg):

        user_shikigamis, top_shikigamis, dead_shikigamis, placed_shikigamis, clear_chances = [], [], [], [], []
        clear_chances, cleared_waves, total_attempts = [], 0, 4

        for result in users.aggregate([
            {
                '$match': {
                    'user_id': str(user.id)
                }
            }, {
                '$unwind': {
                    'path': '$shikigami'
                }
            }, {
                '$match': {
                    'shikigami.owned': {
                        '$gt': 0
                    }
                }
            }, {
                '$project': {
                    'shikigami': 1
                }
            }
        ]):
            user_shikigamis.append(f"{result['shikigami']['name']}")

        for result in users.aggregate([
            {
                '$match': {
                    'user_id': str(user.id)
                }
            }, {
                '$unwind': {
                    'path': '$shikigami'
                }
            }, {
                '$match': {
                    'shikigami.owned': {
                        '$gt': 0
                    }
                }
            }, {
                '$sort': {
                    'shikigami.grade': -1,
                    'shikigami.level': -1
                }
            }, {
                '$match': {
                    'shikigami.level': {
                        '$gte': 2
                    }
                }
            }, {
                '$project': {
                    'shikigami': 1
                }
            }
        ]):
            top_shikigamis.append([result['shikigami']['name'], result['shikigami']['level']])

        def create_embed(t, d, s, b, c, u, r):
            embed = discord.Embed(
                color=user.colour, title=f"Encounter Netherworld",
                description=f"react below and place your shikigamis to start clearing waves",
                timestamp=self.get_timestamp()
            )

            formatted_shikigamis = []
            for e in t:
                if e[0] in d:
                    formatted_shikigamis.append(f"~~{e[0].title()}/{e[1]}~~")
                else:
                    formatted_shikigamis.append(f"{e[0].title()}/{e[1]}")

            embed.add_field(
                name=f"Top {len(top_shikigamis)} {self.pluralize('shikigami', len(top_shikigamis))}",
                value=f"*{', '.join(formatted_shikigamis[:10])}*",
                inline=False
            )
            embed.set_footer(icon_url=user.avatar_url, text=f"{user.display_name}")

            if s in ["accepted", "end"]:
                caption_list = []
                if b is not None:
                    for index2, x in enumerate(placed_shikigamis):
                        caption_list.append(
                            f"`Attempt#{index2 + 1}` :: {x[0].title()} | ~{round(x[1], 2)}% | "
                            f"{x[2]} {self.pluralize('clear', x[2])}\n"
                        )

                caption = ''.join(caption_list)
                if len(caption_list) == 0:
                    caption = "enter a shikigami name"

                embed.add_field(name=f"Cleared waves: {c}/70", value=f"{caption}", inline=False)

                if s == "end":
                    embed.set_image(url=u)
                    if len(r) > 0:
                        embed.add_field(
                            name="Rewards", inline=False,
                            value=f"{r[0]:,d}{self.e_j} | {r[1]:,d}{self.e_c} | "
                                  f"{r[2]:,d}{self.e_x} | {r[3]:,d}{self.e_m}",
                        )
                        card_reward, card_grade = self.encounter_roll_netherworld_generate_cards(user, c)
                        embed.add_field(
                            name="Bonus Reward",
                            value=f"Grade {card_grade} {card_reward.title()}"
                        )

            return embed

        await search_msg.edit(
            embed=create_embed(top_shikigamis, dead_shikigamis, None, None, cleared_waves, "", [])
        )
        await search_msg.add_reaction("🌌")

        def check(r, u):
            return user.id == u.id and str(r.emoji) == "🌌" and r.message.id == search_msg.id

        while True:
            try:
                await self.client.wait_for("reaction_add", timeout=60, check=check)
            except asyncio.TimeoutError:
                await search_msg.clear_reactions()
                return
            else:
                await search_msg.clear_reactions()
                await search_msg.edit(
                    embed=create_embed(top_shikigamis, dead_shikigamis, "accepted", None, cleared_waves, "", [])
                )
                break

        def check_if_valid_shikigami(m):
            if m.content.lower() in dead_shikigamis and m.author.id == user.id:
                raise KeyError
            elif m.content.lower() not in user_shikigamis and m.author.id == user.id:
                raise KeyError

            return m.author.id == user.id and \
                   m.content.lower() in user_shikigamis and \
                   m.channel.id == channel.id and \
                   m.content.lower() not in dead_shikigamis

        while True:
            try:
                if total_attempts == 0:
                    ranges = [[0, 9], [10, 19], [20, 29], [30, 39], [40, 49], [50, 59], [60, 69], [70, 79]]
                    for g, covered in enumerate(ranges):
                        if cleared_waves <= covered[1]:
                            rewards_select = self.actual_rewards[g]

                            jades = random.uniform(rewards_select[0] * 0.95, rewards_select[0] * 1.05)
                            coins = random.uniform(rewards_select[1] * 0.95, rewards_select[1] * 1.05)
                            exp = random.uniform(rewards_select[2] * 0.95, rewards_select[2] * 1.05)
                            medals = random.uniform(rewards_select[3] * 0.95, rewards_select[3] * 1.05)
                            shards_sp = rewards_select[4]
                            shards_ssr = rewards_select[5]
                            shards_ssn = rewards_select[6]

                            users.update_one({
                                "user_id": str(user.id)
                            }, {
                                "$inc": {
                                    "jades": int(jades),
                                    "coins": int(coins),
                                    "medals": int(medals)
                                },
                                "$set": {
                                    "nether_pass": False
                                }
                            })
                            await self.perform_add_log("jades", int(jades), user.id)
                            await self.perform_add_log("coins", int(coins), user.id)
                            await self.perform_add_log("medals", int(medals), user.id)

                            users.update_one({
                                "user_id": str(user.id),
                                "level": {
                                    "$lt": 60
                                }
                            }, {
                                "$inc": {
                                    "experience": int(exp)
                                }
                            })

                            shikigami_pool = {
                                shiki_iterate: 0 for shiki_iterate in self.pool_ssr + self.pool_sp + self.pool_ssn
                            }

                            i = 0
                            while i < shards_sp:
                                shikigami_shard = random.choice(self.pool_sp)
                                shikigami_pool[shikigami_shard] += 1
                                i += 1

                            i = 0
                            while i < shards_ssr:
                                shikigami_shard = random.choice(self.pool_ssr)
                                shikigami_pool[shikigami_shard] += 1
                                i += 1

                            i = 0
                            while i < shards_ssn:
                                shikigami_shard = random.choice(self.pool_ssn)
                                shikigami_pool[shikigami_shard] += 1
                                i += 1

                            shards_reward = list(shikigami_pool.items())

                            await self.encounter_roll_netherworld_issue_shards(user.id, shards_reward)
                            link = await self.encounter_roll_netherworld_generate_shards(user.id, shards_reward)

                            rewards = [int(jades), int(coins), int(exp), int(medals)]
                            await search_msg.edit(
                                embed=create_embed(
                                    top_shikigamis, dead_shikigamis, "end", True, cleared_waves, link, rewards
                                )
                            )
                            break
                        continue
                    break

                answer = await self.client.wait_for("message", timeout=60, check=check_if_valid_shikigami)
            except asyncio.TimeoutError:
                await search_msg.clear_reactions()
                return
            except KeyError:
                embed1 = discord.Embed(
                    colour=self.colour,
                    title="Invalid selection",
                    description=f"this shikigami is not in your possession, already dead, or does not exist"
                )
                msg2 = await channel.send(embed=embed1)
                await msg2.delete(delay=4)
            else:
                shikigami_bet = answer.content.lower()

                user_profile_new = users.find_one({
                    "user_id": str(user.id), "shikigami.name": shikigami_bet
                }, {
                    "_id": 0,
                    "shikigami.$": 1,
                    "level": 1
                })

                shiki_level = user_profile_new["shikigami"][0]['level']
                user_level = user_profile_new["level"]
                shikigami_evolved = user_profile_new["shikigami"][0]['evolved']

                evo_adjustment = 0.4
                if shikigami_evolved is True:
                    evo_adjustment = 0.2

                total_chance = 0
                shiki_clears = 0
                for i in range(cleared_waves + 1, 71):
                    total_chance = shiki_level + user_level - i * evo_adjustment
                    adjusted_chance = random.uniform(total_chance * 0.98, total_chance)

                    roll = random.uniform(0, 100)
                    if roll < adjusted_chance:
                        cleared_waves += 1
                        shiki_clears += 1
                        if cleared_waves == 70:
                            total_attempts = 0
                            await self.achievements_process_announce(user, "Dignified Dance", 3500)
                            break

                    else:
                        dead_shikigamis.append(shikigami_bet)
                        clear_chances.append(total_chance)
                        total_attempts -= 1
                        break

                placed_shikigamis.append([shikigami_bet, total_chance, shiki_clears])

                await search_msg.edit(
                    embed=create_embed(
                        top_shikigamis, dead_shikigamis, "end", shikigami_bet, cleared_waves, "", []
                    )
                )

    async def encounter_roll_netherworld_generate_shards(self, user_id, shards_reward):
        try:
            if len(shards_reward) == 0:
                return ""

            images = []
            font = ImageFont.truetype('data/marker_felt_wide.ttf', 30)
            x, y = 1, 60

            def generate_shikigami_with_shard(shikigami_thumbnail_select, shards_count):

                outline = ImageDraw.Draw(shikigami_thumbnail_select)
                outline.text((x - 1, y - 1), str(shards_count), font=font, fill="black")
                outline.text((x + 1, y - 1), str(shards_count), font=font, fill="black")
                outline.text((x - 1, y + 1), str(shards_count), font=font, fill="black")
                outline.text((x + 1, y + 1), str(shards_count), font=font, fill="black")
                outline.text((x, y), str(shards_count), font=font)

                return shikigami_thumbnail_select

            for entry in shards_reward:
                if entry[1] != 0:
                    address = f"data/shikigamis/{entry[0]}_pre.jpg"

                    shikigami_thumbnail = Image.open(address)
                    shikigami_image_final = generate_shikigami_with_shard(shikigami_thumbnail, entry[1])
                    images.append(shikigami_image_final)
                else:
                    continue

            dimensions = 90
            max_c = 8
            w = 90 * max_c

            def get_image_variables(h):
                total_frames = len(h)
                h = ceil(total_frames / max_c) * dimensions
                return w, h

            width, height = get_image_variables(images)
            new_im = Image.new("RGBA", (width, height))

            def get_coordinates(c):
                a = (c * dimensions - (ceil(c / max_c) - 1) * (dimensions * max_c)) - dimensions
                b = (ceil(c / max_c) * dimensions) - dimensions
                return a, b

            for index, item in enumerate(images):
                new_im.paste(images[index], (get_coordinates(index + 1)))

            address = f"temp/{user_id}.png"
            new_im.save(address)
            new_photo = discord.File(address, filename=f"{user_id}.png")
            hosting_channel = self.client.get_channel(int(self.id_hosting))
            msg = await hosting_channel.send(file=new_photo)
            attachment_link = msg.attachments[0].url
            return attachment_link

        except SystemError:
            return ""

    async def encounter_roll_netherworld_issue_shards(self, user_id, shards_reward):
        trimmed = []
        for entry in shards_reward:
            if entry[1] != 0:
                trimmed.append(entry)
            else:
                continue

        for shikigami_shard in trimmed:

            query = users.find_one({
                "user_id": str(user_id),
                "shikigami.name": shikigami_shard[0]}, {
                "_id": 0, "shikigami.$": 1
            })

            if query is None:
                self.push_new_shikigami(user_id, shikigami_shard[0], False, 0)

            users.update_one({"user_id": str(user_id), "shikigami.name": shikigami_shard[0]}, {
                "$inc": {
                    "shikigami.$.shards": 1
                }
            })

    @commands.command(aliases=["netherworld", "nw"])
    @commands.guild_only()
    async def netherworld_show_information(self, ctx):

        embed = discord.Embed(
            color=self.colour,
            title=f"netherworld, nw",
            description=f"fights and clears unwanted forces and earn rich rewards"
        )
        embed.add_field(
            name="Mechanics",
            value="`1.` Spawns `20%` chance during opening times\n"
                  "`2.` Upon discovering, enter the name of your shikigami to fight the forces\n"
                  "`3.` Fight and clear all the waves up to 70 or until it timeouts\n"
                  "`4.` Losing strikes out the shikigami, enter a new one then repeat\n"
                  "`5.` Each encounter has 4 attempts to max out your rewards"
        )
        embed.add_field(
            name="Format",
            value=f"*`{self.prefix}encounter`*",
            inline=False
        )
        await ctx.channel.send(embed=embed)

    @commands.command(aliases=["raid", "r"])
    @commands.check(check_if_user_has_raid_tickets)
    @commands.guild_only()
    async def raid_perform(self, ctx, *, victim: discord.Member = None):

        if victim is None:
            raise discord.ext.commands.MissingRequiredArgument(ctx.author)

        elif victim.name in ctx.author.name:
            await ctx.message.add_reaction("❌")

        elif victim.bot or victim.id == ctx.author.id:
            return

        else:
            try:
                raid_count = self.get_raid_count(victim)

                if raid_count >= 3:
                    embed = discord.Embed(
                        colour=self.colour,
                        description="raids are capped at 3 times per day and per realm"
                    )
                    embed.set_author(
                        name="Realm is under protection",
                        icon_url=victim.avatar_url
                    )
                    await ctx.channel.send(embed=embed)

                elif raid_count < 4:

                    raider = ctx.author
                    raider_medals = users.find_one({"user_id": str(raider.id)}, {"_id": 0, "level": 1})["level"]
                    victim_medals = users.find_one({"user_id": str(victim.id)}, {"_id": 0, "level": 1})["level"]
                    level_diff = raider_medals - victim_medals
                    range_diff = 60

                    if abs(level_diff) <= range_diff:
                        users.update_one({"user_id": str(victim.id)}, {"$inc": {"raided_count": 1}})
                        users.update_one({"user_id": str(raider.id)}, {"$inc": {"realm_ticket": -1}})
                        await self.raid_perform_attack(victim, raider, ctx)
                        await self.perform_add_log("realm_ticket", -1, raider.id)

                    else:
                        embed = discord.Embed(
                            title=f"Invalid chosen realm", colour=self.colour,
                            description=f"You can only raid realms with ±{range_diff:,d} of your level",
                        )
                        await ctx.channel.send(embed=embed)

            except AttributeError:
                raise discord.ext.commands.BadArgument(ctx.author)
            except TypeError:
                raise discord.ext.commands.BadArgument(ctx.author)

    async def raid_perform_attack(self, victim, raider, ctx):
        try:
            profile_raider = users.find_one({
                "user_id": str(raider.id)}, {
                "_id": 0, "level": 1, "medals": 1, "SP": 1, "SSR": 1, "SR": 1, "R": 1
            })
            profile_victim = users.find_one({
                "user_id": str(victim.id)}, {
                "_id": 0, "level": 1, "medals": 1, "SP": 1, "SSR": 1, "SR": 1, "R": 1
            })

            chance1 = self.calculate(profile_raider["level"], profile_victim["level"], 0.15)
            chance2 = self.calculate(profile_raider["medals"], profile_victim["medals"], 0.15)
            chance3 = self.calculate(profile_raider["SP"], profile_victim["SP"], 0.09)
            chance4 = self.calculate(profile_raider["SSR"], profile_victim["SSR"], 0.07)
            chance5 = self.calculate(profile_raider["SR"], profile_victim["SR"], 0.03)
            chance6 = self.calculate(profile_raider["R"], profile_victim["R"], 0.01)
            total_chance = round((0.5 + chance1 + chance2 + chance3 + chance4 + chance5 + chance6) * 100)
            roll = random.uniform(0, 100)

            if roll <= total_chance:
                coins, jades, medals, exp = 25000, 50, 25, 40
                embed = discord.Embed(
                    title="Realm raid", color=raider.colour,
                    description=f"{raider.mention} raids {victim.display_name}'s realm!",
                    timestamp=self.get_timestamp()
                )
                embed.add_field(
                    name=f"Results, `{total_chance}%`",
                    value=f"{raider.display_name} won!\n"
                          f"{coins:,d}{self.e_c}, {jades:,d}{self.e_j}, {medals:,d}{self.e_m}"
                )
                embed.set_footer(text=raider.display_name, icon_url=raider.avatar_url)
                await self.raid_perform_attack_giverewards_as_winner_raider(raider, coins, jades, medals, exp)
                await ctx.channel.send(embed=embed)

            else:
                coins, jades, medals, exp = 50000, 100, 50, 20
                embed = discord.Embed(
                    title="Realm raid", color=raider.colour,
                    description=f"{raider.mention} raids {victim.display_name}'s realm!",
                    timestamp=self.get_timestamp()
                )
                embed.add_field(
                    name=f"Results, `{total_chance}%`",
                    value=f"{victim.display_name} won!\n"
                          f"{coins:,d}{self.e_c}, {jades:,d}{self.e_j}, {medals:,d}{self.e_m}"
                )
                embed.set_footer(text=raider.display_name, icon_url=raider.avatar_url)
                await self.raid_perform_attack_giverewards_as_winner_victim(victim, raider, coins, jades, medals, exp)
                await ctx.channel.send(embed=embed)

        except KeyError:
            raise discord.ext.commands.BadArgument(ctx.author)

        except TypeError:
            return

    async def raid_perform_attack_giverewards_as_winner_victim(self, victim, raider, coins, jades, medals, exp):
        users.update_one({"user_id": str(raider.id), "level": {"$lt": 60}}, {"$inc": {"experience": exp}})
        users.update_one({"user_id": str(victim.id)}, {"$inc": {"coins": coins, "jades": jades, "medals": medals}})

        await self.perform_add_log("coins", coins, victim.id)
        await self.perform_add_log("jades", jades, victim.id)
        await self.perform_add_log("medals", medals, victim.id)

    async def raid_perform_attack_giverewards_as_winner_raider(self, raider, coins, jades, medals, exp):
        users.update_one({"user_id": str(raider.id), "level": {"$lt": 60}}, {"$inc": {"experience": exp}})
        users.update_one({"user_id": str(raider.id)}, {"$inc": {"coins": coins, "jades": jades, "medals": medals}})

        await self.perform_add_log("coins", coins, raider.id)
        await self.perform_add_log("jades", jades, raider.id)
        await self.perform_add_log("medals", medals, raider.id)

    @commands.command(aliases=["raidcalc", "raidc", "rc"])
    @commands.guild_only()
    async def raid_perform_calculation(self, ctx, *, victim: discord.Member = None):

        if victim is None:
            raise discord.ext.commands.MissingRequiredArgument(ctx.author)

        elif victim == ctx.author or victim.bot is True:
            return

        elif victim != ctx.author:
            await self.raid_perform_calculation_submit(victim, ctx.author, ctx)

    async def raid_perform_calculation_submit(self, victim, raider, ctx):
        try:
            profile_raider = users.find_one({
                "user_id": str(raider.id)}, {
                "_id": 0, "level": 1, "medals": 1, "SP": 1, "SSR": 1, "SR": 1, "R": 1
            })
            profile_victim = users.find_one({
                "user_id": str(victim.id)}, {
                "_id": 0, "level": 1, "medals": 1, "SP": 1, "SSR": 1, "SR": 1, "R": 1
            })

            chance1 = self.calculate(profile_raider["level"], profile_victim["level"], 0.15)
            chance2 = self.calculate(profile_raider["medals"], profile_victim["medals"], 0.15)
            chance3 = self.calculate(profile_raider["SP"], profile_victim["SP"], 0.09)
            chance4 = self.calculate(profile_raider["SSR"], profile_victim["SSR"], 0.07)
            chance5 = self.calculate(profile_raider["SR"], profile_victim["SR"], 0.03)
            chance6 = self.calculate(profile_raider["R"], profile_victim["R"], 0.01)
            total_chance = round((0.5 + chance1 + chance2 + chance3 + chance4 + chance5 + chance6) * 100)

            embed = discord.Embed(
                color=raider.colour,
                title=f"{raider.display_name} vs {victim.display_name} :: {total_chance}%"
            )
            await ctx.channel.send(embed=embed)

        except KeyError:
            raise discord.ext.commands.BadArgument(ctx.author)

        except TypeError:
            return

    @commands.command(aliases=["qz"])
    @commands.check(check_if_user_has_any_admin_roles)
    async def encounter_add_quiz(self, ctx, arg1, *, emoji=None):

        name = arg1.replace("_", " ").lower()
        if name not in self.pool_all:
            await self.shikigami_post_approximate_results(ctx, name)

        elif emoji is None:
            embed = discord.Embed(
                colour=self.colour,
                title="No emojis provided",
                description="specify emojis to change the shikigami's identity"
            )
            await ctx.channel.send(embed=embed)

        elif emoji is not None:
            x = shikigamis.update_one({"name": name}, {"$set": {"demon_quiz": emoji}})
            if x.modified_count != 0:
                await ctx.message.add_reaction("✅")

    @commands.command(aliases=["encounter", "enc"])
    @commands.check(check_if_user_has_encounter_tickets)
    @commands.cooldown(1, 180, commands.BucketType.user)
    @commands.guild_only()
    async def encounter_search(self, ctx):

        users.update_one({"user_id": str(ctx.author.id)}, {"$inc": {"encounter_ticket": -1}})
        await self.encounter_roll(ctx.author, ctx)
        await self.perform_add_log("encounter_ticket", -1, ctx.author.id)
        self.client.get_command("encounter_search").reset_cooldown(ctx)

    async def encounter_roll(self, user, ctx):

        async with ctx.channel.typing():
            search_msg = await ctx.channel.send(content="🔍 Searching the depths of Netherworld...")
            await asyncio.sleep(1)

        survivability = bosses.count({"current_hp": {"$gt": 0}})
        discoverability = bosses.count({"discoverer": {"$eq": 0}})

        if (survivability > 0 or discoverability > 0) and self.boss_spawn is False:
            roll_1 = random.randint(0, 100)

            if roll_1 <= 20:
                self.status_set(True)
                await self.encounter_roll_boss(user, ctx, search_msg)
            else:
                roll_2 = random.randint(0, 100)
                await asyncio.sleep(1)

                if 0 <= roll_2 <= 20 and self.check_if_user_has_nether_pass(ctx):
                    await self.encounter_roll_netherworld(user, ctx.channel, search_msg)
                else:
                    roll_3 = random.randint(0, 100)
                    if roll_3 < 30:
                        await self.encounter_roll_quiz(user, ctx, search_msg)
                    else:
                        await self.encounter_roll_treasure(user, ctx, search_msg)
        else:
            roll_2 = random.randint(0, 100)
            await asyncio.sleep(1)

            if 0 <= roll_2 <= 20 and self.check_if_user_has_nether_pass(ctx):
                await self.encounter_roll_netherworld(user, ctx.channel, search_msg)
            else:
                roll_3 = random.randint(0, 100)
                if roll_3 < 30:
                    await self.encounter_roll_quiz(user, ctx, search_msg)
                else:
                    await self.encounter_roll_treasure(user, ctx, search_msg)

    async def encounter_roll_quiz(self, user, ctx, search_msg):

        quiz_select = next(self.quizzes_cycle)
        answer = quiz_select['name']
        question = quiz_select['demon_quiz']
        timeout = 10
        guesses = 3

        embed = discord.Embed(title=f"Demon Quiz", color=user.colour, timestamp=self.get_timestamp())
        embed.description = f"Time Limit: {timeout} sec"
        embed.add_field(name="Who is this shikigami?", value=f"{question}")
        embed.set_footer(text=f"{guesses} {self.pluralize('guess', guesses)}", icon_url=user.avatar_url)
        await search_msg.edit(embed=embed)

        def check(guess):
            if guess.content.lower() == answer and guess.channel == ctx.channel and guess.author.id == user.id:
                return True
            elif guess.content.lower() != answer and guess.channel == ctx.channel and guess.author.id == user.id:
                raise KeyError

        while guesses != 0:
            try:
                await self.client.wait_for("message", timeout=timeout, check=check)

            except asyncio.TimeoutError:
                embed = discord.Embed(
                    title="Demon Quiz", color=user.colour,
                    description=f"You have failed the quiz",
                    timestamp=self.get_timestamp()
                )
                embed.add_field(name="Correct Answer", value=f"{answer.title()}")
                embed.set_footer(text="Time is up!", icon_url=user.avatar_url)
                await search_msg.edit(embed=embed)
                break

            except KeyError:

                if guesses == 3:
                    guesses -= 1
                    embed.set_footer(text=f"{guesses} {self.pluralize('guess', guesses)}", icon_url=user.avatar_url)
                    await search_msg.edit(embed=embed)

                elif guesses == 2:
                    guesses -= 1
                    embed.set_footer(text=f"{guesses} {self.pluralize('guess', guesses)}", icon_url=user.avatar_url)
                    await search_msg.edit(embed=embed)

                elif guesses == 1:
                    guesses -= 1
                    embed.set_footer(text=f"{guesses} {self.pluralize('guess', guesses)}", icon_url=user.avatar_url)
                    embed.remove_field(0)
                    embed.add_field(name="Correct Answer", value=f"{answer.title()}")
                    await search_msg.edit(embed=embed)
                    break
            else:
                users.update_one({"user_id": str(user.id)}, {"$inc": {"amulets": 5}})
                await self.perform_add_log("amulets", 5, ctx.author.id)
                embed = discord.Embed(
                    title="Demon Quiz", color=user.colour,
                    description=f"You have earned 5{self.e_a}",
                    timestamp=self.get_timestamp()
                )
                embed.set_footer(text="Correct!", icon_url=user.avatar_url)
                await search_msg.edit(embed=embed)
                break

    async def encounter_roll_treasure(self, user, ctx, search_msg):

        rewards = config.find_one({"dict": 1}, {"_id": 0, "rewards": 1})["rewards"]

        roll = random.randint(1, len(rewards))
        offer_item = tuple(dict.keys(rewards[str(roll)]["offer"]))[0]
        offer_amount = tuple(dict.values(rewards[str(roll)]["offer"]))[0]
        cost_item = tuple(dict.keys(rewards[str(roll)]["cost"]))[0]
        cost_amount = tuple(dict.values(rewards[str(roll)]["cost"]))[0]

        embed = discord.Embed(
            color=user.colour,
            title="Encounter treasure",
            description=f"A treasure chest containing {offer_amount:,d}{self.get_emoji(offer_item)}\n"
                        f"It opens using {cost_amount:,d}{self.get_emoji(cost_item)}",
            timestamp=self.get_timestamp()
        )
        embed.set_footer(text=f"Found by {user.display_name}", icon_url=user.avatar_url)
        await search_msg.edit(embed=embed)
        await search_msg.add_reaction("✅")

        def check(r, u):
            return u == ctx.author and str(r.emoji) == "✅" and search_msg.id == r.message.id

        try:
            await self.client.wait_for("reaction_add", timeout=6.0, check=check)

        except asyncio.TimeoutError:
            embed = discord.Embed(
                color=user.colour,
                title="Encounter Treasure",
                description=f"The chest you found turned into ashes 🔥",
                timestamp=self.get_timestamp()
            )
            embed.set_footer(text=f"Found by {user.display_name}", icon_url=user.avatar_url)
            await search_msg.edit(embed=embed)
            await search_msg.clear_reactions()

        else:
            cost_item_current = users.find_one({"user_id": str(user.id)}, {"_id": 0, cost_item: 1})[cost_item]
            if cost_item_current >= cost_amount:
                users.update_one({
                    "user_id": str(user.id)}, {
                    "$inc": {
                        offer_item: offer_amount,
                        cost_item: -cost_amount}
                })

                await self.perform_add_log(offer_item, offer_amount, user.id)
                await self.perform_add_log(cost_item, -cost_amount, user.id)

                cost_item_have = users.find_one({"user_id": str(user.id)}, {"_id": 0, cost_item: 1})[cost_item]
                offer_item_have = users.find_one({"user_id": str(user.id)}, {"_id": 0, offer_item: 1})[offer_item]

                embed = discord.Embed(
                    color=user.colour,
                    title="Encounter treasure",
                    description=f"You acquired `{offer_amount:,d}`{self.get_emoji(offer_item)} in exchange for "
                                f"`{cost_amount:,d}`{self.get_emoji(cost_item)}",
                    timestamp=self.get_timestamp()
                )
                embed.add_field(
                    name="Inventory",
                    value=f"`{offer_item_have:,d}` {self.get_emoji(offer_item)} | "
                          f"`{cost_item_have:,d}` {self.get_emoji(cost_item)}"
                )
                embed.set_footer(text=f"Found by {user.display_name}", icon_url=user.avatar_url)
                await search_msg.edit(embed=embed)
                await search_msg.clear_reactions()
            else:
                embed = discord.Embed(
                    color=user.colour,
                    title="Encounter treasure",
                    description=f"exchange failed, you only have {cost_item_current:,d}{self.get_emoji(cost_item)}",
                    timestamp=self.get_timestamp()
                )
                embed.set_footer(text=f"Found by {user.display_name}", icon_url=user.avatar_url)
                await search_msg.edit(embed=embed)
                await search_msg.clear_reactions()

    async def encounter_roll_boss(self, discoverer, ctx, search_msg):

        boss_alive = []
        for boss_name in bosses.find({
            "$or": [{
                "discoverer": {
                    "$eq": 0}}, {
                "current_hp": {
                    "$gt": 0}}]}, {
            "_id": 0, "boss": 1
        }):
            boss_alive.append(boss_name["boss"])

        boss_select = random.choice(boss_alive)

        if bosses.find_one({"boss": boss_select}, {"_id": 0, "discoverer": 1})["discoverer"] == 0:
            await self.encounter_roll_boss_create(discoverer, boss_select)

        def get_boss_profile(name):
            boss_profile_ = bosses.find_one({
                "boss": name}, {
                "_id": 0, "challengers": 1, "level": 1, "total_hp": 1, "current_hp": 1, "damage_cap": 1, "boss_url": 1,
                "rewards.coins": 1, "rewards.experience": 1, "rewards.jades": 1, "rewards.medals": 1,
            })

            boss_totalhp = boss_profile_["total_hp"]
            boss_currenthp = boss_profile_["current_hp"]
            boss_lvl = boss_profile_["level"]
            boss_url = boss_profile_["boss_url"]
            boss_coins = boss_profile_["rewards"]["coins"]
            boss_exp = boss_profile_["rewards"]["experience"]
            boss_jades = boss_profile_["rewards"]["jades"]
            boss_medals = boss_profile_["rewards"]["medals"]
            boss_hp_remaining = round(((boss_currenthp / boss_totalhp) * 100), 2)
            return boss_lvl, boss_hp_remaining, boss_jades, boss_coins, boss_medals, boss_exp, boss_url

        timeout = 180
        count_players = 0
        assembly_players = []
        assembly_players2 = []
        assembly_players_name = []
        boss_busters_id = guilds.find_one({"server": str(id_guild)}, {"_id": 0, "roles": 1})["roles"]["boss_busters"]

        def generate_embed_boss(time_remaining, listings):

            formatted_listings = ", ".join(listings)
            if len(formatted_listings) == 0:
                formatted_listings = None

            a, b, c, d, e, f, g = get_boss_profile(boss_select)

            embed_new = discord.Embed(
                title="Encounter Boss", color=discoverer.colour,
                description=f"The rare boss {boss_select} has been triggered!\n\n"
                            f"⏰ {round(time_remaining)} secs left!",
                timestamp=self.get_timestamp()
            )
            embed_new.add_field(
                name="Stats",
                value=f"```"
                      f"Level   :  {a}\n"
                      f"HP      :  {b}%\n"
                      f"Jades   :  {c:,d}\n"
                      f"Coins   :  {d:,d}\n"
                      f"Medals  :  {e:,d}\n"
                      f"Exp     :  {f:,d}"
                      f"```"
            )
            embed_new.add_field(
                name=f"Assembly Players [{len(assembly_players)}]",
                value=formatted_listings,
                inline=False
            )
            embed_new.set_thumbnail(url=g)
            embed_new.set_footer(
                text=f"Discovered by {discoverer.display_name}",
                icon_url=discoverer.avatar_url
            )
            return embed_new

        await asyncio.sleep(2)
        time_discovered = self.get_time()
        await search_msg.edit(embed=generate_embed_boss(timeout, assembly_players_name))
        await search_msg.add_reaction("🏁")

        link = f"https://discordapp.com/channels/{search_msg.guild.id}/{search_msg.channel.id}/{search_msg.id}"
        embed = discord.Embed(
            description=f"🏁 [Assemble here!]({link})"
        )
        await ctx.channel.send(content=f"<@&{boss_busters_id}>! {next(self.assemble_captions)}", embed=embed)

        def check(r, u):
            return u != self.client.user and str(r.emoji) == "🏁" and r.message.id == search_msg.id

        while count_players < 10:
            try:
                await asyncio.sleep(1)
                timeout = ((time_discovered + timedelta(seconds=180)) - self.get_time()).total_seconds()
                reaction, user = await self.client.wait_for("reaction_add", timeout=timeout, check=check)

            except asyncio.TimeoutError:
                embed = discord.Embed(title="🎌 Assembly ends!", colour=self.colour)
                await search_msg.clear_reactions()
                await ctx.channel.send(embed=embed)
                break

            else:
                if str(user.id) in assembly_players:
                    pass

                elif self.check_if_user_has_any_alt_roles(user):
                    pass

                elif str(user.id) not in assembly_players:
                    query = bosses.find_one({"boss": boss_select, "challengers.user_id": str(user.id)}, {"_id": 1})

                    if query is None:
                        bosses.update_one({
                            "boss": boss_select}, {
                            "$push": {
                                "challengers": {
                                    "user_id": str(user.id),
                                    "damage": 0
                                }
                            },
                            "$inc": {
                                "rewards.medals": 100,
                                "rewards.jades": 200,
                                "rewards.experience": 150,
                                "rewards.coins": 250000
                            }
                        })

                    assembly_players.append(str(user.id))
                    assembly_players2.append(str(user.name))
                    assembly_players_name.append(user.display_name)
                    timeout_new = ((time_discovered + timedelta(seconds=180)) - self.get_time()).total_seconds()
                    await search_msg.edit(embed=generate_embed_boss(timeout_new, assembly_players_name))
                    count_players += 1

        if len(assembly_players) == 0:
            await asyncio.sleep(3)
            embed = discord.Embed(
                title="Encounter Boss", colour=self.colour,
                description=f"No players have joined the assembly.\nThe rare boss {boss_select} has fled."
            )
            await ctx.channel.send(embed=embed)
            self.status_set(False)

        else:
            await asyncio.sleep(3)
            embed = discord.Embed(title=f"Battle with {boss_select} starts!", colour=self.colour)
            await ctx.channel.send(embed=embed)

            boss_profile = bosses.find_one({
                "boss": boss_select}, {
                "_id": 0, "total_hp": 1,  "damage_cap": 1, "boss_url": 1
            })
            boss_dmgcap = boss_profile["damage_cap"]
            boss_url_ = boss_profile["boss_url"]
            boss_dmg = boss_profile["total_hp"] * 0.01

            async with ctx.channel.typing():
                await asyncio.sleep(3)
                await self.encounter_roll_boss_assembly(
                    boss_select, assembly_players, boss_dmgcap, boss_dmg, boss_url_, ctx
                )

    async def encounter_roll_boss_assembly(self, boss_select, assembly_players, boss_dmgcap, boss_dmg, boss_url, ctx):

        damage_players = []
        for player in assembly_players:
            player_medals = users.find_one({"user_id": player}, {"_id": 0, "medals": 1})["medals"]
            player_level = users.find_one({"user_id": player}, {"_id": 0, "level": 1})["level"]
            player_dmg = boss_dmg + (player_medals * (1 + (player_level / 100)))

            if player_dmg > boss_dmgcap:
                player_dmg = boss_dmgcap

            damage_players.append(player_dmg)
            bosses.update_one({
                "boss": boss_select,
                "challengers.user_id": player}, {
                "$inc": {
                    "challengers.$.damage": round(player_dmg, 0),
                    "current_hp": -round(player_dmg, 0)
                }
            })
            player_ = ctx.guild.get_member(int(player))
            embed = discord.Embed(
                color=player_.colour,
                description=f"*{player_.mention} "
                            f"{next(self.attack_verb)} {boss_select}, dealing {round(player_dmg):,d} damage!*"
            )
            await ctx.channel.send(embed=embed)
            await asyncio.sleep(1)

        boss_profile_new = bosses.find_one({
            "boss": boss_select}, {
            "_id": 0,
            "current_hp": 1,
            "rewards": 1,
            "discoverer": 1
        })

        if boss_profile_new["current_hp"] <= 0:
            bosses.update_one({"boss": boss_select}, {"$set": {"current_hp": 0}})

        await self.encounter_roll_boss_check(assembly_players, boss_select, boss_url, boss_profile_new, ctx)

    async def encounter_roll_boss_check(self, assembly_players, boss_select, boss_url, boss_profile_new, ctx):

        boss_currenthp = bosses.find_one({"boss": boss_select}, {"_id": 0, "current_hp": 1})["current_hp"]

        if boss_currenthp > 0:

            boss_jadesteal = round(boss_profile_new["rewards"]["jades"] * 0.02)
            boss_coinsteal = round(boss_profile_new["rewards"]["coins"] * 0.03)

            description = f"💨 Rare Boss {boss_select} has fled with {round(boss_currenthp):,d} remaining HP\n" \
                          f"💸 Stealing {boss_jadesteal:,d} {self.e_j} & {boss_coinsteal:,d} {self.e_c} " \
                          f"each from its attackers!\n\n{random.choice(self.boss_comment)}~"

            embed = discord.Embed(
                colour=self.colour, description=description, timestamp=self.get_timestamp()
            )
            embed.set_thumbnail(url=boss_url)

            await self.encounter_roll_boss_steal(assembly_players, boss_jadesteal, boss_coinsteal)
            await asyncio.sleep(3)

            bosses.update_one({
                "boss": boss_select}, {
                "$inc": {
                    "rewards.jades": boss_jadesteal,
                    "rewards.coins": boss_coinsteal
                }
            })

            await ctx.channel.send(embed=embed)
            self.client.get_command("encounter_search").reset_cooldown(ctx)
            self.status_set(False)

        elif boss_currenthp == 0:

            players_dmg = 0
            for damage in bosses.aggregate([{
                "$match": {
                    "boss": boss_select}}, {
                "$unwind": {
                    "path": "$challengers"}}, {
                "$group": {
                    "_id": "",
                    "total_damage": {
                        "$sum": "$challengers.damage"}}}, {
                "$project": {
                    "_id": 0
                }}
            ]):
                players_dmg = damage["total_damage"]

            challengers = []
            distribution = []

            for data in bosses.aggregate([{
                "$match": {
                    "boss": boss_select}}, {
                "$unwind": {
                    "path": "$challengers"}}, {
                "$project": {
                    "_id": 0, "challengers": 1
                }
            }]):
                challengers.append(data["challengers"]["user_id"])
                distribution.append(round(((data["challengers"]["damage"]) / players_dmg), 2))

            boss_coins = boss_profile_new["rewards"]["coins"]
            boss_jades = boss_profile_new["rewards"]["jades"]
            boss_medals = boss_profile_new["rewards"]["medals"]
            boss_exp = boss_profile_new["rewards"]["experience"]

            boss_coins_user = [i * boss_coins for i in distribution]
            boss_jades_users = [i * boss_jades for i in distribution]
            boss_medals_users = [i * boss_medals for i in distribution]
            boss_exp_users = [i * boss_exp for i in distribution]

            rewards_zip = list(
                zip(challengers, boss_coins_user, boss_jades_users, boss_medals_users, boss_exp_users, distribution))

            embed = discord.Embed(
                title=f"The Rare Boss {boss_select} has been defeated!", colour=self.colour
            )
            await ctx.channel.send(embed=embed)
            await self.encounter_roll_boss_defeat(boss_select, rewards_zip, boss_url, boss_profile_new, ctx)

    async def encounter_roll_boss_defeat(self, boss_select, rewards_zip, boss_url, boss_profile_new, ctx):

        embed = discord.Embed(
            colour=self.colour,
            title="🎊 Boss defeat rewards!",
            timestamp=self.get_timestamp()
        )
        embed.set_thumbnail(url=boss_url)

        for reward in rewards_zip:
            try:
                name = ctx.guild.get_member(int([reward][0][0]))
                damage_contribution = round([reward][0][5] * 100, 2)
                player_level = users.find_one({"user_id": [reward][0][0]}, {"_id": 0, "level": 1})["level"]
                coins_r = round([reward][0][1] * (1 + player_level / 100))
                jades_r = round([reward][0][2] * (1 + player_level / 100))
                medal_r = round([reward][0][3] * (1 + player_level / 100))
                exp_r = round([reward][0][4] * (1 + player_level / 100))

                embed.add_field(
                    name=f"{name}, {damage_contribution}%",
                    value=f"{coins_r:,d}{self.e_c}, {jades_r:,d}{self.e_j}, "
                          f"{medal_r:,d}{self.e_m}, {exp_r:,d} {self.e_x}",
                    inline=False
                )
                users.update_one({
                    "user_id": [reward][0][0]}, {
                    "$inc": {
                        "jades": round([reward][0][2]),
                        "coins": round([reward][0][1]),
                        "medals": round([reward][0][3])
                    }
                })
                await self.perform_add_log("jades", round([reward][0][2]), [reward][0][0])
                await self.perform_add_log("coins", round([reward][0][1]), [reward][0][0])
                await self.perform_add_log("medals", round([reward][0][3]), [reward][0][0])

                users.update_one({
                    "user_id": [reward][0][0], "level": {"$lt": 60}}, {
                    "$inc": {
                        "experience": round([reward][0][4])
                    }
                })

            except AttributeError:
                continue

        try:
            jades, coins, medals, exp = 250, 150000, 150, 100
            discoverer = boss_profile_new["discoverer"]
            users.update_one({
                "user_id": discoverer}, {
                "$inc": {
                    "jades": jades,
                    "coins": coins,
                    "medals": medals,
                }
            })
            await self.perform_add_log("jades", jades, discoverer)
            await self.perform_add_log("coins", coins, discoverer)
            await self.perform_add_log("medals", medals, discoverer)

            users.update_one({
                "user_id": discoverer, "level": {"$lt": 60}}, {
                "$inc": {
                    "experience": exp
                }
            })

            await asyncio.sleep(3)
            await ctx.channel.send(embed=embed)
            await asyncio.sleep(2)
            user = ctx.guild.get_member(int(discoverer))
            description = f"{user.mention} earned an extra {jades:,d}{self.e_j}, {coins:,d}{self.e_c}, " \
                          f"{medals:,d}{self.e_m} and {exp:,d} {self.e_x} for initially discovering {boss_select}!"
            embed = discord.Embed(
                colour=self.colour,
                description=description, timestamp=self.get_timestamp()
            )
            await ctx.channel.send(embed=embed)
        except AttributeError:
            pass

        self.client.get_command("encounter_search").reset_cooldown(ctx)
        users.update_many({"level": {"$gt": 60}}, {"$set": {"experience": 100000, "level_exp_next": 100000}})
        self.status_set(False)

    async def encounter_roll_boss_create(self, user, boss_select):
        discoverer = users.find_one({"user_id": str(user.id)}, {"_id": 0, "level": 1})
        boss_lvl = discoverer["level"] + 60

        total_medals = 10000
        for x in users.aggregate([{
            "$group": {
                "_id": "",
                "medals": {
                    "$sum": "$medals"}}}, {
            "$project": {
                "_id": 0
            }
        }]):
            total_medals = x["medals"]

        bosses.update_one({
            "boss": boss_select}, {
            "$set": {
                "discoverer": str(user.id),
                "level": boss_lvl,
                "total_hp": round(total_medals * (1 + (boss_lvl / 100)), 0),
                "current_hp": round(total_medals * (1 + (boss_lvl / 100)), 0),
                "damage_cap": round(total_medals * (1 + (boss_lvl / 100)) * 0.2, 0),
                "rewards.medals": 200,
                "rewards.jades": 1000,
                "rewards.experience": 250,
                "rewards.coins": 1000000
            }
        })

    async def encounter_roll_boss_steal(self, assembly_players, boss_jadesteal, boss_coinsteal):
        for player_id in assembly_players:

            deduction_jades = users.update_one({
                "user_id": player_id, "jades": {"$gte": boss_jadesteal}}, {
                "$inc": {
                    "jades": - boss_jadesteal
                }
            })
            if deduction_jades.modified_count > 0:
                await self.perform_add_log("jades", -boss_jadesteal, player_id)


            deduction_coins = users.update_one({
                "user_id": player_id, "coins": {"$gte": boss_coinsteal}}, {
                "$inc": {
                    "coins": - boss_coinsteal
                }
            })
            if deduction_jades.modified_count > 0:
                await self.perform_add_log("coins", -boss_coinsteal, player_id)

            if deduction_jades.modified_count == 0:
                users.update_one({"user_id": player_id}, {"$set": {"jades": 0}})
                current_jades = users.find_one({"user_id": player_id}, {"_id": 0, "jades": 1})["jades"]
                await self.perform_add_log("jades", -current_jades, player_id)
            else:
                await self.perform_add_log("jades", -boss_jadesteal, player_id)

            if deduction_coins.modified_count == 0:
                users.update_one({"user_id": player_id}, {"$set": {"coins": 0}})
                current_coins = users.find_one({"user_id": player_id}, {"_id": 0, "coins": 1})["coins"]
                await self.perform_add_log("coins", -current_coins, player_id)
            else:
                await self.perform_add_log("coins", -boss_coinsteal, player_id)

    @commands.command(aliases=["binfo", "bossinfo"])
    @commands.guild_only()
    async def encounter_boss_stats(self, ctx, *, args=None):

        try:
            query = args.title()
            if query.lower() == "all":

                query = bosses.find({"current_hp": {"$gt": 0}}, {"_id": 0, "boss": 1, "total_hp": 1, "current_hp": 1})
                bosses_formatted = []

                for boss in query:
                    percent = (boss["current_hp"] / boss["total_hp"]) * 100
                    bosses_formatted.append(
                        f"• {round(percent,2)}%    {boss['boss']}"
                    )

                bosses_formatted_lines = "\n".join(bosses_formatted)
                boss_description = f"```" \
                              f"  HP        Boss\n" \
                              f"{bosses_formatted_lines}\n" \
                              f"```"

                if len(bosses_formatted) == 0:
                    boss_description = "All rare bosses are currently dead"

                embed = discord.Embed(
                    title=f"Boss survivability", colour=self.colour,
                    description=boss_description,
                    timestamp=self.get_timestamp()
                )
                await ctx.channel.send(embed=embed)

            elif query not in self.demons:
                raise AttributeError

            else:
                boss_profile = bosses.find_one({
                    "boss": query}, {
                    "_id": 0,
                    "level": 1,
                    "total_hp": 1,
                    "current_hp": 1,
                    "rewards": 1,
                    "discoverer": 1,
                    "boss_url": 1
                })

                try:
                    discoverer = ctx.guild.get_member(int(boss_profile["discoverer"])).display_name
                except AttributeError:
                    discoverer = "None"

                level = boss_profile["level"]
                total_hp = boss_profile["total_hp"]
                current_hp = boss_profile["current_hp"]
                medals = boss_profile["rewards"]["medals"]
                experience = boss_profile["rewards"]["experience"]
                coins = boss_profile["rewards"]["coins"]
                jades = boss_profile["rewards"]["jades"]
                boss_url = boss_profile["boss_url"]

                description = f"```" \
                              f"Discoverer  :: {discoverer}\n" \
                              f"     Level  :: {level}\n" \
                              f"  Total Hp  :: {total_hp}\n" \
                              f"Current Hp  :: {current_hp}\n" \
                              f"    Medals  :: {medals}\n" \
                              f"     Jades  :: {jades}\n" \
                              f"     Coins  :: {coins}\n" \
                              f"Experience  :: {experience}```"

                embed = discord.Embed(
                    title=f"Rare Boss {query} stats", colour=self.colour,
                    description=description,
                    timestamp=self.get_timestamp()
                )
                embed.set_thumbnail(url=boss_url)
                await ctx.channel.send(embed=embed)

        except AttributeError:
            embed = discord.Embed(
                title="bossinfo, binfo", colour=self.colour,
                description="shows discovered boss statistics"
            )
            demons_formatted = ", ".join(self.demons)
            embed.add_field(name="Bosses", value=f"*{demons_formatted}*")
            embed.add_field(
                name="Example",
                value=f"*`{self.prefix}binfo namazu`*\n"
                      f"*`{self.prefix}binfo all`*",
                inline=False
            )
            await ctx.channel.send(embed=embed)


def setup(client):
    client.add_cog(Gameplay(client))
