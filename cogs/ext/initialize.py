""""
Initialize Module
Miketsu, 2020
"""

import asyncio
import os
import random
from collections import Counter
from datetime import datetime
from math import ceil, exp

import discord
import pushbullet
import pytz
from PIL import ImageDraw
from PIL import ImageFont
from discord_webhook import DiscordEmbed, DiscordWebhook

from cogs.ext.database import get_collections

"""SETUP"""

version = "2.0.beta"
command_prefix = ";"
time_start = datetime.now()


"""COLLECTIONS"""

books = get_collections("books")
bosses = get_collections("bosses")
bounties = get_collections("bounties")
changelogs = get_collections("changelogs")
config = get_collections("config")

duelists = get_collections("duelists")
events = get_collections("events")
explores = get_collections("explores")
frames = get_collections("frames")
guilds = get_collections("guilds")

hints = get_collections("hints")
logs = get_collections("logs")
members = get_collections("members")
memos = get_collections("memos")
owls = get_collections("owls")
patronus = get_collections("patronus")
portraits = get_collections("portraits")
quests = get_collections("quests")

realms = get_collections("realms")
reminders = get_collections("reminders")
sendoffs = get_collections("sendoffs")
shikigamis = get_collections("shikigamis")

ships = get_collections("ships")
shoots = get_collections("shoots")
sortings = get_collections("sortings")
souls = get_collections("souls")
stickers = get_collections("stickers")
streaks = get_collections("streaks")

thieves = get_collections("thieves")
users = get_collections("users")
weather = get_collections("weathers")
weathers = get_collections("weathers")
zones = get_collections("zones")


"""CONFIGURATION"""

token = os.environ.get("TOKEN")
id_guild = int(os.environ.get("SERVER"))

dictionaries = config.find_one({"dict": 1}, {"_id": 0})
variables = config.find_one({"var": 1}, {"_id": 0})
listings_1 = config.find_one({"list": 1}, {"_id": 0})
listings_3 = config.find_one({"list": 3}, {"_id": 0})

server = guilds.find_one({"server": str(id_guild)}, {"_id": 0})


"""VARIABLES"""

timezone = variables["timezone"]
colour = variables["embed_color"]
librarian_img = variables["librarian_img"]


"""LISTINGS"""

invalid_channels = listings_1["invalid_channels"]

cogs_loaded = []
admin_roles = listings_1["admin_roles"]
clock_emojis = listings_1["clock_emojis"]

commands_fake = [
    "daily", "weekly", "profile", "set", "buy", "summon", "explore", "explores", "chapter", "card", "realms",
    "rcollect", "evolve", "friendship", "ships", "leaderboard", "shikigami", "shikigamis", "shrine", "sail",
    "pray", "stat", "frames", "wish", "wishlist", "fulfill", "parade", "collections", "shards", "cards",
    "raid", "raidc", "encounter", "netherworld", "bossinfo", "ship", "fpchange", "bento", "raidable",
    "souls [beta]", "equip"
]

commands_others = [
    "changelogs", "bounty", "suggest", "stickers", "newsticker", "wander", "portrait", "clear"
    "stats", "duel\\*\\*", "memo\\*", "manage\\*", "events\\*", "info", "report", "patch", "dm"
]


"""DICTIONARIES"""

emojis = dictionaries["emojis"]
shard_requirement = dictionaries["shard_requirement"]
emoji_dict = dictionaries["get_emojis"]
evo_requirement = dictionaries["evo_requirement"]
mystic_shop = dictionaries["mystic_shop"]
talisman_acquire = dictionaries["talisman_acquire"]
cards_realm = dictionaries["cards_realm"]
get_emojis = dictionaries["get_emojis"]


"""CHANNELS"""

