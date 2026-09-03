# Z3ITT System Bot

All-in-one Discord server bot built on slash commands. Moderation, economy minigames, temporary voice rooms, leveling, security filters, and backup tools in a single codebase.

| | |
|---|---|
| **Language** | Python |
| **Commands** | Slash (`/`) only |
| **Entry point** | `main.py` |

## Highlights

- Moderation: ban, kick, mute, purge, role tools
- Economy: daily rewards, transfers, coinflip, slots, Sweet Bonanza, blackjack
- Voice: temp rooms, time tracking, leaderboards, lock/unlock, pull
- Leveling with XP and automatic role rewards
- Security: ad blocking, whitelist, invite and creation limits
- Server layout backup

## Getting started

```bash
git clone https://github.com/z3itt/z3itt-system-global.git
cd z3itt-system-global
pip install -r requirements.txt
```

Set your bot token and guild channel/category IDs in `main.py`, then:

```bash
python main.py
```

Slash commands sync when the bot starts.

## Command groups

### `/mod`
Ban, kick, unban, mute, unmute, clear messages, give/remove roles, mass role assign.

### `/economy`
Balance, daily, send, rob, coinflip, slot, sweetbonanza, blackjack.

### `/voice`
Join/leave logging, voice time, leaderboard, lock, unlock, pull user.

### `/admin`
Whitelist management, add/remove balance.

### General
`/rank`, `/stats`, `/profile`, `/owner`, `/help`, `/adminmenu`

## Contact

- **Author:** [z3itt](https://github.com/z3itt)
- **Website:** https://bot.z3itt.com/
- **Email:** info@z3itt.com
