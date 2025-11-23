# coding : utf-8
# @Time : 2025/11/6 3:14
# @Author : Adolph
# @File : app.py
# @Software : PyCharm
import hashlib
import json
import os
import pathlib
import sqlite3
import uuid
from datetime import datetime, timedelta
from functools import wraps

import jwt
from flask import Flask, request, jsonify, make_response, g

from backend.baseFunc import hash_pw
from backend.config import config_filename, acc_status, db

APP_SECRET = os.environ.get("APP_SECRET", "change-this-please")
DB_PATH = os.environ.get("DB_PATH", "sr.db")
JWT_EXPIRE_HOURS = 24 * 365

app = Flask(__name__)


def init_config():
	if not os.path.exists(config_filename):
		init_data = {
			'user': 'admin',
			'pwd': hash_pw('123456')
		}
		# 文件写入使用 with open
		with open(config_filename, 'w', encoding='utf8') as f:
			f.write(json.dumps(init_data))


def init_vene():
	init_config()
	init_authkey()


def init_authkey():
	authkey = hashlib.md5(uuid.uuid4().bytes).hexdigest()
	with open('AuthKey', "w", encoding="utf-8") as f:
		f.write(authkey)
	os.chmod('AuthKey', 0o644)


# ---------- Auth ----------
def make_token(uid: int, username: str):
	payload = {
		"uid": uid, "username": username,
		"exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS),
		"iat": datetime.utcnow()
	}
	return jwt.encode(payload, APP_SECRET, algorithm="HS256")


def auth_required(f):
	@wraps(f)
	def wrap(*a, **kw):
		token = (request.headers.get("token") or "")
		if not token:
			return jsonify({"error": "NO_TOKEN"}), 401
		try:
			payload = jwt.decode(token, APP_SECRET, algorithms=["HS256"])
			request.user = payload
		except jwt.ExpiredSignatureError:
			return jsonify({"error": "TOKEN_EXPIRED"}), 401
		except Exception:
			return jsonify({"error": "TOKEN_INVALID"}), 401
		return f(*a, **kw)
	
	return wrap


@app.before_request
def load_json_utf8():
	"""无论 Content-Type 是什么，一律按 UTF-8 解析 JSON"""
	if request.method in {"POST", "PUT", "PATCH"}:
		# 用 get_data 取原始字节，再手动 UTF-8 解码
		raw = request.get_data(as_text=False)  # 一定是 bytes
		if raw:
			try:
				g.json = json.loads(raw.decode("gbk"))
			except:
				g.json = None
		else:
			g.json = None


# ---------- login ----------
@app.route("/admin/login", methods=["POST"])
def api_login():
	data = g.json or {}
	u, p = (data.get("username") or "").strip(), data.get("password") or ""
	
	row = db.user_login(u)
	if row is None:
		return jsonify({"ok": False, "msg": "用户名或密码错误"}), 400
	else:
		token = make_token(row["id"], u)
		return jsonify({"ok": True, "token": token, "username": u})


# ---- pool ----
@app.route(f"/admin/pool/list", methods=["GET"])
@auth_required
def pools_list():
	items = db.get_pool()
	return jsonify({"code": 1, "data": items, 'msg': 'success'})


@app.route("/admin/pool/add", methods=["POST"])
@auth_required
def pools_add():
	data = g.json or {}
	name = data.get("name")
	if not name:
		return jsonify({"ok": False, "msg": "名称不能为空"}), 400
	
	new_id = db.add_pool(name)
	
	return jsonify(
		{
			"code": 1,
			"data": {
				"id": new_id,
				"name": name
			},
			"msg": "success"
		}
	), 200


@app.route("/admin/pool/revise", methods=["POST"])
@auth_required
def pools_revise():
	data = g.json or {}
	pid = data.get("id")
	name = data.get("name")
	
	if not name or not pid:
		return jsonify({"code": 0, "msg": "名称或id不能为空"}), 400
	db.revise_pool(pid, name)
	return jsonify({"code": 1, "msg": "success"})


@app.route("/admin/pool/del", methods=['POST'])
@auth_required
def pools_del():
	data = g.json or {}
	pid = data.get("id")
	if not pid:
		return jsonify({"code": 0, "msg": "id不能为空"}), 400
	if not isinstance(pid, int):
		return jsonify({"code": 0, "msg": "id类型必须是整数"}), 400
	db.delete_pool(pid)
	return jsonify({"code": 1, "msg": "success"}), 200


# ---- accounts ----
@app.route("/admin/account/data", methods=['POST'])
@auth_required
def accounts_list():
	data = g.json or {}
	q_pool = request.args.get("hcid")
	q_status = request.args.get("status")
	kw = (request.args.get("kw") or "").strip()
	page = max(int(request.args.get("page", 1)), 1)
	size = min(max(int(request.args.get("size", 20)), 1), 200)
	
	where, params = [], []
	if q_pool:
		where.append("a.pool_id=?")
		params.append(q_pool)
	if q_status:
		where.append("a.status=?")
		params.append(q_status)
	if kw:
		where.append("(a.email LIKE ? OR a.remark LIKE ?)")
		params += [f"%{kw}%", f"%{kw}%"]
	where_sql = ("WHERE " + " AND ".join(where)) if where else ""
	
	offset = (page - 1) * size
	
	with db() as conn:
		cur = conn.cursor()
		cur.execute(f"SELECT COUNT(*) c FROM accounts a {where_sql}", params)
		total = cur.fetchone()["c"]
		
		cur.execute(f"""
		  SELECT a.id,a.pool_id,p.name AS pool_name,a.use,a.pwd,
				 a.status,a.remark,a.update_ts
		  FROM accounts a
		  JOIN pools p ON p.id=a.pool_id
		  {where_sql}
		  ORDER BY a.id DESC
		  LIMIT ? OFFSET ?
		""", params + [size, offset])
		items = [dict(r) for r in cur.fetchall()]
	
	return jsonify({"ok": True, "total": total, "items": items})