id_hosting = server["channels"]["bot-sparring"]
id_sorting = server["channels"]["sorting-hat"]
id_spell_spam = server["channels"]["spell-spam"]
id_clock = server["channels"]["clock"]
id_headlines = server["channels"]["headlines"]
id_scroll = server["channels"]["scroll-of-everything"]
id_castle = int(server["categories"]["castle"])
id_duelling_room = server["channels"]["duelling-room"]
id_reference = server["channels"]["reference-section"]
id_restricted = server["channels"]["restricted-section"]
id_auror_dept = server["channels"]["auror-department"]
id_office = server["channels"]["headmasters-office"]
id_shard_trading = server["channels"]["shard-trading"]
id_welcome = server["channels"]["welcome"]
id_absence_app = server["channels"]["absence-applications"]
id_common_room = server["channels"]["the-common-room"]
id_diagon_alley = server["categories"]["diagon-alley"]
id_headmaster = server["headmaster"]
id_portrait = server["channels"]["portrait"]

"""ROLES"""

id_boss_busters = server["roles"]["boss_busters"]
id_silver_sickles = server["roles"]["silver_sickles"]
id_shard_seeker = server["roles"]["shard_seekers"]
id_golden_galleons = server["roles"]["golden_galleons"]
id_seers = server["roles"]["seers"]
id_patronus = server["roles"]["patronus"]
id_sushchefs = server["roles"]["sushchefs"]

"""EMOJIS"""

e_1 = emojis["1"]
e_2 = emojis["2"]
e_3 = emojis["3"]
e_4 = emojis["4"]
e_5 = emojis["5"]
e_6 = emojis["6"]
e_a = emojis["a"]
e_b = emojis["b"]
e_c = emojis["c"]
e_e = emojis["e"]
e_f = emojis["f"]
e_j = emojis["j"]
e_m = emojis["m"]
e_p = emojis["p"]
e_r = emojis["r"]
e_s = emojis["s"]
e_t = emojis["t"]
e_x = emojis["x"]

e_fp = emojis["fp"]


"""SUMMON POOL"""

rarities = listings_1["rarities"]

pool_sp = []
pool_ssr = []
pool_sr = []
pool_r = []
pool_n = []
pool_ssn = []

pool_others = []
pool_shrine = []

pool_all = []
pool_all_mystery = []
pool_all_broken = []

trading_list = []

trading_list_formatted = []

for shikigami in shikigamis.find({}, {"_id": 0, "name": 1, "rarity": 1, "shrine": 1, "amulet": 1}):
    if shikigami["shrine"] is True:
        pool_shrine.append(shikigami["name"])
    elif shikigami["amulet"] == "parade":
        pool_others.append(shikigami["name"])
    elif shikigami["rarity"] == "SP":
        pool_sp.append(shikigami["name"])
    elif shikigami["rarity"] == "SSR":
        pool_ssr.append(shikigami["name"])
    elif shikigami["rarity"] == "SR":
        pool_sr.append(shikigami["name"])
    elif shikigami["rarity"] == "R":
        pool_r.append(shikigami["name"])
    elif shikigami["rarity"] == "N":
        pool_n.append(shikigami["name"])
    elif shikigami["rarity"] == "SSN":
        pool_ssn.append(shikigami["name"])

pool_all_mystery.extend(pool_sp)
pool_all_mystery.extend(pool_ssr)
pool_all_mystery.extend(pool_sr)
pool_all_mystery.extend(pool_r)
pool_all_mystery.extend(pool_shrine)
pool_all_broken.extend(pool_n)
pool_all_broken.extend(pool_ssn)
pool_all.extend(pool_all_mystery)
pool_all.extend(pool_all_broken)
pool_all.extend(pool_others)

rarity_dict = {"SP": pool_sp, "SSR": pool_ssr, "SR": pool_sr, "R": pool_r, "N": pool_n, "SSN": pool_ssn}

"""REALMS"""

realm_cards = []
listings_cards = []

for card in realms.find({}, {"_id": 0}):
    realm_cards.append(f"{card['name'].lower()}")
    listings_cards.append([card["name"], card["rewards"], card["base"], card['link']["6"]])


