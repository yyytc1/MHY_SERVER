# coding : utf-8
# @Time : 2025/11/16 13:56 
# @Author : Adolph
# @File : main.py 
# @Software : PyCharm
from flask import Flask, request, jsonify
import redis

from baseObject import MHYObj

app = Flask(__name__)

# ========== 远程 Redis 配置 ==========
REDIS_HOST = "47.105.189.174"
REDIS_PORT = 6379
REDIS_PASSWORD = "qq197603"  # 若无密码填 None
REDIS_DB = 0
# =====================================

r = redis.Redis(
	host=REDIS_HOST,
	port=REDIS_PORT,
	password=REDIS_PASSWORD,
	db=REDIS_DB,
	decode_responses=True  # 直接返回 str
)


@app.route("/api/getGameTokenByAccount", methods=["POST"])
def query_value():
	data = request.get_json(silent=True) or {}
	account = data.get("account")
	password = data.get("password")
	if not account:
		return jsonify({"code": 400, "msg": "account 不能为空"}), 400
	
	value = r.hget("1:token", account)
	if value is None:
		return jsonify({"code": 404, "msg": "account 不存在"}), 404
	
	if value.count('----') == 2:
		combo_token, game_token, uid = value.split('----')
		msg = {
			'game_token': game_token,
		}
	else:
		combo_token, cookie_token, uid, mid = value.split('----')
		msg = {
			'cookie_token': cookie_token,
			'mid': mid,
		}
	msg.update({
		"account": account,
		"password": password,
		'combo_token': combo_token,
		'uid': int(uid)
	})
	obj = MHYObj(msg)
	ret = obj.run_task()
	obj.close()
	if isinstance(ret, dict):
		msg['stoken'] = ret['stoken']
		msg['mid'] = ret['mid']
		return jsonify({"code": 0, "msg": msg})
	else:
		return jsonify({"code": 404, "msg": ret}), 404


if __name__ == '__main__':
	# 0.0.0.0 允许局域网/公网访问
	app.run(host="0.0.0.0", port=1234, debug=False)
