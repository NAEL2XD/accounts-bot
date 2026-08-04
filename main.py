from glob import glob
from os.path import isfile
from os import listdir

blockedExts = [".jar", ".apk", "gradlew", ".ogg", ".fbc", ".png", ".ttf", ".xml", ".sb3", ".pyc", ".AppImage", ".wav"]
blockedDirs = [".gradle", "app/build", "luas", "SKINNERREMAKE", "__pycache__"]
with open("out.txt", "w") as g:
	for file in glob("**", recursive=True):
		bext = any(file.endswith(x) for x in blockedExts)
		bdir = any(file.startswith(f"{x}/") for x in blockedDirs)
		if file == "out.txt" or file == "z.py" or bext or bdir:
			if bext and not bdir:
				g.write(f"{file}: [HIDDEN]\n")
			continue

		print(file)
		if isfile(file):
			g.write(f"{file}:\n")
			with open(file, "r") as f:
				g.write(f"{f.read()}\n\n")
		else:
			g.write(f"{file} [DIRECTORY LIST]:\n")
			for direct in listdir(file):
				g.write(f"{direct}\n")
			g.write("\n")