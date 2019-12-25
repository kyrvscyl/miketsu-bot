"""
Error Module
Miketsu, 2019
"""
import asyncio
import os
import random
from datetime import datetime, timedelta
from math import exp, ceil

import discord
import pytz
from discord.ext import commands, tasks

from cogs.mongo.database import get_collections

# Collections
config = get_collections("config")
guilds = get_collections("guilds")
logs = get_collections("logs")
realms = get_collections("realms")
ships = get_collections("ships")
users = get_collections("users")

# Instantiations
id_guild = int(os.environ.get("SERVER"))


class Beta(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.prefix = self.client.command_prefix

        self.colour = config.find_one({"var": 1}, {"_id": 0, "embed_color": 1})["embed_color"]
        self.timezone = config.find_one({"var": 1}, {"_id": 0, "timezone": 1})["timezone"]

        self.get_emojis = config.find_one({"dict": 1}, {"_id": 0, "get_emojis": 1})["get_emojis"]
        
        self.channels = guilds.find_one({"server": str(id_guild)}, {"_id": 0, "channels": 1})
        
        self.id_scroll = self.channels["channels"]["scroll-of-everything"]
        self.id_spell_spam = self.channels["channels"]["spell-spam"]

        self.cards_realm = config.find_one({"dict": 1}, {"_id": 0, "cards_realm": 1})["cards_realm"]

        self.realm_cards = []

        for card in realms.find({}, {"_id": 0}):
            self.realm_cards.append(f"{card['name'].lower()}")

    def get_bond(self, x, y):
        bond_list = sorted([x, y], reverse=True)
        return f"{bond_list[0]}x{bond_list[1]}"

    def get_emoji(self, item):
        return self.get_emojis[item]

    def get_emoji_cards(self, x):
        return self.cards_realm[x]

    def get_time(self):
        return datetime.now(tz=pytz.timezone(self.timezone))
    
    def get_timestamp(self):
        return datetime.utcfromtimestamp(datetime.timestamp(datetime.now()))
    
    def get_time_converted(self, utc_dt):
        return utc_dt.replace(tzinfo=pytz.timezone("UTC")).astimezone(tz=pytz.timezone(self.timezone))

    def pluralize(self, singular, count):
        if count > 1:
            if singular[-1:] == "s":
                return singular + "es"
            return singular + "s"
        else:
            return singular

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

    @commands.Cog.listener()
    async def on_ready(self):
        self.sushi_bento_increment.start()

    @tasks.loop(minutes=4)
    async def sushi_bento_increment(self):

        users.update_many({"bento": {"$lt": 360}}, {"$inc": {"bento": 1}})

    @commands.command(aliases=["bento"])
    @commands.guild_only()
    async def sushi_bento(self, ctx):

        query = users.find_one({"user_id": str(ctx.author.id)}, {"_id": 0, "bento": 1})
        reserves = query["bento"]

        def embed_new_create(strike):
            embed_new = discord.Embed(
                description=f"{strike}You currently have `{reserves:,d}`{self.get_emoji('sushi')} "
                            f"in your reserve{strike}",
                color=self.colour,
                timestamp=self.get_timestamp()
            )
            embed_new.set_footer(
                text=f"{ctx.author.display_name}",
                icon_url=ctx.author.avatar_url
            )
            return embed_new

        msg = await ctx.channel.send(embed=embed_new_create(""))
        await msg.add_reaction("🍽️")

        def check(r, u):
            return u != self.client.user and r.message.id == msg.id and str(r.emoji) == "🍽️" and u.id == ctx.author.id

        while True:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=60, check=check)
            except asyncio.TimeoutError:
                await msg.clear_reactions()
                break
            else:
                users.update_one({"user_id": str(user.id)}, {"$inc": {"sushi": reserves, "bento": -reserves}})
                await msg.edit(embed=embed_new_create("~~"))
                await self.perform_add_log("sushi", reserves, user.id)
                await msg.clear_reactions()

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
                title="realms, rlms",
                description="equip cards with your ships to obtained shared rewards",
                color=self.colour
            )

            def generate_data():
                values, data = [], cards_listing[page_new - 1]

                for y in range(1, 7):
                    rewards = int(data[2] * exp(0.3868 * y))
                    values.append(
                        f"{self.get_emoji_cards(data[0])}`Grade {y}` :: `~ {rewards:,d}`{self.get_emoji(data[1])}\n"
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

    @commands.command(aliases=["cards"])
    @commands.guild_only()
    async def realm_card_show_user(self, ctx, *, member: discord.Member = None):

        if member is None:
            await self.realm_card_show_user_post(ctx.author, ctx)

        else:
            await self.realm_card_show_user_post(member, ctx)

    async def realm_card_show_user_post(self, member, ctx):

        cards = users.find_one({"user_id": str(member.id)}, {"_id": 0, "cards": 1})["cards"]
        list_formatted = []

        for c in cards:
            list_formatted.append(f"{self.get_emoji_cards(c['name'])} {c['name'].title()} | Grade `{c['grade']} 🌟`\n")

        await self.realm_card_show_user_post_paginate(ctx, list_formatted)

    async def realm_card_show_user_post_paginate(self, ctx, list_formatted):

        page, lines_max = 1, 10
        page_total = ceil(len(list_formatted) / lines_max)
        if page_total == 0:
            page_total = 1

        def embed_create_page_new(page_new):
            end = page_new * lines_max
            start = end - lines_max
            description_new = "".join(list_formatted[start:end])

            embed_new = discord.Embed(
                color=ctx.author.colour,
                description=f"{description_new}", timestamp=self.get_timestamp()
            )
            embed_new.set_author(name=f"{ctx.author.display_name}'s realm cards", icon_url=ctx.author.avatar_url)
            embed_new.set_footer(text=f"Page: {page_new} of {page_total}")
            return embed_new

        msg = await ctx.channel.send(embed=embed_create_page_new(page))
        await msg.add_reaction("⬅")
        await msg.add_reaction("➡")

        def check(r, u):
            return u != self.client.user and r.message.id == msg.id

        while True:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=180, check=check)
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
                await msg.edit(embed=embed_create_page_new(page))

    @commands.command(aliases=["realm", "rlm"])
    @commands.guild_only()
    async def realm_card_use(self, ctx, arg1=None, *, member: discord.Member = None):

        if arg1 is None and member is None:
            embed = discord.Embed(
                color=self.colour,
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

            code = self.get_bond(ctx.author.id, member.id)
            ship_data = ships.find_one({"code": code}, {"_id": 0})

            if ship_data is not None:

                if ship_data["cards"]["equipped"] is True:
                    return

                elif ship_data["cards"]["equipped"] is False:

                    user_cards = []
                    for x in users.find_one({"user_id": str(ctx.author.id)}, {"_id": 0, "cards": 1})["cards"]:
                        user_cards.append(f"{x['name']}/{x['grade']}")

                    embed = discord.Embed(
                        color=self.colour,
                        title="Realm card selection",
                        description=f"enter a valid realm card and grade"
                    )
                    embed.add_field(
                        name="Available cards",
                        value=f"*{', '.join(user_cards)}*",
                        inline=False
                    )
                    await ctx.channel.send(embed=embed)

                    def check(m):
                        return m.content.lower() in user_cards and m.author.id == ctx.author.id

                    try:
                        select = await self.client.wait_for("message", timeout=60, check=check)
                    except asyncio.TimeoutError:
                        return
                    else:
                        select_formatted = select.content.lower().split("/")
                        ships.update_one({
                            "code": code
                        }, {
                            "$set": {
                                "cards.equipped": True,
                                "cards.name": select_formatted[0],
                                "cards.grade": int(select_formatted[1]),
                                "cards.timestamp": self.get_time(),
                                "cards.collected": False
                            }
                        })
                        users.update({
                            'user_id': str(ctx.author.id),
                            'cards': {
                                '$elemMatch': {
                                    'name': select_formatted[0],
                                    'grade': int(select_formatted[1])
                                }
                            }
                        }, {
                            "$pull": {
                                "cards": {
                                    'name': select_formatted[0],
                                    'grade': int(select_formatted[1])
                                }
                            }
                        })
                        await select.add_reaction("✅")

    @commands.command(aliases=["rcollect", "rcol"])
    @commands.guild_only()
    async def realm_card_collect_rewards(self, ctx, *, member: discord.Member = None):

        try:
            code = self.get_bond(ctx.author.id, member.id)
            ship_data = ships.find_one({"code": code}, {"_id": 0})
        except AttributeError:
            embed = discord.Embed(
                colour=self.colour,
                title="rcollect, rcol",
                description=f"collect your cruising rewards"
            )
            embed.add_field(
                name="Format",
                value=f"*{self.prefix}rcollect <@member>*"
            )
            await ctx.channel.send(embed=embed)
            return
        except TypeError:
            embed = discord.Embed(
                colour=self.colour,
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
                colour=self.colour,
                title="Invalid ship",
                description=f"that ship has sunk before it was even fully built"
            )
            await ctx.channel.send(embed=embed)

        elif ship_data["cards"]["collected"] is True or ship_data["cards"]["equipped"] is False:
            embed = discord.Embed(
                colour=self.colour,
                title="Invalid collection",
                description=f"the ship has not yet been deployed for cruise"
            )
            await ctx.channel.send(embed=embed)

        elif ship_data["cards"]["collected"] is False and ship_data["cards"]["equipped"] is True:

            card_name = ship_data["cards"]["name"]
            time_deployed = self.get_time_converted(ship_data["cards"]["timestamp"])
            now = datetime.now(tz=pytz.timezone("UTC"))

            if now < (time_deployed + timedelta(days=1)):
                embed = discord.Embed(
                    colour=self.colour,
                    title="Invalid collection",
                    description=f"the ship has not yet returned from its cruise"
                )
                await ctx.channel.send(embed=embed)

            elif now >= (time_deployed + timedelta(days=1)):
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
                                    f"Card: {self.get_emoji_cards(card_name)}`Grade {grade}` {card_name.title()}",
                        color=shipper1.colour,
                        timestamp=self.get_timestamp()
                    )
                    embed.set_author(name=f"Cruise rewards", icon_url=shipper1.avatar_url)
                    embed.add_field(
                        name="Earnings per captain",
                        value=f"{adjusted_rewards_count:,d}{self.get_emoji(rewards)}"
                    )
                    embed.set_thumbnail(url=link)
                    embed.set_footer(text=f"Ship Level: {ship_data['level']}", icon_url=shipper2.avatar_url)
                except TypeError:
                    return

                if rewards != "experience":
                    users.update_one({"user_id": str(shipper1.id)}, {"$inc": {f"{rewards}": adjusted_rewards_count}})
                    await self.perform_add_log(f"{rewards}", adjusted_rewards_count, shipper1.id)

                    users.update_one({"user_id": str(shipper2.id)}, {"$inc": {f"{rewards}": adjusted_rewards_count}})
                    await self.perform_add_log(f"{rewards}", adjusted_rewards_count, shipper2.id)

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

    @commands.command(aliases=["raidable"])
    @commands.guild_only()
    async def raid_perform_check_users(self, ctx):

        query = users.find({"raided_count": {"$lt": 3}}, {"_id": 0, "user_id": 1, "level": 1, "raided_count": 1})

        list_raw = []
        list_formatted = []

        for user in query:
            try:
                member_name = self.client.get_user(int(user["user_id"]))
                list_raw.append((member_name, user["level"], user["raided_count"]))
            except AttributeError:
                continue

        for user in sorted(list_raw, key=lambda x: x[1], reverse=True):
            list_formatted.append(f"• {user[0]}, `lvl.{user[1]:,d}`, `{user[2]}/3`\n")

        await self.raid_perform_check_users_paginate("Available Realms", ctx, list_formatted)

    async def raid_perform_check_users_paginate(self, title, ctx, formatted_list):

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


def setup(client):
    client.add_cog(Beta(client))
