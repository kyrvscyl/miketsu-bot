"""
Economy Module
Miketsu, 2019
"""

import asyncio
import collections
import os
import random
from datetime import datetime, timedelta
from itertools import cycle
from math import ceil

import discord
import pytz
from PIL import Image, ImageFont, ImageDraw, ImageOps
from discord.ext import commands

from cogs.frames import Frames
from cogs.mongo.database import get_collections

# Collections
bosses = get_collections("bosses")
bounties = get_collections("bounties")
config = get_collections("config")
explores = get_collections("explores")
frames = get_collections("frames")
guilds = get_collections("guilds")
logs = get_collections("logs")
shikigamis = get_collections("shikigamis")
ships = get_collections("ships")
streaks = get_collections("streaks")
users = get_collections("users")
zones = get_collections("zones")

# Dictionaries
emojis = config.find_one({"dict": 1}, {"_id": 0, "emojis": 1})["emojis"]
emoji_dict = config.find_one({"dict": 1}, {"_id": 0, "get_emojis": 1})["get_emojis"]
evo_requirement = config.find_one({"dict": 1}, {"_id": 0, "evo_requirement": 1})["evo_requirement"]
mystic_shop = config.find_one({"dict": 1}, {"_id": 0, "mystic_shop": 1})["mystic_shop"]
shard_requirement = config.find_one({"dict": 1}, {"_id": 0, "shard_requirement": 1})["shard_requirement"]
talisman_acquire = config.find_one({"dict": 1}, {"_id": 0, "talisman_acquire": 1})["talisman_acquire"]

# Variables
id_guild = int(os.environ.get("SERVER"))
colour = config.find_one({"var": 1}, {"_id": 0, "embed_color": 1})["embed_color"]
id_hosting = guilds.find_one({"server": str(id_guild)}, {"_id": 0, "channels": 1})["channels"]["bot-sparring"]
timezone = config.find_one({"var": 1}, {"_id": 0, "timezone": 1})["timezone"]

e_1 = emojis["1"]
e_2 = emojis["2"]
e_3 = emojis["3"]
e_4 = emojis["4"]
e_5 = emojis["5"]
e_6 = emojis["6"]
e_a = emojis["a"]
e_b = emojis["b"]
e_c = emojis["c"]
e_f = emojis["f"]
e_j = emojis["j"]
e_m = emojis["m"]
e_s = emojis["s"]
e_t = emojis["t"]
e_x = emojis["x"]

# Lists
pool_sp = []
pool_ssr = []
pool_sr = []
pool_r = []
pool_n = []
pool_ssn = []

pool_shrine = []
pool_all = []
pool_all_mystery = []
pool_all_broken = []

trading_list = []
purchasable_frames = []
trading_list_formatted = []

rarities = config.find_one({"list": 1}, {"_id": 0, "rarities": 1})["rarities"]

steal_adverb = config.find_one({"list": 1}, {"_id": 0, "steal_adverb": 1})["steal_adverb"]
steal_verb = config.find_one({"list": 1}, {"_id": 0, "steal_verb": 1})["steal_verb"]
steal_noun = config.find_one({"list": 1}, {"_id": 0, "steal_noun": 1})["steal_noun"]
steal_comment = config.find_one({"list": 1}, {"_id": 0, "steal_comment": 1})["steal_comment"]

prayer_heard = cycle(config.find_one({"list": 1}, {"_id": 0, "prayer_heard": 1})["prayer_heard"])
prayer_ignored = cycle(config.find_one({"list": 1}, {"_id": 0, "prayer_ignored": 1})["prayer_ignored"])

developer_team = guilds.find_one({"server": str(id_guild)}, {"_id": 0, "developers": 1})["developers"]
id_spell_spam = guilds.find_one({"server": str(id_guild)}, {"_id": 0, "channels": 1})["channels"]["spell-spam"]

summon_captions = cycle(config.find_one({"list": 1}, {"_id": 0, "summon_captions": 1})["summon_captions"])

# Instantiations

for s in shikigamis.find({}, {"_id": 0, "name": 1, "rarity": 1, "shrine": 1}):
    if s["shrine"] is True:
        pool_shrine.append(s["name"])
    elif s["rarity"] == "SP":
        pool_sp.append(s["name"])
    elif s["rarity"] == "SSR":
        pool_ssr.append(s["name"])
    elif s["rarity"] == "SR":
        pool_sr.append(s["name"])
    elif s["rarity"] == "R":
        pool_r.append(s["name"])
    elif s["rarity"] == "N":
        pool_n.append(s["name"])
    elif s["rarity"] == "SSN":
        pool_ssn.append(s["name"])


for doc in frames.find({"purchase": True}, {"_id": 1, "name": 1}):
    purchasable_frames.append(doc["name"].lower())

for _offer in mystic_shop:
    for _amount in mystic_shop[_offer]:
        trading_list.append([
            mystic_shop[_offer][_amount]["offer"][0],
            mystic_shop[_offer][_amount]["offer"][1],
            mystic_shop[_offer][_amount]["cost"][0],
            mystic_shop[_offer][_amount]["cost"][1],
            _offer, _amount
        ])


for trade in trading_list:
    trading_list_formatted.append(
        f"▫ `{trade[1]}`{emoji_dict[trade[0]]} → `{trade[3]:,d}`{emoji_dict[trade[2]]} | {trade[4]} {trade[5]}\n"
    )


pool_all_mystery.extend(pool_sp)
pool_all_mystery.extend(pool_ssr)
pool_all_mystery.extend(pool_sr)
pool_all_mystery.extend(pool_r)
pool_all_mystery.extend(pool_shrine)
pool_all_broken.extend(pool_n)
pool_all_broken.extend(pool_ssn)
pool_all.extend(pool_all_mystery)
pool_all.extend(pool_all_broken)


def check_if_user_has_development_role(ctx):
    return str(ctx.author.id) in developer_team


def check_if_user_has_any_alt_roles(user):
    for role in reversed(user.roles):
        if role.name in ["Geminio"]:
            return True
    return False


def check_if_user_has_prayers(ctx):
    return users.find_one({"user_id": str(ctx.author.id)}, {"_id": 0, "prayers": 1})["prayers"] > 0


def check_if_user_has_parade_tickets(ctx):
    return users.find_one({"user_id": str(ctx.author.id)}, {"_id": 0, "parade_tickets": 1})["parade_tickets"] > 0


def check_if_user_has_shiki_set(ctx):
    return users.find_one({"user_id": str(ctx.author.id)}, {"_id": 0, "display": 1})["display"] is not None


def check_if_user_has_sushi_1(ctx):
    return users.find_one({"user_id": str(ctx.author.id)}, {"_id": 0, "sushi": 1})["sushi"] > 0


def check_if_user_has_sushi_2(ctx, required):
    return users.find_one({"user_id": str(ctx.author.id)}, {"_id": 0, "sushi": 1})["sushi"] >= required


