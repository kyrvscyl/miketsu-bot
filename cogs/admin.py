"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import discord, json, re, shutil
from discord.ext import commands
from datetime import datetime
from config.guild import guildID

timeStamp2 = datetime.now().strftime("%m.%d.%Y.%H%M")

class Admin(commands.Cog):
	
	def __init__(self, client):
		self.client = client
	
	@commands.command()
	@commands.is_owner()
	async def iterate_data(self, ctx):
	
		with open("../data/users.json", "r") as f:
			users = json.load(f)

		for user in users:
			users[user]["friendship"] = 0
	
		with open("../data/users.json", "w") as f:
			json.dump(users, f, indent="\t")
	
	@commands.command()
	@commands.is_owner()
	async def reset(self, ctx, *args):
		
		# Reset daily
		if args[0] == "daily":
			with open("../data/daily.json","r") as f:
				daily = json.load(f)
			
			daily["daily"].clear()
			
			for user in daily["raid"]:
				daily["raid"][user]["raid_count"] = 0
			
			with open("../data/daily.json", "w") as f:
				json.dump(daily, f, indent="\t")
			
			msg = ":confetti_ball: Daily rewards have been reset."
			await ctx.channel.send(msg)
			
		# Resets weekly
		elif args[0] == "weekly":
			with open("../data/daily.json","r") as f:
				daily = json.load(f)
				
			daily["weekly"].clear()
			
			with open("../data/daily.json", "w") as f:
				json.dump(daily, f, indent="\t")
				
			msg = ":confetti_ball: Weekly rewards have been reset."
			await ctx.channel.send(msg)
			
		# Resets the boss	
		elif args[0] == "boss":
			with open("../data/boss.json", "r") as f:
				boss = json.load(f)
				
			for Bosses in boss:
				boss[Bosses]["discoverer"] = "None"
				boss[Bosses]["level"] = 0
				boss[Bosses]["damage_cap"] = 0
				boss[Bosses]["total_hp"] = 0
				boss[Bosses]["current_hp"] = 0
				boss[Bosses]["rewards"].clear()
				boss[Bosses]["challengers"].clear()
			
			with open("../data/boss.json", "w") as f:
				json.dump(boss, f, indent="\t")	

			msg = "Assembly Boss encounter has been reset."
			await ctx.channel.send(msg)
		
		else:
			msg = "Please provide a valid argument: daily, weekly, or boss"
			await ctx.channel.send(msg)
	
	@commands.command(aliases=["c", "clear", "purge", "cl"])
	async def deleteMsg(self, ctx, amount=2):
		if ctx.channel.permissions_for(ctx.author).administrator == True:
			await ctx.channel.purge(limit=amount+1)
	
	@commands.command(aliases=["bc"])
	async def broadcast(self, ctx, *args):
		if ctx.channel.permissions_for(ctx.author).administrator == True:
			channel = self.client.get_channel(int(re.sub('[<>#]', '', args[0])))
			msg = ":loudspeaker: {}".format(" ".join(args[1:]))
			await channel.send(msg)
	
	@commands.command(alises=["backup"])
	@commands.is_owner()
	async def backupData(self, ctx):
		channel = self.client.get_channel(584638230729850880)
		shutil.make_archive("backup", "zip", "../data/")
		
		backup = discord.File("backup.zip", filename="{}.{}.zip".format(self.client.get_guild(guildID), timeStamp2))
		await channel.send(file=backup)	
	
def setup(client):
	client.add_cog(Admin(client))