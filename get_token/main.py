# coding : utf-8
# @Time : 2025/11/16 13:56 
# @Author : Adolph
# @File : main.py 
# @Software : PyCharm
import datetime
import traceback

from flask import Flask, request, jsonify

from baseObject import MHYObj
from config import REDIS, res_404, REMOTE_UPLOAD_HOST
from 打包 import debug
from task import task_queue, run_task

app = Flask(__name__)
app.json.ensure_ascii = False


@app.before_request
def block_non_white():
	if request.path.startswith('/task'):
		if request.remote_addr != REMOTE_UPLOAD_HOST:
			return res_404


if debug:
	@app.route("/api/getTokenByAccount", methods=["POST"])
	def getTokenByAccount():
		data = request.get_json(silent=True) or {}
		account = data.get("account")
		password = data.get("password")
		if not account:
			return jsonify({"code": 400, "msg": "account 不能为空"}), 400
		
		value = REDIS.hget("1:token", account)
		if value is None:
			return jsonify({"code": 404, "msg": "account 不存在"}), 404
			mhy_obj = MHYObj(data)
			try:
				msg = mhy_obj.web_login()
				data.update(msg)
			except:
				e = f'【{datetime.datetime.now()}】 {account}\n{traceback.format_exc()}\n'
				open('get_token_error.txt', 'a', encoding='utf8').write(e)
				return jsonify({"code": 404, "msg": '代码未知错误'}), 404
			mhy_obj.close()
			del mhy_obj, account, password
			return jsonify({"code": 0, "msg": data})
		
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
		try:
			obj = MHYObj(msg)
			ret = obj.run_task()
			obj.close()
			if isinstance(ret, dict):
				msg.update(ret)
				return jsonify({"code": 0, "msg": msg})
			else:
				return jsonify({"code": 404, "msg": ret}), 404
		except:
			open('get_token_error.txt', 'a', encoding='utf8').write(
				f'【{datetime.datetime.now()}】 {account}\n{traceback.format_exc()}\n')
			return jsonify({"code": 404, "msg": '代码未知错误'}), 404
	
	
	@app.route("/api/getCookieToken", methods=["POST"])
	def getCookieToken():
		data = request.get_json(silent=True) or {}
		account = data.get("account")
		password = data.get("password")
		if not account or not password:
			return jsonify({"code": 400, "msg": "用户名 密码 不能为空"}), 400
		
		mhy_obj = MHYObj(data)
		try:
			msg = mhy_obj.web_login()
			data.update(msg)
		except:
			e = f'【{datetime.datetime.now()}】 {account}\n{traceback.format_exc()}\n'
			open('get_token_error.txt', 'a', encoding='utf8').write(e)
			return jsonify({"code": 404, "msg": '代码未知错误'}), 404
		mhy_obj.close()
		del mhy_obj, account, password
		return jsonify({"code": 0, "msg": data})


@app.route("/task/upload", methods=["POST"])
def task_api_upload():
	data = request.get_json(silent=True) or {}
	p_type = data.get('p_type')
	lst = data.get('list')
	card_id = data.get('card_id')
	if not p_type or not lst or not card_id:
		return jsonify({'ok': False, 'error': 'p_type list card_id不能为空'}), 400
	try:
		for ret in lst:
			ret['p_type'] = p_type
			ret['card_id'] = card_id
			task_queue.put_nowait(ret)
		return jsonify({'ok': True}), 200
	except:
		return jsonify({'ok': False, 'error': '未知错误'}), 500


if __name__ == '__main__':
	# 0.0.0.0 允许局域网/公网访问
	run_task()
	app.run(host="0.0.0.0", port=1234, debug=False)
