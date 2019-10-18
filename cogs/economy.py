"""
Economy Module
Miketsu, 2019
"""

import asyncio
import os
import random
from datetime import datetime
from itertools import cycle
from math import ceil

import discord
import pytz
from PIL import Image, ImageFont, ImageDraw
from discord.ext import commands

from cogs.frames import Frames
from cogs.mongo.database import get_collections

# Collections
guilds = get_collections("guilds")
bounties = get_collections("bounties")
shikigamis = get_collections("shikigamis")
users = get_collections("users")
ships = get_collections("ships")
streaks = get_collections("streaks")
frames = get_collections("frames")
bosses = get_collections("bosses")
config = get_collections("config")
logs = get_collections("logs")

# Dictionary
emojis = config.find_one({"dict": 1}, {"_id": 0, "emojis": 1})["emojis"]
mystic_shop = config.find_one({"dict": 1}, {"_id": 0, "mystic_shop": 1})["mystic_shop"]
shard_requirement = config.find_one({"dict": 1}, {"_id": 0, "shard_requirement": 1})["shard_requirement"]
evo_requirement = config.find_one({"dict": 1}, {"_id": 0, "evo_requirement": 1})["evo_requirement"]
talisman_acquire = config.find_one({"dict": 1}, {"_id": 0, "talisman_acquire": 1})["talisman_acquire"]

# Variables
guild_id = int(os.environ.get("SERVER"))
timezone = config.find_one({"var": 1}, {"_id": 0, "timezone": 1})["timezone"]
embed_color = config.find_one({"var": 1}, {"_id": 0, "embed_color": 1})["embed_color"]
hosting_id = guilds.find_one({"server": str(guild_id)}, {"_id": 0, "channels": 1})["channels"]["bot-sparring"]


e_m = emojis["m"]
e_j = emojis["j"]
e_c = emojis["c"]
e_f = emojis["f"]
e_t = emojis["t"]
e_a = emojis["a"]
e_b = emojis["b"]
e_1 = emojis["1"]
e_2 = emojis["2"]
e_3 = emojis["3"]
e_4 = emojis["4"]
e_5 = emojis["5"]

# Lists
pool_sp = []
pool_ssr = []
pool_sr = []
pool_r = []
pool_n = []

pool_shrine = []
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

developer_team = guilds.find_one({"server": str(guild_id)}, {"_id": 0, "developers": 1})["developers"]
spell_spam_id = guilds.find_one({"server": str(guild_id)}, {"_id": 0, "channels": 1})["channels"]["spell-spam"]
summon_captions_a = cycle(config.find_one({"list": 1}, {"_id": 0, "summon_captions": 1})["summon_captions"])


for document in frames.find({"purchase": True}, {"_id": 1, "name": 1}):
    purchasable_frames.append(document["name"].lower())

for shikigami in shikigamis.find({}, {"_id": 0, "name": 1, "rarity": 1, "shrine": 1, "amulet": "mystery"}):
    if shikigami["shrine"] is True:
        pool_shrine.append(shikigami["name"])
    elif shikigami["rarity"] == "SP":
        pool_sp.append(shikigami["name"])
    elif shikigami["rarity"] == "SSR":
        pool_ssr.append(shikigami["name"])
    elif shikigami["rarity"] == "SR":
        pool_sr.append(shikigami["name"])
    elif shikigami["rarity"] == "R":
        pool_r.append(shikigami["name"])


pool_all_mystery.extend(pool_sp)
pool_all_mystery.extend(pool_ssr)
pool_all_mystery.extend(pool_sr)
pool_all_mystery.extend(pool_r)
pool_all_mystery.extend(pool_shrine)


def pluralize(singular, count):
    if count > 1:
        if singular[-1:] == "s":
            return singular + "es"
        return singular + "s"
    else:
        return singular


def check_if_developer_team(ctx):
    return str(ctx.author.id) in developer_team


def check_if_user_has_prayers(ctx):
    return users.find_one({"user_id": str(ctx.author.id)}, {"_id": 0, "prayers": 1})["prayers"] > 0


def check_if_user_has_parade_tickets(ctx):
    return users.find_one({"user_id": str(ctx.author.id)}, {"_id": 0, "parade_tickets": 1})["parade_tickets"] > 0


def get_frame_thumbnail(frame):
    return frames.find_one({"name": frame}, {"_id": 0, "link": 1})["link"]


def get_time():
    return datetime.now(tz=pytz.timezone(timezone))


def get_timestamp():
    return datetime.utcfromtimestamp(datetime.timestamp(datetime.now()))


def get_bond(x, y):
    bond_list = sorted([x.id, y.id], reverse=True)
    return f"{bond_list[0]}x{bond_list[1]}"


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


def emojify(item):
    emoji_dict = {
        "jades": e_j, "coins": e_c, "realm_ticket": "🎟", "amulets": e_a,
        "medals": e_m, "friendship": e_f, "encounter_ticket": "🎫", "talisman": e_t,
        "prayers": "🙏", "friendship_pass": "💗", "parade_tickets": "🎏"
    }
    return emoji_dict[item]


def get_offer_and_cost(x):
    _offer_item = mystic_shop[x[0]][x[1]]["offer"][0]
    _offer_amount = mystic_shop[x[0]][x[1]]["offer"][1]
    _cost_item = mystic_shop[x[0]][x[1]]["cost"][0]
    _cost_amount = mystic_shop[x[0]][x[1]]["cost"][1]

    return _offer_item, _offer_amount, _cost_item, _cost_amount


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
        f"▫ `{trade[1]}`{emojify(trade[0])} → `{trade[3]:,d}`{emojify(trade[2])} | {trade[4]} {trade[5]}\n"
    )


def get_shard_requirement(shiki):
    rarity = shikigamis.find_one({"name": shiki.lower()}, {"_id": 0, "rarity": 1})["rarity"]
    return shard_requirement[rarity], rarity


def get_evo_link(evolution):
    return {True: "evo", False: "pre"}[evolution]


def get_rarity_emoji(rarity):
    return {"SP": e_1, "SSR": e_2, "SR": e_3, "R": e_4}[rarity]


def get_rarity_shikigami(shiki):
    return shikigamis.find_one({"name": shiki}, {"_id": 0, "rarity": 1})["rarity"]


def get_evo_requirement(r):
    return evo_requirement[r]


def get_talisman_acquire(rarity):
    return talisman_acquire[rarity]


def get_thumbnail_shikigami(shiki, evolution):
    return shikigamis.find_one({"name": shiki.lower()}, {"_id": 0, "thumbnail": 1})["thumbnail"][evolution]


async def reset_boss():
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


async def frame_acquisition(user, frame_name, channel, jades):
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
    await logs_add_line("jades", jades, user.id)
    embed = discord.Embed(
        color=user.colour,
        title="Frame Acquisition",
        description=f"{user.mention}, you acquired the {frame_name} frame and {jades:,d}{e_j}",
        timestamp=get_timestamp()
    )
    embed.set_footer(icon_url=user.avatar_url, text=f"{user.display_name}")
    embed.set_thumbnail(url=get_frame_thumbnail(frame_name.title()))
    await channel.send(embed=embed)


async def claim_rewards_daily_give(user, ctx):
    friendship_pass, jades, coins, realm_ticket, encounter_ticket, parade_tickets = 5, 100, 50000, 3, 4, 3

    users.update_one({"user_id": str(user.id)}, {
        "$inc": {
            "friendship_pass": friendship_pass,
            "jades": jades,
            "coins": coins,
            "realm_ticket": realm_ticket,
            "encounter_ticket": encounter_ticket,
            "parade_tickets": parade_tickets
        },
        "$set": {
            "daily": True
        }
    })

    await logs_add_line("friendship_pass", friendship_pass, user.id)
    await logs_add_line("jades", jades, user.id)
    await logs_add_line("coins", coins, user.id)
    await logs_add_line("realm_ticket", realm_ticket, user.id)
    await logs_add_line("encounter_ticket", encounter_ticket, user.id)
    await logs_add_line("parade_tickets", parade_tickets, user.id)

    embed = discord.Embed(
        color=ctx.author.colour,
        title="🎁 Daily Rewards",
        description=f"A box containing {friendship_pass} 💗, {jades}{e_j}, {coins:,d}{e_c}, {realm_ticket} 🎟, "
                    f"{encounter_ticket} 🎫, {parade_tickets} 🎏",
        timestamp=get_timestamp()
    )
    embed.set_footer(text=f"Opened by {user.display_name}", icon_url=user.avatar_url)
    await ctx.channel.send(embed=embed)


async def claim_rewards_weekly_give(user, ctx):
    jades, coins, amulets = 750, 250000, 10

    users.update_one({"user_id": str(user.id)}, {
        "$inc": {
            "jades": jades,
            "coins": coins,
            "amulets": amulets
        },
        "$set": {
            "weekly": True
        }
    })

    await logs_add_line("jades", jades, user.id)
    await logs_add_line("coins", coins, user.id)
    await logs_add_line("amulets", amulets, user.id)

    embed = discord.Embed(
        color=ctx.author.colour,
        title="💝 Weekly Rewards",
        description=f"A mythical box containing {jades}{e_j}, {coins:,d}{e_c}, and {amulets}{e_a}",
        timestamp=get_timestamp()
    )
    embed.set_footer(text=f"Opened by {user.display_name}", icon_url=user.avatar_url)
    await ctx.channel.send(embed=embed)


