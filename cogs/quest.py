"""
Quests Module
Miketsu, 2020
"""

from datetime import timedelta

from discord.ext import commands

from cogs.ext.initialize import *


class Quest(commands.Cog):

    def __init__(self, client):

        self.client = client
        self.prefix = self.client.command_prefix

        self.dictionary = config.find_one({"dict": 2}, {"_id": 0})
        self.listings = config.find_one({"list": 2}, {"_id": 0})

        self.quest1_responses = self.dictionary["quest1_responses"]

        self.flexibilities = self.listings["flexibilities"]
        self.lengths = self.listings["lengths"]
        self.patronuses = self.listings["patronuses"]
        self.traits = self.listings["traits"]

        self.woods = self.listings["woods"]

    def get_responses_quest1(self, key):
        return self.quest1_responses[key]

    async def logging(self, msg):
        channel = self.client.get_channel(int(id_scroll))
        await channel.send(f"[{get_time().strftime('%Y-%b-%d %HH')}] " + msg)

    @commands.command(aliases=["hint"])
    @commands.has_role("🐬")
    async def hint_request(self, ctx):

        user = ctx.author
        cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(user.id)
        t1 = datetime.strptime(timestamp, "%Y-%b-%d %HH")
        t2 = datetime.strptime(get_time().strftime("%Y-%b-%d %HH"), "%Y-%b-%d %HH")
        delta = (t2 - t1).days * 24 + (t2 - t1).seconds // 3600

        if delta < 1:
            await process_msg_submit(ctx.channel, f"{user.mention}, you must wait until the clock ticks an hour", None)

        elif delta >= 1:
            try:
                hint, hint_num, h = "", 0, 0
                while h <= 5:
                    if user_hints[path][h] == "locked":
                        hint_num = str(h + 1)
                        hint = hints.find_one({
                            "quest": 1, f"{path}.{hint_num}": {"$type": 2}}, {
                            "_id": 0, f"{path}.{hint_num}": 1
                        })[path][hint_num]
                        break
                    h += 1

            except (IndexError, KeyError):
                await process_msg_submit(user, "You have used up all your hints for this path.", None)

            else:
                embed = discord.Embed(color=user.colour, description="*\"" + hint + "\"*", timestamp=get_timestamp())
                embed.set_footer(
                    icon_url=user.avatar_url,
                    text=f"Quest# 1 | Path# {path[4::]} | Hint# {hint_num}"
                )
                await update_hint_quest1(user, path, cycle, h)
                await penalize_quest1(user, cycle, points=10)
                await process_msg_reaction_add(ctx.message, "✅")
                await process_msg_submit(user, None, embed)

    @commands.Cog.listener()
    async def on_message(self, m):

        if m.author == self.client.user:
            return

        elif isinstance(m.channel, discord.DMChannel):
            return

        elif m.author.bot:
            return

        elif not check_if_user_has_accepted(m.author):
            return

        else:
            msg = m.content.lower()
            user = m.author
            role_dolphin = discord.utils.get(m.guild.roles, name="🐬")

            if user not in role_dolphin.members:
                return

            elif spell_check(m.content) and user in role_dolphin.members:
                await Expecto(self.client).expecto_spell_check(m.guild, user, m.channel, m)

            elif str(m.channel.category.id) == id_diagon_alley:

                if msg == "eeylops owl emporium" and str(m.channel) != "eeylops-owl-emporium":
                    await Expecto(self.client).expecto_create_emporium(m.channel.category, m.guild, msg, m, user)

                elif msg in ["gringotts bank", "gringotts wizarding bank"] and str(m.channel) != "gringotts-bank":
                    await self.quest_gringotts_create(m.channel.category, m.guild, m, user)

                elif msg == "ollivanders" and str(m.channel) != "ollivanders":
                    await Expecto(self.client).expecto_create_ollivanders(m.channel.category, m.guild, msg, m, user)

                elif "gringotts-bank" == str(m.channel) and m.content.startswith(f"{self.prefix}") is False:
                    await self.quest_gringotts_transact(user, m.guild, m)

    async def quest_gringotts_create(self, category, guild, message, user):

        role_galleons = discord.utils.get(message.guild.roles, name="💰")
        channels = [channel.name for channel in category.text_channels]
        cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(user.id)

        list_thieves_name = []
        for thief in thieves.find_one({}, {"_id": 0, "names": 1})["names"]:
            try:
                list_thieves_name.append(guild.get_member(int(thief)).display_name)
            except AttributeError:
                continue

        formatted_thieves = "\n".join(list_thieves_name)
        topic = f"List of Potential Thieves:\n{formatted_thieves}"

        if "gringotts-bank" not in channels and int(get_time().strftime("%H")) in [9, 10, 11, 12, 21, 22, 23, 0]:

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True),
                guild.get_member(user.id): discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    read_message_history=True
                )
            }

            gringotts = await guild.create_text_channel(
                "gringotts-bank",
                category=category,
                overwrites=overwrites,
                topic=topic
            )
            await generate_data(guild, "gringotts-bank", gringotts)
            await process_msg_reaction_add(message, "✨")

            if user not in role_galleons.members:
                if path not in ["path8", "path18", "path12", "path13", "path0"]:
                    await Expecto(self.client).expecto_update_path(user, cycle, path_new="path8")
                await asyncio.sleep(3)
                await process_msg_delete(message, 0)
            else:
                await asyncio.sleep(3)
                await process_msg_delete(message, 0)
                await penalize_quest1(user, cycle, points=30)

        elif "gringotts-bank" in channels and int(get_time().strftime("%H")) in [9, 10, 11, 12, 21, 22, 23, 0]:

            gringotts_id = guilds.find_one({"server": str(guild.id)}, {"gringotts-bank": 1})["gringotts-bank"]["id"]
            gringotts_channel = self.client.get_channel(int(gringotts_id))

            await gringotts_channel.set_permissions(
                user,
                read_messages=True,
                send_messages=True,
                read_message_history=True
            )
            await process_msg_reaction_add(message, "✨")
            await process_channel_edit(gringotts_channel, None, topic)

            if user not in role_galleons.members:
                if path not in ["path8", "path18", "path12", "path13", "path0"]:
                    await Expecto(self.client).expecto_update_path(user, cycle, path_new="path8")
                await asyncio.sleep(3)
                await process_msg_delete(message, 0)
            else:
                await asyncio.sleep(3)
                await process_msg_delete(message, 0)
                await penalize_quest1(user, cycle, points=30)

        else:
            await reaction_closed(message)

    async def quest_gringotts_transact(self, user, guild, message):

        role_galleons = discord.utils.get(message.guild.roles, name="💰")
        cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(user.id)

        if user in role_galleons.members:

            if actions >= 3:
                return

            else:
                responses = self.get_responses_quest1("gringotts_bank")
                msg = responses["has_moneybag"].format(user.mention)
                await secret_response(message.channel.name, msg)
                await action_update_quest1(user, cycle, actions=3)
                await penalize_quest1(user, cycle, points=20)

        elif user not in role_galleons.members:

            if actions >= 3:
                return

            elif actions < 3 and message.content.lower() in ["vault", "money", "galleon", "galleons"]:
                responses = self.get_responses_quest1("gringotts_bank")
                await action_update_quest1(user, cycle, actions=10)
                await self.quest_gringotts_vault_access(user, guild, role_galleons, message, responses)

            elif actions < 3:
                responses = self.get_responses_quest1("gringotts_bank")
                msg = responses["transaction"][actions].format(user.mention)
                await secret_response(message.channel.name, msg)
                await action_update_quest1(user, cycle, actions=1)
                await penalize_quest1(user, cycle, points=10)

    async def quest_gringotts_vault_access(self, user, guild, role_galleons, message, responses):

        identity = await self.quest_gringotts_vault_identity(user, message, responses)

        if identity == "Correct":
            vault_number = await self.quest_gringotts_vault_number(user, message, responses)

            if vault_number == "Correct":
                vault_password = await self.quest_gringotts_vault_password(user, message, responses)

                if vault_password == "Correct":
                    msg1 = f"{user.mention} has acquired 💰 role"
                    msg2 = responses["success"].format(user.mention)
                    vault = f"{str(user.id).replace('1', '@').replace('5', '%').replace('7', '&').replace('3', '#')}"

                    secret = guilds.find_one({"server": str(guild.id)}, {"_id": 0, str(message.channel.name): 1})
                    webhook_url = secret[str(message.channel.name)]["webhook"]
                    avatar = secret[str(message.channel.name)]["avatar"]
                    username = secret[str(message.channel.name)]["username"]

                    cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(user.id)

                    embed = DiscordEmbed(color=0xffffff, title=f"🔐 Opening Vault# {vault}")
                    embed.set_image(url="https://i.imgur.com/RIS1TLh.gif")

                    webhook = DiscordWebhook(url=webhook_url, avatar_url=avatar, username=username)
                    webhook.add_embed(embed)
                    webhook.execute()

                    if path != "path0":
                        await Expecto(self.client).expecto_update_path(user, cycle, path_new="path15")

                    await process_role_add(user, role_galleons)
                    await asyncio.sleep(6)
                    await process_msg_submit(message.channel, msg1, None)
                    await secret_response(message.channel.name, msg2)

                    thieves.update_one({}, {"$pull": {"names": str(user.id)}})

    async def quest_gringotts_vault_identity(self, user, message, responses):

        answer, topic = "Wrong", ""
        msg = responses["get_identity"]["1"].format(user.mention)
        await secret_response(message.channel.name, msg)
        cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(user.id)

        if path != "path0":
            await Expecto(self.client).expecto_update_path(user, cycle, path_new="path21")

        def check(g):
            key = (str(user.avatar_url).rsplit('/', 2)[1:])[1][:32:]
            if g.channel != message.channel:
                return
            elif str(g.content) == key and g.author == user and g.channel == message.channel:
                return True
            elif g.author == user and f"{self.prefix}" not in str(g.content):
                raise KeyError

        i = 0
        while i < 3:
            try:
                guess = await self.client.wait_for("message", timeout=120, check=check)

            except asyncio.TimeoutError:
                answer = "Wrong"
                msg = responses["get_identity"]["timeout"][0].format(user.mention)
                topic = responses["get_identity"]["timeout"][1]

                if thieves.find_one({"names": str(user.id)}, {"_id": 0}) is None:
                    thieves.update_one({}, {"$push": {"names": str(user.id)}})

                await Expecto(self.client).expecto_update_path(user, cycle, path_new="path18")
                await action_update_quest1(user, cycle, actions=3)
                await penalize_quest1(user, cycle, points=10)
                await secret_response(message.channel.name, msg)
                await process_channel_edit(message.channel, None, topic)
                break

            except KeyError:

                if i == 0:
                    msg = responses["get_identity"]["invalid1"][0].format(user.mention)
                    topic = responses["get_identity"]["invalid1"][1]
                    await penalize_quest1(user, cycle, points=10)

                elif i == 1:
                    msg = responses["get_identity"]["invalid2"][0].format(user.mention)
                    topic = responses["get_identity"]["invalid2"][1]
                    await penalize_quest1(user, cycle, points=10)

                elif i == 2:
                    msg = responses["get_identity"]["invalid3"][0].format(user.mention)
                    topic = responses["get_identity"]["invalid3"][1]

                    if thieves.find_one({"names": str(user.id)}, {"_id": 0}) is None:
                        thieves.update_one({}, {"$push": {"names": str(user.id)}})

                    await Expecto(self.client).expecto_update_path(user, cycle, path_new="path18")
                    await action_update_quest1(user, cycle, actions=3)
                    await penalize_quest1(user, cycle, points=10)

                await process_channel_edit(message.channel, None, topic)
                await secret_response(message.channel.name, msg)
                i += 1

            else:
                answer = "Correct"
                await process_msg_reaction_add(guess, "✅")
                await asyncio.sleep(3)
                await process_msg_delete(guess, 0)
                break

        return answer

    async def quest_gringotts_vault_number(self, user, message, responses):

        answer, topic = "Wrong", ""
        msg = responses["get_vault"]["1"].format(user.mention)
        await secret_response(message.channel.name, msg)
        cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(user.id)

        if path != "path0":
            await Expecto(self.client).expecto_update_path(user, cycle, path_new="path22")

        if path == "path18":
            await Expecto(self.client).expecto_update_path(user, cycle, path_new="path5")

        def check(g):
            if g.channel != message.channel:
                return
            elif str(g.content) == str(user.id) and g.author == user and g.channel == message.channel:
                return True
            elif g.author == user and f"{self.prefix}" not in str(g.content):
                raise KeyError

        i = 0
        while i < 3:
            try:
                guess = await self.client.wait_for("message", timeout=120, check=check)

            except asyncio.TimeoutError:
                answer = "Wrong"
                msg = responses["get_vault"]["timeout"][0].format(user.mention)
                topic = responses["get_vault"]["timeout"][1]

                if thieves.find_one({"names": str(user.id)}, {"_id": 0}) is None:
                    thieves.update_one({}, {"$push": {"names": str(user.id)}})

                await Expecto(self.client).expecto_update_path(user, cycle, path_new="path12")
                await action_update_quest1(user, cycle, actions=3)
                await penalize_quest1(user, cycle, points=10)
                await secret_response(message.channel.name, msg)
                await process_channel_edit(message.channel, None, topic)
                break

            except KeyError:

                if i == 0:
                    msg = responses["get_vault"]["invalid1"][0].format(user.mention)
                    topic = responses["get_vault"]["invalid1"][1]
                    await penalize_quest1(user, cycle, points=10)

                elif i == 1:
                    msg = responses["get_vault"]["invalid2"][0].format(user.mention)
                    topic = responses["get_vault"]["invalid2"][1]
                    await penalize_quest1(user, cycle, points=10)

                elif i == 2:
                    answer = "Wrong"
                    msg = responses["get_vault"]["invalid3"][0].format(user.mention)
                    topic = responses["get_vault"]["invalid3"][1]

                    if thieves.find_one({"names": str(user.id)}, {"_id": 0}) is None:
                        thieves.update_one({}, {"$push": {"names": str(user.id)}})

                    await Expecto(self.client).expecto_update_path(user, cycle, path_new="path12")
                    await action_update_quest1(user, cycle, actions=3)
                    await penalize_quest1(user, cycle, points=10)

                await process_channel_edit(message.channel, None, topic)
                await secret_response(message.channel.name, msg)
                i += 1

            else:
                answer = "Correct"
                await process_msg_reaction_add(guess, "✅")
                await asyncio.sleep(3)
                await process_msg_delete(guess, 0)
                break

        return answer

    async def quest_gringotts_vault_password(self, user, message, responses):

        answer, topic, msg = "Wrong", "", ""
        msg1 = responses["get_password"]["1"].format(user.mention)
        msg2 = responses["get_password"]["2"].format(user.mention)
        await asyncio.sleep(1)
        await secret_response(message.channel.name, msg1)
        await asyncio.sleep(3)
        await secret_response(message.channel.name, msg2)
        cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(user.id)

        if path != "path0":
            await Expecto(self.client).expecto_update_path(user, cycle, path_new="path23")

        def check(g):
            if g.channel != message.channel:
                return
            elif str(g.content) == (str(user.id))[::-1] and g.author == user \
                    and g.channel == message.channel:
                return True
            elif g.author == user and f"{self.prefix}" not in str(g.content):
                raise KeyError

        i = 0
        while i < 3:
            try:
                guess = await self.client.wait_for("message", timeout=120, check=check)

            except asyncio.TimeoutError:
                answer = "Wrong"
                msg = responses["get_password"]["timeout"][0].format(user.mention)
                topic = responses["get_password"]["timeout"][1]

                if thieves.find_one({"names": str(user.id)}, {"_id": 0}) is None:
                    thieves.update_one({}, {"$push": {"names": str(user.id)}})

                await Expecto(self.client).expecto_update_path(user, cycle, path_new="path13")
                await action_update_quest1(user, cycle, actions=3)
                await penalize_quest1(user, cycle, points=10)
                await secret_response(message.channel.name, msg)
                await process_channel_edit(message.channel, None, topic)
                break

            except KeyError:

                if i == 0:
                    msg = responses["get_password"]["invalid1"][0].format(user.mention)
                    topic = responses["get_password"]["invalid1"][1]
                    await penalize_quest1(user, cycle, points=10)

                elif i == 1:
                    msg = responses["get_password"]["invalid2"][0].format(user.mention)
                    topic = responses["get_password"]["invalid2"][1]
                    await penalize_quest1(user, cycle, points=10)

                elif i == 2:
                    answer = "Wrong"
                    msg = responses["get_password"]["invalid3"][0].format(user.mention)
                    topic = responses["get_password"]["invalid3"][1]

                    if thieves.find_one({"names": str(user.id)}, {"_id": 0}) is None:
                        thieves.update_one({}, {"$push": {"names": str(user.id)}})

                    await Expecto(self.client).expecto_update_path(user, cycle, path_new="path13")
                    await action_update_quest1(user, cycle, actions=3)
                    await penalize_quest1(user, cycle, points=10)

                await process_channel_edit(message.channel, None, topic)
                await secret_response(message.channel.name, msg)
                i += 1

            else:
                answer = "Correct"
                await process_msg_reaction_add(guess, "✅")
                await asyncio.sleep(3)
                await process_msg_delete(guess, 0)
                break

        return answer


