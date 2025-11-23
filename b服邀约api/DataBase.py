# coding : utf-8
# @Time : 2025/8/21 20:02 
# @Author : Adolph
# @File : dataBase.py 
# @Software : PyCharm
import datetime
import sqlite3


class DataBase:
	def __init__(self):
		self.db_path = 'account.db'
		self.init_database()
	
	def _conn(self):
		# timeout 防止立刻抛 OperationalError；row_factory 便于取字段
		conn = sqlite3.connect(self.db_path, timeout=3.0, isolation_level=None)
		conn.row_factory = sqlite3.Row
		return conn
	
	def init_database(self):
		conn = sqlite3.connect(self.db_path)
		c = conn.cursor()
		c.execute('''
			CREATE TABLE IF NOT EXISTS accounts (
				id INTEGER PRIMARY KEY,
				username TEXT UNIQUE,
				password TEXT,
				account_status TEXT,
				account_token TEXT,
				invite_status TEXT DEFAULT 'pending',
				com_token TEXT,
				devicecode TEXT,
				devicename TEXT,
				hkrpg_token TEXT,
				uid TEXT,
				invite_code TEXT,
				start_at DATETIME,
                update_at DATETIME
			)
		''')
		c.execute('''
			CREATE TABLE IF NOT EXISTS user_info (
				secret_key TEXT PRIMARY KEY,
				invite_code TEXT,
				invite_num INTEGER
			)
		''')
		conn.commit()
		conn.close()
	
	def get_not_invited(self):
		with self._conn() as conn:
			sql = """
			UPDATE accounts
			SET invite_status = 'binding'
			WHERE id = (SELECT id FROM accounts WHERE invite_status = 'not_invited' LIMIT 1)
			RETURNING *
			"""
			row = conn.execute(sql).fetchone()
			return dict(row) if row else None
	
	def update_token(self, id_: int, invite_status: str, token: str | None = None,
	                 uid: str | None = None) -> dict | None:
		"""
		更新 invite_status / hkrpg_token / uid
		若 start_at 为 NULL 或空字符串，则设为本地当前时间
		返回更新后的整行，若无此 id 返回 None
		"""
		now_local = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		
		with self._conn() as conn:
			parts = ["invite_status = ?", "start_at = COALESCE(NULLIF(start_at,''), ?)"]
			params = [invite_status, now_local]
			
			if token is not None and token != '':
				parts.append("hkrpg_token = ?")
				params.append(token)
			
			if uid is not None and uid != '':
				parts.append("uid = ?")
				params.append(uid)
			
			params.append(id_)
			sql = f"UPDATE accounts SET {', '.join(parts)} WHERE id = ?"
			cur = conn.execute(sql, params)
			
			if cur.rowcount == 0:
				return None
			
			row = conn.execute("SELECT * FROM accounts WHERE id = ?", (id_,)).fetchone()
			return dict(row) if row else None
	
	def update_account_row(self, acc_id: int, status: str, invite_code: str | None = None) -> dict | None:
		now_local = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		parts = ["invite_status = ?", "update_at = ?"]
		params = [status, now_local]
		
		if invite_code is not None:
			parts.append("invite_code = ?")
			params.append(invite_code)
		
		params.append(acc_id)
		sql = f"UPDATE accounts SET {', '.join(parts)} WHERE id = ? RETURNING *"
		
		with self._conn() as conn:
			row = conn.execute(sql, params).fetchone()
			return dict(row) if row else None
	
	def get_pending_or_running(self, devicename: str, devicecode: str):
		with self._conn() as conn:
			row = conn.execute(
				"""
				SELECT *
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
			RETURNING *
			"""
			row = conn.execute(sql, (devicename, devicecode)).fetchone()
			return dict(row) if row else None
	
	#############################  用户密钥  #############################
	def update_order(self, secret_key: str, invite_code: str, invite_num=4):
		conn = sqlite3.connect(self.db_path)
		cursor = conn.cursor()
		cursor.execute('''
				INSERT INTO user_info (secret_key, invite_code, invite_num)
				VALUES (?, ?, ?)
				ON CONFLICT(secret_key) DO UPDATE SET invite_code=?, invite_num=?
			''', (secret_key, invite_code, invite_num, invite_code, invite_num))
		conn.commit()
		conn.close()
	
	def get_invite_num(self, secret_key: str):
		conn = sqlite3.connect(self.db_path)
		cursor = conn.cursor()
		cursor.execute('SELECT invite_num FROM user_info WHERE secret_key = ?', (secret_key,))
		row = cursor.fetchone()
		conn.close()
		
		if row and row[0]:
			return row[0]
		return None
	
	def delete_order(self, secret_key: str):
		conn = sqlite3.connect(self.db_path)
		cursor = conn.cursor()
		cursor.execute("DELETE FROM user_info WHERE secret_key = ?", (secret_key,))
		conn.commit()
		conn.close()
	
	def get_secret_key(self, using_secret_keys: set):
		conn = sqlite3.connect(self.db_path)
		cursor = conn.cursor()
		if len(using_secret_keys) == 0:
			cursor.execute("SELECT * FROM user_info LIMIT 1")
		else:
			placeholders = ','.join('?' * len(using_secret_keys))
			sql = f"""
                SELECT *
                FROM user_info
                WHERE secret_key NOT IN ({placeholders})
                LIMIT 1
            """
			cursor.execute(sql, tuple(using_secret_keys))
		row = cursor.fetchone()
		conn.close()
		return row

	def get_all_orders(self):
		with self._conn() as conn:
			row = conn.execute('SELECT COUNT(*) AS c FROM user_info').fetchone()
			return row['c'] if row is not None else 0

	def get_all_accounts(self):
		with self._conn() as conn:
			status_rows = conn.execute("SELECT DISTINCT invite_status FROM accounts ORDER BY invite_status").fetchall()
			statuses = [r['invite_status'] for r in status_rows]
			ui_rows = conn.execute("SELECT * FROM user_info ORDER BY secret_key").fetchall()
			return ui_rows, statuses
	

if __name__ == '__main__':
	asd = DataBase()
	asd.update_order('1', '3', 2)
