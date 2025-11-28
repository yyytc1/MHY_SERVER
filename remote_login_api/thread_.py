# coding : utf-8
# @Time : 2025/11/6 7:16 
# @Author : Adolph
# @File : proxy_pool.py
# @Software : PyCharm
import json
import queue
import time
from datetime import datetime

import requests

from baseConn import Conn

# 限制 sk5_queue 大小，避免在异常或生产速度过快时内存无限增长
sk5_queue = queue.Queue()


def contains(q, item):
	with q.mutex:
		return item in q.queue  # q.queue 是底层 deque


def get_sk5(path):
	# path = 'http://need1.dmdaili.com:7771/dmgetip.asp%EF%BC%9Fapikey=9308a72e&pwd=6f556d52a7d7698aa818adb88e227bfe&getnum=10&httptype=1&geshi=1&fenge=1&fengefu=&operate=all'
	while 1:
		try:
			if sk5_queue.qsize() > 0:
				time.sleep(1)
			else:
				res = requests.get(path)
				res.close()
				if res.status_code == 200:
					data = res.text
					if 'data' in data:
						for i in json.loads(data)['data']:
							ts = int(datetime.strptime(i['endtime'], "%Y/%m/%d %H:%M:%S").timestamp())
							sk5_queue.put([f'{i["ip"]}:{i["port"]}', ts])
					else:
						now = int(time.time()) + 30
						for i in res.text.split('\r\n'):
							if not i:
								continue
							sk5_queue.put([i, now])
		except:
			pass


if __name__ == '__main__':
	# Thread(target=get_tasks).start()
	# for asd in range(100):
	# 	print(task_queue.get())
	get_sk5('')
