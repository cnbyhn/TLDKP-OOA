import mysql.connector
import json
from datetime import datetime, timedelta
import discord
from discord.ext import commands
import os
from flask import Flask
from threading import Thread

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


DATABASE_CONFIG = {
    "host": "xxxxxx",
    "user": "xxxxxx",
    "password": "xxxxxx",
    "database": "xxxxxxx",
    "port": "xxxxxxx"
}

ITEMS_JSON_FILE = "items.json"  


def init_db(guild_id):
    conn = mysql.connector.connect(**DATABASE_CONFIG)
    c = conn.cursor()
    members_table = f"members_{guild_id}"
    auctions_table = f"auctions_{guild_id}"

    c.execute(f"""CREATE TABLE IF NOT EXISTS {members_table} (
                    member_id BIGINT PRIMARY KEY,
                    guild_id BIGINT,
                    points INT DEFAULT 0,
                    last_loot DATETIME,
                    remaining_adjusted_points INT DEFAULT 0
                )""")
    c.execute(f"""CREATE TABLE IF NOT EXISTS {auctions_table} (
                    auction_id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    item_name VARCHAR(255),
                    color VARCHAR(50),
                    min_bid INT DEFAULT 10,
                    highest_bid INT DEFAULT 10,
                    highest_bidder BIGINT,
                    channel_id BIGINT,
                    guild_id BIGINT
                )""")
    conn.commit()
    conn.close()


def last_sunday(date):
    return date - timedelta(days=date.weekday() + 1) if date.weekday() != 6 else date


def calculate_adjusted_points(guild_id, member_id):
    conn = mysql.connector.connect(**DATABASE_CONFIG)
    c = conn.cursor()
    table_name = f"members_{guild_id}"
    c.execute(f"SELECT points, last_loot FROM {table_name} WHERE member_id = %s", (member_id,))
    result = c.fetchone()
    conn.close()
    if not result:
        return 0

    points, last_loot = result
    last_loot_date = last_loot if last_loot else datetime.now()
    weeks_missed = (last_sunday(datetime.now()) - last_sunday(last_loot_date)).days // 7
    adjusted_points = points * (1 + ((weeks_missed - 1) * 0.5)) if weeks_missed >= 2 else points
    return adjusted_points


def load_items_from_json():
    try:
        with open(ITEMS_JSON_FILE, "r") as f:
            items = json.load(f)
        print("✅ Items loaded from JSON.")
        return items
    except FileNotFoundError:
        print(f"❌ {ITEMS_JSON_FILE} not found.")
        return []
    except json.JSONDecodeError:
        print(f"❌ Error decoding {ITEMS_JSON_FILE}.")
        return []


async def item_name_autocomplete(interaction: discord.Interaction, current: str):
    items = load_items_from_json()
    return [
        discord.app_commands.Choice(name=item, value=item)
        for item in items if current.lower() in item.lower()
    ][:25]


async def setup_auction_channels(guild):
    auction_category = discord.utils.get(guild.categories, name="Auctions")
    if not auction_category:
        try:
            auction_category = await guild.create_category("Auctions")
        except discord.Forbidden:
            return

    winners_channel = discord.utils.get(guild.text_channels, name="auction-winners")
    if not winners_channel:
        try:
            await guild.create_text_channel("auction-winners", category=auction_category)
        except discord.Forbidden:
            pass

@bot.event
async def on_guild_join(guild):
    print(f"Joined new guild: {guild.name}")
    init_db(guild.id)
    await setup_auction_channels(guild)

@bot.event
async def on_ready():
    print(f"Bot {bot.user} is ready!")
    await bot.tree.sync()
    for guild in bot.guilds:
        init_db(guild.id)
        await setup_auction_channels(guild)

@bot.event
async def on_guild_join(guild):
    print(f"Joined new guild: {guild.name}")
    init_db(guild.id)
    await setup_auction_channels(guild)


