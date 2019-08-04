"""
Summon Module
Miketsu, 2019
"""

import random

import discord
from discord.ext import commands

from cogs.mongo.db import get_collections
from cogs.startup import e_a, pluralize

# Collections
streak = get_collections("miketsu", "streak")
users = get_collections("miketsu", "users")
shikigamis = get_collections("miketsu", "shikigamis")

# Listings
pool_sp = []
pool_ssr = []
pool_sr = []
pool_r = []

caption = open("lists/summon.lists")
summon_caption = caption.read().splitlines()
caption.close()


def get_not_shrine_rarity(rarity):
    query_ssr_not_shrine = [{
        '$match': {'rarity': rarity}}, {'$unwind': {'path': '$shikigami'}}, {
        '$match': {'shikigami.shrine': False}}, {'$project': {'shikigami.name': 1}}
    ]
    return query_ssr_not_shrine


for shiki in shikigamis.aggregate(get_not_shrine_rarity("SP")):
    pool_sp.append(shiki["shikigami"]["name"])

for shiki in shikigamis.aggregate(get_not_shrine_rarity("SSR")):
    pool_ssr.append(shiki["shikigami"]["name"])

for shiki in shikigamis.aggregate(get_not_shrine_rarity("SR")):
    pool_sr.append(shiki["shikigami"]["name"])

for shiki in shikigamis.aggregate(get_not_shrine_rarity("R")):
    pool_r.append(shiki["shikigami"]["name"])


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

            evolve = "False"
            if summon[0] == "SP":
                evolve = "True"

            users.update_one({
                "user_id": str(user.id)}, {
                "$push": {
                    "shikigami": {
                        "name": summon[1].replace("||", ""),
                        "rarity": summon[0],
                        "grade": 1,
                        "owned": 0,
                        "evolved": evolve}
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
        profile = {
            "user_id": str(user.id),
            "SSR_current": 0, "SSR_record": 0
        }
        streak.insert_one(profile)

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
        description += ":small_orange_diamond:{}\n".format(x[1])

    embed = discord.Embed(color=user.colour, title="🎊 Results", description=description)

    if amulet_pull == 10:
        embed.set_footer(text=f"{f_sp}; {f_ssr}; {f_sr}; {f_r}")

    elif amulet_pull == 1:
        rarity = summon_pull[0][0]
        shikigami_pulled = summon_pull[0][1].replace("||", "")

        thumbnail = shikigamis.find_one({
            "rarity": rarity}, {
            "_id": 0, "shikigami": {
                "$elemMatch": {
                    "name": shikigami_pulled
                }
            }
        })
        embed.set_thumbnail(url=thumbnail["shikigami"][0]["thumbnail"]["pre_evo"])

    msg = "{}".format(random.choice(summon_caption)).format(user.mention)
    await ctx.channel.send(msg, embed=embed)
    await summon_update(user, sum_sp, sum_ssr, sum_sr, sum_r, amulet_pull, summon_pull)
    await summon_streak(user, summon_pull)


class Summon(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(aliases=["summon", "s"])
    @commands.guild_only()
    @commands.cooldown(1, 180, commands.BucketType.user)
    async def summon_perform(self, ctx, args):

        embed = discord.Embed(
            title="summon, s", colour=discord.Colour(0xffe6a7),
            description="simulate summon and collect shikigamis"
        )
        embed.add_field(name="Format", value="*`;summon <1 or 10>`*")

        try:
            user = ctx.author
            amulet_pull = int(args)
            amulet_have = users.find_one({"user_id": str(user.id)}, {"_id": 0, "amulets": 1})["amulets"]

            if amulet_have == 0:
                embed = discord.Embed(
                    title="Insufficient amulets", colour=discord.Colour(0xffe6a7),
                    description="Exchange at the shop to obtain more"
                )
                await ctx.channel.send(embed=embed)

            elif args not in ["1", "10"]:
                await ctx.channel.send(embed=embed)

            elif amulet_have > 0:

                if amulet_pull > amulet_have:
                    embed = discord.Embed(
                        title="Insufficient amulets", colour=discord.Colour(0xffe6a7),
                        description=f"{user.mention}, you only have {amulet_have}{e_a} in your possession"
                    )
                    await ctx.channel.send(embed=embed)

                elif amulet_pull == 10 and amulet_have >= 10:
                    await summon_perform(ctx, user, amulet_pull)

                elif amulet_pull == 1 and amulet_have >= 1:
                    await summon_perform(ctx, user, amulet_pull)

        except ValueError:
            await ctx.channel.send(embed=embed)

        self.client.get_command("summon_perform").reset_cooldown(ctx)


def setup(client):
    client.add_cog(Summon(client))
