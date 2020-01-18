"""
Encounter Module
Miketsu, 2020
"""

from datetime import timedelta
from itertools import cycle
from math import floor

from PIL import Image
from discord.ext import commands

from cogs.ext.initialize import *


class Encounter(commands.Cog):

    def __init__(self, client):

        self.client = client
        self.prefix = self.client.command_prefix

        self.demons, self.quizzes, self.actual_rewards = [], [], []
        self.boss_spawn = False

        self.attack_verb = cycle(dictionaries["attack_verb"])

        self.assemble_captions = cycle(listings_1["assemble_captions"])
        self.boss_comment = listings_1["boss_comment"]
        self.rewards_nether = listings_1["rewards_nether"]

        self.enc_nether_info_generate()

        for document in bosses.find({}, {"_id": 0, "boss": 1}):
            self.demons.append(document["boss"])

        for quiz in shikigamis.find({"demon_quiz": {"$ne": None}}, {"_id": 0, "demon_quiz": 1, "name": 1}):
            self.quizzes.append(quiz)

        random.shuffle(self.quizzes)
        self.quizzes_cycle = cycle(self.quizzes)

    def enc_nether_info_generate(self):

        for index, reward in enumerate(range(1, 9)):
            lvl = index + 1
            jades, coins = self.rewards_nether[0] * lvl, self.rewards_nether[1] * lvl
            experience, medals = self.rewards_nether[2] * lvl, self.rewards_nether[3] * lvl
            shards_sp = int(self.rewards_nether[4] * lvl) + floor(lvl / 8)
            shards_ssr = int(self.rewards_nether[5] * lvl) + floor(lvl / 8)
            shards_ssn = int(self.rewards_nether[6] * lvl) + floor(lvl / 8)
            self.actual_rewards.append([jades, coins, experience, medals, shards_sp, shards_ssr, shards_ssn])

    def enc_roll_boss_stats_get(self, boss):

        query = bosses.find_one({"boss": boss}, {"_id": 0, })

        hp_total = query["total_hp"]
        hp_current = query["current_hp"]
        hp_percent = round(((hp_current / hp_total) * 100), 2)

        discoverer = query["discoverer"]
        lvl = query["level"]
        url = query["boss_url"]
        coins = query["rewards"]["coins"]
        experience = query["rewards"]["experience"]
        jades = query["rewards"]["jades"]
        medals = query["rewards"]["medals"]

        return hp_total, hp_current, hp_percent, lvl, url, coins, experience, jades, medals, discoverer

    def enc_roll_boss_status_set(self, x):
        self.boss_spawn = x

    def enc_roll_nether_generate_cards(self, user, waves):

        card_rewards = random.choice(realm_cards)
        if waves >= 60:
            grade = random.choice([5, 5, 6])
        elif waves >= 50:
            grade = random.choice([4, 4, 5])
        elif waves >= 40:
            grade = random.choice([3, 3, 4])
        elif waves >= 30:
            grade = random.choice([2, 2, 3])
        elif waves >= 20:
            grade = random.choice([1, 1, 2])
        else:
            grade = random.choice([1, 1, 2])

        if users.find_one({
            "user_id": str(user.id), "cards": {"$elemMatch": {"name": card_rewards, "grade": grade}}
        }) is None:
            users.update_one({"user_id": str(user.id)}, {
                "$push": {
                    "cards": {
                        "name": card_rewards,
                        "grade": int(grade),
                        "count": 1
                    }
                }
            })
        else:
            users.update_one({
                "user_id": str(user.id),
                "cards": {"$elemMatch": {"name": card_rewards, "grade": grade}}
            }, {
                "$inc": {
                    "cards.$.count": 1
                }
            })

        return card_rewards, grade

    def enc_roll_nether_get_chance(self, user, name, evo_adj_max, min_chance, adj, stage, evo_adj):

        grade_total, soul_set_chance, listings_souls = 0, 0, []
        query = users.find_one({"user_id": str(user.id)}, {"_id": 0, "level": 1})
        user_level = query["level"]
        shikigami_level, shikigami_evo, shikigami_souls = get_shikigami_stats_1(user.id, name)

        if shikigami_evo is True:
            evo_adj = evo_adj_max

        for result in users.aggregate([{
            '$match': {'user_id': str(user.id)}}, {
            '$project': {'souls': 1}}, {
            '$project': {'souls': {'$objectToArray': '$souls'}}}, {
            '$unwind': {'path': '$souls'}}, {
            '$unwind': {'path': '$souls.v'}}, {
            '$match': {'souls.v.equipped': name}
        }]):
            grade_total += result["souls"]["v"]["slot"]
            listings_souls.append(result["souls"]["k"])

        soul_count = dict(Counter(listings_souls))

        for a in soul_count:
            if soul_count[a] == 1:
                continue
            elif soul_count[a] == 2:
                soul_set_chance += 1.85
            elif soul_count[a] == 4:
                soul_set_chance += 6.475

        total_soul = 0.696138186504516 * exp(grade_total * 0.0783) + soul_set_chance
        total_soul_adj = random.uniform(total_soul * 0.98, total_soul) + random.uniform(adj[0], adj[1])

        total_chance = user_level + shikigami_level - stage * evo_adj + total_soul_adj

        if total_chance <= min_chance:
            total_chance = min_chance

        return total_chance

    async def enc_nether_announce(self):

        users.update_many({}, {"$set": {"nether_pass": True}})

        content = f"<@&{id_boss_busters}>"
        embed = discord.Embed(
            color=colour, timestamp=get_timestamp(),
            title="Netherworld gates update",
            description=f"The gates of Netherworld have reset\nUse `{self.prefix}encounter` to explore them by chance"
        )
        spell_spam_channel = self.client.get_channel(int(id_spell_spam))
        await process_msg_submit(spell_spam_channel, content, embed)

    async def enc_perform_reset_boss(self):

        bosses.update_many({}, {
            "$set": {
                "discoverer": 0,
                "level": 0,
                "damage_cap": 0,
                "total_hp": 0,
                "current_hp": 0,
                "challengers": [],
                "rewards": {}
            }
        })

    async def enc_perform_reset_boss_check(self):

        survivability = bosses.count_documents({"current_hp": {"$gt": 0}})
        discoverability = bosses.count_documents({"discoverer": {"$eq": 0}})

        if survivability == 0 and discoverability == 0:
            await self.enc_perform_reset_boss()

    @commands.command(aliases=["netherworld", "nw"])
    @commands.guild_only()
    async def enc_nether_info(self, ctx):

        embed = discord.Embed(
            color=colour, title=f"netherworld, nw",
            description=f"fights and clears unwanted forces and earn rich rewards"
        )
        embed.add_field(
            name="Mechanics",
            value="`1.` Spawns `20%` chance during opening times\n"
                  "`2.` Upon discovering, enter the name of your shikigami to fight the forces\n"
                  "`3.` Fight and clear all the waves up to 70 or until it timeouts\n"
                  "`4.` Losing strikes out the shikigami, enter a new one then repeat\n"
                  "`5.` Each encounter has 4 attempts to max out your rewards"
        )
        embed.add_field(
            name="Format", inline=False,
            value=f"*`{self.prefix}encounter`*"
        )
        await process_msg_submit(ctx.channel, None, embed)

    async def enc_roll_nether(self, user, channel, msg):

        user_shikigamis, shikis_t, shikis_d, placed_shikigamis, clear_chances = [], [], [], [], []
        clear_chances, waves_c, total_attempts, max_waves = [], 0, 4, 70

        for result in users.aggregate([{
            '$match': {'user_id': str(user.id)}}, {
            '$unwind': {'path': '$shikigami'}}, {
            '$match': {'shikigami.owned': {'$gt': 0}}}, {
            '$project': {'shikigami': 1}
        }
        ]):
            user_shikigamis.append(f"{result['shikigami']['name']}")

        for result in users.aggregate([{
            '$match': {'user_id': str(user.id)}}, {
            '$unwind': {'path': '$shikigami'}}, {
            '$match': {'shikigami.owned': {'$gt': 0}}}, {
            '$sort': {'shikigami.grade': -1, 'shikigami.level': -1}}, {
            '$match': {'shikigami.level': {'$gte': 2}}}, {
            '$project': {'shikigami': 1}}
        ]):
            shikis_t.append([result['shikigami']['name'], result['shikigami']['level']])

        def embed_new_create(t, d, s, b, c, u, r):

            shikigamis_formatted = []
            embed_new = discord.Embed(
                color=user.colour, title=f"Encounter Netherworld", timestamp=get_timestamp(),
                description=f"react below and place your shikigamis to start clearing waves",
            )

            for e in t:
                if e[0] in d:
                    shikigamis_formatted.append(f"~~{e[0].title()}/{e[1]}~~")
                else:
                    shikigamis_formatted.append(f"{e[0].title()}/{e[1]}")

            embed_new.add_field(
                name=f"Top {len(shikis_t)} {pluralize('shikigami', len(shikis_t))}",
                value=f"*{', '.join(shikigamis_formatted[:10])}*", inline=False
            )
            embed_new.set_footer(icon_url=user.avatar_url, text=f"{user.display_name}")

            if s in ["accepted", "end"]:
                caption_list = []
                if b is not None:
                    for index2, x in enumerate(placed_shikigamis):
                        caption_list.append(
                            f"`Attempt#{index2 + 1}` :: {x[0].title()} | ~{round(x[1], 2)}% | "
                            f"{x[2]} {pluralize('clear', x[2])}\n"
                        )

                caption = ''.join(caption_list)
                if len(caption_list) == 0:
                    caption = "Enter a shikigami"

                embed_new.add_field(name=f"Cleared waves: {c}/{max_waves}", value=f"{caption}", inline=False)

                if s == "end":
                    embed_new.set_image(url=u)
                    if len(r) > 0:
                        embed_new.add_field(
                            name="Rewards", inline=False,
                            value=f"{r[0]:,d}{e_j} | {r[1]:,d}{e_c} | {r[2]:,d} {e_x} | {r[3]:,d}{e_m}",
                        )
                        card_reward, card_grade = self.enc_roll_nether_generate_cards(user, c)
                        embed_new.add_field(
                            name="Bonus Reward", inline=False,
                            value=f"Grade {card_grade} {card_reward.title()}"
                        )
            return embed_new

        await process_msg_edit(msg, None, embed_new_create(shikis_t, shikis_d, None, None, waves_c, "", []))

        emojis_add = ["🌌"]
        for emoji in emojis_add:
            await process_msg_reaction_add(msg, emoji)

        def check(r, u):
            return user.id == u.id and str(r.emoji) in emojis_add and r.message.id == msg.id

        try:
            await self.client.wait_for("reaction_add", timeout=60, check=check)
        except asyncio.TimeoutError:
            await process_msg_reaction_clear(msg)
            return
        else:
            await process_msg_reaction_clear(msg)
            embed = embed_new_create(shikis_t, shikis_d, "accepted", None, waves_c, "", [])
            await process_msg_edit(msg, None, embed)

        def check_if_valid_shikigami(m):
            if m.content.lower() in shikis_d and m.author.id == user.id:
                raise KeyError
            elif m.content.lower() not in user_shikigamis and m.author.id == user.id:
                raise KeyError

            return m.author.id == user.id and \
                   m.content.lower() in user_shikigamis and \
                   m.channel.id == channel.id and \
                   m.content.lower() not in shikis_d

        while True:
            try:
                if total_attempts == 0:
                    await self.enc_roll_nether_finish(
                        user, waves_c, embed_new_create, msg, shikis_t, shikis_d
                    )
                    break

                answer = await self.client.wait_for("message", timeout=60, check=check_if_valid_shikigami)
            except asyncio.TimeoutError:
                await process_msg_reaction_clear(msg)
                return
            except KeyError:
                embed1 = discord.Embed(
                    colour=colour, title="Invalid selection",
                    description=f"this shikigami is not in your possession, already dead, or does not exist"
                )
                msg2 = await process_msg_submit(channel, None, embed1)
                await process_msg_delete(msg2, 4)
            else:
                shiki_bet = answer.content.lower()
                total_chance = self.enc_roll_nether_get_chance(user, shiki_bet, 0.2, 40, [0, 0], 70, 1)

                shiki_clears = 0
                for i in range(waves_c + 1, max_waves + 1):
                    total_chance_2 = total_chance - i * 0.09
                    adjusted_chance = random.uniform(total_chance_2 * 0.98, total_chance_2)

                    if random.uniform(0, 100) < adjusted_chance:
                        waves_c += 1
                        shiki_clears += 1

                        if waves_c == 70:
                            total_attempts = 0
                            spell_spam_channel = self.client.get_channel(int(id_spell_spam))
                            await frame_acquisition(user, "Dignified Dance", 3500, spell_spam_channel)
                            break
                    else:
                        shikis_d.append(shiki_bet)
                        clear_chances.append(total_chance)
                        total_attempts -= 1
                        break

                placed_shikigamis.append([shiki_bet, total_chance, shiki_clears])
                embed = embed_new_create(shikis_t, shikis_d, "end", shiki_bet, waves_c, "", [])
                await process_msg_edit(msg, None, embed)

    async def enc_roll_nether_finish(self, user, cleared_waves, embed_create, msg, shikis_t, shikis_d):

        ranges = [[0, 9], [10, 19], [20, 29], [30, 39], [40, 49], [50, 59], [60, 69], [70, 79]]
        for g, covered in enumerate(ranges):
            if cleared_waves <= covered[1]:
                rewards_select = self.actual_rewards[g]

                jades = random.uniform(rewards_select[0] * 0.95, rewards_select[0] * 1.05)
                coins = random.uniform(rewards_select[1] * 0.95, rewards_select[1] * 1.05)
                experience = random.uniform(rewards_select[2] * 0.95, rewards_select[2] * 1.05)
                medals = random.uniform(rewards_select[3] * 0.95, rewards_select[3] * 1.05)
                shards_sp = rewards_select[4]
                shards_ssr = rewards_select[5]
                shards_ssn = rewards_select[6]

                users.update_one({
                    "user_id": str(user.id)
                }, {
                    "$inc": {
                        "jades": int(jades),
                        "coins": int(coins),
                        "medals": int(medals)
                    },
                    "$set": {
                        "nether_pass": False
                    }
                })
                await perform_add_log("jades", int(jades), user.id)
                await perform_add_log("coins", int(coins), user.id)
                await perform_add_log("medals", int(medals), user.id)

                users.update_one({
                    "user_id": str(user.id),
                    "level": {
                        "$lt": 60
                    }
                }, {
                    "$inc": {
                        "experience": int(experience)
                    }
                })

                shikigami_pool = {
                    shiki_iterate: 0 for shiki_iterate in pool_ssr + pool_sp + pool_ssn
                }

                i = 0
                while i < shards_sp:
                    shikigami_shard = random.choice(pool_sp)
                    shikigami_pool[shikigami_shard] += 1
                    i += 1

                i = 0
                while i < shards_ssr:
                    shikigami_shard = random.choice(pool_ssr)
                    shikigami_pool[shikigami_shard] += 1
                    i += 1

                i = 0
                while i < shards_ssn:
                    shikigami_shard = random.choice(pool_ssn)
                    shikigami_pool[shikigami_shard] += 1
                    i += 1

                shards_reward = list(shikigami_pool.items())

                await self.enc_roll_nether_shards_issue(user.id, shards_reward)
                link = await self.enc_roll_nether_shards_generate(user.id, shards_reward)
                rewards = [int(jades), int(coins), int(experience), int(medals)]

                embed = embed_create(shikis_t, shikis_d, "end", True, cleared_waves, link, rewards)
                await process_msg_edit(msg, None, embed)
                break
            continue

    async def enc_roll_nether_shards_generate(self, user_id, shards_reward):

        font, images = font_create(30), []
        x, y, cols = 1, 60, 8
        rows = 90 * cols

        for entry in shards_reward:
            if entry[1] != 0:
                address = f"data/shikigamis/{entry[0]}_pre.jpg"
                shikigami_thumbnail = Image.open(address)
                shikigami_image_final = shikigami_shards_count_generate(shikigami_thumbnail, entry[1], font, x, y)
                images.append(shikigami_image_final)
            else:
                continue

        if len(images) == 0:
            return ""

        else:
            width, height = get_image_variables(images, cols, rows)
            new_im = Image.new("RGBA", (width, height))

            for index, item in enumerate(images):
                new_im.paste(images[index], (get_shiki_tile_coordinates(index + 1, cols, rows)))

            address_temp = f"temp/{user_id}.png"
            new_im.save(address_temp)
            image_file = discord.File(address_temp, filename=f"{user_id}.png")
            hosting_channel = self.client.get_channel(int(id_hosting))
            msg = await process_msg_submit_file(hosting_channel, image_file)
            attachment_link = msg.attachments[0].url

            return attachment_link

    async def enc_roll_nether_shards_issue(self, user_id, shards_reward):

        trimmed = []
        for entry in shards_reward:
            if entry[1] != 0:
                trimmed.append(entry)
            else:
                continue

        for shikigami_shard in trimmed:

            query = users.find_one({
                "user_id": str(user_id),
                "shikigami.name": shikigami_shard[0]}, {
                "_id": 0, "shikigami.$": 1
            })

            if query is None:
                shikigami_push_user(user_id, shikigami_shard[0], False, 0)

            users.update_one({"user_id": str(user_id), "shikigami.name": shikigami_shard[0]}, {
                "$inc": {
                    "shikigami.$.shards": 1
                }
            })

    @commands.command(aliases=["encounter", "enc"])
    @commands.cooldown(1, 180, commands.BucketType.user)
    @commands.guild_only()
    async def enc_roll(self, ctx):

        user = ctx.author

        if not check_if_user_has_encounter_tickets(ctx):
            embed = discord.Embed(
                colour=user.colour, title="Insufficient tickets",
                description=f"Purchase at the *`{self.prefix}shop`* to obtain more"
            )
            await process_msg_submit(ctx.channel, None, embed)

        elif check_if_user_has_encounter_tickets(ctx):

            users.update_one({"user_id": str(user.id)}, {"$inc": {"encounter_ticket": -1}})
            await perform_add_log("encounter_ticket", -1, user.id)

            async with ctx.channel.typing():
                msg = await process_msg_submit(ctx.channel, "🔍 Searching the depths of Netherworld...", None)
                await asyncio.sleep(1)

                survivability = bosses.count({"current_hp": {"$gt": 0}})
                discoverability = bosses.count({"discoverer": {"$eq": 0}})

                if (survivability > 0 or discoverability > 0) and self.boss_spawn is False:

                    if random.uniform(0, 100) <= 20:
                        self.enc_roll_boss_status_set(True)
                        await self.enc_roll_boss(user, ctx, msg)

                    else:
                        if 0 <= random.uniform(0, 100) <= 20 and check_if_user_has_nether_pass(ctx):
                            await self.enc_roll_nether(user, ctx.channel, msg)
                        else:
                            if random.uniform(0, 100) < 30:
                                await self.enc_roll_quiz(user, ctx, msg)
                            else:
                                await self.enc_roll_treasure(user, ctx, msg)
                else:

                    if 0 <= random.uniform(0, 100) <= 20 and check_if_user_has_nether_pass(ctx):
                        await self.enc_roll_nether(user, ctx.channel, msg)

                    else:
                        if random.uniform(0, 100) < 30:
                            await self.enc_roll_quiz(user, ctx, msg)
                        else:
                            await self.enc_roll_treasure(user, ctx, msg)

            self.client.get_command("enc_roll").reset_cooldown(ctx)

    async def enc_roll_quiz(self, user, ctx, msg):

        quiz_select = next(self.quizzes_cycle)
        answer, question = quiz_select['name'], quiz_select['demon_quiz']
        timeout, guesses = 20, 3

        embed = discord.Embed(title=f"Demon Quiz", color=user.colour, timestamp=get_timestamp())
        embed.description = f"Time Limit: {timeout} sec"
        embed.add_field(name="Who is this shikigami?", value=f"{question}")
        embed.set_footer(text=f"{guesses} {pluralize('guess', guesses)}", icon_url=user.avatar_url)
        await process_msg_edit(msg, None, embed)

        def check(m):
            if m.content.lower() == answer and m.channel == ctx.channel and m.author.id == user.id:
                return True
            elif m.content.lower() != answer and m.channel == ctx.channel and m.author.id == user.id:
                raise KeyError

        while guesses != 0:
            try:
                await self.client.wait_for("message", timeout=timeout, check=check)

            except asyncio.TimeoutError:
                embed = discord.Embed(
                    title="Demon Quiz", color=user.colour, timestamp=get_timestamp(),
                    description=f"You have failed the quiz",
                )
                embed.add_field(name="Correct Answer", value=f"{answer.title()}")
                embed.set_footer(text="Time is up!", icon_url=user.avatar_url)
                await process_msg_edit(msg, None, embed)
                break

            except KeyError:

                if guesses == 3:
                    guesses -= 1
                    embed.set_footer(text=f"{guesses} {pluralize('guess', guesses)}", icon_url=user.avatar_url)
                    await process_msg_edit(msg, None, embed)

                elif guesses == 2:
                    guesses -= 1
                    embed.set_footer(text=f"{guesses} {pluralize('guess', guesses)}", icon_url=user.avatar_url)
                    await process_msg_edit(msg, None, embed)

                elif guesses == 1:
                    guesses -= 1
                    embed.set_footer(text=f"{guesses} {pluralize('guess', guesses)}", icon_url=user.avatar_url)
                    embed.remove_field(0)
                    embed.add_field(name="Correct Answer", value=f"{answer.title()}")
                    await process_msg_edit(msg, None, embed)
                    break
            else:
                users.update_one({"user_id": str(user.id)}, {"$inc": {"amulets": 5}})
                await perform_add_log("amulets", 5, user.id)
                embed = discord.Embed(
                    title="Demon Quiz", color=user.colour,
                    description=f"You have earned 5{e_a}",
                    timestamp=get_timestamp()
                )
                embed.set_footer(text="Correct!", icon_url=user.avatar_url)
                await process_msg_edit(msg, None, embed)
                break

    async def enc_roll_treasure(self, user, ctx, msg):

        rewards = config.find_one({"dict": 1}, {"_id": 0, "rewards": 1})["rewards"]

        roll_key = str(random.randint(1, len(rewards)))
        offer_i = tuple(dict.keys(rewards[roll_key]["offer"]))[0]
        offer_a = tuple(dict.values(rewards[roll_key]["offer"]))[0]
        cost_i = tuple(dict.keys(rewards[roll_key]["cost"]))[0]
        cost_a = tuple(dict.values(rewards[roll_key]["cost"]))[0]

        embed = discord.Embed(
            color=user.colour, timestamp=get_timestamp(),
            title="Encounter treasure",
            description=f"A treasure chest containing {offer_a:,d}{get_emoji(offer_i)}\n"
                        f"It opens using {cost_a:,d}{get_emoji(cost_i)}",
        )
        embed.set_footer(text=f"Found by {user.display_name}", icon_url=user.avatar_url)
        await process_msg_edit(msg, None, embed)

        emojis_add = ["✅"]
        for emoji in emojis_add:
            await process_msg_reaction_add(msg, emoji)

        def check(r, u):
            return u == ctx.author and str(r.emoji) in emojis_add and msg.id == r.message.id

        try:
            await self.client.wait_for("reaction_add", timeout=6.0, check=check)

        except asyncio.TimeoutError:
            embed = discord.Embed(
                color=user.colour, timestamp=get_timestamp(),
                title="Encounter Treasure", description=f"The chest you found turned into ashes 🔥",
            )
            embed.set_footer(text=f"Found by {user.display_name}", icon_url=user.avatar_url)
            await process_msg_edit(msg, None, embed)
            await process_msg_reaction_clear(msg)

        else:
            cost_item_current = users.find_one({"user_id": str(user.id)}, {"_id": 0, cost_i: 1})[cost_i]

            if cost_item_current >= cost_a:

                users.update_one({"user_id": str(user.id)}, {"$inc": {offer_i: offer_a, cost_i: -cost_a}})
                await perform_add_log(offer_i, offer_a, user.id)
                await perform_add_log(cost_i, -cost_a, user.id)

                query = users.find_one({"user_id": str(user.id)}, {"_id": 0, cost_i: 1, offer_i: 1})
                cost_i_have, offer_i_have = query[cost_i], query[offer_i]

                embed = discord.Embed(
                    color=user.colour, timestamp=get_timestamp(),
                    title="Encounter treasure",
                    description=f"You acquired `{offer_a:,d}`{get_emoji(offer_i)} in exchange for "
                                f"`{cost_a:,d}`{get_emoji(cost_i)}",
                )
                embed.add_field(
                    name="Updated Inventory", inline=False,
                    value=f"`{offer_i_have:,d}` {get_emoji(offer_i)} | `{cost_i_have:,d}` {get_emoji(cost_i)}"
                )
                embed.set_footer(text=f"Found by {user.display_name}", icon_url=user.avatar_url)
                await process_msg_edit(msg, None, embed)
                await process_msg_reaction_clear(msg)

            else:
                embed = discord.Embed(
                    color=user.colour, timestamp=get_timestamp(),
                    title="Encounter treasure",
                    description=f"Exchange failed, you only have {cost_item_current:,d}{get_emoji(cost_i)} left",
                )
                embed.set_footer(text=f"Found by {user.display_name}", icon_url=user.avatar_url)
                await process_msg_edit(msg, None, embed)
                await process_msg_reaction_clear(msg)

    async def enc_roll_boss(self, discoverer, ctx, msg):

        boss_alive = []
        timeout, count_players = 180, 0
        assembly_players, assembly_players_name = [], []
        time_discovered = get_time()

        for boss_name in bosses.find({
            "$or": [{"discoverer": {"$eq": 0}}, {"current_hp": {"$gt": 0}}]}, {
            "_id": 0, "boss": 1
        }):
            boss_alive.append(boss_name["boss"])

        boss = random.choice(boss_alive)

        if bosses.find_one({"boss": boss}, {"_id": 0, "discoverer": 1})["discoverer"] == 0:
            await self.enc_roll_boss_create(discoverer, boss)

        def embed_new_create(time_remaining, color):

            listings_formatted = ", ".join(assembly_players_name)
            if len(listings_formatted) == 0:
                listings_formatted = None

            a, b, c, d, e, f, g, h, i, j = self.enc_roll_boss_stats_get(boss)

            embed_new = discord.Embed(
                title="Encounter Boss", color=color, timestamp=get_timestamp(),
                description=f"The rare boss {boss} has been triggered!\n\n"
                            f"⏰ {round(time_remaining)} secs left!",
            )
            embed_new.add_field(
                name="Stats", inline=False,
                value=f"```"
                      f"Level   :  {d}\n"
                      f"HP      :  {c}%\n"
                      f"Jades   :  {h:,d}\n"
                      f"Coins   :  {f:,d}\n"
                      f"Medals  :  {i:,d}\n"
                      f"Exp     :  {g:,d}"
                      f"```"
            )
            embed_new.add_field(
                name=f"Assembly Players [{len(assembly_players)}]",
                value=listings_formatted, inline=False
            )
            embed_new.set_thumbnail(url=e)
            embed_new.set_footer(
                text=f"Discovered by {discoverer.display_name}",
                icon_url=discoverer.avatar_url
            )
            return embed_new

        await asyncio.sleep(2)

        await process_msg_edit(msg, None, embed_new_create(timeout, discoverer.colour))
        await msg.add_reaction("🏁")

        emojis_add = ["🏁"]
        for emoji in emojis_add:
            await process_msg_reaction_add(msg, emoji)

        link = f"https://discordapp.com/channels/{msg.guild.id}/{msg.channel.id}/{msg.id}"

        content = f"<@&{id_boss_busters}>! {next(self.assemble_captions)}"
        embed = discord.Embed(description=f"🏁 [Assemble here!]({link})")
        await process_msg_submit(ctx.channel, content, embed)

        def check(r, u):
            return u != self.client.user and str(r.emoji) in emojis_add and r.message.id == msg.id

        while count_players < 10:
            try:
                await asyncio.sleep(1)
                timeout = ((time_discovered + timedelta(seconds=180)) - get_time()).total_seconds()
                reaction, user = await self.client.wait_for("reaction_add", timeout=timeout, check=check)

            except asyncio.TimeoutError:
                embed = discord.Embed(title="🎌 Assembly ends!", colour=discoverer.colour)
                await process_msg_reaction_clear(msg)
                await process_msg_submit(ctx.channel, None, embed)
                break

            else:
                if str(user.id) in assembly_players or check_if_user_has_any_alt_roles(user):
                    pass

                elif str(user.id) not in assembly_players:

                    if bosses.find_one({"boss": boss, "challengers.user_id": str(user.id)}, {"_id": 1}) is None:
                        bosses.update_one({
                            "boss": boss}, {
                            "$push": {
                                "challengers": {
                                    "user_id": str(user.id),
                                    "damage": 0
                                }
                            },
                            "$inc": {
                                "rewards.medals": 100,
                                "rewards.jades": 200,
                                "rewards.experience": 150,
                                "rewards.coins": 250000
                            }
                        })

                    assembly_players.append(str(user.id))
                    assembly_players_name.append(user.display_name)
                    timeout_new = ((time_discovered + timedelta(seconds=180)) - get_time()).total_seconds()

                    await process_msg_edit(msg, None, embed_new_create(timeout_new, user.colour))
                    count_players += 1

        if len(assembly_players) == 0:

            await asyncio.sleep(3)
            embed = discord.Embed(
                title="Encounter Boss", colour=discoverer.colour, timestamp=get_timestamp(),
                description=f"No players have joined the assembly.\nThe rare boss {boss} has fled."
            )
            await process_msg_submit(ctx.channel, None, embed)
            self.enc_roll_boss_status_set(False)

        else:
            await asyncio.sleep(3)
            embed = discord.Embed(title=f"Battle with {boss} starts!", colour=discoverer.colour)
            await process_msg_submit(ctx.channel, None, embed)

            query = bosses.find_one({"boss": boss}, {"_id": 0, "total_hp": 1, "damage_cap": 1, "boss_url": 1})
            b_dmgcap, b_url, b_dmg = query["damage_cap"], query["boss_url"], query["total_hp"] * 0.01

            async with ctx.channel.typing():
                await asyncio.sleep(3)
                await self.enc_roll_boss_assembly(boss, assembly_players, b_dmgcap, b_dmg, b_url, ctx, discoverer)

    async def enc_roll_boss_assembly(self, boss, players, b_dmgcap, b_dmg, url, ctx, discoverer):

        damage_players = []
        for p in players:

            query = users.find_one({"user_id": p}, {"_id": 0, "medals": 1, "level": 1})

            p_medals, p_level = query["medals"], query["level"]
            p_dmg = b_dmg + (p_medals * (1 + (p_level / 100)))

            if p_dmg > b_dmgcap:
                p_dmg = b_dmgcap

            damage_players.append(p_dmg)
            bosses.update_one({
                "boss": boss,
                "challengers.user_id": p}, {
                "$inc": {
                    "challengers.$.damage": round(p_dmg, 0),
                    "current_hp": -round(p_dmg, 0)
                }
            })
            member = ctx.guild.get_member(int(p))
            embed = discord.Embed(
                color=member.colour,
                description=f"*{member.mention} "
                            f"{next(self.attack_verb)} {boss}, dealing {round(p_dmg):,d} damage!*"
            )
            await process_msg_submit(ctx.channel, None, embed)
            await asyncio.sleep(1)

        boss_stats = bosses.find_one({"boss": boss}, {"_id": 0})

        if boss_stats["current_hp"] <= 0:
            bosses.update_one({"boss": boss}, {"$set": {"current_hp": 0}})

        await self.enc_roll_boss_check(players, boss, url, boss_stats, ctx, discoverer)

    async def enc_roll_boss_check(self, players, boss, url, boss_stats, ctx, discoverer):

        boss_currenthp = bosses.find_one({"boss": boss}, {"_id": 0, "current_hp": 1})["current_hp"]

        if boss_currenthp > 0:

            jade_steal = round(boss_stats["rewards"]["jades"] * 0.05)
            coin_steal = round(boss_stats["rewards"]["coins"] * 0.08)

            description = f"💨 The Rare Boss {boss} has fled with `{round(boss_currenthp):,d}` remaining HP\n" \
                          f"💸 Stealing `{jade_steal:,d}` {e_j} & `{coin_steal:,d}` {e_c} " \
                          f"each from its attackers!\n\n{random.choice(self.boss_comment)}~"

            embed = discord.Embed(colour=discoverer.colour, description=description, timestamp=get_timestamp())
            embed.set_thumbnail(url=url)

            await self.enc_roll_boss_steal(players, jade_steal, coin_steal)
            await asyncio.sleep(3)

            bosses.update_one({"boss": boss}, {"$inc": {"rewards.jades": jade_steal, "rewards.coins": coin_steal}})

            await process_msg_submit(ctx.channel, None, embed)
            self.enc_roll_boss_status_set(False)

        elif boss_currenthp == 0:

            players_dmg = 0
            challengers, distribution = [], []

            for damage in bosses.aggregate([{
                "$match": {
                    "boss": boss}}, {
                "$unwind": {
                    "path": "$challengers"}}, {
                "$group": {
                    "_id": "",
                    "total_damage": {
                        "$sum": "$challengers.damage"}}}, {
                "$project": {
                    "_id": 0
                }}
            ]):
                players_dmg = damage["total_damage"]

            for data in bosses.aggregate([{
                "$match": {
                    "boss": boss}}, {
                "$unwind": {
                    "path": "$challengers"}}, {
                "$project": {
                    "_id": 0, "challengers": 1
                }
            }]):
                challengers.append(data["challengers"]["user_id"])
                distribution.append(round(((data["challengers"]["damage"]) / players_dmg), 2))

            coins, jades = boss_stats["rewards"]["coins"], boss_stats["rewards"]["jades"]
            medals, experience = boss_stats["rewards"]["medals"], boss_stats["rewards"]["experience"]

            coins_users = [i * coins for i in distribution]
            jades_users = [i * jades for i in distribution]
            medals_users = [i * medals for i in distribution]
            experience_users = [i * experience for i in distribution]

            rewards_zip = list(zip(challengers, coins_users, jades_users, medals_users, experience_users, distribution))

            embed = discord.Embed(title=f"The Rare Boss {boss} has been defeated!", colour=discoverer.colour)
            await process_msg_submit(ctx.channel, None, embed)
            await self.enc_roll_boss_defeat(boss, rewards_zip, url, boss_stats, ctx, discoverer)

    async def enc_roll_boss_defeat(self, boss, rewards, url, boss_stats, ctx, discoverer2):

        discoverers = [ctx.guild.get_member(int(boss_stats["discoverer"])), discoverer2]

        embed = discord.Embed(colour=ctx.author.colour, title="🎊 Boss defeat rewards!", timestamp=get_timestamp())
        embed.set_thumbnail(url=url)

        for reward in rewards:

            name = ctx.guild.get_member(int([reward][0][0]))

            if name is not None:
                user_id = [reward][0][0]
                p_lvl = users.find_one({"user_id": user_id}, {"_id": 0, "level": 1})["level"]

                damage = round([reward][0][5] * 100, 2)
                coins = round([reward][0][1] * (1 + p_lvl / 100))
                jades = round([reward][0][2] * (1 + p_lvl / 100))
                medals = round([reward][0][3] * (1 + p_lvl / 100))
                experience = round([reward][0][4] * (1 + p_lvl / 100))

                embed.add_field(
                    name=f"{name}, {damage}%", inline=False,
                    value=f"{coins:,d}{e_c}, {jades:,d}{e_j}, {medals:,d}{e_m}, {experience:,d} {e_x}",
                )

                users.update_one({"user_id": user_id}, {"$inc": {"jades": jades, "coins": coins, "medals": medals}})
                users.update_one({"user_id": user_id, "level": {"$lt": 60}}, {"$inc": {"experience": experience}})
                await perform_add_log("jades", jades, user_id)
                await perform_add_log("coins", coins, user_id)
                await perform_add_log("medals", medals, user_id)

        for i, d in enumerate(discoverers):

            if d is not None:
                jades, coins, medals, experience = 250, 150000, 150, 100
                users.update_one({"user_id": d.id}, {"$inc": {"jades": jades, "coins": coins, "medals": medals}})
                users.update_one({"user_id": d.id, "level": {"$lt": 60}}, {"$inc": {"experience": experience}})
                await perform_add_log("jades", jades, d.id)
                await perform_add_log("coins", coins, d.id)
                await perform_add_log("medals", medals, d.id)

                await asyncio.sleep(2)
                await process_msg_submit(ctx.channel, None, embed)
                await asyncio.sleep(1)

                caption = "initially"
                if i == len(discoverers) - 1:
                    caption = "lastly"

                description = f"{d.mention} earned an extra {jades:,d}{e_j}, {coins:,d}{e_c}, " \
                              f"{medals:,d}{e_m} and {experience:,d} {e_x} for {caption} discovering Rare Boss {boss}!"
                embed = discord.Embed(colour=d.colour, description=description, timestamp=get_timestamp())
                await process_msg_submit(ctx.channel, None, embed)

        users.update_many({"level": {"$gt": 60}}, {"$set": {"experience": 100000, "level_exp_next": 100000}})
        self.enc_roll_boss_status_set(False)

    async def enc_roll_boss_create(self, user, boss):

        discoverer = users.find_one({"user_id": str(user.id)}, {"_id": 0, "level": 1})
        boss_lvl = discoverer["level"] + 60
        multiplier = (1 + (boss_lvl / 100))

        total_medals = 10000
        for x in users.aggregate([{
            "$group": {
                "_id": "",
                "medals": {
                    "$sum": "$medals"}}}, {
            "$project": {
                "_id": 0
            }
        }]):
            total_medals = x["medals"]

        bosses.update_one({
            "boss": boss}, {
            "$set": {
                "discoverer": str(user.id),
                "level": boss_lvl,
                "total_hp": round(total_medals * multiplier, 0),
                "current_hp": round(total_medals * multiplier, 0),
                "damage_cap": round(total_medals * multiplier * 0.15, 0),
                "rewards.medals": 250,
                "rewards.jades": 1250,
                "rewards.experience": 350,
                "rewards.coins": 1500000
            }
        })

    async def enc_roll_boss_steal(self, players, jades, coins):

        for user_id in players:

            j = users.update_one({"user_id": user_id, "jades": {"$gte": jades}}, {"$inc": {"jades": - jades}})
            c = users.update_one({"user_id": user_id, "coins": {"$gte": coins}}, {"$inc": {"coins": - coins}})

            if j.modified_count > 0:
                await perform_add_log("jades", -jades, user_id)

            elif j.modified_count == 0:
                users.update_one({"user_id": user_id}, {"$set": {"jades": 0}})
                current_jades = users.find_one({"user_id": user_id}, {"_id": 0, "jades": 1})["jades"]
                await perform_add_log("jades", -current_jades, user_id)

            if c.modified_count > 0:
                await perform_add_log("coins", -coins, user_id)

            elif c.modified_count == 0:
                users.update_one({"user_id": user_id}, {"$set": {"coins": 0}})
                current_coins = users.find_one({"user_id": user_id}, {"_id": 0, "coins": 1})["coins"]
                await perform_add_log("coins", -current_coins, user_id)

    async def enc_boss_stats_help(self, ctx):

        embed = discord.Embed(
            title="bossinfo, binfo", colour=colour,
            description="shows discovered boss statistics"
        )
        demons_formatted = ", ".join(self.demons)
        embed.add_field(name="Bosses", value=f"*{demons_formatted}*")
        embed.add_field(
            name="Example",
            value=f"*`{self.prefix}binfo namazu`*\n"
                  f"*`{self.prefix}binfo all`*",
            inline=False
        )
        await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["binfo", "bossinfo"])
    @commands.guild_only()
    async def enc_boss_stats(self, ctx, *, boss_name=None):

        if boss_name is None:
            await self.enc_boss_stats_help(ctx)

        elif boss_name is not None:

            boss_name_formatted = boss_name.title()
            if boss_name_formatted.lower() == "all":

                query = bosses.find({"discoverer": {"$ne": 0}}, {"_id": 0})
                bosses_formatted = []

                for boss in query:
                    percent = (boss["current_hp"] / boss["total_hp"]) * 100
                    bosses_formatted.append(f"• {round(percent, 2)}%    {boss['boss']}")

                bosses_formatted_lines = "\n".join(bosses_formatted)
                boss_description = f"```" \
                                   f"  HP        Boss\n" \
                                   f"{bosses_formatted_lines}\n" \
                                   f"```"

                if len(bosses_formatted) == 0:
                    boss_description = "All rare bosses are currently dead or undiscovered"

                embed = discord.Embed(
                    title=f"Boss survivability", colour=colour,
                    description=boss_description, timestamp=get_timestamp()
                )
                await process_msg_submit(ctx.channel, None, embed)

            elif boss_name_formatted in self.demons:

                a, b, c, d, e, f, g, h, i, j = self.enc_roll_boss_stats_get(boss_name_formatted)

                try:
                    discoverer = ctx.guild.get_member(int(j)).display_name
                except AttributeError:
                    discoverer = None

                description = f"```" \
                              f"Discoverer  :: {discoverer}\n" \
                              f"     Level  :: {d:,d}\n" \
                              f"  Total Hp  :: {a:,d}\n" \
                              f"Current Hp  :: {b:,d}\n" \
                              f"    Medals  :: {i:,d}\n" \
                              f"     Jades  :: {h:,d}\n" \
                              f"     Coins  :: {f:,d}\n" \
                              f"Experience  :: {g:,d}```"

                embed = discord.Embed(
                    title=f"Rare Boss {boss_name_formatted} stats", colour=ctx.author.colour,
                    description=description, timestamp=get_timestamp()
                )
                embed.set_thumbnail(url=e)
                await process_msg_submit(ctx.channel, None, embed)

    @commands.command(aliases=["qz"])
    @commands.check(check_if_user_has_any_admin_roles)
    async def enc_add_quiz(self, ctx, arg1, *, emoji=None):

        name = arg1.replace("_", " ").lower()
        if name not in pool_all:
            await shikigami_post_approximate_results(ctx, name)

        elif emoji is None:
            embed = discord.Embed(
                colour=colour, title="No emojis provided",
                description="specify emojis to change the shikigami's identity"
            )
            await process_msg_submit(ctx.channel, None, embed)

        elif emoji is not None:
            x = shikigamis.update_one({"name": name}, {"$set": {"demon_quiz": emoji}})
            if x.modified_count != 0:
                await process_msg_reaction_add(ctx.message, "✅")


def setup(client):
    client.add_cog(Encounter(client))
