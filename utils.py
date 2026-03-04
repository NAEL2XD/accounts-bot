import os
import requests

def formatToTimeAgo(num:float) -> str:
	output = ""

	for timer, fmt, mod in [
		[60 * 60 * 24 * 7, "week", 31],
		[60 * 60 * 24, "day", 7],
		[60 * 60, "hour", 24],
		[60, "minute", 60],
		[1, "second", 60]]:
		if num > timer:
			oldn = num
			num = int(num / timer) % mod
			if num != 0:
				output += f"{num} {fmt}{"s" if num != 1 else ""}, "
			num = oldn

	return output[:-2] if output else "0 seconds"

def getCommit() -> str:
	r = requests.get("https://api.github.com/repos/NAEL2XD/accounts-bot/commits")

	try:
		r.raise_for_status()
	except requests.HTTPError:
		return ""

	return r.json()[0]["sha"]

def emptyFile(file:str):
	f = f"data/{file}"
	if not os.path.exists(f):
		open(f"data/{file}", "w").close() # same as doing this command: "touch data/{file}"