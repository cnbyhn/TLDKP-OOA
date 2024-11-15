import discord
from discord.ext import commands
import json
import os

class ReactionRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message_id = self.load_message_id() 

        self.role_mappings = {
            "⚔️": "DD",        # Damage Dealer
            "🛡️": "Tank",      # Tank
            "❤️": "Healer"     # Healer
        }

    def load_message_id(self):
        """Loads the message ID from a JSON file if it exists."""
        if os.path.exists("message_id.json"):
            with open("message_id.json", "r") as f:
                data = json.load(f)
                return data.get("message_id")
        return None

    def save_message_id(self, message_id):
        """Saves the message ID to a JSON file."""
        with open("message_id.json", "w") as f:
            json.dump({"message_id": message_id}, f)

    @discord.app_commands.command(name="setup_reaction_roles", description="Setup a reaction role message for Healer, Tank, and DD")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def setup_reaction_roles(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Creates a reaction role message and saves its ID."""
        description = (
            "React to this message to assign yourself a role:\n\n"
            "⚔️ for **DD (Damage Dealer)**\n"
            "🛡️ for **Tank**\n"
            "❤️ for **Healer**"
        )
        embed = discord.Embed(title="Role Assignment", description=description, color=discord.Color.blue())
        message = await channel.send(embed=embed)

        
        for emoji in self.role_mappings.keys():
            await message.add_reaction(emoji)

    
        self.message_id = message.id
        self.save_message_id(self.message_id)
        print(f"Reaction role message created and message ID set to: {self.message_id}")
        await interaction.response.send_message(f"✅ Reaction role message sent to {channel.mention}", ephemeral=True)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Handles adding roles when a user reacts to the reaction role message."""
        if payload.message_id != self.message_id:
            return  

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        member = guild.get_member(payload.user_id)
        if not member or member.bot:
            return

        
        role_name = self.role_mappings.get(payload.emoji.name)
        if role_name:
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                try:
                    await member.add_roles(role)
                    print(f"Assigned {role_name} role to {member.display_name}")
                except discord.Forbidden:
                    print(f"❌ Permission error: Cannot assign the {role_name} role.")
                except discord.HTTPException as e:
                    print(f"❌ HTTP error while adding role: {e}")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """Handles removing roles when a user removes their reaction from the reaction role message."""
        if payload.message_id != self.message_id:
            return  

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        member = guild.get_member(payload.user_id)
        if not member or member.bot:
            return

        
        role_name = self.role_mappings.get(payload.emoji.name)
        if role_name:
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                try:
                    await member.remove_roles(role)
                    print(f"Removed {role_name} role from {member.display_name}")
                except discord.Forbidden:
                    print(f"❌ Permission error: Cannot remove the {role_name} role.")
                except discord.HTTPException as e:
                    print(f"❌ HTTP error while removing role: {e}")


async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))




