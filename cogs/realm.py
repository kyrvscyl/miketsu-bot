"""
Realm Module
"Miketsu, 2021
"""

from datetime import timedelta

from discord.ext import commands

from cogs.ext.initialize import *


class Realm(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.prefix = self.client.command_prefix

    @commands.command(aliases=["realms"])
    @commands.guild_only()
    async def realm_card_show_all(self, ctx):

        page, page_total = 1, len(listings_cards)

        def embed_new_create(page_new):

            embed_new = discord.Embed(
                title="realms", color=colour,
                description="equip cards with your ships to obtained shared rewards"
            )

            def realm_data_generate():
                field_value = []
                card_details = listings_cards[page_new - 1]
                name = card_details[0]
                reward = card_details[1]

                for y in range(1, 7):
                    rewards = int(card_details[2] * exp(0.3868 * y))
                    field_value.append(f"`Grade {y} 🌟` :: {get_emoji(reward)}`~ +{rewards:,d}`\n")

                embed_new.set_thumbnail(url=card_details[3])
                embed_new.add_field(
                    name=f"{get_emoji_cards(name)} {name.title()} card",
                    value=f"{' '.join(field_value)}"
                )
                embed_new.set_footer(text=f"Page: {page_new} of {len(listings_cards)}")

            realm_data_generate()
            return embed_new

        msg = await process_msg_submit(ctx.channel, None, embed_new_create(1))

        emojis_add = ["⬅", "➡"]
        for emoji in emojis_add:
            await process_msg_reaction_add(msg, emoji)

        def check(r, u):
            return msg.id == r.message.id and str(r.emoji) in emojis_add and u.id == ctx.author.id

        while True:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=60, check=check)
            except asyncio.TimeoutError:
                await process_msg_reaction_clear(msg)
                break
            else:
                if str(reaction.emoji) == emojis_add[1]:
                    page += 1
                elif str(reaction.emoji) == emojis_add[0]:
                    page -= 1
                if page == 0:
                    page = page_total
                elif page > page_total:
                    page = 1
                await process_msg_edit(msg, None, embed_new_create(page))

    @commands.command(aliases=["cards"])
    @commands.guild_only()
    async def realm_card_show_user(self, ctx, *, member: discord.Member = None):

        if member is None:
            await self.realm_card_show_user_post(ctx.author, ctx)

        else:
            try:
                member.id
            except AttributeError:
                await process_msg_invalid_member(ctx)
            else:
                await self.realm_card_show_user_post(member, ctx)

    async def realm_card_show_user_post(self, member, ctx):

        listings_cards_user = users.find_one({"user_id": str(member.id)}, {"_id": 0, "cards": 1})["cards"]
        listings_cards_user_formatted = []

        for d in sorted(listings_cards_user, key=lambda x: x['grade'], reverse=True):
            if d['count'] > 0:
                listings_cards_user_formatted.append(
                    f"`[x{d['count']}]` Grade `{d['grade']} 🌟` | {get_emoji_cards(d['name'])} {d['name'].title()}\n"
                )
        await self.realm_card_show_user_post_paginate(ctx, member, listings_cards_user_formatted)

    async def realm_card_show_user_post_paginate(self, ctx, member, list_formatted):

        page, lines_max = 1, 10
        page_total = ceil(len(list_formatted) / lines_max)
        if page_total == 0:
            page_total = 1

        def embed_new_create(page_new):
            end = page_new * lines_max
            start = end - lines_max
            description = "".join(list_formatted[start:end])

            embed_new = discord.Embed(color=member.colour, timestamp=get_timestamp(), description=f"{description}")
            embed_new.set_author(name=f"{member.display_name}'s realm cards", icon_url=member..avatar.url)
            embed_new.set_footer(text=f"Page: {page_new} of {page_total}")
            return embed_new

        msg = await process_msg_submit(ctx.channel, None, embed_new_create(page))

        emojis_add = ["⬅", "➡"]
        for emoji in emojis_add:
            await process_msg_reaction_add(msg, emoji)

        def check(r, u):
            return msg.id == r.message.id and str(r.emoji) in emojis_add and u.id == ctx.author.id

        while True:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=60, check=check)
            except asyncio.TimeoutError:
                await process_msg_reaction_clear(msg)
                break
            else:
                if str(reaction.emoji) == emojis_add[1]:
                    page += 1
                elif str(reaction.emoji) == emojis_add[0]:
                    page -= 1
                if page == 0:
                    page = page_total
                elif page > page_total:
                    page = 1
                await process_msg_edit(msg, None, embed_new_create(page))
                await process_msg_reaction_remove(msg, str(reaction.emoji), user)

    async def realm_card_use_help(self, ctx):

        embed = discord.Embed(
            color=colour, title="card, c",
            description=f"equip your ship with cards to obtain rewards"
        )
        embed.add_field(name="Formats", value=f"*`{self.prefix}card use <@member>`*\n")
        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["card", "c"])
    @commands.guild_only()
    async def realm_card_use(self, ctx, arg1=None, *, member: discord.Member = None):

        if arg1 is None and member is None:
            await self.realm_card_use_help(ctx)

        elif arg1.lower() in ["use", "u"] and member is None:
            await self.realm_card_use_help(ctx)

        elif arg1.lower() in ["use", "u"] and member is not None:

            user = ctx.author

            try:
                code = get_bond(user.id, member.id)
            except AttributeError:
                await process_msg_invalid_member(ctx)
            else:
                ship_data = ships.find_one({"code": code}, {"_id": 0})

                if ship_data is None:
                    embed = discord.Embed(
                        colour=user.colour, title="Invalid ship", timestamp=get_timestamp(),
                        description=f"That ship has sunk before it was even fully built"
                    )
                    await process_msg_submit(ctx.channel, None, embed)

                elif ship_data is not None:

                    if ship_data["cards"]["equipped"] is True:
                        await process_msg_reaction_add(ctx.message, "🛳")

                    elif ship_data["cards"]["equipped"] is False:
                        user_cards, user_cards_description = [], []

                        for d in users.find_one({"user_id": str(user.id)}, {"_id": 0, "cards": 1})["cards"]:
                            if d["count"] > 0:
                                user_cards.append(f"{d['name']}/{d['grade']}")
                                user_cards_description.append(f"{d['name']}/{d['grade']} [x{d['count']}]")

                        embed = discord.Embed(
                            color=user.colour, title="Realm card selection", timestamp=get_timestamp(),
                            description=f"enter a valid realm card and grade (ex. moon/4)"
                        )
                        embed.add_field(name="Available cards", value=f"*{', '.join(user_cards_description[:25])}*")
                        await process_msg_submit(ctx.channel, None, embed)

                        def check(m):
                            return m.content.lower() in user_cards and m.author.id == user.id

                        try:
                            message = await self.client.wait_for("message", timeout=60, check=check)
                        except asyncio.TimeoutError:
                            return
                        else:
                            name_grade = message.content.lower().split("/")
                            name, grade = name_grade[0], int(name_grade[1])

                            ships.update_one({
                                "code": code
                            }, {
                                "$set": {
                                    "cards.equipped": True, "cards.name": name, "cards.grade": grade,
                                    "cards.timestamp": get_time(), "cards.collected": False
                                }
                            })

                            users.update_one({
                                "user_id": str(user.id),
                                "cards": {"$elemMatch": {"name": name, "grade": grade}}
                            }, {
                                "$inc": {"cards.$.count": -1}
                            })
                            await process_msg_reaction_add(message, "✅")

    async def realm_card_collect_help(self, ctx):

        embed = discord.Embed(
            colour=colour, title="rcollect, rcol", description=f"collect your cruise rewards"
        )
        embed.add_field(name="Format", value=f"*`{self.prefix}rcollect <@member>`*")
        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["rcollect", "rcol"])
    @commands.guild_only()
    async def realm_card_collect(self, ctx, *, member: discord.Member = None):

        user = ctx.author

        try:
            code = get_bond(user.id, member.id)
        except (AttributeError, TypeError, commands.BadArgument):
            await self.realm_card_collect_help(ctx)
        else:
            ship_data = ships.find_one({"code": code}, {"_id": 0})

            if ship_data is None:
                embed = discord.Embed(
                    colour=user.colour, title="Invalid ship", timestamp=get_timestamp(),
                    description=f"That ship has sunk before it was even fully built"
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif ship_data["cards"]["collected"] is True or ship_data["cards"]["equipped"] is False:
                embed = discord.Embed(
                    colour=user.colour, title="Invalid collection", timestamp=get_timestamp(),
                    description=f"The ship has not yet been deployed for cruise"
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif ship_data["cards"]["collected"] is False and ship_data["cards"]["equipped"] is True:

                card_name = ship_data["cards"]["name"]
                time_deployed = get_time_converted(ship_data["cards"]["timestamp"])
                now = datetime.now(tz=pytz.timezone("UTC"))
                delta = time_deployed + timedelta(days=1)

                if now < delta:
                    embed = discord.Embed(
                        colour=user.colour, title="Invalid collection", timestamp=get_timestamp(),
                        description=f"The ship has not yet returned from its cruise"
                    )
                    await process_msg_submit(ctx.channel, None, embed)

                elif now >= delta:
                    card_data = realms.find_one({"name": card_name}, {"_id": 0})

                    rewards, base = card_data["rewards"], card_data["base"]
                    grade, level = ship_data["cards"]["grade"], int(ship_data['level'])
                    link = card_data["link"][str(grade)]

                    shipper1 = ctx.guild.get_member(int(ship_data["shipper1"]))
                    shipper2 = ctx.guild.get_member(int(ship_data["shipper2"]))

                    multiplier = 0.0375 * level + 0.9625
                    rewards_count = int((base * exp(0.3868 * grade)) * multiplier)
                    rewards_count_adj = int(random.uniform(rewards_count * 0.95, rewards_count * 1.05))

                    try:
                        shipper1_mention = shipper1.mention
                        shipper2_mention = shipper2.mention
                    except AttributeError:
                        return

                    embed = discord.Embed(
                        color=shipper1.colour, timestamp=get_timestamp(),
                        description=f"Captains {shipper1_mention} x {shipper2_mention}\n"
                                    f"Cruise: {ship_data['ship_name']}\n"
                                    f"Card: {get_emoji_cards(card_name)} `Grade {grade}` {card_name.title()}",
                    )
                    embed.set_author(name=f"Cruise rewards", icon_url=shipper1..avatar.url)
                    embed.add_field(
                        name="Earnings per captain",
                        value=f"{rewards_count_adj:,d}{get_emoji(rewards)}"
                    )
                    embed.set_thumbnail(url=link)
                    embed.set_footer(
                        text=f"Ship Level: {ship_data['level']} | Multiplier: {multiplier}",
                        icon_url=shipper2..avatar.url
                    )

                    if rewards != "experience":
                        users.update_one({"user_id": str(shipper1.id)}, {"$inc": {rewards: rewards_count_adj}})
                        await perform_add_log(rewards, rewards_count_adj, shipper1.id)

                        users.update_one({"user_id": str(shipper2.id)}, {"$inc": {rewards: rewards_count_adj}})
                        await perform_add_log(rewards, rewards_count_adj, shipper2.id)

                    else:
                        users.update_one({
                            "user_id": str(shipper1.id),
                            "shikigami.name": get_shikigami_display(shipper1)
                        }, {
                            "$inc": {
                                "shikigami.$.exp": rewards_count_adj
                            }
                        })
                        users.update_one({
                            "user_id": str(shipper2.id),
                            "shikigami.name": get_shikigami_display(shipper2)
                        }, {
                            "$inc": {
                                "shikigami.$.exp": rewards_count_adj
                            }
                        })

                    ships.update_one({"code": code}, {
                        "$set": {
                            "cards.equipped": False, "cards.name": None, "cards.grade": None,
                            "cards.timestamp": None, "cards.collected": True
                        }
                    })
                    await process_msg_submit(ctx.channel, None, embed)


def setup(client):
    client.add_cog(Realm(client))
