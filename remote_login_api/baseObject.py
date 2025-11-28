import re
import traceback
from threading import Thread

import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

import rsa
from loguru import logger

from config import *
from baseConn import Conn
from device import new_ext_fields
from remote_login_api.bilibili import bili_new_params, bili_encode
from stringFunc import *
from thread_ import sk5_queue, get_sk5

Thread(target=get_sk5, args=(proxy_url,), daemon=True).start()


class Method:
	GET = "GET"
	POST = "POST"


class Device:
	uid = get_uuid()
	seed_id = random_seed_id()
	platform = '1'
	app_name = 'bh2_cn'
	fp = random_device_fp()
	device_id = uid
	seed_ts = seed_ts()
	ext_fields = new_ext_fields(uid)


class BaseObj:
	
	def __init__(self, info=None):
		super().__init__()
		if info is None:
			info = {}
		self.user = info.get('user')
		self.pwd = info.get('pass')
		self.city = info.get('city', '1')
		self.working = True
		self.conn_by_proxy = Conn()
		self.conn_no_proxy = Conn()
		self.change_proxy()
	
	def log(self, message):
		if self.working:
			if self.user:
				logger.info(f'{self.user}  {message}')
			else:
				logger.info(f'{message}')
	
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
			sk5, end_time = None, None
			while self.working:
				if sk5_queue.qsize() > 0:
					sk5, end_time = sk5_queue.get()
					break
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
	
	def conn_request(self, method, path, payload=None, timeout=5):
		res = self.conn_by_proxy.request(method, path, payload, timeout)
		return res
	
	def conn_request_no_proxy(self, method, path, payload=None, timeout=5):
		res = self.conn_no_proxy.request(method, path, payload, timeout)
		return res
	
	def close(self):
		# 关闭可能存在的 Conn 实例，避免会话未释放导致的内存增长
		for attr in ('conn_by_proxy', 'conn_no_proxy', 'conn'):
			if hasattr(self, attr):
				obj_ = getattr(self, attr)
				try:
					if isinstance(obj_, Conn):
						obj_.close()
				except:
					pass
				# 尝试删除引用，帮助 GC 及早回收大对象
				try:
					delattr(self, attr)
				except:
					pass
		# 标记停止工作
		self.working = False
		# 触发一次显式 GC（可选，帮助释放循环引用）
		try:
			import gc
			gc.collect()
		except:
			pass
	
	def change_proxy(self):
		proxy = self.get_proxy()
		self.conn_by_proxy.conn.proxies = {
			"http": f"http://{proxy}",
			"https": f"http://{proxy}"
		}


class Gt4Obj:
	
	def __init__(self, captcha_id, session_id):
		self.working = True
		self.conn = Conn()
		self.captcha_id = captcha_id
		self.session_id = session_id
		self.cookies = {
			# "captcha_v4_user": random_device_id(32)
			"captcha_v4_user": '5cfcee290d56477e9f8002b003f20558'
		}
		self.conn.conn.headers = {
			"accept": "*/*",
			"accept-language": "zh-CN,zh;q=0.9",
			"cache-control": "no-cache",
			"pragma": "no-cache",
			"sec-ch-ua": "\"Chromium\";v=\"142\", \"Google Chrome\";v=\"142\", \"Not_A Brand\";v=\"99\"",
			"sec-ch-ua-mobile": "?0",
			"sec-ch-ua-platform": "\"Windows\"",
			"sec-fetch-dest": "script",
			"sec-fetch-mode": "no-cors",
			"sec-fetch-site": "cross-site",
			"sec-fetch-storage-access": "active",
			'host': 'gcaptcha4.geetest.com',
			'referrer': "https://user.mihoyo.com/",
		}
	
	def log(self, message):
		if self.working:
			logger.info(f'{message}')
	
	def y_sleep(self, times):
		for i in range(times):
			try:
				if not self.working:
					break
				time.sleep(1)
			except:
				pass
	
	def conn_request(self, method, path, payload=None, timeout=5):
		res = self.conn.request(method, path, payload, timeout)
		return res
	
	def load_first(self):
		path = 'https://gcaptcha4.geetest.com/load'
		
		while self.working:
			try:
				params = {
					'callback': 'geetest_' + str(int(time.time() * 1000)),
					'captcha_id': self.captcha_id,
					'challenge': get_uuid(),
					'client_type': 'web',
					'risk_type': 'icon',
					'user_info': json.dumps({'session_id': self.session_id}),
					'lang': 'zho',
				}
				res = self.conn.conn.get(path, params=params)
				res.close()
				json_str = re.sub(r'^geetest_\d+\(|\);?$', '', res.text)
				data = json.loads(json_str)['data']
				return data
			except:
				e = traceback.format_exc()
				pass
			self.y_sleep(2)
		
		def close(self):
			"""关闭内部 Conn 并清理大对象引用，帮助 GC 回收"""
			try:
				self.working = False
			except:
				pass
			try:
				if hasattr(self, 'conn') and isinstance(self.conn, Conn):
					self.conn.close()
			except:
				pass
			# 清理可能占用大内存的字段
			try:
				del self.captcha_id
			except:
				pass
			try:
				del self.session_id
			except:
				pass
			try:
				import gc
				gc.collect()
			except:
				pass
	
	def match_icons(self, img_list):
		imgs, ques0, ques1, ques2 = img_list
		path = "http://47.104.101.1:19197/runtime/text/invoke"
		while self.working:
			pos_list = []
			try:
				res = self.conn_request(Method.POST, path, {
					"project_name": "geetest4_icon_sim",
					"image": imgs,
					"title": [ques0, ques1, ques2],
					
				})
				if res.status_code == 200:
					for i in res.json()['data'].split('|'):
						x, y = i.split(',')
						x = int(int(x) / 300.03125 * 100 * 100)
						y = int(int(y) / 200.109375 * 100 * 100)
						pos_list.append([x, y])
					return pos_list
			except:
				pass
			self.y_sleep(1)
	
	def damagou_geetest_verify(self):
		url = 'http://api.damagou.top/apiv1/jiyan4Recognize.html'
		data = {
			'userkey': 'c6deeb6d46fd26ec52264a0c95e2eb91',
			'captchaId': self.captcha_id,
			'riskType': 'icon',
			'referer': "https://user.mihoyo.com/",
			'isJson': '1'
		}
		res = requests.get(url, params=data)
		res.close()
		'lot_number|pass_token|gen_time|captcha_output'
		lst = res.text.split('|')
		data = {
			'captcha_id': self.captcha_id,
			'lot_number': lst[0],
			'pass_token': lst[1],
			'gen_time': lst[2],
			'captcha_output': lst[3],
		}
		return self.session_id + ';' + base64_sccode(data)
	
	def geetest_verify(self):
		data = self.load_first()
		lst = self.get_gt4_icon_imgs(data)
		arr = self.match_icons(lst)
		w = self.get_w(data, arr)
		return self.verify(data, w)
	
	def verify(self, data, w):
		path = 'https://gcaptcha4.geetest.com/verify'
		while self.working:
			params = {
				"callback": "geetest_" + str(int(time.time() * 1000)),
				"captcha_id": self.captcha_id,
				"client_type": "web",
				"lot_number": data['lot_number'],
				'risk_type': 'icon',
				"payload": data['payload'],
				"process_token": data['process_token'],
				"payload_protocol": "1",
				"pt": "1",
				"w": w,
			}
			try:
				res = self.conn.conn.get(path, params=params, cookies=self.cookies)
				res.close()
				json_str = re.sub(r'^geetest_\d+\(|\);?$', '', res.text)
				json_str = json.loads(json_str)
				print(f"score：{json_str['data']['score']}")
				seccode = json_str['data']['seccode']
				json_data = {
					"captcha_id": self.captcha_id,
					"lot_number": seccode['lot_number'],
					"pass_token": seccode['pass_token'],
					"gen_time": seccode['gen_time'],
					"captcha_output": seccode['captcha_output'],
				}
				return self.session_id + ';' + base64_sccode(json_data)
			except:
				pass
	
	def get_w(self, data, get_array):
		lot_number = data['lot_number']
		bits = data['pow_detail']['bits']
		hashfunc = data['pow_detail']['hashfunc']
		version = data['pow_detail']['version']
		datetime = data['pow_detail']['datetime']
		
		# 获取签名
		sign = self.get_sign(lot_number, hashfunc, version, bits, datetime)
		_obj = {
			"device_id": "",
			"lot_number": lot_number,
			"pow_msg": sign['pow_msg'],
			"pow_sign": sign['pow_sign'],
			"geetest": "captcha",
			"lang": "zh",
			"ep": "123",
			"biht": "1426265548",
			"gee_guard": {
				"roe": {
					"aup": "3",
					"sep": "3",
					"egp": "3",
					"auh": "3",
					"rew": "3",
					"snh": "3",
					"res": "3",
					"cdc": "3"
				}
			},
			# "W4Ec": "7RXi",
			"Vbp4": "4SAo",
			"em": {
				"ph": 0,
				"cp": 0,
				"ek": "11",
				"wd": 1,
				"nt": 0,
				"si": 0,
				"sc": 0
			},
			# lot_number[15:19]: {
			# 	lot_number[10:14] + lot_number[14:18]: lot_number[12:20]
			# }
		}
		_obj.update({
			"passtime": random.randint(2000, 3000),
			"userresponse": get_array,
		})
		res = json.dumps(_obj, separators=(',', ':'))
		key = self.get_key()
		rsa_enc = self.rsa_public_encrypt(key)
		iv = "0000000000000000"
		aes_enc = self.aes_encrypt(res, key, iv)
		return aes_enc + rsa_enc
	
	@staticmethod
	def aes_encrypt(word, key, iv):
		# 确保 key 和 iv 是字节类型
		key = key.encode('utf-8')
		iv = iv.encode('utf-8')
		
		# 创建 AES 加密器
		cipher = AES.new(key, AES.MODE_CBC, iv)
		
		# 对明文进行 PKCS7 填充
		padded_word = pad(word.encode('utf-8'), AES.block_size)
		
		# 加密
		encrypted = cipher.encrypt(padded_word)
		
		# 将加密后的字节转换为 Base64 字符串
		encrypted_base64 = base64.b64encode(encrypted).decode('utf-8')
		
		# 将 Base64 字符串转换为十六进制字符串
		encrypted_hex = binascii.hexlify(base64.b64decode(encrypted_base64)).decode('utf-8')
		
		return encrypted_hex
	
	@staticmethod
	def get_key():
		part = hex(int(65536 * (1.0 + random.random())))[2:].lower()[1:]
		part1 = hex(int(65536 * (1.0 + random.random())))[2:].lower()[1:]
		part2 = hex(int(65536 * (1.0 + random.random())))[2:].lower()[1:]
		part3 = hex(int(65536 * (1.0 + random.random())))[2:].lower()[1:]
		return part + part1 + part2 + part3
	
	@staticmethod
	def rsa_public_encrypt(plain_text):
		# 公钥的模数和指数
		public_modulus_hex = "00C1E3934D1614465B33053E7F48EE4EC87B14B95EF88947713D25EECBFF7E74C7977D02DC1D9451F79DD5D1C10C29ACB6A9B4D6FB7D0A0279B6719E1772565F09AF627715919221AEF91899CAE08C0D686D748B20A3603BE2318CA6BC2B59706592A9219D0BF05C9F65023A21D2330807252AE0066D59CEEFA5F2748EA80BAB81"
		public_exponent_hex = "10001"
		
		# 将十六进制字符串转换为整数
		public_modulus = int(public_modulus_hex, 16)
		public_exponent = int(public_exponent_hex, 16)
		
		# 创建公钥对象
		public_key = rsa.PublicKey(public_modulus, public_exponent)
		
		# 加密明文
		encrypted_text = rsa.encrypt(plain_text.encode('utf8'), public_key)
		
		# 将加密后的字节转换为十六进制字符串
		encrypted_hex = encrypted_text.hex()
		
		return encrypted_hex
	
	def get_sign(self, lot_number, hashfunc, version, bits, datetime):
		a = bits % 4
		_ = bits // 4  # 计算需要的前缀0的数量
		u = '0' * _  # 生成前缀0字符串
		# r=get_formatted_time_with_timezone()
		# 构建基础字符串
		c = f"{version}|{bits}|{hashfunc}|{datetime}|{self.captcha_id}|{lot_number}||"
		
		while self.working:
			# 生成GUID（UUID4）
			h = str(uuid.uuid4()).replace('-', '')
			
			# 构建待哈希的字符串
			p = f"{c}{h}"
			
			# 根据算法计算哈希值
			if hashfunc == "md5":
				hash_obj = hashlib.md5(p.encode())
			elif hashfunc == "sha1":
				hash_obj = hashlib.sha1(p.encode())
			elif hashfunc == "sha256":
				hash_obj = hashlib.sha256(p.encode())
			else:
				raise ValueError(f"不支持的哈希算法: {hashfunc}")
			
			l = hash_obj.hexdigest()  # 获取十六进制哈希结果
			
			# 检查前缀是否符合条件
			if l.startswith(u):
				# 当a为0时，只要前缀符合就返回
				if a == 0:
					return {
						"pow_msg": f"{c}{h}",
						"pow_sign": l
					}
				else:
					# 检查特定位置的字符是否符合条件
					if _ < len(l):
						g = l[_]
						# 转换为16进制数值
						try:
							g_val = int(g, 16)
						except ValueError:
							continue
						
						# 根据a的值确定阈值
						if a == 1:
							f = 7
						elif a == 2:
							f = 3
						elif a == 3:
							f = 1
						else:
							continue  # 不应该发生
						
						if g_val <= f:
							return {
								"pow_msg": f"{c}{h}",
								"pow_sign": l
							}
	
	def get_gt4_icon_imgs(self, data):
		imgs = self.download_img(data['imgs'])
		ques0 = self.download_img(data['ques'][0])
		ques1 = self.download_img(data['ques'][1])
		ques2 = self.download_img(data['ques'][2])
		return imgs, ques0, ques1, ques2
	
	def download_img(self, url):
		base_url = "https://static.geetest.com/"
		headers = {
			"Referer": "https://gt4.geetest.com/",
			"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
		}
		self.conn.conn.headers = headers
		while self.working:
			res = None
			try:
				res = self.conn_request(Method.GET, f'{base_url}{url}')
				if res is None:
					continue
				content = res.content
				# 把二进制转为 base64 并返回
				return base64.b64encode(content).decode()
			except:
				pass
			finally:
				# 确保如有未关闭的 Response 被关闭并删除引用
				try:
					if isinstance(res, requests.Response):
						res.close()
				except:
					pass
				try:
					del res
				except:
					pass
			self.y_sleep(2)


