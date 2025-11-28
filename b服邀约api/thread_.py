# coding : utf-8
# @Time : 2025/11/6 7:16 
# @Author : Adolph
# @File : proxy_pool.py
# @Software : PyCharm
import json
import queue
import time
from datetime import datetime

from baseConn import Conn

# 限制队列长度，防止生产速度过快导致内存无限增长
task_queue = queue.Queue()
sk5_queue = queue.Queue()

session = Conn()
session.set_headers('cookie',
                    'admin_session=MTc2MjM3NTk5N3xEWDhFQVFMX2dBQUJFQUVRQUFCSl80QUFBZ1p6ZEhKcGJtY01DZ0FJWVdSdGFXNWZhV1FFZFdsdWRBWUNBQUVHYzNSeWFXNW5EQkFBRG1Ga2JXbHVYM1Z6WlhKdVlXMWxCbk4wY21sdVp3d0hBQVZoWkcxcGJnPT18bRfFAMvfIULpecpdR7iomitQFvjVU78rUbFIV3ZbDss=')


def contains(q, item):
	with q.mutex:
		return item in q.queue  # q.queue 是底层 deque


def get_tasks():
	path = 'http://115.190.5.154:8888/admin/tasks?page=1&pageSize=50&status=%E5%BE%85%E9%82%80%E8%AF%B7'
	while 1:
		try:
			if task_queue.qsize() > 0:
				time.sleep(1)
			else:
				res = session.conn.get(path)
				if res.status_code == 200:
					json_data = res.json()['data']
					for i in json_data:
						if 'secret_key' in i and 'invite_code' in i and i.get('status') == '待邀请':
							info = [i.get('invite_code'), i.get('secret_key'), i.get('invite_count')]
							if not contains(task_queue, info):
								task_queue.put(info)
					if not json_data:
						time.sleep(30)
		except:
			pass


def get_sk5(path):
	# path = 'http://need1.dmdaili.com:7771/dmgetip.asp%EF%BC%9Fapikey=9308a72e&pwd=6f556d52a7d7698aa818adb88e227bfe&getnum=10&httptype=1&geshi=1&fenge=1&fengefu=&operate=all'
	while 1:
		try:
			if sk5_queue.qsize() > 0:
				# if int(time.time()) - last_time >= 60:
				# 	while 1:
				# 		if sk5_queue.qsize() > 0:
				# 			sk5_queue.get()
				# 		else:
				# 			break
				time.sleep(1)
			else:
				res = session.conn.get(path)
				if res.status_code == 200:
					data = res.text
					if 'data' in data:
						for i in json.loads(data)['data']:
							ts = datetime.strptime(i['endtime'], "%Y/%m/%d %H:%M:%S").timestamp()
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
