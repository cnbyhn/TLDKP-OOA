import discord
from discord.ext import commands
from utils.autocomplete import boss_autocomplete
from datetime import datetime, timedelta

class RaidCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="announce_raid", description="Announce a raid at a specified time and tag a role")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def announce_raid(self, interaction: discord.Interaction, event: str, time: int, role: discord.Role):
        await interaction.response.defer()
        raid_time = (datetime.now() + timedelta(hours=time)).strftime('%H:%M')
        announcement = (
            f"{role.mention} 📢 **{event} Alert!** {event} will take place in {time} hour(s) at {raid_time} UTC.\n"
            "Please prepare accordingly!"
        )
        await interaction.followup.send(announcement, allowed_mentions=discord.AllowedMentions(roles=True))

    @discord.app_commands.command(name="raid_poll", description="Create a poll for members to vote on raid bosses")
    @discord.app_commands.autocomplete(
        boss1=boss_autocomplete,
        boss2=boss_autocomplete,
        boss3=boss_autocomplete,
        boss4=boss_autocomplete,
        boss5=boss_autocomplete,
        boss6=boss_autocomplete,
        boss7=boss_autocomplete
    )
    async def raid_poll(
        self, interaction: discord.Interaction,
        boss1: str, boss2: str, boss3: str, boss4: str = None, boss5: str = None, boss6: str = None, boss7: str = None
    ):
        await interaction.response.defer()
        bosses = [boss1, boss2, boss3, boss4, boss5, boss6, boss7]
        poll_message = "**Raid Boss Poll**\nVote on which raid bosses to fight!"
        boss_emoji_map = {}

        for i, boss in enumerate(filter(None, bosses), start=1):
            emoji = f"{i}\u20E3"
            poll_message += f"\n{emoji} - {boss}"
            boss_emoji_map[emoji] = boss

        poll_message_obj = await interaction.followup.send(poll_message)
        for emoji in boss_emoji_map:
            await poll_message_obj.add_reaction(emoji)

async def setup(bot):
    await bot.add_cog(RaidCommands(bot))