async def perform_evolution_shikigami(ctx, rarity, evo, user, query, count):
    if rarity == "SP":
        embed = discord.Embed(
            colour=discord.Colour(embed_color),
            title="Invalid shikigami",
            description=f"SP shikigamis are already evolved upon summoning"
        )
        await ctx.channel.send(embed=embed)

    elif evo is True:
        embed = discord.Embed(
            colour=discord.Colour(embed_color),
            description=f"{user.mention}, your {query.title()} is already evolved.",
            timestamp=get_timestamp()
        )
        embed.set_footer(icon_url=user.avatar_url, text=f"{user.display_name}")
        embed.set_thumbnail(url=get_thumbnail_shikigami(query, "evo"))
        await ctx.channel.send(embed=embed)

    elif evo is False:
        rarity_count = get_evo_requirement(rarity)

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
                description=f"{user.mention}, you have evolved your {query.title()}!\n"
                            f"Acquired 5 shards of this shikigami!",
                timestamp=get_timestamp()
            )
            embed.set_footer(icon_url=user.avatar_url, text=f"{user.    display_name}")
            embed.set_thumbnail(url=image_url)
            await ctx.channel.send(embed=embed)

            if query == "orochi":
                await frame_acquisition(user, "Sword Swallowing-Snake", ctx.channel, jades=2500)

        elif count == 0:
            embed = discord.Embed(
                colour=discord.Colour(embed_color),
                description=f"{user.mention}, you do not own that shikigami",
                timestamp=get_timestamp()
            )
            await ctx.channel.send(embed=embed)

        elif count <= (get_evo_requirement(rarity) - 1):
            required = rarity_count - count
            noun_duplicate = pluralize('dupe', required)
            embed = discord.Embed(
                colour=discord.Colour(embed_color),
                title="Insufficient shikigamis",
                description=f"{user.mention}, you lack {required} more {query.title()} {noun_duplicate} "
                            f"to evolve yours",
                timestamp=get_timestamp()
            )
            await ctx.channel.send(embed=embed)


async def frame_starlight(guild, spell_spam_channel):
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
            f"🍀 No SSR streak as of posting: {streak_list_new[0][1]} summons!"

        embed = discord.Embed(
            color=0xac330f,
            title="📨 Hall of Framers Update",
            description=description,
            timestamp=get_timestamp()
        )
        embed.set_thumbnail(url="https://vignette.wikia.nocookie.net/onmyoji/images/1/17/Frame7.png")
        await spell_spam_channel.send(embed=embed)
        await frame_acquisition(starlight_new, "Starlight Sky", spell_spam_channel, jades=2500)

    if starlight_current == starlight_new:
        users.update_one({"user_id": str(starlight_current.id)}, {"$inc": {"jades": 2000}})
        await logs_add_line("jades", 2000, starlight_current.id)
        msg = f"{starlight_current.mention} has earned 2,000{e_j} " \
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
            f"🍀 No SSR streak record as of posting: {streak_list_new[0][1]} summons!"

        embed = discord.Embed(
            color=0xac330f,
            title="📨 Hall of Framers Update",
            description=description,
            timestamp=get_timestamp()
        )
        embed.set_thumbnail(url="https://vignette.wikia.nocookie.net/onmyoji/images/1/17/Frame7.png")
        await spell_spam_channel.send(embed=embed)
        await frame_acquisition(starlight_new, "Starlight Sky", spell_spam_channel, jades=2500)


async def frame_blazing(guild, spell_spam_channel):
    blazing_role = discord.utils.get(guild.roles, name="Blazing Sun")

    ssr_list = []
    for user in users.find({}, {"_id": 0, "user_id": 1, "SSR": 1}):
        ssr_list.append((user["user_id"], user["SSR"]))

    ssr_list_new = sorted(ssr_list, key=lambda x: x[1], reverse=True)
    blazing_new = guild.get_member(int(ssr_list_new[0][0]))
    blazing_current = blazing_role.members[0]

    if len(blazing_role.members) == 0:
        await blazing_new.add_roles(blazing_role)
        await asyncio.sleep(3)

        description = \
            f"{blazing_new.mention}\"s fortune luck earned themselves the Rare Blazing Sun Frame!\n\n" \
            f"🍀 Distinct SSRs under possession: {ssr_list_new[0][1]} shikigamis"

        embed = discord.Embed(
            color=0xac330f,
            title="📨 Hall of Framers Update",
            description=description,
            timestamp=get_timestamp()
        )
        embed.set_thumbnail(url="https://vignette.wikia.nocookie.net/onmyoji/images/7/72/Frame62.png")
        await spell_spam_channel.send(embed=embed)
        await frame_acquisition(blazing_new, "Blazing Sun", spell_spam_channel, jades=2500)

    if blazing_current == blazing_new:
        users.update_one({"user_id": str(blazing_current.id)}, {"$inc": {"amulets": 10}})
        await logs_add_line("amulets", 10, blazing_current.id)
        msg = f"{blazing_current.mention} has earned 10{e_a} for wielding the Blazing Sun frame for a day!"
        await spell_spam_channel.send(msg)

    else:
        await blazing_new.add_roles(blazing_role)
        await asyncio.sleep(3)
        await blazing_current.remove_roles(blazing_role)
        await asyncio.sleep(3)

        description = f"{blazing_new.mention} {random.choice(steal_adverb)} {random.choice(steal_verb)} " \
                      f"the Rare Blazing Sun Frame from {blazing_current.mention}\"s {random.choice(steal_noun)}!! " \
                      f"{random.choice(steal_comment)}\n\n" \
                      f"🍀 Distinct SSRs under possession: {ssr_list_new[0][1]} shikigamis"

        embed = discord.Embed(
            color=0xffff80,
            title="📨 Hall of Framers Update",
            description=description,
            timestamp=get_timestamp()
        )
        embed.set_thumbnail(url="https://vignette.wikia.nocookie.net/onmyoji/images/7/72/Frame62.png")
        await spell_spam_channel.send(embed=embed)
        await frame_acquisition(blazing_new, "Blazing Sun", spell_spam_channel, jades=2500)


async def shop_process_purchase(user, ctx, offer_item, offer_amount, cost_item, cost_amount, msg):

    if users.find_one({"user_id": str(user.id)}, {"_id": 0, cost_item: 1})[cost_item] >= int(cost_amount):
        users.update_one({
            "user_id": str(user.id)}, {
            "$inc": {
                offer_item: int(offer_amount),
                cost_item: -int(cost_amount)
            }
        })
        await logs_add_line(offer_item, offer_amount, user.id)
        await logs_add_line(cost_item, -cost_amount, user.id)

        cost_item_have = users.find_one({"user_id": str(user.id)}, {"_id": 0, cost_item: 1})[cost_item]
        offer_item_have = users.find_one({"user_id": str(user.id)}, {"_id": 0, offer_item: 1})[offer_item]

        embed = discord.Embed(
            title="Purchase successful", colour=discord.Colour(embed_color),
            timestamp=get_timestamp()
        )
        embed.set_footer(icon_url=user.avatar_url, text=f"{user.display_name}")
        embed.description = f"acquired `{offer_amount:,d}`{emojify(offer_item)} " \
                            f"in exchanged for `{cost_amount:,d}`{emojify(cost_item)}"
        embed.set_thumbnail(url="https://vignette.wikia.nocookie.net/onmyoji/images/8/86/246a.jpg")
        embed.add_field(
            name="Inventory",
            value=f"`{offer_item_have:,d}` {emojify(offer_item)} | `{cost_item_have:,d}` {emojify(cost_item)}"
        )
        await msg.edit(embed=embed)

    else:
        embed = discord.Embed(
            title="Purchase failure", colour=discord.Colour(embed_color),
            description=f"{user.mention}, you have insufficient {emojify(cost_item)}",
            timestamp=get_timestamp()
        )
        embed.set_footer(icon_url=user.avatar_url, text=f"{user.display_name}")
        await ctx.channel.send(embed=embed)


async def shop_process_purchase_frame(ctx, user, currency, amount, frame_name, emoji):
    if users.find_one({"user_id": str(user.id)}, {"_id": 0, currency: 1})[currency] >= amount:

        if users.find_one({"user_id": str(user.id), "achievements.name": frame_name}, {"_id": 0}) is not None:
            users.update_one({
                "user_id": str(user.id)}, {
                "$inc": {
                    currency: -amount
                },
                "$push": {
                    "achievements": {
                        "name": frame_name,
                        "date_acquired": get_time()
                    }
                }
            })
            await logs_add_line(currency, -amount, user.id)

            embed = discord.Embed(
                title="Confirmation receipt", colour=discord.Colour(embed_color),
                description=f"{user.mention} acquired {emoji} {frame_name} "
                            f"in exchanged for {amount:,d}{emojify(currency)}",
                timestamp=get_timestamp()
            )
            await ctx.channel.send(embed=embed)

        else:
            embed = discord.Embed(
                title="Purchase failure", colour=discord.Colour(embed_color),
                description=f"{user.mention}, you already have that frame",
                timestamp=get_timestamp()
            )
            await ctx.channel.send(embed=embed)

    else:
        embed = discord.Embed(
            title="Purchase failure", colour=discord.Colour(embed_color),
            description=f"{user.mention}, you have insufficient {emojify(currency)}",
            timestamp=get_timestamp()
        )
        await ctx.channel.send(embed=embed)


