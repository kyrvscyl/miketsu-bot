"""
Economy Module
Miketsu, 2019
"""

import asyncio
import json
import random
from datetime import datetime
from math import ceil

import discord
import pytz
from PIL import Image
from discord.ext import commands

from cogs.frames import Frames
from cogs.mongo.database import get_collections
from cogs.startup import \
    e_m, e_j, e_c, e_f, e_a, e_sp, e_ssr, e_sr, e_r, e_t, pluralize, guild_id, embed_color, hosting_id

# Collections
guilds = get_collections("guilds")
bounties = get_collections("bounties")
shikigamis = get_collections("shikigamis")
users = get_collections("users")
ships = get_collections("ships")
streaks = get_collections("streaks")
frames = get_collections("frames")
bosses = get_collections("bosses")

# Listings
pool_sp = []
pool_ssr = []
pool_sr = []
pool_r = []
pool_shrinable = []
pool_all = []

trading_list = []
spell_spams_id = []
purchasable_frames = []
trading_list_formatted = []

rarities = ["SP", "SSR", "SR", "R"]
adverb = ["deliberately", "forcefully", "unknowingly", "accidentally", "dishonestly"]
verb = ["snatched", "stole", "took", "looted", "shoplifted", "embezzled"]
noun = ["custody", "care", "control", "ownership"]
comment = ["Sneaky!", "Gruesome!", "Madness!"]

developer_team = guilds.find_one({"server": str(guild_id)}, {"_id": 0, "developers": 1})["developers"]

caption = open("lists/summon.lists")
summon_caption = caption.read().splitlines()
caption.close()

for document in frames.find({"purchase": True}, {"_id": 1, "name": 1}):
    purchasable_frames.append(document["name"].lower())


for shikigami in shikigamis.find({}, {"_id": 0, "name": 1, "rarity": 1, "shrine": 1}):
    if shikigami["shrine"] is True:
        pool_shrinable.append(shikigami["name"])
    elif shikigami["rarity"] == "SP":
        pool_sp.append(shikigami["name"])
    elif shikigami["rarity"] == "SSR":
        pool_ssr.append(shikigami["name"])
    elif shikigami["rarity"] == "SR":
        pool_sr.append(shikigami["name"])
    elif shikigami["rarity"] == "R":
        pool_r.append(shikigami["name"])


for document in guilds.find({}, {"_id": 0, "channels.spell-spam": 1}):
    try:
        spell_spams_id.append(document["channels"]["spell-spam"])
    except KeyError:
        continue

pool_all.extend(pool_sp)
pool_all.extend(pool_ssr)
pool_all.extend(pool_sr)
pool_all.extend(pool_r)
pool_all.extend(pool_shrinable)


def check_if_developer_team(ctx):
    return str(ctx.author.id) in developer_team


def check_if_user_has_prayers(ctx):
    return users.find_one({"user_id": str(ctx.author.id)}, {"_id": 0, "prayers": 1})["prayers"] > 0


def check_if_user_has_parade_tickets(ctx):
    return users.find_one({"user_id": str(ctx.author.id)}, {"_id": 0, "parade_tickets": 1})["parade_tickets"] > 0


def get_frame_thumbnail(frame):
    request = frames.find_one({"name": frame}, {"_id": 0, "link": 1})
    return request["link"]


def get_time():
    return datetime.now(tz=pytz.timezone("America/Atikokan"))


def get_timestamp():
    return datetime.utcfromtimestamp(datetime.timestamp(datetime.now()))


def get_bond(x, y):
    bond_list = sorted([x.id, y.id], reverse=True)
    return f"{bond_list[0]}x{bond_list[1]}"


def get_emoji(item):
    emoji_dict = {
        "jades": e_j, "coins": e_c, "realm_ticket": "🎟", "amulets": e_a, "medals": e_m, "friendship": e_f,
        "encounter_ticket": "🎫", "talisman": e_t
    }
    return emoji_dict[item]


def get_offer_and_cost(x):
    with open("data/shop.json") as g:
        shop = json.load(g)

    _shop = shop[x[0]][x[1]]
    offer_item_ = _shop["offer"][0]
    offer_amount_ = _shop["offer"][1]
    cost_item_ = _shop["cost"][0]
    cost_amount_ = _shop["cost"][1]

    return offer_item_, offer_amount_, cost_item_, cost_amount_


with open("data/shop.json") as f:
    shop_dict = json.load(f)

for offer in shop_dict:
    for _amount in shop_dict[offer]:
        trading_list.append([
            shop_dict[offer][_amount]["offer"][0],
            shop_dict[offer][_amount]["offer"][1],
            shop_dict[offer][_amount]["cost"][0],
            shop_dict[offer][_amount]["cost"][1],
            offer,
            _amount
        ])


