"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import discord, json, asyncio, random
from cogs.mongo.db import users, streak
from discord.ext import commands

# Global static variables
adverb = ["deliberately", "deliberately", "forcefully", "unknowingly", "accidentally", "dishonestly"]
verb = ["snatched", "stole", "took", "looted", "shoplifted", "embezzled"]
noun = ["custody", "care", "guardianship", "control", "ownership"]
comment = ["Horrifying!", "Gruesome!", "Madness!", "Unbelievable!"]

class Frame(commands.Cog):
	
	def __init__(self, client):
		self.client = client
	
	@commands.command()
	@commands.is_owner()
	async def frame(self, ctx):
		await self.frame_starlight(ctx)
		await asyncio.sleep(2)
		await self.frame_blazing(ctx)

	async def frame_starlight(self, ctx):
		server = ctx.guild
		starlight_role = discord.utils.get(server.roles, name="Starlight Sky")
		channel = self.client.get_channel(585104196026630185)
		
		streak_list = []
		for user in streak.find({}, {"_id": 0, "user_id": 1, "SSR_current": 1}):
			streak_list.append((user["user_id"], user["SSR_current"]))
		
		streak_list_new = sorted(streak_list, key=lambda x: x[1], reverse=True)
		starlight_new = server.get_member(int(streak_list_new[0][0]))
		
		if len(starlight_role.members) == 0:

			await starlight_new.add_roles(starlight_role)
			await asyncio.sleep(3)
			
			embed = discord.Embed(color=0xac330f, title = ":incoming_envelope: Hall of Framers Update",
			description = "{}\"s undying luck of not summoning an SSR has earned themselves the Rare Starlight Sky Frame!\n\n:four_leaf_clover: No SSR streak as of posting: {} summons!".format(starlight_new.mention, streak_list_new[0][1]))
			embed.set_thumbnail(url = "https://vignette.wikia.nocookie.net/onmyoji/images/1/17/Frame7.png")
			
			await channel.send(embed=embed)
		
		starlight_current = starlight_role.members[0]
		
		if starlight_current == starlight_new:
			users.update_one({"user_id": str(starlight_current.id)}, {"$inc": {"jades": 2000}})
			
			msg = "{} has earned 2,000{} for wielding the Starlight Sky frame for a day!".format(starlight_current.mention, "<:jade:555630314282811412>")
			await channel.send(msg)
			
		else:
			await starlight_new.add_roles(starlight_role)
			await asyncio.sleep(3)
			await starlight_current.remove_roles(starlight_role)
			await asyncio.sleep(3)
			
			embed = discord.Embed(color=0xac330f, title = ":incoming_envelope: Hall of Framers Update",
			description = "{} {} {} the Rare Starlight Sky Frame from {}\"s {}!! {}\n\n:four_leaf_clover: No SSR streak record as of posting: {} summons!".format(starlight_new.mention, random.choice(adverb), random.choice(verb), starlight_current.mention,  random.choice(noun), random.choice(comment), streak_list_new[0][1]))
			embed.set_thumbnail(url = "https://vignette.wikia.nocookie.net/onmyoji/images/1/17/Frame7.png")
			
			await channel.send(embed=embed)
					
	async def frame_blazing(self, ctx):
		server = ctx.guild
		blazing_role = discord.utils.get(server.roles, name="Blazing Sun")
		channel = self.client.get_channel(585104196026630185)
		
		ssr_list = []
		for user in users.find({}, {"_id": 0, "user_id": 1, "SSR": 1}):
			ssr_list.append((user["user_id"], user["SSR"]))
		
		ssr_list_new = sorted(ssr_list, key=lambda x: x[1], reverse=True)
		blazing_new = server.get_member(int(ssr_list_new[0][0]))
		
		if len(blazing_role.members) == 0:
			
			await blazing_new.add_roles(blazing_role)
			await asyncio.sleep(3)
			
			embed = discord.Embed(color=0xac330f, title = ":incoming_envelope: Hall of Framers Update",
			description = "{}\"s fortune luck earned themselves the Rare Blazing Sun Frame!\n\n:four_leaf_clover: Distinct SSRs under possession: {} shikigamis".format(blazing_new.mention, ssr_list_new[0][1]))
			embed.set_thumbnail(url = "https://vignette.wikia.nocookie.net/onmyoji/images/7/72/Frame62.png")
		
			await channel.send(embed=embed)	
		
		blazing_current = blazing_role.members[0]
		
		if blazing_current == blazing_new:
			users.update_one({"user_id": str(blazing_current.id)}, {"$inc": {"amulets": 10}})
			
			msg = "{} has earned 10{} for wielding the Blazing Sun frame for a day!".format(blazing_current.mention, "<:amulet:573071120685596682>")
			await channel.send(msg)
		
		else :
			await blazing_new.add_roles(blazing_role)
			await asyncio.sleep(3)
			await blazing_current.remove_roles(blazing_role)
			await asyncio.sleep(3)
			
			embed = discord.Embed(color=0xffff80, title=":incoming_envelope: Hall of Framers Update",
			description = "{} {} {} the Rare Blazing Sun Frame from {}\"s {}!! {}\n\n:four_leaf_clover: Distinct SSRs under possession: {} shikigamis".format(blazing_new.mention, random.choice(adverb), random.choice(verb), blazing_current.mention, random.choice(noun), random.choice(comment), ssr_list_new[0][1]))
			embed.set_thumbnail(url="https://vignette.wikia.nocookie.net/onmyoji/images/7/72/Frame62.png")
			await channel.send(embed=embed)
			
def setup(client):
	client.add_cog(Frame(client))