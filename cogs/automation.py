"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import discord, json, pytz
from datetime import datetime
from cogs.mongo.db import books, users
from discord.ext import commands

# Date and Time
tz_target = pytz.timezone("America/Atikokan")

class Events(commands.Cog):
	
	def __init__(self, client):
		self.client = client
	
	# Whenever a old shard post is pinned
	@commands.Cog.listener()
	async def on_message_edit(self, before, after):
		request = books.find_one({"server": "{}".format(before.guild.id)}, {"_id": 0, "shard-trading": 1, "headlines": 1})
		shard_trading = request["shard-trading"]
		
		if str(before.channel.id) == shard_trading and after.pinned == True:
			headlines = request["headlines"]
			time_stamp = datetime.now(tz=tz_target).strftime("%b %d, %Y %m:%M EST")
					
			embed = discord.Embed(
			color=0xffff80, 
			title="{} is looking for shards!".format(before.author.name), 
			description="{}".format(before.content))
			
			# Checks if it has image:
			if len(before.attachments) != 0:
				image_posted = before.attachments[0].url
				embed.set_image(url=image_posted)
			
			embed.set_thumbnail(url=before.author.avatar_url)
			embed.set_footer(text="#{} | {}".format(before.channel, time_stamp))
			await self.client.get_channel(int(headlines)).send(embed=embed)
	
	# Whenever a newly shard post is pinned
	@commands.Cog.listener()
	async def on_raw_message_edit(self, payload):
		request = books.find_one({"server": "{}".format(payload.data["guild_id"])}, {"_id": 0, "shard-trading": 1, "headlines": 1})
		shard_trading = request["shard-trading"]
			
		if str(payload.data["channel_id"]) == shard_trading and payload.data["pinned"] == True:
			time_stamp = datetime.now(tz=tz_target).strftime("%b %d, %Y %I:%M EST")
			headlines = self.client.get_channel(int(request["headlines"]))
			user = self.client.get_user(int(payload.data["author"]["id"]))
			shard_trading = self.client.get_channel(int(shard_trading))
			
			embed = discord.Embed(
			color=0xffff80, 
			title="{} is looking for shards!".format(user.name), 
			description="{}".format(payload.data["content"]))
			
			# Checks if it has image:
			if len(payload.data["attachments"][0]) != 0:
				embed.set_image(url=payload.data["attachments"][0]["url"])

			embed.set_thumbnail(url=user.avatar_url)
			embed.set_footer(text="#{} | {}".format(shard_trading.name, time_stamp))
			await headlines.send(embed=embed)
				
	# Whenever a member joins
	@commands.Cog.listener()
	async def on_member_join(self, member):
		
		# Setup Variables
		time_stamp = datetime.now(tz=tz_target).strftime("%b %d, %Y %m:%M EST")
		guild = member.guild
		request = books.find_one({"server": "{}".format(guild.id)}, {"_id": 0, "welcome": 1, "sorting": 1, "landing_zone": 1, "scroll-of-everything": 1, "default_role": 1})
		welcome = request["welcome"]
		sorting = request["sorting"]
		landing_zone = request["landing_zone"]
		record_scroll = request["scroll-of-everything"]
		default_role = request["default_role"]
		scrolls = member.guild.member_count
		guild_icon = member.guild.icon_url
		
		# Sets default role
		default_role2 = guild.get_role(int(default_role))
		await member.add_roles(default_role2)
		
		# Landing Zone 
		msg = ":sparkles:Welcome to Patronus, {}. Kindly read your acceptance letter first".format(member.mention)
		await self.client.get_channel(int(landing_zone)).send(msg)
		
		# Acceptance Letter
		description = "Dear {},\n\nWe are pleased to accept you at House Patronus.\nDo browse the server's <#{}> channel for the basics and essentials of the guild then proceed to <#{}> to assign yourself some roles.\n\nWe await your return owl.\n\nYours Truly,\nThe Headmaster".format(member.name, welcome, sorting)
		embed = discord.Embed(color=0xffff80, title=":love_letter: Acceptance Letter".format(member), description=description)
		await member.send(embed=embed)
		
		# Scroll of Everything
		embed = discord.Embed(color=0xffff80, title=":newspaper2: Memory Scroll Update", description=">> {} has joined the House!\n\nSending acceptance letter.. :love_letter:".format(member.mention))
		embed.set_thumbnail(url=member.avatar_url)
		embed.set_footer(text="Total Scrolls: {} | {}".format(scrolls, time_stamp))
		
		await self.client.get_channel(int(record_scroll)).send(embed=embed)
	
	# Whenever a member leaves
	@commands.Cog.listener()
	async def on_member_remove(self, member):
		
		users.delete_one({"user_id": str(member.id)})
		
		time_stamp = datetime.now(tz=tz_target).strftime("%b %d, %Y %m:%M EST")
		guild_id = member.guild.id
		request = books.find_one({"server": "{}".format(guild_id)}, {"_id": 0, "scroll-of-everything": 1})
		record_scroll = request["scroll-of-everything"]
		scrolls = member.guild.member_count
		guild_icon = member.guild.icon_url
		
		# Scroll of Everything
		embed = discord.Embed(color=0xac330f, title=":newspaper2: Memory Scroll Update", description=">> {} has left the House!\n\nObliviating their memory scroll..:sparkles:".format(member.mention))
		embed.set_thumbnail(url=member.avatar_url)
		embed.set_footer(text="Total Scrolls: {} | {}".format(scrolls, time_stamp), icon_url=guild_icon)

		await self.client.get_channel(int(record_scroll)).send(embed=embed)
	
	# Spying members
	@commands.Cog.listener()
	async def on_member_update(self, before, after):
		time_stamp = datetime.now(tz=tz_target).strftime("%b %d, %Y %m:%M EST")
		
		if before.roles != after.roles:
			roles_before = before.roles
			roles_after = after.roles

			changed_role1 = list(set(roles_after) - set(roles_before))
			changed_role2 = list(set(roles_before) - set(roles_after))
			
			if changed_role1 == []:

				request = books.find_one({"server": "{}".format(before.guild.id)}, {"_id": 0, "scroll-of-everything": 1})
				record_scroll = request["scroll-of-everything"]
					
				embed = discord.Embed(color=0xac330f, title=":camera_with_flash: Role Update")
				embed.set_thumbnail(url=before.avatar_url)
				embed.add_field(inline=False, name="Removed role for {}:".format(after.name), value=changed_role2[0].name)
				embed.set_footer(text="{}".format(time_stamp))
				
				await self.client.get_channel(int(record_scroll)).send(embed=embed)
				
			elif changed_role2 == []:
		
				request = books.find_one({"server": "{}".format(before.guild.id)}, {"_id": 0, "scroll-of-everything": 1})
				record_scroll = request["scroll-of-everything"]
					
				embed = discord.Embed(color=0xffff80, title=":camera_with_flash: Role Update")
				embed.set_thumbnail(url=before.avatar_url)
				embed.add_field(inline=False, name="Added role for {}:".format(after.name), value=changed_role1[0].name)
				embed.set_footer(text="{}".format(time_stamp))
				
				await self.client.get_channel(int(record_scroll)).send(embed=embed)
		
		elif before.nick != after.nick:
			request = books.find_one({"server": "{}".format(before.guild.id)}, {"_id": 0, "scroll-of-everything": 1})
			record_scroll = request["scroll-of-everything"]
			
			embed = discord.Embed(color=0xffff80, title=":camera_with_flash: Nickname Change")
			embed.set_thumbnail(url=before.avatar_url)
				
			if before.nick == None:
				embed.add_field(inline=True, name="Before:", value=before.name)
			else:
				embed.add_field(inline=True, name="Before:", value=before.nick)
			
			embed.add_field(inline=True, name="After:", value=after.nick)
			embed.set_footer(text="{}".format(time_stamp))
			
			await self.client.get_channel(int(record_scroll)).send(embed=embed)
			
def setup(client):
	client.add_cog(Events(client))