import discord
from discord.ext import commands
import mysql.connector
from datetime import datetime
from database.db_init import init_db
from utils.autocomplete import item_name_autocomplete
from config import DATABASE_CONFIG

class AuctionCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="start_auction", description="Start auctions for multiple items with a specific color")
    @discord.app_commands.autocomplete(
        item1=item_name_autocomplete, item2=item_name_autocomplete, item3=item_name_autocomplete,
        item4=item_name_autocomplete, item5=item_name_autocomplete, item6=item_name_autocomplete,
        item7=item_name_autocomplete, item8=item_name_autocomplete, item9=item_name_autocomplete,
        item10=item_name_autocomplete, item11=item_name_autocomplete, item12=item_name_autocomplete,
        item13=item_name_autocomplete, item14=item_name_autocomplete, item15=item_name_autocomplete,
        item16=item_name_autocomplete, item17=item_name_autocomplete, item18=item_name_autocomplete,
        item19=item_name_autocomplete, item20=item_name_autocomplete
    )
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def start_auction(self, interaction: discord.Interaction, role: discord.Role, color: str, item1: str, item2: str = None, item3: str = None, item4: str = None, item5: str = None, item6: str = None, item7: str = None, item8: str = None, item9: str = None, item10: str = None, item11: str = None, item12: str = None, item13: str = None, item14: str = None, item15: str = None, item16: str = None, item17: str = None, item18: str = None, item19: str = None, item20: str = None):
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
            c.execute(f"""INSERT INTO {auction_table} (item_name, color, min_bid, highest_bid, channel_id, guild_id) VALUES (%s, %s, 10, 10, %s, %s)""", (item, color, channel.id, guild_id))
            await channel.send(f"Auction for {item} started with color {color}. Minimum bid is 10 points.")

        conn.commit()
        conn.close()

        announcements_channel = discord.utils.get(interaction.guild.text_channels, name="auction-announcements")
        if announcements_channel:
            await announcements_channel.send(f"{role.mention} New auctions have started for items: {', '.join(item_list)}!")

        await interaction.followup.send(f"Auction channels created for items: {', '.join(item_list)}.")

    @discord.app_commands.command(name="end_auction", description="End all active auctions")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def end_auction(self, interaction: discord.Interaction):
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
            conn.close()
            return

        winners_channel = discord.utils.get(interaction.guild.text_channels, name="auction-winners")
        if not winners_channel:
            winners_channel = await interaction.guild.create_text_channel("auction-winners")

        auction_end_messages = []
        today = datetime.now().strftime('%Y-%m-%d')

        for item_name, color, channel_id, highest_bid, highest_bidder in auctions:
            channel = interaction.guild.get_channel(channel_id) or await self.bot.fetch_channel(channel_id)
            highest_bidder_name = "No bids"

            if highest_bidder:
                try:
                    highest_bidder_member = interaction.guild.get_member(highest_bidder) or await interaction.guild.fetch_member(highest_bidder)
                    highest_bidder_name = highest_bidder_member.display_name if highest_bidder_member else "Unknown User (left server)"

                    if color.lower() == "purple":
                        try:
                            c.execute(f"UPDATE {members_table} SET last_loot = %s WHERE member_id = %s", (datetime.now(), highest_bidder))
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
            channel = interaction.guild.get_channel(channel_id) or await self.bot.fetch_channel(channel_id)
            await channel.delete()

        c.execute(f"DELETE FROM {auction_table} WHERE guild_id = %s", (guild_id,))
        conn.commit()
        conn.close()
        await interaction.followup.send("All auctions ended and channels deleted.")

    @discord.app_commands.command(name="bid", description="Place a bid in the current auction")
    async def bid(self, interaction: discord.Interaction, bid_amount: int):
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
            await interaction.response.send_message("🚫 You don't have enough adjusted points to place this bid.", ephemeral=True)
            return
        if bid_amount < highest_bid + 5:
            await interaction.response.send_message(f"🚫 Your bid must be at least {highest_bid + 5} points.", ephemeral=True)
            return
        if highest_bidder:
            c.execute(f"UPDATE {members_table} SET remaining_adjusted_points = remaining_adjusted_points + %s WHERE member_id = %s", (highest_bid, highest_bidder))
        c.execute(f"UPDATE {auction_table} SET highest_bid = %s, highest_bidder = %s WHERE channel_id = %s", (bid_amount, member.id, channel.id))
        c.execute(f"UPDATE {members_table} SET remaining_adjusted_points = remaining_adjusted_points - %s WHERE member_id = %s", (bid_amount, member.id))
        conn.commit()
        conn.close()
        await interaction.response.send_message(f"🎉 {member.display_name} is now the highest bidder for **{item_name}** with a bid of {bid_amount} points!")

async def setup(bot):
    await bot.add_cog(AuctionCommands(bot))

