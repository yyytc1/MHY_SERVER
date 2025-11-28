# coding : utf-8
# @Time : 2025/11/18 14:42
# @Author : Adolph
# @File : main.py
# @Software : PyCharm
import datetime
import logging
import multiprocessing
import subprocess
import time
import traceback

from baseObject import MHYObj
from config import *

from flask import Flask, request, jsonify

app = Flask(__name__)
app.json.ensure_ascii = False


@app.route('/api/login', methods=['POST'])
def MiHoYoApiBHLogin():
	data = request.get_json(silent=True) or {}
	user = data.get('user')
	pwd = data.get('pass')
	city = data.get('city')  # 1 国服 6 B服  其他国际服
	if not user or not pwd or not city:
		return jsonify({"error": "账号 密码 区服 不能为空"}), 400
	mhy_obj = MHYObj(data)
	city = str(city)
	try:
		if city == '1':
			msg, status_code = mhy_obj.BHLoginWithProxy()
			mhy_obj.log('国服账密登录')
		elif city == '6':
			mhy_obj.log('B服账密登录')
			msg, status_code = mhy_obj.BiliLogHandle()
		else:
			mhy_obj.log('国际服账密登录')
			msg, status_code = mhy_obj.HoYoVerse()
	except:
		open(error_file, 'a', encoding='utf8').write(f'【{datetime.datetime.now()}】 {user}\n{traceback.format_exc()}\n')
		msg, status_code = {'error': '代码未知错误'}, 400
	mhy_obj.close()
	del mhy_obj, data, user, pwd, city
	return jsonify(msg), status_code


@app.route('/api/loginPhone', methods=['POST'])
def MiHoYoApiPhoneLogin():
	data = request.get_json(silent=True) or {}
	user = data.get('user')
	pwd = data.get('pass')
	if not user or not pwd:
		return jsonify({"error": "手机号 链接 不能为空"}), 400
	mhy_obj = MHYObj(data)
	mhy_obj.log('国服短信登录')
	try:
		msg, status_code = mhy_obj.MiHoYoPhoneLoginCaptchaWithProxy()
	except:
		open(error_file, 'a', encoding='utf8').write(f'【{datetime.datetime.now()}】 {user}\n{traceback.format_exc()}\n')
		msg, status_code = {'error': '代码未知错误'}, 400
	mhy_obj.close()
	del mhy_obj, data, user, pwd
	return jsonify(msg), status_code


# @app.route('/api/getCookieToken', methods=['POST'])
# def MiHoYoApiWebLogin():
# 	data = request.get_json(silent=True) or {}
# 	user = data.get('user')
# 	pwd = data.get('pass')
# 	if not user or not pwd:
# 		return jsonify({"error": "账号 密码 不能为空"}), 400
# 	data['city'] = '1'
# 	mhy_obj = MHYObj(data)
# 	mhy_obj.log('国服获取cookie_token')
# 	try:
# 		msg, status_code = mhy_obj.MiHoYoWebLogin()
# 	except:
# 		open(error_file, 'a', encoding='utf8').write(f'【{datetime.datetime.now()}】 {user}\n{traceback.format_exc()}\n')
# 		msg, status_code = {'error': '代码未知错误'}, 400
# 	mhy_obj.close()
# 	del mhy_obj, data, user, pwd
# 	return jsonify(msg), status_code


def is_port_in_use(port):
	try:
		res = subprocess.run('netstat -ano', shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
		text = res.stdout.decode('gbk', errors='ignore')
		return f'0.0.0.0:{port}' in text
	except:
		return False


def run_server():
	try:
		print(f'本地服务已启动 port={server_port}')
		logging.getLogger('werkzeug').disabled = False
		app.logger.disabled = False
		app.run(host='0.0.0.0', port=server_port, debug=True, use_reloader=False, threaded=True)
	except:
		e = traceback.format_exc()
		error_text = f'{datetime.datetime.now()}\n{e}\n\n'
		try:
			with open('error.txt', 'a', encoding='utf8') as _f:
				_f.write(error_text)
		except:
			pass


if __name__ == '__main__':
	run_server()
	while True:
		if not is_port_in_use(server_port):
			print(f'服务崩溃，尝试重启...')
			p = multiprocessing.Process(target=run_server, daemon=True)
			p.start()
			p.join()
		time.sleep(60)
