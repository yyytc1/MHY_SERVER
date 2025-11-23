# coding : utf-8
# @Time : 2025/11/5 22:38 
# @Author : Adolph
# @File : config.py 
# @Software : PyCharm
from backend.dataBase import DataBase

config_filename = 'config.json'

acc_status = ['待使用', '运行中', '完成', '账号异常', '账号封禁']

db = DataBase()
