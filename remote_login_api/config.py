# coding : utf-8
# @Time : 2025/9/5 0:00 
# @Author : Adolph
# @File : config.py 
# @Software : PyCharm
import json
import os.path
from queue import Queue

import execjs
import redis

from 打包 import w_path

config_file = 'config.json'
error_file = 'error.txt'
account_queue = Queue()

with open(w_path, 'r', encoding='utf-8-sig') as f:
	ctx = execjs.compile(f.read())

"""
d47umitaylmo  nap_cn	zzz
c90mr1bwo2rk  hkrpg_cn  sr
dw9y09jqjpxc  plat_cn   通行证
c8zzish3z5z4  bh3_cn    bh3
ccv4svj20z5s  bh2_cn    bh2
cb6iq1v11ibk  nxx_cn    事件簿

x-rpc-client_type 4：网页 3：客户端 2：移动端

https://bbs-api.miyoushe.com/user/api/getUserFullInfo?uid=453154415
"""

game_info = {
	'hkrpg_cn': 'c90mr1bwo2rk',
	'nap_cn': 'd47umitaylmo',
	'plat_cn': 'dw9y09jqjpxc',
	'bh3_cn': 'c8zzish3z5z4',
	'bh2_cn': 'ccv4svj20z5s',
	'nxx_cn': 'cb6iq1v11ibk',
}
rpc_game_biz = 'hkrpg_cn'
rpc_app_id = game_info[rpc_game_biz]

DEFAULT_CONFIG = {
	"gt_icon_url": "http://115.190.5.154:5000/jy",
	"rpc_ver": "2.28.0.0",
	"rpc_ver1": "2.28.0",
	"max_retry_times": 3,
	"server_port": 8080,
	"proxy_url": "http://need1.dmdaili.com:7771/dmgetip.asp?apikey=9308a72e&pwd=6f556d52a7d7698aa818adb88e227bfe&getnum=200&httptype=1&geshi=0&fenge=1&fengefu=&operate=all",
	"redis": {
		"host": "47.105.189.174",
		"port": 6379,
		"password": "qq197603",
		"db": 0
	},
	"gt3": {
		"space": "http://115.190.5.154:18898",
		"nine": "http://47.104.101.1:19197",
		"word": "http://115.190.5.154:18889",
		"slide": "http://115.190.5.154:19197"
	}
}


def load_config() -> dict:
	"""读配置，缺字段自动用默认值补全"""
	if not os.path.exists(config_file):
		# 第一次：写出默认配置
		with open(config_file, 'w', encoding='utf8') as f:
			f.write(json.dumps(DEFAULT_CONFIG, indent=4))
		return DEFAULT_CONFIG.copy()
	
	with open(config_file, 'r', encoding='utf8') as f:
		user_cfg = json.load(f)
	
	# 递归补全缺省字段
	def merge(src, dst):
		for k, v in src.items():
			if k not in dst:
				dst[k] = v
			elif isinstance(v, dict) and isinstance(dst[k], dict):
				merge(v, dst[k])
		return dst
	
	return merge(DEFAULT_CONFIG, user_cfg)


# 全局配置对象（导入即可用）
cfg = load_config()

# 导出常用变量（可选）
REDIS_HOST = cfg["redis"]["host"]
REDIS_PORT = cfg["redis"]["port"]
REDIS_PASSWORD = cfg["redis"]["password"]
REDIS_DB = cfg["redis"]["db"]

gt_icon_url = cfg["gt_icon_url"]
rpc_ver = cfg["rpc_ver"]
rpc_ver1 = cfg["rpc_ver1"]
MAX_RETRY_TIMES = cfg["max_retry_times"]
server_port = cfg["server_port"]
proxy_url = cfg["proxy_url"]
gt3 = cfg["gt3"]
space_orc_url = gt3.get('space')
nine_orc_url = gt3.get('nine')
word_orc_url = gt3.get('word')
slide_orc_url = gt3.get('slide')

# ========== 远程 Redis 配置 ==========
REDIS = redis.Redis(
	host=REDIS_HOST,
	port=REDIS_PORT,
	password=REDIS_PASSWORD,
	db=REDIS_DB,
	decode_responses=True  # 直接返回 str
)

if __name__ == '__main__':
	pass