"""SOULS"""

souls_all = []
soul_dungeons = [f"{x}" for x in list(range(1, 11))]

for soul in souls.find({}, {"_id": 0, "name": 1}):
    souls_all.append(soul["name"])


"""SHOP"""

seller_img = variables["seller_img"]
shop_frames = []

for doc in frames.find({"purchase": True}, {"_id": 1, "name": 1}):
    shop_frames.append(doc["name"].lower())

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
        f"▫ `{trade[1]}`{emoji_dict[trade[0]]} → `{trade[3]:,d}`{emoji_dict[trade[2]]} | "
        f"{trade[4]} {trade[5]}\n"
    )


"""FUNCTIONS"""


def get_offer_and_cost(seq):
    return mystic_shop[seq[0]][seq[1]]["offer"][0], mystic_shop[seq[0]][seq[1]]["offer"][1], \
           mystic_shop[seq[0]][seq[1]]["cost"][0], mystic_shop[seq[0]][seq[1]]["cost"][1]


def lengthen_code_3(index):
    prefix = "#{}"
    if index < 10:
        prefix = "#00{}"
    elif index < 100:
        prefix = "#0{}"
    return prefix.format(index)


def lengthen_code_2(x):
    prefix = "#{}"
    if x < 10:
        prefix = "0{}"
    elif x < 100:
        prefix = "{}"
    return prefix.format(x)


def lengthen_code_4(index):
    prefix = "{}"
    if index < 10:
        prefix = "000{}"
    elif index < 100:
        prefix = "00{}"
    elif index < 1000:
        prefix = "0{}"
    return prefix.format(index)


def font_create(size):
    return ImageFont.truetype('data/marker_felt_wide.ttf', size)


def check_if_valid_and_castle(ctx):
    return ctx.channel.category.id == id_castle and str(ctx.channel.name) not in invalid_channels


def check_if_user_has_any_admin_roles(ctx):
    for role in reversed(ctx.author.roles):
        if role.name in config.find_one({"list": 1}, {"_id": 0})["admin_roles"]:
            return True
    return False


def check_if_user_has_any_alt_roles(user):
    for role in reversed(user.roles):
        if role.name in ["Geminio"]:
            return True
    return False


def check_if_user_has_friendship_passes(ctx):
    return users.find_one({"user_id": str(ctx.author.id)}, {"_id": 0, "friendship_pass": 1})["friendship_pass"] > 0


def check_if_user_has_encounter_tickets(ctx):
    return users.find_one({"user_id": str(ctx.author.id)}, {"_id": 0, "encounter_ticket": 1})["encounter_ticket"] > 0


def check_if_user_has_raid_tickets(ctx):
    return users.find_one({"user_id": str(ctx.author.id)}, {"_id": 0, "realm_ticket": 1})["realm_ticket"] > 0


def check_if_user_has_nether_pass(ctx):
    return users.find_one({"user_id": str(ctx.author.id)}, {"_id": 0, "nether_pass": 1})["nether_pass"] is True


def check_if_user_has_prayers(ctx):
    return users.find_one({"user_id": str(ctx.author.id)}, {"_id": 0, "prayers": 1})["prayers"] > 0


def check_if_user_has_development_role(ctx):
    return str(ctx.author.id) in guilds.find_one({"server": str(id_guild)}, {"_id": 0, "developers": 1})["developers"]


def check_if_user_has_parade_tickets(ctx):
    return users.find_one({"user_id": str(ctx.author.id)}, {"_id": 0, "parade_tickets": 1})["parade_tickets"] > 0


def check_if_user_has_shiki_set(ctx):
    return users.find_one({"user_id": str(ctx.author.id)}, {"_id": 0, "display": 1})["display"] is not None


def check_if_user_has_sushi_1(ctx):
    return users.find_one({"user_id": str(ctx.author.id)}, {"_id": 0, "sushi": 1})["sushi"] > 0


