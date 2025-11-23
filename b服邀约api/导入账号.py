# coding : utf-8
# @Time : 2025/11/8 2:50 
# @Author : Adolph
# @File : 导入账号.py
# @Software : PyCharm
import sqlite3
from pathlib import Path

DB_PATH = 'account_b.db'
TXT_PATH = 'B服已完成.txt'


def load_txt_to_db(db_path=DB_PATH, txt_path=TXT_PATH):
	with sqlite3.connect(db_path) as conn:
		cur = conn.cursor()
		
		# 批量插入
		sql = "INSERT INTO accounts (username, password) VALUES (?, ?)"
		batch = []
		
		for line in Path(txt_path).read_text(encoding="utf8").splitlines():
			if not line.strip():
				continue
			try:
				username, password, _time = map(str.strip, line.split("----", 2))
				batch.append((username, password))
			except ValueError:
				print(f"跳过格式错误行: {line}")
				continue
		try:
			cur.executemany(sql, batch)
		except sqlite3.IntegrityError:
			print(f"跳过重复用户名: {line[0]}")
		conn.commit()
		print(f"已导入 {len(batch)} 条记录，状态默认为 pending")

if __name__ == '__main__':
	load_txt_to_db()
