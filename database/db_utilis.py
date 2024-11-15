import mysql.connector
from datetime import datetime, timezone
from config import DATABASE_CONFIG

def calculate_adjusted_points(guild_id, member_id):
    conn = mysql.connector.connect(**DATABASE_CONFIG)
    c = conn.cursor()
    table_name = f"members_{guild_id}"
    c.execute(f"SELECT points, last_loot FROM {table_name} WHERE member_id = %s", (member_id,))
    result = c.fetchone()
    conn.close()

    if not result:
        return 0

    points, last_loot = result
    last_loot_date = last_loot.date() if last_loot else datetime.now(timezone.utc).date()
    current_date = datetime.now(timezone.utc).date()

    days_difference = (current_date - last_loot_date).days
    weeks_missed = max(0, days_difference // 7)
    adjusted_points = points * (1 + ((weeks_missed - 1) * 0.5)) if weeks_missed >= 2 else points
    return adjusted_points