class Economy(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.prefix = self.client.command_prefix

    def get_emoji(self, item):
        return emoji_dict[item]

    def get_variables(self, r):
        dictionary = {
            "SP": [90 * 6, 6],
            "SSR": [90 * 8, 8],
            "SR": [90 * 10, 10],
            "R": [90 * 8, 8],
            "N": [90 * 6, 6],
            "SSN": [90 * 7, 7]
        }
        return dictionary[r]
    
    def get_frame_thumbnail(self, frame):
        return frames.find_one({"name": frame}, {"_id": 0, "link": 1})["link"]
    
    def get_time(self):
        return datetime.now(tz=pytz.timezone(timezone))
    
    def get_timestamp(self):
        return datetime.utcfromtimestamp(datetime.timestamp(datetime.now()))
    
    def get_time_converted(self, utc_dt):
        return utc_dt.replace(tzinfo=pytz.timezone("UTC")).astimezone(tz=pytz.timezone(timezone))
    
    def get_bond(self, x, y):
        bond_list = sorted([x.id, y.id], reverse=True)
        return f"{bond_list[0]}x{bond_list[1]}"
    
    def get_shard_requirement(self, shiki):
        rarity = shikigamis.find_one({"name": shiki.lower()}, {"_id": 0, "rarity": 1})["rarity"]
        return shard_requirement[rarity], rarity
    
    def get_evo_link(self, evolution):
        return {True: "evo", False: "pre"}[evolution]
    
    def get_evo_requirement(self, r):
        return evo_requirement[r]
    
    def get_rarity_emoji(self, rarity):
        return {"SP": e_1, "SSR": e_2, "SR": e_3, "R": e_4, "N": e_5, "SSN": e_6}[rarity]
    
    def get_rarity_shikigami(self, shiki):
        return shikigamis.find_one({"name": shiki}, {"_id": 0, "rarity": 1})["rarity"]
    
    def get_talisman_acquire(self, rarity):
        return talisman_acquire[rarity]
    
    def get_thumbnail_shikigami(self, shiki, evolution):
        return shikigamis.find_one({"name": shiki.lower()}, {"_id": 0, "thumbnail": 1})["thumbnail"][evolution]
    
    def shikigami_push_user(self, user_id, shiki, evolve, shards):
        users.update_one({
            "user_id": str(user_id)}, {
            "$push": {
                "shikigami": {
                    "name": shiki,
                    "rarity": self.get_rarity_shikigami(shiki),
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
    
    def pluralize(self, singular, count):
        if count > 1:
            if singular[-1:] == "s":
                return singular + "es"
            return singular + "s"
        else:
            return singular
    
    def hours_minutes(self, td):
        return td.seconds // 3600, (td.seconds // 60) % 60
    
    async def frame_automate(self):

        print("Recalculating frames distribution")
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
                timestamp=self.get_timestamp()
            )
            embed.set_thumbnail(url="https://vignette.wikia.nocookie.net/onmyoji/images/1/17/Frame7.png")
            await spell_spam_channel.send(embed=embed)
            await self.frame_acquisition(starlight_new, "Starlight Sky", jades=2500)

        if starlight_current == starlight_new:
            jades = 2000
            users.update_one({"user_id": str(starlight_current.id)}, {"$inc": {"jades": jades}})
            await self.perform_add_log("jades", jades, starlight_current.id)
            msg = f"{starlight_current.mention} has earned {jades:,d}{e_j} " \
                  f"for wielding the Starlight Sky frame for a day!"
            await spell_spam_channel.send(msg)

        else:
            await starlight_new.add_roles(starlight_role)
            await asyncio.sleep(3)
            await starlight_current.remove_roles(starlight_role)
            await asyncio.sleep(3)

            description = \
                f"{starlight_new.mention} {random.choice(steal_adverb)} {random.choice(steal_verb)} " \
                f"the Rare Starlight Sky Frame from {starlight_current.mention}\"s " \
                f"{random.choice(steal_noun)}!! {random.choice(steal_comment)}\n\n" \
                f"🍀 No SSR streak record of {streak_list_new[0][1]} summons! " \
                f"Cuts in three fourths every reset!"

            embed = discord.Embed(
                color=0xac330f,
                title="📨 Hall of Framers update",
                description=description,
                timestamp=self.get_timestamp()
            )
            embed.set_thumbnail(url="https://vignette.wikia.nocookie.net/onmyoji/images/1/17/Frame7.png")
            await spell_spam_channel.send(embed=embed)
            await self.frame_acquisition(starlight_new, "Starlight Sky", jades=2500)
            
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
            await self.perform_add_log("amulets", 10, member.id)

        embed = discord.Embed(
            title="Blazing Sun Frame Update",
            description=f"completed the SSR shikigami collection\n"
                        f"earns 10{e_a} every reset",
            color=colour,
            timestamp=self.get_timestamp()
        )
        embed.add_field(
            name="Frame Wielders",
            value=f"{', '.join(blazing_users)}"
        )
        embed.set_thumbnail(url=self.get_frame_thumbnail("Blazing Sun"))
        await spell_spam_channel.send(embed=embed)
    
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

    async def shikigami_post_approximate_results(self, ctx, query):
        shikigamis_search = shikigamis.find({
            "name": {"$regex": f"^{query[:2].lower()}"}
        }, {"_id": 0, "name": 1})

        approximate_results = []
        for result in shikigamis_search:
            approximate_results.append(f"{result['name'].title()}")

        embed = discord.Embed(
            title="Invalid shikigami", colour=discord.Colour(colour),
            description=f"check the spelling of the shikigami"
        )
        embed.add_field(
            name="Possible matches",
            value="*{}*".format(", ".join(approximate_results)),
            inline=False
        )
        await ctx.channel.send(embed=embed)

    async def shikigami_process_levelup(self, user_id, shiki):
        profile = users.find_one({
            "user_id": str(user_id), "shikigami.name": shiki}, {
            "_id": 0,
            "shikigami.$": 1,
        })
        exp = profile["shikigami"][0]["exp"]
        level = profile["shikigami"][0]["level"]
        level_end = int(exp ** 0.400515000062462)

        if level > level_end:
            users.update_one({
                "user_id": str(user_id), "shikigami.name": shiki}, {
                "$set": {
                    "shikigami.$.level": level_end
                }
            })

        if level < level_end:
            level_next = 5 * (round(((level + 2) ** (1 / 0.400515000062462)) / 5))
            users.update_one({
                "user_id": str(user_id), "shikigami.name": shiki
            }, {
                "$set": {
                    "shikigami.$.level_exp_next": level_next,
                    "shikigami.$.level": level_end
                }
            })
            if level_end == 40:
                users.update_one({
                    "user_id": str(user_id), "shikigami.name": shiki
                }, {
                    "$set": {
                        "shikigami.$.level_exp_next": 10000,
                        "shikigami.$.exp": 10000
                    }
                })

    @commands.command(aliases=["sushi", "food", "ap", "hungry"])
    @commands.guild_only()
    @commands.cooldown(1, 60 * 60, commands.BucketType.guild)
    async def spawn_random_sushi(self, ctx):

        minutes, sushi_claimers, timestamp = 10, [], self.get_timestamp()
        role = guilds.find_one({"server": str(id_guild)}, {"_id": 0, "roles.sushchefs": 1})["roles"]["sushchefs"]

        def create_embed(listings, strike):
            embed = discord.Embed(
                title=f"{strike}Free sushi!{strike} 25🍣",
                description=f"claim your free sushi every hour! 🎉\n"
                            f"served {len(listings)} hungry {self.pluralize('Onmyoji', len(listings))}",
                color=colour,
                timestamp=timestamp
            )
            embed.set_footer(text=f"lasts {minutes} minutes", icon_url=self.client.user.avatar_url)
            return embed

        content = f"<@&{role}>!"
        msg = await ctx.channel.send(content=content, embed=create_embed(sushi_claimers, ""))
        await msg.add_reaction("🍽️")

        def check(r, u):
            return u != self.client.user and \
                   r.message.id == msg.id and \
                   str(r.emoji) == "🍽️" and \
                   str(u.id) not in sushi_claimers

        while True:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=60 * minutes, check=check)
            except asyncio.TimeoutError:
                await msg.edit(embed=create_embed(sushi_claimers, "~~"))
                await msg.clear_reactions()
                break
            else:
                sushi = 25
                users.update_one({"user_id": str(user.id)}, {"$inc": {"sushi": sushi}})
                sushi_claimers.append(str(user.id))
                await msg.edit(embed=create_embed(sushi_claimers, ""))
                await self.perform_add_log("sushi", sushi, user.id)
                continue

    @commands.command(aliases=["wish"])
    @commands.guild_only()
    async def wish_perform(self, ctx, *, shiki=None):

        user = ctx.author
        profile = users.find_one({"user_id": str(user.id)}, {"_id": 0, "wish": 1})

        if shiki is None:
            embed = discord.Embed(
                color=colour,
                title="wish, w",
                description=f"wish for a shikigami shard to manually summon it"
            )
            embed.add_field(name="Example", value=f"*`{self.prefix}wish inferno ibaraki`*")
            await ctx.channel.send(embed=embed)

        elif profile["wish"] is False:
            embed = discord.Embed(
                color=user.colour,
                description=f"Your wish has been fulfilled already today",
            )
            await ctx.channel.send(embed=embed)

        elif profile["wish"] is not True:
            embed = discord.Embed(
                color=user.colour,
                description=f"Your wish has been placed already today",
            )
            await ctx.channel.send(embed=embed)

        elif profile["wish"] is True and shiki.lower() not in pool_all_mystery:
            await self.shikigami_post_approximate_results(ctx, shiki.lower())

        elif profile["wish"] is True and shiki.lower() in pool_all_mystery:

            users.update_one({"user_id": str(user.id)}, {"$set": {"wish": shiki.lower()}})
            query = users.find_one({
                "user_id": str(user.id),
                "shikigami.name": shiki.lower()}, {
                "_id": 0, "shikigami.$": 1
            })

            if query is None:
                self.shikigami_push_user(user.id, shiki.lower(), False, 0)

            embed = discord.Embed(
                color=user.colour,
                title=f"Wish registered",
                description=f"You have wished for {shiki.title()} shard today",
                timestamp=self.get_timestamp()
            )
            embed.set_footer(icon_url=user.avatar_url, text=f"{user.display_name}")
            embed.set_thumbnail(url=self.get_thumbnail_shikigami(shiki, "pre"))
            await ctx.message.add_reaction("✅")
            await ctx.channel.send(embed=embed)

    @commands.command(aliases=["wishlist", "wl"])
    @commands.guild_only()
    async def wish_show_list(self, ctx):

        wishes = users.find({"wish": {"$ne": True}}, {"_id": 0, "wish": 1, "user_id": 1})

        shard_wishes = []
        for wish in wishes:
            user = self.client.get_user(int(wish["user_id"]))
            wish = wish['wish']
            if wish is False:
                wish = "✅"
            shard_wishes.append(f"▫{user} | {wish.title()}\n")

        await self.wish_show_list_paginate(ctx, shard_wishes)

    async def wish_show_list_paginate(self, ctx, shard_wishes):

        page = 1
        max_lines = 10
        page_total = ceil(len(shard_wishes) / max_lines)
        if page_total == 0:
            page_total = 1

        ordinal = lambda n: "%d%s" % (n, "tsnrhtdd"[(n / 10 % 10 != 1) * (n % 10 < 4) * n % 10::4])

        def create_new_embed_page(page_new):
            end = page_new * max_lines
            start = end - max_lines
            description_new = "".join(shard_wishes[start:end])

            embed_new = discord.Embed(
                color=colour,
                title=f"🗒 Wish List [{ordinal(self.get_time().timetuple().tm_yday)} day]",
                description=f"{description_new}",
                timestamp=self.get_timestamp()
            )
            embed_new.set_footer(text=f"Page: {page_new} of {page_total}")
            return embed_new

        def check(r, u):
            return u != self.client.user and r.message.id == msg.id

        msg = await ctx.channel.send(embed=create_new_embed_page(page))
        await msg.add_reaction("⬅")
        await msg.add_reaction("➡")

        while True:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=60, check=check)
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

    @commands.command(aliases=["fulfill", "ff"])
    @commands.guild_only()
    async def wish_grant(self, ctx, *, member: discord.Member = None):

        user = ctx.author

        if member is None:
            embed = discord.Embed(
                color=ctx.author.colour,
                title=f"fulfill, ff",
                description=f"fulfill a wish from a member in *`{self.prefix}wishlist`*\n"
                            f"no confirmation prompt for fulfilling",
                timestamp=self.get_timestamp()
            )
            embed.add_field(name="Format", value=f"*`{self.prefix}ff <@member>`*")
            await ctx.channel.send(embed=embed)
            return

        try:
            shikigami_wished_for = users.find_one({"user_id": str(member.id)}, {"_id": 0, "wish": 1})["wish"]

        except KeyError:
            embed = discord.Embed(
                title="Invalid member", colour=discord.Colour(colour),
                description="that member doesn't exist or lacks a profile in this guild",
                timestamp=self.get_timestamp()
            )
            await ctx.channel.send(embed=embed)
            return

        except TypeError:
            return

        if shikigami_wished_for is True:
            embed = discord.Embed(
                color=user.colour,
                title=f"Invalid member",
                description=f"member has not placed their daily wish yet",
            )
            await ctx.channel.send(embed=embed)

        elif shikigami_wished_for is False:
            embed = discord.Embed(
                color=user.colour,
                title=f"Wish fulfillment failed",
                description=f"this member has their wish fulfilled already",
            )
            await ctx.channel.send(embed=embed)

        elif check_if_user_has_any_alt_roles(member):
            await ctx.message.add_reaction("❌")

        else:
            profile = users.find_one({
                "user_id": str(user.id), "shikigami.name": shikigami_wished_for}, {
                "_id": 0, "shikigami.$.name": 1
            })

            if profile is None or profile["shikigami"][0]["shards"] == 0:
                embed = discord.Embed(
                    color=user.colour,
                    title=f"Insufficient shards",
                    description=f"lacks a shard to donate",
                )
                await ctx.channel.send(embed=embed)

            elif profile["shikigami"][0]["shards"] > 0:
                users.update_one({"user_id": str(user.id), "shikigami.name": shikigami_wished_for}, {
                    "$inc": {
                        "shikigami.$.shards": -1,
                        "friendship_pass": 3,
                        "friendship": 10
                    }
                })
                await self.perform_add_log("friendship_pass", 3, user.id)
                await self.perform_add_log("friendship", 10, user.id)

                users.update_one({"user_id": str(member.id), "shikigami.name": shikigami_wished_for}, {
                    "$inc": {
                        "shikigami.$.shards": 1
                    },
                    "$set": {
                        "wish": False
                    }
                })

                embed = discord.Embed(
                    color=user.colour,
                    title=f"Wish fulfilled",
                    description=f"Donated 1 {shikigami_wished_for.title()} shard to {member.mention}\n"
                                f"Also acquired 10{e_f} and 3 💗",
                    timestamp=self.get_timestamp()
                )
                embed.set_footer(
                    text=f"{user.display_name}",
                    icon_url=user.avatar_url
                )
                embed.set_thumbnail(url=self.get_thumbnail_shikigami(shikigami_wished_for, "pre"))
                await ctx.channel.send(embed=embed)

    @commands.command(aliases=["reset"])
    @commands.check(check_if_user_has_development_role)
    async def perform_reset(self, ctx, *, args):

        if args == "daily":
            await self.perform_reset_rewards_daily()
            await ctx.message.add_reaction("✅")

        elif args == "weekly":
            await self.perform_reset_rewards_weekly()
            await Frames(self.client).achievements_process_weekly()
            await ctx.message.add_reaction("✅")

        elif args == "boss":
            await self.perform_reset_boss()
            await ctx.message.add_reaction("✅")

        elif args not in ["daily", "weekly", "boss"]:
            embed = discord.Embed(
                colour=discord.Colour(colour),
                title="Invalid argument",
                description="provide a valid argument: `daily`, `weekly`, or `boss`"
            )
            await ctx.channel.send(embed=embed)

    async def perform_reset_rewards_daily(self):

        print("Resetting daily rewards")
        users.update_many({}, {"$set": {"daily": False, "raided_count": 0, "prayers": 3, "wish": True}})
        query = {"level": {"$gt": 1}}
        project = {"ship_name": 1, "shipper1": 1, "shipper2": 1, "level": 1}

        for ship in ships.find(query, project):
            rewards = ship["level"] * 25
            users.update_one({"user_id": ship["shipper1"]}, {"$inc": {"jades": rewards}})
            users.update_one({"user_id": ship["shipper2"]}, {"$inc": {"jades": rewards}})

            await self.perform_add_log("jades", rewards, ship['shipper1'])
            await self.perform_add_log("jades", rewards, ship['shipper2'])

        embed1 = discord.Embed(
            title="🎁 Daily rewards reset and issued", colour=discord.Colour(colour),
            description=f"claim yours using `{self.prefix}daily` and check your income using `{self.prefix}sail`"
        )

        spell_spam_channel = self.client.get_channel(int(id_spell_spam))
        await spell_spam_channel.send(embed=embed1)

    async def perform_reset_rewards_weekly(self):
        print("Resetting weekly rewards")
        users.update_many({}, {"$set": {"weekly": False}})

        embed = discord.Embed(
            title="💝 Weekly rewards reset", colour=discord.Colour(colour),
            description=f"claim yours using `{self.prefix}weekly`"
        )
        spell_spam_channel = self.client.get_channel(int(id_spell_spam))
        await spell_spam_channel.send(embed=embed)

    async def perform_reset_boss(self):
        bosses.update_many({}, {
            "$set": {
                "discoverer": 0,
                "level": 0,
                "damage_cap": 0,
                "total_hp": 0,
                "current_hp": 0,
                "challengers": [],
                "rewards": {}
            }
        })
    
    @commands.command(aliases=["stat", "st"])
    @commands.guild_only()
    async def stat_shikigami(self, ctx, *, name):

        if name.lower() == "all":
            rarity_evolved = [0]
            count_all = []

            for rarity in rarities:

                for result in users.aggregate([
                    {
                        "$match": {
                            "shikigami.evolved": True
                        }
                    }, {
                        "$unwind": {
                            "path": "$shikigami"
                        }
                    }, {
                        "$project": {
                            "shikigami": 1
                        }
                    }, {
                        "$match": {
                            "shikigami.evolved": True,
                            "shikigami.rarity": rarity
                        }
                    }, {
                        "$count": "count"
                    }
                ]):
                    rarity_evolved.append(result["count"])

            for rarity in rarities:

                for result in users.aggregate([
                    {
                        "$project": {
                            "_id": 0,
                            "user_id": 1,
                            "shikigami": 1
                        }
                    }, {
                        "$unwind": {
                            "path": "$shikigami"
                        }
                    }, {
                        "$match": {
                            "shikigami.rarity": rarity
                        }
                    }, {
                        "$group": {
                            "_id": "",
                            "evolved": {
                                "$sum": "$shikigami.owned"
                            }
                        }
                    }
                ]):
                    count_all.append(result["evolved"])

            count_1 = count_all[0] + rarity_evolved[0]
            count_2 = count_all[1] + rarity_evolved[1] * 1
            count_3 = count_all[2] + rarity_evolved[2] * 10
            count_4 = count_all[3] + rarity_evolved[3] * 20
            count_total = count_1 + count_2 + count_3 + count_4

            distribution_1 = round(count_1 / count_total * 100, 3)
            distribution_2 = round(count_2 / count_total * 100, 3)
            distribution_3 = round(count_3 / count_total * 100, 3)
            distribution_4 = round(count_4 / count_total * 100, 3)

            embed = discord.Embed(
                title="Rarity | Distribution | Count", color=ctx.author.colour,
                description=f"```"
                            f"Rarity\n"
                            f"SP    ::    {distribution_1}%  ::   {count_1:,d}\n"
                            f"SSR   ::    {distribution_2}%  ::   {count_2:,d}\n"
                            f"SR    ::   {distribution_3}%  ::   {count_3:,d}\n"
                            f"R     ::   {distribution_4}%  ::   {count_4:,d}"
                            f"```",
                timestamp=self.get_timestamp()
            )

            embed.set_author(name="Summon Pull Statistics")
            embed.add_field(name="Total Amulets Spent", value=f"{count_total:,d}")
            await ctx.channel.send(embed=embed)

        elif name.lower() not in pool_all:
            await self.shikigami_post_approximate_results(ctx, name.lower())

        elif name.lower() in pool_all:

            listings = []
            for entry in users.aggregate([
                {
                    "$match": {
                        "shikigami.name": name.lower()
                    }
                }, {
                    "$project": {
                        "_id": 0,
                        "user_id": 1,
                        "shikigami.name": 1
                    }
                }, {
                    "$unwind": {
                        "path": "$shikigami"
                    }
                }, {
                    "$match": {
                        "shikigami.name": name.lower()
                    }
                }
            ]):
                try:
                    listings.append(self.client.get_user(int(entry["user_id"])).display_name)
                except AttributeError:
                    continue

            thumbnail_url_evo = self.get_thumbnail_shikigami(name.lower(), "evo")
            thumbnail_url_pre = self.get_thumbnail_shikigami(name.lower(), "pre")

            count_pre_evo = 0
            count_evolved = 0

            for result_pre_evo in users.aggregate([
                {
                    "$match": {
                        "shikigami.name": name.lower()
                    }
                }, {
                    "$project": {
                        "_id": 0,
                        "user_id": 1,
                        "shikigami": 1
                    }
                }, {
                    "$unwind": {
                        "path": "$shikigami"
                    }
                }, {
                    "$match": {
                        "shikigami.name": name.lower(),
                        "shikigami.evolved": False
                    }
                }, {
                    "$count": "pre_evo"
                }
            ]):
                count_pre_evo = result_pre_evo["pre_evo"]

            for result_evolved in users.aggregate([
                {
                    "$match": {
                        "shikigami.name": name.lower()
                    }
                }, {
                    "$project": {
                        "_id": 0,
                        "user_id": 1,
                        "shikigami": 1
                    }
                }, {
                    "$unwind": {
                        "path": "$shikigami"
                    }
                }, {
                    "$match": {
                        "shikigami.name": name.lower(),
                        "shikigami.evolved": True
                    }
                }, {
                    "$count": "evolved"
                }
            ]):
                count_evolved = result_evolved["evolved"]

            embed = discord.Embed(
                colour=ctx.author.colour,
                description=f"```"
                            f"Pre-evolve    ::   {count_pre_evo}\n"
                            f"Evolved       ::   {count_evolved}"
                            f"```",
                timestamp=self.get_timestamp()
            )
            embed.set_author(
                name=f"Stats for {name.title()}",
                icon_url=thumbnail_url_pre
            )

            listings_formatted = ", ".join(listings)

            if len(listings) == 0:
                listings_formatted = "None"

            embed.set_thumbnail(url=thumbnail_url_evo)
            embed.add_field(
                name=f"Owned by {len(listings)} {self.pluralize('member', len(listings))}",
                value=f"{listings_formatted}"
            )
            await ctx.channel.send(embed=embed)

    @commands.command(aliases=["parade", "prd"])
    @commands.guild_only()
    @commands.cooldown(1, 60, commands.BucketType.user)
    @commands.check(check_if_user_has_parade_tickets)
    async def perform_parade(self, ctx):
        users.update_one({"user_id": str(ctx.author.id)}, {"$inc": {"parade_tickets": -1}})
        await self.perform_add_log("parade_tickets", -1, ctx.author.id)

        max_rows, beans, beaned_shikigamis, parade_pull = 7, 10, [], []

        for x in range(0, 49):
            roll = random.uniform(0, 100)

            if roll < 5:
                p = random.uniform(0, 1.2)
                if p >= 126 / 109:
                    parade_pull.append(random.choice(pool_sp))
                else:
                    if random.uniform(1, 50) >= 0:
                        parade_pull.append(random.choice(pool_ssr))
                    else:
                        parade_pull.append(random.choice(pool_ssn))
            elif roll <= 25:
                parade_pull.append(random.choice(pool_sr))
            else:
                parade_pull.append(random.choice(pool_r))

        x_init, y_init = random.randint(1, max_rows), random.randint(1, max_rows)
        attachment_link = await self.perform_parade_generate_image(ctx, max_rows, parade_pull, x_init, y_init)

        def generate_parade_embed(listings, remaining_chances):
            value = ", ".join([shiki.title() for shiki in listings])
            if len(value) == 0:
                value = None

            embed = discord.Embed(
                color=ctx.author.color,
                title="🎏 Demon Parade",
                description=f"Beans: 10\n"
                            f"Time Limit: 45 seconds, resets for every bean\n"
                            f"Note: Cannot bean the same shikigami twice",
                timestamp=self.get_timestamp()
            )
            embed.set_image(url=attachment_link)
            embed.add_field(name="Beaned shikigamis", value=value)
            embed.set_footer(text=f"{remaining_chances} beans", icon_url=ctx.author.avatar_url)
            return embed

        msg = await ctx.channel.send(embed=generate_parade_embed(beaned_shikigamis, beans))

        arrows = ["⬅", "⬆", "⬇", "➡"]
        for arrow in arrows:
            await msg.add_reaction(arrow)

        def check(r, u):
            return msg.id == r.message.id and str(r.emoji) in arrows and u.id == ctx.author.id

        def get_new_coordinates(x_coor, y_coor, emoji):
            dictionary = {"⬅": -1, "⬆": -1, "⬇": 1, "➡": 1}
            new_x, new_y = x_coor, y_coor

            if emoji in ["⬅", "➡"]:
                new_x, new_y = x_coor + dictionary[emoji], y_coor
                if new_x > max_rows:
                    new_x = 1

                if new_x < 1:
                    new_x = max_rows

            elif emoji in ["⬇", "⬆"]:
                new_x, new_y = x_coor, y_coor + dictionary[emoji]
                if new_y > max_rows:
                    new_y = 1

                if new_y < 1:
                    new_y = max_rows

            return new_x, new_y

        while beans != -1:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=45, check=check)
            except asyncio.TimeoutError:
                await msg.clear_reactions()
                break
            else:
                bean_x, bean_y = get_new_coordinates(x_init, y_init, str(reaction.emoji))

                def get_bean_shikigami(x_coor_get, y_coor_get):
                    index_bean = (max_rows * y_coor_get) - (max_rows - x_coor_get)
                    return parade_pull[index_bean - 1]

                shikigami_beaned = get_bean_shikigami(bean_x, bean_y)

                if shikigami_beaned not in beaned_shikigamis:
                    beaned_shikigamis.append(shikigami_beaned)

                await msg.edit(embed=generate_parade_embed(beaned_shikigamis, beans))
                await msg.remove_reaction(str(reaction.emoji), user)
                x_init, y_init = bean_x, bean_y
                beans -= 1

        await self.perform_parade_issue_shards(ctx.author, beaned_shikigamis, ctx, msg)

    async def perform_parade_generate_image(self, ctx, max_rows, parade_pull, x_init, y_init):

        achievements_address = []
        for entry in parade_pull:
            try:
                roll = random.uniform(0, 100)
                suffix = "_pre"
                if roll < 30:
                    suffix = "_evo"
                achievements_address.append(f"data/shikigamis/{entry}{suffix}.jpg")
            except KeyError:
                continue

        images = list(map(Image.open, achievements_address))
        new_im = Image.new("RGBA", (max_rows * 90, max_rows * 90))

        def get_coordinates(c):
            a = (c * 90 - (ceil(c / max_rows) - 1) * max_rows * 90) - 90
            b = (ceil(c / max_rows) * 90) - 90
            return a, b

        def add_border(input_image):
            border1, border2 = 9, 9
            address_temp = f"temp/{ctx.message.id}.jpg"
            bordered_thumbnail = ImageOps.expand(input_image, border=(border1, border2), fill=ctx.author.color.to_rgb())
            bordered_thumbnail.save(address_temp)
            img = Image.open(address_temp)
            return img.resize((90, 90))

        def get_bean_shikigami_initial(x_coor_get, y_coor_get):
            index_bean = (max_rows * y_coor_get) - (max_rows - x_coor_get)
            return index_bean - 1

        index_initial = get_bean_shikigami_initial(x_init, y_init)

        for index, item in enumerate(images):
            if index == index_initial:
                new_im.paste(add_border(images[index]), (get_coordinates(index + 1)))
            else:
                new_im.paste(images[index], (get_coordinates(index + 1)))

        address = f"temp/{ctx.author.id}.png"
        new_im.save(address)
        new_photo = discord.File(address, filename=f"{ctx.message.id}.png")
        hosting_channel = self.client.get_channel(int(id_hosting))
        msg = await hosting_channel.send(file=new_photo)
        attachment_link = msg.attachments[0].url

        return attachment_link

    async def perform_parade_issue_shards(self, user, beaned_shikigamis, ctx, msg):
        await msg.clear_reactions()
        self.client.get_command("perform_parade").reset_cooldown(ctx)
        rarities_beaned = []
        for beaned_shikigami in beaned_shikigamis:

            query = users.find_one({
                "user_id": str(user.id),
                "shikigami.name": beaned_shikigami}, {
                "_id": 0, "shikigami.$": 1
            })
            rarities_beaned.append(self.get_rarity_shikigami(beaned_shikigami))

            if query is None:
                self.shikigami_push_user(user.id, beaned_shikigami, False, 0)

            users.update_one({"user_id": str(ctx.author.id), "shikigami.name": beaned_shikigami}, {
                "$inc": {
                    "shikigami.$.shards": 1
                }
            })

        try:
            counter = collections.Counter(rarities_beaned)
            SSR_count = dict(counter)["SSR"]
            if SSR_count >= 4:
                await self.frame_acquisition(user, "Flower Fest", 3500)

        except KeyError:
            pass

    @commands.command(aliases=["pray"])
    @commands.guild_only()
    @commands.cooldown(1, 150, commands.BucketType.user)
    @commands.check(check_if_user_has_prayers)
    async def pray_use(self, ctx):

        embed = discord.Embed(
            title="Pray to the Goddess of Hope and Prosperity!",
            color=ctx.author.colour,
            description="45% chance to obtain rich rewards",
            timestamp=self.get_timestamp()
        )
        embed.set_footer(text=f"{ctx.author.display_name}", icon_url=ctx.author.avatar_url)
        msg = await ctx.channel.send(embed=embed)

        rewards_emoji = [e_j, e_f, e_a, e_c, e_t, e_m, e_s]
        rewards_selection = []

        for x in range(0, 3):
            emoji = random.choice(rewards_emoji)
            await msg.add_reaction(emoji.replace("<", "").replace(">", ""))
            rewards_emoji.remove(emoji)
            rewards_selection.append(emoji)

        def check(r, u):
            return str(r.emoji) in rewards_selection and u == ctx.author

        def get_rewards(y):
            rewards_amount = {e_j: 250, e_f: 50, e_a: 3, e_c: 450000, e_t: 1500, e_m: 150, e_s: 25}
            rewards_text = {
                e_j: "jades",
                e_f: "friendship",
                e_a: "amulets",
                e_c: "coins",
                e_t: "talisman",
                e_m: "medals",
                e_s: "sushi"
            }
            return rewards_amount[y], rewards_text[y]

        try:
            roll = random.randint(1, 100)
            reaction, user = await self.client.wait_for("reaction_add", timeout=150, check=check)

        except asyncio.TimeoutError:
            users.update_one({"user_id": str(ctx.author.id)}, {"$inc": {"prayers": -1}})
            await self.perform_add_log("prayers", -1, ctx.author.id)
            self.client.get_command("pray_use").reset_cooldown(ctx)

        else:
            users.update_one({"user_id": str(ctx.author.id)}, {"$inc": {"prayers": -1}})
            await self.perform_add_log("prayers", -1, ctx.author.id)

            if roll >= 55:
                embed = discord.Embed(
                    title=f"Prayer results", color=ctx.author.colour,
                    description=f"{next(prayer_ignored)}",
                    timestamp=self.get_timestamp()
                )
                embed.set_footer(text=f"{ctx.author.display_name}", icon_url=ctx.author.avatar_url)
                await msg.edit(embed=embed)
                self.client.get_command("pray_use").reset_cooldown(ctx)

            else:
                amount, rewards = get_rewards(str(reaction.emoji))
                embed = discord.Embed(
                    title=f"Prayer results", color=ctx.author.colour,
                    description=f"{next(prayer_heard)} You obtained {amount:,d}{str(reaction.emoji)}",
                    timestamp=self.get_timestamp()
                )
                embed.set_footer(text=f"{ctx.author.display_name}", icon_url=ctx.author.avatar_url)
                users.update_one({"user_id": str(ctx.author.id)}, {"$inc": {rewards: amount}})
                await self.perform_add_log(rewards, amount, user.id)
                await msg.edit(embed=embed)
                self.client.get_command("pray_use").reset_cooldown(ctx)

    @commands.command(aliases=["baa"])
    @commands.guild_only()
    async def bounty_add_alias(self, ctx, name, *, alias):

        name_formatted = name.replace("_", " ")

        bounties.update_one({"aliases": name.lower()}, {"$push": {"aliases": alias.lower()}})
        embed = discord.Embed(
            colour=discord.Colour(colour),
            title="Bounty profile updated",
            description=f"successfully added {alias} to {name_formatted.title()}",
            timestamp=self.get_timestamp()
        )
        await ctx.channel.send(embed=embed)

    @commands.command(aliases=["bal"])
    @commands.guild_only()
    async def bounty_add_location(self, ctx, name, *, location):

        bounties.update_one({"aliases": name.lower()}, {"$push": {"location": location}})
        embed = discord.Embed(
            colour=discord.Colour(colour),
            title=f"Successfully added new location to {name.title()}",
            description=f"{location}",
            timestamp=self.get_timestamp()
        )
        await ctx.channel.send(embed=embed)

    @commands.command(aliases=["b", "bounty"])
    @commands.guild_only()
    async def bounty_query(self, ctx, *, query):

        if len(query) < 2:
            return

        bounty_search1 = bounties.find_one({"aliases": query.lower()}, {"_id": 0})
        bounty_search2 = bounties.find({"aliases": {"$regex": f"^{query[:2].lower()}"}}, {"_id": 0})

        if bounty_search1 is not None:
            try:
                thumbnail = self.get_thumbnail_shikigami(bounty_search1["bounty"].lower(), "pre")
            except TypeError:
                thumbnail = ""

            name = bounty_search1["bounty"].title()
            description = ("• " + "\n• ".join(bounty_search1["location"]))
            aliases = bounty_search1["aliases"]
            text = ", ".join(aliases)

            embed = discord.Embed(
                color=ctx.author.colour,
                title=f"Bounty location(s) for {name}",
                description=description,
                timestamp=self.get_timestamp()
            )
            embed.set_footer(icon_url=thumbnail, text=f"aliases: {text}")
            await ctx.channel.send(embed=embed)

        elif bounty_search2 is not None:
            bounty_list = []
            for result in bounty_search2:
                bounty_list.append(result["bounty"])

            embed = discord.Embed(
                title="No exact results", colour=discord.Colour(colour),
                description="the provided name/keyword is non-existent",
                timestamp=self.get_timestamp()
            )
            embed.add_field(name="Possible queries", value="*{}*".format(", ".join(bounty_list)))
            await ctx.channel.send(embed=embed)

    @commands.command(aliases=["daily"])
    @commands.guild_only()
    async def claim_rewards_daily(self, ctx):
        user = ctx.author
        profile = users.find_one({"user_id": str(user.id)}, {"_id": 0, "daily": 1})

        if profile["daily"] is False:
            await self.claim_rewards_daily_give(user, ctx)

        elif profile["daily"] is True:
            embed = discord.Embed(
                title="Collection failed", colour=discord.Colour(colour),
                description=f"already collected today, check back tomorrow"
            )
            await ctx.channel.send(embed=embed)

    async def claim_rewards_daily_give(self, user, ctx):
        friendship_pass, jades, coins, realm_ticket = 5, 100, 50000, 3
        encounter_ticket, parade_tickets, sushi = 4, 3, 150

        users.update_one({"user_id": str(user.id)}, {
            "$inc": {
                "friendship_pass": friendship_pass,
                "jades": jades,
                "coins": coins,
                "realm_ticket": realm_ticket,
                "encounter_ticket": encounter_ticket,
                "parade_tickets": parade_tickets,
                "sushi": sushi
            },
            "$set": {
                "daily": True
            }
        })

        await self.perform_add_log("friendship_pass", friendship_pass, user.id)
        await self.perform_add_log("jades", jades, user.id)
        await self.perform_add_log("coins", coins, user.id)
        await self.perform_add_log("realm_ticket", realm_ticket, user.id)
        await self.perform_add_log("encounter_ticket", encounter_ticket, user.id)
        await self.perform_add_log("parade_tickets", parade_tickets, user.id)
        await self.perform_add_log("sushi", sushi, user.id)

        embed = discord.Embed(
            color=ctx.author.colour,
            title="🎁 Daily rewards",
            description=f"A box containing {friendship_pass} 💗, {jades}{e_j}, {coins:,d}{e_c}, {realm_ticket} 🎟, "
                        f"{encounter_ticket} 🎫, {parade_tickets} 🎏, {sushi} 🍣",
            timestamp=self.get_timestamp()
        )
        embed.set_footer(text=f"Opened by {user.display_name}", icon_url=user.avatar_url)
        await ctx.channel.send(embed=embed)
    
    @commands.command(aliases=["weekly"])
    @commands.guild_only()
    async def claim_rewards_weekly(self, ctx):

        user = ctx.author
        profile = users.find_one({"user_id": str(user.id)}, {"_id": 0, "weekly": 1})

        if profile["weekly"] is False:
            await self.claim_rewards_weekly_give(user, ctx)

        elif profile["weekly"] is True:
            embed = discord.Embed(
                title="Collection Failed", colour=discord.Colour(colour),
                description=f"already collected this reset, check back next week"
            )
            await ctx.channel.send(embed=embed)

    async def claim_rewards_weekly_give(self, user, ctx):
        jades, coins, amulets, sushi = 750, 250000, 10, 150

        users.update_one({"user_id": str(user.id)}, {
            "$inc": {
                "jades": jades,
                "coins": coins,
                "amulets": amulets,
                "sushi": sushi
            },
            "$set": {
                "weekly": True
            }
        })
        await self.perform_add_log("jades", jades, user.id)
        await self.perform_add_log("coins", coins, user.id)
        await self.perform_add_log("amulets", amulets, user.id)
        await self.perform_add_log("sushi", sushi, user.id)

        embed = discord.Embed(
            color=ctx.author.colour,
            title="💝 Weekly rewards",
            description=f"A mythical box containing {jades:,d}{e_j}, {coins:,d}{e_c}, and {amulets:,d}{e_a}, & "
                        f"{sushi:,d}{e_s}",
            timestamp=self.get_timestamp()
        )
        embed.set_footer(text=f"Opened by {user.display_name}", icon_url=user.avatar_url)
        await ctx.channel.send(embed=embed)
    
    @commands.command(aliases=["profile", "p", "pf"])
    @commands.guild_only()
    async def profile_show(self, ctx, *, member: discord.Member = None):

        if member is None:
            await self.profile_post(ctx.author, ctx)

        else:
            await self.profile_post(member, ctx)

    async def profile_post(self, member, ctx):

        p = users.find_one({
            "user_id": str(member.id)}, {
            "_id": 0, "SP": 1, "SSR": 1, "SR": 1, "R": 1, "amulets": 1,
            "amulets_spent": 1, "experience": 1, "level": 1, "level_exp_next": 1,
            "jades": 1, "coins": 1, "medals": 1, "realm_ticket": 1, "display": 1, "friendship": 1,
            "encounter_ticket": 1, "friendship_pass": 1, "talisman": 1, "prayers": 1, "achievements": 1,
            "achievements_count": 1, "parade_tickets": 1, "N": 1, "amulets_spent_b": 1, "amulets_b": 1, "SSN": 1,
            "sushi": 1, "nether_pass": 1
        })

        ships_count = ships.find({"code": {"$regex": f".*{ctx.author.id}.*"}}).count()
        amulets = p["amulets"]
        amulets_b = p["amulets_b"]
        amulets_spent = p["amulets_spent"]
        amulets_spent_b = p["amulets_spent_b"]
        exp = p["experience"]
        level = p["level"]
        level_exp_next = p["level_exp_next"]
        jades = p["jades"]
        coins = p["coins"]
        medals = p["medals"]
        realm_ticket = p["realm_ticket"]
        display = p["display"]
        friendship_points = p["friendship"]
        enc_ticket = p["encounter_ticket"]
        friendship_pass = p["friendship_pass"]
        talismans = p["talisman"]
        prayers = p["prayers"]
        achievements = p["achievements"]
        parade = p["parade_tickets"]
        sushi = p["sushi"]
        nether_pass = p["nether_pass"]

        embed = discord.Embed(color=member.colour, timestamp=self.get_timestamp())

        if display is not None:
            evo = users.find_one({
                "user_id": str(member.id), "shikigami.name": display}, {
                "shikigami.$.name": 1
            })["shikigami"][0]["evolved"]
            thumbnail = self.get_thumbnail_shikigami(display.lower(), self.get_evo_link(evo))
            embed.set_thumbnail(url=thumbnail)

        else:
            embed.set_thumbnail(url=member.avatar_url)

        def get_emoji_nether(x):
            if x is False:
                return "❌"
            return "✅"

        embed.set_author(
            name=f"{member.display_name}'s profile",
            icon_url=member.avatar_url
        )
        embed.add_field(
            name=f"{e_x} Experience | Nether Pass",
            value=f"Level: {level} ({exp:,d}/{level_exp_next:,d}) | {get_emoji_nether(nether_pass)}"
        )
        embed.add_field(
            name=f"{e_1} | {e_2} | {e_3} | {e_4} | {e_5} | {e_6}",
            value=f"{p['SP']} | {p['SSR']} | {p['SR']} | {p['R']:,d} | {p['N']:,d} | "
                  f"{p['SSN']:,d}",
            inline=False
        )
        embed.add_field(
            name=f"{e_b} Broken Amulets",
            value=f"On Hand: {amulets_b} | Used: {amulets_spent_b:,d}"
        )
        embed.add_field(
            name=f"{e_a} Mystery Amulets",
            value=f"On Hand: {amulets} | Used: {amulets_spent:,d}", inline=False
        )
        embed.add_field(
            name=f"💗 | 🎟 | 🎫 | 🚢 | 🙏 | 🎏",
            value=f"{friendship_pass} | {realm_ticket:,d} | {enc_ticket:,d} | {ships_count} | {prayers} | {parade}",
            inline=False
        )
        embed.add_field(
            name=f"🍣 | {e_f} | {e_t} | {e_m} | {e_j} | {e_c}",
            value=f"{sushi} | {friendship_points:,d} | {talismans:,d} | {medals:,d} | {jades:,d} | {coins:,d}"
        )
        msg = await ctx.channel.send(embed=embed)
        await msg.add_reaction("🖼")

        def check(r, u):
            return str(r.emoji) in ["🖼"] and r.message.id == msg.id and u.bot is False and ctx.author.id == u.id

        def check2(r, u):
            return str(r.emoji) in ["➡", "⬅"] and r.message.id == msg.id and u.bot is False and ctx.author.id == u.id

        async def generate_embed(page_new):
            embed_new = discord.Embed(color=member.colour, timestamp=self.get_timestamp())
            embed_new.set_author(
                name=f"{member.display_name}'s achievements [{len(achievements)}]",
                icon_url=member.avatar_url
            )
            embed_new.set_image(url=await self.profile_generate_frame_image_new(member, achievements, page_new))
            embed_new.set_footer(text="Hall of Frames")
            return embed_new

        page = 1
        page_total = ceil(len(achievements) / 20)

        try:
            await self.client.wait_for("reaction_add", timeout=15, check=check)
        except asyncio.TimeoutError:
            await msg.clear_reactions()
        else:
            await msg.edit(embed=await generate_embed(page))
            await msg.clear_reactions()
            await msg.add_reaction("➡")

        try:
            reaction, user = await self.client.wait_for("reaction_add", timeout=15, check=check2)
        except asyncio.TimeoutError:
            await msg.clear_reactions()
        else:
            if str(reaction.emoji) == "➡":
                page += 1

            if page > page_total:
                page = 1
            await msg.edit(embed=await generate_embed(page))

    async def profile_generate_frame_image_new(self, member, achievements, page_new):

        end = page_new * 20
        start = end - 20

        achievements_address = []
        for entry in achievements:
            try:
                achievements_address.append(f"data/achievements/{entry['name']}.png")
            except KeyError:
                continue

        images = list(map(Image.open, achievements_address[start:end]))

        width, height = 1000, 800
        new_im = Image.new("RGBA", (width, height))

        def get_coordinates(c):
            x = (c * 200 - (ceil(c / 5) - 1) * 1000) - 200
            y = (ceil(c / 5) * 200) - 200
            return x, y

        for q, item in enumerate(images):
            new_im.paste(images[q], (get_coordinates(q + 1)))

        address = f"temp/{member.id}.png"
        new_im.save(address)
        new_photo = discord.File(address, filename=f"{member.id}.png")
        hosting_channel = self.client.get_channel(int(id_hosting))
        msg = await hosting_channel.send(file=new_photo)
        attachment_link = msg.attachments[0].url
        return attachment_link

    @commands.command(aliases=["set", "display"])
    @commands.guild_only()
    async def profile_change_shikigami_main(self, ctx, *, select):

        user = ctx.author
        select_formatted = select.lower()

        if select_formatted is None:
            users.update_one({"user_id": str(user.id)}, {"$set": {"display": select_formatted}})
            await ctx.message.add_reaction("✅")

        elif select_formatted not in pool_all_mystery:
            await self.shikigami_post_approximate_results(ctx, select_formatted)

        elif select_formatted in pool_all_mystery:
            count = users.count_documents({"user_id": str(user.id), "shikigami.name": select_formatted})

            if count != 1:
                embed = discord.Embed(
                    colour=discord.Colour(colour),
                    title="Invalid selection",
                    description=f"this shikigami is not in your possession"
                )
                await ctx.channel.send(embed=embed)

            elif count == 1:
                users.update_one({"user_id": str(user.id)}, {"$set": {"display": select_formatted}})
                await ctx.message.add_reaction("✅")

    @commands.command(aliases=["collections", "col", "collection"])
    @commands.guild_only()
    async def shikigami_image_show_collected(self, ctx, arg1, *, member: discord.Member = None):

        rarity = str(arg1.upper())

        if rarity not in rarities:
            raise commands.MissingRequiredArgument(ctx.author)

        elif member is None:
            await self.shikigami_show_post_collected(ctx.author, rarity, ctx)

        else:
            await self.shikigami_show_post_collected(member, rarity, ctx)

    async def shikigami_show_post_collected(self, member, rarity, ctx):

        user_shikigamis_with_evo = []
        user_shikigamis = []
        for entry in users.aggregate([{
            "$match": {
                "user_id": str(member.id)}}, {
            "$unwind": {
                "path": "$shikigami"}}, {
            "$match": {
                "shikigami.rarity": rarity}}, {
            "$project": {
                "_id": 0,
                "shikigami.name": 1,
                "shikigami.owned": 1,
                "shikigami.shards": 1,
                "shikigami.evolved": 1
            }}, {
            "$match": {
                "shikigami.owned": {
                    "$gt": 0
                }}}
        ]):
            user_shikigamis_with_evo.append((entry["shikigami"]["name"], entry["shikigami"]["evolved"]))
            user_shikigamis.append(entry["shikigami"]["name"])

        pool_rarity_select = []
        for entry in shikigamis.find({"rarity": rarity}, {"_id": 0, "name": 1}):
            pool_rarity_select.append(entry["name"])

        uncollected_list = list(set(pool_rarity_select) - set(user_shikigamis))

        link = await self.shikigami_show_post_collected_generate(
            user_shikigamis_with_evo, uncollected_list, pool_rarity_select, rarity, member
        )

        embed = discord.Embed(
            title=f"{self.get_rarity_emoji(rarity)} Collection",
            color=member.colour,
            timestamp=self.get_timestamp()
        )
        embed.set_image(url=link)
        embed.set_footer(icon_url=member.avatar_url, text=f"{member.display_name}")
        await ctx.channel.send(embed=embed)

    async def shikigami_show_post_collected_generate(self, user_shikis, user_unc, pool_rarity_select, rarity, member):

        images = []
        for entry in user_shikis:
            address = f"data/shikigamis/{entry[0]}_pre.jpg"
            if entry[1] is True:
                address = f"data/shikigamis/{entry[0]}_evo.jpg"
            images.append(Image.open(address))

        for entry in user_unc:
            address = f"data/shikigamis/{entry}_pre.jpg"
            images.append(Image.open(address).convert("LA"))

        w = self.get_variables(rarity)[0]
        col = self.get_variables(rarity)[1]

        def get_image_variables(x):
            total_shikis = len(x)
            h = ceil(total_shikis / col) * 90
            return w, h

        width, height = get_image_variables(pool_rarity_select)
        new_im = Image.new("RGBA", (width, height))

        def get_coordinates(c):
            a = (c * 90 - (ceil(c / col) - 1) * w) - 90
            b = (ceil(c / col) * 90) - 90
            return a, b

        for index, item in enumerate(images):
            new_im.paste(images[index], (get_coordinates(index + 1)))

        address = f"temp/{member.id}.png"
        new_im.save(address)
        new_photo = discord.File(address, filename=f"{member.id}.png")
        hosting_channel = self.client.get_channel(int(id_hosting))
        msg = await hosting_channel.send(file=new_photo)
        attachment_link = msg.attachments[0].url
        return attachment_link

    @commands.command(aliases=["shikilist", "sl"])
    @commands.guild_only()
    async def shikigami_list_show_collected(self, ctx, arg1, *, member: discord.Member = None):

        rarity = str(arg1.upper())

        if rarity not in rarities:
            raise commands.MissingRequiredArgument(ctx.author)

        elif member is None:
            await self.shikigami_list_post_collected(ctx.author, rarity, ctx)

        else:
            await self.shikigami_list_post_collected(member, rarity, ctx)

    async def shikigami_list_post_collected(self, member, rarity, ctx):

        user_shikigamis = []
        for entry in users.aggregate([{
            "$match": {
                "user_id": str(member.id)
            }}, {
            "$unwind": {
                "path": "$shikigami"
            }}, {
            "$match": {
                "shikigami.rarity": rarity
            }}, {
            "$project": {
                "_id": 0,
                "shikigami.name": 1,
                "shikigami.owned": 1,
                "shikigami.shards": 1
            }
        }]):
            user_shikigamis.append((
                entry["shikigami"]["name"],
                entry["shikigami"]["owned"],
                entry["shikigami"]["shards"]
            ))

        user_shikigamis_sorted = sorted(user_shikigamis, key=lambda x: x[1], reverse=True)

        formatted_list = []
        for shiki in user_shikigamis_sorted:
            formatted_list.append(f"• {shiki[0].title()} | `x{shiki[1]} [{shiki[2]} shards]`\n")

        await self.shikigami_list_paginate(member, formatted_list, rarity, ctx, "Shikigamis")

    async def shikigami_list_paginate(self, member, formatted_list, rarity, ctx, title):

        page = 1
        max_lines = 10
        page_total = ceil(len(formatted_list) / max_lines)
        if page_total == 0:
            page_total = 1

        def create_new_embed_page(page_new):
            end = page_new * max_lines
            start = end - max_lines
            embed_new = discord.Embed(color=member.colour, timestamp=self.get_timestamp())
            embed_new.title = f"{self.get_rarity_emoji(rarity.upper())} {title}"
            embed_new.description = "".join(formatted_list[start:end])
            embed_new.set_footer(
                text=f"Page: {page_new} of {page_total}",
                icon_url=member.avatar_url
            )
            return embed_new

        msg = await ctx.channel.send(embed=create_new_embed_page(1))
        await msg.add_reaction("⬅")
        await msg.add_reaction("➡")

        def check(r, m):
            return m != self.client.user and r.message.id == msg.id

        while True:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=60, check=check)
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

    @commands.command(aliases=["addshiki", "as"])
    @commands.check(check_if_user_has_development_role)
    async def shikigami_add(self, ctx, *args):

        # ;addshiki <rarity> <shikigami_name> <yes/no> <broken/mystery> <pre_link> <evo_link>

        if len(args) < 6:
            return

        elif len(args) == 6:
            shrine = False

            if args[2].lower() == "yes":
                shrine = True

            profile = {
                "name": (args[1].replace("_", " ")).lower(),
                "rarity": args[0].upper(),
                "shrine": shrine,
                "thumbnail": {
                    "pre": args[4],
                    "evo": args[5]
                },
                "demon_quiz": None,
                "amulet": args[3].lower()
            }

            shikigamis.insert_one(profile)
            await ctx.message.add_reaction("✅")
        else:
            await ctx.message.add_reaction("❌")

    @commands.command(aliases=["update"])
    @commands.check(check_if_user_has_development_role)
    async def shikigami_update(self, ctx, *args):

        if len(args) == 0:
            return

        elif len(args) == 3:
            query = (args[0].replace("_", " ")).lower()
            profile_shikigami = shikigamis.find_one({
                "shikigami.name": query}, {
                "_id": 0,
                "shikigami": {
                    "$elemMatch": {
                        "name": query
                    }}
            })

            try:
                if profile_shikigami["shikigami"][0]["profiler"] != "":
                    await ctx.message.add_reaction("❌")

            except KeyError:
                try:
                    pre_evo = args[1]
                    evo = args[2]
                    profiler = ctx.author.display_name

                    shikigamis.update_one({"shikigami.name": query}, {
                        "$set": {
                            "shikigami.$.thumbnail.pre_evo": pre_evo,
                            "shikigami.$.thumbnail.evo": evo,
                            "shikigami.$.profiler": str(profiler)
                        }
                    })
                except KeyError:
                    await ctx.message.add_reaction("❌")
        else:
            await ctx.message.add_reaction("❌")

    @commands.command(aliases=["shrine", "shr"])
    @commands.guild_only()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def shikigami_shrine(self, ctx, arg1="", *, args=""):

        user = ctx.author
        shiki = args.lower()

        def get_talisman_required(x):
            dictionary = {"SSR": 350000, "SR": 150000, "R": 50000}
            return dictionary[x]

        if arg1.lower() not in ["sacrifice", "exchange", "s", "exc"]:
            raise commands.MissingRequiredArgument(ctx.author)

        elif arg1.lower() in ["sacrifice", "s"] and len(args) == 0:
            embed = discord.Embed(
                title="shrine sacrifice, shr s", colour=discord.Colour(colour),
                description="sacrifice your shikigamis to the shrine in exchange for talismans"
            )
            embed.add_field(
                name="Rarity :: Talisman",
                value="```"
                      "SP     ::  50,000\n"
                      "SSR    ::  25,000\n"
                      "SR     ::   1,000\n"
                      "R      ::      75\n"
                      "```",
                inline=False
            )
            embed.add_field(
                name="Format",
                value=f"*`{self.prefix}shrine s <shikigami>`*"
            )
            await ctx.channel.send(embed=embed)

        elif arg1.lower() in ["exchange", "exc"] and len(args) == 0:
            embed = discord.Embed(
                title="shrine exchange, shrine exc", colour=discord.Colour(colour),
                description="exchange your talismans for exclusive shrine only shikigamis"
            )
            embed.add_field(
                name="Shikigami :: Talisman",
                value="```"
                      "Juzu          ::     50,000\n"
                      "Usagi         ::     50,000\n"
                      "Tenjo Kudari  ::     50,000\n"
                      "Mannendake    ::    150,000\n"
                      "Jinmenju      ::    150,000\n"
                      "Kainin        ::    150,000\n"
                      "Ryomen        ::    350,000"
                      "```",
                inline=False
            )
            embed.add_field(
                name="Formats",
                value=f"*`{self.prefix}shrine exc <shikigami>`*"
            )
            await ctx.channel.send(embed=embed)

        elif arg1.lower() in ["sacrifice", "s"] and shiki not in pool_all_mystery:
            await self.shikigami_post_approximate_results(ctx, shiki)

        elif arg1.lower() in ["exchange", "exc"] and shiki not in pool_shrine:
            await self.shikigami_post_approximate_results(ctx, shiki)

        elif arg1.lower() in ["sacrifice", "s"] and shiki in pool_all_mystery:

            try:
                request = users.find_one({
                    "user_id": str(user.id), "shikigami.name": shiki}, {
                    "_id": 0, "shikigami.$.name": 1
                })
                count_shikigami = request["shikigami"][0]["owned"]
                rarity = request["shikigami"][0]["rarity"]
                talismans = self.get_talisman_acquire(rarity)

            except TypeError:
                embed = discord.Embed(
                    colour=user.colour,
                    title=f"Invalid shikigami",
                    description=f"no shikigami {shiki.title()} in your possession yet"
                )
                await ctx.channel.send(embed=embed)
                return

            def check(m):
                try:
                    int(m.content)
                    return m.author == ctx.author and m.channel == ctx.channel
                except TypeError:
                    return
                except ValueError:
                    return

            try:
                embed = discord.Embed(
                    colour=user.colour,
                    title=f"Specify amount",
                    description=f"You currently have {count_shikigami:,d} {shiki.title()}",
                    timestamp=self.get_timestamp()
                )
                embed.set_thumbnail(url=self.get_thumbnail_shikigami(shiki, "evo"))
                embed.set_footer(text=f"{user.display_name}", icon_url=user.avatar_url)
                msg = await ctx.channel.send(embed=embed)
                answer = await self.client.wait_for("message", timeout=15, check=check)

            except asyncio.TimeoutError:
                embed = discord.Embed(
                    title="Invalid amount", colour=user.colour,
                    description=f"provide a valid integer",
                )
                embed.set_thumbnail(url=self.get_thumbnail_shikigami(shiki, "evo"))
                embed.set_footer(text=f"{user.display_name}", icon_url=user.avatar_url)
                await ctx.channel.send(embed=embed)

            else:
                request_shrine = int(answer.content)
                if count_shikigami >= request_shrine:
                    final_talismans = talismans * request_shrine
                    users.update_one({
                        "user_id": str(user.id),
                        "shikigami.name": shiki}, {
                        "$inc": {
                            "shikigami.$.owned": - request_shrine,
                            "talisman": final_talismans,
                            f"{rarity}": - request_shrine
                        }
                    })
                    await self.perform_add_log("talisman", final_talismans, user.id)
                    embed = discord.Embed(
                        title="Shrine successful", colour=user.colour,
                        description=f"You shrined {shiki.title()} for {final_talismans:,d}{e_t}",
                        timestamp=self.get_timestamp()
                    )
                    embed.set_thumbnail(url=self.get_thumbnail_shikigami(shiki, "evo"))
                    embed.set_footer(text=f"{user.display_name}", icon_url=user.avatar_url)
                    await msg.edit(embed=embed)

                else:
                    embed = discord.Embed(
                        title="Insufficient shikigamis", colour=user.colour,
                        description=f"You lack that amount of shikigami {shiki.title()}",
                        timestamp=self.get_timestamp()
                    )
                    embed.set_thumbnail(url=self.get_thumbnail_shikigami(shiki, "evo"))
                    embed.set_footer(text=f"{user.display_name}", icon_url=user.avatar_url)
                    await ctx.channel.send(embed=embed)

        elif arg1.lower() in ["exchange", "exc"] and shiki in pool_shrine:

            rarity = shikigamis.find_one({"name": shiki}, {"_id": 0, "rarity": 1})["rarity"]
            talisman = users.find_one({"user_id": str(user.id)}, {"_id": 0, "talisman": 1})["talisman"]
            required_talisman = get_talisman_required(rarity)

            if talisman >= required_talisman:
                embed = discord.Embed(
                    title="Exchange confirmation", colour=discord.Colour(colour),
                    description=f"confirm exchange of {required_talisman:,d}{e_t} for a {shiki.title()}",
                    timestamp=self.get_timestamp()
                )
                embed.set_footer(icon_url=user.avatar_url, text=f"{user.display_name}")
                confirm_ = await ctx.channel.send(embed=embed)
                await confirm_.add_reaction("✅")

                def check(r, u):
                    return u == ctx.author and str(r.emoji) == "✅"

                try:
                    await self.client.wait_for("reaction_add", timeout=10.0, check=check)

                except asyncio.TimeoutError:
                    embed = discord.Embed(
                        title="Timeout!", colour=discord.Colour(colour),
                        description=f"no confirmation received for {e_t} exchange",
                    )
                    embed.set_footer(icon_url=user.avatar_url, text=f"{user.display_name}")
                    await confirm_.edit(embed=embed)
                    await confirm_.clear_reactions()

                else:
                    query = users.find_one({
                        "user_id": str(user.id),
                        "shikigami.name": shiki}, {
                        "_id": 0, "shikigami.$": 1
                    })

                    if query is None:
                        self.shikigami_push_user(user.id, shiki, False, 0)

                    users.update_one({
                        "user_id": str(user.id),
                        "shikigami.name": shiki}, {
                        "$inc": {
                            "shikigami.$.owned": 1,
                            "talisman": - required_talisman,
                            f"{rarity}": 1
                        }
                    })
                    await self.perform_add_log("talisman", - required_talisman, user.id)
                    embed = discord.Embed(
                        title="Exchange success!", colour=discord.Colour(colour),
                        description=f"You acquired {shiki.title()} for {required_talisman:,d}{e_t}",
                        timestamp=self.get_timestamp()
                    )
                    embed.set_footer(icon_url=user.avatar_url, text=f"{user.display_name}")
                    await confirm_.edit(embed=embed)

            elif talisman < required_talisman:
                embed = discord.Embed(
                    title="Insufficient talismans", colour=discord.Colour(colour),
                    description=f"You lack {required_talisman - talisman:,d}{e_t}",
                )
                embed.set_footer(icon_url=user.avatar_url, text=f"{user.display_name}")
                await ctx.channel.send(embed=embed)

        self.client.get_command("shikigami_shrine").reset_cooldown(ctx)

    @commands.command(aliases=["evolve", "evo"])
    async def perform_evolution(self, ctx, *args):

        user = ctx.author
        query = (" ".join(args)).lower()
        profile_my_shikigami = users.find_one({
            "user_id": str(user.id)}, {
            "_id": 0,
            "shikigami": {
                "$elemMatch": {
                    "name": query
                }}
        })

        if len(query) < 2:
            embed = discord.Embed(
                title="evolve, evo", colour=discord.Colour(colour),
                description="perform evolution of owned shikigami"
            )
            embed.add_field(
                name="Mechanics",
                inline=False,
                value="```"
                      "• SP  :: pre-evolved\n"
                      "• SSR :: requires 1 dupe\n"
                      "• SR  :: requires 10 dupes\n"
                      "• R   :: requires 20 dupes"
                      "```"
            )
            embed.add_field(name="Format", value=f"*`{self.prefix}evolve <shikigami>`*")
            await ctx.channel.send(embed=embed)

        elif shikigamis.find_one({"name": query}, {"_id": 0}) is None:
            await self.shikigami_post_approximate_results(ctx, query)

        elif profile_my_shikigami == {}:
            embed = discord.Embed(
                title="Invalid selection", colour=discord.Colour(colour),
                description=f"this shikigami is not in your possession yet",
            )
            await ctx.channel.send(embed=embed)

        elif profile_my_shikigami != {}:
            rarity = profile_my_shikigami["shikigami"][0]["rarity"]
            count = profile_my_shikigami["shikigami"][0]["owned"]
            evo = profile_my_shikigami["shikigami"][0]["evolved"]
            await self.perform_evolution_shikigami(ctx, rarity, evo, user, query, count)

    async def perform_evolution_shikigami(self, ctx, rarity, evo, user, query, count):
        if rarity == "SP":
            embed = discord.Embed(
                colour=discord.Colour(colour),
                title="Invalid shikigami",
                description=f"this shikigami is already evolved upon summoning"
            )
            await ctx.channel.send(embed=embed)

        elif evo is True:
            embed = discord.Embed(
                colour=discord.Colour(colour),
                title="Evolution failed",
                description=f"Your {query.title()} is already evolved",
            )
            embed.set_footer(icon_url=user.avatar_url, text=f"{user.display_name}")
            embed.set_thumbnail(url=self.get_thumbnail_shikigami(query, "evo"))
            await ctx.channel.send(embed=embed)

        elif evo is False:
            rarity_count = self.get_evo_requirement(rarity)

            if count >= rarity_count:

                users.update_one({
                    "user_id": str(user.id),
                    "shikigami.name": query}, {
                    "$inc": {
                        "shikigami.$.owned": -(rarity_count - 1),
                        f"{rarity}": -(rarity_count - 1)
                    },
                    "$set": {
                        "shikigami.$.evolved": True,
                        "shikigami.$.shards": 5
                    }
                })

                shikigami_profile = shikigamis.find_one({"name": query}, {"_id": 0, "thumbnail": 1})
                image_url = shikigami_profile["thumbnail"]["evo"]

                embed = discord.Embed(
                    colour=user.colour,
                    title="Evolution successful",
                    description=f"You have evolved your {query.title()}\n"
                                f"Also acquired 5 shards of this shikigami",
                    timestamp=self.get_timestamp()
                )
                embed.set_footer(icon_url=user.avatar_url, text=f"{user.display_name}")
                embed.set_thumbnail(url=image_url)
                await ctx.channel.send(embed=embed)

                if query == "orochi":
                    await self.frame_acquisition(user, "Sword Swallowing-Snake", jades=2500)

            elif count == 0:
                embed = discord.Embed(
                    colour=discord.Colour(colour),
                    title="Invalid selection",
                    description=f"this shikigami is not in your possession"
                )
                await ctx.channel.send(embed=embed)

            elif count <= (self.get_evo_requirement(rarity) - 1):
                required = rarity_count - count
                noun_duplicate = self.pluralize('dupe', required)
                embed = discord.Embed(
                    colour=discord.Colour(colour),
                    title="Insufficient shikigamis",
                    description=f"You lack {required} more {query.title()} {noun_duplicate} to evolve",
                )
                await ctx.channel.send(embed=embed)

    @commands.command(aliases=["sail"])
    @commands.guild_only()
    async def friendship_check_sail(self, ctx, *, member: discord.Member = None):

        if member is None:
            await self.friendship_check_sail_post(ctx.author, ctx.channel)

        else:
            await self.friendship_check_sail_post(member, ctx.channel)

    async def friendship_check_sail_post(self, user, channel):

        request = ships.find({"level": {"$gt": 1}, "code": {"$regex": f".*{user.id}.*"}})
        ships_count = request.count()
        total_rewards = 0

        for ship in request:
            total_rewards += ship["level"] * 25

        embed = discord.Embed(
            color=user.colour,
            description=f"Your total daily ship sail rewards: {total_rewards:,d}{e_j}",
            timestamp=self.get_timestamp()
        )
        embed.set_footer(
            text=f"{ships_count} {self.pluralize('ship', ships_count)}",
            icon_url=user.avatar_url
        )
        await channel.send(embed=embed)

    @commands.command(aliases=["ships"])
    @commands.guild_only()
    async def friendship_ship_show_all(self, ctx, *, member: discord.Member = None):

        if member is None:
            await self.friendship_ship_show_generate(ctx.author, ctx)

        else:
            await self.friendship_ship_show_generate(member, ctx)

    async def friendship_ship_show_generate(self, member, ctx):

        ships_listings = []
        for ship in ships.find({"code": {"$regex": f".*{member.id}.*"}}):
            ship_entry = [ship["shipper1"], ship["shipper2"], ship["ship_name"], ship["level"]]
            ships_listings.append(ship_entry)

        await self.friendship_ship_show_paginate(ships_listings, member, ctx)

    async def friendship_ship_show_paginate(self, formatted_list, member, ctx):

        page = 1
        max_lines = 5
        page_total = ceil(len(formatted_list) / max_lines)
        if page_total == 0:
            page_total = 1

        def create_new_embed_page(page_new):
            end = page_new * 5
            start = end - 5
            total_ships = len(formatted_list)

            embed = discord.Embed(
                color=member.colour,
                title=f"🚢 {member.display_name}'s ships [{total_ships} {self.pluralize('ship', total_ships)}]",
                timestamp=self.get_timestamp()
            )
            embed.set_footer(text=f"Page {page_new} of {page_total}")

            while start < end:
                try:
                    embed.add_field(
                        name=f"{formatted_list[start][2]}, level {formatted_list[start][3]}",
                        value=f"<@{formatted_list[start][0]}> & <@{formatted_list[start][1]}>",
                        inline=False
                    )
                    start += 1
                except IndexError:
                    break
            return embed

        def check_pagination(r, u):
            return u != self.client.user and r.message.id == msg.id

        msg = await ctx.channel.send(embed=create_new_embed_page(page))
        await msg.add_reaction("⬅")
        await msg.add_reaction("➡")

        while True:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=180, check=check_pagination)
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

    @commands.command(aliases=["ship"])
    @commands.guild_only()
    async def friendship_ship(self, ctx, query1: discord.Member = None, *, query2: discord.Member = None):

        try:
            code = self.get_bond(ctx.author, query1)
        except TypeError:
            embed = discord.Embed(
                colour=discord.Colour(colour),
                title="Invalid ship",
                description=f"that ship has sunk before it was even fully built"
            )
            await ctx.channel.send(embed=embed)
            return

        if query1 is None and query2 is None:
            embed = discord.Embed(
                title="ship, ships", colour=discord.Colour(colour),
                description=f"shows a ship profile or your own list of ships\n"
                            f"to change your ship's name use *`{self.prefix}fpchange`*"
            )
            embed.add_field(
                name="Formats",
                value=f"*• `{self.prefix}ship <@member>`*\n"
                      f"*• `{self.prefix}ship <@member> <@member>`*\n"
                      f"*• `{self.prefix}ships`*"
            )
            await ctx.channel.send(embed=embed)

        elif query1 is not None and query2 is None:
            await self.friendship_post_ship(code, query1, ctx)

        elif query1 is not None and query2 is not None:
            await self.friendship_post_ship(code, query1, ctx)

    async def friendship_post_ship(self, code, query1, ctx):

        ship_profile = ships.find_one({"code": code}, {"_id": 0, })

        list_rank = []
        for entry in ships.find({}, {"code": 1, "points": 1}):
            list_rank.append((entry["code"], entry["points"]))

        rank = (sorted(list_rank, key=lambda x: x[1], reverse=True)).index((code, ship_profile["points"])) + 1

        if ship_profile['level'] > 1:
            rewards = str(ship_profile["level"] * 25) + " jades/day"
        else:
            rewards = "Must be Level 2 & above"

        description = f"```" \
                      f"• Level:        :: {ship_profile['level']}/5\n" \
                      f"• Total Points: :: {ship_profile['points']}/{ship_profile['points_required']}\n" \
                      f"• Server Rank:  :: {rank}\n" \
                      f"• Rewards       :: {rewards}" \
                      f"```"

        embed = discord.Embed(color=query1.colour, description=description, timestamp=self.get_timestamp())
        print(self.get_time_converted(ship_profile['cards']['timestamp']))

        time_deployed = self.get_time_converted(ship_profile["cards"]["timestamp"])
        hours, minutes = self.hours_minutes((time_deployed + timedelta(days=1)) - datetime.now(tz=pytz.timezone("UTC")))
        embed.add_field(
            name=f"Equipped realm card",
            value=f"{ship_profile['cards']['name'].title()} | "
                  f"Grade {ship_profile['cards']['grade']} | "
                  f"Collect in {hours}h, {minutes}m"
        )

        embed.set_author(
            name=f"{ship_profile['ship_name']}",
            icon_url=self.client.get_user(int(ship_profile["shipper1"])).avatar_url
        )
        embed.set_thumbnail(url=self.client.get_user(int(ship_profile['shipper2'])).avatar_url)
        await ctx.channel.send(embed=embed)

    @commands.command(aliases=["friendship", "fp"])
    @commands.guild_only()
    @commands.cooldown(1, 0.5, commands.BucketType.user)
    async def friendship_give(self, ctx, *, receiver: discord.Member = None):

        giver = ctx.author
        profile = users.find_one({"user_id": str(giver.id)}, {"_id": 0, "friendship_pass": 1})

        if receiver is None:
            embed = discord.Embed(
                title="friendship, fp", colour=discord.Colour(colour),
                description=f"sends and receives friendship & builds ship that earns daily reward\n"
                            f"built ships are shown using *`{self.prefix}ship`*"
            )
            embed.add_field(
                name="Mechanics",
                value="```"
                      "• Send hearts      ::  + 5\n"
                      " * added ship exp  ::  + 5\n\n"
                      "• Confirm receipt < 2 min"
                      "\n * Receiver        ::  + 3"
                      "\n * added ship exp  ::  + 3```",
                inline=False
            )
            embed.add_field(name="Format", value=f"*`{self.prefix}friendship <@member>`*", inline=False)
            await ctx.channel.send(embed=embed)

        elif receiver.bot is True or receiver == ctx.author:
            return

        elif receiver.name == giver.name:
            await ctx.message.add_reaction("❌")

        elif check_if_user_has_any_alt_roles(receiver):
            await ctx.message.add_reaction("❌")

        elif profile["friendship_pass"] < 1:
            embed = discord.Embed(
                colour=discord.Colour(colour),
                title="Insufficient friendship passes",
                description=f"fulfill wishes or claim your dailies to obtain more"
            )
            await ctx.channel.send(embed=embed)

        elif profile["friendship_pass"] > 0:
            code = self.get_bond(giver, receiver)
            users.update_one({
                "user_id": str(giver.id)}, {
                "$inc": {
                    "friendship_pass": -1
                }
            })
            await self.perform_add_log("friendship_pass", -1, giver)

            if ships.find_one({"code": code}, {"_id": 0}) is None:
                profile = {
                    "code": code,
                    "shipper1": str(ctx.author.id),
                    "shipper2": str(receiver.id),
                    "ship_name": f"{giver.name} and {receiver.name}'s ship",
                    "level": 1,
                    "points": 0,
                    "points_required": 50,
                    "cards": {
                        "equipped": False,
                        "name": None,
                        "grade": None,
                        "timestamp": None,
                        "collected": None
                    }
                }
                ships.insert_one(profile)

            ships.update_one({"code": code}, {"$inc": {"points": 5}})
            await self.friendship_give_check_levelup(ctx, code, giver)
            users.update_one({"user_id": str(giver.id)}, {"$inc": {"friendship": 5}})
            await self.perform_add_log("friendship", 5, giver)
            await ctx.message.add_reaction(f"{e_f.replace('<', '').replace('>', '')}")

            def check(r, u):
                return u.id == receiver.id and str(r.emoji) == e_f and r.message.id == ctx.message.id

            try:
                await self.client.wait_for("reaction_add", timeout=120, check=check)
            except asyncio.TimeoutError:
                await self.friendship_give_check_levelup(ctx, code, giver)
                await ctx.message.clear_reactions()
            else:
                ships.update_one({"code": code, "level": {"$lt": 5}}, {"$inc": {"points": 3}})
                await self.friendship_give_check_levelup(ctx, code, giver)
                users.update_one({"user_id": str(receiver.id)}, {"$inc": {"friendship": 3}})
                await self.perform_add_log("friendship", 3, receiver)
                await ctx.message.clear_reactions()
                await ctx.message.add_reaction("✅")

    async def friendship_give_check_levelup(self, ctx, code, giver):
        ship = ships.find_one({
            "code": code}, {
            "_id": 0, "level": 1, "points": 1, "points_required": 1, "ship_name": 1
        })
        bond_current = ship["points"]
        level = ship["level"]

        if level < 5:
            if bond_current >= ship["points_required"]:
                ships.update_one({"code": code}, {"$inc": {"level": 1}})
                level_next = level + 1
                points_required = \
                    round(-1.875 * (level_next ** 4) + 38.75 * (level_next ** 3) - 170.63 * (level_next ** 2)
                          + 313.75 * level_next - 175)
                ships.update_one({"code": code}, {"$inc": {"points_required": points_required}})

                if level_next == 5:
                    ships.update_one({"code": code}, {"$set": {"points": 575, "points_required": 575}})

                await self.friendship_post_ship(code, giver, ctx)

    @commands.command(aliases=["fpchange", "fpc"])
    @commands.guild_only()
    async def friendship_change_name(self, ctx, receiver: discord.Member = None, *, new_name=None):

        embed = discord.Embed(
            title="fpchange, fpc", colour=discord.Colour(colour),
            description="changes your ship name with the mentioned member"
        )
        embed.add_field(name="Format", value=f"*• `{self.prefix}fpc <@member> <ship name>`*")

        if new_name is None:
            await ctx.channel.send(embed=embed)

        try:
            code = self.get_bond(ctx.author, receiver)
            ships.update_one({"code": code}, {"$set": {"ship_name": new_name}})
            await self.friendship_post_ship(code, ctx.author, ctx)

        except AttributeError:
            await ctx.channel.send(embed=embed)

    @commands.command(aliases=["shop"])
    @commands.guild_only()
    async def shop_buy_items_show_all(self, ctx):

        embed = discord.Embed(
            title="Mystic Trader", colour=discord.Colour(colour),
            description="exchange various economy items"
        )
        embed.set_thumbnail(url="https://vignette.wikia.nocookie.net/onmyoji/images/8/86/246a.jpg")
        embed.add_field(
            name="Trading List",
            value="".join(trading_list_formatted),
            inline=False
        )
        embed.add_field(name="Example", value=f"*`{self.prefix}buy amulets 11`*", inline=False)

        msg = await ctx.channel.send(embed=embed)
        await msg.add_reaction("🖼")

        def check(r, u):
            return str(r.emoji) == "🖼" and r.message.id == msg.id and u.bot is False

        try:
            await self.client.wait_for("reaction_add", timeout=30, check=check)
        except asyncio.TimeoutError:
            await msg.clear_reactions()
            return
        else:
            try:
                url = self.client.get_user(518416258312699906).avatar_url
            except AttributeError:
                url = ""

            embed = discord.Embed(
                title="AkiraKL's Frame Shop", colour=discord.Colour(colour),
                description="purchase premium frames for premium prices"
            )
            embed.set_thumbnail(url=url)
            for frame in frames.find({"purchase": True}, {"_id": 0, "currency": 1, "amount": 1, "name": 1, "emoji": 1}):
                embed.add_field(
                    name=f"{frame['emoji']} {frame['name']}",
                    value=f"Acquire for {frame['amount']:,d}{self.get_emoji(frame['currency'])}",
                    inline=False
                )
            embed.add_field(name=f"Format", value=f"*`{self.prefix}buy frame <name>`*", inline=False)
            await msg.edit(embed=embed)

    @commands.command(aliases=["buy"])
    @commands.guild_only()
    async def shop_buy_items(self, ctx, *args):

        user = ctx.author

        if len(args) == 0:
            embed = discord.Embed(
                title="buy", colour=discord.Colour(colour),
                description=f"purchase from the list of items from the *`{self.prefix}shop`*\n"
                            f"react to confirm purchase"
            )
            embed.add_field(
                name="Format",
                value=f"*`{self.prefix}buy <purchase_code>`*\n*`{self.prefix}buy frame <frame_name>`*"
            )
            await ctx.channel.send(embed=embed)

        elif args[0].lower() in ["frame"] and len(args) > 1 and " ".join(args[1::]).lower() in purchasable_frames:

            frame = " ".join(args[1::]).lower()
            request = frames.find_one({"name": frame.title()}, {"_id": 0})
            emoji, currency, amount = request["emoji"], request["currency"], request["amount"]
            cost_item_have = users.find_one({"user_id": str(user.id)}, {"_id": 0, currency: 1})[currency]

            try:
                url = self.client.get_user(518416258312699906).avatar_url
            except AttributeError:
                url = ""

            embed = discord.Embed(title="Confirm purchase?", color=ctx.author.colour, timestamp=self.get_timestamp())
            embed.description = f"{emoji} {frame.title()} frame for `{amount:,d}` {self.get_emoji(currency)}"
            embed.add_field(
                name="Inventory",
                value=f"`{cost_item_have:,d}` {self.get_emoji(currency)}"
            )
            embed.set_thumbnail(url=url)
            embed.set_footer(icon_url=user.avatar_url, text=user.display_name)

            msg = await ctx.channel.send(embed=embed)
            await msg.add_reaction("✅")
            answer = await self.shop_buy_items_confirmation(ctx, msg)

            if answer is True:
                await self.shop_buy_items_process_purchase_frame(ctx, user, currency, amount, frame.title(), emoji)

        else:
            def get_offer_and_cost(x):
                _offer_item = mystic_shop[x[0]][x[1]]["offer"][0]
                _offer_amount = mystic_shop[x[0]][x[1]]["offer"][1]
                _cost_item = mystic_shop[x[0]][x[1]]["cost"][0]
                _cost_amount = mystic_shop[x[0]][x[1]]["cost"][1]
                return _offer_item, _offer_amount, _cost_item, _cost_amount

            try:
                offer_item, offer_amount, cost_item, cost_amount = get_offer_and_cost(args)
                cost_item_have = users.find_one({"user_id": str(user.id)}, {"_id": 0, cost_item: 1})[cost_item]
                offer_item_have = users.find_one({"user_id": str(user.id)}, {"_id": 0, offer_item: 1})[offer_item]

                embed = discord.Embed(title="Confirm purchase?", colour=user.colour, timestamp=self.get_timestamp())
                embed.set_footer(icon_url=user.avatar_url, text=user.display_name)
                embed.description = \
                    f"`{offer_amount}` {self.get_emoji(offer_item)} `for` " \
                    f"`{cost_amount:,d}` {self.get_emoji(cost_item)}\n\n"
                embed.add_field(
                    name="Inventory",
                    value=f"`{offer_item_have:,d}` {self.get_emoji(offer_item)} | "
                          f"`{cost_item_have:,d}` {self.get_emoji(cost_item)}"
                )
                embed.set_thumbnail(url="https://vignette.wikia.nocookie.net/onmyoji/images/8/86/246a.jpg")

                msg = await ctx.channel.send(embed=embed)
                await msg.add_reaction("✅")
                answer = await self.shop_buy_items_confirmation(ctx, msg)

                if answer is True:
                    await self.shop_buy_items_process_purchase(
                        user, ctx, offer_item, offer_amount, cost_item, cost_amount, msg
                    )

            except KeyError:
                embed = discord.Embed(
                    title="Invalid purchase code", colour=discord.Colour(colour),
                    description=f"You entered an invalid purchase code",
                )
                await ctx.channel.send(embed=embed)

            except IndexError:
                embed = discord.Embed(
                    title="Invalid purchase code", colour=discord.Colour(colour),
                    description=f"You entered an invalid purchase code",
                )
                await ctx.channel.send(embed=embed)

    async def shop_buy_items_confirmation(self, ctx, msg):

        def check(r, u):
            return u == ctx.author and str(r.emoji) == "✅" and msg.id == r.message.id

        try:
            await self.client.wait_for("reaction_add", timeout=10.0, check=check)
        except asyncio.TimeoutError:
            embed = discord.Embed(
                title="Timeout!", colour=discord.Colour(colour),
                description=f"no confirmation was received",
                timestamp=self.get_timestamp()
            )
            embed.set_footer(text=f"{ctx.author.display_name}", icon_url=ctx.author.avatar_url)
            embed.set_thumbnail(url="https://vignette.wikia.nocookie.net/onmyoji/images/8/86/246a.jpg")
            await msg.edit(embed=embed)
            await msg.clear_reactions()
            return False
        else:
            return True

    async def shop_buy_items_process_purchase(self, user, ctx, offer_item, offer_amount, cost_item, cost_amount, msg):
        if users.find_one({"user_id": str(user.id)}, {"_id": 0, cost_item: 1})[cost_item] >= int(cost_amount):
            users.update_one({
                "user_id": str(user.id)}, {
                "$inc": {
                    offer_item: int(offer_amount),
                    cost_item: -int(cost_amount)
                }
            })
            await self.perform_add_log(offer_item, offer_amount, user.id)
            await self.perform_add_log(cost_item, -cost_amount, user.id)

            cost_item_have = users.find_one({"user_id": str(user.id)}, {"_id": 0, cost_item: 1})[cost_item]
            offer_item_have = users.find_one({"user_id": str(user.id)}, {"_id": 0, offer_item: 1})[offer_item]

            embed = discord.Embed(
                title="Purchase successful", colour=user.color,
                timestamp=self.get_timestamp()
            )
            embed.set_footer(icon_url=user.avatar_url, text=f"{user.display_name}")
            embed.description = f"You acquired `{offer_amount:,d}`{self.get_emoji(offer_item)} " \
                                f"in exchange for `{cost_amount:,d}`{self.get_emoji(cost_item)}"
            embed.set_thumbnail(url="https://vignette.wikia.nocookie.net/onmyoji/images/8/86/246a.jpg")
            embed.add_field(
                name="Inventory",
                value=f"`{offer_item_have:,d}` {self.get_emoji(offer_item)} | "
                      f"`{cost_item_have:,d}` {self.get_emoji(cost_item)}"
            )
            await msg.edit(embed=embed)

        else:
            embed = discord.Embed(
                title="Purchase failure", colour=discord.Colour(colour),
                description=f"You have insufficient {self.get_emoji(cost_item)}",
            )
            embed.set_footer(icon_url=user.avatar_url, text=f"{user.display_name}")
            await ctx.channel.send(embed=embed)

    async def shop_buy_items_process_purchase_frame(self, ctx, user, currency, amount, frame_name, emoji):
        if users.find_one({"user_id": str(user.id)}, {"_id": 0, currency: 1})[currency] >= amount:

            if users.find_one({"user_id": str(user.id), "achievements.name": frame_name}, {"_id": 0}) is None:
                users.update_one({
                    "user_id": str(user.id)}, {
                    "$inc": {
                        currency: -amount
                    },
                    "$push": {
                        "achievements": {
                            "name": frame_name,
                            "date_acquired": self.get_time()
                        }
                    }
                })
                await self.perform_add_log(currency, -amount, user.id)

                embed = discord.Embed(
                    title="Confirmation receipt", colour=discord.Colour(colour),
                    description=f"You acquired {emoji} {frame_name} in exchange for "
                                f"{amount:,d}{self.get_emoji(currency)}",
                    timestamp=self.get_timestamp()
                )
                await ctx.channel.send(embed=embed)

            else:
                embed = discord.Embed(
                    title="Purchase failure", colour=discord.Colour(colour),
                    description=f"this frame is already in your possession",
                )
                await ctx.channel.send(embed=embed)

        else:
            embed = discord.Embed(
                title="Purchase failure", colour=discord.Colour(colour),
                description=f" You have insufficient {self.get_emoji(currency)}",
            )
            await ctx.channel.send(embed=embed)

    @commands.command(aliases=["summon", "s"])
    @commands.guild_only()
    async def summon_perform(self, ctx, *, shiki=None):

        if shiki is None:
            embed = discord.Embed(
                title="summon, s", colour=discord.Colour(colour),
                description="simulates summon and collect shikigamis"
            )
            embed.add_field(
                name="Shard Requirement",
                value=f"```"
                      "SP    ::   15\n"
                      "SSR   ::   12\n"
                      "SR    ::    9\n"
                      "R     ::    6\n"
                      "N     ::    3\n"
                      "SSN   ::   12\n"
                      "```",
                inline=False
            )
            embed.add_field(
                name="Formats",
                value=f"*`{self.prefix}summon <shikigami>`*\n"
                      f"*`{self.prefix}sb`*\n"
                      f"*`{self.prefix}sm <1 or 10>`*\n",
                inline=False
            )
            await ctx.channel.send(embed=embed)

        else:
            shiki_formatted = shiki.lower()

            if shiki_formatted in pool_all_mystery or shiki_formatted in pool_all_broken:
                await self.summon_perform_shards(ctx, shiki_formatted, ctx.author)

            else:
                await self.shikigami_post_approximate_results(ctx, shiki_formatted)

    @commands.command(aliases=["sb"])
    @commands.guild_only()
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def summon_perform_broken(self, ctx):

        user = ctx.author
        amulet_have = users.find_one({"user_id": str(user.id)}, {"_id": 0, "amulets_b": 1})["amulets_b"]

        if amulet_have == 0:
            embed = discord.Embed(
                title="Insufficient amulets", colour=discord.Colour(colour),
                description="perform exploration to obtain more",
            )
            await ctx.channel.send(embed=embed)

        elif amulet_have > 0:

            if amulet_have >= 5:
                await self.summon_perform_broken_pull(ctx, user, 5)

            elif 0 < amulet_have < 5:
                await self.summon_perform_broken_pull(ctx, user, amulet_have)

        self.client.get_command("summon_perform_broken").reset_cooldown(ctx)

    async def summon_perform_broken_pull(self, ctx, user, amulet_pull):

        summon_pull = []
        for count in range(amulet_pull):
            roll = random.uniform(0, 100)

            if roll < 1:
                summon_pull.append(("SSN", "||{}||".format(random.choice(pool_ssn))))
            else:
                roll = random.uniform(0, 100)
                if roll <= 13:
                    summon_pull.append(("R", "{}".format(random.choice(pool_r))))
                else:
                    summon_pull.append(("N", random.choice(pool_n)))

        sum_ssn = sum(x.count("SSN") for x in summon_pull)
        sum_r = sum(x.count("R") for x in summon_pull)
        sum_n = sum(x.count("N") for x in summon_pull)

        f_ssn = str(sum_ssn) + " " + self.pluralize("SSN", sum_ssn)
        f_r = str(sum_r) + " " + self.pluralize("R", sum_r)
        f_n = str(sum_n) + " " + self.pluralize("N", sum_n)

        description = ""
        for x in summon_pull:
            description += "🔸{}\n".format(x[1].title())

        embed = discord.Embed(
            color=user.colour, title="🎊 Summon results", description=description, timestamp=self.get_timestamp()
        )
        embed.set_footer(text=f"{f_ssn}; {f_r}; {f_n}", icon_url=user.avatar_url)

        msg = "{}".format(next(summon_captions)).format(user.mention)
        await ctx.channel.send(msg, embed=embed)
        await self.summon_perform_broken_pull_update(user, sum_ssn, sum_n, sum_r, amulet_pull, summon_pull)

    async def summon_perform_broken_pull_update(self, user, sum_ssn, sum_n, sum_r, amulet_pull, summon_pull):
        users.update_one({
            "user_id": str(user.id)}, {
            "$inc": {
                "SSN": sum_ssn,
                "N": sum_n,
                "R": sum_r,
                "amulets_spent_b": amulet_pull,
                "amulets_b": -amulet_pull
            }
        })

        for summon in summon_pull:

            query = users.find_one({
                "user_id": str(user.id),
                "shikigami.name": summon[1].replace("||", "")}, {
                "_id": 0, "shikigami.$": 1
            })

            if query is None:
                evolve, shards = False, 0
                self.shikigami_push_user(user.id, summon[1].replace("||", ""), evolve, shards)

            users.update_one({
                "user_id": str(user.id),
                "shikigami.name": summon[1].replace("||", "")}, {
                "$inc": {
                    "shikigami.$.owned": 1
                }
            })

    @commands.command(aliases=["sm"])
    @commands.guild_only()
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def summon_perform_mystery(self, ctx, *, args=None):

        user = ctx.author

        try:
            amulet_pull = int(args)
            amulet_have = users.find_one({"user_id": str(user.id)}, {"_id": 0, "amulets": 1})["amulets"]

            if amulet_have == 0:
                embed = discord.Embed(
                    title="Insufficient amulets", colour=discord.Colour(colour),
                    description="exchange at the shop to obtain more",
                )
                await ctx.channel.send(embed=embed)

            elif args not in ["1", "10"]:
                raise commands.MissingRequiredArgument(ctx.author)

            elif amulet_have > 0:

                if amulet_pull > amulet_have:
                    embed = discord.Embed(
                        title="Insufficient amulets", colour=discord.Colour(colour),
                        description=f"You only have {amulet_have}{e_a} in possession",
                        timestamp=self.get_timestamp()
                    )
                    embed.set_footer(icon_url=user.avatar_url, text=user.display_name)
                    await ctx.channel.send(embed=embed)

                elif amulet_pull == 10 and amulet_have >= 10:
                    await self.summon_perform_mystery_pull(ctx, user, amulet_pull)

                elif amulet_pull == 1 and amulet_have >= 1:
                    await self.summon_perform_mystery_pull(ctx, user, amulet_pull)

        except TypeError:
            raise commands.MissingRequiredArgument(ctx.author)

        except ValueError:
            pass

        self.client.get_command("summon_perform_mystery").reset_cooldown(ctx)

    async def summon_perform_mystery_pull(self, ctx, user, amulet_pull):
        summon_pull = []

        for count in range(amulet_pull):
            roll = random.uniform(0, 100)

            if roll < 1.2:
                p = random.uniform(0, 1.2)
                if p >= 126 / 109:
                    summon_pull.append(("SP", "||{}||".format(random.choice(pool_sp))))
                else:
                    summon_pull.append(("SSR", "||{}||".format(random.choice(pool_ssr))))
            elif roll <= 18.8:
                summon_pull.append(("SR", random.choice(pool_sr)))
            else:
                summon_pull.append(("R", random.choice(pool_r)))

        sum_sp = sum(x.count("SP") for x in summon_pull)
        sum_ssr = sum(x.count("SSR") for x in summon_pull)
        sum_sr = sum(x.count("SR") for x in summon_pull)
        sum_r = sum(x.count("R") for x in summon_pull)

        f_sp = str(sum_sp) + " " + self.pluralize("SP", sum_sp)
        f_ssr = str(sum_ssr) + " " + self.pluralize("SSR", sum_ssr)
        f_sr = str(sum_sr) + " " + self.pluralize("SR", sum_sr)
        f_r = str(sum_r) + " " + self.pluralize("R", sum_r)

        description = ""
        for x in summon_pull:
            description += "🔸{}\n".format(x[1].title())

        embed = discord.Embed(
            color=user.colour, title="🎊 Summon results", description=description, timestamp=self.get_timestamp()
        )

        if amulet_pull == 10:
            embed.set_footer(text=f"{f_sp}; {f_ssr}; {f_sr}; {f_r}", icon_url=user.avatar_url)

        elif amulet_pull == 1:
            shikigami_pulled = summon_pull[0][1].replace("||", "")
            embed.set_thumbnail(url=self.get_thumbnail_shikigami(shikigami_pulled, "pre"))

        msg = "{}".format(next(summon_captions)).format(user.mention)
        await ctx.channel.send(msg, embed=embed)
        await self.summon_perform_mystery_pull_update(user, sum_sp, sum_ssr, sum_sr, sum_r, amulet_pull, summon_pull)
        await self.summon_perform_mystery_pull_update_streak(user, summon_pull)

    async def summon_perform_mystery_pull_update(self, user, sum_sp, sum_ssr, sum_sr, sum_r, amulet_pull, summon_pull):
        users.update_one({
            "user_id": str(user.id)}, {
            "$inc": {
                "SP": sum_sp,
                "SSR": sum_ssr,
                "SR": sum_sr,
                "R": sum_r,
                "amulets_spent": amulet_pull,
                "amulets": -amulet_pull
            }
        })
        await self.perform_add_log("amulets", -amulet_pull, user.id)

        for summon in summon_pull:
            shiki = summon[1].replace("||", "")
            query = users.find_one({"user_id": str(user.id), "shikigami.name": shiki}, {"_id": 0, "shikigami.$": 1})

            if query is None:
                evolve, shards = False, 0
                if summon[0] == "SP":
                    evolve, shards = True, 5

                self.shikigami_push_user(user.id, shiki, evolve, shards)

            if summon[0] == "SP":
                users.update_one({"user_id": str(user.id), "shikigami.name": shiki}, {
                    "$inc": {"shikigami.$.shards": 5}
                })

            users.update_one({"user_id": str(user.id), "shikigami.name": shiki}, {"$inc": {"shikigami.$.owned": 1}})

    async def summon_perform_mystery_pull_update_streak(self, user, summon_pull):

        if streaks.find_one({"user_id": str(user.id)}, {"_id": 0}) is None:
            streaks.insert_one({"user_id": str(user.id), "SSR_current": 0, "SSR_record": 0})

        for summon in summon_pull:
            ssr_current = streaks.find_one({"user_id": str(user.id)}, {"_id": 0})["SSR_current"]
            ssr_record = streaks.find_one({"user_id": str(user.id)}, {"_id": 0})["SSR_record"]

            if summon[0] in ["SP", "SR", "R"]:
                if ssr_current == ssr_record:
                    streaks.update_one({"user_id": str(user.id)}, {"$inc": {"SSR_current": 1, "SSR_record": 1}})
                else:
                    streaks.update_one({"user_id": str(user.id)}, {"$inc": {"SSR_current": 1}})

            elif summon[0] == "SSR":
                streaks.update_one({"user_id": str(user.id)}, {"$set": {"SSR_current": 0}})

    async def summon_perform_shards(self, ctx, shiki, user):

        try:
            profile = users.find_one({
                "user_id": str(user.id), "shikigami.name": shiki}, {
                "_id": 0, "shikigami.$.name": 1
            })

            shards = profile["shikigami"][0]["shards"]
            required_shards, rarity = self.get_shard_requirement(shiki)

            if shards >= required_shards:
                query = users.find_one({
                    "user_id": str(user.id),
                    "shikigami.name": shiki}, {
                    "_id": 0, "shikigami.$": 1
                })

                if query is None:
                    evolve, shards = False, 0
                    if rarity == "SP":
                        evolve, shards = True, 0

                    users.update_one({
                        "user_id": str(user.id)}, {
                        "$push": {
                            "shikigami": {
                                "name": shiki,
                                "rarity": rarity,
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

                users.update_one({
                    "user_id": str(user.id),
                    "shikigami.name": shiki}, {
                    "$inc": {
                        f"{rarity}": 1,
                        "shikigami.$.owned": 1,
                        "shikigami.$.shards": -required_shards
                    }
                })
                embed = discord.Embed(
                    title="Summon success", colour=discord.Colour(colour),
                    description=f"You acquired the {rarity} shikigami {shiki.title()}!",
                    timestamp=self.get_timestamp()
                )
                embed.set_footer(text=f"{user.display_name}", icon_url=user.avatar_url)
                embed.set_thumbnail(url=self.get_thumbnail_shikigami(shiki, "pre"))
                await ctx.channel.send(embed=embed)

            else:
                embed = discord.Embed(
                    title="Summon failed", colour=discord.Colour(colour),
                    description=f"You lack {required_shards - shards} {shiki.title()} shards",
                )
                embed.set_thumbnail(url=self.get_thumbnail_shikigami(shiki, "pre"))
                await ctx.channel.send(embed=embed)

        except TypeError:
            embed = discord.Embed(
                title="Summon failed", colour=discord.Colour(colour),
                description=f"You have insufficient shards of {shiki.title()}",
                timestamp=self.get_timestamp()
            )
            await ctx.channel.send(embed=embed)

    @commands.command(aliases=["leaderboard", "lb"])
    @commands.guild_only()
    async def leaderboard_show(self, ctx, *, args):

        if args.lower() in ["ssr"]:
            query = users.find({}, {"_id": 0, "user_id": 1, "SSR": 1})
            await self.leaderboard_post_record_users(ctx, query, f"{e_2} LeaderBoard", "SSR")

        elif args.lower() in ["sp"]:
            query = users.find({}, {"_id": 0, "user_id": 1, "SP": 1})
            await self.leaderboard_post_record_users(ctx, query, f"{e_1} LeaderBoard", "SP")

        elif args.lower() in ["sr"]:
            query = users.find({}, {"_id": 0, "user_id": 1, "SR": 1})
            await self.leaderboard_post_record_users(ctx, query, f"{e_3} LeaderBoard", "SR")

        elif args.lower() in ["ssn"]:
            query = users.find({}, {"_id": 0, "user_id": 1, "SSN": 1})
            await self.leaderboard_post_record_users(ctx, query, f"{e_6} LeaderBoard", "SSN")

        elif args.lower() in ["medal", "medals"]:
            query = users.find({}, {"_id": 0, "user_id": 1, "medals": 1})
            await self.leaderboard_post_record_users(ctx, query, f"{e_m} Medal LeaderBoard", "medals")

        elif args.lower() in ["amulet", "amulets"]:
            query = users.find({}, {"_id": 0, "user_id": 1, "amulets_spent": 1})
            await self.leaderboard_post_record_users(ctx, query, f"{e_a} Spender LeaderBoard", "amulets_spent")

        elif args.lower() in ["friendship", "fp"]:
            query = users.find({}, {"_id": 0, "user_id": 1, "friendship": 1})
            await self.leaderboard_post_record_users(ctx, query, f"{e_f} Friendship LeaderBoard", "friendship")

        elif args.lower() in ["streak", "ssrstreak"]:
            query = streaks.find({}, {"_id": 0, "user_id": 1, "SSR_current": 1})
            await self.leaderboard_post_record_users(ctx, query, f"No {e_2} Summon Streak LeaderBoard", "SSR_current")

        elif args.lower() in ["level"]:
            query = users.find({}, {"_id": 0, "user_id": 1, "level": 1})
            await self.leaderboard_post_record_users(ctx, query, f"{e_x} Level LeaderBoard", "level")

        elif args.lower() in ["achievements", "frames"]:
            query = users.find({}, {"_id": 0, "user_id": 1, "achievements": 1})
            await self.leaderboard_post_record_users(ctx, query, "🖼 Frames LeaderBoard", "achievements")

        elif args.lower() in ["ship", "ships"]:
            query = ships.find({}, {"_id": 0, "points": 1, "ship_name": 1})
            await self.leaderboard_post_record_ships(ctx, query, "🚢 Ships LeaderBoard")

    async def leaderboard_post_record_users(self, ctx, query, title, key):

        raw_list = []
        formatted_list = []

        for user in query:
            try:
                member_name = self.client.get_user(int(user["user_id"])).display_name
                if isinstance(user[key], list):
                    raw_list.append((member_name, len(user[key])))
                else:
                    raw_list.append((member_name, user[key]))
            except AttributeError:
                continue

        for user in sorted(raw_list, key=lambda x: x[1], reverse=True):
            formatted_list.append(f"🔸{user[0]}, x{user[1]:,d}\n")

        await self.leaderboard_paginate(title, ctx, formatted_list)

    async def leaderboard_post_record_ships(self, ctx, query, title):

        raw_list = []
        formatted_list = []

        for ship in query:
            raw_list.append((ship["ship_name"], ship["points"]))

        for ship in sorted(raw_list, key=lambda x: x[1], reverse=True):
            formatted_list.append(f"🔸{ship[0]}, x{ship[1]} {e_f} \n")

        await self.leaderboard_paginate(title, ctx, formatted_list)

    async def leaderboard_paginate(self, title, ctx, formatted_list):

        page = 1
        max_lines = 15
        page_total = ceil(len(formatted_list) / max_lines)
        if page_total == 0:
            page_total = 1

        def create_new_embed_page(page_new):
            end = page * max_lines
            start = end - max_lines
            description = "".join(formatted_list[start:end])

            embed_new = discord.Embed(
                color=ctx.author.colour,
                title=title,
                description=f"{description}",
                timestamp=self.get_timestamp()
            )
            embed_new.set_footer(text=f"Page: {page_new} of {page_total}")
            return embed_new

        msg = await ctx.channel.send(embed=create_new_embed_page(page))
        await msg.add_reaction("⬅")
        await msg.add_reaction("➡")

        def check(r, u):
            return u != self.client.user and r.message.id == msg.id

        while True:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=60, check=check)
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

    @commands.command(aliases=["logs"])
    @commands.guild_only()
    async def logs_show(self, ctx, *, member: discord.Member = None):

        if member is None:
            await self.logs_show_member(ctx, ctx.author)

        elif member is not None:
            await self.logs_show_member(ctx, member)

    async def logs_show_member(self, ctx, member):

        profile = logs.find_one({"user_id": str(member.id)}, {"_id": 0, "logs": 1})
        formatted_list = []

        for entry in profile["logs"][:200]:
            operator = "+"
            if entry['amount'] < 0:
                operator = ""
            emoji = self.get_emoji(entry['currency'])
            timestamp = self.get_time_converted(entry['date'])
            formatted_list.append(
                f"`[{timestamp.strftime('%d.%b %H:%M')}]` | `{operator}{entry['amount']:,d}`{emoji}\n"
            )

        await self.logs_show_paginate(ctx.channel, formatted_list, member)

    async def logs_show_paginate(self, channel, formatted_list, member):

        page = 1
        max_lines = 15
        page_total = ceil(len(formatted_list) / max_lines)
        if page_total == 0:
            page_total = 1

        def create_new_embed_page(page_new):
            end = page * max_lines
            start = end - max_lines
            description = "".join(formatted_list[start:end])

            embed_new = discord.Embed(
                color=member.colour,
                description=description
            )
            embed_new.set_author(
                name=f"{member.display_name}",
                icon_url=member.avatar_url
            )
            embed_new.set_footer(text=f"Last 200 only | Page: {page_new} of {page_total}")
            return embed_new

        msg = await channel.send(embed=create_new_embed_page(page))
        await msg.add_reaction("⬅")
        await msg.add_reaction("➡")

        def check(r, u):
            return u != self.client.user and r.message.id == msg.id

        while True:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=60, check=check)
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

    @commands.command(aliases=["shards"])
    @commands.guild_only()
    async def shikigami_show_post_shards(self, ctx, arg1, *, member: discord.Member = None):

        rarity = str(arg1.upper())

        if rarity not in rarities:
            raise commands.MissingRequiredArgument(ctx.author)

        elif member is None:
            await self.shikigami_show_post_shards_user(ctx.author, rarity, ctx)

        else:
            await self.shikigami_show_post_shards_user(member, rarity, ctx)

    async def shikigami_show_post_shards_user(self, member, rarity, ctx):

        user_shikigamis_with_evo = []
        user_shikigamis = []
        for entry in users.aggregate([{
            "$match": {
                "user_id": str(member.id)}}, {
            "$unwind": {
                "path": "$shikigami"}}, {
            "$match": {
                "shikigami.rarity": rarity}}, {
            "$project": {
                "_id": 0,
                "shikigami.name": 1,
                "shikigami.owned": 1,
                "shikigami.shards": 1,
                "shikigami.evolved": 1
            }}, {
            "$match": {
                "shikigami.owned": {
                    "$gt": 0
                }}}
        ]):
            user_shikigamis_with_evo.append(
                (entry["shikigami"]["name"], entry["shikigami"]["evolved"], entry["shikigami"]["shards"])
            )
            user_shikigamis.append(entry["shikigami"]["name"])

        pool_rarity_select = []
        for entry in shikigamis.find({"rarity": rarity}, {"_id": 0, "name": 1}):
            pool_rarity_select.append(entry["name"])

        uncollected_list = list(set(pool_rarity_select) - set(user_shikigamis))

        link = await self.shikigami_show_post_shards_generate(
            user_shikigamis_with_evo, uncollected_list, pool_rarity_select, rarity, member
        )

        embed = discord.Embed(
            title=f"{self.get_rarity_emoji(rarity)} Collection - Shards",
            color=member.colour,
            timestamp=self.get_timestamp()
        )
        embed.set_image(url=link)
        embed.set_footer(icon_url=member.avatar_url, text=f"{member.display_name}")
        await ctx.channel.send(embed=embed)

    async def shikigami_show_post_shards_generate(self, user_shikis, user_unc, pool_rarity_select, rarity, member):

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

        def get_shard_uncollected(user_id, rarity_selected, shikigami_name):
            try:
                for result in users.aggregate([
                    {
                        '$match': {
                            'user_id': str(user_id)
                        }
                    }, {
                        '$unwind': {
                            'path': '$shikigami'
                        }
                    }, {
                        '$match': {
                            'shikigami.rarity': rarity_selected
                        }
                    }, {
                        '$project': {
                            '_id': 0,
                            'shikigami.name': 1,
                            'shikigami.shards': 1,
                        }
                    }, {
                        '$match': {
                            'shikigami.name': shikigami_name
                        }
                    }
                ]):
                    return result["shikigami"]["shards"]

            except KeyError:
                return 0

        for entry in user_shikis:
            address = f"data/shikigamis/{entry[0]}_pre.jpg"
            if entry[1] is True:
                address = f"data/shikigamis/{entry[0]}_evo.jpg"

            shikigami_thumbnail = Image.open(address)
            shikigami_image_final = generate_shikigami_with_shard(shikigami_thumbnail, entry[2])
            images.append(shikigami_image_final)

        for entry in user_unc:
            address = f"data/shikigamis/{entry}_pre.jpg"
            count = get_shard_uncollected(member.id, rarity, entry)

            if count is None:
                count = 0

            shikigami_thumbnail = Image.open(address).convert("LA")
            shikigami_image_final = generate_shikigami_with_shard(shikigami_thumbnail, count)
            images.append(shikigami_image_final)

        w = self.get_variables(rarity)[0]
        col = self.get_variables(rarity)[1]

        def get_image_variables(a):
            total_shikis = len(a)
            h = ceil(total_shikis / col) * 90
            return w, h

        width, height = get_image_variables(pool_rarity_select)
        new_im = Image.new("RGBA", (width, height))

        def get_coordinates(c):
            a = (c * 90 - (ceil(c / col) - 1) * w) - 90
            b = (ceil(c / col) * 90) - 90
            return a, b

        for index, item in enumerate(images):
            new_im.paste(images[index], (get_coordinates(index + 1)))

        address = f"temp/{member.id}.png"
        new_im.save(address)
        new_photo = discord.File(address, filename=f"{member.id}.png")
        hosting_channel = self.client.get_channel(int(id_hosting))
        msg = await hosting_channel.send(file=new_photo)
        attachment_link = msg.attachments[0].url
        return attachment_link

    @commands.command(aliases=["shiki", "shikigami"])
    @commands.guild_only()
    async def shikigami_show_post_shiki(self, ctx, *, arg1):

        shiki = arg1.lower()
        user = ctx.author
        user_shikigami = users.find_one({
            "user_id": str(user.id), "shikigami.name": shiki}, {
            "_id": 0, "shikigami.$": 1
        })

        if shiki not in pool_all_mystery and shiki not in pool_all_broken:
            await self.shikigami_post_approximate_results(ctx, shiki)

        elif user_shikigami is None:
            embed = discord.Embed(
                colour=discord.Colour(colour),
                title="Invalid selection",
                description=f"this shikigami is not in your possession"
            )
            await ctx.channel.send(embed=embed)

        else:
            await self.shikigami_show_post_shiki_user(user, user_shikigami, shiki, ctx)

    async def shikigami_show_post_shiki_user(self, user, user_shikigami, shiki, ctx):

        shiki_profile = user_shikigami["shikigami"]
        evolve = "pre"
        if shiki_profile[0]["evolved"] is True:
            evolve = "evo"

        thumbnail = self.get_thumbnail_shikigami(shiki, evolve)

        embed = discord.Embed(
            colour=user.colour,
            description=f"```"
                        f"Level    ::   {shiki_profile[0]['level']}\n"
                        f"Exp      ::   {shiki_profile[0]['exp']}/{shiki_profile[0]['level_exp_next']}\n"
                        f"Grade    ::   {shiki_profile[0]['grade']}\n"
                        f"Owned    ::   {shiki_profile[0]['owned']}\n"
                        f"Shards   ::   {shiki_profile[0]['shards']}\n"
                        f"```",
            timestamp=self.get_timestamp()
        )
        embed.set_thumbnail(url=thumbnail)
        embed.set_author(
            name=f"{user.display_name}'s {shiki.title()}",
            icon_url=user.avatar_url
        )
        embed.set_footer(text=f"Rarity: {shiki_profile[0]['rarity']}")
        await ctx.channel.send(embed=embed)

    @commands.command(aliases=["shikis", "shikigamis"])
    @commands.guild_only()
    async def shikigami_show_post_shikis(self, ctx, arg1, *, member: discord.Member = None):

        rarity = str(arg1.upper())

        if rarity not in rarities:
            embed = discord.Embed(
                title="Invalid rarity", color=colour,
                description=f"you provided an invalid shikigami rarity"
            )
            embed.add_field(
                name="Rarities",
                value="SP, SSR, SR, R, N, SSN"
            )
            await ctx.channel.send(embed=embed)

        elif member is None:
            await self.shikigami_show_post_shikis_user(ctx.author, rarity, ctx)

        else:
            await self.shikigami_show_post_shikis_user(member, rarity, ctx)

    async def shikigami_show_post_shikis_user(self, member, rarity, ctx):

        user_shikigamis_with_evo = []
        user_shikigamis = []
        for entry in users.aggregate([{
            "$match": {
                "user_id": str(member.id)}}, {
            "$unwind": {
                "path": "$shikigami"}}, {
            "$match": {
                "shikigami.rarity": rarity}}, {
            "$project": {
                "_id": 0,
                "shikigami.name": 1,
                "shikigami.owned": 1,
                "shikigami.shards": 1,
                "shikigami.evolved": 1
            }}, {
            "$match": {
                "shikigami.owned": {
                    "$gt": 0
                }}}
        ]):
            user_shikigamis_with_evo.append(
                (entry["shikigami"]["name"], entry["shikigami"]["evolved"], entry["shikigami"]["owned"])
            )
            user_shikigamis.append(entry["shikigami"]["name"])

        pool_rarity_select = []
        for entry in shikigamis.find({"rarity": rarity}, {"_id": 0, "name": 1}):
            pool_rarity_select.append(entry["name"])

        uncollected_list = list(set(pool_rarity_select) - set(user_shikigamis))

        link = await self.shikigami_show_post_shikis_generate(
            user_shikigamis_with_evo, uncollected_list, pool_rarity_select, rarity, member
        )

        embed = discord.Embed(
            title=f"{self.get_rarity_emoji(rarity)} Collection - Count",
            color=member.colour,
            timestamp=self.get_timestamp()
        )
        embed.set_image(url=link)
        embed.set_footer(icon_url=member.avatar_url, text=f"{member.display_name}")
        await ctx.channel.send(embed=embed)

    async def shikigami_show_post_shikis_generate(self, user_shikis, user_unc, pool_rarity_select, rarity, member):

        images = []
        font = ImageFont.truetype('data/marker_felt_wide.ttf', 30)
        x, y = 1, 60

        def generate_shikigami_with_count(shikigami_thumbnail_select, owned_count):

            outline = ImageDraw.Draw(shikigami_thumbnail_select)
            outline.text((x - 1, y - 1), str(owned_count), font=font, fill="black")
            outline.text((x + 1, y - 1), str(owned_count), font=font, fill="black")
            outline.text((x - 1, y + 1), str(owned_count), font=font, fill="black")
            outline.text((x + 1, y + 1), str(owned_count), font=font, fill="black")
            outline.text((x, y), str(owned_count), font=font)

            return shikigami_thumbnail_select

        for entry in user_shikis:
            address = f"data/shikigamis/{entry[0]}_pre.jpg"
            if entry[1] is True:
                address = f"data/shikigamis/{entry[0]}_evo.jpg"

            shikigami_thumbnail = Image.open(address)
            shikigami_image_final = generate_shikigami_with_count(shikigami_thumbnail, entry[2])
            images.append(shikigami_image_final)

        for entry in user_unc:
            address = f"data/shikigamis/{entry}_pre.jpg"
            shikigami_thumbnail = Image.open(address).convert("LA")
            shikigami_image_final = generate_shikigami_with_count(shikigami_thumbnail, 0)
            images.append(shikigami_image_final)

        w = self.get_variables(rarity)[0]
        col = self.get_variables(rarity)[1]

        def get_image_variables(a):
            total_shikis = len(a)
            h = ceil(total_shikis / col) * 90
            return w, h

        width, height = get_image_variables(pool_rarity_select)
        new_im = Image.new("RGBA", (width, height))

        def get_coordinates(c):
            a = (c * 90 - (ceil(c / col) - 1) * w) - 90
            b = (ceil(c / col) * 90) - 90
            return a, b

        for index, item in enumerate(images):
            new_im.paste(images[index], (get_coordinates(index + 1)))

        address = f"temp/{member.id}.png"
        new_im.save(address)
        new_photo = discord.File(address, filename=f"{member.id}.png")
        hosting_channel = self.client.get_channel(int(id_hosting))
        msg = await hosting_channel.send(file=new_photo)
        attachment_link = msg.attachments[0].url
        return attachment_link

    @commands.command(aliases=["explores", "exps"])
    @commands.guild_only()
    async def perform_exploration_check_clears(self, ctx, *, member: discord.Member = None):

        if member is None:
            await self.perform_exploration_check_clears_post(ctx.author, ctx)
        else:
            await self.perform_exploration_check_clears_post(member, ctx)

    async def perform_exploration_check_clears_post(self, member, ctx):

        total_explorations = 0
        for result in explores.aggregate([
            {
                '$match': {
                    'user_id': str(member.id)
                }
            }, {
                '$unwind': {
                    'path': '$explores'
                }
            }, {
                '$match': {
                    'explores.completion': True
                }
            }, {
                '$count': 'count'
            }
        ]):
            total_explorations = result["count"]

        embed = discord.Embed(
            colour=ctx.author.colour,
            description=f"Your total exploration clears: {total_explorations}",
            timestamp=self.get_timestamp()
        )
        embed.set_footer(
            text=f"{member.display_name}",
            icon_url=member.avatar_url
        )
        await ctx.channel.send(embed=embed)

    @commands.command(aliases=["explore", "exp"])
    @commands.guild_only()
    @commands.check(check_if_user_has_sushi_1)
    @commands.check(check_if_user_has_shiki_set)
    @commands.cooldown(1, 500, commands.BucketType.user)
    async def perform_exploration(self, ctx, *, arg):
        user = ctx.author

        try:
            chapter = int(arg)
            await self.perform_exploration_by_chapter(chapter, user, ctx)
        except ValueError:
            if arg.lower() in ["last", "unf", "unfinished"]:
                query = explores.find_one({
                    "user_id": str(user.id),
                    "explores.completion": False
                }, {
                    "_id": 0,
                    "explores.$": 1
                })
                try:
                    chapter = query["explores"][0]["chapter"]
                    await self.perform_exploration_by_chapter(chapter, user, ctx)
                    self.client.get_command("perform_exploration").reset_cooldown(ctx)
                except TypeError:
                    embed = discord.Embed(
                        color=ctx.author.colour,
                        description=f"You have no pending explorations",
                        timestamp=self.get_timestamp()
                    )
                    embed.set_footer(text=user.display_name, icon_url=user.avatar_url)
                    await ctx.channel.send(embed=embed)
                    self.client.get_command("perform_exploration").reset_cooldown(ctx)

            else:
                embed = discord.Embed(
                    color=ctx.author.colour,
                    title="Invalid chapter",
                    description=f"that is not a valid chapter",
                )
                await ctx.channel.send(embed=embed)
                self.client.get_command("perform_exploration").reset_cooldown(ctx)

    async def perform_exploration_by_chapter(self, chapter, user, ctx):

        zone = zones.find_one({"chapter": chapter}, {"_id": 0})
        user_profile = users.find_one({"user_id": str(user.id)}, {"_id": 0, "level": 1, "display": 1, "exploration": 1})

        if chapter > zones.count():
            embed = discord.Embed(
                color=ctx.author.colour,
                title="Invalid chapter",
                description=f"that is not a valid chapter, < {zones.count()}",
            )
            await ctx.channel.send(embed=embed)

        elif chapter > user_profile["exploration"]:
            embed = discord.Embed(
                color=user.colour,
                title="Invalid chapter",
                description=f"you have not yet unlocked this chapter",
            )
            await ctx.channel.send(embed=embed)
            self.client.get_command("perform_exploration").reset_cooldown(ctx)

        else:
            def get_shikigami_stats(user_id, shiki):
                p = users.find_one({
                    "user_id": str(user_id), "shikigami.name": shiki
                }, {
                    "_id": 0,
                    "shikigami.$": 1
                })
                return p["shikigami"][0]["level"], p["shikigami"][0]["evolved"]

            spirits = zone["spirits"]
            sushi_required = zone["sushi_required"]
            user_level = user_profile["level"]
            shikigami_set = user_profile["display"]
            shikigami_level, shikigami_evolved = get_shikigami_stats(user.id, shikigami_set)

            evo_adjustment = 1
            if shikigami_evolved is True:
                evo_adjustment = 0.75

            total_chance = user_level + shikigami_level - chapter * evo_adjustment
            if total_chance <= 40:
                total_chance = 40

            adjusted_chance = random.uniform(total_chance * 0.95, total_chance)

            def create_embed_exploration(x, progress, strike):

                description2 = ""
                for log in progress:
                    description2 += log

                num = x + 1
                if num > spirits:
                    num = spirits

                user_profile_new = users.find_one({
                    "user_id": str(user.id), "shikigami.name": user_profile["display"]
                }, {
                    "_id": 0, "shikigami.$": 1, "sushi": 1
                })
                exp = user_profile_new["shikigami"][0]['exp']
                level_exp_next = user_profile_new["shikigami"][0]['level_exp_next']
                shiki_level = user_profile_new["shikigami"][0]['level']

                evo = users.find_one({
                    "user_id": str(user.id), "shikigami.name": shikigami_set}, {
                    "shikigami.$.name": 1
                })["shikigami"][0]["evolved"]
                thumbnail = self.get_thumbnail_shikigami(shikigami_set.lower(), self.get_evo_link(evo))

                embed_explore = discord.Embed(
                    color=ctx.author.colour,
                    title=f"{strike}Exploration stage: {num}/{spirits}{strike}",
                    description=f"Chapter {chapter}: {zone['name']}\n{description2}",
                    timestamp=self.get_timestamp()
                )
                embed_explore.add_field(
                    name=f"Shikigami: {user_profile['display'].title()} | {user_profile_new['sushi']} {e_s}",
                    value=f"Level: {shiki_level} | Experience: {exp}/{level_exp_next}\n"
                          f"Clear Chance: ~{round(total_chance, 2)}%"
                )
                embed_explore.set_footer(
                    text=f"{ctx.author.display_name}",
                    icon_url=ctx.author.avatar_url
                )
                embed_explore.set_thumbnail(url=thumbnail)

                return embed_explore

            if explores.find_one({"user_id": str(user.id)}, {"_id": 0}) is None:
                profile = {
                    "user_id": str(user.id),
                    "explores": []
                }
                explores.insert_one(profile)

            exploration_continuation = explores.find_one({
                "user_id": str(user.id),
                "explores.completion": False,
                "explores": {
                    "$elemMatch": {
                        "completion": False,
                        "chapter": chapter
                    }
                }
            }, {
                "_id": 0,
                "explores.$": 1
            })

            if exploration_continuation is None:
                explores.update_one({
                    "user_id": str(user.id)
                }, {
                    "$push": {
                        "explores": {
                            "$each": [{
                                "attempts": 0,
                                "logs": [],
                                "required": spirits,
                                "chapter": chapter,
                                "completion": False,
                                "date": self.get_time(),
                            }],
                            "$position": 0
                        }
                    }
                })

            new_explore = explores.find_one({
                "user_id": str(user.id),
                "explores.completion": False,
                "explores": {
                    "$elemMatch": {
                        "completion": False,
                        "chapter": chapter
                    }
                }
            }, {
                "_id": 0,
                "explores.$": 1
            })

            msg = await ctx.channel.send(
                embed=create_embed_exploration(new_explore['explores'][0]['attempts'], [], "")
            )
            await msg.add_reaction("🏹")

            def check(r, u):
                return \
                    msg.id == r.message.id and \
                    str(r.emoji) == "🏹" and \
                    u.id == ctx.author.id and \
                    check_if_user_has_sushi_2(ctx, sushi_required)

            while True:
                try:
                    reaction, user = await self.client.wait_for("reaction_add", timeout=60, check=check)
                except asyncio.TimeoutError:
                    await msg.clear_reactions()
                    break
                else:
                    users.update_one({
                        "user_id": str(user.id)
                    }, {
                        "$inc": {
                            "sushi": - sushi_required
                        }
                    })
                    await self.perform_add_log("sushi", -sushi_required, ctx.author.id)
                    roll = random.uniform(0, 100)
                    if roll < adjusted_chance:
                        explores.update_one({
                            "user_id": str(user.id), "explores.completion": False}, {
                            "$inc": {
                                "explores.$.attempts": 1
                            }
                        })

                        explores.update_one({
                            "user_id": str(user.id), "explores.completion": False}, {
                            "$push": {
                                "explores.$.logs": "✅"
                            }
                        })
                        new_explore = explores.find_one({
                            "user_id": str(user.id), "explores.completion": False}, {
                            "_id": 0,
                            "explores.$": 1,
                        })
                        shikigami_add_exp = users.update_one({
                            "user_id": str(user.id),
                            "$and": [{
                                "shikigami": {
                                    "$elemMatch": {
                                        "name": user_profile["display"],
                                        "level": {"$lt": 40}}
                                }}]
                        }, {
                            "$inc": {
                                "shikigami.$.exp": 5 * round((chapter + 1) / 2)
                            }
                        })

                        if shikigami_add_exp.modified_count > 0:
                            await self.shikigami_process_levelup(user.id, user_profile["display"])

                        report = new_explore["explores"][0]["logs"]
                        await msg.edit(
                            embed=create_embed_exploration(new_explore['explores'][0]['attempts'], report, "")
                        )

                        if new_explore["explores"][0]["attempts"] == spirits:
                            explores.update_one({
                                "user_id": str(user.id), "explores.completion": False}, {
                                "$set": {
                                    "explores.$.completion": True
                                }
                            })
                            new_explore = explores.find_one({
                                "user_id": str(user.id), "explores.completion": True}, {
                                "_id": 0,
                                "explores.$": 1,
                            })
                            report = new_explore["explores"][0]["logs"]
                            await msg.edit(embed=create_embed_exploration(spirits, report, "~~"))
                            await msg.clear_reactions()

                            embed_new = create_embed_exploration(spirits, report, "~~")
                            await self.perform_exploration_process_rewards(user.id, msg, embed_new, chapter)

                            explorations = users.find_one({"user_id": str(user.id)}, {"_id": 0, "exploration": 1})

                            if chapter == explorations["exploration"]:
                                users.update_one({
                                    "user_id": str(user.id),
                                    "exploration": {
                                        "$lt": 28
                                    }
                                }, {
                                    "$inc": {
                                        "exploration": 1
                                    }
                                })
                            break

                    else:
                        explores.update_one({
                            "user_id": str(user.id), "explores.completion": False}, {
                            "$push": {
                                "explores.$.logs": "❌"
                            }
                        })
                        new_explore = explores.find_one({
                            "user_id": str(user.id), "explores.completion": False}, {
                            "_id": 0,
                            "explores.$": 1,
                        })
                        report = new_explore["explores"][0]["logs"]
                        await msg.edit(
                            embed=create_embed_exploration(new_explore['explores'][0]['attempts'], report, "")
                        )

                    await msg.remove_reaction(str(reaction.emoji), user)

        self.client.get_command("perform_exploration").reset_cooldown(ctx)

    async def perform_exploration_process_rewards(self, user_id, msg, embed, chapter):

        zone = zones.find_one({"chapter": chapter})

        jades = round(random.uniform(zone["rewards_exact"]["jades"] * 0.8, zone["rewards_exact"]["jades"] * 1.1))
        coins = round(random.uniform(zone["rewards_exact"]["coins"] * 0.8, zone["rewards_exact"]["coins"] * 1.1))
        medals = round(random.uniform(zone["rewards_exact"]["medals"] * 0.8, zone["rewards_exact"]["medals"] * 1.1))
        amulets_b = zone["rewards_exact"]["amulets_b"] + random.randint(0, 2)

        users.update_one({
            "user_id": str(user_id)
        }, {
            "$inc": {
                "jades": jades,
                "coins": coins,
                "medals": medals,
                "amulets_b": amulets_b,
            }
        })
        await self.perform_add_log("jades", jades, user_id)
        await self.perform_add_log("coins", coins, user_id)
        await self.perform_add_log("medals", medals, user_id)
        await self.perform_add_log("amulets_b", amulets_b, user_id)

        shards_sp = zone["shards_count"]["SP"]
        shards_ssr = zone["shards_count"]["SSR"]
        shards_sr = zone["shards_count"]["SR"]
        shards_r = zone["shards_count"]["R"]
        shards_n = zone["shards_count"]["N"]

        shikigami_pool = {shiki: 0 for shiki in pool_ssr + pool_sp + pool_sr + pool_r + pool_n}

        i = 0
        while i < shards_sp:
            shikigami_shard = random.choice(pool_sp)
            shikigami_pool[shikigami_shard] += 1
            i += 1

        i = 0
        while i < shards_ssr:
            shikigami_shard = random.choice(pool_ssr)
            shikigami_pool[shikigami_shard] += 1
            i += 1

        i = 0
        while i < shards_sr:
            shikigami_shard = random.choice(pool_sr)
            shikigami_pool[shikigami_shard] += 1
            i += 1

        i = 0
        while i < shards_r:
            shikigami_shard = random.choice(pool_r)
            shikigami_pool[shikigami_shard] += 1
            i += 1

        i = 0
        while i < shards_n:
            shikigami_shard = random.choice(pool_n)
            shikigami_pool[shikigami_shard] += 1
            i += 1

        shards_reward = list(shikigami_pool.items())
        await self.perform_exploration_issue_shard_rewards(user_id, shards_reward)

        link = await self.perform_exploration_generate_shards(user_id, shards_reward)
        embed.set_image(url=link)

        embed.add_field(
            name="Completion rewards",
            value=f"{jades:,d}{self.get_emoji('jades')}, "
                  f"{coins:,d}{self.get_emoji('coins')}, "
                  f"{medals:,d}{self.get_emoji('medals')}, "
                  f"{amulets_b:,d}{self.get_emoji('amulets_b')}",
            inline=False
        )
        await msg.edit(embed=embed)

    async def perform_exploration_generate_shards(self, user_id, shards_reward):

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
        hosting_channel = self.client.get_channel(int(id_hosting))
        msg = await hosting_channel.send(file=new_photo)
        attachment_link = msg.attachments[0].url
        return attachment_link

    async def perform_exploration_issue_shard_rewards(self, user_id, shards_reward):
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
                self.shikigami_push_user(user_id, shikigami_shard[0], False, 0)

            users.update_one({"user_id": str(user_id), "shikigami.name": shikigami_shard[0]}, {
                "$inc": {
                    "shikigami.$.shards": 1
                }
            })

    @commands.command(aliases=["chapter", "ch"])
    @commands.guild_only()
    async def show_exploration_zones(self, ctx, *, arg1=None):

        if arg1 is None:
            embed = discord.Embed(
                title=f"chapter, ch",
                color=colour,
                description=f"shows chapter information and unlocked chapters"
            )
            embed.add_field(
                name="Format",
                value=f"*`{self.prefix}chapter <chapter#1-28>`*\n"
                      f"*`{self.prefix}chapter unlocked`*\n",
                inline=False
            )
            await ctx.channel.send(embed=embed)

        elif arg1.lower() == "unlocked":

            profile = users.find_one({
                "user_id": str(ctx.author.id)
            }, {
                "_id": 0,
                "exploration": 1
            })
            embed = discord.Embed(
                color=ctx.author.colour,
                description=f"You have access up to chapter {profile['exploration']}",
                timestamp=self.get_timestamp()
            )
            embed.set_footer(
                text=f"{ctx.author.display_name}",
                icon_url=ctx.author.avatar_url
            )
            await ctx.channel.send(embed=embed)

        else:

            chapter = int(arg1)
            profile = zones.find_one({"chapter": chapter}, {"_id": 0})

            try:
                description = f"```" \
                              f"Spirits          ::    {profile['spirits']}\n" \
                              f"Sushi/explore    ::    {profile['sushi_required']}" \
                              f"```"

                jades = profile["rewards_exact"]["jades"]
                coins = profile["rewards_exact"]["coins"]
                medals = profile["rewards_exact"]["medals"]
                amulets_b = profile["rewards_exact"]["amulets_b"]

                shards_sp = profile["shards_count"]["SP"]
                shards_ssr = profile["shards_count"]["SSR"]
                shards_sr = profile["shards_count"]["SR"]
                shards_r = profile["shards_count"]["R"]
                shards_n = profile["shards_count"]["N"]

                embed = discord.Embed(
                    title=f"Chapter {chapter}: {profile['name']}",
                    color=ctx.author.colour,
                    description=description
                )
                embed.add_field(
                    name="Completion rewards",
                    value=f"~{jades:,d}{self.get_emoji('jades')}, "
                          f"~{coins:,d}{self.get_emoji('coins')}, "
                          f"~{medals:,d}{self.get_emoji('medals')}, "
                          f"~{amulets_b:,d}{self.get_emoji('amulets_b')}",
                    inline=False
                )
                embed.add_field(
                    name="Shards drop count",
                    value=f"{e_1} {shards_sp} | {e_2} {shards_ssr} | {e_3} {shards_sr} | "
                          f"{e_4} {shards_r} | {e_5} {shards_n}",
                    inline=False
                )
                await ctx.channel.send(embed=embed)

            except TypeError:
                embed = discord.Embed(
                    title=f"Invalid chapter",
                    color=colour,
                    description="Available chapters: 1-28 only"
                )
                await ctx.channel.send(embed=embed)

    async def frame_acquisition(self, user, frame_name, jades):
        for entry in users.aggregate([
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
            if entry["count"] != 0:
                return

        spell_spam_channel = self.client.get_channel(int(id_spell_spam))

        users.update_one({
            "user_id": str(user.id)}, {
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
        await self.perform_add_log("jades", jades, user.id)
        intro_caption = " The "
        if frame_name[:3] == "The":
            intro_caption = " "

        embed = discord.Embed(
            color=user.colour,
            title="Frame acquisition",
            description=f"{user.mention} has obtained{intro_caption}{frame_name} frame!\n"
                        f"Acquired {jades:,d}{e_j} as bonus rewards!",
            timestamp=self.get_timestamp()
        )
        embed.set_footer(icon_url=user.avatar_url, text=f"{user.display_name}")
        embed.set_thumbnail(url=self.get_frame_thumbnail(frame_name))
        await spell_spam_channel.send(embed=embed)

    @commands.command(aliases=["up"])
    @commands.is_owner()
    async def compensate_increase_shikigami_level(self, ctx, member: discord.Member = None, *, args):

        shiki = args.lower()
        if shiki in pool_all:

            query = users.find_one({
                "user_id": str(member.id),
                "shikigami.name": shiki}, {
                "_id": 0, "shikigami.$": 1
            })

            if query is not None:
                users.update_one({
                    "user_id": str(member.id),
                    "shikigami.name": shiki}, {
                    "$set": {
                        "shikigami.$.level": 40,
                        "shikigami.$.exp": 10000,
                        "shikigami.$.level_exp_next": 10000
                    }
                })
                await ctx.message.add_reaction("✅")

    @commands.command(aliases=["lvl"])
    @commands.is_owner()
    async def compensate_increase_level(self, ctx, member: discord.Member = None):

        current_level = users.find_one({"user_id": str(member.id)}, {"_id": 0, "level": 1})["level"]

        if current_level != 60:
            users.update_one({
                "user_id": str(member.id)}, {
                "$set": {
                    "level": 60, "experience": 100000, "level_exp_next": 100000
                },
                "$inc": {
                    "amulets": (60 - current_level) * 10
                }
            })
            await ctx.message.add_reaction("✅")

    @commands.command(aliases=["compensate"])
    @commands.is_owner()
    async def compensate_economy_items(self, ctx, member: discord.Member = None):

        users.update_one({
            "user_id": str(member.id)}, {
            "$inc": {
                "amulets": 2500,
                "jades": 30000,
                "coins": 50000000,
                "amulets_b": 750,
                "sushi": 2500,
                "realm_ticket": 250,
                "encounter_ticket": 150,
                "parade_tickets": 100,
                "talisman": 500000,
                "friendship_pass": 250,
                "friendship": 2000
            }
        })
        await ctx.message.add_reaction("✅")

    @commands.command(aliases=["push"])
    @commands.is_owner()
    async def compensate_push_shikigami_manually(self, ctx, member: discord.Member = None, *, args):

        shiki = args.lower()
        if shiki in pool_all:

            query = users.find_one({
                "user_id": str(member.id),
                "shikigami.name": shiki}, {
                "_id": 0, "shikigami.$": 1
            })

            if query is None:
                self.shikigami_push_user(member.id, shiki, evolve=True, shards=0)

            users.update_one({
                "user_id": str(member.id),
                "shikigami.name": shiki}, {
                "$inc": {
                    "shikigami.$.owned": 1
                }
            })
            users.update_one({
                "user_id": str(member.id)
            }, {
                "$inc": {
                    self.get_rarity_shikigami(shiki): 1
                }
            })
            await ctx.message.add_reaction("✅")


def setup(client):
    client.add_cog(Economy(client))
