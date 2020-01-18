"""
Clock Module
Miketsu, 2020
"""

import sys

from discord.ext import commands

from cogs.development import Economy
from cogs.encounter import Encounter
from cogs.events import Events
from cogs.ext.initialize import *
from cogs.frames import Frames
from cogs.quest import Expecto, owls_restock
from cogs.souls import Souls
from cogs.summon import Summon


class Clock(commands.Cog):

    def __init__(self, client):

        self.client = client
        self.prefix = self.client.command_prefix

    async def perform_delete_secret_channels(self):

        for entry in guilds.find({}, {"_id": 0, "eeylops-owl-emporium": 1, "ollivanders": 1, "gringotts-bank": 1}):
            for secret in entry:
                for key in entry[secret]:
                    if key == "id":
                        channel = self.client.get_channel(int(entry[secret][key]))
                        await process_channel_delete(channel)

    async def perform_penalize_score(self):

        print(f"Penalizing all ongoing quest1 users")
        quests.update_many({"quest1.status": "ongoing", "quest1.score": {"$gt": 5}}, {"$inc": {"quest1.$.score": -5}})

    async def perform_reset_actions(self):

        print(f"Resetting all quest1 actions to 0")
        quests.update_many({"quest1.status": "ongoing"}, {"$set": {"quest1.$.actions": 0}})

    async def perform_reset_purchase(self):

        print(f"Resetting all quest1 purchases to True")
        quests.update_many({"quest1.purchase": False}, {"$set": {"quest1.$.purchase": True}})

    @commands.Cog.listener()
    async def on_ready(self):

        await self.clock_start()

    async def clock_start(self):

        if config.find_one({"var": 1}, {"_id": 0, "clock": 1})["clock"] is False:

            config.update_one({"var": 1}, {"$set": {"clock": True}})
            print("Initializing a clock instance")
            push_note("Miketsu Bot", "Initializing a clock instance")

            while True:
                try:
                    if get_time().strftime("%S") == "00":
                        await self.clock_start_update()
                        await asyncio.sleep(1)
                    else:
                        await asyncio.sleep(1)

                except KeyboardInterrupt:
                    push_note("Miketsu Bot", "Stopping a concurrent function")
                    break
                except:
                    push_note("Miketsu Bot", "Ignoring exception on clock processing ~10s")
                    continue

    async def clock_start_update(self):

        time_current = get_time().strftime("%H:%M EST | %a")
        hour_minute = get_time().strftime("%H:%M")
        minute_hand = get_time().strftime("%M")
        hour_24 = get_time().strftime("%H")
        hour_12 = get_time().strftime("%I")
        weather1 = weathers.find_one({"weather1": {"$type": "string"}}, {"weather1": 1})["weather1"]
        weather2 = weathers.find_one({"weather2": {"$type": "string"}}, {"weather2": 1})["weather2"]

        if minute_hand == "00":
            def generate_weather(hour):
                if 18 > hour >= 6:
                    w_1 = random.choice(list(weathers.find_one({"type": "day"}, {"_id": 0, "type": 0}).values()))
                    w_2 = ""
                    weathers.update_one({"weather1": {"$type": "string"}}, {"$set": {"weather1": w_1}})
                    weathers.update_one({"weather2": {"$type": "string"}}, {"$set": {"weather2": w_2}})
                else:
                    w_1 = random.choice(list(weathers.find_one({"type": "night"}, {"_id": 0, "type": 0}).values()))
                    w_2 = random.choice(list(weathers.find_one({"type": "moon"}, {"_id": 0, "type": 0}).values()))
                    weathers.update_one({"weather1": {"$type": "string"}}, {"$set": {"weather1": w_1}})
                    weathers.update_one({"weather2": {"$type": "string"}}, {"$set": {"weather2": w_2}})
                return w_1, w_2

            weather1, weather2 = generate_weather(int(hour_24))

        def get_emoji_clock(hours, minutes):
            if int(minutes) >= 30:
                emoji_clock_index = (int(hours) * 2) + 2
            else:
                emoji_clock_index = (int(hours) * 2) + 1

            emoji_clock = clock_emojis[emoji_clock_index]
            return emoji_clock

        clock = self.client.get_channel(int(id_clock))
        clock_name = f"{get_emoji_clock(hour_12, minute_hand)} {time_current} {weather1} {weather2}"
        print(f"{clock.name} -> {clock_name}")

        if clock.name == clock_name:
            raise KeyboardInterrupt
        else:
            await process_channel_edit(clock, clock_name, None)

        try:
            if minute_hand == "00":
                await self.perform_penalize_score()
                await self.perform_reset_actions()
                await self.perform_reset_purchase()
                await Expecto(self.client).expecto_sendoff_report()
                await Expecto(self.client).expecto_send_off_complete_quest1()
                await self.perform_delete_secret_channels()
                await Events(self.client).events_reminders_announce_bidding(get_time().strftime("%b %d, %Y %H:%M"))
                await Events(self.client).events_reminders_announce_others()

            if hour_minute in ["02:00", "08:00", "14:00", "20:00"]:
                await owls_restock()

            if hour_minute in ["06:00", "18:00"]:
                await Encounter(self.client).enc_nether_announce()

            if hour_minute == "00:00":
                await Encounter(self.client).enc_perform_reset_boss_check()
                await Economy(self.client).economy_issue_rewards_reset_daily()

                if get_time().strftime("%a").lower() == "mon":
                    await Economy(self.client).economy_issue_rewards_reset_weekly()

                await Frames(self.client).frames_automate()
                await Summon(self.client).summon_perform_streak_penalize()
                await Frames(self.client).achievements_process_daily()
                await Souls(self.client).souls_rewards_generate()

            if minute_hand == "00":
                await Frames(self.client).achievements_process_hourly()

        except:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            push_note("Miketsu Bot", f"{exc_type}, Line {exc_tb.tb_lineno}")
            print("clock.py error: ", f"{exc_type}, Line {exc_tb.tb_lineno}")

    @commands.command(aliases=["tick"])
    @commands.check(check_if_user_has_any_admin_roles)
    async def clock_start_manual(self, ctx):

        config.update_one({"var": 1}, {"$set": {"clock": False}})
        await process_msg_reaction_add(ctx.message, "✅")
        await self.clock_start()


def setup(client):
    client.add_cog(Clock(client))