for trade in trading_list:
    trading_list_formatted.append(
        f"▫ `{trade[1]}`{get_emoji(trade[0])} for `{trade[3]:,d}`{get_emoji(trade[2])} | {trade[4]} {trade[5]}\n"
    )


def get_shard_requirement(shiki):
    rarity = shikigamis.find_one({"name": shiki.lower()}, {"_id": 0, "rarity": 1})["rarity"]
    dictionary = {
        "SP": 15, "SSR": 12, "SR": 9, "R": 6
    }
    return dictionary[rarity], rarity


def get_evo_link(evolution):
    key = {True: "evo", False: "pre"}
    return key[evolution]


def get_rarity_emoji(rarity):
    dictionary = {
        "SP": e_sp,
        "SSR": e_ssr,
        "SR": e_sr,
        "R": e_r
    }
    return dictionary[rarity]


def get_rarity_shikigami(shiki):
    profile = shikigamis.find_one({"name": shiki}, {"_id": 0, "rarity": 1})
    return profile["rarity"]


def get_requirement(r):
    key = {"R": 21, "SR": 11, "SSR": 2, "SP": 0}
    return key[r]


def get_talisman_acquire(rarity):
    dictionary = {"R": 50, "SR": 250, "SSR": 10000, "SP": 15000}
    return dictionary[rarity]


def get_thumbnail_shikigami(shiki, evolution):
    profile = shikigamis.find_one({"name": shiki.lower()}, {"_id": 0, "thumbnail": 1})
    return profile["thumbnail"][evolution]


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
    embed = discord.Embed(
        color=user.colour,
        title="Frame Acquisition",
        description=f"{user.mention}, you acquired the {frame_name} frame and {jades:,d}{e_j}"
    )
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
    embed = discord.Embed(
        color=ctx.author.colour,
        title="🎁 Daily Rewards",
        description=f"A box containing {friendship_pass} 💗, {jades}{e_j}, {coins:,d}{e_c}, {realm_ticket} 🎟, "
                    f"{encounter_ticket} 🎫, {parade_tickets} 🎏"
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

    embed = discord.Embed(
        color=ctx.author.colour,
        title="💝 Weekly Rewards",
        description=f"A mythical box containing {jades}{e_j}, {coins:,d}{e_c}, and {amulets}{e_a}"
    )
    embed.set_footer(text=f"Opened by {user.display_name}", icon_url=user.avatar_url)
    await ctx.channel.send(embed=embed)


async def perform_evolution_shikigami(ctx, rarity, evo, user, query, count):
    if rarity == "SP":
        embed = discord.Embed(
            colour=discord.Colour(embed_color),
            description=f"{user.mention}, SP shikigamis are already evolved"
        )
        await ctx.channel.send(embed=embed)

    elif evo is True:
        embed = discord.Embed(
            colour=discord.Colour(embed_color),
            description=f"{user.mention}, your {query.title()} is already evolved."
        )
        await ctx.channel.send(embed=embed)

    elif evo is False:
        rarity_count = get_requirement(rarity)

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
                            f"Acquired 5 shards of this shikigami!"
            )
            embed.set_thumbnail(url=image_url)
            await ctx.channel.send(embed=embed)

            if query == "orochi":
                await frame_acquisition(user, "Sword Swallowing-Snake", ctx.channel, jades=2500)

        elif count == 0:
            embed = discord.Embed(
                colour=discord.Colour(embed_color),
                description=f"{user.mention}, you do not own that shikigami"
            )
            await ctx.channel.send(embed=embed)

        elif count <= (get_requirement(rarity) - 1):
            required = rarity_count - count
            noun_duplicate = pluralize('dupe', required)
            embed = discord.Embed(
                colour=discord.Colour(embed_color),
                title="Insufficient shikigamis",
                description=f"{user.mention}, you lack {required} more {query.title()} {noun_duplicate} to evolve yours"
            )
            await ctx.channel.send(embed=embed)


