"""
Funfun Module
Miketsu, 2020
"""
import asyncio
import random
import re
from itertools import cycle

from discord.ext import commands

from cogs.ext.initialize import *


class Funfun(commands.Cog):

    def __init__(self, client):
        self.client = client

        self.actions = []
        self.stickers_list = []

        self.shoots_failed = cycle(listings_3["failed_shoots"])
        self.shoots_success = cycle(listings_3["success_shoots"])
        self.reactions = cycle(listings_3["reactions"])

        self.generate_new_stickers()

    def generate_new_stickers(self):
        self.actions.clear()
        self.stickers_list.clear()

        for sticker in stickers.find({}, {"_id": 0}):
            self.stickers_list.append("`{}`, ".format(sticker["alias"]))
            self.actions.append(sticker["alias"])

    async def mike_how_hot(self, guild, channel, msg):
        msg_formatted = msg.lower().split(" ")
    
        for word in msg_formatted:
    
            if re.match(r"^<@![0-9]+>$", word) or re.match(r"^<@[0-9]+>$", word):
    
                user_id = re.sub("[<>@!]", "", word)
                random.seed(int(user_id))
                member = guild.get_member(int(user_id))
                r = random.randint(1, 100)
                hot = r / 1.17
    
                emoji = "💔"
                if hot > 25:
                    emoji = "❤"
                if hot > 50:
                    emoji = "💖"
                if hot > 75:
                    emoji = "💞"
    
                embed = discord.Embed(
                    color=member.colour,
                    title=f"**{member.display_name}** is **{hot:.2f}%** hot {emoji}"
                )
                await channel.send(embed=embed)
                break
    
    async def mikes_shoot_post_process(self, user, victim, winner, response, channel):
    
        if shoots.find_one({"user_id": str(user.id)}, {"_id": 0}) is None:
            profile = {
                "user_id": str(user.id),
                "victim": []
            }
            shoots.insert_one(profile)
    
        if shoots.find_one({"user_id": str(user.id), "victim.user_id": str(victim.id)}, {"_id": 0}) is None:
            shoots.update_one({
                "user_id": str(user.id)}, {
                "$push": {
                    "victim": {
                        "user_id": str(victim.id),
                        "successes": 0,
                        "fails": 0
                    }
                }
            })
    
        embed = discord.Embed(color=user.colour, description=f"*{response}*")
    
        if winner.id == user.id:
            increment = {"victim.$.successes": 1, "victim.$.fails": 0}
    
            shoots.update_one({
                "user_id": str(user.id), "victim.user_id": str(victim.id)}, {
                "$inc": increment
            }
            )
    
            query = shoots.find_one({
                "user_id": str(user.id), "victim.user_id": str(victim.id)}, {
                "_id": 0,
                "victim.$": 1
            })
            successes = query["victim"][0]["successes"]
            fails = query["victim"][0]["fails"]
    
            embed.set_footer(
                text=f"{successes}/{successes + fails} successful {pluralize('shooting', successes + fails)}",
                icon_url=user.avatar_url
            )
    
        else:
            increment = {"victim.$.successes": 0, "victim.$.fails": 1}
    
            shoots.update_one({
                "user_id": str(user.id), "victim.user_id": str(victim.id)}, {
                "$inc": increment
            }
            )
            query = shoots.find_one({
                "user_id": str(user.id), "victim.user_id": str(victim.id)}, {
                "_id": 0,
                "victim.$": 1
            })
            successes = query["victim"][0]["successes"]
            fails = query["victim"][0]["fails"]
    
            embed.set_footer(
                text=f"{fails}/{successes + fails} failed {pluralize('shooting', successes + fails)}",
                icon_url=user.avatar_url
            )
    
        await channel.send(embed=embed)
    
    async def mike_shoot(self, user, guild, channel, args):
        msg_formatted = args.lower().split(" ")

        for word in msg_formatted:

            if re.match(r"^<@![0-9]+>$", word) or re.match(r"^<@[0-9]+>$", word):

                user_id = re.sub("[<>@!]", "", word)
                member_target = guild.get_member(int(user_id))

                if member_target.id != self.client.user.id:
                    roll = random.randint(1, 100)

                    if roll >= 45:
                        response = next(self.shoots_failed).format(user.mention)
                        await self.mikes_shoot_post_process(user, member_target, member_target, response, channel)
                    else:
                        response = next(self.shoots_success).format(member_target.mention)
                        await self.mikes_shoot_post_process(user, member_target, user, response, channel)

                    break

    @commands.command(aliases=["sticker", "stickers"])
    @commands.guild_only()
    async def sticker_help(self, ctx):

        quotient = int(len(self.stickers_list) / 2)
        page = 1
        page_total = 2

        def check(r, u):
            return u != self.client.user and r.message.id == msg.id

        def generate_stickers_embed(y):

            end = y * quotient
            start = end - quotient
            description = "".join(sorted(self.stickers_list[start:end]))[:-2:]

            embed = discord.Embed(
                color=0xffe6a7, title="stickers",
                description="posts a reaction image embed\n"
                            "just add \"mike\" in your message + the `<alias>`"
            )
            embed.add_field(name="Aliases", value="*" + description + "*")
            embed.set_footer(text=f"Page {y}")
            return embed

        msg = await ctx.channel.send(embed=generate_stickers_embed(page))
        emoji_arrows = ["⬅", "➡"]
        for emoji in emoji_arrows:
            await process_msg_reaction_add(msg, emoji)

        while True:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=30, check=check)
            except asyncio.TimeoutError:
                await process_msg_reaction_clear(msg)
                break
            else:
                if str(reaction.emoji) == emoji_arrows[1]:
                    page += 1
                elif str(reaction.emoji) == emoji_arrows[0]:
                    page -= 1
                if page == 0:
                    page = page_total
                elif page > page_total:
                    page = 1
                await msg.edit(embed=generate_stickers_embed(page))

    @commands.command(aliases=["newsticker", "ns"])
    @commands.guild_only()
    async def sticker_add_new(self, ctx, arg1, *, args):

        alias = arg1.lower()
        link = args

        if alias in self.actions:
            embed = discord.Embed(color=ctx.author.colour, title=f"Alias `{alias}` is already taken", )
            await process_msg_submit(ctx.channel, None, embed)

        elif link[:20] == "https://i.imgur.com/" and link[-4:] == ".png":
            stickers.insert_one({"alias": alias, "link": link})
            embed = discord.Embed(color=ctx.author.colour, title=f"New sticker added with alias: `{alias}`")
            embed.set_image(url=link)
            await process_msg_submit(ctx.channel, None, embed)
            self.generate_new_stickers()

        else:
            await process_msg_reaction_add(ctx.message, "❌")

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author.bot:
            return

        elif isinstance(message.channel, discord.DMChannel):
            return

        elif "mike" in message.content.lower().split(" ") and len(message.content.lower().split(" ")) < 6:

            user = message.author
            list_message = message.content.lower().split()
            sticker_recognized = None

            for sticker_try in list_message:
                if sticker_try in self.actions:
                    sticker_recognized = sticker_try
                    break

            if sticker_recognized is None:

                try:
                    if len(message.content) == 4:
                        embed = discord.Embed(
                            colour=discord.Colour(0xffe6a7),
                            description=next(self.reactions)
                        )
                        msg = await message.channel.send(embed=embed)
                        await msg.delete(delay=15)
                        await message.delete(delay=15)

                    elif message.content.lower().split(" ", 2)[1] == "shoot":
                        await self.mike_shoot(message.author, message.guild, message.channel, message.content)

                    elif message.content.lower().split(" ", 1)[1][:7] == "how hot":
                        await self.mike_how_hot(message.guild, message.channel, message.content)

                except IndexError:
                    return

            else:
                x = users.update_one({
                    "user_id": str(user.id),
                    "stickers": {
                        "$lt": 21
                    },
                    "level": {
                        "$lt": 60
                    }
                }, {
                    "$inc": {
                        "experience": 20
                    }})
                sticker_url = stickers.find_one({"alias": sticker_recognized}, {"_id": 0, "link": 1})["link"]
                comment = " "
                if x.modified_count > 0:
                    comment = ", +20exp"
                    users.update_one({
                        "user_id": str(user.id)
                    }, {
                        "$inc": {
                            "stickers": 1
                        }
                    })

                embed = discord.Embed(color=user.colour)
                embed.set_footer(text=f"{user.display_name}{comment}", icon_url=user.avatar_url)
                embed.set_image(url=sticker_url)
                await message.channel.send(embed=embed)
                await message.delete()


def setup(client):
    client.add_cog(Funfun(client))
