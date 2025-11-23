# coding : utf-8
# @Time : 2024/3/13 14:30
# @Author : Adolph
# @File : 打包.py
# @Software : PyCharm
import datetime
import glob
import os
import shutil
import subprocess
import sys
import time

static_dir = 'bd1bd376b05a46ad98c16ba0c'
icon_filename = 'icon.ico'
base_dir = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)

if getattr(sys, 'frozen', False):
	icon_path = os.path.join(sys._MEIPASS, static_dir, icon_filename)
else:
	icon_path = os.path.join(os.path.dirname(__file__), 'static', icon_filename)

ver = f'1.0'
app_name = f'BCG-Arc_{ver}'
if __name__ == '__main__':
	file = 'main.py'
	if not os.path.exists(file):
		print(f'{file} 文件不存在')
	else:
		add_icon = f'--add-data "static/{icon_filename}:{static_dir}"'
		cmd = f'pyinstaller -F -i static/icon.ico {add_icon} -n {app_name} {file}'
		if os.path.exists('build'):
			shutil.rmtree('build')
		if os.path.exists('dist'):
			shutil.rmtree('dist')
		
		files = glob.glob("*.spec")
		if files:
			for file in files:
				os.remove(file)
		
		subprocess.Popen(cmd, shell=True)
		while 1:
			if os.path.exists('dist'):
				if os.path.exists(f'dist/{app_name}.exe'):
					time.sleep(1)
					print(f'{datetime.datetime.now()}  打包完成')
					print('记得检查有没有加验证！！！')
					print('记得检查有没有加验证！！！')
					print('记得检查有没有加验证！！！')
					print('记得检查有没有加验证！！！')
					print('记得检查有没有加验证！！！')
					break
			time.sleep(1)