def check_if_user_has_sushi_2(ctx, required):
    return users.find_one({"user_id": str(ctx.author.id)}, {"_id": 0, "sushi": 1})["sushi"] >= required


def check_if_channel_is_pvp(ctx):
    return ctx.channel.id == id_duelling_room


def check_if_restricted_section(ctx):
    return ctx.channel.id == id_restricted


def check_if_reference_section(ctx):
    return ctx.channel.id == id_reference


def get_shikigami_stats_1(user_id, shiki):
    stats = users.find_one({"user_id": str(user_id), "shikigami.name": shiki}, {"_id": 0, "shikigami.$": 1})
    try:
        return stats["shikigami"][0]["level"], stats["shikigami"][0]["evolved"], stats["shikigami"][0]["souls"]
    except KeyError:
        return stats["shikigami"][0]["level"], stats["shikigami"][0]["evolved"], {}


def get_shikigami_stats_2(user_id, shiki):
    p = users.find_one({"user_id": str(user_id), "shikigami.name": shiki}, {"_id": 0, "shikigami.$": 1})
    return p["shikigami"][0]["level"], p["shikigami"][0]["evolved"], p["shikigami"][0]["exp"], \
           p["shikigami"][0]["level_exp_next"]


def get_time():
    return datetime.now(tz=pytz.timezone(timezone))


def get_timestamp():
    return datetime.utcfromtimestamp(datetime.timestamp(datetime.now()))


def get_time_converted(utc_dt):
    return utc_dt.replace(tzinfo=pytz.timezone("UTC")).astimezone(tz=pytz.timezone(timezone))


def get_shikigami_display(u):
    return users.find_one({"user_id": str(u.id)}, {"_id": 0, "display": 1})["display"]


def get_shikigami_url(shiki, evolution):
    return shikigamis.find_one({"name": shiki.lower()}, {"_id": 0, "thumbnail": 1})["thumbnail"][evolution]


def get_evo_link(evolution):
    return {True: "evo", False: "pre"}[evolution]


def get_soul_url(name):
    return souls.find_one({"name": name.lower()}, {"_id": 0, "icon_circle": 1})["icon_circle"]


def get_bond(x, y):
    bond_list = sorted([x, y], reverse=True)
    return f"{bond_list[0]}x{bond_list[1]}"


def get_evo_requirement(r):
    return evo_requirement[r]


def get_rarity_emoji(rarity):
    return {"SP": e_1, "SSR": e_2, "SR": e_3, "R": e_4, "N": e_5, "SSN": e_6}[rarity]


def get_rarity_shikigami(shiki):
    return shikigamis.find_one({"name": shiki}, {"_id": 0, "rarity": 1})["rarity"]


def get_emoji(item):
    return emoji_dict[item]


def get_emoji_cards(x):
    return cards_realm[x]


def get_image_variables(rarity_sum, cols, width):
    return width, ceil(len(rarity_sum) / cols) * 90


def get_shiki_tile_coordinates(c, cols, rows):
    return (c * 90 - (ceil(c / cols) - 1) * rows) - 90, (ceil(c / cols) * 90) - 90


def get_variables(r):
    dictionary = {
        "SP": [90 * 6, 6], "SSR": [90 * 8, 8],
        "SR": [90 * 10, 10], "R": [90 * 8, 8],
        "N": [90 * 6, 6], "SSN": [90 * 7, 7]
    }
    return dictionary[r][0], dictionary[r][1]


def get_pool_rarity(r):
    return rarity_dict[r]


def get_frame_thumbnail(frame):
    return frames.find_one({"name": frame}, {"_id": 0, "link": 1})["link"]


def get_talisman_acquire(rarity):
    return talisman_acquire[rarity]


def get_hours_minutes(td):
    return td.seconds // 3600, (td.seconds // 60) % 60


def get_random_shikigami(r):
    return random.choice(rarity_dict[r])


