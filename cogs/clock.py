"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import discord, pytz
from cogs.mongo.db import books
from discord.ext import tasks, commands
from datetime import datetime

# Get the clock channels
clock_channels = []
for guild_clock in books.find({}, {"clock": 1, "_id": 0}):
	if guild_clock["clock"] != "":
		clock_channels.append(guild_clock["clock"])

# Date and Time
tz_target = pytz.timezone("America/Atikokan")
list_clock = ["", "🕐", "🕜", "🕑", "🕑", "🕒", "🕞", "🕓", "🕓", "🕔", "🕠", "🕕", "🕕", "🕖", "🕢", "🕗", "🕣", "🕘", "🕤", "🕙", "🕥", "🕚", "🕦", "🕛", "🕧"]

class Clock(commands.Cog):
	
	def __init__(self, client):
		self.client = client
	
	def current_time1(self):
		time_current1 = (datetime.now(tz=tz_target)).strftime("%I:%M %p EST")
		return time_current1
	
	@commands.Cog.listener()
	async def on_ready(self):
		self.clock_update.start()
	
	@tasks.loop(seconds=30)
	async def clock_update(self):
		
		hour = datetime.now(tz=pytz.timezone("America/Atikokan")).strftime("%H")
		minute = datetime.now(tz=pytz.timezone("America/Atikokan")).strftime("%M")
		
		for clock_channel in clock_channels:
			clock = self.client.get_channel(int(clock_channel))

			def get_emoji(hour, minute):
				if int(minute) >= 30:
					emoji_clock_index = int(hour)*2 + 1
				else:
					emoji_clock_index = int(hour)*2
				emoji_clock = list_clock[int(emoji_clock_index)]
				return emoji_clock
			
			await clock.edit(name="{} {}".format(get_emoji(hour, minute), self.current_time1()))
	
def setup(client):
	client.add_cog(Clock(client))