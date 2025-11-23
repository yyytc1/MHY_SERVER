import datetime
import random
import subprocess

from loguru import logger


def now():
	return str(datetime.datetime.now())[:-3]


def log(msg):
	logger.info(msg)


def check_port():
	while 1:
		try:
			port = random.randint(10000, 65535)
			ret, err = subprocess.Popen('netstat -ano', shell=True, stdout=subprocess.PIPE).communicate()
			text = ret.decode('gbk')
			if f'127.0.0.1:{port}' not in text:
				return port
		except:
			pass