async def summon_mystery_update(user, sum_sp, sum_ssr, sum_sr, sum_r, amulet_pull, summon_pull):
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

    for summon in summon_pull:

        query = users.find_one({
            "user_id": str(user.id),
            "shikigami.name": summon[1].replace("||", "")}, {
            "_id": 0, "shikigami.$": 1
        })

        if query is None:
            evolve, shards = False, 0
            if summon[0] == "SP":
                evolve, shards = True, 5

            users.update_one({
                "user_id": str(user.id)}, {
                "$push": {
                    "shikigami": {
                        "name": summon[1].replace("||", ""),
                        "rarity": summon[0],
                        "grade": 1,
                        "owned": 0,
                        "evolved": evolve,
                        "shards": shards
                    }
                }
            })

        users.update_one({
            "user_id": str(user.id),
            "shikigami.name": summon[1].replace("||", "")}, {
            "$inc": {
                "shikigami.$.owned": 1
            }
        })


async def summon_mystery_streak(user, summon_pull):
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


async def summon_mystery_perform(ctx, user, amulet_pull):
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

    f_sp = str(sum_sp) + " " + pluralize("SP", sum_sp)
    f_ssr = str(sum_ssr) + " " + pluralize("SSR", sum_ssr)
    f_sr = str(sum_sr) + " " + pluralize("SR", sum_sr)
    f_r = str(sum_r) + " " + pluralize("R", sum_r)

    description = ""
    for x in summon_pull:
        description += "🔸{}\n".format(x[1].title())

    embed = discord.Embed(color=user.colour, title="🎊 Results", description=description, timestamp=get_timestamp())

    if amulet_pull == 10:
        embed.set_footer(text=f"{f_sp}; {f_ssr}; {f_sr}; {f_r}", icon_url=user.avatar_url)

    elif amulet_pull == 1:
        shikigami_pulled = summon_pull[0][1].replace("||", "")
        embed.set_thumbnail(url=get_thumbnail_shikigami(shikigami_pulled, "pre"))

    msg = "{}".format(next(summon_captions_a)).format(user.mention)
    await ctx.channel.send(msg, embed=embed)
    await summon_mystery_update(user, sum_sp, sum_ssr, sum_sr, sum_r, amulet_pull, summon_pull)
    await summon_mystery_streak(user, summon_pull)


async def summon_mystery_perform_shards(ctx, shiki, user):
    try:
        profile = users.find_one({
            "user_id": str(user.id), "shikigami.name": shiki}, {
            "_id": 0, "shikigami.$.name": 1
        })

        shards = profile["shikigami"][0]["shards"]
        required_shards, rarity = get_shard_requirement(shiki)

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
                            "shards": shards
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
                title="Summon success", colour=discord.Colour(embed_color),
                description=f"{user.mention}, you summoned the {rarity} shikigami {shiki.title()}!",
                timestamp=get_timestamp()
            )
            embed.set_thumbnail(url=get_thumbnail_shikigami(shiki, "pre"))
            await ctx.channel.send(embed=embed)

        else:
            embed = discord.Embed(
                title="Summon failed", colour=discord.Colour(embed_color),
                description=f"{user.mention}, you lack {required_shards - shards} {shiki} shards",
                timestamp=get_timestamp()
            )
            await ctx.channel.send(embed=embed)

    except TypeError:
        embed = discord.Embed(
            title="Summon failed", colour=discord.Colour(embed_color),
            description=f"{user.mention}, you do not have any shards of {shiki}",
            timestamp=get_timestamp()
        )
        await ctx.channel.send(embed=embed)


async def level_add_experience(user, exp):
    if users.find_one({"user_id": str(user.id)}, {"_id": 0, "level": 1})["level"] == 60:
        return
    else:
        users.update_one({"user_id": str(user.id)}, {"$inc": {"experience": exp}})


async def level_add_level(user, ctx):
    profile = users.find_one({"user_id": str(user.id)}, {"_id": 0, "experience": 1, "level": 1})
    exp = profile["experience"]
    level = profile["level"]
    level_end = int(exp ** 0.3556302501)

    if level > level_end:
        users.update_one({"user_id": str(user.id)}, {"$set": {"level": level_end}})

    if level < level_end:
        level_next = 5 * (round(((level + 2) ** 2.811909279) / 5))
        users.update_one({
            "user_id": str(user.id)}, {
            "$set": {
                "level_exp_next": level_next,
                "level": level_end
            },
            "$inc": {
                "jades": 150, "amulets": 10, "coins": 100000
            }
        })

        await logs_add_line("jades", 150, user.id)
        await logs_add_line("amulets", 10, user.id)
        await logs_add_line("coins", 100000, user.id)

        if level_end == 60:
            users.update_one({
                "user_id": str(user.id)}, {
                "$set": {
                    "level_exp_next": 100000,
                    "level": 60
                },
                "$inc": {
                    "jades": 4000, "amulets": 50, "coins": 1000000
                }
            })

            await logs_add_line("jades", 4000, user.id)
            await logs_add_line("amulets", 50, user.id)
            await logs_add_line("coins", 1000000, user.id)

        try:
            await ctx.add_reaction("⤴")
        except discord.errors.HTTPException:
            return


async def level_create_user(user):
    if users.find_one({"user_id": str(user.id)}, {"_id": 0}) is None:
        profile = {
            "user_id": str(user.id),
            "experience": 0,
            "level": 1,
            "level_exp_next": 5,
            "amulets": 10,
            "amulets_spent": 0,
            "SP": 0,
            "SSR": 0,
            "SR": 0,
            "R": 0,
            "jades": 0,
            "coins": 0,
            "medals": 0,
            "realm_ticket": 3,
            "honor": 0,
            "talisman": 0,
            "friendship": 0,
            "guild_medal": 0,
            "shikigami": [],
            "encounter_ticket": 0,
            "daily": False,
            "weekly": False,
            "raided_count": 0,
            "friendship_pass": 0,
            "display": None,
            "prayers": 3,
            "achievements": [],
            "frame": "",
            "achievements_count": 0,
            "wish": True,
            "parade_tickets": 0,
            "amulets_b": 0,
            "amulets_spent_b": 0,
            "N": 0
        }
        users.insert_one(profile)


async def logs_add_line(currency, amount, user_id):

    if logs.find_one({"user_id": str(user_id)}, {"_id": 0}) is None:
        profile = {
            "user_id": str(user_id),
            "logs": []
        }
        logs.insert_one(profile)

    logs.update_one({
        "user_id": str(user_id)
    }, {
        "$push": {
            f"logs": {
                "$each": [{
                    "currency": currency,
                    "amount": amount,
                    "date": get_time(),
                }],
                "$position": 0
            }
        }
    })


async def shikigami_post_approximate_results(ctx, query):

    shikigamis_search = shikigamis.find({
        "name": {"$regex": f"^{query[:2].lower()}"}
    }, {"_id": 0, "name": 1})

    approximate_results = []
    for result in shikigamis_search:
        approximate_results.append(f"{result['name'].title()}")

    embed = discord.Embed(
        title="Invalid shikigami", colour=discord.Colour(embed_color),
        description=f"check the spelling of the shikigami"
    )
    embed.add_field(
        name="Possible matches",
        value="*{}*".format(", ".join(approximate_results)),
        inline=False
    )
    await ctx.channel.send(embed=embed)


