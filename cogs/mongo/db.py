"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
from pymongo import MongoClient

address = "mongodb+srv://headmaster:headmaster@memory-scrolls-uhsu0.mongodb.net/test?retryWrites=true&w=majority"
memory = MongoClient(address)

boss = memory["miketsu"]["boss"]
friendship = memory["miketsu"]["friendship"]
shikigami = memory["miketsu"]["shikigami"]
streak = memory["miketsu"]["streak"]
users = memory["miketsu"]["users"]
sendoff = memory["miketsu"]["sendoff"]
quests = memory["miketsu"]["quests"]
owls = memory["miketsu"]["owls"]
thieves = memory["miketsu"]["thieves"]
frames = memory["miketsu"]["achievements"]

books = memory["bukkuman"]["books"]
bounty = memory["bukkuman"]["bounty"]
tokens = memory["bukkuman"]["tokens"]
members = memory["bukkuman"]["members"]
weather = memory["bukkuman"]["weather"]
patronus = memory["bukkuman"]["patronus"]
library = memory["bukkuman"]["library"]
errors = memory["bukkuman"]["errors"]
portraits = memory["bukkuman"]["frames"]
stickers = memory["bukkuman"]["stickers"]
