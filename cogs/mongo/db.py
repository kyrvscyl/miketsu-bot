"""
Discord Miketsu Bot.
kyrvscyl, 2019
"""
from pymongo import MongoClient

# Mongo Database Startup
address = "mongodb+srv://headmaster:headmaster@memory-scrolls-uhsu0.mongodb.net/test?retryWrites=true&w=majority"
memory = MongoClient(address)

# Collections - Miketsu
boss = memory["miketsu"]["boss"]
bounty = memory["miketsu"]["bounty"]
compensation = memory["miketsu"]["compensation"]
daily = memory["miketsu"]["daily"]
friendship = memory["miketsu"]["friendship"]
shikigami = memory["miketsu"]["shikigami"]
streak = memory["miketsu"]["streak"]
users = memory["miketsu"]["users"]
sendoff = memory["miketsu"]["sendoff"]
quests = memory["miketsu"]["quests"]
owls = memory["miketsu"]["owls"]
thieves = memory["miketsu"]["thieves"]

# Collections - Bukkuman
books = memory["bukkuman"]["books"]
shikigamis = memory["bukkuman"]["shikigamis"]
members = memory["bukkuman"]["members"]
weather = memory["bukkuman"]["weather"]
patronus = memory["bukkuman"]["patronus"]