async def perform_parade_issue_shards(user, beaned_shikigamis, ctx, msg):

    await msg.clear_reactions()
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
            description=description
        )
        embed.set_thumbnail(url="https://vignette.wikia.nocookie.net/onmyoji/images/1/17/Frame7.png")
        await spell_spam_channel.send(embed=embed)
        await frame_acquisition(starlight_new, "Starlight Sky", spell_spam_channel, jades=2500)

    if starlight_current == starlight_new:
        users.update_one({"user_id": str(starlight_current.id)}, {"$inc": {"jades": 2000}})
        msg = f"{starlight_current.mention} has earned 2,000{e_j} " \
              f"for wielding the Starlight Sky frame for a day!"
        await spell_spam_channel.send(msg)

    else:
        await starlight_new.add_roles(starlight_role)
        await asyncio.sleep(3)
        await starlight_current.remove_roles(starlight_role)
        await asyncio.sleep(3)

        description = \
            f"{starlight_new.mention} {random.choice(adverb)} {random.choice(verb)} " \
            f"the Rare Starlight Sky Frame from {starlight_current.mention}\"s " \
            f"{random.choice(noun)}!! {random.choice(comment)}\n\n" \
            f"🍀 No SSR streak record as of posting: {streak_list_new[0][1]} summons!"

        embed = discord.Embed(
            color=0xac330f,
            title="📨 Hall of Framers Update",
            description=description
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
            description=description
        )
        embed.set_thumbnail(url="https://vignette.wikia.nocookie.net/onmyoji/images/7/72/Frame62.png")
        await spell_spam_channel.send(embed=embed)
        await frame_acquisition(blazing_new, "Blazing Sun", spell_spam_channel, jades=2500)

    if blazing_current == blazing_new:
        users.update_one({"user_id": str(blazing_current.id)}, {"$inc": {"amulets": 10}})
        msg = f"{blazing_current.mention} has earned 10{e_a} for wielding the Blazing Sun frame for a day!"
        await spell_spam_channel.send(msg)

    else:
        await blazing_new.add_roles(blazing_role)
        await asyncio.sleep(3)
        await blazing_current.remove_roles(blazing_role)
        await asyncio.sleep(3)

        description = f"{blazing_new.mention} {random.choice(adverb)} {random.choice(verb)} " \
                      f"the Rare Blazing Sun Frame from {blazing_current.mention}\"s {random.choice(noun)}!! " \
                      f"{random.choice(comment)}\n\n" \
                      f"🍀 Distinct SSRs under possession: {ssr_list_new[0][1]} shikigamis"

        embed = discord.Embed(
            color=0xffff80,
            title="📨 Hall of Framers Update",
            description=description
        )
        embed.set_thumbnail(url="https://vignette.wikia.nocookie.net/onmyoji/images/7/72/Frame62.png")
        await spell_spam_channel.send(embed=embed)
        await frame_acquisition(blazing_new, "Blazing Sun", spell_spam_channel, jades=2500)


async def shop_process_purchase(user, ctx, offer_item, offer_amount, cost_item, cost_amount):

    if users.find_one({"user_id": str(user.id)}, {"_id": 0, cost_item: 1})[cost_item] >= int(cost_amount):
        users.update_one({
            "user_id": str(user.id)}, {
            "$inc": {
                offer_item: int(offer_amount),
                cost_item: -int(cost_amount)
            }
        })
        embed = discord.Embed(
            title="Confirmation receipt", colour=discord.Colour(embed_color),
            description=f"{user.mention} acquired {offer_amount:,d}{get_emoji(offer_item)} "
                        f"in exchanged for {cost_amount:,d}{get_emoji(cost_item)}"
        )
        await ctx.channel.send(embed=embed)

    else:
        embed = discord.Embed(
            title="Purchase failure", colour=discord.Colour(embed_color),
            description=f"{user.mention}, you have insufficient {get_emoji(cost_item)}"
        )
        await ctx.channel.send(embed=embed)


async def shop_process_purchase_frame(ctx, user, currency, amount, frame_name, emoji):

    if users.find_one({"user_id": str(user.id)}, {"_id": 0, currency: 1})[currency] >= amount:
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
        embed = discord.Embed(
            title="Confirmation receipt", colour=discord.Colour(embed_color),
            description=f"{user.mention} acquired {emoji} {frame_name} "
                        f"in exchanged for {amount:,d}{get_emoji(currency)}",
            timestamp=get_timestamp()
        )
        await ctx.channel.send(embed=embed)

    else:
        embed = discord.Embed(
            title="Purchase failure", colour=discord.Colour(embed_color),
            description=f"{user.mention}, you have insufficient {get_emoji(currency)}"
        )
        await ctx.channel.send(embed=embed)


async def summon_update(user, sum_sp, sum_ssr, sum_sr, sum_r, amulet_pull, summon_pull):
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


async def summon_streak(user, summon_pull):
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


async def summon_perform(ctx, user, amulet_pull):
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

    embed = discord.Embed(color=user.colour, title="🎊 Results", description=description)

    if amulet_pull == 10:
        embed.set_footer(text=f"{f_sp}; {f_ssr}; {f_sr}; {f_r}")

    elif amulet_pull == 1:
        shikigami_pulled = summon_pull[0][1].replace("||", "")
        embed.set_thumbnail(url=get_thumbnail_shikigami(shikigami_pulled, "pre"))

    msg = "{}".format(random.choice(summon_caption)).format(user.mention)
    await ctx.channel.send(msg, embed=embed)
    await summon_update(user, sum_sp, sum_ssr, sum_sr, sum_r, amulet_pull, summon_pull)
    await summon_streak(user, summon_pull)


