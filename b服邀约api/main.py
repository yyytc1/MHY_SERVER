# coding : utf-8
# @Time : 2025/11/6 3:14
# @Author : Adolph
# @File : main.py
# @Software : PyCharm
import logging
import multiprocessing
import time
import traceback

from baseObject import BindObj, AccStatus
from thread_ import session
from config import db
import config
from const import *

from flask import Flask, request, jsonify, render_template_string
import os
from threading import Lock

app = Flask(__name__)
server_port = 8888

# 远程订单服务配置
REMOTE_ORDER_API = 'http://115.190.5.154:8888'
remote_order_lock = Lock()  # 保护远程订单缓存的并发访问


# ---------- Test / UI 集成部分（从 test.py 合并） ----------
# 邀请状态映射
STATUS_LABELS = {
	'pending': '待处理',
	'running': '处理中',
	'not_invited': '未邀约',
	'invited': '已邀约',
	'abnormality': '账号异常',
	'binding': '绑定中',
}

# 订单状态映射
ORDER_STATUS_LABELS = {
	'待邀请': '待邀请',
	'邀请中': '邀请中',
	'完成': '完成',
	'失败': '失败',
}


def fetch_remote_orders(page=1, page_size=20, status=None):
	"""
	从远程服务器获取订单列表
	:param page: 页码
	:param page_size: 每页数量
	:param status: 订单状态（待邀请/邀请中/完成/失败），None 表示全部
	:return: (total, items) 或 (0, [])
	"""
	try:
		url = f'{REMOTE_ORDER_API}/admin/tasks'
		params = {
			'page': page,
			'pageSize': page_size,
		}
		# 只有当 status 不为 None 时才添加到请求参数中
		if status is not None:
			params['status'] = status
		
		resp = session.conn.get(url, params=params, timeout=10)
		if resp.status_code == 200:
			data = resp.json()
			items = data.get('data', [])
			total = data.get('total', len(items))
			return total, items
	except Exception as e:
		print(f'远程订单获取失败: {e}')
	return 0, []


def update_remote_order_status(secret_key, new_status):
	"""
	更新远程订单状态
	:param secret_key: 订单密钥
	:param new_status: 新状态（待邀请/邀请中/完成/失败）
	:return: True/False
	"""
	try:
		url = f'{REMOTE_ORDER_API}/api/tasks/{secret_key}/update/{new_status}'
		resp = session.conn.get(url, timeout=10)
		return resp.status_code == 200
	except Exception as e:
		print(f'远程订单更新失败: {e}')
	return False


def delete_remote_order(secret_key):
	"""
	删除远程订单
	:param secret_key: 订单密钥
	:return: True/False
	"""
	try:
		url = f'{REMOTE_ORDER_API}/api/admin/keys/batch/delete'
		data = {"keys": [secret_key]}
		resp = session.conn.post(url, json=data, timeout=10)
		return resp.status_code == 200
	except Exception as e:
		print(f'远程订单删除失败: {e}')
	return False


def get_conn():
	# 使用 AccDataBase 的连接工厂
	return db._conn()


def query_accounts_page(invite_status=None, page=1, page_size=50, sort_field='id', sort_dir='dasc', keyword=None):
	if page < 1:
		page = 1
	if page_size < 1:
		page_size = 50

	allowed_sort_fields = {
		'id': 'id',
		'username': 'username',
		'invite_status': 'invite_status',
		'devicename': 'devicename',
		'start_at': 'start_at',
		'update_at': 'update_at',
	}
	sort_field_db = allowed_sort_fields.get(sort_field, 'id')
	sort_dir_db = 'DESC' if str(sort_dir).lower() == 'asc' else 'ASC'

	where_clauses = []
	params = []

	if invite_status not in (None, "", "all"):
		where_clauses.append("invite_status = ?")
		params.append(invite_status)

	if keyword not in (None, ""):
		kw = f'%{keyword}%'
		where_clauses.append("(username LIKE ? OR devicename LIKE ? OR invite_code LIKE ?)")
		params.extend([kw, kw, kw])

	where_sql = ""
	if where_clauses:
		where_sql = "WHERE " + " AND ".join(where_clauses)

	offset = (page - 1) * page_size

	with get_conn() as conn:
		total = conn.execute(f"SELECT COUNT(*) AS c FROM accounts {where_sql}", params).fetchone()[0]
		rows = conn.execute(
			f"""
			SELECT * FROM accounts
			{where_sql}
			ORDER BY {sort_field_db} {sort_dir_db}
			LIMIT ? OFFSET ?
			""",
			params + [page_size, offset]
		).fetchall()

	return total, [dict(r) for r in rows]


# 读取页面模板（保持与 test.py 行为一致）
INDEX_HTML = ''
if os.path.exists('local.html'):
	try:
		INDEX_HTML = open('local.html', 'r', encoding='utf8').read()
	except Exception:
		INDEX_HTML = '<h1>local.html not found or unreadable</h1>'

	

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
	log(f'{info.get("username")} 取号登录')
	return jsonify({"data": {
		"account_status": info.get("account_status"),
		"device_code": info.get("devicecode"),
		"device_name": info.get("devicename"),
		"id": info.get("id"),
		"account_token": info.get("account_token"),
		"com_token": info.get("com_token"),
		"invite_status": info.get("invite_status"),
		"password": info.get("password"),
		"username": info.get("username"),
	}}), 200