def get_chance_soul_explore(user, min_chance, stage_ref, adj, evo_adj_max, evo_adj):

    grade_total, soul_set_chance, listings_souls = 1, 0, []
    query = users.find_one({"user_id": str(user.id)}, {"_id": 0, "level": 1, "display": 1})

    user_level = query["level"]
    shikigami_name = query["display"]
    shikigami_level, shikigami_evo, shikigami_souls = get_shikigami_stats_1(user.id, shikigami_name)

    if shikigami_evo is True:
        evo_adj = evo_adj_max

    for result in users.aggregate([{
        '$match': {'user_id': str(user.id)}}, {
        '$project': {'souls': 1}}, {
        '$project': {'souls': {'$objectToArray': '$souls'}}}, {
        '$unwind': {'path': '$souls'}}, {
        '$unwind': {'path': '$souls.v'}}, {
        '$match': {'souls.v.equipped': shikigami_name}
    }]):
        grade_total += result["souls"]["v"]["slot"]
        listings_souls.append(result["souls"]["k"])

    soul_count = dict(Counter(listings_souls))

    for a in soul_count:
        if soul_count[a] == 1:
            continue
        elif soul_count[a] == 2:
            soul_set_chance += 1.85
        elif soul_count[a] == 4:
            soul_set_chance += 6.475

    total_soul = 0.696138186504516 * exp(grade_total * 0.0783) + soul_set_chance
    total_soul_adj = random.uniform(total_soul * 0.98, total_soul) + random.uniform(adj[0], adj[1])

    total_chance = user_level + shikigami_level - stage_ref * evo_adj + total_soul_adj

    if total_chance <= min_chance:
        total_chance = min_chance

    return total_chance, shikigami_name, shikigami_evo


def get_shiki_exp_lvl_next_sushi(user, shikigami_name):
    x = users.find_one({"user_id": str(user.id), "shikigami.name": shikigami_name}, {"shikigami.$": 1, "sushi": 1})
    return x["shikigami"][0]['exp'], x["shikigami"][0]['level_exp_next'], x["shikigami"][0]['level'], x["sushi"]


def shikigami_shards_count_generate(shikigami_draw, shards_count, font, x, y):
    outline = ImageDraw.Draw(shikigami_draw)
    outline.text((x - 1, y - 1), str(shards_count), font=font, fill="black")
    outline.text((x + 1, y - 1), str(shards_count), font=font, fill="black")
    outline.text((x - 1, y + 1), str(shards_count), font=font, fill="black")
    outline.text((x + 1, y + 1), str(shards_count), font=font, fill="black")
    outline.text((x, y), str(shards_count), font=font)

    return shikigami_draw


def shikigami_push_user(user_id, shiki, evolve, shards):
    users.update_one({
        "user_id": str(user_id)}, {
        "$push": {
            "shikigami": {
                "name": shiki,
                "rarity": get_rarity_shikigami(shiki),
                "grade": 1,
                "owned": 0,
                "evolved": evolve,
                "shards": shards,
                "level": 1,
                "exp": 0,
                "level_exp_next": 6,
            }
        }
    })


def shikigami_experience_add(user, shikigami_name, experience):

    shikigami_add_exp = users.update_one({
        "user_id": str(user.id),
        "$and": [{
            "shikigami": {
                "$elemMatch": {
                    "name": shikigami_name,
                    "level": {"$lt": 40}}
            }}]
    }, {
        "$inc": {
            "shikigami.$.exp": experience
        }
    })

    if shikigami_add_exp.modified_count > 0:
        shikigami_process_levelup(user.id, shikigami_name)


def shikigami_process_levelup(user_id, shiki):
    query = users.find_one({
        "user_id": str(user_id), "shikigami.name": shiki}, {
        "_id": 0, "shikigami.$": 1,
    })
    experience = query["shikigami"][0]["exp"]
    level = query["shikigami"][0]["level"]
    level_end = int(experience ** 0.400515000062462)

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
                "user_id": str(user_id), "shikigami.name": shiki}, {
                "$set": {
                    "shikigami.$.level_exp_next": 10000,
                    "shikigami.$.exp": 10000
                }
            })


