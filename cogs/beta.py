"""
Beta Module
"Miketsu, 2021
"""

from discord.ext import commands


class Beta(commands.Cog):

    def __init__(self, client):

        self.client = client
        self.prefix = self.client.command_prefix




def setup(client):
    client.add_cog(Beta(client))
