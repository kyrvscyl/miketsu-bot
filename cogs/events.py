"""
Events Module
Miketsu, 2020
"""

from datetime import timedelta

from PIL import Image
from discord.ext import commands

from cogs.ext.initialize import *


class Events(commands.Cog):

    def __init__(self, client):

        self.client = client
        self.prefix = self.client.command_prefix

    async def events_reminders_announce_bidding(self, date_time):

        query = events.find_one({"event": "showdown bidding", "dates": date_time}, {"_id": 0})

        if query is not None:
            headlines_channel = self.client.get_channel(int(id_headlines))
            listings_dates = query["dates"]

            content = f"<@&{id_golden_galleons}>"
            embed = discord.Embed(
                color=colour, timestamp=get_timestamp(),
                title="A new round of showdown bidding has started!"
            )
            embed.description = query["comments"][listings_dates.index(date_time)]
            embed.set_footer(text=f"Round {listings_dates.index(date_time) + 1} of {len(listings_dates)}")

            msg = await process_msg_submit(headlines_channel, content, embed)
            await process_msg_reaction_add(msg, "🔵")
            await process_msg_reaction_add(msg, "🔴")

    async def events_reminders_announce_others(self):

        for reminder in events.find({"status": True}, {"_id": 0}):

            if reminder["next"].strftime("%Y-%m-%d %H:%M") == get_time().strftime("%Y-%m-%d %H:%M"):
                events.update_one({
                    "code": reminder["code"],
                    "status": True
                }, {
                    "$set": {
                        "last": reminder["next"],
                        "next": reminder["next"] + timedelta(days=reminder["delta"])
                    }
                })

                content = f"<@&{reminder['role_id']}>"
                embed = discord.Embed(
                    title="⏰ Reminder", color=16733562, timestamp=get_timestamp(),
                    description=reminder['description'].replace('\\n', '\n'),
                )
                headlines_channel = self.client.get_channel(int(id_headlines))
                await process_msg_submit(headlines_channel, content, embed)

                reminder_new = events.find_one({"code": reminder["code"], "status": True}, {"_id": 0})

                if reminder_new["next"] > reminder["end"]:
                    events.update_one({"code": reminder["code"], "status": True}, {"$set": {"status": False}})

    async def events_manipulate_help(self, ctx):

        embed = discord.Embed(
            title="events, e", color=colour,
            description="manipulate event settings for reminders, etc.",
        )
        embed.add_field(
            name="Arguments", inline=False,
            value="activate, deactivate",
        )
        await process_msg_submit(ctx.channel, None, embed)

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author.bot is True:
            return

        elif not isinstance(message.channel, discord.DMChannel):
            return

        elif len(message.attachments) > 0:

            bot_info = await self.client.application_info()
            owner = self.client.get_user(bot_info.owner.id)

            embed = discord.Embed(color=colour, timestamp=get_timestamp())
            embed.set_author(
                name=f"{message.author}",
                icon_url=message.author.avatar_url
            )
            embed.set_image(url=message.attachments[0].url)
            await process_msg_submit(owner, None, embed)

            content = f"You have successfully submitted an entry"
            await process_msg_submit(message.author, content, embed)

    @commands.command(aliases=["events", "e"])
    @commands.check(check_if_user_has_any_admin_roles)
    async def events_manipulate(self, ctx, *args):

        user = ctx.author

        if len(args) == 0:
            await self.events_manipulate_help(ctx)

        elif len(args) == 1 and args[0].lower() in ["activate", "a"]:

            embed = discord.Embed(
                title="events activate, e a", color=user.colour,
                description="activate repetitive events",
            )
            embed.add_field(
                name="Timing", inline=False,
                value="now, next",
            )
            embed.add_field(
                name="Event codes", inline=False,
                value="coin chaos [cc], fortune temple [ft]",
            )
            embed.add_field(
                name="Example", inline=False,
                value="*`;events a next cc`* - next Wed patch\n"
                      "*`;events a now cc`* - activates this week",
            )
            await process_msg_submit(ctx.channel, None, embed)

        elif len(args) == 1 and args[0].lower() in ["deactivate", "d"]:

            embed = discord.Embed(
                title="events deactivate, e d", colour=user.colour,
                description="deactivate events",
            )
            embed.add_field(
                name="Event codes", inline=False,
                value="coin chaos [cc], fortune temple [ft]",
            )
            embed.add_field(
                name="Example", inline=False,
                value="*`;events d cc`*\n",
            )
            await process_msg_submit(ctx.channel, None, embed)

        elif len(args) == 3 and args[0].lower() in ["activate", "a"]:

            if args[1].lower() in ["now", "next"] and args[2].lower() in ["cc", "ft"]:
                await self.events_manipulate_activate(ctx, args[2].lower(), args[1].lower(), user)

        elif len(args) == 2 and args[0].lower() in ["deactivate", "d"] and args[1].lower() in ["cc", "ft"]:

            action = events.update_one({"code": args[1].lower(), "status": True}, {"$set": {"status": False}})

            if action.modified_count == 0:
                embed = discord.Embed(
                    title="Invalid action", color=user.colour,
                    description="this event is already deactivated",
                )
                await process_msg_submit(ctx.channel, None, embed)

            else:
                await process_msg_reaction_add(ctx.message, "✅")

        else:
            await process_msg_reaction_add(ctx.message, "❌")

    async def events_manipulate_activate(self, ctx, event, timing, user):

        if timing.lower() == "now":
            offset = (get_time().weekday() - 2) % 7
            get_patch_start_day = (get_time() - timedelta(days=offset)).strftime("%Y-%m-%d")
        else:
            offset = (get_time().weekday() - 2) % 7
            get_patch_start_day = (get_time() + timedelta(days=offset)).strftime("%Y-%m-%d")

        date_absolute = datetime.strptime(get_patch_start_day, "%Y-%m-%d")
        query = events.find_one({"code": event}, {"_id": 0})

        date_next = date_absolute + timedelta(days=query['delta']) - timedelta(hours=query['delta_hr'])
        date_start = date_absolute

        if timing.lower() == "now":
            date_start = datetime.strptime(get_time().strftime("%Y-%m-%d"), "%Y-%m-%d")
            date_next = date_start + timedelta(days=query['delta']) - timedelta(hours=query['delta_hr'])

            if date_start < datetime.strptime(get_time().strftime("%Y-%m-%d %H:%M"), "%Y-%m-%d %H:%M"):
                date_start = date_start + timedelta(days=1)
                date_next = date_next + timedelta(days=1)

        date_end = date_absolute + timedelta(days=query['duration']) - timedelta(hours=query['delta_hr'])

        events.update_one({
            "code": event, }, {
            "$set": {
                "status": True,
                "last": None,
                "next": date_next,
                "start": date_start,
                "end": date_end
            }
        })
        await asyncio.sleep(2)
        query = events.find_one({"code": event}, {"_id": 0})
        role_id = query['role_id']

        embed = discord.Embed(
            title="Event activation",
            description=f"Title: {query['event'].title()}\n"
                        f"Duration: `{date_start.strftime('%Y-%m-%d | %a')}` until "
                        f"`{date_end.strftime('%Y-%m-%d | %a')}`",
            color=user.colour, timestamp=get_timestamp()
        )
        embed.add_field(
            name="Action", inline=False,
            value=f"Pings <@&{role_id}> role; {query['delta_hr']} hours before the reset at <#{id_headlines}>"
        )
        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["potg1"])
    @commands.is_owner()
    async def events_start_potg(self, ctx):

        channel = self.client.get_channel(int(id_portrait))

        for index, entry in enumerate(events.find_one({"event": "portrait"}, {"_id": 0})["links"]):

            embed = discord.Embed(
                timestamp=get_timestamp(),
                description=f"{entry['emoji']} *{entry['caption']}*",
                color=colour
            )
            embed.set_author(name=f"PotG Entry #{index + 1}", icon_url=self.client.user.avatar_url)
            embed.set_image(url=entry["link"])
            await process_msg_submit(channel, None, embed)

    @commands.command(aliases=["potg"])
    @commands.is_owner()
    async def events_start_potg(self, ctx):

        channel = self.client.get_channel(int(id_portrait))
        reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]

        embed = discord.Embed(
            description="Voting is now opened until March 21, 2020\n"
                        "Pick your favorite me! :kissing_heart:\n\n"
                        "To change your vote, remove your previous reaction vote first",
            timestamp=get_timestamp(),
            color=colour
        )
        embed.set_author(name="Portrait of the Goddess Vote Casting!", icon_url=self.client.user.avatar_url)

        default_role = ctx.guild.default_role
        msg = await process_msg_submit(channel, default_role, embed)
        guilds.update_one({"server": str(ctx.guild.id)}, {"$set": {"messages.portrait": str(msg.id)}})

        for react in reactions:
            await process_msg_reaction_add(msg, react)

        for index, entry in enumerate(events.find_one({"event": "portrait"}, {"_id": 0})["links"]):

            embed = discord.Embed(
                timestamp=get_timestamp(),
                description=f"{entry['emoji']} *{entry['caption']}*",
                color=colour
            )
            embed.set_author(name=f"PotG Entry #{index + 1}", icon_url=self.client.user.avatar_url)
            embed.set_image(url=entry["link"])
            await process_msg_submit(channel, None, embed)

    @commands.command(aliases=["potg1"])
    @commands.is_owner()
    async def events_start_potg(self, ctx):

        channel = self.client.get_channel(int(id_headlines))

        embed = discord.Embed(
            description="We are pleased to conclude the result of our\n"
                        "**2nd Patronus Anniversary: Portrait of a Goddess Event!**\n\n"
                        "Our winning art with an RNG of 45% is.... :drum:\n\n"
                        "||Our voters' choice!||\n"
                        "||PoaG entry #3: Together, let's bring new life to this wonderful place :sparkles:||\n"
                        "||Congratulations to <@!628219450931544065>!||\n\n"
                        "Our organizer will contact you for your 10USD worth of prize! :gift_heart::ear_of_rice:",
            timestamp=get_timestamp(),
            color=colour
        )
        embed.set_author(name="Portrait of the Goddess Results!", icon_url=self.client.user.avatar_url)

        default_role = ctx.guild.default_role
        await process_msg_submit(channel, default_role, embed)

        for index, entry in enumerate(events.find_one({"event": "portrait"}, {"_id": 0})["links"]):

            embed = discord.Embed(
                timestamp=get_timestamp(),
                description=f"{entry['emoji']} *{entry['caption']}*\n\n"
                            f"Illustration by <@!{entry['id']}>",
                color=colour
            )
            embed.set_author(name=f"PotG Entry #{index + 1}", icon_url=self.client.user.avatar_url)
            embed.set_image(url=entry["link"])
            await process_msg_submit(channel, None, embed)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):

        if self.client.get_user(int(payload.user_id)).bot:
            return

        elif str(payload.channel_id) == id_portrait:

            msg_id = guilds.find_one({
                "server": str(payload.guild_id)
            }, {"_id": 0, "messages.portrait": 1})["messages"]["portrait"]

            if msg_id == str(payload.message_id):

                guild = self.client.get_guild(int(id_guild))
                member = guild.get_member(int(payload.user_id))
                portrait_channel = self.client.get_channel(int(id_portrait))
                msg = await portrait_channel.fetch_message(int(payload.message_id))

                for reaction in msg.reactions:
                    if str(reaction.emoji) == str(payload.emoji):
                        continue

                    users_reacted = await reaction.users().flatten()
                    if member in users_reacted:
                        await process_msg_reaction_remove(msg, payload.emoji, member)

    @commands.command(aliases=["freeze"])
    @commands.is_owner()
    async def events_start_frozen(self, ctx):

        await process_msg_reaction_add(ctx.message, "❄")
        theme_dict = events.find_one({"event": "afd2019"}, {"_id": 0})
        themed_names_id = [str(self.client.user.id)]

        # bot
        with open(f"data/raw/{theme_dict['server'][2]['new']}", "rb") as f:
            image_file = f.read()
        try:
            await self.client.user.edit(avatar=image_file)
        except discord.errors.HTTPException:
            pass

        # server name
        with open(f"data/raw/{theme_dict['server'][1]['new']}", "rb") as f:
            image_file = f.read()
        try:
            await ctx.guild.edit(name=theme_dict["server"][0]["themed"])
            await ctx.guild.edit(icon=image_file)
        except discord.errors.HTTPException:
            pass

        # categories
        for category in theme_dict["categories"]:
            category_id = category["id"]
            category_name_new = category["themed"]
            category = self.client.get_channel(int(category_id))
            await category.edit(name=category_name_new)

        # categories
        for channel in theme_dict["channels"]:
            channel_id = channel["id"]
            channel_name_new = channel["themed"]
            channel_target = self.client.get_channel(int(channel_id))
            await channel_target.edit(name=channel_name_new)

        # roles
        for role in theme_dict["roles"]:
            role_id = role["id"]
            role_name_new = role["themed"]
            role_target = discord.utils.get(ctx.guild.roles, id=int(role_id))
            await role_target.edit(name=role_name_new)

        # officers
        for officer in theme_dict["specials"]:
            officer_id = officer["id"]
            themed_names_id.append(officer_id)
            officer_name_new = officer["themed"]
            officer_target = ctx.guild.get_member(int(officer_id))

            events.update_one({
                "event": "afd2019",
                "officers.id": officer_id
            }, {
                "$set": {
                    "officers.$.name": officer_target.display_name
                }
            })

            try:
                await officer_target.edit(nick=officer_name_new)
            except discord.errors.Forbidden:
                continue

        # members
        for member in ctx.guild.members:
            if str(member.id) in themed_names_id:
                continue

            events.update_one({"event": "afd2019"}, {
                "$push": {
                    "members": {
                        "id": str(member.id),
                        "name": member.display_name,
                        "themed": "Troll"
                    }}
            })
            await member.edit(nick="Troll")

        embed = discord.Embed(
            description=None,
            color=colour
        )
        embed.set_author(name="Elsa", icon_url=None)

    @commands.command(aliases=["defrost"])
    @commands.is_owner()
    async def events_end_frozen(self, ctx):

        await process_msg_reaction_add(ctx.message, "🔥")
        theme_dict = events.find_one({"event": "afd2019"}, {"_id": 0})
        themed_names_id = [str(self.client.user.id)]

        # bot
        with open(f"data/raw/{theme_dict['server'][2]['old']}", "rb") as f:
            image_file = f.read()
        try:
            await self.client.user.edit(avatar=image_file)
        except discord.errors.HTTPException:
            pass

        # server name
        with open(f"data/raw/{theme_dict['server'][1]['old']}", "rb") as f:
            image_file = f.read()
        try:
            await ctx.guild.edit(name=theme_dict["server"][0]["name"])
            await ctx.guild.edit(icon=image_file)
        except discord.errors.HTTPException:
            pass

        # categories
        for category in theme_dict["categories"]:
            category_id = category["id"]
            category_name_new = category["name"]
            category = self.client.get_channel(int(category_id))
            await category.edit(name=category_name_new)

        # categories
        for channel in theme_dict["channels"]:
            channel_id = channel["id"]
            channel_name_new = channel["name"]
            channel_target = self.client.get_channel(int(channel_id))
            await channel_target.edit(name=channel_name_new)

        # roles
        for role in theme_dict["roles"]:
            role_id = role["id"]
            role_name_new = role["name"]
            role_target = discord.utils.get(ctx.guild.roles, id=int(role_id))
            await role_target.edit(name=role_name_new)

        # officers
        for officer in theme_dict["specials"]:
            officer_id = officer["id"]
            themed_names_id.append(officer_id)
            officer_name_new = officer["name"]
            officer_target = ctx.guild.get_member(int(officer_id))

            try:
                await officer_target.edit(nick=officer_name_new)
            except discord.errors.Forbidden:
                continue

        # members
        for member in ctx.guild.members:
            if str(member.id) in themed_names_id:
                continue

            name_original = events.find_one({
                "event": "afd2019",
                "members.id": str(member.id)
            }, {
                "_id": 0,
                "members.$": 1
            })["members"][0]["name"]

            await member.edit(nick=name_original)


def setup(client):
    client.add_cog(Events(client))