@bot.tree.command(name="start_auction", description="Start auctions for multiple items with a specific color")
@discord.app_commands.autocomplete(
    item1 = item_name_autocomplete, item2 = item_name_autocomplete, item3 = item_name_autocomplete, 
    item4 = item_name_autocomplete, item5 = item_name_autocomplete, item6 = item_name_autocomplete, 
    item7 = item_name_autocomplete, item8 = item_name_autocomplete, item9 = item_name_autocomplete, 
    item10 = item_name_autocomplete, item11 = item_name_autocomplete, item12 = item_name_autocomplete, 
    item13 = item_name_autocomplete, item14 = item_name_autocomplete, item15 = item_name_autocomplete, 
    item16 = item_name_autocomplete, item17 = item_name_autocomplete, item18 = item_name_autocomplete, 
    item19 = item_name_autocomplete, item20 = item_name_autocomplete
)
@discord.app_commands.checks.has_permissions(administrator=True)
async def start_auction(interaction: discord.Interaction, role: discord.Role, color: str, item1: str, item2: str = None, item3: str = None, item4: str = None, item5: str = None, item6: str = None, item7: str = None, item8: str = None, item9: str = None, item10: str = None, item11: str = None, item12: str = None, item13: str = None, item14: str = None, item15: str = None, item16: str = None, item17: str = None, item18: str = None, item19: str = None, item20: str = None):
    await interaction.response.defer()
    guild_id = interaction.guild.id
    init_db(guild_id)

    conn = mysql.connector.connect(**DATABASE_CONFIG)
    c = conn.cursor()
    auction_category = discord.utils.get(interaction.guild.categories, name="Auctions")
    if not auction_category:
        await interaction.followup.send("⚠️ 'Auctions' category not found.")
        return

    item_list = [item for item in [item1, item2, item3, item4, item5, item6, item7, item8, item9, item10, item11, item12, item13, item14, item15, item16, item17, item18, item19, item20] if item]
    auction_table = f"auctions_{guild_id}"

    for item in item_list:
        channel_name = f"{color}-{item.replace(' ', '-').lower()}-auction"
        channel = await interaction.guild.create_text_channel(channel_name, category=auction_category)
        # Properly format the auction_table name using f-string
        c.execute(f"""INSERT INTO {auction_table} (item_name, color, min_bid, highest_bid, channel_id, guild_id) 
                     VALUES (%s, %s, 10, 10, %s, %s)""",
                  (item, color, channel.id, guild_id))
        await channel.send(f"Auction for {item} started with color {color}. Minimum bid is 10 points.")

    conn.commit()
    conn.close()

    announcements_channel = discord.utils.get(interaction.guild.text_channels, name="auction-announcements")
    if announcements_channel:
        await announcements_channel.send(f"{role.mention} New auctions have started for items: {', '.join(item_list)}!")

    await interaction.followup.send(f"Auction channels created for items: {', '.join(item_list)}.")


@bot.tree.command(name="end_auction", description="End all active auctions")
@discord.app_commands.checks.has_permissions(administrator=True)
async def end_auction(interaction: discord.Interaction):
    await interaction.response.defer()
    guild_id = interaction.guild.id
    auction_table = f"auctions_{guild_id}"
    members_table = f"members_{guild_id}"

    conn = mysql.connector.connect(**DATABASE_CONFIG)
    c = conn.cursor()

    try:
        c.execute(f"SELECT item_name, color, channel_id, highest_bid, highest_bidder FROM {auction_table} WHERE guild_id = %s", (guild_id,))
        auctions = c.fetchall()
    except mysql.connector.Error as e:
        await interaction.followup.send("❌ Error accessing the database.")
        print(f"Database error: {e}")
        conn.close()
        return

    winners_channel = discord.utils.get(interaction.guild.text_channels, name="auction-winners")
    if not winners_channel:
        winners_channel = await interaction.guild.create_text_channel("auction-winners")

    auction_end_messages = []
    today = datetime.now().strftime('%Y-%m-%d')

    for item_name, color, channel_id, highest_bid, highest_bidder in auctions:
        channel = interaction.guild.get_channel(channel_id) or await bot.fetch_channel(channel_id)
        highest_bidder_name = "No bids"

        if highest_bidder:
            try:
                highest_bidder_member = interaction.guild.get_member(highest_bidder) or await interaction.guild.fetch_member(highest_bidder)
                highest_bidder_name = highest_bidder_member.display_name if highest_bidder_member else "Unknown User (left server)"

                # Reset the last_loot date if the item is purple
                if color.lower() == "purple":
                    try:
                        c.execute(f"UPDATE {members_table} SET last_loot = %s WHERE member_id = %s", (datetime.now(), highest_bidder))
                        print(f"✅ last_loot reset for {highest_bidder_name} (ID: {highest_bidder}) due to purple item.")
                    except mysql.connector.Error as e:
                        print(f"❌ Failed to update last_loot for {highest_bidder_name}: {e}")

            except Exception as e:
                print(f"Error fetching highest bidder with ID {highest_bidder}: {e}")
                highest_bidder_name = "Unknown User (error retrieving info)"

        auction_end_messages.append(f"{highest_bidder_name} won {item_name} with {highest_bid} points on {today}.")
        await channel.send(f"Auction ended. {highest_bidder_name} won {item_name} with {highest_bid} points on {today}.")

    for message in auction_end_messages:
        await winners_channel.send(message)

    for _, _, channel_id, _, _ in auctions:
        channel = interaction.guild.get_channel(channel_id) or await bot.fetch_channel(channel_id)
        await channel.delete()

    # Clear all auction records for the guild after ending auctions
    c.execute(f"DELETE FROM {auction_table} WHERE guild_id = %s", (guild_id,))
    conn.commit()
    conn.close()
    await interaction.followup.send("All auctions ended and channels deleted.")



