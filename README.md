TLDKP Discord Bot

A custom Discord bot for managing a guild DKP (Dragon Kill Points) system in Throne and Liberty, enhancing guild activities like raids, auctions, and participation tracking. This bot uses MySQL for data storage, allowing persistent and automated management of guild reputation points.
Features

    Automated Auctions: Run auctions with reputation points for items, including point-based bidding and winner announcements.
    Point Management: Track, set, and adjust member points based on participation.
    Event Announcements: Schedule and announce raids or events with role tagging.
    Raid Polls: Create polls to vote on raid bosses for upcoming guild activities.

Setup

    Clone the repository:

git clone https://github.com/username/TLDKP-discord-bot.git
cd TLDKP-discord-bot

Install dependencies:

pip install -r requirements.txt

Configure environment variables:

    Set up your MySQL database and update DATABASE_CONFIG in the code.
    Set the DISCORD_BOT_TOKEN environment variable with your Discord bot token.

Run the bot:

    python main.py

Usage

    /start_auction: Begin an auction for multiple items.
    /end_auction: Close all active auctions and declare winners.
    /set_points: Manually set or adjust points for a member.
    /announce_raid: Announce a raid with time and role tagging.
    /raid_poll: Start a poll for raid boss selection.

License

This project is licensed under the MIT License.