def exploration_check_add_unlocked(user, chapter):
    if users.find_one({
        "user_id": str(user.id)}, {
        "_id": 0, "exploration": 1
    })["exploration"] == chapter:
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


def pluralize(singular, count):
    if count > 1:
        if singular[-1:] == "s":
            return singular + "es"
        return singular + "s"
    else:
        return singular


def push_note(title, content):
    api_key = str(os.environ.get("PUSHBULLET"))
    try:
        pb = pushbullet.Pushbullet(api_key=api_key)
    except pushbullet.errors.PushbulletError:
        pass
    else:
        try:
            pb.push_note(title, content)
        except pushbullet.errors.PushError:
            pass


async def shikigami_post_approximate_results(ctx, query):
    shikigamis_search = shikigamis.find({
        "name": {"$regex": f"^{query[:2].lower()}"}}, {
        "_id": 0, "name": 1
    })

    listings_shikigamis = []
    for result in shikigamis_search:
        listings_shikigamis.append(f"{result['name'].title()}")

    embed = discord.Embed(
        title="Invalid shikigami", colour=ctx.author.colour,
        description=f"check the spelling of the shikigami"
    )
    embed.add_field(
        name="Possible matches", inline=False,
        value="*{}*".format(", ".join(listings_shikigamis)),
    )
    await process_msg_submit(ctx.channel, None, embed)


async def perform_add_log(currency, amount, user_id):

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
                    "date": get_time(),
                }],
                "$position": 0,
                "$slice": 200
            }
        }
    })


async def frame_acquisition(user, frame_name, jades, channel):
    for entry in users.aggregate([{
        "$match": {"user_id": str(user.id)}}, {
        "$unwind": {"path": "$achievements"}}, {
        "$project": {"achievements": 1}}, {
        "$match": {"achievements.name": frame_name}}, {
        "$count": "count"
    }]):
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
    await perform_add_log("jades", jades, user.id)

    intro_caption = " The "
    if frame_name[:3] == "The":
        intro_caption = " "

    embed = discord.Embed(
        color=user.colour, title="Frame acquisition", timestamp=get_timestamp(),
        description=f"{user.mention} has obtained{intro_caption}{frame_name} frame!\n"
                    f"Acquired {jades:,d}{e_j} as bonus rewards!",
    )
    embed.set_footer(icon_url=user.avatar_url, text=f"{user.display_name}")
    embed.set_thumbnail(url=get_frame_thumbnail(frame_name))
    await process_msg_submit(channel, None, embed)


async def process_msg_delete(message, delay):
    try:
        await message.delete(delay=delay)
    except discord.errors.Forbidden:
        pass
    except discord.errors.HTTPException:
        pass


async def process_msg_submit_file(channel, file):
    try:
        return await channel.send(file=file)
    except AttributeError:
        pass
    except discord.errors.Forbidden:
        pass
    except discord.errors.HTTPException:
        pass


async def process_msg_submit(channel, content, embed):
    try:
        return await channel.send(content=content, embed=embed)
    except AttributeError:
        pass
    except discord.errors.Forbidden:
        pass
    except discord.errors.HTTPException:
        pass


async def process_msg_edit(message, content, embed):
    try:
        return await message.edit(content=content, embed=embed)
    except discord.errors.Forbidden:
        pass
    except discord.errors.HTTPException:
        pass


async def process_msg_reaction_add(message, emoji):
    try:
        await message.add_reaction(emoji)
    except discord.errors.Forbidden:
        pass
    except discord.errors.HTTPException:
        pass


async def process_msg_reaction_remove(message, emoji, user):
    try:
        await message.remove_reaction(emoji, user)
    except discord.errors.Forbidden:
        pass
    except discord.errors.HTTPException:
        pass


async def process_msg_reaction_clear(message):
    try:
        await message.clear_reactions()
    except discord.errors.Forbidden:
        pass
    except discord.errors.HTTPException:
        pass


