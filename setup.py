import subprocess
import sys

def install(package):
	try:
		subprocess.call([sys.executable, "-m", "pip", "install", "-U", package, "--user"])
	except:
		subprocess.call([sys.executable, "-m", "pip", "install", "-U", package])

install("pip")
install("discord.py")
install("tinydb")
install("pysqlite3")
