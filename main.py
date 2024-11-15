import os
import discord
from discord.ext import commands
from server.keep_alive import keep_alive  
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  
bot = commands.Bot(command_prefix="!", intents=intents)

async def load_cogs():
    for cog in ["auction_commands", "points_commands", "guild_management", "raid_commands", "timers", "reaction_roles", "sync_commands", "welcome_new_member"]:
        try:
            await bot.load_extension(f"cogs.{cog}")
            print(f"Loaded cog: {cog}")
        except Exception as e:
            print(f"Failed to load cog {cog}: {e}")

@bot.event
async def on_ready():
    print(f"Bot {bot.user} is ready!")
    try:
        await bot.tree.sync()  
        print("✅ Commands have been globally synced.")
    except Exception as e:
        print(f"❌ Error syncing commands: {e}")

async def main():
    
    keep_alive()  
    
    
    await load_cogs()
    
    
    TOKEN = os.getenv("DISCORD_BOT_TOKEN")
    await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
