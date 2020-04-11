"""
Admin Module
Miketsu, 2020
"""

import re
import urllib.request

from discord.ext import commands

from cogs.ext.initialize import *


class Admin(commands.Cog):

    def __init__(self, client):

        self.client = client
        self.prefix = self.client.command_prefix

        self.roles = listings_1["roles"]
        self.fields = listings_1["fields"]
        self.member_status = listings_1["member_status"]

        self.roles_emoji = dictionaries["roles_emoji"]
        self.shortened = dictionaries["shortened"]
        self.status_batch = dictionaries["status_batch"]
        self.status_code = dictionaries["status_code"]
        self.code_status = dictionaries["code_status"]

    def get_shortened_code(self, key):
        return self.shortened[key]

    async def admin_post_patch_notes_help(self, ctx):

        embed = discord.Embed(
            title="patch", colour=colour,
            description=f"submit the patch notes to the <#{id_headlines}>"
        )
        embed.add_field(
            name="Format", inline=False,
            value=f"*`{self.prefix}patch <pastebin_key> <image_link>`*"
        )
        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["patch"])
    @commands.guild_only()
    @commands.check(check_if_user_has_any_admin_roles)
    async def admin_post_patch_notes(self, ctx, key=None, *, link_image=None):

        if key is None or link_image is None:
            await self.admin_post_patch_notes(ctx)

        else:
            user = ctx.author
            headlines_channel = self.client.get_channel(int(id_headlines))
            link_pastebin, cap = f"https://pastebin.com/raw/{key}", 1500

            f = urllib.request.urlopen(link_pastebin)
            text = f.read().decode('utf-8')
            text_split = text.replace("\r", "\\n").split("\n")
            embeds_max = ceil(len(text) / cap)

            lines, lines_start, description_length = 0, 0, 0
            lines_end = len(text_split)

            for n in range(0, embeds_max):

                for line in text_split[lines_start:lines_end]:
                    description_length += len(line)
                    if description_length > cap:
                        break
                    lines += 1

                description = "".join(text_split[lines_start:lines]).replace("\\n", "\n")
                lines_start = lines
                description_length = 0

                embed = discord.Embed(color=user.colour, description=description)
                if embeds_max - 1 == n:
                    embed.set_image(url=link_image)

                await process_msg_submit(headlines_channel, None, embed)
                await asyncio.sleep(1)

            await process_msg_reaction_add(ctx.message, "✅")

    async def admin_post_memorandum_help(self, ctx):

        embed = discord.Embed(
            title="memo", colour=colour,
            description="submit a paperwork memorandum"
        )
        embed.add_field(
            name="Format", inline=False,
            value=f"*`{self.prefix}memo <#channel>`*"
        )
        embed.add_field(
            name="Notes", inline=False,
            value=f"follow the step by step procedure\n"
                  f"enter any non-image link text to remove the memorandum's embed image"
        )
        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["memo"])
    @commands.guild_only()
    @commands.check(check_if_user_has_any_admin_roles)
    async def admin_post_memorandum(self, ctx, channel_target: discord.TextChannel = None):

        user = ctx.author

        if channel_target is None:
            await self.admin_post_memorandum_help(ctx)

        elif channel_target is not None:

            try:
                channel_target.id
            except AttributeError:
                embed = discord.Embed(
                    colour=user.colour, title="Invalid channel",
                    description="tag a valid channel", timestamp=get_timestamp()
                )
                await process_msg_submit(ctx.channel, None, embed)
            else:
                query = guilds.find_one({"server": str(id_guild)}, {"_id": 0})
                memos_count = memos.count_documents({})

                id_head = query["roles"]["head"]
                id_channel_memo = query["channels"]["memorandum"]
                link_image_memo = query["links"]["memo"]

                memo_channel = self.client.get_channel(int(id_channel_memo))
                memo_channel_name = "memorandum"

                if memo_channel is not None:
                    memo_channel_name = memo_channel.name

                details = [
                    "Step 1: <Required> Enter message content (useful for pinging roles)",
                    "Step 2: <Required> Enter the embed title",
                    "Step 3: <Required> Enter the embed description:\n\nNote: Maximum of 2000 characters",
                    link_image_memo
                ]

                def create_content(c):
                    return c

                def embed_new_create(t, d, link):

                    embed_new = discord.Embed(colour=user.colour, title=t, description=d, timestamp=get_timestamp())
                    embed_new.set_thumbnail(url=ctx.guild.icon_url)
                    embed_new.set_footer(
                        text=f"#{memo_channel_name}-{lengthen_code_4(memos_count + 1)}",
                        icon_url=user.avatar_url
                    )
                    if link is not None:
                        embed_new.set_image(url=link)

                    return embed_new

                msg = await process_msg_submit(
                    ctx.channel, create_content(details[0]), embed_new_create(details[1], details[2], details[3])
                )

                def check(m):
                    return m.author == ctx.author and m.channel.id == ctx.channel.id

                for index, item in enumerate(details):
                    try:
                        answer = await self.client.wait_for("message", timeout=120, check=check)
                    except asyncio.TimeoutError:
                        break
                    else:
                        details[index] = answer.content
                        await process_msg_reaction_add(answer, "✅")

                        try:
                            await process_msg_edit(
                                msg, create_content(details[0]), embed_new_create(details[1], details[2], details[3])
                            )
                        except discord.errors.HTTPException:
                            details[index] = None
                            await process_msg_edit(
                                msg, create_content(details[0]), embed_new_create(details[1], details[2], None)
                            )

                memos.insert_one({
                    "#": memos_count + 1,
                    "timestamp": get_time(),
                    "user_id": str(ctx.author.id),
                    "content": details[0],
                    "title": details[1],
                    "description": details[2],
                    "image": details[3],
                })

                embed = discord.Embed(
                    colour=ctx.author.colour, timestamp=get_timestamp(),
                    title="Confirm issuance",
                    description="Do you want to send the memo drafted above?\nAnnounces immediately",
                )
                embed.set_footer(text=f"{ctx.author.display_name}", icon_url=ctx.author.avatar_url)

                msg1 = await process_msg_submit(ctx.channel, None, embed)

                emojis_add = ["✅"]
                for emoji in emojis_add:
                    await process_msg_reaction_add(msg1, emoji)

                def check2(r, u):
                    return u == ctx.author and str(r.emoji) in emojis_add and msg1.id == r.message.id

                try:
                    await self.client.wait_for("reaction_add", check=check2, timeout=15)
                except asyncio.TimeoutError:
                    pass
                else:
                    await process_msg_submit(
                        channel_target,
                        create_content(details[0]),
                        embed_new_create(details[1], details[2], details[3])
                    )
                    await process_msg_submit(
                        memo_channel,
                        f"*<@&{id_head}>, a new memo has been issued:*" + "\n" + create_content(details[0]),
                        embed_new_create(details[1], details[2], details[3])
                    )

    async def admin_post_message_textchannel_help(self, ctx):

        embed = discord.Embed(
            colour=colour, title="say",
            description="allows me to repeat a text message"
        )
        embed.add_field(
            name="Format", inline=False,
            value=f"*`{self.prefix}say <#channel or channel_id> <any message>`*"
        )
        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["say"])
    @commands.guild_only()
    @commands.check(check_if_user_has_any_admin_roles)
    async def admin_post_message_textchannel(self, ctx, id_channel=None, *, content=None):

        if id_channel is None or content is None:
            await self.admin_post_message_textchannel_help(ctx)

        else:
            user = ctx.author
            channel_id = re.sub("[<>#]", "", id_channel)
            channel_target = self.client.get_channel(int(channel_id))

            if channel_target is None:
                raise commands.UserInputError(user)

            else:
                await process_msg_submit(channel_target, content, None)
                await process_msg_reaction_add(ctx.message, "✅")

    async def admin_post_message_user_help(self, ctx):

        embed = discord.Embed(
            colour=colour, title="dm",
            description="allows me to message a user"
        )
        embed.add_field(name="Format", value=f"*`{self.prefix}dm <@member or member_id> <any message>`*")
        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["dm"])
    @commands.guild_only()
    @commands.check(check_if_user_has_any_admin_roles)
    async def admin_post_message_user(self, ctx, id_member=None, *, content=None):

        if id_member is None or content is None:
            await self.admin_post_message_user_help(ctx)

        else:
            user = ctx.author
            member_id = re.sub("[<>@&!]", "", id_member)
            member = ctx.guild.get_member(int(member_id))

            if member is None:
                embed = discord.Embed(
                    title="Invalid member", colour=user.colour,
                    description="Provide a valid member ID or tag them"
                )
                await process_msg_submit(ctx.channel, None, embed)

            else:
                await process_msg_submit(member, content, None)
                await process_msg_reaction_add(ctx.message, "✅")

    async def admin_purge_messages_help(self, ctx):

        embed = discord.Embed(
            colour=colour, title="clear",
            description="allows me to clear an amount of messages in the same channel"
        )
        embed.add_field(name="Format", value=f"*`{self.prefix}clear <non negative integer: max of 100>`*")
        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["clear"])
    @commands.guild_only()
    @commands.check(check_if_user_has_any_admin_roles)
    async def admin_purge_messages(self, ctx, amount=None):

        if amount is None:
            await self.admin_purge_messages_help(ctx)

        else:
            try:
                int(amount)
            except ValueError:
                await self.admin_purge_messages_help(ctx)
            else:
                if int(amount) > 0:
                    await process_msg_purge(ctx.channel, amount)

    async def admin_manage_guild_help(self, ctx, invoke, args_v):

        embed = discord.Embed(
            title=f"{invoke}, {invoke[:1]}", colour=colour,
            description="recognizable first arguments for this command"
        )
        embed.add_field(name="Arguments", inline=False, value=f"*{', '.join(args_v)}*", )
        embed.add_field(
            name="Example", inline=False,
            value=f"*`{self.prefix}{invoke} {random.choice(args_v)}`*",
        )
        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["manage", "m"])
    @commands.guild_only()
    @commands.check(check_if_user_has_any_admin_roles)
    async def admin_manage_guild(self, ctx, *args):

        invoke = "manage"
        args_v = ["help", "add", "delete", "update", "show"]

        if len(args) == 0:
            await self.admin_manage_guild_help(ctx, invoke, args_v)

        elif args[0].lower() in [args_v[0], args_v[0][:1]]:
            await self.admin_manage_guild_help(ctx, invoke, args_v)

        elif args[0].lower() in [args_v[1], args_v[1][:1]]:

            if len(args) <= 2:
                embed = discord.Embed(
                    title=f"{invoke} {args_v[1]}, {invoke[:1]} {args_v[1][:1]}", colour=colour,
                    description="adds a new user in the database"
                )
                embed.add_field(
                    name="Format", inline=False,
                    value=f"*`{self.prefix}{invoke} {args_v[1]} <role> <name>`*"
                )
                embed.add_field(name="Roles", inline=False, value=f"*{', '.join(self.roles)}*")
                await process_msg_submit(ctx.channel, None, embed)

            elif len(args) == 3 and args[1].lower() in self.roles:
                await self.admin_manage_guild_add_member(ctx, args)

            else:
                await process_msg_reaction_add(ctx.message, "❌")

        elif args[0].lower() in [args_v[2], args_v[2][:1]]:

            if len(args) <= 1:
                embed = discord.Embed(
                    title=f"{invoke} {args_v[2]}, {invoke[:1]} {args_v[2][:1]}", colour=colour,
                    description="removes a member in the database"
                )
                embed.add_field(
                    name="Format", inline=False,
                    value=f"*`{self.prefix}{invoke} {args_v[2]} <exact_name>`*"
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif len(args) == 2:
                await self.admin_manage_guild_add_delete(ctx, args)

            else:
                await process_msg_reaction_add(ctx.message, "❌")

        elif args[0].lower() in [args_v[3], args_v[3][:1]]:

            if len(args) <= 1:
                embed = discord.Embed(
                    title=f"{invoke} {args_v[3]}, {invoke[:1]} {args_v[3][:1]}", colour=colour,
                    description="updates a guild member's profile"
                )
                embed.add_field(
                    name="field :: value", inline=False,
                    value=f"• **name** :: <exact_name>\n"
                          f"• **notes** :: *<any officer notes>*\n"
                          f"• **role** :: *{', '.join(self.roles)}*\n"
                          f"• **status** :: *{', '.join(self.member_status)}*"
                )
                embed.add_field(
                    name="Format", inline=False,
                    value=f"*`{self.prefix}{args_v[3]} {args_v[3][:1]} <name or id> <field> <value>`*"
                )
                embed.add_field(
                    name="Batch updating", inline=False,
                    value="available for inactives & semi-actives [pluralized form]"
                )
                embed.add_field(
                    name="Example", inline=False,
                    value=f"*`{self.prefix}{invoke[:1]} {args_v[3][:1]} 1 role member`*\n"
                          f"*`{self.prefix}{invoke[:1]} {args_v[3][:1]} 100 notes alt account`*\n"
                          f"*`{self.prefix}{invoke[:1]} {args_v[3][:1]} 45 strikes <insert reason>`*\n"
                          f"*`{self.prefix}{invoke[:1]} {args_v[3][:1]} inactives`*"
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif len(args) == 2 and args[1].lower() == "feats":
                await self.admin_manage_guild_update_feats(ctx, ctx.author)

            elif len(args) >= 3 and args[2].lower() not in self.fields:

                fields_formatted = []
                for field in self.fields:
                    fields_formatted.append(f"`{field}`")

                embed = discord.Embed(
                    colour=colour, title=f"Invalid `{args_v[3]}` syntax",
                    description="field entered is not valid"
                )
                embed.add_field(
                    name="Valid fields",
                    value="*" + ', '.join(fields_formatted) + "*"
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif len(args) == 2 and args[1].lower() in list(self.status_batch):
                await self.admin_manage_guild_update_performance(
                    ctx, args[1].lower()[:-1], self.status_batch[args[1].lower()], ctx.author
                )

            elif len(args) == 2:

                fields_formatted = []
                for field in self.fields:
                    fields_formatted.append(f"`{field}`")

                embed = discord.Embed(
                    colour=colour, title=f"Invalid `{args_v[3]}` syntax",
                    description="no field and value provided"
                )
                embed.add_field(name="Valid fields", value="*" + ', '.join(fields_formatted) + "*")
                embed.add_field(
                    name="Example", inline=False,
                    value=f"*`{self.prefix}{invoke[:1]} {args_v[3][:1]} 1 role member`*\n",
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif len(args) == 3 and args[2].lower() in self.fields:

                embed = discord.Embed(
                    colour=colour, title=f"Invalid `{args_v[3]}` syntax",
                    description="no value provided for the field"
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif len(args) == 3 and args[2].lower() == "strikes":

                embed = discord.Embed(
                    colour=colour, title=f"Invalid `{args_v[3]}` syntax",
                    description="No reason provided"
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif len(args) >= 4 and args[2].lower() in self.fields:
                await self.admin_manage_guild_update_field(ctx, args)

            else:
                await process_msg_reaction_add(ctx.message, "❌")

        elif args[0].lower() in [args_v[4], args_v[4][:1]]:

            if len(args) == 1:
                embed = discord.Embed(
                    title=f"{invoke} {args_v[4]}, {invoke[:1]} {args_v[4][:1]}", colour=colour,
                    description="queries the guild database"
                )
                embed.add_field(
                    name="Formats",
                    value=f"• *`{self.prefix}{invoke[:1]} {args_v[4][:1]} all <opt: [<startswith> or guild]>`*\n"
                          f"• *`{self.prefix}{invoke[:1]} {args_v[4][:1]} all <role or status> <value>`*\n"
                          f"• *`{self.prefix}{invoke[:1]} {args_v[4][:1]} <name or id_num>`*",
                    inline=False
                )
                embed.add_field(
                    name="Examples",
                    value=f"• *`{self.prefix}{invoke[:1]} {args_v[4][:1]} all`*\n"
                          f"• *`{self.prefix}{invoke[:1]} {args_v[4][:1]} all aki`*\n"
                          f"• *`{self.prefix}{invoke[:1]} {args_v[4][:1]} status inactive`*\n"
                          f"• *`{self.prefix}{invoke[:1]} {args_v[4][:1]} 120`*\n"
                          f"• *`{self.prefix}{invoke[:1]} {args_v[4][:1]} all <guild/[abc]/123>`*\n"
                          f"• *`{self.prefix}{invoke[:1]} {args_v[4][:1]} all guild strike`*",
                    inline=False
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif len(args) == 2 and args[1].lower() == "role":

                roles_formatted = []
                for role in self.roles:
                    roles_formatted.append(f"{role}")

                embed = discord.Embed(
                    colour=colour,
                    title=f"Invalid `{args_v[4]}` syntax",
                    description="provide a role value to show"
                )
                embed.add_field(
                    name="Valid statuses",
                    value="*" + ', '.join(roles_formatted) + "*"
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif len(args) == 2 and args[1].lower() == "status":

                statuses_formatted = []
                for status in self.member_status:
                    statuses_formatted.append(f"{status}")

                embed = discord.Embed(
                    colour=colour,
                    title=f"Invalid `{args_v[4]}` syntax",
                    description="provide a status value to show"
                )
                embed.add_field(
                    name="Valid statuses",
                    value="*" + ', '.join(statuses_formatted) + "*"
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif len(args) == 2 and args[1].lower() == "stats":
                await self.admin_manage_guild_show_stats(ctx)

            elif len(args) == 2 and args[1].lower() == "all":
                await self.admin_manage_guild_show_all(ctx, [("name_lower", 1)])

            elif len(args) == 3 and args[1].lower() == "all" and args[2].lower() in ["abc", "123"]:

                if args[2].lower() == "abc":
                    await self.admin_manage_guild_show_all(ctx, [("name_lower", 1)])

                elif args[2].lower() == "123":
                    await self.admin_manage_guild_show_all(ctx, [("#", 1)])

                else:
                    await process_msg_reaction_add(ctx.message, "❌")

            elif len(args) == 3 and args[1].lower() == "all" and args[2].lower() == "guild":
                await self.admin_manage_guild_show_current_members(ctx)

            elif len(args) == 4 and args[1].lower() == "all" and args[2].lower() == "guild" \
                    and args[3].lower() == "strike":
                await self.admin_manage_guild_show_current_members_strikes(ctx)

            elif len(args) == 3 and args[1].lower() == "all":
                await self.admin_manage_guild_show_startswith(ctx, args)

            elif len(args) == 2 and args[1].lower() != "all" and args[1].lower() not in self.fields:
                await self.admin_manage_guild_show_profile(ctx, args)

            elif len(args) == 3 and args[1].lower() == "status" and args[2].lower() in self.member_status:
                await self.admin_manage_guild_show_field_status(ctx, args)

            elif len(args) == 3 and args[1].lower() == "role" and args[2].lower() in self.roles:
                await self.admin_manage_guild_show_field_role(ctx, args)

            else:
                await process_msg_reaction_add(ctx.message, "❌")

        else:
            await process_msg_reaction_add(ctx.message, "❌")

    async def admin_manage_guild_update_feats(self, ctx, user):

        embed = discord.Embed(colour=colour, title="initializing batch updating of feats..")
        msg = await process_msg_submit(ctx.channel, None, embed)
        await asyncio.sleep(3)

        embed = discord.Embed(
            colour=user.colour,
            title="enter `stop`/`skip` to exit the update or skip a member, respectively.."
        )
        await process_msg_edit(msg, None, embed)
        await asyncio.sleep(3)

        embed = discord.Embed(
            color=user.colour, title="Performing initial calculations..",
            description="iterating through the list..."
        )
        msg = await process_msg_submit(ctx.channel, "Enter the total feats for: ", embed)

        def check(m):
            try:
                int(m.content)
            except ValueError:
                if m.content.lower() == "stop" \
                        and m.author == ctx.message.author and m.channel == ctx.channel:
                    raise TypeError
                elif m.content.lower() == "skip" \
                        and m.author == ctx.message.author and m.channel == ctx.channel:
                    raise IndexError
                elif m.content.lower() not in ["stop", "skip"] \
                        and m.author == ctx.message.author and m.channel == ctx.channel:
                    raise KeyError
            return m.author == ctx.message.author and m.channel == ctx.channel

        for member in members.find({
            "role": {"$in": ["officer", "member", "leader"]}
        }, {
            "_id": 0, "name_lower": 0, "notes": 0
        }).sort([("total_feats", 1)]):

            embed = discord.Embed(
                color=ctx.author.colour, title=f"#{member['#']} : {member['name']} | 🎀 {member['role']}"
            )
            embed.set_thumbnail(url=ctx.guild.icon_url)
            embed.add_field(
                name="⛳ Status",
                value=f"{member['status']} [{member['status_update'].strftime('%d.%b %y')}]"
            )
            embed.add_field(
                name="🏆 Feats | GQ",
                value=f"{member['total_feats']} | {member['weekly_gq']} [Wk{get_time().isocalendar()[1]}]"
            )
            await asyncio.sleep(1)
            await process_msg_edit(msg, None, embed)

            i = 0
            while i < 1:
                try:
                    answer = await self.client.wait_for("message", timeout=180, check=check)
                except IndexError:
                    break
                except TypeError:
                    embed = discord.Embed(colour=colour, title="Exiting..")
                    msg = await process_msg_submit(ctx.channel, None, embed)
                    await process_msg_reaction_add(msg, "✅")
                    i = "cancel"
                    break
                except KeyError:
                    embed = discord.Embed(colour=colour, title="Invalid input")
                    msg = await process_msg_submit(ctx.channel, None, embed)
                    await asyncio.sleep(2)
                    await process_msg_delete(msg, 0)
                    i = 0
                except asyncio.TimeoutError:
                    embed = discord.Embed(colour=colour, title="Timeout! Exiting..")
                    msg = await process_msg_submit(ctx.channel, None, embed)
                    await asyncio.sleep(1)
                    await process_msg_reaction_add(msg, "✅")
                    i = "cancel"
                    break
                else:
                    value = int(answer.content)
                    members.update_one({"name": str(member["name"])}, {"$set": {"total_feats": value}})
                    await process_msg_reaction_add(answer, "✅")
                    await asyncio.sleep(2)
                    await answer.delete()
                    break
            if i == "cancel":
                break
            else:
                continue

    async def admin_manage_guild_update_field(self, ctx, args):

        try:
            reference_id = int(args[1])
        except ValueError:
            find_query = {"name_lower": args[1].lower()}
            reference_id = 1
            name = args[1].lower()
        else:
            find_query = {"#": reference_id}
            name = "kyrvscyl"

        if members.find_one({"name_lower": name}) is None or members.find_one({"#": reference_id}) is None:
            await self.admin_manage_guild_show_approximate(ctx, args[1])

        elif args[2].lower() in ["status"] and args[3].lower() in self.member_status:
            update = {"status": args[3].lower(), "status_update": get_time()}

            if args[3].lower() in ["active", "inactive", "semi-active"]:
                def get_status_code(key):
                    return self.status_code[str(key)]

                update.update({"weekly_gq": get_status_code(args[3].lower()), "role": "member"})

            if args[3].lower() in ["away", "left", "kicked"]:
                update.update({"role": "ex-member"})

            members.update_one(find_query, {"$set": update})
            await process_msg_reaction_add(ctx.message, "✅")

        elif args[2].lower() in ["notes", "note"]:
            members.update_one(find_query, {
                "$push": {
                    "notes": {
                        "officer": ctx.author.name,
                        "time": get_time(),
                        "note": " ".join(args[3::])
                    }
                }
            })
            await process_msg_reaction_add(ctx.message, "✅")

        elif args[2].lower() in ["strikes"]:
            members.update_one(find_query, {
                "$push": {
                    "notes": {
                        "officer": ctx.author.name,
                        "time": get_time(),
                        "note": "🎯 " + " ".join(args[3::])
                    }
                },
                "$inc": {
                    "strikes": 1
                },
                "$set": {
                    "status": "inactive"
                }
            })
            await process_msg_reaction_add(ctx.message, "✅")

        elif args[2].lower() in ["name"]:
            members.update_one(find_query, {"$set": {"name": args[3], "name_lower": args[3].lower()}})
            await process_msg_reaction_add(ctx.message, "✅")

        elif args[2].lower() in ["role"] and args[3].lower() in self.roles:
            update = {"role": args[3].lower()}

            if args[3].lower() in ["applicant"]:
                update.update({"status": "active", "status_update": get_time()})

            members.update_one(find_query, {"$set": update})
            await process_msg_reaction_add(ctx.message, "✅")

            embed = discord.Embed(
                colour=colour, title="Role updating notice",
                description="changes in roles may require to adjust their statuses as well"
            )
            msg = await process_msg_submit(ctx.channel, None, embed)
            await process_msg_delete(msg, 7)

        elif args[2].lower() in ["tfeat"]:

            try:
                total_feat_new = int(args[3])
            except ValueError:
                await process_msg_reaction_add(ctx.message, "❌")
            else:
                members.update_one(find_query, {"$set": {"total_feats": total_feat_new}})
                await process_msg_reaction_add(ctx.message, "✅")

        elif args[2].lower() in ["gq"]:

            try:
                value = int(args[3])
            except ValueError:
                await process_msg_reaction_add(ctx.message, "❌")
            else:
                def get_code_status(key):
                    return self.code_status[str(key)]

                if value in [30, 60, 90]:
                    members.update_one(find_query, {
                        "$set": dict(
                            status=get_code_status(value),
                            status_update=get_time(),
                            weekly_gq=value
                        )
                    })
                else:
                    await process_msg_reaction_add(ctx.message, "❌")

        else:
            await process_msg_reaction_add(ctx.message, "❌")

    async def admin_manage_guild_update_performance(self, ctx, status, weekly_gq, user):

        embed = discord.Embed(
            color=ctx.author.colour, title="Batch updating",
            description=f"enter the ID/names of the {status} members separated by spaces"
        )
        embed.add_field(name="Example", value="*`kyrvsycl xann happybunny shaly, 5, 7, 172`*")
        await process_msg_submit(ctx.channel, None, embed)

        def check(m):
            return m.author == ctx.message.author and m.channel.id == ctx.channel.id

        async with ctx.channel.typing():
            try:
                submitted_list = await self.client.wait_for("message", timeout=360, check=check)
            except asyncio.TimeoutError:
                embed = discord.Embed(
                    colour=colour, title="Batch updating cancelled", description=f"the submission time lapsed"
                )
                await process_msg_submit(ctx.channel, None, embed)
                return
            else:
                accepted, not_accepted, already_inactive = [], [], []

                for member in submitted_list.content.split(" "):

                    try:
                        search = int(member)
                    except ValueError:
                        search = member.lower()
                        find_query = {"name_lower": search}
                    else:
                        find_query = {"#": search}

                    if members.find_one(find_query) is not None:
                        query = members.find_one(find_query, {"_id": 0, "name": 1, "status": 1})

                        if query["status"] == status:
                            already_inactive.append(query["name"])
                        else:
                            accepted.append(query["name"])
                    else:
                        not_accepted.append(member)

        values = [already_inactive, accepted, not_accepted]
        values_formatted = []

        for value in values:
            if len(value) == 0:
                values_formatted.append("None")
            else:
                values_formatted.append(", ".join(value))

        timeout = 120
        embed = discord.Embed(
            colour=ctx.author.colour, title="Revision summary",
            description=f"react within {timeout} seconds to confirm the changes", timestamp=get_timestamp()
        )
        embed.add_field(
            name=f"{len(not_accepted)} already inactive {pluralize('member', len(not_accepted))}",
            value=values_formatted[0], inline=False
        )
        embed.add_field(
            name=f"{len(accepted)} new inactive {pluralize('member', len(accepted))}",
            value=values_formatted[1], inline=False
        )
        embed.add_field(
            name=f"{len(not_accepted)} invalid {pluralize('member', len(not_accepted))}",
            value=values_formatted[2], inline=False
        )
        msg = await process_msg_submit(ctx.channel, None, embed)
        await process_msg_reaction_add(msg, "✅")

        def check(r, u):
            return u == ctx.author and str(r.emoji) == "✅" and msg.id == r.message.id

        try:
            await self.client.wait_for("reaction_add", timeout=timeout, check=check)
        except asyncio.TimeoutError:
            embed = discord.Embed(
                colour=user.colour, description=f"there was no confirmation received",
                title="Batch update cancelled", timestamp=get_timestamp()
            )
            embed.set_footer(text=user.display_name, icon_url=user.avatar_url)
            await process_msg_submit(ctx.channel, None, embed)
        else:
            async with ctx.channel.typing():
                for member in accepted:
                    members.update_one({
                        "name_lower": member.lower()}, {
                        "$set": {
                            "status": status,
                            "weekly_gq": weekly_gq,
                            "status_update": get_time()
                        }
                    })

                embed = discord.Embed(
                    colour=user.colour, title=f"{status.capitalize()} list batch update successful",
                    description=", ".join(accepted), timestamp=get_timestamp()
                )
                embed.set_footer(text=f"{len(accepted)} inactive {pluralize('member', len(accepted))}")
                await process_msg_submit(ctx.channel, None, embed)

    async def admin_manage_guild_show_field_status(self, ctx, args):

        listings_formatted = []
        find_query = {"status": args[2]}
        project = {"_id": 0, "name": 1, "status_update": 1, "#": 1}

        for member in members.find(find_query, project).sort([("status_update", 1)]):
            number = lengthen_code_3(member["#"])
            status_update_formatted = member["status_update"].strftime("%d.%b %y")
            listings_formatted.append(f"`{number}: {status_update_formatted}` | {member['name']}\n")

        noun = pluralize("result", len(listings_formatted))
        content = f"I've got {len(listings_formatted)} {noun} for members with status {args[2].lower()}"
        await self.admin_manage_guild_paginate_embeds(ctx, listings_formatted, content)

    async def admin_manage_guild_show_current_members(self, ctx):

        formatted_list = []
        find_query = {"role": {"$in": ["officer", "member", "leader", "trader"]}}
        project = {"_id": 0, "name": 1, "role": 1, "#": 1, "status": 1, "strikes": 1}

        for member in members.find(find_query, project).sort([("total_feats", -1)]):
            role = self.get_shortened_code(member["role"])
            status = self.get_shortened_code(member["status"])
            number = lengthen_code_3(member["#"])
            strike = member['strikes']
            formatted_list.append(f"`{number}: {role}` | `{status}` | `{strike}` | {member['name']}\n")

        noun = pluralize("member", len(formatted_list))
        content = f"There are {len(formatted_list)} {noun} currently in the guild"
        await self.admin_manage_guild_paginate_embeds(ctx, formatted_list, content)

    async def admin_manage_guild_show_current_members_strikes(self, ctx):

        formatted_list = []
        find_query = {"role": {"$in": ["officer", "member", "leader", "trader"]}, "strikes": {"$gt": 0}}
        project = {"_id": 0, "name": 1, "role": 1, "#": 1, "status": 1, "strikes": 1}

        for member in members.find(find_query, project).sort([("strikes", -1)]):
            role = self.get_shortened_code(member["role"])
            status = self.get_shortened_code(member["status"])
            number = lengthen_code_3(member["#"])
            strike = member['strikes']
            formatted_list.append(f"`{number}: {role}` | `{status}` | `{strike}` | {member['name']}\n")

        noun = pluralize("member", len(formatted_list))
        content = f"There are {len(formatted_list)} {noun} with strikes in the guild"
        await self.admin_manage_guild_paginate_embeds(ctx, formatted_list, content)

    async def admin_manage_guild_show_startswith(self, ctx, args):

        formatted_list = []
        find_query = {"name_lower": {"$regex": f"^{args[2].lower()}"}}
        project = {"_id": 0, "name": 1, "role": 1, "#": 1, "status": 1}

        for member in members.find(find_query, project).sort([("name_lower", 1)]):
            role = self.get_shortened_code(member["role"])
            status = self.get_shortened_code(member["status"])
            number = lengthen_code_3(member["#"])
            formatted_list.append(f"`{number}: {role}` | `{status}` | {member['name']}\n")

        noun = pluralize("result", len(formatted_list))
        content = f"I've got {len(formatted_list)} {noun} for names starting with __{args[2].lower()}__"
        await self.admin_manage_guild_paginate_embeds(ctx, formatted_list, content)

    async def admin_manage_guild_show_stats(self, ctx):

        query_in_guild = {"$in": ["officer", "member", "leader", "trader"]}

        members_all = members.count_documents({"role": query_in_guild})

        members_actv = members.count_documents({"role": query_in_guild, "status": "active"})
        members_inac = members.count_documents({"role": query_in_guild, "status": "inactive"})
        members_onlv = members.count_documents({"role": query_in_guild, "status": "on-leave"})
        members_smac = members.count_documents({"role": query_in_guild, "status": "semi-active"})
        members_away = members.count_documents({"role": "ex-member", "status": "away"})

        users_apl = members.count_documents({"role": "applicant"})
        users_blk = members.count_documents({"role": "blacklist"})
        users_trd = members.count_documents({"role": "trader"})

        description = \
            f"```" \
            f"• Total Accounts    :: {members.count_documents({}):,d}\n" \
            f"• Guild Occupancy   :: {members_all:,d}/170\n" \
            f"  • Traders         :: {users_trd:,d}\n" \
            f"  • Active          :: {members_actv:,d}\n" \
            f"  • Semi-active     :: {members_smac:,d}\n" \
            f"  • Inactive        :: {members_inac:,d}\n" \
            f"  • On-leave        :: {members_onlv:,d}\n" \
            f"  • Away            :: {members_away:,d}\n" \
            f"  • ~ GQ/week       :: {members_actv * 90 + members_smac * 30:,d}\n" \
            f"• Applicants        :: {users_apl:,d}\n" \
            f"• Blacklisted       :: {users_blk:,d}" \
            f"```"

        embed = discord.Embed(
            color=ctx.author.colour, title="🔱 Guild Statistics",
            description=f"{description}", timestamp=get_timestamp()
        )
        embed.set_thumbnail(url=ctx.guild.icon_url)
        await process_msg_submit(ctx.channel, None, embed)

    async def admin_manage_guild_show_all(self, ctx, sort):

        listings_formatted = []
        find_query = {}
        project = {"_id": 0, "name": 1, "role": 1, "#": 1, "status": 1}

        for member in members.find(find_query, project).sort(sort):
            role = self.get_shortened_code(member["role"])
            status = self.get_shortened_code(member["status"])
            number = lengthen_code_3(member["#"])
            name = member['name']
            listings_formatted.append(f"`{number}: {role}` | `{status}` | {name} \n")

        noun = pluralize("account", len(listings_formatted))
        content = f"There are {len(listings_formatted)} registered {noun}"
        await self.admin_manage_guild_paginate_embeds(ctx, listings_formatted, content)

    async def admin_manage_guild_show_field_role(self, ctx, args):

        listings_formatted = []
        filter_query = {"role": args[2]}
        project = {"_id": 0, "name": 1, "status_update": 1, "#": 1, "role": 1}

        for member in members.find(filter_query, project).sort([("status_update", 1)]):
            number = lengthen_code_3(member["#"])
            status_update_formatted = member["status_update"].strftime("%d.%b %y")
            listings_formatted.append(f"`{number}: {status_update_formatted}` | {member['name']}\n")

        noun = pluralize("result", len(listings_formatted))
        content = f"I've got {len(listings_formatted)} {noun} for members with role {args[2].lower()}"
        await self.admin_manage_guild_paginate_embeds(ctx, listings_formatted, content)

    async def admin_manage_guild_show_profile(self, ctx, args):

        try:
            name_id = int(args[1])
        except ValueError:
            member = members.find_one({"name_lower": args[1].lower()}, {"_id": 0})
        else:
            member = members.find_one({"#": name_id}, {"_id": 0})

        if member is None:
            await self.admin_manage_guild_show_approximate(ctx, args[1])
        else:
            code, name, role = member['#'], member['name'], member['role']
            status, status_update = member["status"], member['status_update']
            strikes = member["strikes"]

            def get_emoji_role(x):
                return self.roles_emoji[x]

            role_emoji = get_emoji_role(member['role'])

            if strikes > 0:
                strikes_formatted, i = "", 0
                while i < strikes:
                    strikes_formatted += "🎯"
                    i += 1
            else:
                strikes_formatted = None

            embed = discord.Embed(
                color=ctx.author.colour, timestamp=get_timestamp(),
                title=f"#{code} : {name} | {role_emoji} {role.title()}",
            )
            embed.set_thumbnail(url=ctx.guild.icon_url)
            embed.add_field(name="⛳ Status", value=f"{status.title()} [{status_update.strftime('%d.%b %y')}]")
            embed.add_field(name="🏹 Strikes", value=strikes_formatted)

            if not member["notes"]:
                embed.add_field(name="🗒 Notes", value="No notes yet.")

            elif len(member["notes"]) != 0:
                notes = ""
                for note in member["notes"]:
                    entry = f"[{note['time'].strftime('%d.%b %y')} | {note['officer']}]: {note['note']}\n"
                    notes += entry

                embed.add_field(name="🗒 Notes", value=notes, inline=False)
            await process_msg_submit(ctx.channel, None, embed)

    async def admin_manage_guild_show_approximate(self, ctx, member_name):

        members_search = members.find({"name_lower": {"$regex": f"^{member_name[:2].lower()}"}}, {"_id": 0})

        results_approximate = []
        for result in members_search:
            results_approximate.append(f"{result['#']}/{result['name']}")

        embed = discord.Embed(
            colour=colour, title="Invalid query",
            description=f"The ID/name `{member_name}` returned no results"
        )
        embed.add_field(name="Possible matches", value="*{}*".format(", ".join(results_approximate)))
        await process_msg_submit(ctx.channel, None, embed)

    async def admin_manage_guild_add_member(self, ctx, args):

        if members.find_one({"name_lower": args[2].lower()}) is None:
            members.insert_one({
                "#": members.count_documents({}) + 1,
                "name": args[2],
                "role": args[1].lower(),
                "status": "active",
                "notes": [],
                "name_lower": args[2].lower(),
                "total_feats": 0,
                "weekly_gq": 30,
                "status_update": get_time(),
                "strikes": 0
            })
            await process_msg_reaction_add(ctx.message, "✅")

        else:
            embed = discord.Embed(
                title="Invalid name", colour=colour,
                description="that name already exists in the database"
            )
            await process_msg_submit(ctx.channel, None, embed)

    async def admin_manage_guild_add_delete(self, ctx, args):

        if members.find_one({"name": args[1]}) is not None:

            members.delete_one({"name": args[1]})
            await process_msg_reaction_add(ctx.message, "✅")

            name_id = 1
            for member in members.find({}, {"_id": 0, "name": 1}):
                members.update_one({"name": member["name"]}, {"$set": {"#": name_id}})
                name_id += 1

        else:
            embed = discord.Embed(
                colour=colour, title="Invalid user",
                descrption="Input the exact name including the letter cases"
            )
            await process_msg_submit(ctx.channel, None, embed)

    async def admin_manage_guild_paginate_embeds(self, ctx, list_formatted, caption):

        page, lines_max = 1, 20
        page_total = ceil(len(list_formatted) / lines_max)
        if page_total == 0:
            page_total = 1

        def embed_new_create(page_new):

            end = page_new * lines_max
            start = end - lines_max
            description_new = "".join(list_formatted[start:end])

            embed_new = discord.Embed(
                color=ctx.author.colour, title="🔱 Guild Registry",
                description=f"{description_new}", timestamp=get_timestamp()
            )
            embed_new.set_footer(text=f"Page: {page_new} of {page_total}")
            embed_new.set_thumbnail(url=ctx.guild.icon_url)
            return embed_new

        msg = await process_msg_submit(ctx.channel, caption, embed_new_create(page))

        emojis_add = ["⬅", "➡"]
        for emoji in emojis_add:
            await process_msg_reaction_add(msg, emoji)

        def check(r, u):
            return u != self.client.user and r.message.id == msg.id and str(r.emoji) in emojis_add

        while True:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=180, check=check)
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
                await process_msg_edit(msg, caption, embed_new_create(page))
                await process_msg_reaction_remove(msg, str(reaction.emoji), user)


def setup(client):
    client.add_cog(Admin(client))
