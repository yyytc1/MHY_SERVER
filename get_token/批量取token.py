# coding : utf-8
# @Time : 2025/11/24 18:46 
# @Author : Adolph
# @File : 批量取token.py 
# @Software : PyCharm
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# ========== 可配置区域 ==========
URL = "http://127.0.0.1:1234/api/getTokenByAccount"  # 换成你的接口
METHOD = "POST"  # GET/POST/PUT...
TIMEOUT = 120  # 单次请求超时
THREADS = 100  # 并发线程数
HEADERS = {
	"User-Agent": "Mozilla/5.0",
	"Content-Type": "application/json"
}
# =================================

success = 0
failure = 0


def do_one(info):
	"""单线程任务：发一次请求"""
	global success, failure
	user = info[0]
	try:
		payload = {
			'account': info[0],
			'password': '123123',
		}
		if METHOD.upper() == "GET":
			resp = requests.get(URL, headers=HEADERS, timeout=TIMEOUT)
		else:
			resp = requests.request(
				METHOD, URL, headers=HEADERS, json=payload, timeout=TIMEOUT
			)
		if resp.status_code == 200:
			success += 1
			print(f"[{user}] ✔ ok")
			uid = resp.json()['msg']['uid']
			mid = resp.json()['msg']['mid']
			cookie_token = resp.json()['msg']['cookie_token']
			open('token.txt', 'a', encoding='utf8').write(f'{user}----{uid}|{mid}|{cookie_token}\n')
		else:
			failure += 1
			print(f"[{user}] ✘ status={resp.status_code} text={resp.text}")
	except Exception as e:
		failure += 1
		print(f"[{user}] ✘ exc={e}")


def main():
	start = time.time()
	data = open('账号.txt', 'r', encoding='utf8').readlines()
	TOTAL = len(data)  # 总请求数
	lst = [i.strip().split('----') for i in data]
	#################  去重  #################
	done = open('token.txt', 'r', encoding='utf8').readlines()
	a = ''
	for i in done:
		if '----' in i and i.split('----')[0] not in a:
			a += i
	
	open('token.txt', 'w', encoding='utf8').write(a)
	###################################################
	done = open('token.txt', 'r', encoding='utf8').read()
	with ThreadPoolExecutor(max_workers=THREADS) as pool:
		# 提交所有任务
		futures = [pool.submit(do_one, lst[i]) for i in range(TOTAL) if lst[i][0].strip() not in done]
		# 等待全部完成
		for _ in as_completed(futures):
			pass
	cost = time.time() - start
	print("\n========== 统计 ==========")
	print(f"总请求: {TOTAL}")
	print(f"成功   : {success}")
	print(f"失败   : {failure}")
	print(f"耗时   : {cost:.2f}s")
	print(f"QPS    : {TOTAL / cost:.2f}")


if __name__ == "__main__":
	main()