@app.route('/api/accounts/update_token', methods=['POST'])
def api_update_token():
	# 不抛异常：解析失败返回 None
	data = request.get_json(silent=True) or {}
	id_ = data.get("id")
	token = data.get("hkrpg_token")
	uid = data.get("uid")
	invite_status = data.get('invite_status')
	if not id_ or not invite_status:
		return jsonify({"msg": "id, invite_status 不能为空"}), 400
	if not token or not uid:
		invite_status = AccStatus.abnormality
	ret = db.update_token(int(id_), invite_status, token, uid)
	if ret:
		return jsonify({"invite_status": 0}), 200
		username = ret.get('username')
		# if ret.get('start_at') and ret.get('update_at'):
		# 	start = datetime.datetime.strptime(ret["start_at"], "%Y-%m-%d %H:%M:%S")
		# 	update = datetime.datetime.strptime(ret["update_at"], "%Y-%m-%d %H:%M:%S")
		# 	if (update - start).total_seconds() >= 6 * 3600:
		# 		log(f'{username} 超过6小时，换号')
		# 		return jsonify({"invite_status": 1}), 200
		if invite_status == AccStatus.abnormality:
			log(f'{username} 脚本置账号异常')
			return jsonify({"invite_status": 0}), 200
		log(f'{username} 开始执行绑定')
		# 执行绑定
		obj = BindObj(ret, None)
		ret = obj.run_task()
		obj.close()
		return jsonify({"invite_status": ret}), 200
	else:
		return jsonify({"msg": "更新出错"}), 404


@app.route('/api/accounts/<int:acc_id>', methods=['POST'])
def api_update_account(acc_id):
	"""
	更新指定账号的 invite_status 与可选 invite_code
	与 update_account 方法对接
	"""
	data = request.get_json(silent=True) or {}
	status = data.get("invite_status")
	if not status:
		return jsonify({"msg": "invite_status 不能为空"}), 400
	log(f'修改账号状态：{status}')
	# 可选字段
	invite_code = data.get("invite_code")
	
	ret = db.update_account_row(acc_id, status, invite_code)
	if ret:
		return jsonify({"msg": "success"}), 200
	else:
		return jsonify({"msg": "账号不存在"}), 404


@app.route('/api/accounts/not_invited', methods=['GET'])
def api_not_invited():
	info = db.get_not_invited()
	if info is None:
		return jsonify({"error": "未取到状态为not_invited的账号"}), 404
	return jsonify({"data": {
		"username": info.get("username"),
		"id": info.get("id"),
		"invite_status": info.get("invite_status"),
		"hkrpg_token": info.get("hkrpg_token"),
		"uid": info.get("uid"),
	}}), 200


@app.route('/')
def web_page():
	ui_rows, statuses = db.get_all_accounts()
	return render_template_string(INDEX_HTML, user_info=[dict(r) for r in ui_rows], statuses=statuses, status_labels=STATUS_LABELS)


@app.route('/api/accounts')
def api_accounts():
	page = request.args.get('page', default='1')
	page_size = request.args.get('page_size', default='50')
	invite_status = request.args.get('invite_status', default=None)
	sort_field = request.args.get('sort_field', default='id')
	sort_dir = request.args.get('sort_dir', default='desc')
	keyword = request.args.get('keyword', default=None)

	try:
		page = int(page)
	except ValueError:
		page = 1
	try:
		page_size = int(page_size)
	except ValueError:
		page_size = 50

	total, rows = query_accounts_page(invite_status=invite_status, page=page, page_size=page_size, sort_field=sort_field, sort_dir=sort_dir, keyword=keyword)

	items = []
	for r in rows:
		r['invite_status_label'] = STATUS_LABELS.get(r.get('invite_status'), r.get('invite_status'))
		items.append(r)

	return jsonify(total=total, page=page, page_size=page_size, items=items)


@app.route('/api/orders')
def api_orders():
	pending = db.get_all_orders()
	return jsonify(pending_orders=pending, completed_orders=config.COMPLETED_ORDERS, failed_orders=config.FAILED_ORDERS)


@app.route('/api/local_orders/<secret_key>', methods=['DELETE'])
def api_delete_local_order(secret_key):
	"""
	删除单个本地订单
	DELETE /api/local_orders/{secret_key}
	"""
	try:
		# 从数据库中删除该邀请码的订单
		db.delete_order(secret_key)
		return jsonify(msg='deleted'), 200
	except Exception as e:
		print(f'删除本地订单失败: {e}')
		return jsonify(msg='delete failed'), 400


