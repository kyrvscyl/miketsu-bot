"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import discord, json, random
from discord.ext import commands

with open("data/emotes.json", "r") as f:
	stickers = json.load(f)
	
actions = list(stickers.keys())
emotes = stickers

list_stickers = []
for sticker in actions:
	list_stickers.append("`{}`, ".format(sticker))

description = "".join(list_stickers)[:-2:]

class Emotes(commands.Cog):
	
	def __init__(self, client):
		self.client = client
	
	@commands.command(aliases=["sticker"])
	async def stickers(self, ctx):
		embed = discord.Embed(color=0xffff80, title = "<:mikechan:587658757413273616> Available stickers!", description=description)
		embed.set_footer(text="just add 'mike' plus the sticker name in your message!")
		await ctx.channel.send(embed=embed)
		
	@commands.Cog.listener()
	async def on_message(self, message):
		
		# Ignore myself
		if message.author == self.client.user:
			return
		
		# Ignore other bots
		elif message.author.bot == True:
			return
		
		elif "mike" in message.content:
			list = message.content.split()
			action_recognized = None
			
			# find the action
			for action_try in list:
				if action_try in actions:
					action_recognized = action_try
					break
			
			if action_recognized == None :
				return
			
			else:
				selection = [ v for v in emotes[action_recognized].values() ]
				thumbnail = random.choice(selection)
				embed = discord.Embed(color=0xffff80)
				embed.set_image(url=thumbnail)
				await message.channel.send(embed=embed)
				await message.delete()
				
def setup(client):
	client.add_cog(Emotes(client))