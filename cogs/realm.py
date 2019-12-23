"""
Error Module
Miketsu, 2019
"""
import asyncio
import random
from datetime import datetime, timedelta
from math import exp

import discord
import pytz
from discord.ext import commands

from cogs.mongo.database import get_collections
from cogs.startup import embed_color, guild_id

# Collections
guilds = get_collections("guilds")
realms = get_collections("realms")
config = get_collections("config")
ships = get_collections("ships")
users = get_collections("users")
logs = get_collections("logs")

# Lists
realm_cards = []

# Variables
spell_spam_id = guilds.find_one({"server": str(guild_id)}, {"_id": 0, "channels": 1})["channels"]["spell-spam"]
scroll_id = guilds.find_one({"server": str(guild_id)}, {"_id": 0, "channels": 1})["channels"]["scroll-of-everything"]
emoji_dict = config.find_one({"dict": 1}, {"_id": 0, "get_emojis": 1})["get_emojis"]
developer_team = guilds.find_one({"server": str(guild_id)}, {"_id": 0, "developers": 1})["developers"]
timezone = config.find_one({"var": 1}, {"_id": 0, "timezone": 1})["timezone"]


for card in realms.find({}, {"_id": 0}):
    realm_cards.append(f"{card['name'].lower()}")


def get_time():
    return datetime.now(tz=pytz.timezone(timezone))


def get_timestamp():
    return datetime.utcfromtimestamp(datetime.timestamp(datetime.now()))


def get_bond(x, y):
    bond_list = sorted([x.id, y.id], reverse=True)
    return f"{bond_list[0]}x{bond_list[1]}"


def emojify(item):
    return emoji_dict[item]


def pluralize(singular, count):
    if count > 1:
        if singular[-1:] == "s":
            return singular + "es"
        return singular + "s"
    else:
        return singular


def check_if_user_has_development_role(ctx):
    return str(ctx.author.id) in developer_team


async def logs_add_line(currency, amount, user_id):

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


