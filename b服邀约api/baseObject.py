import base64
import json
import random
import string
import time
import traceback
import uuid
from queue import Queue
from threading import Thread, Lock

from loguru import logger

import config
from baseConn import Conn
from thread_ import get_tasks, task_queue, sk5_queue, get_sk5

# 把后台任务线程设置为 daemon，避免主线程退出时被阻塞
Thread(target=get_tasks, daemon=True).start()
url = 'http://need1.dmdaili.com:7771/dmgetip.asp?apikey=9308a72e&pwd=6f556d52a7d7698aa818adb88e227bfe&getnum=200&httptype=1&geshi=0&fenge=1&fengefu=&operate=all'
Thread(target=get_sk5, args=(url,), daemon=True).start()

get_secret_queue = Queue()
get_secret_queue.put(1)
# using_secret_keys 在多线程下被并发修改，使用 Lock 保护
using_secret_keys = set()
using_secret_keys_lock = Lock()


class BindStatus:
	pending = '待邀请'
	processing = '邀请中'
	completed = '完成'
	failed = '失败'


class AccStatus:
	pending = 'pending'
	running = 'running'
	not_invited = 'not_invited'
	invited = 'invited'
	abnormality = 'abnormality'
	binding = 'binding'


def random_device_fp():
	return '38d813cfab1' + ''.join(random.choices(string.hexdigits, k=2)).lower()


class BaseObject:
	
	def __init__(self, info, proxy):
		super().__init__()
		self.email = info.get('username')
		self.id = info.get('id')
		self.uid = info.get('uid')
		self.header = {
			"Accept": "application/json, text/plain, */*",
			"Accept-Encoding": "gzip, deflate, br",
			"Accept-Language": "zh-cn,zh;q=0.9",
			"Connection": "keep-alive",
			"Content-Type": "application/json",
			"cookie": info.get('hkrpg_token'),
			"Host": "act-api-takumi.mihoyo.com",
			"Origin": "https://act.mihoyo.com",
			"Referer": "https://act.mihoyo.com/",
			"Sec-Fetch-Dest": "empty",
			"Sec-Fetch-Mode": "cors",
			"Sec-Fetch-Site": "same-site",
			"User-Agent": 'Mozilla/5.0 (Windows NT 6.1; Unity 3D; ZFBrowser 2.1.0; ??????? 3.7.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.0 Safari/537.36 miHoYo/hkrpg/prod_qd_cn/zh-cn/3.7.0',
			"sec-ch-ua": '"Chromium";v="100"',
			"sec-ch-ua-mobile": "?0",
			"sec-ch-ua-platform": '"Windows"',
			"x-rpc-device_fp": random_device_fp(),
			"x-rpc-device_id": str(uuid.uuid4()),
			"x-rpc-lang": "zh-cn",
			"x-rpc-platform": "4"
		}
		self.port1 = '8888'
		self.port2 = '8888'
		self.base_url = f'http://127.0.0.1'
		self.working = True
		self.proxy_ = proxy
		self.conn_no_proxy = Conn()
		self.test_proxy_times = 0
	
	def log(self, message):
		if self.working:
			logger.info(f'{self.email}  {message}')
	
	def warning(self, message):
		if self.working:
			logger.warning(f'{self.email}  {message}')
	
	def y_sleep(self, times):
		for i in range(times):
			try:
				if not self.working:
					break
				time.sleep(1)
			except:
				pass
	
	def init_proxy_conn(self):
		self.warning('初始化conn')
		# 若已存在旧连接，先尝试关闭再删除，避免未关闭的 socket/会话泄漏
		if hasattr(self, 'conn_by_proxy'):
			try:
				self.conn_by_proxy.close()
			except:
				pass
			try:
				del self.conn_by_proxy
			except:
				pass
		if config.get_sk5_enabled:
			self.conn_by_proxy = Conn(self.get_proxy())
		else:
			self.conn_by_proxy = Conn(self.proxy_)
	
	def get_proxy(self):
		while self.working:
			sk5, end_time = sk5_queue.get()
			if int(time.time()) >= end_time - 10:
				continue
			if sk5 not in ['None', None, '']:
				if '|' in sk5:
					base_str = '|'
				elif '/' in sk5:
					base_str = '/'
				else:
					base_str = ':'
				lst = sk5.replace('\n', '').split(base_str)
				return f'{lst[0]}:{lst[1]}'
	
	def conn_request(self, method, path, payload=None, timeout=4):
		res = None
		try:
			res = self.conn_by_proxy.request(method, path, payload, timeout)
		finally:
			try:
				res.close()
			except:
				pass
		return res
	
	def conn_request_no_proxy(self, method, path, payload=None):
		res = None
		try:
			res = self.conn_no_proxy.request(method, path, payload)
		finally:
			try:
				res.close()
			except:
				pass
		return res
	
	@staticmethod
	def json_loads_jwt(jwt_str):
		header_b64, payload_b64, signature_b64 = jwt_str.split(".")
		
		def b64_decode(data):
			# 修复 padding
			rem = len(data) % 4
			if rem > 0:
				data += "=" * (4 - rem)
			return base64.urlsafe_b64decode(data)
		
		return json.loads(b64_decode(payload_b64))
	
	def return_jwt_exp(self, jwt_str):
		return self.json_loads_jwt(jwt_str).get('exp')
	
	def close(self):
		if hasattr(self, 'conn_by_proxy'):
			self.conn_by_proxy.close()
		if hasattr(self, 'conn_no_proxy'):
			self.conn_no_proxy.close()
		self.working = False
	
	def test_proxy(self):
		while self.working:
			try:
				# res = self.conn_request('GET', 'https://ip234.in/ip.json')
				res = self.conn_request('GET', 'https://baidu.com/', timeout=4)
				if res is not None:
					# print(res.text)
					# self.log(res.json().get('ip'))
					break
				else:
					self.init_proxy_conn()
			except:
				e = traceback.format_exc()
				pass
			self.y_sleep(2)