class Expecto(commands.Cog):

    def __init__(self, client):

        self.client = client
        self.prefix = self.client.command_prefix

        self.dictionary = config.find_one({"dict": 2}, {"_id": 0})
        self.listings = config.find_one({"list": 2}, {"_id": 0})

        self.owl_type = self.dictionary["owl_type"]
        self.quest1_responses = self.dictionary["quest1_responses"]
        self.length_category = self.dictionary["length_category"]
        self.flexibility_category = self.dictionary["flexibility_category"]

        self.cores = self.listings["cores"]
        self.wand_lengths = self.listings["wand_lengths"]
        self.flexibility_types = self.listings["flexibility_types"]

        self.owls_list = []
        for owl in owls.find({"key": "owl"}, {"_id": 0, "type": 1}):
            self.owls_list.append(owl["type"])

    def get_length_category(self, x):
        return self.length_category[x]

    def get_flexibility_category(self, wand_flexibility):
        return self.flexibility_category[wand_flexibility]

    def get_owl_type(self, x):
        return self.owl_type[x]

    def get_responses_quest1(self, key):
        return self.quest1_responses[key]

    async def expecto_send_off_complete_quest1(self):

        for entry in sendoffs.find({"timestamp_complete": get_time().strftime("%Y-%b-%d %HH")}, {"_id": 0}):
            try:
                user = self.client.get_user(int(entry["user_id"]))
                cycle, path, timestamp, user_hint, actions, purchase = get_data_quest1(user.id)
            except AttributeError:
                continue

            if entry["scenario"] == 2:
                async with user.typing():
                    responses = self.get_responses_quest1("send_off")["complete"]

                    if path != "path0":
                        await self.expecto_update_path(user, cycle, path_new="path3")

                    await process_msg_submit(user, responses[0], None)
                    await asyncio.sleep(4)
                    await process_msg_submit(user, responses[1], None)
                    await asyncio.sleep(4)
                    msg = await process_msg_submit(user, responses[2].format(entry['type'].capitalize()), None)
                    await process_msg_reaction_add(msg, "✉")
                    sendoffs.update_one({"user_id": str(user.id), "cycle": cycle}, {"$set": {"status": "done"}})

            elif entry["scenario"] == 1:

                await self.expecto_update_path(user, cycle, path_new="path20")
                await process_msg_submit(user, "Your {entry['type']} has fully recovered", None)
                sendoffs.update_one({
                    "user_id": str(user.id), "cycle": cycle}, {
                    "$unset": {
                        "delay": "",
                        "report": "",
                        "scenario": "",
                        "timestamp": "",
                        "timestamp_complete": "",
                        "timestamp_update": "",
                        "weather1": "",
                        "weather2": ""
                    }
                })

    async def expecto_sendoff_report(self):

        query = sendoffs.find({"quest": 1, "timestamp_update": get_time().strftime("%Y-%b-%d %HH")}, {"_id": 0})

        for entry in query:
            user = self.client.get_user(int(entry["user_id"]))

            if entry["scenario"] == 1:
                try:
                    cycle, path, timestamp, user_hint, actions, purchase = get_data_quest1(user.id)
                    await penalize_quest1(user, cycle, points=20)
                except AttributeError:
                    continue

            embed = discord.Embed(color=0xffffff, title="Owl Report", description=entry["report"])
            embed.set_footer(text=f"{entry['timestamp_update']}")

            await process_msg_submit(user, None, embed)
            await asyncio.sleep(1)

    async def expecto_spell_check(self, guild, user, channel, message):

        role_star = discord.utils.get(guild.roles, name="🌟")
        cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(user.id)

        if path in ["path3", "path0", "path25"] and user not in role_star.members:
            await process_msg_reaction_add(message, "❎")
            await self.expecto_update_path(user, cycle, path_new="path10")
            await penalize_quest1(user, cycle, points=5)

        elif path == "path10":
            await process_msg_reaction_add(message, "❔")
            await penalize_quest1(user, cycle, points=15)

        elif user in role_star.members:

            async with channel.typing():

                role_dolphin = discord.utils.get(guild.roles, name="🐬")
                role_galleon = discord.utils.get(guild.roles, name="💰")
                role_owl = discord.utils.get(guild.roles, name="🦉")
                cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(user.id)
                uppers = len([char for char in message.content if char.isupper()])
                lowers = len([char for char in message.content if char.islower()])
                symbol = len([char for char in message.content if char == "!"])
                strength = round((uppers * 1.35) + lowers + (symbol * 1.5), 2)
                strength = round(random.uniform(strength - 5, strength + 5), 2)

                if strength > 100:
                    strength = round(random.uniform(98, 99.99), 2)

                added_points = round(50 * (strength / 100))

                score, timestamp_start, patronus_summon, hints_unlocked, owl_final, wand, paths \
                    = get_profile_finished_quest1(user)

                t1 = datetime.strptime(timestamp_start, "%Y-%b-%d %HH")
                t2 = datetime.strptime(get_time().strftime("%Y-%b-%d %HH"), "%Y-%b-%d %HH")
                delta = (t2 - t1).days * 24 + (t2 - t1).seconds // 3600

                paths_unlocked = ""
                for y in list(paths.keys()):
                    paths_unlocked += "{}, ".format(y.replace("path", ""))

                description = \
                    f"• Cycle Score: {score + added_points} points, (+{added_points} bonus points)\n" \
                    f"• Hints unlocked: {hints_unlocked}\n" \
                    f"• No. of Paths unlocked: {len(paths)}\n" \
                    f"• Paths unlocked: [{paths_unlocked[:-2]}]\n" \
                    f"• Owl: {owl_final.title()} [{patronus_summon['trait'].title()}]"

                quests.update_one({
                    "user_id": str(user.id), "quest1.cycle": cycle}, {
                    "$inc": {
                        "quest1.$.score": added_points
                    },
                    "$set": {
                        "quest1.$.strength": strength,
                        "quest1.$.timestamp": get_time().strftime("%Y-%b-%d %HH"),
                        "quest1.$.status": "completed"
                    }
                })

                embed = discord.Embed(
                    color=0x50e3c2, description=description,
                    title=f"Patronus: {patronus_summon['patronus'].title()} | Strength: {strength}%",
                )
                embed.set_image(url=patronus_summon["link"])
                embed.set_footer(text=f"Hours spent: {delta} hours")
                embed.set_author(
                    name=f"{user.display_name} | Cycle #{cycle} results!",
                    icon_url=user.avatar_url
                )
                embed.add_field(
                    name="Wand Properties",
                    value=f"{wand['length']} inches, {wand['flexibility']}, {wand['core'].replace(' ', '-')}-cored, "
                          f"{wand['wood']} wand"
                )
                content = f"{user.mention}, 🎊 **Congratulations!** You have finished the quest!"
                await user.remove_roles(role_dolphin, role_galleon, role_owl, role_star)
                await process_msg_submit(channel, content, embed)

    async def expecto_sendoff_owl(self, user, cycle):

        responses = self.get_responses_quest1("send_off")
        await process_msg_submit(user, responses["success1"], None)
        await asyncio.sleep(2)
        await process_msg_submit(user, responses["success2"], None)
        await self.expecto_owl_report_generate(user, cycle, responses)

    async def expecto_owl_report_generate(self, user, cycle, responses):

        query = sendoffs.find_one({"user_id": str(user.id), "cycle": cycle}, {"_id": 0})
        weather1 = weather.find_one({"weather1": {"$type": "string"}}, {"weather1": 1})["weather1"]
        weather2 = weather.find_one({"weather2": {"$type": "string"}}, {"weather2": 1})["weather2"]

        def get_specific_report(key):
            return responses["reports"][key]["delay"], \
                   responses["reports"][key]["scenario"], \
                   responses["reports"][key]["content"]

        if weather1 == "⛈":
            delay, scenario, content = get_specific_report("thunderstorms")
            await self.expecto_update_path(user, cycle, path_new="path19")

        elif weather1 == "🌨" and query["type"] == "snowy":
            delay, scenario, content = get_specific_report("snowy_snowy_owl")

        elif weather2 == "🌕" or weather2 == "🌑":
            delay, scenario, content = get_specific_report("night_time")

        elif weather1 == "🌧" or weather1 == "🌨":
            delay, scenario, content = get_specific_report("rainy_snowy")

        else:
            delay, scenario, content = get_specific_report("cloudy_sunny")

        timestamp_update = (get_time() + timedelta(days=1 / 24)).strftime("%Y-%b-%d %HH")
        timestamp_complete = (get_time() + timedelta(days=delay / 24)).strftime("%Y-%b-%d %HH")

        sendoffs.update_one({
            "user_id": str(user.id),
            "cycle": cycle}, {
            "$set": {
                "report": content,
                "weather1": weather1,
                "weather2": weather2,
                "timestamp": get_time().strftime("%Y-%b-%d %HH"),
                "timestamp_update": timestamp_update,
                "timestamp_complete": timestamp_complete,
                "delay": delay,
                "scenario": scenario,
                "quest": 1
            }
        })

    async def expecto_update_path(self, user, cycle, path_new):

        quests.update_one({
            "user_id": str(user.id), "quest1.cycle": cycle}, {
            "$set": {
                "quest1.$.current_path": path_new
            }
        })

        path_profile = quests.find_one({
            "user_id": str(user.id), "quest1.cycle": cycle}, {
            "_id": 0, "quest1.$.hints": 1
        })

        if path_new not in path_profile["quest1"][0]["hints"]:
            quests.update_one({
                "user_id": str(user.id), "quest1.cycle": cycle}, {
                "$set": {
                    f"quest1.$.hints.{path_new}": ["locked", "locked", "locked", "locked", "locked"]
                }
            })
        await Quest(self.client).logging(f"Shifted {user} path to {path_new}")

    @commands.command(aliases=["patronus"])
    @commands.check(check_if_user_has_development_role)
    @commands.guild_only()
    async def expecto_patronus_show(self, ctx, *, _patronus):

        query = patronus.find({"patronus": _patronus.lower()})
        patronus_descriptions = []

        name, link = "", ""
        for profile in query:
            name = profile["patronus"]
            wood = profile["wood"]
            flexibility = profile["flexibility"]
            length = profile["length"]
            core = profile["core"]
            trait = profile["trait"]
            link = profile["link"]

            description = \
                f"Owl Requirements: \n" \
                f"• Type: {self.get_owl_type(trait)} owl\n" \
                f"•Trait: {trait.title()}\n\n" \
                f"Wand Requirements:\n" \
                f"• Flexibility: {flexibility.title()}\n" \
                f"• Length: {length.title()}\n" \
                f"• Core: {core.title()}\n" \
                f"• Wood: {wood.title()}\n"

            patronus_descriptions.append(description)

        embed1 = discord.Embed(
            color=0x50e3c2, title=f"{name.title()} | Combination # 1",
            description=patronus_descriptions[0]
        )
        embed1.set_image(url=link)

        msg = await process_msg_submit(ctx.channel, None, embed1)

        emojis_add = ["⬅", "➡"]
        for emoji in emojis_add:
            await process_msg_reaction_add(msg, emoji)

        def check(r, u):
            return u != self.client.user and r.message.id == msg.id

        def create_embed(p):

            try:
                embed = discord.Embed(
                    color=0x50e3c2,
                    title=f"{name.title()} | Combination # {p + 1}",
                    description=patronus_descriptions[p]
                )
                embed.set_image(url=link)

            except IndexError:
                embed = embed1

            return embed

        page = 0
        while True:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=60, check=check)
            except asyncio.TimeoutError:
                await process_msg_reaction_clear(msg)
                break
            else:
                if str(reaction.emoji) == emojis_add[1]:
                    page += 1
                elif str(reaction.emoji) == emojis_add[0]:
                    page -= 1
                await process_msg_edit(msg, None, create_embed(page))
                await process_msg_reaction_remove(msg, str(reaction.emoji), user)

    async def expecto_show_cycle_help(self, ctx):

        embed = discord.Embed(
            colour=colour, title="cycle",
            description="Patronus quest command participants only"
        )
        embed.add_field(
            name="Format", inline=False,
            value=f"*`{self.prefix}cycle <cycle#1> <optional: @member>`*"
        )
        embed.add_field(name="Example", value=f"*`{self.prefix}cycle 1`*")
        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["cycle"])
    @commands.guild_only()
    async def expecto_show_cycle(self, ctx, cycle_query=None, *, user: discord.Member = None):

        requestor = ctx.author
        requestor_profile = quests.find_one({"user_id": str(requestor)}, {"_id": 0})

        if cycle_query is None:
            await self.expecto_show_cycle_help(ctx)

        if requestor_profile is None:
            await process_msg_submit(ctx.channel, "You have to finish your own first cycle first.", None)

        elif requestor_profile is not None:

            profile = {}
            for result in quests.aggregate([{
                "$match": {"user_id": str(requestor.id)}}, {
                "$project": {"_id": 0, "status": {"$slice": ["$quest1.status", 1]}}
            }]):
                profile = result
                break

            if profile["status"][0] == "ongoing":
                await process_msg_submit(ctx.channel, "You have to finish your own first cycle first.", None)

            elif profile["status"][0] == "completed":

                try:
                    cycle_query = int(cycle_query)
                except (ValueError, TypeError):
                    await process_msg_submit(ctx.channel, f"Use `{self.prefix}cycle <cycle#> <@mention>.", None)
                else:
                    if user is None:
                        user = ctx.message.author

                    profile = get_profile_history_quest1(user, cycle_query)
                    patronus_summon = profile["quest1"]["patronus"]["patronus"]
                    score = profile["quest1"]["score"]
                    timestamp_start = profile["quest1"]["timestamp_start"]
                    timestamp_end = profile["quest1"]["timestamp"]
                    hints_unlocked = profile["quest1"]["hints_unlocked"]
                    owl_final = profile["quest1"]["owl"]
                    wand = profile["quest1"]["wand"]
                    paths = profile["quest1"]["hints"]
                    strength = profile["quest1"]["strength"]
                    patronus_profile = profile["quest1"]["patronus"]

                    t1 = datetime.strptime(timestamp_start, "%Y-%b-%d %HH")
                    t2 = datetime.strptime(timestamp_end, "%Y-%b-%d %HH")
                    delta = (t2 - t1).days * 24 + (t2 - t1).seconds // 3600

                    paths_unlocked = ""
                    for y in list(paths.keys()):
                        paths_unlocked += "{}, ".format(y.replace("path", ""))

                    description = \
                        f"• Cycle Score: {score} points\n" \
                        f"• Hints unlocked: {hints_unlocked}\n" \
                        f"• No. of paths unlocked: {len(paths)}\n" \
                        f"• Paths unlocked: [{paths_unlocked[:-2]}]\n" \
                        f"• Owl: {owl_final.title()} [{patronus_profile['trait'].title()}]"

                    embed = discord.Embed(
                        color=0x50e3c2, title=f"Your Patronus: {patronus_summon.title()} | Strength: {strength}%",
                        description=description
                    )
                    embed.set_image(url=patronus_profile["link"])
                    embed.set_footer(text=f"Hours spent: {delta} hours")
                    embed.set_author(
                        name=f"{user.display_name} | Cycle #{cycle_query} results",
                        icon_url=user.avatar_url
                    )
                    embed.add_field(
                        name="Wand Properties",
                        value=f"{wand['length']} inches, {wand['flexibility']}, {wand['core'].replace(' ', '-')}-cored,"
                              f" {wand['wood']} wand"
                    )
                    await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["progress"])
    @commands.has_role("🐬")
    async def expecto_progress(self, ctx):

        user = ctx.message.author
        query = quests.find_one({"user_id": str(user.id)}, {"_id": 0})

        if query is None:
            await process_msg_submit(ctx.channel, "You have to signup first to the quest.", None)

        elif query is not None:

            score, timestamp_start, current_path, cycle, hints_unlocked, paths = get_profile_progress_quest1(user)
            t1 = datetime.strptime(timestamp_start, "%Y-%b-%d %HH")
            t2 = datetime.strptime(get_time().strftime("%Y-%b-%d %HH"), "%Y-%b-%d %HH")
            hours_passed = (t2 - t1).days * 24 + (t2 - t1).seconds // 3600

            paths_unlocked = ""
            for y in list(paths.keys()):
                paths_unlocked += "{}, ".format(y.replace("path", ""))

            description = \
                f"• Current Score: {score}\n" \
                f"• Hours passed: {hours_passed}\n" \
                f"• Penalties: {1000 - score}\n" \
                f"• Current path: {current_path.replace('path', 'Path ').capitalize()}\n" \
                f"• No. of paths unlocked: {len(paths)}\n" \
                f"• Paths unlocked: {paths_unlocked[:-2]}\n" \
                f"• Hints unlocked: {hints_unlocked}"

            embed = discord.Embed(color=user.colour, description=description)
            embed.set_author(
                name=f"{user}'s Cycle #{cycle}",
                icon_url=user.avatar_url
            )
            await process_msg_submit(user, None, embed)
            await process_msg_reaction_add(ctx.message, "✅")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):

        if str(payload.emoji) != "🐬":
            return

        elif self.client.get_user(payload.user_id).bot is True:
            return

        server_ = self.client.get_guild(payload.guild_id)
        role_dolphin = discord.utils.get(server_.roles, name="🐬")
        user = self.client.get_user(payload.user_id)

        if user in role_dolphin.members:
            return

        query = guilds.find_one({
            "server": f"{payload.guild_id}"}, {
            "_id": 0, "messages.quests": 1
        })

        if str(payload.emoji) == "🐬" and payload.message_id == int(query["messages"]["quests"]):
            member = server_.get_member(user.id)

            if quests.find_one({"user_id": str(user.id)}, {"_id": 0}) is None:
                profile = {"user_id": str(payload.user_id), "server": str(payload.guild_id), "quest1": []}
                quests.insert_one(profile)

            for i in (range(300)):
                cycle = i + 1

                if len(quests.find_one({"user_id": str(payload.user_id)}, {"_id": 0})["quest1"]) < cycle:
                    quests.update_one({
                        "user_id": str(user.id)}, {
                        "$push": {
                            "quest1": dict(
                                status="ongoing",
                                cycle=cycle,
                                score=1000,
                                timestamp=get_time().strftime("%Y-%b-%d %HH"),
                                timestamp_start=get_time().strftime("%Y-%b-%d %HH"),
                                current_path="path0",
                                paths_unlocked=0,
                                actions=0,
                                purchase=True,
                                hints_unlocked=0,
                                hints={"path0": ["locked", "locked", "locked", "locked", "locked"]}
                            )
                        }
                    })
                    await Quest(self.client).logging(f"Started quest1: cycle#{cycle} for {user}")
                    break

            await member.add_roles(role_dolphin)
            responses = self.get_responses_quest1("start_quest")

            async with user.typing():
                await asyncio.sleep(3)
                await user.send(responses["1"])
                await asyncio.sleep(5)
                await user.send(responses["2"])
                await asyncio.sleep(6)
                await user.send(responses["3"])
                await asyncio.sleep(5)
                await user.send(responses["4"])
                await asyncio.sleep(5)
                msg = await user.send(responses["5"])
                await asyncio.sleep(2)
                await msg.add_reaction("✉")

    @commands.Cog.listener()
    async def on_reaction_add(self, r, u):

        msg = r.message.content

        if u == self.client.user:
            return

        elif u.bot:
            return

        elif str(r.emoji) == "✉" and u != self.client.user \
                and "envelope" in msg and r.message.author == self.client.user:

            cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(u.id)
            server_ = quests.find_one({"user_id": str(u.id)}, {"_id": 0, "server": 1})
            query = guilds.find_one({
                "server": server_["server"]}, {
                "_id": 0, "channels.welcome": 1, "channels.sorting-hat": 1
            })

            description = self.get_responses_quest1("start_quest")["letter"].format(
                u.name, query["channels"]["welcome"], query["channels"]["sorting-hat"]
            )
            embed = discord.Embed(color=0xffff80, title="Acceptance Letter", description=description)
            embed.set_thumbnail(url=self.client.get_guild(int(server_["server"])).icon_url)
            await process_msg_submit(u, None, embed)
            await self.expecto_update_path(u, cycle, path_new="path1")
            await penalize_quest1(u, cycle, points=20)

        elif str(r.emoji) == "✉" and "returned with" in msg and r.message.author == self.client.user:

            server_ = quests.find_one({"user_id": str(u.id)}, {"_id": 0, "server": 1})
            cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(u.id)
            description = self.get_responses_quest1("send_off")["letter"].format(u.name)
            embed = discord.Embed(color=0xffff80, description=description)
            embed.set_thumbnail(url=self.client.get_guild(int(server_["server"])).icon_url)

            if path != "path0":
                await Expecto(self.client).expecto_update_path(u, cycle, path_new="path25")
                await penalize_quest1(u, cycle, points=25)

            await process_msg_submit(u, None, embed)

        elif str(r.emoji) == "🦉":

            role_owl = discord.utils.get(r.message.guild.roles, name="🦉")
            query = guilds.find_one({
                "server": f"{r.message.guild.id}"}, {
                "_id": 0, "channels.absence-applications": 1
            })
            valid_channel_id = query["channels"]["absence-applications"]
            cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(u.id)

            if u not in role_owl.members:
                await penalize_quest1(u, cycle, points=30)

            elif (valid_channel_id not in msg or id_headmaster not in msg) and "✉" not in msg:

                await r.message.add_reaction("❔")
                await penalize_quest1(u, cycle, points=10)

            elif (valid_channel_id in msg or id_headmaster in msg) and "✉" in msg:

                cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(u.id)

                if path in ["path0", "path2", "path20"]:
                    if path != "path0":
                        await self.expecto_update_path(u, cycle, path_new="path4")

                    await self.expecto_sendoff_owl(u, cycle)
                    await r.message.add_reaction("✅")
                    await asyncio.sleep(2)
                    await r.message.delete()

                elif path == "path19":
                    msg = self.get_responses_quest1("send_off")["penalize"]
                    await penalize_quest1(u, cycle, points=20)
                    await process_msg_submit(u, msg, None)
                    await asyncio.sleep(2)
                    await process_msg_delete(r.message, 0)

    @commands.command(aliases=["knock", "inquire"])
    @commands.guild_only()
    @commands.has_role("🐬")
    async def expecto_transact_emporium(self, ctx):

        if str(ctx.channel.name) != "eeylops-owl-emporium":
            return

        elif str(ctx.channel.name) == "eeylops-owl-emporium":

            user = ctx.author
            cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(user.id)

            if actions > 3:
                if ctx.message.content in [f"{self.prefix}knock", f"{self.prefix}inquire"]:
                    await process_msg_delete(ctx.message, 0)

            elif ctx.message.content == f"{self.prefix}knock":
                if path == "path6":
                    await self.expecto_update_path(user, cycle, path_new="path9")
                elif path == "path15":
                    await self.expecto_update_path(user, cycle, path_new="path16")

                responses = self.get_responses_quest1("eeylops_owl")
                msg = responses["knock"][0]
                topic = responses["knock"][1]
                await process_channel_edit(ctx.channel, None, topic)
                await process_msg_delete(ctx.message, 0)
                await secret_response(ctx.channel.name, msg)
                await penalize_quest1(user, cycle, points=15)

            elif ctx.message.content == f"{self.prefix}inquire" and actions < 3:
                if path == "path9":
                    await self.expecto_update_path(user, cycle, path_new="path14")
                elif path == "path15":
                    await self.expecto_update_path(user, cycle, path_new="path16")

                responses = self.get_responses_quest1("eeylops_owl")["inquire"]
                msg, topic = responses[actions]
                await process_channel_edit(ctx.channel, None, topic)
                await process_msg_delete(ctx.message, 0)
                await action_update_quest1(user, cycle, actions=1)
                await penalize_quest1(user, cycle, points=15)
                await secret_response(ctx.channel.name, msg)

    @commands.command(aliases=["purchase"])
    @commands.guild_only()
    @commands.has_role("🐬")
    async def expecto_buy_items(self, ctx, *args):

        if ctx.channel.name != "eeylops-owl-emporium":
            return

        elif ctx.channel.name == "eeylops-owl-emporium":

            try:
                owl_buy = args[0].lower()
            except (IndexError, TypeError, AttributeError):
                return
            else:
                user = ctx.author
                cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(user.id)
                responses = self.get_responses_quest1("eeylops_owl")

                if purchase is False:
                    msg = responses["purchasing"]["max_actions"]
                    await penalize_quest1(user, cycle, points=20)
                    await process_msg_submit(user, msg, None)
                    await process_msg_delete(ctx.message, 0)

                elif owl_buy not in self.owls_list:
                    msg = responses["purchasing"]["invalid_owl"]
                    await penalize_quest1(user, cycle, points=20)
                    await secret_response(ctx.channel.name, msg)
                    await process_msg_delete(ctx.message, 0)

                elif owl_buy in self.owls_list:
                    purchaser_id = owls.find_one({"type": f"{owl_buy}"}, {"_id": 0, "purchaser": 1})["purchaser"]
                    role_owl = discord.utils.get(ctx.guild.roles, name="🦉")
                    role_galleons = discord.utils.get(ctx.guild.roles, name="💰")

                    if user in role_owl.members:
                        msg = responses["purchasing"]["buying_again"][0].format(user.mention)
                        topic = responses["purchasing"]["buying_again"][1]
                        await penalize_quest1(user, cycle, points=75)
                        await secret_response(ctx.channel.name, msg)
                        await process_channel_edit(ctx.channel, None, topic)
                        await process_msg_delete(ctx.message, 0)

                    elif user not in role_galleons.members:
                        msg = responses["purchasing"]["no_moneybag"][0].format(user.mention)
                        topic = responses["purchasing"]["no_moneybag"][1]
                        await self.expecto_update_path(user, cycle, path_new="path7")
                        await penalize_quest1(user, cycle, points=10)
                        await secret_response(ctx.channel.name, msg)
                        await process_channel_edit(ctx.channel, None, topic)
                        await process_msg_delete(ctx.message, 0)

                        quests.update_one({
                            "user_id": str(user.id), "quest1.cycle": cycle}, {
                            "$set": {
                                "quest1.$.purchase": False
                            }
                        })

                    elif purchaser_id != "None":
                        purchaser = ctx.guild.get_member(int(purchaser_id))
                        msg = responses["purchasing"]["out_of_stock"][0].format(user.mention, purchaser.display_name)
                        topic = responses["purchasing"]["out_of_stock"][1]
                        await self.expecto_update_path(user, cycle, path_new="path24")
                        await penalize_quest1(user, cycle, points=20)
                        await secret_response(ctx.channel.name, msg)
                        await process_channel_edit(ctx.channel, None, topic)
                        await process_msg_delete(ctx.message, 0)

                        quests.update_one({
                            "user_id": str(user.id), "quest1.cycle": cycle}, {
                            "$set": {
                                "quest1.$.purchase": False
                            }
                        })

                    elif purchaser_id == "None":
                        async with ctx.channel.typing():
                            role_owl = discord.utils.get(ctx.guild.roles, name="🦉")
                            owl_profile = owls.find_one({"type": owl_buy}, {"_id": 0})
                            description = owl_profile["description"]
                            msg = responses["purchasing"]["success_purchase"][0].format(user.mention)
                            topic = responses["purchasing"]["success_purchase"][1]

                            embed = discord.Embed(description="*" + description + "*", color=user.colour)
                            embed.set_thumbnail(url=owl_profile["thumbnail"])

                            owls.update_one({"type": owl_buy}, {"$set": {"purchaser": str(user.id)}})
                            sendoffs.insert_one({"user_id": str(user.id), "type": owl_buy, "cycle": cycle})
                            quests.update_one({
                                "user_id": str(user.id),
                                "quest1.cycle": cycle}, {
                                "$set": {
                                    "quest1.$.purchase": False,
                                    "quest1.$.owl": owl_buy
                                }
                            })
                            await process_channel_edit(ctx.channel, None, topic)

                            if path != "path0":
                                await self.expecto_update_path(user, cycle, path_new="path2")

                            await process_msg_reaction_add(ctx.message, "🦉")
                            await process_role_add(user, role_owl)
                            await asyncio.sleep(1)
                            await process_msg_submit(ctx.channel, f"{user.mention} has acquired 🦉 role", None)
                            await asyncio.sleep(2)
                            await secret_response(ctx.channel.name, msg)
                            await asyncio.sleep(3)
                            await process_msg_submit(ctx.channel, None, embed)
                            await asyncio.sleep(2)
                            await process_msg_delete(ctx.message, 0)

    async def expecto_create_emporium(self, category, guild, msg, message, user):

        role_owl = discord.utils.get(guild.roles, name="🦉")
        role_galleons = discord.utils.get(guild.roles, name="💰")
        channels = [channel.name for channel in category.text_channels]
        cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(user.id)

        if "eeylops-owl-emporium" not in channels \
                and int(get_time().strftime("%H")) in [8, 9, 10, 11, 12, 13, 20, 21, 22, 23, 0, 1]:

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True),
                guild.get_member(user.id): discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    read_message_history=True
                )
            }

            emporium = await guild.create_text_channel("eeylops-owl-emporium", category=category, overwrites=overwrites)
            await generate_data(guild, msg, emporium)
            await process_msg_reaction_add(message, "✨")

            if user not in role_owl.members and user not in role_galleons.members:
                if path not in ["path9"]:
                    await self.expecto_update_path(user, cycle, path_new="path6")

            await asyncio.sleep(3)
            await process_msg_delete(message, 0)

        elif "eeylops-owl-emporium" in channels \
                and int(get_time().strftime("%H")) in [8, 9, 10, 11, 12, 13, 20, 21, 22, 23, 0, 1]:

            emporium_id = guilds.find_one({
                "server": str(guild.id)}, {
                "eeylops-owl-emporium": 1
            })

            emporium_channel = self.client.get_channel(int(emporium_id["eeylops-owl-emporium"]["id"]))

            await emporium_channel.set_permissions(
                user, read_messages=True,
                send_messages=True,
                read_message_history=True
            )
            await process_msg_reaction_add(message, "✨")

            if user not in role_owl.members and user not in role_galleons.members:
                await self.expecto_update_path(user, cycle, path_new="path6")

            await asyncio.sleep(3)
            await process_msg_delete(message, 0)

        else:
            await reaction_closed(message)

    async def expecto_create_ollivanders(self, category, guild, msg, message, user):

        channels = [channel.name for channel in category.text_channels]
        cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(user.id)

        if "ollivanders" not in channels and int(get_time().strftime("%H")) in [13, 14, 15, 16, 17, 1, 2, 3, 4, 5]:

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True),
                guild.get_member(user.id): discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    read_message_history=True
                )
            }

            ollivanders = await guild.create_text_channel("ollivanders", category=category, overwrites=overwrites)
            await generate_data(guild, msg, ollivanders)
            await process_msg_reaction_add(message, "✨")
            await asyncio.sleep(3)
            await process_msg_delete(message, 0)

            if path in ["path10", "path3", "path25"]:
                await self.expecto_update_path(user, cycle, path_new="path11")

            await self.expecto_transaction_ollivanders(guild, user, ollivanders)

        elif "ollivanders" in channels and int(get_time().strftime("%H")) in [13, 14, 15, 16, 17, 1, 2, 3, 4, 5]:

            ollivanders_id = guilds.find_one({"server": str(guild.id)}, {"ollivanders": 1})["ollivanders"]["id"]
            ollivanders_channel = self.client.get_channel(int(ollivanders_id))

            await ollivanders_channel.set_permissions(
                user,
                read_messages=True,
                send_messages=True,
                read_message_history=True
            )
            await process_msg_reaction_add(message, "✨")
            await asyncio.sleep(1)
            await asyncio.sleep(3)
            await process_msg_delete(message, 0)

            if path in ["path10", "path3", "path25"]:
                await self.expecto_update_path(user, cycle, path_new="path11")

            await self.expecto_transaction_ollivanders(guild, user, ollivanders_channel)

        else:
            await reaction_closed(message)

    async def expecto_transaction_ollivanders(self, guild, user, channel):

        cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(user.id)

        if actions >= 3:
            return

        elif actions < 3:
            role_star = discord.utils.get(guild.roles, name="🌟")
            responses = self.get_responses_quest1("ollivanders")
            msg1 = responses["intro"].format(user.mention)
            await secret_response(channel.name, msg1)
            await asyncio.sleep(3)

            def check(guess):
                if guess.author != user:
                    return
                elif guess.content.lower() in ["yes", "yeah", "yea", "maybe", "probably", "perhaps"]:
                    return guess.author == user and channel == guess.channel
                else:
                    raise KeyError

            try:
                await self.client.wait_for("message", timeout=30, check=check)

            except asyncio.TimeoutError:
                msg = responses["timeout_intro"].format(user.mention)
                await penalize_quest1(user, cycle, points=10)
                await action_update_quest1(user, cycle, actions=3)
                await secret_response(channel.name, msg)

            except KeyError:
                msg = responses["invalid"]
                await penalize_quest1(user, cycle, points=10)
                await action_update_quest1(user, cycle, actions=3)
                await secret_response(channel.name, msg)

            else:
                if user not in role_star.members and path in [
                    "path11", "path3", "path10", "path0", "path25", "path17"
                ]:
                    msg1 = responses["valid"][0].format(user.mention)
                    msg2 = responses["valid"][1].format(user.mention)
                    topic = responses["valid"][2]
                    await action_update_quest1(user, cycle, actions=3)
                    await secret_response(channel.name, msg1)
                    await asyncio.sleep(6)
                    await secret_response(channel.name, msg2)
                    await process_channel_edit(channel, None, topic)
                    await asyncio.sleep(5)
                    await self.expecto_wand_personalise(user, channel, cycle, role_star, responses)

                else:
                    msg = responses["valid_no_owl"][0].format(user.mention)
                    topic = responses["valid_no_owl"][1]
                    await penalize_quest1(user, cycle, points=25)
                    await action_update_quest1(user, cycle, actions=3)
                    await secret_response(channel.name, msg)
                    await process_channel_edit(channel, None, topic)

    async def expecto_wand_personalise(self, user, channel, cycle, role_star, responses):

        owl_type_ = ""

        for profile in quests.aggregate([{
            "$match": {"user_id": str(user.id)}}, {
            "$project": {
                "_id": 0,
                "quest1": {
                    "$slice": ["$quest1", -1]
                }
            }
        }]):
            owl_type_ = profile["quest1"][0]["owl"]
            break

        trait = owls.find_one({"type": owl_type_}, {"_id": 0, "trait": 1})["trait"]
        msg1 = responses["owl_analysis"][trait][0]
        topic = responses["owl_analysis"][trait][1]

        await secret_response(channel.name, msg1)
        await process_channel_edit(channel, None, topic)
        await asyncio.sleep(9)

        wand_length = await self.expecto_get_wand_length(user, channel, responses)

        if wand_length != "Wrong":
            wand_flexibility = await self.expecto_get_wand_flexibility(user, channel, responses)

            if wand_flexibility != "Wrong":
                wand_length_category = self.get_length_category(wand_length)
                wand_flexibility_category = self.get_flexibility_category(wand_flexibility)

                wood_selection = []
                query = patronus.find({
                    "flexibility": wand_flexibility_category,
                    "length": wand_length_category,
                    "trait": trait.lower()}, {
                    "_id": 0, "wood": 1
                })

                for wand in query:
                    if wand["wood"] not in wood_selection:
                        wood_selection.append(wand["wood"])

                wand_wood = await self.expecto_get_wand_wood(user, channel, wood_selection, responses)

                if wand_wood != "Wrong":
                    wand_core = await self.expecto_get_wand_core(user, channel, responses)
                    wand_creation = {
                        "flexibility_category": wand_flexibility_category,
                        "flexibility": wand_flexibility,
                        "length_category": wand_length_category,
                        "length": wand_length,
                        "core": wand_core,
                        "trait": trait,
                        "wood": wand_wood
                    }
                    __patronus = patronus.find_one({
                        "flexibility": wand_flexibility_category,
                        "length": wand_length_category,
                        "trait": trait,
                        "core": wand_core,
                        "wood": wand_wood}, {
                        "_id": 0
                    })

                    if __patronus is None:
                        msg = responses["no_patronus"].format(user.mention)
                        await secret_response(channel.name, msg)

                    elif __patronus is not None:
                        description = f"Wood: `{wand_wood.title()}`\n" \
                                      f"Length: `{wand_length} in`\n" \
                                      f"Flexibility: `{wand_flexibility.title()}`\n" \
                                      f"Core: `{wand_core.title()}`"

                        embed = discord.Embed(color=user.colour, description=description)
                        embed.set_author(name="Wand Properties", icon_url=user.avatar_url)
                        embed.set_footer(text="Confirm purchase? Y/N")

                        msg_confirm = await process_msg_submit(channel, None, embed)

                        def check(_answer):
                            return user.id == _answer.author.id \
                                   and _answer.content.lower() in ["y", "n"] \
                                   and msg_confirm.channel.id == _answer.channel.id

                        while True:
                            try:
                                answer = await self.client.wait_for("message", timeout=120, check=check)

                            except asyncio.TimeoutError:
                                msg = responses["timeout_response"].format(user.mention)
                                await penalize_quest1(user, cycle, points=20)
                                await secret_response(channel.name, msg)
                                break

                            else:
                                if answer.content.lower() == "y":
                                    msg1 = f"{user.mention} has acquired 🌟 role"
                                    msg2 = responses["success_purchase"].format(user.mention)
                                    quests.update_one({
                                        "user_id": str(user.id),
                                        "quest1.cycle": cycle}, {
                                        "$set": {
                                            "quest1.$.wand": wand_creation,
                                            "quest1.$.patronus": __patronus
                                        }
                                    })

                                    await process_role_add(user, role_star)
                                    await process_msg_submit(channel, msg1, None)
                                    await secret_response(channel.name, msg2)
                                    break

                                elif answer.content.lower() == "n":
                                    msg = responses["timeout_response"].format(user.mention)
                                    cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(user.id)

                                    if path == "path0":
                                        await self.expecto_update_path(user, cycle, path_new="path17")

                                    await penalize_quest1(user, cycle, points=20)
                                    await secret_response(channel.name, msg)
                                    break

    async def expecto_get_wand_core(self, user, channel, responses):

        wand_core = ""
        formatted_cores = "`, `".join(self.cores)
        msg = responses["core_selection"]["1"].format(user.mention, formatted_cores)
        await asyncio.sleep(1)
        await secret_response(channel.name, msg)
        cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(user.id)

        def check(guess):
            if guess.channel != channel or guess.author != user:
                return False
            elif guess.content.lower() in self.cores and guess.author == user and channel == guess.channel:
                return True
            elif guess.content.lower() not in self.cores and guess.author == user and channel == guess.channel:
                raise KeyError

        i = 0
        while i < 2:
            try:
                answer = await self.client.wait_for("message", timeout=60, check=check)

            except asyncio.TimeoutError:
                msg = responses["core_selection"]["timeout"].format(user.mention)
                wand_core = "Wrong"

                if path == "path0":
                    await self.expecto_update_path(user, cycle, path_new="path17")

                await action_update_quest1(user, cycle, actions=3)
                await penalize_quest1(user, cycle, points=10)
                await secret_response(channel.name, msg)
                break

            except KeyError:

                if path == "path0":
                    await self.expecto_update_path(user, cycle, path_new="path17")

                if i == 0:
                    msg = responses["core_selection"]["invalid1"][0].format(user.mention)
                    topic = responses["core_selection"]["invalid1"][1]
                    await process_channel_edit(channel, None, topic)
                    await penalize_quest1(user, cycle, points=5)

                elif i == 1:
                    wand_core = "Wrong"
                    msg = responses["core_selection"]["invalid2"][0].format(user.mention)
                    topic = responses["core_selection"]["invalid2"][1]
                    await action_update_quest1(user, cycle, actions=3)
                    await penalize_quest1(user, cycle, points=10)
                    await process_channel_edit(channel, None, topic)

                await secret_response(channel.name, msg)
                i += 1

            else:
                wand_core = answer.content
                msg = responses["core_selection"]["chose"][0].format(
                    wand_core.capitalize(),
                    responses["core_description"][f'{wand_core.lower()}']
                )
                topic = responses["core_selection"]["chose"][1]
                await process_channel_edit(channel, None, topic)
                await secret_response(channel.name, msg)
                break

        return wand_core.lower()

    async def expecto_get_wand_wood(self, user, channel, wood_selection, responses):

        wand_wood = ""
        formatted_woods = "`, `".join(wood_selection)
        msg = responses["wood_selection"]["1"].format(user.mention, formatted_woods)
        await asyncio.sleep(1)
        await secret_response(channel.name, msg)
        cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(user.id)

        def check(guess):
            if guess.channel != channel or guess.author != user:
                return False
            elif guess.content.lower() in wood_selection and guess.author == user and channel == guess.channel:
                return True
            elif guess.content.lower() not in wood_selection and guess.author == user and channel == guess.channel:
                raise KeyError

        i = 0
        while i < 2:
            try:
                answer = await self.client.wait_for("message", timeout=60, check=check)

            except asyncio.TimeoutError:
                wand_wood = "Wrong"
                msg = responses["wood_selection"]["timeout"].format(user.mention)

                if path == "path0":
                    await self.expecto_update_path(user, cycle, path_new="path17")

                await penalize_quest1(user, cycle, points=15)
                await action_update_quest1(user, cycle, actions=3)
                await secret_response(channel.name, msg)
                break

            except KeyError:

                if path == "path0":
                    await self.expecto_update_path(user, cycle, path_new="path17")

                if i == 0:
                    msg = responses["wood_selection"]["invalid1"][0].format(user.mention)
                    topic = responses["wood_selection"]["invalid1"][1]
                    await process_channel_edit(channel, None, topic)
                    await penalize_quest1(user, cycle, points=10)

                elif i == 1:
                    wand_wood = "Wrong"
                    msg = responses["wood_selection"]["invalid2"][0].format(user.mention)
                    topic = responses["wood_selection"]["invalid2"][1]
                    await action_update_quest1(user, cycle, actions=3)
                    await penalize_quest1(user, cycle, points=10)
                    await process_channel_edit(channel, None, topic)

                await secret_response(channel.name, msg)
                i += 1

            else:
                wand_wood = answer.content
                msg = responses["wood_selection"]["chose"][0].format(
                    wand_wood.capitalize(),
                    responses["wood_description"][f'{wand_wood.lower()}']
                )
                topic = responses["wood_selection"]["chose"][1]
                await process_channel_edit(channel, None, topic)
                await secret_response(channel.name, msg)
                break

        return wand_wood.lower()

    async def expecto_get_wand_length(self, user, channel, responses):

        wand_length = ""
        msg = responses["length_selection"]["1"].format(user.mention)
        await asyncio.sleep(1)
        await secret_response(channel.name, msg)
        cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(user.id)

        def check(guess):
            if guess.channel != channel or guess.author != user:
                return False
            elif guess.content in self.wand_lengths and guess.author == user and channel == guess.channel:
                return True
            elif guess.content not in self.wand_lengths and guess.author == user and channel == guess.channel:
                raise KeyError

        i = 0
        while i < 2:

            try:
                answer = await self.client.wait_for("message", timeout=120, check=check)

            except asyncio.TimeoutError:
                wand_length = "Wrong"
                msg = responses["length_selection"]["timeout"].format(user.mention)

                if path == "path0":
                    await self.expecto_update_path(user, cycle, path_new="path17")

                await penalize_quest1(user, cycle, points=15)
                await action_update_quest1(user, cycle, actions=3)
                await secret_response(channel.name, msg)
                break

            except KeyError:

                if path == "path0":
                    await self.expecto_update_path(user, cycle, path_new="path17")

                if i == 0:
                    msg = responses["length_selection"]["invalid1"][0].format(user.mention)
                    topic = responses["length_selection"]["invalid1"][1]
                    await process_channel_edit(channel, None, topic)
                    await penalize_quest1(user, cycle, points=10)

                elif i == 1:
                    wand_length = "Wrong"
                    msg = responses["length_selection"]["invalid2"][0].format(user.mention)
                    topic = responses["length_selection"]["invalid2"][1]
                    await action_update_quest1(user, cycle, actions=3)
                    await penalize_quest1(user, cycle, points=15)
                    await process_channel_edit(channel, None, topic)

                await secret_response(channel.name, msg)
                i += 1

            else:
                wand_length = answer.content
                msg = responses["length_selection"]["chose"][0].format(wand_length)
                topic = responses["length_selection"]["chose"][1]
                await process_channel_edit(channel, None, topic)
                await secret_response(channel.name, msg)
                break

        return wand_length

    async def expecto_get_wand_flexibility(self, user, channel, responses):

        wand_flexibility = ""
        formatted_flexibility = "`, `".join(self.flexibility_types)
        msg = responses["flexibility_selection"]["1"].format(user.mention, formatted_flexibility)
        await asyncio.sleep(2)
        await secret_response(channel.name, msg)
        cycle, path, timestamp, user_hints, actions, purchase = get_data_quest1(user.id)

        def check(g):
            if g.channel != channel or g.author != user:
                return False
            elif g.content.lower() in self.flexibility_types and g.author == user and channel == g.channel:
                return True
            elif g.content.lower() not in self.flexibility_types and g.author == user and channel == g.channel:
                raise KeyError

        i = 0
        while i < 2:
            try:
                answer = await self.client.wait_for("message", timeout=60, check=check)

            except asyncio.TimeoutError:
                wand_flexibility = "Wrong"
                msg = responses["flexibility_selection"]["timeout"].format(user.mention)

                if path == "path0":
                    await self.expecto_update_path(user, cycle, path_new="path17")

                await penalize_quest1(user, cycle, points=15)
                await action_update_quest1(user, cycle, actions=3)
                await secret_response(channel.name, msg)
                break

            except KeyError:

                if path == "path0":
                    await self.expecto_update_path(user, cycle, path_new="path17")

                if i == 0:
                    msg = responses["flexibility_selection"]["invalid1"][0].format(user.mention)
                    topic = responses["flexibility_selection"]["invalid1"][1]
                    await process_channel_edit(channel, None, topic)
                    await penalize_quest1(user, cycle, points=10)

                elif i == 1:
                    wand_flexibility = "Wrong"
                    msg = responses["flexibility_selection"]["invalid2"][0].format(user.mention)
                    topic = responses["flexibility_selection"]["invalid2"][1]
                    await action_update_quest1(user, cycle, actions=3)
                    await penalize_quest1(user, cycle, points=15)
                    await process_channel_edit(channel, None, topic)

                await secret_response(channel.name, msg)
                i += 1

            else:
                wand_flexibility = answer.content
                msg = responses["flexibility_selection"]["chose"][0].format(wand_flexibility.title())
                topic = responses["flexibility_selection"]["chose"][1]
                await process_channel_edit(channel, None, topic)
                await secret_response(channel.name, msg)
                break

        return wand_flexibility.lower()


def setup(client):
    client.add_cog(Quest(client))
    client.add_cog(Expecto(client))
