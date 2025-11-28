# coding : utf-8
# @Time : 2025/11/28 21:47 
# @Author : Adolph
# @File : task.py 
# @Software : PyCharm
import queue
from threading import Thread


from baseObject import MHYObj
from get_token.config import THREAD_NUM


task_queue = queue.Queue()


def task_thread(index):
	print(f'做单线程{index} 启动')
	while True:
		try:
			data = task_queue.get()
			mhy = MHYObj(data)
			p_type = data['p_type']
			mhy.log(f'开始任务，任务类型：{p_type}')
			if p_type == 2:
				ret = mhy.web_login()
				order_ret = {
					'user': mhy.email,
					'pwd': mhy.password,
					'card_id': data['card_id'],
				}
				if isinstance(ret, dict):
					info = f'{ret["uid"]}|{ret["mid"]}|{ret["cookie_token"]}'
				else:
					info = ret
				mhy.log(info)
				order_ret['info'] = info
			else:
				order_ret = f'不支持的任务类型：{p_type}'
			mhy.upload_order(order_ret)
			mhy.close()
			del data, mhy, p_type, ret, order_ret, info
		except:
			try:
				mhy.close()
			except:
				pass


def run_task():
	for i in range(THREAD_NUM):
		Thread(target=task_thread, args=(i+1,), daemon=True).start()


if __name__ == '__main__':
	run_task()
