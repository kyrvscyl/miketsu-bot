"""
Initialize Module
Miketsu, 2020
"""

import os
from datetime import datetime

import discord
import pytz
from pushbullet import Pushbullet

from cogs.ext.database import get_collections

"""SETUP"""

version = "1.7.beta"
command_prefix = ";"
time_start = datetime.now()


"""PUSHBULLET"""

api_key = str(os.environ.get("PUSHBULLET"))
pb = Pushbullet(api_key=api_key)


"""COLLECTIONS"""

books = get_collections("books")
bosses = get_collections("bosses")
bounties = get_collections("bounties")
config = get_collections("config")
duelists = get_collections("duelists")

changelogs = get_collections("changelogs")
events = get_collections("events")
explores = get_collections("explores")
frames = get_collections("frames")
guilds = get_collections("guilds")
logs = get_collections("logs")
sortings = get_collections("sortings")
members = get_collections("members")
memos = get_collections("memos")
portraits = get_collections("portraits")
quests = get_collections("quests")
realms = get_collections("realms")

reminders = get_collections("reminders")
shikigamis = get_collections("shikigamis")
ships = get_collections("ships")
souls = get_collections("souls")
streaks = get_collections("streaks")

users = get_collections("users")
weathers = get_collections("weathers")
zones = get_collections("zones")

shoots = get_collections("shoots")
stickers = get_collections("stickers")


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
    "souls [beta]"
]

commands_others = [
    "changelogs", "bounty", "suggest", "stickers", "newsticker", "wander", "portrait",
    "stats", "duel\\*\\*", "memo\\*", "manage\\*", "events\\*", "info", "report"
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

"""ROLES"""

id_boss_busters = server["roles"]["boss_busters"]
id_silver_sickles = server["roles"]["silver_sickles"]
id_shard_seeker = server["roles"]["shard_seekers"]

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
e_f = emojis["f"]
e_j = emojis["j"]
e_m = emojis["m"]
e_s = emojis["s"]
e_t = emojis["t"]
e_x = emojis["x"]


"""SUMMON POOL"""

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

for shikigami in shikigamis.find({}, {"_id": 0, "name": 1, "rarity": 1, "shrine": 1}):
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

"""REALMS"""

realm_cards = []

for card in realms.find({}, {"_id": 0}):
    realm_cards.append(f"{card['name'].lower()}")


"""SOULS"""

souls_all = []
soul_dungeons = [f"{x}" for x in list(range(1, 11))]

for soul in souls.find({}, {"_id": 0, "name": 1}):
    souls_all.append(soul["name"])

"""SHOP"""

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
        f"▫ `{trade[1]}`{emoji_dict[trade[0]]} → `{trade[3]:,d}`{emoji_dict[trade[2]]} | "
        f"{trade[4]} {trade[5]}\n"
    )


"""FUNCTIONS"""


def lengthen_code(index):
    prefix = "#{}"
    if index < 10:
        prefix = "#00{}"
    elif index < 100:
        prefix = "#0{}"
    return prefix.format(index)


def lengthen_memo(index):
    prefix = "{}"
    if index < 10:
        prefix = "000{}"
    elif index < 100:
        prefix = "00{}"
    elif index < 1000:
        prefix = "0{}"
    return prefix.format(index)


def check_if_valid_and_castle(ctx):
    return ctx.channel.category.id == id_castle and str(ctx.channel.name) not in invalid_channels


def check_if_restricted_section(ctx):
    return str(ctx.channel.id) == id_restricted


def check_if_developer_team(ctx):
    return str(ctx.author.id) in guilds.find_one({"server": str(id_guild)}, {"_id": 0, "developers": 1})["developers"]


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


def get_time():
    return datetime.now(tz=pytz.timezone(timezone))


def get_timestamp():
    return datetime.utcfromtimestamp(datetime.timestamp(datetime.now()))


def get_time_converted(utc_dt):
    return utc_dt.replace(tzinfo=pytz.timezone("UTC")).astimezone(tz=pytz.timezone(timezone))


def pluralize(singular, count):
    if count > 1:
        if singular[-1:] == "s":
            return singular + "es"
        return singular + "s"
    else:
        return singular


def get_thumbnail_shikigami(shiki, evolution):
    return shikigamis.find_one({"name": shiki.lower()}, {"_id": 0, "thumbnail": 1})["thumbnail"][evolution]


def get_evo_link(evolution):
    return {True: "evo", False: "pre"}[evolution]


def get_soul_thumbnail(name):
    query = souls.find_one({"name": name.lower()}, {"_id": 0, "icon_circle": 1})
    return query["icon_circle"]


def get_bond(x, y):
    bond_list = sorted([x, y], reverse=True)
    return f"{bond_list[0]}x{bond_list[1]}"


def check_if_channel_is_pvp(ctx):
    return str(ctx.channel.id) == guilds.find_one({
        "server": str(id_guild)}, {"_id": 0, "channels": 1}
    )["channels"]["duelling-room"]


def check_if_reference_section(ctx):
    return str(ctx.channel.id) == guilds.find_one({
        "server": str(id_guild)}, {"_id": 0, "channels": 1}
    )["channels"]["reference-section"]


def get_shard_requirement(shiki):
    rarity = shikigamis.find_one({"name": shiki.lower()}, {"_id": 0, "rarity": 1})["rarity"]
    return shard_requirement[rarity], rarity


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


def get_variables(r):
    dictionary = {
        "SP": [90 * 6, 6],
        "SSR": [90 * 8, 8],
        "SR": [90 * 10, 10],
        "R": [90 * 8, 8],
        "N": [90 * 6, 6],
        "SSN": [90 * 7, 7]
    }
    return dictionary[r]


def get_frame_thumbnail(frame):
    return frames.find_one({"name": frame}, {"_id": 0, "link": 1})["link"]


def get_talisman_acquire(rarity):
    return talisman_acquire[rarity]


def hours_minutes(td):
    return td.seconds // 3600, (td.seconds // 60) % 60


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
                "level_exp_next": 6
            }
        }
    })


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


async def process_msg_delete(message, delay):
    try:
        await message.delete(delay=delay)
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
