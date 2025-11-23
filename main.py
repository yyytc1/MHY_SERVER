# app.py
# -*- coding: utf-8 -*-

import os
import sqlite3
from functools import wraps
from datetime import timedelta
from flask import (
    Flask, request, redirect, url_for, session, abort,
    make_response
)

from html import escape
from hashlib import sha256

APP_SECRET = os.environ.get("APP_SECRET", "dev-secret-change-me")
DB_PATH = os.environ.get("DB_PATH", "app.db")

app = Flask(__name__)
app.secret_key = APP_SECRET
app.permanent_session_lifetime = timedelta(days=7)


# ---------------------------
# 工具：数据库
# ---------------------------
def db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pools (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pool_id INTEGER NOT NULL,
            account_name TEXT NOT NULL,
            account_password TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active', -- active / disabled / banned / unknown
            remark TEXT DEFAULT '',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(pool_id) REFERENCES pools(id) ON DELETE CASCADE
        );
    """)
    conn.commit()

    # 初始化默认 admin
    cur.execute("SELECT id FROM users WHERE username = ?", ("admin",))
    if cur.fetchone() is None:
        # 默认密码 admin123
        cur.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    ("admin", hash_password("admin123")))
        conn.commit()

    conn.close()


# ---------------------------
# 工具：密码哈希（简洁起见用 sha256+salt，生产可换为 passlib/bcrypt）
# ---------------------------
def hash_password(plain: str) -> str:
    salt = "s@lt/2025"
    return sha256((salt + plain).encode("utf-8")).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    return hash_password(plain) == hashed


# ---------------------------
# 工具：登录保护
# ---------------------------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("uid"):
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return wrapper


# ---------------------------
# 简易 HTML 渲染（内联模板）
# ---------------------------
def layout_html(title: str, body: str, user=None, msg=""):
    nav = ""
    if user:
        nav = f"""
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
          <div>
            <a href="{url_for('dashboard')}">首页</a> |
            <a href="{url_for('pools')}">号池</a> |
            <a href="{url_for('accounts')}">账号</a> |
            <a href="{url_for('export_accounts')}">导出账号</a>
          </div>
          <div>
            <span>已登录：<b>{escape(user)}</b></span>
            &nbsp;|&nbsp;<a href="{url_for('change_password')}">修改密码</a>
            &nbsp;|&nbsp;<a href="{url_for('logout')}">退出</a>
          </div>
        </div>
        """
    info = f"""<div style="color:#0a0;margin:6px 0;">{escape(msg)}</div>""" if msg else ""
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>{escape(title)}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{{font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, 'Noto Sans', 'PingFang SC', 'Microsoft YaHei', sans-serif; margin:24px;}}
input,select,button,textarea{{padding:6px 8px;margin:3px 0;}}
table{{border-collapse:collapse;width:100%;}}
th,td{{border:1px solid #ddd;padding:8px;text-align:left;}}
th{{background:#fafafa;}}
.card{{border:1px solid #eee;border-radius:8px;padding:12px;margin:12px 0;}}
.row{{display:flex;gap:12px;flex-wrap:wrap;}}
.col{{flex:1 1 320px;min-width:320px;}}
a.button,button.button{{padding:6px 10px;border:1px solid #ddd;border-radius:6px;background:#f6f6f6;text-decoration:none;}}
a.button:hover,button.button:hover{{background:#eee;}}
form.inline{{display:inline;}}
.badge{{padding:2px 8px;border-radius:999px;border:1px solid #ddd;background:#f7f7f7;}}
.badge.active{{border-color:#4caf50;}}
.badge.disabled{{border-color:#ff9800;}}
.badge.banned{{border-color:#f44336;}}
.badge.unknown{{border-color:#9e9e9e;}}
</style>
</head>
<body>
{nav}
{info}
{body}
</body>
</html>"""


def flash_msg_text() -> str:
    # 轻量“闪存”，通过 query 参数 ?msg=
    return request.args.get("msg", "")


