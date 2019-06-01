"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import discord, json, asyncio, random
from discord.ext import commands
from config.guild import guildBroadcast, eJade, eAmulet

class Frame(commands.Cog):
	
	def __init__(self, client):
		self.client = client
	
	@commands.command()
	async def frame(self, ctx):
		if ctx.author.id == 180717337475809281:
			await self.frame_starlight(ctx)
			await asyncio.sleep(2)
			await self.frame_blazing(ctx)
		else:
			msg = "You do not have the power to do this."
			await ctx.channel.send(msg)

	async def frame_starlight(self, ctx):
		server = ctx.guild
		starlight_role = discord.utils.get(server.roles, name="Starlight Sky")
		channel = self.client.get_channel(guildBroadcast)
		
		with open("../data/streak.json", "r") as f:
			streak = json.load(f)
		
		get_streak1 = list(streak.keys())
		get_streak2 = list([streak[i]["SSR_record"] for i in streak])
		get_streak3 = sorted(list(zip(get_streak1, get_streak2)), key=lambda x: x[1], reverse=True)
		
		starlight_new = server.get_member(int(get_streak3[0][0]))
		
		if len(starlight_role.members) == 0:

			await starlight_new.add_roles(starlight_role)
			await asyncio.sleep(3)
			
			embed = discord.Embed(color=0xac330f, title = ":incoming_envelope: Hall of Framers Update",
			description = "{}\"s undying luck of not summoning an SSR has earned themselves the Rare Starlight Sky Frame!\n\n:four_leaf_clover: No SSR streak as of posting: {} summons!".format(starlight_new.mention, get_streak3[0][1]))
			embed.set_thumbnail(url = "https://vignette.wikia.nocookie.net/onmyoji/images/1/17/Frame7.png")
			
			await channel.send(embed=embed)
		
		starlight_current = starlight_role.members[0]
		
		if starlight_current == starlight_new:
			with open("../data/users.json", "r") as f:
				users = json.load(f)

			users[str(starlight_current.id)]["jades"] += 2000
				
			with open("../data/users.json", "w") as f:
				json.dump(users, f, indent="\t")	
			
			msg = "{} has earned 2,000{} for wielding the Starlight Sky frame for a day!".format(starlight_current.mention, eJade)
			await channel.send(msg)
			
		else:
		
			await starlight_new.add_roles(starlight_role)
			await asyncio.sleep(3)
			await starlight_current.remove_roles(starlight_role)
			await asyncio.sleep(3)
			
			adverb = ["deliberately", "deliberately", "forcefully", "unknowingly", "accidentally", "dishonestly"]
			verb = ["snatched", "stole", "took", "looted", "shoplifted", "embezzled"]
			noun = ["custody", "care", "guardianship", "control", "ownership"]
			comment = ["Horrifying!", "Gruesome!", "Madness!", "Unbelievable!"]
			
			embed = discord.Embed(color=0xac330f, title = ":incoming_envelope: Hall of Framers Update",
			description = "{} {} {} the Rare Starlight Sky Frame from {}\"s {}!! {}\n\n:four_leaf_clover: No SSR streak record as of posting: {} summons!".format(starlight_new.mention, adverb[random.randint(1,6)-1], verb[random.randint(1,6)-1], starlight_current.mention, noun[random.randint(1,5)-1], comment[random.randint(1,5)-1], get_streak3[0][1]))
			embed.set_thumbnail(url = "https://vignette.wikia.nocookie.net/onmyoji/images/1/17/Frame7.png")
			
			await channel.send(embed=embed)
					
	async def frame_blazing(self, ctx):
		server = ctx.guild
		blazing_role = discord.utils.get(server.roles, name="Blazing Sun")
		channel = self.client.get_channel(guildBroadcast)
		
		with open("../data/users.json", "r") as f:
			users = json.load(f)
		
		get_score1 = list(users.keys())
		get_score2 = []
		
		for key in users.keys() :
			get_score3 = 0
			for shikigami in users[key]["shikigami"]["SSR"]:
				if users[key]["shikigami"]["SSR"][shikigami]["owned"] != 0:
					get_score3 += 1	
			get_score2.append(get_score3)
		
		get_score4 = sorted(list(zip(get_score1, get_score2)), key=lambda x: x[1], reverse=True)
		
		
		blazing_new = server.get_member(int(get_score4[0][0]))
		
		if len(blazing_role.members) == 0:
			
			await blazing_new.add_roles(blazing_role)
			await asyncio.sleep(3)
			
			embed = discord.Embed(color=0xac330f, title = ":incoming_envelope: Hall of Framers Update",
			description = "{}\"s fortune luck earned themselves the Rare Blazing Sun Frame!\n\n:four_leaf_clover: Distinct SSRs under possession: {} shikigamis".format(blazing_new.mention, get_score4[0][1]))
			embed.set_thumbnail(url = "https://vignette.wikia.nocookie.net/onmyoji/images/7/72/Frame62.png")
		
			await channel.send(embed=embed)	
		
		blazing_current = blazing_role.members[0]
		
		if blazing_current == blazing_new:
			with open("../data/users.json", "r") as f:
				users = json.load(f)

			users[str(blazing_current.id)]["amulets"] += 10
				
			with open("../data/users.json", "w") as f:
				json.dump(users, f, indent="\t")	
			
			msg = "{} has earned 10{} for wielding the Blazing Sun frame for a day!".format(blazing_current.mention, eAmulet)
			await channel.send(msg)
		
		else :
		
			await blazing_new.add_roles(blazing_role)
			await asyncio.sleep(3)
			await blazing_current.remove_roles(blazing_role)
			await asyncio.sleep(3)
			
			adverb = ["deliberately", "sneakily", "forcefully", "unknowingly", "accidentally", "dishonestly"]
			verb = ["snatched", "stole", "took", "looted", "shoplifted", "embezzled"]
			noun = ["custody", "care", "guardianship", "control", "ownership"]
			comment = ["How horrifying!", "How gruesome!", "This is madness!", "Unbelievable!", "Such theft case!"]
			
			embed = discord.Embed(color = 0xac330f, title = ":incoming_envelope: Hall of Framers Update",
			description = "{} {} {} the Rare Blazing Sun Frame from {}\"s {}!! {}\n\n:four_leaf_clover: Distinct SSRs under possession: {} shikigamis".format(blazing_new.mention, adverb[random.randint(1,6)-1], verb[random.randint(1,6)-1], blazing_current.mention, noun[random.randint(1,5)-1], comment[random.randint(1,5)-1], get_score4[0][1]))
			embed.set_thumbnail(url="https://vignette.wikia.nocookie.net/onmyoji/images/7/72/Frame62.png")
			
			await channel.send(embed=embed)
			
def setup(client):
	client.add_cog(Frame(client))