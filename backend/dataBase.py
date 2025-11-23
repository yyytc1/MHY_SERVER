# coding : utf-8
# @Time : 2025/8/21 20:02 
# @Author : Adolph
# @File : dataBase.py 
# @Software : PyCharm
import datetime
import sqlite3
from baseFunc import *


class DataBase:
	def __init__(self):
		self.db_path = 'sr.db'
		self.init_database()

	def init_database(self):
		conn = sqlite3.connect(self.db_path)
		cur = conn.cursor()
		
		# 用户
		cur.execute("""
		        CREATE TABLE IF NOT EXISTS users(
		          id INTEGER PRIMARY KEY AUTOINCREMENT,
		          username TEXT UNIQUE NOT NULL,
		          password_hash TEXT NOT NULL,
		          created_at INTEGER DEFAULT (strftime('%s','now'))
		        );
		        """)
		
		# 号池（只有 id、name）
		cur.execute("""
		        CREATE TABLE IF NOT EXISTS pool(
		          id INTEGER PRIMARY KEY AUTOINCREMENT,
		          name TEXT NOT NULL
		        );
		        """)
		
		# 代理
		cur.execute("""
		        CREATE TABLE IF NOT EXISTS proxies(
		          id INTEGER PRIMARY KEY AUTOINCREMENT,
		          device TEXT DEFAULT '',
		          proxy  TEXT NOT NULL,
		          status INTEGER NOT NULL DEFAULT 0,  -- 0:未使用 1:使用中 2:已封禁
		          remark TEXT DEFAULT '',
		          expired INTEGER DEFAULT 0,
		          updated_at INTEGER DEFAULT 0
		        );
		        """)
		
		# 密钥
		cur.execute("""
		        CREATE TABLE IF NOT EXISTS keys(
		          id INTEGER PRIMARY KEY AUTOINCREMENT,
		          value TEXT NOT NULL,
		          device_name TEXT DEFAULT '',
		          device_uuid TEXT DEFAULT '',
		          status INTEGER NOT NULL DEFAULT 0,  -- 0:未使用 1:使用中 2:已封禁
		          expired INTEGER DEFAULT 0,
		          remark TEXT DEFAULT ''
		        );
		        """)
		
		# 账号（绑定号池；可选绑定代理）
		cur.execute("""
		        CREATE TABLE IF NOT EXISTS accounts(
		          id INTEGER PRIMARY KEY AUTOINCREMENT,
		          hcid INTEGER NOT NULL, --号池id
		          use TEXT NOT NULL,    --用户名
		          pwd TEXT NOT NULL,    --游戏密码
		          email TEXT DEFAULT '', --邮箱密码
		          name TEXT DEFAULT '', --用户名
		          device TEXT DEFAULT '', --设备名
		          rate TEXT DEFAULT '', --性别
		          socket TEXT DEFAULT '', --代理
		          level INTEGER, --等级
		          money INTEGER, --星琼
		          tangle INTEGER, --专票
		          meet INTEGER, --通票
		          sid TEXT DEFAULT '', --绑定信息
		          status INTEGER NOT NULL DEFAULT 1,           -- 1:待使用 2:运行中 3:完成 4:异常 5:封禁
		          start_at INTEGER, --取号时间
		          updated_at INTEGER, --更新时间
		          note TEXT DEFAULT '', --备注
		          FOREIGN KEY(hcid) REFERENCES pool(id) ON DELETE CASCADE,
		          FOREIGN KEY(socket) REFERENCES proxies(id) ON DELETE SET NULL,
		          CHECK (status IN (0,1,2,3,4,5))
		        );
		        """)
		
		# 索引（常用筛选列）——修正：proxy_id 索引建在 proxy_id 上
		cur.execute("CREATE INDEX IF NOT EXISTS idx_accounts_pool ON accounts(hcid);")
		cur.execute("CREATE INDEX IF NOT EXISTS idx_accounts_status ON accounts(status);")
		cur.execute("CREATE INDEX IF NOT EXISTS idx_accounts_proxy ON accounts(id);")
		
		# 默认 admin
		cur.execute("SELECT 1 FROM users WHERE username='admin'")
		if cur.fetchone() is None:
			cur.execute(
				"INSERT INTO users(username,password_hash) VALUES(?,?)",
				("admin", hash_pw("123456"))
			)
		conn.commit()
		conn.close()
	
	def _conn(self):
		# timeout 防止立刻抛 OperationalError；row_factory 便于取字段
		conn = sqlite3.connect(self.db_path, timeout=3.0, isolation_level=None)
		conn.row_factory = sqlite3.Row
		return conn
	
	def user_login(self, user):
		with self._conn() as conn:
			cursor = conn.cursor()
			cursor.execute("SELECT * FROM users WHERE username=?", (user,))
			row = cursor.fetchone()
			return dict(row) if row else None

	def get_pool(self):
		with self._conn() as conn:
			cur = conn.cursor()
			cur.execute("SELECT id,name FROM pool ORDER BY id")
			items = [dict(r) for r in cur.fetchall()]
			return items
	
	def add_pool(self, name):
		with self._conn() as conn:
			cur = conn.cursor()
			cur.execute("INSERT INTO pool (name) VALUES (?)", (name,))
			return cur.lastrowid
	
	def revise_pool(self, pid, name):
		with self._conn() as conn:
			cur = conn.cursor()
			cur.execute("UPDATE pool SET name=? WHERE id=?", (name, pid))
	
	def delete_pool(self, pid):
		with self._conn() as conn:
			cur = conn.cursor()
			cur.execute("DELETE FROM pool WHERE id=?", (pid,))
	
	def add_account(self, hcid, data: dict) -> int:
		"""
		插入一条账号数据，返回新插入的 id
		data 预期结构：
		"""
		with self._conn() as conn:
			cur = conn.cursor()
			cur.execute(
				"""
				INSERT INTO accounts
				(hcid, use, pwd, email, name, device, rate, socket, level, money, tangle, meet, status, sid, note)
				VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
				""",
				(
					hcid,
					data.get("use"),
					data.get("pwd"),
					data.get("email"),
					data.get("name"),
					data.get("device"),
					data.get("rate"),
					data.get("socket"),
					data.get("level"),
					data.get("money"),
					data.get("tangle"),
					data.get("meet"),
					data.get("status"),
					data.get("sid"),
					data.get("note"),
				),
			)
			conn.commit()
			return cur.lastrowid
	
	
	def delete_account(self, email: str):
		with self._conn() as conn:
			cursor = conn.cursor()
			cursor.execute("DELETE FROM user_info WHERE email = ?", (email,))
			conn.commit()
