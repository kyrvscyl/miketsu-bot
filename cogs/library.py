"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import urllib.request

import discord
import pytz
from discord.ext import commands

from cogs.mongo.db import library, users, daily
from discord_webhook import DiscordWebhook, DiscordEmbed

# Timezone
tz_target = pytz.timezone("America/Atikokan")

# Global variable
lists_souls = []
lists_souls_raw = []
for soul in library.find({"section": "sbs", "index": {"$nin": ["1", "2"]}}, {"_id": 0, "index": 1}):
    lists_souls.append("`{}`".format(soul["index"].lower()))
    lists_souls_raw.append(soul["index"].lower())


async def post_process_books(user, ctx, query):
    library.update_one(query, {"$inc": {"borrows": 1}})
    profile = daily.find_one({"key": "library", f"{user.id}": {"$type": "int"}}, {"_id": 0, f"{user.id}": 1})

    if profile[f"{user.id}"] <= 3:
        users.update_one({"user_id": str(user.id)}, {"$inc": {"experience": 50}})
        daily.update_one({
            "key": "library"}, {
            "$inc": {
                f"{user.id}": 1
            }
        })
    await ctx.message.delete()


def check_if_reference_section(ctx):
    return ctx.channel.name == "reference-section"


class Library(commands.Cog):

    def __init__(self, client):
        self.client = client

    def create_webhook_post(self, webhooks, book):

        bukkuman = webhooks[0]
        webhook = DiscordWebhook(
            content=book['content'],
            url=bukkuman.url,
            avatar_url="https://i.imgur.com/5FflHQ5.jpg",
            username="Professor Bukkuman"
        )

        def generate_embed_value_1(dictionary, key):
            try:
                value = dictionary[key]
            except KeyError:
                value = None
            return value

        try:
            for entry in book["embeds"]:
                embed = DiscordEmbed(
                    title=generate_embed_value_1(entry, "title"),
                    description=generate_embed_value_1(entry, "description"),
                    color=generate_embed_value_1(entry, "color"),
                )

                try:
                    embed.set_thumbnail(url=generate_embed_value_1(entry, "thumbnail")["url"])
                except TypeError:
                    pass

                try:
                    embed.set_image(url=generate_embed_value_1(entry, "image")["url"])
                except TypeError:
                    pass

                try:
                    for field in entry["fields"]:
                        embed.add_embed_field(
                            name=field["name"],
                            value=field["value"],
                            inline=False
                        )
                except KeyError:
                    pass

                try:
                    user_id = generate_embed_value_1(entry, "footer")["text"]
                    user = self.client.get_user(int(user_id))
                    embed.set_footer(
                        text=f"Guide by {user.name}",
                        icon_url=str(user.avatar_url_as(format="jpg", size=128))
                    )
                except TypeError:
                    pass
                except AttributeError:
                    pass

                webhook.add_embed(embed)

        except KeyError:
            pass

        return webhook

    @commands.command(aliases=["toc", "table"])
    @commands.check(check_if_reference_section)
    async def post_table_of_content(self, ctx):

        await ctx.message.delete()
        webhooks = await ctx.channel.webhooks()
        bukkuman = webhooks[0]
        webhook = DiscordWebhook(url=bukkuman.url, avatar_url="https://i.imgur.com/5FflHQ5.jpg")

        lists_souls_formatted = ", ".join(lists_souls)
        description = \
            "• To open a book use `;open [section] [index]`\n" \
            "• Example: `;open sbs 3`"

        embed = DiscordEmbed(
            title=":bookmark: Table of Magical Contents",
            colour=discord.Colour(0xa0c29a),
            description=description
        )
        embed.add_embed_field(
            name=":book: The Standard Book of Souls - Year 1 `[SBS]`",
            value="{}".format(lists_souls_formatted)
        )
        embed.add_embed_field(
            name=":book: The Standard Book of Souls - Year 5 `[SBS]`",
            value="• `[1]` Souls 10 Speed Run (24-25s)\n"
                  "• `[2]` Souls 10 Speed Run (20-21s)\n"
                  "• `[3]` Souls Moan Team Varieties"
        )
        embed.add_embed_field(
            name=":closed_book: Secret Duelling Books `[SDB]`",
            value="• `[1]` Curses & Counter-Curses by zu(IA)uz - Book 1\n"
                  "• `[2]` Curses & Counter-Curses by zu(IA)uz - Book 1\n"
                  "• `[3]` What if by Quinlynn - Book 1\n"
                  "• `[4]` What if by Quinlynn - Book 2"
        )
        embed.add_embed_field(
            name=":books: Assorted Books `[AB]`",
            value="• `[1]` Advanced Realm-Making\n"
                  "• `[2]` A Beginner's Guide to Shikigami Affection\n"
                  "• `[3]` Predicting the Unpredictable: Summon Odds\n"
                  "• `[4]` Spellman's Syllabary: Contractions"
        )
        embed.set_footer(
            text="grants 50 exp per book opened (max of 150/day)"
        )
        webhook.add_embed(embed)
        webhook.execute()

    @commands.command(aliases=["open"])
    @commands.check(check_if_reference_section)
    async def post_book(self, ctx, arg1, *, args):

        webhooks = await ctx.channel.webhooks()
        user = ctx.message.author
        query = {"section": arg1.lower(), "index": args.lower()}
        book = library.find_one(query, {"_id": 0})


        if arg1.lower() in ["ab", "sbs"] and args.lower() in ["3"]:

            opener = urllib.request.build_opener()
            opener.addheaders = [('User-agent', 'Mozilla/5.0')]
            urllib.request.install_opener(opener)
            urllib.request.urlretrieve(book["attachment"], book["address"])

            file = discord.File(book["address"], filename=book["filename"])
            contributor = self.client.get_user(int(book["contributor"]))
            await ctx.channel.send(
                content=f"{book['content']} {contributor}",
                file=file
            )
            await post_process_books(user, ctx, query)

        elif arg1.lower() in ["sbs", "sdb", "ab"] and \
                (args.lower() in lists_souls_raw or args.lower() in ["1", "2", "4"]):

            webhook = self.create_webhook_post(webhooks, book)
            webhook.execute()
            # await post_process_books(user, ctx, query)


def setup(client):
    client.add_cog(Library(client))
