"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import discord, json, asyncio
from discord.ext import commands
from config.guild import eAmulet, eJade, eAmulet2

class Economy(commands.Cog):
	
	def __init__(self, client):
		self.client = client
	
	@commands.command()
	async def buy(self, ctx, *args):
		user = ctx.author
		
		try:
			if args[0] == "amulet":
				await ctx.message.add_reaction(eAmulet2)
				def check(reaction, user):
					return user == ctx.author and str(reaction.emoji) == eAmulet
				
				try:
					reaction, user = await self.client.wait_for("reaction_add", timeout=10.0, check=check)
					
				except asyncio.TimeoutError:
					
					msg = "{}, timeout! You did not click {} on time. Please try again.".format(user.mention, eAmulet)
					await ctx.channel.send(msg)
					
				else:
					await self.buy_amulet(user, ctx)
		
		except IndexError:
			embed = discord.Embed(color=0xffff80, title=":shopping_cart: Shopping District",
				description = "Purchase 11{} for 1000{}. `;buy amulet`".format(eAmulet, eJade))
			embed.set_thumbnail(url=self.client.user.avatar_url)
			await ctx.channel.send(embed=embed)
			
	async def buy_amulet(self, user, ctx):
		
		with open("../data/users.json", "r") as f:
			users = json.load(f)
			
			if str(user.id) in users:
				if users[str(user.id)]["jades"] >= 1000:
					users[str(user.id)]["amulets"] += 11
					amulet = users[str(user.id)]["amulets"]
					users[str(user.id)]["jades"] -= 1000
					
					with open("../data/users.json", "w") as f:
						json.dump(users, f, indent="\t")
						
					msg = "{}, You have bought 11{}. You now have {}{}".format(user.mention, eAmulet, amulet, eAmulet)
					await ctx.channel.send(msg)
					
				else: 
					msg = "{}, You have insufficient {}".format(user.mention, eAmulet)
					await ctx.channel.send(msg)
			else: 
				return
	
def setup(client):
	client.add_cog(Economy(client))