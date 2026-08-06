# 🤖 Z 3 İ T T System Bot

An advanced, modern Discord bot fully built on Slash Commands (App Commands). Designed to make your server safer, more engaging, and interactive. It provides a wide range of services, from powerful moderation tools to a detailed economy system and dynamic voice/leveling features.

---

## ✨ Key Features

- **🛡️ Advanced Moderation:** Comprehensive server management, automated penalty systems (spam protection, etc.), quick role management, and bulk operations.
- **💰 Comprehensive Economy System:** Entertaining games of chance (Sweet Bonanza, Blackjack, Slots, etc.) and daily rewards where users can earn and spend their balance.
- **🎙️ Advanced Voice Systems:** Custom temporary voice rooms, tracking time spent in voice channels, and detailed voice leaderboards.
- **📈 Leveling System:** Users level up based on their chat activity and automatically earn roles upon reaching specific levels.
- **🛡️ Protection & Security:** Ad/link blocking, whitelist management, channel/role/webhook creation limits, and invite tracking.
- **💾 Backup:** Server layout backup capabilities.
- **⚡ Modern Architecture:** Built using the `discord.py` library, fully migrated to interactive slash commands.

---

## 🛠️ Commands and Usage

All commands in the system are categorized. Below is a list of all available Slash (`/`) commands:

### 🛡️ Moderation Commands (`/mod`)
Tools for server staff to maintain order in the server.
- `/mod ban <user> [reason]` : Bans the specified user from the server.
- `/mod kick <user> [reason]` : Kicks the specified user from the server.
- `/mod unban <user_id> [reason]` : Unbans the specified user.
- `/mod mute <user> <duration> [reason]` : Temporarily or permanently times out a user.
- `/mod unmute <user>` : Removes the timeout from a user.
- `/mod clear <amount>` : Deletes the specified number of messages in the channel.
- `/mod clearall` : Special mass-delete operation to clear the entire chat history.
- `/mod giverole <user> <role>` : Gives a role to the specified user.
- `/mod takerole <user> <role>` : Removes a role from the specified user.
- `/mod giveroleall <role>` : Gives the specified role to all eligible users in the server.

### 💰 Economy & Entertainment Commands (`/economy`)
Economy games for users to have fun and compete with each other.
- `/economy balance [user]` : Shows your or the specified user's current balance.
- `/economy daily` : Claim your daily balance reward.
- `/economy send <user> <amount>` : Transfer money to another user.
- `/economy rob <user>` : Attempt to steal from another user's balance.
- `/economy coinflip <amount>` : Play a coinflip game for a chance to double your bet.
- `/economy slot <amount>` : Classic slot machine game.
- `/economy sweetbonanza <amount>` : A fun spinning wheel and multiplier game.
- `/economy blackjack <amount>` : The popular card game (21) played against the dealer.
- `/economy allin` : Go all-in with your entire balance (All or nothing).

### 🎙️ Voice & Temporary Room Commands (`/voice`)
Tools for creating private voice channels and tracking statistics.
- `/voice join` : Logs/displays the status of the user in a voice channel.
- `/voice leave` : Handles operations when a user leaves a voice channel.
- `/voice time [user]` : Shows how much total time you have spent in voice channels.
- `/voice leaderboard` : Displays the leaderboard of users who spend the most time in voice channels.
- `/voice lock` : Locks your temporary voice room to prevent others from joining.
- `/voice unlock` : Unlocks your temporary voice room for everyone or a specific user.
- `/voice pull <user>` : Pulls the specified user into your current voice channel.

### 👑 Management & Admin Commands (`/admin`)
Bot settings and economy controls accessible only by high-level staff.
- `/admin whitelist <user>` : Adds a user to the whitelist, exempting them from security systems.
- `/admin whitelist_list` : Shows the users on the whitelist.
- `/admin addmoney <user> <amount>` : Creates unlimited balance and gives it to the specified person (Economy management).
- `/admin removemoney <user> <amount>` : Removes balance from the specified person.

### 📌 General & Single Commands
Statistics and information commands available to everyone.
- `/rank` : Shows your current level, experience points (XP), and progress.
- `/stats` : Lists the general statistics of the bot (server count, ping, uptime).
- `/profile [user]` : Displays the user's level, balance, and general bot statistics all together.
- `/owner` : Provides information about the bot's creator/owner.
- `/help` : Opens a detailed and interactive help menu.
- `/adminmenu` : Opens a special control panel with buttons designed for staff.

---

## ⚙️ Installation & Setup

1. **Requirements:** Ensure Python 3.9 or a newer version is installed.
2. **Libraries:** Enter the following command in the console to install the required modules:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configuration:** Enter your Discord Bot Token in the `TOKEN` variable inside `main.py` and configure the channel/category IDs for your server.
4. **Running:** 
   ```bash
   python main.py
   ```
   *When the bot is active, you will see a confirmation message in the console and the slash commands will be synced to Discord.*

---
*This bot is carefully developed and managed by [Z 3 İ T T System].*