async def process_msg_purge(channel, amount):
    try:
        await channel.purge(limit=amount + 1)
    except discord.errors.Forbidden:
        pass
    except discord.errors.HTTPException:
        pass


async def process_msg_pin(message):
    try:
        await message.pin()
    except discord.errors.Forbidden:
        pass
    except discord.errors.NotFound:
        pass
    except discord.errors.HTTPException:
        pass


async def process_role_remove(member, role):
    try:
        await member.remove_roles(role)
    except discord.errors.Forbidden:
        pass
    except discord.errors.HTTPException:
        pass


async def process_role_add(member, role):
    try:
        await member.add_roles(role)
    except discord.errors.Forbidden:
        pass
    except discord.errors.HTTPException:
        pass


async def process_channel_edit(channel, name, topic):
    try:
        await channel.edit(name=name, topic=topic)
    except AttributeError:
        pass
    except discord.errors.Forbidden:
        pass
    except discord.errors.NotFound:
        pass
    except discord.errors.HTTPException:
        pass


async def process_channel_delete(channel):
    try:
        await channel.delete()
    except AttributeError:
        pass
    except discord.errors.Forbidden:
        pass
    except discord.errors.NotFound:
        pass
    except discord.errors.HTTPException:
        pass


async def process_msg_invalid_member(ctx):
    embed = discord.Embed(
        title="Invalid member", colour=ctx.author.colour,
        description="That member does not exist or does not have a profile in this guild"
    )
    await process_msg_submit(ctx.channel, None, embed)


"""QUESTS"""


def check_if_user_has_accepted(user):
    return quests.find_one({"user_id": str(user.id)}, {"_id": 0, "user_id": 1}) != {}


def get_data_quest1(user_id):
    cycle, current_path, timestamp, hints_user, actions, purchase = "", "", "", "", "", ""
    for profile in quests.aggregate([{
        "$match": {"user_id": str(user_id)}}, {
        "$project": {"_id": 0, "quest1": {"$slice": ["$quest1", -1]}}}
    ]):
        cycle = profile["quest1"][0]["cycle"]
        current_path = profile["quest1"][0]["current_path"]
        timestamp = profile["quest1"][0]["timestamp"]
        hints_user = profile["quest1"][0]["hints"]
        actions = profile["quest1"][0]["actions"]
        purchase = profile["quest1"][0]["purchase"]
        break
    return cycle, current_path, timestamp, hints_user, actions, purchase


def get_profile_finished_quest1(user):
    score, timestamp_start, patronus_summon, hints_unlocked, owl_final, wand, paths = "", "", "", "", "", "", ""

    for profile in quests.aggregate([{
        "$match": {"user_id": str(user.id)}}, {
        "$project": {"_id": 0, "quest1": {"$slice": ["$quest1", -1]}}
    }]):
        patronus_summon = profile["quest1"][0]["patronus"]
        score = profile["quest1"][0]["score"]
        timestamp_start = profile["quest1"][0]["timestamp_start"]
        hints_unlocked = profile["quest1"][0]["hints_unlocked"]
        owl_final = profile["quest1"][0]["owl"]
        wand = profile["quest1"][0]["wand"]
        paths = profile["quest1"][0]["hints"]
        break

    return score, timestamp_start, patronus_summon, hints_unlocked, owl_final, wand, paths


def get_profile_history_quest1(user, cycle):
    for result in quests.aggregate([{
        '$match': {'user_id': str(user.id)}}, {
        '$unwind': {'path': '$quest1'}}, {
        '$match': {'quest1.cycle': cycle
                   }
    }]):
        return result


