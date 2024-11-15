import discord
from discord.ext import commands
import mysql.connector
from datetime import datetime
from config import DATABASE_CONFIG

class Timers(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="adjust_timer", description="Manually adjust the timer for a member")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def adjust_timer(self, interaction: discord.Interaction, member: discord.Member, date: str):
        await interaction.response.defer()
        try:
            new_date = datetime.strptime(date, "%Y-%m-%d")
            guild_id = interaction.guild.id
            members_table = f"members_{guild_id}"

            conn = mysql.connector.connect(**DATABASE_CONFIG)
            c = conn.cursor()

            c.execute(f"SELECT points FROM {members_table} WHERE member_id = %s", (member.id,))
            result = c.fetchone()
            if not result:
                await interaction.followup.send(
                    f"⚠️ {member.display_name} has no points record. Use `/set_points` to initialize."
                )
                conn.close()
                return

            c.execute(f"UPDATE {members_table} SET last_loot = %s WHERE member_id = %s", (new_date, member.id))

            points = result[0]
            days_difference = (datetime.now().date() - new_date.date()).days
            weeks_missed = max(0, days_difference // 7)
            adjusted_points = points * (1 + ((weeks_missed - 1) * 0.5)) if weeks_missed >= 2 else points

            c.execute(f"UPDATE {members_table} SET remaining_adjusted_points = %s WHERE member_id = %s", (adjusted_points, member.id))

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

async def setup(bot):
    await bot.add_cog(Timers(bot))
