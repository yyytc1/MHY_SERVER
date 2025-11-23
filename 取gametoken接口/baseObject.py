import time
import traceback
from threading import Thread

import cloudscraper
from loguru import logger

from thread_ import sk5_queue, get_sk5
from strFunc import rsa_encrypt, random_device_fp, random_uuid

url = 'http://need1.dmdaili.com:7771/dmgetip.asp?apikey=9308a72e&pwd=6f556d52a7d7698aa818adb88e227bfe&getnum=200&httptype=1&geshi=0&fenge=1&fengefu=&operate=all'
Thread(target=get_sk5, args=(url,), daemon=True).start()


class BaseObject:
	
	def __init__(self, info):
		super().__init__()
		self.email = info.get('account')
		self.password = info.get('password')
		self.uid = info.get('uid')
		self.mid = info.get('mid')
		self.game_token = info.get('game_token')
		self.cookie_token = info.get('cookie_token')
		self.working = True
	
	def log(self, message):
		if self.working:
			logger.info(f'{self.email}  {message}')
	
	def y_sleep(self, times):
		for i in range(times):
			try:
				if not self.working:
					break
				time.sleep(1)
			except:
				pass
	
	def init_proxy_conn(self):
		if hasattr(self, 'conn_by_proxy'):
			try:
				self.conn_by_proxy.close()
			except:
				pass
			try:
				del self.conn_by_proxy
			except:
				pass
		self.conn_by_proxy = cloudscraper.create_scraper()
		self.conn_by_proxy.trust_env = False
		self.conn_by_proxy.proxies = {
			"http": f"http://{self.get_proxy()}",
			"https": f"http://{self.get_proxy()}"
		}
	
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
	
	def conn_request(self, method, path, timeout=10, *args, **kwargs):
		res = None
		try:
			res = self.conn_by_proxy.request(method, path, timeout=timeout, *args, **kwargs)
		finally:
			try:
				res.close()
			except:
				pass
		return res
	
	def close(self):
		if hasattr(self, 'conn_by_proxy'):
			self.conn_by_proxy.close()
		self.working = False


class MHYObj(BaseObject):
	
	def __init__(self, info):
		super().__init__(info)
	
	def passport_web_login(self):
		# 通行证登录
		path = 'https://passport-api.mihoyo.com/account/ma-cn-passport/web/loginByPassword'
		method = "POST"
		times = 0
		while self.working:
			try:
				headers = {
					"Accept": "application/json, text/plain, */*",
					"Accept-Language": "zh-CN,zh;q=0.9",
					"Connection": "keep-alive",
					"Content-Type": "application/json",
					"Host": "passport-api.mihoyo.com",
					"Origin": "https://user.mihoyo.com",
					"Referer": "https://user.mihoyo.com/",
					"x-rpc-app_id": "dw9y09jqjpxc",
					"x-rpc-client_type": "4",
					"x-rpc-device_fp": random_device_fp(),
					"x-rpc-device_id": random_uuid(),
					"x-rpc-game_biz": "plat_cn",
					"x-rpc-source": "v2.webLogin"
				}
				data = {
					'account': rsa_encrypt(self.email),
					'password': rsa_encrypt(self.password),
				}
				res = self.conn_request(method, path, json=data, headers=headers, timeout=5)
				if res.status_code == 200:
					if '风险' in res.text:
						return True
					elif '密码错误' in res.text:
						return False
					else:
						times += 1
				else:
					times += 1
				if times >= 5:
					return None
			except:
				self.init_proxy_conn()
				pass
			self.y_sleep(2)
	
	def run_task(self):
		self.init_proxy_conn()
		if self.game_token:
			return self.get_stoken_by_game_token()
		else:
			return self.get_stoken_by_cookie_token()
	
	def get_stoken_by_game_token(self):
		path = 'https://api-takumi.mihoyo.com/account/ma-cn-session/app/getTokenByGameToken'
		method = 'POST'
		times = 0
		data = {
			"account_id": self.uid,
			"game_token": self.game_token
		}
		while self.working:
			try:
				headers = {'x-rpc-app_id': 'c90mr1bwo2rk'}
				res = self.conn_request(method, path, json=data, headers=headers, timeout=5)
				if res.status_code == 200:
					if 'token' in res.text:
						data = res.json()['data']
						return {
							'stoken': data['token']['token'],
							'mid': data['user_info']['mid'],
						}
					elif '登录状态失效' in res.text:
						return '登录状态失效'
					else:
						times += 1
				else:
					times += 1
				if times >= 5:
					return '获取stoken超时，请重试'
			except:
				self.init_proxy_conn()
				pass
			self.y_sleep(2)
	
	def get_stoken_by_cookie_token(self):
		path = 'https://passport-api.mihoyo.com/account/ma-cn-session/web/webVerifyForGame'
		method = 'POST'
		times = 0
		headers = {
			'x-rpc-app_id': 'c90mr1bwo2rk',
			'cookie': f'account_id_v2={self.uid};account_mid_v2={self.mid};cookie_token_v2={self.cookie_token}'
		}
		while self.working:
			try:
				res = self.conn_request(method, path, headers=headers, timeout=5)
				if res.status_code == 200:
					if 'token' in res.text:
						data = res.json()['data']
						return {
							'stoken': data['token']['token'],
							'mid': data['user_info']['mid'],
						}
					elif '登录状态失效' in res.text:
						return '登录状态失效'
					else:
						times += 1
				else:
					times += 1
				if times >= 5:
					return '获取stoken超时，请重试'
			except:
				self.init_proxy_conn()
				pass
			self.y_sleep(2)
	

if __name__ == '__main__':
	info_ = {
		"account": 'pnmv76451263@163.com',
		'game_token': 'v2_Tg804PSzqkTacJjstnl68H_-093T_2kxq38MzM-jb7GQCWBcQV4MHyPNSuX5BeQjp3tyBmVXdi5tCdlFUaHDTQ1hBtiLPWkoGr62TXOyXJl25TBvlSVb_yChqMQsFRUwNPk5HP5p4s5v-zbFQ6mCysZCQ7_M-n6nxaq8NWciCCokdA==.CAE=',
		'uid': 443882447,
	}
	mhy = MHYObj(info_)
	a = mhy.run_task()
	print(a)
