# Account's *r*Bot

This repo is where Account's rBot functions, it is open source so users can see on how it works. It is designed to work for 2 servers, 1 for public and 1 for private.

# Features:

- Achievements.
- Auto-Updating from GIT.
- Automatic Upvote/Downvote on #COMMUNITY category, with forwarded message support.
- Custom Commands that uses Discord's built in `/` command.
- Honeypot Handling.
- Sticky Roles.
- Storage handling (Bomb counter, etc.)
- User's Account Age checking.

# Installation

Installing this is easy, as long as you have Python 3.12+, PIP and GIT, i'll assume you already have both of them.

If you want to run in developement mode, set the global env to this:
- `set D_TESTING=1` (Windows)
- `export D_TESTING=1` (Linux)
This will disable checking for commit updates and won't ruin some stuff.

1. Clone this repo `git clone https://github.com/NAEL2XD/accounts-rbot`
2. Go inside the repo `cd accounts-rbot`
3. Install the requirements `python3 -m pip install -r requirements.txt`
4. ! DO NOT SKIP THIS ! You'll need to set all the values at consts.py to make it work the same from your server.
5. You'll need to get your Bot Token, Search it up.
6. Run the bot: `python bot.py [BOT TOKEN HERE]`