@bot.tree.command(name="set_points", description="Set points for yourself or another member (admins only)")
@discord.app_commands.checks.has_permissions(administrator=True)
async def set_points(interaction: discord.Interaction, points: int, member: discord.Member = None):
    target_member = member or interaction.user
    guild_id = interaction.guild.id
    members_table = f"members_{guild_id}"
    conn = mysql.connector.connect(**DATABASE_CONFIG)
    c = conn.cursor()

    # Step 1: Check if the member is already in the database
    c.execute(f"SELECT points, last_loot FROM {members_table} WHERE member_id = %s", (target_member.id,))
    result = c.fetchone()

    if result is None:
        last_loot_date = datetime.now()
        adjusted_points = points
        print(f"🆕 New member entry. Setting initial last_loot for {target_member.display_name} and points to {points}.")

        try:
            # Insert new member record with formatted table name
            c.execute(
                f"""INSERT INTO {members_table} (member_id, guild_id, points, last_loot, remaining_adjusted_points)
                    VALUES (%s, %s, %s, %s, %s)""",
                (target_member.id, guild_id, points, last_loot_date, adjusted_points)
            )
            conn.commit()
            print(f"✅ Successfully set points for new member {target_member.display_name}. Adjusted points: {adjusted_points}.")
        except mysql.connector.Error as e:
            print(f"❌ Database error when inserting new member {target_member.display_name}: {e}")
            await interaction.response.send_message("❌ An error occurred while setting points. Please try again.")
            conn.close()
            return
    else:
        current_points, last_loot_date = result
        weeks_missed = (last_sunday(datetime.now()) - last_sunday(last_loot_date)).days // 7
        adjusted_points = points * (1 + ((weeks_missed - 1) * 0.5)) if weeks_missed >= 2 else points
        print(f"🔄 Existing member {target_member.display_name}. Weeks missed = {weeks_missed}, Adjusted points = {adjusted_points}.")

        # Update points without resetting last_loot
        try:
            c.execute(
                f"""UPDATE {members_table} 
                    SET points = %s, remaining_adjusted_points = %s 
                    WHERE member_id = %s""",
                (points, adjusted_points, target_member.id)
            )
            conn.commit()
            print(f"✅ Successfully updated points for {target_member.display_name}. Adjusted points: {adjusted_points}.")
        except mysql.connector.Error as e:
            print(f"❌ Database error when updating points for {target_member.display_name}: {e}")
            await interaction.response.send_message("❌ An error occurred while setting points. Please try again.")
            conn.close()
            return

    conn.close()

    # Send response to the user
    if target_member == interaction.user:
        await interaction.response.send_message(
            f"✅ Your points have been set to {points}. Adjusted points: {adjusted_points}."
        )
    else:
        await interaction.response.send_message(
            f"✅ {target_member.display_name}'s points have been set to {points} by an admin. Adjusted points: {adjusted_points}."
        )