class BindObj(BaseObject):
	
	def __init__(self, info, proxy):
		super().__init__(info, proxy)
		self.conn_no_proxy.set_headers('cookie',
		                               'admin_session=MTc2MjM3NTk5N3xEWDhFQVFMX2dBQUJFQUVRQUFCSl80QUFBZ1p6ZEhKcGJtY01DZ0FJWVdSdGFXNWZhV1FFZFdsdWRBWUNBQUVHYzNSeWFXNW5EQkFBRG1Ga2JXbHVYM1Z6WlhKdVlXMWxCbk4wY21sdVp3d0hBQVZoWkcxcGJnPT18bRfFAMvfIULpecpdR7iomitQFvjVU78rUbFIV3ZbDss=')
		self.log('线程启动')
	
	def change_order_status(self, secret_key, status):
		path = f'http://115.190.5.154:8888/api/tasks/{secret_key}/update/{status}'
		method = 'GET'
		while self.working:
			try:
				res = self.conn_request_no_proxy(method, path)
				if res.status_code == 200:
					return True
				elif res.status_code == 404 and 'Task not found for the given secret key' in res.text:
					return False
			except:
				pass
			self.y_sleep(2)
	
	def api_update_account(self, acc_id, status, invite_code=None):
		# 更新账号
		update_data = {"invite_status": status}
		if invite_code:
			update_data['invite_code'] = invite_code
		while self.working:
			try:
				res = self.conn_no_proxy.conn.post(f"{self.base_url}:{self.port1}/api/accounts/{acc_id}",
				                                   json=update_data)
				if res.status_code == 200:
					self.log(f'api更新账号状态为{status}')
					break
			except:
				pass
			self.y_sleep(2)
	
	def local_update_account(self, acc_id, status, invite_code=None):
		# 本地更新账号
		config.db.update_account_row(acc_id, status, invite_code)
		self.log(f'本地更新账号状态为{status}')
	
	@staticmethod
	def db_del_order(secret_key):
		config.db.delete_order(secret_key)
		with using_secret_keys_lock:
			if secret_key in using_secret_keys:
				using_secret_keys.remove(secret_key)
	
	def run_task(self):
		while self.working:
			try:
				get_secret_queue.get()
				with using_secret_keys_lock:
					info = config.db.get_secret_key(set(using_secret_keys))
				get_secret_queue.put(1)
				update_db = True
				if info:
					secret_key, invite_code, invite_num = info
					update_db = False
				else:
					self.log('等待订单...')
					invite_code, secret_key, invite_num = task_queue.get()
				with using_secret_keys_lock:
					using_secret_keys.add(secret_key)
				self.log(f'获取到订单  邀请码：{invite_code} 数量：{invite_num} 卡密：{secret_key}')
				if update_db:
					config.db.update_order(secret_key, invite_code, invite_num)
				ret = self.change_order_status(secret_key, BindStatus.processing)
				if ret:
					while self.working:
						self.init_proxy_conn()
						self.test_proxy()
						self.conn_by_proxy.conn.headers = self.header
						ret = self.invite_b(invite_code)
						using_secret_keys.remove(secret_key)
						self.conn_by_proxy.pop_headers('cookie')
						if ret == 0:
							return ret
						elif ret == 1:
							return ret
						elif ret == 2:
							self.db_del_order(secret_key)
							with open(config.error_order_file, 'a', encoding='utf8') as _f:
								_f.write(f'{secret_key}----{ret}\n')
							self.change_order_status(secret_key, BindStatus.failed)
							config.FAILED_ORDERS += 1
							self.log('订单异常')
							return 0
						elif ret == 3:
							invite_num -= 1
							if invite_num <= 0:
								self.db_del_order(secret_key)
								self.change_order_status(secret_key, BindStatus.completed)
								config.COMPLETED_ORDERS += 1
								self.log('订单完成')
							else:
								config.db.update_order(secret_key, invite_code, invite_num)
							return 1
						elif ret == 4:
							self.db_del_order(secret_key)
							self.change_order_status(secret_key, BindStatus.completed)
							self.log('订单完成')
							config.COMPLETED_ORDERS += 1
							return 0
			except:
				e = traceback.print_exc()
				pass
	
	def get_game_uid(self):
		path = 'https://passport-api.mihoyo.com/binding/api/getUserGameRolesByCookieToken?game_biz=hkrpg_cn'
		method = 'GET'
		while self.working:
			try:
				res = self.conn_request(method, path)
				if res.status_code == 200 and 'nickname' in res.text:
					self.game_uid = res.json().get('data').get('list')[0].get('game_uid')
					break
			except:
				pass
	
	def login(self):
		path = 'https://api-takumi.mihoyo.com/common/badge/v1/login/account'
		method = 'POST'
		while self.working:
			try:
				data = {
					"game_biz": "hkrpg_cn",
					"lang": "zh-cn",
					"region": "prod_gf_cn",
					"uid": self.game_uid
				}
				res = self.conn_request(method, path, data)
				if res.status_code == 200 and 'region_name' in res.text:
					break
			except:
				pass
	
	def invite_b(self, invite_code, check=False):
		# b服绑定
		"""
		Cookie:
		mi18nLang=zh-cn;
		_MHYUUID=14a75ca8-dc93-45bb-9072-9d56d2558718;
		DEVICEFP_SEED_ID=947a62df0b6f0711;
		DEVICEFP_SEED_TIME=1762524708513;
		DEVICEFP=38d81386cb5f2;
		e_hkrpg_token=cprj5A+v/zRjusg4unN9MDXVU4fB5lZSLhpb9nOeyeoV3diU3+Ezyp95x0a9eXBG;
		SERVERID=5d0f1927e414431d50d24629073ab580|1762525055|1762524840;
		SERVERCORSID=5d0f1927e414431d50d24629073ab580|1762525055|1762524840
		"""
		path = f'https://act-api-takumi.mihoyo.com/event/return/bind/3.7?isBili=1&game_biz=hkrpg_cn&mode=fullscreen&win_mode=fullscreen&sign_type=2&auth_appid=return37&authkey_ver=1&utm_source=op&utm_medium=gamepanel&lang=zh-cn&plat_type=pc&os_system=Windows+10++(10.0.19044)+64bit&device_model=Unknown+(HUANANZHI)&badge_uid={self.uid}&badge_region=prod_qd_cn&source=4'
		method = 'POST'
		times = 0
		while self.working:
			if times >= 5:
				self.log('绑定超过5次')
				# 继续
				return 0
			try:
				data = {"invite_code": invite_code, "check": check}
				res = self.conn_request(method, path, data)
				if res is None:
					times += 1
					continue
				if res.status_code == 200:
					message = res.json().get('message')
					if message == 'OK':
						self.log(f'邀约成功')
						self.local_update_account(self.id, AccStatus.invited, invite_code)
						# 换号
						return 3
					elif message == '该邀请码绑定人数已达上限':
						# 换订单 订单完成
						return 4
					self.log(f'message:{message}')
					if '邀请码错误' in message:
						# 换订单
						return 2
					elif '请先登录后参与活动' in message:
						# 继续
						return 0
					elif '已经绑定过邀请码' in message:
						self.local_update_account(self.id, AccStatus.invited)
						# 换号
						return 1
					else:
						# 继续
						return 0
				else:
					print(res.status_code, res.text)
					times += 1
			except:
				pass
			self.y_sleep(2)


if __name__ == '__main__':
	info_ = {
		# 'key': '2cc06e1b84abb98ca075e759c84c788903f5230dc98ce652624d8964463acd09',
		'key': 'ba72d50970a7e24e7f2074f77279dde9664edacce85bb7393154de11b94e9b1b',
		# 'sk5': 'eu.9674ce61a61a20cc.abcproxy.vip|4950|abc9778188_sypb-zone-abc|72248743',
	}
	for i in range(1):
		obj = BindObj(1, '192.168.1.21', '075644:321d6b@48224119.sd.proxy.xiequ.cn:2829', 0)
		obj.conn_by_proxy = Conn()
		obj.get_account()
