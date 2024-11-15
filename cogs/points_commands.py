import discord
from discord.ext import commands
import mysql.connector
from datetime import datetime, timezone
from config import DATABASE_CONFIG

class PointsCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="set_points", description="Set points for yourself or another member (admins only)")
    async def set_points(self, interaction: discord.Interaction, points: int, member: discord.Member = None):
        target_member = member or interaction.user
        guild_id = interaction.guild.id
        members_table = f"members_{guild_id}"
        conn = mysql.connector.connect(**DATABASE_CONFIG)
        c = conn.cursor()

        c.execute(f"SELECT points, last_loot FROM {members_table} WHERE member_id = %s", (target_member.id,))
        result = c.fetchone()

        if result is None:
            last_loot_date = datetime.now()
            adjusted_points = points
            try:
                c.execute(
                    f"""INSERT INTO {members_table} (member_id, guild_id, points, last_loot, remaining_adjusted_points)
                        VALUES (%s, %s, %s, %s, %s)""",
                    (target_member.id, guild_id, points, last_loot_date, adjusted_points)
                )
                conn.commit()
            except mysql.connector.Error as e:
                await interaction.response.send_message("❌ An error occurred while setting points. Please try again.")
                conn.close()
                return
        else:
            current_points, last_loot_date = result
            days_difference = (datetime.now().date() - last_loot_date.date()).days
            weeks_missed = max(0, days_difference // 7)
            adjusted_points = points * (1 + ((weeks_missed - 1) * 0.5)) if weeks_missed >= 2 else points

            try:
                c.execute(
                    f"""UPDATE {members_table} 
                        SET points = %s, remaining_adjusted_points = %s 
                        WHERE member_id = %s""",
                    (points, adjusted_points, target_member.id)
                )
                conn.commit()
            except mysql.connector.Error as e:
                await interaction.response.send_message("❌ An error occurred while setting points. Please try again.")
                conn.close()
                return

        conn.close()
        message = (f"✅ {target_member.display_name}'s points have been set to {points}."
                   f" Adjusted points: {adjusted_points}.") if target_member != interaction.user else \
                  (f"✅ Your points have been set to {points}. Adjusted points: {adjusted_points}.")
        await interaction.response.send_message(message)

    @discord.app_commands.command(name="check_points", description="Check a member's points")
    async def check_points(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        guild_id = interaction.guild.id
        members_table = f"members_{guild_id}"
        conn = mysql.connector.connect(**DATABASE_CONFIG)
        c = conn.cursor()

        c.execute(f"SELECT points, last_loot, remaining_adjusted_points FROM {members_table} WHERE member_id = %s", (member.id,))
        result = c.fetchone()
        conn.close()

        if result:
            base_points, last_loot, remaining_adjusted_points = result
            days_difference = (datetime.now().date() - (last_loot if last_loot else datetime.now()).date()).days
            weeks_missed = max(0, days_difference // 7)

            await interaction.response.send_message(
                f"📊 **{member.display_name}**'s Points Check:\n"
                f"- Base Points: {base_points}\n"
                f"- Weeks Missed: {weeks_missed}\n"
                f"- **Remaining Adjusted Points for Bidding**: {remaining_adjusted_points}\n"
                f"- **Last Loot**: {last_loot.strftime('%Y-%m-%d %H:%M:%S') if last_loot else 'First Set'}"
            )
        else:
            await interaction.response.send_message(f"⚠️ No points record found for {member.display_name}.")

    @discord.app_commands.command(name="reset_all_points", description="Reset points for all members to 0")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def reset_all_points(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        members_table = f"members_{guild_id}"

        conn = mysql.connector.connect(**DATABASE_CONFIG)
        c = conn.cursor()
        c.execute(f"UPDATE {members_table} SET points = 0, remaining_adjusted_points = 0 WHERE guild_id = %s", (guild_id,))
        conn.commit()
        conn.close()
        await interaction.response.send_message("✅ All members' points have been reset to 0.")

    @discord.app_commands.command(name="add_points", description="Add points to a member's base points (admins only)")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def add_points(self, interaction: discord.Interaction, points: int, member: discord.Member):
        guild_id = interaction.guild.id
        members_table = f"members_{guild_id}"

        conn = mysql.connector.connect(**DATABASE_CONFIG)
        c = conn.cursor()
        c.execute(f"SELECT points, last_loot FROM {members_table} WHERE member_id = %s", (member.id,))
        result = c.fetchone()
        
        if result:
            current_points, last_loot_date = result
            new_points = current_points + points
            MAX_POINTS = 9223372036854775807
            if new_points > MAX_POINTS:
                await interaction.response.send_message(
                    f"⚠️ Cannot add {points} points to {member.display_name}. It would exceed the maximum allowed points."
                )
                conn.close()
                return
            c.execute(f"UPDATE {members_table} SET points = %s WHERE member_id = %s", (new_points, member.id))
            days_difference = (datetime.now().date() - (last_loot_date if last_loot_date else datetime.now(timezone.utc)).date()).days
            weeks_missed = max(0, days_difference // 7)
            adjusted_points = new_points * (1 + ((weeks_missed - 1) * 0.5)) if weeks_missed >= 2 else new_points
            c.execute(f"UPDATE {members_table} SET remaining_adjusted_points = %s WHERE member_id = %s", (adjusted_points, member.id))
            conn.commit()
            await interaction.response.send_message(
                f"✅ {points} points have been added to {member.display_name}'s base points. New total: {new_points}. Adjusted points: {adjusted_points}."
            )
        else:
            await interaction.response.send_message(f"⚠️ No points record found for {member.display_name}.")
        
        conn.close()

async def setup(bot):
    await bot.add_cog(PointsCommands(bot))