@app.route('/api/local_orders/batch_delete', methods=['POST'])
def api_batch_delete_local_orders():
	"""
	批量删除本地订单
	POST /api/local_orders/batch_delete
	Body: {invite_codes: [code1, code2, ...]}
	"""
	try:
		data = request.get_json()
		secret_keys = data.get('secret_keys', [])
		if not secret_keys:
			return jsonify(msg='no items to delete'), 400
		for secret_key in secret_keys:
			db.delete_order(secret_key)
		
		return jsonify(msg='deleted', count=len(secret_keys)), 200
	except Exception as e:
		print(f'批量删除本地订单失败: {e}')
		return jsonify(msg='delete failed'), 400


@app.route('/api/remote_orders', methods=['GET'])
def api_remote_orders():
	"""
	获取远程订单（分页）
	GET /api/remote_orders?page=1&pageSize=20&status=待邀请
	若 status 为空或不传，则获取全部状态的订单
	"""
	page = request.args.get('page', default='1', type=int)
	page_size = request.args.get('pageSize', default='20', type=int)
	status = request.args.get('status', default='')  # 空值表示全部状态
	
	if page < 1:
		page = 1
	if page_size < 1 or page_size > 100:
		page_size = 20
	
	# 如果 status 为空，设为 None 表示不按状态过滤
	if not status:
		status = None
	
	total, items = fetch_remote_orders(page, page_size, status)
	return jsonify(total=total, page=page, pageSize=page_size, items=items)


@app.route('/api/remote_orders/update', methods=['POST'])
def api_update_remote_order():
	"""
	批量更新远程订单状态
	POST /api/remote_orders/update
	Body: { "secret_keys": ["key1", "key2"], "new_status": "邀请中" }
	"""
	data = request.get_json(silent=True) or {}
	secret_keys = data.get('secret_keys', [])
	new_status = data.get('new_status', '邀请中')
	
	if not secret_keys or not isinstance(secret_keys, list):
		return jsonify(msg='invalid secret_keys'), 400
	
	results = {}
	for key in secret_keys:
		success = update_remote_order_status(key, new_status)
		results[key] = 'success' if success else 'failed'
	
	return jsonify(msg='batch update completed', results=results)


@app.route('/api/remote_orders/<secret_key>', methods=['DELETE'])
def api_delete_remote_order(secret_key):
	"""
	删除单个远程订单
	DELETE /api/remote_orders/{secret_key}
	"""
	db.delete_order(secret_key)
	success = delete_remote_order(secret_key)
	if success:
		return jsonify(msg='deleted'), 200
	else:
		return jsonify(msg='delete failed'), 400


@app.route('/api/remote_orders/search/invite_code', methods=['POST'])
def api_search_by_invite_code():
	"""
	通过邀请码批量查询远程订单
	POST /api/remote_orders/search/invite_code
	Body: { "invite_codes": ["code1", "code2"] }
	"""
	data = request.get_json(silent=True) or {}
	invite_codes = data.get('invite_codes', [])
	
	if not invite_codes or not isinstance(invite_codes, list):
		return jsonify(msg='invalid invite_codes', items=[]), 400
	
	try:
		url = f'{REMOTE_ORDER_API}/api/admin/tasks/batch/query'
		resp = session.conn.post(url, json={'invite_codes': invite_codes}, timeout=10)
		if resp.status_code == 200:
			result = resp.json()
			# 远程 API 返回的是 'tasks' 字段而不是 'data'
			items = result.get('tasks', [])
			return jsonify(msg='success', items=items)
		else:
			return jsonify(msg='remote error', items=[]), 400
	except Exception as e:
		print(f'邀请码搜索失败: {e}')
		return jsonify(msg='search failed', items=[]), 400


@app.route('/api/remote_orders/search/secret_key', methods=['POST'])
def api_search_by_secret_key():
	"""
	通过卡密查询远程订单
	POST /api/remote_orders/search/secret_key
	Body: { "secret_key": "xxx" }
	"""
	data = request.get_json(silent=True) or {}
	secret_key = data.get('secret_key', '')
	
	if not secret_key:
		return jsonify(msg='invalid secret_key', items=[]), 400
	
	try:
		url = f'{REMOTE_ORDER_API}/api/admin/keys/search/{secret_key}'
		resp = session.conn.get(url, timeout=10)
		if resp.status_code == 200:
			result = resp.json()
			# 根据远程 API 的实际返回格式调整（可能是 'tasks', 'data', 或直接的列表）
			items = result.get('tasks', result.get('data', []))
			return jsonify(msg='success', items=items)
		else:
			return jsonify(msg='remote error', items=[]), 400
	except Exception as e:
		print(f'卡密搜索失败: {e}')
		return jsonify(msg='search failed', items=[]), 400



def is_port_in_use(port):
	try:
		res = subprocess.run('netstat -ano', shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
		text = res.stdout.decode('gbk', errors='ignore')
		return f'0.0.0.0:{port}' in text
	except:
		return False


def run_server():
	try:
		log(f'本地服务已启动 port={server_port}')
		logging.getLogger('werkzeug').disabled = True
		app.logger.disabled = True
		app.run(host='0.0.0.0', port=server_port, debug=False, use_reloader=False, threaded=True)
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
			log(f'服务崩溃，尝试重启...')
			p = multiprocessing.Process(target=run_server, daemon=True)
			p.start()
			p.join()
		time.sleep(60)
