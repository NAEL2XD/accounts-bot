def formatToTimeAgo(num:float) -> str:
	output = ""

	for timer, fmt, mod in [
		[60 * 60 * 24 * 7, "day", 31],
		[60 * 60 * 24, "day", 7],
		[60 * 60, "hour", 24],
		[60, "minute", 60],
		[1, "second", 60]]:
		if num > timer:
			oldn = num
			num = int(num / timer) % mod
			if num != 0:
				output += "%d %s%s, ".format(num, fmt, "s" if num != 1 else "")
			num = oldn

	return output[:-2] if output else "0 seconds"