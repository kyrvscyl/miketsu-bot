"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import discord, json, asyncio
from discord.ext import commands
from config.guild import eFship, eFship2

class Friendship(commands.Cog):
	
	def __init__(self, client):
		self.client = client
	
	def getBondCode(self, x, y):
		bondList = sorted([x.id, y.id], reverse=True)
		bondCode = "{}x{}".format(bondList[0], bondList[1])
		return bondCode
		
	@commands.command(aliases=["ship"])
	async def friendshipShip(self, ctx, query1: discord.User=None, query2: discord.User=None):
		
		try: 
			# No mentioned User
			if query1 == None and query2 == None:
				msg = "Please mention a user or users to view ships."
				await ctx.channel.send(msg)
				return
			
			# Only 1 mentioned user
			elif query1 != None and query2 == None:
				
				bondCode = self.getBondCode(ctx.author, query1)
				
				with open("../data/friendship.json", "r") as f:
					friendship = json.load(f)
				
				shipper1 = friendship[bondCode]["shipper1"]
				shipper2 = friendship[bondCode]["shipper2"]
				bondCurrent = friendship[bondCode]["points"]
				
				listPoints = []
				for ship in friendship:
					listPoints.append((ship, friendship[ship]["points"]))
				
				rank = (sorted(listPoints, key=lambda x: x[1], reverse=True)).index((bondCode, bondCurrent)) + 1
				
				embed = discord.Embed(color=0xffff80, 
					description = "Level: `{}`\nTotal points: `{}`{}\nServer Rank: `{}`".format(friendship[bondCode]["level"], bondCurrent, eFship, rank))
				embed.set_author(name="{}".format(friendship[bondCode]["ship_name"]), icon_url=self.client.get_user(int(shipper1)).avatar_url)
				embed.set_thumbnail(url=self.client.get_user(int(shipper2)).avatar_url)
				await ctx.channel.send(embed=embed)
			
			# 2 mentioned users
			elif query2 != None and query2 != None:
				
				bondCode = self.getBondCode(query1, query2)
		
				with open("../data/friendship.json", "r") as f:
					friendship = json.load(f)
				
				shipper1 = friendship[bondCode]["shipper1"]
				shipper2 = friendship[bondCode]["shipper2"]
				bondCurrent = friendship[bondCode]["points"]
				
				listPoints = []
				for ship in friendship:
					listPoints.append((ship, friendship[ship]["points"]))
				
				rank = (sorted(listPoints, key=lambda x: x[1], reverse=True)).index((bondCode, bondCurrent)) + 1
				
				embed = discord.Embed(color=0xffff80, 
					description = "Level: `{}`\nTotal points: `{}`{}\nServer Rank: `{}`".format(friendship[bondCode]["level"], bondCurrent, eFship, rank))
				embed.set_author(name="{}".format(friendship[bondCode]["ship_name"]), icon_url=self.client.get_user(int(shipper1)).avatar_url)
				embed.set_thumbnail(url=self.client.get_user(int(shipper2)).avatar_url)
				await ctx.channel.send(embed=embed)
		
		except:
			msg = "{}, I'm sorry, but that ship has sunk before it was built.".format(ctx.author.mention)
			await ctx.channel.send(msg)
	
	@commands.command(aliases=["fp"])
	async def friendship(self, ctx, receiver: discord.User=None):
		
		try: 
			# Checks if no user mentioned
			if receiver != None :
			
				#Check if the user mention is a bot
				if receiver.bot != True:
				
					#Check if the user mention is themselves
					if receiver != ctx.author:
				
						giver = ctx.author
						bondCode = self.getBondCode(giver, receiver)
					
						with open("../data/daily.json", "r") as f:
							daily = json.load(f)

						if str(giver.id) in daily["daily"]:

							if daily["daily"][str(giver.id)]["friendship_pass"] > 0:
								daily["daily"][str(giver.id)]["friendship_pass"] -= 1
								
								with open("../data/daily.json", "w") as f:
									json.dump(daily, f, indent="\t")
								
								# Add bond points to the ship
								with open("../data/friendship.json", "r") as f:
									friendship = json.load(f)
								
								# Create bond entry in friendship file, if none
								if not bondCode in friendship:
									friendship[bondCode] = {}
									friendship[bondCode]["shipper1"] = str(ctx.author.id)
									friendship[bondCode]["shipper2"] = str(receiver.id)
									friendship[bondCode]["ship_name"] = "{} and {}'s ship".format(giver.name, receiver.name)
									friendship[bondCode]["level"] = 1
									friendship[bondCode]["points"] = 0
									friendship[bondCode]["points_required"] = 50
									
								friendship[bondCode]["points"] += 5
								
								await ctx.message.add_reaction(eFship2)
								
								# Checks if the mentioned user receives
								def check(reaction, user):
									return user == receiver and str(reaction.emoji) == eFship
								
								try:
									reaction, user = await self.client.wait_for("reaction_add", timeout=8.0, check=check)
									friendship[bondCode]["points"] += 3
									await self.friendshipLevelUp(ctx, friendship, bondCode, giver, receiver)
									await ctx.message.clear_reactions()
									
								except asyncio.TimeoutError:
									await self.friendshipLevelUp(ctx, friendship, bondCode, giver, receiver)
									await ctx.message.clear_reactions()
								
								with open("../data/friendship.json", "w") as f:
									json.dump(friendship, f, indent="\t")
								
								# Add friendship points on the giver:
								with open("../data/users.json", "r") as f:
									users = json.load(f)
									
								users[str(giver.id)]["friendship"] += 5
								
								with open("../data/users.json", "w") as f:
									json.dump(users, f, indent="\t")	
							else:
								msg = "You have used up all your friendship points today."
								await ctx.channel.send(msg)
						else: 
							msg = "Please claim your daily rewards first."
							await ctx.channel.send(msg)
					else:
						msg = "{}, why? You're so lonely you wanna ship yourself with yourself?".format(ctx.author.mention)
						await ctx.channel.send(msg)
				else:
					msg = "{}, you cannot ship a bot.".format(ctx.author.mention)
					await ctx.channel.send(msg)
			else: 
				embed = discord.Embed(color=0xffff80, title="{}Friendship System".format(eFship),
					description = "Send & receive friendship points: `;fp @mention`\nShow ship's information: `;ship @mention`\nChange ship's name: `;fpc @mention <name>`")
				embed.set_thumbnail(url=self.client.user.avatar_url)
				await ctx.channel.send(embed=embed)
		except:
			return
			
	async def friendshipLevelUp(self, ctx, friendship, bondCode, giver, receiver):
		
		bondCurrent = friendship[bondCode]["points"]
		bondRequired = friendship[bondCode]["points_required"]
		
		# Checks for max level
		if not friendship[bondCode]["level"] == 5: 
			if bondCurrent >= bondRequired:
				shipName = friendship[bondCode]["ship_name"]
				friendship[bondCode]["level"] += 1
				level = friendship[bondCode]["level"] + 1
				friendship[bondCode]["points_required"] = round(-1.875*(level**4)+38.75*(level**3)-170.63*(level**2)+313.75*(level)-175)
				
				listPoints = []
				for ship in friendship:
					listPoints.append((ship, friendship[ship]["points"]))
					
				rank = (sorted(listPoints, key=lambda x: x[1], reverse=True)).index((bondCode, bondCurrent)) + 1
				
				embed = discord.Embed(color=0xffff80, 
					description = "Level: `{}`\nTotal points: `{}`{}\nServer Rank: `{}`".format(friendship[bondCode]["level"], bondCurrent, eFship, rank))
				embed.set_author(name="{}".format(shipName), icon_url=giver.avatar_url)
				embed.set_thumbnail(url=receiver.avatar_url)
					
				await ctx.channel.send(embed=embed)
			
	@commands.command(aliases=["fpchange", "fpc"])
	async def friendshipChangeName(self, ctx, receiver: discord.User=None, *args):
		
		try:
			bondCode = self.getBondCode(ctx.author, receiver)
			
			newName = " ".join(args)
			
			with open("../data/friendship.json", "r") as f:
				friendship = json.load(f)
			
			shipper1 = friendship[bondCode]["shipper1"]
			shipper2 = friendship[bondCode]["shipper2"]
			bondCurrent = friendship[bondCode]["points"]
			friendship[bondCode]["ship_name"] = newName
			
			with open("../data/friendship.json", "w") as f:
				json.dump(friendship, f, indent="\t")
			
			listPoints = []
			for ship in friendship:
				listPoints.append((ship, friendship[ship]["points"]))
			
			rank = (sorted(listPoints, key=lambda x: x[1], reverse=True)).index((bondCode, bondCurrent)) + 1
			
			embed = discord.Embed(color=0xffff80, 
				description = "Level: `{}`\nTotal points: `{}`{}\nServer Rank: `{}`".format(friendship[bondCode]["level"], bondCurrent, eFship, rank))
			embed.set_author(name="{}".format(friendship[bondCode]["ship_name"]), icon_url=self.client.get_user(int(shipper1)).avatar_url)
			embed.set_thumbnail(url=self.client.get_user(int(shipper2)).avatar_url)
				
			await ctx.channel.send(embed=embed)
			
		except:
			return
	
	
def setup(client):
	client.add_cog(Friendship(client))