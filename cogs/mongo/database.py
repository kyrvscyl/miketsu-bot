"""
Database Module
Miketsu, 2019
"""
import os

from pymongo import MongoClient

mongo_user = os.environ.get("MONGOUSER")
mongo_pass = os.environ.get("MONGOPASS")

address = f"mongodb+srv://{mongo_user}:{mongo_pass}@memory-scrolls-uhsu0.mongodb.net/test?retryWrites=true&w=majority"
memory = MongoClient(address)


def get_collections(shikigami, scroll):
    return memory[shikigami][scroll]
