import mysql.connector
import os

DATABASE_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "port": int(os.getenv("DB_PORT", 3306))
}

def init_db(guild_id):
    conn = mysql.connector.connect(**DATABASE_CONFIG)
    c = conn.cursor()
    members_table = f"members_{guild_id}"
    auctions_table = f"auctions_{guild_id}"

    c.execute(f"""CREATE TABLE IF NOT EXISTS {members_table} (
                    member_id BIGINT PRIMARY KEY,
                    guild_id BIGINT,
                    points INT DEFAULT 0,
                    last_loot DATETIME,
                    remaining_adjusted_points INT DEFAULT 0
                )""")
    c.execute(f"""CREATE TABLE IF NOT EXISTS {auctions_table} (
                    auction_id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    item_name VARCHAR(255),
                    color VARCHAR(50),
                    min_bid INT DEFAULT 10,
                    highest_bid INT DEFAULT 10,
                    highest_bidder BIGINT,
                    channel_id BIGINT,
                    guild_id BIGINT
                )""")
    conn.commit()
    conn.close()

