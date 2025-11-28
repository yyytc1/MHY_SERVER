# coding : utf-8
# @Time : 2025/11/16 16:10 
# @Author : Adolph
# @File : base_func.py
# @Software : PyCharm
import base64
import random
import string
import uuid

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

PUBLIC_KEY_PEM = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDDvekdPMHN3AYhm/vktJT+YJr7
cI5DcsNKqdsx5DZX0gDuWFuIjzdwButrIYPNmRJ1G8ybDIF7oDW2eEpm5sMbL9zs
9ExXCdvqrn51qELbqj0XxtMTIpaCHFSI50PfPpTFV9Xt/hmyVwokoOXFlAEgCn+Q
CgGs52bFoYMtyi+xEQIDAQAB
-----END PUBLIC KEY-----"""


def rsa_encrypt(message: str) -> str:
	"""RSA PKCS#1 v1.5 加密并返回 Base64 字符串"""
	# 1. 加载 PEM 公钥
	public_key = serialization.load_pem_public_key(
		PUBLIC_KEY_PEM.encode(),
		backend=default_backend()
	)
	
	# 2. 加密
	encrypted = public_key.encrypt(
		message.encode("utf-8"),
		padding.PKCS1v15()
	)
	
	# 3. Base64 编码
	return base64.b64encode(encrypted).decode("utf-8")


def random_device_fp():
	return '38d813cfab1' + ''.join(random.choices(string.hexdigits, k=2)).lower()


def random_uuid():
	return str(uuid.uuid4())
