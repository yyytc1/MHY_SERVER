# coding : utf-8
# @Time : 2025/11/12 22:40 
# @Author : Adolph
# @File : baseFunc.py 
# @Software : PyCharm
from hashlib import sha256


def hash_pw(s: str) -> str:
	return sha256(("slat@QF" + s).encode("utf-8")).hexdigest()
