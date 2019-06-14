from pymongo import MongoClient

# Mongo Database Startup
# memory = MongoClient("mongodb+srv://headmaster:headmaster@memory-scrolls-uhsu0.mongodb.net/test?retryWrites=true&w=majority")
memory = MongoClient("mongodb://localhost:27017/")


# Collections
boss = memory["miketsu"]["boss"]
bounty = memory["miketsu"]["bounty"]
compensation = memory["miketsu"]["compensation"]
daily = memory["miketsu"]["daily"]
friendship = memory["miketsu"]["friendship"]
shikigami = memory["miketsu"]["shikigami"]
streak = memory["miketsu"]["streak"]
users = memory["miketsu"]["users"]
books = memory["bukkuman"]["books"]
shikigamis = memory["bukkuman"]["shikigamis"]