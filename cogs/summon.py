"""
Summon Module
Miketsu, 2019
"""

import random

import discord
from discord.ext import commands

from cogs.mongo.database import get_collections
from cogs.startup import e_a, pluralize, embed_color

# Collections
streak = get_collections("miketsu", "streak")
users = get_collections("miketsu", "users")
shikigamis = get_collections("miketsu", "shikigamis")

# Listings
pool_sp = []
pool_ssr = []
pool_sr = []
pool_r = []
pool_all = []

caption = open("lists/summon.lists")
summon_caption = caption.read().splitlines()
caption.close()

for document in shikigamis.aggregate([
    {
        "$project": {
            "shikigami.name": 1
        }
    }, {
        "$unwind": {
            "path": "$shikigami"
        }
    }, {
        "$project": {
            "_id": 0
        }
    }
]):
    pool_all.append(document["shikigami"]["name"])


def get_not_shrine_rarity(rarity):
    query_ssr_not_shrine = [{
        '$match': {'rarity': rarity}}, {'$unwind': {'path': '$shikigami'}}, {
        '$match': {'shikigami.shrine': False}}, {'$project': {'shikigami.name': 1}}
    ]
    return query_ssr_not_shrine


def get_shard_requirement(x):
    rarity = shikigamis.find_one({"shikigami.name": x}, {"_id": 0, "rarity": 1})["rarity"]
    dictionary = {
        "SP": 25, "SSR": 20, "SR": 15, "R": 10
    }
    return dictionary[rarity], rarity


for shiki in shikigamis.aggregate(get_not_shrine_rarity("SP")):
    pool_sp.append(shiki["shikigami"]["name"])

for shiki in shikigamis.aggregate(get_not_shrine_rarity("SSR")):
    pool_ssr.append(shiki["shikigami"]["name"])

for shiki in shikigamis.aggregate(get_not_shrine_rarity("SR")):
    pool_sr.append(shiki["shikigami"]["name"])

for shiki in shikigamis.aggregate(get_not_shrine_rarity("R")):
    pool_r.append(shiki["shikigami"]["name"])


def get_thumbnail_shikigami(shikigami):
    url = shikigamis.find_one({
        "shikigami": {
            "$elemMatch": {
                "name": shikigami}}}, {
        "_id": 0, "shikigami.$.name": 1
    })["shikigami"][0]["thumbnail"]["pre_evo"]
    return url


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
            evolve, shards = "False", 0
            if summon[0] == "SP":
                evolve, shards = "True", 5

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
    if streak.find_one({"user_id": str(user.id)}, {"_id": 0}) is None:
        streak.insert_one({"user_id": str(user.id), "SSR_current": 0, "SSR_record": 0})

    for summon in summon_pull:
        ssr_current = streak.find_one({"user_id": str(user.id)}, {"_id": 0})["SSR_current"]
        ssr_record = streak.find_one({"user_id": str(user.id)}, {"_id": 0})["SSR_record"]

        if summon[0] == "SP" or summon[0] == "SR" or summon[0] == "R":
            if ssr_current == ssr_record:
                streak.update_one({"user_id": str(user.id)}, {"$inc": {"SSR_current": 1, "SSR_record": 1}})
            else:
                streak.update_one({"user_id": str(user.id)}, {"$inc": {"SSR_current": 1}})

        if summon[0] == "SSR":
            streak.update_one({"user_id": str(user.id)}, {"$set": {"SSR_current": 0}})


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
        description += "🔸{}\n".format(x[1])

    embed = discord.Embed(color=user.colour, title="🎊 Results", description=description)

    if amulet_pull == 10:
        embed.set_footer(text=f"{f_sp}; {f_ssr}; {f_sr}; {f_r}")

    elif amulet_pull == 1:
        shikigami_pulled = summon_pull[0][1].replace("||", "")
        embed.set_thumbnail(url=get_thumbnail_shikigami(shikigami_pulled))

    msg = "{}".format(random.choice(summon_caption)).format(user.mention)
    await ctx.channel.send(msg, embed=embed)
    await summon_update(user, sum_sp, sum_ssr, sum_sr, sum_r, amulet_pull, summon_pull)
    await summon_streak(user, summon_pull)


async def summon_perform_shards(ctx, shikigami, user):
    try:
        profile = users.find_one({
            "user_id": str(user.id), "shikigami.name": shikigami}, {
            "_id": 0, "shikigami.$.name": 1
        })

        shards = profile["shikigami"][0]["shards"]
        required_shards, rarity = get_shard_requirement(shikigami)

        if shards >= required_shards:
            query = users.find_one({
                "user_id": str(user.id),
                "shikigami.name": shikigami}, {
                "_id": 0, "shikigami.$": 1
            })

            if query is None:
                evolve, shards = "False", 0
                if rarity == "SP":
                    evolve, shards = "True", 0

                users.update_one({
                    "user_id": str(user.id)}, {
                    "$push": {
                        "shikigami": {
                            "name": shikigami,
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
                "shikigami.name": shikigami}, {
                "$inc": {
                    f"{rarity}": 1,
                    "shikigami.$.owned": 1,
                    "shikigami.$.shards": -required_shards
                }
            })
            embed = discord.Embed(
                title="Summon success", colour=discord.Colour(embed_color),
                description=f"{user.mention}, you summon the {rarity} shikigami {shikigami}!"
            )
            embed.set_thumbnail(url=get_thumbnail_shikigami(shikigami))
            await ctx.channel.send(embed=embed)

        else:
            embed = discord.Embed(
                title="Summon failed", colour=discord.Colour(embed_color),
                description=f"{user.mention}, you lack {required_shards - shards} {shikigami} shards"
            )
            await ctx.channel.send(embed=embed)

    except TypeError:
        embed = discord.Embed(
            title="Summon failed", colour=discord.Colour(embed_color),
            description=f"{user.mention}, you do not have any shards of {shikigami}"
        )
        await ctx.channel.send(embed=embed)


class Summon(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(aliases=["summon", "s"])
    @commands.guild_only()
    @commands.cooldown(1, 180, commands.BucketType.user)
    async def summon_perform(self, ctx, *, args=None):

        user = ctx.author
        embed = discord.Embed(
            title="summon, s", colour=discord.Colour(embed_color),
            description="simulate summon and collect shikigamis"
        )
        embed.add_field(
            name="Shard Requirement",
            value="```"
                  "SP    ::   25\n"
                  "SSR   ::   20\n"
                  "SR    ::   15\n"
                  "R     ::   10\n"
                  "```",
            inline=False
        )
        embed.add_field(name="Formats", value="*`;summon <1, 10, shikigami_name>`*", inline=False)

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
                await ctx.channel.send(embed=embed)

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
            await ctx.channel.send(embed=embed)

        except ValueError:
            shikigami = args.title()

            if shikigami in pool_all:
                await summon_perform_shards(ctx, shikigami, user)

            else:
                await ctx.channel.send(embed=embed)

        self.client.get_command("summon_perform").reset_cooldown(ctx)


def setup(client):
    client.add_cog(Summon(client))
