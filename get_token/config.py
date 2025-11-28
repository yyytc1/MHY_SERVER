# coding : utf-8
# @Time : 2025/11/27 15:15 
# @Author : Adolph
# @File : config.py 
# @Software : PyCharm
import redis

# ============ Redis ============
REDIS_HOST = "47.105.189.174"
REDIS_PORT = 6379
REDIS_PASSWORD = "qq197603"  # 若无密码填 None
REDIS_DB = 0

REDIS = redis.Redis(
	host=REDIS_HOST,
	port=REDIS_PORT,
	password=REDIS_PASSWORD,
	db=REDIS_DB,
	decode_responses=True  # 直接返回 str
)

# ============ REMOTE ============
REMOTE_UPLOAD_HOST = '118.25.65.191'
REMOTE_UPLOAD_URL = f'http://{REMOTE_UPLOAD_HOST}:6789/orders/upload'
THREAD_NUM = 100

res_404 = '<!DOCTYPE html><html><head><title>404 Not Found</title></head><body><h1>Not Found</h1><p>The requested URL was not found on this server.</p></body></html>', 404
