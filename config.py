import os


DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "your_default_token_here")

DATABASE_CONFIG = {
    "host": os.getenv("DB_HOST", "your_default_host"),
    "user": os.getenv("DB_USER", "your_default_user"),
    "password": os.getenv("DB_PASSWORD", "your_default_password"),
    "database": os.getenv("DB_NAME", "your_default_database"),
    "port": int(os.getenv("DB_PORT", 3306))  
}



