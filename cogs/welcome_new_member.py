import discord
from discord.ext import commands

class WelcomeNewMember(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        
        welcome_channel = discord.utils.get(guild.text_channels, name="welcome")

        if welcome_channel is None:
            welcome_channel = await guild.create_text_channel("welcome")
            await welcome_channel.send("👋 Welcome channel created! This channel will greet all new members.")

        channel_message = (
            f"Welcome to the **OutOfAnger** Discord server, {member.mention}! 🎉\n\n"
            "Please reach out to one of our **@LEADER** team members and provide your in-game name so they can assign you the appropriate role. "
            "We're excited to have you here and hope you enjoy your time with us!"
        )

        dm_message = (
            f"Hi {member.name}, welcome to the **OutOfAnger** Discord server! 🎉\n\n"
            "We're thrilled to have you join our community. Please reach out to one of our **@Leader** members in the server and let them know your in-game name. "
            "They'll help set you up with the right role.\n\n"
            "Feel free to explore the channels, connect with other members, and let us know if you have any questions. Enjoy your stay, and welcome aboard! 🌟"
        )

        if welcome_channel:
            await welcome_channel.send(channel_message)

        try:
            await member.send(dm_message)
        except discord.Forbidden:
            pass

async def setup(bot):
    await bot.add_cog(WelcomeNewMember(bot))