async def summon_perform_shards(ctx, shiki, user):
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
                description=f"{user.mention}, you summon the {rarity} shikigami {shiki}!"
            )
            embed.set_thumbnail(url=get_thumbnail_shikigami(shiki, "pre"))
            await ctx.channel.send(embed=embed)

        else:
            embed = discord.Embed(
                title="Summon failed", colour=discord.Colour(embed_color),
                description=f"{user.mention}, you lack {required_shards - shards} {shiki} shards"
            )
            await ctx.channel.send(embed=embed)

    except TypeError:
        embed = discord.Embed(
            title="Summon failed", colour=discord.Colour(embed_color),
            description=f"{user.mention}, you do not have any shards of {shiki}"
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
            "parade_tickets": 0
        }
        users.insert_one(profile)


class Economy(commands.Cog):

    def __init__(self, client):
        self.client = client

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
            embed.add_field(name="Example", value="*`;wish inferno ibaraki`*")
            await ctx.channel.send(embed=embed)

        elif profile["wish"] is False:
            embed = discord.Embed(
                color=user.colour,
                description=f"{user.mention}, your wish has been fulfilled already today",
            )
            await ctx.channel.send(embed=embed)

        elif profile["wish"] is not True:
            embed = discord.Embed(
                color=user.colour,
                description=f"{user.mention}, you have wished already today",
            )
            await ctx.channel.send(embed=embed)

        elif profile["wish"] is True and shiki.lower() not in pool_all:
            embed = discord.Embed(
                color=user.colour,
                description=f"{user.mention}, you provided an invalid shikigami name"
            )
            await ctx.channel.send(embed=embed)

        elif profile["wish"] is True and shiki.lower() in pool_all:

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
                description=f"fulfill a wish from a member in *`;wishlist`*\nno confirmation prompt for fulfilling",
            )
            embed.add_field(name="Format", value="*`;ff <@member>`*")
            await ctx.channel.send(embed=embed)
            return

        try:
            shikigami_wished_for = users.find_one({"user_id": str(member.id)}, {"_id": 0, "wish": 1})["wish"]

        except KeyError:
            embed = discord.Embed(
                title="Invalid member", colour=discord.Colour(embed_color),
                description="That member doesn't exist nor has a profile in this guild"
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
            )
            await ctx.channel.send(embed=embed)

        elif shikigami_wished_for is False:
            embed = discord.Embed(
                color=user.colour,
                title=f"Wish fulfillment failed",
                description=f"{user.mention}, that user has their wish fulfilled already"
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
                )
                await ctx.channel.send(embed=embed)

            elif profile["shikigami"][0]["shards"] == 0:
                embed = discord.Embed(
                    color=user.colour,
                    title=f"Insufficient shards",
                    description=f"{user.mention}, you do not have any shards of that shikigami",
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

        embed1 = discord.Embed(
            title="🎁 Daily rewards have been reset", colour=discord.Colour(embed_color),
            description="Claim yours using `;daily`"
        )
        embed2 = discord.Embed(
            title="🛳 Daily ship sail rewards have been issued", colour=discord.Colour(0xf8f4b1),
            description="Check your income using `;sail`"
        )

        for channel in spell_spams_id:
            current_channel = self.client.get_channel(int(channel))
            try:
                await current_channel.send(embed=embed1)
                await current_channel.send(embed=embed2)
            except AttributeError:
                continue
            except discord.errors.Forbidden:
                continue

    async def reset_rewards_weekly(self):

        users.update_many({}, {"$set": {"weekly": False}})

        embed = discord.Embed(
            title="💝 Weekly rewards have been perform_reset", colour=discord.Colour(embed_color),
            description="Claim yours using `;weekly`"
        )
        for channel in spell_spams_id:
            current_channel = self.client.get_channel(int(channel))
            await current_channel.send(embed=embed)

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

        elif name.lower() not in pool_all:
            embed = discord.Embed(
                title="Invalid shikigami name",
                colour=discord.Colour(embed_color),
                description="Try again"
            )
            await ctx.channel.send(embed=embed)

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
    @commands.check(check_if_user_has_parade_tickets)
    async def perform_parade(self, ctx):
        users.update_one({"user_id": str(ctx.author.id)}, {"$inc": {"parade_tickets": -1}})

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
        hosting_channel = self.client.get_channel(hosting_id)
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
                            f"Note: Cannot bean the same shikigami twice"
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

        await perform_parade_issue_shards(ctx.author, beaned_shikigamis, ctx, msg)

    @commands.command(aliases=["pray"])
    @commands.guild_only()
    @commands.check(check_if_user_has_prayers)
    async def pray_use(self, ctx):

        embed = discord.Embed(
            title="Pray to the Goddess of Hope and Prosperity!",
            color=ctx.author.colour,
            description="45% chance to obtain rich rewards"
        )
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
            dictionary1 = {e_j: 250, e_f: 50, e_a: 3, e_c: 450000, e_t: 1500, e_m: 150}
            dictionary2 = {
                e_j: "jades",
                e_f: "friendship",
                e_a: "amulets",
                e_c: "coins",
                e_t: "talisman",
                e_m: "medals"
            }
            return dictionary1[y], dictionary2[y]

        try:
            roll = random.randint(1, 100)
            reaction, user = await self.client.wait_for("reaction_add", timeout=150, check=check)
        except asyncio.TimeoutError:
            return

        else:
            users.update_one({"user_id": str(ctx.author.id)}, {"$inc": {"prayers": -1}})

            if roll >= 55:
                embed = discord.Embed(
                    title=f"Results", color=ctx.author.colour,
                    description=f"||Sometimes, you have to pray harder to be heard||"
                )
                await ctx.channel.send(embed=embed)

            else:
                amount, rewards = get_rewards(str(reaction.emoji))
                embed = discord.Embed(
                    title=f"Results", color=ctx.author.colour,
                    description=f"||Your prayer has been heard, you obtained {amount:,d}{str(reaction.emoji)}||"
                )
                users.update_one({"user_id": str(ctx.author.id)}, {"$inc": {rewards: amount}})
                await ctx.channel.send(embed=embed)
                return

    @commands.command(aliases=["fm"])
    @commands.check(check_if_developer_team)
    async def frame_manual(self, ctx):

        await self.frame_automate()
        await ctx.message.delete()

    async def frame_automate(self):

        request = guilds.find_one({"server": str(guild_id)}, {"_id": 0, "channels": 1})
        spell_spam_id = request["channels"]["spell-spam"]
        spell_spam_channel = self.client.get_channel(int(spell_spam_id))
        guild = spell_spam_channel.guild

        await frame_starlight(guild, spell_spam_channel)
        await asyncio.sleep(1)
        await frame_blazing(guild, spell_spam_channel)

    @commands.command(aliases=["add"])
    @commands.check(check_if_developer_team)
    async def bounty_add_alias(self, ctx, *args):

        name = args[0].replace("_", " ").lower()
        alias = " ".join(args[1::]).replace("_", " ").lower()
        bounties.update_one({"aliases": name}, {"$push": {"aliases": alias}})
        embed = discord.Embed(
            colour=discord.Colour(embed_color),
            title=f"Successfully added {alias} to {name}"
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
                description=description
            )
            embed.set_footer(icon_url=thumbnail, text=f"aliases: {text}")
            await ctx.channel.send(embed=embed)

        elif bounty_search2 is not None:
            bounty_list = []
            for result in bounty_search2:
                bounty_list.append(result["bounty"])

            embed = discord.Embed(
                title="No exact results", colour=discord.Colour(embed_color),
                description="But here are the list of shikigamis that match the first two letters"
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
                title="You have collected already today", colour=discord.Colour(embed_color),
                description="Resets everyday at 00:00 EST")
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
                title="You have collected already this week", colour=discord.Colour(embed_color),
                description="Resets every Monday at 00:00 EST"
            )
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
        hosting_channel = self.client.get_channel(hosting_id)
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
            "achievements_count": 1, "parade_tickets": 1
        })

        ships_count = ships.find({"code": {"$regex": f".*{ctx.author.id}.*"}}).count()
        amulets = profile["amulets"]
        amulets_spent = profile["amulets_spent"]
        exp = profile["experience"]
        level = profile["level"]
        level_exp_next = profile["level_exp_next"]
        jades = profile["jades"]
        coins = profile["coins"]
        medals = profile["medals"]
        realm_ticket = profile["realm_ticket"]
        display = profile["display"]
        friendship_points = profile["friendship"]
        encounter_ticket = profile["encounter_ticket"]
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

        embed = discord.Embed(color=member.colour)

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
            name=":arrow_heading_up: Experience",
            value=f"Level: {level} ({exp:,d}/{level_exp_next:,d})"
        )
        embed.add_field(
            name=f"{e_sp} | {e_ssr} | {e_sr} | {e_r}",
            value=f"{profile['SP']} | {profile['SSR']} | {profile['SR']} | {profile['R']:,d}"
        )
        embed.add_field(
            name=f"{e_a} Amulets",
            value=f"On Hand: {amulets} | Used: {amulets_spent:,d}"
        )
        embed.add_field(
            name=f"💗 | 🎟 | 🎫 | 🚢 | 🙏 ",
            value=f"{friendship_pass} | {realm_ticket:,d} | {encounter_ticket:,d} | {ships_count} | {prayers}"
        )
        embed.add_field(
            name=f"🎏 | {e_f} | {e_t} | {e_m} | {e_j} | {e_c}",
            value=f"{parade} | {friendship_points:,d} | {talismans:,d} | {medals:,d} | {jades:,d} | {coins:,d}"
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

        elif select_formatted not in pool_all:
            embed = discord.Embed(
                colour=discord.Colour(embed_color),
                title="Invalid shikigami name"
            )
            await ctx.channel.send(embed=embed)

        elif select_formatted in pool_all:
            count = users.count_documents({"user_id": str(user.id), "shikigami.name": select_formatted})

            if count != 1:
                embed = discord.Embed(
                    colour=discord.Colour(embed_color),
                    description=f"{user.mention}, you do not own that shikigami"
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

    async def shikigami_show_post_collected_generate(
            self, user_shikis, user_uncollected, pool_rarity_select, rarity, member
    ):

        images = []
        for entry in user_shikis:
            address = f"data/shikigamis/{entry[0]}_pre.jpg"
            if entry[1] is True:
                address = f"data/shikigamis/{entry[0]}_evo.jpg"
            images.append(Image.open(address))

        for entry in user_uncollected:
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
        hosting_channel = self.client.get_channel(hosting_id)
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

        await self.shikigami_list_paginate(member, formatted_list, rarity, ctx, "Owned")

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

    @commands.command(aliases=["addshiki"])
    @commands.check(check_if_developer_team)
    async def shikigami_add(self, ctx, *args):

        if len(args) < 5:
            return

        elif len(args) == 5:

            rarity = args[0].upper()
            name = (args[1].replace("_", " ")).lower()
            shrine = False

            if args[2] == "shrine":
                shrine = True

            profile = {
                "name": name,
                "rarity": rarity,
                "shrine": shrine,
                "thumbnail": {
                    "pre": args[3],
                    "evo": args[4]
                }
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
                description="perform evolution of owned shikigami")
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
            embed.add_field(name="Format", value="*`;evolve <shikigami>`*")
            await ctx.channel.send(embed=embed)

        elif profile_my_shikigami == {}:
            embed = discord.Embed(
                title="Invalid shikigami", colour=discord.Colour(embed_color),
                description=f"{user.mention}, I did not find that shikigami nor you have it"
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
        name = args.lower().lower()

        def get_talisman_required(x):
            dictionary = {
                "SSR": 1500000,
                "SR": 500000,
                "R": 50000
            }
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
                value="*`;shrine s <shikigami>`*"
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
                      "Mannendake    ::    500,000\n"
                      "Jinmenju      ::    500,000\n"
                      "Kainin        ::    500,000\n"
                      "Ryomen        ::  1,500,000"
                      "```",
                inline=False
            )
            embed.add_field(
                name="Formats",
                value="*`;shrine exc <shikigami>`*"
            )
            await ctx.channel.send(embed=embed)

        elif arg1.lower() in ["sacrifice", "s"] and name not in pool_all:
            embed = discord.Embed(
                title="Invalid shikigami name", colour=discord.Colour(embed_color),
                description="use *`;shikis`* to get the list of your shikigamis"
            )
            await ctx.channel.send(embed=embed)

        elif arg1.lower() in ["exchange", "exc"] and name not in pool_shrinable:
            embed = discord.Embed(
                title="Invalid shikigami name", colour=discord.Colour(embed_color),
                description="use *`;shrine`* to check the list of valid shikigamis"
            )
            await ctx.channel.send(embed=embed)

        elif arg1.lower() in ["sacrifice", "s"] and name in pool_all:

            request = users.find_one({
                "user_id": str(user.id), "shikigami.name": name}, {
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
                    title=f"Specify amount of {name.title()} to sacrifice",
                    description=f"{user.mention}, you currently have {count_shikigami:,d} of that shikigami"
                )
                await ctx.channel.send(embed=embed)
                answer = await self.client.wait_for("message", timeout=15, check=check)

            except asyncio.TimeoutError:
                embed = discord.Embed(
                    title="Invalid amount", colour=user.colour,
                    description=f"{user.mention}, that is not a valid number"
                )
                await ctx.channel.send(embed=embed)

            else:
                request_shrine = int(answer.content)
                if count_shikigami >= request_shrine:
                    final_talismans = talismans * request_shrine
                    users.update_one({
                        "user_id": str(user.id),
                        "shikigami.name": name}, {
                        "$inc": {
                            "shikigami.$.owned": - request_shrine,
                            "talisman": final_talismans,
                            f"{rarity}": - request_shrine
                        }
                    })
                    embed = discord.Embed(
                        title="Confirmation sacrifice", colour=user.colour,
                        description=f"{user.mention}, you sacrificed your {name.title()} for {final_talismans:,d}{e_t}"
                    )
                    await ctx.channel.send(embed=embed)

                else:
                    embed = discord.Embed(
                        title="Insufficient shikigamis", colour=user.colour,
                        description=f"{user.mention}, you do not have that amount of shikigamis"
                    )
                    await ctx.channel.send(embed=embed)

        elif arg1.lower() in ["exchange", "exc"] and name in pool_shrinable:

            rarity = shikigamis.find_one({"name": name}, {"_id": 0, "rarity": 1})["rarity"]
            talisman = users.find_one({"user_id": str(user.id)}, {"_id": 0, "talisman": 1})["talisman"]
            required_talisman = get_talisman_required(rarity)

            if talisman >= required_talisman:
                embed = discord.Embed(
                    title="Exchange confirmation", colour=discord.Colour(embed_color),
                    description=f"{user.mention}, confirm exchange of {required_talisman:,d}{e_t} for a {name.title()}"
                )
                confirm_ = await ctx.channel.send(embed=embed)
                await confirm_.add_reaction("✅")

                def check(r, u):
                    return u == ctx.author and str(r.emoji) == "✅"

                try:
                    await self.client.wait_for("reaction_add", timeout=10.0, check=check)
                except asyncio.TimeoutError:
                    embed = discord.Embed(
                        title="Timeout!", colour=discord.Colour(embed_color),
                        description=f"{ctx.author.mention}, you did not confirm the {e_t} exchange"
                    )
                    await ctx.channel.send(embed=embed)
                else:
                    query = users.find_one({
                        "user_id": str(user.id),
                        "shikigami.name": name}, {
                        "_id": 0, "shikigami.$": 1
                    })

                    if query is None:
                        users.update_one({
                            "user_id": str(user.id)}, {
                            "$push": {
                                "shikigami": {
                                    "name": name,
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
                        "shikigami.name": name}, {
                        "$inc": {
                            "shikigami.$.owned": 1,
                            "talisman": - required_talisman,
                            f"{rarity}": 1
                        }
                    })
                    embed = discord.Embed(
                        title="Exchange success!", colour=discord.Colour(embed_color),
                        description=f"{ctx.author.mention}, acquired {name.title()} for {required_talisman:,d}{e_t}"
                    )
                    await ctx.channel.send(embed=embed)

            elif talisman < required_talisman:
                embed = discord.Embed(
                    title="Insufficient talisman", colour=discord.Colour(embed_color),
                    description=f"{user.mention}, shrine shikigamis to obtain more. "
                                f"Lacks {required_talisman - talisman:,d}{e_t}"
                )
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

        embed = discord.Embed(color=query1.colour, description=description)
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
            description=f"Total daily ship sail rewards: {total_rewards:,d}{e_j}"
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
                    description="shows a ship profile or your own ships\nto change your ship's name use *`;fpchange`*"
                )
                embed.add_field(
                    name="Formats",
                    value="*• `;ship <@member>`*\n"
                          "*• `;ship <@member> <@member>`*\n"
                          "*• `;ships`*"
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
                description="sends and receives friendship & builds ship that earns daily reward\n"
                            "built ships are shown using *`;ship`*"
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
            embed.add_field(name="Format", value="*`;friendship <@member>`*", inline=False)
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
                await ctx.message.clear_reactions()
                await ctx.message.add_reaction("✅")

    @commands.command(aliases=["fpchange", "fpc"])
    @commands.guild_only()
    async def friendship_change_name(self, ctx, receiver: discord.Member = None, *, new_name=None):

        embed = discord.Embed(
            title="fpchange, fpc", colour=discord.Colour(embed_color),
            description="changes your ship name with the mentioned member"
        )
        embed.add_field(name="Format", value="*• `;fpc <@member> <ship name>`*")

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
        embed.add_field(name="Example", value="*`;buy amulets 11`*", inline=False)

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
                    value=f"Acquire for {frame['amount']:,d}{get_emoji(frame['currency'])}",
                    inline=False
                )
            embed.add_field(name=f"Format", value="*`;buy frame <frame_name>`*", inline=False)
            await msg.edit(embed=embed)

    @commands.command(aliases=["buy"])
    @commands.guild_only()
    async def shop_buy_items(self, ctx, *args):

        user = ctx.author
        embed = discord.Embed(title="confirm purchase?", color=ctx.author.colour)

        if len(args) == 0:
            embed = discord.Embed(
                title="buy", colour=discord.Colour(embed_color),
                description="purchase from the list of items from the *`;shop`*\nreact to confirm purchase")
            embed.add_field(name="Format", value="*`;buy <purchase code>`*\n*`;buy frame <frame_name>`*")
            await ctx.channel.send(embed=embed)

        elif args[0].lower() in ["frame"] and len(args) > 1 and " ".join(args[1::]).lower() in purchasable_frames:

            frame = " ".join(args[1::]).lower()
            request = frames.find_one({"name": frame.title()}, {"_id": 0})
            emoji, currency, amount = request["emoji"], request["currency"], request["amount"]
            embed.description = f"{emoji} {frame.title()} frame for `{amount:,d}` {get_emoji(currency)}"

            msg = await ctx.channel.send(embed=embed)
            await msg.add_reaction("✅")
            answer = await self.shop_buy_confirmation(ctx, msg)

            if answer is True:
                await shop_process_purchase_frame(ctx, user, currency, amount, frame.title(), emoji)

        else:
            try:
                offer_item, offer_amount, cost_item, cost_amount = get_offer_and_cost(args)
                embed = discord.Embed(title="Confirm purchase?", colour=user.colour)
                embed.description = \
                    f"`{offer_amount}` {get_emoji(offer_item)} `for` `{cost_amount:,d}` {get_emoji(cost_item)}"

                msg = await ctx.channel.send(embed=embed)
                await msg.add_reaction("✅")
                answer = await self.shop_buy_confirmation(ctx, msg)

                if answer is True:
                    await shop_process_purchase(user, ctx, offer_item, offer_amount, cost_item, cost_amount)

            except KeyError:
                embed = discord.Embed(
                    title="Invalid purchase code", colour=discord.Colour(embed_color),
                    description=f"{user.mention}, you entered an invalid purchase code"
                )
                await ctx.channel.send(embed=embed)

            except IndexError:
                embed = discord.Embed(
                    title="Invalid purchase code", colour=discord.Colour(embed_color),
                    description=f"{user.mention}, you entered an invalid purchase code"
                )
                await ctx.channel.send(embed=embed)

    async def shop_buy_confirmation(self, ctx, msg):

        def check(r, u):
            return u == ctx.author and str(r.emoji) == "✅" and msg.id == r.message.id

        try:
            await self.client.wait_for("reaction_add", timeout=10.0, check=check)
        except asyncio.TimeoutError:
            embed = discord.Embed(
                title="Timeout!", colour=discord.Colour(embed_color),
                description=f"{ctx.author.mention}, you did not confirm the purchase"
            )
            await ctx.channel.send(embed=embed)
            return False
        else:
            return True

    @commands.command(aliases=["summon", "s"])
    @commands.guild_only()
    @commands.cooldown(1, 180, commands.BucketType.user)
    async def summon_perform(self, ctx, *, args=None):

        user = ctx.author

        try:
            amulet_pull = int(args)
            amulet_have = users.find_one({"user_id": str(user.id)}, {"_id": 0, "amulets": 1})["amulets"]

            if amulet_have == 0:
                embed = discord.Embed(
                    title="Insufficient amulets", colour=discord.Colour(embed_color),
                    description="Exchange at the shop to obtain more"
                )
                await ctx.channel.send(embed=embed)

            elif args not in ["1", "10"]:
                raise commands.MissingRequiredArgument(ctx.author)

            elif amulet_have > 0:

                if amulet_pull > amulet_have:
                    embed = discord.Embed(
                        title="Insufficient amulets", colour=discord.Colour(embed_color),
                        description=f"{user.mention}, you only have {amulet_have}{e_a} in your possession"
                    )
                    await ctx.channel.send(embed=embed)

                elif amulet_pull == 10 and amulet_have >= 10:
                    await summon_perform(ctx, user, amulet_pull)

                elif amulet_pull == 1 and amulet_have >= 1:
                    await summon_perform(ctx, user, amulet_pull)

        except TypeError:
            raise commands.MissingRequiredArgument(ctx.author)

        except ValueError:
            shikigami_summon = args.lower()

            if shikigami_summon in pool_all:
                await summon_perform_shards(ctx, shikigami_summon, user)

            else:
                embed = discord.Embed(
                    title="Invalid shikigami name", colour=discord.Colour(embed_color),
                    description="Check the spelling via *`;unc`*"
                )
                await ctx.channel.send(embed=embed)

        self.client.get_command("summon_perform").reset_cooldown(ctx)


def setup(client):
    client.add_cog(Economy(client))
