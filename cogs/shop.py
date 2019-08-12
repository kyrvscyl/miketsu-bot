"""
Shop Module
Miketsu, 2019
"""

import asyncio
import json
from datetime import datetime

import discord
import pytz
from discord.ext import commands

from cogs.mongo.database import get_collections
from cogs.startup import e_a, e_j, e_c, e_m, e_f, e_t, embed_color

# Collections
users = get_collections("miketsu", "users")
frames = get_collections("miketsu", "frames")

with open("data/shop.json") as f:
    shop_dict = json.load(f)

# Listings
purchasable_frames = []
trading_list = []
trading_list_formatted = []

for document in frames.find({"purchase": True}, {"_id": 1, "name": 1}):
    purchasable_frames.append(document["name"].lower())

print(purchasable_frames)

def get_emoji(item):
    emoji_dict = {
        "jades": e_j, "coins": e_c, "realm_ticket": "🎟", "amulets": e_a, "medals": e_m, "friendship": e_f,
        "encounter_ticket": "🎫", "talisman": e_t
    }
    return emoji_dict[item]


def get_time():
    tz_target = pytz.timezone("America/Atikokan")
    return datetime.now(tz=tz_target)


def get_timestamp():
    return datetime.utcfromtimestamp(datetime.timestamp(datetime.now()))


def get_offer_and_cost(x):
    with open("data/shop.json") as g:
        shop = json.load(g)

    _shop = shop[x[0]][x[1]]
    offer_item_ = _shop["offer"][0]
    offer_amount_ = _shop["offer"][1]
    cost_item_ = _shop["cost"][0]
    cost_amount_ = _shop["cost"][1]

    return offer_item_, offer_amount_, cost_item_, cost_amount_


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


class Economy(commands.Cog):

    def __init__(self, client):
        self.client = client

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


def setup(client):
    client.add_cog(Economy(client))
