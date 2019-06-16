"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import discord, json, re, pytz, random, asyncio
from cogs.mongo.db import daily, boss, members
from discord.ext import commands
from datetime import datetime

tz_target = pytz.timezone("America/Atikokan")

# Global Variables
fields = ["name", "role", "status", "country", "timezone", "notes", "note", "tz"]
roles = ["member", "ex-member", "ex-officer", "officer", "leader"]
status_values = ["active", "inactive", "on-leave", "kicked", "semi-active", "away", "left"]

class Admin(commands.Cog):
	
	def __init__(self, client):
		self.client = client
	
	@commands.command()
	@commands.is_owner()
	async def reset(self, ctx, *args):
	
		# Reset daily
		if args[0] == "daily":
			
			for entry in daily.find({"key": "daily"}, {"key": 0, "_id": 0}):
				for user_id in entry:
					daily.update_one({"key": "daily"}, {"$set": {"{}.rewards".format(user_id): "unclaimed"}})
			
			for user_id in daily.find_one({"key" : "raid"}, {"_id": 0, "key": 0}):
				daily.update_one({"key" : "raid"}, {"$set": {"{}.raid_count".format(user_id): 0}})
				
			msg = ":confetti_ball: Daily rewards have been reset."
			await ctx.channel.send(msg)
			
		# Resets weekly
		elif args[0] == "weekly":
				
			for entry in daily.find({"key": "weekly"}, {"key": 0, "_id": 0}):
				for user in entry:
					daily.update({"key": "weekly"}, {"$set": {"{}.rewards".format(user): "unclaimed"}})
				
			msg = ":confetti_ball: Weekly rewards have been reset."
			await ctx.channel.send(msg)
			
		# Resets the boss	
		elif args[0] == "boss":
			
			boss.update_many({}, {"$set": {"discoverer": 0, "level": 0, "damage_cap": 0, "total_hp": 0, "current_hp": 0, "rewards": 0, "challengers": [], "rewards": {}}})

			msg = "Assembly Boss encounter has been reset."
			await ctx.channel.send(msg)
		
		else:
			msg = "Please provide a valid argument: daily, weekly, or boss"
			await ctx.channel.send(msg)
	
	@commands.command(aliases=["c", "clear", "purge", "cl"])
	async def purge_messages(self, ctx, amount=2):
		if ctx.channel.permissions_for(ctx.author).administrator == True:
			await ctx.channel.purge(limit=amount+1)
	
	@commands.command(aliases=["bc"])
	async def broadcast(self, ctx, *args):
		channel = self.client.get_channel(int(re.sub("[<>#]", "", args[0])))
		
		# Checks if admin
		if ctx.channel.permissions_for(ctx.author).administrator == True:
			msg = "{}".format(" ".join(args[1:]))
			await channel.send(msg)
	
	@commands.command(aliases=["m"])
	@commands.has_role("Head")
	async def management_guild(self, ctx, *args):
		
		# No argument passed
		if len(args) == 0 or args[0].lower() == "help" or args[0].lower() == "h":
			msg = ":white_small_square: `;m help` : shows this help\n:white_small_square: `;m add` : adds member data\n:white_small_square: `;m update` : updates member data\n:white_small_square: `;m show` : query the data"
			embed = discord.Embed(color=0xffff80)
			embed.add_field(name=":trident: Management Commands", value=msg)
			embed.set_thumbnail(url=ctx.guild.icon_url)
			await ctx.channel.send(embed=embed)
		
		# ;g add <onmyoji>
		elif args[0].lower() == "add" and len(args) <= 2:
			embed = discord.Embed(color=0xffff80, title=":trident: Adding Members", description=":white_small_square: `;m add {name} {role}`")
			embed.add_field(name=":ribbon: Roles", value=":white_small_square: `member` : a current member\n:white_small_square: `ex-member` : a former member\n:white_small_square: `ex-officer` : pre/post merge\n:white_small_square: `officer` : currently appointed")
			embed.set_thumbnail(url=ctx.guild.icon_url)
			await ctx.channel.send(embed=embed)
			
		# ;g add <role> <name>
		elif args[0].lower() == "add" and len(args) == 3 and args[1] in roles and args[2].lower() not in members_registered:
			count = members.count() + 1
			profile = {}
			profile["#"] = count
			profile["name"] = args[2]
			profile["role"] = args[1].title()
			profile["status"] = "< None >"
			profile["status_update1"] = ""
			profile["status_update2"] = ""
			profile["country"] = "<CC>"
			profile["timezone"] = "['/']"
			profile["notes"] = []
			profile["name_lower"] = args[2].lower()
			members.insert_one(profile)
			await ctx.message.add_reaction("✅")
		
		# ;m update <onmyoji or #> <field> <value>
		elif (args[0].lower() == "update" or args[0].lower() == "u") and len(args) <= 1:
			embed = discord.Embed(color=0xffff80, title=":trident: Updating Member Data", description=":white_small_square: `;m update {name} {field} {value}`\n:white_small_square: `;m update {#} {field} {value}`")
			embed.add_field(inline=True, name=":ribbon: Role", value="member, ex-member, ex-officer, officer")
			embed.add_field(inline=True, name=":golf: Status", value="active, inactive, on-leave, kicked, semi-active, away, left")
			embed.add_field(inline=True, name=":globe_with_meridians: Country", value="Use country codes: PH, MY, ID, AU, etc")
			embed.add_field(inline=True, name=":notepad_spiral: Notes", value="Any officer notes")
			embed.set_footer(text="Use name as field to change name")
			embed.set_thumbnail(url=ctx.guild.icon_url)
			await ctx.channel.send(embed=embed)
		
		# ;m update 1
		elif (args[0].lower() == "update" or args[0].lower() == "u") and len(args) == 2:
			msg = "No field and value provided. Valid fields: `name`, `role`, `status`, `country`, `notes`"
			await ctx.channel.send(msg)
		
		# ;m update weird active
		elif (args[0].lower() == "update" or args[0].lower() == "u") and args[2].lower() not in fields and len(args) >= 3:
			msg = "Invalid field update request. Valid fields: `name`, `role`, `status`, `country`, `notes`"
			await ctx.channel.send(msg)
		
		# ;m update 1 name
		elif (args[0].lower() == "update" or args[0].lower() == "u") and args[2].lower() in fields and len(args) == 3:
			msg = "No value provided for the field."
			await ctx.channel.send(msg)
		
		# ;m update status active
		elif (args[0].lower() == "update" or args[0].lower() == "u") and len(args) >= 4 and args[2].lower() in fields:
			await self.management_update_field(ctx, args)
			
		# ;m show <name or #>
		elif args[0].lower() == "show" and len(args) == 1:
			embed = discord.Embed(color=0xffff80, title=":trident: Showing Members' Data", description=":white_small_square: `;m show all` - shows all registered members\n:white_small_square: `;m show {name or #}` - shows a member profile\n:white_small_square: `;m show {field} {data}` - shows specific data")
			embed.add_field(inline=True, name=":ribbon: Role", value="member, ex-member, ex-officer, officer")
			embed.add_field(inline=True, name=":golf: Status", value="active, inactive, on-leave, kicked, semi-active, away, left")
			embed.set_thumbnail(url=ctx.guild.icon_url)
			await ctx.channel.send(embed=embed)
		
		# ;m show <name or #>
		elif args[0].lower() == "show" and len(args) == 2 and args[1].lower() == "role":
			msg = "Provide a role value to show. `;m show role {member, ex-member, etc..}`"
			await ctx.channel.send(msg)
		
		elif args[0].lower() == "show" and len(args) == 2 and (args[1].lower() == "status"):
			msg = "Provide a role value to show. `;m show status {active, inactive, etc..}`"
			await ctx.channel.send(msg)
		
		elif args[0].lower() == "show" and len(args) == 2 and (args[1].lower() == "tz" or args[1].lower() == "timezone"):
			msg = "Provide a timezone value to show. `;m show tz {guild, {member}, all}`"
			await ctx.channel.send(msg)
		
		# ;m show all
		elif args[0].lower() == "show" and len(args) == 2 and args[1].lower() == "all":
			await self.management_show_guild(ctx, args)
			
		elif args[0].lower() == "show" and len(args) == 2 and args[1].lower() != "all" and args[1].lower() not in fields:
			await self.management_show_profile(ctx, args)
		
		# ;m show status <value>
		elif args[0].lower() == "show" and len(args) == 3 and args[1].lower() == "status" and args[2].lower() in status_values:
			await self.management_show_field_status(ctx, args)
		
		# ;m show role <value>
		elif args[0].lower() == "show" and len(args) == 3 and args[1].lower() == "role" and args[2].lower() in roles:
			await self.management_show_field_role(ctx, args)
		
		# ;m show timezone
		elif args[0].lower() == "show" and len(args) == 3 and (args[1].lower() == "timezone" or args[1].lower() == "tz") and (args[2].lower() in roles or args[2].lower() == "guild"):
			await self.management_show_field_timezone(ctx, args)
		
		# No command hit
		else:
			await ctx.message.add_reaction("❌")
	
	async def management_show_guild(self, ctx, args):
		time_current1 = (datetime.now(tz=tz_target)).strftime("%d.%b %Y %H:%M EST")
		query_list = []
		
		# query all members
		for member in members.find({}, {"_id": 0, "name": 1, "role": 1, "#": 1}).sort([("#", 1)]):
			query_list.append("`#{}:` {} | {}\n".format(member["#"], member["role"], member["name"]))
		
		description = "".join(query_list[0:20])
		embed = discord.Embed(color=0xffff80, title=":trident: Registered Members", description=description)
		embed.set_footer(text="Page: 1 | Queried on {}".format(time_current1))
		embed.set_thumbnail(url=ctx.guild.icon_url)
		msg = await ctx.channel.send(embed=embed)
		
		await msg.add_reaction("⬅")
		await msg.add_reaction("➡")
		
		def create_embed(page):
			end = page * 20
			start =  end - 20
			description = "".join(query_list[start:end])
			embed = discord.Embed(color=0xffff80, title=":trident: Registered Members", description=description)
			embed.set_footer(text="Page: {} | Queried on {}".format(page, time_current1))
			embed.set_thumbnail(url=ctx.guild.icon_url)
			return embed
		
		def check(reaction, user):
			return user != self.client.user and reaction.message.id == msg.id
		
		page = 1
		while True:
			try:
				timeout = 180
				reaction, user=await self.client.wait_for("reaction_add", timeout = timeout, check=check)
				if str(reaction.emoji) == "➡":
					page += 1
				elif str(reaction.emoji) == "⬅":
					page -= 1
				if page == 0:
					page = 1
				await msg.edit(embed=create_embed(page))
				timeout=timeout - 1
			except asyncio.TimeoutError:
				return False
	
	async def management_show_field_timezone(self, ctx, args):
		time_current1 = (datetime.now(tz=tz_target)).strftime("%d.%b %Y %H:%M EST")
		query_list = []
		
		# query all members of the guild
		if args[2].lower() == "guild":
			for member in members.aggregate([{"$match": {"timezone": {"$ne": "['/']"}, "role": {"$ne": "Ex-member"}}}, {"$project": {"_id": 0, "name": 1, "timezone": 1, "#": 1}}]):
				tz_target2 = pytz.timezone(re.sub("['\[\]]", '', member["timezone"]))
				current_time = datetime.now(tz=tz_target2).strftime("%I:%M %p")
				query_list.append("`#{}:` `{}` | {}\n".format(member["#"], current_time, member["name"]))
		# query a specific role
		else:
			for member in members.aggregate([{"$match": {"timezone": {"$ne": "['/']"}, "role": {"$eq": args[2].capitalize()}}}, {"$project": {"_id": 0, "name": 1, "timezone": 1, "#": 1}}]):
				tz_target2 = pytz.timezone(re.sub("['\[\]]", '', member["timezone"]))
				current_time = datetime.now(tz=tz_target2).strftime("%I:%M %p")
				query_list.append("`#{}:` `{}` | {}\n".format(member["#"], current_time, member["name"]))
		
		description = "".join(query_list[0:20])
		embed = discord.Embed(color=0xffff80, title=":globe_with_meridians: Showing Local Time [{}]".format(args[2].capitalize()), description=description)
		embed.set_footer(text="Page: 1 | Queried on {}".format(time_current1))
		embed.set_thumbnail(url=ctx.guild.icon_url)
		msg = await ctx.channel.send(embed=embed)
		
		await msg.add_reaction("⬅")
		await msg.add_reaction("➡")
		
		def create_embed(page):
			end = page * 20
			start =  end - 20
			description = "".join(query_list[start:end])
			embed = discord.Embed(color=0xffff80, title=":globe_with_meridians: Showing Local Time [{}]".format(args[2].capitalize()), description=description)
			embed.set_footer(text="Page: {} | Queried on {}".format(page, time_current1))
			embed.set_thumbnail(url=ctx.guild.icon_url)
			return embed
		
		def check(reaction, user):
			return user != self.client.user and reaction.message.id == msg.id
		
		page = 1
		while True:
			try:
				timeout = 60
				reaction, user=await self.client.wait_for("reaction_add", timeout = timeout, check=check)
				if str(reaction.emoji) == "➡":
					page += 1
				elif str(reaction.emoji) == "⬅":
					page -= 1
				if page == 0:
					page = 1
				await msg.edit(embed=create_embed(page))
				timeout=timeout - 1
			except asyncio.TimeoutError:
				return False

	async def management_show_field_role(self, ctx, args):
		time_current1 = (datetime.now(tz=tz_target)).strftime("%d.%b %Y %H:%M EST")
		query_list = []
		
		for member in members.find({"role": args[2].capitalize()}, {"_id": 0, "name": 1, "status_update1": 1, "status_update1": 2, "#": 1}).sort([("status_update2", 1)]):
			query_list.append("`#{}:` `{}` | {}\n".format(member["#"], member["status_update1"], member["name"]))
		
		description = "".join(query_list[0:20])
		embed = discord.Embed(color=0xffff80, title=":trident: Members with Role '{}'".format(args[2].capitalize()), description=description)
		embed.set_footer(text="Page: 1 | Queried on {}".format(time_current1))
		embed.set_thumbnail(url=ctx.guild.icon_url)
		msg = await ctx.channel.send(embed=embed)
		
		await msg.add_reaction("⬅")
		await msg.add_reaction("➡")
		
		def create_embed(page):
			end = page*20
			start =  end - 20
			description = "".join(query_list[start:end])
			embed = discord.Embed(color=0xffff80, title="Members with Status '{}'".format(args[2].capitalize()), description=description)
			embed.set_footer(text="Page: {} | Queried on {}".format(page, time_current1))
			embed.set_thumbnail(url=ctx.guild.icon_url)
			return embed
		
		def check(reaction, user):
			return user != self.client.user and reaction.message.id == msg.id
		
		page = 1
		while True:
			try:
				timeout = 60
				reaction, user=await self.client.wait_for("reaction_add", timeout = timeout, check=check)
				if str(reaction.emoji) == "➡":
					page += 1
				elif str(reaction.emoji) == "⬅":
					page -= 1
				if page == 0:
					page = 1
				
				await msg.edit(embed=create_embed(page))
				timeout=timeout - 1
			except asyncio.TimeoutError:
				return False
	
	async def management_show_field_status(self, ctx, args):
		time_current1 = (datetime.now(tz=tz_target)).strftime("%d.%b %Y %H:%M EST")
		query_list = []
		
		for member in members.find({"status": args[2].capitalize()}, {"_id": 0, "name": 1, "status_update1": 1, "status_update1": 2, "#": 1}).sort([("status_update2", 1)]):
			query_list.append("`#{}: {}` | {}\n".format(member["#"], member["status_update1"], member["name"]))
		
		description = "".join(query_list[0:20])
		embed = discord.Embed(color=0xffff80, title=":trident: Members with Status '{}'".format(args[2].capitalize()), description=description)
		embed.set_footer(text="Page: 1 | Queried on {}".format(time_current1))
		embed.set_thumbnail(url=ctx.guild.icon_url)
		msg = await ctx.channel.send(embed=embed)
		
		await msg.add_reaction("⬅")
		await msg.add_reaction("➡")
		
		def create_embed(page):
			end = page*20
			start =  end - 20
			description = "".join(query_list[start:end])
			embed = discord.Embed(color=0xffff80, title=":trident: Members with Status '{}'".format(args[2].capitalize()), description=description)
			embed.set_footer(text="Page: {} | Queried on {}".format(page, time_current1))
			embed.set_thumbnail(url=ctx.guild.icon_url)
			return embed
		
		def check(reaction, user):
			return user != self.client.user and reaction.message.id == msg.id
		
		page = 1
		while True:
			try:
				timeout = 60
				reaction, user=await self.client.wait_for("reaction_add", timeout = timeout, check=check)
				if str(reaction.emoji) == "➡":
					page += 1
				elif str(reaction.emoji) == "⬅":
					page -= 1
				if page == 0:
					page = 1
				await msg.edit(embed=create_embed(page))
				timeout=timeout - 1
			except asyncio.TimeoutError:
				return False
	
	async def management_show_profile(self, ctx, args):
		time_current1 = (datetime.now(tz=tz_target)).strftime("%d.%b %Y %H:%M EST")
		
		try:
			id = int(args[1])
			member = members.find_one({"#": id}, {"_id": 0})
		except ValueError:
			member = members.find_one({"name_lower": args[1].lower()}, {"_id": 0})
			
		try:
			embed = discord.Embed(color=0xffff80, title="#{} : {} | :ribbon: {}".format(member["#"], member["name"], member["role"]))
			embed.add_field(inline=True, name=":golf: Status", value="{} [{}]".format(member["status"], member["status_update1"]))
			embed.add_field(inline=True, name=":globe_with_meridians: Country | Timezone", value="{} | {}".format(member["country"], member["timezone"]))
			
			if member["notes"] == []:
				embed.add_field(inline=True, name=":notepad_spiral: Notes", value="No notes yet.")
			elif len(member["notes"]) != 0:
				note_formatted = ""
				for note in member["notes"]:
					entry = "[{} | {}]: {}\n".format(note["time"], note["officer"], note["note"])
					note_formatted += entry
					
				embed.add_field(inline=True, name=":notepad_spiral: Notes", value=note_formatted)
			
			embed.set_footer(text="Queried on {}".format(time_current1))
			embed.set_thumbnail(url=ctx.guild.icon_url)
			await ctx.channel.send(embed=embed)
		except TypeError:
			msg = "That user is not in the Guild Database"
			await ctx.channel.send(msg)
		
	async def management_update_field(self, ctx, args):
		members_registered = []
		ids_registered = []
		
		for member in members.find({}, {"_id": 0, "name": 1, "#": 1}):
				members_registered.append(member["name"].lower())
				ids_registered.append(member["#"])
	
		try: # check if code is provided
			id = int(args[1])
			time_current2 = (datetime.now(tz=tz_target)).strftime("%d.%b %y")
			time_current3 = (datetime.now(tz=tz_target)).strftime("%Y:%m:%d") #YYYY-MM-DD HH:MM
			# Check if registered
			if id not in ids_registered:
				msg = "Provided username or number is not in the guild database."
				await ctx.channel.send(msg)
			
			# Updating the Status
			elif args[2].lower() == "status" and args[3].lower() in status_values:
				members.update_one({"#": id}, {"$set": {"status": "{}".format(args[3].capitalize())}})
				members.update_one({"#": id}, {"$set": {"status_update1": "{}".format(time_current2)}})
				members.update_one({"#": id}, {"$set": {"status_update2": "{}".format(time_current3)}})
				await ctx.message.add_reaction("✅")
			
			# Updating the notes
			elif (args[2].lower() == "notes" or args[2].lower() == "note"):
				new_note = " ".join(args[3::])
				members.update_one({"#": id}, {"$push": {"notes": {"officer": ctx.author.name, "time": time_current2, "note": new_note}}})
				await ctx.message.add_reaction("✅")
			
			# Updating country
			elif args[2] == "country":
				try:
					country = args[3].upper()
					timezone = random.choice(pytz.country_timezones(country))
					members.update_one({"#": id}, {"$set": {"country": country}})
					members.update_one({"#": id}, {"$set": {"timezone": "['{}']".format(timezone)}})
					await ctx.message.add_reaction("✅")
				except KeyError:
					msg = "Invalid country code."
					await ctx.channel.send(msg)
			
			# Updating the name
			elif args[2].lower() == "name":
				members.update_one({"#": id}, {"$set": {"name": "{}".format(args[3]), "name_lower": "{}".format(args[3].lower())}})
				await ctx.message.add_reaction("✅")
			
			elif args[2].lower() == "role" and args[3].lower() in roles:
				members.update_one({"#": id}, {"$set": {"role": args[3].capitalize()}})
				await ctx.message.add_reaction("✅")
			
			else:
				await ctx.message.add_reaction("❌")
			
		# name instead is provided
		except ValueError:
			time_current2 = (datetime.now(tz=tz_target)).strftime("%d.%b %y")
			time_current3 = (datetime.now(tz=tz_target)).strftime("%Y:%m:%d") #YYYY-MM-DD HH:MM
			# Not in the registered ones
			if args[1].lower() not in members_registered:
				msg = "That user is not in the Guild Database"
				await ctx.channel.send(msg)
			
			# Updating the Status
			elif args[2] == "status" and args[3].lower() in status_values:
				members.update_one({"name_lower": args[1].lower()}, {"$set": {"status": "{}".format(args[3].capitalize())}})
				members.update_one({"name_lower": args[1].lower()}, {"$set": {"status_update1": "{}".format(time_current2)}})
				members.update_one({"name_lower": args[1].lower()}, {"$set": {"status_update2": "{}".format(time_current3)}})
				await ctx.message.add_reaction("✅")
			
			# Updating the notes
			elif args[2] == "notes" or args[2] == "note":
				new_note = " ".join(args[3::])
				members.update_one({"name_lower": args[1].lower()}, {"$push": {"notes": {"officer": ctx.author.name, "time": time_current2, "note": new_note}}})
				await ctx.message.add_reaction("✅")
			
			# Updating country
			elif args[2] == "country":
				try:
					country = args[3].upper()
					timezone = random.choice(pytz.country_timezones(country))
					members.update_one({"name_lower": args[1].lower()}, {"$set": {"country": country}})
					members.update_one({"name_lower": args[1].lower()}, {"$set": {"timezone": "['{}']".format(timezone)}})
					await ctx.message.add_reaction("✅")
				except KeyError:
					msg = "Invalid country code."
					await ctx.channel.send(msg)
			
			elif args[2].lower() == "name":
				members.update_one({"name_lower": args[1].lower()}, {"$set": {"name": "{}".format(args[3]), "name_lower": "{}".format(args[3].lower())}})
				await ctx.message.add_reaction("✅")
			
			elif args[2].lower() == "role" and args[3].lower() in roles:
				members.update_one({"name_lower": args[1].lower()}, {"$set": {"role": "{}".format(args[3].capitalize())}})
				await ctx.message.add_reaction("✅")
			
			else:
				await ctx.message.add_reaction("❌")
				
def setup(client):
	client.add_cog(Admin(client))