class Gt3Obj(BaseObj):
	
	def __init__(self, gt, challenge, host=None):
		super().__init__()
		self.gt = gt
		self.challenge = challenge
		self.host = host or 'api.geetest.com'
		self.static_server = ''
	
	def new_params(self):
		return {
			'callback': f'geetest_{str(int(time.time() * 1000))}',
			'gt': self.gt,
			'challenge': self.challenge,
			'lang': 'zh-cn',
			'client_type': 'web',
		}
	
	@staticmethod
	def format_gt_resp(gt_text):
		start = gt_text.find('{')
		end = gt_text.rfind('}')
		if start != -1 and end != -1:
			return json.loads(gt_text[start:end + 1])
		return None
	
	def get_pt0(self):
		url = f'https://{self.host}/get.php'
		while self.working:
			try:
				params = self.new_params()
				params['pt'] = '0'
				params['w'] = ''
				res = self.conn_request(Method.GET, url, params)
				if res.status_code == 200:
					data = self.format_gt_resp(res.text)
					if data and data['status'] == 'success':
						self.host = data['data']['api_server']
						self.static_server = data['data']['static_servers'][0]
						self.log('获取pt0成功')
						return True, ''
					else:
						return False, '获取pt0失败'
				else:
					return False, '获取pt0失败'
			except:
				pass
			self.y_sleep(2)
			self.change_proxy()
	
	def ajax_pt3(self):
		url = f'https://{self.host}/ajax.php'
		while self.working:
			try:
				params = self.new_params()
				params['pt'] = '3'
				res = self.conn_request(Method.GET, url, params)
				if res.status_code == 200:
					data = self.format_gt_resp(res.text)
					if data and data['status'] == 'success':
						captcha_type = data['data']['result']
						self.log(f'获取pt3成功，验证码类型：{captcha_type}')
						return True, captcha_type
					else:
						return True, '获取pt3失败'
				else:
					return True, '获取pt3失败'
			except:
				pass
			self.y_sleep(2)
			self.change_proxy()
	
	def task(self):
		ret, msg = self.get_pt0()
		if not ret:
			self.log(msg)
			return msg, 400
		ret, msg = self.ajax_pt3()
		if not ret:
			self.log(msg)
			return msg, 400
		# if msg == 'slide':
		# 	ret1, w = self.slide()
		if msg == 'click':
			ret1, w = self.click()
		else:
			return f'暂不支持的验证码类型:{msg}', 400
		if ret1:
			return self.verify_click(w)
		else:
			return w, 400
	
	def verify_click(self, w):
		url = f'https://api.geevisit.com/ajax.php'
		params = {
			'pt': '0',
			'w': w,
		}
		while self.working:
			try:
				params.update(self.new_params())
				res = self.conn_request(Method.GET, url, params)
				if res.status_code == 200:
					data = self.format_gt_resp(res.text).get('data', {})
					if data.get('result') == 'success':
						return data.get('validate'), 200
					else:
						return '极验验证失败', 400
				else:
					return '极验验证失败', 400
			except:
				pass
			self.y_sleep(2)
			self.change_proxy()
	
	def click(self):
		# 获取点选验证码信息
		params = {
			'is_next': 'true',
			'type': 'click',
			'https': 'false',
			'protocol': 'https://',
			'offline': 'false',
			'product': 'embed',
			'api_server': self.host,
			'isPC': 'true',
			'autoReset': 'true',
			'width': '100%',
		}
		url = f'https://{self.host}/get.php'
		while self.working:
			try:
				params.update(self.new_params())
				res = self.conn_request(Method.GET, url, params)
				if res.status_code == 200:
					data = self.format_gt_resp(res.text)
					if data and data['status'] == 'success':
						self.log(f'获取点选验证码成功')
						data = data['data']
						pic = data['pic']
						pic_type = data.get('pic_type', '')
						if pic_type == 'space':
							w = self.space(pic, data.get('sign', ''))
						elif pic_type == 'nine':
							w = self.nine(pic)
						elif pic_type == 'word':
							w = self.word(pic)
						else:
							return False, f'暂不支持的类型:{pic_type}'
						return True, w
					else:
						return False, '获取点选验证码失败'
				else:
					return False, '获取点选验证码失败'
			except:
				pass
			self.y_sleep(2)
			self.change_proxy()
	
	def download_image(self, url):
		while self.working:
			try:
				if not url.startswith('http'):
					url = 'https://' + self.static_server + url
				res = self.conn_request(Method.GET, url)
				if res is None:
					continue
				# 读取 content 并尽快释放 Response 引用
				content = None
				try:
					content = res.content
				except:
					content = None
				try:
					res.close()
				except:
					pass
				try:
					del res
				except:
					pass
				return content
			except:
				pass
			self.y_sleep(2)
			self.change_proxy()
	
	def nine(self, pic):
		img_bytes = self.download_image(pic)
		# 先把大二进制转为 base64 字符串，尽快释放二进制内存
		encoded = base64.b64encode(img_bytes).decode()
		del img_bytes
		ocr_url = nine_orc_url + '/runtime/text/invoke'
		data = {'image': encoded, 'project_name': 'gt3_nine'}
		# 下载图片，调用九宫格 OCR 服务
		while self.working:
			try:
				res = self.conn_no_proxy.conn.post(ocr_url, json=data)
				res.close()
				resp = res.json()
				if not resp.get('success') or resp.get('code') != 0:
					return ''
				# 解析点位
				return self.encode_points(resp['data'])
			except:
				pass
			self.y_sleep(2)
	
	def word(self, pic):
		img_bytes = self.download_image(pic)
		# 先把大二进制转为 base64 字符串，尽快释放二进制内存
		encoded = base64.b64encode(img_bytes).decode()
		del img_bytes
		ocr_url = word_orc_url + '/runtime/text/invoke'
		data = {'image': encoded, 'project_name': 'geetest_zh'}
		while self.working:
			try:
				res = self.conn_no_proxy.conn.post(ocr_url, json=data)
				res.close()
				resp = res.json()
				if not resp.get('success'):
					return ''
				return self.get_w(self.parse_points(resp['data']), pic)
			except:
				pass
			self.y_sleep(2)
	
	def space(self, pic, title):
		img_bytes = self.download_image(pic)
		# 先把大二进制转为 base64 字符串，尽快释放二进制内存
		encoded = base64.b64encode(img_bytes).decode()
		del img_bytes
		ocr_url = space_orc_url + '/runtime/text/invoke'
		data = {'image': encoded, 'title': title, 'project_name': 'geetest_space'}
		while self.working:
			try:
				res = self.conn_no_proxy.conn.post(ocr_url, json=data)
				res.close()
				resp = res.json()
				if resp.get('code') == 0:
					return self.parse_points(resp['data'])
				else:
					return 0
			except:
				pass
			self.y_sleep(2)
	
	@staticmethod
	def parse_points(data):
		# data: "x1,y1|x2,y2|..."
		points = []
		for item in data.split('|'):
			arr = item.split(',')
			if len(arr) == 2:
				x, y = int(int(arr[0]) / 344 * 10000), int(int(arr[1]) / 344 * 10000)
				points.append(f'{x}_{y}')
		return ','.join(points)
	
	@staticmethod
	def encode_points(points_str):
		# 按九宫格分区
		points = [[int(x), int(y)] for x, y in (p.split(',') for p in points_str.split('|'))]
		point_arr = []
		for x, y in points:
			if 0 <= x <= 114:
				if 0 <= y <= 114:
					point_arr.append('1_1')
				elif 115 <= y <= 229:
					point_arr.append('1_2')
				else:
					point_arr.append('1_3')
			elif 115 <= x <= 229:
				if 0 <= y <= 114:
					point_arr.append('2_1')
				elif 115 <= y <= 229:
					point_arr.append('2_2')
				else:
					point_arr.append('2_3')
			elif 230 <= x <= 344:
				if 0 <= y <= 114:
					point_arr.append('3_1')
				elif 115 <= y <= 229:
					point_arr.append('3_2')
				else:
					point_arr.append('3_3')
		return ','.join(point_arr)
	
	def get_w(self, point: str, pic: str) -> str:
		passtime = random.randint(2000, 3000)
		time.sleep(passtime / 1000)
		return ctx.call('getwords', passtime, point, pic, self.gt, self.challenge)
	
	def close(self):
		"""清理 Gt3Obj 占用的大对象并关闭父类可能持有的 Conn"""
		try:
			self.working = False
		except:
			pass
		# 删除大字段，释放引用
		for attr in ('pic', 'c', 's', 'cache', 'cjy', 'gct_path', 'resp'):
			try:
				if hasattr(self, attr):
					delattr(self, attr)
			except:
				pass
		# 关闭 BaseObj 中的 Conn 实例（如果存在）
		try:
			super().close()
		except:
			pass
		try:
			import gc
			gc.collect()
		except:
			pass


