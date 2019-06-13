from pymongo import MongoClient

# Mongo Startup
memory = MongoClient("mongodb+srv://headmaster:headmaster@memory-scrolls-uhsu0.mongodb.net/test?retryWrites=true&w=majority")
boss = memory["miketsu"]["boss"]
bounty = memory["miketsu"]["bounty"]
compensation = memory["miketsu"]["compensation"]
daily = memory["miketsu"]["daily"]
friendship = memory["miketsu"]["friendship"]
shikigami = memory["miketsu"]["shikigami"]
streak = memory["miketsu"]["streak"]
users = memory["miketsu"]["users"]
books = memory["bukkuman"]["books"]