"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import random

import discord
from discord.ext import commands

from cogs.mongo.db import users, streak, shikigami

# Generate summon pool
pool_sp = []
for shiki in shikigami.find({"rarity": "SP"}, {"_id": 0, "shikigami.name": 1}):
    for entry in shiki["shikigami"]:
        pool_sp.append(entry["name"])

pool_ssr = []
for shiki in shikigami.find({"rarity": "SSR"}, {"_id": 0, "shikigami.name": 1}):
    for entry in shiki["shikigami"]:
        pool_ssr.append(entry["name"])

pool_sr = []
for shiki in shikigami.find({"rarity": "SR"}, {"_id": 0, "shikigami.name": 1}):
    for entry in shiki["shikigami"]:
        pool_sr.append(entry["name"])

pool_r = []
for shiki in shikigami.find({"rarity": "R"}, {"_id": 0, "shikigami.name": 1}):
    for entry in shiki["shikigami"]:
        pool_r.append(entry["name"])

# Global Variables
emoji_a = "<:amulet:573071120685596682>"

# Lists startup
caption = open("lists/summon.lists")
summon_caption = caption.read().splitlines()
caption.close()


def pluralize(singular, count):
    if count > 1:
        return singular + "s"
    else:
        return singular


# noinspection PyShadowingNames
async def summon_update(user, users, sum_sp, sum_ssr, sum_sr, sum_r, amulet_pull, summon_pull):
    users.update_one({"user_id": str(user.id)}, {
        "$inc": {"SP": sum_sp, "SSR": sum_ssr, "SR": sum_sr, "R": sum_r, "amulets_spent": amulet_pull,
                 "amulets": -amulet_pull}})

    for summon in summon_pull:
        # Creates a shikigami profile
        if users.find_one({"user_id": str(user.id), "shikigami.name": summon[1].replace("||", "")},
                          {"_id": 0, "shikigami.$": 1}) is None:
            users.update_one({"user_id": str(user.id)}, {"$push": {
                "shikigami": {"name": summon[1].replace("||", ""), "rarity": summon[0], "grade": 1, "owned": 0,
                              "evolved": "False"}
            }})

        users.update_one({"user_id": str(user.id), "shikigami.name": summon[1].replace("||", "")}, {
            "$inc": {
                "shikigami.$.owned": 1
            }})


async def summon_streak(user, summon_pull):
    if streak.find_one({"user_id": str(user.id)}, {"_id": 0}) is None:
        profile = {"user_id": str(user.id), "SSR_current": 0, "SSR_record": 0}
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


# noinspection PyShadowingNames
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

    sum_sp = sum(entry.count("SP") for entry in summon_pull)
    sum_ssr = sum(entry.count("SSR") for entry in summon_pull)
    sum_sr = sum(entry.count("SR") for entry in summon_pull)
    sum_r = sum(entry.count("R") for entry in summon_pull)

    f_sp = str(sum_sp) + " " + pluralize("SP", sum_sp)
    f_ssr = str(sum_ssr) + " " + pluralize("SSR", sum_ssr)
    f_sr = str(sum_sr) + " " + pluralize("SR", sum_sr)
    f_r = str(sum_r) + " " + pluralize("R", sum_r)

    description = ""
    for entry in summon_pull:
        description += ":small_orange_diamond:{}\n".format(entry[1])

    embed = discord.Embed(color=user.colour, title=":confetti_ball: Results", description=description)

    if amulet_pull == 10:
        embed.set_footer(text=f"{f_sp}; {f_ssr}; {f_sr}; {f_r}")

    # Thumbnails
    elif amulet_pull == 1:
        rarity = summon_pull[0][0]
        shiki = summon_pull[0][1].replace("||", "")
        thumbnail = \
            shikigami.find_one({"rarity": rarity}, {"_id": 0, "shikigami": {"$elemMatch": {"name": shiki}}})[
                "shikigami"][0]["thumbnail"]["pre_evo"]
        embed.set_thumbnail(url=thumbnail)

    msg = "{}".format(random.choice(summon_caption)).format(user.mention)
    await ctx.channel.send(msg, embed=embed)
    await summon_update(user, users, sum_sp, sum_ssr, sum_sr, sum_r, amulet_pull, summon_pull)
    await summon_streak(user, summon_pull)


class Summon(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(aliases=["s"])
    @commands.guild_only()
    async def summon(self, ctx, arg):
        user = ctx.author
        try:
            amulet_pull = int(arg)
            amulet_have = users.find_one({"user_id": str(user.id)}, {"_id": 0, "amulets": 1})["amulets"]
            if amulet_have > 0:
                if amulet_pull > amulet_have:
                    await ctx.channel.send(f"{user.mention}, you only have {amulet_have}{emoji_a} to summon")

                elif amulet_pull == 10 and amulet_have >= 10:
                    await summon_perform(ctx, user, amulet_pull)

                elif amulet_pull == 1 and amulet_have >= 1:
                    await summon_perform(ctx, user, amulet_pull)
                else:
                    await ctx.channel.send("{user.mention}, summon can only be by ones or by tens.")
            else:
                await ctx.channel.send(f"{user.mention}, you have no {emoji_a} to summon")
        except ValueError:
            await ctx.channel.send("Type `;summon <1 or 10>` to perform summon.")


def setup(client):
    client.add_cog(Summon(client))
