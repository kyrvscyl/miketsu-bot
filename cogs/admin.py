"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import discord, json, re, pytz, random
from cogs.mongo.db import daily, boss, members
from discord.ext import commands
from datetime import datetime

tz_target = pytz.timezone("America/Atikokan")

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
		time_current1 = (datetime.now(tz=tz_target)).strftime("%d.%b %Y %H:%M EST")
		fields = ["name", "role", "status", "country", "timezone", "notes", "note"]
		roles = ["member", "ex-member", "ex-officer", "officer", "leader"]
		activity_values = ["active", "inactive", "on-leave", "kicked", "semi-active"]
		
		members_registered = []
		ids_registered = []
		for member in members.find({}, {"_id": 0, "name": 1, "#": 1}):
				members_registered.append(member["name"])
				ids_registered.append(member["#"])
		
		if len(args) == 0:
			msg = "These are the available guild management commands:\n`;m` - shows this help\n`;m add` - Add member data\n`;m update` - Update member data"
			await ctx.channel.send(msg)
		
		# ;g add <onmyoji>
		elif args[0] == "add" and len(args) <= 2:
			msg = "`;m add <name> <role>`"
			
			embed = discord.Embed(
			color=0xffff80, 
			title="Adding Members", 
			description=msg)
			
			embed.add_field(name="Available roles", value="`member` : current member\n`ex-member` : former member\n`ex-officer` : pre/post merge\n`officer` : current one")
			embed.set_thumbnail(url=ctx.guild.icon_url)
			await ctx.channel.send(embed=embed)
			
		# ;g add <role> <name>
		elif args[0] == "add" and len(args) == 3 and args[1] in roles and args[2] not in members_registered:
			
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
			members.insert_one(profile)
			await ctx.message.add_reaction("✅")
		
		# ;m update <onmyoji or #> <field> <value>
		elif args[0] == "update" and len(args) <= 2:
			msg = "`;m update <name or #> <field> <data>`"
			embed = discord.Embed(color=0xffff80, title="Updating Member Field Data", description=msg)
			embed.add_field(inline=True, name="Role", value="member, ex-member, ex-officer, officer")
			embed.add_field(inline=True, name="Status", value="active, inactive, on-leave, kicked, semi-active")
			embed.add_field(inline=True, name="Country", value="Use country codes: PH, MY, ID, AU, etc")
			embed.add_field(inline=True, name="Notes", value="Any officer notes")
			embed.set_thumbnail(url=ctx.guild.icon_url)
			await ctx.channel.send(embed=embed)
		
		elif args[0] == "update" and len(args) >= 3 and args[2] not in fields:
			msg = "Invalid field update request. Valid fields: `name`, `role`, `status`, `country`, `notes`"
			await ctx.channel.send(msg)
		
		elif args[0] == "update" and len(args) > 1 and args[2] in fields:
				
			try: # check if #
				id = int(args[1])
				time_current2 = (datetime.now(tz=tz_target)).strftime("%d.%b %y")
				time_current3 = (datetime.now(tz=tz_target)).strftime("%Y:%m:%d") #YYYY-MM-DD HH:MM
				
				# Updating the Status
				if args[2] == "status" and id in ids_registered:
					
					members.update_one({"#": id}, {"$set": {"status": "{}".format(args[3].capitalize())}})
					members.update_one({"#": id}, {"$set": {"status_update1": "{}".format(time_current2)}})
					members.update_one({"#": id}, {"$set": {"status_update2": "{}".format(time_current3)}})
					await ctx.message.add_reaction("✅")
				
				# Updating the notes
				elif (args[2] == "notes" or args[2] == "note") and id in ids_registered:
					new_note = " ".join(args[3::])
					
					members.update_one({"#": id}, {"$push": {
					"notes": {"officer": ctx.author.name, "time": time_current2, "note": new_note}
					}})
					await ctx.message.add_reaction("✅")
				
				# Updating country
				elif args[2] == "country" and id in ids_registered:
					try:
						country = args[3].upper()
						timezone = random.choice(pytz.country_timezones(country))
						members.update_one({"#": id}, {"$set": {"country": country}})
						members.update_one({"#": id}, {"$set": {"timezone": "['{}']".format(timezone)}})
						await ctx.message.add_reaction("✅")
						
					except KeyError:
						msg = "Invalid country code."
						await ctx.channel.send(msg)
				else:
					msg = "Provided username or number is not in the guild database."
					await ctx.channel.send(msg)
					await ctx.message.add_reaction("❌")
			
			# name instead
			except ValueError:
			
				if args[1] not in members_registered:
					msg = "The user is not in the Guild Database"
					await ctx.channel.send(msg)
				else:
					members.update_one({"name": args[1]}, {"$set": {"{}".format(args[2].lower()): args[3].capitalize()}})
					await ctx.message.add_reaction("✅")
		
		# ;m show <name or #>
		elif args[0] == "show" and len(args) == 1:
			msg = "Provide an argument to show. `;m show <name or #>` or `;m show status`"
			await ctx.channel.send(msg)
		
		# ;m show <name or #>
		elif args[0] == "show" and len(args) == 2:
			
			try:
				id = int(args[1])
				member = members.find_one({"#": id}, {"_id": 0})
			except ValueError:
				member = members.find_one({"name": args[1]}, {"_id": 0})
				
			embed = discord.Embed(color=0xffff80, title="#{} : {} | {}".format(member["#"], member["name"], member["role"]))
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
		
		# ;m show <field>
		elif args[0] == "show" and len(args) == 2 and args[1] == "status":
			msg = "Provide a field value to show. `active`, `inactive`, `on-leave`, `kicked`, or `semi-active`"
			await ctx.channel.send(msg)
		
		# ;m show status <value>
		elif args[0] == "show" and len(args) == 3 and args[1] == "status" and args[2].lower() in activity_values:
			
			query_list = []
			sort = [("status_update2", 1)]
			cursor = members.find({"status": args[2].capitalize()}, {"_id": 0, "name": 1, "status_update1": 1, "status_update1": 2, "#": 1}).sort(sort)
			
			for member in cursor:
				query_list.append("`#{}: {}` | {}\n".format(member["#"], member["status_update1"], member["name"]))
			
			description = "".join(query_list)
			embed = discord.Embed(color=0xffff80, title="Members with Status {}".format(args[2].capitalize()), description=description)
			embed.set_footer(text="Queried on {}".format(time_current1))
			embed.set_thumbnail(url=ctx.guild.icon_url)
			await ctx.channel.send(embed=embed)
		
		else:
			await ctx.message.add_reaction("❌")

def setup(client):
	client.add_cog(Admin(client))