@app.route("/admin/account/add", methods=['POST'])
@auth_required
def add_account():
	"""
	插入一条账号数据
	请求 JSON 例子：
	{
		"email": "test@example.com",
		"pwd": "123456",
		"name": "阿萨德",
		"script": "auto1",
		"level": 10,
		"money": 1000,
		"tangle": 5,
		"meet": 10,
		"status": "0",
		"note": "这是备注"
	}
	"""
	data = g.json or {}
	if not data:
		return jsonify({"ok": False, "msg": "body 不是合法 JSON"}), 400
	
	hcid = data.get('hcid')
	dat = data.get('data')
	# 简单必填字段检查，你可以按需扩展
	if not hcid or not dat.get("use") or not dat.get("pwd") or not dat.get("status"):
		return jsonify({"ok": False, "msg": "use,pwd,status 必填"}), 400

	try:
		new_id = db.add_account(hcid, dat)
	except Exception as e:
		return jsonify({"ok": False, "msg": f"数据库错误: {e}"}), 500

	return jsonify({"ok": True, "id": new_id})


@app.route("/admin/account/<int:aid>", methods=["PATCH"])
@auth_required
def accounts_patch(aid):
	data = g.json or {}
	fields, params = [], []
	for k in ("status", "email", "pwd", "remark", "pool_id", "proxy_id"):
		if k in data:
			fields.append(f"{k}=?")
			params.append(data[k])
	
	if not fields:
		return jsonify({"ok": False, "msg": "无更新项"}), 400
	
	params.append(aid)
	
	with db() as conn:
		cur = conn.cursor()
		cur.execute(f"UPDATE accounts SET {', '.join(fields)} WHERE id=?", params)
	
	return jsonify({"ok": True})


@app.route("/admin/account/<int:aid>", methods=['DELETE'])
@auth_required
def accounts_del(aid):
	with db() as conn:
		cur = conn.cursor()
		cur.execute("DELETE FROM accounts WHERE id=?", (aid,))
	return jsonify({"ok": True})


@app.route("/admin/change-password", methods=["POST"])
@auth_required
def api_change_password():
	data = g.json or {}
	old_pwd = data.get("old_password") or ""
	new_pwd = data.get("new_password") or ""
	
	if len(new_pwd) < 6:
		return jsonify({"ok": False, "msg": "新密码至少 6 位"}), 400
	
	uid = request.user["uid"]
	
	with db() as conn:
		cur = conn.cursor()
		cur.execute("SELECT password_hash FROM users WHERE id=?", (uid,))
		row = cur.fetchone()
		if not row or hash_pw(old_pwd) != row["password_hash"]:
			return jsonify({"ok": False, "msg": "原密码不正确"}), 400
		
		cur.execute("UPDATE users SET password_hash=? WHERE id=?", (hash_pw(new_pwd), uid))
	
	return jsonify({"ok": True})


@app.route("/admin/account/export", methods=["GET"])
@auth_required
def accounts_export():
	pool_id = request.args.get("pool_id")
	status = request.args.get("status")
	
	where, params = [], []
	if pool_id:
		where.append("a.pool_id=?")
		params.append(pool_id)
	if status:
		where.append("a.status=?")
		params.append(status)
	where_sql = ("WHERE " + " AND ".join(where)) if where else ""
	
	with db() as conn:
		cur = conn.cursor()
		cur.execute(f"""
			SELECT p.name AS pool,a.use,a.pwd,a.status,a.remark
			FROM accounts a JOIN pools p ON p.id=a.pool_id
			{where_sql} ORDER BY a.id ASC
		""", params)
		rows = cur.fetchall()
	
	def esc(s):
		s = "" if s is None else str(s)
		return s.replace(",", "，")
	
	lines = ["pool,account,password,status,remark"]
	for r in rows:
		lines.append(
			f"{esc(r['pool'])},{esc(r['email'])},{esc(r['pwd'])},{esc(r['status'])},{esc(r['remark'])}"
		)
	txt = "\n".join(lines)
	
	resp = make_response(txt)
	resp.headers["Content-Type"] = "text/plain; charset=utf-8"
	resp.headers["Content-Disposition"] = "attachment; filename=accounts.txt"
	return resp


# 在根路径直接返回前端页面
@app.route("/", methods=["GET"])
def serve_index():
	# 前端 index.html 用 with open 读取再响应（可选；send_file 也可）
	front = pathlib.Path(__file__).resolve().parents[1] / "frontend" / "index.html"
	if not front.exists():
		return "frontend/index.html 未找到", 404
	with open(front, "rb") as f:
		data = f.read()
	resp = make_response(data)
	resp.headers["Content-Type"] = "text/html; charset=utf-8"
	return resp


if __name__ == "__main__":
	init_vene()
	# 开发期建议单线程，进一步降低锁冲突
	app.run(host="0.0.0.0", port=8000)