# ---------------------------
# 路由：认证
# ---------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        conn = db_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        conn.close()
        if row and verify_password(password, row["password_hash"]):
            session.permanent = True
            session["uid"] = row["id"]
            session["username"] = username
            next_url = request.args.get("next") or url_for("dashboard")
            return redirect(next_url)
        else:
            body = f"""
            <div class="card">
              <h3>登录</h3>
              <div style="color:#c00;margin:6px 0;">用户名或密码错误</div>
              {login_form()}
            </div>
            """
            return layout_html("登录", body, None)

    body = f"""
    <div class="card">
      <h3>登录</h3>
      {login_form()}
    </div>
    """
    return layout_html("登录", body, None)


def login_form():
    return f"""
    <form method="post">
      <div><label>用户名</label><br><input name="username" required></div>
      <div><label>密码</label><br><input name="password" type="password" required></div>
      <div style="margin-top:8px;"><button class="button" type="submit">登录</button></div>
    </form>
    """


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login", msg="已退出登录"))


@app.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        old = request.form.get("old") or ""
        new = request.form.get("new") or ""
        if len(new) < 6:
            return redirect(url_for("change_password", msg="新密码至少6位"))
        conn = db_conn()
        cur = conn.cursor()
        cur.execute("SELECT password_hash FROM users WHERE id = ?", (session["uid"],))
        row = cur.fetchone()
        if not row or not verify_password(old, row["password_hash"]):
            conn.close()
            return redirect(url_for("change_password", msg="原密码不正确"))
        cur.execute("UPDATE users SET password_hash=? WHERE id=?", (hash_password(new), session["uid"]))
        conn.commit()
        conn.close()
        return redirect(url_for("dashboard", msg="密码已更新"))
    body = f"""
    <div class="card">
      <h3>修改密码</h3>
      <form method="post">
        <div><label>原密码</label><br><input name="old" type="password" required></div>
        <div><label>新密码</label><br><input name="new" type="password" required></div>
        <div style="margin-top:8px;"><button class="button" type="submit">保存</button></div>
      </form>
    </div>
    """
    return layout_html("修改密码", body, session.get("username"), flash_msg_text())


# ---------------------------
# 路由：首页仪表盘
# ---------------------------
@app.route("/")
@login_required
def dashboard():
    conn = db_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM pools")
    pool_count = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM accounts")
    account_count = cur.fetchone()["c"]
    cur.execute("SELECT status, COUNT(*) c FROM accounts GROUP BY status")
    stats = {r["status"]: r["c"] for r in cur.fetchall()}
    conn.close()

    def badge(k):
        v = stats.get(k, 0)
        return f'<span class="badge {k}">{k}: {v}</span>'

    body = f"""
    <div class="row">
      <div class="col">
        <div class="card">
          <h3>总览</h3>
          <div>号池：<b>{pool_count}</b> 个</div>
          <div>账号：<b>{account_count}</b> 个</div>
          <div style="margin-top:8px;display:flex;gap:8px;flex-wrap:wrap;">
            {badge('active')}{badge('disabled')}{badge('banned')}{badge('unknown')}
          </div>
        </div>
      </div>
      <div class="col">
        <div class="card">
          <h3>快速入口</h3>
          <div style="display:flex;gap:8px;flex-wrap:wrap;">
            <a class="button" href="{url_for('pools')}">管理号池</a>
            <a class="button" href="{url_for('accounts')}">管理账号</a>
            <a class="button" href="{url_for('export_accounts')}">导出账号</a>
          </div>
        </div>
      </div>
    </div>
    """
    return layout_html("仪表盘", body, session.get("username"), flash_msg_text())


