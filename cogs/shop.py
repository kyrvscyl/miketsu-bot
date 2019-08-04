"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import asyncio
import json
from datetime import datetime

import discord
import pytz
from discord.ext import commands

from cogs.mongo.db import users, frames
from cogs.startup import emoji_a, emoji_j, emoji_c, emoji_m, emoji_f

purchasable_frames = []
for document in frames.find({"purchase": True}, {"_id": 1, "name": 1}):
    purchasable_frames.append(document["name"].lower())


def get_time():
    tz_target = pytz.timezone("America/Atikokan")
    return datetime.now(tz=tz_target)


def get_emoji(item):
    emoji_dict = {
        "jades": emoji_j,
        "coins": emoji_c,
        "realm_ticket": "🎟",
        "amulets": emoji_a,
        "medals": emoji_m,
        "friendship": emoji_f,
        "encounter_ticket": "🎫"
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

trading_value_list = []
for key in shop_dict:

    for key2 in shop_dict[key]:
        _offer_item = shop_dict[key][key2]["offer"][0]
        _offer_amount = shop_dict[key][key2]["offer"][1]
        _cost_item = shop_dict[key][key2]["cost"][0]
        _cost_amount = shop_dict[key][key2]["cost"][1]
        trading_value_list.append(
            f"• `{_offer_amount}` {get_emoji(_offer_item)} ` "
            f"for ` `{_cost_amount:,d}` {get_emoji(_cost_item)} "
            f"| `{key} {key2}`\n"
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
            title="Confirmation receipt", colour=discord.Colour(0xffe6a7),
            description=f"{user.mention} acquired {offer_amount:,d}{get_emoji(offer_item)} "
                        f"in exchanged for {cost_amount:,d}{get_emoji(cost_item)}"
        )
        await ctx.channel.send(embed=embed)

    else:
        embed = discord.Embed(
            title="Purchase failure", colour=discord.Colour(0xffe6a7),
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
            title="Confirmation receipt", colour=discord.Colour(0xffe6a7),
            description=f"{user.mention} acquired {emoji} {frame_name} "
                        f"in exchanged for {amount:,d}{get_emoji(currency)}"
        )
        await ctx.channel.send(embed=embed)

    else:
        embed = discord.Embed(
            title="Purchase failure", colour=discord.Colour(0xffe6a7),
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
            title="Mystic Trader", colour=discord.Colour(0xffe6a7),
            description="exchange various economy items"
        )
        embed.set_thumbnail(url="https://vignette.wikia.nocookie.net/onmyoji/images/8/86/246a.jpg")
        embed.add_field(
            inline=False,
            name="Trading List",
            value="".join(trading_value_list)
        )
        embed.add_field(name="Example", value="*`;buy amulets 11`*", inline=False)
        await ctx.channel.send(embed=embed)

    @commands.command(aliases=["buy"])
    @commands.guild_only()
    async def shop_buy_items(self, ctx, *args):

        user = ctx.author
        embed = discord.Embed(title="confirm purchase?", color=ctx.author.colour)

        if len(args) == 0:
            embed = discord.Embed(
                title="buy", colour=discord.Colour(0xffe6a7),
                description="purchase from the list of items from the *`;shop`*\nreact to confirm purchase")
            embed.add_field(name="Format", value="*`;buy <item> <amount>`*")
            await ctx.channel.send(embed=embed)

        elif args[0].lower() in ["frame", "frames"] and len(args) == 1:

            embed = discord.Embed(
                title="AkiraKL's Frame Shop", colour=discord.Colour(0xffe6a7),
                description="purchase premium frames for premium prices"
            )

            for frame in frames.find({"purchase": True}, {"_id": 0, "currency": 1, "amount": 1, "name": 1, "emoji": 1}):
                embed.add_field(
                    name=f"{frame['emoji']} {frame['name']}",
                    value=f"Acquire for {frame['amount']:,d}{get_emoji(frame['currency'])}"
                )

            embed.add_field(
                name=f"Format",
                value="*`;buy frame <frame_name>`*",
                inline=False
            )

            await ctx.channel.send(embed=embed)
            return

        elif args[0].lower() in ["frame", "frames"] \
                and len(args) > 1 and " ".join(args[-2:]).lower() in \
                purchasable_frames:

            frame = " ".join(args[-2:]).lower()
            request = frames.find_one({"name": frame.title()}, {"_id": 0})
            emoji = request["emoji"]
            currency = request["currency"]
            amount = request["amount"]

            embed.description = \
                f"{emoji} {frame.title()} frame for `{amount:,d}` {get_emoji(currency)}"

            msg = await ctx.channel.send(embed=embed)
            await msg.add_reaction("✅")
            answer = await self.shop_buy_confirmation(ctx, msg)

            if answer is True:
                await shop_process_purchase_frame(ctx, user, currency, amount, frame.title(), emoji)

        elif len(args) == 1:
            embed = discord.Embed(
                title="buy", colour=discord.Colour(0xffe6a7),
                description="buy items from the mystic trader"
            )
            embed.add_field(
                name=f"Arguments",
                value="*amulets, frames, enc, raid, medals*",
                inline=False
            )
            embed.add_field(
                name=f"Example",
                value="*`;buy frames`*",
                inline=False
            )
            await ctx.channel.send(embed=embed)

        else:
            try:
                offer_item, offer_amount, cost_item, cost_amount = get_offer_and_cost(args)
                embed.description = \
                    f"`{offer_amount}` {get_emoji(offer_item)} `for` `{cost_amount:,d}` {get_emoji(cost_item)}"

                msg = await ctx.channel.send(embed=embed)
                await msg.add_reaction("✅")
                answer = await self.shop_buy_confirmation(ctx, msg)

                if answer is True:
                    await shop_process_purchase(user, ctx, offer_item, offer_amount, cost_item, cost_amount)

            except KeyError:
                embed = discord.Embed(
                    title="Invalid purchase code", colour=discord.Colour(0xffe6a7),
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
                title="Timeout!", colour=discord.Colour(0xffe6a7),
                description=f"{ctx.author.mention}, you did not confirm the purchase"
            )
            await ctx.channel.send(embed=embed)
            return False
        else:
            return True


def setup(client):
    client.add_cog(Economy(client))
