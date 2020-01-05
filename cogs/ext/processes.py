"""
Processes Module
Miketsu, 2020
"""

import discord


async def process_msg_delete(message, delay):
    try:
        await message.delete(delay=delay)
    except discord.errors.Forbidden:
        pass
    except discord.errors.HTTPException:
        pass


async def process_msg_submit(channel, content, embed):
    try:
        return await channel.send(content=content, embed=embed)
    except AttributeError:
        pass
    except discord.errors.Forbidden:
        pass
    except discord.errors.HTTPException:
        pass


async def process_msg_edit(message, content, embed):
    try:
        return await message.edit(content=content, embed=embed)
    except discord.errors.Forbidden:
        pass
    except discord.errors.HTTPException:
        pass


async def process_msg_reaction_add(message, emoji):
    try:
        await message.add_reaction(emoji)
    except discord.errors.Forbidden:
        pass
    except discord.errors.HTTPException:
        pass


async def process_msg_reaction_remove(message, emoji, user):
    try:
        await message.remove_reaction(emoji, user)
    except discord.errors.Forbidden:
        pass
    except discord.errors.HTTPException:
        pass


async def process_msg_reaction_clear(message):
    try:
        await message.clear_reactions()
    except discord.errors.Forbidden:
        pass
    except discord.errors.HTTPException:
        pass
