"""
Embeds Module
Miketsu, 2020
"""

from PIL import Image
from discord.ext import commands

from cogs.ext.initialize import *


class Embeds(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.prefix = self.client.command_prefix

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):

        if self.client.get_user(int(payload.user_id)).bot:
            return

        query = guilds.find_one({"server": f"{id_guild}"}, {"_id": 0, "channels": 1, "messages": 1, "links": 1})

        if str(payload.message_id) == query["messages"]["banner"] and str(payload.emoji) in ["⬅", "➡"]:

            banners = query["links"]["banners"]
            banners_contributor = query["links"]["banners_contributor"]
            welcome_channel = self.client.get_channel(int(id_welcome))
            banner_msg = await welcome_channel.fetch_message(int(query["messages"]["banner"]))

            current_thumbnail = banner_msg.embeds[0].image.url
            current_index = banners.index(current_thumbnail)

            def get_new_banner(i):
                if str(payload.emoji) == "⬅":
                    new_index = i - 1
                    if i < 0:
                        return len(banners) - 1, len(banners)
                    else:
                        return new_index, new_index + 1
                else:
                    new_index = i + 1
                    if i >= len(banners) - 1:
                        return 0, 1
                    else:
                        return new_index, new_index + 1

            index, page = get_new_banner(current_index)
            embed6 = discord.Embed(
                colour=discord.Colour(0xffd6ab), title=f"🎏 Banners {page}/{len(banners)}"
            )
            embed6.set_image(url=banners[index])
            contributor = self.client.get_user(int(banners_contributor[index]))
            embed6.set_footer(text=f"Assets: Official Onmyoji art; Designed by: {contributor}")
            await process_msg_edit(banner_msg, None, embed6)

    @commands.command(aliases=["welcome"])
    @commands.is_owner()
    async def embeds_welcome_edit(self, ctx):

        query = guilds.find_one({"server": f"{id_guild}"}, {"_id": 0})

        crest_link = query["links"]["crest"]
        rules_link = query["links"]["rules_link"]
        banners = query["links"]["banners"]
        splash_link = query["links"]["splash"]
        arts = query["roles"]["arts"]
        id_head = query["roles"]["head"]

        embed1 = discord.Embed(
            colour=discord.Colour(0xe77eff),
            title="Welcome to House Patronus!",
            description=f"Herewith are the rules and information of our server!\n\n"
                        f"Crest designed by <@!281223518103011340>\n"
                        f"Server banner designed by our <@&{arts}>"
        )
        embed1.set_image(url=splash_link)
        embed1.set_thumbnail(url=crest_link)

        embed2 = discord.Embed(
            colour=discord.Colour(0xff44),
            title="Primary Server Roles",
            description=f"Sub roles are provided at the <#{id_sorting}>"
        )
        embed2.add_field(
            name="🔱 Head",
            value="• The Ministers of Patronus",
            inline=False
        )
        embed2.add_field(
            name="⚜ Auror",
            value="• The Prime Witches, Wizards, & Spirits",
            inline=False
        )
        embed2.add_field(
            name="🔮 Patronus",
            value="• Existing members of the guild",
            inline=False
        )
        embed2.add_field(
            name="🔥 No-Maj",
            value="• Obliviated, former members; guests",
            inline=False
        )
        embed2.add_field(
            name="🐼 Animagus",
            value="• Transformed members; Bots",
            inline=False
        )

        embed3 = discord.Embed(
            title="📋 Rules",
            colour=discord.Colour(0xf8e71c),
            description="• Useless and official warnings may be issued!\n​ "
        )
        embed3.add_field(
            name="# 1. Server nickname",
            value="• It must contain your actual in-game name\n​ "
        )
        embed3.add_field(
            name="# 2. Message content",
            value="• No any form of harassment, racism, toxicity, etc.\n"
                  "• Avoid posting NSFW or NSFL\n​ ",
            inline=False
        )
        embed3.add_field(
            name="# 3. Role/member mention",
            value="• Avoid unnecessary pinging\n"
                  "• Check for the specific roles for free pinging\n​ ",
            inline=False
        )
        embed3.add_field(
            name="# 4. Spamming",
            value="• Posting at the wrong channel is spamming\n"
                  "• Channels are provided for spamming bot commands\n​ ",
            inline=False
        )
        embed3.add_field(
            name="# 5. No unsolicited promotions",
            value="• Like advertising of other guilds/servers without permission\n​ ",
            inline=False
        )
        embed3.add_field(
            name="# 6. Extensions",
            value="• Above rules apply on members' direct messages\n"
                  "• Follow [Discord Community Guidelines](https://discordapp.com/guidelines)\n​ ",
            inline=False
        )

        embed4 = discord.Embed(
            colour=discord.Colour(0xb8e986),
            title="🎀 Benefits & Requirements",
            description=f"• <@&{id_patronus}> must be fully guided for #2&5\n​ ",
            inline=False
        )
        embed4.add_field(
            name="# 1. No duel/tier requirements",
            value="• But do test your limits and improve!\n​ ",
            inline=False
        )
        embed4.add_field(
            name="# 2. Guild Quest (GQ) requirements",
            value=f"• For members as well as traders, min 90 weekly GQ\n"
                  f"• Consistent inactivity will be forewarned by <@&{id_head}>\n"
                  f"• AQ is not the only option to fulfill GQs\n​ ",
            inline=False
        )
        embed4.add_field(
            name="# 3. Alternate Accounts",
            value=f"• We can accommodate if slots are available\n"
                  f"• Notify a <@&{id_head}> before applying\n​ ",
            inline=False
        )
        embed4.add_field(
            name="# 4. Guild Bonuses",
            value="• Top 50 guild in overall activeness ranking\n"
                  "• Rated at 60-70 guild packs per week\n"
                  "• Weekly 1-hour soul & evo bonus\n"
                  "• 24/7 exp, coin, & medal buffs\n"
                  "• Max guild feast rewards\n"
                  "• Ultimate Orochi carries\n"
                  "• Souls 10 carries\n"
                  "• Rich Discord content\n"
                  "• Fun, playful, & experienced members\n​ ",
            inline=False
        )
        embed4.add_field(
            name="# 5. Absenteeism/Leave",
            value=f"• File your leave prior long vacation via <#{id_absence_app}> or contact any <@&{id_head}>\n"
                  f"• Your maximum inactivity is assessed based on your guild retention/feats\n​ ",
            inline=False
        )
        embed4.add_field(
            name="# 6. Inactivity strikes system",
            value=f"• After missing any 2 weeks of GQ requirements without notice in <#{id_absence_app}>"
                  f" or pming an officer you will get a strike\n"
                  f"• After the above, offenders will receive +1 strike for every 1 week\n"
                  f"• If space in guild is required, anyone who has warnings is considered eligible for removal\n"
                  f"• Getting 3 strikes in 3 weeks or 6 strikes in 2 months will result in being kicked from "
                  f"the guild\n​ ",
            inline=False
        )
        embed4.add_field(
            name="# 7. Shard Trading",
            value=f"• If leaving for shards, contact any <@&{id_head}> & specify amount of days\n"
                  f"• If inviting a trader, notify the <@&{id_head}> in advance\n"
                  f"• Traders are required to fulfill our minimum GQ requirements or they will be kicked\n​ ",
            inline=False
        )

        embed4.set_image(url=rules_link)

        embed5 = discord.Embed(
            colour=discord.Colour(0x50e3c2),
            title="🎊 Events & Timings",
            description=f"• <@&{id_seers}> role is pinged for events #2-4\n​ "
        )
        embed5.add_field(
            name="# 1. Guild Raid",
            value="• `05:00 EST` | Resets Everyday \n​"
        )
        embed5.add_field(
            name="# 2. Kirin Hunt",
            value="• `19:00 EST` | Every Mon to Thu\n​",
            inline=False
        )
        embed5.add_field(
            name="# 3. Guild Feast",
            value="• `10:00 EST` | Every Sat \n"
                  "• `00:00 EST` | Every Sun\n​",
            inline=False
        )
        embed5.add_field(
            name="# 4. Boss Defense",
            value="• `10:15 EST` | Every Sat \n​",
            inline=False
        )
        embed5.add_field(
            name="# 5. Exclusive Guild Contests",
            value="• Announced once in a while in Discord\n​ ",
            inline=False
        )

        embed6 = discord.Embed(
            colour=discord.Colour(0xffd6ab),
            title=f"🎏 Banners 1/{len(banners)}"
        )
        embed6.set_image(
            url=banners[0]
        )
        embed6.set_footer(
            text="Assets: Official Onmyoji art; Designed by: xann#8194"
        )
        welcome_channel = self.client.get_channel(int(id_welcome))

        msg_intro = await welcome_channel.fetch_message(int(query["messages"]["intro"]))
        msg_roles = await welcome_channel.fetch_message(int(query["messages"]["roles"]))
        msg_rules = await welcome_channel.fetch_message(int(query["messages"]["rules"]))
        msg_benefits = await welcome_channel.fetch_message(int(query["messages"]["benefits"]))
        msg_events = await welcome_channel.fetch_message(int(query["messages"]["events"]))
        msg_banner = await welcome_channel.fetch_message(int(query["messages"]["banner"]))
        msg_invite = await welcome_channel.fetch_message(int(query["messages"]["invite"]))

        await process_msg_edit(msg_intro, None, embed1)
        await process_msg_edit(msg_roles, None, embed2)
        await process_msg_edit(msg_rules, None, embed3)
        await process_msg_edit(msg_benefits, None, embed4)
        await process_msg_edit(msg_events, None, embed5)
        await process_msg_edit(msg_banner, None, embed6)
        await process_msg_edit(msg_invite, "Our invite link: https://discord.gg/H6N8AHB", None)

        await process_msg_delete(ctx.message, 0)
        await process_msg_delete(ctx.message, 0)

    async def embeds_lineup_create_help(self, ctx):

        embed = discord.Embed(
            title="lineup", colour=colour,
            description="creates a shikigami lineup with souls"
        )
        embed.add_field(
            name="Formats", inline=False,
            value=f"*`{self.prefix}lineup <shikigami1-soul1-soul2, ...>`*",
        )
        embed.add_field(
            name="Example", inline=False,
            value=f"*`{self.prefix}lineup shuten doji-kyoukotsu, enmusubi-shadow`*",
        )
        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["lineup"])
    @commands.guild_only()
    async def embeds_lineup_create(self, ctx, *, args=None):

        if args is None:
            await self.embeds_lineup_create_help(ctx)

        else:
            args_formatted = args.lower().replace(", ", ",").replace(" ,", ",").split(",")
            link = await self.embeds_lineup_create_link(args_formatted, ctx)

            if link.startswith("http") is True:
                embed = discord.Embed(color=ctx.author.colour, timestamp=get_timestamp())
                embed.set_image(url=link)
                embed.set_footer(icon_url=ctx.author.avatar_url, text=f"{ctx.author.display_name}")
                await process_msg_submit(ctx.channel, None, embed)

            else:
                embed = discord.Embed(
                    color=ctx.author.colour, title="Invalid shikigami/soul",
                    description=f"I did not recognize this -> `{link}`"
                )
                await process_msg_submit(ctx.channel, None, embed)

    async def embeds_lineup_create_link(self, args_formatted, ctx):

        images, images_address = [], []
        height, width = 80, len(args_formatted) * 80
        x_init, y_init = -80, 0

        for x in args_formatted:
            x_formatted = x.replace(" - ", "-").replace("- ", "-").replace(" -", "-").split("-")
            height_new = len(x_formatted) * 80
            if height <= height_new:
                height = height_new

            if shikigamis.find_one({"aliases": x_formatted[0]}, {"_id": 0, "name": 1}) is None:
                return x_formatted[0]
            else:
                address_shikigami = f"data/shikigamis/{x_formatted[0]}_evo.jpg"
                images_address.append(address_shikigami)
                images.append(Image.open(address_shikigami).resize((80, 80), Image.ANTIALIAS))

            for y in x_formatted[1:]:
                if souls.find_one({"name": y.lower()}, {"_id": 0, "name": 1}) is None:
                    return y.lower()

                address_soul = f"data/souls/{y.lower()}.png"
                images_address.append(address_soul)
                images.append(Image.open(address_soul))

        new_im = Image.new("RGBA", (width, height))

        def get_coordinates(i, x_coordinate, y_coordinate):

            if images_address[i][:10] == "data/souls":
                y_coordinate += 80
                return x_coordinate, y_coordinate

            elif images_address[i][:10] == "data/shiki":
                x_coordinate += 80
                y_coordinate = 0
                return x_coordinate, y_coordinate

        for index, item in enumerate(images):
            x_new, y_new = get_coordinates(index, x_init, y_init)
            new_im.paste(images[index], (x_new, y_new))
            x_init = x_new
            y_init = y_new

        address_temp = f"temp/{ctx.author.id}.png"
        new_im.save(address_temp)

        image_file = discord.File(address_temp, filename=f"{ctx.author.id}.png")
        hosting_channel = self.client.get_channel(int(id_hosting))
        msg = await process_msg_submit_file(hosting_channel, image_file)
        attachment_link = msg.attachments[0].url

        return attachment_link

    async def embeds_post_help(self, ctx):

        embed = discord.Embed(
            title="embed", colour=colour,
            description="submit a an embed message"
        )
        embed.add_field(
            name="Format", inline=False,
            value=f"*`{self.prefix}embed <#channel> <title|description|image_link>`*"
        )
        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["embed"])
    @commands.guild_only()
    async def embeds_post_(self, ctx, channel: discord.TextChannel = None, *, args):

        if channel is None:
            await self.embeds_post_help(ctx)
            return

        list_msg = args.replace(" | ", "|").split("|", 3)
        print(list_msg)
        embed = discord.Embed(color=ctx.author.colour)

        if len(list_msg) == 1:
            embed.description = list_msg[0]

        elif len(list_msg) == 2:
            embed.title = list_msg[0]
            embed.description = list_msg[1]

        elif len(list_msg) == 3:
            embed.title = list_msg[0]
            embed.description = list_msg[1]
            embed.set_image(url=list_msg[2])
        else:
            return

        await process_msg_submit(channel, None, embed)
        await process_msg_reaction_add(ctx.message, "✅")


def setup(client):
    client.add_cog(Embeds(client))
