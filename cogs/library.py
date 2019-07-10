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
for soul in library.find({"book": "souls"}, {"_id": 0, "title": 1}):
    lists_souls.append("`{}`".format(soul["title"].lower()))
    lists_souls_raw.append(soul["title"].lower())


# noinspection PyShadowingNames
def check_if_none(embedding, parameter):
    try:
        value = embedding[parameter]
        return value
    except KeyError:
        return None


async def post_process_books(user, ctx):

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


class Library(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(aliases=["table"])
    async def post_table_of_content(self, ctx):

        webhooks = await ctx.channel.webhooks()
        bukkuman = webhooks[0]
        webhook = DiscordWebhook(url=bukkuman.url, avatar_url="https://i.imgur.com/5FflHQ5.jpg")

        lists_souls_formatted = ", ".join(lists_souls)
        description = \
            "• To open a book use `;open [field] [value]`\n" \
            "• Example: `;open ab 3`"

        embed = DiscordEmbed(
            title=":bookmark: Table of Magical Contents",
            colour=discord.Colour(0xa0c29a),
            description=description
        )
        embed.add_embed_field(
            name=":book: The Standard Book of Souls - Year 1 `[s1]`",
            value="{}".format(lists_souls_formatted)
        )
        embed.add_embed_field(
            name=":book: The Standard Book of Souls - Year 5 `[s5]`",
            value="• `[25]` Souls 10 Speed run (24-25s)\n"
                  "• `[21]` Souls 10 Speed run (20-21s)"
        )
        embed.add_embed_field(
            name=":books: Assorted Books `[ab]`",
            value="• `[1]` Advanced Realm-Making\n"
                  "• `[2]` A Beginner's Guide to Shikigami Affection\n"
                  "• `[3]` Predicting the Unpredictable: Summon Odds\n"
                  "• `[4]` Curses & Counter-Curses by zu(IA)uz - Book 1\n"
                  "• `[5]` Curses & Counter-Curses by zu(IA)uz - Book 1\n"
                  "• `[6]` Spellman's Syllabary: Contractions\n"
                  "• `[7]` What if by Quinlynn - Book 1\n"
                  "• `[8]` What if by Quinlynn - Book 2\n"
        )
        embed.set_footer(
            text="grants 50 exp per book opened (max of 150/day)"
        )
        webhook.add_embed(embed)
        webhook.execute()

    @commands.command(aliases=["open"])
    async def post_book(self, ctx, arg1, *, args):

        webhooks = await ctx.channel.webhooks()
        bukkuman = webhooks[0]
        user = ctx.message.author

        if arg1.lower() == "s1" and args.lower() in lists_souls_raw:

            book = library.find_one({"title": args.title()}, {"_id": 0, "book": 0})
            webhook = DiscordWebhook(url=bukkuman.url, avatar_url="https://i.imgur.com/5FflHQ5.jpg")

            embed = DiscordEmbed(
                title=book["title"],
                color=book["color"]
            )
            embed.set_thumbnail(url=book["thumbnail"]["url"])

            for field in book["fields"]:
                embed.add_embed_field(
                    name=field["name"],
                    value=field["value"],
                    inline=field["inline"]
                )

            webhook.add_embed(embed)
            webhook.execute()
            library.update_one({"title": args.title()}, {"$inc": {"borrows": 1}})
            await post_process_books(user, ctx)

        elif arg1.lower() == "s5" and args.lower() in ["21", "25"]:

            book = library.find_one({"book": arg1.lower(), "chapter": args.lower()}, {"_id": 0, "book": 0})
            webhook = DiscordWebhook(
                url=bukkuman.url,
                avatar_url="https://i.imgur.com/5FflHQ5.jpg",
                content=book["title"]
            )

            for embedding in book["embeds"]:
                title = check_if_none(embedding, "title")
                color = check_if_none(embedding, "color")
                description = check_if_none(embedding, "description")

                try:
                    image_url = check_if_none(embedding, "image")["url"]
                except TypeError:
                    image_url = None

                embed = DiscordEmbed(
                    title=title,
                    color=color,
                    description=description
                )
                embed.set_image(url=image_url)
                webhook.add_embed(embed)

            webhook.execute()
            library.update_one({"book": arg1.lower(), "chapter": args.lower()}, {"$inc": {"borrows": 1}})
            await post_process_books(user, ctx)

        elif arg1.lower() == "ab" and args.lower() in ["1", "2", "6"]:

            book = library.find_one({"book": "assorted", "chapter": args.lower()}, {"_id": 0, "book": 0})
            webhook = DiscordWebhook(
                content=f"📙 {book['title']}",
                url=bukkuman.url,
                avatar_url="https://i.imgur.com/5FflHQ5.jpg"
            )

            for embedding in book["embeds"]:

                try:
                    image_url = check_if_none(embedding, "image")["url"]
                except TypeError:
                    image_url = None

                try:
                    footer_text = check_if_none(embedding, "footer")["icon_url"]
                    footer_text = "Guide contributed by {}".format(self.client.get_user(int(footer_text)))
                except TypeError:
                    footer_text = None

                try:
                    footer_url = check_if_none(embedding, "footer")["icon_url"]
                    footer_url = self.client.get_user(int(footer_url)).avatar_url
                except TypeError:
                    footer_url = None
                except AttributeError:
                    footer_url = None

                embed = DiscordEmbed(
                    title=check_if_none(embedding, "title"),
                    color=check_if_none(embedding, "color"),
                    description=check_if_none(embedding, "description")
                )
                embed.set_image(url=image_url)
                embed.set_footer(
                    text=footer_text,
                    icon_url=footer_url
                )
                webhook.add_embed(embed)

            webhook.execute()
            library.update_one({"book": "assorted", "chapter": args.lower()}, {"$inc": {"borrows": 1}})
            await post_process_books(user, ctx)

        elif arg1.lower() == "ab" and args.lower() in ["4", "5", "7", "8"]:

            book = library.find_one({"book": "assorted", "chapter": args.lower()}, {"_id": 0, "book": 0})
            webhook = DiscordWebhook(
                content=f"📕 {book['title']}\n{book['url']}",
                url=bukkuman.url,
                avatar_url="https://i.imgur.com/5FflHQ5.jpg"
            )

            webhook.execute()
            library.update_one({"book": "assorted", "chapter": args.lower()}, {"$inc": {"borrows": 1}})
            await post_process_books(user, ctx)

        elif arg1.lower() == "ab" and args.lower() in ["3"]:

            book = library.find_one({"book": "assorted", "chapter": args.lower()}, {"_id": 0})
            link = book["attachment"]
            contributor = book["user"]

            opener = urllib.request.build_opener()
            opener.addheaders = [('User-agent', 'Mozilla/5.0')]
            urllib.request.install_opener(opener)
            urllib.request.urlretrieve(link, "data/SSR_rates.pdf")

            file = discord.File("data/SSR_rates.pdf", filename="SSR_Rates.pdf")
            await ctx.channel.send(
                content="📙 {}".format(book["title"]).format(self.client.get_user(int(contributor))),
                file=file
            )

            library.update_one({"book": "assorted", "chapter": args.lower()}, {"$inc": {"borrows": 1}})
            await post_process_books(user, ctx)


def setup(client):
    client.add_cog(Library(client))