class Realm(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.prefix = self.client.command_prefix

    @commands.command(aliases=["rca"])
    @commands.is_owner()
    async def realm_card_add(self, ctx, args):

        # ;rc moon 1 experience 130 link

        profile = {
            "name": args[0].lower(),
            "base": int(args[1]),
            "rewards": args[2],
            "link": args[4]
        }
        realms.insert_one(profile)
        await ctx.message.add_reaction("✅")

    @commands.command(aliases=["realms", "rlms"])
    @commands.guild_only()
    async def realm_card_show_all(self, ctx):

        dictionary, cards_listing, page = {}, [], 1
        for x in realms.find({}, {"_id": 0}):
            cards_listing.append([x["name"], x["rewards"], x["base"], x['link']["6"]])
            dictionary.update(
                {f"str({x['page']})": f"{x['name']}"}
            )

        page_total = len(dictionary)

        def create_new_embed_page(page_new):
            embed = discord.Embed(
                title="realms",
                description="equip realms with your ships to obtained shared rewards",
                color=embed_color
            )

            def generate_data():
                values, data = [], cards_listing[page_new - 1]

                for y in range(1, 7):
                    rewards = int(data[2] * exp(0.3868 * y))
                    values.append(
                        f"`Grade {y}` :: `~ {rewards:,d}`{emojify(data[1])}\n"
                    )
                embed.set_thumbnail(url=data[3])

                # noinspection PyUnresolvedReferences
                embed.add_field(
                    name=f"{data[0].title()} card",
                    value=f"{' '.join(values)}"
                )
                embed.set_footer(text=f"Page: {page_new} of {len(cards_listing)}")

            generate_data()
            return embed

        msg = await ctx.channel.send(embed=create_new_embed_page(1))
        await msg.add_reaction("⬅")
        await msg.add_reaction("➡")

        def check(r, u):
            return msg.id == r.message.id and str(r.emoji) in ["⬅", "➡"] and u.id == ctx.author.id

        while True:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=60, check=check)
            except asyncio.TimeoutError:
                return
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

    @commands.command(aliases=["realm", "rlm"])
    @commands.guild_only()
    async def realm_card_use(self, ctx, arg1=None, *, member: discord.Member = None):

        if arg1 is None and member is None:
            embed = discord.Embed(
                color=embed_color,
                title="realm use, rlm u",
                description=f"equip your realm by mentioning a member"
            )
            embed.add_field(
                name="Formats",
                value=f"*`{self.prefix}realm use <@member>`*\n"
                      f"*`{self.prefix}rlm u <@member>`*\n",
                inline=False
            )
            await ctx.channel.send(embed=embed)

        elif arg1.lower() in ["use", "u"] and member is None:
            return

        elif arg1.lower() in ["use", "u"] and member is not None:

            code = get_bond(ctx.author, member)
            ship_data = ships.find_one({"code": code}, {"_id": 0})
            if ship_data is not None:

                if ship_data["card"]["equipped"] is True:
                    return

                elif ship_data["card"]["equipped"] is False:

                    user_cards = []
                    for x in users.find_one({"user_id": str(ctx.author.id)}, {"_id": 0, "cards": 1}):
                        user_cards.append(f"{x['name']}/{x['grade']}")

                    embed = discord.Embed(
                        color=embed_color,
                        title="Realm card selection",
                        description=f"enter a valid realm card and grade"
                    )
                    embed.add_field(
                        name="Available cards",
                        value=f"*{', '.join(user_cards)}*",
                        inline=False
                    )
                    msg = await ctx.channel.send(embed=embed)

                    def check(m):
                        return m.lower() in user_cards and m.author.id == ctx.author.id

                    try:
                        select = await self.client.wait_for("message", timeout=60, check=check)
                    except asyncio.TimeoutError:
                        return
                    else:
                        select_formatted = select.lower().split("/")
                        ships.update_one({
                            "code": code
                        }, {
                            "$set": {
                                "card.equipped": True,
                                "card.name": select_formatted[0],
                                "card.grade": select_formatted[1],
                                "card.timestamp": get_time(),
                                "card.collected": False
                            }
                        })
                        await msg.add_reaction("✅")

    @commands.command(aliases=["rcollect", "rcol"])
    @commands.guild_only()
    async def realm_card_collect_rewards(self, ctx, member: discord.Member = None):

        try:
            code = get_bond(ctx.author, member)
            ship_data = ships.find_one({"code": code}, {"_id": 0})
        except TypeError:
            embed = discord.Embed(
                colour=discord.Colour(embed_color),
                title="rcollect, rcol",
                description=f"collect your cruising rewards"
            )
            embed.add_field(
                name="Format",
                value=f"*{self.prefix}rcollect <@member>*"
            )
            await ctx.channel.send(embed=embed)
            return

        if ship_data is None:
            embed = discord.Embed(
                colour=discord.Colour(embed_color),
                title="Invalid ship",
                description=f"that ship has sunk before it was even fully built"
            )
            await ctx.channel.send(embed=embed)

        elif ship_data["cards"]["collected"] is True or ship_data["cards"]["equipped"] is False:
            embed = discord.Embed(
                colour=discord.Colour(embed_color),
                title="Invalid collection",
                description=f"the ship has not yet been deployed for cruise"
            )
            await ctx.channel.send(embed=embed)

        elif ship_data["cards"]["collected"] is False and ship_data["cards"]["equipped"] is True:

            card_name = ship_data["cards"]["name"]
            time_deployed = ship_data["cards"]["timestamp"]

            if datetime.now() < (time_deployed + timedelta(days=1)):
                embed = discord.Embed(
                    colour=discord.Colour(embed_color),
                    title="Invalid collection",
                    description=f"the ship has not yet returned from its cruise"
                )
                await ctx.channel.send(embed=embed)

            elif datetime.now() >= (time_deployed + timedelta(days=1)):
                card_data = realms.find_one({"name": card_name}, {"_id": 0})

                rewards = card_data["rewards"]
                base = card_data["base"]
                grade = ship_data["cards"]["grade"]
                link = card_data["link"][str(grade)]

                rewards_count = int(base * exp(0.3868 * grade))
                adjusted_rewards_count = int(random.uniform(rewards_count * 0.95, rewards_count * 1.05))

                try:
                    shipper1 = ctx.guild.get_member(int(ship_data["shipper1"]))
                    shipper2 = ctx.guild.get_member(int(ship_data["shipper2"]))

                    embed = discord.Embed(
                        description=f"Captains {shipper1.mention} x {shipper2.mention}\n"
                                    f"Cruise: {ship_data['ship_name']}\n"
                                    f"Card: Grade {grade} {card_name.title()}",
                        color=shipper1.colour,
                        timestamp=get_timestamp()
                    )
                    embed.set_author(name=f"Rewards collection", icon_url=shipper1.avatar_url)
                    embed.add_field(
                        name="Earnings per captain",
                        value=f"{adjusted_rewards_count}{emojify(rewards)}"
                    )
                    embed.set_thumbnail(url=link)
                    embed.set_footer(text=f"Level: {ship_data['level']}", icon_url=shipper2.avatar_url)
                except TypeError:
                    return

                if rewards != "experience":
                    users.update_one({"user_id": str(shipper1.id)}, {"$inc": {f"{rewards}": adjusted_rewards_count}})
                    await logs_add_line(f"{rewards}", adjusted_rewards_count, shipper1.id)

                    users.update_one({"user_id": str(shipper2.id)}, {"$inc": {f"{rewards}": adjusted_rewards_count}})
                    await logs_add_line(f"{rewards}", adjusted_rewards_count, shipper2.id)

                else:
                    def get_shikigami_display(u):
                        return users.find_one({"user_id": str(u.id)}, {"_id": 0, "display": 1})["display"]

                    users.update_one({
                        "user_id": str(shipper1.id),
                        "shikigami.name": get_shikigami_display(shipper1)
                    }, {
                        "$inc": {
                            "shikigami.exp": adjusted_rewards_count
                        }
                    })
                    users.update_one({
                        "user_id": str(shipper1.id),
                        "shikigami.name": get_shikigami_display(shipper2)
                    }, {
                        "$inc": {
                            "shikigami.exp": adjusted_rewards_count
                        }
                    })


                ships.update_one({"code": code}, {
                    "$set": {
                        "cards.equipped": False,
                        "cards.name": None,
                        "cards.grade": None,
                        "cards.timestamp": None,
                        "cards.collected": True
    
                    }
                })
                await ctx.channel.send(embed=embed)


def setup(client):
    client.add_cog(Realm(client))
