"""
Events Module
Miketsu, 2020
"""
import asyncio
from datetime import timedelta

from discord.ext import commands

from cogs.ext.initialize import *


class Events(commands.Cog):

    def __init__(self, client):

        self.client = client
        self.prefix = self.client.command_prefix

    async def perform_announce_reminders_bidding(self, date_time):

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

    async def perform_announce_reminders(self):

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
                    title="⏰ Reminder", color=16733562,
                    description=reminder['description'].replace('\\n', '\n'),
                    timestamp=get_timestamp()
                )
                headlines_channel = self.client.get_channel(int(id_headlines))
                await process_msg_submit(headlines_channel, content, embed)

                reminder_new = events.find_one({"code": reminder["code"], "status": True}, {"_id": 0})

                if reminder_new["next"] > reminder["end"]:
                    events.update_one({"code": reminder["code"], "status": True}, {"$set": {"status": False}})

    @commands.command(aliases=["events", "event", "e"])
    @commands.check(check_if_user_has_any_admin_roles)
    async def events_manipulate(self, ctx, *args):

        if len(args) == 0:
            embed = discord.Embed(
                title="events, e",
                description="manipulate event settings for reminders, etc.",
                color=colour
            )
            embed.add_field(
                name="Arguments",
                value="activate, deactivate",
                inline=False
            )
            await process_msg_submit(ctx.channel, None, embed)

        elif len(args) == 1 and args[0].lower() in ["activate", "a"]:
            embed = discord.Embed(
                title="events activate, e a",
                description="activate repetitive events",
                color=colour
            )
            embed.add_field(
                name="Timing",
                value="now, next",
                inline=False
            )
            embed.add_field(
                name="Event codes",
                value="coin chaos [cc], fortune temple [ft]",
                inline=False
            )
            embed.add_field(
                name="Example",
                value="*`;events act next cc`* - next Wed patch\n"
                      "*`;events act now cc`* - activates this week",
                inline=False
            )
            await process_msg_submit(ctx.channel, None, embed)

        elif len(args) == 1 and args[0].lower() in ["deactivate", "d"]:
            embed = discord.Embed(
                title="events deactivate, e d",
                description="deactivate events",
                color=colour
            )
            embed.add_field(
                name="Event codes",
                value="coin chaos [cc], fortune temple [ft]",
                inline=False
            )
            embed.add_field(
                name="Example",
                value="*`;events d cc`*\n",
                inline=False
            )
            await process_msg_submit(ctx.channel, None, embed)

        elif len(args) == 3 and args[0].lower() in ["activate", "a"] \
                and args[1].lower() in ["now", "next"] and args[2].lower() in ["cc", "ft"]:
            await self.events_manipulate_activate(ctx, args[2].lower(), args[1].lower())

        elif len(args) == 2 and args[0].lower() in ["deactivate", "d"] and args[1].lower() in ["cc", "ft"]:

            action = events.update_one({"code": args[1].lower(), "status": True}, {"$set": {"status": False}})

            if action.modified_count == 0:
                embed = discord.Embed(
                    title="Invalid action",
                    description="this event is already deactivated",
                    color=colour
                )
                await process_msg_submit(ctx.channel, None, embed)

            else:
                await process_msg_reaction_add(ctx.message, "✅")

        else:
            await process_msg_reaction_add(ctx.message, "❌")

    async def events_manipulate_activate(self, ctx, event, timing):

        if timing.lower() == "now":
            offset = (get_time().weekday() - 2) % 7
            get_patch_start_day = (get_time() - timedelta(days=offset)).strftime("%Y-%m-%d")
        else:
            offset = (get_time().weekday() - 2) % 7
            get_patch_start_day = (get_time() + timedelta(days=offset)).strftime("%Y-%m-%d")

        date_absolute = datetime.strptime(get_patch_start_day, "%Y-%m-%d")
        request = events.find_one({"code": event}, {"_id": 0})

        date_next = date_absolute + timedelta(days=request['delta']) - timedelta(hours=request['delta_hr'])
        date_start = date_absolute

        if timing.lower() == "now":
            date_start = datetime.strptime(get_time().strftime("%Y-%m-%d"), "%Y-%m-%d")
            date_next = date_start + timedelta(days=request['delta']) - timedelta(hours=request['delta_hr'])

            if date_start < datetime.strptime(get_time().strftime("%Y-%m-%d %H:%M"), "%Y-%m-%d %H:%M"):
                date_start = date_start + timedelta(days=1)
                date_next = date_next + timedelta(days=1)

        date_end = date_absolute + timedelta(days=request['duration']) - timedelta(hours=request['delta_hr'])

        events.update_one({
            "code": event,
        }, {
            "$set": {
                "status": True,
                "last": None,
                "next": date_next,
                "start": date_start,
                "end": date_end
            }
        })
        await asyncio.sleep(2)
        request = events.find_one({"code": event}, {"_id": 0})
        role_id = request['role_id']

        embed = discord.Embed(
            title="Event activation",
            description=f"Title: {request['event'].title()}\n"
                        f"Duration: `{date_start.strftime('%Y-%m-%d | %a')}` until "
                        f"`{date_end.strftime('%Y-%m-%d | %a')}`",
            color=colour,
            timestamp=get_timestamp()
        )
        embed.add_field(
            name="Action",
            value=f"Pings <@&{role_id}> role; {request['delta_hr']} hours before the reset at <#{id_headlines}>"
        )
        await process_msg_submit(ctx.channel, None, embed)


def setup(client):
    client.add_cog(Events(client))