class Economy(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.prefix = self.client.command_prefix

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author == self.client.user:
            return

        elif message.author.bot is True:
            return

        await level_create_user(message.author)
        await level_add_experience(message.author, 5)
        await level_add_level(message.author, message)

    @commands.command(aliases=["wish"])
    @commands.guild_only()
    async def wish_perform(self, ctx, *, shiki=None):

        user = ctx.author
        profile = users.find_one({"user_id": str(user.id)}, {"_id": 0, "wish": 1})

        if shiki is None:
            embed = discord.Embed(
                color=embed_color,
                title="wish, w",
                description=f"wish for a shikigami shard to manually summon it"
            )
            embed.add_field(name="Example", value=f"*`{self.prefix}wish inferno ibaraki`*")
            await ctx.channel.send(embed=embed)

        elif profile["wish"] is False:
            embed = discord.Embed(
                color=user.colour,
                description=f"{user.mention}, your wish has been fulfilled already today",
                timestamp=get_timestamp()
            )
            await ctx.channel.send(embed=embed)

        elif profile["wish"] is not True:
            embed = discord.Embed(
                color=user.colour,
                description=f"{user.mention}, you have wished already today",
                timestamp=get_timestamp()
            )
            await ctx.channel.send(embed=embed)

        elif profile["wish"] is True and shiki.lower() not in pool_all_mystery:
            embed = discord.Embed(
                color=user.colour,
                description=f"{user.mention}, you provided an invalid shikigami name",
                timestamp=get_timestamp()
            )
            await ctx.channel.send(embed=embed)

        elif profile["wish"] is True and shiki.lower() in pool_all_mystery:

            users.update_one({"user_id": str(user.id)}, {"$set": {"wish": shiki.lower()}})
            query = users.find_one({
                "user_id": str(user.id),
                "shikigami.name": shiki.lower()}, {
                "_id": 0, "shikigami.$": 1
            })

            if query is None:
                users.update_one({
                    "user_id": str(user.id)}, {
                    "$push": {
                        "shikigami": {
                            "name": shiki.lower(),
                            "rarity": get_rarity_shikigami(shiki.lower()),
                            "grade": 1,
                            "owned": 0,
                            "evolved": False,
                            "shards": 0
                        }
                    }
                })



            embed = discord.Embed(
                color=user.colour,
                title=f"Wish registered",
                description=f"{user.mention}, you wished for {shiki.title()} shard",
                timestamp=get_timestamp()
            )
            embed.set_footer(icon_url=user.avatar_url, text=f"{user.display_name}")
            embed.set_thumbnail(url=get_thumbnail_shikigami(shiki, "pre"))
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
                color=embed_color,
                title=f"🗒 Wish List [{ordinal(get_time().timetuple().tm_yday)} day]",
                description=f"{description_new}",
                timestamp=get_timestamp()
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
                timestamp=get_timestamp()
            )
            embed.add_field(name="Format", value=f"*`{self.prefix}ff <@member>`*")
            await ctx.channel.send(embed=embed)
            return

        try:
            shikigami_wished_for = users.find_one({"user_id": str(member.id)}, {"_id": 0, "wish": 1})["wish"]

        except KeyError:
            embed = discord.Embed(
                title="Invalid member", colour=discord.Colour(embed_color),
                description="That member doesn't exist nor has a profile in this guild",
                timestamp=get_timestamp()
            )
            await ctx.channel.send(embed=embed)
            return

        except TypeError:
            return

        if shikigami_wished_for is True:
            embed = discord.Embed(
                color=user.colour,
                title=f"Invalid member",
                description=f"{user.mention}, that user has not placed their daily wish yet",
                timestamp=get_timestamp()
            )
            await ctx.channel.send(embed=embed)

        elif shikigami_wished_for is False:
            embed = discord.Embed(
                color=user.colour,
                title=f"Wish fulfillment failed",
                description=f"{user.mention}, that user has their wish fulfilled already",
                timestamp=get_timestamp()
            )
            await ctx.channel.send(embed=embed)

        else:
            profile = users.find_one({
                "user_id": str(user.id), "shikigami.name": shikigami_wished_for}, {
                "_id": 0, "shikigami.$.name": 1
            })

            if profile is None:
                embed = discord.Embed(
                    color=user.colour,
                    title=f"Insufficient shards",
                    description=f"{user.mention}, you do not have any shards of that shikigami",
                    timestamp=get_timestamp()
                )
                await ctx.channel.send(embed=embed)

            elif profile["shikigami"][0]["shards"] == 0:
                embed = discord.Embed(
                    color=user.colour,
                    title=f"Insufficient shards",
                    description=f"{user.mention}, you do not have any shards of that shikigami",
                    timestamp=get_timestamp()
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
                await logs_add_line("friendship_pass", 3, user.id)
                await logs_add_line("friendship", 10, user.id)

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
                    description=f"{user.mention}, you donated 1 "
                                f"{shikigami_wished_for.title()} shard to {member.mention}\n"
                                f"Acquired 10{e_f} and 3 💗",
                    timestamp=get_timestamp()
                )
                embed.set_thumbnail(url=get_thumbnail_shikigami(shikigami_wished_for, "pre"))
                await ctx.channel.send(embed=embed)

    @commands.command(aliases=["reset"])
    @commands.check(check_if_developer_team)
    async def perform_reset(self, ctx, *, args):

        if args == "daily":
            await self.reset_rewards_daily()
            await ctx.message.add_reaction("✅")

        elif args == "weekly":
            await self.reset_rewards_weekly()
            await Frames(self.client).achievements_process_weekly()
            await ctx.message.add_reaction("✅")

        elif args == "boss":
            await reset_boss()
            await ctx.message.add_reaction("✅")

        elif args not in ["daily", "weekly", "boss"]:
            embed = discord.Embed(
                colour=discord.Colour(embed_color),
                title="Invalid argument",
                description="Provide a valid argument: `daily`, `weekly`, or `boss`"
            )
            await ctx.channel.send(embed=embed)

    async def reset_rewards_daily(self):

        users.update_many({}, {"$set": {"daily": False, "raided_count": 0, "prayers": 3, "wish": True}})
        query = {"level": {"$gt": 1}}
        project = {"ship_name": 1, "shipper1": 1, "shipper2": 1, "level": 1}

        for ship in ships.find(query, project):
            rewards = ship["level"] * 25
            users.update_one({"user_id": ship["shipper1"]}, {"$inc": {"jades": rewards}})
            users.update_one({"user_id": ship["shipper2"]}, {"$inc": {"jades": rewards}})

            await logs_add_line("jades", rewards, ship['shipper1'])
            await logs_add_line("jades", rewards, ship['shipper2'])

        embed1 = discord.Embed(
            title="🎁 Daily rewards have been reset and issued", colour=discord.Colour(embed_color),
            description=f"Claim yours using `{self.prefix}daily` and your income using `{self.prefix}sail`"
        )

        spell_spam_channel = self.client.get_channel(int(spell_spam_id))
        await spell_spam_channel.send(embed=embed1)

    async def reset_rewards_weekly(self):

        users.update_many({}, {"$set": {"weekly": False}})

        embed = discord.Embed(
            title="💝 Weekly rewards have been reset", colour=discord.Colour(embed_color),
            description=f"Claim yours using `{self.prefix}weekly`"
        )
        spell_spam_channel = self.client.get_channel(int(spell_spam_id))
        await spell_spam_channel.send(embed=embed)

    @commands.command(aliases=["stat"])
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
                timestamp=get_timestamp()
            )

            embed.set_author(name="Summon Pull Statistics")
            embed.add_field(name="Total Amulets Spent", value=f"{count_total:,d}")
            await ctx.channel.send(embed=embed)

        elif name.lower() not in pool_all_mystery:
            embed = discord.Embed(
                title="Invalid shikigami name",
                colour=discord.Colour(embed_color),
                description="Try again",
                timestamp=get_timestamp()
            )
            await ctx.channel.send(embed=embed)

        elif name.lower() in pool_all_mystery:

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

            thumbnail_url = get_thumbnail_shikigami(name.lower(), "evo")

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
                title=f"Stats for {name.title()}", colour=ctx.author.colour,
                description=f"```"
                            f"Pre-evolve    ::   {count_pre_evo}\n"
                            f"Evolved       ::   {count_evolved}"
                            f"```",
                timestamp=get_timestamp()
            )

            listings_formatted = ", ".join(listings)

            if len(listings) == 0:
                listings_formatted = "None"

            embed.set_thumbnail(url=thumbnail_url)
            embed.add_field(
                name=f"Owned by {len(listings)} {pluralize('member', len(listings))}",
                value=f"{listings_formatted}"
            )
            await ctx.channel.send(embed=embed)

    @commands.command(aliases=["parade"])
    @commands.guild_only()
    @commands.cooldown(1, 60, commands.BucketType.user)
    @commands.check(check_if_user_has_parade_tickets)
    async def perform_parade(self, ctx):
        users.update_one({"user_id": str(ctx.author.id)}, {"$inc": {"parade_tickets": -1}})
        await logs_add_line("parade_tickets", -1, ctx.author.id)

        parade_pull = []
        for x in range(0, 49):
            roll = random.uniform(0, 100)

            if roll < 5:
                p = random.uniform(0, 1.2)
                if p >= 126 / 109:
                    parade_pull.append(random.choice(pool_sp))
                else:
                    parade_pull.append(random.choice(pool_ssr))
            elif roll <= 25:
                parade_pull.append(random.choice(pool_sr))
            else:
                parade_pull.append(random.choice(pool_r))

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
        max_rows = 7
        new_im = Image.new("RGBA", (max_rows * 90, max_rows * 90))

        def get_coordinates(c):
            a = (c * 90 - (ceil(c / max_rows) - 1) * max_rows * 90) - 90
            b = (ceil(c / max_rows) * 90) - 90
            return a, b

        for index, item in enumerate(images):
            new_im.paste(images[index], (get_coordinates(index + 1)))

        address = f"temp/{ctx.author.id}.png"
        new_im.save(address)
        new_photo = discord.File(address, filename=f"{ctx.message.id}.png")
        hosting_channel = self.client.get_channel(int(hosting_id))
        msg = await hosting_channel.send(file=new_photo)
        attachment_link = msg.attachments[0].url

        x_init, y_init = random.randint(0, max_rows), random.randint(0, max_rows)
        beaned_shikigamis = []
        beans = 10

        def generate_parade_embed(listings, remaining_chances):
            value = ", ".join([shiki.title() for shiki in listings])
            if len(value) == 0:
                value = "None"

            embed = discord.Embed(
                color=ctx.author.color,
                title="🎏 Demon Parade",
                description=f"Beans: 10\n"
                            f"Time Limit: 45 seconds, resets for every bean\n"
                            f"Note: Cannot bean the same shikigami twice",
                timestamp=get_timestamp()
            )
            embed.set_image(url=attachment_link)
            embed.add_field(name="Beaned Shikigamis", value=value)
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
                x_init, y_init = bean_x, bean_y
                beans -= 1

        await self.perform_parade_issue_shards(ctx.author, beaned_shikigamis, ctx, msg)

    async def perform_parade_issue_shards(self, user, beaned_shikigamis, ctx, msg):
        await msg.clear_reactions()
        self.client.get_command("perform_parade").reset_cooldown(ctx)
        for beaned_shikigami in beaned_shikigamis:

            query = users.find_one({
                "user_id": str(user.id),
                "shikigami.name": beaned_shikigami}, {
                "_id": 0, "shikigami.$": 1
            })

            if query is None:
                users.update_one({
                    "user_id": str(user.id)}, {
                    "$push": {
                        "shikigami": {
                            "name": beaned_shikigami,
                            "rarity": get_rarity_shikigami(beaned_shikigami),
                            "grade": 1,
                            "owned": 0,
                            "evolved": False,
                            "shards": 0
                        }
                    }
                })

            users.update_one({"user_id": str(ctx.author.id), "shikigami.name": beaned_shikigami}, {
                "$inc": {
                    "shikigami.$.shards": 1
                }
            })

    @commands.command(aliases=["pray"])
    @commands.guild_only()
    @commands.cooldown(1, 150, commands.BucketType.user)
    @commands.check(check_if_user_has_prayers)
    async def pray_use(self, ctx):

        embed = discord.Embed(
            title="Pray to the Goddess of Hope and Prosperity!",
            color=ctx.author.colour,
            description="45% chance to obtain rich rewards",
            timestamp=get_timestamp()
        )
        embed.set_footer(text=f"{ctx.author.display_name}", icon_url=ctx.author.avatar_url)
        msg = await ctx.channel.send(embed=embed)

        rewards_emoji = [e_j, e_f, e_a, e_c, e_t, e_m]
        rewards_selection = []

        for x in range(0, 3):
            emoji = random.choice(rewards_emoji)
            await msg.add_reaction(emoji.replace("<", "").replace(">", ""))
            rewards_emoji.remove(emoji)
            rewards_selection.append(emoji)

        def check(r, u):
            return str(r.emoji) in rewards_selection and u == ctx.author

        def get_rewards(y):
            rewards_amount = {e_j: 250, e_f: 50, e_a: 3, e_c: 450000, e_t: 1500, e_m: 150}
            rewards_text = {
                e_j: "jades",
                e_f: "friendship",
                e_a: "amulets",
                e_c: "coins",
                e_t: "talisman",
                e_m: "medals"
            }
            return rewards_amount[y], rewards_text[y]

        try:
            roll = random.randint(1, 100)
            reaction, user = await self.client.wait_for("reaction_add", timeout=150, check=check)

        except asyncio.TimeoutError:
            users.update_one({"user_id": str(ctx.author.id)}, {"$inc": {"prayers": -1}})
            await logs_add_line("prayers", -1, ctx.author.id)
            self.client.get_command("pray_use").reset_cooldown(ctx)

        else:
            users.update_one({"user_id": str(ctx.author.id)}, {"$inc": {"prayers": -1}})
            await logs_add_line("prayers", -1, ctx.author.id)

            if roll >= 55:
                embed = discord.Embed(
                    title=f"Prayer results", color=ctx.author.colour,
                    description=f"||{next(prayer_ignored)}||",
                    timestamp=get_timestamp()
                )
                embed.set_footer(text=f"{ctx.author.display_name}", icon_url=ctx.author.avatar_url)
                await msg.edit(embed=embed)
                self.client.get_command("pray_use").reset_cooldown(ctx)

            else:
                amount, rewards = get_rewards(str(reaction.emoji))
                embed = discord.Embed(
                    title=f"Prayer results", color=ctx.author.colour,
                    description=f"||{next(prayer_heard)} You obtained {amount:,d}{str(reaction.emoji)}||",
                    timestamp=get_timestamp()
                )
                embed.set_footer(text=f"{ctx.author.display_name}", icon_url=ctx.author.avatar_url)
                users.update_one({"user_id": str(ctx.author.id)}, {"$inc": {rewards: amount}})
                await logs_add_line(rewards, amount, user.id)
                await msg.edit(embed=embed)
                self.client.get_command("pray_use").reset_cooldown(ctx)

    async def frame_automate(self):

        spell_spam_channel = self.client.get_channel(int(spell_spam_id))
        guild = spell_spam_channel.guild

        await frame_starlight(guild, spell_spam_channel)
        await asyncio.sleep(1)
        await frame_blazing(guild, spell_spam_channel)

    @commands.command(aliases=["baa"])
    @commands.guild_only()
    async def bounty_add_alias(self, ctx, name, *, alias):

        name_formatted = name.replace("_", " ")

        bounties.update_one({"aliases": name.lower()}, {"$push": {"aliases": alias.lower()}})
        embed = discord.Embed(
            colour=discord.Colour(embed_color),
            title=f"Successfully added {alias} to {name_formatted.title()}",
            timestamp=get_timestamp()
        )
        await ctx.channel.send(embed=embed)

    @commands.command(aliases=["bal"])
    @commands.guild_only()
    async def bounty_add_location(self, ctx, name, *, location):

        bounties.update_one({"aliases": name.lower()}, {"$push": {"location": location}})
        embed = discord.Embed(
            colour=discord.Colour(embed_color),
            title=f"Successfully added new location to {name}",
            description=f"{location}",
            timestamp=get_timestamp()
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
                thumbnail = get_thumbnail_shikigami(query.lower(), "pre")
            except TypeError:
                thumbnail = ""

            name = bounty_search1["bounty"].title()
            description = ("• " + "\n• ".join(bounty_search1["location"]))
            aliases = bounty_search1["aliases"]
            text = ", ".join(aliases)

            embed = discord.Embed(
                color=ctx.author.colour,
                title=f"Bounty location for {name}:",
                description=description,
                timestamp=get_timestamp()
            )
            embed.set_footer(icon_url=thumbnail, text=f"aliases: {text}")
            await ctx.channel.send(embed=embed)

        elif bounty_search2 is not None:
            bounty_list = []
            for result in bounty_search2:
                bounty_list.append(result["bounty"])

            embed = discord.Embed(
                title="No exact results", colour=discord.Colour(embed_color),
                description="But here are the list of shikigamis that match the first two letters",
                timestamp=get_timestamp()
            )
            embed.add_field(name="Possible queries", value="*{}*".format(", ".join(bounty_list)))
            await ctx.channel.send(embed=embed)

    @commands.command(aliases=["daily"])
    @commands.guild_only()
    async def claim_rewards_daily(self, ctx):
        user = ctx.author
        profile = users.find_one({"user_id": str(user.id)}, {"_id": 0, "daily": 1})

        if profile["daily"] is False:
            await claim_rewards_daily_give(user, ctx)

        elif profile["daily"] is True:
            embed = discord.Embed(
                title="Collection Failed", colour=discord.Colour(embed_color),
                description=f"You have collected already today. Resets everyday at 00:00 EST",
                timestamp=get_timestamp()
            )
            embed.set_footer(icon_url=user.avatar_url, text=f"{user.display_name}")
            await ctx.channel.send(embed=embed)

    @commands.command(aliases=["weekly"])
    @commands.guild_only()
    async def claim_rewards_weekly(self, ctx):

        user = ctx.author
        profile = users.find_one({"user_id": str(user.id)}, {"_id": 0, "weekly": 1})

        if profile["weekly"] is False:
            await claim_rewards_weekly_give(user, ctx)

        elif profile["weekly"] is True:
            embed = discord.Embed(
                title="Collection Failed", colour=discord.Colour(embed_color),
                description=f"You have collected already this week. Resets every Mon at 00:00 EST",
                timestamp=get_timestamp()
            )
            embed.set_footer(icon_url=user.avatar_url, text=f"{user.display_name}")
            await ctx.channel.send(embed=embed)

    @commands.command(aliases=["profile", "p"])
    @commands.guild_only()
    async def profile_show(self, ctx, *, member: discord.Member = None):

        if member is None:
            await self.profile_post(ctx.author, ctx)

        else:
            await self.profile_post(member, ctx)

    async def profile_generate_frame_image(self, member, achievements):

        achievements_address = []
        for entry in achievements:
            try:
                achievements_address.append(f"data/achievements/{entry['name']}.png")
            except KeyError:
                continue

        images = list(map(Image.open, achievements_address))

        def get_image_variables(x):
            total_frames = len(x)
            w = 1000
            h = ceil(total_frames / 5) * 200
            return w, h

        width, height = get_image_variables(achievements_address)
        new_im = Image.new("RGBA", (width, height))

        def get_coordinates(c):
            x = (c * 200 - (ceil(c / 5) - 1) * 1000) - 200
            y = (ceil(c / 5) * 200) - 200
            return x, y

        for index, item in enumerate(images):
            new_im.paste(images[index], (get_coordinates(index + 1)))

        address = f"temp/{member.id}.png"
        new_im.save(address)
        new_photo = discord.File(address, filename=f"{member.id}.png")
        hosting_channel = self.client.get_channel(int(hosting_id))
        msg = await hosting_channel.send(file=new_photo)
        attachment_link = msg.attachments[0].url
        return attachment_link

    async def profile_post(self, member, ctx):

        profile = users.find_one({
            "user_id": str(member.id)}, {
            "_id": 0, "SP": 1, "SSR": 1, "SR": 1, "R": 1, "amulets": 1,
            "amulets_spent": 1, "experience": 1, "level": 1, "level_exp_next": 1,
            "jades": 1, "coins": 1, "medals": 1, "realm_ticket": 1, "display": 1, "friendship": 1,
            "encounter_ticket": 1, "friendship_pass": 1, "talisman": 1, "prayers": 1, "achievements": 1, "frame": 1,
            "achievements_count": 1, "parade_tickets": 1, "N": 1, "amulets_spent_b": 1, "amulets_b": 1
        })

        ships_count = ships.find({"code": {"$regex": f".*{ctx.author.id}.*"}}).count()
        amulets = profile["amulets"]
        amulets_b = profile["amulets_b"]
        amulets_spent = profile["amulets_spent"]
        amulets_spent_b = profile["amulets_spent_b"]
        exp = profile["experience"]
        level = profile["level"]
        level_exp_next = profile["level_exp_next"]
        jades = profile["jades"]
        coins = profile["coins"]
        medals = profile["medals"]
        realm_ticket = profile["realm_ticket"]
        display = profile["display"]
        friendship_points = profile["friendship"]
        enc_ticket = profile["encounter_ticket"]
        friendship_pass = profile["friendship_pass"]
        talismans = profile["talisman"]
        prayers = profile["prayers"]
        frame = profile["frame"]
        achievements_count = profile["achievements_count"]
        achievements = profile["achievements"]
        parade = profile["parade_tickets"]

        if len(achievements) != achievements_count:
            frame = await self.profile_generate_frame_image(member, achievements)
            users.update_one({"user_id": str(member.id)}, {
                "$set": {
                    "frame": frame, "achievements_count": len(achievements)
                }
            })

        embed = discord.Embed(color=member.colour, timestamp=get_timestamp())

        if display is not None:
            evo = users.find_one({
                "user_id": str(member.id), "shikigami.name": display}, {
                "shikigami.$.name": 1
            })["shikigami"][0]["evolved"]
            thumbnail = get_thumbnail_shikigami(display.lower(), get_evo_link(evo))
            embed.set_thumbnail(url=thumbnail)

        else:
            embed.set_thumbnail(url=member.avatar_url)

        embed.set_author(
            name=f"{member.display_name}'s profile",
            icon_url=member.avatar_url
        )
        embed.add_field(
            name="⤴ Experience",
            value=f"Level: {level} ({exp:,d}/{level_exp_next:,d})"
        )
        embed.add_field(
            name=f"{e_1} | {e_2} | {e_3} | {e_4} | {e_5}",
            value=f"{profile['SP']} | {profile['SSR']} | {profile['SR']} | {profile['R']:,d} | {profile['N']:,d}"
        )
        embed.add_field(
            name=f"{e_b} Amulets",
            value=f"On Hand: {amulets_b} | Used: {amulets_spent_b:,d}"
        )
        embed.add_field(
            name=f"{e_a} Amulets",
            value=f"On Hand: {amulets} | Used: {amulets_spent:,d}"
        )
        embed.add_field(
            name=f"💗 | 🎟 | 🎫 | 🚢 | 🙏 | 🎏",
            value=f"{friendship_pass} | {realm_ticket:,d} | {enc_ticket:,d} | {ships_count} | {prayers} | {parade}",
            inline=False
        )
        embed.add_field(
            name=f"{e_f} | {e_t} | {e_m} | {e_j} | {e_c}",
            value=f"{friendship_points:,d} | {talismans:,d} | {medals:,d} | {jades:,d} | {coins:,d}"
        )
        msg = await ctx.channel.send(embed=embed)
        await msg.add_reaction("🖼")

        def check(r, u):
            return str(r.emoji) == "🖼" and r.message.id == msg.id and u.bot is False

        try:
            await self.client.wait_for("reaction_add", timeout=30, check=check)
        except asyncio.TimeoutError:
            return
        else:
            embed = discord.Embed(color=member.colour, timestamp=get_timestamp())
            embed.set_author(
                name=f"{member.display_name}'s achievements",
                icon_url=member.avatar_url
            )
            embed.set_image(url=frame)
            embed.set_footer(text="Hall of Frames")
            await msg.edit(embed=embed)

    @commands.command(aliases=["display"])
    @commands.guild_only()
    async def profile_change_display(self, ctx, *, select):

        user = ctx.author
        select_formatted = select.lower()

        if select_formatted is None:
            users.update_one({"user_id": str(user.id)}, {"$set": {"display": select_formatted}})
            await ctx.message.add_reaction("✅")

        elif select_formatted not in pool_all_mystery:
            embed = discord.Embed(
                colour=discord.Colour(embed_color),
                title="Invalid shikigami name",
                timestamp=get_timestamp()
            )
            await ctx.channel.send(embed=embed)

        elif select_formatted in pool_all_mystery:
            count = users.count_documents({"user_id": str(user.id), "shikigami.name": select_formatted})

            if count != 1:
                embed = discord.Embed(
                    colour=discord.Colour(embed_color),
                    description=f"{user.mention}, you do not own that shikigami",
                    timestamp=get_timestamp()
                )
                await ctx.channel.send(embed=embed)

            elif count == 1:
                users.update_one({"user_id": str(user.id)}, {"$set": {"display": select_formatted}})
                await ctx.message.add_reaction("✅")

    @commands.command(aliases=["collections", "col"])
    @commands.guild_only()
    async def shikigami_image_show_collected(self, ctx, arg1, member: discord.Member = None):

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
            title=f"{get_rarity_emoji(rarity)} Collection",
            color=member.colour,
            timestamp=get_timestamp()
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

        def get_variables(r):
            dictionary = {
                "SP": [90 * 6, 6],
                "SSR": [90 * 8, 8],
                "SR": [90 * 10, 10],
                "R": [90 * 8, 8]
            }
            return dictionary[r]

        w = get_variables(rarity)[0]
        col = get_variables(rarity)[1]

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
        hosting_channel = self.client.get_channel(int(hosting_id))
        msg = await hosting_channel.send(file=new_photo)
        attachment_link = msg.attachments[0].url
        return attachment_link

    @commands.command(aliases=["shikigamis", "shikis"])
    @commands.guild_only()
    async def shikigami_list_show_collected(self, ctx, arg1, member: discord.Member = None):

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

    @commands.command(aliases=["uncollected", "unc"])
    @commands.guild_only()
    async def shikigami_list_show_uncollected(self, ctx, arg1, member: discord.Member = None):

        rarity = str(arg1.upper())

        if rarity not in rarities:
            return

        elif member is None:
            await self.shikigami_list_post_uncollected(ctx.author, rarity, ctx)

        else:
            await self.shikigami_list_post_uncollected(member, rarity, ctx)

    async def shikigami_list_post_uncollected(self, member, rarity, ctx):

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
                "shikigami.shards": 1
            }}, {
            "$match": {
                "shikigami.owned": {
                    "$gt": 0
                }}}
        ]):
            user_shikigamis.append((
                entry["shikigami"]["name"]
            ))

        pool_rarity_select = []
        for entry in shikigamis.find({"rarity": rarity}, {"_id": 0, "name": 1}):
            pool_rarity_select.append(entry["name"])

        uncollected_list = list(set(pool_rarity_select) - set(user_shikigamis))

        formatted_list = []
        for shiki in uncollected_list:
            formatted_list.append(f"• {shiki.title()}\n")

        await self.shikigami_list_paginate(member, formatted_list, rarity, ctx, "Uncollected")

    async def shikigami_list_paginate(self, member, formatted_list, rarity, ctx, title):

        page = 1
        max_lines = 10
        page_total = ceil(len(formatted_list) / max_lines)
        if page_total == 0:
            page_total = 1

        def create_new_embed_page(page_new):
            end = page_new * max_lines
            start = end - max_lines
            embed_new = discord.Embed(color=member.colour, timestamp=get_timestamp())
            embed_new.title = f"{get_rarity_emoji(rarity.upper())} {title}"
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
    @commands.check(check_if_developer_team)
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
    @commands.check(check_if_developer_team)
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
                title="evolve, evo", colour=discord.Colour(embed_color),
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
            await shikigami_post_approximate_results(ctx, query)

        elif profile_my_shikigami == {}:
            embed = discord.Embed(
                title="Invalid shikigami", colour=discord.Colour(embed_color),
                description=f"{user.mention}, I did not find that shikigami nor you have it",
                timestamp=get_timestamp()
            )
            await ctx.channel.send(embed=embed)

        elif profile_my_shikigami != {}:
            rarity = profile_my_shikigami["shikigami"][0]["rarity"]
            count = profile_my_shikigami["shikigami"][0]["owned"]
            evo = profile_my_shikigami["shikigami"][0]["evolved"]
            await perform_evolution_shikigami(ctx, rarity, evo, user, query, count)

    @commands.command(aliases=["shrine"])
    @commands.guild_only()
    async def shrine_shikigami(self, ctx, arg1="", *, args=""):

        user = ctx.author
        shiki = args.lower()

        def get_talisman_required(x):
            dictionary = {"SSR": 350000, "SR": 150000, "R": 50000}
            return dictionary[x]

        if arg1.lower() not in ["sacrifice", "exchange", "s", "exc"]:
            raise commands.MissingRequiredArgument(ctx.author)

        elif arg1.lower() in ["sacrifice", "s"] and len(args) == 0:
            embed = discord.Embed(
                title="shrine sacrifice, shrine s", colour=discord.Colour(embed_color),
                description="sacrifice your shikigamis to the shrine in exchange for talismans"
            )
            embed.add_field(
                name="Rarity :: Talisman",
                value="```"
                      "SP     ::  15,000\n"
                      "SSR    ::  10,000\n"
                      "SR     ::     250\n"
                      "R      ::      50\n"
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
                title="shrine exchange, shrine exc", colour=discord.Colour(embed_color),
                description="exchange your talismans for exclusive shikigamis"
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
            embed = discord.Embed(
                title="Invalid shikigami name", colour=discord.Colour(embed_color),
                description=f"use *`{self.prefix}shikis`* to get the list of your shikigamis",
                timestamp=get_timestamp()
            )
            await ctx.channel.send(embed=embed)

        elif arg1.lower() in ["exchange", "exc"] and shiki not in pool_shrine:
            embed = discord.Embed(
                title="Invalid shikigami name", colour=discord.Colour(embed_color),
                description=f"use *`{self.prefix}shrine`* to check the list of valid shikigamis",
                timestamp=get_timestamp()
            )
            await ctx.channel.send(embed=embed)

        elif arg1.lower() in ["sacrifice", "s"] and shiki in pool_all_mystery:

            request = users.find_one({
                "user_id": str(user.id), "shikigami.name": shiki}, {
                "_id": 0, "shikigami.$.name": 1
            })
            count_shikigami = request["shikigami"][0]["owned"]
            rarity = request["shikigami"][0]["rarity"]
            talismans = get_talisman_acquire(rarity)

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
                    timestamp=get_timestamp()
                )
                embed.set_thumbnail(url=get_thumbnail_shikigami(shiki, "evo"))
                embed.set_footer(text=f"{user.display_name}", icon_url=user.avatar_url)
                msg = await ctx.channel.send(embed=embed)
                answer = await self.client.wait_for("message", timeout=15, check=check)

            except asyncio.TimeoutError:
                embed = discord.Embed(
                    title="Invalid amount", colour=user.colour,
                    description=f"That is not a valid number",
                    timestamp=get_timestamp()
                )
                embed.set_thumbnail(url=get_thumbnail_shikigami(shiki, "evo"))
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
                    await logs_add_line("talisman", final_talismans, user.id)
                    embed = discord.Embed(
                        title="Shrine successful", colour=user.colour,
                        description=f"You shrined your {shiki.title()} for {final_talismans:,d}{e_t}",
                        timestamp=get_timestamp()
                    )
                    embed.set_thumbnail(url=get_thumbnail_shikigami(shiki, "evo"))
                    embed.set_footer(text=f"{user.display_name}", icon_url=user.avatar_url)
                    await msg.edit(embed=embed)

                else:
                    embed = discord.Embed(
                        title="Insufficient shikigamis", colour=user.colour,
                        description=f"You do not have that amount of shikigamis",
                        timestamp=get_timestamp()
                    )
                    embed.set_thumbnail(url=get_thumbnail_shikigami(shiki, "evo"))
                    embed.set_footer(text=f"{user.display_name}", icon_url=user.avatar_url)
                    await ctx.channel.send(embed=embed)

        elif arg1.lower() in ["exchange", "exc"] and shiki in pool_shrine:

            rarity = shikigamis.find_one({"name": shiki}, {"_id": 0, "rarity": 1})["rarity"]
            talisman = users.find_one({"user_id": str(user.id)}, {"_id": 0, "talisman": 1})["talisman"]
            required_talisman = get_talisman_required(rarity)

            if talisman >= required_talisman:
                embed = discord.Embed(
                    title="Exchange confirmation", colour=discord.Colour(embed_color),
                    description=f"{user.mention}, confirm exchange of {required_talisman:,d}{e_t} for a {shiki.title()}",
                    timestamp=get_timestamp()
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
                        title="Timeout!", colour=discord.Colour(embed_color),
                        description=f"{ctx.author.mention}, you did not confirm the {e_t} exchange",
                        timestamp=get_timestamp()
                    )
                    embed.set_footer(icon_url=user.avatar_url, text=f"{user.display_name}")
                    await ctx.channel.send(embed=embed)
                else:
                    query = users.find_one({
                        "user_id": str(user.id),
                        "shikigami.name": shiki}, {
                        "_id": 0, "shikigami.$": 1
                    })

                    if query is None:
                        users.update_one({
                            "user_id": str(user.id)}, {
                            "$push": {
                                "shikigami": {
                                    "name": shiki,
                                    "rarity": rarity,
                                    "grade": 1,
                                    "owned": 0,
                                    "evolved": False,
                                    "shards": 0
                                }
                            }
                        })

                    users.update_one({
                        "user_id": str(user.id),
                        "shikigami.name": shiki}, {
                        "$inc": {
                            "shikigami.$.owned": 1,
                            "talisman": - required_talisman,
                            f"{rarity}": 1
                        }
                    })
                    await logs_add_line("talisman", - required_talisman, user.id)
                    embed = discord.Embed(
                        title="Exchange success!", colour=discord.Colour(embed_color),
                        description=f"{ctx.author.mention}, acquired {shiki.title()} for {required_talisman:,d}{e_t}",
                        timestamp=get_timestamp()
                    )
                    await ctx.channel.send(embed=embed)

            elif talisman < required_talisman:
                embed = discord.Embed(
                    title="Insufficient talismans", colour=discord.Colour(embed_color),
                    description=f"{user.mention}, shrine shikigamis to obtain more. "
                                f"Lacks {required_talisman - talisman:,d}{e_t}",
                    timestamp=get_timestamp()
                )
                embed.set_footer(icon_url=user.avatar_url, text=f"{user.display_name}")
                await ctx.channel.send(embed=embed)

    async def friendship_check_levelup(self, ctx, code, giver):
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

    async def friendship_post_ship(self, code, query1, ctx):

        ship_profile = ships.find_one({
            "code": code}, {
            "_id": 0, "shipper1": 1, "shipper2": 1, "points": 1, "level": 1, "ship_name": 1, "points_required": 1
        })

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

        embed = discord.Embed(color=query1.colour, description=description, timestamp=get_timestamp())
        embed.set_author(
            name=f"{ship_profile['ship_name']}",
            icon_url=self.client.get_user(int(ship_profile["shipper1"])).avatar_url
        )
        embed.set_thumbnail(url=self.client.get_user(int(ship_profile['shipper2'])).avatar_url)
        await ctx.channel.send(embed=embed)

    @commands.command(aliases=["sail"])
    @commands.guild_only()
    async def friendship_check_sail(self, ctx):

        request = ships.find({"level": {"$gt": 1}, "code": {"$regex": f".*{ctx.author.id}.*"}})
        ships_count = request.count()
        total_rewards = 0

        for ship in request:
            total_rewards += ship["level"] * 25

        embed = discord.Embed(
            color=ctx.author.colour,
            description=f"Total daily ship sail rewards: {total_rewards:,d}{e_j}",
            timestamp=get_timestamp()
        )
        embed.set_footer(
            text=f"{ships_count} {pluralize('ship', ships_count)}",
            icon_url=ctx.author.avatar_url
        )
        await ctx.channel.send(embed=embed)

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
                title=f"🚢 {member.display_name}'s ships [{total_ships} {pluralize('ship', total_ships)}]",
                timestamp=get_timestamp()
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
    async def friendship_ship(self, ctx, query1: discord.Member = None, query2: discord.Member = None):

        try:
            if query1 is None and query2 is None:
                embed = discord.Embed(
                    title="ship, ships", colour=discord.Colour(embed_color),
                    description=f"shows a ship profile or your own ships\n"
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
                code = get_bond(ctx.author, query1)
                await self.friendship_post_ship(code, query1, ctx)

            elif query1 is not None and query2 is not None:
                code = get_bond(query1, query2)
                await self.friendship_post_ship(code, query1, ctx)

        except TypeError:
            embed = discord.Embed(
                colour=discord.Colour(embed_color),
                title="Invalid ship",
                description=f"{ctx.author.mention}, I'm sorry, but that ship has sunk before it was built."
            )
            await ctx.channel.send(embed=embed)

    @commands.command(aliases=["friendship", "fp"])
    @commands.guild_only()
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def friendship_give(self, ctx, *, receiver: discord.Member = None):

        giver = ctx.author
        profile = users.find_one({"user_id": str(giver.id)}, {"_id": 0, "friendship_pass": 1})

        if receiver is None:
            embed = discord.Embed(
                title="friendship, fp", colour=discord.Colour(embed_color),
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

        elif profile["friendship_pass"] < 1:
            embed = discord.Embed(
                colour=discord.Colour(embed_color),
                title="Insufficient friendship passes",
                description=f"{giver.mention}, you have used up all your friendship passes"
            )
            await ctx.channel.send(embed=embed)

        elif profile["friendship_pass"] > 0:
            code = get_bond(giver, receiver)
            users.update_one({
                "user_id": str(giver.id)}, {
                "$inc": {
                    "friendship_pass": -1
                }
            })
            await logs_add_line("friendship_pass", -1, giver)

            if ships.find_one({"code": code}, {"_id": 0}) is None:
                profile = {
                    "code": code,
                    "shipper1": str(ctx.author.id),
                    "shipper2": str(receiver.id),
                    "ship_name": f"{giver.name} and {receiver.name}'s ship",
                    "level": 1,
                    "points": 0,
                    "points_required": 50
                }
                ships.insert_one(profile)

            ships.update_one({"code": code}, {"$inc": {"points": 5}})
            users.update_one({"user_id": str(giver.id)}, {"$inc": {"friendship": 5}})
            await logs_add_line("friendship", 5, giver)
            await ctx.message.add_reaction(f"{e_f.replace('<', '').replace('>', '')}")

            def check(r, u):
                return u.id == receiver.id and str(r.emoji) == e_f and r.message.id == ctx.message.id

            try:
                await self.client.wait_for("reaction_add", timeout=120, check=check)
            except asyncio.TimeoutError:
                await self.friendship_check_levelup(ctx, code, giver)
                await ctx.message.clear_reactions()
            else:
                ships.update_one({"code": code, "level": {"$lt": 5}}, {"$inc": {"points": 3}})
                await self.friendship_check_levelup(ctx, code, giver)
                users.update_one({"user_id": str(receiver.id)}, {"$inc": {"friendship": 3}})
                await logs_add_line("friendship", 3, receiver)
                await ctx.message.clear_reactions()
                await ctx.message.add_reaction("✅")

    @commands.command(aliases=["fpchange", "fpc"])
    @commands.guild_only()
    async def friendship_change_name(self, ctx, receiver: discord.Member = None, *, new_name=None):

        embed = discord.Embed(
            title="fpchange, fpc", colour=discord.Colour(embed_color),
            description="changes your ship name with the mentioned member"
        )
        embed.add_field(name="Format", value=f"*• `{self.prefix}fpc <@member> <ship name>`*")

        if new_name is None:
            await ctx.channel.send(embed=embed)

        try:
            code = get_bond(ctx.author, receiver)
            ships.update_one({"code": code}, {"$set": {"ship_name": new_name}})
            await self.friendship_post_ship(code, ctx.author, ctx)

        except AttributeError:
            await ctx.channel.send(embed=embed)

    @commands.command(aliases=["shop"])
    @commands.guild_only()
    async def shop_show_items(self, ctx):

        embed = discord.Embed(
            title="Mystic Trader", colour=discord.Colour(embed_color),
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
            return
        else:
            try:
                url = self.client.get_user(518416258312699906).avatar_url
            except AttributeError:
                url = ""

            embed = discord.Embed(
                title="AkiraKL's Frame Shop", colour=discord.Colour(embed_color),
                description="purchase premium frames for premium prices"
            )
            embed.set_thumbnail(url=url)
            for frame in frames.find({"purchase": True}, {"_id": 0, "currency": 1, "amount": 1, "name": 1, "emoji": 1}):
                embed.add_field(
                    name=f"{frame['emoji']} {frame['name']}",
                    value=f"Acquire for {frame['amount']:,d}{emojify(frame['currency'])}",
                    inline=False
                )
            embed.add_field(name=f"Format", value=f"*`{self.prefix}buy frame <frame_name>`*", inline=False)
            await msg.edit(embed=embed)

    @commands.command(aliases=["buy"])
    @commands.guild_only()
    async def shop_buy_items(self, ctx, *args):

        user = ctx.author

        if len(args) == 0:
            embed = discord.Embed(
                title="buy", colour=discord.Colour(embed_color),
                description=f"purchase from the list of items from the *`{self.prefix}shop`*\n"
                            f"react to confirm purchase")
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

            embed = discord.Embed(title="Confirm purchase?", color=ctx.author.colour, timestamp=get_timestamp())
            embed.description = f"{emoji} {frame.title()} frame for `{amount:,d}` {emojify(currency)}"
            embed.add_field(
                name="Inventory",
                value=f"`{cost_item_have:,d}` {emojify(currency)}"
            )
            embed.set_thumbnail(url=url)
            embed.set_footer(icon_url=user.avatar_url, text=user.display_name)

            msg = await ctx.channel.send(embed=embed)
            await msg.add_reaction("✅")
            answer = await self.shop_buy_confirmation(ctx, msg)

            if answer is True:
                await shop_process_purchase_frame(ctx, user, currency, amount, frame.title(), emoji)

        else:
            try:
                offer_item, offer_amount, cost_item, cost_amount = get_offer_and_cost(args)
                cost_item_have = users.find_one({"user_id": str(user.id)}, {"_id": 0, cost_item: 1})[cost_item]
                offer_item_have = users.find_one({"user_id": str(user.id)}, {"_id": 0, offer_item: 1})[offer_item]

                embed = discord.Embed(title="Confirm purchase?", colour=user.colour, timestamp=get_timestamp())
                embed.set_footer(icon_url=user.avatar_url, text=user.display_name)
                embed.description = \
                    f"`{offer_amount}` {emojify(offer_item)} `for` `{cost_amount:,d}` {emojify(cost_item)}\n\n"
                embed.add_field(
                    name="Inventory",
                    value=f"`{offer_item_have:,d}` {emojify(offer_item)} | `{cost_item_have:,d}` {emojify(cost_item)}"
                )
                embed.set_thumbnail(url="https://vignette.wikia.nocookie.net/onmyoji/images/8/86/246a.jpg")

                msg = await ctx.channel.send(embed=embed)
                await msg.add_reaction("✅")
                answer = await self.shop_buy_confirmation(ctx, msg)

                if answer is True:
                    await shop_process_purchase(user, ctx, offer_item, offer_amount, cost_item, cost_amount, msg)

            except KeyError:
                embed = discord.Embed(
                    title="Invalid purchase code", colour=discord.Colour(embed_color),
                    description=f"{user.mention}, you entered an invalid purchase code",
                    timestamp=get_timestamp()
                )
                embed.set_footer(icon_url=user.avatar_url, text=user.display_name)
                await ctx.channel.send(embed=embed)

            except IndexError:
                embed = discord.Embed(
                    title="Invalid purchase code", colour=discord.Colour(embed_color),
                    description=f"{user.mention}, you entered an invalid purchase code",
                    timestamp=get_timestamp()
                )
                embed.set_footer(icon_url=user.avatar_url, text=user.display_name)
                await ctx.channel.send(embed=embed)

    async def shop_buy_confirmation(self, ctx, msg):

        def check(r, u):
            return u == ctx.author and str(r.emoji) == "✅" and msg.id == r.message.id

        try:
            await self.client.wait_for("reaction_add", timeout=10.0, check=check)
        except asyncio.TimeoutError:
            embed = discord.Embed(
                title="Timeout!", colour=discord.Colour(embed_color),
                description=f"You did not confirm the purchase",
                timestamp=get_timestamp()
            )
            embed.set_footer(text=f"{ctx.author.display_name}", icon_url=ctx.author.avatar_url)
            embed.set_thumbnail(url="https://vignette.wikia.nocookie.net/onmyoji/images/8/86/246a.jpg")
            await msg.edit(embed=embed)
            await msg.clear_reactions()
            return False
        else:
            return True

    @commands.command(aliases=["summon", "s"])
    @commands.guild_only()
    @commands.cooldown(1, 180, commands.BucketType.user)
    async def summon_mystery_perform(self, ctx, *, args=None):

        user = ctx.author

        try:
            amulet_pull = int(args)
            amulet_have = users.find_one({"user_id": str(user.id)}, {"_id": 0, "amulets": 1})["amulets"]

            if amulet_have == 0:
                embed = discord.Embed(
                    title="Insufficient amulets", colour=discord.Colour(embed_color),
                    description="Exchange at the shop to obtain more",
                    timestamp=get_timestamp()
                )
                await ctx.channel.send(embed=embed)

            elif args not in ["1", "10"]:
                raise commands.MissingRequiredArgument(ctx.author)

            elif amulet_have > 0:

                if amulet_pull > amulet_have:
                    embed = discord.Embed(
                        title="Insufficient amulets", colour=discord.Colour(embed_color),
                        description=f"{user.mention}, you only have {amulet_have}{e_a} in your possession",
                        timestamp=get_timestamp()
                    )
                    await ctx.channel.send(embed=embed)

                elif amulet_pull == 10 and amulet_have >= 10:
                    await summon_mystery_perform(ctx, user, amulet_pull)

                elif amulet_pull == 1 and amulet_have >= 1:
                    await summon_mystery_perform(ctx, user, amulet_pull)

        except TypeError:
            raise commands.MissingRequiredArgument(ctx.author)

        except ValueError:
            shikigami_summon = args.lower()

            if shikigami_summon in pool_all_mystery:
                await summon_mystery_perform_shards(ctx, shikigami_summon, user)

            else:
                embed = discord.Embed(
                    title="Invalid shikigami name", colour=discord.Colour(embed_color),
                    description=f"Check the spelling via *`{self.prefix}unc`*",
                    timestamp=get_timestamp()
                )
                await ctx.channel.send(embed=embed)

        self.client.get_command("summon_mystery_perform").reset_cooldown(ctx)

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
            await self.leaderboard_post_record_users(ctx, query, "⤴ Level LeaderBoard", "level")

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
            formatted_list.append(f"🔸{ship[0]}, x{ship[1]}{e_f}\n")

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
                timestamp=get_timestamp()
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

        try:
            if member is None:
                await self.logs_show_member(ctx, ctx.author)

            elif member is not None:
                await self.logs_show_member(ctx, member)

        except TypeError:
            pass

    async def logs_show_member(self, ctx, member):

        profile = logs.find_one({"user_id": str(member.id)}, {"_id": 0, "logs": 1})
        formatted_list = []

        for entry in profile["logs"][:200]:
            operator = "+"
            if entry['amount'] < 0:
                operator = ""
            emoji = emojify(entry['currency'])
            formatted_list.append(
                f"`[{entry['date'].strftime('%d.%b %H:%M')}]` | `{operator}{entry['amount']:,d}`{emoji}\n"
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
    async def shikigami_show_post_shards(self, ctx, arg1, member: discord.Member = None):

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
            title=f"{get_rarity_emoji(rarity)} Collection - Shards",
            color=member.colour,
            timestamp=get_timestamp()
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


        def get_variables(r):
            dictionary = {
                "SP": [90 * 6, 6],
                "SSR": [90 * 8, 8],
                "SR": [90 * 10, 10],
                "R": [90 * 8, 8]
            }
            return dictionary[r]

        w = get_variables(rarity)[0]
        col = get_variables(rarity)[1]

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
        hosting_channel = self.client.get_channel(int(hosting_id))
        msg = await hosting_channel.send(file=new_photo)
        attachment_link = msg.attachments[0].url
        return attachment_link


def setup(client):
    client.add_cog(Economy(client))
