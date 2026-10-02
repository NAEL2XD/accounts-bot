from sys import argv

MINIMUM_AGE = 14 * 24 * 60 * 60

COMMUNITY_IDS = [1208732034340487208, 1530349198879359026]
GUILD_ID = 1036051546284249139

RESTART_SCRIPT = f"""
#!/bin/bash

rm -r data/help

if [ -d ".tmp" ]; then
	cd .tmp
	git pull origin main
	cd ..
else
	git clone https://github.com/NAEL2XD/accounts-bot.git .tmp
fi

cp -rf ./.tmp/. .
~/env/bin/python -m pip install -r requirements.txt
~/env/bin/python bot.py "{argv[1]}"
"""