# ---------------------------
# 路由：号池
# ---------------------------
@app.route("/pools", methods=["GET", "POST"])
@login_required
def pools():
    conn = db_conn()
    cur = conn.cursor()

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        if not name:
            conn.close()
            return redirect(url_for("pools", msg="名称不能为空"))
        try:
            cur.execute("INSERT INTO pools (name) VALUES (?)", (name,))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return redirect(url_for("pools", msg="号池已存在"))
        conn.close()
        return redirect(url_for("pools", msg="已添加"))

    # delete
    del_id = request.args.get("del")
    if del_id:
        try:
            cur.execute("DELETE FROM pools WHERE id=?", (del_id,))
            conn.commit()
        except Exception:
            pass
        conn.close()
        return redirect(url_for("pools", msg="已删除（关联账号也被移除）"))

    cur.execute("SELECT id, name, created_at FROM pools ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()

    rows_html = "".join(
        f"<tr><td>{r['id']}</td><td>{escape(r['name'])}</td><td>{r['created_at']}</td>"
        f"<td><a class='button' href='{url_for('accounts')}?pool_id={r['id']}'>查看账号</a> "
        f"<a class='button' href='{url_for('pools')}?del={r['id']}' onclick=\"return confirm('删除该号池及其下账号？')\">删除</a></td></tr>"
        for r in rows
    )

    body = f"""
    <div class="card">
      <h3>添加号池</h3>
      <form method="post">
        <div><label>名称</label><br><input name="name" required placeholder="例如：抖音-测试池A"></div>
        <div style="margin-top:6px;"><button class="button" type="submit">添加</button></div>
      </form>
    </div>

    <div class="card">
      <h3>号池列表</h3>
      <table>
        <thead><tr><th>ID</th><th>名称</th><th>创建时间</th><th>操作</th></tr></thead>
        <tbody>{rows_html or '<tr><td colspan=4>暂无数据</td></tr>'}</tbody>
      </table>
    </div>
    """
    return layout_html("号池管理", body, session.get("username"), flash_msg_text())


# ---------------------------
# 路由：账号
# ---------------------------
@app.route("/accounts", methods=["GET", "POST"])
@login_required
def accounts():
    conn = db_conn()
    cur = conn.cursor()

    # 号池下拉
    cur.execute("SELECT id, name FROM pools ORDER BY name ASC")
    pools_list = cur.fetchall()

    # 新增账号
    if request.method == "POST":
        pool_id = request.form.get("pool_id")
        account_name = (request.form.get("account_name") or "").strip()
        account_password = request.form.get("account_password") or ""
        status = request.form.get("status") or "active"
        remark = request.form.get("remark") or ""
        if not pool_id or not account_name:
            conn.close()
            return redirect(url_for("accounts", msg="必填项不能为空"))
        cur.execute("""
            INSERT INTO accounts (pool_id, account_name, account_password, status, remark)
            VALUES (?, ?, ?, ?, ?)
        """, (pool_id, account_name, account_password, status, remark))
        conn.commit()
        conn.close()
        return redirect(url_for("accounts", msg="账号已添加", pool_id=pool_id))

    # 修改状态
    change_id = request.args.get("set")
    new_status = request.args.get("status")
    if change_id and new_status:
        cur.execute("UPDATE accounts SET status=? WHERE id=?", (new_status, change_id))
        conn.commit()
        conn.close()
        return redirect(url_for("accounts", msg="状态已更新"))

    # 删除账号
    del_id = request.args.get("del")
    if del_id:
        cur.execute("DELETE FROM accounts WHERE id=?", (del_id,))
        conn.commit()
        conn.close()
        return redirect(url_for("accounts", msg="账号已删除"))

    # 过滤
    q_pool = request.args.get("pool_id")
    q_status = request.args.get("q_status")
    params = []
    where = []
    if q_pool:
        where.append("a.pool_id = ?")
        params.append(q_pool)
    if q_status:
        where.append("a.status = ?")
        params.append(q_status)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    cur.execute(f"""
        SELECT a.id, a.account_name, a.account_password, a.status, a.remark,
               a.created_at, p.name as pool_name, a.pool_id
        FROM accounts a
        JOIN pools p ON a.pool_id = p.id
        {where_sql}
        ORDER BY a.id DESC
        LIMIT 1000
    """, tuple(params))
    rows = cur.fetchall()
    conn.close()

    # 号池选项
    options_pool = "".join(
        f"<option value='{p['id']}' {'selected' if q_pool and str(p['id'])==str(q_pool) else ''}>{escape(p['name'])}</option>"
        for p in pools_list
    )
    # 状态选项
    statuses = ["active", "disabled", "banned", "unknown"]
    options_status = "".join(
        f"<option value='{s}' {'selected' if q_status==s else ''}>{s}</option>"
        for s in [""] + statuses
    )
    # 新增账号表单用的号池选
    options_pool_new = "".join(
        f"<option value='{p['id']}'>{escape(p['name'])}</option>"
        for p in pools_list
    )
    # 行
    def row_html(r):
        badge = f"<span class='badge {r['status']}'>{r['status']}</span>"
        actions = " | ".join(
            f"<a class='button' href='{url_for('accounts')}?set={r['id']}&status={s}'>" + s + "</a>"
            for s in statuses
        )
        return f"""
        <tr>
          <td>{r['id']}</td>
          <td>{escape(r['pool_name'])}</td>
          <td>{escape(r['account_name'])}</td>
          <td>{escape(r['account_password'])}</td>
          <td>{badge}</td>
          <td>{escape(r['remark'] or '')}</td>
          <td>{r['created_at']}</td>
          <td>
            {actions}
            <a class='button' href='{url_for('accounts')}?del={r['id']}' onclick="return confirm('确认删除该账号？')">删除</a>
          </td>
        </tr>
        """

    rows_html = "".join(row_html(r) for r in rows) or "<tr><td colspan=8>暂无数据</td></tr>"

    body = f"""
    <div class="row">
      <div class="col">
        <div class="card">
          <h3>新增账号</h3>
          <form method="post">
            <div><label>号池</label><br>
              <select name="pool_id" required>{options_pool_new}</select>
            </div>
            <div><label>账号</label><br><input name="account_name" required placeholder="login/email/phone"></div>
            <div><label>密码</label><br><input name="account_password" required></div>
            <div><label>状态</label><br>
              <select name="status">
                {''.join(f"<option value='{s}'>{s}</option>" for s in statuses)}
              </select>
            </div>
            <div><label>备注</label><br><input name="remark" placeholder="可选"></div>
            <div style="margin-top:6px;"><button class="button" type="submit">添加</button></div>
          </form>
        </div>
      </div>
      <div class="col">
        <div class="card">
          <h3>筛选</h3>
          <form method="get">
            <div><label>号池</label><br>
              <select name="pool_id"><option value="">（全部）</option>{options_pool}</select>
            </div>
            <div><label>状态</label><br>
              <select name="q_status">{options_status}</select>
            </div>
            <div style="margin-top:6px;">
              <button class="button" type="submit">查询</button>
              <a class="button" href="{url_for('accounts')}">重置</a>
              <a class="button" href="{url_for('export_accounts')}?pool_id={escape(q_pool or '')}&status={escape(q_status or '')}">导出当前筛选</a>
            </div>
          </form>
        </div>
      </div>
    </div>

    <div class="card">
      <h3>账号列表（最多显示 1000 条）</h3>
      <table>
        <thead>
          <tr><th>ID</th><th>号池</th><th>账号</th><th>密码</th><th>状态</th><th>备注</th><th>创建时间</th><th>操作</th></tr>
        </thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>
    """
    return layout_html("账号管理", body, session.get("username"), flash_msg_text())


# ---------------------------
# 路由：导出账号到文本
# ---------------------------
@app.route("/export", methods=["GET"])
@login_required
def export_accounts():
    pool_id = request.args.get("pool_id")
    status = request.args.get("status")

    conn = db_conn()
    cur = conn.cursor()
    params = []
    where = []
    if pool_id:
        where.append("a.pool_id = ?")
        params.append(pool_id)
    if status:
        where.append("a.status = ?")
        params.append(status)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    cur.execute(f"""
        SELECT p.name AS pool_name, a.account_name, a.account_password, a.status, a.remark
        FROM accounts a
        JOIN pools p ON a.pool_id = p.id
        {where_sql}
        ORDER BY a.id ASC
    """, tuple(params))
    rows = cur.fetchall()
    conn.close()

    # 文本格式：pool,account,password,status,remark
    lines = ["pool,account,password,status,remark"]
    for r in rows:
        # 简单转义逗号
        def esc(s):
            s = s or ""
            s = str(s).replace(",", "，")
            return s
        lines.append(f"{esc(r['pool_name'])},{esc(r['account_name'])},{esc(r['account_password'])},{esc(r['status'])},{esc(r['remark'])}")

    text = "\n".join(lines)
    resp = make_response(text)
    resp.headers["Content-Type"] = "text/plain; charset=utf-8"
    resp.headers["Content-Disposition"] = "attachment; filename=accounts.txt"
    return resp


# ---------------------------
# 启动
# ---------------------------
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
