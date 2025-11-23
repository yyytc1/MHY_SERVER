# coding : utf-8
# @Time : 2025/11/6 7:16 
# @Author : Adolph
# @File : thread_.py 
# @Software : PyCharm
import json
import queue
import time
from datetime import datetime

import requests

sk5_queue = queue.Queue()

session = requests.Session()


def contains(q, item):
	with q.mutex:
		return item in q.queue


def get_sk5(path):
	while 1:
		try:
			if sk5_queue.qsize() > 0:
				time.sleep(1)
			else:
				res = session.get(path)
				if res.status_code == 200:
					data = res.text
					if 'data' in data:
						for i in json.loads(data)['data']:
							ts = datetime.strptime(i['endtime'], "%Y/%m/%d %H:%M:%S").timestamp()
							sk5_queue.put([f'{i["ip"]}:{i["port"]}', ts])
					else:
						now = int(time.time()) + 60
						for i in res.text.split('\r\n'):
							if not i:
								continue
							sk5_queue.put([i, now])
		except:
			pass


if __name__ == '__main__':
	get_sk5('')
