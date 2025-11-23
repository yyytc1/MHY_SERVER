# coding : utf-8
# @Time : 2025/8/26 21:40 
# @Author : Adolph
# @File : baseConn.py
# @Software : PyCharm
import traceback

import cloudscraper


class Conn:
	def __init__(self, proxy=None, token=None):
		"""
		:param proxy: 代理地址，格式为 username:password@host:port 或 host:port
		:param token: Bearer Token，可选
		"""
		self.proxy = proxy
		self.token = token
		self.init_conn()
	
	def init_conn(self):
		headers = None
		cookie = None
		if hasattr(self, 'conn'):
			headers = self.conn.headers
			cookie = self.conn.cookies
		self.conn = cloudscraper.create_scraper(
			browser={
				'browser': 'chrome',
				'platform': 'windows',
				'mobile': False
			}
		)
		self.conn.trust_env = False
		self.conn.headers = headers
		if cookie:
			self.conn.cookies = cookie
		
		# 设置代理
		if self.proxy:
			self.conn.proxies = {
				"http": f"http://{self.proxy}",
				"https": f"http://{self.proxy}"
			}
	
	def set_token(self, token):
		"""动态更新 Bearer Token"""
		self.token = token
		self.conn.headers['authorization'] = f'Bearer {self.token}'
	
	def set_headers(self, key, value):
		if self.conn.headers is None:
			self.conn.headers = {}
		self.conn.headers[key] = value
	
	def pop_headers(self, key):
		if isinstance(self.conn.headers, dict):
			if key in self.conn.headers:
				self.conn.headers.pop(key)
	
	def request(self, method, url, payload=None, timeout=10):
		"""
		通用请求
		:param timeout:
		:param method: GET / POST
		:param url: 请求地址
		:param payload: 请求参数/数据
		:param return_json: 返回 json() 还是 Response 对象
		:param verify: 临时覆盖 SSL 验证 (True / False / crt路径)
		"""
		try:
			if method.upper() == "GET":
				res = self.conn.request(method, url=url, params=payload, timeout=timeout)
			else:
				res = self.conn.request(method, url=url, json=payload, timeout=timeout)
			
			return res
		except:
			e = traceback.format_exc()
			return None
	
	def close(self):
		try:
			self.conn.close()
		except:
			pass
		try:
			del self.conn
		except:
			pass