@bot.tree.command(name="check_points", description="Check a member's points")
async def check_points(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    guild_id = interaction.guild.id
    members_table = f"members_{guild_id}"
    conn = mysql.connector.connect(**DATABASE_CONFIG)
    c = conn.cursor()

    print(f"🔍 Checking points for member: {member.display_name} (ID: {member.id}) in guild: {guild_id}")
    c.execute(f"SELECT points, last_loot, remaining_adjusted_points FROM {members_table} WHERE member_id = %s", (member.id,))
    result = c.fetchone()
    
    conn.close()

    if result:
        base_points, last_loot, remaining_adjusted_points = result
        last_loot_date = last_loot if last_loot else datetime.now()
        weeks_missed = (last_sunday(datetime.now()) - last_sunday(last_loot_date)).days // 7

        await interaction.response.send_message(
            f"📊 **{member.display_name}**'s Points Check:\n"
            f"- Base Points: {base_points}\n"
            f"- Weeks Missed: {weeks_missed}\n"
            f"- **Remaining Adjusted Points for Bidding**: {remaining_adjusted_points}"
        )
    else:
        await interaction.response.send_message(f"⚠️ No points record found for {member.display_name}.")


@bot.tree.command(name="adjust_timer", description="Manually adjust the timer for a member")
@discord.app_commands.checks.has_permissions(administrator=True)
async def adjust_timer(interaction: discord.Interaction, member: discord.Member, date: str):
    await interaction.response.defer()
    try:
        new_date = datetime.strptime(date, "%Y-%m-%d")
        user_id = member.id
        guild_id = interaction.guild.id
        members_table = f"members_{guild_id}"

        conn = mysql.connector.connect(**DATABASE_CONFIG)
        c = conn.cursor()

        c.execute(f"SELECT points FROM {members_table} WHERE member_id = %s", (user_id,))
        result = c.fetchone()
        if not result:
            await interaction.followup.send(
                f"⚠️ {member.display_name} has no points record. Use `/set_points` to initialize."
            )
            conn.close()
            return

        c.execute(f"UPDATE {members_table} SET last_loot = %s WHERE member_id = %s", (new_date, user_id))

        points = result[0]
        weeks_missed = (last_sunday(datetime.now()) - last_sunday(new_date)).days // 7
        adjusted_points = points * (1 + ((weeks_missed - 1) * 0.5)) if weeks_missed >= 2 else points

        c.execute(f"UPDATE {members_table} SET remaining_adjusted_points = %s WHERE member_id = %s", (adjusted_points, user_id))

        conn.commit()
        conn.close()

        await interaction.followup.send(
            f"✅ {member.display_name}'s timer has been successfully adjusted to {new_date.strftime('%Y-%m-%d')}."
            f"\nAdjusted points now: {adjusted_points}"
        )

    except ValueError:
        await interaction.followup.send("❌ Invalid date format! Please use the correct format: YYYY-MM-DD.")
    except Exception as e:
        print(f"Error in adjust_timer command: {e}")
        await interaction.followup.send("❌ An error occurred while processing this command.")


@bot.tree.command(name="bid", description="Place a bid in the current auction")
async def bid(interaction: discord.Interaction, bid_amount: int):
    member = interaction.user
    channel = interaction.channel
    guild_id = interaction.guild.id
    auction_table = f"auctions_{guild_id}"
    members_table = f"members_{guild_id}"

    conn = mysql.connector.connect(**DATABASE_CONFIG)
    c = conn.cursor()

    c.execute(f"SELECT item_name, highest_bid, highest_bidder FROM {auction_table} WHERE channel_id = %s", (channel.id,))
    auction = c.fetchone()
    if not auction:
        await interaction.response.send_message("⚠️ This channel is not part of an active auction.", ephemeral=True)
        return
    item_name, highest_bid, highest_bidder = auction

    c.execute(f"SELECT points, remaining_adjusted_points FROM {members_table} WHERE member_id = %s", (member.id,))
    member_data = c.fetchone()
    if not member_data or member_data[1] < bid_amount:
        await interaction.response.send_message("🚫 You don't have enough adjusted points to place this bid.",
                                                ephemeral=True)
        return
    if bid_amount < highest_bid + 5:
        await interaction.response.send_message(f"🚫 Your bid must be at least {highest_bid + 5} points.",
                                                ephemeral=True)
        return
    if highest_bidder:
        c.execute(f"UPDATE {members_table} SET remaining_adjusted_points = remaining_adjusted_points + %s WHERE member_id = %s",
                  (highest_bid, highest_bidder))
    c.execute(f"UPDATE {auction_table} SET highest_bid = %s, highest_bidder = %s WHERE channel_id = %s",
              (bid_amount, member.id, channel.id))
    c.execute(f"UPDATE {members_table} SET remaining_adjusted_points = remaining_adjusted_points - %s WHERE member_id = %s",
              (bid_amount, member.id))
    conn.commit()
    conn.close()
    await interaction.response.send_message(
        f"🎉 {member.display_name} is now the highest bidder for **{item_name}** with a bid of {bid_amount} points!")


@bot.tree.command(name="announce_raid", description="Announce a raid at a specified time and tag a role")
@discord.app_commands.checks.has_permissions(administrator=True)
async def announce_raid(interaction: discord.Interaction, event: str, time: int, role: discord.Role):
    await interaction.response.defer()
    try:
        raid_time = (datetime.now() + timedelta(hours=time)).strftime('%H:%M')
        announcement = (
            f"{role.mention} 📢 **{event} Alert!** {event} will take place in {time} hour(s) at {raid_time}.\n"
            "Please prepare accordingly!"
        )
        await interaction.followup.send(announcement, allowed_mentions=discord.AllowedMentions(roles=True))

    except Exception as e:
        print(f"Error in announce_raid command: {e}")
        await interaction.followup.send("❌ An error occurred while processing this command.")


@bot.tree.command(name="reset_all_points", description="Reset points for all members to 0")
@discord.app_commands.checks.has_permissions(administrator=True)
async def reset_all_points(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    members_table = f"members_{guild_id}"

    conn = mysql.connector.connect(**DATABASE_CONFIG)
    c = conn.cursor()
    c.execute(f"UPDATE {members_table} SET points = 0, remaining_adjusted_points = 0 WHERE guild_id = %s",
              (guild_id,))
    conn.commit()
    conn.close()
    await interaction.response.send_message("✅ All members' points have been reset to 0.")


BOSS_LIST = [
    "Grand Aelon", "Kowazan", "Nirma", "Morkus", "Minezerok", "Cornelius", "Junobote", "Excavator",
    "Ahzreil", "Talus", "Malakar", "Adentus", "Chernobog", "Aridus"
]


async def boss_autocomplete(interaction: discord.Interaction, current: str):
    return [
        discord.app_commands.Choice(name=boss, value=boss)
        for boss in BOSS_LIST if current.lower() in boss.lower()
    ][:25]


@bot.tree.command(name="raid_poll", description="Create a poll for members to vote on raid bosses")
@discord.app_commands.autocomplete(boss1=boss_autocomplete, boss2=boss_autocomplete, boss3=boss_autocomplete)
@discord.app_commands.describe(
    boss1="Mandatory boss option 1",
    boss2="Mandatory boss option 2",
    boss3="Optional boss option 3"
)
async def raid_poll(interaction: discord.Interaction, boss1: str, boss2: str, boss3: str = None):
    if boss1 not in BOSS_LIST or boss2 not in BOSS_LIST or \
            (boss3 and boss3 not in BOSS_LIST):
        await interaction.response.send_message("⚠️ Please choose bosses from the predefined list.", ephemeral=True)
        return

    await interaction.response.defer()

    poll_message = "**Raid Boss Poll**\nVote on which raid bosses to fight!"
    bosses = [boss1, boss2, boss3]
    boss_emoji_map = {}
    for i, boss in enumerate(filter(None, bosses), start=1):
        emoji = f"{i}\u20E3"
        poll_message += f"\n{emoji} - {boss}"
        boss_emoji_map[emoji] = boss

    poll_message = await interaction.followup.send(poll_message)
    for emoji in boss_emoji_map:
        await poll_message.add_reaction(emoji)


app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
bot.run(TOKEN)
