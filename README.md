# Massacre Card Game Discord Bot

A Discord bot that runs a two-player implementation of the card game Massacre through commands and private-message embeds.

## How it works

The bot maintains one active game in memory. It builds a standard card deck plus jokers, deals each player hidden, shown, and hand cards, determines turns, validates plays, handles pile burns and pickups, and updates each player's private embed view. Players can accept invitations, prepare their layout during intermission, play the game, leave, and opt into a rematch.

The command prefix is `!`. The source includes aliases and usage feedback for actions such as inviting a player, swapping cards, picking up the pile, becoming ready, and cancelling.

## Setup

This project uses the older `discord.py 1.7.3` API listed in `requirements.txt`.

```bash
python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set:

```dotenv
DISCORD_TOKEN=your_bot_token
DISCORD_STREAMING_URL=https://example.com
DISCORD_OWNER_ID=your_numeric_discord_user_id
```

Enable the intents required by this older command-based bot in the Discord developer portal, invite the bot to a test server, and run:

```bash
python massacre_game_discord_bot.py
```

## Limitations

- Game state is stored only in memory and is lost when the process restarts.
- The implementation supports a single shared game rather than independent games per server/channel.
- `discord.py 1.7.3` is legacy software; migration may be required for current Discord API behaviour.
- Never commit the populated `.env` file or bot token.
