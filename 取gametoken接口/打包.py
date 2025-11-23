# coding : utf-8
# @Time : 2025/11/16 14:17 
# @Author : Adolph
# @File : 打包.py 
# @Software : PyCharm
# coding : utf-8
# @Time : 2025/11/6 7:07
# @Author : Adolph
# @File : 打包.py
# @Software : PyCharm
import datetime
import glob
import os
import shutil
import subprocess
import time


ver = '1.2'
app_name = f'取gametoken_{ver}'


if __name__ == '__main__':
	file = 'main.py'
	if not os.path.exists(file):
		print(f'{file} 文件不存在')
	else:
		cmd = f'pyinstaller -F -n {app_name} {file}'
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
