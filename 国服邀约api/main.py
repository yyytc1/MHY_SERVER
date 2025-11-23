# coding : utf-8
# @Time : 2025/11/6 3:14 
# @Author : Adolph
# @File : main.py 
# @Software : PyCharm
import multiprocessing
import time
import traceback

from const import *

from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)
server_port = 8999


class ScoreDatabase:
	def __init__(self):
		self.db_path = 'account.db'
		self.init_database()
	
	def _conn(self):
		# timeout 防止立刻抛 OperationalError；row_factory 便于取字段
		conn = sqlite3.connect(self.db_path, timeout=3.0, isolation_level=None)
		conn.row_factory = sqlite3.Row
		return conn
	
	def init_database(self):
		with self._conn() as conn:
			cur = conn.cursor()
			cur.execute("PRAGMA journal_mode=WAL;")
			cur.execute("PRAGMA synchronous=NORMAL;")
			# 索引避免全表扫描
			cur.execute("CREATE INDEX IF NOT EXISTS idx_accounts_invite_status ON accounts(invite_status);")
			cur.execute("CREATE INDEX IF NOT EXISTS idx_accounts_device ON accounts(devicename, devicecode);")
	
	def get_not_invited(self):
		with self._conn() as conn:
			sql = """
			UPDATE accounts
			SET invite_status = 'binding'
			WHERE id = (SELECT id FROM accounts WHERE invite_status = 'not_invited' LIMIT 1)
			RETURNING id, username, password, account_status, account_token,
					  invite_status, com_token, devicecode, devicename,
					  created_at, updated_at
			"""
			row = conn.execute(sql).fetchone()
			return dict(row) if row else None
	
	def get_pending_or_running(self, devicename: str, devicecode: str):
		with self._conn() as conn:
			row = conn.execute(
				"""
				SELECT id, username, password, account_status, account_token, invite_status,
					   com_token, devicecode, devicename, created_at, updated_at
				FROM accounts
				WHERE invite_status='running' AND devicename=? AND devicecode=?
				LIMIT 1
				""",
				(devicename, devicecode)
			).fetchone()
			if row:
				return dict(row)
		with self._conn() as conn:
			sql = """
			UPDATE accounts
			SET invite_status='running', devicename=?, devicecode=?
			WHERE id = (SELECT id FROM accounts WHERE invite_status='pending' LIMIT 1)
			RETURNING id, username, password, account_status, account_token,
					  invite_status, com_token, devicecode, devicename,
					  created_at, updated_at
			"""
			row = conn.execute(sql, (devicename, devicecode)).fetchone()
			return dict(row) if row else None


db = ScoreDatabase()


@app.route('/api/accounts/pending', methods=['POST'])
def api_pending():
	# 不抛异常：解析失败返回 None
	data = request.get_json(silent=True) or {}
	devicename = data.get("devicename")
	devicecode = data.get("devicecode")
	
	if not devicename or not devicecode:
		return jsonify({"error": "devicecode 与 devicename 不能为空"}), 400
	
	info = db.get_pending_or_running(devicename, devicecode)
	if info is None:
		# 建议不要用 400，这不是“请求格式错误”
		return jsonify({"error": "无pending或running账号"}), 404
	
	return jsonify({"data": {
		"account_status": info["account_status"],
		"created_at": info["created_at"],
		"device_code": info["devicecode"],
		"device_name": info["devicename"],
		"id": info["id"],
		"account_token": info["account_token"],
		"com_token": info["com_token"],
		"invite_status": info["invite_status"],
		"password": info["password"],
		"updated_at": info["updated_at"],
		"username": info["username"],
	}}), 200


@app.route('/api/accounts/not_invited', methods=['GET'])
def api_not_invited():
	info = db.get_not_invited()
	if info is None:
		# 同理：资源语义，返回 404 或 204
		return jsonify({"error": "未取到状态为not_invited的账号"}), 404
	return jsonify({"data": {
		"account_status": info["account_status"],
		"created_at": info["created_at"],
		"device_code": info["devicecode"],
		"device_name": info["devicename"],
		"id": info["id"],
		"account_token": info["account_token"],
		"com_token": info["com_token"],
		"invite_status": info["invite_status"],
		"password": info["password"],
		"updated_at": info["updated_at"],
		"username": info["username"],
	}}), 200


def is_port_in_use(port):
	ret, err = subprocess.Popen('netstat -ano', shell=True, stdout=subprocess.PIPE).communicate()
	text = ret.decode('gbk')
	return f'0.0.0.0:{port}' in text


def run_server():
	try:
		log(f'本地服务已启动 port={server_port}')
		# logging.getLogger('werkzeug').disabled = True
		app.logger.disabled = True
		app.run(host='0.0.0.0', port=server_port, debug=False, use_reloader=False, threaded=True)
	except:
		e = traceback.format_exc()
		error_text = f'{datetime.datetime.now()}\n{e}\n\n'
		open('error.txt', 'a', encoding='utf8').write(error_text)


if __name__ == '__main__':
	run_server()
	while True:
		if not is_port_in_use(server_port):
			log(f'服务崩溃，尝试重启...')
			p = multiprocessing.Process(target=run_server, daemon=True)
			p.start()
			p.join()  # 等待进程退出（服务崩溃）
		# else:
		# 	log(f'端口 {dfn_port} 已占用，30秒后继续检测...')
		time.sleep(60)
