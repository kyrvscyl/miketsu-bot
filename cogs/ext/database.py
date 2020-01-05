"""
Database Module
Miketsu, 2020
"""
import os

from pymongo import MongoClient

mongo_user = os.environ.get("MONGOUSER")
mongo_pass = os.environ.get("MONGOPASS")
cluster = os.environ.get("CLUSTER")

address = f"mongodb+srv://{mongo_user}:{mongo_pass}@{cluster}.mongodb.net/test?retryWrites=true&w=majority"
memory = MongoClient(address)


def get_collections(scroll):
    return memory["miketsu"][scroll]
