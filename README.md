# Snoo-per
 A discord.py and reddit api mashup named after Discord's own mascot, Snoo. Written in Python.
 
 Visit us on Discord and see Snoo-per in action!
 
 https://discord.gg/rqTVmdMBJX

# Installation and Setup

Set your environment variables or .env file up with the following details:

```
DISCORD_BOT_SECRET=makeme
BOT_DEFAULT_PREFIX=!
REDDIT_CLIENT_ID=makeme
REDDIT_CLIENT_SECRET=makemestronger
REDDIT_USER=makeme
REDDIT_PASS=makemestronger
```

DISCORD_BOT_SECRET: Make a Discord application here: https://discord.com/developers/applications/ , invite it to your server with permissions for posting and editing its own messages. It should have Bot scope with View Channels and Send Messages permissions. It does not require any other additional permissions but this may change over time. Make sure to get the key from the "Bot" tab, not the general information. See example of Discord Bot Permission settings below.

BOT_DEFAULT_PREFIX: Choose an available bot prefix for that works for your server. The default is assumed to be simply '!'

REDDIT_USER, REDDIT_PASS, REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET: You need to register a new reddit account and then an API key pair with that account in order to access the public reddit API. See here: (1) https://www.reddit.com/register/  (2) https://www.reddit.com/prefs/apps

Install Python to the host and upload the complete bot package.

Review requirements.txt and install as needed. Note Windows bot hosts need to move the comment hash over to re-include asyncio. Linux hosts should not install this as it will cause a conflict in the code that requires further troubleshooting.

```
pip install -r requirements.txt
python main.py
```

Follow bot commands within your Discord server to complete setup.

Typically the bot will be told to join at least 1 (or more) designated channels.

The bot can then be told to subscribe to specific subreddits and to check for updates (posts and comments) to those subreddits every time it updates. Following this it can be refinned to only match on specified terms. Use !help (with your chosen prefix) or !help command for more details.

# Supporting Docs:

Example of minimal Discord bot permissions needed:

![Minimum Bot Permissions](https://i.imgur.com/dp75WdF.png)

Get the correct API Key for Discord:

![Bot API Key Location](https://i.imgur.com/i7wsq7E.png)
