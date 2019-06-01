"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
import discord, json, random, asyncio
from discord.ext import commands
from config.lists import poolAll
from config.guild import eAmulet

class Quiz(commands.Cog):
	
	def __init__(self, client):
		self.client = client
	
	@commands.command(aliases=["qadd"])
	async def quizadd(self, ctx, arg1, arg2):

		qShiki = (arg2.replace("_", " ")).title()
		eShiki = arg1
		
		with open("../data/quiz.json", "r") as f:
			quiz = json.load(f)
		
		if qShiki in poolAll:
			for shikigami in poolAll:
				if shikigami == qShiki:
					if not shikigami in quiz:
						quiz[shikigami] = {}
						quiz[shikigami] = {"1": 0, "2": 0, "3": 0}
					for entry in quiz[shikigami]:
						if quiz[shikigami][entry] == 0:				
							quiz[qShiki][entry] = eShiki
							with open("../data/quiz.json", "w") as f:
								json.dump(quiz, f, indent="\t")
							msg = "You have added: {}: {}".format(qShiki, eShiki)
							await ctx.channel.send(msg)
							return
		
		else: 
			msg = "Wrong shikigami name"
			await ctx.channel.send(msg)
	
	@commands.command(aliases=["q"])	
	async def quiz(self, ctx):
		
		guesser = ctx.author
		
		with open("../data/quiz.json", "r") as f:
			quiz = json.load(f)
			
		shikiAll = list(quiz.keys())
		answer = random.choice(shikiAll)
		questions = []
		
		for entry in quiz[answer]:
			if quiz[answer][entry] != 0:
				questions.append(quiz[answer][entry])
		
		question = random.choice(questions)
				
		embed = discord.Embed(color=0xffff80, description=":grey_question:Who is this shikigami: {}".format(question))
		embed.set_author(name="Demon Quiz")
		embed.set_footer(text="Quiz for {}. 10 sec | 2 guesses".format(ctx.message.author.name), icon_url=ctx.message.author.avatar_url)
		
		msgQuestion = await ctx.channel.send(embed=embed)
			
		def check(guess):
			guessFormatted = ("".join(guess.content)).title()
			if guess.author != guesser:
				return False
			elif guessFormatted == answer:
				return True
			elif guessFormatted != answer:
				raise KeyError
		
		guesses = 0
		while guesses <= 2:
			
			try: 
				guessAnswer = await self.client.wait_for("message", timeout=10, check=check)
				msg = "{}, correct! You have earned 5{}".format(ctx.message.author.mention, eAmulet)
				await ctx.channel.send(msg)
				guesses = 5
				
				with open("../data/users.json", "r") as f:
					users = json.load(f)
					
				users[str(guesser.id)]["amulets"] += 5

				with open("../data/users.json", "w") as f:
					json.dump(users, f, indent="\t")
				
				
				
			except asyncio.TimeoutError:
				msg = "{}, time is up! You failed the quiz".format(ctx.message.author.mention)
				await ctx.channel.send(msg)
				guesses = 3

			except KeyError:
				guesses += 1
				if guesses == 2:
					msg = "{}, wrong answer. You failed the quiz".format(ctx.message.author.mention)
					await ctx.channel.send(msg)
				
				elif guesses == 1:
					msg = "{}, wrong answer! 1 more try left.".format(ctx.message.author.mention)
					await ctx.channel.send(msg)
				
		await msgQuestion.delete()
					
def setup(client):
	client.add_cog(Quiz(client))