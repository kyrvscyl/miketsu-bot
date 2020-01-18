"""
Beta Module
Miketsu, 2020
"""
import urllib.request

from discord.ext import commands
from discord_webhook import DiscordEmbed, DiscordWebhook

from cogs.ext.initialize import *


class Beta(commands.Cog):

    def __init__(self, client):

        self.client = client
        self.prefix = self.client.command_prefix

        self.primary_emojis = dictionaries["primary_emojis"]
        self.primary_roles = listings_1["primary_roles"]

    def castle_create_webhook_post(self, webhooks, book):

        bukkuman = webhooks[0]
        webhook = DiscordWebhook(
            content=book['content'], url=bukkuman.url, username="Professor Bukkuman", avatar_url=librarian_img
        )

        def embed_new_value_1_generate(d, k):
            try:
                value = d[k]
            except KeyError:
                value = None
            return value

        try:
            book["embeds"]
        except KeyError:
            pass
        else:
            for entry in book["embeds"]:
                embed = DiscordEmbed(color=embed_new_value_1_generate(entry, "color"))

                try:
                    title = embed_new_value_1_generate(entry, "title")
                except (AttributeError, TypeError):
                    pass
                else:
                    embed.title = title

                try:
                    description = embed_new_value_1_generate(entry, "description")
                except (AttributeError, TypeError):
                    pass
                else:
                    embed.description = description.replace("\\n", "\n")

                try:
                    url_thumbnail = embed_new_value_1_generate(entry, "thumbnail")["url"]
                except TypeError:
                    pass
                else:
                    embed.set_thumbnail(url=url_thumbnail)

                try:
                    url_image = embed_new_value_1_generate(entry, "image")["url"]
                except TypeError:
                    pass
                else:
                    embed.set_image(url=url_image)

                try:
                    entry["fields"]
                except KeyError:
                    pass
                else:
                    for f in entry["fields"]:
                        embed.add_embed_field(name=f["name"], inline=False, value=f["value"].replace("\\n", "\n"))

                try:
                    user_id = embed_new_value_1_generate(entry, "author")["icon_url"]
                except (ValueError, TypeError, AttributeError):
                    pass
                else:
                    user = self.client.get_user(int(user_id))
                    name = embed_new_value_1_generate(entry, "author")["name"]
                    embed.set_author(name=name, icon_url=str(user.avatar_url_as(format="jpg", size=128)))

                try:
                    user_id = embed_new_value_1_generate(entry, "footer")["text"]
                except ValueError:
                    embed.set_footer(text=embed_new_value_1_generate(entry, "footer")["text"])
                except (TypeError, AttributeError):
                    pass
                else:
                    user = self.client.get_user(int(user_id))
                    embed.set_footer(
                        text=f"Guide by {user.name}",
                        icon_url=str(user.avatar_url_as(format="jpg", size=128))
                    )

                webhook.add_embed(embed)

        return webhook

    @commands.command(aliases=["guides"])
    @commands.guild_only()
    async def castle_post_guides(self, ctx):

        if check_if_reference_section(ctx):
            await self.castle_post_guides_reference(ctx.channel)

        elif check_if_restricted_section(ctx):
            await self.castle_post_guides_restricted(ctx.channel)

        else:
            embed = discord.Embed(
                title="guides", colour=colour,
                description="show the guild's game guides collection, usable only at the library"
            )
            embed.add_field(name="Library sections", value=f"<#{id_reference}>, <#{id_restricted}>", inline=False)
            await process_msg_submit(ctx.channel, None, embed)

    async def castle_post_guides_restricted(self, channel):

        webhooks = await channel.webhooks()

        try:
            bukkuman = webhooks[0]
            url = bukkuman.url
        except (AttributeError, IndexError):
            return
        else:
            webhook = DiscordWebhook(url=url, avatar_url=librarian_img)

            listings_formatted_1 = []
            for b in books.find({"section": "da"}):
                listings_formatted_1.append(f"• `{b['index']}` {b['boss'].title()}\n")

            listings_formatted_2 = []
            for b in books.find({"section": "fb"}):
                listings_formatted_2.append(f"• `{b['index']}` {b['boss'].title()}\n")

            listings_formatted_3 = []
            for b in books.find({"section": "dao"}):
                listings_formatted_3.append(f"• `{b['index']}` {b['boss'].title()}\n")

            embed = DiscordEmbed(
                title="🔖 Table of Contents", colour=discord.Colour(0xa0c29a),
                description="• To open a book use `;open [section] [index]`\n"
                            "• Example: `;open da 8`"
            )
            embed.add_embed_field(
                name="📓 Defense Against The Dark Arts `[DA]`",
                value="".join(listings_formatted_1)
            )
            embed.add_embed_field(
                name="📓 Fantastic Beasts and How to Deal with Them `[FB]`",
                value="".join(listings_formatted_2)
            )
            embed.add_embed_field(
                name="📓 The Dark Arts Outsmarted `[DAO]`",
                value="".join(listings_formatted_3)
            )
            webhook.add_embed(embed)
            webhook.execute()

    async def castle_post_guides_reference(self, channel):

        webhooks = await channel.webhooks()

        try:
            bukkuman = webhooks[0]
            url = bukkuman.url
        except (AttributeError, IndexError):
            return
        else:
            webhook = DiscordWebhook(url=url, avatar_url=librarian_img)

            listings_souls = []
            for s in books.find({
                "section": "sbs", "content": "The Standard Book of Souls - Year 1"}, {
                "_id": 0, "index": 1
            }):
                listings_souls.append(f"`{s['index'].lower()}`")

            listings_souls_sbs = []
            for x in books.find({"section": "sbs", "index": {"$in": ["1", "2", "3"]}}, {"index": 1, "name": 1}):
                listings_souls_sbs.append(f"• `[{x['index']}]` {x['name']}\n")

            listings_souls_sdb = []
            for x in books.find({"section": "sdb"}, {"index": 1, "name": 1}):
                listings_souls_sdb.append(f"• `[{x['index']}]` {x['name']}\n")

            listings_souls_sdb = []
            listings_souls_sdb_valid = [f"{x}" for x in list(range(1, 11))]
            for x in books.find({"section": "ab", "index": {"$in": listings_souls_sdb_valid}}, {"index": 1, "name": 1}):
                listings_souls_sdb.append(f"• `[{x['index']}]` {x['name']}\n")

            embed = DiscordEmbed(
                title="🔖 Table of Magical Contents",
                colour=discord.Colour(0xa0c29a),
                description="• To open a book use `;open [section] [index]`\n"
                            "• Example: `;open sbs 3`"
            )
            embed.add_embed_field(
                name="📖 The Standard Book of Souls - Year 1 `[SBS]`",
                value=", ".join(listings_souls), inline=False
            )
            embed.add_embed_field(
                name="📖 The Standard Book of Souls - Year 5 `[SBS]`",
                value="".join(listings_souls_sbs), inline=False
            )
            embed.add_embed_field(
                name="📕 Secret Duelling Books `[SDB]`",
                value="".join(listings_souls_sdb), inline=False
            )
            embed.add_embed_field(
                name="📚 Assorted Books `[AB]`",
                value="".join(listings_souls_sdb), inline=False
            )
            webhook.add_embed(embed)
            webhook.execute()
            return True

    @commands.command(aliases=["open"])
    @commands.guild_only()
    async def castle_post_guides_book_open(self, ctx, arg1, *, args="None"):

        if check_if_reference_section(ctx):

            webhooks = await ctx.channel.webhooks()
            query = {"section": arg1.lower(), "index": args.lower()}

            if arg1.lower() == "pb" and args.lower() == "bgt":
                query = {"section": arg1.lower(), "index": "0"}

            book = books.find_one(query, {"_id": 0})

            if arg1.lower() in ["ab", "sbs"] and args.lower() in ["3"]:

                opener = urllib.request.build_opener()
                opener.addheaders = [('User-agent', 'Mozilla/5.0')]
                urllib.request.install_opener(opener)
                urllib.request.urlretrieve(book["attachment"], book["address"])

                file = discord.File(book["address"], filename=book["filename"])
                contributor = self.client.get_user(int(book["contributor"]))
                await ctx.channel.send(content=f"{book['content']} {contributor}", file=file)
                await self.castle_post_guides_book_process(ctx, query)

            elif book is not None:

                webhook = self.castle_create_webhook_post(webhooks, book)
                webhook.execute()
                await self.castle_post_guides_book_process(ctx, query)

        elif check_if_restricted_section(ctx):

            webhooks = await ctx.channel.webhooks()
            query = {"section": arg1.lower(), "index": args.lower()}
            book = books.find_one(query, {"_id": 0})

            if arg1.lower() in ["fb"] and args.lower() in ["1", "2"]:

                opener = urllib.request.build_opener()
                opener.addheaders = [('User-agent', 'Mozilla/5.0')]
                urllib.request.install_opener(opener)
                urllib.request.urlretrieve(book["attachment"], book["address"])

                file = discord.File(book["address"], filename=book["filename"])
                await ctx.channel.send(content=f"{book['content']}", file=file)
                await self.castle_post_guides_book_process(ctx, query)

            elif book is not None:

                webhook = self.castle_create_webhook_post(webhooks, book)
                webhook.execute()
                await self.castle_post_guides_book_process(ctx, query)

    async def castle_post_guides_book_process(self, ctx, query):
        books.update_one(query, {"$inc": {"borrows": 1}})
        await process_msg_delete(ctx.message, None)


def setup(client):
    client.add_cog(Beta(client))
