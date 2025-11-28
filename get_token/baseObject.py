import time
from threading import Thread

import cloudscraper
from loguru import logger

from config import REDIS, REMOTE_UPLOAD_URL
from proxy_pool import sk5_queue, get_sk5
from base_func import rsa_encrypt, random_device_fp, random_uuid

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
		self.conn_by_proxy = cloudscraper.create_scraper()
		self.conn_no_proxy = cloudscraper.create_scraper()
		self.change_proxy()
	
	def change_proxy(self):
		proxy = self.get_proxy()
		self.conn_by_proxy.proxies = {
			"http": f"http://{proxy}",
			"https": f"http://{proxy}"
		}
	
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
		if hasattr(self, 'conn_no_proxy'):
			self.conn_no_proxy.close()
		self.working = False


class MHYObj(BaseObject):
	
	def __init__(self, info):
		super().__init__(info)
		
	def web_login(self):
		path = 'https://passport-api.mihoyo.com/account/ma-cn-passport/web/loginByPassword'
		times = 0
		while self.working:
			try:
				headers = {
					"x-rpc-app_id": "ess4np01pji8",
					"x-rpc-client_type": "4",
					"x-rpc-device_fp": random_device_fp(),
					"x-rpc-device_id": random_uuid(),
					"x-rpc-game_biz": "abc_cn",
					"x-rpc-mi_referrer": "https://user.mihoyo.com/login-platform/index.html?app_id=ess4np01pji8&theme=abc&token_type=4&game_biz=abc_cn&fs_ql_w=0&fs_ql_m=0&message_origin=https%253A%252F%252Fyyjl.mihoyo.com&succ_back_type=message%253Alogin-platform%253Alogin-success&fail_back_type=message%253Alogin-platform%253Alogin-fail&ux_mode=popup&iframe_level=1#/login/password",
					"x-rpc-sdk_version": "2.44.0",
					"x-rpc-source": "v2.webLogin"
				}
				data = {
					'account': rsa_encrypt(self.email),
					'password': rsa_encrypt(self.password),
				}
				res = self.conn_request("POST", path, json=data, headers=headers)
				if res.status_code == 200 and 'message' in res.json():
					message = res.json()['message']
					if message == 'OK':
						user_info = res.json()['data']['user_info']
						uid = user_info['aid']
						mid = user_info['mid']
						cookie_token = self.conn_by_proxy.cookies.get_dict()['cookie_token_v2']
						REDIS.hset(f"1:cookieToken", f'{self.email}----{self.password}', f'{uid}----{mid}----{cookie_token}')
						return {
							'uid': uid,
							'mid': mid,
							'cookie_token': cookie_token,
						}
					elif '账号或密码错误' in message or '账号格式错误' in message:
						return message
				else:
					times += 1
				if times >= 10:
					return '登录超时'
			except:
				pass
			self.y_sleep(2)
			self.change_proxy()
	
	def upload_order(self, data):
		while True:
			try:
				res = self.conn_no_proxy.post(REMOTE_UPLOAD_URL, json=data)
				res.close()
				if res.status_code == 200:
					self.log(f'回传任务结果：{data}')
					break
			finally:
				pass
			self.y_sleep(5)
	
	def run_task(self):
		if self.game_token:
			return self.get_stoken_by_game_token()
		else:
			return self.get_stoken_by_cookie_token()
	
	def exchange(self, stoken, mid):
		path = 'https://passport-api.mihoyo.com/account/ma-cn-session/app/exchange'
		data = {
			"mid": mid,
			"dst_token_type": 4,
			"src_token": {
				"token_type": 1,
				"token": stoken
			}
		}
		headers = {
			'x-rpc-game_biz': 'hkrpg_cn',
			'x-rpc-app_id': 'c90mr1bwo2rk',
		}
		while self.working:
			try:
				res = self.conn_by_proxy.post(path, json=data, headers=headers, timeout=5)
				if res.status_code == 200 and 'message' in res.json() and res.json()['message'] == 'OK':
					return res.json()['data']['token']['token']
			except:
				pass
			self.y_sleep(2)
			self.change_proxy()
	
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
						stoken = data['token']['token']
						mid = data['user_info']['mid']
						cookie_token = self.exchange(stoken, mid)
						return {
							'stoken': stoken,
							'mid': mid,
							'cookie_token': cookie_token
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
				pass
			self.y_sleep(2)
			self.change_proxy()
	
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
				pass
			self.y_sleep(2)
			self.change_proxy()
	

if __name__ == '__main__':
	info_ = {
		"account": 'pnmv76451263@163.com',
		'game_token': 'v2_Tg804PSzqkTacJjstnl68H_-093T_2kxq38MzM-jb7GQCWBcQV4MHyPNSuX5BeQjp3tyBmVXdi5tCdlFUaHDTQ1hBtiLPWkoGr62TXOyXJl25TBvlSVb_yChqMQsFRUwNPk5HP5p4s5v-zbFQ6mCysZCQ7_M-n6nxaq8NWciCCokdA==.CAE=',
		'uid': 443882447,
	}
	mhy = MHYObj(info_)
	a = mhy.run_task()
	print(a)
