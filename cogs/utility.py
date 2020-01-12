"""
Clock Module
Miketsu, 2020
"""

from discord.ext import commands

from cogs.ext.initialize import *


class Utility(commands.Cog):

    def __init__(self, client):

        self.client = client
        self.prefix = self.client.command_prefix

    @commands.command(aliases=["baa"])
    @commands.guild_only()
    async def economy_bounty_add_alias(self, ctx, name, *, alias):

        name_formatted = name.replace("_", " ")
        bounties.update_one({"aliases": name.lower()}, {"$push": {"aliases": alias.lower()}})

        embed = discord.Embed(
            colour=colour, timestamp=get_timestamp(), title="Bounty profile updated",
            description=f"successfully added {alias} to {name_formatted.title()}",
        )
        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["bal"])
    @commands.guild_only()
    async def economy_bounty_add_location(self, ctx, name, *, location):

        bounties.update_one({"aliases": name.lower()}, {"$push": {"location": location}})
        embed = discord.Embed(
            colour=colour, timestamp=get_timestamp(),
            title=f"Successfully added new location to {name.title()}", description=f"{location}",
        )
        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["bounty", "b"])
    @commands.guild_only()
    async def economy_bounty_query(self, ctx, *, query):

        if len(query) > 2:

            bounty_search1 = bounties.find_one({"aliases": query.lower()}, {"_id": 0})
            bounty_search2 = bounties.find({"aliases": {"$regex": f"^{query[:2].lower()}"}}, {"_id": 0})

            if bounty_search1 is not None:

                shikigami_name = bounty_search1["bounty"].title()
                description = ("• " + "\n• ".join(bounty_search1["location"]))
                aliases = ", ".join(bounty_search1["aliases"])

                embed = discord.Embed(
                    color=ctx.author.colour, timestamp=get_timestamp(),
                    title=f"Bounty location(s) for {shikigami_name}", description=description
                )
                try:
                    thumbnail = get_thumbnail_shikigami(bounty_search1["bounty"].lower(), "pre")
                    embed.set_footer(icon_url=thumbnail, text=f"aliases: {aliases}")
                except TypeError:
                    pass

                await process_msg_submit(ctx.channel, None, embed)

            elif bounty_search2 is not None:

                bounty_list = []
                for result in bounty_search2:
                    bounty_list.append(result["bounty"])

                embed = discord.Embed(
                    title="No exact results", colour=colour, timestamp=get_timestamp(),
                    description="the provided name/keyword is non-existent",
                )
                embed.add_field(name="Possible queries", value="*{}*".format(", ".join(bounty_list)))
                await process_msg_submit(ctx.channel, None, embed)


def setup(client):
    client.add_cog(Utility(client))
