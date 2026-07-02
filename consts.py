from sys import argv

REPO_COMMIT_API = "https://api.github.com/repos/NAEL2XD/accounts-bot/commits"
MINIMUM_AGE = 14 * 24 * 60 * 60

COMMUNITY_ID = 1208732034340487208
DEVELOPER_ID = 786639413282209802
GUILD_ID = 1036051546284249139
HONEYPOT_ID = 1511783751577768057
LOGS_ID = 1179012815479115786

ADMIN_ROLE = 1188212983940255824
BE_ROLE = 1475909457270804653
ELI_ROLE = 1473009251399110687
MOD_ROLE = 1483900217945231481
WDP_ROLE = 1505569438618091520

RESTART_SCRIPT = f"""
#!/bin/bash

# Delete our help folder due to updates in there.
rm -r data/help

# Git cloning handler...
if [ -d ".tmp" ]; then
	cd .tmp
	git pull origin main
	cd ..
else
	git clone https://github.com/NAEL2XD/accounts-bot.git .tmp
fi

# Finishing touches
cp -rf ./.tmp/. .
~/env/bin/python bot.py "{argv[1]}"
"""