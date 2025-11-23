# coding : utf-8
# @Time : 2025/9/5 0:00 
# @Author : Adolph
# @File : config.py 
# @Software : PyCharm
from DataBase import DataBase

config_file = 'config.json'
error_file = 'error.txt'
error_order_file = '异常订单.txt'
error_acc_file = '异常账号.txt'
db = DataBase()

get_sk5_enabled = True

COMPLETED_ORDERS = 0
FAILED_ORDERS = 0