class MHYObj(BaseObj):
	
	def __init__(self, info):
		super().__init__(info)
		self.random_device()
		if self.city == '1':
			self.app_id = '8'
			self.channel_id = '1'
		elif self.city == '6':
			self.app_id = '8'
			self.channel_id = '14'
		else:
			self.app_id = '11'
			self.channel_id = '1'
	
	def random_device(self):
		self.device_uid = get_uuid()
		self.device_id = random_device_id()
		self.seed_id = random_seed_id()
		self.device_name = random_device_name()
		self.device_model = random_device_model()
		self.lifecycle_id = get_uuid()
	
	def get_fp(self):
		headers = {
			"Content-Type": "application/json;charset=UTF-8",
		}
		if self.city in ['1', '6']:
			url = "https://public-data-api.mihoyo.com/device-fp/api/getFp"
			headers['Referer'] = 'https://user.mihoyo.com/'
		else:
			url = "https://sg-public-data-api.hoyoverse.com/device-fp/api/getFp"
			headers['Referer'] = 'https://sr.mihoyo.com/'
		times = 0
		self.conn_by_proxy.conn.headers = headers
		while self.working:
			try:
				data = {
					"app_name": "hkrpg_cn",
					"device_fp": random_device_fp(),
					"device_id": self.device_uid,
					"ext_fields": get_fixed_ext_fields(),
					"platform": "22",
					"seed_id": self.seed_id,
					"seed_time": seed_ts()
				}
				res = self.conn_request(Method.POST, url, data)
				if res.status_code == 200:
					if 'data' in res.json():
						self.device_fp = res.json()['data']['device_fp']
						self.log(f'获取到fp: {self.device_fp}')
						return True
					else:
						times += 1
				else:
					times += 1
				if times >= MAX_RETRY_TIMES:
					self.log(f'获取fp超时')
					return False
			except:
				pass
			self.y_sleep(2)
			self.change_proxy()
	
	def remote_geetest_icon(self, captchaId):
		data = {'captchaId': captchaId}
		res = self.conn_request_no_proxy(Method.POST, gt_icon_url, data)
		if res is None:
			return None
		if res.status_code == 200:
			if res.json()['status'] == 'success':
				self.log('极验识别成功')
				return base64_sccode(res.json()['data']['seccode'])
	
	def web_login(self):
		path = 'https://passport-api.mihoyo.com/account/ma-cn-passport/web/loginByPassword'
		times = 0
		while self.working:
			try:
				headers = {
					"x-rpc-app_id": "ess4np01pji8",
					"x-rpc-client_type": "4",
					"x-rpc-device_fp": self.device_fp,
					"x-rpc-device_id": self.device_uid,
					"x-rpc-game_biz": "abc_cn",
					"x-rpc-mi_referrer": "https://user.mihoyo.com/login-platform/index.html?app_id=ess4np01pji8&theme=abc&token_type=4&game_biz=abc_cn&fs_ql_w=0&fs_ql_m=0&message_origin=https%253A%252F%252Fyyjl.mihoyo.com&succ_back_type=message%253Alogin-platform%253Alogin-success&fail_back_type=message%253Alogin-platform%253Alogin-fail&ux_mode=popup&iframe_level=1#/login/password",
					"x-rpc-sdk_version": "2.44.0",
					"x-rpc-source": "v2.webLogin"
				}
				data = {
					'account': rsa_encrypt(self.city, self.user),
					'password': rsa_encrypt(self.city, self.pwd),
				}
				res = self.conn_by_proxy.conn.post(path, json=data, headers=headers)
				res.close()
				if res.status_code == 200 and 'message' in res.json() and res.json()['message'] == 'OK':
					cookie = self.conn_by_proxy.conn.cookies.get_dict()
					user_info = res.json()['data']['user_info']
					return True, f"{self.user}----{user_info['aid']}|{user_info['mid']}|{cookie['cookie_token_v2']}"
				else:
					times += 1
				if times >= MAX_RETRY_TIMES:
					return False, '登录超时'
			except:
				e = traceback.format_exc()
				pass
			self.y_sleep(2)
			self.change_proxy()
		
	# 米哈游BH极验 用ip能过 返回id
	def bh_check(self):
		if self.city in ['1', '6']:
			path = "https://gameapi-account.mihoyo.com/account/risky/api/check"
		else:
			path = 'https://api-account-os.hoyoverse.com/account/risky/api/check'
		data = {
			"api_name": "/shield/api/login",
			"action_type": "login",
			"username": self.user,
		}
		times = 0
		while self.working:
			try:
				device = Device()
				headers = {
					"Content-Type": "application/json",
					"x-rpc-device_model": device.ext_fields.ext.model,
					"User-Agent": "HSoDv2CN/11.2.3 CFNetwork/1496.0.7 Darwin/23.5.0",
					"x-rpc-language": "zh-cn",
					"x-rpc-lifecycle_id": get_uuid(),
					"x-rpc-device_name": device.ext_fields.ext.deviceName,
					"x-rpc-device_fp": self.device_fp,
					"x-rpc-mdk_version": device.ext_fields.ext.packageVersion,
					"x-rpc-client_type": "1",
					"x-rpc-device_id": self.device_uid,
					"x-rpc-channel_version": device.ext_fields.ext.packageVersion,
					"x-rpc-channel_id": "1",
					"x-rpc-sys_version": device.ext_fields.ext.osVersion,
					"Accept-Encoding": "gzip, deflate, br"
				}
				if self.city in ['1', '6']:
					headers['x-rpc-game_biz'] = 'hkrpg_cn'
				else:
					headers['x-rpc-game_biz'] = 'hkrpg_global'
				self.conn_by_proxy.conn.headers = headers
				res = self.conn_request(Method.POST, path, data)
				if res.status_code == 200 and res.json().get('message') == 'OK':
					gt_id = res.json()['data']['id']
					self.log(f"获取到极验id: {gt_id}")
					return gt_id
				else:
					times += 1
				if times >= MAX_RETRY_TIMES:
					self.log(f"获取极验id超时")
					return None
			except:
				e = traceback.format_exc()
				pass
			self.y_sleep(2)
			self.change_proxy()
	
	def BHLoginWithProxy(self):
		# 对应QFG新登录 国服
		ret = self.get_fp()
		if not ret:
			return {'error': '获取fp失败'}, 500
		gt_id = self.bh_check()
		if not gt_id:
			return {'error': '获取极验id失败'}, 500
		msg, combo_token = self.bh_login(gt_id)
		if combo_token == '':
			return {'error': msg}, 400
		else:
			return {'result': msg, 'combo_token': combo_token}, 200
	
	def HoYoVerse(self):
		# 对应QFG老登录 国际服
		ret = self.get_fp()
		if not ret:
			return {'error': '获取fp失败'}, 500
		msg, token = self.bh_login_gj()
		if token == '':
			return {'error': msg}, 400
		else:
			return {
				'result': msg,
				'combo_token': token['combo_token'],
				'cookie_token': token['cookie_token_v2'],
			}, 200
	
	def bh_login_gj(self, aigis=None, data=None):
		url = "https://sg-public-api.hoyoverse.com/account/ma-passport/api/webLoginByPassword"
		times = 0
		if not data:
			data = {
				'account': rsa_encrypt(self.city, self.user),
				'password': rsa_encrypt(self.city, self.pwd),
				'token_type': 4
			}
		headers = {
			"x-rpc-app_id": "de8ohyzxreo0",
			"x-rpc-game_biz": "plat_os",
			"x-rpc-language": "zh-cn",
			"x-rpc-client_type": "4",
			"x-rpc-app_version": "",
			"x-rpc-age_gate": "true",
			"x-rpc-aigis_v4": "false",
			"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
			"x-rpc-device_fp": self.device_fp,  # 变量，需保证已定义
			"x-rpc-device_id": self.device_uid,  # 变量，需保证已定义
			"x-rpc-device_model": "Chrome 138.0.0.0",
			"x-rpc-device_name": "Chrome",
			"x-rpc-device_os": "Windows 10 64-bit",
			"x-rpc-sdk_version": "2.41.0",
			"Origin": "https://account.hoyoverse.com",
			"Pragma": "no-cache",
			"Referer": "https://account.hoyoverse.com/passport/index.html#/login",
			"x-rpc-lifecycle_id": self.lifecycle_id  # 变量，需保证已定义
		}
		if aigis:
			headers['X-Rpc-Aigis'] = aigis
		while self.working:
			try:
				res = self.conn_by_proxy.conn.post(url, json=data, headers=headers)
				res.close()
				if res.status_code == 200 and 'message' in res.json():
					message = res.json()['message']
					if message == 'OK':
						msg, status_code = self.get_combo_token_by_len160_cookie_token_v2()
						if status_code == 200:
							return res.json(), msg
						else:
							return msg, ''
					else:
						return message, ''
				else:
					times += 1
				if times >= MAX_RETRY_TIMES:
					return '国际服登录超时', ''
			except:
				pass
			self.y_sleep(2)
			self.change_proxy()
	
	
	
	def BiliLogHandle(self):
		ret = self.get_fp()
		if not ret:
			return {'error': '获取fp失败'}, 500
		# 对应QFG新登录 B服
		hash_str = self.bili_rsa()
		if not hash_str:
			return {'error': 'RSA密钥解析失败'}, 400
		params = bili_new_params()
		params.update({
			'user_id': self.user,
			'is_gov_ver': '1',
			'pwd': rsa_encrypt(self.city, hash_str + self.pwd)
		})
		# 尝试获取验证码并执行极验任务，最多重试 3 次
		max_attempts = 3
		last_err = '未知错误'
		for attempt in range(1, max_attempts + 1):
			captcha_ret = self.bili_get_captcha()
			if isinstance(captcha_ret, str):
				# bili_get_captcha 返回字符串表示错误，记录并重试
				last_err = captcha_ret
				self.log(f'bili_get_captcha 第{attempt}次失败: {captcha_ret}')
				continue
			gt, challenge = captcha_ret.get('gt'), captcha_ret.get('challenge')
			if not gt or not challenge:
				last_err = '获取到的验证码数据不完整'
				self.log(f'bili_get_captcha 第{attempt}次返回数据不完整')
				continue
			gt3_obj = Gt3Obj(gt, challenge)
			try:
				msg, status_code = gt3_obj.task()
			finally:
				try:
					gt3_obj.close()
				except:
					pass
				try:
					del gt3_obj
				except:
					pass
			if status_code == 200:
				params.update({
					'challenge': challenge,
					'validate': msg,
					'seccode': msg + '|jordan',
					'captcha_type': captcha_ret.get('captcha_type'),
					'gt_user_id': captcha_ret.get('userid'),
					'gs': captcha_ret.get('gs'),
					'timestamp': str(int(time.time() * 1000)),
				})
				access_key, ret = self.bili_get_access_key(params)
				if not ret:
					# 失败前尽量清理大对象引用
					try:
						del params
					except:
						pass
					return {'error': access_key}, 400
				msg, combo_token = self.bili_login_by_sign(access_key)
				# 成功返回前清理临时引用
				try:
					del captcha_ret
				except:
					pass
				try:
					del params
				except:
					pass
				return {'result': msg, 'combo_token': combo_token}, 200
			else:
				last_err = msg
				self.log(f'gt3.task 第{attempt}次失败: {msg} (status {status_code})')
		# 若循环自然结束且未成功，则返回最后的错误信息
		if not (isinstance(captcha_ret, dict) and status_code == 200):
			# status_code 可能未定义（若 bili_get_captcha 一直失败），确保返回合理的状态
			code = status_code if 'status_code' in locals() else 400
			return {'error': last_err}, code
	
	def bili_get_access_key(self, params):
		url = 'https://wpg-api.biligame.com/api/pcg/login?' + bili_encode(params)
		times = 0
		while self.working:
			try:
				res = self.conn_request(Method.POST, url)
				if res.status_code == 200 and 'code' in res.json():
					"""
					{
						"request-id": "6a9be4a0c62011f08fba92927e223089",
						"request_id": "6a9be4a0c62011f08fba92927e223089",
						"ts": 1763650297834,
						"timestamp": 1763650297834,
						"is_need_real_name": 1,
						"is_real_name": 1,
						"limit_alert_message": "",
						"user_limit_status": 0,
						"uname": "bili64993911368",
						"face": "https://static.hdslb.com/images/member/noface.gif",
						"s_face": "https://static.hdslb.com/images/member/noface.gif",
						"code": 0,
						"access_key": "62c3552dc933222d030f83f0835d7501_t1",
						"uid": 1272851821,
						"expires": 1766242298,
						"game_open_id": None,
						"game_open_id_enable": False
					}
					"""
					data = res.json()
					code = data['code']
					if code == 0:
						if data['access_key'] == '':
							return data['message'], False
						if data['is_real_name'] == 0:
							return '未实名', False
						if data['user_limit_status'] != 0:
							return '限制登录', False
						return res.json()['access_key'], True
					elif code == 200000:
						params['timestamp'] = str(int(time.time() * 1000))
						return self.bili_get_access_key(params)
					elif code == -662:
						return '获取access_key失败', False
					elif code == 200001:
						return data['message'], False
					else:
						print(res.status_code, res.text)
						times += 1
				else:
					print(res.status_code, res.text)
					times += 1
				if times >= MAX_RETRY_TIMES:
					return '获取access_key超时', False
			except:
				pass
			self.y_sleep(2)
			self.change_proxy()
	
	def bili_login_by_sign(self, access_key):
		data_data = {'access_key': access_key}
		data = {
			'app_id': self.app_id,
			'channel_id': '14',
			'data': json.dumps(data_data),
			'device': self.device_id,
			"sign": get_sign(self.app_id, self.channel_id, json.dumps(data_data), self.device_id)
		}
		headers = {
			"Accept": "*/*",
			"Accept-Encoding": "deflate, gzip",
			"Content-Type": "application/json",
			"Host": "hkrpg-sdk.mihoyo.com",
			"User-Agent": "UnityPlayer/2019.4.34f1 (UnityWebRequest/1.0, libcurl/7.75.0-DEV)",
			"X-Unity-Version": "2019.4.34f1",
			"x-rpc-app_version": "2.43.1.0",
			"x-rpc-channel_id": self.channel_id,
			"x-rpc-channel_version": "2.43.1.0",
			"x-rpc-client_type": "3",
			"x-rpc-combo_version": "2.43.1",
			"x-rpc-device_fp": self.device_fp,
			"x-rpc-device_id": self.device_id,
			"x-rpc-device_model": self.device_model,
			"x-rpc-device_name": self.device_name,
			"x-rpc-game_biz": "hkrpg_cn",
			"x-rpc-goods_third_party": "unsupported",
			"x-rpc-language": "zh-cn",
			"x-rpc-lifecycle_id": get_uuid(),
			"x-rpc-mdk_version": "2.43.1.0",
			"x-rpc-payment_version": "2.43.1",
			"x-rpc-sdk_version": "2.43.1.0",
			"x-rpc-sub_channel_id": "0",
			"x-rpc-sys_version": "Windows 10  (10.0.19044) 64bit"
		}
		times = 0
		url = 'https://hkrpg-sdk.mihoyo.com/hkrpg_cn/combo/granter/login/v2/login'
		while self.working:
			try:
				res = self.conn_by_proxy.conn.post(url, json=data, headers=headers)
				res.close()
				if res.status_code == 200 and 'combo_token' in res.text:
					combo_token = res.json()['data']['combo_token']
					uid = res.json()['data']['open_id']
					REDIS.hset("6:token", self.user, f'{combo_token}----{access_key}----{uid}')
					return res.json(), combo_token
				else:
					times += 1
				if times >= MAX_RETRY_TIMES:
					return 'B服登录超时', ''
			except:
				pass
			self.y_sleep(2)
			self.change_proxy()
	
	def bili_get_captcha(self) -> dict | str:
		path = f'https://wpg-api.biligame.com/api/pcg/start_captcha?game_id=7840&_=0'
		times = 0
		while self.working:
			try:
				res = self.conn_request("GET", path)
				if res.status_code == 200:
					if res.json()['code'] == 0:
						"""
						{
							"code": 0,
							"data": {
								"captcha_type": 1,
								"challenge": "44b984fd96681b1d01ac3c2b7c6fcb82",
								"gs": 1,
								"gt": "245273d7fa73f7b657098bf7441fe12f",
								"userid": "ae40370ad9844e0aaa974a2bc27a184d"
							},
							"request-id": "3414feb0c5e111f09ba93a99e982708d",
							"request_id": "3414feb0c5e111f09ba93a99e982708d",
							"timestamp": 1763623148059,
							"ts": 1763623148059
						}
						"""
						return res.json()['data']
					else:
						return 'B服请求极验异常'
				else:
					times += 1
				if times >= MAX_RETRY_TIMES:
					return 'B服请求极验超时'
			except:
				pass
			self.y_sleep(2)
			self.change_proxy()
	
	def bili_rsa(self):
		# 构造 URL
		query = bili_encode(bili_new_params())
		url = "https://wpg-api.biligame.com/api/pcg/rsa?" + query
		while self.working:
			try:
				resp = self.conn_request(Method.POST, url)
				data = resp.json()
				code = int(data.get("code", -1))
				hash_val = data.get("hash", "")
				rsa_pem = data.get("rsa_key", "")
				
				if code == 0 and hash_val:
					try:
						self.rsa_key = serialization.load_pem_public_key(rsa_pem.encode())
					except:
						return None
					return hash_val
				return None
			except:
				e = traceback.format_exc()
				pass
			self.y_sleep(2)
			self.change_proxy()
	
	def format_phone_info(self):
		if 'COM' in self.user.upper() and '|' in self.user:
			self.com, self.phone = self.user.split('|')
			self.com = self.com.upper().replace('COM', '')
		else:
			self.com = ''
			self.phone = self.user
	
	def sf_get_mhy_code(self):
		times = 0
		# 四方 http://sms.szfangmm.com:3000/U3K9t5qKkxoBBARYPJskfe
		sf_token = self.pwd.split('3000/')[-1]
		self.pwd = 'http://sms.szfangmm.com:3000/api/smslist?token=' + sf_token
		while self.working:
			try:
				res = self.conn_request(Method.GET, self.pwd)
				data = res.json()[0]
				if res.status_code == 200 and '验证码' in res.text and self.com == str(data['com']):
					code = re.sub(r'.*：(\d{6}).*', r'\1', data['content'])
					self.log(f'四方接码: {code}')
					return code
				else:
					times += 1
				if times >= 10:
					text = '四方接码超时'
					self.log(text)
					return text
			except:
				pass
			self.y_sleep(3)
			self.change_proxy()
	
	def other_get_mhy_code(self):
		if 'activationCode' in self.pwd:
			# 月卡 http://192.243.125.222:8081/?activationCode=zsJ16l
			lst = self.pwd.split('?')
			lst.insert(1, 'api/sms/search?')
			self.pwd = ''.join(lst)
		times = 0
		while self.working:
			try:
				res = self.conn_request_no_proxy(Method.GET, self.pwd)
				if res.status_code == 200:
					if res.json().get('data'):
						code = res.json()['data']['message']
						self.log(f'月卡接码: {code}')
						return code
					else:
						times += 1
				if times >= 10:
					text = '月卡接码超时'
					self.log(text)
					return text
			except:
				pass
			self.y_sleep(3)
	
	def MiHoYoPhoneLoginCaptchaWithProxy(self):
		self.format_phone_info()
		ret = self.get_fp()
		if not ret:
			return '获取fp失败', 500
		msg = self.mhy_phone_captcha()
		if msg != 'OK':
			return {'error': msg}, 400
		self.log('开始接码')
		# code = ''
		if self.com == '':
			code = self.other_get_mhy_code()
		else:
			code = self.sf_get_mhy_code()
		if '超时' not in code:
			msg, token = self.mhy_login_by_phone(code)
			if token == '':
				return {'error': msg}, 400
			else:
				return {
					'result': msg,
					'combo_token': token['combo_token'],
					'cookie_token': token['cookie_token_v2'],
				}, 200
		else:
			return {'error': '未取到短信内容'}, 400
	
	def MiHoYoWebLogin(self):
		ret = self.get_fp()
		if not ret:
			return '获取fp失败', 500
		ret, msg = self.web_login()
		if ret:
			return {'result': ret, 'msg': msg}, 200
		else:
			return {'error': msg}, 400
	
	def mhy_login_by_phone(self, code):
		self.get_fp()
		path = "https://passport-api.mihoyo.com/account/ma-cn-passport/web/loginByMobileCaptcha"
		data = {
			"area_code": rsa_encrypt(self.city, '+86'),
			"mobile": rsa_encrypt(self.city, self.phone),
			'captcha': code
		}
		headers = {
			"Content-Type": "application/json",
			"x-rpc-device_fp": self.device_fp,
			"x-rpc-app_id": "c90mr1bwo2rk",
			"x-rpc-game_biz": "hkrpg_cn",
			"x-rpc-client_type": "1",
			"x-rpc-device_id": self.device_uid,
			"Referer": "https://sr.mihoyo.com/",
			"User-Agent": "hkrpg/2 CFNetwork/3826.600.41 Darwin/24.6.0",
			"x-rpc-device_model": "iPhone12,1",
			"x-rpc-device_name": "iPhone",
			"x-rpc-account_version": "2.39.0",
			"x-rpc-app_version": "3.5.0",
			"x-rpc-sdk_version": "2.39.0",
			"x-rpc-sys_version": "18.6.2"
		}
		times = 0
		while self.working:
			try:
				res = self.conn_by_proxy.conn.post(path, json=data, headers=headers)
				res.close()
				if res.status_code == 200 and 'message' in res.json():
					message = res.json()['message']
					if message == '验证码错误':
						return message, ''
					elif message == "OK":
						msg, status_code = self.get_combo_token_by_len160_cookie_token_v2()
						if status_code == 200:
							return res.json(), msg
						else:
							return msg, ''
					else:
						times += 1
				else:
					times += 1
				if times >= MAX_RETRY_TIMES:
					return '验证码登录超时', ''
			except:
				pass
			self.y_sleep(2)
			self.change_proxy()
	
	def get_stoken_by_len160_cookie_token_v2(self):
		headers = {'x-rpc-app_id': 'c90mr1bwo2rk'}
		path = 'https://passport-api.mihoyo.com/account/ma-cn-session/web/webVerifyForGame'
		times = 0
		while self.working:
			try:
				res = self.conn_by_proxy.conn.post(path, headers=headers)
				res.close()
				if res.status_code == 200 and 'token' in res.text:
					self.stoken = res.json()['data']['token']
					return True
				else:
					times += 1
				if times >= MAX_RETRY_TIMES:
					return False
			except:
				pass
	
	def get_combo_token_by_len160_cookie_token_v2(self):
		if self.city in ['1', '6']:
			path = 'https://hkrpg-sdk.mihoyo.com/hkrpg_cn/combo/granter/login/webLogin'
		else:
			path = 'https://hkrpg-sdk-os.hoyoverse.com/hkrpg_global/combo/granter/login/webLogin'
		data = {
			"app_id": self.app_id,
			"channel_id": self.channel_id
		}
		headers = {
			"Content-Type": "application/json",
			"x-rpc-device_fp": self.device_fp,
			"x-rpc-device_id": self.device_uid,
			"x-rpc-channel_id": "1",
			"x-rpc-client_type": "22",
			"x-rpc-mdk_version": "2.42.0"
		}
		if self.city in ['1', '6']:
			headers['x-rpc-game_biz'] = "hkrpg_cn"
		else:
			headers['x-rpc-game_biz'] = "hkrpg_global"
		times = 0
		while self.working:
			try:
				res = self.conn_by_proxy.conn.post(path, json=data, headers=headers)
				res.close()
				if res.status_code == 200 and 'combo_token' in res.text:
					cookie = self.conn_by_proxy.conn.cookies.get_dict()
					"""
					cookie = {
						"account_id": "453155809",
						"account_id_v2": "453155809",
						"account_mid_v2": "0rx7ethcpz_mhy",
						"cookie_token": "PvJPea9kIvx7NM6aC2ENq04xoo6IJOwqeZCn8LHR",
						"cookie_token_v2": "v2_Ap9QyiJDLQTMQbXZIiZfWwKjukWorpgxx7m91Nnklet9FVN__q2nahCLS50mCegsTvcSvlF39qSovUcq2SQCSju6TR4AZ2Z_RQWNWtkWpkPuyg5498o2t5E7C78ty1WkCNvEKj4mljA8ohbFF_bPuMsp.CAE=",
						"ltmid_v2": "0rx7ethcpz_mhy",
						"ltoken": "rNDCuyGcuYrO2TQ75ayECZAEGrQyef5VS8LsnyzK",
						"ltoken_v2": "v2_VfIJxyqbKUbH3hfNQR-13RDo20CyDDwU7MOVVqEzT2EIkAgGYd72rfWWnsVzCGf1gK2VJPgLbvhnb4LTlbsFjs21cVD1qBRblCbP0vr8Npzdt3dgKCgkz4rYKiP8HUH7awZOC5r2Ohd8orlrX1p3ibGt.CAE=",
						"ltuid": "453155809",
						"ltuid_v2": "453155809",
						"uni_web_token": "be0711452e704a638238ac7d984ee4b90rx7ethcpz_mhy"
					}
					res.json() = {
					"retcode": 0,
					"message": "OK",
					"data": {
						"combo_id": "0",
						"open_id": "453155809",
						"combo_token": "v2_258d96da04a7cb8a5da3897e8500cdd06c780690",
						"data": "{\"guest\":false}",
						"heartbeat": false,
						"account_type": 1,
						"fatigue_remind": null
						}
					}
					"""
					combo_token = res.json()['data']['combo_token']
					cookie_token_v2 = cookie['cookie_token_v2']
					uid = res.json()['data']['open_id']
					mid = cookie['account_mid_v2']
					if self.city in ['1']:
						r_db = 1
					else:
						r_db = 2
					REDIS.hset(f"{r_db}:token", self.user, f'{combo_token}----{cookie_token_v2}----{uid}----{mid}')
					return {
						'combo_token': combo_token,
						'cookie_token_v2': cookie_token_v2,
						'uid': uid,
						'mid': mid,
					}, 200
				else:
					times += 1
				if times >= MAX_RETRY_TIMES:
					return '获取combo token超时', 400
			except:
				pass
			self.y_sleep(2)
			self.change_proxy()
	
	def mhy_phone_captcha(self, aigis=None, data=None):
		path = 'https://passport-api.mihoyo.com/account/ma-cn-verifier/verifier/createLoginCaptcha'
		if not data:
			data = {
				"mobile": rsa_encrypt(self.city, self.phone),
				"area_code": rsa_encrypt(self.city, '+86'),
			}
		# 客户端抓包
		headers = {
			"Accept": "*/*",
			"Content-Length": "372",
			"Content-Type": "application/json",
			"Host": "passport-api.mihoyo.com",
			"x-rpc-app_id": "c90mr1bwo2rk",
			"x-rpc-channel_id": "1",
			"x-rpc-channel_version": "2.43.0.176",
			"x-rpc-client_type": "3",
			"x-rpc-device_fp": self.device_fp,
			"x-rpc-device_id": self.device_id,
			"x-rpc-device_model": "X99-BD4",
			"x-rpc-device_name": "YYYTC",
			"x-rpc-game_biz": "hkrpg_cn",
			"x-rpc-language": "zh-cn",
			"x-rpc-lifecycle_id": self.lifecycle_id,
			"x-rpc-mdk_version": "2.43.0.176",
			"x-rpc-sdk_version": "2.43.0.176",
			"x-rpc-sys_version": "Windows 10"
		}
		# cz代码
		# headers = {
		# 	"Content-Type": "application/json",
		# 	"x-rpc-device_fp": self.device_fp,
		# 	"x-rpc-app_id": "c90mr1bwo2rk",
		# 	"x-rpc-game_biz": "hkrpg_cn",
		# 	"x-rpc-client_type": "22",
		# 	"x-rpc-device_id": self.device_uid,
		# 	"Referer": "https://user.mihoyo.com/",
		# 	"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.57",
		# 	"x-rpc-device_model": "Microsoft Edge 113.0.1774.57",
		# 	"x-rpc-device_name": "Microsoft Edge",
		# 	"x-rpc-device_os": "Windows 10 64-bit",
		# 	"x-rpc-lifecycle_id": "9821e34f41",
		# 	"x-rpc-mi_referrer": "https://user.mihoyo.com/login-platform/index.html?client_type=22&app_id=c90mr1bwo2rk&theme=rpg&token_type=4&game_biz=hkrpg_cn&message_origin=https%3A%2F%2Fsr.mihoyo.com&succ_back_type=message%3Alogin-platform%3Alogin-success&fail_back_type=message%3Alogin-platform%3Alogin-fail&ux_mode=popup&iframe_level=1&extra_trace=1#/login/captcha",
		# 	"x-rpc-sdk_version": "2.44.0"
		# }
		
		# 网页因缘抓包
		# headers = {
		# 	"accept": "application/json, text/plain, */*",
		# 	"accept-language": "zh-CN,zh;q=0.9",
		# 	"cache-control": "no-cache",
		# 	"content-type": "application/json",
		# 	"pragma": "no-cache",
		# 	"sec-ch-ua": "\"Chromium\";v=\"142\", \"Google Chrome\";v=\"142\", \"Not_A Brand\";v=\"99\"",
		# 	"sec-ch-ua-mobile": "?0",
		# 	"sec-ch-ua-platform": "\"Windows\"",
		# 	"sec-fetch-dest": "empty",
		# 	"sec-fetch-mode": "cors",
		# 	"sec-fetch-site": "same-site",
		# 	"x-rpc-app_id": "ess4np01pji8",
		# 	"x-rpc-client_type": "4",
		# 	"x-rpc-device_fp": self.device_fp,
		# 	"x-rpc-device_id": self.device_uid,
		# 	"x-rpc-device_model": "Chrome%20142.0.0.0",
		# 	"x-rpc-device_name": "Chrome",
		# 	"x-rpc-device_os": "Windows%2010%2064-bit",
		# 	"x-rpc-game_biz": "abc_cn",
		# 	"x-rpc-lifecycle_id": "a7f4562720",
		# 	"x-rpc-mi_referrer": "https://user.mihoyo.com/login-platform/index.html?app_id=ess4np01pji8&theme=abc&token_type=4&game_biz=abc_cn&fs_ql_w=0&fs_ql_m=0&message_origin=https%253A%252F%252Fyyjl.mihoyo.com&succ_back_type=message%253Alogin-platform%253Alogin-success&fail_back_type=message%253Alogin-platform%253Alogin-fail&ux_mode=popup&iframe_level=1#/login/captcha",
		# 	"x-rpc-sdk_version": "2.44.0"
		# }
		
		if aigis:
			headers['X-Rpc-Aigis'] = aigis
		self.conn_by_proxy.conn.headers = headers
		times = 0
		while self.working:
			try:
				res = self.conn_by_proxy.conn.post(path, data=json.dumps(data))
				res.close()
				if res.status_code == 200 and 'message' in res.json():
					message = res.json()['message']
					print(message)
					if message == '账号或密码错误' or '您的账号存在安全风险' in message or message == 'OK':
						return message
					elif message == '请求过于频繁，请稍后再试':
						pass
					elif message == '请求频繁，请稍后再试':
						return message
						self.log('触发极验')
						"""
							{
							    "data": "{"success":1,"gt":"84a0028ac7205630c6defaea81bd304d","new_captcha":1,"use_v4":true,"risk_type":"icon"}",
							    "mmt_type": 1,
							    "session_id": "ac8848d9755b462b9e0fc3b406f9d080"
							}
						"""
						json_data = json.loads(res.headers['x-rpc-aigis'])
						session_id = json_data['session_id']
						captcha_id = json.loads(json_data['data'])['gt']
						# captcha_id = 'fea961eab2cbfc565bcbcce80d171553'
						gt_obj = Gt4Obj(captcha_id, session_id)
						for i in range(MAX_RETRY_TIMES):
							aigis = gt_obj.geetest_verify()
							gt_obj.conn.close()
							if aigis:
								return self.mhy_phone_captcha(aigis, data)
						return f'极验验证超时'
					elif message == '图片验证码失败':
						headers.pop('x-rpc-aigis')
					else:
						times += 1
				else:
					times += 1
				if times >= MAX_RETRY_TIMES:
					return f'发送短信超时'
			except:
				e = traceback.format_exc()
				pass
			self.y_sleep(2)
			self.change_proxy()
	
	# v370 cz
	def bh_login(self, risky):
		path = 'https://api-sdk.mihoyo.com/hkrpg_cn/mdk/shield/api/login'
		times = 0
		combo_token = ''
		while self.working:
			device = Device()
			headers = {
				"Content-Type": "application/json",
				"x-rpc-device_model": device.ext_fields.ext.model,
				"User-Agent": "HSoDv2CN/11.2.3 CFNetwork/1496.0.7 Darwin/23.5.0",
				"x-rpc-language": "zh-cn",
				"x-rpc-lifecycle_id": get_uuid(),
				"x-rpc-device_name": device.ext_fields.ext.deviceName,
				"x-rpc-device_fp": self.device_fp,
				"x-rpc-mdk_version": device.ext_fields.ext.packageVersion,
				"x-rpc-client_type": "5",
				"x-rpc-device_id": self.device_uid,
				"x-rpc-channel_version": device.ext_fields.ext.packageVersion,
				"x-rpc-channel_id": "1",
				"x-rpc-sys_version": device.ext_fields.ext.osVersion,
				"x-rpc-game_biz": "hyg_cn",
				"Accept-Encoding": "gzip, deflate, br",
				"x-rpc-risky": f"id={risky};",
			}
			try:
				data = {
					'account': self.user,
					'password': rsa_encrypt(self.city, self.pwd),
					'is_crypto': True
				}
				res = self.conn_by_proxy.conn.post(path, json=data, headers=headers)
				res.close()
				if res.status_code == 200 and 'message' in res.json():
					message = res.json()['message']
					if message == 'OK':
						self.game_token = res.json()['data']['account']['token']
						self.get_stoken_by_game_token()
						combo_token = self.get_combo_token_by_stoken()['data']['combo_token']
						return res.json(), combo_token
					else:
						return f'登录失败: {message}', combo_token
				else:
					times += 1
				if times >= MAX_RETRY_TIMES:
					return '请求失败，超过重试次数', combo_token
			except:
				pass
			self.y_sleep(2)
			self.change_proxy()
	
	@staticmethod
	def now_ts():
		return int(time.time() * 1000)
	
	def create_mmt(self):
		path = 'https://webapi.account.mihoyo.com/Api/create_mmt'
		while self.working:
			try:
				now = self.now_ts()
				params = {
					"scene_type": 1,
					"now": now,
					# "reason": "user.mihoyo.com#/login/password",
					"reason": "webstatic.mihoyo.com",
					"action_type": "login_by_password",
					"account": self.user,
					"t": now + 1
				}
				res = self.conn_request(Method.GET, path, params)
				if res.status_code == 200 and '成功' in res.text:
					data = res.json().get('data')
					mmt_key = data['mmt_data']['mmt_key']
					return mmt_key
			except:
				e = traceback.format_exc()
				pass
			self.y_sleep(2)
	
	# 300 CNY
	def gt4_verify(self, mmt_key):
		path = f'http://127.0.0.1:5000/geetest_verify'
		while self.working:
			try:
				data = {
					'captcha_id': '0b2abaab0ad3f4744ab45342a2f3d409',
					'user_info': json.dumps({'mmt_key': mmt_key}),
					'proxies': '075644:321d6b@48224119.sd.proxy.xiequ.cn:2829'
				}
				res = self.conn_request_no_proxy(Method.POST, path, data)
				if res.status_code == 200:
					return res.text.replace('\n', '')
			except:
				pass
			self.y_sleep(2)
	
	# 废弃
	def login_by_password(self):
		# path = 'https://webapi.account.mihoyo.com/Api/login_by_password'  # 老通行证登录 废了
		# path = 'https://api-takumi.mihoyo.com/account/auth/api/webLoginByPassword'
		path = 'https://passport-api-v4.mihoyo.com/account/auth/api/webLoginByPassword'  # 老活动登录 废了
		mmt_key = None
		gt4_data = None
		while self.working:
			try:
				mmt_key = self.create_mmt()
				gt4_data = self.gt4_verify(mmt_key)
				break
			except:
				pass
		while self.working:
			try:
				data = {
					"t": self.now_ts(),
					"is_bh2": False,
					"account": self.user,
					"password": rsa_encrypt(self.city, self.pwd),
					"is_crypto": True,
					"mmt_key": mmt_key,
					"geetest_v4_data": gt4_data,
					"token_type": 4,
					"support_reactivate": True
				}
				res = self.conn_by_proxy.conn.post(url=path, json=data, timeout=5)
				res.close()
				if res.status_code == 200 and 'weblogin_token' in res.text:
					account_info = res.json()['data']['account_info']
					self.account_id = account_info['account_id']
					self.weblogin_token = account_info['weblogin_token']
					self.log('登录成功')
					break
			except:
				pass
			self.y_sleep(2)
	
	# 服务器登录
	def remote_login(self):
		path = 'http://115.190.5.154:8080/api/login'
		while self.working:
			try:
				data = {
					'user': self.user,
					'pass': self.pwd,
				}
				res = self.conn_request(Method.POST, path, data)
				if res.status_code == 200 and 'combo_token' in res.text:
					data = json.loads(res.json()['result'])['data']
					return res.json()['combo_token'], int(data['user_info']['aid'])
			except:
				pass
			self.y_sleep(2)
	
	# 组装接口
	def bh_geetest(self) -> str:
		data = {
			"action_type": "login",
			"api_name": "/shield/api/login",
			"username": self.user
		}
		self.log('bh_geetest')
		headers = {
			"Host": "gameapi-account.mihoyo.com",
			"User-Agent": "UnityPlayer/2017.4.18f1 (UnityWebRequest/1.0, libcurl/7.51.0-DEV)",
			"Accept": "*/*",
			"Accept-Encoding": "identity",
			"Content-Type": "application/json",
			"x-rpc-client_type": "3",
			"x-rpc-sys_version": "Windows 10  (10.0.0) 64bit",
			"x-rpc-device_id": self.device_id,
			"x-rpc-device_model": self.device_model,
			"x-rpc-device_name": self.device_name,
			"x-rpc-mdk_version": rpc_ver,
			"x-rpc-sdk_version": rpc_ver,
			"x-rpc-channel_version": rpc_ver,
			"x-rpc-app_version": rpc_ver,
			"x-rpc-channel_id": "1",
			"x-rpc-sub_channel_id": "1",
			"x-rpc-language": "zh-cn",
			"x-rpc-game_biz": rpc_game_biz,
			"x-rpc-combo_version": rpc_ver1,
			"x-rpc-payment_version": rpc_ver1,
			"x-rpc-goods_third_party": "unsupported",
			"x-rpc-device_fp": self.device_fp,
			"x-rpc-lifecycle_id": "null",
			"X-Unity-Version": "2017.4.18f1",
		}
		path = "https://gameapi-account.mihoyo.com/account/risky/api/check"
		while self.working:
			try:
				res = self.conn_by_proxy.conn.post(path, json=data, headers=headers, timeout=5)
				res.close()
				if res.status_code == 200 and '' in res.text:
					result = res.json()
					jy_id = result.get("data", {}).get("id", "")
					if jy_id == '':
						self.y_sleep(6)
					return str(jy_id)
			except:
				pass
			self.y_sleep(2)
			self.change_proxy()
	
	def get_game_token(self, jy_id):
		self.log('开始登录')
		headers = {
			"Host": "api-sdk.mihoyo.com",
			"User-Agent": "UnityPlayer/2017.4.18f1 (UnityWebRequest/1.0, libcurl/7.51.0-DEV)",
			"Accept": "*/*",
			"Accept-Encoding": "identity",
			"Content-Type": "application/json",
			"x-rpc-client_type": "3",
			"x-rpc-sys_version": "Windows 10  (10.0.0) 64bit",
			"x-rpc-device_id": self.device_id,  # 外部传入
			"x-rpc-device_model": self.device_model,
			"x-rpc-device_name": self.device_name,  # 外部传入
			"x-rpc-mdk_version": rpc_ver,
			"x-rpc-sdk_version": rpc_ver,
			"x-rpc-channel_version": rpc_ver,
			"x-rpc-app_version": rpc_ver,
			"x-rpc-channel_id": "1",
			"x-rpc-sub_channel_id": "1",
			"x-rpc-language": "zh-cn",
			"x-rpc-game_biz": rpc_game_biz,
			"x-rpc-combo_version": rpc_ver1,
			"x-rpc-payment_version": rpc_ver1,
			"x-rpc-goods_third_party": "unsupported",
			"x-rpc-device_fp": '38d7fd606c7f4',
			"x-rpc-lifecycle_id": "null",
			"x-rpc-risky": f"id={jy_id};c=;s=;v=",
			"X-Unity-Version": "2017.4.18f1",
		}
		path = f"https://api-sdk.mihoyo.com/{rpc_game_biz}/mdk/shield/api/login"
		times = 0
		while self.working:
			try:
				data = {
					"account": self.user,
					"password": rsa_encrypt(self.city, self.pwd),
					"is_crypto": True
				}
				res = self.conn_by_proxy.conn.post(path, json=data, headers=headers, timeout=5)
				res.close()
				if res.status_code == 200:
					if 'token' in res.text:
						account = res.json()['data']['account']
						self.game_token = account['token']
						self.uid = account['uid']
						self.log(f'登录成功')
						return res.json()
					elif '账号或密码错误' in res.text:
						self.log(f'账号或密码错误')
						break
					elif '风险' in res.text:
						self.log(res.json()['message'])
					else:
						if times <= 3:
							self.log(f'尝试登录：{times}')
						else:
							self.log(res.json()['message'])
							break
			except:
				pass
			self.y_sleep(2)
			self.change_proxy()
	
	def get_stoken_by_game_token(self):
		url = 'https://api-takumi.mihoyo.com/account/ma-cn-session/app/getTokenByGameToken'
		headers = {
			'x-rpc-app_id': rpc_app_id
		}
		while self.working:
			try:
				data = {"account_id": int(self.uid), "game_token": self.game_token}
				res = self.conn_by_proxy.conn.post(url, headers=headers, json=data)
				res.close()
				self.stoken = res.json()['data']['token']['token']
				break
			except:
				pass
			self.y_sleep(2)
			self.change_proxy()
	
	def get_cookie_token_by_game_token(self):
		url = f'https://api-takumi.mihoyo.com/auth/api/getCookieAccountInfoByGameToken?account_id={self.uid}&game_token={self.game_token}'
		while self.working:
			try:
				res = self.conn_request(Method.GET, url)
				if res.status_code == 200 and 'cookie_token' in res.text:
					self.cookie_token = res.json()['data']['cookie_token']
					break
			except:
				pass
			self.y_sleep(2)
	
	def get_combo_token_by_stoken(self):
		path = "https://hkrpg-sdk.mihoyo.com/hkrpg_cn/combo/granter/login/v2/login"
		headers = {
			"Content-Type": "application/json",
			"x-rpc-device_model": self.device_model,
			"User-Agent": "HSoDv2CN/11.2.3 CFNetwork/1496.0.7 Darwin/23.5.0",
			"x-rpc-language": "zh-cn",
			"x-rpc-lifecycle_id": get_uuid(),
			"x-rpc-device_name": self.device_name,
			"x-rpc-device_fp": self.device_fp,
			"x-rpc-mdk_version": rpc_ver,
			"x-rpc-client_type": "1",
			"x-rpc-device_id": self.device_id,
			"x-rpc-channel_version": rpc_ver,
			"x-rpc-channel_id": "1",
			"x-rpc-sys_version": rpc_ver,
			"x-rpc-game_biz": rpc_game_biz,
			"Accept-Encoding": "gzip, deflate, br",
		}
		while self.working:
			try:
				data_data = {"uid": str(self.uid), "guest": False, "token": self.stoken}
				data = {
					"app_id": self.app_id,
					"channel_id": self.channel_id,
					"data": json.dumps(data_data),
					"device": self.device_id,
					"sign": get_sign(self.app_id, self.channel_id, json.dumps(data_data), self.device_id),
				}
				res = self.conn_by_proxy.conn.post(path, headers=headers, json=data)
				res.close()
				if res.status_code == 200 and 'combo_token' in res.text:
					"""
					{
						"retcode": 0,
						"message": "OK",
						"data": {
							"combo_id": "0", "open_id": "412373617",
							"combo_token": "v2_ed47ff987420b99fa182f90231e56adc6865db10",
							"data": "{\"guest\":false}",
							"heartbeat": false,
							"account_type": 1, "fatigue_remind": null
						}
					}
					"""
					return res.json()
			except:
				pass
			self.y_sleep(2)
			self.change_proxy()
	
	# 5000 CNY
	def bh_geetest_login_task(self):
		self.get_fp()
		while self.working:
			try:
				jy_id = self.bh_check()
				game_token = self.get_game_token(jy_id)
				if game_token:
					self.get_cookie_token_by_game_token()
					self.get_stoken_by_game_token()
					combo_token = self.get_combo_token_by_stoken()
					break
			except:
				pass


if __name__ == '__main__':
	info_ = {
		'user': 'katzi99@163.com',
		'pass': 'BA5201314.4',
		# 'user': 'vedenev2025@list.ru',
		# 'pass': 'r2z3`YlDNVpx',
		# 'user': 'COM120|17287256208',
		# 'pass': 'http://sms.newszfang.vip:3000/2jLuuGbqVVfVy6ndDKuTCi',
		# 'user': 'asher48cya@outlook.com',
		# 'pass': 'whircx78433',
		'city': '1'
	}
	proxy_ = '075644:321d6b@48224119.sd.proxy.xiequ.cn:2829'
	obj = MHYObj(info_)
	obj.MiHoYoWebLogin()
# obj.MiHoYoPhoneLoginCaptchaWithProxy()
# obj.bh_geetest_login_task()
# ret_ = obj.BiliLogHandle()
# print(ret_)
