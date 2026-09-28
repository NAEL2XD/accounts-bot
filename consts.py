from sys import argv

REPO_COMMIT_API = "https://api.github.com/repos/NAEL2XD/accounts-bot/commits"
MINIMUM_AGE = 14 * 24 * 60 * 60

COMMUNITY_IDS = [1208732034340487208, 1530349198879359026]
DEVELOPER_ID = 786639413282209802
GUILD_ID = 1036051546284249139
LOGS_ID = 1179012815479115786

ADMIN_ROLE = 1188212983940255824
MOD_ROLE = 1483900217945231481

RESTART_SCRIPT = f"""
#!/bin/bash

echo Removing data/help to update to newest.
rm -r data/help

echo Updating/Cloning the new repo and applying the new code to ours.
if [ -d ".tmp" ]; then
	cd .tmp
	git pull origin main
	cd ..
else
	git clone https://github.com/NAEL2XD/accounts-bot.git .tmp
fi

echo Cleaning Up
cp -rf ./.tmp/. .

echo Done
~/env/bin/python bot.py "{argv[1]}"
"""