def get_profile_progress_quest1(user):
    score, timestamp_start, current_path, cycle, hints_unlocked, paths = "", "", "", "", "", ""

    for profile in quests.aggregate([{
        "$match": {"user_id": str(user.id)}}, {
        "$project": {"_id": 0, "quest1": {"$slice": ["$quest1", -1]}}
    }]):
        cycle = profile["quest1"][0]["cycle"]
        current_path = profile["quest1"][0]["current_path"]
        score = profile["quest1"][0]["score"]
        timestamp_start = profile["quest1"][0]["timestamp_start"]
        hints_unlocked = profile["quest1"][0]["hints_unlocked"]
        paths = profile["quest1"][0]["hints"]
        break

    return score, timestamp_start, current_path, cycle, hints_unlocked, paths


def spell_check(msg):
    translate, spell = msg.lower().translate({ord(i): None for i in "! "}), "expectopatronum"
    return all(c in spell for c in translate) and all(c in translate for c in spell)


async def generate_data(guild, secret_channel, channel):
    channel_name = secret_channel.replace(" ", "-")
    webhook = await channel.create_webhook(name="webhooker")

    if channel_name == "eeylops-owl-emporium":
        avatar_url = "https://i.imgur.com/8xR61b4.jpg"
        username = "Manager Eeylops"
        url = "https://i.imgur.com/wXSibYR.jpg"

    elif channel_name == "gringotts-bank":
        avatar_url = "https://i.imgur.com/IU882rV.jpg"
        username = "Bank Manager Gringotts"
        url = "https://i.imgur.com/whPMNPb.jpg"

    else:
        avatar_url = "https://i.imgur.com/DEuO4la.jpg"
        username = "Ollivanders"
        url = "https://i.imgur.com/5ibOfcp.jpg"

    guilds.update_one({
        "server": str(guild.id)}, {
        "$set": {
            f"{channel_name}.id": str(channel.id),
            f"{channel_name}.webhook": webhook.url,
            f"{channel_name}.avatar": avatar_url,
            f"{channel_name}.username": username
        }
    })
    await secret_banner(webhook.url, avatar_url, username, url)


async def secret_banner(webhook_url, avatar, username, url):
    webhook = DiscordWebhook(url=webhook_url, avatar_url=avatar, username=username)
    embed = DiscordEmbed(color=0xffffff)
    embed.set_image(url=url)
    webhook.add_embed(embed)
    webhook.execute()


async def reaction_closed(message):
    await message.add_reaction("🇨")
    await message.add_reaction("🇱")
    await message.add_reaction("🇴")
    await message.add_reaction("🇸")
    await message.add_reaction("🇪")
    await message.add_reaction("🇩")
    await asyncio.sleep(4)
    await process_msg_delete(message, 0)


async def secret_response(channel_name, description):
    secret = guilds.find_one({"server": str(id_guild)}, {"_id": 0, str(channel_name): 1})
    webhook_url = secret[str(channel_name)]["webhook"]
    avatar = secret[str(channel_name)]["avatar"]
    username = secret[str(channel_name)]["username"]
    webhook = DiscordWebhook(url=webhook_url, avatar_url=avatar, username=username)
    embed = DiscordEmbed(color=0xffffff, description="*\"" + description + "\"*")
    webhook.add_embed(embed)
    webhook.execute()


async def owls_restock():
    owls.update_many({}, {"$set": {"purchaser": "None"}})


async def penalize_quest1(user, cycle, points):
    quests.update_one({"user_id": str(user.id), "quest1.cycle": cycle}, {"$inc": {"quest1.$.score": -points}})


async def action_update_quest1(user, cycle, actions):
    quests.update_one({"user_id": str(user.id), "quest1.cycle": cycle}, {"$inc": {"quest1.$.actions": actions}})


async def update_hint_quest1(user, path, cycle, hint):
    quests.update_one({
        "user_id": str(user.id), "quest1.cycle": cycle}, {
        "$set": {
            f"quest1.$.hints.{path}.{hint}": "unlocked",
            f"quest1.$.timestamp": get_time().strftime("%Y-%b-%d %HH")
        },
        "$inc": {
            f"quest1.$.hints_unlocked": 1
        }
    })
