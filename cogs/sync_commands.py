import discord
from discord.ext import commands

class SyncCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    @discord.app_commands.command(name="sync", description="Manually sync commands for this server")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def sync(self, interaction: discord.Interaction):
    
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        try:
            await self.bot.tree.sync(guild=guild)
            await interaction.response.send_message(f"✅ Commands have been synced for this server: {guild.name}", ephemeral=True)
            print(f"Commands synced for guild: {guild.name} (ID: {guild.id})")
        except Exception as e:
            await interaction.response.send_message("❌ An error occurred while syncing commands.", ephemeral=True)
            print(f"Error syncing commands for guild {guild.name} (ID: {guild.id}): {e}")

async def setup(bot):
    await bot.add_cog(SyncCommands(bot))
