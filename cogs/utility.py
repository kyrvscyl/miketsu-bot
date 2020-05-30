"""
Utility Module
Miketsu, 2020
"""

from discord.ext import commands

from cogs.ext.initialize import *


class Utility(commands.Cog):

    def __init__(self, client):

        self.client = client
        self.prefix = self.client.command_prefix

    async def shikigami_bounty_help(self, ctx):

        embed = discord.Embed(
            title="bounty, b",
            colour=colour,
            description="search shikigami bounty locations or modify them"
        )
        embed.add_field(
            name="Format",
            value=f"*"
                  f"`{self.prefix}bounty <shikigami>`\n"
                  f"`{self.prefix}baa <shikigami_name> <new alias/keyword>`\n"
                  f"`{self.prefix}bal <shikigami_name> <new location>`"
                  f"*",
            inline=False
        )
        embed.add_field(
            name="Examples",
            value=f"*"
            f"`{self.prefix}bounty yuki onna`\n"
            f"`{self.prefix}baa yuki_onna <new alias/keyword>`\n"
            f"`{self.prefix}bal shuten_doji <new location>`"
            f"*",
            inline=False
        )
        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["bounty", "b"])
    @commands.guild_only()
    async def shikigami_bounty_query(self, ctx, *, shikigami_name=None):

        if shikigami_name is None:
            await self.shikigami_bounty_help(ctx)

        else:

            search = shikigamis.find_one({
                "aliases": shikigami_name.lower()
            }, {
                "_id": 0, "location": 1, "thumbnail": 1, "name": 1, "aliases": 1, "queries": 1
            })

            if search is not None:

                description = ("• " + "\n• ".join(search["location"]))

                embed = discord.Embed(
                    color=ctx.author.colour, timestamp=get_timestamp(),
                    title=f"Bounty location(s) for {search['name'].title()}",
                    description=description
                )
                embed.set_footer(icon_url=search["thumbnail"]["pre"], text=f"Queried {search['queries']} time(s)")
                await process_msg_submit(ctx.channel, None, embed)

                shikigamis.update_one({"aliases": shikigami_name.lower()}, {"$inc": {"queries": 1}})

            else:
                await shikigami_post_approximate_results(ctx, shikigami_name)

    @commands.command(aliases=["baa"])
    @commands.guild_only()
    async def shikigami_bounty_add_alias(self, ctx, shikigami_name=None, *, alias_new=None):

        if shikigami_name is None or alias_new is None:
            await self.shikigami_bounty_help(ctx)
            return

        shikigami_name_formatted = shikigami_name.replace("_", " ")
        x = shikigamis.update_one({"aliases": shikigami_name.lower()}, {"$push": {"aliases": alias_new.lower()}})

        if x.modified_count == 1:
            embed = discord.Embed(
                colour=colour, timestamp=get_timestamp(), title="Bounty profile updated",
                description=f"successfully added new alias `{alias_new}` to {shikigami_name_formatted.title()}",
            )
            await process_msg_submit(ctx.channel, None, embed)

        else:
            await process_msg_reaction_add(ctx.message, "❌")

    @commands.command(aliases=["bal"])
    @commands.guild_only()
    async def shikigami_bounty_add_location(self, ctx, shikigami_name=None, *, location_new=None):

        if shikigami_name is None or location_new is None:
            await self.shikigami_bounty_help(ctx)
            return

        shikigami_name = shikigami_name.replace("_", " ").lower()
        x = shikigamis.update_one({"aliases": shikigami_name.lower()}, {"$push": {"location": location_new}})

        if x.modified_count == 1:
            embed = discord.Embed(
                colour=colour, timestamp=get_timestamp(),
                title=f"Successfully added new location to {shikigami_name.title()}", description=f"{location_new}",
            )
            await process_msg_submit(ctx.channel, None, embed)

        else:
            await process_msg_reaction_add(ctx.message, "❌")


def setup(client):
    client.add_cog(Utility(client))
