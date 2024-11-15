import discord
from discord.ext import commands
import mysql.connector
from database.db_init import init_db
from config import DATABASE_CONFIG

class GuildManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="reset_tables", description="Reset all tables for this server")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def reset_tables(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        try:
            conn = mysql.connector.connect(**DATABASE_CONFIG)
            c = conn.cursor()
            members_table = f"members_{guild_id}"
            auctions_table = f"auctions_{guild_id}"

            c.execute(f"DROP TABLE IF EXISTS {members_table}")
            c.execute(f"DROP TABLE IF EXISTS {auctions_table}")
            init_db(guild_id)
            conn.commit()
            conn.close()
            await interaction.response.send_message("✅ Tables have been successfully reset for this server.")
        except mysql.connector.Error as e:
            await interaction.response.send_message("❌ An error occurred while resetting tables. Please try again.")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        print(f"Joined new guild: {guild.name}")
        init_db(guild.id)
        await self.setup_auction_channels(guild)

    async def setup_auction_channels(self, guild):
        auction_category = discord.utils.get(guild.categories, name="Auctions")
        if not auction_category:
            auction_category = await guild.create_category("Auctions")
        winners_channel = discord.utils.get(guild.text_channels, name="auction-winners")
        if not winners_channel:
            await guild.create_text_channel("auction-winners", category=auction_category)

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Bot {self.bot.user} is ready!")
        for guild in self.bot.guilds:
            try:
                await self.bot.tree.sync(guild=guild)
                print(f"Commands synced for guild: {guild.name} ({guild.id})")
            except Exception as e:
                print(f"Error syncing commands for guild {guild.name}: {e}")

async def setup(bot):
    await bot.add_cog(GuildManagement(bot))

