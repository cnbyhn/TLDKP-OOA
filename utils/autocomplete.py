import discord
import json
from utils.json_utils import load_items_from_json

BOSS_LIST = [
    "Grand Aelon", "Kowazan", "Nirma", "Morkus", "Minezerok", "Cornelius", "Junobote", "Excavator",
    "Ahzreil", "Talus", "Malakar", "Adentus", "Chernobog", "Aridus"
]

async def item_name_autocomplete(interaction: discord.Interaction, current: str):
    items = load_items_from_json()
    return [
        discord.app_commands.Choice(name=item, value=item)
        for item in items if current.lower() in item.lower()
    ][:25]

async def boss_autocomplete(interaction: discord.Interaction, current: str):
    return [
        discord.app_commands.Choice(name=boss, value=boss)
        for boss in BOSS_LIST if current.lower() in boss.lower()
    ][:25]
